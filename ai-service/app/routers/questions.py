import asyncio
import logging
import random

from fastapi import APIRouter

from app.llm.question_generator import (
    QuestionGenerator,
    GenerationContext,
    CATEGORIES,
)
from app.schemas.analyze import (
    QuestionRequest, QuestionResponse, GeneratedQuestion,
)

log = logging.getLogger(__name__)
router = APIRouter()

_generator = QuestionGenerator()


def _pick_categories(role: str, requested: list[str], count: int) -> list[str]:
    if requested:
        # döngüsel doldur
        return [requested[i % len(requested)] for i in range(count)]
    # role'e göre dağılım: behavioral + technical karışık
    role_l = role.lower()
    if "data" in role_l or "ml" in role_l:
        pool = ["technical", "problem_solving", "behavioral", "communication", "system_design"]
    elif "front" in role_l:
        pool = ["technical", "behavioral", "system_design", "communication", "problem_solving"]
    elif "back" in role_l or "platform" in role_l:
        pool = ["technical", "system_design", "behavioral", "problem_solving", "communication"]
    elif "product" in role_l or "ürün" in role_l:
        pool = ["leadership", "communication", "behavioral", "problem_solving", "system_design"]
    else:
        pool = ["behavioral", "technical", "communication", "problem_solving", "leadership"]
    return [pool[i % len(pool)] for i in range(count)]


def _vary_difficulty(base: float, i: int, count: int) -> float:
    """Hedef etrafında ±0.15 sınır içinde değiştir."""
    spread = 0.30
    rel = (i / max(1, count - 1)) - 0.5  # -0.5..+0.5
    return max(0.05, min(0.95, base + spread * rel))


@router.post("/questions", response_model=QuestionResponse)
async def questions(req: QuestionRequest) -> QuestionResponse:
    seen = set(req.seen_hashes or [])
    cats = _pick_categories(req.role, req.categories, req.count)

    out: list[GeneratedQuestion] = []

    async def _one(i: int, cat: str):
        ctx = GenerationContext(
            role=req.role,
            level=req.level,
            category=cat,
            difficulty=_vary_difficulty(req.difficulty, i, req.count),
            skill_level=req.skill_level,
            recent_topics=req.recent_topics,
            seen_hashes=seen,
            weak_areas=req.weak_areas,
        )
        prompt, source = await _generator.generate(ctx)
        h = QuestionGenerator._fingerprint(prompt)
        # tekrar gelirse sessizce ekle (çok zorlandı)
        seen.add(h)
        return GeneratedQuestion(
            prompt=prompt,
            category=cat,
            difficulty=round(ctx.difficulty, 3),
            source=source,
            content_hash=h,
        )

    # Birkaçını paralel üret — Ollama yavaşsa toplam süre düşer
    results = await asyncio.gather(*[_one(i, cats[i]) for i in range(req.count)])
    out.extend(results)
    return QuestionResponse(questions=out)
