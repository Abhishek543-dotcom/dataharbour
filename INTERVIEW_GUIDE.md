# DataHarbour — Complete Interview Guide

> **One-liner pitch:** _"I built DataHarbour — a lightweight, containerized Data Lakehouse platform with a REST API that orchestrates Apache Spark, MinIO object storage, PostgreSQL, and Apache Iceberg for local data engineering development."_

---

## Table of Contents

1. [What is DataHarbour?](#1-what-is-dataharbour)
2. [High-Level Design (HLD)](#2-high-level-design-hld)
3. [Low-Level Design (LLD)](#3-low-level-design-lld)
4. [Technology Stack & Tools](#4-technology-stack--tools)
5. [How It Works — End-to-End Flow](#5-how-it-works--end-to-end-flow)
6. [API Endpoints Reference](#6-api-endpoints-reference)
7. [Architecture Patterns Used](#7-architecture-patterns-used)
8. [Advantages](#8-advantages)
9. [Disadvantages & Limitations](#9-disadvantages--limitations)
10. [What Can Be Enhanced](#10-what-can-be-enhanced)
11. [Interview Q&A Cheat Sheet](#11-interview-qa-cheat-sheet)

---

## 1. What is DataHarbour?

DataHarbour is a **self-contained, Docker-based data engineering platform** that provides:

- **Spark Job Management** — Upload, submit, monitor, and kill PySpark jobs via REST API
- **Object Storage (MinIO)** — S3-compatible file storage with bucket and file CRUD operations
- **Relational Database (PostgreSQL)** — Database/table creation, metadata catalog
- **Apache Iceberg** — Open table format for data lakehouse with metadata browsing
- **Notebook Management** — Create, edit, execute Jupyter notebooks as Spark jobs
- **Cluster Monitoring** — Real-time Spark cluster health, worker stats, and application tracking
- **Dashboard Stats** — Aggregated metrics for an operational overview

**In simple terms:** It's like a mini **Databricks/AWS EMR** that runs entirely on your laptop using Docker.

---

## 2. High-Level Design (HLD)

### 2.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT / FRONTEND                            │
│              (curl / Postman / React UI / test_apis.py)             │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP REST (port 8000)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (Python)                         │
│  ┌───────────┐  ┌──────────────┐  ┌───────────┐  ┌──────────────┐  │
│  │ Job Mgmt  │  │ Storage/DHFS │  │ Catalog   │  │ Notebooks    │  │
│  │ /jobs/*   │  │ /dhfs/*      │  │ /catalog/*│  │ /notebooks/* │  │
│  └─────┬─────┘  └──────┬───────┘  └─────┬─────┘  └──────┬───────┘  │
│        │               │                │                │          │
│  ┌─────┴─────────────────────────────────┴────────────────┘         │
│  │                   Core Layer                                     │
│  │  config.py │ db.py (Connection Pool) │ scheduler.py              │
│  └──────────────────────────────────────────────────────────────────│
└──────┬──────────────┬───────────────────┬───────────────────────────┘
       │              │                   │
       │ Docker SDK   │ boto3 (S3)        │ psycopg2
       │ (docker exec)│                   │
       ▼              ▼                   ▼
┌──────────┐   ┌──────────┐       ┌──────────────┐
│  Spark   │   │  MinIO   │       │  PostgreSQL  │
│  Cluster │   │  (S3)    │       │   Database   │
│          │   │          │       │              │
│ ┌──────┐ │   │ Port 9000│       │  Port 5432   │
│ │Master│ │   └──────────┘       └──────────────┘
│ │:7077 │ │
│ │:8080 │ │         ┌───────────────────────────┐
│ └──┬───┘ │         │     Shared Volume          │
│    │     │         │     /workspace/             │
│ ┌──┴───┐ │         │  ├── jobs/    (PySpark .py) │
│ │Worker│ │◄────────│  ├── logs/    (stdout/err)  │
│ │:8081 │ │         │  ├── notebooks/ (.ipynb)    │
│ └──────┘ │         │  ├── data/    (MinIO data)  │
└──────────┘         │  └── iceberg/ (table files) │
                     └───────────────────────────┘
```

### 2.2 Component Responsibilities

| Component        | Role                                                                 |
|------------------|----------------------------------------------------------------------|
| **FastAPI**      | Central REST API gateway — all client interactions go through here   |
| **Spark Master** | Cluster coordinator — accepts and schedules Spark jobs               |
| **Spark Worker** | Executes Spark tasks distributed by the master                       |
| **MinIO**        | S3-compatible object storage — stores raw data files                 |
| **PostgreSQL**   | Relational metadata store — job registry, user databases, catalogs   |
| **Iceberg**      | Open table format — ACID transactions on top of file-based storage   |
| **Shared Volume**| `/workspace/` mounted across all containers for file sharing         |

### 2.3 Communication Patterns

```
FastAPI  ──(Docker SDK)──►  Spark Master   (spark-submit via docker exec)
FastAPI  ──(boto3/S3)────►  MinIO          (object storage operations)
FastAPI  ──(psycopg2)────►  PostgreSQL     (metadata, job registry, catalog)
FastAPI  ──(HTTP GET)────►  Spark Web UI   (cluster status JSON at :8080)
FastAPI  ──(filesystem)──►  /workspace/    (read/write jobs, logs, notebooks)
```

---

## 3. Low-Level Design (LLD)

### 3.1 Project Structure

```
dataharbour/
├── docker-compose.yml          # Orchestrates all 5 services
├── backend/
│   ├── Dockerfile              # Python 3.9-slim + uvicorn
│   ├── main.py                 # FastAPI app init, CORS, scheduler, lifecycle
│   ├── requirements.txt        # fastapi, pyspark, boto3, psycopg2, docker, etc.
│   ├── api/
│   │   └── routes.py           # 1362 lines — ALL API endpoints (30+ routes)
│   └── core/
│       ├── config.py           # Environment variable config class
│       ├── db.py               # PostgreSQL ThreadedConnectionPool
│       ├── scheduler.py        # APScheduler wrapper (for future cron jobs)
│       └── spark_client.py     # PySpark session builder (utility)
├── spark/
│   ├── Dockerfile              # apache/spark:3.5.0 + Iceberg + Hadoop-AWS + JDBC jars
│   └── spark-defaults.conf     # S3A (MinIO) + Iceberg catalog config
├── workspace/                  # Shared Docker volume
│   ├── data/                   # MinIO storage
│   ├── jobs/                   # PySpark scripts (.py files)
│   ├── notebooks/              # Jupyter .ipynb files
│   └── iceberg/                # Iceberg warehouse (Hadoop catalog)
└── test_apis.py                # 811 lines — comprehensive API test suite
```

### 3.2 FastAPI Application Lifecycle (`main.py`)

```python
# Startup
1. Create FastAPI app with title "DataHarbour API"
2. Add CORS middleware (allow all origins)
3. Include API router (all routes from api/routes.py)
4. Initialize PostgreSQL connection pool (ThreadedConnectionPool, 1-10 conns)
5. Start APScheduler (AsyncIOScheduler)

# Shutdown
1. Shutdown APScheduler
2. Close PostgreSQL connection pool
```

### 3.3 Database Connection Pool (`db.py`)

```
┌──────────────────────────────────────────┐
│     ThreadedConnectionPool (psycopg2)     │
│  ┌──────┐ ┌──────┐ ┌──────┐    ┌──────┐ │
│  │Conn 1│ │Conn 2│ │Conn 3│ ...│Conn10│ │    minconn=1, maxconn=10
│  └──────┘ └──────┘ └──────┘    └──────┘ │
│                                          │
│  get_db_connection(db_name=None)         │    ← If default DB → pool
│  get_db_connection(db_name="custom")     │    ← If custom DB → new connection
│  release_db_connection(conn, db_name)    │    ← Return to pool or close
│  close_db_pool()                         │    ← Cleanup on shutdown
└──────────────────────────────────────────┘
```

### 3.4 Job Submission Deep Dive

This is the most complex flow in the system:

```
Client
  │
  │ POST /jobs/submit  (multipart file upload: .py)
  ▼
FastAPI (/jobs/submit endpoint)
  │
  ├─ 1. Validate file is .py
  ├─ 2. Generate UUID job_id
  ├─ 3. Save file to /workspace/jobs/{job_id}_{filename}
  │
  ├─ 4. _spark_submit(job_id, file_path, app_name)
  │     │
  │     ├─ Connect to Docker daemon via mounted /var/run/docker.sock
  │     ├─ Find container named "spark-master"
  │     ├─ docker exec spark-master /opt/spark/bin/spark-submit \
  │     │     --master spark://spark-master:7077 \
  │     │     --name DataHarbour-{job_id[:8]} \
  │     │     --deploy-mode client \
  │     │     /workspace/jobs/{job_id}_{filename}
  │     │
  │     ├─ Capture stdout → /workspace/logs/{job_id}.stdout
  │     ├─ Capture stderr → /workspace/logs/{job_id}.stderr
  │     └─ Track in _SPARK_PROCESSES dict (in-memory + thread lock)
  │
  ├─ 5. _upsert_job() → INSERT/UPDATE into PostgreSQL "jobs" table
  │     │
  │     │  jobs table schema:
  │     │  ┌──────────────────┬───────────┐
  │     │  │ Column           │ Type      │
  │     │  ├──────────────────┼───────────┤
  │     │  │ job_id (PK)      │ VARCHAR   │
  │     │  │ filename         │ VARCHAR   │
  │     │  │ file_path        │ VARCHAR   │
  │     │  │ submitted_at     │ VARCHAR   │
  │     │  │ status           │ VARCHAR   │
  │     │  │ spark_submission_id│ VARCHAR  │
  │     │  │ worker_host_port │ VARCHAR   │
  │     │  └──────────────────┴───────────┘
  │
  └─ 6. Return JSON: { job_id, spark_submission_id, filename, status }
```

### 3.5 Job State Machine

```
                  ┌──────────┐
  POST /submit ──►│SUBMITTED │
                  └────┬─────┘
                       │ Spark picks up
                       ▼
                  ┌──────────┐
                  │ RUNNING  │
                  └────┬─────┘
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
         ┌────────┐ ┌──────┐ ┌──────┐
         │FINISHED│ │FAILED│ │ERROR │
         └────────┘ └──────┘ └──────┘
                       ▲
                       │ DELETE /jobs/{id}
                  ┌────┴───┐
                  │ KILLED │
                  └────────┘

Terminal states: FINISHED, FAILED, KILLED, ERROR
(Never re-query Spark for jobs in terminal states)
```

### 3.6 Spark Docker Image Build

```dockerfile
FROM apache/spark:3.5.0

# Downloaded JARs into /opt/spark/jars/:
# 1. iceberg-spark-runtime-3.5_2.12-1.4.3.jar    → Iceberg table format support
# 2. hadoop-aws-3.3.4.jar                         → S3A filesystem (MinIO access)
# 3. aws-java-sdk-bundle-1.12.540.jar             → AWS SDK for S3 operations
# 4. postgresql-42.6.0.jar                        → JDBC driver for PostgreSQL
```

### 3.7 Spark Configuration (`spark-defaults.conf`)

| Config Key | Value | Purpose |
|------------|-------|---------|
| `fs.s3a.endpoint` | `http://minio:9000` | Point Spark to MinIO instead of AWS |
| `fs.s3a.path.style.access` | `true` | Required for MinIO (not virtual-hosted) |
| `fs.s3a.impl` | `S3AFileSystem` | Hadoop S3A filesystem implementation |
| `sql.catalog.spark_catalog` | `SparkCatalog` (Iceberg) | Use Iceberg as default catalog |
| `sql.catalog.spark_catalog.type` | `hadoop` | Hadoop-based Iceberg catalog |
| `sql.catalog.spark_catalog.warehouse` | `/workspace/iceberg` | Local Iceberg warehouse path |

### 3.8 Docker Compose Service Map

```yaml
services:
  minio:          # S3-compatible object storage
    port: 9000
    volume: ./workspace/data → /data
    
  postgres:       # Relational database
    port: 5432
    volume: postgres_data (named volume, persistent)
    
  spark-master:   # Spark cluster coordinator
    ports: 7077 (Spark), 8080 (Web UI), 6066 (REST)
    volume: ./workspace → /workspace
    
  spark-worker:   # Spark executor
    depends_on: spark-master
    volume: ./workspace → /workspace
  
  fastapi:        # REST API backend
    port: 8000
    volumes:
      - ./workspace → /workspace       # Shared data
      - /var/run/docker.sock            # Docker-in-Docker for spark-submit
```

**Key Design Decision:** The FastAPI container mounts the Docker socket (`/var/run/docker.sock`) so it can execute `docker exec` commands inside the Spark master container to run `spark-submit`. This avoids needing Java/Spark installed in the FastAPI image.

---

## 4. Technology Stack & Tools

### 4.1 Complete Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **API Framework** | FastAPI | Latest | Async REST API with auto-generated OpenAPI docs |
| **ASGI Server** | Uvicorn | Latest | High-performance Python web server |
| **Processing Engine** | Apache Spark | 3.5.0 | Distributed data processing (PySpark) |
| **Object Storage** | MinIO | Latest | S3-compatible storage for data lake |
| **Relational DB** | PostgreSQL | 13 | Metadata store, job registry, user databases |
| **Table Format** | Apache Iceberg | 1.4.3 | ACID transactions, schema evolution, time travel |
| **Container Orchestration** | Docker Compose | v2 | Multi-container orchestration |
| **Scheduler** | APScheduler | Latest | Async job scheduling (extensible) |
| **S3 Client** | boto3 | Latest | AWS SDK for MinIO operations |
| **DB Client** | psycopg2 | Latest | PostgreSQL adapter with connection pooling |
| **Docker Client** | docker-py | Latest | Docker SDK for spark-submit via container exec |
| **Validation** | Pydantic | v1/v2 | Request/response model validation |

### 4.2 Why These Tools?

| Tool | Why Chosen | Alternative Considered |
|------|-----------|----------------------|
| **FastAPI** | Auto-docs (Swagger), async support, Pydantic validation, fastest Python framework | Flask, Django REST |
| **Spark** | Industry-standard for big data processing, supports SQL + Python + Iceberg | Flink, Dask |
| **MinIO** | Drop-in S3 replacement, runs locally, same API as AWS S3 | LocalStack, actual S3 |
| **PostgreSQL** | Robust, supports JSONB, handles metadata + catalog duties | MySQL, SQLite |
| **Iceberg** | Open table format, ACID, schema evolution, partition evolution, time travel | Delta Lake, Hudi |
| **Docker Compose** | Simple multi-container setup, reproducible, no cloud dependency | Kubernetes, Podman |

---

## 5. How It Works — End-to-End Flow

### 5.1 Complete Data Pipeline Example

```
Step 1: Upload raw data to MinIO
  POST /dhfs/upload/raw-data  (file: sales_2024.csv)
  → File stored in MinIO bucket "raw-data"

Step 2: Create a PySpark job that reads from MinIO, transforms, writes Iceberg
  # sample_job.py
  spark = SparkSession.builder.appName("ETL").getOrCreate()
  df = spark.read.csv("s3a://raw-data/sales_2024.csv", header=True)
  df = df.filter(df.amount > 100)
  df.writeTo("spark_catalog.dataharbour.clean_sales").createOrReplace()

Step 3: Submit the job
  POST /jobs/submit  (file: sample_job.py)
  → Returns { job_id: "abc-123", status: "SUBMITTED" }

Step 4: Monitor the job
  GET /jobs/abc-123/status  → { status: "RUNNING" }
  GET /jobs/abc-123/logs    → { logs: "Processing 1M rows..." }

Step 5: Browse results in Iceberg catalog
  GET /catalog/iceberg/tables
  → { tables: [{ name: "clean_sales", hasMetadata: true }] }

Step 6: Check dashboard
  GET /stats/summary
  → { jobs: 1, jobsRunning: 0, buckets: 1, databases: 0 }
```

### 5.2 Notebook Execution Flow

```
1. POST /notebooks?name=analysis.ipynb     → Creates empty notebook with PySpark starter
2. PUT  /notebooks/analysis.ipynb          → Save notebook cells (code + markdown)
3. POST /notebooks/analysis.ipynb/execute  → Extracts code cells → .py → spark-submit
4. GET  /jobs/{job_id}/status              → Monitor execution
5. GET  /jobs/{job_id}/logs                → View output
```

---

## 6. API Endpoints Reference

### 30+ REST Endpoints organized by domain:

| Method | Endpoint | Description |
|--------|----------|-------------|
| **Authentication** | | |
| POST | `/auth/login` | Login with username/password |
| POST | `/auth/logout` | Logout |
| **Jobs (Spark)** | | |
| POST | `/jobs/submit` | Upload & submit PySpark script |
| GET | `/jobs` | List all jobs (with optional status filter) |
| GET | `/jobs/running` | List active jobs |
| GET | `/jobs/pending` | List queued jobs |
| GET | `/jobs/completed` | List finished/failed/killed jobs |
| GET | `/jobs/{job_id}/status` | Get single job status (live Spark query) |
| GET | `/jobs/{job_id}/logs` | Get job stdout/stderr logs |
| DELETE | `/jobs/{job_id}` | Kill a running job |
| **Storage (MinIO/DHFS)** | | |
| GET | `/dhfs/buckets` | List all buckets |
| POST | `/dhfs/buckets/{name}` | Create bucket |
| DELETE | `/dhfs/buckets/{name}` | Delete bucket |
| GET | `/dhfs/files/{bucket}` | List files in bucket |
| POST | `/dhfs/upload/{bucket}` | Upload file to bucket |
| DELETE | `/dhfs/files/{bucket}/{key}` | Delete file |
| GET | `/dhfs/download/{bucket}/{key}` | Get pre-signed download URL |
| **Catalog (PostgreSQL)** | | |
| GET | `/catalog/databases` | List databases with sizes |
| POST | `/catalog/databases/{name}` | Create database |
| DELETE | `/catalog/databases/{name}` | Drop database (terminates active conns first) |
| GET | `/catalog/databases/{db}/tables` | List tables in a database |
| POST | `/catalog/databases/{db}/tables/{name}` | Create JSONB table |
| DELETE | `/catalog/databases/{db}/tables/{name}` | Drop table |
| **Catalog (Iceberg)** | | |
| GET | `/catalog/iceberg/tables` | List Iceberg tables |
| GET | `/catalog/iceberg/tables/{name}` | Get table metadata JSON |
| **Notebooks** | | |
| GET | `/notebooks` | List all notebooks |
| POST | `/notebooks` | Create new notebook |
| GET | `/notebooks/{name}` | Get notebook content |
| PUT | `/notebooks/{name}` | Save/update notebook |
| DELETE | `/notebooks/{name}` | Delete notebook |
| POST | `/notebooks/{name}/execute` | Execute notebook as Spark job |
| **Cluster Monitoring** | | |
| GET | `/cluster/status` | Spark cluster health (cores, memory, apps) |
| GET | `/cluster/workers` | List registered workers |
| GET | `/cluster/applications` | Active and completed Spark apps |
| **Dashboard** | | |
| GET | `/stats/summary` | Aggregated platform metrics |
| GET | `/activities/recent` | Last 10 activities (jobs + notebooks) |

---

## 7. Architecture Patterns Used

### 7.1 Patterns You Can Mention in Interview

| Pattern | Where Used | Explanation |
|---------|-----------|-------------|
| **Microservices** | Docker Compose services | Each service (Spark, MinIO, Postgres, API) is independently deployable |
| **API Gateway** | FastAPI backend | Single entry point for all client requests, routes to internal services |
| **Connection Pooling** | `db.py` ThreadedConnectionPool | Reuse DB connections instead of creating new ones per request |
| **Registry Pattern** | PostgreSQL `jobs` table | Centralized job metadata with upsert semantics |
| **Shared Volume** | `/workspace/` mount | File-based communication between containers |
| **Docker-in-Docker** | Docker socket mount | FastAPI controls Spark container via Docker SDK |
| **Sidecar-like** | spark-submit via exec | API container delegates execution to Spark container |
| **State Machine** | Job status lifecycle | SUBMITTED → RUNNING → FINISHED/FAILED/KILLED/ERROR |
| **Pre-signed URLs** | MinIO download | Secure time-limited file access without exposing credentials |
| **Health Check Pattern** | `/cluster/status` | Graceful degradation — returns "unavailable" instead of crashing |
| **CORS Middleware** | FastAPI CORS | Cross-origin support for frontend integration |
| **Thread-safe Process Tracking** | `_SPARK_PROCESSES` + `_PROCESSES_LOCK` | Threading lock protects shared state for concurrent job management |

### 7.2 Data Flow Patterns

```
Write Path:  Client → FastAPI → MinIO/Postgres → Shared Volume → Spark
Read Path:   Client → FastAPI → Spark Web UI / Logs / PostgreSQL → Client
```

---

## 8. Advantages

### Technical Advantages

| # | Advantage | Detail |
|---|----------|--------|
| 1 | **Zero Cloud Cost** | Runs entirely on localhost — no AWS/GCP/Azure billing |
| 2 | **One Command Setup** | `docker-compose up -d` launches entire platform |
| 3 | **S3-Compatible** | Code using MinIO works identically with real AWS S3 |
| 4 | **Interactive API Docs** | FastAPI auto-generates Swagger UI at `/docs` |
| 5 | **Iceberg Support** | ACID transactions, schema evolution, time travel on data lake |
| 6 | **Connection Pooling** | Efficient DB access, handles concurrent requests |
| 7 | **Comprehensive Test Suite** | 811-line test script with auto-discovery, retry, color output |
| 8 | **Idempotent Operations** | Upsert logic for jobs, IF NOT EXISTS for tables |
| 9 | **Graceful Degradation** | Cluster endpoints return "unavailable" instead of 500 errors |
| 10 | **Separation of Concerns** | API, compute, storage, metadata all in separate containers |
| 11 | **Reproducible** | Entire env defined in code (Docker), version-controlled |
| 12 | **Pre-signed URLs** | Secure file downloads with expiring tokens |

### Business/Team Advantages

| # | Advantage | Detail |
|---|----------|--------|
| 1 | **Onboarding** | New team members can spin up a full lakehouse in minutes |
| 2 | **CI/CD Friendly** | Can run test suite in pipelines to validate API changes |
| 3 | **Cloud Migration Ready** | Swap MinIO → S3, Postgres RDS, Spark → EMR with config changes |
| 4 | **No Vendor Lock-in** | All components are open-source |

---

## 9. Disadvantages & Limitations

### Current Limitations

| # | Limitation | Impact | Potential Fix |
|---|-----------|--------|---------------|
| 1 | **No Authentication/Authorization** | Login is a stub (returns demo token), no JWT, no RBAC | Implement OAuth2/JWT with FastAPI Security |
| 2 | **Single Spark Worker** | Limited parallelism in default config | Scale with `docker-compose up --scale spark-worker=3` |
| 3 | **No Frontend UI** | API-only — requires curl/Postman | Build React/Next.js dashboard |
| 4 | **In-Memory Process Tracking** | `_SPARK_PROCESSES` dict lost on restart | Already mitigated by PostgreSQL registry, but live status lost |
| 5 | **Synchronous spark-submit** | `exec_run()` blocks until job finishes for long jobs | Use `exec_run(detach=True)` + polling |
| 6 | **No Data Versioning / Lineage** | Can't track which job produced which data | Integrate Apache Atlas or OpenLineage |
| 7 | **No Rate Limiting** | API vulnerable to abuse | Add FastAPI middleware / Redis-based rate limiter |
| 8 | **No Secrets Management** | Passwords in .env / environment variables | Use Docker Secrets or HashiCorp Vault |
| 9 | **CORS Allow All** | `allow_origins=["*"]` is insecure for production | Restrict to specific frontend domains |
| 10 | **No TLS/HTTPS** | Plain HTTP communication between services | Add Nginx reverse proxy with SSL |
| 11 | **Single Point of Failure** | If FastAPI goes down, no jobs can be submitted | Add load balancer, health checks, auto-restart |
| 12 | **Monolithic Route File** | 1362-line `routes.py` — hard to maintain | Split into domain modules (jobs.py, storage.py, catalog.py) |
| 13 | **No Input Sanitization** | SQL injection risk in some queries (mitigated by psycopg2 parameterization, but dynamic SQL constructs exist) | Use ORM (SQLAlchemy) for safer queries |
| 14 | **Hardcoded Worker Host** | `workerHostPort: "spark-worker-1:8081"` is hardcoded | Dynamically discover from Spark master |

---

## 10. What Can Be Enhanced

### Priority Enhancements (Quick Wins)

| # | Enhancement | Effort | Impact |
|---|------------|--------|--------|
| 1 | **JWT Authentication** | Medium | Secure all endpoints with token-based auth |
| 2 | **Async spark-submit** | Low | Use `detach=True` in Docker exec for non-blocking job submission |
| 3 | **Split routes.py** | Low | Modularize into `routes/jobs.py`, `routes/storage.py`, etc. |
| 4 | **WebSocket for live logs** | Medium | Stream logs in real-time instead of polling |
| 5 | **Pagination** | Low | Add limit/offset to all list endpoints |
| 6 | **Docker health checks** | Low | Add `healthcheck` to docker-compose for auto-restart |
| 7 | **Environment-specific configs** | Low | Dev/staging/prod config profiles |

### Major Enhancements (High Impact)

| # | Enhancement | Effort | Impact |
|---|------------|--------|--------|
| 8 | **React/Next.js Dashboard** | High | Visual job management, file browser, cluster monitoring |
| 9 | **Apache Airflow Integration** | High | DAG-based pipeline orchestration |
| 10 | **Data Quality Checks** | Medium | Integrate Great Expectations or Deequ |
| 11 | **Schema Registry** | Medium | Avro/Protobuf schema management |
| 12 | **Multi-tenant Support** | High | Namespace isolation per user/team |
| 13 | **Kubernetes Deployment** | High | Helm chart for production-grade scaling |
| 14 | **Streaming Support** | High | Add Spark Structured Streaming endpoints |
| 15 | **Data Lineage** | High | Track data flow across jobs with OpenLineage |
| 16 | **Caching Layer (Redis)** | Medium | Cache cluster status, job registry for faster reads |
| 17 | **SQLAlchemy ORM** | Medium | Replace raw SQL with an ORM for safety and productivity |
| 18 | **Logging Framework** | Low | Replace `print()` with structured logging (Python `logging` module) |
| 19 | **CI/CD Pipeline** | Medium | GitHub Actions — build, test, deploy on push |
| 20 | **Monitoring Stack** | Medium | Prometheus + Grafana for cluster & API metrics |

---

## 11. Interview Q&A Cheat Sheet

### Q1: "Tell me about a project you built."

> "I built **DataHarbour**, a containerized data lakehouse platform. It's a REST-API driven platform that lets you manage the full data engineering lifecycle — from uploading raw data to MinIO (S3-compatible storage), submitting PySpark jobs, browsing Iceberg table catalogs, managing PostgreSQL databases, and monitoring a Spark cluster — all through 30+ REST endpoints. Everything runs via Docker Compose with 5 services: FastAPI, Spark Master, Spark Worker, MinIO, and PostgreSQL."

### Q2: "How does job submission work?"

> "When a user uploads a .py file to `POST /jobs/submit`, the API saves it to a shared Docker volume, then uses the Docker SDK to execute `spark-submit` inside the Spark master container via `docker exec`. The job's stdout/stderr is captured to log files, and the job metadata is persisted in a PostgreSQL `jobs` table with a UUID job_id. The client can then poll `/jobs/{id}/status` and `/jobs/{id}/logs` to track progress. Jobs follow a state machine: SUBMITTED → RUNNING → FINISHED/FAILED/KILLED."

### Q3: "Why did you use Docker socket mounting?"

> "The alternative was installing Java and Spark inside the FastAPI container, which would bloat the image from ~150MB to ~1.5GB. Instead, I mount `/var/run/docker.sock` so the Python Docker SDK can execute `spark-submit` inside the already-running Spark master container. This keeps the API image lightweight and avoids duplicating the Spark installation."

### Q4: "How does MinIO fit in?"

> "MinIO acts as our data lake storage layer. It's S3-compatible, so the same `boto3` code and Spark S3A configuration that works with MinIO will work with real AWS S3 in production. The API exposes CRUD endpoints for buckets and files. Spark jobs can read/write data using `s3a://` paths, configured through `spark-defaults.conf` to point at MinIO."

### Q5: "Why Iceberg?"

> "Apache Iceberg gives us lakehouse capabilities on top of file storage — ACID transactions, schema evolution, partition evolution, and time travel. Our Spark image includes the Iceberg runtime JAR, and `spark-defaults.conf` configures Iceberg as the default Spark catalog with a Hadoop-based warehouse at `/workspace/iceberg`. The API can browse table metadata via the `/catalog/iceberg/tables` endpoint."

### Q6: "How do you ensure data consistency?"

> "Three mechanisms: (1) PostgreSQL connection pooling with thread-safe `ThreadedConnectionPool` and proper upsert logic for the jobs table. (2) Thread-safe process tracking using `threading.Lock` for the in-memory `_SPARK_PROCESSES` dict. (3) Terminal state detection — once a job reaches FINISHED/FAILED/KILLED/ERROR, we never re-query Spark, preventing stale state overwrites."

### Q7: "How would you take this to production?"

> "First: proper authentication with JWT/OAuth2. Second: replace MinIO with AWS S3, PostgreSQL with RDS, and deploy Spark on EMR or Kubernetes. Third: add an Nginx reverse proxy for TLS. Fourth: switch from Docker socket mounting to a proper Spark REST API (like Apache Livy). Fifth: add monitoring with Prometheus/Grafana. Sixth: CI/CD with GitHub Actions for automated testing and deployment."

### Q8: "What was the hardest challenge?"

> "Getting Spark job submission to work reliably from the FastAPI container. Initially I tried using Spark's built-in REST submission API (port 6066), but it doesn't support Python jobs in client mode well. I then pivoted to the Docker SDK approach — executing `spark-submit` inside the Spark master container via `docker exec`. This required mounting the Docker socket, sharing the workspace volume, and carefully handling stdout/stderr capture and process lifecycle management across container boundaries."

### Q9: "How did you test it?"

> "I built a comprehensive 811-line test suite (`test_apis.py`) that auto-discovers routes from the `/openapi.json` spec, tests all 30+ endpoints with assertions on response keys and status codes, has retry logic for flaky connections, differentiates between code bugs (FAIL) and infrastructure issues (WARN for HTTP 503), and generates colored terminal output with a detailed summary."

### Q10: "What design patterns did you use?"

> "API Gateway pattern (FastAPI as single entry point), Connection Pooling (psycopg2 ThreadedConnectionPool), Registry pattern (PostgreSQL jobs table), State Machine (job lifecycle), Pre-signed URL pattern (MinIO downloads), Graceful Degradation (cluster status returns 'unavailable' instead of erroring), Sidecar pattern (API delegates to Spark container via Docker exec), and Shared Volume pattern for inter-container file communication."

---

## Appendix: Key Code Snippets for Discussion

### A. Thread-safe Job Tracking

```python
# In-memory process tracking with thread lock
_SPARK_PROCESSES: Dict[str, dict] = {}
_PROCESSES_LOCK = threading.Lock()

with _PROCESSES_LOCK:
    _SPARK_PROCESSES[job_id] = {
        "container_name": container_name,
        "status": "SUBMITTED" if exit_code == 0 else "ERROR",
        "stdout_file": stdout_file,
        "stderr_file": stderr_file,
        "exit_code": exit_code,
    }
```

### B. Docker Exec Spark Submit

```python
client = docker.from_env()
container = client.containers.get("spark-master")
exec_result = container.exec_run(
    cmd=["/opt/spark/bin/spark-submit",
         "--master", "spark://spark-master:7077",
         "--deploy-mode", "client",
         file_path],
    stdout=True, stderr=True, demux=False,
)
```

### C. PostgreSQL Connection Pool

```python
_pg_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=1, maxconn=10,
    host=Config.postgres_host,
    port=Config.postgres_port,
    user=Config.postgres_user,
    password=Config.postgres_password,
    database=Config.postgres_db
)
```

### D. Iceberg Spark Configuration

```properties
spark.sql.catalog.spark_catalog = org.apache.iceberg.spark.SparkCatalog
spark.sql.catalog.spark_catalog.type = hadoop
spark.sql.catalog.spark_catalog.warehouse = /workspace/iceberg
```

---

> **Last Updated:** March 2026 | **Author:** DataHarbour Team
