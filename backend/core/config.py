import os

class Config:
    spark_master_url = os.getenv("SPARK_MASTER_URL", "spark://spark-master:7077")
    spark_rest_url = os.getenv("SPARK_REST_URL", "http://spark-master:8080")  # Web UI for JSON API
    spark_submit_url = os.getenv("SPARK_SUBMIT_URL", "http://spark-master:6066")  # Livy or custom REST wrapper (NOT built-in Spark)
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    postgres_host = os.getenv("POSTGRES_HOST", "postgres")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    postgres_user = os.getenv("POSTGRES_USER", "postgres")
    postgres_db = os.getenv("POSTGRES_DB", "postgres")