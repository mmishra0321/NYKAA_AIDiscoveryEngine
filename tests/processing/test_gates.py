from datetime import datetime, timezone

from src.ingestion.document_factory import make_document
from src.models.schemas import Platform, Relevance, SourceKind, SourceType
from src.processing.classify import _coerce_result, heuristic_classify
from src.processing.clean import clean_text, contains_pii
from src.processing.jsonutil import parse_json_object
from src.processing.relevance import heuristic_relevance


def test_json_object_from_fenced_block():
    payload = parse_json_object('```json\n{"relevance": "wishlist_signal"}\n```')
    assert payload["relevance"] == "wishlist_signal"


def test_heuristic_relevance_splits_signal_and_logistics():
    signal = heuristic_relevance(
        "Liked the dress but reviews say it runs small so it sits in my wishlist."
    )
    noise = heuristic_relevance("Delivery was two days late and refund took a week. OTP failed once.")
    other = heuristic_relevance("Nice app I shop here sometimes for random stuff.")
    size_only = heuristic_relevance("Good collection but the size chart for kurtas is confusing.")
    assert signal is Relevance.WISHLIST_SIGNAL
    assert noise is Relevance.LOGISTICS_NOISE
    assert other is Relevance.OTHER
    assert size_only is Relevance.OTHER


def test_classifier_never_assigns_q10():
    result = heuristic_classify(
        "Unmet need q10_unmet_needs across sources: sizing runs small on my wishlist."
    )
    assert "q10_unmet_needs" not in result["research_questions"]
    coerced = _coerce_result(
        {
            "research_questions": ["q3_uncertainties", "q10_unmet_needs"],
            "decision_factors": ["size", "coupon"],
            "segment_hint": "made_up",
            "product_category": "ethnic",
            "intent_label": "unclear",
        }
    )
    assert coerced["research_questions"] == ["q3_uncertainties"]
    assert "q10_unmet_needs" not in coerced["research_questions"]
    assert "coupon" not in coerced["decision_factors"]
    assert coerced["segment_hint"] == "unknown"


def test_clean_strips_html_and_pii():
    cleaned = clean_text(
        "<p>Saved a kurta to wishlist. Email me at user@example.com or +919876543210 @handle</p>"
    )
    assert "<p>" not in cleaned
    assert "example.com" not in cleaned
    assert "[email]" in cleaned
    assert "[phone]" in cleaned
    assert not contains_pii(cleaned)


def test_make_document_roundtrip_source():
    doc = make_document(
        source=SourceType.REDDIT,
        raw_text="Saved two blazers to compare fit on Nykaa Fashion.",
        date=datetime.now(timezone.utc),
        platform=Platform.WEB,
        source_type=SourceKind.COMMUNITY,
    )
    assert doc.source is SourceType.REDDIT
    assert "wishlist" in doc.raw_text or "compare" in doc.raw_text
