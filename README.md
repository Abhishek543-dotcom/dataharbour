# PySpark, Hive, Delta Lake, Jupyter Notebook, Airflow, PostgreSQL, and MinIO Docker Setup

This project provides a Docker-based environment for running PySpark, Hive, Delta Lake, Jupyter Notebook, Airflow, PostgreSQL, and MinIO. It is designed for data engineering and analytics workflows.

## Features
- **PySpark:** Distributed data processing with Spark.
- **Hive:** Data warehouse infrastructure built on top of Hadoop.
- **Delta Lake:** Reliable data lakes with ACID transactions.
- **Jupyter Notebook:** Interactive development environment.
- **Airflow:** Workflow orchestration and scheduling.
- **PostgreSQL:** Relational database for Airflow metadata.
- **MinIO:** S3-compatible object storage.

## Prerequisites
- Docker installed on your machine.
- Docker Compose installed.
- Basic knowledge of Docker and the tools mentioned above.

## Setup
1. **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/pyspark-hive-delta-docker.git
    cd pyspark-hive-delta-docker
    ```
2. **Build and Start the Services**
    Run the following command to build and start all services:
    ```bash
    docker-compose up --build
    ```

3. **Access the Services**
    - Jupyter Notebook: http://localhost:8888
    - Airflow: http://localhost:8080
    - pgAdmin (PostgreSQL Admin): http://localhost:5050
    - MinIO Console: http://localhost:9001

## Services Overview
1. **Spark, Jupyter, and Airflow**
    - **Spark:** Used for distributed data processing.
    - **Jupyter Notebook:** Provides an interactive environment for writing and testing PySpark code.
    - **Airflow:** Manages workflows and schedules tasks.
    
2. **PostgreSQL**
    - Acts as the backend database for Airflow.
    - Accessible via `psql` or pgAdmin.

3. **MinIO**
    - Provides S3-compatible object storage.
    - Used for storing data in Delta Lake.

## Usage
1. **Initialize Airflow Database**
    Access the spark container:
    ```bash
    docker exec -it <SPARK_CONTAINER_ID> /bin/bash
    ```
    Initialize the Airflow database:
    ```bash
    airflow db init
    ```
    Create an admin user:
    ```bash
    airflow users create \
        --username admin \
        --password admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com
    ```
2. **Access Jupyter Notebook**
    Open [http://localhost:8888](http://localhost:8888) in your browser.
    Use the token provided in the terminal logs to log in.

3. **Access Airflow**
    Open [http://localhost:8080](http://localhost:8080) in your browser.
    Log in with the credentials you created (admin:admin).

4. **Access MinIO**
    Open [http://localhost:9001](http://localhost:9001) in your browser.
    Log in with the credentials:
    - Username: `minioadmin`
    - Password: `minioadmin`

## Configuration
1. **PostgreSQL Connection**
    - Host: `postgres`
    - Port: `5432`
    - Username: `admin`
    - Password: `admin`
    - Database: `airflow`

2. **MinIO Configuration**
    - Endpoint: `http://minio:9000`
    - Access Key: `minioadmin`
    - Secret Key: `minioadmin`

3. **Airflow Configuration**
    - Database Connection: `postgresql+psycopg2://admin:admin@postgres:5432/airflow`
    - Executor: `LocalExecutor`

## Troubleshooting
1. **PostgreSQL Connection Issues**
    Ensure the postgres service is running:
    ```bash
    docker ps
    ```
    Check the logs:
    ```bash
    docker logs postgres-1
    ```

2. **Airflow Database Initialization**
    If Airflow fails to start, initialize the database manually:
    ```bash
    docker exec -it <AIRFLOW_CONTAINER_ID> /bin/bash
    airflow db init
    ```

3. **MinIO Access Issues**
    Ensure MinIO is running:
    ```bash
    docker logs minio-1
    ```
    Verify the credentials in the MinIO console.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request.

## Contact
For questions or feedback, please contact Your Name.

Enjoy using the PySpark, Hive, Delta Lake, Jupyter Notebook, Airflow, PostgreSQL, and MinIO Docker setup! 🚀