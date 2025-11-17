"""
Storage API endpoints for MinIO
"""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Response
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

from ....services.storage_service import get_storage_service

logger = logging.getLogger(__name__)
router = APIRouter()


class CreateBucketRequest(BaseModel):
    """Request model for creating a bucket"""
    bucket_name: str


class CopyObjectRequest(BaseModel):
    """Request model for copying an object"""
    source_bucket: str
    source_object: str
    dest_bucket: str
    dest_object: str


@router.get("/buckets")
async def list_buckets() -> Dict[str, Any]:
    """List all buckets"""
    try:
        service = get_storage_service()
        buckets = await service.list_buckets()
        return {
            'success': True,
            'buckets': buckets,
            'count': len(buckets)
        }
    except Exception as e:
        logger.error(f"Error listing buckets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buckets")
async def create_bucket(request: CreateBucketRequest) -> Dict[str, Any]:
    """Create a new bucket"""
    try:
        service = get_storage_service()
        result = await service.create_bucket(request.bucket_name)
        return {
            'success': True,
            **result
        }
    except Exception as e:
        logger.error(f"Error creating bucket: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/buckets/{bucket_name}")
async def delete_bucket(bucket_name: str) -> Dict[str, Any]:
    """Delete a bucket"""
    try:
        service = get_storage_service()
        result = await service.delete_bucket(bucket_name)
        return {
            'success': True,
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting bucket: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buckets/{bucket_name}/stats")
async def get_bucket_stats(bucket_name: str) -> Dict[str, Any]:
    """Get statistics for a bucket"""
    try:
        service = get_storage_service()
        stats = await service.get_bucket_stats(bucket_name)
        return {
            'success': True,
            **stats
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting bucket stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buckets/{bucket_name}/objects")
async def list_objects(
    bucket_name: str,
    prefix: str = Query("", description="Object prefix to filter by"),
    recursive: bool = Query(False, description="List recursively")
) -> Dict[str, Any]:
    """List objects in a bucket"""
    try:
        service = get_storage_service()
        objects = await service.list_objects(bucket_name, prefix, recursive)
        return {
            'success': True,
            'bucket': bucket_name,
            'prefix': prefix,
            'objects': objects,
            'count': len(objects)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing objects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buckets/{bucket_name}/objects/{object_path:path}/info")
async def get_object_info(bucket_name: str, object_path: str) -> Dict[str, Any]:
    """Get detailed information about an object"""
    try:
        service = get_storage_service()
        info = await service.get_object_info(bucket_name, object_path)
        return {
            'success': True,
            'bucket': bucket_name,
            **info
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting object info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buckets/{bucket_name}/objects/{object_path:path}/url")
async def get_object_url(
    bucket_name: str,
    object_path: str,
    expiry: int = Query(3600, ge=60, le=604800, description="URL expiry in seconds")
) -> Dict[str, Any]:
    """Get a presigned URL for an object"""
    try:
        service = get_storage_service()
        url = await service.get_object_url(bucket_name, object_path, expiry)
        return {
            'success': True,
            'bucket': bucket_name,
            'object': object_path,
            'url': url,
            'expiry': expiry
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting object URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buckets/{bucket_name}/objects/{object_path:path}")
async def upload_object(
    bucket_name: str,
    object_path: str,
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    """Upload an object to a bucket"""
    try:
        service = get_storage_service()
        data = await file.read()
        result = await service.upload_object(
            bucket_name,
            object_path,
            data,
            file.content_type or "application/octet-stream"
        )
        return {
            'success': True,
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading object: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buckets/{bucket_name}/objects/{object_path:path}/download")
async def download_object(bucket_name: str, object_path: str) -> Response:
    """Download an object from a bucket"""
    try:
        service = get_storage_service()
        data = await service.download_object(bucket_name, object_path)

        # Get object info for content type
        info = await service.get_object_info(bucket_name, object_path)

        return Response(
            content=data,
            media_type=info.get('content_type', 'application/octet-stream'),
            headers={
                'Content-Disposition': f'attachment; filename="{object_path.split("/")[-1]}"'
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error downloading object: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/buckets/{bucket_name}/objects/{object_path:path}")
async def delete_object(bucket_name: str, object_path: str) -> Dict[str, Any]:
    """Delete an object from a bucket"""
    try:
        service = get_storage_service()
        result = await service.delete_object(bucket_name, object_path)
        return {
            'success': True,
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting object: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/objects/copy")
async def copy_object(request: CopyObjectRequest) -> Dict[str, Any]:
    """Copy an object from one location to another"""
    try:
        service = get_storage_service()
        result = await service.copy_object(
            request.source_bucket,
            request.source_object,
            request.dest_bucket,
            request.dest_object
        )
        return {
            'success': True,
            **result
        }
    except Exception as e:
        logger.error(f"Error copying object: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
