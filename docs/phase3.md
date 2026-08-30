# Phase 3 — Embed and index

Status: **complete** (MiniLM when installed; `--stub` hash vectors for CI)

Processed `wishlist_signal` chunks → 384-d embeddings → Chroma collection `nykaa_fashion_wishlist_v1`. Upsert is idempotent on `chunk_id`.

## Metadata

`source`, `research_questions` (joined), `sub_theme_ids`, `segment_hint`, `product_category`, `relevance`, `date`, `url`, `chunk_id`, plus `has_{qid}` booleans for filters. `decision_factors` / `intent_label` are stored for Phase 4.

## Smoke

Query all 10 catalog questions via `has_{qid}`. **Fail if ≥8/10 are empty** (Q10 may be thin early).

## Run

```bash
source .venv/bin/activate
pip install -r requirements.txt
python -m src.indexing --stub --verbose
python -m src.indexing --run-date 2026-08-30
pytest tests/indexing -q
```

`--stub` skips MiniLM (no model download). Without `--stub`, `sentence-transformers/all-MiniLM-L6-v2` is used when installed.

## Outputs

| Path | Contents |
|---|---|
| `data/chroma/` | Persistent Chroma store |
| `data/index/{date}/indexing_summary.json` | Counts, embedder, smoke hits / gaps |

## Known limitations

- Stub embeddings are not semantic; smoke uses metadata flags, not cosine.
- Q10 stays empty until Phase 2 sees 3+ sources.
