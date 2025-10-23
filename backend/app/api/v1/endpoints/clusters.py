from fastapi import APIRouter, HTTPException
from typing import List
import logging

from app.models.schemas import Cluster, ClusterCreate, APIResponse
from app.services.spark_service import spark_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[Cluster])
async def get_clusters():
    """Get all Spark clusters"""
    try:
        clusters = await spark_service.get_clusters()
        return clusters
    except Exception as e:
        logger.error(f"Error getting clusters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cluster_id}", response_model=Cluster)
async def get_cluster(cluster_id: str):
    """Get specific cluster details"""
    try:
        cluster = await spark_service.get_cluster(cluster_id)
        if not cluster:
            raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
        return cluster
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cluster {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Cluster)
async def create_cluster(cluster_data: ClusterCreate):
    """Create a new Spark cluster"""
    try:
        cluster = await spark_service.create_cluster(cluster_data)
        return cluster
    except Exception as e:
        logger.error(f"Error creating cluster: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{cluster_id}", response_model=APIResponse)
async def delete_cluster(cluster_id: str):
    """Delete a Spark cluster"""
    try:
        success = await spark_service.delete_cluster(cluster_id)
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
