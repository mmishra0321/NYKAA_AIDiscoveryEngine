# Evaluation rubric (Phase 7)

Validates insight quality for the **10** Nykaa Fashion wishlist research questions.

Harness: `python -m src.eval`. Latest write-up: [phase7.md](./phase7.md). Gold lives in `data/eval/gold/`.

## Metrics

| Metric | Target | How measured |
|---|---|---|
| Relevance precision | ≥ 0.85 | Human labels: wishlist_signal vs logistics_noise |
| Q-classification Jaccard | ≥ 0.75 | Multi-label gold set (~40 rows, q1–q9 only) |
| Citation accuracy | ≥ 90% | Claim maps to a real `chunk_id` |
| Answer faithfulness | ≥ 0.85 | Manual audit |
| Question coverage | **10 / 10** | Catalog has a quantified section or explicit `data_gap` |
| Monetary-incentive lint | 0 hits | Generated implications never recommend coupons/discounts/cashback/price-cuts |
| Latency p95 | < 5s | End-to-end `/api/v1` query (cached catalog instant) |
| Relevant corpus | ≥ 400 | After relevance gate |

## Scoring guide (manual)

For each sample answer:

1. **Relevant evidence?** (0/1) — chunks address wishlist / purchase hesitation, not delivery-only
2. **Cited / paraphrased correctly?** (0/1) — no verbatim PII dump; claims match chunks
3. **No hallucination?** (0/1) — no invented stats or competitor scope
4. **Actionable without discounts?** (0/1) — implication is friction, doubt, or forgetting

Pass a query if score ≥ 3/4.

## Golden set (minimum)

- 10 canonical questions × 2 paraphrases = 20 retrieval judgments
- 20 relevance labels (10 noise / 10 signal)
- 10 generated answers reviewed once for citations, paraphrase, and discount-ban

Artifacts land in `data/eval/` during Phase 7.
