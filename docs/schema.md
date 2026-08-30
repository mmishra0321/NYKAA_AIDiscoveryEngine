# Unified schema (Phase 0)

Pydantic models live in `src/models/schemas.py`. Field names match [problemStatement.md](../problemStatement.md) §7 plus engine fields from [architecture.md](../architecture.md).

## ReviewDocument

| Field | Type | Notes |
|---|---|---|
| `id` | string | Stable UUID |
| `source` | enum | `play_store`, `app_store`, `reddit`, `trustpilot`, `mouthshut`, `youtube`, `forum`, `blog`, `social`, `nykaa_beauty_xref` |
| `source_type` | enum | `app_review`, `community`, `video_comment`, `complaint`, `article` |
| `date` | ISO-8601 | Required |
| `product_category` | enum | `ethnic`, `western`, `footwear`, `accessories`, `jewellery`, `beauty_crossover`, `unknown` |
| `raw_text` | string | Anonymized body |
| `url` | string | Permalink |
| `rating` | 1–5 \| null | Store ratings when present |
| `platform` | enum | `ios`, `android`, `web`, `unknown` |
| `relevance` | enum | `wishlist_signal`, `logistics_noise`, `other` |
| `research_questions` | string[] | q1–q9 ids only at classify time; q10 computed later |
| `sub_theme_ids` | string[] | `{question_id}_{slug}` |
| `segment_hint` | enum | `first_time`, `repeat`, `price_sensitive`, `occasion_shopper`, `unknown` |
| `decision_factors` | string[] | fit, size, styling, price, reviews, occasion, social_validation |
| `intent_label` | enum | `purchase_intent`, `bookmark`, `unclear` |
| `content_hash` | string | SHA-256 of normalized text |
| `pii_stripped` | bool | Must be true before persist |

## ReviewChunk

Inherits `research_questions`, `sub_theme_ids`, `segment_hint`, `product_category`, `source`, `url`, `date` from the parent document. Short reviews = one chunk. Long threads ≈ 350 words, 50 overlap (`config/processing.yaml`).

## SubTheme

`share_of_bucket`, `source_diversity`, `frequency`, `severity`, `impact_rank`, `impact_score`, `paraphrased_examples`, `hypothesis`, `interview_probes`, `chunk_ids`.

## CatalogReport

`kpi: wishlist_to_purchase_30d`. `questions[]` is Q1–Q10, each with ranked `sub_themes`. User-facing examples are paraphrases, not verbatim dumps.
