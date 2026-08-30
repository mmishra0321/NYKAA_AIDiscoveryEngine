"""Catalog smoke: retrieve all 10 questions; fail if ≥8/10 are empty."""

from __future__ import annotations

from typing import Any

from src.config_loader import canonical_queries
from src.indexing.store import VectorIndex

SMOKE_FAIL_IF_EMPTY_GE = 8


def smoke_catalog(index: VectorIndex, *, limit: int = 5) -> dict[str, Any]:
    hits: dict[str, int] = {}
    empty: list[str] = []
    for query in canonical_queries():
        qid = str(query["id"])
        result = index.get_where({f"has_{qid}": True}, limit=limit)
        ids = result.get("ids") or []
        n = len(ids)
        hits[qid] = n
        if n == 0:
            empty.append(qid)
    empty_count = len(empty)
    return {
        "questions": 10,
        "hits": hits,
        "empty": empty,
        "empty_count": empty_count,
        "passed": empty_count < SMOKE_FAIL_IF_EMPTY_GE,
        "threshold": f"fail if empty_count >= {SMOKE_FAIL_IF_EMPTY_GE}/10",
        "note": "Q10 may be thin early; metadata filter has_{question_id}.",
    }
