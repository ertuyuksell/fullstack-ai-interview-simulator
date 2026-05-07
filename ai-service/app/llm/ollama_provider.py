"""Ollama (local LLM) sağlayıcısı. Hem hızlı hem ücretsiz."""
from __future__ import annotations

import logging
import os
from typing import Optional

import httpx

from .base import LLMProvider

log = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")  # küçük ve hızlı

    async def complete(self, system: str, user: str,
                       max_tokens: int = 256, temperature: float = 0.8) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": temperature,
                        },
                    },
                )
                r.raise_for_status()
                data = r.json()
                return data.get("message", {}).get("content")
        except Exception as e:
            log.warning("ollama complete failed: %s", e)
            return None

    async def healthy(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False
