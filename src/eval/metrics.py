"""Metric helpers for Phase 7."""

from __future__ import annotations

from typing import Iterable, Sequence


def jaccard(pred: Iterable[str], gold: Iterable[str]) -> float:
    a = set(pred)
    b = set(gold)
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def percentile(values: Sequence[float], p: float) -> float:
    if not values:
        return 0.0
    xs = sorted(float(v) for v in values)
    if len(xs) == 1:
        return xs[0]
    rank = (len(xs) - 1) * (p / 100.0)
    lo = int(rank)
    hi = min(lo + 1, len(xs) - 1)
    frac = rank - lo
    return xs[lo] * (1.0 - frac) + xs[hi] * frac


def precision_binary(y_true: Sequence[str], y_pred: Sequence[str], *, positive: str) -> float:
    tp = fp = 0
    for gold, pred in zip(y_true, y_pred):
        if pred != positive:
            continue
        if gold == positive:
            tp += 1
        else:
            fp += 1
    if tp + fp == 0:
        return 0.0
    return tp / (tp + fp)


def review_score(row: dict) -> int:
    return int(
        int(row.get("relevant_evidence") or 0)
        + int(row.get("cited_paraphrased") or 0)
        + int(row.get("no_hallucination") or 0)
        + int(row.get("actionable_without_discounts") or 0)
    )
