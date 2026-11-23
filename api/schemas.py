"""Pydantic request/response models."""

from datetime import datetime

from pydantic import BaseModel, Field


# --- Player schemas ---


class AddPlayerRequest(BaseModel):
    tag: str = Field(..., min_length=2, max_length=20, examples=["#8YVRRJQYY"])


class PlayerResponse(BaseModel):
    id: int
    tag: str
    name: str
    trophies: int
    highest_trophies: int
    experience_level: int
    club_name: str | None
    is_tracked: bool
    last_synced_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PlayerDetailResponse(PlayerResponse):
    snapshots: list["SnapshotResponse"]
    recent_battles: list["BattleResponse"]
    brawler_count: int


class SnapshotResponse(BaseModel):
    trophies: int
    highest_trophies: int
    brawlers_count: int
    avg_brawler_power: float
    timestamp: datetime

    model_config = {"from_attributes": True}


class BattleResponse(BaseModel):
    battle_time: datetime
    mode: str
    map_name: str | None
    result: str
    trophy_change: int
    brawler_name: str
    brawler_power: int
    is_star_player: bool
    duration: int | None

    model_config = {"from_attributes": True}


# --- Prediction schemas ---


class TopFeature(BaseModel):
    name: str
    value: float
    importance: float


class PredictionResponse(BaseModel):
    player_tag: str
    player_name: str
    outcome: str  # "gain" or "loss"
    confidence: float
    predicted_trophy_change: float | None
    top_features: list[TopFeature]
    current_trophies: int


class PredictionHistoryResponse(BaseModel):
    id: int
    predicted_at: datetime
    predicted_outcome: str | None
    confidence: float | None
    predicted_trophy_change: float | None
    actual_outcome: str | None
    actual_trophy_change: int | None

    model_config = {"from_attributes": True}


# --- Stats schemas ---


class ModelStatsResponse(BaseModel):
    is_trained: bool
    samples: int | None = None
    accuracy: float | None = None
    f1: float | None = None
    roc_auc: float | None = None
    feature_count: int | None = None
    feature_importance: dict[str, float] | None = None
    class_distribution: dict[str, int] | None = None


class DashboardStatsResponse(BaseModel):
    total_players: int
    total_battles: int
    total_predictions: int
    last_sync: datetime | None
    model_accuracy: float | None


class SyncLogResponse(BaseModel):
    id: int
    started_at: datetime
    completed_at: datetime | None
    players_synced: int
    battles_added: int
    errors: int
    status: str

    model_config = {"from_attributes": True}
