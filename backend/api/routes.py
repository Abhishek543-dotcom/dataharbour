from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List
import boto3
from botocore.exceptions import ClientError
import psycopg2
from psycopg2 import sql
import requests
import os
import json
import uuid
from datetime import datetime
from core.config import Config

router = APIRouter()

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class NotebookContent(BaseModel):
    cells: List[dict] = []
    metadata: dict = {}
    nbformat: int = 4
    nbformat_minor: int = 5

# MinIO client
try:
    s3_client = boto3.client(
        's3',
        endpoint_url=Config.minio_endpoint,
        aws_access_key_id=Config.minio_access_key or "minioadmin",
        aws_secret_access_key=Config.minio_secret_key or "minioadmin"
    )
except Exception as e:
    print(f"Warning: Could not initialize MinIO client: {e}")
    s3_client = None

# Postgres connection
def get_db_connection(db_name=None):
    return psycopg2.connect(
        host=Config.postgres_host,
        port=Config.postgres_port,
        user=Config.postgres_user,
        password=Config.postgres_password,
        database=db_name or Config.postgres_db
    )

@router.post("/minio/upload/{bucket}")
async def upload_file_to_minio(bucket: str, file: UploadFile = File(...)):
    if s3_client is None:
        raise HTTPException(status_code=503, detail="MinIO client not available")
    try:
        # Ensure bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket)
        except ClientError:
            s3_client.create_bucket(Bucket=bucket)

        # Upload file
        s3_client.put_object(
            Bucket=bucket,
            Key=file.filename,
            Body=await file.read()
        )
        return {"message": f"File {file.filename} uploaded to bucket {bucket}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/minio/delete/{bucket}/{key}")
async def delete_file_from_minio(bucket: str, key: str):
    if s3_client is None:
        raise HTTPException(status_code=503, detail="MinIO client not available")
    try:
        s3_client.delete_object(Bucket=bucket, Key=key)
        return {"message": f"File {key} deleted from bucket {bucket}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/database/create/{db_name}")
async def create_database(db_name: str):
    conn = get_db_connection()
    conn.autocommit = True
    cursor = conn.cursor()
    try:
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        return {"message": f"Database {db_name} created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.delete("/database/delete/{db_name}")
async def delete_database(db_name: str):
    conn = get_db_connection()
    conn.autocommit = True
    cursor = conn.cursor()
    try:
        cursor.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(db_name)))
        return {"message": f"Database {db_name} deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/table/create/{db_name}/{table_name}")
async def create_table(db_name: str, table_name: str):
    # For Iceberg tables, this would require Spark session
    # For simplicity, create a basic table in Postgres
    conn = get_db_connection(db_name)
    cursor = conn.cursor()
    try:
        cursor.execute(
            sql.SQL("CREATE TABLE IF NOT EXISTS {} (id SERIAL PRIMARY KEY, data JSONB)").format(
                sql.Identifier(table_name)
            )
        )
        conn.commit()
        return {"message": f"Table {table_name} created in database {db_name}"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.delete("/table/delete/{db_name}/{table_name}")
async def delete_table(db_name: str, table_name: str):
    conn = get_db_connection(db_name)
    cursor = conn.cursor()
    try:
        cursor.execute(
            sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table_name))
        )
        conn.commit()
        return {"message": f"Table {table_name} deleted from database {db_name}"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/jobs/submit")
async def submit_job(file: UploadFile = File(...)):
    try:
        # Save the file to workspace/jobs
        job_id = str(uuid.uuid4())
        file_path = f"/workspace/jobs/{job_id}_{file.filename}"

        # Ensure jobs directory exists
        os.makedirs("/workspace/jobs", exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(await file.read())

        # For now, just return success - actual job submission would require
        # proper Spark cluster communication
        return {"message": "Job file uploaded successfully", "job_id": job_id, "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/jobs/running")
async def get_running_jobs():
    spark_url = f"{Config.spark_rest_url}/v1/submissions/status"
    # This endpoint might need adjustment for standalone mode
    # For simplicity, return placeholder
    return {"running_jobs": []}

@router.get("/jobs/pending")
async def get_pending_jobs():
    # Placeholder
    return {"pending_jobs": []}

@router.get("/jobs/completed")
async def get_completed_jobs():
    # Placeholder
    return {"completed_jobs": []}

# Existing endpoints
@router.get("/jobs")
def get_jobs():
    return {"jobs": []}

@router.get("/logs")
def get_logs():
    return {"logs": []}

@router.get("/cluster")
def get_cluster():
    return {"cluster": "status"}

# ==================== AUTHENTICATION ====================
@router.post("/auth/login")
async def login(credentials: LoginRequest):
    """Simple login - in production, use proper auth like JWT"""
    # Demo: accept any credentials
    return {
        "success": True,
        "user": {
            "username": credentials.username,
            "name": "DataHarbour User",
            "token": "demo-token-12345"
        }
    }

@router.post("/auth/logout")
async def logout():
    """Logout endpoint"""
    return {"success": True, "message": "Logged out successfully"}

# ==================== DHFS (MinIO File System) ====================
@router.get("/dhfs/buckets")
async def list_buckets():
    """List all MinIO buckets"""
    if s3_client is None:
        raise HTTPException(status_code=503, detail="MinIO client not available")
    try:
        response = s3_client.list_buckets()
        buckets = [
            {
                "name": bucket["Name"],
                "created": bucket["CreationDate"].isoformat() if bucket.get("CreationDate") else None
            }
            for bucket in response.get("Buckets", [])
        ]
        return {"buckets": buckets}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/dhfs/buckets/{bucket_name}")
async def create_bucket(bucket_name: str):
    """Create a new MinIO bucket"""
    if s3_client is None:
        raise HTTPException(status_code=503, detail="MinIO client not available")
    try:
        s3_client.create_bucket(Bucket=bucket_name)
        return {"message": f"Bucket {bucket_name} created", "bucket": bucket_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/dhfs/buckets/{bucket_name}")
async def delete_bucket(bucket_name: str):
    """Delete a MinIO bucket"""
    if s3_client is None:
        raise HTTPException(status_code=503, detail="MinIO client not available")
    try:
        s3_client.delete_bucket(Bucket=bucket_name)
        return {"message": f"Bucket {bucket_name} deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/dhfs/files/{bucket_name}")
async def list_files(bucket_name: str, prefix: str = ""):
    """List files in a MinIO bucket"""
    if s3_client is None:
        raise HTTPException(status_code=503, detail="MinIO client not available")
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        files = [
            {
                "name": obj["Key"],
                "size": obj["Size"],
                "lastModified": obj["LastModified"].isoformat(),
                "type": obj["Key"].split(".")[-1] if "." in obj["Key"] else "unknown"
            }
            for obj in response.get("Contents", [])
        ]
        return {"files": files, "bucket": bucket_name}
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            raise HTTPException(status_code=404, detail=f"Bucket {bucket_name} not found")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/dhfs/download/{bucket_name}/{file_key:path}")
async def download_file(bucket_name: str, file_key: str):
    """Get presigned URL for file download"""
    if s3_client is None:
        raise HTTPException(status_code=503, detail="MinIO client not available")
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': file_key},
            ExpiresIn=3600
        )
        return {"url": url, "file": file_key}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== CATALOG (Databases & Tables) ====================
@router.get("/catalog/databases")
async def list_databases():
    """List all PostgreSQL databases"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
            FROM pg_database
            WHERE datistemplate = false AND datname NOT IN ('postgres')
        """)
        databases = [
            {"name": row[0], "size": row[1]}
            for row in cursor.fetchall()
        ]
        return {"databases": databases}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/catalog/databases/{db_name}/tables")
async def list_tables(db_name: str):
    """List all tables in a database"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection(db_name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name,
                   pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        tables = [
            {"name": row[0], "size": row[1]}
            for row in cursor.fetchall()
        ]
        return {"tables": tables, "database": db_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/catalog/iceberg/tables")
async def list_iceberg_tables():
    """List all Iceberg tables"""
    tables_path = "/workspace/iceberg/dataharbour"
    try:
        if os.path.exists(tables_path):
            tables = [
                {
                    "name": name,
                    "path": os.path.join(tables_path, name),
                    "hasMetadata": os.path.exists(os.path.join(tables_path, name, "metadata"))
                }
                for name in os.listdir(tables_path)
                if os.path.isdir(os.path.join(tables_path, name))
            ]
        else:
            tables = []
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/catalog/iceberg/tables/{table_name}")
async def get_iceberg_table_details(table_name: str):
    """Get Iceberg table metadata"""
    metadata_path = f"/workspace/iceberg/dataharbour/{table_name}/metadata"
    try:
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail="Table not found")

        # Find the latest metadata file
        metadata_files = [f for f in os.listdir(metadata_path) if f.endswith('.metadata.json')]
        if metadata_files:
            latest_metadata = sorted(metadata_files)[-1]
            with open(os.path.join(metadata_path, latest_metadata), 'r') as f:
                metadata = json.load(f)
            return {"table": table_name, "metadata": metadata}
        return {"table": table_name, "metadata": None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== NOTEBOOKS ====================
@router.get("/notebooks")
async def list_notebooks():
    """List all notebooks"""
    notebooks_path = "/workspace/notebooks"
    try:
        if os.path.exists(notebooks_path):
            notebooks = []
            for f in os.listdir(notebooks_path):
                if f.endswith(".ipynb"):
                    file_path = os.path.join(notebooks_path, f)
                    stat = os.stat(file_path)
                    notebooks.append({
                        "id": f,
                        "name": f,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "lastModified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        else:
            notebooks = []
        return {"notebooks": notebooks}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/notebooks/{notebook_name}")
async def get_notebook(notebook_name: str):
    """Get notebook content"""
    notebook_path = f"/workspace/notebooks/{notebook_name}"
    try:
        if not os.path.exists(notebook_path):
            raise HTTPException(status_code=404, detail="Notebook not found")
        with open(notebook_path, "r") as f:
            content = json.load(f)
        return {"notebook": notebook_name, "content": content}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid notebook format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/notebooks")
async def create_notebook(name: str):
    """Create a new notebook"""
    if not name.endswith('.ipynb'):
        name = f"{name}.ipynb"
    notebook_path = f"/workspace/notebooks/{name}"

    try:
        if os.path.exists(notebook_path):
            raise HTTPException(status_code=400, detail="Notebook already exists")

        empty_notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": ["# New DataHarbour Notebook\n", "print('Hello, DataHarbour!')"]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 5
        }

        os.makedirs(os.path.dirname(notebook_path), exist_ok=True)
        with open(notebook_path, "w") as f:
            json.dump(empty_notebook, f, indent=2)

        return {"message": f"Notebook {name} created", "notebook": name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/notebooks/{notebook_name}")
async def save_notebook(notebook_name: str, content: NotebookContent):
    """Save notebook content"""
    notebook_path = f"/workspace/notebooks/{notebook_name}"
    try:
        with open(notebook_path, "w") as f:
            json.dump(content.dict(), f, indent=2)
        return {"message": "Notebook saved", "notebook": notebook_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/notebooks/{notebook_name}")
async def delete_notebook(notebook_name: str):
    """Delete a notebook"""
    notebook_path = f"/workspace/notebooks/{notebook_name}"
    try:
        if not os.path.exists(notebook_path):
            raise HTTPException(status_code=404, detail="Notebook not found")
        os.remove(notebook_path)
        return {"message": f"Notebook {notebook_name} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/notebooks/{notebook_name}/execute")
async def execute_notebook(notebook_name: str):
    """Execute a notebook as a Spark job"""
    notebook_path = f"/workspace/notebooks/{notebook_name}"
    try:
        if not os.path.exists(notebook_path):
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Convert notebook to Python script and submit as job
        with open(notebook_path, "r") as f:
            notebook = json.load(f)

        # Extract code cells
        code = "\n".join([
            "".join(cell.get("source", []))
            for cell in notebook.get("cells", [])
            if cell.get("cell_type") == "code"
        ])

        # Save as job file
        job_id = str(uuid.uuid4())
        job_path = f"/workspace/jobs/{job_id}_{notebook_name.replace('.ipynb', '.py')}"

        # Ensure jobs directory exists
        os.makedirs("/workspace/jobs", exist_ok=True)

        with open(job_path, "w") as f:
            f.write(code)

        return {
            "message": "Notebook execution started",
            "job_id": job_id,
            "job_path": job_path
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== CLUSTER STATUS ====================
@router.get("/cluster/status")
async def get_cluster_status():
    """Get detailed Spark cluster status"""
    try:
        # Try to get Spark master status
        response = requests.get(f"{Config.spark_rest_url}/json/", timeout=5)
        if response.ok:
            spark_data = response.json()
            return {
                "status": "running",
                "masterUrl": f"spark://spark-master:7077",
                "workers": len(spark_data.get("workers", [])),
                "cores": spark_data.get("cores", 0),
                "memory": spark_data.get("memory", "0 GB"),
                "activeApps": len(spark_data.get("activeapps", [])),
                "completedApps": len(spark_data.get("completedapps", []))
            }
    except:
        pass

    # Return default/unavailable status
    return {
        "status": "unavailable",
        "masterUrl": "spark://spark-master:7077",
        "workers": 0,
        "cores": 0,
        "memory": "0 GB",
        "activeApps": 0,
        "completedApps": 0
    }

@router.get("/cluster/workers")
async def get_cluster_workers():
    """Get Spark cluster workers"""
    try:
        response = requests.get(f"{Config.spark_rest_url}/json/", timeout=5)
        if response.ok:
            spark_data = response.json()
            return {"workers": spark_data.get("workers", [])}
    except:
        pass
    return {"workers": []}

@router.get("/cluster/applications")
async def get_cluster_applications():
    """Get running and completed Spark applications"""
    try:
        response = requests.get(f"{Config.spark_rest_url}/json/", timeout=5)
        if response.ok:
            spark_data = response.json()
            return {
                "active": spark_data.get("activeapps", []),
                "completed": spark_data.get("completedapps", [])
            }
    except:
        pass
    return {"active": [], "completed": []}

# ==================== STATS (Dashboard) ====================
@router.get("/stats/summary")
async def get_stats_summary():
    """Get summary stats for dashboard"""
    notebooks_count = 0
    jobs_count = 0
    buckets_count = 0
    databases_count = 0

    # Count notebooks
    notebooks_path = "/workspace/notebooks"
    if os.path.exists(notebooks_path):
        notebooks_count = len([f for f in os.listdir(notebooks_path) if f.endswith('.ipynb')])

    # Count jobs
    jobs_path = "/workspace/jobs"
    if os.path.exists(jobs_path):
        jobs_count = len([f for f in os.listdir(jobs_path) if f.endswith('.py')])

    # Count buckets
    try:
        if s3_client:
            response = s3_client.list_buckets()
            buckets_count = len(response.get("Buckets", []))
    except:
        pass

    # Count databases
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres')")
        databases_count = cursor.fetchone()[0]
    except:
        pass
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return {
        "notebooks": notebooks_count,
        "jobs": jobs_count,
        "buckets": buckets_count,
        "databases": databases_count
    }

@router.get("/activities/recent")
async def get_recent_activities():
    """Get recent activities for dashboard"""
    activities = []

    # Get recent notebooks
    notebooks_path = "/workspace/notebooks"
    if os.path.exists(notebooks_path):
        for f in os.listdir(notebooks_path):
            if f.endswith('.ipynb'):
                file_path = os.path.join(notebooks_path, f)
                stat = os.stat(file_path)
                activities.append({
                    "type": "notebook",
                    "action": "Modified",
                    "name": f,
                    "time": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

    # Get recent jobs
    jobs_path = "/workspace/jobs"
    if os.path.exists(jobs_path):
        for f in os.listdir(jobs_path):
            if f.endswith('.py'):
                file_path = os.path.join(jobs_path, f)
                stat = os.stat(file_path)
                activities.append({
                    "type": "job",
                    "action": "Submitted",
                    "name": f,
                    "time": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

    # Sort by time, most recent first
    activities.sort(key=lambda x: x["time"], reverse=True)

    return {"activities": activities[:10]}
