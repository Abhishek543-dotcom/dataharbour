# DataHarbour

This project provides a Docker-based environment for running PySpark, Hive, Delta Lake, Jupyter Notebook, Airflow, PostgreSQL, and MinIO. It is designed for data engineering and analytics workflows.

## Features
- **PySpark:** Distributed data processing with Spark
- **Hive:** Data warehouse infrastructure built on top of Hadoop
- **Delta Lake:** Reliable data lakes with ACID transactions
- **Jupyter Notebook:** Interactive development environment
- **Airflow:** Workflow orchestration and scheduling
- **PostgreSQL:** Relational database for Airflow metadata
- **MinIO:** S3-compatible object storage
- **Service Dashboard:** Real-time monitoring and management interface for all services

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

### 7. Service Dashboard
- **URL:** http://localhost:5000
- **Features:**
  - Real-time monitoring of all services
  - View container status and health
  - Monitor CPU and memory usage
  - View container logs
  - Service management capabilities

To enable the dashboard, first build and run the dashboard service:

```bash
cd dashboard
docker build -t dataharbour-dashboard .
docker run -d \
  -p 5000:5000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --name dataharbour-dashboard \
  dataharbour-dashboard
```

The dashboard provides:
- **Service Overview:**
  - Status of all running containers
  - Real-time CPU and memory usage
  - Port mappings
  - Container health status

- **Monitoring:**
  - CPU usage graphs
  - Memory consumption
  - Container uptime
  - Service state (running/stopped)

- **Logs:**
  - Real-time log viewing
  - Last 10 log entries per container
  - Auto-refresh every 5 seconds

- **Service Management:**
  - View all running services
  - Monitor resource usage
  - Check service health
  - View service logs in real-time

To add the dashboard service to your existing setup, add the following to your `docker-compose.yml`:

```yaml
  dashboard:
    build: ./dashboard
    ports:
      - "5000:5000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      - spark
      - jupyter
      - postgres
      - minio
      - airflow-webserver
```

Note: The dashboard requires access to the Docker socket to monitor containers. Make sure the proper permissions are set up for security.

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

<header className="flex items-center p-4 border-b">
  {/* Logo SVG */}
  <span className="mr-2 flex items-center">
    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-ship h-7 w-7 mr-2 text-primary">
      <path d="M12 10.189V14"></path>
      <path d="M12 2v3"></path>
      <path d="M19 13V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v6"></path>
      <path d="M19.38 20A11.6 11.6 0 0 0 21 14l-8.188-3.639a2 2 0 0 0-1.624 0L3 14a11.6 11.6 0 0 0 2.81 7.76"></path>
      <path d="M2 21c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1s1.2 1 2.5 1c2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"></path>
    </svg>
    <span className="text-xl font-bold">DataHarbour</span>
  </span>
</header>