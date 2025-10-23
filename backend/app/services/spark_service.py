import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark import SparkContext, SparkConf
import uuid

from app.core.config import settings
from app.models.schemas import Cluster, ClusterStatus, ClusterCreate

logger = logging.getLogger(__name__)


class SparkService:
    def __init__(self):
        self._spark_session: Optional[SparkSession] = None
        self._clusters: Dict[str, Cluster] = {}
        self._initialize_default_cluster()

    def _initialize_default_cluster(self):
        """Initialize default Spark cluster"""
        try:
            default_cluster = Cluster(
                id="spark-cluster-default",
                name="Default Spark Cluster",
                status=ClusterStatus.RUNNING,
                master_url=settings.SPARK_MASTER_URL,
                ui_url=settings.SPARK_UI_URL,
                worker_nodes=2,
                total_cores=4,
                total_memory="4g",
                created_at=datetime.now()
            )
            self._clusters[default_cluster.id] = default_cluster
        except Exception as e:
            logger.error(f"Error initializing default cluster: {e}")

    def get_spark_session(self, cluster_id: Optional[str] = None) -> SparkSession:
        """Get or create Spark session"""
        try:
            if self._spark_session is None:
                cluster = self._clusters.get(cluster_id or "spark-cluster-default")
                master_url = cluster.master_url if cluster else settings.SPARK_MASTER_URL

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

    async def get_clusters(self) -> List[Cluster]:
        """Get all Spark clusters"""
        return list(self._clusters.values())

    async def get_cluster(self, cluster_id: str) -> Optional[Cluster]:
        """Get specific cluster by ID"""
        return self._clusters.get(cluster_id)

    async def create_cluster(self, cluster_data: ClusterCreate) -> Cluster:
        """Create a new Spark cluster"""
        try:
            cluster_id = f"spark-cluster-{uuid.uuid4().hex[:8]}"

            # In a real implementation, this would start new Spark worker nodes
            cluster = Cluster(
                id=cluster_id,
                name=cluster_data.name,
                status=ClusterStatus.STARTING,
                master_url=settings.SPARK_MASTER_URL,
                ui_url=f"{settings.SPARK_UI_URL.replace('4040', str(4040 + len(self._clusters)))}",
                worker_nodes=cluster_data.worker_nodes,
                total_cores=cluster_data.worker_nodes * cluster_data.cores_per_node,
                total_memory=f"{cluster_data.worker_nodes * int(cluster_data.memory_per_node[:-1])}{cluster_data.memory_per_node[-1]}",
                created_at=datetime.now()
            )

            self._clusters[cluster_id] = cluster

            # Simulate cluster startup
            import asyncio
            asyncio.create_task(self._start_cluster(cluster_id))

            logger.info(f"Cluster {cluster_id} created")
            return cluster
        except Exception as e:
            logger.error(f"Error creating cluster: {e}")
            raise

    async def _start_cluster(self, cluster_id: str):
        """Simulate cluster startup"""
        import asyncio
        await asyncio.sleep(5)  # Simulate startup time

        if cluster_id in self._clusters:
            self._clusters[cluster_id].status = ClusterStatus.RUNNING
            logger.info(f"Cluster {cluster_id} is now running")

    async def delete_cluster(self, cluster_id: str) -> bool:
        """Delete a cluster"""
        try:
            if cluster_id == "spark-cluster-default":
                raise ValueError("Cannot delete default cluster")

            if cluster_id in self._clusters:
                self._clusters[cluster_id].status = ClusterStatus.STOPPING
                # Simulate cleanup
                import asyncio
                await asyncio.sleep(2)
                del self._clusters[cluster_id]
                logger.info(f"Cluster {cluster_id} deleted")
                return True

            return False
        except Exception as e:
            logger.error(f"Error deleting cluster: {e}")
            raise

    async def execute_code(self, code: str, cluster_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute PySpark code on a cluster"""
        try:
            spark = self.get_spark_session(cluster_id)

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
