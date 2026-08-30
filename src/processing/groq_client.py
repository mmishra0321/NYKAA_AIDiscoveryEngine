"""Groq chat client for Phase 2 classify / name calls."""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

import httpx

from src.config_loader import load_prompts

logger = logging.getLogger(__name__)


def groq_api_key() -> str:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    return (os.getenv("GROQ_API_KEY") or "").strip()


class GroqClient:
    def __init__(self, *, api_key: Optional[str] = None) -> None:
        cfg = load_prompts()
        self.base_url = str(cfg.get("base_url") or "https://api.groq.com/openai/v1")
        self.model = str(cfg.get("model") or "llama-3.3-70b-versatile")
        self.timeout = float(cfg.get("timeout_seconds") or 60)
        self.max_retries = int(cfg.get("max_retries") or 1)
        self.api_key = api_key if api_key is not None else groq_api_key()

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.1,
    ) -> str:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not set")
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        last_error: Exception | None = None
        attempts = self.max_retries + 1
        for attempt in range(attempts):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                content = (
                    (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
                )
                if not content:
                    raise ValueError("Empty Groq response")
                return str(content).strip()
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning("Groq attempt %s/%s failed: %s", attempt + 1, attempts, exc)
                if attempt + 1 < attempts:
                    time.sleep(1.2 * (attempt + 1))
        raise RuntimeError(f"Groq request failed: {last_error}")
