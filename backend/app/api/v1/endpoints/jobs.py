from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
import logging

from app.models.schemas import Job, JobDetails, JobCreate, JobFilter, JobStatus, APIResponse, User
from app.services.job_service import job_service
from app.db.session import get_db
from app.api.dependencies import get_optional_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[Job])
async def get_jobs(
    status: Optional[JobStatus] = None,
    cluster: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get all jobs with optional filtering"""
    try:
        filter_params = JobFilter(status=status, cluster=cluster, search=search)
        user_id = str(current_user.id) if current_user else None
        jobs = await job_service.get_all_jobs(db, filter_params, user_id)
        return jobs
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=JobDetails)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get specific job details"""
    try:
        job = await job_service.get_job(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=JobDetails)
async def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Submit a new Spark job"""
    try:
        user_id = str(current_user.id) if current_user else None
        job = await job_service.create_job(db, job_data, user_id)
        return job
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/kill", response_model=APIResponse)
async def kill_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Kill a running job"""
    try:
        success = await job_service.kill_job(db, job_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return APIResponse(
            success=True,
            message=f"Job {job_id} killed successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error killing job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/restart", response_model=JobDetails)
async def restart_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Restart a job"""
    try:
        user_id = str(current_user.id) if current_user else None
        job = await job_service.restart_job(db, job_id, user_id)
        return job
    except Exception as e:
        logger.error(f"Error restarting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/logs")
async def get_job_logs(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get job logs"""
    try:
        logs = await job_service.get_job_logs(db, job_id)
        return {"job_id": job_id, "logs": logs}
    except Exception as e:
        logger.error(f"Error getting logs for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/spark-ui")
async def get_spark_ui(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get Spark UI URL for job"""
    try:
        job = await job_service.get_job(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return {
            "job_id": job_id,
            "spark_ui_url": job.spark_ui_url
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Spark UI for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/convert-to-dag")
async def convert_job_to_dag(
    job_id: str,
    schedule_interval: Optional[str] = "0 0 * * *",
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Convert a Spark job into an Airflow DAG for scheduling"""
    try:
        job = await job_service.get_job(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Create DAG file from job
        dag_id = f"spark_job_{job.name.lower().replace(' ', '_')}_{job_id[:8]}"
        dag_file_path = f"/opt/airflow/dags/{dag_id}.py"

        # Properly escape the job code for Python string
        escaped_code = job.code.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

        dag_content = f'''"""
Auto-generated Airflow DAG from Spark Job: {job.name}
Job ID: {job_id}
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import requests

default_args = {{
    'owner': 'dataharbour',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}}

dag = DAG(
    '{dag_id}',
    default_args=default_args,
    description='Spark Job: {job.name}',
    schedule_interval='{schedule_interval}',
    catchup=False,
    tags=['spark', 'dataharbour', 'auto-generated'],
)

def execute_spark_job():
    """Execute the Spark job via DataHarbour API"""
    import requests
    response = requests.post(
        'http://backend:8000/api/v1/jobs',
        json={{
            'name': '{job.name}',
            'code': "{escaped_code}",
            'cluster_id': '{job.cluster}'
        }}
    )
    if response.status_code != 200:
        raise Exception(f"Job execution failed: {{response.text}}")
    return response.json()

execute_job_task = PythonOperator(
    task_id='execute_spark_job',
    python_callable=execute_spark_job,
    dag=dag,
)
'''

        # Write DAG file
        import os
        os.makedirs("/opt/airflow/dags", exist_ok=True)
        with open(dag_file_path, 'w') as f:
            f.write(dag_content)

        return APIResponse(
            success=True,
            message=f"Job converted to DAG '{dag_id}'. It will appear in Airflow shortly."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting job to DAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))
