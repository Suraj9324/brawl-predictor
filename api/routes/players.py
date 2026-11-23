"""Player management routes."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas import AddPlayerRequest, BattleResponse, PlayerDetailResponse, PlayerResponse, SnapshotResponse
from db.models import Battle, BrawlerStats, Player, PlayerSnapshot
from db.session import get_db
from pipeline.collector import BrawlStarsClient, parse_battlelog, parse_brawlers, parse_profile
from pipeline.storage import save_battles, save_snapshot, upsert_brawler_stats, upsert_player

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/", response_model=list[PlayerResponse])
def list_players(db: Session = Depends(get_db)):
    """List all tracked players."""
    players = (
        db.query(Player)
        .filter(Player.is_tracked == True)
        .order_by(Player.trophies.desc())
        .all()
    )
    return players


@router.post("/", response_model=PlayerResponse, status_code=201)
async def add_player(body: AddPlayerRequest, db: Session = Depends(get_db)):
    """Add a player to track."""
    tag = body.tag.strip().upper()
    if not tag.startswith("#"):
        tag = f"#{tag}"

    existing = db.query(Player).filter(Player.tag == tag).first()
    if existing:
        if not existing.is_tracked:
            existing.is_tracked = True
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(status_code=409, detail="Player already tracked")

    # Fetch profile + battles from Brawl Stars API
    client = BrawlStarsClient()
    try:
        raw = await client.get_player(tag)
        raw_battlelog = await client.get_battlelog(tag)
    except ValueError:
        raise HTTPException(status_code=404, detail="Player not found on Brawl Stars")
    except RuntimeError:
        raise HTTPException(status_code=429, detail="Rate limited, try again later")

    profile = parse_profile(raw)
    brawlers = parse_brawlers(raw)
    battles = parse_battlelog(tag, raw_battlelog)

    player = upsert_player(db, profile)
    save_snapshot(db, player, profile)
    upsert_brawler_stats(db, player.id, brawlers)
    save_battles(db, player.id, battles)
    db.commit()
    db.refresh(player)

    return player


@router.get("/{tag:path}", response_model=PlayerDetailResponse)
def get_player(tag: str, db: Session = Depends(get_db)):
    """Get detailed player info with snapshots and recent battles."""
    clean_tag = tag.strip().upper()
    if not clean_tag.startswith("#"):
        clean_tag = f"#{clean_tag}"

    player = db.query(Player).filter(Player.tag == clean_tag).first()
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    snapshots = (
        db.query(PlayerSnapshot)
        .filter(PlayerSnapshot.player_id == player.id)
        .order_by(PlayerSnapshot.timestamp.desc())
        .limit(30)
        .all()
    )

    battles = (
        db.query(Battle)
        .filter(Battle.player_id == player.id)
        .order_by(Battle.battle_time.desc())
        .limit(25)
        .all()
    )

    brawler_count = db.query(BrawlerStats).filter(BrawlerStats.player_id == player.id).count()

    return PlayerDetailResponse(
        id=player.id,
        tag=player.tag,
        name=player.name,
        trophies=player.trophies,
        highest_trophies=player.highest_trophies,
        experience_level=player.experience_level,
        club_name=player.club_name,
        is_tracked=player.is_tracked,
        last_synced_at=player.last_synced_at,
        created_at=player.created_at,
        snapshots=[SnapshotResponse.model_validate(s) for s in snapshots],
        recent_battles=[BattleResponse.model_validate(b) for b in battles],
        brawler_count=brawler_count,
    )


@router.delete("/{tag:path}", status_code=204)
def remove_player(tag: str, db: Session = Depends(get_db)):
    """Stop tracking a player (soft delete)."""
    clean_tag = tag.strip().upper()
    if not clean_tag.startswith("#"):
        clean_tag = f"#{clean_tag}"

    player = db.query(Player).filter(Player.tag == clean_tag).first()
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    player.is_tracked = False
    db.commit()
