"""Q1–Q9 multi-label classifier — Groq JSON, heuristic stub fallback. Never assigns q10."""

from __future__ import annotations

import logging
from typing import Any, Optional

from src.config_loader import classifier_question_ids, load_prompts
from src.models.schemas import IntentLabel, ProductCategory, SegmentHint
from src.processing.groq_client import GroqClient
from src.processing.jsonutil import parse_json_object

logger = logging.getLogger(__name__)

ALLOWED = set(classifier_question_ids())
FACTORS = {"fit", "size", "styling", "price", "reviews", "occasion", "social_validation"}


def heuristic_classify(text: str) -> dict[str, Any]:
    lower = text.lower()
    qs: list[str] = []
    factors: list[str] = []

    if any(k in lower for k in ("wishlist", "saved", "save it", "shortlist", "bookmark")):
        qs.append("q1_wishlist_motive")
    if any(k in lower for k in ("never bought", "didn't buy", "did not buy", "won't buy", "sits in", "still there")):
        qs.append("q2_conversion_blockers")
    if any(k in lower for k in ("size", "sizing", "fit", "fabric", "colour", "color", "authentic", "fake", "material")):
        qs.append("q3_uncertainties")
        qs.append("q7_decision_factors")
    if any(k in lower for k in ("waiting", "later", "payday", "not sure yet", "saving for now", "will decide")):
        qs.append("q4_postpone")
    if any(k in lower for k in ("compar", "between two", "vs ", " versus ", "shortlist")):
        qs.append("q5_compare")
    if any(k in lower for k in ("instagram", "youtube", "haul", "friend", "whatsapp")):
        qs.append("q6_off_platform")
    if any(k in lower for k in ("inspiration", "moodboard", "just saving", "not really planning", "dream closet")):
        qs.append("q8_intent_vs_bookmark")
    if "i will buy" in lower or "going to buy" in lower:
        qs.append("q8_intent_vs_bookmark")
    if any(k in lower for k in ("first time", "first order", "repeat", "ethnic", "western", "footwear", "budget")):
        qs.append("q9_segments")

    if "fit" in lower:
        factors.append("fit")
    if "size" in lower or "sizing" in lower:
        factors.append("size")
    if "styl" in lower:
        factors.append("styling")
    if "price" in lower or "expensive" in lower or "cheap" in lower:
        factors.append("price")
    if "review" in lower:
        factors.append("reviews")
    if any(k in lower for k in ("wedding", "occasion", "sangeet", "festive")):
        factors.append("occasion")
    if any(k in lower for k in ("instagram", "friend", "creator")):
        factors.append("social_validation")

    segment = SegmentHint.UNKNOWN
    if "first time" in lower or "first order" in lower:
        segment = SegmentHint.FIRST_TIME
    elif "repeat" in lower:
        segment = SegmentHint.REPEAT
    elif any(k in lower for k in ("wedding", "festive", "sangeet")):
        segment = SegmentHint.OCCASION_SHOPPER
    elif any(k in lower for k in ("budget", "payday", "expensive")):
        segment = SegmentHint.PRICE_SENSITIVE

    category = ProductCategory.UNKNOWN
    if any(k in lower for k in ("kurta", "saree", "lehenga", "ethnic", "anarkali")):
        category = ProductCategory.ETHNIC
    elif any(k in lower for k in ("heel", "sneaker", "sandal", "footwear", "shoe")):
        category = ProductCategory.FOOTWEAR
    elif any(k in lower for k in ("jewellery", "jewelry", "earring", "necklace")):
        category = ProductCategory.JEWELLERY
    elif any(k in lower for k in ("dress", "blazer", "western", "co-ord", "coord")):
        category = ProductCategory.WESTERN
    elif any(k in lower for k in ("bag", "belt", "accessory")):
        category = ProductCategory.ACCESSORIES

    intent = IntentLabel.UNCLEAR
    if any(k in lower for k in ("just saving", "inspiration", "moodboard", "not really planning")):
        intent = IntentLabel.BOOKMARK
    elif any(k in lower for k in ("i will buy", "going to buy", "definite buy")):
        intent = IntentLabel.PURCHASE_INTENT

    qs = [q for q in dict.fromkeys(qs) if q in ALLOWED]
    return {
        "research_questions": qs,
        "confidence": "medium" if qs else "low",
        "decision_factors": [f for f in dict.fromkeys(factors) if f in FACTORS],
        "segment_hint": segment.value,
        "product_category": category.value,
        "intent_label": intent.value,
        "rationale": "heuristic stub",
    }


def _coerce_result(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = set(classifier_question_ids())
    raw_qs = payload.get("research_questions") or []
    qs = [str(q) for q in raw_qs if str(q) in allowed]
    factors = [str(f) for f in (payload.get("decision_factors") or []) if str(f) in FACTORS]
    try:
        segment = SegmentHint(str(payload.get("segment_hint") or "unknown"))
    except ValueError:
        segment = SegmentHint.UNKNOWN
    try:
        category = ProductCategory(str(payload.get("product_category") or "unknown"))
    except ValueError:
        category = ProductCategory.UNKNOWN
    try:
        intent = IntentLabel(str(payload.get("intent_label") or "unclear"))
    except ValueError:
        intent = IntentLabel.UNCLEAR
    conf = str(payload.get("confidence") or ("medium" if qs else "low"))
    if conf not in {"high", "medium", "low"}:
        conf = "medium"
    return {
        "research_questions": qs,
        "confidence": conf,
        "decision_factors": factors,
        "segment_hint": segment.value,
        "product_category": category.value,
        "intent_label": intent.value,
        "rationale": str(payload.get("rationale") or "")[:240],
    }


def _groq_classify(client: GroqClient, text: str) -> dict[str, Any]:
    prompts = load_prompts()
    temp = float(prompts.get("classify_temperature") or 0.1)
    user = (
        f"{prompts.get('question_definitions')}\n\n"
        f"Text:\n{text[:1500]}"
    )
    raw = client.chat(
        [
            {"role": "system", "content": str(prompts.get("classifier_system") or "")},
            {"role": "user", "content": user},
        ],
        temperature=temp,
    )
    return _coerce_result(parse_json_object(raw))


def classify_document(text: str, *, stub: bool, client: Optional[GroqClient] = None) -> dict[str, Any]:
    if stub or client is None or not client.available:
        return heuristic_classify(text)
    try:
        return _groq_classify(client, text)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Classify Groq failed, using heuristic: %s", exc)
        return heuristic_classify(text)
