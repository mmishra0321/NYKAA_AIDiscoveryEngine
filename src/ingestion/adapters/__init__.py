"""Source adapter registry."""

from src.ingestion.adapters.app_store import AppStoreScraper
from src.ingestion.adapters.forum import ForumScraper
from src.ingestion.adapters.play_store import PlayStoreScraper
from src.ingestion.adapters.reddit import RedditScraper
from src.ingestion.adapters.youtube import YouTubeScraper

ADAPTERS = {
    "play_store": PlayStoreScraper,
    "app_store": AppStoreScraper,
    "reddit": RedditScraper,
    "forum": ForumScraper,
    "youtube": YouTubeScraper,
}

__all__ = [
    "ADAPTERS",
    "AppStoreScraper",
    "ForumScraper",
    "PlayStoreScraper",
    "RedditScraper",
    "YouTubeScraper",
]
