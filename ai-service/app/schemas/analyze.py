from pydantic import BaseModel, Field
from typing import Optional


class AnalyzeRequest(BaseModel):
    transcript: Optional[str] = None
    question: Optional[str] = None
    reference_answer: Optional[str] = None
    audio_base64: Optional[str] = None
    frame_base64: Optional[str] = None
    response_time_ms: Optional[int] = None
    difficulty: float = 0.5
    skill_level: float = 0.5
    category: Optional[str] = None
    user_id: Optional[str] = None


class AnalyzeResponse(BaseModel):
    confidence_score: float
    answer_quality_score: float
    facial_emotion: str
    speech_emotion: str
    features: dict
    detail: dict


class QuestionRequest(BaseModel):
    role: str
    level: str
    count: int = 5
    user_id: Optional[str] = None
    difficulty: float = Field(0.5, ge=0.0, le=1.0)
    seen_hashes: list[str] = []
    recent_topics: list[str] = []
    weak_areas: list[str] = []
    skill_level: float = Field(0.5, ge=0.0, le=1.0)
    categories: list[str] = []   # boş bırakılırsa karışık üretilir


class GeneratedQuestion(BaseModel):
    prompt: str
    category: str
    difficulty: float
    source: str
    content_hash: str


class QuestionResponse(BaseModel):
    questions: list[GeneratedQuestion]


class TrainRequest(BaseModel):
    """Manuel label ile eğitim için."""
    features: dict
    quality_target: float = Field(..., ge=0.0, le=1.0)
    confidence_target: float = Field(..., ge=0.0, le=1.0)
