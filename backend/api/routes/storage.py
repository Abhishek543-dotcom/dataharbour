"""
DHFS — DataHarbour File System (MinIO Storage) Routes
=====================================================
GET    /dhfs/buckets                        — List all buckets
POST   /dhfs/buckets/{name}                 — Create bucket
DELETE /dhfs/buckets/{name}                 — Delete bucket
GET    /dhfs/files/{bucket}                 — List files in bucket
POST   /dhfs/upload/{bucket}                — Upload file to bucket
DELETE /dhfs/files/{bucket}/{key}           — Delete file
GET    /dhfs/download/{bucket}/{key}        — Get pre-signed download URL
"""

import logging

from botocore.exceptions import ClientError
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from api.helpers import get_s3_client

logger = logging.getLogger("dataharbour.routes.storage")
router = APIRouter(prefix="/dhfs", tags=["Storage (MinIO/DHFS)"])


# ──────────────────────────────────────────────────────
#  Buckets
# ──────────────────────────────────────────────────────

@router.get("/buckets")
def list_buckets():
    """List all MinIO buckets."""
    s3 = get_s3_client()
    try:
        resp = s3.list_buckets()
        buckets = [
            {
                "name": b["Name"],
                "created": b["CreationDate"].isoformat() if b.get("CreationDate") else None,
            }
            for b in resp.get("Buckets", [])
        ]
        return {"buckets": buckets, "count": len(buckets)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/buckets/{bucket_name}")
def create_bucket(bucket_name: str):
    """Create a new MinIO bucket."""
    s3 = get_s3_client()
    try:
        s3.create_bucket(Bucket=bucket_name)
        logger.info("Bucket created: %s", bucket_name)
        return {"message": f"Bucket '{bucket_name}' created", "bucket": bucket_name}
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code in ("BucketAlreadyExists", "BucketAlreadyOwnedByYou"):
            raise HTTPException(status_code=409, detail=f"Bucket '{bucket_name}' already exists")
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/buckets/{bucket_name}")
def delete_bucket(bucket_name: str):
    """Delete an empty MinIO bucket."""
    s3 = get_s3_client()
    try:
        s3.delete_bucket(Bucket=bucket_name)
        logger.info("Bucket deleted: %s", bucket_name)
        return {"message": f"Bucket '{bucket_name}' deleted"}
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code == "NoSuchBucket":
            raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' not found")
        if code == "BucketNotEmpty":
            raise HTTPException(
                status_code=409,
                detail=f"Bucket '{bucket_name}' is not empty — delete all files first",
            )
        raise HTTPException(status_code=400, detail=str(exc))


# ──────────────────────────────────────────────────────
#  Files
# ──────────────────────────────────────────────────────

@router.get("/files/{bucket_name}")
def list_files(bucket_name: str, prefix: str = Query("", description="Filter by key prefix")):
    """List files in a MinIO bucket, optionally filtered by prefix."""
    s3 = get_s3_client()
    try:
        resp = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        files = [
            {
                "name": obj["Key"],
                "size": obj["Size"],
                "lastModified": obj["LastModified"].isoformat(),
                "type": obj["Key"].rsplit(".", 1)[-1] if "." in obj["Key"] else "unknown",
            }
            for obj in resp.get("Contents", [])
        ]
        return {"files": files, "bucket": bucket_name, "count": len(files)}
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "NoSuchBucket":
            raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' not found")
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/upload/{bucket_name}")
def upload_file(bucket_name: str, file: UploadFile = File(...)):
    """
    Upload a file to a MinIO bucket.

    Auto-creates the bucket if it does not exist.
    """
    s3 = get_s3_client()
    try:
        # Auto-create bucket
        try:
            s3.head_bucket(Bucket=bucket_name)
        except ClientError:
            s3.create_bucket(Bucket=bucket_name)

        content = file.file.read()
        s3.put_object(Bucket=bucket_name, Key=file.filename, Body=content)
        logger.info("File uploaded: %s → %s (%d bytes)", file.filename, bucket_name, len(content))
        return {
            "message": f"File '{file.filename}' uploaded to '{bucket_name}'",
            "bucket": bucket_name,
            "filename": file.filename,
            "size": len(content),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/files/{bucket_name}/{file_key:path}")
def delete_file(bucket_name: str, file_key: str):
    """Delete a specific file from a MinIO bucket."""
    s3 = get_s3_client()
    try:
        s3.head_object(Bucket=bucket_name, Key=file_key)
        s3.delete_object(Bucket=bucket_name, Key=file_key)
        logger.info("File deleted: %s/%s", bucket_name, file_key)
        return {"message": f"File '{file_key}' deleted from '{bucket_name}'"}
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code in ("404", "NoSuchKey"):
            raise HTTPException(
                status_code=404,
                detail=f"File '{file_key}' not found in '{bucket_name}'",
            )
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/download/{bucket_name}/{file_key:path}")
def download_file(bucket_name: str, file_key: str):
    """Generate a pre-signed download URL valid for 1 hour."""
    s3 = get_s3_client()
    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": file_key},
            ExpiresIn=3600,
        )
        return {"url": url, "file": file_key, "bucket": bucket_name, "expires_in": 3600}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

