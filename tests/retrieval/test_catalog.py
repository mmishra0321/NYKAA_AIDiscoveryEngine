from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
import json

from src.config_loader import canonical_queries
from src.ingestion.document_factory import make_document
from src.indexing.pipeline import run_indexing
from src.models.schemas import (
    IntentLabel,
    ProductCategory,
    Relevance,
    SegmentHint,
    SourceKind,
    SourceType,
    SubTheme,
)
from src.processing.chunker import chunk_document
from src.retrieval.pipeline import run_catalog_retrieval


def _chunk(
    text: str,
    questions: list[str],
    *,
    source: SourceType = SourceType.PLAY_STORE,
    factors: list[str] | None = None,
    intent: IntentLabel = IntentLabel.UNCLEAR,
    segment: SegmentHint = SegmentHint.UNKNOWN,
    category: ProductCategory = ProductCategory.UNKNOWN,
    themes: list[str] | None = None,
):
    kind = SourceKind.COMMUNITY if source is SourceType.REDDIT else SourceKind.APP_REVIEW
    doc = make_document(
        source=source,
        raw_text=text,
        date=datetime.now(timezone.utc),
        source_type=kind,
        product_category=category,
        segment=segment,
    )
    doc = doc.model_copy(
        update={
            "research_questions": questions,
            "relevance": Relevance.WISHLIST_SIGNAL,
            "decision_factors": factors or [],
            "intent_label": intent,
            "sub_theme_ids": themes or [],
        }
    )
    return chunk_document(doc)[0], doc


def retrieval_corpus():
    pairs = [
        _chunk("Saved a festive kurta to style later against pieces I already own.", ["q1_wishlist_motive"]),
        _chunk(
            "Liked the dress but reviews say it runs small so it sits in my wishlist.",
            ["q2_conversion_blockers", "q3_uncertainties"],
        ),
        _chunk("Will decide after payday. Wishlist is how I remember the listing.", ["q4_postpone"]),
        _chunk(
            "Two black blazers saved. Comparing shoulder structure before I pick one.",
            ["q5_compare"],
            source=SourceType.REDDIT,
        ),
        _chunk(
            "I watch a YouTube haul of the same SKU before converting a wishlist item.",
            ["q6_off_platform"],
        ),
        _chunk(
            "Fit and size reviews decided it; occasion is a wedding sangeet.",
            ["q7_decision_factors"],
            factors=["fit", "size", "occasion"],
        ),
        _chunk(
            "Most of my Nykaa Fashion wishlist is a moodboard. Not really planning to buy.",
            ["q8_intent_vs_bookmark"],
            intent=IntentLabel.BOOKMARK,
        ),
        _chunk(
            "First time ordering. I wishlist everything because I do not know ethnic sizes.",
            ["q9_segments"],
            segment=SegmentHint.FIRST_TIME,
            category=ProductCategory.ETHNIC,
        ),
        _chunk(
            "Repeat buyer: western dresses stay in my wishlist until the fit is obvious.",
            ["q9_segments"],
            segment=SegmentHint.REPEAT,
            category=ProductCategory.WESTERN,
            source=SourceType.APP_STORE,
        ),
        _chunk(
            "Sizing runs small on saved items across Play, App, and Reddit.",
            ["q3_uncertainties", "q10_unmet_needs"],
            source=SourceType.REDDIT,
            themes=["q10_unmet_needs_sizing_runs_small"],
        ),
    ]
    chunks = [p[0] for p in pairs]
    docs = [p[1] for p in pairs]
    q10 = SubTheme(
        sub_theme_id="q10_unmet_needs_sizing_runs_small",
        question_id="q10_unmet_needs",
        name="Sizing runs small",
        source_diversity=3,
        sources=["play_store", "app_store", "reddit"],
        chunk_ids=[chunks[-1].chunk_id],
    )
    return chunks, docs, [q10]


def test_catalog_retrieval_writes_packs_and_respects_filters(tmp_path, monkeypatch):
    from src.indexing import storage as idx_store
    from src.retrieval import storage as ret_store

    monkeypatch.setattr(idx_store, "INDEX_DIR", tmp_path / "index")
    monkeypatch.setattr(ret_store, "RETRIEVAL_DIR", tmp_path / "retrieval")
    chunks, docs, themes = retrieval_corpus()
    chroma = tmp_path / "chroma"
    run_indexing(
        chunks=chunks,
        documents=docs,
        stub=True,
        persist_directory=chroma,
        run_date=date(2026, 8, 30),
        skip_smoke=True,
    )
    summary = run_catalog_retrieval(
        stub=True,
        persist_directory=chroma,
        run_date=date(2026, 8, 30),
        themes=themes,
    )
    assert summary["questions"] == 10
    assert summary["with_hits"] >= 8
    assert "q10_unmet_needs" not in summary["data_gaps"]
    out = Path(summary["output_dir"])
    for q in canonical_queries():
        path = out / f"{q['id']}.json"
        assert path.exists()
    q1 = (out / "q1_wishlist_motive.json").read_text(encoding="utf-8")
    assert "q1_wishlist_motive" in q1
    q7 = json.loads((out / "q7_decision_factors.json").read_text(encoding="utf-8"))
    assert q7["strategy"] == "q7_factors"
    assert q7["hits"][0]["decision_factors"]
    q8 = json.loads((out / "q8_intent_vs_bookmark.json").read_text(encoding="utf-8"))
    assert q8["hits"][0]["intent_label"] == "bookmark"
    q9 = json.loads((out / "q9_segments.json").read_text(encoding="utf-8"))
    assert q9["strategy"] == "q9_strata"
    assert len(q9.get("strata") or {}) >= 2
    q10 = json.loads((out / "q10_unmet_needs.json").read_text(encoding="utf-8"))
    assert q10["flag"] is None
    assert q10["hit_count"] >= 1


def test_q10_is_data_gap_without_diverse_themes(tmp_path, monkeypatch):
    from src.indexing import storage as idx_store
    from src.retrieval import storage as ret_store

    monkeypatch.setattr(idx_store, "INDEX_DIR", tmp_path / "index")
    monkeypatch.setattr(ret_store, "RETRIEVAL_DIR", tmp_path / "retrieval")
    chunks, docs, _themes = retrieval_corpus()
    chroma = tmp_path / "chroma"
    run_indexing(
        chunks=chunks,
        documents=docs,
        stub=True,
        persist_directory=chroma,
        run_date=date(2026, 8, 30),
        skip_smoke=True,
    )
    summary = run_catalog_retrieval(
        stub=True,
        persist_directory=chroma,
        run_date=date(2026, 8, 30),
        themes=[],
        query_ids=["q10_unmet_needs"],
    )
    assert summary["data_gaps"] == ["q10_unmet_needs"]
    pack = json.loads(
        (Path(summary["output_dir"]) / "q10_unmet_needs.json").read_text(encoding="utf-8")
    )
    assert pack["flag"] == "data_gap"
    assert pack["hit_count"] == 0
