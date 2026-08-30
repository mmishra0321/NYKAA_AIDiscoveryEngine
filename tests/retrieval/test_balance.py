from src.retrieval.balance import source_balance
from src.retrieval.filters import interleave_intent, prefer_decision_factors, stratify_segment_category


def test_source_balance_caps_majority_when_alternatives_exist():
    hits = [{"source": "play_store", "i": i} for i in range(8)]
    hits += [{"source": "reddit", "i": i} for i in range(8)]
    packed = source_balance(hits, n=10, max_fraction=0.6)
    assert len(packed) == 10
    play = sum(1 for h in packed if h["source"] == "play_store")
    assert play <= 6
    assert sum(1 for h in packed if h["source"] == "reddit") >= 4


def test_source_balance_fills_when_single_source():
    hits = [{"source": "play_store"} for _ in range(12)]
    packed = source_balance(hits, n=10, max_fraction=0.6)
    assert len(packed) == 10
    assert all(h["source"] == "play_store" for h in packed)


def test_q7_prefers_decision_factors():
    hits = [
        {"decision_factors": [], "similarity": 0.9},
        {"decision_factors": ["fit"], "similarity": 0.5},
    ]
    ordered = prefer_decision_factors(hits)
    assert ordered[0]["decision_factors"] == ["fit"]


def test_q8_interleaves_intent():
    hits = [
        {"intent_label": "unclear"},
        {"intent_label": "bookmark"},
        {"intent_label": "purchase_intent"},
        {"intent_label": "bookmark"},
    ]
    ordered = interleave_intent(hits)
    assert [h["intent_label"] for h in ordered[:3]] == [
        "purchase_intent",
        "bookmark",
        "unclear",
    ]


def test_q9_stratifies_segments():
    hits = [
        {"segment_hint": "first_time", "product_category": "ethnic"},
        {"segment_hint": "first_time", "product_category": "ethnic"},
        {"segment_hint": "repeat", "product_category": "western"},
    ]
    ordered = stratify_segment_category(hits)
    keys = [(h["segment_hint"], h["product_category"]) for h in ordered[:2]]
    assert ("first_time", "ethnic") in keys
    assert ("repeat", "western") in keys
