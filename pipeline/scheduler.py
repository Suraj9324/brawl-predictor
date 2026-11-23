"""Periodic data collection scheduler."""

import asyncio
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from db.session import SessionLocal
from pipeline.collector import run_collection
from pipeline.storage import (
    complete_sync_log,
    create_sync_log,
    get_tracked_tags,
    save_collection_results,
)

logger = logging.getLogger(__name__)


def sync_all_players() -> None:
    """Collect and store data for all tracked players."""
    db = SessionLocal()
    sync_log = create_sync_log(db)

    try:
        tags = get_tracked_tags(db)
        if not tags:
            logger.info("No tracked players found")
            complete_sync_log(db, sync_log, {"players_synced": 0, "battles_added": 0, "errors": 0})
            return

        logger.info(f"Starting sync for {len(tags)} players")
        results = asyncio.run(run_collection(tags))
        summary = save_collection_results(db, results)
        complete_sync_log(db, sync_log, summary)
        logger.info(f"Sync completed: {summary}")

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        complete_sync_log(db, sync_log, {"players_synced": 0, "battles_added": 0, "errors": 1}, status="failed")
    finally:
        db.close()


def start_scheduler(interval_hours: int = 2) -> None:
    """Start the periodic collection scheduler."""
    scheduler = BlockingScheduler()
    scheduler.add_job(sync_all_players, "interval", hours=interval_hours, id="sync_players")

    logger.info(f"Scheduler started — syncing every {interval_hours}h")

    # Run once immediately on startup
    sync_all_players()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    start_scheduler()
