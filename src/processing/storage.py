"""Persist Phase 2 processed artifacts."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from src.config_loader import ROOT
from src.models.schemas import ReviewChunk, ReviewDocument, SubTheme

PROCESSED_DIR = ROOT / "data" / "processed"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_run_date(run_date: date | str | None = None) -> str:
    if run_date is None:
        return date.today().isoformat()
    return run_date.isoformat() if isinstance(run_date, date) else str(run_date)


def get_output_dir(run_date: date | str | None = None) -> Path:
    output_dir = PROCESSED_DIR / get_run_date(run_date)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_log_dir(run_date: date | str | None = None) -> Path:
    log_dir = PROCESSED_DIR / "_logs" / get_run_date(run_date)
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _write_jsonl(path: Path, rows: list[Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(row.model_dump_json() + "\n")


def save_processed(
    *,
    documents: list[ReviewDocument],
    chunks: list[ReviewChunk],
    themes: list[SubTheme],
    noise_docs: list[ReviewDocument],
    processing_summary: dict[str, Any],
    noise_summary: dict[str, Any],
    run_date: date | str | None = None,
) -> Path:
    output_dir = get_output_dir(run_date)
    _write_jsonl(output_dir / "documents.jsonl", documents)
    _write_jsonl(output_dir / "chunks.jsonl", chunks)
    _write_jsonl(output_dir / "noise.jsonl", noise_docs)
    (output_dir / "sub_themes.json").write_text(
        json.dumps([t.model_dump(mode="json") for t in themes], indent=2),
        encoding="utf-8",
    )
    (output_dir / "processing_summary.json").write_text(
        json.dumps(processing_summary, indent=2),
        encoding="utf-8",
    )
    (output_dir / "noise_summary.json").write_text(
        json.dumps(noise_summary, indent=2),
        encoding="utf-8",
    )
    log_dir = get_log_dir(run_date)
    (log_dir / "processing_summary.json").write_text(
        json.dumps(processing_summary, indent=2),
        encoding="utf-8",
    )
    (log_dir / "noise_summary.json").write_text(
        json.dumps(noise_summary, indent=2),
        encoding="utf-8",
    )
    return output_dir
