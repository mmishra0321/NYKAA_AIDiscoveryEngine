# Phase 1 — Multi-source ingestion

Status: **complete** (live Play + App adapters; Reddit live; forum/YouTube/X deferred)

Public Nykaa Fashion text → `data/raw/{source}/{date}/documents.jsonl`.

## Adapters

| Source | Status |
|---|---|
| Play Store `com.fsn.nds` | Live (`google-play-scraper`) |
| App Store `1439872423` | Live (iTunes RSS) |
| Reddit | Live (PullPush search, Nykaa-only) |
| Forum / Trustpilot / MouthShut | **Deferred** — no HTML scrape |
| YouTube | Skipped without `YOUTUBE_API_KEY` |
| Twitter / Quora / login | **Deferred** |

## Constraints (enforced)

Time window 12 months (24 fallback) → length → English → **keyword recall prefilter** → spam → competitor blocklist (drop unless Nykaa is also named) → PII strip → exact + near-dup → per-source cap.

LLM relevance / Q1–Q10 classify is **Phase 2**.

## Run

```bash
source .venv/bin/activate
pip install -r requirements.txt
python -m src.ingestion --verbose
python -m src.ingestion --sources play_store app_store
pytest tests/ingestion -q
```

Writes `data/raw/_logs/{date}/ingestion_summary.json` with fetched / kept / drop reasons.

## GitHub Actions (weekly scrape)

Scheduled **Monday 06:00 UTC** (`cron: 0 6 * * 1`) plus **Run workflow** in the Actions tab.

1. Repo → **Settings → Actions → General** → allow GitHub Actions (if it is off).
2. Optional: **Settings → Secrets and variables → Actions** → add `GROQ_API_KEY` (classify/generate use Groq; without it the job uses `--stub`).
3. **Actions → Ingest Classify Index Nykaa Fashion → Run workflow** once so the schedule is allowed to fire.

The job scrapes Play + App + Reddit, then stub-indexes and refreshes `data/responses/` (committed). Raw JSONL stays gitignored and is uploaded as a run artifact (14 days). To scrape daily instead, change the cron to `0 6 * * *`.

## Known limitations

- Keyword prefilter is recall-only; delivery-only reviews still appear until Phase 2.
- Forum HTML and X/Quora are out of V1.
- Live counts depend on store APIs and rate limits; CI tests are offline.
