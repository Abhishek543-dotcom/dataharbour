import logging
from typing import List, Dict
from datetime import datetime
import psutil
import docker
from docker.errors import DockerException

from app.models.schemas import SystemMetrics, ServiceHealth, ServiceStatus, ServiceLog
from app.core.config import settings

logger = logging.getLogger(__name__)


class MonitoringService:
    def __init__(self):
        try:
            self.docker_client = docker.from_env()
        except DockerException as e:
            logger.warning(f"Could not connect to Docker: {e}")
            self.docker_client = None

    async def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            net_io = psutil.net_io_counters()

            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_in=net_io.bytes_recv / (1024 ** 2),  # MB
                network_out=net_io.bytes_sent / (1024 ** 2)  # MB
            )
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            raise

    async def get_metrics_history(self, hours: int = 24) -> List[SystemMetrics]:
        """Get historical metrics (simulated for now)"""
        # In a real implementation, this would fetch from a time-series database
        metrics = []
        import random

        for i in range(hours):
            metrics.append(SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=random.uniform(20, 80),
                memory_usage=random.uniform(30, 70),
                disk_usage=random.uniform(40, 60),
                network_in=random.uniform(10, 100),
                network_out=random.uniform(5, 50)
            ))

        return metrics

    async def get_service_health(self) -> List[ServiceHealth]:
        """Get health status of all services"""
        services = []

        # Define expected services
        service_configs = [
            {"name": "spark", "port": 4040, "url": "http://spark:4040"},
            {"name": "jupyter", "port": 8888, "url": "http://jupyter:8888"},
            {"name": "airflow-webserver", "port": 8080, "url": "http://airflow-webserver:8080"},
            {"name": "postgres", "port": 5432, "url": "postgresql://postgres:5432"},
            {"name": "minio", "port": 9000, "url": "http://minio:9000"},
            {"name": "pgadmin", "port": 80, "url": "http://pgadmin:80"},
        ]

        if self.docker_client:
            try:
                containers = self.docker_client.containers.list(all=True)

                for service_config in service_configs:
                    # Find matching container
                    container = next(
                        (c for c in containers if service_config["name"] in c.name),
                        None
                    )

                    if container:
                        status = ServiceStatus.RUNNING if container.status == "running" else ServiceStatus.STOPPED

                        # Calculate uptime if running
                        uptime = None
                        if status == ServiceStatus.RUNNING:
                            started_at = container.attrs.get("State", {}).get("StartedAt")
                            if started_at:
                                # Parse and calculate uptime
                                uptime = "Running"

                        services.append(ServiceHealth(
                            name=service_config["name"],
                            status=status,
                            uptime=uptime,
                            health_check="healthy" if status == ServiceStatus.RUNNING else "unhealthy",
                            url=service_config["url"]
                        ))
                    else:
                        services.append(ServiceHealth(
                            name=service_config["name"],
                            status=ServiceStatus.STOPPED,
                            uptime=None,
                            health_check="not found",
                            url=service_config["url"]
                        ))

            except Exception as e:
                logger.error(f"Error getting service health from Docker: {e}")
        else:
            # Fallback: return mock data if Docker is not available
            for service_config in service_configs:
                services.append(ServiceHealth(
                    name=service_config["name"],
                    status=ServiceStatus.RUNNING,
                    uptime="Running",
                    health_check="healthy",
                    url=service_config["url"]
                ))

        return services

    async def get_service_logs(self, service_name: str, lines: int = 100) -> List[ServiceLog]:
        """Get logs from a specific service"""
        logs = []

        if self.docker_client:
            try:
                containers = self.docker_client.containers.list(all=True)
                container = next(
                    (c for c in containers if service_name in c.name),
                    None
                )

                if container:
                    log_lines = container.logs(tail=lines, timestamps=True).decode('utf-8').split('\n')

                    for line in log_lines:
                        if line.strip():
                            # Parse timestamp and message
                            parts = line.split(' ', 1)
                            if len(parts) == 2:
                                timestamp_str, message = parts
                                try:
                                    # Parse Docker timestamp format
                                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                except:
                                    timestamp = datetime.now()

                                # Determine log level
                                level = "INFO"
                                if "ERROR" in message or "Error" in message:
                                    level = "ERROR"
                                elif "WARN" in message or "Warning" in message:
                                    level = "WARN"
                                elif "DEBUG" in message:
                                    level = "DEBUG"

                                logs.append(ServiceLog(
                                    timestamp=timestamp,
                                    level=level,
                                    message=message.strip()
                                ))

            except Exception as e:
                logger.error(f"Error getting logs for service {service_name}: {e}")
        else:
            # Return mock logs if Docker is not available
            for i in range(10):
                logs.append(ServiceLog(
                    timestamp=datetime.now(),
                    level="INFO",
                    message=f"[{service_name}] Service is running normally"
                ))

        return logs


# Singleton instance
monitoring_service = MonitoringService()
