"""Phase 0 theme taxonomy helpers."""

from __future__ import annotations

from enum import Enum

from src.config_loader import load_themes, theme_ids


class ThemeId(str, Enum):
    WISHLIST_MOTIVE = "wishlist_motive"
    CONVERSION_BLOCKER = "conversion_blocker"
    POST_LIKE_UNCERTAINTY = "post_like_uncertainty"
    PURCHASE_DEFERRAL = "purchase_deferral"
    COMPARISON_BEHAVIOR = "comparison_behavior"
    OFF_PLATFORM_RESEARCH = "off_platform_research"
    DECISION_FACTOR = "decision_factor"
    INTENT_VS_BOOKMARK = "intent_vs_bookmark"
    SEGMENT_CONTEXT = "segment_context"
    UNMET_NEED = "unmet_need"
    LOGISTICS_NOISE = "logistics_noise"


def validate_theme_registry() -> None:
    yaml_ids = set(theme_ids())
    enum_ids = {t.value for t in ThemeId}
    if yaml_ids != enum_ids:
        missing = enum_ids - yaml_ids
        extra = yaml_ids - enum_ids
        raise ValueError(f"Theme mismatch. missing_in_yaml={missing} extra_in_yaml={extra}")


def deprioritized_themes() -> set[str]:
    return set(load_themes().get("deprioritize") or [])
