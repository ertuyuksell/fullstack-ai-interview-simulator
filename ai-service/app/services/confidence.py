"""
Confidence score combines:
  • Speech emotion (calm/happy/neutral lift it; fearful/sad lower it).
  • Facial emotion (happy/neutral lift; fear/sad lower).
  • Filler density in transcript ("um", "uh", "like", "you know").
"""
from __future__ import annotations

import re

POSITIVE_VOICE = {"hap", "happy", "neu", "neutral", "calm"}
NEGATIVE_VOICE = {"sad", "fea", "fear", "ang", "angry"}

POSITIVE_FACE = {"happy", "neutral", "surprise"}
NEGATIVE_FACE = {"fear", "sad", "disgust", "angry"}

FILLERS = re.compile(r"\b(um+|uh+|er+|like|you know|i mean|kinda|sorta)\b", re.I)


def score(transcript: str | None, voice_emotion: str, face_emotion: str) -> tuple[float, dict]:
    base = 0.55

    v = voice_emotion.lower()
    if any(v.startswith(p) for p in POSITIVE_VOICE):
        base += 0.15
    elif any(v.startswith(p) for p in NEGATIVE_VOICE):
        base -= 0.15

    f = face_emotion.lower()
    if f in POSITIVE_FACE:
        base += 0.10
    elif f in NEGATIVE_FACE:
        base -= 0.15

    filler_penalty = 0.0
    if transcript:
        words = max(1, len(transcript.split()))
        fillers = len(FILLERS.findall(transcript))
        ratio = fillers / words
        filler_penalty = min(0.25, ratio * 2.0)
        base -= filler_penalty

    base = max(0.0, min(1.0, base))
    return round(base, 3), {
        "voice_component": voice_emotion,
        "face_component": face_emotion,
        "filler_penalty": round(filler_penalty, 3),
    }
