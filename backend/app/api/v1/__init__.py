from fastapi import APIRouter
from app.api.v1.endpoints import dashboard, notebooks, jobs, clusters, monitoring

router = APIRouter()

router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
router.include_router(notebooks.router, prefix="/notebooks", tags=["notebooks"])
router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
router.include_router(clusters.router, prefix="/clusters", tags=["clusters"])
router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
