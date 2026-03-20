"""
Dashboard & Stats Routes
========================
GET /stats/summary       — Aggregated platform metrics
GET /activities/recent   — Last 10 activities (jobs + notebooks)
"""

import logging
import os
from datetime import datetime

from fastapi import APIRouter

from api.helpers import get_db, get_s3_client, load_registry, release_db
from core.config import Config

logger = logging.getLogger("dataharbour.routes.dashboard")
router = APIRouter(tags=["Dashboard"])


@router.get("/stats/summary")
def get_stats_summary():
    """Aggregate counts for the dashboard overview panel."""

    # Notebooks count
    notebooks_count = 0
    if os.path.exists(Config.notebooks_dir):
        with os.scandir(Config.notebooks_dir) as it:
            notebooks_count = sum(
                1 for entry in it if entry.is_file() and entry.name.endswith(".ipynb")
            )

    # Job counts
    registry = load_registry()
    jobs_count = len(registry)
    jobs_running = sum(
        1 for j in registry.values() if j.get("status") in ("SUBMITTED", "RUNNING")
    )
    jobs_failed = sum(
        1 for j in registry.values() if j.get("status") in ("FAILED", "ERROR")
    )

    # Buckets count (graceful)
    buckets_count = 0
    try:
        buckets_count = len(get_s3_client().list_buckets().get("Buckets", []))
    except Exception:
        pass

    # Database count (graceful)
    databases_count = 0
    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT count(*) FROM pg_database "
            "WHERE datistemplate = false AND datname NOT IN ('postgres')"
        )
        databases_count = cursor.fetchone()[0]
    except Exception:
        pass
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db(conn)

    return {
        "notebooks": notebooks_count,
        "jobs": jobs_count,
        "jobsRunning": jobs_running,
        "jobsFailed": jobs_failed,
        "buckets": buckets_count,
        "databases": databases_count,
    }


@router.get("/activities/recent")
def get_recent_activities():
    """Return the 10 most recent activities across notebooks and jobs."""
    activities = []

    # Notebook activities
    if os.path.exists(Config.notebooks_dir):
        with os.scandir(Config.notebooks_dir) as it:
            for entry in it:
                if entry.is_file() and entry.name.endswith(".ipynb"):
                    stat = entry.stat()
                    activities.append({
                        "type": "notebook",
                        "action": "Modified",
                        "name": entry.name,
                        "time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })

    # Job activities
    for job in load_registry().values():
        activities.append({
            "type": "job",
            "action": "Submitted",
            "name": job.get("filename", job["job_id"]),
            "status": job.get("status"),
            "job_id": job["job_id"],
            "time": job.get("submitted_at", ""),
        })

    activities.sort(key=lambda x: x.get("time", ""), reverse=True)
    return {"activities": activities[:10]}

