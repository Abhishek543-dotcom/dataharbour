"""
DataHarbour API Routes
======================
Job submission uses the Spark Standalone REST API (port 6066) because the
FastAPI container is python:3.9-slim — no Java, no spark-submit binary.

Submit flow
-----------
  POST /jobs/submit
    1. Save .py file to /workspace/jobs/{job_id}_{filename}   (shared volume)
    2. POST http://spark-master:6066/v1/submissions/create
       → Spark assigns a submissionId, runs the driver on a worker
    3. Store job_id → submissionId in the registry JSON

Status flow
-----------
  GET /jobs/{job_id}/status
    → GET http://spark-master:6066/v1/submissions/status/{submissionId}
    → driverState: SUBMITTED | RUNNING | FINISHED | FAILED | KILLED | ERROR

Log flow
--------
  GET /jobs/{job_id}/logs
    1. Spark status response returns workerHostPort (e.g. spark-worker-1:8081)
    2. Fetch http://{workerHostPort}/logPage?driverId={submissionId}&logType=stdout
    3. Fall back to /workspace/logs/{job_id}.log if worker UI is unreachable

Kill flow
---------
  DELETE /jobs/{job_id}
    → POST http://spark-master:6066/v1/submissions/kill/{submissionId}
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import boto3
from botocore.exceptions import ClientError
import psycopg2
from psycopg2 import sql
import requests
import os
import json
import uuid
from datetime import datetime
from core.config import Config

router = APIRouter()

# ─────────────────────────────────────────────────────────────
# Directory constants (shared Docker volume)
# ─────────────────────────────────────────────────────────────
JOBS_DIR          = "/workspace/jobs"
LOGS_DIR          = "/workspace/logs"
NOTEBOOKS_DIR     = "/workspace/notebooks"
JOB_REGISTRY_PATH = "/workspace/jobs/.registry.json"

# Terminal states — never re-query these
_TERMINAL = {"FINISHED", "FAILED", "KILLED", "ERROR"}


# ─────────────────────────────────────────────────────────────
# Job registry helpers (PostgreSQL)
# ─────────────────────────────────────────────────────────────

def _init_jobs_table():
    conn = cursor = None
    try:
        conn = _get_db()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id VARCHAR PRIMARY KEY,
                filename VARCHAR,
                file_path VARCHAR,
                submitted_at VARCHAR,
                status VARCHAR,
                spark_submission_id VARCHAR,
                worker_host_port VARCHAR
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"Failed to initialize jobs table: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn: _release_db(conn)

def _load_registry() -> dict:
    _init_jobs_table()
    conn = cursor = None
    registry = {}
    try:
        conn = _get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT job_id, filename, file_path, submitted_at, status, spark_submission_id, worker_host_port
            FROM jobs
        """)
        for row in cursor.fetchall():
            registry[row[0]] = {
                "job_id": row[0],
                "filename": row[1],
                "file_path": row[2],
                "submitted_at": row[3],
                "status": row[4],
                "spark_submission_id": row[5],
                "worker_host_port": row[6]
            }
    except Exception as e:
        print(f"Failed to load registry: {e}")
    finally:
        if cursor: cursor.close()
        if conn: _release_db(conn)
    return registry

def _save_registry(registry: dict) -> None:
    # Not used directly anymore, left here for any missed references,
    # but actual saving happens in _upsert_job or direct DB queries
    pass

def _upsert_job(job_id: str, **fields) -> dict:
    _init_jobs_table()
    conn = cursor = None
    try:
        conn = _get_db()
        cursor = conn.cursor()

        # Check if exists
        cursor.execute("SELECT job_id FROM jobs WHERE job_id = %s", (job_id,))
        exists = cursor.fetchone() is not None

        if not exists:
            cursor.execute("""
                INSERT INTO jobs (job_id, filename, file_path, submitted_at, status, spark_submission_id, worker_host_port)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                job_id,
                fields.get("filename"),
                fields.get("file_path"),
                fields.get("submitted_at"),
                fields.get("status"),
                fields.get("spark_submission_id"),
                fields.get("worker_host_port")
            ))
        else:
            updates = []
            values = []
            for k, v in fields.items():
                if k in ("filename", "file_path", "submitted_at", "status", "spark_submission_id", "worker_host_port"):
                    updates.append(f"{k} = %s")
                    values.append(v)
            if updates:
                values.append(job_id)
                query = f"UPDATE jobs SET {', '.join(updates)} WHERE job_id = %s"
                cursor.execute(query, tuple(values))

        conn.commit()

        # return full record
        cursor.execute("""
            SELECT job_id, filename, file_path, submitted_at, status, spark_submission_id, worker_host_port
            FROM jobs WHERE job_id = %s
        """, (job_id,))
        row = cursor.fetchone()
        if row:
            return {
                "job_id": row[0],
                "filename": row[1],
                "file_path": row[2],
                "submitted_at": row[3],
                "status": row[4],
                "spark_submission_id": row[5],
                "worker_host_port": row[6]
            }

    except Exception as e:
        print(f"Failed to upsert job: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn: _release_db(conn)

    return {"job_id": job_id, **fields}


# ─────────────────────────────────────────────────────────────
# Spark REST API helpers  (port 6066)
# ─────────────────────────────────────────────────────────────

def _spark_submit(job_id: str, file_path: str, app_name: str) -> dict:
    """
    Submit a PySpark file to the Spark standalone REST API (port 6066).
    The file must be accessible by the Spark worker via the shared /workspace volume.
    Returns the Spark response dict which includes submissionId.
    Raises HTTPException(503) when Spark is unreachable.
    """
    payload = {
        "action":      "CreateSubmissionRequest",
        "appResource": f"file://{file_path}",
        "mainClass":   "org.apache.spark.deploy.SparkSubmit",
        "environmentVariables": {
            "SPARK_ENV_LOADED": "1",
        },
        "sparkProperties": {
            "spark.master":            Config.spark_master_url,
            "spark.app.name":          app_name,
            "spark.submit.deployMode": "cluster",
            "spark.driver.supervise":  "false",
        },
        "appArgs": [],
    }
    try:
        resp = requests.post(
            f"{Config.spark_submit_url}/v1/submissions/create",
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Spark master unreachable at {Config.spark_submit_url}. "
                "Ensure the spark-master container is running and "
                "SPARK_MASTER_REST_ENABLED=true."
            ),
        )
    except requests.exceptions.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Spark REST API error: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Spark submission failed: {exc}")


def _spark_status(submission_id: str) -> Optional[dict]:
    """Query Spark for a submission's current state. Returns None on failure."""
    try:
        resp = requests.get(
            f"{Config.spark_submit_url}/v1/submissions/status/{submission_id}",
            timeout=5,
        )
        if resp.ok:
            return resp.json()
    except Exception:
        pass
    return None


def _spark_kill(submission_id: str) -> bool:
    """Send a kill request to the Spark REST API. Returns True on success."""
    try:
        resp = requests.post(
            f"{Config.spark_submit_url}/v1/submissions/kill/{submission_id}",
            timeout=5,
        )
        return resp.ok
    except Exception:
        return False


def _fetch_spark_logs(submission_id: str, worker_host_port: str, log_type: str = "stdout") -> Optional[str]:
    """
    Fetch driver logs from the Spark worker web UI.
    worker_host_port comes from the status response (e.g. spark-worker-1:8081).
    """
    try:
        resp = requests.get(
            f"http://{worker_host_port}/logPage",
            params={"driverId": submission_id, "logType": log_type},
            timeout=5,
        )
        if resp.ok:
            text  = resp.text
            start = text.find("<pre>")
            end   = text.find("</pre>")
            if start != -1 and end != -1:
                return text[start + 5 : end]
            return text
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class NotebookContent(BaseModel):
    cells:          List[dict] = []
    metadata:       dict       = {}
    nbformat:       int        = 4
    nbformat_minor: int        = 5


# ─────────────────────────────────────────────────────────────
# Service helpers
# ─────────────────────────────────────────────────────────────

def _get_s3():
    """Return a boto3 S3 client pointed at MinIO, or raise HTTP 503."""
    try:
        return boto3.client(
            "s3",
            endpoint_url=Config.minio_endpoint,
            aws_access_key_id=Config.minio_access_key     or "minioadmin",
            aws_secret_access_key=Config.minio_secret_key or "minioadmin",
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"MinIO unavailable: {exc}")


from core.db import get_db_connection, release_db_connection

def _get_db(db_name: str = None):
    """Return a psycopg2 connection from the pool, or raise HTTP 503."""
    try:
        return get_db_connection(db_name)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"PostgreSQL unavailable: {exc}")

def _release_db(conn, db_name: str = None):
    """Release the connection back to the pool."""
    if conn:
        try:
            release_db_connection(conn, db_name)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════
#  JOBS
# ══════════════════════════════════════════════════════════════

@router.post("/jobs/submit")
def submit_job(file: UploadFile = File(...)):
    """
    Upload a PySpark .py script and submit it to the Spark cluster.

    The file is saved to the shared /workspace/jobs/ volume so the Spark
    worker can read it.  Submission goes via the Spark standalone REST API
    (port 6066) — the FastAPI container has no spark-submit binary.

    Returns job_id for subsequent /status and /logs polling.
    """
    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py PySpark scripts are accepted")

    os.makedirs(JOBS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    job_id    = str(uuid.uuid4())
    file_path = os.path.join(JOBS_DIR, f"{job_id}_{file.filename}")
    app_name  = f"DataHarbour-{job_id[:8]}"

    with open(file_path, "wb") as fh:
        fh.write(file.file.read())

    # Raises 503/502 if Spark is down — don't leave orphan files
    try:
        spark_resp = _spark_submit(job_id, file_path, app_name)
    except HTTPException:
        os.remove(file_path)
        raise

    submission_id = spark_resp.get("submissionId")

    record = _upsert_job(
        job_id,
        filename=file.filename,
        file_path=file_path,
        submitted_at=datetime.utcnow().isoformat(),
        status="SUBMITTED",
        spark_submission_id=submission_id,
        worker_host_port=None,
    )

    return {
        "job_id":              job_id,
        "spark_submission_id": submission_id,
        "filename":            file.filename,
        "submitted_at":        record["submitted_at"],
        "status":              "SUBMITTED",
    }


@router.get("/jobs")
def list_jobs(
    status: Optional[str] = Query(
        None,
        description="Filter: SUBMITTED | RUNNING | FINISHED | FAILED | KILLED | ERROR"
    )
):
    """List all jobs from the registry with live status refresh for non-terminal jobs."""
    registry = _load_registry()
    jobs     = []

    for job_id, job in registry.items():
        sub_id = job.get("spark_submission_id")
        if sub_id and job.get("status") not in _TERMINAL:
            spark = _spark_status(sub_id)
            if spark:
                new_state = spark.get("driverState", job["status"])
                if new_state != job["status"]:
                    job["status"]           = new_state
                    job["worker_host_port"] = spark.get("workerHostPort")
                    _upsert_job(job_id, status=new_state, worker_host_port=job["worker_host_port"])

        if status is None or job.get("status", "").upper() == status.upper():
            jobs.append(job)

    jobs.sort(key=lambda j: j.get("submitted_at", ""), reverse=True)
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/jobs/running")
def get_running_jobs():
    """Return all jobs in SUBMITTED or RUNNING state (live refresh)."""
    result = list_jobs(status=None)
    active = [j for j in result["jobs"] if j.get("status") in ("SUBMITTED", "RUNNING")]
    return {"running_jobs": active, "count": len(active)}


@router.get("/jobs/pending")
def get_pending_jobs():
    """Return jobs queued but not yet picked up by a worker (SUBMITTED)."""
    registry = _load_registry()
    pending  = [j for j in registry.values() if j.get("status") == "SUBMITTED"]
    return {"pending_jobs": pending, "count": len(pending)}


@router.get("/jobs/completed")
def get_completed_jobs():
    """Return all terminal jobs: FINISHED, FAILED, KILLED, ERROR."""
    registry  = _load_registry()
    completed = [j for j in registry.values() if j.get("status") in _TERMINAL]
    completed.sort(key=lambda j: j.get("submitted_at", ""), reverse=True)
    return {"completed_jobs": completed, "count": len(completed)}


@router.get("/jobs/{job_id}/status")
def get_job_status(job_id: str):
    """
    Return the current status of a single job.
    Queries the Spark REST API live for non-terminal jobs.
    Falls back to the last-known registry status when Spark is unreachable,
    and includes a 'source' field ('spark' or 'registry') so the caller knows.
    """
    registry = _load_registry()
    if job_id not in registry:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    job    = registry[job_id]
    sub_id = job.get("spark_submission_id")
    source = "registry"

    if sub_id and job.get("status") not in _TERMINAL:
        spark = _spark_status(sub_id)
        if spark:
            job["status"]           = spark.get("driverState", job["status"])
            job["worker_host_port"] = spark.get("workerHostPort")
            _upsert_job(job_id, status=job["status"], worker_host_port=job["worker_host_port"])
            source = "spark"

    return {
        "job_id":              job_id,
        "spark_submission_id": sub_id,
        "filename":            job.get("filename"),
        "file_path":           job.get("file_path"),
        "submitted_at":        job.get("submitted_at"),
        "status":              job.get("status", "UNKNOWN"),
        "worker_host_port":    job.get("worker_host_port"),
        "source":              source,
    }


@router.get("/jobs/{job_id}/logs")
def get_job_logs(
    job_id:   str,
    tail:     int = Query(200, ge=1, le=5000, description="Lines to return from the end"),
    log_type: str = Query("stdout", description="'stdout' or 'stderr'"),
):
    """
    Return the last `tail` lines from a job's driver log.

    Resolution order:
      1. Spark worker web UI  — via workerHostPort stored in the job record
      2. Local file           — /workspace/logs/{job_id}.log  (job-side redirect)
      3. Empty response       — job may still be starting up
    """
    registry = _load_registry()
    if job_id not in registry:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    job    = registry[job_id]
    sub_id = job.get("spark_submission_id")

    # Refresh workerHostPort if we don't have it yet
    worker_host_port = job.get("worker_host_port")
    if sub_id and not worker_host_port:
        spark = _spark_status(sub_id)
        if spark:
            worker_host_port            = spark.get("workerHostPort")
            job["worker_host_port"]     = worker_host_port
            job["status"]               = spark.get("driverState", job.get("status"))
            _upsert_job(job_id, status=job["status"], worker_host_port=worker_host_port)

    log_content = None
    log_source  = "none"

    # 1. Spark worker web UI
    if sub_id and worker_host_port:
        log_content = _fetch_spark_logs(sub_id, worker_host_port, log_type)
        if log_content:
            log_source = f"spark_worker ({worker_host_port})"

    # 2. Local log file fallback
    if not log_content:
        local_log = os.path.join(LOGS_DIR, f"{job_id}.log")
        if os.path.exists(local_log):
            with open(local_log, "r", errors="replace") as f:
                log_content = f.read()
            log_source = "local_file"

    if not log_content:
        return {
            "job_id":              job_id,
            "spark_submission_id": sub_id,
            "filename":            job.get("filename"),
            "submitted_at":        job.get("submitted_at"),
            "status":              job.get("status"),
            "log_source":          "none",
            "line_count":          0,
            "logs":                "",
            "message":             (
                "No logs available yet. "
                "The Spark driver may still be starting, "
                "or the worker UI is unreachable."
            ),
        }

    lines = log_content.splitlines(keepends=True)
    if len(lines) > tail:
        lines = lines[-tail:]

    return {
        "job_id":              job_id,
        "spark_submission_id": sub_id,
        "filename":            job.get("filename"),
        "submitted_at":        job.get("submitted_at"),
        "status":              job.get("status"),
        "log_source":          log_source,
        "line_count":          len(lines),
        "logs":                "".join(lines),
    }


@router.delete("/jobs/{job_id}")
def cancel_job(job_id: str):
    """Kill a RUNNING/SUBMITTED job via the Spark REST API."""
    registry = _load_registry()
    if job_id not in registry:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    job    = registry[job_id]
    sub_id = job.get("spark_submission_id")

    if job.get("status") in _TERMINAL:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel — job is already '{job.get('status')}'"
        )
    if not sub_id:
        raise HTTPException(status_code=400, detail="No Spark submission ID recorded for this job")

    if not _spark_kill(sub_id):
        raise HTTPException(
            status_code=502,
            detail="Spark kill request failed — master may be unreachable"
        )

    _upsert_job(job_id, status="KILLED")
    return {"message": f"Job '{job_id}' killed", "spark_submission_id": sub_id}


# ══════════════════════════════════════════════════════════════
#  AUTHENTICATION
# ══════════════════════════════════════════════════════════════

@router.post("/auth/login")
def login(credentials: LoginRequest):
    """Login — replace with JWT in production."""
    return {
        "success": True,
        "user": {
            "username": credentials.username,
            "name":     "DataHarbour User",
            "token":    "demo-token-12345",
        },
    }


@router.post("/auth/logout")
def logout():
    return {"success": True, "message": "Logged out successfully"}


# ══════════════════════════════════════════════════════════════
#  DHFS — DataHarbour File System (MinIO)
# ══════════════════════════════════════════════════════════════

@router.get("/dhfs/buckets")
def list_buckets():
    """List all MinIO buckets."""
    s3 = _get_s3()
    try:
        resp    = s3.list_buckets()
        buckets = [
            {
                "name":    b["Name"],
                "created": b["CreationDate"].isoformat() if b.get("CreationDate") else None,
            }
            for b in resp.get("Buckets", [])
        ]
        return {"buckets": buckets, "count": len(buckets)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/dhfs/buckets/{bucket_name}")
def create_bucket(bucket_name: str):
    """Create a new MinIO bucket."""
    s3 = _get_s3()
    try:
        s3.create_bucket(Bucket=bucket_name)
        return {"message": f"Bucket '{bucket_name}' created", "bucket": bucket_name}
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code in ("BucketAlreadyExists", "BucketAlreadyOwnedByYou"):
            raise HTTPException(status_code=409, detail=f"Bucket '{bucket_name}' already exists")
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/dhfs/buckets/{bucket_name}")
def delete_bucket(bucket_name: str):
    """Delete an empty MinIO bucket."""
    s3 = _get_s3()
    try:
        s3.delete_bucket(Bucket=bucket_name)
        return {"message": f"Bucket '{bucket_name}' deleted"}
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code == "NoSuchBucket":
            raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' not found")
        if code == "BucketNotEmpty":
            raise HTTPException(
                status_code=409,
                detail=f"Bucket '{bucket_name}' is not empty — delete all files first"
            )
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/dhfs/files/{bucket_name}")
def list_files(bucket_name: str, prefix: str = ""):
    """List files in a MinIO bucket, optionally filtered by prefix."""
    s3 = _get_s3()
    try:
        resp  = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        files = [
            {
                "name":         obj["Key"],
                "size":         obj["Size"],
                "lastModified": obj["LastModified"].isoformat(),
                "type":         obj["Key"].rsplit(".", 1)[-1] if "." in obj["Key"] else "unknown",
            }
            for obj in resp.get("Contents", [])
        ]
        return {"files": files, "bucket": bucket_name, "count": len(files)}
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "NoSuchBucket":
            raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' not found")
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/dhfs/upload/{bucket_name}")
def upload_file(bucket_name: str, file: UploadFile = File(...)):
    """
    Upload a file to a MinIO bucket.
    Auto-creates the bucket if it does not exist.
    """
    s3 = _get_s3()
    try:
        try:
            s3.head_bucket(Bucket=bucket_name)
        except ClientError:
            s3.create_bucket(Bucket=bucket_name)

        content = file.file.read()
        s3.put_object(Bucket=bucket_name, Key=file.filename, Body=content)
        return {
            "message":  f"File '{file.filename}' uploaded to '{bucket_name}'",
            "bucket":   bucket_name,
            "filename": file.filename,
            "size":     len(content),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/dhfs/files/{bucket_name}/{file_key:path}")
def delete_file(bucket_name: str, file_key: str):
    """Delete a specific file from a MinIO bucket."""
    s3 = _get_s3()
    try:
        s3.head_object(Bucket=bucket_name, Key=file_key)
        s3.delete_object(Bucket=bucket_name, Key=file_key)
        return {"message": f"File '{file_key}' deleted from '{bucket_name}'"}
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code in ("404", "NoSuchKey"):
            raise HTTPException(
                status_code=404,
                detail=f"File '{file_key}' not found in '{bucket_name}'"
            )
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/dhfs/download/{bucket_name}/{file_key:path}")
def download_file(bucket_name: str, file_key: str):
    """Generate a pre-signed download URL valid for 1 hour."""
    s3 = _get_s3()
    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": file_key},
            ExpiresIn=3600,
        )
        return {"url": url, "file": file_key, "bucket": bucket_name, "expires_in": 3600}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ══════════════════════════════════════════════════════════════
#  CATALOG — Databases, Tables, Iceberg
# ══════════════════════════════════════════════════════════════

@router.get("/catalog/databases")
def list_databases():
    """List all user-created PostgreSQL databases with their sizes."""
    conn = cursor = None
    try:
        conn   = _get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT datname, pg_size_pretty(pg_database_size(datname)) AS size
            FROM   pg_database
            WHERE  datistemplate = false AND datname NOT IN ('postgres')
            ORDER  BY datname
        """)
        databases = [{"name": r[0], "size": r[1]} for r in cursor.fetchall()]
        return {"databases": databases, "count": len(databases)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if cursor: cursor.close()
        if conn: _release_db(conn)


@router.post("/catalog/databases/{db_name}")
def create_database(db_name: str):
    """Create a new PostgreSQL database."""
    conn = cursor = None
    try:
        conn            = _get_db()
        conn.autocommit = True
        cursor          = conn.cursor()
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        return {"message": f"Database '{db_name}' created", "database": db_name}
    except psycopg2.errors.DuplicateDatabase:
        raise HTTPException(status_code=409, detail=f"Database '{db_name}' already exists")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if cursor: cursor.close()
        if conn: _release_db(conn)


@router.delete("/catalog/databases/{db_name}")
def delete_database(db_name: str):
    """
    Drop a PostgreSQL database.
    Terminates active connections first to avoid lock errors.
    """
    conn = cursor = None
    try:
        conn            = _get_db()
        conn.autocommit = True
        cursor          = conn.cursor()
        cursor.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = %s AND pid <> pg_backend_pid()",
            (db_name,),
        )
        cursor.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(db_name)))
        return {"message": f"Database '{db_name}' deleted"}
    except psycopg2.errors.InvalidCatalogName:
        raise HTTPException(status_code=404, detail=f"Database '{db_name}' not found")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if cursor: cursor.close()
        if conn: _release_db(conn)


@router.get("/catalog/databases/{db_name}/tables")
def list_tables(db_name: str):
    """List all tables in a PostgreSQL database with their sizes."""
    conn = cursor = None
    try:
        conn   = _get_db(db_name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name,
                   pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) AS size
            FROM   information_schema.tables
            WHERE  table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER  BY table_name
        """)
        tables = [{"name": r[0], "size": r[1]} for r in cursor.fetchall()]
        return {"tables": tables, "database": db_name, "count": len(tables)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if cursor: cursor.close()
        if conn: _release_db(conn, db_name)


@router.post("/catalog/databases/{db_name}/tables/{table_name}")
def create_table(db_name: str, table_name: str):
    """Create a JSONB table in a PostgreSQL database."""
    conn = cursor = None
    try:
        conn   = _get_db(db_name)
        cursor = conn.cursor()
        cursor.execute(
            sql.SQL(
                "CREATE TABLE IF NOT EXISTS {} "
                "(id SERIAL PRIMARY KEY, data JSONB, created_at TIMESTAMP DEFAULT NOW())"
            ).format(sql.Identifier(table_name))
        )
        conn.commit()
        return {"message": f"Table '{table_name}' created in '{db_name}'", "table": table_name}
    except HTTPException:
        raise
    except Exception as exc:
        if conn: conn.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if cursor: cursor.close()
        if conn: _release_db(conn, db_name)


@router.delete("/catalog/databases/{db_name}/tables/{table_name}")
def delete_table(db_name: str, table_name: str):
    """Drop a table from a PostgreSQL database."""
    conn = cursor = None
    try:
        conn   = _get_db(db_name)
        cursor = conn.cursor()
        cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table_name)))
        conn.commit()
        return {"message": f"Table '{table_name}' deleted from '{db_name}'"}
    except HTTPException:
        raise
    except Exception as exc:
        if conn: conn.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if cursor: cursor.close()
        if conn: _release_db(conn, db_name)


@router.get("/catalog/iceberg/tables")
def list_iceberg_tables():
    """List all Iceberg tables in the workspace."""
    tables_path = "/workspace/iceberg/dataharbour"
    try:
        if not os.path.exists(tables_path):
            return {"tables": [], "count": 0}

        tables = []
        with os.scandir(tables_path) as it:
            for entry in it:
                if entry.is_dir():
                    tables.append({
                        "name":        entry.name,
                        "path":        entry.path,
                        "hasMetadata": os.path.exists(os.path.join(entry.path, "metadata")),
                    })
        return {"tables": tables, "count": len(tables)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/catalog/iceberg/tables/{table_name}")
def get_iceberg_table_details(table_name: str):
    """Return the latest Iceberg metadata JSON for a table."""
    metadata_path = f"/workspace/iceberg/dataharbour/{table_name}/metadata"
    try:
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail=f"Iceberg table '{table_name}' not found")
        metadata_files = sorted(
            f for f in os.listdir(metadata_path) if f.endswith(".metadata.json")
        )
        if not metadata_files:
            return {"table": table_name, "metadata": None}
        with open(os.path.join(metadata_path, metadata_files[-1]), "r") as f:
            metadata = json.load(f)
        return {"table": table_name, "metadata": metadata}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ══════════════════════════════════════════════════════════════
#  NOTEBOOKS
# ══════════════════════════════════════════════════════════════

@router.get("/notebooks")
def list_notebooks():
    """List all Jupyter notebooks sorted by last-modified date."""
    try:
        if not os.path.exists(NOTEBOOKS_DIR):
            return {"notebooks": [], "count": 0}
        notebooks = []
        with os.scandir(NOTEBOOKS_DIR) as it:
            for entry in it:
                if entry.is_file() and entry.name.endswith(".ipynb"):
                    stat = entry.stat()
                    notebooks.append({
                        "id":           entry.name,
                        "name":         entry.name,
                        "created":      datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "lastModified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
        notebooks.sort(key=lambda n: n["lastModified"], reverse=True)
        return {"notebooks": notebooks, "count": len(notebooks)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/notebooks/{notebook_name}")
def get_notebook(notebook_name: str):
    """Return the full JSON content of a notebook."""
    path = os.path.join(NOTEBOOKS_DIR, notebook_name)
    try:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Notebook not found")
        with open(path, "r") as f:
            content = json.load(f)
        return {"notebook": notebook_name, "content": content}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid notebook format")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/notebooks")
def create_notebook(name: str):
    """Create a new empty notebook with a PySpark starter cell."""
    if not name.endswith(".ipynb"):
        name = f"{name}.ipynb"
    path = os.path.join(NOTEBOOKS_DIR, name)
    try:
        if os.path.exists(path):
            raise HTTPException(status_code=409, detail=f"Notebook '{name}' already exists")
        os.makedirs(NOTEBOOKS_DIR, exist_ok=True)
        empty = {
            "cells": [{
                "cell_type":       "code",
                "execution_count": None,
                "metadata":        {},
                "outputs":         [],
                "source": [
                    "# New DataHarbour Notebook\n",
                    "from pyspark.sql import SparkSession\n",
                    "\n",
                    "spark = SparkSession.builder.appName('DataHarbour').getOrCreate()\n",
                    "print('Spark session created')\n",
                ],
            }],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language":     "python",
                    "name":         "python3",
                }
            },
            "nbformat":       4,
            "nbformat_minor": 5,
        }
        with open(path, "w") as f:
            json.dump(empty, f, indent=2)
        return {"message": f"Notebook '{name}' created", "notebook": name}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/notebooks/{notebook_name}")
def save_notebook(notebook_name: str, content: NotebookContent):
    """Save (overwrite) a notebook's content."""
    path = os.path.join(NOTEBOOKS_DIR, notebook_name)
    try:
        os.makedirs(NOTEBOOKS_DIR, exist_ok=True)
        with open(path, "w") as f:
            json.dump(content.dict(), f, indent=2)
        return {"message": "Notebook saved", "notebook": notebook_name}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/notebooks/{notebook_name}")
def delete_notebook(notebook_name: str):
    """Delete a notebook."""
    path = os.path.join(NOTEBOOKS_DIR, notebook_name)
    try:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Notebook not found")
        os.remove(path)
        return {"message": f"Notebook '{notebook_name}' deleted"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/notebooks/{notebook_name}/execute")
def execute_notebook(notebook_name: str):
    """
    Extract all code cells from a notebook, write them as a .py file,
    and submit to the Spark cluster — same pipeline as POST /jobs/submit.
    Returns a job_id for /status and /logs polling.
    """
    nb_path = os.path.join(NOTEBOOKS_DIR, notebook_name)
    try:
        if not os.path.exists(nb_path):
            raise HTTPException(status_code=404, detail="Notebook not found")

        with open(nb_path, "r") as f:
            notebook = json.load(f)

        code = "\n\n".join(
            "".join(cell.get("source", []))
            for cell in notebook.get("cells", [])
            if cell.get("cell_type") == "code"
        )
        if not code.strip():
            raise HTTPException(status_code=400, detail="Notebook has no executable code cells")

        os.makedirs(JOBS_DIR, exist_ok=True)
        os.makedirs(LOGS_DIR, exist_ok=True)

        job_id    = str(uuid.uuid4())
        script    = notebook_name.replace(".ipynb", ".py")
        file_path = os.path.join(JOBS_DIR, f"{job_id}_{script}")
        app_name  = f"DataHarbour-nb-{job_id[:8]}"

        with open(file_path, "w") as f:
            f.write(f"# Generated from notebook: {notebook_name}\n\n{code}")

        try:
            spark_resp = _spark_submit(job_id, file_path, app_name)
        except HTTPException:
            os.remove(file_path)
            raise

        submission_id = spark_resp.get("submissionId")
        record = _upsert_job(
            job_id,
            filename=script,
            file_path=file_path,
            submitted_at=datetime.utcnow().isoformat(),
            status="SUBMITTED",
            spark_submission_id=submission_id,
            worker_host_port=None,
        )

        return {
            "message":             f"Notebook '{notebook_name}' submitted as Spark job",
            "job_id":              job_id,
            "spark_submission_id": submission_id,
            "submitted_at":        record["submitted_at"],
            "status":              "SUBMITTED",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ══════════════════════════════════════════════════════════════
#  CLUSTER
# ══════════════════════════════════════════════════════════════

@router.get("/cluster/status")
def get_cluster_status():
    """Fetch live Spark cluster status from the master Web UI JSON API."""
    try:
        resp = requests.get(f"{Config.spark_rest_url}/json/", timeout=5)
        if resp.ok:
            d = resp.json()
            return {
                "status":        "running",
                "masterUrl":     Config.spark_master_url,
                "workers":       len(d.get("workers", [])),
                "cores":         d.get("cores", 0),
                "coresUsed":     d.get("coresused", 0),
                "memory":        d.get("memory", "0 MB"),
                "memoryUsed":    d.get("memoryused", "0 MB"),
                "activeApps":    len(d.get("activeapps", [])),
                "completedApps": len(d.get("completedapps", [])),
            }
    except Exception:
        pass
    return {
        "status":        "unavailable",
        "masterUrl":     Config.spark_master_url,
        "workers":       0, "cores": 0, "coresUsed": 0,
        "memory":        "0 MB", "memoryUsed": "0 MB",
        "activeApps":    0, "completedApps": 0,
    }


@router.get("/cluster/workers")
def get_cluster_workers():
    """Return the list of registered Spark workers."""
    try:
        resp = requests.get(f"{Config.spark_rest_url}/json/", timeout=5)
        if resp.ok:
            return {"workers": resp.json().get("workers", [])}
    except Exception:
        pass
    return {"workers": []}


@router.get("/cluster/applications")
def get_cluster_applications():
    """Return active and completed Spark applications from the master."""
    try:
        resp = requests.get(f"{Config.spark_rest_url}/json/", timeout=5)
        if resp.ok:
            d = resp.json()
            return {"active": d.get("activeapps", []), "completed": d.get("completedapps", [])}
    except Exception:
        pass
    return {"active": [], "completed": []}


# ══════════════════════════════════════════════════════════════
#  STATS & RECENT ACTIVITIES  (dashboard)
# ══════════════════════════════════════════════════════════════

@router.get("/stats/summary")
def get_stats_summary():
    """Aggregate counts for the dashboard overview panel."""
    notebooks_count = 0
    if os.path.exists(NOTEBOOKS_DIR):
        with os.scandir(NOTEBOOKS_DIR) as it:
            notebooks_count = sum(1 for entry in it if entry.is_file() and entry.name.endswith(".ipynb"))

    registry     = _load_registry()
    jobs_count   = len(registry)
    jobs_running = sum(1 for j in registry.values() if j.get("status") in ("SUBMITTED", "RUNNING"))
    jobs_failed  = sum(1 for j in registry.values() if j.get("status") in ("FAILED", "ERROR"))

    buckets_count = 0
    try:
        buckets_count = len(_get_s3().list_buckets().get("Buckets", []))
    except Exception:
        pass

    databases_count = 0
    conn = cursor = None
    try:
        conn   = _get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT count(*) FROM pg_database "
            "WHERE datistemplate = false AND datname NOT IN ('postgres')"
        )
        databases_count = cursor.fetchone()[0]
    except Exception:
        pass
    finally:
        if cursor: cursor.close()
        if conn: _release_db(conn)

    return {
        "notebooks":   notebooks_count,
        "jobs":        jobs_count,
        "jobsRunning": jobs_running,
        "jobsFailed":  jobs_failed,
        "buckets":     buckets_count,
        "databases":   databases_count,
    }


@router.get("/activities/recent")
def get_recent_activities():
    """Return the 10 most recent activities across notebooks and jobs."""
    activities = []

    if os.path.exists(NOTEBOOKS_DIR):
        with os.scandir(NOTEBOOKS_DIR) as it:
            for entry in it:
                if entry.is_file() and entry.name.endswith(".ipynb"):
                    stat = entry.stat()
                    activities.append({
                        "type":   "notebook",
                        "action": "Modified",
                        "name":   entry.name,
                        "time":   datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })

    for job in _load_registry().values():
        activities.append({
            "type":   "job",
            "action": "Submitted",
            "name":   job.get("filename", job["job_id"]),
            "status": job.get("status"),
            "job_id": job["job_id"],
            "time":   job.get("submitted_at", ""),
        })

    activities.sort(key=lambda x: x.get("time", ""), reverse=True)
    return {"activities": activities[:10]}