"""Share, frequency tertiles, severity, and impact ranking."""

from __future__ import annotations

from typing import Sequence

from src.config_loader import load_processing
from src.models.schemas import FrequencyLabel, SubTheme

SEVERITY_NUM = {"high": 1.0, "medium": 0.6, "low": 0.3}


def severity_num(label: str) -> float:
    return SEVERITY_NUM.get((label or "medium").lower(), 0.6)


def share_norm(share: float, shares: Sequence[float]) -> float:
    peak = max(shares) if shares else 0.0
    if peak <= 0:
        return 0.0
    return share / peak


def frequency_from_tertiles(share: float, shares: Sequence[float]) -> FrequencyLabel:
    """High/medium/low from tertiles of share_of_bucket within one question."""
    values = [float(s) for s in shares]
    if len(values) < 3:
        if share >= 0.28:
            return FrequencyLabel.HIGH
        if share < 0.12:
            return FrequencyLabel.LOW
        return FrequencyLabel.MEDIUM
    ordered = sorted(values)
    low_cut = ordered[len(ordered) // 3]
    high_cut = ordered[(2 * len(ordered)) // 3]
    if share >= high_cut:
        return FrequencyLabel.HIGH
    if share <= low_cut:
        return FrequencyLabel.LOW
    return FrequencyLabel.MEDIUM


def impact_weights() -> dict[str, float]:
    weights = load_processing().get("impact_weights") or {}
    return {
        "share": float(weights.get("share", 0.4)),
        "source_diversity": float(weights.get("source_diversity", 0.3)),
        "severity": float(weights.get("severity", 0.3)),
    }


def compute_impact_score(
    *,
    share: float,
    shares: Sequence[float],
    source_diversity: int,
    n_sources: int,
    severity: str,
    weights: dict[str, float] | None = None,
) -> float:
    w = weights or impact_weights()
    n = max(int(n_sources), 1)
    return round(
        w["share"] * share_norm(share, shares)
        + w["source_diversity"] * (source_diversity / n)
        + w["severity"] * severity_num(severity),
        3,
    )


def score_and_rank(themes: list[SubTheme], *, n_sources: int) -> list[SubTheme]:
    if not themes:
        return []
    shares = [t.share_of_bucket for t in themes]
    weights = impact_weights()
    for theme in themes:
        theme.frequency = frequency_from_tertiles(theme.share_of_bucket, shares)
        theme.impact_score = compute_impact_score(
            share=theme.share_of_bucket,
            shares=shares,
            source_diversity=theme.source_diversity,
            n_sources=n_sources,
            severity=theme.severity.value,
            weights=weights,
        )
    themes.sort(key=lambda t: t.impact_score, reverse=True)
    for rank, theme in enumerate(themes, start=1):
        theme.impact_rank = rank
    return themes
