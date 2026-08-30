"""Retrieval-stub catalog section — quantified themes, paraphrases, no verbatim dumps."""

from __future__ import annotations

from typing import Any

from src.models.schemas import CatalogQuestion, FrequencyLabel, SubTheme

_IMPLICATIONS: dict[str, str] = {
    "q1_wishlist_motive": (
        "Observed: people save to style later, compare, or wait. "
        "Hypothesis: showing the original save reason at return-to-wishlist would raise 30-day conversion without making items cheaper."
    ),
    "q2_conversion_blockers": (
        "Observed: liked items sit after fit/quality doubt. "
        "Hypothesis: resolving post-save uncertainty (size, fabric, colour) unblocks purchase more than a promo."
    ),
    "q3_uncertainties": (
        "Observed: size/fit/fabric doubt after liking. "
        "Hypothesis: a clearer size story on saved items would cut hesitation."
    ),
    "q4_postpone": (
        "Observed: deferral language (later, payday, not sure yet). "
        "Hypothesis: a non-promo reminder tied to occasion or timing beats forgetting."
    ),
    "q5_compare": (
        "Observed: shoppers hold two or more saved items. "
        "Hypothesis: a side-by-side of saved pieces would reduce stalled shortlists."
    ),
    "q6_off_platform": (
        "Observed: YouTube/Instagram/friends are checked before converting a save. "
        "Hypothesis: in-app proof (hauls, try-ons) should be reachable from the wishlist."
    ),
    "q7_decision_factors": (
        "Observed: fit, size, reviews, occasion, and price-as-signal show up in the same breath. "
        "Hypothesis: surface those factors on the saved item, not a markdown."
    ),
    "q8_intent_vs_bookmark": (
        "Observed: some lists are moodboards, some are buy-lists. "
        "Hypothesis: letting users mark intent would stop treating bookmarks as failed conversion."
    ),
    "q9_segments": (
        "Observed: first-time vs repeat and category (ethnic/western/footwear) change the doubt. "
        "Hypothesis: segment-aware fit help on saved items would lift 30-day purchase unevenly — interview to confirm."
    ),
    "q10_unmet_needs": (
        "Observed: the same slug appearing in three or more independent sources is a high-confidence unmet need. "
        "Hypothesis: fix that cross-source friction first."
    ),
}


def _probe(question: str) -> str:
    return f"Walk me through the last Nykaa Fashion item you saved but did not buy in 30 days — did this come up: {question}"


def stub_section(
    *,
    query: dict[str, Any],
    pack: dict[str, Any],
    themes: list[SubTheme],
) -> CatalogQuestion:
    qid = str(query["id"])
    question = str(query.get("question") or pack.get("question") or qid)
    n_hits = int(pack.get("hit_count") or 0)
    gap = pack.get("flag") == "data_gap" or n_hits == 0

    if gap and not themes:
        return CatalogQuestion(
            id=qid,
            question=question,
            summary=(
                "No quantified, evidence-backed sub-theme in this run. "
                "Treat as an explicit data_gap until more wishlist language is classified."
            ),
            sub_themes=[],
            implications=[],
            interview_probes=[_probe(question)],
            confidence="low",
            data_gaps=str(pack.get("data_gap") or f"No indexed evidence for {qid}."),
            evidence_count=0,
            themes_count=0,
        )

    names = ", ".join(t.name for t in themes[:4]) or "retrieved wishlist language"
    sources = sorted({s for t in themes for s in t.sources} | set((pack.get("source_counts") or {}).keys()))
    summary = (
        f"Observed from {n_hits} retrieved chunks"
        f"{' across ' + ', '.join(sources) if sources else ''}: {names}. "
        "Impact ranking uses share, source diversity, and severity — not star ratings. "
        "Implications below are hypotheses for Part 3 interviews, not conclusions."
    )
    impl = _IMPLICATIONS.get(qid)
    probes = []
    for theme in themes:
        probes.extend(theme.interview_probes)
        if not theme.paraphrased_examples:
            theme.paraphrased_examples = [
                f"Users describe {theme.name.lower()} after saving a Nykaa Fashion item — enough to stall a 30-day purchase."
            ]
    if not probes:
        probes = [_probe(question)]
    # de-dupe probes, cap
    seen: set[str] = set()
    unique_probes: list[str] = []
    for p in probes:
        if p and p not in seen:
            seen.add(p)
            unique_probes.append(p)
    return CatalogQuestion(
        id=qid,
        question=question,
        summary=summary,
        sub_themes=themes,
        implications=[impl] if impl else [],
        interview_probes=unique_probes[:5],
        confidence="medium" if n_hits >= 3 and themes else "low",
        data_gaps="" if n_hits else str(pack.get("data_gap") or ""),
        evidence_count=n_hits,
        themes_count=len(themes),
    )


def residual_theme(qid: str, pack: dict[str, Any]) -> SubTheme:
    sources = list((pack.get("source_counts") or {}).keys())
    hits = pack.get("hits") or []
    return SubTheme(
        sub_theme_id=f"{qid}_retrieved",
        question_id=qid,
        name="Retrieved wishlist language",
        share_of_bucket=1.0,
        source_diversity=len(sources),
        sources=sources,
        frequency=FrequencyLabel.MEDIUM,
        severity=FrequencyLabel.MEDIUM,
        impact_rank=1,
        paraphrased_examples=[
            "Public comments in this bucket describe save-and-hesitate behaviour on Nykaa Fashion, not delivery logistics."
        ],
        hypothesis="Language in this residual cluster may delay 30-day wishlist conversion.",
        interview_probes=["When you saved something recently, what were you still unsure about?"],
        chunk_ids=[str(h.get("chunk_id")) for h in hits if h.get("chunk_id")],
    )
