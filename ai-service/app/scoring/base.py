"""Scoring sağlayıcısı için soyutlama. Model değiştirilebilir olmalı."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

import numpy as np


class ScoringModel(ABC):
    """Bir feature vektörü → (skor, güven) döner. Skor 0..1."""
    name: str
    version: str

    @abstractmethod
    def predict(self, x: np.ndarray) -> tuple[float, float]: ...

    @abstractmethod
    def partial_fit(self, X: np.ndarray, y: np.ndarray) -> None: ...

    @abstractmethod
    def save(self, path: str) -> None: ...

    @classmethod
    @abstractmethod
    def load(cls, path: str) -> "ScoringModel": ...
