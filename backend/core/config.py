import os


class Config:
    """Centralized configuration loaded from environment variables with sensible defaults."""

    # ── Spark ─────────────────────────────────────────
    spark_master_url: str = os.getenv("SPARK_MASTER_URL", "spark://spark-master:7077")
    spark_rest_url: str = os.getenv("SPARK_REST_URL", "http://spark-master:8080")
    spark_submit_url: str = os.getenv("SPARK_SUBMIT_URL", "http://spark-master:6066")

    # ── MinIO (S3-compatible) ─────────────────────────
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")

    # ── PostgreSQL ────────────────────────────────────
    postgres_host: str = os.getenv("POSTGRES_HOST", "postgres")
    postgres_port: str = os.getenv("POSTGRES_PORT", "5432")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    postgres_db: str = os.getenv("POSTGRES_DB", "dataharbour")

    # ── Filesystem Paths (shared Docker volume) ──────
    workspace_dir: str = os.getenv("WORKSPACE_DIR", "/workspace")
    jobs_dir: str = os.path.join(workspace_dir, "jobs")
    logs_dir: str = os.path.join(workspace_dir, "logs")
    notebooks_dir: str = os.path.join(workspace_dir, "notebooks")
    iceberg_warehouse: str = os.path.join(workspace_dir, "iceberg")

    # ── Application ──────────────────────────────────
    app_name: str = "DataHarbour"
    app_version: str = "2.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

