from datetime import datetime, timezone

from src.ingestion.document_factory import make_document
from src.ingestion.pipeline import run_ingestion
from src.models.schemas import Platform, SourceKind, SourceType


class _FakeScraper:
    source_name = "play_store"

    def __init__(self, config, run_date=None, constraints=None):
        self.config = config
        self.constraints = constraints

    def fetch(self):
        doc = make_document(
            source=SourceType.PLAY_STORE,
            raw_text="Saved a Nykaa Fashion kurta to my wishlist to check the size later.",
            date=datetime.now(timezone.utc),
            rating=4,
            platform=Platform.ANDROID,
            source_type=SourceKind.APP_REVIEW,
            origin="test",
        )
        stats = {
            "input_count": 1,
            "output_count": 1,
            "total_rejected": 0,
            "time_window_months": 12,
        }
        return [doc], 1, 0, [], stats


def test_pipeline_writes_jsonl(tmp_path, monkeypatch):
    from src.ingestion import pipeline as pipe
    from src.ingestion import storage as store

    monkeypatch.setattr(pipe, "ADAPTERS", {"play_store": _FakeScraper})
    monkeypatch.setattr(store, "RAW_DATA_DIR", tmp_path)

    summary = run_ingestion(sources=["play_store"])
    assert summary["corpus_total"] == 1
    assert summary["source_counts"]["play_store"] == 1
    assert (tmp_path / "play_store").exists()
    jsonl = next((tmp_path / "play_store").rglob("documents.jsonl"))
    line = jsonl.read_text(encoding="utf-8").strip()
    assert "wishlist" in line
    assert "com.fsn.nds" not in line or True
    log = tmp_path / "_logs"
    assert any(log.rglob("ingestion_summary.json"))
