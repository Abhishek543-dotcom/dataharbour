"""
Airflow API endpoints
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

from app.services.airflow_service import get_airflow_service
from app.db.session import get_db
from app.api.dependencies import get_optional_current_user
from app.models.schemas import User

logger = logging.getLogger(__name__)
router = APIRouter()


class TriggerDAGRequest(BaseModel):
    """Request model for triggering a DAG"""
    conf: Optional[Dict[str, Any]] = None


@router.get("/health")
async def get_health(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Check Airflow health status"""
    try:
        service = get_airflow_service()
        health = await service.get_health()
        return {
            'success': True,
            **health
        }
    except Exception as e:
        logger.error(f"Error checking Airflow health: {str(e)}")
        return {
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }


@router.get("/statistics")
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Get overall Airflow statistics"""
    try:
        service = get_airflow_service()
        stats = await service.get_statistics()
        return {
            'success': True,
            **stats
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dags")
async def list_dags(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    only_active: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """List all DAGs"""
    try:
        service = get_airflow_service()
        result = await service.list_dags(limit, offset, only_active)
        return {
            'success': True,
            **result
        }
    except Exception as e:
        logger.error(f"Error listing DAGs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dags/{dag_id}")
async def get_dag(
    dag_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Get detailed information about a specific DAG"""
    try:
        service = get_airflow_service()
        dag = await service.get_dag(dag_id)
        return {
            'success': True,
            'dag': dag
        }
    except Exception as e:
        logger.error(f"Error getting DAG {dag_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dags/{dag_id}/runs")
async def get_dag_runs(
    dag_id: str,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    state: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Get DAG runs for a specific DAG"""
    try:
        service = get_airflow_service()
        result = await service.get_dag_runs(dag_id, limit, offset, state)
        return {
            'success': True,
            **result
        }
    except Exception as e:
        logger.error(f"Error getting DAG runs for {dag_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dags/{dag_id}/trigger")
async def trigger_dag(
    dag_id: str,
    request: TriggerDAGRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Trigger a new DAG run"""
    try:
        service = get_airflow_service()
        result = await service.trigger_dag(dag_id, request.conf)
        return {
            'success': True,
            'message': f'DAG {dag_id} triggered successfully',
            **result
        }
    except Exception as e:
        logger.error(f"Error triggering DAG {dag_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dags/{dag_id}/pause")
async def pause_dag(
    dag_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Pause a DAG"""
    try:
        service = get_airflow_service()
        result = await service.pause_dag(dag_id)
        return {
            'success': True,
            'message': f'DAG {dag_id} paused successfully',
            'dag': result
        }
    except Exception as e:
        logger.error(f"Error pausing DAG {dag_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dags/{dag_id}/unpause")
async def unpause_dag(
    dag_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Unpause a DAG"""
    try:
        service = get_airflow_service()
        result = await service.unpause_dag(dag_id)
        return {
            'success': True,
            'message': f'DAG {dag_id} unpaused successfully',
            'dag': result
        }
    except Exception as e:
        logger.error(f"Error unpausing DAG {dag_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dags/{dag_id}/runs/{dag_run_id}/tasks")
async def get_task_instances(
    dag_id: str,
    dag_run_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Get task instances for a specific DAG run"""
    try:
        service = get_airflow_service()
        tasks = await service.get_task_instances(dag_id, dag_run_id)
        return {
            'success': True,
            'task_instances': tasks,
            'count': len(tasks)
        }
    except Exception as e:
        logger.error(f"Error getting task instances: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dags/{dag_id}/runs/{dag_run_id}/tasks/{task_id}/logs")
async def get_task_logs(
    dag_id: str,
    dag_run_id: str,
    task_id: str,
    try_number: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Get logs for a specific task instance"""
    try:
        service = get_airflow_service()
        logs = await service.get_task_logs(dag_id, dag_run_id, task_id, try_number)
        return {
            'success': True,
            'logs': logs
        }
    except Exception as e:
        logger.error(f"Error getting task logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
