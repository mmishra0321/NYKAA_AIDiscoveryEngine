from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from src.config_loader import canonical_queries
from src.generation.generate import generate_section
from src.generation.lint import lint_hits
from src.generation.pipeline import run_generation
from src.models.schemas import SubTheme


def _pack(qid: str, question: str, *, hits: int = 0, text: str = "") -> dict:
    items = []
    if hits:
        items = [
            {
                "chunk_id": f"c-{qid}",
                "text": text or "Every time I open the app to buy what I saved, it shows me ten new things instead.",
                "source": "play_store",
                "sub_theme_ids": [f"{qid}_other"],
            }
        ]
    return {
        "query_id": qid,
        "question": question,
        "flag": None if hits else "data_gap",
        "data_gap": None if hits else f"No indexed evidence for {qid}.",
        "hit_count": hits,
        "source_counts": {"play_store": hits} if hits else {},
        "hits": items,
    }


def test_stub_catalog_covers_ten_and_lints_clean(tmp_path, monkeypatch):
    from src.generation import storage as gen_store

    monkeypatch.setattr(gen_store, "RESPONSES_DIR", tmp_path / "responses")
    queries = canonical_queries()
    packs = []
    themes = []
    for q in queries:
        qid = q["id"]
        if qid in {"q1_wishlist_motive", "q3_uncertainties", "q7_decision_factors"}:
            packs.append(_pack(qid, q["question"], hits=3, text="verbatim dump should not appear in catalog"))
            themes.append(
                SubTheme(
                    sub_theme_id=f"{qid}_sizing_runs_small" if "q3" in qid else f"{qid}_styling_later",
                    question_id=qid,
                    name="Sizing runs small" if "q3" in qid else "Saving to style later",
                    share_of_bucket=0.31,
                    source_diversity=2,
                    sources=["play_store", "reddit"],
                    paraphrased_examples=["Users like a piece, then hesitate on fit after saving."],
                    hypothesis="Post-save doubt delays 30-day conversion.",
                    interview_probes=["What were you still unsure about after you saved it?"],
                )
            )
        else:
            packs.append(_pack(qid, q["question"], hits=0))

    summary = run_generation(
        packs=packs,
        themes=themes,
        stub=True,
        run_date=date(2026, 8, 30),
        corpus={"relevant": 13, "noise": 67, "sources": {"play_store": 13}},
    )
    assert summary["coverage_10_of_10"] is True
    assert summary["mode"] == "stub"
    assert summary["questions"] == 10
    out = Path(summary["output_dir"])
    md = (out / "catalog_summary.md").read_text(encoding="utf-8")
    report = json.loads((out / "catalog_summary.json").read_text(encoding="utf-8"))
    assert "verbatim dump should not appear in catalog" not in md
    assert lint_hits(md) == []
    assert report["kpi"] == "wishlist_to_purchase_30d"
    assert len(report["questions"]) == 10
    ids = [q["id"] for q in report["questions"]]
    assert ids[0] == "q1_wishlist_motive"
    assert ids[-1] == "q10_unmet_needs"
    q2 = json.loads((out / "q2_conversion_blockers.json").read_text(encoding="utf-8"))
    assert q2["data_gaps"]
    assert q2["confidence"] == "low"
    q3 = json.loads((out / "q3_uncertainties.json").read_text(encoding="utf-8"))
    assert q3["themes_count"] >= 1
    assert q3["sub_themes"][0]["share_of_bucket"] == 0.31
    assert "discount" not in json.dumps(q3).lower()
    assert "coupon" not in md.lower()


def test_groq_lint_falls_back_to_stub():
    query = canonical_queries()[0]
    pack = _pack(query["id"], query["question"], hits=2)
    theme = SubTheme(
        sub_theme_id="q1_wishlist_motive_styling_later",
        question_id="q1_wishlist_motive",
        name="Saving to style later",
        share_of_bucket=0.4,
        source_diversity=1,
        sources=["play_store"],
    )

    class _Fake:
        available = True

        def chat(self, messages, *, temperature=0.1):
            return json.dumps(
                {
                    "summary": "Send coupons so the wishlist converts.",
                    "implications": ["Offer a discount and cashback."],
                    "interview_probes": ["Would a price-cut help?"],
                    "confidence": "high",
                    "data_gaps": "",
                    "paraphrased_examples": ["Just use a promo code."],
                }
            )

    section, mode = generate_section(
        query=query,
        pack=pack,
        themes=[theme],
        stub=False,
        client=_Fake(),  # type: ignore[arg-type]
    )
    assert mode == "groq_fallback_stub"
    blob = json.dumps(section.model_dump(mode="json")).lower()
    assert "coupon" not in blob
    assert "discount" not in blob
    assert section.sub_themes
