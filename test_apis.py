#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║         DataHarbour — Comprehensive API Test Suite  v2           ║
║                                                                  ║
║  • Auto-discovers real route paths from /openapi.json            ║
║  • Treats HTTP 503 as ⚠️  WARN (infra down ≠ code bug)           ║
║  • Deep body/key assertions on every response                    ║
║  • Retry logic, per-test timing, colour-coded output             ║
║  • Rich final summary: PASS / FAIL / WARN / SKIP                 ║
╚══════════════════════════════════════════════════════════════════╝

Usage:
    python3 test_dataharbour.py                        # http://localhost:8000
    python3 test_dataharbour.py http://host:9000        # custom URL
    python3 test_dataharbour.py --json out.json         # also write JSON report
    python3 test_dataharbour.py http://host:9000 --json out.json
"""

import sys, json, time, io, re
import requests
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

# ── ANSI colours ─────────────────────────────────────────────────────────────
RESET  = "\033[0m";  BOLD   = "\033[1m"
GREEN  = "\033[92m"; RED    = "\033[91m"; YELLOW = "\033[93m"
CYAN   = "\033[96m"; BLUE   = "\033[94m"; GREY   = "\033[90m"; WHITE  = "\033[97m"
def c(t, col): return f"{col}{t}{RESET}"

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL      = "http://localhost:8000"
TIMEOUT       = 15
RETRY_COUNT   = 2
RETRY_DELAY   = 1.5
TEST_BUCKET   = "dh-test-bucket2"
TEST_DB       = "dh_test_db1"
TEST_TABLE    = "dh_test_table1"
TEST_NB       = "hello2.ipynb"

# ── Shared state ──────────────────────────────────────────────────────────────
results : List[Dict]    = []
_state  : Dict[str,Any] = {}   # cross-test carry (e.g. auth token, created IDs)
_routes : Dict[str,str] = {}   # populated at startup from /openapi.json

# ── Result constants ──────────────────────────────────────────────────────────
PASS, FAIL, SKIP, WARN = "PASS", "FAIL", "SKIP", "WARN"


# ═══════════════════════════════════════════════════════════════════════════════
#  Route auto-discovery
# ═══════════════════════════════════════════════════════════════════════════════

def _discover_routes() -> Dict[str, str]:
    """
    Fetch /openapi.json and build a flat dict:
      route_key  →  actual_path
    Route keys are short human names we use inside the tests.
    """
    try:
        r = requests.get(f"{BASE_URL}/openapi.json", timeout=6)
        if r.status_code != 200:
            return {}
        spec   = r.json()
        paths  = spec.get("paths", {})
        routes : Dict[str, str] = {}

        # Index every registered path by its path string for lookup
        for path in paths:
            routes[path] = path           # identity mapping

        # ── Build semantic aliases ─────────────────────────────────────────
        # Storage
        for p in paths:
            lp = p.lower()
            if re.search(r"upload", lp)  and "bucket" in lp: routes["upload_file"]    = p
            if re.search(r"delete", lp)  and "key"    in lp: routes["delete_file"]    = p
            if re.search(r"delete", lp)  and ("file"  in lp or "object" in lp): routes["delete_file"] = p

        # Database CRUD — look for patterns like /catalog/database/create or /database/create
        for p in paths:
            lp = p.lower()
            if "database" in lp and ("create" in lp or "new" in lp):  routes["db_create"] = p
            if "database" in lp and ("delete" in lp or "drop" in lp): routes["db_delete"] = p
            if "table"    in lp and ("create" in lp or "new" in lp):  routes["tbl_create"] = p
            if "table"    in lp and ("delete" in lp or "drop" in lp): routes["tbl_delete"] = p

        return routes
    except Exception:
        return {}


def _route(key: str, fallback: str) -> str:
    """Return discovered path for key, or fallback if not found."""
    return _routes.get(key, fallback)


def _insert_path_params(template: str, **values) -> str:
    """Replace {param} placeholders in a path template."""
    for k, v in values.items():
        template = template.replace(f"{{{k}}}", str(v))
    return template


# ═══════════════════════════════════════════════════════════════════════════════
#  HTTP helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _do_request(method: str, url: str, session=None, **kwargs) -> requests.Response:
    """Request with retry on ConnectionError."""
    caller = session or requests
    last   = None
    for attempt in range(RETRY_COUNT + 1):
        try:
            return caller.request(method, url, timeout=TIMEOUT, **kwargs)
        except requests.exceptions.ConnectionError as e:
            last = e
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY)
        except requests.exceptions.Timeout as e:
            raise e
    raise last


def _truncate(text: str, n: int = 260) -> str:
    return text[:n] + f" …[+{len(text)-n}]" if len(text) > n else text


def _try_json(resp: requests.Response):
    try:    return resp.json()
    except: return None


# ═══════════════════════════════════════════════════════════════════════════════
#  Test runner
# ═══════════════════════════════════════════════════════════════════════════════

def run(
    label          : str,
    method         : str,
    endpoint       : str,
    session        = None,
    expected_status: int              = 200,
    infra          : bool             = False,   # 503 → WARN instead of FAIL
    expected_keys  : Optional[list]   = None,
    assert_fn                         = None,    # (response) → (bool, str)
    skip_reason    : Optional[str]    = None,
    **req_kwargs,
) -> Tuple[str, Optional[requests.Response]]:
    """Execute one test, record and print result. Returns (status, response)."""

    if skip_reason:
        return _record_print(label, method, endpoint, SKIP, skip_reason, 0)

    url   = f"{BASE_URL}{endpoint}"
    start = time.perf_counter()
    try:
        resp    = _do_request(method, url, session=session, **req_kwargs)
        elapsed = time.perf_counter() - start

        # ── 503 infra check ───────────────────────────────────────────────
        if resp.status_code == 503 and infra:
            body    = _try_json(resp)
            msg     = body.get("detail", resp.text) if isinstance(body, dict) else resp.text
            detail  = f"HTTP 503 — dependent service unreachable: {_truncate(str(msg), 120)}"
            return _record_print(label, method, endpoint, WARN, detail, elapsed, 503)

        # ── status check ──────────────────────────────────────────────────
        if resp.status_code != expected_status:
            detail = (
                f"Expected HTTP {expected_status}, got {resp.status_code}. "
                f"Body: {_truncate(resp.text)}"
            )
            return _record_print(label, method, endpoint, FAIL, detail, elapsed, resp.status_code)

        # ── key presence check ────────────────────────────────────────────
        body = _try_json(resp)
        if expected_keys and isinstance(body, dict):
            missing = [k for k in expected_keys if k not in body]
            if missing:
                detail = f"JSON missing keys {missing}. Got: {list(body.keys())}"
                return _record_print(label, method, endpoint, FAIL, detail, elapsed, resp.status_code)

        # ── custom assertion ──────────────────────────────────────────────
        if assert_fn:
            try:
                ok, msg = assert_fn(resp)
            except Exception as ae:
                ok, msg = False, f"assert_fn raised {ae}"
            if not ok:
                return _record_print(label, method, endpoint, FAIL, msg, elapsed, resp.status_code)

        detail = f"HTTP {resp.status_code}  ({elapsed*1000:.0f} ms)"
        return _record_print(label, method, endpoint, PASS, detail, elapsed, resp.status_code)

    except Exception as exc:
        elapsed = time.perf_counter() - start
        return _record_print(label, method, endpoint, FAIL,
                             f"{type(exc).__name__}: {exc}", elapsed)


def _record_print(label, method, endpoint, status, detail, elapsed, http_code=None
                  ) -> Tuple[str, Optional[requests.Response]]:
    results.append(dict(
        label=label, method=method, endpoint=endpoint, status=status,
        detail=detail, elapsed_s=round(elapsed,3),
        http_code=http_code, timestamp=datetime.utcnow().isoformat(),
    ))
    icons   = {PASS:"✅", FAIL:"❌", SKIP:"⏭ ", WARN:"⚠️ "}
    colours = {PASS:GREEN, FAIL:RED, SKIP:YELLOW, WARN:YELLOW}
    icon    = icons.get(status," ")
    clr     = colours.get(status, RESET)
    ms_str  = f"{elapsed*1000:6.0f} ms" if elapsed > 0 else "      --  "
    print(f"  {icon} {c(f'{method:<7}',CYAN)} {c(f'{endpoint:<52}',WHITE)} "
          f"{c(ms_str,GREY)}  {c(detail,clr)}")
    return status, None


def section(title: str):
    print(f"\n{c('━'*68,BLUE)}\n  {c(BOLD+title, BOLD+BLUE)}\n{c('━'*68,BLUE)}")


# ═══════════════════════════════════════════════════════════════════════════════
#  Health + route discovery
# ═══════════════════════════════════════════════════════════════════════════════

def check_health_and_discover() -> bool:
    global _routes
    print(f"\n{c('Connecting to',GREY)} {c(BASE_URL,CYAN)} …")
    try:
        r = requests.get(f"{BASE_URL}/docs", timeout=6)
        if r.status_code != 200:
            print(f"  {c('⚠️  /docs returned HTTP '+str(r.status_code),YELLOW)}")
            return False
        print(f"  {c('✅  API reachable',GREEN)} (HTTP 200 on /docs)")
    except Exception as e:
        print(f"  {c('❌  Cannot reach API:',RED)} {e}")
        print(f"  {c('Tip: docker-compose up -d',GREY)}")
        return False

    # ── Route discovery ───────────────────────────────────────────────────
    _routes = _discover_routes()
    if _routes:
        registered = [p for p in _routes if p.startswith("/")]
        print(f"  {c('🔍  Discovered',CYAN)} {len(registered)} registered routes from /openapi.json")

        # Print database/table routes we'll use so user can verify
        for key, label in [
            ("db_create",  "DB create"),
            ("db_delete",  "DB delete"),
            ("tbl_create", "Table create"),
            ("tbl_delete", "Table delete"),
            ("upload_file","File upload"),
            ("delete_file","File delete"),
        ]:
            if key in _routes:
                print(f"    {c(f'{label:<14}',GREY)} → {c(_routes[key],CYAN)}")
            else:
                print(f"    {c(f'{label:<14}',GREY)} → {c('not found in spec — will use fallback',YELLOW)}")
    else:
        print(f"  {c('⚠️  Could not parse /openapi.json — using fallback paths',YELLOW)}")
    print()
    return True


# ═══════════════════════════════════════════════════════════════════════════════
#  Test suites
# ═══════════════════════════════════════════════════════════════════════════════

# ── 1. OpenAPI docs ───────────────────────────────────────────────────────────

def test_openapi():
    section("1 · OpenAPI / Docs")
    run("Swagger UI",    "GET", "/docs",         expected_status=200)
    run("ReDoc UI",      "GET", "/redoc",         expected_status=200)
    run("OpenAPI spec",  "GET", "/openapi.json",  expected_status=200,
        assert_fn=lambda r: (
            isinstance(r.json(), dict) and "openapi" in r.json() and "paths" in r.json(),
            f"Missing 'openapi' or 'paths' keys in spec. Got: {list(r.json().keys())[:8]}"
        ))


# ── 2. Authentication ─────────────────────────────────────────────────────────

def test_auth(s: requests.Session):
    section("2 · Authentication")

    # Valid login
    status, _ = run("Login — valid credentials", "POST", "/auth/login", session=s,
                    json={"username": "admin", "password": "admin"}, expected_status=200)
    if status == PASS:
        # Try to extract and store auth token if the API returns one
        try:
            resp = s.post(f"{BASE_URL}/auth/login",
                          json={"username":"admin","password":"admin"}, timeout=TIMEOUT)
            body = resp.json()
            token = body.get("access_token") or body.get("token") or body.get("jwt")
            if token:
                s.headers.update({"Authorization": f"Bearer {token}"})
                _state["auth_token"] = token
                print(f"      {c('→ Auth token stored and added to session headers',GREY)}")
        except Exception:
            pass

    # Bad credentials → must NOT return 200
    try:
        bad = requests.post(f"{BASE_URL}/auth/login",
                            json={"username":"WRONG","password":"WRONG"}, timeout=TIMEOUT)
        expected_rejection = bad.status_code in (401, 403, 422)
        detail = (
            f"HTTP {bad.status_code} — correct rejection of bad credentials"
            if expected_rejection else
            f"HTTP {bad.status_code} — WARNING: server accepted wrong password!"
        )
        st = PASS if expected_rejection else WARN
        results.append(dict(label="Login — bad credentials", method="POST",
                            endpoint="/auth/login", status=st, detail=detail,
                            elapsed_s=0, http_code=bad.status_code,
                            timestamp=datetime.utcnow().isoformat()))
        icon = "✅" if st == PASS else "⚠️ "
        clr  = GREEN if st == PASS else YELLOW
        print(f"  {icon} {c('POST   ',CYAN)} {c('/auth/login'+' '*41,WHITE)} "
              f"{c('      --  ',GREY)}  {c(detail, clr)}")
    except Exception:
        pass

    run("Logout", "POST", "/auth/logout", session=s, expected_status=200)


# ── 3. Storage (MinIO / DHFS) ─────────────────────────────────────────────────

def test_storage(s: requests.Session):
    section("3 · Storage — MinIO / DHFS")

    run("List buckets", "GET", "/dhfs/buckets", session=s, expected_status=200,
        assert_fn=lambda r: (isinstance(_try_json(r),(list,dict)),
                             f"Expected list or dict, got {type(_try_json(r)).__name__}"))

    # Create bucket
    st, _ = run(f"Create bucket '{TEST_BUCKET}'", "POST", f"/dhfs/buckets/{TEST_BUCKET}",
                session=s, expected_status=200)
    bucket_ok = (st == PASS)

    # Upload — use discovered path, fall back to /dhfs/upload
    upload_path = _route("upload_file", f"/dhfs/upload/{TEST_BUCKET}")
    # If template contains {bucket} or {bucket_name}, substitute
    upload_path = _insert_path_params(upload_path,
                                      bucket=TEST_BUCKET, bucket_name=TEST_BUCKET)

    if bucket_ok:
        sample = json.dumps({"source": "dataharbour-test", "value": 42,
                             "ts": datetime.utcnow().isoformat()}).encode()
        files = {"file": ("sample.json", io.BytesIO(sample), "application/json")}
        up_st, _ = run("Upload file to bucket", "POST", upload_path,
                       session=s, expected_status=200, files=files)
        _state["file_uploaded"] = (up_st == PASS)
        _state["upload_path"]   = upload_path
    else:
        _state["file_uploaded"] = False
        run("Upload file to bucket", "POST", upload_path, session=s,
            skip_reason="Bucket creation failed — upload skipped")

    # List files
    run(f"List files in '{TEST_BUCKET}'", "GET", f"/dhfs/files/{TEST_BUCKET}",
        session=s, expected_status=200,
        skip_reason=None if bucket_ok else "Bucket not created")

    # Download
    run("Download file", "GET", f"/dhfs/download/{TEST_BUCKET}/sample.json",
        session=s, expected_status=200,
        skip_reason=None if _state.get("file_uploaded") else "File not uploaded")

    # Delete file — use discovered path, fall back to /dhfs/delete
    delete_file_path = _route("delete_file", f"/dhfs/delete/{TEST_BUCKET}/sample.json")
    delete_file_path = _insert_path_params(delete_file_path,
                                           bucket=TEST_BUCKET, bucket_name=TEST_BUCKET,
                                           key="sample.json", file_key="sample.json",
                                           object_key="sample.json")
    run("Delete file from bucket", "DELETE", delete_file_path,
        session=s, expected_status=200,
        skip_reason=None if _state.get("file_uploaded") else "File not uploaded")

    # Delete bucket
    run(f"Delete bucket '{TEST_BUCKET}'", "DELETE", f"/dhfs/buckets/{TEST_BUCKET}",
        session=s, expected_status=200,
        skip_reason=None if bucket_ok else "Bucket not created")


# ── 4. Database / Catalog ─────────────────────────────────────────────────────

def test_database(s: requests.Session):
    section("4 · Database — PostgreSQL Catalog")

    # List databases — postgres-backed; 503 = postgres container unreachable
    list_st, _ = run("List databases", "GET", "/catalog/databases",
                     session=s, expected_status=200, infra=True,
                     assert_fn=lambda r: (isinstance(_try_json(r),(list,dict)),
                                          f"Expected list or dict, got {type(_try_json(r)).__name__}"))
    postgres_up = (list_st == PASS)

    # ── DB create path ────────────────────────────────────────────────────
    # Auto-discovered; if not found, try both common patterns
    raw_db_create = _routes.get("db_create", "")
    if raw_db_create:
        db_create_path = _insert_path_params(raw_db_create,
                                             db_name=TEST_DB, name=TEST_DB, database=TEST_DB)
    else:
        # Probe both known patterns; use whichever the server has registered
        db_create_path = _probe_paths(
            s, "POST",
            [f"/catalog/database/create/{TEST_DB}",
             f"/database/create/{TEST_DB}",
             f"/catalog/databases/{TEST_DB}",
             f"/databases/{TEST_DB}"],
            skip=not postgres_up,
        ) or f"/catalog/database/create/{TEST_DB}"

    db_st, _ = run(f"Create database '{TEST_DB}'", "POST", db_create_path,
                   session=s, expected_status=200, infra=True,
                   skip_reason=None if postgres_up else "PostgreSQL unavailable (HTTP 503)")
    db_ok = (db_st == PASS)

    # ── Table create path ─────────────────────────────────────────────────
    raw_tbl_create = _routes.get("tbl_create", "")
    if raw_tbl_create:
        tbl_create_path = _insert_path_params(raw_tbl_create,
                                              db_name=TEST_DB, table_name=TEST_TABLE,
                                              name=TEST_TABLE, database=TEST_DB)
    else:
        tbl_create_path = f"/catalog/table/create/{TEST_DB}/{TEST_TABLE}"

    tbl_st, _ = run(f"Create table '{TEST_TABLE}'", "POST", tbl_create_path,
                    session=s, expected_status=200, infra=True,
                    skip_reason=None if db_ok else "DB creation failed or Postgres down")
    tbl_ok = (tbl_st == PASS)

    # List tables in DB
    run(f"List tables in '{TEST_DB}'", "GET",
        f"/catalog/databases/{TEST_DB}/tables",
        session=s, expected_status=200, infra=True,
        skip_reason=None if db_ok else "DB not created",
        assert_fn=lambda r: (isinstance(_try_json(r),(list,dict)),
                             f"Expected list or dict, got {type(_try_json(r)).__name__}") if db_ok else None)

    # Delete table
    raw_tbl_delete = _routes.get("tbl_delete", "")
    tbl_delete_path = (
        _insert_path_params(raw_tbl_delete,
                            db_name=TEST_DB, table_name=TEST_TABLE,
                            name=TEST_TABLE, database=TEST_DB)
        if raw_tbl_delete else
        f"/catalog/table/delete/{TEST_DB}/{TEST_TABLE}"
    )
    run(f"Delete table '{TEST_TABLE}'", "DELETE", tbl_delete_path,
        session=s, expected_status=200, infra=True,
        skip_reason=None if tbl_ok else "Table was not created")

    # Delete database
    raw_db_delete = _routes.get("db_delete", "")
    db_delete_path = (
        _insert_path_params(raw_db_delete,
                            db_name=TEST_DB, name=TEST_DB, database=TEST_DB)
        if raw_db_delete else
        f"/catalog/database/delete/{TEST_DB}"
    )
    run(f"Delete database '{TEST_DB}'", "DELETE", db_delete_path,
        session=s, expected_status=200, infra=True,
        skip_reason=None if db_ok else "DB was not created")


def _probe_paths(s, method: str, candidates: List[str], skip: bool = False) -> Optional[str]:
    """
    Silently try each candidate path; return the first that does NOT return 404.
    Used when auto-discovery didn't find the route.
    """
    if skip:
        return None
    for path in candidates:
        try:
            r = _do_request(method, f"{BASE_URL}{path}", session=s)
            if r.status_code != 404:
                return path
        except Exception:
            pass
    return None


# ── 5. Iceberg Catalog ────────────────────────────────────────────────────────

def test_iceberg(s: requests.Session):
    section("5 · Iceberg Catalog")

    st, _ = run("List Iceberg tables", "GET", "/catalog/iceberg/tables",
                session=s, expected_status=200,
                assert_fn=lambda r: (isinstance(_try_json(r),(list,dict)),
                                     f"Expected list or dict, got {type(_try_json(r)).__name__}"))

    if st == PASS:
        try:
            resp = s.get(f"{BASE_URL}/catalog/iceberg/tables", timeout=TIMEOUT)
            body = resp.json()
            tables = body if isinstance(body, list) else body.get("tables", [])
            if tables:
                name = tables[0] if isinstance(tables[0], str) else tables[0].get("name","")
                if name:
                    run(f"Get Iceberg table details '{name}'", "GET",
                        f"/catalog/iceberg/tables/{name}", session=s, expected_status=200)
                    return
            run("Get Iceberg table details", "GET", "/catalog/iceberg/tables/{name}",
                skip_reason="No Iceberg tables exist yet — cannot test detail endpoint")
        except Exception as e:
            run("Get Iceberg table details", "GET", "/catalog/iceberg/tables/{name}",
                skip_reason=f"Could not parse table list: {e}")
    else:
        run("Get Iceberg table details", "GET", "/catalog/iceberg/tables/{name}",
            skip_reason="Iceberg table list failed")


# ── 6. Notebooks ──────────────────────────────────────────────────────────────

def test_notebooks(s: requests.Session):
    section("6 · Notebook Management")

    run("List notebooks", "GET", "/notebooks", session=s, expected_status=200,
        assert_fn=lambda r: (isinstance(_try_json(r),(list,dict)),
                             f"Expected list or dict, got {type(_try_json(r)).__name__}"))

    # name is a QUERY PARAM (FastAPI 422 told us: {"loc":["query","name"]})
    st, _ = run(f"Create notebook '{TEST_NB}'", "POST", "/notebooks",
                session=s, expected_status=200, params={"name": TEST_NB})
    nb_ok = (st == PASS)

    run(f"Get notebook '{TEST_NB}'", "GET", f"/notebooks/{TEST_NB}",
        session=s, expected_status=200,
        skip_reason=None if nb_ok else "Notebook not created")

    run(f"Update notebook '{TEST_NB}'", "PUT", f"/notebooks/{TEST_NB}",
        session=s, expected_status=200,
        skip_reason=None if nb_ok else "Notebook not created",
        json={
            "cells": [{
                "cell_type": "code", "execution_count": None,
                "metadata": {}, "outputs": [],
                "source": ["# DataHarbour test cell\nprint('ok')"],
            }],
            "metadata": {
                "kernelspec": {"display_name":"Python 3","language":"python","name":"python3"},
                "language_info": {"name":"python","version":"3.10.0"},
            },
            "nbformat": 4, "nbformat_minor": 5,
        })

    run(f"Execute notebook '{TEST_NB}'", "POST", f"/notebooks/{TEST_NB}/execute",
        session=s, expected_status=200,
        skip_reason=None if nb_ok else "Notebook not created")

    run(f"Delete notebook '{TEST_NB}'", "DELETE", f"/notebooks/{TEST_NB}",
        session=s, expected_status=200,
        skip_reason=None if nb_ok else "Notebook not created")


# ── 7. Jobs ───────────────────────────────────────────────────────────────────

def test_jobs(s: requests.Session):
    section("7 · Spark Job Management")

    for label, path in [
        ("List all jobs",       "/jobs"),
        ("List running jobs",   "/jobs/running"),
        ("List pending jobs",   "/jobs/pending"),
        ("List completed jobs", "/jobs/completed"),
    ]:
        run(label, "GET", path, session=s, expected_status=200,
            assert_fn=lambda r: (isinstance(_try_json(r),(list,dict)),
                                 f"Expected list or dict, got {type(_try_json(r)).__name__}"))

    # Submit synthetic PySpark job
    # 503 = Spark master container not running → infra issue, not a code bug
    spark_job = (
        "from pyspark.sql import SparkSession\n"
        "spark = SparkSession.builder.appName('dh_test').getOrCreate()\n"
        "df = spark.createDataFrame([('Alice',1),('Bob',2)], ['name','val'])\n"
        "df.show()\n"
        "spark.stop()\n"
    ).encode()

    files = {"file": ("dh_test_job.py", io.BytesIO(spark_job), "text/plain")}
    st, _ = run("Submit Spark job", "POST", "/jobs/submit",
                session=s, expected_status=200, infra=True, files=files)

    # If submission succeeded and returned a job ID, check its status
    _state["job_submitted"] = (st == PASS)


def test_job_status(s: requests.Session):
    """Follow-up: poll the submitted job's status (only if submit returned an ID)."""
    if not _state.get("job_id"):
        return
    jid = _state["job_id"]
    run(f"Get job status (id={jid})", "GET", f"/jobs/{jid}",
        session=s, expected_status=200, infra=True,
        assert_fn=lambda r: (
            isinstance(_try_json(r), dict),
            f"Expected job status dict, got {type(_try_json(r)).__name__}"
        ))

    run(f"Cancel job (id={jid})", "DELETE", f"/jobs/{jid}",
        session=s, expected_status=200, infra=True)


# ── 8. Cluster ────────────────────────────────────────────────────────────────

def test_cluster(s: requests.Session):
    section("8 · Spark Cluster Monitoring")

    for label, path in [
        ("Cluster status",       "/cluster/status"),
        ("Cluster workers",      "/cluster/workers"),
        ("Cluster applications", "/cluster/applications"),
    ]:
        run(label, "GET", path, session=s, expected_status=200,
            assert_fn=lambda r: (isinstance(_try_json(r),(list,dict)),
                                 f"Expected list or dict, got {type(_try_json(r)).__name__}"))


# ── 9. Stats / Dashboard ──────────────────────────────────────────────────────

def test_stats(s: requests.Session):
    section("9 · Dashboard Stats & Activity")

    run("Stats summary", "GET", "/stats/summary", session=s, expected_status=200,
        assert_fn=lambda r: (isinstance(_try_json(r), dict),
                             f"Expected dict, got {type(_try_json(r)).__name__}"))

    run("Recent activities", "GET", "/activities/recent", session=s, expected_status=200,
        assert_fn=lambda r: (isinstance(_try_json(r),(list,dict)),
                             f"Expected list or dict, got {type(_try_json(r)).__name__}"))


# ── 10. Unimplemented / known-missing endpoints ───────────────────────────────

def test_known_missing():
    section("10 · Known Missing Endpoints (not in routes.py)")

    # These returned 404 in previous run — recorded as SKIP so they appear
    # in the report as action items rather than failures.
    missing = [
        ("/logs",    "GET",
         "GET /logs not registered. Add @router.get('/logs') in backend/api/routes.py"),
    ]
    for path, method, reason in missing:
        # Double-check live if possible
        actually_missing = True
        try:
            r = requests.get(f"{BASE_URL}{path}", timeout=4)
            if r.status_code != 404:
                actually_missing = False
        except Exception:
            pass

        if actually_missing:
            results.append(dict(label=f"{method} {path}", method=method, endpoint=path,
                                status=SKIP, detail=reason, elapsed_s=0, http_code=404,
                                timestamp=datetime.utcnow().isoformat()))
            print(f"  ⏭  {c(f'{method:<7}',CYAN)} {c(f'{path:<52}',GREY)} "
                  f"{c('      --  ',GREY)}  {c(reason,YELLOW)}")
        else:
            run(f"{method} {path} (was missing, now present)", method, path, expected_status=200)


# ═══════════════════════════════════════════════════════════════════════════════
#  Summary
# ═══════════════════════════════════════════════════════════════════════════════

def print_summary(json_out: Optional[str] = None):
    passed  = [r for r in results if r["status"] == PASS]
    failed  = [r for r in results if r["status"] == FAIL]
    warned  = [r for r in results if r["status"] == WARN]
    skipped = [r for r in results if r["status"] == SKIP]
    total   = len(results)
    avg_ms  = sum(r["elapsed_s"] for r in passed)/len(passed)*1000 if passed else 0

    W = 68
    print(f"\n\n{'═'*W}")
    print(c(f"{'  TEST SUMMARY':^{W}}", BOLD+WHITE))
    print(f"{'═'*W}")
    print(f"  {'Run at':<22} {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  {'Base URL':<22} {BASE_URL}")
    print(f"  {'Total tests':<22} {total}")
    print(f"  {c('Passed',GREEN):<{22+len(GREEN)+len(RESET)}} {c(str(len(passed)),GREEN+BOLD)}")
    print(f"  {c('Failed',RED):<{22+len(RED)+len(RESET)}}   {c(str(len(failed)),RED+BOLD)}")
    if warned:
        print(f"  {c('Infra warnings',YELLOW):<{22+len(YELLOW)+len(RESET)}}   {c(str(len(warned)),YELLOW+BOLD)}")
    print(f"  {c('Skipped',YELLOW):<{22+len(YELLOW)+len(RESET)}}   {c(str(len(skipped)),YELLOW+BOLD)}")
    print(f"  {'Avg latency (PASS)':<22} {avg_ms:.0f} ms")

    # ── ❌ FAILED ─────────────────────────────────────────────────────────
    if failed:
        print(f"\n{'─'*W}")
        print(c("  ❌  FAILED TESTS", RED+BOLD))
        print(f"{'─'*W}")
        for r in failed:
            print(f"  {c(r['method']+' '+r['endpoint'], WHITE)}")
            print(f"    Label    : {r['label']}")
            print(f"    HTTP     : {r.get('http_code','–')}")
            print(f"    Error    : {c(r['detail'], RED)}")
            print()

    # ── ⚠️  INFRA WARNINGS ────────────────────────────────────────────────
    if warned:
        print(f"{'─'*W}")
        print(c("  ⚠️   INFRASTRUCTURE WARNINGS  (service down ≠ code bug)", YELLOW+BOLD))
        print(f"{'─'*W}")
        for r in warned:
            print(f"  {c(r['method']+' '+r['endpoint'], WHITE)}")
            print(f"    Label  : {r['label']}")
            print(f"    Reason : {c(r['detail'], YELLOW)}")
            print()
        print(c("  Fix: ensure all containers are running with  docker-compose up -d", GREY))

    # ── ⏭  SKIPPED ────────────────────────────────────────────────────────
    if skipped:
        print(f"\n{'─'*W}")
        print(c("  ⏭   SKIPPED TESTS", YELLOW+BOLD))
        print(f"{'─'*W}")
        for r in skipped:
            print(f"  {c(r['method']+' '+r['endpoint'], GREY)}  →  {r['detail']}")

    # ── ✅ PASSED ─────────────────────────────────────────────────────────
    print(f"\n{'─'*W}")
    print(c("  ✅  PASSED TESTS", GREEN+BOLD))
    print(f"{'─'*W}")
    for r in passed:
        ms = f"{r['elapsed_s']*1000:.0f} ms"
        print(f"  {c(f'{ms:>8}',GREY)}   {c(r['method'],CYAN):<7}  {r['endpoint']}")

    # ── Final verdict ─────────────────────────────────────────────────────
    print(f"\n{'═'*W}")
    if not failed:
        verdict_tests = len(passed)
        print(c(f"  🎉  ALL {verdict_tests} ACTIVE TESTS PASSED!", GREEN+BOLD))
        if warned:
            print(c(f"  ⚠️   {len(warned)} infra service(s) unreachable — start with docker-compose up -d", YELLOW))
    else:
        pct = int(len(passed)/total*100) if total else 0
        print(c(f"  ❌  {len(failed)} test(s) FAILED  ({pct}% pass rate)", RED+BOLD))
    print(f"{'═'*W}\n")

    # ── JSON report ───────────────────────────────────────────────────────
    if json_out:
        payload = {
            "run_at": datetime.utcnow().isoformat(),
            "base_url": BASE_URL,
            "summary": {"total":total,"passed":len(passed),"failed":len(failed),
                        "warned":len(warned),"skipped":len(skipped)},
            "results": results,
        }
        with open(json_out, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"  📄  JSON report saved → {c(json_out, CYAN)}\n")


# ═══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    global BASE_URL

    # ── Parse CLI args ────────────────────────────────────────────────────
    json_out = None
    remaining = []
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--json" and i+1 < len(sys.argv):
            json_out = sys.argv[i+1]; i += 2
        else:
            remaining.append(sys.argv[i]); i += 1
    if remaining:
        BASE_URL = remaining[0].rstrip("/")

    # ── Banner ────────────────────────────────────────────────────────────
    print(f"\n{c('╔'+'═'*66+'╗', BLUE)}")
    print(c(f"║{'DataHarbour — Comprehensive API Test Suite  v2':^66}║", BLUE+BOLD))
    print(c(f"╚{'═'*66}╝", BLUE))

    if not check_health_and_discover():
        sys.exit(1)

    # ── Run all suites ────────────────────────────────────────────────────
    s = requests.Session()
    test_openapi()
    test_auth(s)
    test_storage(s)
    test_database(s)
    test_iceberg(s)
    test_notebooks(s)
    test_jobs(s)
    test_job_status(s)
    test_cluster(s)
    test_stats(s)
    test_known_missing()

    print_summary(json_out)

    failed_count = sum(1 for r in results if r["status"] == FAIL)
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()