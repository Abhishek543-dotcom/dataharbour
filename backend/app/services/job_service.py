import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import asyncio

from app.models.schemas import Job, JobCreate, JobDetails, JobStatus, JobFilter
from app.services.spark_service import spark_service
from app.core.websocket_manager import manager

logger = logging.getLogger(__name__)


class JobService:
    def __init__(self):
        self._jobs: Dict[str, JobDetails] = {}
        self._job_logs: Dict[str, List[str]] = {}

    async def get_all_jobs(self, filter_params: Optional[JobFilter] = None) -> List[Job]:
        """Get all jobs with optional filtering"""
        jobs = list(self._jobs.values())

        if filter_params:
            if filter_params.status:
                jobs = [j for j in jobs if j.status == filter_params.status]
            if filter_params.cluster:
                jobs = [j for j in jobs if j.cluster == filter_params.cluster]
            if filter_params.search:
                search_lower = filter_params.search.lower()
                jobs = [j for j in jobs if search_lower in j.name.lower() or search_lower in j.id.lower()]

        # Sort by start time, newest first
        jobs.sort(key=lambda x: x.start_time or datetime.now(), reverse=True)
        return jobs

    async def get_job(self, job_id: str) -> Optional[JobDetails]:
        """Get specific job by ID"""
        return self._jobs.get(job_id)

    async def create_job(self, job_data: JobCreate) -> JobDetails:
        """Create and submit a new Spark job"""
        try:
            job_id = f"job_{uuid.uuid4().hex[:12]}"

            cluster_id = job_data.cluster_id or "spark-cluster-default"
            cluster = await spark_service.get_cluster(cluster_id)

            if not cluster:
                raise ValueError(f"Cluster {cluster_id} not found")

            job = JobDetails(
                id=job_id,
                name=job_data.name,
                status=JobStatus.PENDING,
                cluster=cluster.name,
                code=job_data.code,
                start_time=datetime.now(),
                duration=None,
                logs="",
                config=job_data.config,
                spark_ui_url=f"{cluster.ui_url}/jobs/job?id={job_id}"
            )

            self._jobs[job_id] = job
            self._job_logs[job_id] = []

            # Start job execution in background
            asyncio.create_task(self._execute_job(job_id, job_data.code, cluster_id))

            logger.info(f"Job {job_id} created and submitted")
            return job
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            raise

    async def _execute_job(self, job_id: str, code: str, cluster_id: str):
        """Execute job asynchronously"""
        try:
            job = self._jobs[job_id]
            job.status = JobStatus.RUNNING
            self._add_log(job_id, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} INFO SparkContext: Starting Spark application")
            self._add_log(job_id, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} INFO SparkSession: Created SparkSession for {job.name}")

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
            if result["status"] == "success" or result["status"] == "completed_with_warnings":
                job.status = JobStatus.COMPLETED
                self._add_log(job_id, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} INFO DAGScheduler: Job {job_id} completed successfully")
                if result["output"]:
                    self._add_log(job_id, f"\nOutput:\n{result['output']}")
            else:
                job.status = JobStatus.FAILED
                job.error_message = result["errors"]
                self._add_log(job_id, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ERROR SparkContext: Job execution failed")
                self._add_log(job_id, f"Error: {result['errors']}")

            job.end_time = datetime.now()
            job.duration = f"{result['execution_time']:.2f}s"
            job.logs = "\n".join(self._job_logs[job_id])

            # Broadcast completion
            await manager.broadcast_job_update({
                "job_id": job_id,
                "status": job.status.value,
                "duration": job.duration,
                "timestamp": datetime.now().isoformat()
            })

            logger.info(f"Job {job_id} finished with status: {job.status}")

        except Exception as e:
            logger.error(f"Error executing job {job_id}: {e}")
            job = self._jobs.get(job_id)
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.end_time = datetime.now()
                self._add_log(job_id, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ERROR: {str(e)}")
                job.logs = "\n".join(self._job_logs[job_id])

    def _add_log(self, job_id: str, log_entry: str):
        """Add log entry to job"""
        if job_id not in self._job_logs:
            self._job_logs[job_id] = []
        self._job_logs[job_id].append(log_entry)

    async def kill_job(self, job_id: str) -> bool:
        """Kill a running job"""
        try:
            job = self._jobs.get(job_id)
            if not job:
                return False

            if job.status != JobStatus.RUNNING:
                raise ValueError(f"Job {job_id} is not running")

            # In a real implementation, this would kill the Spark job
            job.status = JobStatus.FAILED
            job.error_message = "Job killed by user"
            job.end_time = datetime.now()
            self._add_log(job_id, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WARN: Job killed by user request")
            job.logs = "\n".join(self._job_logs[job_id])

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

    async def restart_job(self, job_id: str) -> JobDetails:
        """Restart a job"""
        try:
            old_job = self._jobs.get(job_id)
            if not old_job:
                raise ValueError(f"Job {job_id} not found")

            # Create new job with same code
            job_data = JobCreate(
                name=f"{old_job.name} (Restarted)",
                code=old_job.code or "",
                config=old_job.config or {}
            )

            new_job = await self.create_job(job_data)
            logger.info(f"Job {job_id} restarted as {new_job.id}")
            return new_job
        except Exception as e:
            logger.error(f"Error restarting job {job_id}: {e}")
            raise

    async def get_job_logs(self, job_id: str) -> str:
        """Get job logs"""
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        return job.logs or "No logs available"

    async def get_jobs_by_date(self, date: datetime) -> List[Job]:
        """Get jobs that started on a specific date"""
        jobs = []
        for job in self._jobs.values():
            if job.start_time and job.start_time.date() == date.date():
                jobs.append(job)
        return jobs


# Singleton instance
job_service = JobService()
