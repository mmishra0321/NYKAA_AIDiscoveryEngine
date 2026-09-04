"""Groq catalog section; retry once on parse/lint failure, then stub."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from src.config_loader import load_prompts
from src.generation.lint import catalog_lint_text, lint_hits
from src.generation.stub import residual_theme, stub_section
from src.models.schemas import CatalogQuestion, SubTheme
from src.processing.groq_client import GroqClient
from src.processing.jsonutil import parse_json_object

logger = logging.getLogger(__name__)


def themes_for_question(
    qid: str,
    pack: dict[str, Any],
    all_themes: list[SubTheme],
) -> list[SubTheme]:
    matched = [t for t in all_themes if t.question_id == qid]
    matched.sort(key=lambda t: (t.impact_rank or 99, -t.impact_score))
    if matched:
        return matched
    if int(pack.get("hit_count") or 0) > 0:
        return [residual_theme(qid, pack)]
    return []


def _user_prompt(query: dict[str, Any], pack: dict[str, Any], themes: list[SubTheme]) -> str:
    excerpts = []
    for hit in (pack.get("hits") or [])[:10]:
        cid = hit.get("chunk_id") or ""
        text = (hit.get("text") or "")[:400]
        excerpts.append(f"[{cid}] source={hit.get('source')} {text}")
    rollup = [
        {
            "sub_theme_id": t.sub_theme_id,
            "name": t.name,
            "share_of_bucket": t.share_of_bucket,
            "source_diversity": t.source_diversity,
            "sources": t.sources,
            "frequency": t.frequency.value if hasattr(t.frequency, "value") else t.frequency,
            "severity": t.severity.value if hasattr(t.severity, "value") else t.severity,
            "impact_score": t.impact_score,
            "hypothesis": t.hypothesis,
        }
        for t in themes
    ]
    return (
        f"Question id: {query['id']}\n"
        f"Question: {query.get('question')}\n"
        f"Focus: {query.get('generation_focus') or ''}\n"
        f"Retrieved hit_count: {pack.get('hit_count')}\n"
        f"Source counts: {json.dumps(pack.get('source_counts') or {})}\n"
        f"Sub-theme rollup (authoritative stats — do not invent numbers):\n{json.dumps(rollup, indent=2)}\n\n"
        f"Excerpts (cite [chunk_id] internally; paraphrase for user-facing examples):\n"
        + "\n".join(excerpts)
        + "\n\nReturn JSON with keys: summary, implications (array of strings), "
        "interview_probes (array), confidence (high|medium|low), data_gaps (string), "
        "paraphrased_examples (array of short paraphrases, not quotes)."
    )


def _apply_prose(base: CatalogQuestion, payload: dict[str, Any]) -> CatalogQuestion:
    summary = str(payload.get("summary") or base.summary).strip()
    implications = [str(x).strip() for x in (payload.get("implications") or []) if str(x).strip()]
    probes = [str(x).strip() for x in (payload.get("interview_probes") or []) if str(x).strip()]
    examples = [str(x).strip() for x in (payload.get("paraphrased_examples") or []) if str(x).strip()]
    conf = str(payload.get("confidence") or base.confidence).lower()
    if conf not in {"high", "medium", "low"}:
        conf = base.confidence
    gaps = str(payload.get("data_gaps") or base.data_gaps)
    themes = list(base.sub_themes)
    if examples and themes:
        themes[0] = themes[0].model_copy(update={"paraphrased_examples": examples[:3]})
    return base.model_copy(
        update={
            "summary": summary,
            "implications": implications or base.implications,
            "interview_probes": probes or base.interview_probes,
            "confidence": conf,
            "data_gaps": gaps,
            "sub_themes": themes,
        }
    )


def _section_dict(section: CatalogQuestion) -> dict[str, Any]:
    return section.model_dump(mode="json")


def generate_section(
    *,
    query: dict[str, Any],
    pack: dict[str, Any],
    themes: list[SubTheme],
    stub: bool,
    client: Optional[GroqClient] = None,
    classified_docs: int | None = None,
) -> tuple[CatalogQuestion, str]:
    """Returns (section, mode) where mode is stub | groq | groq_fallback_stub."""
    q_themes = themes_for_question(str(query["id"]), pack, themes)
    fallback = stub_section(
        query=query,
        pack=pack,
        themes=q_themes,
        classified_docs=classified_docs,
    )
    if stub or client is None or not client.available:
        return fallback, "stub"

    prompts = load_prompts()
    temp = float(prompts.get("temperature") or 0.2)
    messages = [
        {"role": "system", "content": str(prompts.get("generate_system") or "")},
        {"role": "user", "content": _user_prompt(query, pack, q_themes)},
    ]
    last_err = ""
    for attempt in range(2):
        try:
            if attempt == 1:
                messages = messages + [
                    {
                        "role": "user",
                        "content": (
                            "Rewrite. Do not recommend coupons, discounts, cashback, or price-cuts. "
                            "JSON only."
                        ),
                    }
                ]
            raw = client.chat(messages, temperature=temp)
            payload = parse_json_object(raw)
            section = _apply_prose(fallback, payload)
            hits = lint_hits(catalog_lint_text(_section_dict(section)))
            if hits:
                last_err = f"lint: {hits}"
                logger.warning("Generate lint %s on %s attempt %s", hits, query["id"], attempt + 1)
                continue
            return section, "groq"
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
            logger.warning("Generate Groq failed for %s: %s", query["id"], exc)
    logger.info("Falling back to stub for %s (%s)", query["id"], last_err)
    return fallback, "groq_fallback_stub"
