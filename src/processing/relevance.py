"""Relevance gate — Groq JSON, heuristic stub if no key / --stub."""

from __future__ import annotations

import logging
from typing import Optional

from src.config_loader import load_prompts
from src.models.schemas import Relevance
from src.processing.groq_client import GroqClient
from src.processing.jsonutil import parse_json_object

logger = logging.getLogger(__name__)

WISHLIST_HINTS = (
    "wishlist",
    "wish list",
    "saved",
    "shortlist",
    "bookmark",
    "haven't bought",
    "havent bought",
    "compare",
    "instagram",
    "youtube",
    "haul",
)
FIT_HINTS = (
    "size",
    "sizing",
    "fit",
    "fabric",
    "colour",
    "color",
)
HESITATION_HINTS = (
    "not sure",
    "doubt",
    "hesitat",
    "won't buy",
    "didn't buy",
    "did not buy",
    "sits in",
    "still there",
    "waiting",
    "later",
)
LOGISTICS_HINTS = (
    "delivery",
    "delivered",
    "refund",
    "otp",
    "rider",
    "courier",
    "packed",
    "packaging",
    "late",
    "crash",
    "login",
)


def heuristic_relevance(text: str) -> Relevance:
    lower = text.lower()
    wish = sum(1 for h in WISHLIST_HINTS if h in lower)
    hesitate = sum(1 for h in HESITATION_HINTS if h in lower)
    fit = sum(1 for h in FIT_HINTS if h in lower)
    logi = sum(1 for h in LOGISTICS_HINTS if h in lower)
    signal = wish >= 1 or (fit >= 1 and hesitate >= 1)
    if signal:
        return Relevance.WISHLIST_SIGNAL
    if logi >= 1:
        return Relevance.LOGISTICS_NOISE
    return Relevance.OTHER


def _groq_relevance(client: GroqClient, text: str) -> Relevance:
    prompts = load_prompts()
    temp = float(prompts.get("classify_temperature") or 0.1)
    raw = client.chat(
        [
            {"role": "system", "content": str(prompts.get("relevance_system") or "")},
            {"role": "user", "content": text[:1500]},
        ],
        temperature=temp,
    )
    payload = parse_json_object(raw)
    label = str(payload.get("relevance") or "other").strip().lower()
    try:
        return Relevance(label)
    except ValueError:
        return heuristic_relevance(text)


def label_relevance(text: str, *, stub: bool, client: Optional[GroqClient] = None) -> Relevance:
    if stub or client is None or not client.available:
        return heuristic_relevance(text)
    try:
        return _groq_relevance(client, text)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Relevance Groq failed, using heuristic: %s", exc)
        return heuristic_relevance(text)
