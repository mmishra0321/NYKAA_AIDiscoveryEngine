"""Persist raw documents and ingestion logs."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from src.config_loader import ROOT
from src.ingestion.types import IngestionResult, utc_now_iso
from src.models.schemas import ReviewDocument

RAW_DATA_DIR = ROOT / "data" / "raw"


def get_run_date(run_date: date | None = None) -> str:
    return (run_date or date.today()).isoformat()


def get_output_dir(source: str, run_date: date | None = None) -> Path:
    output_dir = RAW_DATA_DIR / source / get_run_date(run_date)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def save_documents(
    source: str,
    documents: list[ReviewDocument],
    run_date: date | None = None,
) -> Path:
    output_dir = get_output_dir(source, run_date)
    output_path = output_dir / "documents.jsonl"
    with output_path.open("w", encoding="utf-8") as handle:
        for doc in documents:
            handle.write(doc.model_dump_json() + "\n")
    summary = {
        "source": source,
        "count": len(documents),
        "run_date": get_run_date(run_date),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return output_path


def save_ingestion_log(
    results: list[IngestionResult],
    run_date: date | None = None,
    corpus_target: int | None = None,
    corpus_total: int | None = None,
) -> Path:
    log_dir = RAW_DATA_DIR / "_logs" / get_run_date(run_date)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "ingestion_summary.json"
    payload = {
        "run_date": get_run_date(run_date),
        "finished_at": utc_now_iso(),
        "corpus_target": corpus_target,
        "corpus_total": corpus_total,
        "corpus_target_met": (
            corpus_total >= corpus_target
            if corpus_target is not None and corpus_total is not None
            else None
        ),
        "sources": [result.to_dict() for result in results],
        "totals": {
            "records_fetched": sum(r.records_fetched for r in results),
            "records_saved": sum(r.records_saved for r in results),
            "records_skipped": sum(r.records_skipped for r in results),
            "errors": sum(len(r.errors) for r in results),
        },
        "limitations": [
            "forum HTML scrape deferred (ToS / robots.txt)",
            "youtube skipped unless YOUTUBE_API_KEY is set and adapter enabled",
            "twitter_x / quora / login walls deferred",
            "keyword prefilter is recall-only; LLM relevance is Phase 2",
        ],
    }
    log_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return log_path
