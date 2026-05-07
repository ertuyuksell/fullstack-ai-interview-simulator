"""
Feature engineering pipeline.

Bir cevabı puanlamak için ham metin + meta verilerden ~20 sayısal feature çıkarır.
Bu vektör hem dinamik scoring engine'in (sklearn) girdisi olur hem de DB'ye
loglanarak offline retraining'de kullanılır.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np

# Türkçe + İngilizce dolgu/kararsızlık ifadeleri
HESITATION_PATTERNS = re.compile(
    r"\b("
    r"e+h+|hı+m+|şe+y+|yani|aslında|işte|gibi|falan|filan|"
    r"um+|uh+|er+|like|you know|i mean|kinda|sorta"
    r")\b",
    re.IGNORECASE,
)

GIVE_UP_PATTERNS = re.compile(
    r"\b(bilmiyorum|fikrim yok|emin değilim|geçmek istiyorum|pas|"
    r"i don'?t know|no idea|not sure|skip|pass)\b",
    re.IGNORECASE,
)

NEGATIVE_HEDGES = re.compile(
    r"\b(belki|sanırım|galiba|tahmin ediyorum|olabilir mi|olabilirim|"
    r"maybe|i guess|i think maybe|kind of)\b",
    re.IGNORECASE,
)

POSITIVE_MARKERS = re.compile(
    r"\b(eminim|kesinlikle|öncelikle|özellikle|sonuç olarak|"
    r"definitely|certainly|specifically|because|therefore)\b",
    re.IGNORECASE,
)

VOWELS = set("aeıioöuüâîûAEIİOÖUÜ")
SENT_BOUND = re.compile(r"[.!?]+")


@dataclass
class Features:
    word_count: int
    char_count: int
    avg_word_length: float
    sentence_count: int
    avg_sentence_length: float
    unique_word_ratio: float
    vowel_ratio: float
    hesitation_density: float       # dolgu/kararsızlık ifade oranı
    negative_hedge_count: int
    positive_marker_count: int
    is_give_up: int                 # 0/1
    is_gibberish: int               # 0/1
    repetition_ratio: float         # bigram tekrar oranı
    response_time_ratio: float      # uzunluğa göre normalize edilmiş süre
    response_time_z: float          # genel ortalamadan sapma (-3..+3 clip)
    semantic_similarity: float      # referans veya soru ile cosine
    sentiment_score: float          # -1..1
    coherence_score: float          # cümle-cümle benzerlik ortalaması
    difficulty: float               # sorunun zorluğu
    skill_level: float              # kullanıcının kategorideki yeteneği

    def to_array(self) -> np.ndarray:
        d = asdict(self)
        return np.array(list(d.values()), dtype=np.float32)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def feature_names(cls) -> list[str]:
        return [f for f in cls.__dataclass_fields__.keys()]


def extract(
    transcript: str,
    *,
    question: Optional[str] = None,
    reference: Optional[str] = None,
    response_time_ms: Optional[int] = None,
    difficulty: float = 0.5,
    skill_level: float = 0.5,
    embedder=None,
    sentiment_pipe=None,
) -> Features:
    t = (transcript or "").strip()
    words = t.split()
    n_words = len(words)
    n_chars = len(t)
    sentences = [s.strip() for s in SENT_BOUND.split(t) if s.strip()]
    n_sent = max(1, len(sentences))

    letters = [c for c in t if c.isalpha()]
    vowel_ratio = (sum(1 for c in letters if c in VOWELS) / len(letters)) if letters else 0.0

    is_gib = 0
    if not letters or vowel_ratio < 0.15:
        is_gib = 1
    elif n_words >= 3 and sum(1 for w in words if len(w) <= 2) / n_words > 0.7:
        is_gib = 1
    elif " " not in t and len(t) > 12 and vowel_ratio < 0.25:
        is_gib = 1

    is_give_up = 1 if GIVE_UP_PATTERNS.search(t) else 0

    hes = len(HESITATION_PATTERNS.findall(t))
    hesitation_density = hes / max(1, n_words)
    neg = len(NEGATIVE_HEDGES.findall(t))
    pos = len(POSITIVE_MARKERS.findall(t))

    unique_word_ratio = (len(set(w.lower() for w in words)) / n_words) if n_words else 0.0
    repetition_ratio = _bigram_repeat(words)

    avg_word_len = (sum(len(w) for w in words) / n_words) if n_words else 0.0
    avg_sent_len = n_words / n_sent

    # Yanıt süresi sezgisi: kelime başına 0.4 sn ideal, çok kısa veya çok uzun ödün
    response_time_ratio = 0.5
    response_time_z = 0.0
    if response_time_ms and n_words > 0:
        sec_per_word = (response_time_ms / 1000.0) / n_words
        # Z benzeri ölçü: 0.4 sn/kelime merkez, ±1 sn/kelime sapma
        response_time_z = float(np.clip((sec_per_word - 0.4) / 1.0, -3.0, 3.0))
        # Süre oranı: 1 dakikalık limite göre
        response_time_ratio = float(np.clip(response_time_ms / 60000.0, 0.0, 1.0))

    # semantic similarity (referans varsa onunla, yoksa soru ile)
    sim = 0.0
    target = (reference or "").strip() or (question or "").strip()
    if target and embedder and n_words >= 2:
        try:
            emb = embedder.encode([t, target], convert_to_numpy=True)
            a, b = emb[0], emb[1]
            denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9
            sim = float(max(0.0, np.dot(a, b) / denom))
        except Exception:
            sim = 0.5

    sentiment = 0.0
    if sentiment_pipe and t and not is_gib:
        try:
            r = sentiment_pipe(t[:512])
            if r:
                top = r[0]
                label = top.get("label", "").lower()
                conf = float(top.get("score", 0.0))
                # üç sınıflı veya ikili sentiment'i normalize et
                if "pos" in label:
                    sentiment = conf
                elif "neg" in label:
                    sentiment = -conf
                else:
                    sentiment = 0.0
        except Exception:
            sentiment = 0.0

    coherence = 0.0
    if embedder and len(sentences) >= 2:
        try:
            embs = embedder.encode(sentences[:6], convert_to_numpy=True)
            sims = []
            for i in range(len(embs) - 1):
                a, b = embs[i], embs[i + 1]
                denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9
                sims.append(float(max(0.0, np.dot(a, b) / denom)))
            coherence = float(np.mean(sims)) if sims else 0.0
        except Exception:
            coherence = 0.0

    return Features(
        word_count=n_words,
        char_count=n_chars,
        avg_word_length=avg_word_len,
        sentence_count=n_sent,
        avg_sentence_length=avg_sent_len,
        unique_word_ratio=unique_word_ratio,
        vowel_ratio=vowel_ratio,
        hesitation_density=hesitation_density,
        negative_hedge_count=neg,
        positive_marker_count=pos,
        is_give_up=is_give_up,
        is_gibberish=is_gib,
        repetition_ratio=repetition_ratio,
        response_time_ratio=response_time_ratio,
        response_time_z=response_time_z,
        semantic_similarity=sim,
        sentiment_score=sentiment,
        coherence_score=coherence,
        difficulty=difficulty,
        skill_level=skill_level,
    )


def _bigram_repeat(words: list[str]) -> float:
    if len(words) < 4:
        return 0.0
    bigrams = [f"{words[i].lower()} {words[i+1].lower()}" for i in range(len(words) - 1)]
    if not bigrams:
        return 0.0
    return 1.0 - (len(set(bigrams)) / len(bigrams))
