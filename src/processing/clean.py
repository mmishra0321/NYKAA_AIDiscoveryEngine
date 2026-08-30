"""Text cleaning for Phase 2."""

from __future__ import annotations

import re

from src.ingestion.constraints import EMAIL_RE, HANDLE_RE, ORDER_RE, PHONE_RE, strip_pii

HTML_RE = re.compile(r"<[^>]+>")


def clean_text(text: str) -> str:
    cleaned = HTML_RE.sub(" ", text or "")
    cleaned, _ = strip_pii(cleaned)
    return " ".join(cleaned.split())


def contains_pii(text: str) -> bool:
    blob = text or ""
    return bool(
        EMAIL_RE.search(blob)
        or PHONE_RE.search(blob)
        or HANDLE_RE.search(blob)
        or ORDER_RE.search(blob)
    )
