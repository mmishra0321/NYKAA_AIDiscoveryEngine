# Phase 6 — Live Nykaa UI

Status: **complete locally** (public URL needs your Render + Vercel accounts)

React + Vite + Tailwind in `frontend/`. FastAPI serves the cached catalog. Groq stays on the server; the browser never sees `GROQ_API_KEY`.

## Local

Terminal 1:

```bash
source .venv/bin/activate
pip install -r requirements-api.txt   # or requirements.txt
python -m src.api
```

Terminal 2:

```bash
cd frontend
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). Vite proxies `/api` → `:8000`.

```bash
pytest tests/api -q
```

## API

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/health` | Catalog present? |
| GET | `/api/v1/pipeline/summary` | Phase 1–5 run stats |
| GET | `/api/v1/catalog` | Full Q1–Q10 JSON |
| GET | `/api/v1/themes` | Flattened sub-themes by impact |
| GET | `/api/v1/insights/{query_id}` | One question |
| POST | `/api/v1/ask` | `{ "question": "..." }` — Groq if keyed, else catalog stub |
| POST | `/api/v1/export` | `{ "format": "markdown" \| "json" }` |

Ask answers are grounded on `catalog_summary.json` and linted so they cannot recommend coupons/discounts/cashback/price-cuts.

## Deploy (you run this)

Ship `data/responses/{date}/` in git so Render does not need MiniLM, Chroma, or a scrape.

1. **API (Render)** — New Web Service from this repo, Docker runtime (`Dockerfile` / `render.yaml`). Set `GROQ_API_KEY` (optional; Ask falls back to the catalog) and `FRONTEND_ORIGINS` to the Vercel origin. `ALLOW_VERCEL_ORIGINS=1` is already defaulted.
2. **UI (Vercel)** — Root directory `frontend`. Build `npm run build`, output `dist`. Set `VITE_API_BASE_URL` to the Render URL (no trailing slash), e.g. `https://nykaa-fashion-wishlist-api.onrender.com`.
3. Paste the Vercel URL into the Phase 6 exit checkbox in [architecture.md](../architecture.md).

## Brand

`#FC2779` italic-caps **NYKAA**, peach→pink promo bar, listing grey canvas. Not Blinkit (no dark green/yellow, no bolt).

## Known limitations

- Public URL is not created in this repo — Render/Vercel need your login.
- Slim API image (`requirements-api.txt`) serves the catalog only; it does not re-run ingest/index.
- Sparse Q2/Q6/Q8/Q10 in the stub corpus show as explicit `data_gap` sections.
