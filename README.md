# Nykaa Fashion — Wishlist Discovery Engine

Growth capstone, deliverable 1 of 3.

| Doc | Role |
|---|---|
| [problemStatement.md](./problemStatement.md) | Product brief |
| [architecture.md](./architecture.md) | Phase-wise plan |
| [docs/phase0.md](./docs/phase0.md) | Contracts |
| [docs/phase1.md](./docs/phase1.md) | Ingestion |
| [docs/phase2.md](./docs/phase2.md) | Relevance, classify, cluster |
| [docs/phase3.md](./docs/phase3.md) | Embed + Chroma index |
| [docs/phase4.md](./docs/phase4.md) | Retrieval packs |
| [docs/phase5.md](./docs/phase5.md) | Catalog JSON + Markdown |
| [docs/phase6.md](./docs/phase6.md) | Nykaa UI + FastAPI live link |
| [docs/phase7.md](./docs/phase7.md) | Gold labels + validation |

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Phase 0

```bash
python3 -m src.phase0_check
pytest tests/phase0 -q
```

## Phase 1

```bash
python -m src.ingestion --verbose
python -m src.ingestion --sources play_store app_store
pytest tests/ingestion -q
```

**Limitations:** forum HTML, YouTube (no key), Twitter/X, and Quora are deferred. Keyword prefilter is recall-only; LLM relevance is Phase 2.

Weekly scrape: GitHub Action `Ingest Classify Index Nykaa Fashion` (Monday 06:00 UTC). Enable Actions, add optional `GROQ_API_KEY`, then **Run workflow** once. See [docs/phase1.md](./docs/phase1.md).

## Phase 2

```bash
python -m src.processing --stub --verbose
python -m src.processing --run-date 2026-08-30
pytest tests/processing -q
```

Writes `data/processed/{date}/` (`documents.jsonl`, `chunks.jsonl`, `sub_themes.json`, noise + summaries). `mode` is `stub` without `GROQ_API_KEY` (or with `--stub`); `groq` when a key is set.

## Phase 3

```bash
python -m src.indexing --stub --verbose
python -m src.indexing --run-date 2026-08-30
pytest tests/indexing -q
```

Writes `data/chroma/` (collection `nykaa_fashion_wishlist_v1`) and `data/index/{date}/indexing_summary.json`. Smoke queries all 10 catalog questions (fail if ≥8/10 empty).

## Phase 4

```bash
python -m src.retrieval --catalog --stub --verbose
python -m src.retrieval --catalog --run-date 2026-08-30
pytest tests/retrieval -q
```

Writes `data/retrieval/{date}/{query_id}.json`. Empty questions are flagged `data_gap`. Source mix capped at ~60% when more than one source is available.

## Phase 5

```bash
python -m src.generation --stub --verbose
python -m src.generation --run-date 2026-08-30
pytest tests/generation -q
```

Writes `data/responses/{date}/catalog_summary.json` + `.md` and per-question JSON. Groq is used when `GROQ_API_KEY` is set; `--stub` builds from packs + sub-themes. Output is linted so implications never recommend coupons/discounts/cashback/price-cuts.

## Phase 6

```bash
source .venv/bin/activate
python -m src.api
# other terminal:
cd frontend && npm install && npm run dev
pytest tests/api -q
```

UI: [http://127.0.0.1:5173](http://127.0.0.1:5173). API: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). Vite proxies `/api` → FastAPI. Export downloads Q1–Q10 Markdown.

Deploy: FastAPI on Render (`Dockerfile`, `render.yaml`), React on Vercel (`frontend/`, `VITE_API_BASE_URL`). Steps in [docs/phase6.md](./docs/phase6.md).

## Phase 7

```bash
python -m src.eval --stub --verbose
pytest tests/eval -q
```

Gold: 20 relevance labels, 40 classify rows (Q1–Q9), 10×2 paraphrases, 10 answer reviews. Report: `data/eval/{date}/eval_summary.md`. Notes: Hinglish, delivery-dominated Play reviews, gaps on Q2/Q6/Q8/Q10, no YouTube key, deferred X/Quora. Public URL still needs your Render/Vercel deploy.
