"""Orchestrate multi-source Nykaa Fashion ingestion."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Optional

from src.config_loader import load_sources, source_priority
from src.ingestion.adapters import ADAPTERS
from src.ingestion.constraints import ScrapeConstraints, content_hash
from src.ingestion.storage import save_documents, save_ingestion_log
from src.ingestion.types import IngestionResult, utc_now_iso
from src.models.schemas import ReviewDocument

logger = logging.getLogger(__name__)


def _source_config(sources: dict[str, Any], name: str) -> dict[str, Any]:
    cfg = dict(sources.get(name) or {})
    cfg.setdefault("enabled", True)
    return cfg


def run_ingestion(
    *,
    sources: Optional[list[str]] = None,
    run_date: Optional[date] = None,
) -> dict[str, Any]:
    cfg = load_sources()
    constraints = ScrapeConstraints.load()
    selected = sources or list(source_priority())
    results: list[IngestionResult] = []
    by_source: dict[str, list[ReviewDocument]] = {}
    seen_hashes: set[str] = set()

    for name in selected:
        source_cfg = _source_config(cfg, name)
        result = IngestionResult(source=name, finished_at=utc_now_iso())

        if not source_cfg.get("enabled", True):
            result.metadata = {"skipped": "disabled"}
            results.append(result)
            continue

        if name not in ADAPTERS:
            result.metadata = {"skipped": "no_live_adapter"}
            results.append(result)
            continue

        scraper = ADAPTERS[name](config=source_cfg, run_date=run_date, constraints=constraints)
        try:
            documents, fetched, skipped, errors, filter_summary = scraper.fetch()
            result.records_fetched = fetched
            result.records_skipped = skipped
            result.errors = errors
            result.metadata = {"filter_stats": filter_summary}
        except Exception as exc:  # noqa: BLE001
            result.errors = [str(exc)]
            documents = []
            logger.exception("%s failed", name)

        unique: list[ReviewDocument] = []
        for doc in documents:
            h = doc.content_hash or content_hash(doc.raw_text)
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            unique.append(doc)

        remaining = constraints.max_corpus_total - sum(len(v) for v in by_source.values())
        cap = min(constraints.cap_for_source(name), max(remaining, 0))
        kept = unique[:cap]
        by_source[name] = kept
        result.records_saved = len(kept)
        if kept:
            path = save_documents(name, kept, run_date)
            result.output_path = str(path)
        result.finished_at = utc_now_iso()
        results.append(result)

    corpus_total = sum(len(v) for v in by_source.values())
    log_path = save_ingestion_log(
        results,
        run_date=run_date,
        corpus_target=constraints.min_corpus_total,
        corpus_total=corpus_total,
    )
    summary = {
        "run_date": (run_date or date.today()).isoformat(),
        "corpus_total": corpus_total,
        "corpus_cap": constraints.max_corpus_total,
        "source_counts": {k: len(v) for k, v in by_source.items() if v},
        "log_path": str(log_path),
        "sources": [r.to_dict() for r in results],
        "limitations": [
            "forum HTML scrape deferred",
            "youtube requires YOUTUBE_API_KEY",
            "twitter_x / quora deferred",
        ],
    }
    logger.info("Ingestion complete: %s docs → %s", corpus_total, log_path)
    return summary
