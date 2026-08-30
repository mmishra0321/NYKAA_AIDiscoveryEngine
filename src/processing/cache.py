"""In-memory / disk cache keyed by content_hash (Groq cost control)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


class HashCache:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path
        self._data: dict[str, Any] = {}
        if path is not None and path.exists():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    self._data = loaded
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def _key(self, kind: str, content_hash: str) -> str:
        return f"{kind}:{content_hash}"

    def get(self, kind: str, content_hash: str) -> Any | None:
        return self._data.get(self._key(kind, content_hash))

    def set(self, kind: str, content_hash: str, value: Any) -> None:
        self._data[self._key(kind, content_hash)] = value

    def save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
