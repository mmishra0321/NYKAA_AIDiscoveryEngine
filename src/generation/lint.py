"""Reject generated text that recommends coupons / discounts / cashback / price-cuts."""

from __future__ import annotations

import re
from typing import Iterable

from src.config_loader import load_prompts

# Price as a *decision factor* is in scope. These phrases are solution-language.
_EXTRA = (
    r"promo codes?",
    r"vouchers?",
    r"cash[\s-]?back",
    r"%\s*off",
    r"percent off",
    r"make (?:it|them|the item) cheaper",
    r"lower the price",
    r"cut the price",
    r"price[\s-]?match",
)

_COMPILED: re.Pattern[str] | None = None


def forbidden_patterns() -> list[str]:
    cfg = load_prompts().get("forbidden_mechanisms") or []
    parts = [re.escape(str(p).lower()) for p in cfg if p]
    parts.extend(_EXTRA)
    return parts


def _compiled() -> re.Pattern[str]:
    global _COMPILED
    if _COMPILED is None:
        _COMPILED = re.compile(r"(?:%s)" % "|".join(forbidden_patterns()), re.IGNORECASE)
    return _COMPILED


def lint_hits(text: str) -> list[str]:
    if not text:
        return []
    return sorted({m.group(0).lower() for m in _compiled().finditer(text)})


def lint_blob(parts: Iterable[str]) -> list[str]:
    return lint_hits("\n".join(p for p in parts if p))


def catalog_lint_text(section: dict) -> str:
    chunks = [
        str(section.get("summary") or ""),
        str(section.get("data_gaps") or ""),
        *[str(x) for x in (section.get("implications") or [])],
        *[str(x) for x in (section.get("interview_probes") or [])],
    ]
    for theme in section.get("sub_themes") or []:
        if hasattr(theme, "model_dump"):
            data = theme.model_dump()
        elif isinstance(theme, dict):
            data = theme
        else:
            continue
        chunks.append(str(data.get("name") or ""))
        chunks.append(str(data.get("hypothesis") or ""))
        chunks.extend(str(x) for x in (data.get("paraphrased_examples") or []))
        chunks.extend(str(x) for x in (data.get("interview_probes") or []))
    return "\n".join(chunks)
