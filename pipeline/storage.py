"""Database operations for saving collected data."""

import logging
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from db.models import Battle, BrawlerStats, Player, PlayerSnapshot, SyncLog

logger = logging.getLogger(__name__)


def upsert_player(db: Session, profile: dict) -> Player:
    """Create or update a player record."""
    player = db.query(Player).filter(Player.tag == profile["tag"]).first()

    if player is None:
        player = Player(
            tag=profile["tag"],
            name=profile["name"],
            trophies=profile["trophies"],
            highest_trophies=profile["highest_trophies"],
            experience_level=profile["experience_level"],
            club_name=profile["club_name"],
            icon_id=profile["icon_id"],
            name_color=profile["name_color"],
            last_synced_at=datetime.utcnow(),
        )
        db.add(player)
    else:
        player.name = profile["name"]
        player.trophies = profile["trophies"]
        player.highest_trophies = profile["highest_trophies"]
        player.experience_level = profile["experience_level"]
        player.club_name = profile["club_name"]
        player.icon_id = profile["icon_id"]
        player.name_color = profile["name_color"]
        player.last_synced_at = datetime.utcnow()

    db.flush()
    return player


def save_snapshot(db: Session, player: Player, profile: dict) -> PlayerSnapshot:
    """Save a trophy snapshot for a player."""
    snapshot = PlayerSnapshot(
        player_id=player.id,
        trophies=profile["trophies"],
        highest_trophies=profile["highest_trophies"],
        experience_level=profile["experience_level"],
        brawlers_count=profile["brawlers_count"],
        avg_brawler_power=profile["avg_brawler_power"],
    )
    db.add(snapshot)
    return snapshot


def save_battles(db: Session, player_id: int, battles: list[dict]) -> int:
    """Save battles, skipping duplicates. Returns count of new battles."""
    added = 0
    for b in battles:
        exists = db.query(Battle.id).filter(Battle.battle_hash == b["battle_hash"]).first()
        if exists:
            continue

        battle = Battle(
            player_id=player_id,
            battle_time=b["battle_time"],
            mode=b["mode"],
            map_name=b["map_name"],
            result=b["result"],
            trophy_change=b["trophy_change"],
            duration=b["duration"],
            brawler_id=b["brawler_id"],
            brawler_name=b["brawler_name"],
            brawler_power=b["brawler_power"],
            brawler_trophies=b["brawler_trophies"],
            is_star_player=b["is_star_player"],
            team_size=b["team_size"],
            battle_hash=b["battle_hash"],
        )
        db.add(battle)
        added += 1

    return added


def upsert_brawler_stats(db: Session, player_id: int, brawlers: list[dict]) -> None:
    """Create or update brawler stats for a player."""
    for b in brawlers:
        existing = (
            db.query(BrawlerStats)
            .filter(BrawlerStats.player_id == player_id, BrawlerStats.brawler_id == b["brawler_id"])
            .first()
        )
        if existing:
            existing.brawler_name = b["brawler_name"]
            existing.trophies = b["trophies"]
            existing.highest_trophies = b["highest_trophies"]
            existing.power = b["power"]
            existing.rank = b["rank"]
            existing.gadgets_count = b["gadgets_count"]
            existing.star_powers_count = b["star_powers_count"]
            existing.gears_count = b["gears_count"]
        else:
            db.add(BrawlerStats(player_id=player_id, **b))


def save_collection_results(db: Session, results: dict) -> dict:
    """Persist all collected data and return summary."""
    total_battles = 0
    total_players = 0
    total_errors = len(results.get("errors", []))

    for entry in results.get("profiles", []):
        profile = entry["profile"]
        brawlers = entry["brawlers"]

        player = upsert_player(db, profile)
        save_snapshot(db, player, profile)
        upsert_brawler_stats(db, player.id, brawlers)
        total_players += 1

    for entry in results.get("battlelogs", []):
        tag = entry["tag"]
        player = db.query(Player).filter(Player.tag == tag).first()
        if player is None:
            continue
        added = save_battles(db, player.id, entry["battles"])
        total_battles += added

    db.commit()

    summary = {
        "players_synced": total_players,
        "battles_added": total_battles,
        "errors": total_errors,
    }
    logger.info(f"Collection saved: {summary}")
    return summary


def create_sync_log(db: Session) -> SyncLog:
    """Create a new sync log entry."""
    log = SyncLog(status="running")
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def complete_sync_log(db: Session, log: SyncLog, summary: dict, status: str = "completed") -> None:
    """Update a sync log with results."""
    log.completed_at = datetime.utcnow()
    log.players_synced = summary.get("players_synced", 0)
    log.battles_added = summary.get("battles_added", 0)
    log.errors = summary.get("errors", 0)
    log.status = status
    db.commit()


def get_tracked_tags(db: Session) -> list[str]:
    """Get all tracked player tags."""
    players = db.query(Player.tag).filter(Player.is_tracked == True).all()
    return [p.tag for p in players]
