"""
DataHarbour API — Shared Helpers
=================================
Common utilities used across all route modules: S3 client, DB helpers,
job registry operations, Pydantic models.
"""

import logging
import os
from datetime import datetime
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from pydantic import BaseModel, Field

from core.config import Config
from core.db import get_db_connection, release_db_connection

logger = logging.getLogger("dataharbour.helpers")

# Terminal states — never re-query Spark for these
TERMINAL_STATES = frozenset({"FINISHED", "FAILED", "KILLED", "ERROR"})


# ══════════════════════════════════════════════════════════════
#  Pydantic Request / Response Models
# ══════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    username: str
    password: str


class NotebookContent(BaseModel):
    cells: list = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    nbformat: int = 4
    nbformat_minor: int = 5


class CreateTableRequest(BaseModel):
    """Optional body for table creation — allows column definitions."""
    columns: list = Field(
        default=None,
        description="List of column defs. If omitted, a generic JSONB table is created.",
    )


# ══════════════════════════════════════════════════════════════
#  Service Clients
# ══════════════════════════════════════════════════════════════

def get_s3_client():
    """Return a boto3 S3 client pointed at MinIO, or raise HTTP 503."""
    try:
        return boto3.client(
            "s3",
            endpoint_url=Config.minio_endpoint,
            aws_access_key_id=Config.minio_access_key or "minioadmin",
            aws_secret_access_key=Config.minio_secret_key or "minioadmin",
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"MinIO unavailable: {exc}")


def get_db(db_name: str = None):
    """Return a psycopg2 connection (from pool for default DB), or raise 503."""
    try:
        return get_db_connection(db_name)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"PostgreSQL unavailable: {exc}")


def release_db(conn, db_name: str = None):
    """Release connection back to the pool (or close if custom db)."""
    if conn:
        try:
            release_db_connection(conn, db_name)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════
#  Job Registry (PostgreSQL)
# ══════════════════════════════════════════════════════════════

def init_jobs_table():
    """Ensure the ``jobs`` table exists in the default database."""
    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id              VARCHAR PRIMARY KEY,
                filename            VARCHAR,
                file_path           VARCHAR,
                submitted_at        VARCHAR,
                status              VARCHAR DEFAULT 'SUBMITTED',
                spark_submission_id VARCHAR,
                worker_host_port    VARCHAR
            )
        """)
        conn.commit()
    except Exception as e:
        logger.error("Failed to initialise jobs table: %s", e)
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db(conn)


def load_registry() -> dict:
    """Load all jobs from PostgreSQL into a dict keyed by job_id."""
    init_jobs_table()
    conn = cursor = None
    registry = {}
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT job_id, filename, file_path, submitted_at, status, "
            "spark_submission_id, worker_host_port FROM jobs"
        )
        for row in cursor.fetchall():
            registry[row[0]] = {
                "job_id": row[0],
                "filename": row[1],
                "file_path": row[2],
                "submitted_at": row[3],
                "status": row[4],
                "spark_submission_id": row[5],
                "worker_host_port": row[6],
            }
    except Exception as e:
        logger.error("Failed to load registry: %s", e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db(conn)
    return registry


def upsert_job(job_id: str, **fields) -> dict:
    """Insert or update a job record. Returns the full record dict."""
    init_jobs_table()
    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT job_id FROM jobs WHERE job_id = %s", (job_id,))
        exists = cursor.fetchone() is not None

        if not exists:
            cursor.execute(
                "INSERT INTO jobs "
                "(job_id, filename, file_path, submitted_at, status, spark_submission_id, worker_host_port) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    job_id,
                    fields.get("filename"),
                    fields.get("file_path"),
                    fields.get("submitted_at"),
                    fields.get("status"),
                    fields.get("spark_submission_id"),
                    fields.get("worker_host_port"),
                ),
            )
        else:
            allowed = {"filename", "file_path", "submitted_at", "status",
                       "spark_submission_id", "worker_host_port"}
            updates, values = [], []
            for k, v in fields.items():
                if k in allowed:
                    updates.append(f"{k} = %s")
                    values.append(v)
            if updates:
                values.append(job_id)
                cursor.execute(
                    f"UPDATE jobs SET {', '.join(updates)} WHERE job_id = %s",
                    tuple(values),
                )

        conn.commit()

        # Return full record
        cursor.execute(
            "SELECT job_id, filename, file_path, submitted_at, status, "
            "spark_submission_id, worker_host_port FROM jobs WHERE job_id = %s",
            (job_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "job_id": row[0],
                "filename": row[1],
                "file_path": row[2],
                "submitted_at": row[3],
                "status": row[4],
                "spark_submission_id": row[5],
                "worker_host_port": row[6],
            }
    except Exception as e:
        logger.error("Failed to upsert job %s: %s", job_id, e)
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db(conn)

    return {"job_id": job_id, **fields}

