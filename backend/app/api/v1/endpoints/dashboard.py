from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
import logging

from app.models.schemas import DashboardStats, JobTrends, APIResponse, User
from app.services.spark_service import spark_service
from app.services.job_service import job_service
from app.services.notebook_service import notebook_service
from app.db.session import get_db
from app.api.dependencies import get_optional_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get overall dashboard statistics"""
    try:
        user_id = str(current_user.id) if current_user else None

        # Get job statistics
        all_jobs = await job_service.get_all_jobs(db, user_id=user_id)

        running_jobs = len([j for j in all_jobs if j.status == "running"])
        completed_jobs = len([j for j in all_jobs if j.status == "completed"])
        failed_jobs = len([j for j in all_jobs if j.status == "failed"])

        # Get cluster statistics
        clusters = await spark_service.get_clusters(db, user_id)
        active_clusters = len([c for c in clusters if c.status == "running"])

        # Get notebook count from database
        total_notebooks = await notebook_service.get_notebook_count(db, user_id)

        return DashboardStats(
            total_notebooks=total_notebooks,
            total_jobs=len(all_jobs),
            active_clusters=active_clusters,
            running_jobs=running_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs
        )
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends", response_model=JobTrends)
async def get_job_trends(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get job completion trends for the last 7 days"""
    try:
        user_id = str(current_user.id) if current_user else None

        # Generate last 7 days
        today = datetime.now()
        labels = []
        completed = []
        failed = []

        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            labels.append(date.strftime("%a"))

            # Get jobs for this day
            day_jobs = await job_service.get_jobs_by_date(db, date, user_id)
            completed.append(len([j for j in day_jobs if j.status == "completed"]))
            failed.append(len([j for j in day_jobs if j.status == "failed"]))

        return JobTrends(
            labels=labels,
            completed=completed,
            failed=failed
        )
    except Exception as e:
        logger.error(f"Error getting job trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview")
async def get_overview(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get complete dashboard overview"""
    try:
        stats = await get_dashboard_stats(db, current_user)
        trends = await get_job_trends(db, current_user)

        return {
            "stats": stats,
            "trends": trends,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))
