"""App Store RSS adapter — Nykaa Fashion id 1439872423."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import requests

from src.ingestion.base import BaseScraper
from src.ingestion.document_factory import make_document
from src.models.schemas import Platform, ReviewDocument, SourceKind, SourceType

logger = logging.getLogger(__name__)


def _label(node, default: str = "") -> str:
    if node is None:
        return default
    if isinstance(node, dict):
        return str(node.get("label") or default)
    return str(node or default)


class AppStoreScraper(BaseScraper):
    source_name = "app_store"

    def collect_candidates(self, time_window_months: int) -> tuple[list[ReviewDocument], int, list[str]]:
        errors: list[str] = []
        app_id = str(self.config.get("app_id", "1439872423"))
        country = self.config.get("country", "in")
        cap = self.constraints.cap_for_source(self.source_name)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
        }

        collected: list[ReviewDocument] = []
        fetched = 0
        seen: set[str] = set()

        for page in range(1, 11):
            url = (
                f"https://itunes.apple.com/rss/customerreviews/page={page}/"
                f"id={app_id}/sortby=mostrecent/json?l=en&cc={country}"
            )
            try:
                resp = requests.get(url, headers=headers, timeout=30)
                if not resp.ok:
                    errors.append(f"app_store page {page} status={resp.status_code}")
                    break
                payload = resp.json()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"app_store page {page}: {exc}")
                break

            entries = payload.get("feed", {}).get("entry") or []
            if isinstance(entries, dict):
                entries = [entries]

            page_reviews = 0
            for entry in entries:
                rating_raw = _label(entry.get("im:rating"))
                content = _label(entry.get("content"))
                title = _label(entry.get("title"))
                if not content or not rating_raw.isdigit():
                    continue

                page_reviews += 1
                fetched += 1
                key = content.lower()[:200]
                if key in seen:
                    continue
                seen.add(key)

                updated = _label(entry.get("updated"))
                try:
                    ts = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                except Exception:
                    ts = datetime.now(timezone.utc)

                link = ""
                links = entry.get("link")
                if isinstance(links, dict):
                    link = links.get("attributes", {}).get("href", "")
                elif isinstance(links, list) and links:
                    link = (links[0].get("attributes") or {}).get("href", "")

                collected.append(
                    make_document(
                        source=SourceType.APP_STORE,
                        raw_text=content,
                        date=ts,
                        rating=int(rating_raw),
                        title=title or None,
                        url=link or f"https://apps.apple.com/{country}/app/id{app_id}",
                        platform=Platform.IOS,
                        source_type=SourceKind.APP_REVIEW,
                        origin="itunes_rss",
                    )
                )

            if page_reviews == 0 or len(collected) >= cap * 3:
                break

        logger.info("app_store candidates=%s fetched=%s window=%sm", len(collected), fetched, time_window_months)
        return collected, fetched, errors
