"""Embed processed chunks and upsert into Chroma."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any, Optional

from src.config_loader import load_embedding
from src.indexing.embedder import Embedder
from src.indexing.loader import load_processed
from src.indexing.metadata import chunk_metadata
from src.indexing.smoke import smoke_catalog
from src.indexing.store import VectorIndex
from src.indexing import storage as index_store
from src.models.schemas import Relevance, ReviewChunk, ReviewDocument
from src.processing.clean import contains_pii

logger = logging.getLogger(__name__)


def run_indexing(
    *,
    run_date: date | str | None = None,
    stub: bool = False,
    chunks: Optional[list[ReviewChunk]] = None,
    documents: Optional[list[ReviewDocument]] = None,
    persist_directory: Optional[Path] = None,
    skip_smoke: bool = False,
) -> dict[str, Any]:
    cfg = load_embedding()
    if chunks is None:
        loaded_chunks, loaded_docs, day = load_processed(run_date=run_date)
    else:
        loaded_chunks = chunks
        loaded_docs = documents or []
        if run_date is None:
            day = date.today().isoformat()
        else:
            day = run_date.isoformat() if isinstance(run_date, date) else str(run_date)

    docs_by_id = {d.id: d for d in loaded_docs}
    keep: list[tuple[ReviewChunk, ReviewDocument | None]] = []
    skipped_noise = 0
    for chunk in loaded_chunks:
        if not (chunk.text or "").strip():
            continue
        parent = docs_by_id.get(chunk.document_id)
        relevance = parent.relevance if parent is not None else Relevance.WISHLIST_SIGNAL
        if relevance is not Relevance.WISHLIST_SIGNAL:
            skipped_noise += 1
            continue
        keep.append((chunk, parent))

    embedder = Embedder(stub=stub)
    texts = [c.text for c, _ in keep]
    vectors = embedder.encode(texts)
    metadatas = [chunk_metadata(c, doc) for c, doc in keep]
    ids = [c.chunk_id for c, _ in keep]

    index = VectorIndex(persist_directory=persist_directory)
    upserted = index.upsert(
        ids=ids,
        embeddings=vectors,
        documents=texts,
        metadatas=metadatas,
        batch_size=int(cfg.get("batch_size") or 128),
    )

    smoke = {"skipped": True, "passed": True, "empty_count": None, "hits": {}}
    if not skip_smoke:
        smoke = smoke_catalog(index)

    pii_hits = sum(1 for c, _ in keep if contains_pii(c.text))
    summary = {
        "run_date": day,
        "finished_at": index_store.utc_now_iso(),
        "collection": index.name,
        "persist_directory": str(index.persist_directory),
        "embedding_model": embedder.model_name,
        "embedder": embedder.backend,
        "embedding_dim": embedder.dim,
        "similarity": str(cfg.get("similarity") or "cosine"),
        "chunks_in": len(loaded_chunks),
        "chunks_upserted": upserted,
        "skipped_noise": skipped_noise,
        "collection_count": index.count(),
        "smoke": smoke,
        "pii_hits": pii_hits,
        "limitations": [
            "Embeddings are MiniLM when sentence-transformers is installed; --stub uses hash vectors.",
            "Chroma metadata stores question flags as has_{qid} booleans (lists are not supported).",
            "Q10 may be empty until 3+ independent sources exist in Phase 2.",
        ],
    }
    path = index_store.save_indexing_summary(summary, run_date=day)
    summary["summary_path"] = str(path)
    logger.info(
        "Phase 3 %s: upserted %s → %s (smoke passed=%s empty=%s)",
        embedder.backend,
        upserted,
        index.name,
        smoke.get("passed"),
        smoke.get("empty_count"),
    )
    return summary
