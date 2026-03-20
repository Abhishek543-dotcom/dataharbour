"""
Spark Client
============
Docker-based Spark job submission.

Instead of installing Java/Spark inside the FastAPI container, we use the
Docker SDK to execute ``spark-submit`` inside the already-running
``spark-master`` container via ``docker exec``.  This keeps the API image
lightweight (~150 MB vs ~1.5 GB).
"""

import logging
import os
import threading
from typing import Dict, Optional

from core.config import Config

logger = logging.getLogger("dataharbour.spark")

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    logger.warning("docker library not available — job submission will fail")

# ── Thread-safe in-memory process tracking ──────────────────
_SPARK_PROCESSES: Dict[str, dict] = {}
_PROCESSES_LOCK = threading.Lock()


def _get_spark_container_name() -> str:
    """Discover the Spark master container name dynamically."""
    if not DOCKER_AVAILABLE:
        return "dataharbour-spark-master-1"
    try:
        client = docker.from_env()
        containers = client.containers.list(filters={"name": "spark-master"})
        if containers:
            return containers[0].name
    except Exception as e:
        logger.warning("Could not discover Spark container: %s", e)
    return "dataharbour-spark-master-1"


def spark_submit(job_id: str, file_path: str, app_name: str) -> dict:
    """
    Submit a PySpark script to the Spark cluster via ``docker exec``.

    Returns ``{"submissionId": job_id}`` on success.
    Raises ``RuntimeError`` on failure.
    """
    if not DOCKER_AVAILABLE:
        raise RuntimeError(
            "Docker library not available. Install the 'docker' package."
        )

    container_name = _get_spark_container_name()
    logs_dir = Config.logs_dir
    os.makedirs(logs_dir, exist_ok=True)

    stdout_file = os.path.join(logs_dir, f"{job_id}.stdout")
    stderr_file = os.path.join(logs_dir, f"{job_id}.stderr")

    try:
        client = docker.from_env()
        container = client.containers.get(container_name)

        cmd = [
            "/opt/spark/bin/spark-submit",
            "--master",
            Config.spark_master_url,
            "--name",
            app_name,
            "--deploy-mode",
            "client",
            "--conf",
            "spark.driver.supervise=false",
            file_path,
        ]

        logger.info(
            "spark-submit → container=%s, job=%s, file=%s",
            container_name,
            job_id,
            file_path,
        )

        exec_result = container.exec_run(
            cmd=cmd, stdout=True, stderr=True, demux=False
        )

        exit_code = exec_result.exit_code
        output = exec_result.output
        output_str = (
            output.decode("utf-8", errors="replace")
            if isinstance(output, bytes)
            else (output or "")
        )

        # Persist output to log files
        with open(stdout_file, "w") as f:
            f.write(output_str)
        with open(stderr_file, "w") as f:
            f.write("")  # stderr captured combined in demux=False

        status = "FINISHED" if exit_code == 0 else "FAILED"

        with _PROCESSES_LOCK:
            _SPARK_PROCESSES[job_id] = {
                "container_name": container_name,
                "status": status,
                "stdout_file": stdout_file,
                "stderr_file": stderr_file,
                "exit_code": exit_code,
            }

        logger.info(
            "spark-submit completed: job=%s, exit_code=%d, status=%s",
            job_id,
            exit_code,
            status,
        )
        return {"submissionId": job_id}

    except docker.errors.NotFound:
        raise RuntimeError(f"Spark master container '{container_name}' not found")
    except Exception as e:
        logger.error(
            "spark-submit error for job %s: %s", job_id, e, exc_info=True
        )
        with _PROCESSES_LOCK:
            _SPARK_PROCESSES[job_id] = {"status": "ERROR", "error": str(e)}
        raise RuntimeError(f"Failed to submit Spark job: {e}")


def spark_status(submission_id: str) -> Optional[dict]:
    """Return the status of a tracked Spark submission, or None if unknown."""
    with _PROCESSES_LOCK:
        proc = _SPARK_PROCESSES.get(submission_id)
        if not proc:
            return None
        return {
            "submissionId": submission_id,
            "driverState": proc.get("status", "UNKNOWN"),
            "workerHostPort": "spark-worker-1:8081",
            "exitCode": proc.get("exit_code"),
        }


def spark_kill(submission_id: str) -> bool:
    """Mark a tracked submission as KILLED. Returns True if found."""
    with _PROCESSES_LOCK:
        if submission_id not in _SPARK_PROCESSES:
            return False
        _SPARK_PROCESSES[submission_id]["status"] = "KILLED"
        return True


def fetch_spark_logs(submission_id: str, log_type: str = "stdout") -> Optional[str]:
    """Read captured log files for a job."""
    log_file = os.path.join(Config.logs_dir, f"{submission_id}.{log_type}")
    if not os.path.exists(log_file):
        return None
    try:
        with open(log_file, "r", errors="replace") as f:
            return f.read()
    except Exception:
        return None

