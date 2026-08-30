import json
from datetime import date, datetime, timezone
from pathlib import Path

from src.config_loader import classifier_question_ids
from src.ingestion.document_factory import make_document
from src.models.schemas import Platform, SourceKind, SourceType
from src.processing.loader import load_raw_documents
from src.processing.pipeline import run_processing


def _doc(text: str, source: SourceType = SourceType.PLAY_STORE):
    kind = SourceKind.COMMUNITY if source is SourceType.REDDIT else SourceKind.APP_REVIEW
    platform = Platform.ANDROID if source is SourceType.PLAY_STORE else Platform.UNKNOWN
    return make_document(
        source=source,
        raw_text=text,
        date=datetime.now(timezone.utc),
        source_type=kind,
        platform=platform,
        origin="test",
    )


def sample_corpus():
    return [
        _doc("Delivery was two days late and refund took a week. OTP failed once."),
        _doc("Courier never arrived and packaging was torn. Login crashed twice."),
        _doc("Nice app I shop here sometimes for random stuff on weekends."),
        _doc(
            "Saved a festive kurta to style later against pieces I already own. Not buying today. "
            "Email me at user@example.com"
        ),
        _doc("Liked the dress but reviews say it runs small so it sits in my wishlist."),
        _doc("Will decide after payday. Wishlist is how I remember the listing."),
        _doc("Two black blazers saved. Comparing shoulder structure before I pick one."),
        _doc("I watch a YouTube haul of the same SKU before converting a wishlist item."),
        _doc("Most of my Nykaa Fashion wishlist is a moodboard. Not really planning to buy."),
        _doc(
            "First time ordering. I wishlist everything because I do not know which ethnic sizes work."
        ),
        _doc(
            "Reviews say this kurta sizing runs small so it sits in my Nykaa Fashion wishlist.",
            SourceType.PLAY_STORE,
        ),
        _doc(
            "The size chart runs small and I saved the dress on Nykaa Fashion until I know.",
            SourceType.APP_STORE,
        ),
        _doc(
            "Nykaa Fashion listing runs small according to reviews so I have not bought the saved item.",
            SourceType.REDDIT,
        ),
        _doc("Fit looks unsure after I saved the heels so they stay on the wishlist."),
        _doc("Waiting until later this month; the saved ethnic set is for a wedding occasion."),
    ]


def test_pipeline_stub_writes_artifacts_and_meets_exit_gates(tmp_path, monkeypatch):
    from src.processing import storage as store

    monkeypatch.setattr(store, "PROCESSED_DIR", tmp_path)

    summary = run_processing(
        documents=sample_corpus(),
        stub=True,
        run_date=date(2026, 8, 30),
    )
    assert summary["mode"] == "stub"
    assert summary["majority_labeled"] is True
    assert summary["pii_hits"] == 0
    assert summary["relevance"]["logistics_noise"] >= 2
    assert summary["q10_themes"] >= 1

    for qid in classifier_question_ids():
        cov = summary["question_coverage"][qid]
        assert cov["sub_themes"] >= 1 or cov["data_gap"]

    q10 = summary["question_coverage"]["q10_unmet_needs"]
    assert q10["sub_themes"] >= 1
    assert q10["data_gap"] is None

    out = Path(summary["output_dir"])
    assert (out / "documents.jsonl").exists()
    assert (out / "chunks.jsonl").exists()
    assert (out / "sub_themes.json").exists()
    assert (out / "processing_summary.json").exists()
    assert (out / "noise_summary.json").exists()
    assert (out / "noise.jsonl").exists()

    docs = (out / "documents.jsonl").read_text(encoding="utf-8")
    assert "user@example.com" not in docs
    assert "wishlist_signal" in docs
    noise = (out / "noise.jsonl").read_text(encoding="utf-8")
    assert "OTP" in noise or "refund" in noise
    themes = json.loads((out / "sub_themes.json").read_text(encoding="utf-8"))
    assert any(t["question_id"] == "q10_unmet_needs" for t in themes)
    for theme in themes:
        for example in theme.get("paraphrased_examples") or []:
            assert "user@example.com" not in example


def test_loader_reads_jsonl(tmp_path, monkeypatch):
    from src.processing import loader as loadmod

    monkeypatch.setattr(loadmod, "RAW_DATA_DIR", tmp_path)
    day = "2026-08-30"
    path = tmp_path / "play_store" / day
    path.mkdir(parents=True)
    doc = _doc("Saved a Nykaa Fashion kurta to my wishlist to check the size later.")
    (path / "documents.jsonl").write_text(doc.model_dump_json() + "\n", encoding="utf-8")
    documents, resolved = load_raw_documents(run_date=day, sources=["play_store"])
    assert resolved == day
    assert len(documents) == 1
    assert documents[0].raw_text.startswith("Saved a Nykaa Fashion")
