"""Load cached catalog and pipeline summaries (no Groq in this module)."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
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

RAW_LOGS_DIR = ROOT / "data" / "raw" / "_logs"
DEFAULT_GITHUB_REPO = "mmishra0321/NYKAA_AIDiscoveryEngine"
WORKFLOW_FILE = "ingest.yml"


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


def _latest_ingestion_log() -> tuple[Path | None, dict[str, Any]]:
    folder = _latest_dir_with(RAW_LOGS_DIR, "ingestion_summary.json")
    if folder is None:
        return None, {}
    return folder, _read_json(folder / "ingestion_summary.json")


def _committed_workflow_meta(folder: Path | None) -> dict[str, Any]:
    if folder is None:
        return {}
    return _read_json(folder / "workflow_run.json")


def _fetch_github_workflow_run(repo: str) -> dict[str, Any] | None:
    url = (
        f"https://api.github.com/repos/{repo}/actions/workflows/{WORKFLOW_FILE}/runs"
        f"?per_page=1"
    )
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "nykaa-fashion-wishlist-api",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        logger.info("GitHub Actions lookup skipped: %s", exc)
        return None
    runs = payload.get("workflow_runs") or []
    if not runs:
        return None
    run = runs[0]
    return {
        "id": run.get("id"),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "event": run.get("event"),
        "display_title": run.get("display_title") or run.get("name"),
        "created_at": run.get("created_at"),
        "updated_at": run.get("updated_at"),
        "run_started_at": run.get("run_started_at"),
        "html_url": run.get("html_url"),
        "head_branch": run.get("head_branch"),
        "actor": (run.get("actor") or {}).get("login"),
    }


def scrape_status() -> dict[str, Any]:
    """Last local scrape log + latest GitHub Actions run for the ingest workflow."""
    folder, ingestion = _latest_ingestion_log()
    totals = ingestion.get("totals") or {}
    sources = []
    for row in ingestion.get("sources") or []:
        if not isinstance(row, dict):
            continue
        sources.append(
            {
                "source": row.get("source"),
                "records_fetched": row.get("records_fetched"),
                "records_saved": row.get("records_saved"),
                "errors": len(row.get("errors") or []),
            }
        )
    committed = _committed_workflow_meta(folder)
    repo = (os.getenv("GITHUB_REPO") or DEFAULT_GITHUB_REPO).strip()
    live = _fetch_github_workflow_run(repo) if repo else None
    workflow = live or committed or None
    actions_url = f"https://github.com/{repo}/actions/workflows/{WORKFLOW_FILE}"
    return {
        "schedule": "Every ~10 days (1st, 11th, 21st, 31st · 06:00 UTC)",
        "workflow_name": "Ingest Classify Index Nykaa Fashion",
        "actions_url": actions_url,
        "repo": repo,
        "last_scrape": {
            "run_date": ingestion.get("run_date"),
            "finished_at": ingestion.get("finished_at"),
            "corpus_total": ingestion.get("corpus_total"),
            "corpus_target": ingestion.get("corpus_target"),
            "corpus_target_met": ingestion.get("corpus_target_met"),
            "records_fetched": totals.get("records_fetched"),
            "records_saved": totals.get("records_saved"),
            "records_skipped": totals.get("records_skipped"),
            "errors": totals.get("errors"),
            "sources": sources,
            "log_path": str(folder / "ingestion_summary.json") if folder else None,
        }
        if ingestion
        else None,
        "last_github_action": workflow,
        "github_action_source": "live" if live else ("committed" if committed else None),
    }


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
    ingest_folder, ingestion = _latest_ingestion_log()
    ingest_totals = ingestion.get("totals") or {}
    steps = [
        {
            "id": "ingest",
            "label": "Ingest",
            "detail": {
                "run_date": ingestion.get("run_date"),
                "finished_at": ingestion.get("finished_at"),
                "records_saved": ingest_totals.get("records_saved"),
                "records_fetched": ingest_totals.get("records_fetched"),
                "sources": len(ingestion.get("sources") or []),
            }
            if ingestion
            else "Play + App public reviews",
        },
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
        "run_date": generation.get("run_date") or processing.get("run_date") or ingestion.get("run_date"),
        "steps": steps,
        "generation": generation,
        "processing": {
            "relevance": processing.get("relevance"),
            "classified": processing.get("classified"),
            "mode": processing.get("mode"),
        },
        "retrieval": {"hit_counts": retrieval.get("hit_counts"), "data_gaps": retrieval.get("data_gaps")},
        "scrape": scrape_status(),
        "root": str(ROOT),
        "ingest_log_dir": str(ingest_folder) if ingest_folder else None,
    }


def clear_catalog_cache() -> None:
    load_catalog_report.cache_clear()
