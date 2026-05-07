"""
Manuel etiketle eğitim ve modeli persist etme endpoint'leri.

POST /train       — bir feature dict + etiketlerle online güncelleme
POST /train/save  — modelleri diske yaz
GET  /train/info  — model durumu
"""
from fastapi import APIRouter, HTTPException

import numpy as np

from app.features.extractor import Features
from app.scoring.engine import get_engine
from app.schemas.analyze import TrainRequest

router = APIRouter(prefix="/train")


@router.get("/info")
def info() -> dict:
    return get_engine().info()


@router.post("/save")
def save() -> dict:
    get_engine().persist()
    return {"status": "saved"}


@router.post("")
def train(req: TrainRequest) -> dict:
    # Eksik alanları varsayılana çek
    fields = Features.feature_names()
    f_dict = {k: float(req.features.get(k, 0.0)) for k in fields}
    feats = Features(**f_dict)
    try:
        get_engine().learn_with_target(feats, req.quality_target, req.confidence_target)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok", "samples": get_engine().info()}
