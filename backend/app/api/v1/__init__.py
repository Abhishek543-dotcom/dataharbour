from fastapi import APIRouter

from app.api.v1.endpoints import auth, clusters, dashboard, database, jobs, monitoring

router = APIRouter()

# Authentication routes (no prefix, handled in auth.py)
router.include_router(auth.router)

# Other routes
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
router.include_router(clusters.router, prefix="/clusters", tags=["clusters"])
router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
router.include_router(database.router, prefix="/database", tags=["database"])
