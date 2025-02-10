#!/bin/bash

# Create Hive directories
mkdir -p /data/warehouse /data/metastore_db

# Initialize Hive metastore if empty
if [ -z "$(ls -A /data/metastore_db)" ]; then
    echo "Initializing Hive metastore..."
    $SPARK_HOME/bin/schematool -dbType derby -initSchema
fi

# Initialize MinIO (if not already initialized)
if [ ! -f /data/minio/config/config.json ]; then
    echo "Initializing MinIO..."
    mkdir -p /data/minio/data /data/minio/config
    minio server /data/minio/data --console-address ":9001" &
fi

# Initialize Airflow
if [ ! -f /data/airflow/airflow.db ]; then
    echo "Initializing Airflow..."
    mkdir -p /data/airflow
    export AIRFLOW_HOME=/data/airflow
    airflow db init
    airflow users create \
        --username admin \
        --password admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com
fi

# Start Airflow scheduler and webserver
export AIRFLOW_HOME=/data/airflow
airflow scheduler &
airflow webserver &

# Start Jupyter Notebook
jupyter notebook \
  --ip=0.0.0.0 \
  --port=8888 \
  --no-browser \
  --allow-root \
  --NotebookApp.token='' \
  --NotebookApp.password=''