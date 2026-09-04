from src.api.ask import match_question
from src.api.store import get_catalog
from src.eval.gold import load_paraphrases
from src.eval.pipeline import run_eval
from src.generation.lint import catalog_lint_text, lint_hits
from src.generation.pipeline import _coverage_ok


def test_paraphrases_route_to_canonical_questions():
    report = get_catalog()
    paras = load_paraphrases()
    hits = [match_question(p["paraphrase"], report)[0].id == p["query_id"] for p in paras]
    assert sum(hits) / len(hits) >= 0.8


def test_eval_pipeline_writes_and_passes_hard_gates(tmp_path, monkeypatch):
    from src.eval import storage as eval_store

    monkeypatch.setattr(eval_store, "EVAL_DIR", tmp_path / "eval")
    monkeypatch.setattr("src.api.ask.GroqClient", lambda *a, **k: type("Off", (), {"available": False, "chat": lambda *x, **y: (_ for _ in ()).throw(AssertionError("no groq"))})())
    summary = run_eval(stub=True, groq=False, run_date="2026-08-30")
    assert summary["hard_gates_pass"] is True
    assert (tmp_path / "eval" / "2026-08-30" / "eval_summary.json").exists()
    assert (tmp_path / "eval" / "2026-08-30" / "eval_summary.md").exists()
    metrics = summary["metrics"]
    assert metrics["coverage"]["pass"] is True
    assert metrics["lint"]["pass"] is True
    assert metrics["latency"]["p95_seconds"] < 5
    assert metrics["classify"]["q10_leaks"] == 0
    report = get_catalog()
    assert _coverage_ok(report.questions)
    for q in report.questions:
        assert not lint_hits(catalog_lint_text(q.model_dump(mode="json")))
