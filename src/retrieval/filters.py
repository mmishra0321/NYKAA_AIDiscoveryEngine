"""Q7 / Q8 / Q9 / Q10 post-filters on retrieved hits."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.models.schemas import SubTheme


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [part for part in str(value).split(",") if part]


def prefer_decision_factors(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        hits,
        key=lambda h: (0 if h.get("decision_factors") else 1, -float(h.get("similarity") or 0.0)),
    )


def interleave_intent(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {
        "purchase_intent": [],
        "bookmark": [],
        "unclear": [],
    }
    for hit in hits:
        label = str(hit.get("intent_label") or "unclear")
        if label not in buckets:
            label = "unclear"
        buckets[label].append(hit)
    order = ("purchase_intent", "bookmark", "unclear")
    out: list[dict[str, Any]] = []
    while True:
        added = False
        for key in order:
            if buckets[key]:
                out.append(buckets[key].pop(0))
                added = True
        if not added:
            break
    return out


def stratify_segment_category(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for hit in hits:
        key = (
            str(hit.get("segment_hint") or "unknown"),
            str(hit.get("product_category") or "unknown"),
        )
        buckets[key].append(hit)
    keys = sorted(buckets, key=lambda k: (k[0] == "unknown" and k[1] == "unknown", k))
    out: list[dict[str, Any]] = []
    while True:
        added = False
        for key in keys:
            if buckets[key]:
                out.append(buckets[key].pop(0))
                added = True
        if not added:
            break
    return out


def q10_qualifying_themes(themes: list[SubTheme], *, min_sources: int) -> list[SubTheme]:
    return [
        t
        for t in themes
        if t.question_id == "q10_unmet_needs" and t.source_diversity >= min_sources
    ]


def filter_q10_hits(
    hits: list[dict[str, Any]],
    themes: list[SubTheme],
    *,
    min_sources: int,
) -> list[dict[str, Any]]:
    qualifying = q10_qualifying_themes(themes, min_sources=min_sources)
    if not qualifying:
        return []
    theme_ids = {t.sub_theme_id for t in qualifying}
    chunk_ids = {cid for t in qualifying for cid in t.chunk_ids}
    kept: list[dict[str, Any]] = []
    for hit in hits:
        ids = set(hit.get("sub_theme_ids") or [])
        if ids & theme_ids or hit.get("chunk_id") in chunk_ids:
            kept.append(hit)
    return kept
