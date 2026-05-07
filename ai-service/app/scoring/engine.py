"""
Scoring engine — feature extraction → iki model (quality + confidence) → skorlar.
Modeller diskten yüklenir; yoksa yeni instance oluşturulur ve kaydedilir.
"""
from __future__ import annotations

import logging
import os
import threading
from functools import lru_cache
from typing import Optional

import numpy as np

from app.features.extractor import Features, extract
from .online_model import (
    OnlineScoringModel,
    heuristic_target_quality,
    heuristic_target_confidence,
)

log = logging.getLogger(__name__)

MODEL_DIR = os.getenv("MODEL_ARTIFACTS_DIR", "/models/artifacts")
QUALITY_PATH = os.path.join(MODEL_DIR, "quality.joblib")
CONFIDENCE_PATH = os.path.join(MODEL_DIR, "confidence.joblib")


class ScoringEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self.quality = self._load_or_init(QUALITY_PATH, "quality")
        self.confidence = self._load_or_init(CONFIDENCE_PATH, "confidence")

    @staticmethod
    def _load_or_init(path: str, kind: str) -> OnlineScoringModel:
        if os.path.exists(path):
            try:
                m = OnlineScoringModel.load(path)
                log.info("loaded %s model from %s", kind, path)
                return m
            except Exception as e:
                log.warning("failed to load %s model: %s — re-initializing", kind, e)
        m = OnlineScoringModel(kind=kind)
        try:
            m.save(path)
        except Exception as e:
            log.warning("failed to persist initial %s model: %s", kind, e)
        return m

    def score(self, features: Features) -> dict:
        x = features.to_array()
        q_score, q_conf = self.quality.predict(x)
        c_score, c_conf = self.confidence.predict(x)
        return {
            "answer_quality_score": q_score,
            "answer_quality_confidence": q_conf,
            "confidence_score": c_score,
            "confidence_model_confidence": c_conf,
        }

    def learn(self, features: Features) -> None:
        """
        Feature vektörünü sezgisel hedefle online öğret.
        Gerçek etiket varsa `learn_with_target` kullan.
        """
        f_dict = features.to_dict()
        x = features.to_array().reshape(1, -1)
        y_q = np.array([heuristic_target_quality(f_dict)], dtype=np.float32)
        y_c = np.array([heuristic_target_confidence(f_dict)], dtype=np.float32)
        with self._lock:
            self.quality.partial_fit(x, y_q)
            self.confidence.partial_fit(x, y_c)

    def learn_with_target(self, features: Features,
                          quality_target: float,
                          confidence_target: float) -> None:
        x = features.to_array().reshape(1, -1)
        y_q = np.array([float(np.clip(quality_target, 0, 1))], dtype=np.float32)
        y_c = np.array([float(np.clip(confidence_target, 0, 1))], dtype=np.float32)
        with self._lock:
            self.quality.partial_fit(x, y_q)
            self.confidence.partial_fit(x, y_c)

    def persist(self) -> None:
        with self._lock:
            try: self.quality.save(QUALITY_PATH)
            except Exception as e: log.warning("save quality failed: %s", e)
            try: self.confidence.save(CONFIDENCE_PATH)
            except Exception as e: log.warning("save confidence failed: %s", e)

    def info(self) -> dict:
        return {
            "quality": {
                "name": self.quality.name,
                "version": self.quality.version,
                "samples": self.quality._sample_count,
            },
            "confidence": {
                "name": self.confidence.name,
                "version": self.confidence.version,
                "samples": self.confidence._sample_count,
            },
        }


@lru_cache(maxsize=1)
def get_engine() -> ScoringEngine:
    return ScoringEngine()
