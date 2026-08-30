"""Word-window chunker."""

from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any

from src.config_loader import load_processing
from src.models.schemas import ReviewChunk, ReviewDocument

WORD_PATTERN = re.compile(r"\S+")


def _words(text: str) -> list[str]:
    return WORD_PATTERN.findall(text or "")


def chunk_hash(text: str) -> str:
    return hashlib.sha256(" ".join((text or "").lower().split()).encode()).hexdigest()


def stable_chunk_id(document_id: str, chunk_index: int, text_hash: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document_id}:{chunk_index}:{text_hash}"))


def split_into_word_windows(
    text: str,
    *,
    target_words: int = 350,
    overlap_words: int = 50,
    short_doc_word_threshold: int = 100,
) -> list[str]:
    tokens = _words(text)
    if not tokens:
        return []
    if len(tokens) <= short_doc_word_threshold or len(tokens) <= target_words:
        return [" ".join(tokens)]
    step = max(1, target_words - overlap_words)
    windows: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(len(tokens), start + target_words)
        windows.append(" ".join(tokens[start:end]))
        if end >= len(tokens):
            break
        start += step
    return windows


def chunk_document(doc: ReviewDocument, *, config: dict[str, Any] | None = None) -> list[ReviewChunk]:
    cfg = config if config is not None else (load_processing().get("chunking") or {})
    windows = split_into_word_windows(
        doc.raw_text,
        target_words=int(cfg.get("target_words", 350)),
        overlap_words=int(cfg.get("overlap_words", 50)),
        short_doc_word_threshold=int(cfg.get("short_doc_word_threshold", 100)),
    )
    chunks: list[ReviewChunk] = []
    for idx, window in enumerate(windows):
        h = chunk_hash(window)
        chunks.append(
            ReviewChunk(
                chunk_id=stable_chunk_id(doc.id, idx, h),
                document_id=doc.id,
                text=window,
                chunk_index=idx,
                source=doc.source,
                research_questions=list(doc.research_questions),
                sub_theme_ids=list(doc.sub_theme_ids),
                segment_hint=doc.segment_hint,
                product_category=doc.product_category,
                url=doc.url,
                date=doc.date,
                content_hash=h,
            )
        )
    return chunks
