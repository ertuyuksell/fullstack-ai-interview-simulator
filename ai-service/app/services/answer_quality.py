"""
Cevap kalitesi puanlaması.

Sinyaller:
  • Anlamsızlık (gibberish) tespiti — sesli harf yok / aynı karakter tekrarı /
    sözcük yapısı bozuk metinler doğrudan düşürülür.
  • "Bilmiyorum / fikrim yok" gibi teslim cevapları düşük puana çekilir.
  • Referans cevap varsa cosine similarity (sentence-transformers).
  • Referans yoksa soru ile karşılaştırma (alaka düzeyi).
  • Uzunluk doygunluğu — çok kısa cevaplara penaltı.
"""
from __future__ import annotations

import logging
import re
from functools import lru_cache

log = logging.getLogger(__name__)

EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

GIVE_UP_PATTERNS = re.compile(
    r"\b(bilmiyorum|fikrim yok|hiç bir fikrim yok|hiçbir fikrim yok|"
    r"emin değilim|cevabım yok|geçmek istiyorum|pas|"
    r"i don'?t know|no idea|not sure|skip|pass)\b",
    re.IGNORECASE,
)

VOWELS = set("aeıioöuüâîûAEIİOÖUÜ")


@lru_cache(maxsize=1)
def _embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODEL)


def _cosine(a, b) -> float:
    import numpy as np
    a = a / (np.linalg.norm(a) + 1e-9)
    b = b / (np.linalg.norm(b) + 1e-9)
    return float((a * b).sum())


def _is_gibberish(text: str) -> tuple[bool, str]:
    """
    Anlamsız metin sezgileri:
      • Sesli harf oranı çok düşükse (örn. 'asdasd', 'qwerqwer')
      • Tekrarlayan tek karakter (örn. 'aaaaaa')
      • Boşluk hiç yok ve uzun (tek bir uzun gibberish dizesi)
      • Sözcüklerin neredeyse tamamı 2 karakterden kısa
    """
    t = text.strip()
    if not t:
        return True, "empty"

    letters = [c for c in t if c.isalpha()]
    if not letters:
        return True, "no_letters"

    vowel_ratio = sum(1 for c in letters if c in VOWELS) / len(letters)
    if vowel_ratio < 0.15:
        return True, "low_vowel_ratio"

    # tek karakter tekrarı (aaaa, lalala değil)
    if re.fullmatch(r"(.)\1{4,}", t.replace(" ", "")):
        return True, "char_repeat"

    words = t.split()
    if len(words) >= 3 and sum(1 for w in words if len(w) <= 2) / len(words) > 0.7:
        return True, "tiny_words"

    # boşluk yok ve uzun → tek bir gibberish blob
    if " " not in t and len(t) > 12:
        # gerçek bileşik kelimeler için sesli/sessiz dağılımı normaldir
        if vowel_ratio < 0.25:
            return True, "long_no_space_low_vowel"

    return False, ""


def score(transcript: str | None, reference: str | None,
          question: str | None = None) -> tuple[float, dict]:
    transcript = (transcript or "").strip()
    if not transcript:
        return 0.0, {"reason": "empty"}

    is_gib, gib_reason = _is_gibberish(transcript)
    if is_gib:
        return 0.05, {"reason": "gibberish", "detail": gib_reason}

    if GIVE_UP_PATTERNS.search(transcript):
        return 0.15, {"reason": "give_up"}

    words = transcript.split()
    length_score = min(1.0, len(words) / 60.0)  # 60 kelimede doygunluk

    # 5 kelimeden az gerçek cevap olarak kabul edilmez
    if len(words) < 5:
        return round(0.10 + 0.10 * length_score, 3), {
            "reason": "too_short",
            "length_score": length_score,
        }

    # Referans cevap varsa onunla benzerliğe bak (en güvenilir sinyal)
    if reference and reference.strip():
        try:
            emb = _embedder().encode([transcript, reference], convert_to_numpy=True)
            sim = max(0.0, _cosine(emb[0], emb[1]))
        except Exception as e:
            log.warning("embedding failed: %s", e)
            sim = 0.5
        score_value = 0.7 * sim + 0.3 * length_score
        return round(float(score_value), 3), {
            "similarity": round(sim, 3),
            "length_score": round(length_score, 3),
            "mode": "vs_reference",
        }

    # Referans yok — soruyla zayıf bir alaka kontrolü yap (benzerlik × küçük ağırlık)
    # ve uzunluk + içerik yoğunluğuna ağırlık ver.
    relevance_bonus = 0.0
    if question and question.strip():
        try:
            emb = _embedder().encode([transcript, question], convert_to_numpy=True)
            sim = max(0.0, _cosine(emb[0], emb[1]))
            # Düşük benzerlik bile pas: çok düşükse penaltı, normalse hafif bonus
            if sim < 0.10:
                relevance_bonus = -0.10  # konuyla hiç alakasız
            else:
                relevance_bonus = min(0.20, sim * 0.5)
        except Exception as e:
            log.warning("embedding failed: %s", e)

    # Benzersiz kelime oranı — tekrarlı cevaplara penaltı
    words_lower = [w.lower() for w in words]
    unique_ratio = len(set(words_lower)) / max(1, len(words_lower))

    base = 0.45 + 0.35 * length_score + 0.20 * unique_ratio
    score_value = max(0.05, min(1.0, base + relevance_bonus))

    return round(float(score_value), 3), {
        "length_score": round(length_score, 3),
        "unique_ratio": round(unique_ratio, 3),
        "relevance_bonus": round(relevance_bonus, 3),
        "mode": "no_reference",
    }
