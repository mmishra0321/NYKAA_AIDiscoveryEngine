"""Load Phase 2 sub-themes for Q10 filters."""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any

from src.indexing.loader import resolve_processed_date
from src.models.schemas import SubTheme
from src.processing import storage as proc_store

logger = logging.getLogger(__name__)


def load_sub_themes(run_date: date | str | None = None) -> tuple[list[SubTheme], str]:
    day = resolve_processed_date(run_date)
    path = proc_store.PROCESSED_DIR / day / "sub_themes.json"
    if not path.exists():
        logger.warning("No sub_themes.json at %s", path)
        return [], day
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return [], day
    themes: list[SubTheme] = []
    for row in raw:
        try:
            themes.append(SubTheme.model_validate(row))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skip sub-theme: %s", exc)
    return themes, day


def latest_index_embedder(run_date: date | str | None = None) -> str | None:
    from src.indexing import storage as idx_store

    day = None
    if run_date is not None:
        day = run_date.isoformat() if isinstance(run_date, date) else str(run_date)
    root = idx_store.INDEX_DIR
    if not root.exists():
        return None
    if day:
        path = root / day / "indexing_summary.json"
    else:
        candidates = sorted(
            p for p in root.glob("*/indexing_summary.json") if "/_logs/" not in str(p)
        )
        path = candidates[-1] if candidates else None
    if path is None or not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    embedder = payload.get("embedder")
    return str(embedder) if embedder else None
