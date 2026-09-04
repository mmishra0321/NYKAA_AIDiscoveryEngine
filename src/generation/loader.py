"""Load Phase 4 packs, Phase 2 themes, and corpus counts."""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any

from src.indexing.loader import resolve_processed_date
from src.models.schemas import SubTheme
from src.processing import storage as proc_store
from src.retrieval import storage as ret_store
from src.retrieval.loader import load_sub_themes

logger = logging.getLogger(__name__)


def resolve_pack_date(run_date: date | str | None = None) -> str:
    if run_date is not None:
        return run_date.isoformat() if isinstance(run_date, date) else str(run_date)
    root = ret_store.RETRIEVAL_DIR
    dates: set[str] = set()
    if root.exists():
        for day_dir in root.iterdir():
            if not day_dir.is_dir() or day_dir.name.startswith("_"):
                continue
            if (day_dir / "retrieval_summary.json").exists() or (day_dir / "q1_wishlist_motive.json").exists():
                dates.add(day_dir.name)
    if dates:
        return sorted(dates)[-1]
    return resolve_processed_date(None)


def load_packs(run_date: date | str | None = None) -> tuple[list[dict[str, Any]], str]:
    day = resolve_pack_date(run_date)
    folder = ret_store.RETRIEVAL_DIR / day
    packs: list[dict[str, Any]] = []
    if not folder.exists():
        raise FileNotFoundError(f"No retrieval packs at {folder}")
    for path in sorted(folder.glob("q*.json")):
        try:
            packs.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError as exc:
            logger.warning("Skip pack %s: %s", path, exc)
    return packs, day


def load_processing_corpus(run_date: date | str | None = None) -> dict[str, Any]:
    try:
        day = resolve_processed_date(run_date)
    except FileNotFoundError:
        return {"relevant": 0, "noise": 0, "sources": {}, "question_coverage": {}}
    path = proc_store.PROCESSED_DIR / day / "processing_summary.json"
    if not path.exists():
        path = proc_store.PROCESSED_DIR / "_logs" / day / "processing_summary.json"
    if not path.exists():
        return {"relevant": 0, "noise": 0, "sources": {}, "question_coverage": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"relevant": 0, "noise": 0, "sources": {}, "question_coverage": {}}
    rel = payload.get("relevance") or {}
    relevant = int(rel.get("wishlist_signal") or payload.get("classified") or 0)
    noise = int(rel.get("logistics_noise") or 0) + int(rel.get("other") or 0)
    return {
        "relevant": relevant,
        "noise": noise,
        "sources": {},
        "question_coverage": payload.get("question_coverage") or {},
        "classified": payload.get("classified"),
        "input_count": payload.get("input_count"),
    }


def load_generation_inputs(
    run_date: date | str | None = None,
) -> tuple[list[dict[str, Any]], list[SubTheme], dict[str, Any], str]:
    packs, day = load_packs(run_date)
    try:
        themes, _ = load_sub_themes(day)
    except FileNotFoundError:
        themes = []
    corpus = load_processing_corpus(day)
    sources: dict[str, int] = {}
    for pack in packs:
        for src, n in (pack.get("source_counts") or {}).items():
            sources[str(src)] = sources.get(str(src), 0) + int(n)
    corpus["sources"] = sources
    return packs, themes, corpus, day
