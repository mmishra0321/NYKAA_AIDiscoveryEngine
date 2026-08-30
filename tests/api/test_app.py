from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.ask import match_question
from src.api.store import get_catalog
from src.models.schemas import CatalogQuestion, CatalogReport, SubTheme


class _GroqOff:
    available = False

    def chat(self, *args, **kwargs):
        raise AssertionError("Groq must not be called in default API tests")


class _GroqOk:
    available = True

    def chat(self, messages, temperature=0.1):
        return (
            '{"answer": "Fit uncertainty is what stalls the save.", '
            '"implications": ["Surface size guidance when they return to wishlist."], '
            '"confidence": "medium", "data_gaps": ""}'
        )


class _GroqLint:
    available = True

    def chat(self, messages, temperature=0.1):
        return (
            '{"answer": "Give them a coupon and cashback.", '
            '"implications": ["Send a 20% off code."], '
            '"confidence": "high", "data_gaps": ""}'
        )


@pytest.fixture(autouse=True)
def _no_live_groq(monkeypatch):
    monkeypatch.setattr("src.api.ask.GroqClient", lambda *a, **k: _GroqOff())


@pytest.fixture
def client():
    from src.api.app import app

    return TestClient(app)


def test_health_sees_catalog(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    body = res.json()
    assert body["catalog"] is True
    assert body["questions"] == 10


def test_catalog_has_ten_questions(client):
    res = client.get("/api/v1/catalog")
    assert res.status_code == 200
    data = res.json()
    assert data["kpi"] == "wishlist_to_purchase_30d"
    assert len(data["questions"]) == 10


def test_themes_are_ranked(client):
    res = client.get("/api/v1/themes")
    assert res.status_code == 200
    themes = res.json()["themes"]
    assert themes
    scores = [t["impact_score"] for t in themes]
    assert scores == sorted(scores, reverse=True)


def test_insights_by_id(client):
    res = client.get("/api/v1/insights/q1_wishlist_motive")
    assert res.status_code == 200
    assert "wishlist" in res.json()["question"].lower()
    missing = client.get("/api/v1/insights/not_a_question")
    assert missing.status_code == 404


def test_pipeline_summary(client):
    res = client.get("/api/v1/pipeline/summary")
    assert res.status_code == 200
    ids = [s["id"] for s in res.json()["steps"]]
    assert ids == ["ingest", "relevance", "classify", "index", "retrieve", "catalog"]


def test_export_markdown(client):
    res = client.post("/api/v1/export", json={"format": "markdown"})
    assert res.status_code == 200
    assert "attachment" in res.headers.get("content-disposition", "")
    text = res.text
    assert "q1_wishlist_motive" in text
    assert "wishlist_to_purchase_30d" in text


def test_export_json(client):
    res = client.post("/api/v1/export", json={"format": "json"})
    assert res.status_code == 200
    assert res.json()["kpi"] == "wishlist_to_purchase_30d"


def test_ask_stub_when_groq_off(client):
    res = client.post("/api/v1/ask", json={"question": "Why do people add dresses to the wishlist?"})
    assert res.status_code == 200
    body = res.json()
    assert body["mode"] == "catalog"
    assert body["query_id"]
    assert body["answer"]


def test_ask_uses_groq_when_available(client, monkeypatch):
    monkeypatch.setattr("src.api.ask.GroqClient", lambda *a, **k: _GroqOk())
    res = client.post("/api/v1/ask", json={"question": "What is still uncertain after they like an item?"})
    assert res.status_code == 200
    body = res.json()
    assert body["mode"] == "groq"
    assert "Fit uncertainty" in body["answer"]


def test_ask_falls_back_when_groq_lints(client, monkeypatch):
    monkeypatch.setattr("src.api.ask.GroqClient", lambda *a, **k: _GroqLint())
    res = client.post("/api/v1/ask", json={"question": "Why add to wishlist?"})
    assert res.status_code == 200
    assert res.json()["mode"] == "catalog"
    assert "coupon" not in res.json()["answer"].lower()


def test_cors_localhost(client):
    res = client.get("/api/v1/health", headers={"Origin": "http://127.0.0.1:5173"})
    assert res.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"


def test_match_question_prefers_motive():
    report = CatalogReport(
        generated_at="2026-08-30T00:00:00+00:00",
        questions=[
            CatalogQuestion(
                id="q1_wishlist_motive",
                question="Why do users add fashion products to their wishlist?",
                summary="Save for later.",
                sub_themes=[
                    SubTheme(
                        sub_theme_id="t1",
                        question_id="q1_wishlist_motive",
                        name="Occasion later",
                    )
                ],
            ),
            CatalogQuestion(
                id="q7_decision_factors",
                question="Which decision factors matter after save?",
                summary="Fit and size.",
            ),
        ],
    )
    hit = match_question("why add to wishlist", report)
    assert hit.id == "q1_wishlist_motive"


def test_frontend_src_has_no_groq_secrets():
    root = Path("frontend/src")
    blob = "\n".join(p.read_text(encoding="utf-8") for p in root.rglob("*") if p.is_file())
    assert "GROQ" not in blob
    assert "gsk_" not in blob
    assert get_catalog().questions
