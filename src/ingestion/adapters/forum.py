"""Forum adapter — HTML scrape deferred (ToS / robots.txt)."""

from __future__ import annotations

from src.ingestion.base import BaseScraper
from src.models.schemas import ReviewDocument


class ForumScraper(BaseScraper):
    source_name = "forum"

    def collect_candidates(self, time_window_months: int) -> tuple[list[ReviewDocument], int, list[str]]:
        return [], 0, ["forum HTML scrape deferred — prefer official APIs; see README known limitations"]
