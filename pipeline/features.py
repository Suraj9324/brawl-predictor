"""Feature engineering: transform raw battle logs and player data into ML features."""

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from db.models import Battle, BrawlerStats, Player, PlayerSnapshot


def build_player_features(db: Session, player_id: int) -> dict | None:
    """Build a complete feature vector for a player.

    Returns None if insufficient data.
    """
    player = db.query(Player).filter(Player.id == player_id).first()
    if player is None:
        return None

    battles = (
        db.query(Battle)
        .filter(Battle.player_id == player_id)
        .order_by(Battle.battle_time.desc())
        .all()
    )

    if len(battles) < 5:
        return None

    brawler_stats = db.query(BrawlerStats).filter(BrawlerStats.player_id == player_id).all()

    features = {}

    # --- Player-level features ---
    features["trophies"] = player.trophies
    features["highest_trophies"] = player.highest_trophies
    features["trophy_ratio"] = player.trophies / max(player.highest_trophies, 1)
    features["experience_level"] = player.experience_level
    features["brawlers_unlocked"] = len(brawler_stats)
    features["avg_brawler_power"] = (
        np.mean([b.power for b in brawler_stats]) if brawler_stats else 0.0
    )
    features["has_club"] = 1 if player.club_name else 0

    # --- Recent performance (last 10 battles) ---
    last_10 = battles[:10]
    features["win_rate_10"] = _win_rate(last_10)
    features["avg_trophy_change_10"] = np.mean([b.trophy_change for b in last_10])

    # --- Recent performance (last 25 battles) ---
    last_25 = battles[:25]
    features["win_rate_25"] = _win_rate(last_25)
    features["avg_trophy_change_25"] = np.mean([b.trophy_change for b in last_25])

    # --- Streaks ---
    win_streak, loss_streak = _current_streaks(battles)
    features["win_streak"] = win_streak
    features["loss_streak"] = loss_streak

    # --- Most played brawler stats ---
    most_played = _most_played_brawler(last_25)
    features["most_played_brawler_winrate"] = most_played["win_rate"]
    features["most_played_brawler_games"] = most_played["games"]

    # --- Mode diversity ---
    modes = set(b.mode for b in last_25)
    features["mode_diversity"] = len(modes)

    # --- Performance trend (slope of trophy changes over last 25) ---
    trophy_changes = [b.trophy_change for b in reversed(last_25)]
    features["performance_trend"] = _compute_trend(trophy_changes)

    # --- Star player rate ---
    features["star_player_rate"] = sum(1 for b in last_25 if b.is_star_player) / len(last_25)

    # --- Average match duration ---
    durations = [b.duration for b in last_25 if b.duration is not None]
    features["avg_duration"] = np.mean(durations) if durations else 0.0

    # --- Brawler-level features (most recently used) ---
    latest_brawler_id = battles[0].brawler_id
    brawler = next((b for b in brawler_stats if b.brawler_id == latest_brawler_id), None)
    if brawler:
        features["latest_brawler_trophies"] = brawler.trophies
        features["latest_brawler_power"] = brawler.power
        features["latest_brawler_rank"] = brawler.rank
        features["latest_brawler_gadgets"] = brawler.gadgets_count
        features["latest_brawler_star_powers"] = brawler.star_powers_count
    else:
        features["latest_brawler_trophies"] = 0
        features["latest_brawler_power"] = 1
        features["latest_brawler_rank"] = 1
        features["latest_brawler_gadgets"] = 0
        features["latest_brawler_star_powers"] = 0

    # --- Personal win rate with latest brawler ---
    brawler_battles = [b for b in last_25 if b.brawler_id == latest_brawler_id]
    features["latest_brawler_personal_winrate"] = _win_rate(brawler_battles) if brawler_battles else 0.5

    return features


def build_training_dataset(db: Session) -> pd.DataFrame:
    """Build training dataset from all tracked players.

    Each row represents a player at a point in time, with features computed
    from battles BEFORE that point and the target being the outcome of
    the next 5 battles.
    """
    players = db.query(Player).filter(Player.is_tracked == True).all()
    rows = []

    for player in players:
        battles = (
            db.query(Battle)
            .filter(Battle.player_id == player.id)
            .order_by(Battle.battle_time.asc())
            .all()
        )

        if len(battles) < 15:
            continue

        brawler_stats = db.query(BrawlerStats).filter(BrawlerStats.player_id == player.id).all()

        # Create samples using sliding window
        # For each position where we have 10+ past battles and 5 future battles
        for i in range(10, len(battles) - 5):
            past_battles = list(reversed(battles[:i]))  # Most recent first
            future_battles = battles[i:i + 5]

            features = _features_from_battles(player, past_battles, brawler_stats)
            if features is None:
                continue

            # Target: net trophy change over next 5 battles
            trophy_sum = sum(b.trophy_change for b in future_battles)
            features["target_trophy_change"] = trophy_sum
            features["target_gain"] = 1 if trophy_sum > 0 else 0

            rows.append(features)

    return pd.DataFrame(rows)


def _features_from_battles(player: Player, battles: list, brawler_stats: list) -> dict | None:
    """Compute features from a list of battles (ordered most recent first)."""
    if len(battles) < 10:
        return None

    features = {}

    features["trophies"] = player.trophies
    features["highest_trophies"] = player.highest_trophies
    features["trophy_ratio"] = player.trophies / max(player.highest_trophies, 1)
    features["experience_level"] = player.experience_level
    features["brawlers_unlocked"] = len(brawler_stats)
    features["avg_brawler_power"] = (
        np.mean([b.power for b in brawler_stats]) if brawler_stats else 0.0
    )
    features["has_club"] = 1 if player.club_name else 0

    last_10 = battles[:10]
    features["win_rate_10"] = _win_rate(last_10)
    features["avg_trophy_change_10"] = np.mean([b.trophy_change for b in last_10])

    last_25 = battles[:25]
    features["win_rate_25"] = _win_rate(last_25)
    features["avg_trophy_change_25"] = np.mean([b.trophy_change for b in last_25])

    win_streak, loss_streak = _current_streaks(battles)
    features["win_streak"] = win_streak
    features["loss_streak"] = loss_streak

    most_played = _most_played_brawler(last_25)
    features["most_played_brawler_winrate"] = most_played["win_rate"]
    features["most_played_brawler_games"] = most_played["games"]

    modes = set(b.mode for b in last_25)
    features["mode_diversity"] = len(modes)

    trophy_changes = [b.trophy_change for b in reversed(last_25)]
    features["performance_trend"] = _compute_trend(trophy_changes)

    features["star_player_rate"] = sum(1 for b in last_25 if b.is_star_player) / len(last_25)

    durations = [b.duration for b in last_25 if b.duration is not None]
    features["avg_duration"] = np.mean(durations) if durations else 0.0

    latest_brawler_id = battles[0].brawler_id
    brawler = next((b for b in brawler_stats if b.brawler_id == latest_brawler_id), None)
    if brawler:
        features["latest_brawler_trophies"] = brawler.trophies
        features["latest_brawler_power"] = brawler.power
        features["latest_brawler_rank"] = brawler.rank
        features["latest_brawler_gadgets"] = brawler.gadgets_count
        features["latest_brawler_star_powers"] = brawler.star_powers_count
    else:
        features["latest_brawler_trophies"] = 0
        features["latest_brawler_power"] = 1
        features["latest_brawler_rank"] = 1
        features["latest_brawler_gadgets"] = 0
        features["latest_brawler_star_powers"] = 0

    brawler_battles = [b for b in last_25 if b.brawler_id == latest_brawler_id]
    features["latest_brawler_personal_winrate"] = _win_rate(brawler_battles) if brawler_battles else 0.5

    return features


# --- Helper functions ---


def _win_rate(battles: list) -> float:
    if not battles:
        return 0.5
    wins = sum(1 for b in battles if b.result == "victory")
    return wins / len(battles)


def _current_streaks(battles: list) -> tuple[int, int]:
    """Calculate current win and loss streaks (battles ordered most recent first)."""
    win_streak = 0
    loss_streak = 0

    for b in battles:
        if b.result == "victory":
            if loss_streak > 0:
                break
            win_streak += 1
        elif b.result == "defeat":
            if win_streak > 0:
                break
            loss_streak += 1
        else:
            break

    return win_streak, loss_streak


def _most_played_brawler(battles: list) -> dict:
    """Find most played brawler and their win rate in given battles."""
    if not battles:
        return {"win_rate": 0.5, "games": 0}

    counts: dict[int, dict] = {}
    for b in battles:
        if b.brawler_id not in counts:
            counts[b.brawler_id] = {"wins": 0, "total": 0}
        counts[b.brawler_id]["total"] += 1
        if b.result == "victory":
            counts[b.brawler_id]["wins"] += 1

    most = max(counts.values(), key=lambda x: x["total"])
    return {
        "win_rate": most["wins"] / most["total"],
        "games": most["total"],
    }


def _compute_trend(values: list[float]) -> float:
    """Compute linear regression slope as a trend indicator."""
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values))
    coeffs = np.polyfit(x, values, 1)
    return float(coeffs[0])


FEATURE_COLUMNS = [
    "trophies",
    "highest_trophies",
    "trophy_ratio",
    "experience_level",
    "brawlers_unlocked",
    "avg_brawler_power",
    "has_club",
    "win_rate_10",
    "avg_trophy_change_10",
    "win_rate_25",
    "avg_trophy_change_25",
    "win_streak",
    "loss_streak",
    "most_played_brawler_winrate",
    "most_played_brawler_games",
    "mode_diversity",
    "performance_trend",
    "star_player_rate",
    "avg_duration",
    "latest_brawler_trophies",
    "latest_brawler_power",
    "latest_brawler_rank",
    "latest_brawler_gadgets",
    "latest_brawler_star_powers",
    "latest_brawler_personal_winrate",
]
