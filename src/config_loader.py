"""Phase 0 config loader — YAML contracts under config/."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"

QUERY_COUNT = 10
CLASSIFIER_QUESTION_COUNT = 9


def _read_yaml(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config {name} must be a mapping")
    return data


@lru_cache(maxsize=None)
def load_sources() -> dict[str, Any]:
    return _read_yaml("sources.yaml")


@lru_cache(maxsize=None)
def load_constraints() -> dict[str, Any]:
    return _read_yaml("constraints.yaml")


@lru_cache(maxsize=None)
def load_queries() -> dict[str, Any]:
    return _read_yaml("queries.yaml")


@lru_cache(maxsize=None)
def load_themes() -> dict[str, Any]:
    return _read_yaml("themes.yaml")


@lru_cache(maxsize=None)
def load_prompts() -> dict[str, Any]:
    return _read_yaml("prompts.yaml")


@lru_cache(maxsize=None)
def load_brand() -> dict[str, Any]:
    return _read_yaml("brand.yaml")


@lru_cache(maxsize=None)
def load_processing() -> dict[str, Any]:
    return _read_yaml("processing.yaml")


@lru_cache(maxsize=None)
def load_embedding() -> dict[str, Any]:
    return _read_yaml("embedding.yaml")


@lru_cache(maxsize=None)
def load_retrieval() -> dict[str, Any]:
    return _read_yaml("retrieval.yaml")


def clear_config_cache() -> None:
    for fn in (
        load_sources,
        load_constraints,
        load_queries,
        load_themes,
        load_prompts,
        load_brand,
        load_processing,
        load_embedding,
        load_retrieval,
    ):
        fn.cache_clear()


def canonical_queries() -> list[dict[str, Any]]:
    queries = load_queries().get("queries") or []
    if len(queries) != QUERY_COUNT:
        raise ValueError(f"Expected {QUERY_COUNT} canonical queries, found {len(queries)}")
    return queries


def classifier_question_ids() -> list[str]:
    """Q1–Q9 only. Q10 is computed, never assigned per document."""
    return [q["id"] for q in canonical_queries() if not q.get("computed")]


def theme_ids() -> list[str]:
    return [t["id"] for t in (load_themes().get("themes") or [])]


def theme_label_map() -> dict[str, str]:
    return {str(t["id"]): str(t.get("label") or t["id"]) for t in (load_themes().get("themes") or [])}


def source_priority() -> list[str]:
    sources = load_sources()
    priority = sources.get("priority")
    if priority:
        return list(priority)
    return ["play_store", "app_store", "reddit", "forum", "youtube"]


def corpus_cap() -> int:
    constraints = load_constraints()
    return int(constraints.get("max_corpus_total") or 600)
