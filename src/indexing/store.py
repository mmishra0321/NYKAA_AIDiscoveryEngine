"""Chroma persistent collection `nykaa_fashion_wishlist_v1`."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional

from src.config_loader import ROOT, load_embedding

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

logger = logging.getLogger(__name__)


def chroma_settings():
    from chromadb.config import Settings

    return Settings(anonymized_telemetry=False, allow_reset=True)


def persist_path(override: Path | None = None) -> Path:
    if override is not None:
        return override
    cfg = load_embedding()
    rel = str(cfg.get("persist_directory") or "data/chroma")
    path = Path(rel)
    if not path.is_absolute():
        path = ROOT / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def collection_name() -> str:
    return str(load_embedding().get("collection_name") or "nykaa_fashion_wishlist_v1")


class VectorIndex:
    def __init__(
        self,
        *,
        persist_directory: Optional[Path] = None,
        name: Optional[str] = None,
        client: Any = None,
    ) -> None:
        self.name = name or collection_name()
        self.persist_directory = persist_path(persist_directory)
        if client is not None:
            self.client = client
        else:
            import chromadb

            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=chroma_settings(),
            )
        self.collection = self._get_or_create()

    def _get_or_create(self):
        meta = {"hnsw:space": "cosine"}
        try:
            return self.client.get_collection(self.name)
        except Exception:  # noqa: BLE001
            return self.client.create_collection(name=self.name, metadata=meta)

    def count(self) -> int:
        return int(self.collection.count())

    def upsert(
        self,
        *,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
        batch_size: int = 128,
    ) -> int:
        if not ids:
            return 0
        total = 0
        for start in range(0, len(ids), batch_size):
            end = start + batch_size
            slice_ids = ids[start:end]
            self.collection.upsert(
                ids=slice_ids,
                embeddings=embeddings[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )
            total += len(slice_ids)
        logger.info("Upserted %s chunks into %s", total, self.name)
        return total

    def get_where(self, where: dict[str, Any], *, limit: int = 10) -> dict[str, Any]:
        return self.collection.get(where=where, limit=limit, include=["metadatas", "documents"])

    def query(
        self,
        query_embeddings: list[list[float]],
        *,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "query_embeddings": query_embeddings,
            "n_results": n_results,
            "include": ["metadatas", "documents", "distances"],
        }
        if where:
            kwargs["where"] = where
        return self.collection.query(**kwargs)
