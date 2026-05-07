"""FastAPI giriş noktası."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import analyze, questions, health, train

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Interview Service", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(questions.router)
app.include_router(train.router)


@app.on_event("startup")
async def warmup():
    # Engine'i başlangıçta yükle ki ilk istek bekleme yapmasın
    from app.scoring.engine import get_engine
    get_engine()
