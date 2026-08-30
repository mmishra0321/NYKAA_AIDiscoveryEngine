"""Cap any one source at ~60% of the pack; fill remainder if the corpus is single-source."""

from __future__ import annotations

from collections import Counter
from typing import Any


def source_balance(
    hits: list[dict[str, Any]],
    *,
    n: int,
    max_fraction: float,
) -> list[dict[str, Any]]:
    if n <= 0 or not hits:
        return []
    cap = max(1, int(n * max_fraction))
    chosen: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for hit in hits:
        src = str(hit.get("source") or "unknown")
        if counts[src] < cap and len(chosen) < n:
            chosen.append(hit)
            counts[src] += 1
        else:
            deferred.append(hit)
    for hit in deferred:
        if len(chosen) >= n:
            break
        chosen.append(hit)
    return chosen[:n]
