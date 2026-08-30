from datetime import date, datetime, timezone

from src.config_loader import canonical_queries
from src.ingestion.document_factory import make_document
from src.indexing.pipeline import run_indexing
from src.indexing.smoke import SMOKE_FAIL_IF_EMPTY_GE, smoke_catalog
from src.indexing.store import VectorIndex
from src.models.schemas import Relevance, SourceKind, SourceType
from src.processing.chunker import chunk_document


def _labeled_chunk(text: str, questions: list[str], source: SourceType = SourceType.PLAY_STORE):
    kind = SourceKind.COMMUNITY if source is SourceType.REDDIT else SourceKind.APP_REVIEW
    doc = make_document(
        source=source,
        raw_text=text,
        date=datetime.now(timezone.utc),
        source_type=kind,
    )
    doc = doc.model_copy(
        update={"research_questions": questions, "relevance": Relevance.WISHLIST_SIGNAL}
    )
    return chunk_document(doc)[0], doc


def catalog_chunks():
    pairs = [
        ("Saved a festive kurta to style later against pieces I already own.", ["q1_wishlist_motive"]),
        ("Liked the dress but reviews say it runs small so it sits in my wishlist.", ["q2_conversion_blockers", "q3_uncertainties"]),
        ("Will decide after payday. Wishlist is how I remember the listing.", ["q4_postpone"]),
        ("Two black blazers saved. Comparing shoulder structure before I pick one.", ["q5_compare"]),
        ("I watch a YouTube haul of the same SKU before converting a wishlist item.", ["q6_off_platform"]),
        ("Fit and reviews decided it; occasion is a wedding sangeet.", ["q7_decision_factors"]),
        ("Most of my Nykaa Fashion wishlist is a moodboard. Not really planning to buy.", ["q8_intent_vs_bookmark"]),
        ("First time ordering. I wishlist everything because I do not know ethnic sizes.", ["q9_segments"]),
        (
            "Sizing runs small on saved items across Play, App, and Reddit.",
            ["q3_uncertainties", "q10_unmet_needs"],
            SourceType.REDDIT,
        ),
    ]
    chunks = []
    docs = []
    for row in pairs:
        text, questions = row[0], row[1]
        source = row[2] if len(row) > 2 else SourceType.PLAY_STORE
        chunk, doc = _labeled_chunk(text, questions, source)
        chunks.append(chunk)
        docs.append(doc)
    return chunks, docs


def test_upsert_is_idempotent_by_chunk_id(tmp_path):
    chunk, doc = _labeled_chunk("Saved a kurta to my wishlist to check the size later.", ["q1_wishlist_motive"])
    index = VectorIndex(persist_directory=tmp_path / "chroma")
    from src.indexing.embedder import Embedder
    from src.indexing.metadata import chunk_metadata

    emb = Embedder(stub=True)
    vec = emb.encode([chunk.text])
    meta = [chunk_metadata(chunk, doc)]
    index.upsert(ids=[chunk.chunk_id], embeddings=vec, documents=[chunk.text], metadatas=meta)
    index.upsert(ids=[chunk.chunk_id], embeddings=vec, documents=[chunk.text], metadatas=meta)
    assert index.count() == 1


def test_smoke_passes_when_catalog_is_covered(tmp_path, monkeypatch):
    from src.indexing import storage as idx_store

    monkeypatch.setattr(idx_store, "INDEX_DIR", tmp_path / "index")
    chunks, docs = catalog_chunks()
    summary = run_indexing(
        chunks=chunks,
        documents=docs,
        stub=True,
        persist_directory=tmp_path / "chroma",
        run_date=date(2026, 8, 30),
    )
    assert summary["embedder"] == "stub"
    assert summary["collection"] == "nykaa_fashion_wishlist_v1"
    assert summary["chunks_upserted"] == len(chunks)
    assert summary["collection_count"] == len(chunks)
    assert summary["smoke"]["passed"] is True
    assert summary["smoke"]["empty_count"] < SMOKE_FAIL_IF_EMPTY_GE
    assert summary["pii_hits"] == 0
    assert (tmp_path / "index" / "2026-08-30" / "indexing_summary.json").exists()
    for q in canonical_queries():
        assert q["id"] in summary["smoke"]["hits"]


def test_smoke_fails_when_almost_all_empty(tmp_path):
    chunk, doc = _labeled_chunk("Saved one item to the wishlist as a bookmark.", ["q1_wishlist_motive"])
    from src.indexing.embedder import Embedder
    from src.indexing.metadata import chunk_metadata

    index = VectorIndex(persist_directory=tmp_path / "chroma")
    emb = Embedder(stub=True)
    index.upsert(
        ids=[chunk.chunk_id],
        embeddings=emb.encode([chunk.text]),
        documents=[chunk.text],
        metadatas=[chunk_metadata(chunk, doc)],
    )
    result = smoke_catalog(index)
    assert result["empty_count"] >= SMOKE_FAIL_IF_EMPTY_GE
    assert result["passed"] is False
    assert result["hits"]["q1_wishlist_motive"] >= 1
