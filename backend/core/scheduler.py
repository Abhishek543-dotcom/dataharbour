"""
APScheduler wrapper
===================
Provides a ready-to-use AsyncIOScheduler for background / cron tasks.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger("dataharbour.scheduler")

_scheduler: "AsyncIOScheduler" = None


def get_scheduler() -> AsyncIOScheduler:
    """Return the global scheduler instance (lazily created)."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


def start_scheduler():
    """Start the scheduler if not already running."""
    sched = get_scheduler()
    if not sched.running:
        sched.start()
        logger.info("APScheduler started")


def shutdown_scheduler():
    """Gracefully shut down the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down")
    _scheduler = None


def add_job(func, trigger, **kwargs):
    """Convenience wrapper — add a job to the running scheduler."""
    sched = get_scheduler()
    sched.add_job(func, trigger, **kwargs)
    logger.info("Scheduled job: %s with trigger %s", func.__name__, trigger)
