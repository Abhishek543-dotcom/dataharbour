from pydantic_settings import BaseSettings
from typing import Optional
import os
import secrets


class Settings(BaseSettings):
    PROJECT_NAME: str = "DataHarbour API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Spark Configuration
    SPARK_MASTER_URL: str = "spark://spark:7077"
    SPARK_UI_URL: str = "http://spark:4040"

    # Airflow Configuration
    AIRFLOW_BASE_URL: str = "http://airflow-webserver:8080"
    AIRFLOW_USERNAME: str = os.getenv("AIRFLOW_USERNAME", "admin")
    AIRFLOW_PASSWORD: str = os.getenv("AIRFLOW_PASSWORD", "CHANGE_ME")

    # Jupyter Configuration
    JUPYTER_BASE_URL: str = "http://jupyter:8888"
    JUPYTER_TOKEN: Optional[str] = os.getenv("JUPYTER_TOKEN")

    # PostgreSQL Configuration
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "CHANGE_ME")
    POSTGRES_DB: str = "airflow"

    # MinIO Configuration
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ROOT_USER", "CHANGE_ME")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_ROOT_PASSWORD", "CHANGE_ME")
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "dataharbour"

    # Security
    SECRET_KEY: str = os.getenv("BACKEND_SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_KEY: Optional[str] = os.getenv("API_KEY")

    # Docker
    DOCKER_HOST: str = "unix:///var/run/docker.sock"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_AUDIT_LOG: bool = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"

    # CORS
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5000")

    class Config:
        case_sensitive = True
        env_file = ".env"

    def validate_security(self):
        """Validate that security settings are properly configured"""
        if self.ENVIRONMENT == "production":
            warnings = []

            if self.SECRET_KEY == "your-secret-key-change-in-production":
                warnings.append("SECRET_KEY is using default value!")

            if self.POSTGRES_PASSWORD in ["admin", "CHANGE_ME"]:
                warnings.append("POSTGRES_PASSWORD is using weak/default value!")

            if self.MINIO_SECRET_KEY in ["minioadmin", "CHANGE_ME"]:
                warnings.append("MINIO_SECRET_KEY is using weak/default value!")

            if self.AIRFLOW_PASSWORD in ["admin", "CHANGE_ME"]:
                warnings.append("AIRFLOW_PASSWORD is using weak/default value!")

            if warnings:
                warning_msg = "\n".join(f"⚠️  {w}" for w in warnings)
                print(f"\n🔴 SECURITY WARNINGS:\n{warning_msg}\n")
                print("🔒 Please update these values in your .env file before production deployment!\n")


settings = Settings()

# Validate security on startup
if settings.ENVIRONMENT == "production":
    settings.validate_security()


def get_settings() -> Settings:
    """Get settings instance"""
    return settings
