# Phase 2 — Relevance, classify, cluster, quantify

Status: **complete** (`--stub` heuristics for CI; Groq when `GROQ_API_KEY` is set)

Raw Nykaa Fashion JSONL → relevance gate → Q1–Q9 labels → per-question clusters → named sub-themes → Q10 from 3+ source overlap → impact rank.

## Pipeline

1. Clean HTML + PII (again).
2. Relevance: `wishlist_signal` | `logistics_noise` | `other`. Noise is counted, not mixed into Q1–Q10.
3. Groq (or stub) multi-label **q1–q9**. **Never assigns q10.**
4. Segment / category / decision_factors / intent on the same classify JSON.
5. Cluster per question (MiniLM if installed, else character n-grams). Leftovers → `{qN}_other`.
6. Name clusters (`{question_id}_{slug}`).
7. Q10: slugs that appear in ≥3 independent sources.
8. Score: `0.4 * share_norm + 0.3 * (diversity / N_sources) + 0.3 * severity_num`. Rank within each question.

## Run

```bash
source .venv/bin/activate
pip install -r requirements.txt
python -m src.processing --stub --verbose
python -m src.processing --run-date 2026-08-30
pytest tests/processing -q
```

`--stub` (or a missing Groq key) sets `mode: stub` in the summary. With a key, `mode: groq`.

## Outputs

`data/processed/{date}/`

| File | Contents |
|---|---|
| `documents.jsonl` | `wishlist_signal` docs with questions + sub-theme ids |
| `chunks.jsonl` | ~350-word windows, inherit taxonomy |
| `sub_themes.json` | Named, quantified, ranked themes including Q10 |
| `noise.jsonl` | logistics_noise + other |
| `noise_summary.json` | Counts by source |
| `processing_summary.json` | Mode, coverage, `data_gap`, pii_hits |

Copies of the two summaries also go to `data/processed/_logs/{date}/`.

## Known limitations

- Stub classification is keyword recall, not the production taxonomy.
- MiniLM clustering needs `sentence-transformers`; otherwise n-gram cosine.
- Sparse buckets (Q5/Q6/Q8) may only have leftover `Other` or an explicit `data_gap`.
- Q10 needs ≥3 independent sources; Play+App alone cannot satisfy it.
