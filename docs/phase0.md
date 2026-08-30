# Phase 0 — Foundations & Contracts

Status: **complete**

Phase 0 freezes schemas, source inventory, the 10-question catalog, LLM prompt contracts, Nykaa brand tokens, and the eval rubric **before** any scraper. Canonical brief: [problemStatement.md](../problemStatement.md). Plan: [architecture.md](../architecture.md).

## Deliverables

| Task | Artifact |
|---|---|
| 0.1 Repo skeleton | `config/`, `src/`, `data/`, `frontend/`, `tests/`, `.env.example`, `.gitignore` |
| 0.2 Source inventory | [`config/sources.yaml`](../config/sources.yaml) |
| 0.3 Constraints | [`config/constraints.yaml`](../config/constraints.yaml) |
| 0.4 Query catalog (10 Qs) | [`config/queries.yaml`](../config/queries.yaml) |
| 0.5 Document / chunk / sub-theme / catalog schemas | [`src/models/schemas.py`](../src/models/schemas.py), [schema.md](./schema.md) |
| 0.6 Prompts | [`config/prompts.yaml`](../config/prompts.yaml) |
| 0.7 Brand tokens | [`config/brand.yaml`](../config/brand.yaml) |
| 0.8 Eval rubric | [eval-rubric.md](./eval-rubric.md) |
| 0.9 Runnable baseline | `requirements.txt`, root `README.md` |

Supporting contracts (used from Phase 2+): `config/themes.yaml`, `processing.yaml`, `embedding.yaml`, `retrieval.yaml`.

## V1 source priority

1. **P0** — Play Store `com.fsn.nds`, App Store `1439872423`
2. **P1** — Reddit, ToS-safe forums, YouTube comments (API key)
3. **P2** — Nykaa Beauty Play xref (`com.fsn.nykaa`) for shared wishlist UX only
4. **Deferred** — Twitter/X, Quora, login walls

Relevant corpus target: **≥400** after the relevance gate; raw cap **600**.

## Self-check

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m src.phase0_check
pytest tests/phase0 -q
```

Q10 is `computed: true` and is **not** in `classifier_allowed_questions`.
