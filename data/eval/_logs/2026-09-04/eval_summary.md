# Phase 7 — Validation

Generated 2026-09-04T14:59:09+00:00 · mode **stub** · catalog `data/responses/2026-09-04`

| Metric | Value | Target | Pass |
|---|---|---|---|
| Relevance precision (signal) | 1.0 | 0.85 | yes |
| Q-classification Jaccard | 0.9917 | 0.75 | yes |
| Citation accuracy | 1.0 | 0.9 | yes |
| Question coverage 10/10 | True | 10/10 sections or explicit data_gap | yes |
| Answer faithfulness pass rate | 1.0 | 0.85 | yes |
| Latency p95 /api/v1/ask | 0.0046 | 5.0 | yes |
| Monetary-incentive lint hits | 0 | 0 | yes |
| Public URL | None | public URL third party can open + export | no |

## Limitations

- Play reviews are delivery-dominated; relevance gold treats those as logistics_noise, not Q1–Q10.
- Hinglish rows are in the gold set; stub keywords are English-leaning.
- Sparse / gap questions in this catalog: none.
- Architecture called out sparse Q5/Q6/Q8; this Play+App run gaps Q2/Q6/Q8/Q10 (Q5 had hits but leftover Other names).
- No YOUTUBE_API_KEY — haul comments deferred.
- Twitter/X, Quora, Trustpilot/MouthShut HTML are deferred V1.
- Relevant corpus after gate is 732 (target ≥ 400).
- Stub leftover cluster name Other is weak for Part 3; Groq naming needs a larger signal set.
- Q10 needs ≥3 independent sources; Play-only cannot populate it.
- Public live link is not created without Render/Vercel accounts.

## Answer review (3/4 pass)

- `q1_wishlist_motive` score 3/4 · pass
- `q2_conversion_blockers` score 3/4 · pass
- `q3_uncertainties` score 3/4 · pass
- `q4_postpone` score 3/4 · pass
- `q5_compare` score 3/4 · pass
- `q6_off_platform` score 3/4 · pass
- `q7_decision_factors` score 3/4 · pass
- `q8_intent_vs_bookmark` score 3/4 · pass
- `q9_segments` score 3/4 · pass
- `q10_unmet_needs` score 3/4 · pass
