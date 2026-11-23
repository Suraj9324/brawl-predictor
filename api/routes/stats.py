"""Model stats and dashboard routes."""

import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.schemas import DashboardStatsResponse, ModelStatsResponse, SyncLogResponse
from db.models import Battle, Player, Prediction, SyncLog
from db.session import get_db
from model.predict import get_model_meta, is_model_loaded
from pipeline.collector import run_collection
from pipeline.storage import complete_sync_log, create_sync_log, get_tracked_tags, save_collection_results

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/model", response_model=ModelStatsResponse)
def model_stats():
    """Get model training metrics and feature importance."""
    if not is_model_loaded():
        return ModelStatsResponse(is_trained=False)

    meta = get_model_meta()
    return ModelStatsResponse(
        is_trained=True,
        samples=meta.get("samples"),
        accuracy=meta.get("cv_accuracy_mean"),
        f1=meta.get("cv_f1_mean"),
        roc_auc=meta.get("cv_roc_auc_mean"),
        feature_count=meta.get("features"),
        feature_importance=meta.get("feature_importance"),
        class_distribution=meta.get("class_distribution"),
    )


@router.get("/dashboard", response_model=DashboardStatsResponse)
def dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard overview stats."""
    total_players = db.query(func.count(Player.id)).filter(Player.is_tracked == True).scalar() or 0
    total_battles = db.query(func.count(Battle.id)).scalar() or 0
    total_predictions = db.query(func.count(Prediction.id)).scalar() or 0

    last_sync = (
        db.query(SyncLog)
        .filter(SyncLog.status == "completed")
        .order_by(SyncLog.completed_at.desc())
        .first()
    )

    meta = get_model_meta()

    return DashboardStatsResponse(
        total_players=total_players,
        total_battles=total_battles,
        total_predictions=total_predictions,
        last_sync=last_sync.completed_at if last_sync else None,
        model_accuracy=meta.get("cv_accuracy_mean"),
    )


@router.get("/sync-logs", response_model=list[SyncLogResponse])
def sync_logs(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent sync logs."""
    logs = (
        db.query(SyncLog)
        .order_by(SyncLog.started_at.desc())
        .limit(limit)
        .all()
    )
    return logs


@router.post("/sync")
async def trigger_sync(db: Session = Depends(get_db)):
    """Manually trigger a data sync for all tracked players."""
    tags = get_tracked_tags(db)
    if not tags:
        return {"message": "No tracked players", "players_synced": 0, "battles_added": 0}

    sync_log = create_sync_log(db)
    try:
        results = await run_collection(tags)
        summary = save_collection_results(db, results)
        complete_sync_log(db, sync_log, summary)
        return {"message": "Sync completed", **summary}
    except Exception as e:
        complete_sync_log(db, sync_log, {"players_synced": 0, "battles_added": 0, "errors": 1}, status="failed")
        return {"message": f"Sync failed: {e}", "players_synced": 0, "battles_added": 0, "errors": 1}
