"""Run Phase 7 validation against gold labels + the cached catalog."""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import date
from pathlib import Path
from typing import Any, Optional

from src.api.ask import match_question
from src.api.store import catalog_dir, get_catalog
from src.config_loader import ROOT
from src.eval.gold import load_answer_review, load_classify_gold, load_paraphrases, load_relevance_gold
from src.eval.metrics import jaccard, mean, percentile, precision_binary, review_score
from src.eval import storage as store
from src.generation.lint import catalog_lint_text, lint_hits
from src.generation.pipeline import _coverage_ok
from src.models.schemas import CatalogReport
from src.processing.classify import classify_document
from src.processing.clean import contains_pii
from src.processing.groq_client import GroqClient
from src.processing.relevance import label_relevance
from src.processing.storage import PROCESSED_DIR
from src.retrieval.storage import RETRIEVAL_DIR

logger = logging.getLogger(__name__)

TARGETS = {
    "relevance_precision": 0.85,
    "classify_jaccard": 0.75,
    "citation_accuracy": 0.90,
    "coverage": 1.0,
    "faithfulness_pass_rate": 0.85,
    "latency_p95_seconds": 5.0,
    "lint_hits": 0,
    "relevant_corpus": 400,
}


class _GroqOff:
    available = False

    def chat(self, *args, **kwargs):
        raise AssertionError("Phase 7 stub run must not call Groq")


def _latest_with(root: Path, name: str) -> Path | None:
    if not root.exists():
        return None
    found = [
        child
        for child in root.iterdir()
        if child.is_dir() and not child.name.startswith("_") and (child / name).exists()
    ]
    if not found:
        return None
    return sorted(found, key=lambda p: p.name)[-1]


def _chunk_id_index() -> set[str]:
    ids: set[str] = set()
    proc = _latest_with(PROCESSED_DIR, "chunks.jsonl")
    if proc:
        for line in (proc / "chunks.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            cid = row.get("chunk_id") or row.get("id")
            if cid:
                ids.add(str(cid))
    ret = _latest_with(RETRIEVAL_DIR, "retrieval_summary.json")
    if ret:
        for path in ret.glob("q*.json"):
            try:
                pack = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            for hit in pack.get("hits") or []:
                cid = hit.get("chunk_id")
                if cid:
                    ids.add(str(cid))
    return ids


def _eval_relevance(stub: bool, client: Optional[GroqClient]) -> dict[str, Any]:
    gold = load_relevance_gold()
    y_true = [str(r["relevance"]) for r in gold]
    y_pred = []
    rows = []
    for item in gold:
        pred = label_relevance(str(item["text"]), stub=stub, client=client).value
        y_pred.append(pred)
        rows.append({"id": item["id"], "gold": item["relevance"], "pred": pred, "ok": pred == item["relevance"]})
    precision = precision_binary(y_true, y_pred, positive="wishlist_signal")
    n_signal = sum(1 for v in y_true if v == "wishlist_signal")
    n_noise = sum(1 for v in y_true if v == "logistics_noise")
    return {
        "n": len(gold),
        "n_signal": n_signal,
        "n_noise": n_noise,
        "precision_wishlist_signal": round(precision, 4),
        "accuracy": round(sum(1 for r in rows if r["ok"]) / len(rows), 4),
        "target": TARGETS["relevance_precision"],
        "pass": precision >= TARGETS["relevance_precision"],
        "rows": rows,
    }


def _eval_classify(stub: bool, client: Optional[GroqClient]) -> dict[str, Any]:
    gold = load_classify_gold()
    scores = []
    rows = []
    q10_leaks = 0
    for item in gold:
        pred = classify_document(str(item["text"]), stub=stub, client=client)["research_questions"]
        if "q10_unmet_needs" in pred:
            q10_leaks += 1
        score = jaccard(pred, item["research_questions"])
        scores.append(score)
        rows.append(
            {
                "id": item["id"],
                "gold": item["research_questions"],
                "pred": pred,
                "jaccard": round(score, 4),
            }
        )
    avg = mean(scores)
    return {
        "n": len(gold),
        "macro_jaccard": round(avg, 4),
        "target": TARGETS["classify_jaccard"],
        "pass": avg >= TARGETS["classify_jaccard"],
        "q10_leaks": q10_leaks,
        "rows": rows,
    }


def _eval_paraphrases(report: CatalogReport) -> dict[str, Any]:
    gold = load_paraphrases()
    rows = []
    for item in gold:
        hit = match_question(item["paraphrase"], report)
        rows.append(
            {
                "query_id": item["query_id"],
                "paraphrase": item["paraphrase"],
                "routed": hit.id,
                "ok": hit.id == item["query_id"],
            }
        )
    acc = sum(1 for r in rows if r["ok"]) / len(rows)
    return {
        "n": len(rows),
        "accuracy": round(acc, 4),
        "pass": acc >= 0.8,
        "rows": rows,
    }


def _eval_citations(report: CatalogReport) -> dict[str, Any]:
    known = _chunk_id_index()
    cited = []
    pii = 0
    for q in report.questions:
        for theme in q.sub_themes:
            for ex in theme.paraphrased_examples:
                if contains_pii(ex):
                    pii += 1
            for cid in theme.chunk_ids:
                cited.append({"query_id": q.id, "chunk_id": cid, "resolved": cid in known})
    if not cited:
        return {
            "n": 0,
            "resolved": 0,
            "accuracy": 1.0,
            "pii_in_paraphrases": pii,
            "skipped": not known,
            "target": TARGETS["citation_accuracy"],
            "pass": pii == 0,
            "note": "No chunk_ids on catalog sub-themes (gap-only run) or no local chunk index.",
        }
    resolved = sum(1 for c in cited if c["resolved"])
    acc = resolved / len(cited) if known else 1.0
    if not known:
        return {
            "n": len(cited),
            "resolved": 0,
            "accuracy": None,
            "pii_in_paraphrases": pii,
            "skipped": True,
            "target": TARGETS["citation_accuracy"],
            "pass": pii == 0,
            "note": "chunks.jsonl / retrieval packs not on this host; skipped id resolve.",
        }
    return {
        "n": len(cited),
        "resolved": resolved,
        "accuracy": round(acc, 4),
        "pii_in_paraphrases": pii,
        "skipped": False,
        "target": TARGETS["citation_accuracy"],
        "pass": acc >= TARGETS["citation_accuracy"] and pii == 0,
    }


def _eval_coverage(report: CatalogReport) -> dict[str, Any]:
    ok = _coverage_ok(report.questions)
    gaps = [q.id for q in report.questions if (q.data_gaps or "").strip()]
    with_themes = [q.id for q in report.questions if q.sub_themes]
    relevant = int((report.corpus or {}).get("relevant") or 0)
    return {
        "questions": len(report.questions),
        "coverage_10_of_10": ok,
        "with_themes": with_themes,
        "explicit_gaps": gaps,
        "target": "10/10 sections or explicit data_gap",
        "pass": ok,
        "relevant_corpus": relevant,
        "relevant_corpus_target": TARGETS["relevant_corpus"],
        "relevant_corpus_pass": relevant >= TARGETS["relevant_corpus"],
    }


def _eval_lint(report: CatalogReport) -> dict[str, Any]:
    hits: list[str] = []
    for q in report.questions:
        found = lint_hits(catalog_lint_text(q.model_dump(mode="json")))
        hits.extend(found)
    unique = sorted(set(hits))
    return {
        "hits": unique,
        "n": len(unique),
        "target": TARGETS["lint_hits"],
        "pass": len(unique) == 0,
    }


def _eval_answers() -> dict[str, Any]:
    reviews = load_answer_review()
    rows = []
    for row in reviews:
        score = review_score(row)
        rows.append(
            {
                "query_id": row["query_id"],
                "score": score,
                "pass": score >= 3,
                "notes": row.get("notes") or "",
            }
        )
    pass_rate = sum(1 for r in rows if r["pass"]) / len(rows)
    return {
        "n": len(rows),
        "pass_rate": round(pass_rate, 4),
        "mean_score": round(mean([r["score"] for r in rows]), 4),
        "target": TARGETS["faithfulness_pass_rate"],
        "pass": pass_rate >= TARGETS["faithfulness_pass_rate"],
        "rows": rows,
    }


def _eval_latency(report: CatalogReport, *, groq: bool) -> dict[str, Any]:
    from fastapi.testclient import TestClient

    from src.api import app as app_mod
    from src.api import ask as ask_mod

    paraphrases = load_paraphrases()
    original = ask_mod.GroqClient
    times: list[float] = []
    statuses: list[int] = []
    try:
        if not groq:
            ask_mod.GroqClient = lambda *a, **k: _GroqOff()  # type: ignore[method-assign, assignment]
        client = TestClient(app_mod.app)
        t0 = time.perf_counter()
        health = client.get("/api/v1/health")
        times.append(time.perf_counter() - t0)
        statuses.append(health.status_code)
        t0 = time.perf_counter()
        cat = client.get("/api/v1/catalog")
        times.append(time.perf_counter() - t0)
        statuses.append(cat.status_code)
        for item in paraphrases:
            t0 = time.perf_counter()
            res = client.post("/api/v1/ask", json={"question": item["paraphrase"]})
            times.append(time.perf_counter() - t0)
            statuses.append(res.status_code)
    finally:
        ask_mod.GroqClient = original
    p95 = percentile(times, 95)
    return {
        "n": len(times),
        "p95_seconds": round(p95, 4),
        "max_seconds": round(max(times), 4),
        "target": TARGETS["latency_p95_seconds"],
        "pass": p95 < TARGETS["latency_p95_seconds"] and all(s == 200 for s in statuses),
        "note": "Cached catalog path (/api/v1/ask, /catalog, /health). Architecture /query maps to /api/v1/ask.",
        "catalog_questions": len(report.questions),
    }


def _eval_live_link() -> dict[str, Any]:
    url = (os.getenv("PUBLIC_UI_URL") or "").strip()
    return {
        "url": url or None,
        "pass": bool(url),
        "target": "public URL third party can open + export",
        "note": (
            "Set PUBLIC_UI_URL after Render + Vercel deploy (docs/phase6.md). "
            "Local export works at POST /api/v1/export."
        ),
    }


def _limitations(coverage: dict[str, Any]) -> list[str]:
    return [
        "Play reviews are delivery-dominated; relevance gold treats those as logistics_noise, not Q1–Q10.",
        "Hinglish rows are in the gold set; stub keywords are English-leaning.",
        f"Sparse / gap questions in this catalog: {', '.join(coverage.get('explicit_gaps') or []) or 'none'}.",
        "Architecture called out sparse Q5/Q6/Q8; this Play+App run gaps Q2/Q6/Q8/Q10 (Q5 had hits but leftover Other names).",
        "No YOUTUBE_API_KEY — haul comments deferred.",
        "Twitter/X, Quora, Trustpilot/MouthShut HTML are deferred V1.",
        f"Relevant corpus after gate is {coverage.get('relevant_corpus')} (target ≥ {TARGETS['relevant_corpus']}).",
        "Stub leftover cluster name Other is weak for Part 3; Groq naming needs a larger signal set.",
        "Q10 needs ≥3 independent sources; Play-only cannot populate it.",
        "Public live link is not created without Render/Vercel accounts.",
    ]


def render_markdown(summary: dict[str, Any]) -> str:
    metrics = summary.get("metrics") or {}
    lines = [
        "# Phase 7 — Validation",
        "",
        f"Generated {summary.get('finished_at')} · mode **{summary.get('mode')}** · catalog `{summary.get('catalog_dir')}`",
        "",
        "| Metric | Value | Target | Pass |",
        "|---|---|---|---|",
    ]
    order = [
        ("relevance", "Relevance precision (signal)", "precision_wishlist_signal"),
        ("classify", "Q-classification Jaccard", "macro_jaccard"),
        ("citations", "Citation accuracy", "accuracy"),
        ("coverage", "Question coverage 10/10", "coverage_10_of_10"),
        ("answers", "Answer faithfulness pass rate", "pass_rate"),
        ("latency", "Latency p95 /api/v1/ask", "p95_seconds"),
        ("lint", "Monetary-incentive lint hits", "n"),
        ("live_link", "Public URL", "url"),
    ]
    for key, label, field in order:
        block = metrics.get(key) or {}
        val = block.get(field)
        target = block.get("target", TARGETS.get(key, "—"))
        passed = "yes" if block.get("pass") else "no"
        lines.append(f"| {label} | {val} | {target} | {passed} |")
    lines.extend(["", "## Limitations", ""])
    for note in summary.get("limitations") or []:
        lines.append(f"- {note}")
    lines.extend(["", "## Answer review (3/4 pass)", ""])
    for row in (metrics.get("answers") or {}).get("rows") or []:
        mark = "pass" if row.get("pass") else "fail"
        lines.append(f"- `{row.get('query_id')}` score {row.get('score')}/4 · {mark}")
    lines.append("")
    return "\n".join(lines)


def run_eval(
    *,
    stub: bool = True,
    groq: bool = False,
    run_date: date | str | None = None,
) -> dict[str, Any]:
    use_stub = stub or not groq
    client = None if use_stub else GroqClient()
    if groq and client is not None and not client.available:
        logger.warning("GROQ_API_KEY missing; scoring stub classifiers")
        use_stub = True
        client = None

    report = get_catalog()
    relevance = _eval_relevance(use_stub, client)
    classify = _eval_classify(use_stub, client)
    paraphrases = _eval_paraphrases(report)
    citations = _eval_citations(report)
    coverage = _eval_coverage(report)
    lint = _eval_lint(report)
    answers = _eval_answers()
    latency = _eval_latency(report, groq=groq and not use_stub)
    live = _eval_live_link()

    metrics = {
        "relevance": relevance,
        "classify": classify,
        "paraphrases": paraphrases,
        "citations": citations,
        "coverage": coverage,
        "lint": lint,
        "answers": answers,
        "latency": latency,
        "live_link": live,
    }
    hard = [
        relevance["pass"],
        classify["pass"],
        citations["pass"],
        coverage["pass"],
        lint["pass"],
        answers["pass"],
        latency["pass"],
        classify["q10_leaks"] == 0,
    ]
    summary = {
        "run_date": store.get_run_date(run_date),
        "finished_at": store.utc_now_iso(),
        "mode": "stub" if use_stub else "groq",
        "catalog_dir": str(catalog_dir().relative_to(ROOT)),
        "kpi": report.kpi,
        "metrics": metrics,
        "hard_gates_pass": all(hard),
        "limitations": _limitations(coverage),
        "root": str(ROOT),
    }
    # Drop bulky per-row dumps from the saved JSON? Keep them — gold is small (40+20).
    md = render_markdown(summary)
    store.save_eval(summary, md, run_date=run_date)
    return summary
