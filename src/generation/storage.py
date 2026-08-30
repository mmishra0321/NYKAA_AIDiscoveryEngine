"""Write catalog JSON + Markdown."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from src.config_loader import ROOT
from src.models.schemas import CatalogReport

RESPONSES_DIR = ROOT / "data" / "responses"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_run_date(run_date: date | str | None = None) -> str:
    if run_date is None:
        return date.today().isoformat()
    return run_date.isoformat() if isinstance(run_date, date) else str(run_date)


def save_catalog(
    report: CatalogReport,
    markdown: str,
    summary: dict[str, Any],
    *,
    run_date: date | str | None = None,
) -> Path:
    day = get_run_date(run_date)
    out_dir = RESPONSES_DIR / day
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "catalog_summary.json").write_text(
        json.dumps(report.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    (out_dir / "catalog_summary.md").write_text(markdown, encoding="utf-8")
    for q in report.questions:
        (out_dir / f"{q.id}.json").write_text(
            json.dumps(q.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )
    (out_dir / "generation_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    log_dir = RESPONSES_DIR / "_logs" / day
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "generation_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    (log_dir / "catalog_summary.md").write_text(markdown, encoding="utf-8")
    return out_dir
