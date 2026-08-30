from src.models.schemas import FrequencyLabel, SubTheme
from src.processing.quantify import compute_impact_score, frequency_from_tertiles, score_and_rank


def test_impact_score_weights():
    score = compute_impact_score(
        share=0.31,
        shares=[0.31, 0.1],
        source_diversity=3,
        n_sources=3,
        severity="high",
        weights={"share": 0.4, "source_diversity": 0.3, "severity": 0.3},
    )
    assert score == 1.0


def test_frequency_tertiles_within_bucket():
    shares = [0.4, 0.3, 0.2, 0.1]
    assert frequency_from_tertiles(0.4, shares) is FrequencyLabel.HIGH
    assert frequency_from_tertiles(0.1, shares) is FrequencyLabel.LOW
    assert frequency_from_tertiles(0.25, shares) is FrequencyLabel.MEDIUM


def test_score_and_rank_orders_by_impact():
    themes = [
        SubTheme(sub_theme_id="a", question_id="q1_wishlist_motive", name="A", share_of_bucket=0.1, source_diversity=1),
        SubTheme(
            sub_theme_id="b",
            question_id="q1_wishlist_motive",
            name="B",
            share_of_bucket=0.5,
            source_diversity=3,
            severity=FrequencyLabel.HIGH,
        ),
    ]
    ranked = score_and_rank(themes, n_sources=3)
    assert ranked[0].sub_theme_id == "b"
    assert ranked[0].impact_rank == 1
    assert ranked[1].impact_rank == 2
