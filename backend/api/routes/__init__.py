"""
DataHarbour API Routes — Domain-based Modular Structure
========================================================
Each domain has its own router module. This package re-exports all routers
for easy inclusion in the FastAPI app.
"""

from api.routes.auth import router as auth_router
from api.routes.jobs import router as jobs_router
from api.routes.storage import router as storage_router
from api.routes.catalog import router as catalog_router
from api.routes.notebooks import router as notebooks_router
from api.routes.cluster import router as cluster_router
from api.routes.dashboard import router as dashboard_router

all_routers = [
    auth_router,
    jobs_router,
    storage_router,
    catalog_router,
    notebooks_router,
    cluster_router,
    dashboard_router,
]
