"""
Online learning destekli skor modeli.

Mimari:
  • Bootstrap: ilk talep geldiğinde feature → skor için elle hazırlanmış
    sezgisel bir başlangıç regresyonu kullanılır (cold start). Bu sayede
    veri yokken bile mantıklı skor üretir.
  • Online: her gerçek cevap feature vektörü ve sezgisel bir hedef ile
    SGDRegressor'a partial_fit edilir. Kullanıcı verisi biriktikçe model
    rafine olur.
  • Persistence: joblib ile diske yazılır, container restart'ında okunur.

Hedef üretim politikası (`heuristic_target`) ayrıdır — modelin tek bir hedef
fonksiyonuna kilitlenmemesi için. Sonradan gerçek etiket (insan değerlendirmesi)
gelirse aynı arayüzden gönderebilirsin.
"""
from __future__ import annotations

import logging
import os
import threading
from typing import Optional

import joblib
import numpy as np
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler

from .base import ScoringModel

log = logging.getLogger(__name__)

FEATURE_DIM = 20  # Features dataclass'ındaki alan sayısı ile aynı olmalı


class OnlineScoringModel(ScoringModel):
    name = "online_scorer"
    version = "1.0.0"

    def __init__(self, kind: str = "quality"):
        self.kind = kind  # "quality" | "confidence"
        self._lock = threading.Lock()
        self._scaler = StandardScaler()
        self._scaler.partial_fit(np.zeros((1, FEATURE_DIM)))  # init shape
        self._model = SGDRegressor(
            loss="huber",
            penalty="l2",
            alpha=1e-4,
            learning_rate="adaptive",
            eta0=0.01,
            random_state=42,
            warm_start=True,
        )
        # Cold-start: küçük sentetik bir set ile bootstrap et
        X0, y0 = _bootstrap_dataset(kind)
        self._scaler.partial_fit(X0)
        Xs = self._scaler.transform(X0)
        self._model.partial_fit(Xs, y0)
        self._sample_count = len(X0)

    def predict(self, x: np.ndarray) -> tuple[float, float]:
        with self._lock:
            xs = self._scaler.transform(x.reshape(1, -1))
            raw = float(self._model.predict(xs)[0])
        score = float(np.clip(raw, 0.0, 1.0))
        # Güven: örnek sayısı arttıkça güven artar (basit log eğrisi)
        confidence = float(np.clip(np.log1p(self._sample_count) / np.log(500), 0.0, 1.0))
        return score, confidence

    def partial_fit(self, X: np.ndarray, y: np.ndarray) -> None:
        if X.size == 0:
            return
        with self._lock:
            self._scaler.partial_fit(X)
            Xs = self._scaler.transform(X)
            self._model.partial_fit(Xs, y)
            self._sample_count += len(X)

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            "kind": self.kind,
            "scaler": self._scaler,
            "model": self._model,
            "sample_count": self._sample_count,
            "version": self.version,
        }, path)

    @classmethod
    def load(cls, path: str) -> "OnlineScoringModel":
        bundle = joblib.load(path)
        inst = cls(kind=bundle.get("kind", "quality"))
        inst._scaler = bundle["scaler"]
        inst._model = bundle["model"]
        inst._sample_count = bundle.get("sample_count", 0)
        return inst


# ---------- Cold-start sezgisel etiketleme ----------

def heuristic_target_quality(f: dict) -> float:
    """
    Bir feature dict'ten 0..1 arası bir kalite hedefi üretir.
    Gerçek model bu hedefe yaklaşır; sonra retrain ile değişebilir.
    """
    if f["is_gibberish"]:
        return 0.05
    if f["is_give_up"]:
        return 0.15
    if f["word_count"] < 5:
        return 0.15

    base = 0.40
    base += 0.30 * min(1.0, f["word_count"] / 60.0)        # uzunluk
    base += 0.15 * f["unique_word_ratio"]
    base += 0.15 * f["semantic_similarity"]
    base -= 0.40 * f["repetition_ratio"]
    base -= 0.15 * f["hesitation_density"]
    base += 0.10 * f["coherence_score"]
    return float(np.clip(base, 0.0, 1.0))


def heuristic_target_confidence(f: dict) -> float:
    if f["is_gibberish"] or f["is_give_up"]:
        return 0.10

    base = 0.50
    base -= 0.30 * f["hesitation_density"]
    base -= 0.04 * f["negative_hedge_count"]
    base += 0.03 * f["positive_marker_count"]
    base += 0.10 * f["sentiment_score"]
    base += 0.15 * min(1.0, f["word_count"] / 50.0)

    # Yanıt süresi: çok uzun düşünme veya çok hızlı cevap özgüveni etkiler
    z = f["response_time_z"]
    if z > 1.5:    # çok yavaş — kararsız
        base -= 0.10
    elif z < -1.5: # çok hızlı — düşünmeden cevap
        base -= 0.05

    base += 0.10 * f["skill_level"]                # geçmiş performans
    base -= 0.05 * (f["difficulty"] - 0.5) * 2     # zor sorularda hafif düşer

    return float(np.clip(base, 0.0, 1.0))


def _bootstrap_dataset(kind: str) -> tuple[np.ndarray, np.ndarray]:
    """Sentetik 50 örnek üret — cold-start için."""
    rng = np.random.default_rng(42)
    X, y = [], []
    for _ in range(50):
        f = {
            "word_count": int(rng.integers(0, 120)),
            "char_count": int(rng.integers(0, 600)),
            "avg_word_length": float(rng.uniform(2, 8)),
            "sentence_count": int(rng.integers(1, 8)),
            "avg_sentence_length": float(rng.uniform(3, 25)),
            "unique_word_ratio": float(rng.uniform(0.4, 1.0)),
            "vowel_ratio": float(rng.uniform(0.2, 0.5)),
            "hesitation_density": float(rng.uniform(0.0, 0.3)),
            "negative_hedge_count": int(rng.integers(0, 5)),
            "positive_marker_count": int(rng.integers(0, 5)),
            "is_give_up": int(rng.integers(0, 2)),
            "is_gibberish": int(rng.integers(0, 2)) if rng.random() < 0.1 else 0,
            "repetition_ratio": float(rng.uniform(0.0, 0.5)),
            "response_time_ratio": float(rng.uniform(0.0, 1.0)),
            "response_time_z": float(rng.uniform(-3.0, 3.0)),
            "semantic_similarity": float(rng.uniform(0.0, 1.0)),
            "sentiment_score": float(rng.uniform(-0.8, 0.8)),
            "coherence_score": float(rng.uniform(0.0, 1.0)),
            "difficulty": float(rng.uniform(0.2, 0.9)),
            "skill_level": float(rng.uniform(0.2, 0.9)),
        }
        X.append(list(f.values()))
        y.append(
            heuristic_target_quality(f) if kind == "quality"
            else heuristic_target_confidence(f)
        )
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)
