"""Phase 0 self-check — validates configs, schemas, and taxonomy."""

from __future__ import annotations

from src.config_loader import (
    CLASSIFIER_QUESTION_COUNT,
    QUERY_COUNT,
    canonical_queries,
    classifier_question_ids,
    corpus_cap,
    load_brand,
    load_constraints,
    load_embedding,
    load_processing,
    load_prompts,
    load_retrieval,
    load_sources,
    source_priority,
    theme_ids,
)
from src.models.themes import validate_theme_registry


def main() -> None:
    sources = load_sources()
    constraints = load_constraints()
    queries = canonical_queries()
    prompts = load_prompts()
    brand = load_brand()
    validate_theme_registry()

    assert len(queries) == QUERY_COUNT
    assert len(classifier_question_ids()) == CLASSIFIER_QUESTION_COUNT
    assert queries[-1]["id"] == "q10_unmet_needs"
    assert queries[-1].get("computed") is True

    assert corpus_cap() == 600
    assert constraints.get("min_relevant_after_gate") == 400
    assert constraints.get("pii", {}).get("strip_before_save") is True

    assert source_priority()[:2] == ["play_store", "app_store"]
    assert sources["play_store"]["package_name"] == "com.fsn.nds"
    assert str(sources["app_store"]["app_id"]) == "1439872423"
    assert "myntra" in sources["competitor_blocklist"]

    classifier_prompt = str(prompts.get("classifier_system") or "")
    generate_prompt = str(prompts.get("generate_system") or "")
    assert "do not assign q10" in classifier_prompt.lower()
    assert "never recommend coupons" in generate_prompt.lower()
    assert "q10_unmet_needs" not in (prompts.get("classifier_allowed_questions") or [])

    assert brand["colors"]["pink"] == "#FC2779"
    assert brand["wordmark"] == "NYKAA"
    assert brand["layout"]["no_blinkit_bolt"] is True
    assert brand["frontend"]["framework"] == "react"

    load_processing()
    load_embedding()
    load_retrieval()
    assert load_embedding()["collection_name"] == "nykaa_fashion_wishlist_v1"

    print("Phase 0 OK")
    print(f"  queries={len(queries)} classifier_qs={len(classifier_question_ids())} themes={len(theme_ids())}")
    print(f"  corpus_cap={corpus_cap()} source_priority={source_priority()}")
    print(f"  brand_pink={brand['colors']['pink']}")


if __name__ == "__main__":
    main()
