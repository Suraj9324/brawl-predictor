"""Prediction routes."""

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas import PredictionHistoryResponse, PredictionResponse
from db.models import Player, Prediction
from db.session import get_db
from model.predict import is_model_loaded, predict
from pipeline.collector import BrawlStarsClient, parse_battlelog, parse_brawlers, parse_profile
from pipeline.features import build_player_features
from pipeline.storage import save_battles, save_snapshot, upsert_brawler_stats, upsert_player

router = APIRouter(prefix="/predict", tags=["predictions"])


@router.get("/{tag:path}", response_model=PredictionResponse)
async def predict_player(tag: str, db: Session = Depends(get_db)):
    """Predict trophy outcome for a player.

    Fetches latest data from BS API, computes features, runs prediction.
    """
    if not is_model_loaded():
        raise HTTPException(status_code=503, detail="Model not trained yet")

    clean_tag = tag.strip().upper()
    if not clean_tag.startswith("#"):
        clean_tag = f"#{clean_tag}"

    # Fetch fresh data from BS API
    client = BrawlStarsClient()
    try:
        raw_profile = await client.get_player(clean_tag)
        raw_battlelog = await client.get_battlelog(clean_tag)
    except ValueError:
        raise HTTPException(status_code=404, detail="Player not found on Brawl Stars")
    except RuntimeError:
        raise HTTPException(status_code=429, detail="Rate limited, try again later")

    # Update local data
    profile = parse_profile(raw_profile)
    brawlers = parse_brawlers(raw_profile)
    battles = parse_battlelog(clean_tag, raw_battlelog)

    player = upsert_player(db, profile)
    save_snapshot(db, player, profile)
    upsert_brawler_stats(db, player.id, brawlers)
    save_battles(db, player.id, battles)
    db.commit()

    # Compute features
    features = build_player_features(db, player.id)
    if features is None:
        raise HTTPException(
            status_code=422,
            detail="Not enough battle data for prediction (need at least 5 battles)",
        )

    # Run prediction
    result = predict(features)
    if result is None:
        raise HTTPException(status_code=503, detail="Prediction failed")

    # Save prediction to DB
    prediction = Prediction(
        player_id=player.id,
        prediction_type="classification",
        predicted_outcome=result["outcome"],
        predicted_trophy_change=result["predicted_trophy_change"],
        confidence=result["confidence"],
        top_features=json.dumps(result["top_features"]),
    )
    db.add(prediction)
    db.commit()

    return PredictionResponse(
        player_tag=player.tag,
        player_name=player.name,
        outcome=result["outcome"],
        confidence=result["confidence"],
        predicted_trophy_change=result["predicted_trophy_change"],
        top_features=result["top_features"],
        current_trophies=player.trophies,
    )


@router.get("/{tag:path}/history", response_model=list[PredictionHistoryResponse])
def prediction_history(tag: str, limit: int = 20, db: Session = Depends(get_db)):
    """Get prediction history for a player."""
    clean_tag = tag.strip().upper()
    if not clean_tag.startswith("#"):
        clean_tag = f"#{clean_tag}"

    player = db.query(Player).filter(Player.tag == clean_tag).first()
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    predictions = (
        db.query(Prediction)
        .filter(Prediction.player_id == player.id)
        .order_by(Prediction.predicted_at.desc())
        .limit(limit)
        .all()
    )

    return predictions
