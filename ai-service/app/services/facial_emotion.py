"""Facial emotion recognition via the FER library (MTCNN + mini-Xception)."""
from __future__ import annotations

import base64
import io
import logging
from functools import lru_cache
from typing import Optional

import numpy as np
from PIL import Image

log = logging.getLogger(__name__)

EMOTIONS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]


@lru_cache(maxsize=1)
def _detector():
    from fer import FER
    return FER(mtcnn=True)


def predict(frame_b64: str) -> tuple[str, float, dict]:
    """Returns (top_emotion, confidence, raw_scores)."""
    img = _decode(frame_b64)
    if img is None:
        return "neutral", 0.0, {}
    try:
        result = _detector().detect_emotions(np.array(img))
    except Exception as e:
        log.warning("facial detection failed: %s", e)
        return "neutral", 0.0, {}
    if not result:
        return "neutral", 0.0, {}
    scores = result[0]["emotions"]
    top = max(scores, key=scores.get)
    return top, float(scores[top]), {k: float(v) for k, v in scores.items()}


def _decode(b64: str) -> Optional[Image.Image]:
    try:
        data = base64.b64decode(b64.split(",")[-1])
        return Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        return None
