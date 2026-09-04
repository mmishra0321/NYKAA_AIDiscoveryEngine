"""Grounded Ask — catalog only; Groq stays on the server."""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

from src.config_loader import canonical_queries, load_prompts
from src.generation.lint import lint_hits
from src.models.schemas import CatalogQuestion, CatalogReport
from src.processing.groq_client import GroqClient
from src.processing.jsonutil import parse_json_object

logger = logging.getLogger(__name__)

_WORD = re.compile(r"[a-z0-9]+")
_STOP = {
    "a",
    "an",
    "the",
    "to",
    "do",
    "of",
    "and",
    "or",
    "is",
    "in",
    "on",
    "for",
    "what",
    "why",
    "how",
    "when",
    "who",
    "are",
    "be",
    "this",
    "that",
    "with",
    "from",
    "it",
    "as",
    "at",
    "by",
    "into",
    "about",
    "can",
    "does",
    "did",
    "me",
    "my",
    "we",
    "you",
    "their",
    "they",
}
_DOMAIN = {
    "wishlist",
    "wish",
    "saved",
    "save",
    "saving",
    "shortlist",
    "bookmark",
    "fit",
    "size",
    "sizing",
    "nykaa",
    "fashion",
    "purchase",
    "buy",
    "buying",
    "cart",
    "convert",
    "conversion",
    "hesitat",
    "doubt",
    "stall",
    "postpone",
    "later",
    "compare",
    "comparison",
    "instagram",
    "youtube",
    "haul",
    "friend",
    "reels",
    "intent",
    "occasion",
    "segment",
    "kurta",
    "dress",
    "heel",
    "review",
    "unmet",
    "nudge",
    "stock",
}
_MIN_SCORE = 2

_UNMATCHED_ANSWER = (
    "That question does not match any of the ten Nykaa Fashion wishlist research questions. "
    "Ask about why people save items, what blocks a wishlisted buy, fit or size doubt after saving, "
    "why purchases get postponed, how shoppers compare shortlists, what they check off-app "
    "(Instagram, friends, other apps), decision factors like fit and occasion, "
    "intent vs bookmarking, differences across segments, or unmet needs that show up across sources."
)


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall((text or "").lower()))


def _content_tokens(text: str) -> set[str]:
    return {t for t in _tokens(text) if t not in _STOP and len(t) > 1}


def _paraphrase_blob(query_id: str) -> str:
    for row in canonical_queries():
        if row.get("id") == query_id:
            return " ".join(str(p) for p in (row.get("paraphrases") or []))
    return ""


def match_question(
    question: str, report: CatalogReport
) -> tuple[Optional[CatalogQuestion], int]:
    """Return (best catalog question, score). Score 0 + None-like when out of scope.

    Always returns a CatalogQuestion candidate for debugging, but callers should
    treat low scores as unmatched via `is_match`.
    """
    q_tokens = _content_tokens(question)
    best = report.questions[0] if report.questions else None
    best_score = -1
    if best is None:
        return None, 0

    for item in report.questions:
        blob = " ".join(
            [
                item.id,
                item.question,
                item.summary,
                _paraphrase_blob(item.id),
                *[t.name for t in item.sub_themes],
            ]
        )
        overlap = q_tokens & _content_tokens(blob)
        score = len(overlap)
        if item.id.replace("_", " ") in (question or "").lower():
            score += 5
        # Soft boost when the ask clearly sits in wishlist/fashion domain
        if q_tokens & _DOMAIN and overlap:
            score += 1
        if score > best_score:
            best_score = score
            best = item
    return best, max(best_score, 0)


def is_in_scope(question: str, score: int) -> bool:
    q_tokens = _content_tokens(question)
    if not q_tokens:
        return False
    if score >= _MIN_SCORE:
        return True
    # Single strong domain overlap still allowed (e.g. "wishlist motive?")
    if score >= 1 and q_tokens & _DOMAIN:
        return True
    return False


def _unmatched_payload() -> dict[str, Any]:
    return {
        "matched": False,
        "query_id": None,
        "question": None,
        "answer": _UNMATCHED_ANSWER,
        "implications": [],
        "sub_themes": [],
        "paraphrased_examples": [],
        "confidence": "low",
        "data_gaps": "",
        "mode": "unmatched",
        "error": "no_matching_research_question",
    }


def _stub_answer(item: CatalogQuestion) -> dict[str, Any]:
    paraphrases = []
    for theme in item.sub_themes:
        paraphrases.extend(theme.paraphrased_examples[:1])
    answer = item.summary
    if item.data_gaps:
        answer = f"{answer} Gap: {item.data_gaps}"
    return {
        "matched": True,
        "query_id": item.id,
        "question": item.question,
        "answer": answer,
        "implications": list(item.implications),
        "sub_themes": [t.model_dump(mode="json") for t in item.sub_themes],
        "paraphrased_examples": paraphrases[:4],
        "confidence": item.confidence,
        "data_gaps": item.data_gaps,
        "mode": "catalog",
    }


def _groq_answer(item: CatalogQuestion, user_q: str, client: GroqClient) -> dict[str, Any] | None:
    prompts = load_prompts()
    payload = {
        "id": item.id,
        "question": item.question,
        "summary": item.summary,
        "implications": item.implications,
        "sub_themes": [
            {
                "name": t.name,
                "share_of_bucket": t.share_of_bucket,
                "source_diversity": t.source_diversity,
                "impact_score": t.impact_score,
                "paraphrased_examples": t.paraphrased_examples,
                "hypothesis": t.hypothesis,
            }
            for t in item.sub_themes
        ],
        "data_gaps": item.data_gaps,
    }
    try:
        raw = client.chat(
            [
                {"role": "system", "content": str(prompts.get("generate_system") or "")},
                {
                    "role": "user",
                    "content": (
                        f"User question: {user_q}\n\n"
                        f"Answer ONLY from this catalog JSON (paraphrase; no coupons/discounts/"
                        f"cashback/price-cuts):\n{payload}\n\n"
                        "Return JSON: answer, implications, confidence, data_gaps."
                    ),
                },
            ],
            temperature=float(prompts.get("temperature") or 0.2),
        )
        data = parse_json_object(raw)
        answer = str(data.get("answer") or data.get("summary") or "")
        implications = [str(x) for x in (data.get("implications") or [])]
        blob = "\n".join([answer, *implications])
        if not answer or lint_hits(blob):
            return None
        return {
            "matched": True,
            "query_id": item.id,
            "question": item.question,
            "answer": answer,
            "implications": implications or list(item.implications),
            "sub_themes": [t.model_dump(mode="json") for t in item.sub_themes],
            "paraphrased_examples": [
                e for t in item.sub_themes for e in t.paraphrased_examples[:1]
            ],
            "confidence": str(data.get("confidence") or item.confidence),
            "data_gaps": str(data.get("data_gaps") or item.data_gaps),
            "mode": "groq",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Ask Groq failed: %s", exc)
        return None


def answer_ask(user_q: str, report: CatalogReport) -> dict[str, Any]:
    item, score = match_question(user_q, report)
    if item is None or not is_in_scope(user_q, score):
        return _unmatched_payload()
    client = GroqClient()
    if client.available:
        groq = _groq_answer(item, user_q, client)
        if groq:
            return groq
    return _stub_answer(item)
