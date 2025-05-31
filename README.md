# PySpark, Hive, Delta Lake, Jupyter Notebook, Airflow, PostgreSQL, and MinIO Docker Setup

This project provides a Docker-based environment for running PySpark, Hive, Delta Lake, Jupyter Notebook, Airflow, PostgreSQL, and MinIO. It is designed for data engineering and analytics workflows.

## Features
- **PySpark:** Distributed data processing with Spark
- **Hive:** Data warehouse infrastructure built on top of Hadoop
- **Delta Lake:** Reliable data lakes with ACID transactions
- **Jupyter Notebook:** Interactive development environment
- **Airflow:** Workflow orchestration and scheduling
- **PostgreSQL:** Relational database for Airflow metadata
- **MinIO:** S3-compatible object storage

## Prerequisites
- Docker installed on your machine
- Docker Compose installed
- Basic knowledge of Docker and the tools mentioned above

## Setup
1. **Clone the Repository**
    ```bash
    git clone https://github.com/Abhishek543-dotcom/dataharbour.git
    cd dataharbour
    ```

2. **Build and Start the Services**
    ```bash
    docker-compose up --build
    ```

## Accessing Services

### 1. Spark UI
- **URL:** http://localhost:4040
- Available when Spark jobs are running

### 2. Jupyter Notebook
- **URL:** http://localhost:8888
- Use the token from the container logs to login
- To get the token:
    ```bash
    docker logs dataharbour-jupyter-1
    ```

### 3. Airflow
- **URL:** http://localhost:8081
- **Default credentials:**
  - Username: admin
  - Password: admin
- Initialize the database before first use:
    ```bash
    docker exec -it dataharbour-airflow-webserver-1 airflow db init
    docker exec -it dataharbour-airflow-webserver-1 airflow users create \
        --username admin \
        --password admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com
    ```

### 4. PostgreSQL
- **Host:** localhost
- **Port:** 5432
- **Credentials:**
  - Username: admin
  - Password: admin
  - Database: airflow

### 5. pgAdmin
- **URL:** http://localhost:5050
- **Login credentials:**
  - Email: admin@example.com
  - Password: admin
- To connect to PostgreSQL:
  - Host: postgres
  - Port: 5432
  - Username: admin
  - Password: admin

### 6. MinIO
- **API URL:** http://localhost:9000
- **Console URL:** http://localhost:9001
- **Credentials:**
  - Username: minioadmin
  - Password: minioadmin

## Service Configurations

### PostgreSQL Connection Details
```python
{
    'host': 'postgres',
    'port': 5432,
    'database': 'airflow',
    'username': 'admin',
    'password': 'admin'
}
```

### MinIO Connection Details
```python
{
    'endpoint': 'http://minio:9000',
    'access_key': 'minioadmin',
    'secret_key': 'minioadmin'
}
```

### Airflow Connection String
```
postgresql+psycopg2://admin:admin@postgres:5432/airflow
```

## Troubleshooting

### Check Service Status
```bash
docker-compose ps
```

### View Service Logs
```bash
# Spark logs
docker logs dataharbour-spark-1

# Jupyter logs
docker logs dataharbour-jupyter-1

# Airflow webserver logs
docker logs dataharbour-airflow-webserver-1

# PostgreSQL logs
docker logs dataharbour-postgres-1

# MinIO logs
docker logs dataharbour-minio-1
```

### Common Issues

1. **Service Won't Start**
   - Check if ports are already in use
   - Verify docker-compose.yml configuration
   - Check service logs for errors

2. **Cannot Connect to Services**
   - Ensure all services are running
   - Verify you're using correct ports
   - Check if firewalls are blocking connections

3. **Container Volume Issues**
   - Check folder permissions
   - Verify volume paths in docker-compose.yml

## Data Persistence
All data is persisted in the following directories:
- Spark data: `./data/spark`
- Jupyter notebooks: `./data/jupyter`
- PostgreSQL data: `./data/postgres`
- MinIO data: `./data/minio/data`
- Airflow DAGs: `./data/airflow/dags`

## License
This project is licensed under the MIT License.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request.