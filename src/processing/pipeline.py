"""Orchestrate relevance → classify → cluster → quantify → chunk."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import date
from typing import Any, Optional

from src.config_loader import classifier_question_ids, canonical_queries
from src.ingestion.constraints import content_hash
from src.models.schemas import (
    IntentLabel,
    ProductCategory,
    Relevance,
    ReviewDocument,
    SegmentHint,
)
from src.processing.cache import HashCache
from src.processing.chunker import chunk_document
from src.processing.classify import classify_document
from src.processing.clean import clean_text, contains_pii
from src.processing.cluster import cluster_and_score
from src.processing.groq_client import GroqClient
from src.processing.loader import load_raw_documents
from src.processing.relevance import label_relevance
from src.processing import storage as store

logger = logging.getLogger(__name__)


def _apply_clean(doc: ReviewDocument) -> ReviewDocument | None:
    cleaned = clean_text(doc.raw_text)
    if not cleaned:
        return None
    if cleaned == doc.raw_text and doc.pii_stripped:
        return doc
    return doc.model_copy(
        update={
            "raw_text": cleaned,
            "content_hash": content_hash(cleaned),
            "pii_stripped": True,
        }
    )


def _apply_classify(doc: ReviewDocument, payload: dict[str, Any]) -> ReviewDocument:
    return doc.model_copy(
        update={
            "research_questions": list(payload.get("research_questions") or []),
            "decision_factors": list(payload.get("decision_factors") or []),
            "segment_hint": SegmentHint(str(payload.get("segment_hint") or "unknown")),
            "product_category": ProductCategory(str(payload.get("product_category") or "unknown")),
            "intent_label": IntentLabel(str(payload.get("intent_label") or "unclear")),
        }
    )


def _coverage(documents: list[ReviewDocument], themes: list[Any]) -> dict[str, Any]:
    ids = classifier_question_ids() + ["q10_unmet_needs"]
    labels = {q["id"]: q["question"] for q in canonical_queries()}
    theme_counts: Counter[str] = Counter(t.question_id for t in themes)
    doc_counts: Counter[str] = Counter()
    for doc in documents:
        for qid in set(doc.research_questions):
            doc_counts[qid] += 1
    coverage: dict[str, Any] = {}
    for qid in ids:
        n_themes = int(theme_counts.get(qid, 0))
        n_docs = int(doc_counts.get(qid, 0))
        gap = None
        if n_themes == 0:
            gap = f"No named sub-theme for {qid} ({labels.get(qid, qid)}) in this run."
        coverage[qid] = {
            "docs": n_docs,
            "sub_themes": n_themes,
            "data_gap": gap,
        }
    return coverage


def run_processing(
    *,
    run_date: date | str | None = None,
    stub: bool = False,
    sources: Optional[list[str]] = None,
    documents: Optional[list[ReviewDocument]] = None,
) -> dict[str, Any]:
    client = GroqClient()
    use_stub = bool(stub or not client.available)
    mode = "stub" if use_stub else "groq"
    if documents is None:
        loaded, day = load_raw_documents(run_date=run_date, sources=sources)
    else:
        loaded = documents
        if run_date is None:
            day = date.today().isoformat()
        else:
            day = run_date.isoformat() if isinstance(run_date, date) else str(run_date)

    cache = HashCache(store.PROCESSED_DIR / "_cache" / "llm_cache.json" if not use_stub else None)

    cleaned_docs: list[ReviewDocument] = []
    for doc in loaded:
        next_doc = _apply_clean(doc)
        if next_doc is None:
            logger.warning("Dropped empty document after clean: %s", doc.id)
            continue
        cleaned_docs.append(next_doc)

    noise_docs: list[ReviewDocument] = []
    signal_docs: list[ReviewDocument] = []
    relevance_counts: Counter[str] = Counter()

    for doc in cleaned_docs:
        cached = cache.get("relevance", doc.content_hash)
        if cached in {r.value for r in Relevance}:
            label = Relevance(cached)
        else:
            label = label_relevance(doc.raw_text, stub=use_stub, client=client)
            cache.set("relevance", doc.content_hash, label.value)
        tagged = doc.model_copy(update={"relevance": label})
        relevance_counts[label.value] += 1
        if label is Relevance.WISHLIST_SIGNAL:
            signal_docs.append(tagged)
        else:
            noise_docs.append(tagged)

    classified: list[ReviewDocument] = []
    for doc in signal_docs:
        cached = cache.get("classify", doc.content_hash)
        if isinstance(cached, dict):
            payload = cached
        else:
            payload = classify_document(doc.raw_text, stub=use_stub, client=client)
            cache.set("classify", doc.content_hash, payload)
        classified.append(_apply_classify(doc, payload))

    clustered, themes, backend = cluster_and_score(classified, stub=use_stub, client=client)

    chunks = []
    for doc in clustered:
        chunks.extend(chunk_document(doc))

    by_doc: dict[str, list[str]] = {}
    for chunk in chunks:
        by_doc.setdefault(chunk.document_id, []).append(chunk.chunk_id)
    for theme in themes:
        mapped: list[str] = []
        for doc_id in theme.chunk_ids:
            mapped.extend(by_doc.get(doc_id, [doc_id]))
        theme.chunk_ids = mapped

    cache.save()

    labeled = sum(1 for d in clustered if any(not q.startswith("q10") for q in d.research_questions))
    majority = labeled >= (len(clustered) / 2) if clustered else False
    coverage = _coverage(clustered, themes)
    pii_hits = sum(1 for d in clustered + noise_docs if contains_pii(d.raw_text))
    q10_n = sum(1 for t in themes if t.question_id == "q10_unmet_needs")

    noise_by_source: dict[str, dict[str, int]] = {}
    for doc in noise_docs:
        bucket = noise_by_source.setdefault(doc.source.value, {"logistics_noise": 0, "other": 0})
        bucket[doc.relevance.value] = bucket.get(doc.relevance.value, 0) + 1

    noise_summary = {
        "logistics_noise": relevance_counts.get("logistics_noise", 0),
        "other": relevance_counts.get("other", 0),
        "wishlist_signal": relevance_counts.get("wishlist_signal", 0),
        "by_source": noise_by_source,
        "note": "logistics_noise and other are excluded from Q1–Q10.",
    }
    processing_summary = {
        "run_date": day,
        "finished_at": store.utc_now_iso(),
        "mode": mode,
        "cluster_backend": backend,
        "input_count": len(loaded),
        "cleaned_count": len(cleaned_docs),
        "relevance": dict(relevance_counts),
        "classified": len(clustered),
        "with_q1_q9": labeled,
        "majority_labeled": majority,
        "chunks": len(chunks),
        "sub_themes": len(themes),
        "q10_themes": q10_n,
        "question_coverage": coverage,
        "pii_hits": pii_hits,
        "limitations": [
            "Classifier never assigns q10; Q10 is computed from slugs in 3+ sources.",
            "Stub mode uses keyword heuristics; Groq is the production classifier.",
            "MiniLM clustering requires sentence-transformers; otherwise n-gram cosine.",
        ],
    }
    output_dir = store.save_processed(
        documents=clustered,
        chunks=chunks,
        themes=themes,
        noise_docs=noise_docs,
        processing_summary=processing_summary,
        noise_summary=noise_summary,
        run_date=day,
    )
    processing_summary["output_dir"] = str(output_dir)
    logger.info(
        "Phase 2 %s: %s signal / %s noise → %s themes (%s Q10) → %s",
        mode,
        len(clustered),
        len(noise_docs),
        len(themes),
        q10_n,
        output_dir,
    )
    return processing_summary
