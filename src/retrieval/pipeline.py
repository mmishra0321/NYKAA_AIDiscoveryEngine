"""Run catalog retrieval for all 10 questions."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any, Optional

from src.config_loader import canonical_queries
from src.indexing.embedder import Embedder
from src.indexing.loader import resolve_processed_date
from src.indexing.store import VectorIndex
from src.models.schemas import SubTheme
from src.retrieval.loader import latest_index_embedder, load_sub_themes
from src.retrieval.retrieve import retrieve_question
from src.retrieval import storage as store

logger = logging.getLogger(__name__)


def _resolve_stub(stub: bool, run_date: date | str | None) -> bool:
    if stub:
        return True
    return latest_index_embedder(run_date) == "stub"


def run_catalog_retrieval(
    *,
    run_date: date | str | None = None,
    stub: bool = False,
    persist_directory: Optional[Path] = None,
    query_ids: Optional[list[str]] = None,
    themes: Optional[list[SubTheme]] = None,
    index: Optional[VectorIndex] = None,
) -> dict[str, Any]:
    use_stub = _resolve_stub(stub, run_date)
    embedder = Embedder(stub=use_stub)
    vec_index = index or VectorIndex(persist_directory=persist_directory)
    if themes is None:
        try:
            themes, _theme_day = load_sub_themes(run_date)
        except FileNotFoundError:
            themes = []

    if run_date is not None:
        day = run_date.isoformat() if isinstance(run_date, date) else str(run_date)
    else:
        try:
            day = resolve_processed_date(None)
        except FileNotFoundError:
            day = date.today().isoformat()

    queries = canonical_queries()
    if query_ids:
        wanted = set(query_ids)
        queries = [q for q in queries if q["id"] in wanted]

    packs = [
        retrieve_question(q, index=vec_index, embedder=embedder, themes=themes)
        for q in queries
    ]
    for pack in packs:
        pack["retrieved_at"] = store.utc_now_iso()

    gaps = [p["query_id"] for p in packs if p.get("flag")]
    summary = {
        "run_date": day,
        "finished_at": store.utc_now_iso(),
        "embedder": embedder.backend,
        "collection": vec_index.name,
        "questions": len(packs),
        "with_hits": sum(1 for p in packs if p["hit_count"] > 0),
        "data_gaps": gaps,
        "hit_counts": {p["query_id"]: p["hit_count"] for p in packs},
        "limitations": [
            "Source mix is capped at ~60% per source when alternatives exist.",
            "Q10 requires sub-themes with source_diversity >= 3.",
            "Empty packs are flagged data_gap for Phase 5.",
        ],
    }
    out_dir = store.save_packs(packs, summary, run_date=day)
    summary["output_dir"] = str(out_dir)
    logger.info(
        "Phase 4 %s: %s/%s questions have hits (%s gaps) → %s",
        embedder.backend,
        summary["with_hits"],
        len(packs),
        len(gaps),
        out_dir,
    )
    return summary
