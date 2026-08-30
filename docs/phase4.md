# Phase 4 — Retrieval

Status: **complete**

Query Chroma for each of Q1–Q10. Packs are capped at 10 hits, ~60% from any one source. Empty → `data_gap`.

## Strategy

| Question | How |
|---|---|
| Q1–Q8 | `has_{qid}` metadata filter + similarity rank |
| Q7 | Prefer chunks with `decision_factors` |
| Q8 | Interleave `purchase_intent` / `bookmark` / `unclear` |
| Q9 | Round-robin `segment_hint` × `product_category` |
| Q10 | Sub-themes with `source_diversity >= 3` |

## Run

```bash
source .venv/bin/activate
python -m src.retrieval --catalog --stub --verbose
python -m src.retrieval --catalog --run-date 2026-08-30
pytest tests/retrieval -q
```

`--stub` if the index was built with stub embeddings. If the latest `indexing_summary.json` says `embedder: stub`, retrieval stubs automatically.

## Outputs

`data/retrieval/{date}/{query_id}.json` plus `retrieval_summary.json`.

## Known limitations

- Live Play+App corpus often gaps Q2/Q6/Q8/Q10 until Reddit (or Groq classify) fills them.
- Stub ranking is not semantic; filters still apply.
