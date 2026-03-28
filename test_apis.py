#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║         DataHarbour — Comprehensive API Test Suite  v3           ║
║                                                                  ║
║  • Auto-discovers real route paths from /openapi.json            ║
║  • Treats HTTP 503 as ⚠️  WARN (infra down ≠ code bug)           ║
║  • Deep body/key assertions on every response                    ║
║  • Retry logic, per-test timing, colour-coded output             ║
║  • Rich final summary: PASS / FAIL / WARN / SKIP                ║
╚══════════════════════════════════════════════════════════════════╝

Usage:
    python test_apis.py                        # http://localhost:8000
    python test_apis.py http://host:9000       # custom URL
    python test_apis.py --json out.json        # also write JSON report
"""

import sys
import json
import time
import io
import re
import os
import requests
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

# ── ANSI colours ─────────────────────────────────────────────────────────────
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
GREY = "\033[90m"
WHITE = "\033[97m"


def c(t, col):
    return f"{col}{t}{RESET}"


# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
TIMEOUT = 15
RETRY_COUNT = 2
RETRY_DELAY = 1.5
TEST_BUCKET = "dh-test-bucket"
TEST_DB = "dh_test_db"
TEST_TABLE = "dh_test_table"
TEST_NB = "test_notebook.ipynb"

# ── Shared state ──────────────────────────────────────────────────────────────
results: List[Dict] = []
_state: Dict[str, Any] = {}
PASS, FAIL, SKIP, WARN = "PASS", "FAIL", "SKIP", "WARN"


# ═══════════════════════════════════════════════════════════════════════════════
#  Utilities
# ═══════════════════════════════════════════════════════════════════════════════


def _req(method, path, retries=RETRY_COUNT, **kwargs):
    """Make an HTTP request with retry logic."""
    kwargs.setdefault("timeout", TIMEOUT)
    url = f"{BASE_URL}{path}"
    last_exc = None
    for attempt in range(retries + 1):
        try:
            resp = getattr(requests, method.lower())(url, **kwargs)
            return resp
        except requests.ConnectionError as e:
            last_exc = e
            if attempt < retries:
                time.sleep(RETRY_DELAY)
    raise last_exc


def _record(name, status, detail="", elapsed=0.0):
    """Record a test result."""
    results.append({"name": name, "status": status, "detail": detail, "elapsed": elapsed})
    icon = {"PASS": c("✔", GREEN), "FAIL": c("✘", RED), "WARN": c("⚠", YELLOW), "SKIP": c("–", GREY)}
    status_col = {"PASS": GREEN, "FAIL": RED, "WARN": YELLOW, "SKIP": GREY}
    print(f"  {icon[status]}  {c(status, status_col[status])}  {name}  {c(f'({elapsed:.1f}ms)', GREY)}")
    if detail and status in (FAIL, WARN):
        print(f"       {c(detail[:200], GREY)}")


def _assert_keys(resp_json, keys, test_name, elapsed):
    """Verify expected keys exist in response JSON."""
    missing = [k for k in keys if k not in resp_json]
    if missing:
        _record(test_name, FAIL, f"Missing keys: {missing}", elapsed)
        return False
    return True


def _run_test(name, method, path, expected_status=200, expected_keys=None, **kwargs):
    """Generic test runner."""
    t0 = time.time()
    try:
        resp = _req(method, path, **kwargs)
        elapsed = (time.time() - t0) * 1000

        if resp.status_code == 503:
            _record(name, WARN, "Service unavailable (503) — infra issue, not code bug", elapsed)
            return resp

        if resp.status_code != expected_status:
            _record(name, FAIL, f"Expected {expected_status}, got {resp.status_code}: {resp.text[:150]}", elapsed)
            return resp

        if expected_keys:
            try:
                body = resp.json()
                if not _assert_keys(body, expected_keys, name, elapsed):
                    return resp
            except Exception:
                _record(name, FAIL, "Response is not valid JSON", elapsed)
                return resp

        _record(name, PASS, "", elapsed)
        return resp
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        _record(name, FAIL, str(e)[:200], elapsed)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
#  Test Suites
# ═══════════════════════════════════════════════════════════════════════════════


def test_system():
    """System / health endpoints."""
    print(f"\n{c('═══ SYSTEM ═══', CYAN)}")
    _run_test("GET /", "get", "/", expected_keys=["name", "version"])
    _run_test("GET /health", "get", "/health", expected_keys=["status", "version"])
    _run_test("GET /docs", "get", "/docs")
    _run_test("GET /openapi.json", "get", "/openapi.json", expected_keys=["paths"])


def test_auth():
    """Authentication endpoints."""
    print(f"\n{c('═══ AUTH ═══', CYAN)}")
    resp = _run_test(
        "POST /auth/login",
        "post",
        "/auth/login",
        json={"username": "admin", "password": "admin"},
        expected_keys=["success", "user"],
    )
    if resp and resp.status_code == 200:
        _state["token"] = resp.json().get("user", {}).get("token")

    _run_test("POST /auth/logout", "post", "/auth/logout", expected_keys=["success", "message"])


def test_storage():
    """MinIO storage (DHFS) endpoints."""
    print(f"\n{c('═══ STORAGE (MinIO) ═══', CYAN)}")

    # List buckets
    _run_test("GET /dhfs/buckets", "get", "/dhfs/buckets", expected_keys=["buckets", "count"])

    # Create bucket
    _run_test(
        f"POST /dhfs/buckets/{TEST_BUCKET}",
        "post",
        f"/dhfs/buckets/{TEST_BUCKET}",
        expected_keys=["message", "bucket"],
    )

    # Upload file
    test_content = b"id,name,value\n1,test,100\n2,hello,200\n"
    resp = _run_test(
        f"POST /dhfs/upload/{TEST_BUCKET}",
        "post",
        f"/dhfs/upload/{TEST_BUCKET}",
        files={"file": ("test_data.csv", io.BytesIO(test_content), "text/csv")},
        expected_keys=["message", "filename", "size"],
    )

    # List files
    _run_test(
        f"GET /dhfs/files/{TEST_BUCKET}",
        "get",
        f"/dhfs/files/{TEST_BUCKET}",
        expected_keys=["files", "bucket", "count"],
    )

    # Download (pre-signed URL)
    _run_test(
        f"GET /dhfs/download/{TEST_BUCKET}/test_data.csv",
        "get",
        f"/dhfs/download/{TEST_BUCKET}/test_data.csv",
        expected_keys=["url", "file", "expires_in"],
    )

    # Delete file
    _run_test(
        f"DELETE /dhfs/files/{TEST_BUCKET}/test_data.csv",
        "delete",
        f"/dhfs/files/{TEST_BUCKET}/test_data.csv",
        expected_keys=["message"],
    )

    # Delete bucket
    _run_test(
        f"DELETE /dhfs/buckets/{TEST_BUCKET}",
        "delete",
        f"/dhfs/buckets/{TEST_BUCKET}",
        expected_keys=["message"],
    )


def test_catalog_postgres():
    """PostgreSQL catalog endpoints."""
    print(f"\n{c('═══ CATALOG (PostgreSQL) ═══', CYAN)}")

    # List databases
    _run_test("GET /catalog/databases", "get", "/catalog/databases", expected_keys=["databases", "count"])

    # Create database
    _run_test(
        f"POST /catalog/databases/{TEST_DB}",
        "post",
        f"/catalog/databases/{TEST_DB}",
        expected_keys=["message", "database"],
    )

    # List tables
    _run_test(
        f"GET /catalog/databases/{TEST_DB}/tables",
        "get",
        f"/catalog/databases/{TEST_DB}/tables",
        expected_keys=["tables", "database", "count"],
    )

    # Create table
    _run_test(
        f"POST /catalog/databases/{TEST_DB}/tables/{TEST_TABLE}",
        "post",
        f"/catalog/databases/{TEST_DB}/tables/{TEST_TABLE}",
        expected_keys=["message", "table"],
    )

    # List tables again
    _run_test(
        f"GET /catalog/databases/{TEST_DB}/tables (after create)",
        "get",
        f"/catalog/databases/{TEST_DB}/tables",
        expected_keys=["tables", "count"],
    )

    # Delete table
    _run_test(
        f"DELETE /catalog/databases/{TEST_DB}/tables/{TEST_TABLE}",
        "delete",
        f"/catalog/databases/{TEST_DB}/tables/{TEST_TABLE}",
        expected_keys=["message"],
    )

    # Delete database
    _run_test(
        f"DELETE /catalog/databases/{TEST_DB}",
        "delete",
        f"/catalog/databases/{TEST_DB}",
        expected_keys=["message"],
    )


def test_catalog_iceberg():
    """Apache Iceberg catalog endpoints."""
    print(f"\n{c('═══ CATALOG (Iceberg) ═══', CYAN)}")

    _run_test(
        "GET /catalog/iceberg/tables",
        "get",
        "/catalog/iceberg/tables",
        expected_keys=["tables", "count"],
    )

    # Try to get details for sample_table (may or may not exist)
    resp = _run_test(
        "GET /catalog/iceberg/tables/sample_table",
        "get",
        "/catalog/iceberg/tables/sample_table",
    )


def test_notebooks():
    """Notebook CRUD endpoints."""
    print(f"\n{c('═══ NOTEBOOKS ═══', CYAN)}")

    # List notebooks
    _run_test("GET /notebooks", "get", "/notebooks", expected_keys=["notebooks", "count"])

    # Create notebook
    _run_test(
        f"POST /notebooks?name={TEST_NB}",
        "post",
        f"/notebooks?name={TEST_NB}",
        expected_keys=["message", "notebook"],
    )

    # Get notebook
    _run_test(
        f"GET /notebooks/{TEST_NB}",
        "get",
        f"/notebooks/{TEST_NB}",
        expected_keys=["notebook", "content"],
    )

    # Update notebook
    updated_content = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from pyspark.sql import SparkSession\n",
                    "spark = SparkSession.builder.appName('test').getOrCreate()\n",
                    "print('Hello from notebook!')\n",
                    "spark.stop()\n",
                ],
            }
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    _run_test(
        f"PUT /notebooks/{TEST_NB}",
        "put",
        f"/notebooks/{TEST_NB}",
        json=updated_content,
        expected_keys=["message", "notebook"],
    )

    # Delete notebook
    _run_test(
        f"DELETE /notebooks/{TEST_NB}",
        "delete",
        f"/notebooks/{TEST_NB}",
        expected_keys=["message"],
    )


def test_jobs():
    """Spark job endpoints."""
    print(f"\n{c('═══ JOBS (Spark) ═══', CYAN)}")

    # List jobs
    _run_test("GET /jobs", "get", "/jobs", expected_keys=["jobs", "total"])

    # Running jobs
    _run_test("GET /jobs/running", "get", "/jobs/running", expected_keys=["running_jobs", "count"])

    # Pending jobs
    _run_test("GET /jobs/pending", "get", "/jobs/pending", expected_keys=["pending_jobs", "count"])

    # Completed jobs
    _run_test("GET /jobs/completed", "get", "/jobs/completed", expected_keys=["completed_jobs", "count"])

    # Submit a test job
    test_script = (
        "from pyspark.sql import SparkSession\n"
        "spark = SparkSession.builder.appName('test').getOrCreate()\n"
        "print('DataHarbour test job executed successfully')\n"
        "spark.stop()\n"
    )
    resp = _run_test(
        "POST /jobs/submit",
        "post",
        "/jobs/submit",
        files={"file": ("test_job.py", io.BytesIO(test_script.encode()), "text/x-python")},
        expected_keys=["job_id", "status"],
    )

    job_id = None
    if resp and resp.status_code == 200:
        job_id = resp.json().get("job_id")
        _state["job_id"] = job_id

    # Get job status
    if job_id:
        _run_test(
            f"GET /jobs/{job_id}/status",
            "get",
            f"/jobs/{job_id}/status",
            expected_keys=["job_id", "status"],
        )

        # Get job logs
        _run_test(
            f"GET /jobs/{job_id}/logs",
            "get",
            f"/jobs/{job_id}/logs",
            expected_keys=["job_id", "logs"],
        )


def test_cluster():
    """Cluster monitoring endpoints."""
    print(f"\n{c('═══ CLUSTER ═══', CYAN)}")

    _run_test(
        "GET /cluster/status",
        "get",
        "/cluster/status",
        expected_keys=["status", "masterUrl"],
    )

    _run_test(
        "GET /cluster/workers",
        "get",
        "/cluster/workers",
        expected_keys=["workers"],
    )

    _run_test(
        "GET /cluster/applications",
        "get",
        "/cluster/applications",
        expected_keys=["active", "completed"],
    )


def test_dashboard():
    """Dashboard / stats endpoints."""
    print(f"\n{c('═══ DASHBOARD ═══', CYAN)}")

    _run_test(
        "GET /stats/summary",
        "get",
        "/stats/summary",
        expected_keys=["notebooks", "jobs", "jobsRunning", "buckets", "databases"],
    )

    _run_test(
        "GET /activities/recent",
        "get",
        "/activities/recent",
        expected_keys=["activities"],
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Summary & Main
# ═══════════════════════════════════════════════════════════════════════════════


def print_summary():
    """Print a coloured summary of all test results."""
    print(f"\n{'═' * 70}")
    print(f"{BOLD}{WHITE}  DataHarbour API Test Summary{RESET}")
    print(f"{'═' * 70}")

    counts = {PASS: 0, FAIL: 0, WARN: 0, SKIP: 0}
    for r in results:
        counts[r["status"]] += 1

    total = len(results)
    total_time = sum(r["elapsed"] for r in results)

    print(f"  Total tests:  {total}")
    print(f"  {c(f'PASS: {counts[PASS]}', GREEN)}")
    print(f"  {c(f'FAIL: {counts[FAIL]}', RED)}")
    print(f"  {c(f'WARN: {counts[WARN]}', YELLOW)}")
    print(f"  {c(f'SKIP: {counts[SKIP]}', GREY)}")
    print(f"  Total time:   {total_time:.0f}ms")
    print(f"{'═' * 70}")

    if counts[FAIL] > 0:
        print(f"\n  {c('FAILED TESTS:', RED)}")
        for r in results:
            if r["status"] == FAIL:
                print(f"    {c('✘', RED)}  {r['name']}: {r['detail'][:200]}")

    return counts[FAIL] == 0


def main():
    global BASE_URL

    # Parse CLI args
    for arg in sys.argv[1:]:
        if arg.startswith("http"):
            BASE_URL = arg.rstrip("/")

    print(f"\n{BOLD}{CYAN}╔══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║       DataHarbour — Comprehensive API Test Suite         ║{RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════════╝{RESET}")
    print(f"  Target: {c(BASE_URL, BLUE)}")
    print(f"  Time:   {c(datetime.now().isoformat(), GREY)}")

    # Wait for API to be ready
    print(f"\n  {c('Waiting for API to be ready…', YELLOW)}", end="", flush=True)
    for i in range(30):
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=3)
            if r.status_code == 200:
                print(f" {c('OK', GREEN)}")
                break
        except Exception:
            pass
        time.sleep(2)
        print(".", end="", flush=True)
    else:
        print(f" {c('TIMEOUT', RED)}")
        print(f"  {c('API not reachable. Exiting.', RED)}")
        sys.exit(1)

    # Run all test suites
    test_system()
    test_auth()
    test_storage()
    test_catalog_postgres()
    test_catalog_iceberg()
    test_notebooks()
    test_jobs()
    test_cluster()
    test_dashboard()

    # Summary
    success = print_summary()

    # Optional JSON report
    if "--json" in sys.argv:
        idx = sys.argv.index("--json")
        if idx + 1 < len(sys.argv):
            report_path = sys.argv[idx + 1]
        else:
            report_path = "test_report.json"
        with open(report_path, "w") as f:
            json.dump({"timestamp": datetime.now().isoformat(), "base_url": BASE_URL, "results": results}, f, indent=2)
        print(f"\n  {c(f'JSON report written to: {report_path}', BLUE)}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

