"""Build the Q1–Q10 catalog from retrieval packs + sub-theme rollup."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import date
from typing import Any, Optional

from src.config_loader import canonical_queries
from src.generation.generate import generate_section
from src.generation.lint import catalog_lint_text, lint_hits
from src.generation.loader import load_generation_inputs
from src.generation.markdown import render_markdown
from src.generation import storage as store
from src.models.schemas import CatalogQuestion, CatalogReport, SubTheme
from src.processing.groq_client import GroqClient

logger = logging.getLogger(__name__)


def _pack_by_id(packs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(p.get("query_id")): p for p in packs if p.get("query_id")}


def _coverage_ok(questions: list[CatalogQuestion]) -> bool:
    if len(questions) != 10:
        return False
    for q in questions:
        has_section = bool(q.sub_themes) or bool((q.data_gaps or "").strip())
        if not q.summary or not has_section:
            return False
    return True


def run_generation(
    *,
    run_date: date | str | None = None,
    stub: bool = False,
    packs: Optional[list[dict[str, Any]]] = None,
    themes: Optional[list[SubTheme]] = None,
    corpus: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    client = GroqClient()
    use_stub = bool(stub or not client.available)
    if packs is None:
        packs, themes_loaded, corpus_loaded, day = load_generation_inputs(run_date)
        if themes is None:
            themes = themes_loaded
        if corpus is None:
            corpus = corpus_loaded
    else:
        if run_date is None:
            day = date.today().isoformat()
        else:
            day = run_date.isoformat() if isinstance(run_date, date) else str(run_date)
        themes = themes or []
        corpus = corpus or {"relevant": 0, "noise": 0, "sources": {}}

    by_id = _pack_by_id(packs)
    modes: list[str] = []
    questions: list[CatalogQuestion] = []
    lint_blocked = 0

    for query in canonical_queries():
        pack = by_id.get(str(query["id"])) or {
            "query_id": query["id"],
            "question": query.get("question"),
            "flag": "data_gap",
            "data_gap": f"No retrieval pack for {query['id']}.",
            "hit_count": 0,
            "hits": [],
            "source_counts": {},
        }
        section, mode = generate_section(
            query=query,
            pack=pack,
            themes=themes,
            stub=use_stub,
            client=client,
        )
        leftover = lint_hits(catalog_lint_text(section.model_dump(mode="json")))
        if leftover:
            lint_blocked += 1
            logger.warning("Post-generate lint on %s: %s — forcing stub", query["id"], leftover)
            section, mode = generate_section(
                query=query,
                pack=pack,
                themes=themes,
                stub=True,
                client=None,
            )
            mode = "lint_forced_stub"
        modes.append(mode)
        questions.append(section)

    report = CatalogReport(
        generated_at=store.utc_now_iso(),
        kpi="wishlist_to_purchase_30d",
        corpus=corpus,
        questions=questions,
    )
    markdown = render_markdown(report)
    md_lint = lint_hits(markdown)
    if md_lint:
        raise RuntimeError(f"catalog markdown failed monetary-incentive lint: {md_lint}")

    counts = Counter(modes)
    summary = {
        "run_date": day,
        "finished_at": store.utc_now_iso(),
        "mode": "stub" if use_stub else "groq",
        "section_modes": dict(counts),
        "questions": len(questions),
        "with_themes": sum(1 for q in questions if q.themes_count > 0),
        "explicit_gaps": sum(1 for q in questions if q.data_gaps),
        "coverage_10_of_10": _coverage_ok(questions),
        "lint_blocked": lint_blocked,
        "lint_markdown_hits": md_lint,
        "kpi": report.kpi,
        "limitations": [
            "Groq retry-once then retrieval stub if parse or discount-lint fails.",
            "User-facing examples are paraphrases; chunk_ids stay internal on sub-themes.",
            "Price as a decision factor is in scope; coupons/discounts as a mechanism are not.",
        ],
    }
    out_dir = store.save_catalog(report, markdown, summary, run_date=day)
    summary["output_dir"] = str(out_dir)
    logger.info(
        "Phase 5 %s: %s questions, coverage=%s → %s",
        summary["mode"],
        len(questions),
        summary["coverage_10_of_10"],
        out_dir,
    )
    return summary
