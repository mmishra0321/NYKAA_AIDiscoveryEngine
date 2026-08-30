"""Load cached catalog and pipeline summaries (no Groq in this module)."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.config_loader import ROOT
from src.generation.storage import RESPONSES_DIR
from src.indexing.storage import INDEX_DIR
from src.models.schemas import CatalogReport
from src.processing.storage import PROCESSED_DIR
from src.retrieval.storage import RETRIEVAL_DIR

logger = logging.getLogger(__name__)


def _latest_dir_with(root: Path, filename: str) -> Path | None:
    if not root.exists():
        return None
    dates = []
    for child in root.iterdir():
        if not child.is_dir() or child.name.startswith("_"):
            continue
        if (child / filename).exists():
            dates.append(child)
    if not dates:
        return None
    return sorted(dates, key=lambda p: p.name)[-1]


def _read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def catalog_dir() -> Path:
    found = _latest_dir_with(RESPONSES_DIR, "catalog_summary.json")
    if found is None:
        raise FileNotFoundError("No catalog_summary.json under data/responses/")
    return found


@lru_cache(maxsize=4)
def load_catalog_report(signature: str) -> CatalogReport:
    path = Path(signature)
    return CatalogReport.model_validate_json(path.read_text(encoding="utf-8"))


def get_catalog() -> CatalogReport:
    folder = catalog_dir()
    path = folder / "catalog_summary.json"
    return load_catalog_report(str(path))


def catalog_markdown() -> str:
    path = catalog_dir() / "catalog_summary.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def flatten_themes(report: CatalogReport) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for q in report.questions:
        for theme in q.sub_themes:
            row = theme.model_dump(mode="json")
            row["question"] = q.question
            rows.append(row)
    rows.sort(key=lambda r: (-float(r.get("impact_score") or 0), r.get("sub_theme_id") or ""))
    return rows


def pipeline_summary() -> dict[str, Any]:
    gen_dir = _latest_dir_with(RESPONSES_DIR, "generation_summary.json")
    proc_log = _latest_dir_with(PROCESSED_DIR / "_logs", "processing_summary.json")
    if proc_log is None:
        proc_log = _latest_dir_with(PROCESSED_DIR, "processing_summary.json")
    idx_dir = _latest_dir_with(INDEX_DIR, "indexing_summary.json")
    ret_dir = _latest_dir_with(RETRIEVAL_DIR, "retrieval_summary.json")
    generation = _read_json(gen_dir / "generation_summary.json" if gen_dir else None)
    processing = _read_json(proc_log / "processing_summary.json" if proc_log else None)
    indexing = _read_json(idx_dir / "indexing_summary.json" if idx_dir else None)
    retrieval = _read_json(ret_dir / "retrieval_summary.json" if ret_dir else None)
    steps = [
        {"id": "ingest", "label": "Ingest", "detail": "Play + App public reviews"},
        {
            "id": "relevance",
            "label": "Relevance gate",
            "detail": processing.get("relevance") or {},
        },
        {
            "id": "classify",
            "label": "Classify Q1–Q9",
            "detail": {"classified": processing.get("classified"), "mode": processing.get("mode")},
        },
        {
            "id": "index",
            "label": "Embed + index",
            "detail": {
                "collection": indexing.get("collection"),
                "chunks": indexing.get("chunks_upserted"),
            },
        },
        {
            "id": "retrieve",
            "label": "Retrieve",
            "detail": {"with_hits": retrieval.get("with_hits"), "gaps": retrieval.get("data_gaps")},
        },
        {
            "id": "catalog",
            "label": "Catalog",
            "detail": {
                "coverage": generation.get("coverage_10_of_10"),
                "mode": generation.get("mode"),
            },
        },
    ]
    return {
        "kpi": "wishlist_to_purchase_30d",
        "run_date": generation.get("run_date") or processing.get("run_date"),
        "steps": steps,
        "generation": generation,
        "processing": {
            "relevance": processing.get("relevance"),
            "classified": processing.get("classified"),
            "mode": processing.get("mode"),
        },
        "retrieval": {"hit_counts": retrieval.get("hit_counts"), "data_gaps": retrieval.get("data_gaps")},
        "root": str(ROOT),
    }


def clear_catalog_cache() -> None:
    load_catalog_report.cache_clear()
