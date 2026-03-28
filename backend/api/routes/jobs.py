"""
Spark Job Routes
================
POST   /jobs/submit          — Upload & submit a PySpark script
GET    /jobs                  — List all jobs (optional status filter)
GET    /jobs/running          — List active jobs
GET    /jobs/pending          — List queued jobs
GET    /jobs/completed        — List terminal-state jobs
GET    /jobs/{job_id}/status  — Single job status (live Spark query)
GET    /jobs/{job_id}/logs    — Job stdout/stderr logs
DELETE /jobs/{job_id}         — Kill a running job
"""

import logging
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from api.helpers import (
    TERMINAL_STATES,
    load_registry,
    upsert_job,
)
from core.config import Config
from core.spark_client import fetch_spark_logs, spark_kill, spark_status, spark_submit

logger = logging.getLogger("dataharbour.routes.jobs")
router = APIRouter(prefix="/jobs", tags=["Jobs (Spark)"])


# ──────────────────────────────────────────────────────
#  Submit
# ──────────────────────────────────────────────────────

@router.post("/submit")
def submit_job(file: UploadFile = File(...)):
    """
    Upload a PySpark ``.py`` script and submit it to the Spark cluster.

    The file is saved to the shared ``/workspace/jobs/`` volume so the Spark
    worker can read it.  Submission runs via ``docker exec spark-submit``
    inside the ``spark-master`` container.

    Returns ``job_id`` for subsequent ``/status`` and ``/logs`` polling.
    """
    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py PySpark scripts are accepted")

    os.makedirs(Config.jobs_dir, exist_ok=True)
    os.makedirs(Config.logs_dir, exist_ok=True)

    job_id = str(uuid.uuid4())
    file_path = os.path.join(Config.jobs_dir, f"{job_id}_{file.filename}")
    app_name = f"DataHarbour-{job_id[:8]}"

    # Save uploaded file
    with open(file_path, "wb") as fh:
        fh.write(file.file.read())

    # Submit to Spark — rolls back on failure
    try:
        spark_resp = spark_submit(job_id, file_path, app_name)
    except RuntimeError as exc:
        os.remove(file_path)
        raise HTTPException(status_code=503, detail=str(exc))

    submission_id = spark_resp.get("submissionId")

    record = upsert_job(
        job_id,
        filename=file.filename,
        file_path=file_path,
        submitted_at=datetime.utcnow().isoformat(),
        status="SUBMITTED",
        spark_submission_id=submission_id,
        worker_host_port=None,
    )

    logger.info("Job submitted: %s (%s)", job_id, file.filename)

    return {
        "job_id": job_id,
        "spark_submission_id": submission_id,
        "filename": file.filename,
        "submitted_at": record.get("submitted_at"),
        "status": "SUBMITTED",
    }


# ──────────────────────────────────────────────────────
#  List
# ──────────────────────────────────────────────────────

@router.get("")
def list_jobs(
    status: str = Query(
        None,
        description="Filter: SUBMITTED | RUNNING | FINISHED | FAILED | KILLED | ERROR",
    ),
):
    """List all jobs with live status refresh for non-terminal jobs."""
    registry = load_registry()
    jobs = []

    for job_id, job in registry.items():
        sub_id = job.get("spark_submission_id")
        if sub_id and job.get("status") not in TERMINAL_STATES:
            spark = spark_status(sub_id)
            if spark:
                new_state = spark.get("driverState", job["status"])
                if new_state != job["status"]:
                    job["status"] = new_state
                    job["worker_host_port"] = spark.get("workerHostPort")
                    upsert_job(job_id, status=new_state, worker_host_port=job["worker_host_port"])

        if status is None or job.get("status", "").upper() == status.upper():
            jobs.append(job)

    jobs.sort(key=lambda j: j.get("submitted_at", ""), reverse=True)
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/running")
def get_running_jobs():
    """Return all jobs currently in SUBMITTED or RUNNING state."""
    result = list_jobs(status=None)
    active = [j for j in result["jobs"] if j.get("status") in ("SUBMITTED", "RUNNING")]
    return {"running_jobs": active, "count": len(active)}


@router.get("/pending")
def get_pending_jobs():
    """Return jobs queued but not yet picked up by a worker."""
    registry = load_registry()
    pending = [j for j in registry.values() if j.get("status") == "SUBMITTED"]
    return {"pending_jobs": pending, "count": len(pending)}


@router.get("/completed")
def get_completed_jobs():
    """Return all terminal-state jobs: FINISHED, FAILED, KILLED, ERROR."""
    registry = load_registry()
    completed = [j for j in registry.values() if j.get("status") in TERMINAL_STATES]
    completed.sort(key=lambda j: j.get("submitted_at", ""), reverse=True)
    return {"completed_jobs": completed, "count": len(completed)}


# ──────────────────────────────────────────────────────
#  Single Job — Status / Logs / Kill
# ──────────────────────────────────────────────────────

@router.get("/{job_id}/status")
def get_job_status(job_id: str):
    """
    Return the current status of a single job.

    Queries the Spark process tracker live for non-terminal jobs.
    Includes a ``source`` field (``spark`` or ``registry``) so the caller
    knows whether the status was refreshed.
    """
    registry = load_registry()
    if job_id not in registry:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    job = registry[job_id]
    sub_id = job.get("spark_submission_id")
    source = "registry"

    if sub_id and job.get("status") not in TERMINAL_STATES:
        spark = spark_status(sub_id)
        if spark:
            job["status"] = spark.get("driverState", job["status"])
            job["worker_host_port"] = spark.get("workerHostPort")
            upsert_job(job_id, status=job["status"], worker_host_port=job["worker_host_port"])
            source = "spark"

    return {
        "job_id": job_id,
        "spark_submission_id": sub_id,
        "filename": job.get("filename"),
        "file_path": job.get("file_path"),
        "submitted_at": job.get("submitted_at"),
        "status": job.get("status", "UNKNOWN"),
        "worker_host_port": job.get("worker_host_port"),
        "source": source,
    }


@router.get("/{job_id}/logs")
def get_job_logs(
    job_id: str,
    tail: int = Query(200, ge=1, le=5000, description="Lines to return from the end"),
    log_type: str = Query("stdout", description="'stdout' or 'stderr'"),
):
    """
    Return the last *tail* lines from a job's driver log.

    Resolution order:
      1. Captured log file from spark-submit execution
      2. Local ``/workspace/logs/{job_id}.log`` fallback
      3. Empty response (job may still be starting)
    """
    registry = load_registry()
    if job_id not in registry:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    job = registry[job_id]
    sub_id = job.get("spark_submission_id")

    # Refresh status if needed
    worker_host_port = job.get("worker_host_port")
    if sub_id and not worker_host_port:
        spark = spark_status(sub_id)
        if spark:
            worker_host_port = spark.get("workerHostPort")
            job["worker_host_port"] = worker_host_port
            job["status"] = spark.get("driverState", job.get("status"))
            upsert_job(job_id, status=job["status"], worker_host_port=worker_host_port)

    log_content = None
    log_source = "none"

    # 1. Captured spark-submit logs
    if sub_id:
        log_content = fetch_spark_logs(sub_id, log_type)
        if log_content:
            log_source = f"captured ({log_type})"

    # 2. Local .log fallback
    if not log_content:
        local_log = os.path.join(Config.logs_dir, f"{job_id}.log")
        if os.path.exists(local_log):
            with open(local_log, "r", errors="replace") as f:
                log_content = f.read()
            log_source = "local_file"

    if not log_content:
        return {
            "job_id": job_id,
            "spark_submission_id": sub_id,
            "filename": job.get("filename"),
            "submitted_at": job.get("submitted_at"),
            "status": job.get("status"),
            "log_source": "none",
            "line_count": 0,
            "logs": "",
            "message": (
                "No logs available yet. "
                "The Spark driver may still be starting, "
                "or the worker UI is unreachable."
            ),
        }

    lines = log_content.splitlines(keepends=True)
    if len(lines) > tail:
        lines = lines[-tail:]

    return {
        "job_id": job_id,
        "spark_submission_id": sub_id,
        "filename": job.get("filename"),
        "submitted_at": job.get("submitted_at"),
        "status": job.get("status"),
        "log_source": log_source,
        "line_count": len(lines),
        "logs": "".join(lines),
    }


@router.delete("/{job_id}")
def cancel_job(job_id: str):
    """Kill a RUNNING or SUBMITTED job."""
    registry = load_registry()
    if job_id not in registry:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    job = registry[job_id]
    sub_id = job.get("spark_submission_id")

    if job.get("status") in TERMINAL_STATES:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel — job is already '{job.get('status')}'",
        )
    if not sub_id:
        raise HTTPException(status_code=400, detail="No Spark submission ID recorded for this job")

    if not spark_kill(sub_id):
        raise HTTPException(
            status_code=502,
            detail="Spark kill request failed — master may be unreachable",
        )

    upsert_job(job_id, status="KILLED")
    logger.info("Job killed: %s", job_id)
    return {"message": f"Job '{job_id}' killed", "spark_submission_id": sub_id}

