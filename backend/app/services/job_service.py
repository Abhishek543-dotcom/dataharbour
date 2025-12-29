import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import asyncio
from sqlalchemy.orm import Session

from app.models.schemas import Job, JobCreate, JobDetails, JobStatus, JobFilter
from app.services.spark_service import spark_service
from app.core.websocket_manager import manager
from app.db.repositories.job_repository import JobRepository
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class JobService:
    def __init__(self):
        self.repository = JobRepository()

    def _job_model_to_details(self, job_db) -> JobDetails:
        """Convert database model to JobDetails schema"""
        return JobDetails(
            id=job_db.id,
            name=job_db.name,
            status=JobStatus(job_db.status),
            cluster=job_db.cluster,
            code=job_db.code,
            start_time=job_db.start_time,
            end_time=job_db.end_time,
            duration=job_db.duration,
            logs=job_db.logs or "",
            error_message=job_db.error_message,
            config=job_db.config or {},
            spark_ui_url=job_db.spark_ui_url
        )

    async def get_all_jobs(
        self,
        db: Session,
        filter_params: Optional[JobFilter] = None,
        user_id: Optional[str] = None
    ) -> List[Job]:
        """Get all jobs with optional filtering"""
        if filter_params and filter_params.search:
            jobs_db = self.repository.search_jobs(
                db,
                filter_params.search,
                user_id=user_id
            )
        elif filter_params and filter_params.status:
            jobs_db = self.repository.get_by_status(
                db,
                filter_params.status,
                user_id=user_id
            )
        elif filter_params and filter_params.cluster:
            jobs_db = self.repository.get_by_cluster(
                db,
                filter_params.cluster,
                user_id=user_id
            )
        elif user_id:
            jobs_db = self.repository.get_by_user(db, user_id)
        else:
            jobs_db = self.repository.get_all(db, limit=1000)

        # Convert to schema and sort
        jobs = [self._job_model_to_details(j) for j in jobs_db]
        jobs.sort(key=lambda x: x.start_time or datetime.now(), reverse=True)
        return jobs

    async def get_job(self, db: Session, job_id: str) -> Optional[JobDetails]:
        """Get specific job by ID"""
        job_db = self.repository.get_by_id(db, job_id)
        if job_db:
            return self._job_model_to_details(job_db)
        return None

    async def create_job(
        self,
        db: Session,
        job_data: JobCreate,
        user_id: Optional[str] = None
    ) -> JobDetails:
        """Create and submit a new Spark job"""
        try:
            job_id = f"job_{uuid.uuid4().hex[:12]}"

            cluster_id = job_data.cluster_id or "spark-cluster-default"
            cluster = await spark_service.get_cluster(cluster_id)

            if not cluster:
                raise ValueError(f"Cluster {cluster_id} not found")

            # Create job in database
            job_dict = {
                "id": job_id,
                "name": job_data.name,
                "status": JobStatus.PENDING.value,
                "cluster": cluster.name,
                "code": job_data.code,
                "start_time": datetime.now(),
                "config": job_data.config or {},
                "spark_ui_url": f"{cluster.ui_url}/jobs/job?id={job_id}",
                "user_id": user_id,
                "logs": ""
            }

            job_db = self.repository.create(db, job_dict)

            # Start job execution in background
            asyncio.create_task(self._execute_job(job_id, job_data.code, cluster_id))

            logger.info(f"Job {job_id} created and submitted")
            return self._job_model_to_details(job_db)
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            raise

    async def _execute_job(self, job_id: str, code: str, cluster_id: str):
        """Execute job asynchronously"""
        # Create new database session for background task
        db = SessionLocal()
        try:
            job_db = self.repository.get_by_id(db, job_id)
            if not job_db:
                logger.error(f"Job {job_id} not found in database")
                return

            # Update status to running
            self.repository.update(db, job_id, {"status": JobStatus.RUNNING.value})
            logs = [
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} INFO SparkContext: Starting Spark application",
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} INFO SparkSession: Created SparkSession for {job_db.name}"
            ]

            # Broadcast job status update
            await manager.broadcast_job_update({
                "job_id": job_id,
                "status": "running",
                "timestamp": datetime.now().isoformat()
            })

            # Execute the code
            result = await asyncio.to_thread(
                spark_service.execute_code,
                code,
                cluster_id
            )

            # Update job status based on result
            update_dict = {}
            if result["status"] == "success" or result["status"] == "completed_with_warnings":
                update_dict["status"] = JobStatus.COMPLETED.value
                logs.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} INFO DAGScheduler: Job {job_id} completed successfully")
                if result["output"]:
                    logs.append(f"\nOutput:\n{result['output']}")
            else:
                update_dict["status"] = JobStatus.FAILED.value
                update_dict["error_message"] = result["errors"]
                logs.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ERROR SparkContext: Job execution failed")
                logs.append(f"Error: {result['errors']}")

            update_dict["end_time"] = datetime.now()
            update_dict["duration"] = f"{result['execution_time']:.2f}s"
            update_dict["logs"] = "\n".join(logs)

            # Update database
            self.repository.update(db, job_id, update_dict)

            # Broadcast completion
            await manager.broadcast_job_update({
                "job_id": job_id,
                "status": update_dict["status"],
                "duration": update_dict["duration"],
                "timestamp": datetime.now().isoformat()
            })

            logger.info(f"Job {job_id} finished with status: {update_dict['status']}")

        except Exception as e:
            logger.error(f"Error executing job {job_id}: {e}")
            try:
                self.repository.update(db, job_id, {
                    "status": JobStatus.FAILED.value,
                    "error_message": str(e),
                    "end_time": datetime.now(),
                    "logs": f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ERROR: {str(e)}"
                })
            except:
                pass
        finally:
            db.close()

    async def kill_job(self, db: Session, job_id: str) -> bool:
        """Kill a running job"""
        try:
            job_db = self.repository.get_by_id(db, job_id)
            if not job_db:
                return False

            if job_db.status != JobStatus.RUNNING.value:
                raise ValueError(f"Job {job_id} is not running")

            # Update job status
            logs = job_db.logs or ""
            logs += f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WARN: Job killed by user request"

            self.repository.update(db, job_id, {
                "status": JobStatus.FAILED.value,
                "error_message": "Job killed by user",
                "end_time": datetime.now(),
                "logs": logs
            })

            # Broadcast update
            await manager.broadcast_job_update({
                "job_id": job_id,
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            })

            logger.info(f"Job {job_id} killed")
            return True
        except Exception as e:
            logger.error(f"Error killing job {job_id}: {e}")
            raise

    async def restart_job(
        self,
        db: Session,
        job_id: str,
        user_id: Optional[str] = None
    ) -> JobDetails:
        """Restart a job"""
        try:
            old_job_db = self.repository.get_by_id(db, job_id)
            if not old_job_db:
                raise ValueError(f"Job {job_id} not found")

            # Create new job with same code
            job_data = JobCreate(
                name=f"{old_job_db.name} (Restarted)",
                code=old_job_db.code or "",
                config=old_job_db.config or {}
            )

            new_job = await self.create_job(db, job_data, user_id)
            logger.info(f"Job {job_id} restarted as {new_job.id}")
            return new_job
        except Exception as e:
            logger.error(f"Error restarting job {job_id}: {e}")
            raise

    async def get_job_logs(self, db: Session, job_id: str) -> str:
        """Get job logs"""
        job_db = self.repository.get_by_id(db, job_id)
        if not job_db:
            raise ValueError(f"Job {job_id} not found")
        return job_db.logs or "No logs available"

    async def get_jobs_by_date(self, db: Session, date: datetime, user_id: Optional[str] = None) -> List[Job]:
        """Get jobs that started on a specific date"""
        # For now, get all jobs and filter (can be optimized with a repository method)
        if user_id:
            jobs_db = self.repository.get_by_user(db, user_id, limit=1000)
        else:
            jobs_db = self.repository.get_all(db, limit=1000)

        jobs = []
        for job_db in jobs_db:
            if job_db.start_time and job_db.start_time.date() == date.date():
                jobs.append(self._job_model_to_details(job_db))
        return jobs


# Singleton instance
job_service = JobService()
