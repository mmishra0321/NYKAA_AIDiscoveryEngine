from datetime import datetime, timezone

from src.ingestion.document_factory import make_document
from src.models.schemas import Relevance, SourceKind, SourceType
from src.processing.cluster import agglomerative_groups, cluster_and_score, infer_slug


def _doc(text: str, source: SourceType, questions: list[str]):
    doc = make_document(
        source=source,
        raw_text=text,
        date=datetime.now(timezone.utc),
        source_type=SourceKind.APP_REVIEW if source != SourceType.REDDIT else SourceKind.COMMUNITY,
    )
    return doc.model_copy(
        update={"relevance": Relevance.WISHLIST_SIGNAL, "research_questions": questions}
    )


def test_identical_texts_cluster_together():
    texts = ["sizing runs small on saved kurta"] * 4
    kept, leftover = agglomerative_groups(texts, distance_threshold=0.35, min_cluster_size=3)
    assert leftover == []
    assert len(kept) == 1
    assert len(kept[0]) == 4


def test_infer_slug_sizing():
    slug, name, sev = infer_slug(["Reviews say this kurta sizing runs small so it sits in my wishlist."])
    assert slug == "sizing_runs_small"
    assert sev == "high"
    assert "Sizing" in name


def test_q10_requires_three_independent_sources():
    questions = ["q3_uncertainties"]
    docs = [
        _doc(
            "Reviews say this kurta sizing runs small so it sits in my Nykaa Fashion wishlist.",
            SourceType.PLAY_STORE,
            questions,
        ),
        _doc(
            "The size chart runs small and I saved the dress on Nykaa Fashion until I know.",
            SourceType.APP_STORE,
            questions,
        ),
        _doc(
            "Nykaa Fashion listing runs small according to reviews so I have not bought the saved item.",
            SourceType.REDDIT,
            questions,
        ),
    ]
    updated, themes, backend = cluster_and_score(docs, stub=True)
    assert backend == "ngram"
    q10 = [t for t in themes if t.question_id == "q10_unmet_needs"]
    assert q10, "expected a Q10 theme from 3-source sizing overlap"
    assert q10[0].source_diversity >= 3
    assert set(q10[0].sources) >= {"play_store", "app_store", "reddit"}
    assert any("q10_unmet_needs" in d.research_questions for d in updated)
    for theme in themes:
        for example in theme.paraphrased_examples:
            assert "Reviews say this kurta" not in example
