"""Unified document, chunk, sub-theme, and catalog schemas (Phase 0)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SourceType(str, Enum):
    PLAY_STORE = "play_store"
    APP_STORE = "app_store"
    REDDIT = "reddit"
    TRUSTPILOT = "trustpilot"
    MOUTHSHUT = "mouthshut"
    YOUTUBE = "youtube"
    FORUM = "forum"
    BLOG = "blog"
    SOCIAL = "social"
    NYKAA_BEAUTY_XREF = "nykaa_beauty_xref"


class SourceKind(str, Enum):
    APP_REVIEW = "app_review"
    COMMUNITY = "community"
    VIDEO_COMMENT = "video_comment"
    COMPLAINT = "complaint"
    ARTICLE = "article"


class Relevance(str, Enum):
    WISHLIST_SIGNAL = "wishlist_signal"
    LOGISTICS_NOISE = "logistics_noise"
    OTHER = "other"


class Platform(str, Enum):
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"
    UNKNOWN = "unknown"


class SegmentHint(str, Enum):
    FIRST_TIME = "first_time"
    REPEAT = "repeat"
    PRICE_SENSITIVE = "price_sensitive"
    OCCASION_SHOPPER = "occasion_shopper"
    UNKNOWN = "unknown"


class ProductCategory(str, Enum):
    ETHNIC = "ethnic"
    WESTERN = "western"
    FOOTWEAR = "footwear"
    ACCESSORIES = "accessories"
    JEWELLERY = "jewellery"
    BEAUTY_CROSSOVER = "beauty_crossover"
    UNKNOWN = "unknown"


class IntentLabel(str, Enum):
    PURCHASE_INTENT = "purchase_intent"
    BOOKMARK = "bookmark"
    UNCLEAR = "unclear"


class DecisionFactor(str, Enum):
    FIT = "fit"
    SIZE = "size"
    STYLING = "styling"
    PRICE = "price"
    REVIEWS = "reviews"
    OCCASION = "occasion"
    SOCIAL_VALIDATION = "social_validation"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class FrequencyLabel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReviewDocument(BaseModel):
    """Canonical document after ingest + normalize (problem statement §7)."""

    id: str
    source: SourceType
    source_type: SourceKind = SourceKind.APP_REVIEW
    date: datetime
    product_category: ProductCategory = ProductCategory.UNKNOWN
    raw_text: str = Field(min_length=1)
    url: str = ""
    title: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    platform: Platform = Platform.UNKNOWN
    language: str = "en"
    relevance: Relevance = Relevance.WISHLIST_SIGNAL
    research_questions: list[str] = Field(default_factory=list)
    sub_theme_ids: list[str] = Field(default_factory=list)
    segment_hint: SegmentHint = SegmentHint.UNKNOWN
    decision_factors: list[str] = Field(default_factory=list)
    intent_label: IntentLabel = IntentLabel.UNCLEAR
    sentiment: Sentiment = Sentiment.NEUTRAL
    content_hash: str
    pii_stripped: bool = True
    origin: Optional[str] = None

    @field_validator("raw_text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("raw_text must not be empty")
        return cleaned


class ReviewChunk(BaseModel):
    chunk_id: str
    document_id: str
    text: str = Field(min_length=1)
    chunk_index: int = Field(ge=0)
    source: SourceType
    research_questions: list[str] = Field(default_factory=list)
    sub_theme_ids: list[str] = Field(default_factory=list)
    segment_hint: SegmentHint = SegmentHint.UNKNOWN
    product_category: ProductCategory = ProductCategory.UNKNOWN
    url: str = ""
    date: datetime
    content_hash: str


class SubTheme(BaseModel):
    sub_theme_id: str
    question_id: str
    name: str
    share_of_bucket: float = 0.0
    source_diversity: int = 0
    sources: list[str] = Field(default_factory=list)
    frequency: FrequencyLabel = FrequencyLabel.MEDIUM
    severity: FrequencyLabel = FrequencyLabel.MEDIUM
    impact_rank: int = 0
    impact_score: float = 0.0
    segment_skew: list[str] = Field(default_factory=list)
    paraphrased_examples: list[str] = Field(default_factory=list)
    hypothesis: str = ""
    interview_probes: list[str] = Field(default_factory=list)
    chunk_ids: list[str] = Field(default_factory=list)


class CatalogQuestion(BaseModel):
    id: str
    question: str
    summary: str
    sub_themes: list[SubTheme] = Field(default_factory=list)
    implications: list[str] = Field(default_factory=list)
    interview_probes: list[str] = Field(default_factory=list)
    confidence: str = "medium"
    data_gaps: str = ""
    evidence_count: int = 0
    themes_count: int = 0


class CatalogReport(BaseModel):
    generated_at: str
    kpi: str = "wishlist_to_purchase_30d"
    corpus: dict = Field(default_factory=dict)
    questions: list[CatalogQuestion] = Field(default_factory=list)
