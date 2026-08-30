from datetime import datetime, timezone

from src.ingestion.document_factory import make_document
from src.indexing.embedder import Embedder, stub_vector
from src.indexing.metadata import chunk_metadata
from src.models.schemas import Relevance, SourceType
from src.processing.chunker import chunk_document


def _chunk(text: str, questions: list[str]):
    doc = make_document(
        source=SourceType.PLAY_STORE,
        raw_text=text,
        date=datetime.now(timezone.utc),
    )
    doc = doc.model_copy(
        update={
            "research_questions": questions,
            "relevance": Relevance.WISHLIST_SIGNAL,
            "decision_factors": ["size"] if "q3_uncertainties" in questions else [],
        }
    )
    return chunk_document(doc)[0], doc


def test_stub_vector_is_384d_unit():
    vec = stub_vector("wishlist size doubt", 384)
    assert len(vec) == 384
    assert abs(sum(v * v for v in vec) - 1.0) < 1e-6
    assert stub_vector("wishlist size doubt", 384) == vec
    assert stub_vector("other text", 384) != vec


def test_embedder_stub_backend():
    emb = Embedder(stub=True)
    assert emb.backend == "stub"
    out = emb.encode(["a", "b"])
    assert len(out) == 2
    assert len(out[0]) == 384


def test_chunk_metadata_flags_and_no_lists():
    chunk, doc = _chunk("Saved a kurta; sizing runs small so it sits in my wishlist.", ["q3_uncertainties"])
    meta = chunk_metadata(chunk, doc)
    assert meta["has_q3_uncertainties"] is True
    assert meta["has_q10_unmet_needs"] is False
    assert meta["relevance"] == "wishlist_signal"
    assert isinstance(meta["research_questions"], str)
    assert "q3_uncertainties" in meta["research_questions"]
    assert not any(isinstance(v, list) for v in meta.values())
