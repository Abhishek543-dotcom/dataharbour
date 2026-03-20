"""
DataHarbour API — Application Entry Point
==========================================
Initialises FastAPI, CORS middleware, structured logging, PostgreSQL
connection pool, APScheduler, and includes all domain routers.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import Config
from core.db import close_db_pool, init_db_pool
from core.scheduler import shutdown_scheduler, start_scheduler
from api.routes import all_routers

# ── Structured Logging ───────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if Config.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("dataharbour")


# ── Application Lifespan ─────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook (FastAPI ≥ 0.95)."""
    # ── Startup ──
    logger.info("DataHarbour %s starting …", Config.app_version)
    init_db_pool()
    start_scheduler()
    logger.info("DataHarbour ready — listening on port 8000")
    yield
    # ── Shutdown ──
    logger.info("DataHarbour shutting down …")
    shutdown_scheduler()
    close_db_pool()
    logger.info("DataHarbour stopped")


# ── FastAPI Application ──────────────────────────────────────

app = FastAPI(
    title="DataHarbour API",
    description=(
        "A lightweight, containerised Data Lakehouse platform. "
        "Manage Spark jobs, MinIO storage, PostgreSQL catalogs, "
        "Apache Iceberg tables, notebooks, and cluster monitoring — "
        "all through a single REST API."
    ),
    version=Config.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS Middleware (allow all for development) ──────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include all domain routers ───────────────────────────────
for router in all_routers:
    app.include_router(router)


# ── Health Check Endpoint ────────────────────────────────────

@app.get("/health", tags=["System"])
def health_check():
    """Quick liveness probe for container orchestrators."""
    return {"status": "healthy", "version": Config.app_version}


@app.get("/", tags=["System"])
def root():
    """Landing page — confirms the API is running."""
    return {
        "name": Config.app_name,
        "version": Config.app_version,
        "docs": "/docs",
        "health": "/health",
    }
