from src.config_loader import canonical_queries, classifier_question_ids
from src.eval.gold import load_answer_review, load_classify_gold, load_paraphrases, load_relevance_gold
from src.eval.metrics import jaccard, percentile, precision_binary, review_score
from src.processing.classify import heuristic_classify
from src.processing.relevance import heuristic_relevance


def test_jaccard_identity_and_empty():
    assert jaccard(["q1"], ["q1"]) == 1.0
    assert jaccard([], []) == 1.0
    assert jaccard(["q1", "q2"], ["q1"]) == 0.5


def test_precision_and_percentile():
    assert precision_binary(["wishlist_signal", "logistics_noise"], ["wishlist_signal", "wishlist_signal"], positive="wishlist_signal") == 0.5
    assert percentile([1, 2, 3, 4, 5], 100) == 5
    assert percentile([1.0, 2.0], 50) == 1.5


def test_gold_set_sizes_and_no_q10():
    rel = load_relevance_gold()
    assert len(rel) == 20
    assert sum(1 for r in rel if r["relevance"] == "wishlist_signal") == 10
    assert sum(1 for r in rel if r["relevance"] == "logistics_noise") == 10
    clf = load_classify_gold()
    assert len(clf) == 40
    allowed = set(classifier_question_ids())
    for row in clf:
        assert "q10_unmet_needs" not in row["research_questions"]
        assert set(row["research_questions"]) <= allowed
    paras = load_paraphrases()
    assert len(paras) == 20
    assert {p["query_id"] for p in paras} == {q["id"] for q in canonical_queries()}
    reviews = load_answer_review()
    assert len(reviews) == 10
    assert all(review_score(r) >= 3 for r in reviews)


def test_stub_relevance_precision_meets_target():
    gold = load_relevance_gold()
    y_true = [r["relevance"] for r in gold]
    y_pred = [heuristic_relevance(r["text"]).value for r in gold]
    assert precision_binary(y_true, y_pred, positive="wishlist_signal") >= 0.85


def test_stub_classify_jaccard_meets_target():
    gold = load_classify_gold()
    scores = [
        jaccard(heuristic_classify(r["text"])["research_questions"], r["research_questions"])
        for r in gold
    ]
    assert sum(scores) / len(scores) >= 0.75
