# Phase 5 — Catalog generation

Status: **complete** (Groq when `GROQ_API_KEY` is set; `--stub` from retrieval packs + sub-theme rollup)

Top 10 classified chunks + Phase 2 sub-theme stats → one quantified section per Q1–Q10 (or an explicit `data_gap`). User-facing examples are paraphrased. Implications are linted so they never recommend coupons, discounts, cashback, or price-cuts.

## Run

```bash
source .venv/bin/activate
python -m src.generation --stub --verbose
python -m src.generation --run-date 2026-08-30
pytest tests/generation -q
```

`--stub` (or a missing Groq key) builds the catalog without Groq. With a key, Groq writes prose; parse/lint failure retries once, then falls back to the stub.

## Outputs

`data/responses/{date}/`

| File | Contents |
|---|---|
| `catalog_summary.json` | Full `CatalogReport` (KPI `wishlist_to_purchase_30d`) |
| `catalog_summary.md` | Interview-guide Markdown for Parts 2–3 |
| `{query_id}.json` | Per-question section |
| `generation_summary.json` | Mode, coverage, lint counts |

## Lint

Rejects coupons / discounts / cashback / price-cuts / `% off` as the *mechanism*. Price as a decision factor is allowed.

## Known limitations

- Sparse retrieval packs (Q2/Q6/Q8/Q10 on Play+App-only) become explicit `data_gap` sections — still 10/10 coverage.
- Stub prose is template-based; Groq names the same stats in richer language.
