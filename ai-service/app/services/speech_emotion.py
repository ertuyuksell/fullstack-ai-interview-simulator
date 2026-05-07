"""Speech emotion recognition with a wav2vec2 model fine-tuned on RAVDESS/IEMOCAP."""
from __future__ import annotations

import base64
import io
import logging
from functools import lru_cache
from typing import Optional

import numpy as np
import torch

log = logging.getLogger(__name__)

MODEL_ID = "superb/wav2vec2-base-superb-er"
TARGET_SR = 16000


@lru_cache(maxsize=1)
def _pipeline():
    from transformers import pipeline
    return pipeline("audio-classification", model=MODEL_ID)


def predict(audio_b64: str) -> tuple[str, float, dict]:
    waveform = _decode(audio_b64)
    if waveform is None or waveform.size == 0:
        return "neutral", 0.0, {}
    try:
        out = _pipeline()({"raw": waveform.astype(np.float32), "sampling_rate": TARGET_SR}, top_k=5)
    except Exception as e:
        log.warning("speech emotion failed: %s", e)
        return "neutral", 0.0, {}
    if not out:
        return "neutral", 0.0, {}
    top = out[0]
    return top["label"], float(top["score"]), {o["label"]: float(o["score"]) for o in out}


def _decode(b64: str) -> Optional[np.ndarray]:
    try:
        import soundfile as sf
        import librosa
        raw = base64.b64decode(b64.split(",")[-1])
        data, sr = sf.read(io.BytesIO(raw), dtype="float32", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1)
        if sr != TARGET_SR:
            data = librosa.resample(data, orig_sr=sr, target_sr=TARGET_SR)
        return data
    except Exception as e:
        log.warning("audio decode failed: %s", e)
        return None
