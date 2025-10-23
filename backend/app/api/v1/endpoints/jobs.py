from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from app.models.schemas import Job, JobDetails, JobCreate, JobFilter, JobStatus, APIResponse
from app.services.job_service import job_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[Job])
async def get_jobs(
    status: Optional[JobStatus] = None,
    cluster: Optional[str] = None,
    search: Optional[str] = None
):
    """Get all jobs with optional filtering"""
    try:
        filter_params = JobFilter(status=status, cluster=cluster, search=search)
        jobs = await job_service.get_all_jobs(filter_params)
        return jobs
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=JobDetails)
async def get_job(job_id: str):
    """Get specific job details"""
    try:
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=JobDetails)
async def create_job(job_data: JobCreate):
    """Submit a new Spark job"""
    try:
        job = await job_service.create_job(job_data)
        return job
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/kill", response_model=APIResponse)
async def kill_job(job_id: str):
    """Kill a running job"""
    try:
        success = await job_service.kill_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return APIResponse(
            success=True,
            message=f"Job {job_id} killed successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error killing job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/restart", response_model=JobDetails)
async def restart_job(job_id: str):
    """Restart a job"""
    try:
        job = await job_service.restart_job(job_id)
        return job
    except Exception as e:
        logger.error(f"Error restarting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/logs")
async def get_job_logs(job_id: str):
    """Get job logs"""
    try:
        logs = await job_service.get_job_logs(job_id)
        return {"job_id": job_id, "logs": logs}
    except Exception as e:
        logger.error(f"Error getting logs for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/spark-ui")
async def get_spark_ui(job_id: str):
    """Get Spark UI URL for job"""
    try:
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return {
            "job_id": job_id,
            "spark_ui_url": job.spark_ui_url
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Spark UI for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
