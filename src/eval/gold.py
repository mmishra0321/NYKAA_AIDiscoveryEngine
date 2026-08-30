from __future__ import annotations

import json
from typing import Any

from src.config_loader import ROOT, canonical_queries, classifier_question_ids

GOLD_DIR = ROOT / "data" / "eval" / "gold"


def _load_json(name: str) -> dict[str, Any]:
    path = GOLD_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing gold file: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{name} must be an object")
    return data


def load_relevance_gold() -> list[dict[str, Any]]:
    items = list(_load_json("relevance.json").get("items") or [])
    if len(items) < 20:
        raise ValueError(f"Need ≥20 relevance labels, found {len(items)}")
    return items


def load_classify_gold() -> list[dict[str, Any]]:
    allowed = set(classifier_question_ids())
    items = []
    for row in _load_json("classify.json").get("items") or []:
        qs = [q for q in (row.get("research_questions") or []) if q in allowed]
        if "q10_unmet_needs" in (row.get("research_questions") or []):
            raise ValueError(f"{row.get('id')} assigns q10 — forbidden on gold classify rows")
        items.append({**row, "research_questions": qs})
    if len(items) < 40:
        raise ValueError(f"Need ~40 classify rows, found {len(items)}")
    return items


def load_answer_review() -> list[dict[str, Any]]:
    reviews = list(_load_json("answer_review.json").get("reviews") or [])
    if len(reviews) != 10:
        raise ValueError(f"Need 10 answer reviews, found {len(reviews)}")
    return reviews


def load_paraphrases() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for query in canonical_queries():
        paras = query.get("paraphrases") or []
        if len(paras) < 2:
            raise ValueError(f"{query['id']} needs 2 paraphrases in queries.yaml")
        for text in paras[:2]:
            rows.append({"query_id": str(query["id"]), "question": str(query["question"]), "paraphrase": str(text)})
    if len(rows) != 20:
        raise ValueError(f"Need 10×2 paraphrases, found {len(rows)}")
    return rows
