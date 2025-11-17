"""
Storage service for MinIO operations
Provides bucket and object management
"""

from minio import Minio
from minio.error import S3Error
from typing import List, Dict, Any, Optional
import logging
from io import BytesIO
from datetime import timedelta
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class StorageService:
    """Service for managing MinIO storage operations"""

    def __init__(self):
        # Parse endpoint to remove http:// or https://
        endpoint = settings.MINIO_ENDPOINT.replace('http://', '').replace('https://', '')

        self.client = Minio(
            endpoint,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False  # Set to True if using HTTPS
        )
        self.default_bucket = settings.MINIO_BUCKET_NAME

    async def list_buckets(self) -> List[Dict[str, Any]]:
        """List all buckets"""
        try:
            buckets = self.client.list_buckets()
            return [
                {
                    'name': bucket.name,
                    'creation_date': bucket.creation_date.isoformat() if bucket.creation_date else None
                }
                for bucket in buckets
            ]
        except S3Error as e:
            logger.error(f"Error listing buckets: {str(e)}")
            raise

    async def create_bucket(self, bucket_name: str) -> Dict[str, Any]:
        """Create a new bucket"""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                return {
                    'message': f'Bucket {bucket_name} created successfully',
                    'bucket_name': bucket_name
                }
            else:
                return {
                    'message': f'Bucket {bucket_name} already exists',
                    'bucket_name': bucket_name
                }
        except S3Error as e:
            logger.error(f"Error creating bucket: {str(e)}")
            raise

    async def delete_bucket(self, bucket_name: str) -> Dict[str, Any]:
        """Delete a bucket"""
        try:
            if self.client.bucket_exists(bucket_name):
                self.client.remove_bucket(bucket_name)
                return {
                    'message': f'Bucket {bucket_name} deleted successfully'
                }
            else:
                raise ValueError(f'Bucket {bucket_name} does not exist')
        except S3Error as e:
            logger.error(f"Error deleting bucket: {str(e)}")
            raise

    async def list_objects(
        self,
        bucket_name: str,
        prefix: str = "",
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """List objects in a bucket"""
        try:
            if not self.client.bucket_exists(bucket_name):
                raise ValueError(f'Bucket {bucket_name} does not exist')

            objects = self.client.list_objects(
                bucket_name,
                prefix=prefix,
                recursive=recursive
            )

            object_list = []
            for obj in objects:
                # Determine if it's a directory or file
                is_dir = obj.object_name.endswith('/')

                object_info = {
                    'name': obj.object_name,
                    'size': obj.size if not is_dir else 0,
                    'last_modified': obj.last_modified.isoformat() if obj.last_modified else None,
                    'etag': obj.etag,
                    'content_type': obj.content_type,
                    'is_dir': is_dir
                }
                object_list.append(object_info)

            return object_list
        except S3Error as e:
            logger.error(f"Error listing objects: {str(e)}")
            raise

    async def get_object_info(
        self,
        bucket_name: str,
        object_name: str
    ) -> Dict[str, Any]:
        """Get detailed information about an object"""
        try:
            if not self.client.bucket_exists(bucket_name):
                raise ValueError(f'Bucket {bucket_name} does not exist')

            stat = self.client.stat_object(bucket_name, object_name)

            return {
                'name': object_name,
                'size': stat.size,
                'last_modified': stat.last_modified.isoformat() if stat.last_modified else None,
                'etag': stat.etag,
                'content_type': stat.content_type,
                'metadata': stat.metadata
            }
        except S3Error as e:
            logger.error(f"Error getting object info: {str(e)}")
            raise

    async def get_object_url(
        self,
        bucket_name: str,
        object_name: str,
        expiry: int = 3600
    ) -> str:
        """Get a presigned URL for an object"""
        try:
            if not self.client.bucket_exists(bucket_name):
                raise ValueError(f'Bucket {bucket_name} does not exist')

            url = self.client.presigned_get_object(
                bucket_name,
                object_name,
                expires=timedelta(seconds=expiry)
            )

            return url
        except S3Error as e:
            logger.error(f"Error getting object URL: {str(e)}")
            raise

    async def upload_object(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream"
    ) -> Dict[str, Any]:
        """Upload an object to a bucket"""
        try:
            if not self.client.bucket_exists(bucket_name):
                raise ValueError(f'Bucket {bucket_name} does not exist')

            data_stream = BytesIO(data)
            self.client.put_object(
                bucket_name,
                object_name,
                data_stream,
                length=len(data),
                content_type=content_type
            )

            return {
                'message': f'Object {object_name} uploaded successfully',
                'bucket': bucket_name,
                'object': object_name,
                'size': len(data)
            }
        except S3Error as e:
            logger.error(f"Error uploading object: {str(e)}")
            raise

    async def download_object(
        self,
        bucket_name: str,
        object_name: str
    ) -> bytes:
        """Download an object from a bucket"""
        try:
            if not self.client.bucket_exists(bucket_name):
                raise ValueError(f'Bucket {bucket_name} does not exist')

            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()

            return data
        except S3Error as e:
            logger.error(f"Error downloading object: {str(e)}")
            raise

    async def delete_object(
        self,
        bucket_name: str,
        object_name: str
    ) -> Dict[str, Any]:
        """Delete an object from a bucket"""
        try:
            if not self.client.bucket_exists(bucket_name):
                raise ValueError(f'Bucket {bucket_name} does not exist')

            self.client.remove_object(bucket_name, object_name)

            return {
                'message': f'Object {object_name} deleted successfully',
                'bucket': bucket_name,
                'object': object_name
            }
        except S3Error as e:
            logger.error(f"Error deleting object: {str(e)}")
            raise

    async def copy_object(
        self,
        source_bucket: str,
        source_object: str,
        dest_bucket: str,
        dest_object: str
    ) -> Dict[str, Any]:
        """Copy an object from one location to another"""
        try:
            from minio.commonconfig import CopySource

            self.client.copy_object(
                dest_bucket,
                dest_object,
                CopySource(source_bucket, source_object)
            )

            return {
                'message': f'Object copied successfully',
                'source': f'{source_bucket}/{source_object}',
                'destination': f'{dest_bucket}/{dest_object}'
            }
        except S3Error as e:
            logger.error(f"Error copying object: {str(e)}")
            raise

    async def get_bucket_stats(self, bucket_name: str) -> Dict[str, Any]:
        """Get statistics for a bucket"""
        try:
            if not self.client.bucket_exists(bucket_name):
                raise ValueError(f'Bucket {bucket_name} does not exist')

            objects = list(self.client.list_objects(bucket_name, recursive=True))

            total_size = sum(obj.size for obj in objects if not obj.object_name.endswith('/'))
            total_objects = len([obj for obj in objects if not obj.object_name.endswith('/')])

            return {
                'bucket_name': bucket_name,
                'total_objects': total_objects,
                'total_size': total_size,
                'total_size_human': self._human_readable_size(total_size)
            }
        except S3Error as e:
            logger.error(f"Error getting bucket stats: {str(e)}")
            raise

    def _human_readable_size(self, size: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"


# Singleton instance
_storage_service = None

def get_storage_service() -> StorageService:
    """Get or create storage service instance"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
