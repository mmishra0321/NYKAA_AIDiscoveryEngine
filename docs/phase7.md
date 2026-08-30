# Phase 7 — Validation

Status: **complete** (stub gold scores; public URL still needs your Render/Vercel deploy)

Labeled sample + catalog checks against [eval-rubric.md](./eval-rubric.md). Artifacts: `data/eval/gold/` and `data/eval/2026-08-30/`.

## Run

```bash
source .venv/bin/activate
python -m src.eval --stub --verbose
python -m src.eval --groq --run-date 2026-08-30
pytest tests/eval -q
```

Default is `--stub` (no Groq). `--groq` scores the live classifier when `GROQ_API_KEY` is set.

## Gold

| File | Size | Role |
|---|---|---|
| `data/eval/gold/relevance.json` | 10 signal / 10 logistics | Precision on wishlist vs delivery noise (includes Hinglish + Play-style refund/OTP) |
| `data/eval/gold/classify.json` | 40 rows, Q1–Q9 only | Multi-label Jaccard; **never** gold-assigns Q10 |
| `config/queries.yaml` paraphrases | 10 × 2 | Retrieval/Ask routing |
| `data/eval/gold/answer_review.json` | 10 sections | Manual 4-point scores (≥3/4 pass) |

## 2026-08-30 stub run

| Metric | Value | Target | Pass |
|---|---|---|---|
| Relevance precision (signal) | 1.00 | ≥ 0.85 | yes |
| Q-classification Jaccard | 1.00 | ≥ 0.75 | yes |
| Citation accuracy | 1.00 (28/28 chunk_ids) | ≥ 0.90 | yes |
| Question coverage | 10/10 (6 themes + 4 explicit gaps) | 10/10 | yes |
| Answer faithfulness pass rate | 1.00 (all 3/4) | ≥ 0.85 | yes |
| Latency p95 `/api/v1/ask` | ~3ms cached | < 5s | yes |
| Monetary-incentive lint | 0 hits | 0 | yes |
| Relevant corpus after gate | 13 | ≥ 400 | **no** |
| Public URL | not set | third party open + export | **no** |

Hard gates (precision, Jaccard, citations, coverage, lint, faithfulness, latency) pass. Corpus size and live URL do not — see limitations.

## Limitations (required notes)

- Play reviews are **delivery-dominated**; gold treats those as `logistics_noise`, not Q1–Q10.
- **Hinglish** is in the gold set; stub keywords are English-leaning.
- Sparse buckets: catalog gaps on **Q2, Q6, Q8, Q10**. Architecture called out Q5/Q6/Q8; this Play+App run had Q5 hits but leftover `Other` names.
- No `YOUTUBE_API_KEY` — haul comments skipped.
- Twitter/X, Quora, Trustpilot/MouthShut HTML are deferred V1.
- Q10 needs ≥3 independent sources; Play-only cannot fill it.
- Stub cluster name `Other` is weak for Part 3 interviews.
- Public URL: deploy steps in [phase6.md](./phase6.md). Set `PUBLIC_UI_URL` to mark the live-link gate after Vercel is up.
