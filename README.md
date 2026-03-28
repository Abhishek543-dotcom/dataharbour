# DataHarbour 🚢

> A lightweight, containerized **Data Lakehouse platform** with 30+ REST API endpoints.  
> Manage Apache Spark jobs, MinIO object storage, PostgreSQL catalogs, Apache Iceberg tables, notebooks, and cluster monitoring — **all through a single REST API**.

---

## ✨ Overview

DataHarbour is a **self-contained, Docker-based data engineering platform** that runs entirely on your laptop. Think of it as a mini **Databricks / AWS EMR** for local development.

| Capability | What You Can Do |
|---|---|
| **Spark Job Management** | Upload, submit, monitor, and kill PySpark jobs via REST API |
| **Object Storage (MinIO)** | S3-compatible file storage with bucket and file CRUD operations |
| **Relational Database (PostgreSQL)** | Database/table creation, metadata catalog |
| **Apache Iceberg** | Open table format for data lakehouse with metadata browsing |
| **Notebook Management** | Create, edit, execute Jupyter notebooks as Spark jobs |
| **Cluster Monitoring** | Real-time Spark cluster health, worker stats, application tracking |
| **Dashboard Stats** | Aggregated metrics for an operational overview |

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     CLIENT (curl / Postman / UI)                │
└───────────────────────────┬────────────────────────────────────┘
                            │ HTTP REST (port 8000)
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python)                      │
│  Auth │ Jobs │ Storage │ Catalog │ Notebooks │ Cluster │ Stats  │
└───┬───────────┬──────────────┬─────────────────────────────────┘
    │           │              │
    ▼           ▼              ▼
┌────────┐ ┌────────┐  ┌────────────┐
│ Spark  │ │ MinIO  │  │ PostgreSQL │
│ Master │ │  (S3)  │  │   (Meta)   │
│ :7077  │ │ :9000  │  │   :5432    │
│ Worker │ │        │  │            │
└────────┘ └────────┘  └────────────┘
```

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone <repo-url> && cd dataharbour

# 2. Start everything (one command!)
docker-compose up -d --build

# 3. Open the API docs
# → http://localhost:8000/docs

# 4. Run the test suite
python test_apis.py
```

**Ports:**
| Service | Port | URL |
|---------|------|-----|
| FastAPI (REST API) | 8000 | http://localhost:8000/docs |
| Spark Master UI | 8080 | http://localhost:8080 |
| MinIO API | 9000 | http://localhost:9000 |
| MinIO Console | 9001 | http://localhost:9001 |
| PostgreSQL | 5432 | `psql -h localhost -U postgres` |

---

## 📁 Project Structure

```
dataharbour/
├── backend/                  # FastAPI Backend
│   ├── main.py               # App entry point (lifespan, CORS, logging)
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile            # API container image
│   ├── api/
│   │   ├── helpers.py        # Shared: S3 client, DB pool, job registry, models
│   │   ├── routes.py         # Aggregator (includes all domain routers)
│   │   └── routes/           # Domain-based route modules
│   │       ├── auth.py       # POST /auth/login, /auth/logout
│   │       ├── jobs.py       # POST /jobs/submit, GET /jobs, DELETE /jobs/{id}
│   │       ├── storage.py    # GET/POST/DELETE /dhfs/buckets, /dhfs/files
│   │       ├── catalog.py    # Databases, Tables, Iceberg
│   │       ├── notebooks.py  # CRUD + execute notebooks
│   │       ├── cluster.py    # Spark cluster monitoring
│   │       └── dashboard.py  # Stats summary, recent activities
│   └── core/
│       ├── config.py         # Environment variable configuration
│       ├── db.py             # PostgreSQL ThreadedConnectionPool
│       ├── scheduler.py      # APScheduler wrapper
│       └── spark_client.py   # Docker-based spark-submit client
├── spark/                    # Spark Docker image
│   ├── Dockerfile            # Spark 3.5.0 + Iceberg + Hadoop-AWS + JDBC jars
│   └── spark-defaults.conf   # S3A → MinIO, Iceberg catalog config
├── workspace/                # Shared Docker volume
│   ├── data/                 # MinIO storage
│   ├── jobs/                 # PySpark scripts (.py files)
│   ├── logs/                 # Job stdout/stderr logs
│   ├── notebooks/            # Jupyter .ipynb files
│   └── iceberg/              # Iceberg warehouse
├── .env                      # Environment variables
├── docker-compose.yml        # Multi-container orchestration (5 services)
├── test_apis.py              # Comprehensive API test suite
└── INTERVIEW_GUIDE.md        # Complete interview preparation guide
```

---

## 📡 API Endpoints (30+)

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Landing page |
| GET | `/health` | Liveness probe |
| GET | `/docs` | Swagger UI |

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login (demo token) |
| POST | `/auth/logout` | Logout |

### Jobs (Spark)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/jobs/submit` | Upload & submit PySpark script |
| GET | `/jobs` | List all jobs (optional status filter) |
| GET | `/jobs/running` | List active jobs |
| GET | `/jobs/pending` | List queued jobs |
| GET | `/jobs/completed` | List terminal-state jobs |
| GET | `/jobs/{job_id}/status` | Get single job status (live) |
| GET | `/jobs/{job_id}/logs` | Get stdout/stderr logs |
| DELETE | `/jobs/{job_id}` | Kill a running job |

### Storage (MinIO/DHFS)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dhfs/buckets` | List all buckets |
| POST | `/dhfs/buckets/{name}` | Create bucket |
| DELETE | `/dhfs/buckets/{name}` | Delete bucket |
| GET | `/dhfs/files/{bucket}` | List files in bucket |
| POST | `/dhfs/upload/{bucket}` | Upload file |
| DELETE | `/dhfs/files/{bucket}/{key}` | Delete file |
| GET | `/dhfs/download/{bucket}/{key}` | Pre-signed download URL |

### Catalog (PostgreSQL)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/catalog/databases` | List databases with sizes |
| POST | `/catalog/databases/{name}` | Create database |
| DELETE | `/catalog/databases/{name}` | Drop database |
| GET | `/catalog/databases/{db}/tables` | List tables |
| POST | `/catalog/databases/{db}/tables/{name}` | Create JSONB table |
| DELETE | `/catalog/databases/{db}/tables/{name}` | Drop table |

### Catalog (Iceberg)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/catalog/iceberg/tables` | List Iceberg tables |
| GET | `/catalog/iceberg/tables/{name}` | Get table metadata |

### Notebooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notebooks` | List all notebooks |
| POST | `/notebooks` | Create new notebook |
| GET | `/notebooks/{name}` | Get notebook content |
| PUT | `/notebooks/{name}` | Save/update notebook |
| DELETE | `/notebooks/{name}` | Delete notebook |
| POST | `/notebooks/{name}/execute` | Execute as Spark job |

### Cluster Monitoring
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cluster/status` | Cluster health |
| GET | `/cluster/workers` | Registered workers |
| GET | `/cluster/applications` | Active & completed apps |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stats/summary` | Aggregated metrics |
| GET | `/activities/recent` | Last 10 activities |

---

## 🧪 Testing

```bash
# Run the full test suite
python test_apis.py

# Custom URL
python test_apis.py http://localhost:8000

# Generate JSON report
python test_apis.py --json report.json
```

---

## 🔧 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API Framework | FastAPI | REST API with auto-generated Swagger docs |
| Processing | Apache Spark 3.5.0 | Distributed data processing |
| Object Storage | MinIO | S3-compatible local storage |
| Database | PostgreSQL 13 | Metadata store, job registry |
| Table Format | Apache Iceberg 1.4.3 | ACID transactions, schema evolution |
| Orchestration | Docker Compose | Multi-container management |
| Scheduler | APScheduler | Background task scheduling |

---

## 📄 License

MIT
