"""YouTube comments — skipped unless YOUTUBE_API_KEY and adapter enabled."""

from __future__ import annotations

import os

from src.ingestion.base import BaseScraper
from src.models.schemas import ReviewDocument


class YouTubeScraper(BaseScraper):
    source_name = "youtube"

    def collect_candidates(self, time_window_months: int) -> tuple[list[ReviewDocument], int, list[str]]:
        if not os.getenv("YOUTUBE_API_KEY", "").strip():
            return [], 0, ["youtube skipped: YOUTUBE_API_KEY not set"]
        return [], 0, ["youtube Data API collection not implemented in Phase 1"]
