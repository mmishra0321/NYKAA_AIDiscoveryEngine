from datetime import datetime, timedelta, timezone

from src.ingestion.constraints import (
    ScrapeConstraints,
    apply_document_constraints,
    content_hash,
    is_competitor_primary,
    is_english,
    looks_like_spam,
    strip_pii,
)
from src.ingestion.document_factory import make_document
from src.models.schemas import Platform, SourceType


def _doc(text: str, days_ago: int = 10, rating: int = 3):
    return make_document(
        source=SourceType.PLAY_STORE,
        raw_text=text,
        date=datetime.now(timezone.utc) - timedelta(days=days_ago),
        rating=rating,
        platform=Platform.ANDROID,
        origin="test",
    )


def test_english_and_spam_gates():
    assert is_english("I saved a kurta on my Nykaa Fashion wishlist to style later.")
    assert not is_english("यह केवल हिंदी में है और काफी लंबा टेक्स्ट होना चाहिए")
    assert looks_like_spam("BUY NOW CLICK HERE FREE FOLLOWERS")
    assert not looks_like_spam("Size chart on Nykaa Fashion feels small for ethnic wear.")


def test_pii_strip():
    cleaned, hit = strip_pii("Email me at user@example.com or +919876543210 about order id NYK123456")
    assert hit
    assert "example.com" not in cleaned
    assert "[email]" in cleaned
    assert "[phone]" in cleaned
    assert "[order_id]" in cleaned


def test_competitor_primary_dropped_unless_nykaa():
    assert is_competitor_primary("Myntra sizing is better than everyone.", ["myntra", "ajio"])
    assert not is_competitor_primary(
        "Compared Nykaa Fashion wishlist to Myntra size notes.",
        ["myntra", "ajio"],
    )


def test_constraint_pipeline_filters_and_caps():
    constraints = ScrapeConstraints(
        primary_time_window_months=12,
        fallback_time_window_months=24,
        min_relevant_per_source=1,
        min_corpus_total=400,
        max_corpus_total=600,
        min_chars=20,
        min_words=4,
        max_chars=2000,
        required_keywords=["wishlist", "size", "fit"],
        source_caps={"play_store": 2},
        near_duplicate_threshold=0.95,
        competitor_blocklist=["myntra", "ajio"],
        strip_pii=True,
    )
    docs = [
        _doc("Saved this dress to my wishlist until I check the size."),
        _doc("Fit looks unsure so it sits in the wishlist for now."),
        _doc("ok"),
        _doc("Saved this dress to my wishlist until I check the size."),
        _doc("Delivery was late today only."),
        _doc("Old wishlist size note from years ago.", days_ago=800),
        _doc("Ajio size charts are the only ones I trust now for ethnic wear."),
    ]
    kept, stats = apply_document_constraints(docs, constraints, time_window_months=12, cap=2)
    assert len(kept) == 2
    assert stats.rejected_length >= 1
    assert stats.rejected_exact_duplicate >= 1
    assert stats.rejected_keyword >= 1
    assert stats.rejected_time >= 1
    assert stats.rejected_competitor >= 1
    assert stats.output_count == 2


def test_content_hash_stable():
    assert content_hash("Hello World") == content_hash("  hello   world ")
