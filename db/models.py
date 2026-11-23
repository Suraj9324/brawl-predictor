from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    tag = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    trophies = Column(Integer, default=0)
    highest_trophies = Column(Integer, default=0)
    experience_level = Column(Integer, default=1)
    club_name = Column(String(100), nullable=True)
    icon_id = Column(Integer, default=0)
    name_color = Column(String(20), nullable=True)
    is_tracked = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_synced_at = Column(DateTime, nullable=True)

    snapshots = relationship("PlayerSnapshot", back_populates="player", cascade="all, delete-orphan")
    battles = relationship("Battle", back_populates="player", cascade="all, delete-orphan")
    brawler_stats = relationship("BrawlerStats", back_populates="player", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="player", cascade="all, delete-orphan")


class PlayerSnapshot(Base):
    __tablename__ = "player_snapshots"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    trophies = Column(Integer, nullable=False)
    highest_trophies = Column(Integer, nullable=False)
    experience_level = Column(Integer, nullable=False)
    brawlers_count = Column(Integer, default=0)
    avg_brawler_power = Column(Float, default=0.0)
    timestamp = Column(DateTime, server_default=func.now())

    player = relationship("Player", back_populates="snapshots")


class Battle(Base):
    __tablename__ = "battles"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    battle_time = Column(DateTime, nullable=False)
    mode = Column(String(50), nullable=False)
    map_name = Column(String(100), nullable=True)
    result = Column(String(20), nullable=False)  # victory, defeat, draw
    trophy_change = Column(Integer, default=0)
    duration = Column(Integer, nullable=True)
    brawler_id = Column(Integer, nullable=False)
    brawler_name = Column(String(50), nullable=False)
    brawler_power = Column(Integer, default=1)
    brawler_trophies = Column(Integer, default=0)
    is_star_player = Column(Boolean, default=False)
    team_size = Column(Integer, default=3)
    battle_hash = Column(String(64), unique=True, nullable=False)

    player = relationship("Player", back_populates="battles")


class BrawlerStats(Base):
    __tablename__ = "brawler_stats"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    brawler_id = Column(Integer, nullable=False)
    brawler_name = Column(String(50), nullable=False)
    trophies = Column(Integer, default=0)
    highest_trophies = Column(Integer, default=0)
    power = Column(Integer, default=1)
    rank = Column(Integer, default=1)
    gadgets_count = Column(Integer, default=0)
    star_powers_count = Column(Integer, default=0)
    gears_count = Column(Integer, default=0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    player = relationship("Player", back_populates="brawler_stats")

    __table_args__ = (
        UniqueConstraint("player_id", "brawler_id", name="uq_player_brawler"),
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    predicted_at = Column(DateTime, server_default=func.now())
    prediction_type = Column(String(20), nullable=False)  # classification, regression
    predicted_outcome = Column(String(10), nullable=True)  # gain, loss
    predicted_trophy_change = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    top_features = Column(Text, nullable=True)  # JSON string
    actual_outcome = Column(String(10), nullable=True)
    actual_trophy_change = Column(Integer, nullable=True)

    player = relationship("Player", back_populates="predictions")


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    players_synced = Column(Integer, default=0)
    battles_added = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    status = Column(String(20), default="running")  # running, completed, failed
