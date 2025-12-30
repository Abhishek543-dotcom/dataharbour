from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
import logging

from app.models.schemas import Cluster, ClusterCreate, APIResponse, User
from app.services.spark_service import spark_service
from app.db.session import get_db
from app.api.dependencies import get_optional_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[Cluster])
async def get_clusters(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get all Spark clusters"""
    try:
        user_id = str(current_user.id) if current_user else None
        clusters = await spark_service.get_clusters(db, user_id)
        return clusters
    except Exception as e:
        logger.error(f"Error getting clusters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cluster_id}", response_model=Cluster)
async def get_cluster(
    cluster_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get specific cluster details"""
    try:
        cluster = await spark_service.get_cluster(db, cluster_id)
        if not cluster:
            raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
        return cluster
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cluster {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Cluster)
async def create_cluster(
    cluster_data: ClusterCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Create a new Spark cluster"""
    try:
        user_id = str(current_user.id) if current_user else None
        cluster = await spark_service.create_cluster(db, cluster_data, user_id)
        return cluster
    except Exception as e:
        logger.error(f"Error creating cluster: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{cluster_id}", response_model=APIResponse)
async def delete_cluster(
    cluster_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Delete a Spark cluster"""
    try:
        user_id = str(current_user.id) if current_user else None
        success = await spark_service.delete_cluster(db, cluster_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

        return APIResponse(
            success=True,
            message=f"Cluster {cluster_id} deleted successfully"
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting cluster {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cluster_id}/metrics")
async def get_cluster_metrics(
    cluster_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get detailed metrics for a cluster"""
    try:
        metrics = await spark_service.get_cluster_metrics(db, cluster_id)
        return metrics
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting cluster metrics for {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
