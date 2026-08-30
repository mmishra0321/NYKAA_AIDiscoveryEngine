"""Fetch and pack evidence per catalog question."""

from __future__ import annotations

from collections import Counter
from typing import Any, Optional

from src.config_loader import load_retrieval
from src.indexing.embedder import Embedder
from src.indexing.store import VectorIndex
from src.models.schemas import SubTheme
from src.retrieval.balance import source_balance
from src.retrieval.filters import (
    filter_q10_hits,
    interleave_intent,
    prefer_decision_factors,
    q10_qualifying_themes,
    split_csv,
    stratify_segment_category,
)


def retrieval_config() -> dict[str, Any]:
    return load_retrieval()


def _similarity(distance: Any) -> float:
    if distance is None:
        return 1.0
    try:
        return max(0.0, 1.0 - float(distance))
    except (TypeError, ValueError):
        return 0.0


def _hit(chunk_id: str, text: str, meta: dict[str, Any], distance: Any) -> dict[str, Any]:
    meta = meta or {}
    return {
        "chunk_id": chunk_id,
        "text": text or "",
        "source": meta.get("source") or "unknown",
        "similarity": round(_similarity(distance), 4),
        "research_questions": split_csv(meta.get("research_questions")),
        "sub_theme_ids": split_csv(meta.get("sub_theme_ids")),
        "segment_hint": meta.get("segment_hint") or "unknown",
        "product_category": meta.get("product_category") or "unknown",
        "intent_label": meta.get("intent_label") or "unclear",
        "decision_factors": split_csv(meta.get("decision_factors")),
        "relevance": meta.get("relevance") or "wishlist_signal",
        "url": meta.get("url") or "",
        "date": meta.get("date") or "",
        "document_id": meta.get("document_id") or "",
    }


def parse_query_result(result: dict[str, Any]) -> list[dict[str, Any]]:
    ids = (result.get("ids") or [[]])[0] or []
    docs = (result.get("documents") or [[]])[0] or []
    metas = (result.get("metadatas") or [[]])[0] or []
    dists = (result.get("distances") or [[]])[0] or []
    hits: list[dict[str, Any]] = []
    for i, chunk_id in enumerate(ids):
        text = docs[i] if i < len(docs) else ""
        meta = metas[i] if i < len(metas) else {}
        dist = dists[i] if i < len(dists) else None
        hits.append(_hit(str(chunk_id), str(text), meta or {}, dist))
    return hits


def parse_get_result(result: dict[str, Any]) -> list[dict[str, Any]]:
    ids = result.get("ids") or []
    docs = result.get("documents") or []
    metas = result.get("metadatas") or []
    hits: list[dict[str, Any]] = []
    for i, chunk_id in enumerate(ids):
        text = docs[i] if i < len(docs) else ""
        meta = metas[i] if i < len(metas) else {}
        hits.append(_hit(str(chunk_id), str(text), meta or {}, None))
    return hits


def fetch_candidates(
    index: VectorIndex,
    embedder: Embedder,
    query: dict[str, Any],
    *,
    top_k: int,
) -> list[dict[str, Any]]:
    qid = str(query["id"])
    where = {f"has_{qid}": True}
    n = min(max(top_k, 1), max(index.count(), 1))
    blob = str(query.get("question") or "")
    for para in query.get("paraphrases") or []:
        blob += " " + str(para)
    try:
        vector = embedder.encode([blob])[0]
        raw = index.query(query_embeddings=[vector], n_results=n, where=where)
        hits = parse_query_result(raw)
    except Exception:  # noqa: BLE001
        hits = []
    if not hits:
        hits = parse_get_result(index.get_where(where, limit=top_k))
    return hits


def apply_strategy(
    query_id: str,
    hits: list[dict[str, Any]],
    *,
    themes: list[SubTheme],
    min_q10_sources: int,
) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
    extra: dict[str, Any] = {}
    if query_id == "q7_decision_factors":
        hits = prefer_decision_factors(hits)
        extra["by_factor"] = {
            factor: sum(1 for h in hits if factor in (h.get("decision_factors") or []))
            for factor in (
                "fit",
                "size",
                "styling",
                "price",
                "reviews",
                "occasion",
                "social_validation",
            )
            if any(factor in (h.get("decision_factors") or []) for h in hits)
        }
        return hits, "q7_factors", extra
    if query_id == "q8_intent_vs_bookmark":
        return interleave_intent(hits), "q8_intent", extra
    if query_id == "q9_segments":
        ordered = stratify_segment_category(hits)
        extra["strata"] = dict(Counter(
            f"{h.get('segment_hint')}|{h.get('product_category')}" for h in ordered
        ))
        return ordered, "q9_strata", extra
    if query_id == "q10_unmet_needs":
        qualifying = q10_qualifying_themes(themes, min_sources=min_q10_sources)
        extra["qualifying_sub_themes"] = [t.sub_theme_id for t in qualifying]
        return filter_q10_hits(hits, themes, min_sources=min_q10_sources), "q10_cross_source", extra
    return hits, "metadata_filter", extra


def retrieve_question(
    query: dict[str, Any],
    *,
    index: VectorIndex,
    embedder: Embedder,
    themes: Optional[list[SubTheme]] = None,
) -> dict[str, Any]:
    cfg = retrieval_config()
    top_k = int(cfg.get("top_k_initial") or 30)
    context_n = int(cfg.get("context_top_n") or 10)
    max_frac = float(cfg.get("source_balance_max_fraction") or 0.6)
    min_sim = float(cfg.get("min_similarity") or 0.0)
    gap_flag = str(cfg.get("empty_result_flag") or "data_gap")
    min_q10 = int(cfg.get("q10_min_independent_sources") or 3)

    qid = str(query["id"])
    hits = fetch_candidates(index, embedder, query, top_k=top_k)
    hits = [h for h in hits if float(h.get("similarity") or 0.0) >= min_sim]
    hits, strategy, extra = apply_strategy(qid, hits, themes=themes or [], min_q10_sources=min_q10)
    packed = source_balance(hits, n=context_n, max_fraction=max_frac)
    flag = gap_flag if not packed else None
    return {
        "query_id": qid,
        "question": query.get("question") or "",
        "strategy": strategy,
        "flag": flag,
        "data_gap": (
            f"No indexed evidence for {qid}."
            if flag
            else None
        ),
        "hit_count": len(packed),
        "source_counts": dict(Counter(str(h.get("source")) for h in packed)),
        "hits": packed,
        **extra,
    }
