"""Local embeddings: MiniLM L6 v2 (384-d cosine) or deterministic stub for tests."""

from __future__ import annotations

import hashlib
import logging
import math

from src.config_loader import load_embedding

logger = logging.getLogger(__name__)

_MINILM = None


def embedding_config() -> dict:
    return load_embedding()


def stub_vector(text: str, dim: int = 384) -> list[float]:
    digest = hashlib.sha256((text or "").encode("utf-8")).digest()
    raw: list[int] = []
    seed = digest
    while len(raw) < dim:
        raw.extend(seed)
        seed = hashlib.sha256(seed).digest()
    vals = [(b - 127.5) / 127.5 for b in raw[:dim]]
    norm = math.sqrt(sum(v * v for v in vals)) or 1.0
    return [v / norm for v in vals]


def try_minilm():
    global _MINILM
    if _MINILM is not None:
        return _MINILM
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None
    cfg = embedding_config()
    name = str(cfg.get("model_name") or "sentence-transformers/all-MiniLM-L6-v2")
    try:
        _MINILM = SentenceTransformer(name)
        return _MINILM
    except Exception as exc:  # noqa: BLE001
        logger.warning("MiniLM load failed: %s", exc)
        return None


class Embedder:
    def __init__(self, *, stub: bool = False) -> None:
        cfg = embedding_config()
        self.dim = int(cfg.get("embedding_dim") or 384)
        self.model_name = str(cfg.get("model_name") or "sentence-transformers/all-MiniLM-L6-v2")
        self.batch_size = int(cfg.get("batch_size") or 128)
        self.backend = "stub"
        self._model = None
        if not stub:
            self._model = try_minilm()
            if self._model is not None:
                self.backend = "minilm"
            else:
                logger.warning("sentence-transformers unavailable; using stub embeddings")

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.backend == "minilm" and self._model is not None:
            vectors = self._model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            return [list(map(float, row)) for row in vectors]
        return [stub_vector(t, self.dim) for t in texts]
