import logging
from functools import lru_cache

from fastapi import APIRouter

from app.features.extractor import extract
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.scoring.engine import get_engine
from app.services import facial_emotion, speech_emotion

log = logging.getLogger(__name__)
router = APIRouter()


@lru_cache(maxsize=1)
def _embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


@lru_cache(maxsize=1)
def _sentiment():
    try:
        from transformers import pipeline
        return pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
        )
    except Exception as e:
        log.warning("sentiment pipeline unavailable: %s", e)
        return None


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    face_label, face_conf, face_scores = ("neutral", 0.0, {})
    voice_label, voice_conf, voice_scores = ("neutral", 0.0, {})

    if req.frame_base64:
        face_label, face_conf, face_scores = facial_emotion.predict(req.frame_base64)
    if req.audio_base64:
        voice_label, voice_conf, voice_scores = speech_emotion.predict(req.audio_base64)

    feats = extract(
        req.transcript or "",
        question=req.question,
        reference=req.reference_answer,
        response_time_ms=req.response_time_ms,
        difficulty=req.difficulty,
        skill_level=req.skill_level,
        embedder=_embedder(),
        sentiment_pipe=_sentiment(),
    )

    engine = get_engine()
    f_dict = feats.to_dict()

    # İki katmanlı puanlama:
    #   • Sezgisel hedef = güvenilir, predictable (cold start için kullanılan formül)
    #   • Model tahmini = veri biriktikçe değişebilir
    # Final skor: ağırlıklı ortalama. Veri azken sezgisele yaslanırız.
    from app.scoring.online_model import (
        heuristic_target_quality, heuristic_target_confidence,
    )
    h_q = heuristic_target_quality(f_dict)
    h_c = heuristic_target_confidence(f_dict)
    m = engine.score(feats)

    # Model güveni sample sayısına bağlı; düşükse sezgisele yakın kal
    w_model = 0.5 * m["answer_quality_confidence"]  # 0..0.5
    final_q = (1 - w_model) * h_q + w_model * m["answer_quality_score"]
    w_model_c = 0.5 * m["confidence_model_confidence"]
    final_c = (1 - w_model_c) * h_c + w_model_c * m["confidence_score"]

    # Online learning — sezgisel hedefle güncelle
    try:
        engine.learn(feats)
    except Exception as e:
        log.warning("online learn failed: %s", e)

    return AnalyzeResponse(
        confidence_score=round(final_c, 3),
        answer_quality_score=round(final_q, 3),
        facial_emotion=face_label,
        speech_emotion=voice_label,
        features=feats.to_dict(),
        detail={
            "facial": {"top_confidence": face_conf, "scores": face_scores},
            "speech": {"top_confidence": voice_conf, "scores": voice_scores},
            "model_confidence": {
                "quality": m["answer_quality_confidence"],
                "confidence": m["confidence_model_confidence"],
            },
            "heuristic_scores": {"quality": h_q, "confidence": h_c},
            "model_scores": {
                "quality": m["answer_quality_score"],
                "confidence": m["confidence_score"],
            },
        },
    )
