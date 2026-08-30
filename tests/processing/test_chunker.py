from src.processing.chunker import chunk_document, split_into_word_windows
from src.ingestion.document_factory import make_document
from src.models.schemas import SourceType
from datetime import datetime, timezone


def test_short_review_is_single_chunk():
    windows = split_into_word_windows("Saved a kurta to style later against pieces I own.")
    assert len(windows) == 1


def test_long_thread_windows_with_overlap():
    words = ["word"] * 400
    windows = split_into_word_windows(
        " ".join(words),
        target_words=350,
        overlap_words=50,
        short_doc_word_threshold=100,
    )
    assert len(windows) == 2
    assert len(windows[0].split()) == 350
    assert windows[1].split()[0] == "word"


def test_chunk_inherits_question_ids():
    doc = make_document(
        source=SourceType.PLAY_STORE,
        raw_text="Saved a festive kurta to my wishlist to check the size later.",
        date=datetime.now(timezone.utc),
    )
    doc = doc.model_copy(
        update={"research_questions": ["q1_wishlist_motive"], "sub_theme_ids": ["q1_wishlist_motive_styling_later"]}
    )
    chunks = chunk_document(doc)
    assert len(chunks) == 1
    assert chunks[0].research_questions == ["q1_wishlist_motive"]
    assert chunks[0].document_id == doc.id
