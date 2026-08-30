from datetime import datetime, timezone

import pytest

from src.config_loader import (
    CLASSIFIER_QUESTION_COUNT,
    QUERY_COUNT,
    canonical_queries,
    classifier_question_ids,
    clear_config_cache,
    corpus_cap,
    load_brand,
    load_constraints,
    load_embedding,
    load_prompts,
    load_queries,
    load_sources,
    source_priority,
    theme_ids,
)
from src.models.schemas import (
    CatalogReport,
    ProductCategory,
    Relevance,
    ReviewChunk,
    ReviewDocument,
    SourceKind,
    SourceType,
    SubTheme,
)
from src.models.themes import ThemeId, validate_theme_registry


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_config_cache()
    yield
    clear_config_cache()


def test_sources_priority_and_ids():
    sources = load_sources()
    assert sources["play_store"]["package_name"] == "com.fsn.nds"
    assert str(sources["app_store"]["app_id"]) == "1439872423"
    assert sources["nykaa_beauty_xref"]["package_name"] == "com.fsn.nykaa"
    assert source_priority()[:2] == ["play_store", "app_store"]
    assert "myntra" in sources["competitor_blocklist"]
    assert "ajio" in sources["competitor_blocklist"]


def test_constraints_corpus_and_pii():
    constraints = load_constraints()
    assert constraints["max_corpus_total"] == 600
    assert constraints["min_relevant_after_gate"] == 400
    assert corpus_cap() == 600
    assert constraints["pii"]["strip_before_save"] is True
    assert "wishlist" in constraints["keywords_any"]


def test_query_catalog_has_ten_and_q10_computed():
    queries = canonical_queries()
    assert len(queries) == QUERY_COUNT
    ids = [q["id"] for q in queries]
    assert ids[0] == "q1_wishlist_motive"
    assert ids[-1] == "q10_unmet_needs"
    assert len(ids) == len(set(ids))
    for q in queries:
        assert q["question"]
        assert len(q.get("paraphrases") or []) >= 1
        assert len(q.get("theme_filters") or []) >= 1
    assert queries[-1]["computed"] is True
    assert queries[-1].get("min_independent_sources") == 3
    assert all(not q.get("computed") for q in queries[:-1])
    assert len(classifier_question_ids()) == CLASSIFIER_QUESTION_COUNT
    assert "q10_unmet_needs" not in classifier_question_ids()


def test_theme_taxonomy_matches_enum():
    validate_theme_registry()
    assert set(theme_ids()) == {t.value for t in ThemeId}
    assert "logistics_noise" in theme_ids()


def test_prompts_forbid_q10_assignment_and_discounts():
    prompts = load_prompts()
    allowed = prompts["classifier_allowed_questions"]
    assert "q10_unmet_needs" not in allowed
    assert len(allowed) == 9
    classifier = prompts["classifier_system"].lower()
    generate = prompts["generate_system"].lower()
    assert "do not assign q10" in classifier
    assert "never recommend coupons" in generate
    assert "paraphrased" in generate


def test_brand_tokens_are_nykaa_not_blinkit():
    brand = load_brand()
    assert brand["colors"]["pink"] == "#FC2779"
    assert brand["wordmark"] == "NYKAA"
    assert brand["layout"]["no_blinkit_bolt"] is True
    assert brand["layout"]["no_dark_theme"] is True
    assert brand["layout"]["no_cards_in_hero"] is True
    assert brand["frontend"]["framework"] == "react"
    assert brand["frontend"]["bundler"] == "vite"


def test_embedding_collection_name():
    emb = load_embedding()
    assert emb["model_name"].endswith("all-MiniLM-L6-v2")
    assert emb["collection_name"] == "nykaa_fashion_wishlist_v1"
    assert emb["embedding_dim"] == 384


def test_review_document_schema_roundtrip():
    doc = ReviewDocument(
        id="doc-1",
        source=SourceType.PLAY_STORE,
        source_type=SourceKind.APP_REVIEW,
        date=datetime.now(timezone.utc),
        product_category=ProductCategory.ETHNIC,
        raw_text="  Saved a kurta to style later. Not buying today.  ",
        url="https://play.google.com/store/apps/details?id=com.fsn.nds",
        rating=4,
        relevance=Relevance.WISHLIST_SIGNAL,
        research_questions=["q1_wishlist_motive"],
        content_hash="abc",
        pii_stripped=True,
    )
    assert doc.raw_text.startswith("Saved a kurta")
    again = ReviewDocument.model_validate(doc.model_dump(mode="json"))
    assert again.research_questions == ["q1_wishlist_motive"]


def test_review_chunk_and_sub_theme_and_catalog():
    now = datetime.now(timezone.utc)
    chunk = ReviewChunk(
        chunk_id="c1",
        document_id="doc-1",
        text="Size chart feels optimistic so the save never converts.",
        chunk_index=0,
        source=SourceType.REDDIT,
        research_questions=["q3_uncertainties"],
        date=now,
        content_hash="def",
    )
    theme = SubTheme(
        sub_theme_id="q3_uncertainties_sizing_runs_small",
        question_id="q3_uncertainties",
        name="Sizing runs small",
        share_of_bucket=0.31,
        source_diversity=4,
        paraphrased_examples=["Users like a kurta, then hesitate because reviews say the chart runs small."],
        chunk_ids=[chunk.chunk_id],
    )
    report = CatalogReport(
        generated_at=now.isoformat(),
        questions=[],
    )
    assert chunk.source == SourceType.REDDIT
    assert theme.sub_theme_id.endswith("sizing_runs_small")
    assert report.kpi == "wishlist_to_purchase_30d"


def test_queries_yaml_ids_unique():
    ids = [q["id"] for q in load_queries()["queries"]]
    assert len(ids) == len(set(ids))
    assert len(ids) == 10
