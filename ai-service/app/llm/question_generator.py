"""
Adaptif soru üreticisi.

Akış:
  1. Kullanıcının önceki sorularının hash'leri parametre olarak gelir.
  2. Önce LLM'e (Ollama) prompt gönderilir — kullanıcı performansı, kategori,
     zorluk hedefi ve önceki konular prompta enjekte edilir.
  3. LLM yanıt vermezse / sağlıksızsa zengin şablon havuzundan seçilir.
  4. Her durumda dedup hash kontrolü yapılır.
"""
from __future__ import annotations

import hashlib
import logging
import random
import re
from dataclasses import dataclass
from typing import Optional

from .ollama_provider import OllamaProvider

log = logging.getLogger(__name__)


CATEGORIES = ["behavioral", "technical", "system_design", "problem_solving",
              "leadership", "communication"]


@dataclass
class GenerationContext:
    role: str
    level: str
    category: str
    difficulty: float                 # 0..1
    skill_level: float                # kullanıcının bu kategorideki yeteneği 0..1
    recent_topics: list[str]          # son sorulan konuların özeti
    seen_hashes: set[str]             # bu kullanıcıya daha önce sorulan hash'ler
    weak_areas: list[str]             # kullanıcının zorlandığı kategoriler


class QuestionGenerator:
    def __init__(self, llm: Optional[OllamaProvider] = None):
        self.llm = llm or OllamaProvider()

    async def generate(self, ctx: GenerationContext) -> tuple[str, str]:
        """
        Bir soru üretir; (prompt, source) döner. Source: 'llm' veya 'template'.
        """
        for attempt in range(3):
            text = await self._try_llm(ctx, attempt)
            if text and self._fingerprint(text) not in ctx.seen_hashes:
                return text, "llm"

        # LLM çalışmadı veya tüm denemelerde tekrar üretti — şablona dön
        return self._template_fallback(ctx), "template"

    async def _try_llm(self, ctx: GenerationContext, attempt: int) -> Optional[str]:
        system = (
            "Sen Türkçe konuşan kıdemli bir teknik mülakatçısın. "
            "Sadece akıcı ve doğru Türkçe yazarsın. İngilizce kelime kullanma. "
            "Cevap olarak SADECE tek bir mülakat sorusu yaz — açıklama, başlık, "
            "numara, tırnak veya markdown ekleme. Soru bir tam cümle olsun ve '?' "
            "ile bitsin. En az 8 kelime olmalı."
        )
        difficulty_hint = self._difficulty_hint(ctx.difficulty)
        recent = ", ".join(ctx.recent_topics[:5]) if ctx.recent_topics else "yok"
        weak = ", ".join(ctx.weak_areas[:3]) if ctx.weak_areas else "yok"

        user = (
            f"Aday rolü: {ctx.role}\n"
            f"Seviye: {ctx.level}\n"
            f"Kategori: {ctx.category}\n"
            f"Hedef zorluk: {difficulty_hint} ({ctx.difficulty:.2f})\n"
            f"Adayın bu kategorideki seviyesi: {ctx.skill_level:.2f}\n"
            f"Yakın zamanda sorulan konular (TEKRAR ETME): {recent}\n"
            f"Adayın geliştirmesi gereken alanlar (mümkünse buna yönel): {weak}\n"
            f"Deneme: {attempt + 1}\n\n"
            "Bu bilgilere göre özgün, somut ve düşündürücü tek bir Türkçe mülakat sorusu üret."
        )

        raw = await self.llm.complete(system, user, max_tokens=120,
                                      temperature=0.85 + 0.05 * attempt)
        if not raw:
            return None
        return self._clean(raw)

    @staticmethod
    def _difficulty_hint(d: float) -> str:
        if d < 0.33: return "kolay (giriş seviyesi)"
        if d < 0.66: return "orta (uygulama seviyesi)"
        return "zor (derin analiz)"

    @staticmethod
    def _clean(text: str) -> Optional[str]:
        # Boş satırları at, ilk anlamlı satırı al
        lines = [ln for ln in text.strip().split("\n") if ln.strip()]
        if not lines:
            return None
        first = lines[0]
        # markdown / liste işaretleri ve **bold** kalıntılarını sök
        first = re.sub(r"^\s*[-*0-9.\)#]+\s*", "", first)
        first = re.sub(r"\*+", "", first)
        first = first.strip().strip('"').strip("'").strip().strip(":")
        # Aynı kelimenin üst üste tekrarı (model dejenere) → at
        if re.search(r"\b(\w+)\s+\1\b", first, re.IGNORECASE):
            return None
        # İngilizce fragmanları/bozuk Türkçe işaretleri at
        if re.search(r"\b(yourseydinz|yourself|en este|empresa|gelini)\b", first, re.IGNORECASE):
            return None
        if len(first) < 20 or len(first) > 350:
            return None
        # En az 4 kelime ve birden fazla noktasız harf bloğu olmalı
        words = first.split()
        if len(words) < 4:
            return None
        if not first.endswith("?"):
            first += "?"
        return first

    @staticmethod
    def _fingerprint(text: str) -> str:
        norm = re.sub(r"\s+", " ", text.lower().strip())
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:32]

    # ----------------- şablon fallback -----------------

    def _template_fallback(self, ctx: GenerationContext) -> str:
        bank = TEMPLATE_BANK.get(ctx.category, TEMPLATE_BANK["behavioral"])
        rng = random.Random()
        # zorluk filtreli + kullanıcının görmediği şablonlar
        candidates = [
            self._fill(t, ctx) for t in bank
            if abs(t["difficulty"] - ctx.difficulty) < 0.35
        ]
        rng.shuffle(candidates)
        for c in candidates:
            if self._fingerprint(c) not in ctx.seen_hashes:
                return c
        # hepsi görüldü — yine de bir tane döndür (en azından zorluk uyacak)
        return candidates[0] if candidates else self._fill(bank[0], ctx)

    @staticmethod
    def _fill(template: dict, ctx: GenerationContext) -> str:
        return template["text"].format(role=ctx.role, level=ctx.level)


# Kategori başına {text, difficulty} şablonları. {role}/{level} yerine geçer.
TEMPLATE_BANK = {
    "behavioral": [
        {"text": "Yöneticinle anlaşamadığın bir konuda nasıl ilerlersin, somut bir örnek anlatır mısın?", "difficulty": 0.5},
        {"text": "Tek başına çok zor bir kararı verdiğin bir anı anlat — ne öğrendin?", "difficulty": 0.6},
        {"text": "Hata yaptığını fark ettiğin ve düzeltmek için aksiyon aldığın bir an anlatır mısın?", "difficulty": 0.4},
        {"text": "Bir takım arkadaşına yapıcı bir geri bildirim verdiğin bir durumu anlat.", "difficulty": 0.5},
        {"text": "Geçmişte aldığın en zor profesyonel kararı anlatır mısın?", "difficulty": 0.7},
        {"text": "Kapasitenin üzerinde iş yüklendiğinde nasıl önceliklendirme yaptığını bir örnekle anlat.", "difficulty": 0.55},
    ],
    "technical": [
        {"text": "Production'da p99 gecikmesi aniden ikiye katlandı — ilk 30 dakikada ne yaparsın?", "difficulty": 0.7},
        {"text": "İdempotent bir ödeme servisi tasarlayacak olsan hangi mekanizmaları kullanırdın?", "difficulty": 0.7},
        {"text": "Bir endpoint'in %1'i hata dönüyor — bu hatayı nasıl izole edersin?", "difficulty": 0.5},
        {"text": "Database'de N+1 sorgu problemini nasıl yakalarsın ve nasıl çözersin?", "difficulty": 0.45},
        {"text": "Bir cache invalidation stratejisi seç ve neden onu seçtiğini açıkla.", "difficulty": 0.65},
        {"text": "Async ve sync iletişim arasındaki seçimi {role} bağlamında nasıl yapıyorsun?", "difficulty": 0.6},
    ],
    "system_design": [
        {"text": "Günde 100 milyon istek alan bir URL kısaltıcıyı nasıl tasarlarsın?", "difficulty": 0.75},
        {"text": "Gerçek zamanlı bildirim sistemini nasıl kurgularsın — push, polling veya websocket?", "difficulty": 0.7},
        {"text": "Bir feature flag servisini sıfırdan tasarlamanı istesem, ana bileşenler ne olur?", "difficulty": 0.6},
        {"text": "Çoklu bölge (multi-region) bir veri katmanında consistency-availability dengesini nasıl kurarsın?", "difficulty": 0.85},
    ],
    "problem_solving": [
        {"text": "Kuyruktaki işlerin %5'i sessizce kayboluyor — hipotezlerin neler ve hangi sırayla test edersin?", "difficulty": 0.65},
        {"text": "Logları okuyamadığın bir bug için hangi araçları/yaklaşımları kullanırsın?", "difficulty": 0.5},
        {"text": "Bir API yanıtı %1 oranında bozuk JSON dönüyor — nasıl debug edersin?", "difficulty": 0.55},
    ],
    "leadership": [
        {"text": "Takımının motivasyonunu kaybettiği bir dönemi nasıl yönettin?", "difficulty": 0.7},
        {"text": "Bir takım üyesinin performansını yükseltmek için kullandığın somut bir taktik var mı?", "difficulty": 0.6},
        {"text": "Stratejik bir kararla mevcut takım yetkinliği çatıştığında nasıl ilerlersin?", "difficulty": 0.75},
    ],
    "communication": [
        {"text": "Teknik olmayan bir paydaşa karmaşık bir mimari kararı nasıl açıklarsın?", "difficulty": 0.5},
        {"text": "Yazılı dokümantasyonda hangi prensiplere dikkat ediyorsun?", "difficulty": 0.4},
        {"text": "Bir karar dokümanı yazarken hangi başlıkları zorunlu görürsün?", "difficulty": 0.55},
    ],
}
