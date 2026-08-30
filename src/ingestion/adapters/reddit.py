"""Reddit adapter — PullPush public search. Nykaa Fashion only."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import requests

from src.ingestion.base import BaseScraper
from src.ingestion.document_factory import make_document
from src.models.schemas import Platform, ReviewDocument, SourceKind, SourceType

logger = logging.getLogger(__name__)

NYKAA_MARKERS = ("nykaa fashion", "nykaafashion", "nykaa")


class RedditScraper(BaseScraper):
    source_name = "reddit"

    def collect_candidates(self, time_window_months: int) -> tuple[list[ReviewDocument], int, list[str]]:
        errors: list[str] = []
        queries = list(self.config.get("search_queries") or ['"Nykaa Fashion" review'])
        cap = self.constraints.cap_for_source(self.source_name)
        collected: list[ReviewDocument] = []
        fetched = 0
        seen: set[str] = set()

        for query in queries:
            try:
                resp = requests.get(
                    "https://api.pullpush.io/reddit/search/submission/",
                    params={"q": query, "size": 50},
                    timeout=40,
                    headers={"User-Agent": "nykaa-fashion-wishlist-discovery/0.1"},
                )
                if not resp.ok:
                    errors.append(f"reddit query '{query}' status={resp.status_code}")
                    continue
                items = resp.json().get("data") or []
            except Exception as exc:  # noqa: BLE001
                errors.append(f"reddit query '{query}': {exc}")
                continue

            fetched += len(items)
            for item in items:
                title = (item.get("title") or "").strip()
                body = (item.get("selftext") or "").strip()
                text = f"{title}. {body}".strip(". ").strip()
                if not text:
                    continue
                lower = text.lower()
                if not any(m in lower for m in NYKAA_MARKERS):
                    continue
                key = text.lower()[:220]
                if key in seen:
                    continue
                seen.add(key)

                created = item.get("created_utc")
                ts = (
                    datetime.fromtimestamp(created, tz=timezone.utc)
                    if created
                    else datetime.now(timezone.utc)
                )
                permalink = item.get("permalink") or ""
                collected.append(
                    make_document(
                        source=SourceType.REDDIT,
                        raw_text=text[:1800],
                        date=ts,
                        title=title or None,
                        url=f"https://reddit.com{permalink}" if permalink else "",
                        platform=Platform.WEB,
                        source_type=SourceKind.COMMUNITY,
                        origin="pullpush",
                    )
                )

            if len(collected) >= cap * 2:
                break

        logger.info("reddit candidates=%s fetched=%s window=%sm", len(collected), fetched, time_window_months)
        return collected, fetched, errors
