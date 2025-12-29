import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark import SparkContext, SparkConf
import uuid
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.schemas import Cluster, ClusterStatus, ClusterCreate
from app.db.repositories.cluster_repository import ClusterRepository
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class SparkService:
    def __init__(self):
        self._spark_session: Optional[SparkSession] = None
        self.repository = ClusterRepository()

    def ensure_default_cluster(self, db: Session) -> None:
        """Ensure default Spark cluster exists in database"""
        try:
            default_cluster = self.repository.get_by_id(db, "spark-cluster-default")
            if not default_cluster:
                cluster_dict = {
                    "id": "spark-cluster-default",
                    "name": "Default Spark Cluster",
                    "status": ClusterStatus.RUNNING.value,
                    "master_url": settings.SPARK_MASTER_URL,
                    "ui_url": settings.SPARK_UI_URL,
                    "worker_nodes": 2,
                    "total_cores": 4,
                    "total_memory": "4g",
                    "config": {}
                }
                self.repository.create(db, cluster_dict)
                logger.info("Default cluster created in database")
        except Exception as e:
            logger.error(f"Error ensuring default cluster: {e}")

    def _cluster_db_to_schema(self, cluster_db) -> Cluster:
        """Convert database model to Cluster schema"""
        return Cluster(
            id=cluster_db.id,
            name=cluster_db.name,
            status=ClusterStatus(cluster_db.status),
            master_url=cluster_db.master_url,
            ui_url=cluster_db.ui_url,
            worker_nodes=cluster_db.worker_nodes,
            total_cores=cluster_db.total_cores,
            total_memory=cluster_db.total_memory,
            created_at=cluster_db.created_at
        )

    def get_spark_session(self, db: Session, cluster_id: Optional[str] = None) -> SparkSession:
        """Get or create Spark session"""
        try:
            if self._spark_session is None:
                # Ensure default cluster exists
                self.ensure_default_cluster(db)

                cluster_db = self.repository.get_by_id(db, cluster_id or "spark-cluster-default")
                master_url = cluster_db.master_url if cluster_db else settings.SPARK_MASTER_URL

                self._spark_session = SparkSession.builder \
                    .appName("DataHarbour") \
                    .master(master_url) \
                    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
                    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
                    .config("spark.hadoop.fs.s3a.endpoint", f"http://{settings.MINIO_ENDPOINT}") \
                    .config("spark.hadoop.fs.s3a.access.key", settings.MINIO_ACCESS_KEY) \
                    .config("spark.hadoop.fs.s3a.secret.key", settings.MINIO_SECRET_KEY) \
                    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
                    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
                    .getOrCreate()

                logger.info(f"Spark session created with master: {master_url}")

            return self._spark_session
        except Exception as e:
            logger.error(f"Error creating Spark session: {e}")
            raise

    async def get_clusters(self, db: Session, user_id: Optional[str] = None) -> List[Cluster]:
        """Get all Spark clusters"""
        # Ensure default cluster exists
        self.ensure_default_cluster(db)

        if user_id:
            clusters_db = self.repository.get_by_user(db, user_id, limit=1000)
        else:
            clusters_db = self.repository.get_all(db, limit=1000)

        return [self._cluster_db_to_schema(c) for c in clusters_db]

    async def get_cluster(self, db: Session, cluster_id: str) -> Optional[Cluster]:
        """Get specific cluster by ID"""
        # Ensure default cluster exists
        self.ensure_default_cluster(db)

        cluster_db = self.repository.get_by_id(db, cluster_id)
        if cluster_db:
            return self._cluster_db_to_schema(cluster_db)
        return None

    async def create_cluster(
        self,
        db: Session,
        cluster_data: ClusterCreate,
        user_id: Optional[str] = None
    ) -> Cluster:
        """Create a new Spark cluster"""
        try:
            cluster_id = f"spark-cluster-{uuid.uuid4().hex[:8]}"

            # Calculate cluster resources
            total_cores = cluster_data.worker_nodes * cluster_data.cores_per_node
            memory_value = int(cluster_data.memory_per_node[:-1])
            memory_unit = cluster_data.memory_per_node[-1]
            total_memory = f"{cluster_data.worker_nodes * memory_value}{memory_unit}"

            # In a real implementation, this would start new Spark worker nodes
            cluster_dict = {
                "id": cluster_id,
                "name": cluster_data.name,
                "status": ClusterStatus.STARTING.value,
                "master_url": settings.SPARK_MASTER_URL,
                "ui_url": f"{settings.SPARK_UI_URL.replace('4040', str(4040 + self.repository.count(db)))}",
                "worker_nodes": cluster_data.worker_nodes,
                "total_cores": total_cores,
                "total_memory": total_memory,
                "config": {},
                "user_id": user_id
            }

            cluster_db = self.repository.create(db, cluster_dict)

            # Simulate cluster startup
            import asyncio
            asyncio.create_task(self._start_cluster(cluster_id))

            logger.info(f"Cluster {cluster_id} created")
            return self._cluster_db_to_schema(cluster_db)
        except Exception as e:
            logger.error(f"Error creating cluster: {e}")
            raise

    async def _start_cluster(self, cluster_id: str):
        """Simulate cluster startup"""
        import asyncio
        await asyncio.sleep(5)  # Simulate startup time

        # Update cluster status in database
        db = SessionLocal()
        try:
            self.repository.update(db, cluster_id, {"status": ClusterStatus.RUNNING.value})
            logger.info(f"Cluster {cluster_id} is now running")
        finally:
            db.close()

    async def delete_cluster(self, db: Session, cluster_id: str) -> bool:
        """Delete a cluster"""
        try:
            if cluster_id == "spark-cluster-default":
                raise ValueError("Cannot delete default cluster")

            cluster_db = self.repository.get_by_id(db, cluster_id)
            if not cluster_db:
                return False

            # Update status to stopping
            self.repository.update(db, cluster_id, {"status": ClusterStatus.STOPPING.value})

            # Simulate cleanup
            import asyncio
            await asyncio.sleep(2)

            # Delete from database
            success = self.repository.delete(db, cluster_id)
            if success:
                logger.info(f"Cluster {cluster_id} deleted")
            return success
        except Exception as e:
            logger.error(f"Error deleting cluster: {e}")
            raise

    async def execute_code(self, code: str, cluster_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute PySpark code on a cluster"""
        try:
            # Create temporary DB session for getting spark session
            db = SessionLocal()
            try:
                spark = self.get_spark_session(db, cluster_id)
            finally:
                db.close()

            # Create a namespace for code execution
            namespace = {
                'spark': spark,
                'sc': spark.sparkContext
            }

            # Capture output
            import io
            import sys
            from contextlib import redirect_stdout, redirect_stderr

            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()

            start_time = datetime.now()

            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                exec(code, namespace)

            execution_time = (datetime.now() - start_time).total_seconds()

            output = stdout_buffer.getvalue()
            errors = stderr_buffer.getvalue()

            return {
                "output": output or "Code executed successfully",
                "errors": errors,
                "execution_time": execution_time,
                "status": "success" if not errors else "completed_with_warnings"
            }
        except Exception as e:
            logger.error(f"Error executing code: {e}")
            return {
                "output": "",
                "errors": str(e),
                "execution_time": 0,
                "status": "failed"
            }

    def close_session(self):
        """Close Spark session"""
        if self._spark_session:
            self._spark_session.stop()
            self._spark_session = None
            logger.info("Spark session closed")


# Singleton instance
spark_service = SparkService()
