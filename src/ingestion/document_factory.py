"""Build ReviewDocument instances."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from src.ingestion.constraints import content_hash
from src.models.schemas import (
    Platform,
    ProductCategory,
    ReviewDocument,
    SegmentHint,
    Sentiment,
    SourceKind,
    SourceType,
)


def make_document(
    *,
    source: SourceType,
    raw_text: str,
    date: datetime,
    rating: Optional[int] = None,
    title: Optional[str] = None,
    url: str = "",
    platform: Platform = Platform.UNKNOWN,
    source_type: SourceKind = SourceKind.APP_REVIEW,
    origin: Optional[str] = None,
    product_category: ProductCategory = ProductCategory.UNKNOWN,
    segment: SegmentHint = SegmentHint.UNKNOWN,
) -> ReviewDocument:
    cleaned = " ".join(raw_text.split())
    h = content_hash(cleaned)
    doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source.value}:{h}"))
    sentiment = Sentiment.NEUTRAL
    if rating is not None:
        if rating >= 4:
            sentiment = Sentiment.POSITIVE
        elif rating <= 2:
            sentiment = Sentiment.NEGATIVE
    return ReviewDocument(
        id=doc_id,
        source=source,
        source_type=source_type,
        date=date,
        product_category=product_category,
        raw_text=cleaned,
        url=url,
        title=title,
        rating=rating,
        platform=platform,
        segment_hint=segment,
        sentiment=sentiment,
        content_hash=h,
        pii_stripped=True,
        origin=origin,
    )
