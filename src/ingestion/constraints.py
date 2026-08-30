"""Constraint pipeline: time → length → language → keywords → spam → competitor → PII → dedupe → cap."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from src.config_loader import load_constraints, load_sources
from src.ingestion.types import FilterStats
from src.models.schemas import ReviewDocument

PROMO_LINK_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|bit\.ly/\S+|t\.me/\S+)",
    re.IGNORECASE,
)
PROMO_PHRASE_PATTERN = re.compile(
    r"\b(buy now|click here|free followers|promo code|dm me|subscribe to)\b",
    re.IGNORECASE,
)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)
NON_LATIN_PATTERN = re.compile(r"[\u0900-\u097F\u0A00-\u0A7F]")

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\b(?:\+?91[\s-]?)?[6-9]\d{9}\b")
ORDER_RE = re.compile(r"\b(?:order\s*(?:id|#|no\.?)\s*[:\-]?\s*)[A-Z0-9-]{6,}\b", re.IGNORECASE)
HANDLE_RE = re.compile(r"(?<!\w)@[A-Za-z0-9_]{2,30}\b")

NYKAA_RE = re.compile(r"\bnykaa\b", re.IGNORECASE)


@dataclass
class ScrapeConstraints:
    primary_time_window_months: int = 12
    fallback_time_window_months: int = 24
    min_relevant_per_source: int = 40
    min_corpus_total: int = 400
    max_corpus_total: int = 600
    min_chars: int = 20
    min_words: int = 4
    max_chars: int = 2000
    language: str = "en"
    language_min_confidence: float = 0.9
    near_duplicate_threshold: float = 0.95
    required_keywords: list[str] = field(default_factory=list)
    source_caps: dict[str, int] = field(default_factory=dict)
    competitor_blocklist: list[str] = field(default_factory=list)
    strip_pii: bool = True

    @classmethod
    def load(cls) -> ScrapeConstraints:
        data = load_constraints()
        sources = load_sources()
        language = data.get("language") or {}
        length = data.get("length") or {}
        dedupe = data.get("dedupe") or {}
        pii = data.get("pii") or {}
        return cls(
            primary_time_window_months=int(data.get("time_window_months", 12)),
            fallback_time_window_months=int(data.get("time_window_fallback_months", 24)),
            min_relevant_per_source=int(data.get("min_docs_per_source_before_fallback", 40)),
            min_corpus_total=int(data.get("min_corpus_total", 400)),
            max_corpus_total=int(data.get("max_corpus_total", 600)),
            min_chars=int(length.get("min_chars", 20)),
            min_words=int(length.get("min_words", 4)),
            max_chars=int(length.get("max_chars", 2000)),
            language=str(language.get("prefer", "en")),
            language_min_confidence=float(language.get("min_confidence", 0.9)),
            near_duplicate_threshold=float(dedupe.get("near_duplicate_cosine", 0.95)),
            required_keywords=[str(k).lower() for k in (data.get("keywords_any") or [])],
            source_caps={k: int(v) for k, v in (sources.get("caps") or {}).items()},
            competitor_blocklist=[str(b).lower() for b in (sources.get("competitor_blocklist") or [])],
            strip_pii=bool(pii.get("strip_before_save", True)),
        )

    def cap_for_source(self, source_name: str) -> int:
        return int(self.source_caps.get(source_name, 100))


def content_hash(text: str) -> str:
    normalized = " ".join((text or "").lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def _cutoff(months: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=int(months * 30.4375))


def _ensure_aware(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts


def is_english(text: str, min_confidence: float = 0.9) -> bool:
    if not text or len(text.strip()) < 20:
        return False
    if len(NON_LATIN_PATTERN.findall(text)) > 8:
        return False
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return False
    ascii_letters = sum(1 for ch in letters if ch.isascii())
    return (ascii_letters / max(len(letters), 1)) >= min_confidence


def looks_like_spam(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    letters = [ch for ch in stripped if ch.isalpha()]
    if letters and sum(1 for ch in letters if ch.isupper()) / len(letters) > 0.85 and len(letters) > 12:
        return True
    no_emoji = EMOJI_PATTERN.sub("", stripped).strip()
    if len(stripped) >= 8 and len(no_emoji) < 3:
        return True
    if PROMO_LINK_PATTERN.search(stripped) and PROMO_PHRASE_PATTERN.search(stripped):
        return True
    return False


def has_required_keyword(text: str, keywords: list[str]) -> bool:
    lower = text.lower()
    return any(k in lower for k in keywords)


def is_competitor_primary(text: str, blocklist: list[str]) -> bool:
    """Drop if a competitor is named and Nykaa is not."""
    lower = text.lower()
    hit = any(brand in lower for brand in blocklist)
    if not hit:
        return False
    return NYKAA_RE.search(text) is None


def strip_pii(text: str) -> tuple[str, bool]:
    cleaned = EMAIL_RE.sub("[email]", text)
    cleaned = PHONE_RE.sub("[phone]", cleaned)
    cleaned = ORDER_RE.sub("[order_id]", cleaned)
    cleaned = HANDLE_RE.sub("[handle]", cleaned)
    return cleaned, cleaned != text


def _char_ngrams(text: str, n: int = 3) -> set[str]:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    if len(normalized) < n:
        return {normalized}
    return {normalized[i : i + n] for i in range(len(normalized) - n + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    union = len(a | b)
    return len(a & b) / union if union else 0.0


def apply_document_constraints(
    documents: list[ReviewDocument],
    constraints: ScrapeConstraints,
    *,
    time_window_months: int,
    cap: int,
) -> tuple[list[ReviewDocument], FilterStats]:
    stats = FilterStats(input_count=len(documents), time_window_months=time_window_months)
    cutoff = _cutoff(time_window_months)
    kept: list[ReviewDocument] = []
    seen_hashes: set[str] = set()
    ngram_index: list[tuple[str, set[str]]] = []

    for doc in documents:
        text = doc.raw_text.strip()
        if len(text) > constraints.max_chars:
            text = text[: constraints.max_chars].rstrip()

        ts = _ensure_aware(doc.date)
        if ts < cutoff:
            stats.rejected_time += 1
            continue

        if len(text) < constraints.min_chars or word_count(text) < constraints.min_words:
            stats.rejected_length += 1
            continue

        if not is_english(text, constraints.language_min_confidence):
            stats.rejected_language += 1
            continue

        if constraints.required_keywords and not has_required_keyword(text, constraints.required_keywords):
            stats.rejected_keyword += 1
            continue

        if looks_like_spam(text):
            stats.rejected_spam += 1
            continue

        if constraints.competitor_blocklist and is_competitor_primary(text, constraints.competitor_blocklist):
            stats.rejected_competitor += 1
            continue

        pii_hit = False
        if constraints.strip_pii:
            text, pii_hit = strip_pii(text)
            if pii_hit:
                stats.pii_stripped += 1

        h = content_hash(text)
        if h in seen_hashes:
            stats.rejected_exact_duplicate += 1
            continue

        grams = _char_ngrams(text)
        if any(jaccard(grams, prev) >= constraints.near_duplicate_threshold for _, prev in ngram_index):
            stats.rejected_near_duplicate += 1
            continue

        if len(kept) >= cap:
            stats.rejected_cap += 1
            continue

        seen_hashes.add(h)
        ngram_index.append((h, grams))
        kept.append(
            doc.model_copy(
                update={
                    "raw_text": text,
                    "content_hash": h,
                    "pii_stripped": True,
                }
            )
        )

    stats.output_count = len(kept)
    return kept, stats
