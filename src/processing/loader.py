"""Load Phase 1 raw JSONL."""

from __future__ import annotations

import logging
from datetime import date

from src.config_loader import ROOT, source_priority
from src.models.schemas import ReviewDocument

logger = logging.getLogger(__name__)

RAW_DATA_DIR = ROOT / "data" / "raw"


def resolve_raw_date(run_date: date | str | None = None) -> str:
    if run_date is not None:
        return run_date.isoformat() if isinstance(run_date, date) else str(run_date)

    dates: set[str] = set()
    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError(f"No raw data directory at {RAW_DATA_DIR}")
    for source_dir in RAW_DATA_DIR.iterdir():
        if not source_dir.is_dir() or source_dir.name.startswith("_"):
            continue
        for day_dir in source_dir.iterdir():
            if day_dir.is_dir() and (day_dir / "documents.jsonl").exists():
                dates.add(day_dir.name)
    if not dates:
        raise FileNotFoundError(f"No documents.jsonl found under {RAW_DATA_DIR}")
    return sorted(dates)[-1]


def load_raw_documents(
    *,
    run_date: date | str | None = None,
    sources: list[str] | None = None,
) -> tuple[list[ReviewDocument], str]:
    day = resolve_raw_date(run_date)
    selected = sources or source_priority()
    documents: list[ReviewDocument] = []
    for source in selected:
        path = RAW_DATA_DIR / source / day / "documents.jsonl"
        if not path.exists():
            logger.warning("Missing raw file skipped: %s", path)
            continue
        with path.open(encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    documents.append(ReviewDocument.model_validate_json(line))
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Skip %s:%s — %s", path, line_no, exc)
    logger.info("Loaded %s raw documents for %s", len(documents), day)
    return documents, day
