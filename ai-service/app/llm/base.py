"""LLM sağlayıcısı için soyut arayüz."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def complete(self, system: str, user: str,
                       max_tokens: int = 256, temperature: float = 0.8) -> Optional[str]:
        """Bir tek-tur tamamlama döner. Sağlayıcı arızalıysa None dönmeli."""
        ...
