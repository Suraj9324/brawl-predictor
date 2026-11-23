"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import players, predictions, stats
from db.models import Base
from db.session import engine
from model.predict import load_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Brawl Predictor API",
    description="ML-powered Brawl Stars performance predictions",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(players.router, prefix="/api")
app.include_router(predictions.router, prefix="/api")
app.include_router(stats.router, prefix="/api")


@app.on_event("startup")
def on_startup():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified")

    # Try to load the ML model
    if load_model():
        logger.info("ML model loaded")
    else:
        logger.warning("No ML model found — predictions will be unavailable until training")


@app.get("/api/health")
def health():
    return {"status": "ok"}
