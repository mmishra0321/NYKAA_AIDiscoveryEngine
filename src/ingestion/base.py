"""Base scraper: collect → constrain → optional 24-month fallback."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from src.ingestion.constraints import ScrapeConstraints, apply_document_constraints
from src.ingestion.types import utc_now_iso
from src.models.schemas import ReviewDocument

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    source_name: str = "unknown"

    def __init__(
        self,
        config: dict[str, Any],
        run_date: date | None = None,
        constraints: ScrapeConstraints | None = None,
        force_time_window_months: int | None = None,
    ) -> None:
        self.config = config
        self.run_date = run_date
        self.enabled = bool(config.get("enabled", True))
        self.constraints = constraints or ScrapeConstraints.load()
        self.force_time_window_months = force_time_window_months

    @abstractmethod
    def collect_candidates(self, time_window_months: int) -> tuple[list[ReviewDocument], int, list[str]]:
        """Returns documents, fetched_count, errors."""

    def fetch(self) -> tuple[list[ReviewDocument], int, int, list[str], dict]:
        all_errors: list[str] = []
        total_fetched = 0
        total_skipped = 0
        final_documents: list[ReviewDocument] = []
        filter_summary: dict = {}

        if self.force_time_window_months is not None:
            time_windows = [self.force_time_window_months]
        else:
            time_windows = [
                self.constraints.primary_time_window_months,
                self.constraints.fallback_time_window_months,
            ]

        for index, months in enumerate(time_windows):
            candidates, fetched, errors = self.collect_candidates(months)
            total_fetched += fetched
            all_errors.extend(errors)

            filtered, stats = apply_document_constraints(
                candidates,
                self.constraints,
                time_window_months=months,
                cap=self.constraints.cap_for_source(self.source_name),
            )
            total_skipped += stats.total_rejected
            filter_summary = stats.to_dict()
            final_documents = filtered

            logger.info(
                "%s | window=%sm | kept=%s | rejected=%s",
                self.source_name,
                months,
                stats.output_count,
                stats.total_rejected,
            )

            if (
                stats.output_count >= self.constraints.min_relevant_per_source
                or index == len(time_windows) - 1
            ):
                break

            logger.info(
                "Only %s docs for %s in %s months; extending window",
                stats.output_count,
                self.source_name,
                months,
            )

        return final_documents, total_fetched, total_skipped, all_errors, filter_summary
