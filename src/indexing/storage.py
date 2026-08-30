"""Write indexing summaries."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from src.config_loader import ROOT

INDEX_DIR = ROOT / "data" / "index"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_run_date(run_date: date | str | None = None) -> str:
    if run_date is None:
        return date.today().isoformat()
    return run_date.isoformat() if isinstance(run_date, date) else str(run_date)


def save_indexing_summary(
    summary: dict[str, Any],
    *,
    run_date: date | str | None = None,
) -> Path:
    day = get_run_date(run_date)
    out_dir = INDEX_DIR / day
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "indexing_summary.json"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log_dir = INDEX_DIR / "_logs" / day
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "indexing_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return path
