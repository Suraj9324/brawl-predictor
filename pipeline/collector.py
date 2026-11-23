"""Fetches battle logs and player stats from the Brawl Stars API."""

import asyncio
import hashlib
import logging
from datetime import datetime

import httpx

from config import settings

logger = logging.getLogger(__name__)

BRAWL_TIME_FORMAT = "%Y%m%dT%H%M%S.%fZ"


def encode_tag(tag: str) -> str:
    """Encode a player tag for the BS API URL (# -> %23)."""
    clean = tag.strip().upper()
    if not clean.startswith("#"):
        clean = f"#{clean}"
    return clean.replace("#", "%23")


def parse_battle_time(raw: str) -> datetime:
    """Parse Brawl Stars battle time string into datetime."""
    return datetime.strptime(raw, BRAWL_TIME_FORMAT)


def make_battle_hash(player_tag: str, battle_time: str, brawler_name: str) -> str:
    """Create a unique hash for deduplicating battles."""
    key = f"{player_tag}:{battle_time}:{brawler_name}"
    return hashlib.sha256(key.encode()).hexdigest()


class BrawlStarsClient:
    """HTTP client for the Brawl Stars REST API."""

    def __init__(self) -> None:
        self.base_url = settings.brawl_stars_base_url
        self.headers = {"Authorization": f"Bearer {settings.brawl_stars_api_key}"}
        self.delay = settings.api_request_delay

    async def _get(self, path: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{path}",
                headers=self.headers,
                timeout=15.0,
            )
            if response.status_code == 404:
                raise ValueError(f"Not found: {path}")
            if response.status_code == 429:
                raise RuntimeError("Rate limited by Brawl Stars API")
            response.raise_for_status()
            return response.json()

    async def get_player(self, tag: str) -> dict:
        """Fetch a player's profile."""
        encoded = encode_tag(tag)
        return await self._get(f"/players/{encoded}")

    async def get_battlelog(self, tag: str) -> list[dict]:
        """Fetch a player's last 25 battles."""
        encoded = encode_tag(tag)
        data = await self._get(f"/players/{encoded}/battlelog")
        return data.get("items", [])

    async def collect_player_data(self, tag: str) -> dict:
        """Fetch both profile and battlelog for a player."""
        await asyncio.sleep(self.delay)
        profile = await self.get_player(tag)
        await asyncio.sleep(self.delay)
        battlelog = await self.get_battlelog(tag)
        return {"profile": profile, "battlelog": battlelog}


def parse_profile(raw: dict) -> dict:
    """Extract structured player data from API response."""
    brawlers = raw.get("brawlers", [])
    avg_power = sum(b.get("power", 1) for b in brawlers) / max(len(brawlers), 1)

    return {
        "tag": raw["tag"],
        "name": raw.get("name", "Unknown"),
        "trophies": raw.get("trophies", 0),
        "highest_trophies": raw.get("highestTrophies", 0),
        "experience_level": raw.get("expLevel", 1),
        "club_name": raw.get("club", {}).get("name"),
        "icon_id": raw.get("icon", {}).get("id", 0),
        "name_color": raw.get("nameColor"),
        "brawlers_count": len(brawlers),
        "avg_brawler_power": round(avg_power, 2),
    }


def parse_brawlers(raw: dict) -> list[dict]:
    """Extract per-brawler stats from a player profile."""
    results = []
    for b in raw.get("brawlers", []):
        results.append({
            "brawler_id": b["id"],
            "brawler_name": b.get("name", "UNKNOWN"),
            "trophies": b.get("trophies", 0),
            "highest_trophies": b.get("highestTrophies", 0),
            "power": b.get("power", 1),
            "rank": b.get("rank", 1),
            "gadgets_count": len(b.get("gadgets", [])),
            "star_powers_count": len(b.get("starPowers", [])),
            "gears_count": len(b.get("gears", [])),
        })
    return results


def parse_battlelog(player_tag: str, items: list[dict]) -> list[dict]:
    """Extract structured battle data from battlelog API response."""
    battles = []
    for item in items:
        battle = item.get("battle", {})
        event = item.get("event", {})
        battle_time_str = item.get("battleTime", "")

        result = battle.get("result")
        if result is None:
            # Some modes (like showdown) use rank instead of result
            rank = battle.get("rank")
            if rank is not None:
                result = "victory" if rank <= 4 else "defeat"
            else:
                continue

        trophy_change = battle.get("trophyChange", 0)

        # Find this player's brawler in the teams
        brawler_info = _find_player_brawler(player_tag, battle)
        if brawler_info is None:
            continue

        star_player = battle.get("starPlayer", {})
        is_star = star_player.get("tag", "") == player_tag if star_player else False

        team_size = _get_team_size(battle)

        battles.append({
            "battle_time": parse_battle_time(battle_time_str),
            "mode": event.get("mode") or battle.get("mode", "unknown"),
            "map_name": event.get("map"),
            "result": result,
            "trophy_change": trophy_change,
            "duration": battle.get("duration"),
            "brawler_id": brawler_info["id"],
            "brawler_name": brawler_info["name"],
            "brawler_power": brawler_info["power"],
            "brawler_trophies": brawler_info["trophies"],
            "is_star_player": is_star,
            "team_size": team_size,
            "battle_hash": make_battle_hash(player_tag, battle_time_str, brawler_info["name"]),
        })

    return battles


def _find_player_brawler(player_tag: str, battle: dict) -> dict | None:
    """Find the brawler used by the player in a battle."""
    # 3v3 modes: teams is a list of lists
    for team in battle.get("teams", []):
        for member in team:
            if member.get("tag") == player_tag:
                b = member.get("brawler", {})
                return {
                    "id": b.get("id", 0),
                    "name": b.get("name", "UNKNOWN"),
                    "power": b.get("power", 1),
                    "trophies": b.get("trophies", 0),
                }

    # Solo/duo showdown: players is a flat list or list of lists
    for player in battle.get("players", []):
        if isinstance(player, list):
            for p in player:
                if p.get("tag") == player_tag:
                    b = p.get("brawler", {})
                    return {
                        "id": b.get("id", 0),
                        "name": b.get("name", "UNKNOWN"),
                        "power": b.get("power", 1),
                        "trophies": b.get("trophies", 0),
                    }
        elif player.get("tag") == player_tag:
            b = player.get("brawler", {})
            return {
                "id": b.get("id", 0),
                "name": b.get("name", "UNKNOWN"),
                "power": b.get("power", 1),
                "trophies": b.get("trophies", 0),
            }

    return None


def _get_team_size(battle: dict) -> int:
    """Determine team size from battle data."""
    teams = battle.get("teams", [])
    if teams:
        return len(teams[0])
    players = battle.get("players", [])
    if players and isinstance(players[0], list):
        return len(players[0])  # duo showdown
    return 1  # solo showdown


async def run_collection(tags: list[str]) -> dict:
    """Collect data for a list of player tags. Returns summary stats."""
    client = BrawlStarsClient()
    results = {"profiles": [], "battlelogs": [], "errors": []}

    for tag in tags:
        try:
            data = await client.collect_player_data(tag)
            profile = parse_profile(data["profile"])
            brawlers = parse_brawlers(data["profile"])
            battles = parse_battlelog(tag, data["battlelog"])

            results["profiles"].append({
                "profile": profile,
                "brawlers": brawlers,
            })
            results["battlelogs"].append({
                "tag": tag,
                "battles": battles,
            })
            logger.info(f"Collected {len(battles)} battles for {tag}")
        except Exception as e:
            logger.error(f"Failed to collect data for {tag}: {e}")
            results["errors"].append({"tag": tag, "error": str(e)})

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    from db.session import SessionLocal
    from pipeline.storage import get_tracked_tags, save_collection_results

    db = SessionLocal()
    tags = get_tracked_tags(db)

    if not tags:
        print("No tracked players in DB. Add players first via the API.")
    else:
        print(f"Collecting data for {len(tags)} tracked players...")
        result = asyncio.run(run_collection(tags))
        summary = save_collection_results(db, result)
        db.close()

        print(f"Players synced: {summary['players_synced']}")
        print(f"Battles added: {summary['battles_added']}")
        print(f"Errors: {summary['errors']}")
