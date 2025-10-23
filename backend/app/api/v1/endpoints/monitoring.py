from fastapi import APIRouter, HTTPException, Query
from typing import List
import logging

from app.models.schemas import SystemMetrics, ServiceHealth, ServiceLog
from app.services.monitoring_service import monitoring_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/metrics", response_model=SystemMetrics)
async def get_current_metrics():
    """Get current system metrics"""
    try:
        metrics = await monitoring_service.get_system_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/history", response_model=List[SystemMetrics])
async def get_metrics_history(hours: int = Query(default=24, ge=1, le=168)):
    """Get historical system metrics"""
    try:
        metrics = await monitoring_service.get_metrics_history(hours)
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services", response_model=List[ServiceHealth])
async def get_services_health():
    """Get health status of all services"""
    try:
        services = await monitoring_service.get_service_health()
        return services
    except Exception as e:
        logger.error(f"Error getting service health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/{service_name}/logs", response_model=List[ServiceLog])
async def get_service_logs(
    service_name: str,
    lines: int = Query(default=100, ge=1, le=1000)
):
    """Get logs from a specific service"""
    try:
        logs = await monitoring_service.get_service_logs(service_name, lines)
        return logs
    except Exception as e:
        logger.error(f"Error getting logs for service {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview")
async def get_monitoring_overview():
    """Get complete monitoring overview"""
    try:
        metrics = await monitoring_service.get_system_metrics()
        services = await monitoring_service.get_service_health()

        return {
            "metrics": metrics,
            "services": services,
            "timestamp": metrics.timestamp
        }
    except Exception as e:
        logger.error(f"Error getting monitoring overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))
