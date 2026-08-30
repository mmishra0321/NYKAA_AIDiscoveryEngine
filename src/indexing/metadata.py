"""Chroma-safe metadata from processed chunks + parent documents."""

from __future__ import annotations

from typing import Any

from src.config_loader import canonical_queries
from src.models.schemas import ReviewChunk, ReviewDocument


def question_ids() -> list[str]:
    return [q["id"] for q in canonical_queries()]


def _join(values: list[str]) -> str:
    return ",".join(v for v in values if v)


def chunk_metadata(
    chunk: ReviewChunk,
    document: ReviewDocument | None = None,
) -> dict[str, Any]:
    """Primitives only — Chroma rejects lists/None."""
    qs = list(chunk.research_questions)
    themes = list(chunk.sub_theme_ids)
    relevance = "wishlist_signal"
    factors: list[str] = []
    intent = "unclear"
    if document is not None:
        relevance = document.relevance.value
        factors = list(document.decision_factors)
        intent = document.intent_label.value
        if not qs:
            qs = list(document.research_questions)
        if not themes:
            themes = list(document.sub_theme_ids)

    meta: dict[str, Any] = {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "source": chunk.source.value,
        "research_questions": _join(qs),
        "sub_theme_ids": _join(themes),
        "segment_hint": chunk.segment_hint.value,
        "product_category": chunk.product_category.value,
        "relevance": relevance,
        "date": chunk.date.isoformat(),
        "url": chunk.url or "",
        "decision_factors": _join(factors),
        "intent_label": intent,
    }
    assigned = set(qs)
    for qid in question_ids():
        meta[f"has_{qid}"] = qid in assigned
    return meta
