"""Ingestion result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


@dataclass
class FilterStats:
    input_count: int = 0
    output_count: int = 0
    rejected_time: int = 0
    rejected_length: int = 0
    rejected_language: int = 0
    rejected_keyword: int = 0
    rejected_spam: int = 0
    rejected_competitor: int = 0
    rejected_exact_duplicate: int = 0
    rejected_near_duplicate: int = 0
    rejected_cap: int = 0
    pii_stripped: int = 0
    time_window_months: int = 12

    @property
    def total_rejected(self) -> int:
        return (
            self.rejected_time
            + self.rejected_length
            + self.rejected_language
            + self.rejected_keyword
            + self.rejected_spam
            + self.rejected_competitor
            + self.rejected_exact_duplicate
            + self.rejected_near_duplicate
            + self.rejected_cap
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_count": self.input_count,
            "output_count": self.output_count,
            "rejected_time": self.rejected_time,
            "rejected_length": self.rejected_length,
            "rejected_language": self.rejected_language,
            "rejected_keyword": self.rejected_keyword,
            "rejected_spam": self.rejected_spam,
            "rejected_competitor": self.rejected_competitor,
            "rejected_exact_duplicate": self.rejected_exact_duplicate,
            "rejected_near_duplicate": self.rejected_near_duplicate,
            "rejected_cap": self.rejected_cap,
            "pii_stripped": self.pii_stripped,
            "time_window_months": self.time_window_months,
            "total_rejected": self.total_rejected,
        }


@dataclass
class IngestionResult:
    source: str
    records_fetched: int = 0
    records_saved: int = 0
    records_skipped: int = 0
    output_path: str = ""
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    finished_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "records_fetched": self.records_fetched,
            "records_saved": self.records_saved,
            "records_skipped": self.records_skipped,
            "output_path": self.output_path,
            "errors": self.errors,
            "metadata": self.metadata,
            "finished_at": self.finished_at,
        }
