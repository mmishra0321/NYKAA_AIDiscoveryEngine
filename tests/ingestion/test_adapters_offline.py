"""Offline adapter smoke tests — no network."""

from src.ingestion.adapters.forum import ForumScraper
from src.ingestion.adapters.youtube import YouTubeScraper
from src.ingestion.constraints import ScrapeConstraints


def test_forum_is_deferred():
    forum = ForumScraper(config={"enabled": True}, constraints=ScrapeConstraints.load())
    docs, fetched, errors = forum.collect_candidates(12)
    assert docs == []
    assert fetched == 0
    assert errors
    assert "deferred" in errors[0].lower()


def test_youtube_skips_without_key(monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    yt = YouTubeScraper(config={"enabled": True}, constraints=ScrapeConstraints.load())
    docs, fetched, errors = yt.collect_candidates(12)
    assert docs == []
    assert fetched == 0
    assert "YOUTUBE_API_KEY" in errors[0]
