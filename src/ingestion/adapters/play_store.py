"""Play Store adapter — Nykaa Fashion `com.fsn.nds`."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.ingestion.base import BaseScraper
from src.ingestion.document_factory import make_document
from src.models.schemas import Platform, ReviewDocument, SourceKind, SourceType

logger = logging.getLogger(__name__)


class PlayStoreScraper(BaseScraper):
    source_name = "play_store"

    def collect_candidates(self, time_window_months: int) -> tuple[list[ReviewDocument], int, list[str]]:
        errors: list[str] = []
        package = self.config.get("package_name", "com.fsn.nds")
        lang = self.config.get("lang", "en")
        country = self.config.get("country", "in")
        cap = self.constraints.cap_for_source(self.source_name)
        origin = self.config.get("origin", "play_store_api")
        source = SourceType.NYKAA_BEAUTY_XREF if origin == "nykaa_beauty_xref" else SourceType.PLAY_STORE

        try:
            from google_play_scraper import Sort, reviews as gp_reviews
        except ImportError as exc:
            return [], 0, [f"google-play-scraper missing: {exc}"]

        collected: list[ReviewDocument] = []
        fetched = 0
        seen: set[str] = set()

        for sort in (Sort.NEWEST, Sort.MOST_RELEVANT):
            try:
                batch, _ = gp_reviews(
                    package,
                    lang=lang,
                    country=country,
                    sort=sort,
                    count=min(400, max(cap * 3, 120)),
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"play_store fetch failed ({sort}): {exc}")
                continue

            fetched += len(batch)
            for row in batch:
                text = (row.get("content") or "").strip()
                if not text:
                    continue
                key = text.lower()[:200]
                if key in seen:
                    continue
                seen.add(key)

                ts = row.get("at")
                if isinstance(ts, datetime):
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                else:
                    ts = datetime.now(timezone.utc)

                collected.append(
                    make_document(
                        source=source,
                        raw_text=text,
                        date=ts,
                        rating=row.get("score"),
                        url=f"https://play.google.com/store/apps/details?id={package}",
                        platform=Platform.ANDROID,
                        source_type=SourceKind.APP_REVIEW,
                        origin=origin,
                    )
                )
            if len(collected) >= cap * 3:
                break

        logger.info("play_store candidates=%s fetched=%s window=%sm", len(collected), fetched, time_window_months)
        return collected, fetched, errors
