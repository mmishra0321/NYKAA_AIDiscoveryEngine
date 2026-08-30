"""Load Phase 2 processed chunks for indexing."""

from __future__ import annotations

import logging
from datetime import date

from src.models.schemas import ReviewChunk, ReviewDocument
from src.processing import storage as proc_store

logger = logging.getLogger(__name__)


def resolve_processed_date(run_date: date | str | None = None) -> str:
    if run_date is not None:
        return run_date.isoformat() if isinstance(run_date, date) else str(run_date)

    dates: set[str] = set()
    root = proc_store.PROCESSED_DIR
    if not root.exists():
        raise FileNotFoundError(f"No processed data directory at {root}")
    for day_dir in root.iterdir():
        if not day_dir.is_dir() or day_dir.name.startswith("_"):
            continue
        if (day_dir / "chunks.jsonl").exists():
            dates.add(day_dir.name)
    if not dates:
        raise FileNotFoundError(f"No chunks.jsonl found under {root}")
    return sorted(dates)[-1]


def _read_jsonl(path, model):
    rows = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(model.model_validate_json(line))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skip %s:%s — %s", path, line_no, exc)
    return rows


def load_processed(
    *,
    run_date: date | str | None = None,
) -> tuple[list[ReviewChunk], list[ReviewDocument], str]:
    day = resolve_processed_date(run_date)
    folder = proc_store.PROCESSED_DIR / day
    chunks = _read_jsonl(folder / "chunks.jsonl", ReviewChunk)
    documents = _read_jsonl(folder / "documents.jsonl", ReviewDocument)
    logger.info("Loaded %s chunks / %s documents for %s", len(chunks), len(documents), day)
    return chunks, documents, day
