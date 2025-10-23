# DataHarbour Backend API

FastAPI-based backend for DataHarbour - A comprehensive data engineering platform that orchestrates Spark, Airflow, Jupyter, and MinIO services.

## Features

- **Spark Integration**: Submit and manage PySpark jobs, monitor Spark clusters
- **Notebook Management**: Create, execute, and manage Jupyter-style notebooks
- **Job Management**: Track job execution, view logs, restart/kill jobs
- **Cluster Management**: Create and manage Spark clusters
- **Real-time Monitoring**: System metrics, service health checks, and logs
- **WebSocket Support**: Real-time updates for jobs and metrics
- **RESTful API**: Complete REST API with OpenAPI documentation

## Architecture

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   └── websocket_manager.py  # WebSocket connection manager
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   ├── services/
│   │   ├── spark_service.py   # Spark integration
│   │   ├── job_service.py     # Job management
│   │   ├── notebook_service.py  # Notebook management
│   │   └── monitoring_service.py  # Monitoring & health checks
│   └── api/
│       └── v1/
│           └── endpoints/       # API route handlers
│               ├── dashboard.py
│               ├── jobs.py
│               ├── clusters.py
│               ├── notebooks.py
│               └── monitoring.py
├── Dockerfile
├── requirements.txt
└── .env.example
```

## API Endpoints

### Dashboard
- `GET /api/v1/dashboard/stats` - Get dashboard statistics
- `GET /api/v1/dashboard/trends` - Get job completion trends
- `GET /api/v1/dashboard/overview` - Get complete overview

### Jobs
- `GET /api/v1/jobs/` - List all jobs (with filtering)
- `GET /api/v1/jobs/{job_id}` - Get job details
- `POST /api/v1/jobs/` - Submit new job
- `POST /api/v1/jobs/{job_id}/kill` - Kill running job
- `POST /api/v1/jobs/{job_id}/restart` - Restart job
- `GET /api/v1/jobs/{job_id}/logs` - Get job logs
- `GET /api/v1/jobs/{job_id}/spark-ui` - Get Spark UI URL

### Clusters
- `GET /api/v1/clusters/` - List all clusters
- `GET /api/v1/clusters/{cluster_id}` - Get cluster details
- `POST /api/v1/clusters/` - Create new cluster
- `DELETE /api/v1/clusters/{cluster_id}` - Delete cluster

### Notebooks
- `GET /api/v1/notebooks/` - List all notebooks
- `GET /api/v1/notebooks/{notebook_id}` - Get notebook details
- `POST /api/v1/notebooks/` - Create new notebook
- `PUT /api/v1/notebooks/{notebook_id}` - Update notebook
- `DELETE /api/v1/notebooks/{notebook_id}` - Delete notebook
- `POST /api/v1/notebooks/{notebook_id}/cells` - Add cell
- `DELETE /api/v1/notebooks/{notebook_id}/cells/{cell_id}` - Delete cell
- `POST /api/v1/notebooks/{notebook_id}/cells/{cell_id}/execute` - Execute cell
- `POST /api/v1/notebooks/import` - Import notebook
- `GET /api/v1/notebooks/{notebook_id}/export` - Export notebook

### Monitoring
- `GET /api/v1/monitoring/metrics` - Get current system metrics
- `GET /api/v1/monitoring/metrics/history` - Get historical metrics
- `GET /api/v1/monitoring/services` - Get service health status
- `GET /api/v1/monitoring/services/{service_name}/logs` - Get service logs
- `GET /api/v1/monitoring/overview` - Get monitoring overview

### WebSocket
- `WS /ws/{client_id}` - WebSocket connection for real-time updates

## Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)

### Using Docker (Recommended)

1. Start the backend service:
```bash
docker-compose up -d backend
```

2. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Local Development

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Copy environment configuration:
```bash
cp .env.example .env
```

3. Edit `.env` with your configuration

4. Run the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

Environment variables (see `.env.example`):

### Spark Configuration
- `SPARK_MASTER_URL`: Spark master URL (default: `spark://spark:7077`)
- `SPARK_UI_URL`: Spark UI URL (default: `http://spark:4040`)

### Airflow Configuration
- `AIRFLOW_BASE_URL`: Airflow webserver URL
- `AIRFLOW_USERNAME`: Airflow username
- `AIRFLOW_PASSWORD`: Airflow password

### Jupyter Configuration
- `JUPYTER_BASE_URL`: Jupyter server URL
- `JUPYTER_TOKEN`: Jupyter authentication token (optional)

### Database Configuration
- `POSTGRES_HOST`: PostgreSQL host
- `POSTGRES_PORT`: PostgreSQL port
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_DB`: Database name

### MinIO Configuration
- `MINIO_ENDPOINT`: MinIO server endpoint
- `MINIO_ACCESS_KEY`: MinIO access key
- `MINIO_SECRET_KEY`: MinIO secret key
- `MINIO_BUCKET_NAME`: Default bucket name

### Security
- `SECRET_KEY`: JWT secret key (change in production!)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time

## Usage Examples

### Submit a Spark Job

```bash
curl -X POST http://localhost:8000/api/v1/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Word Count Job",
    "code": "from pyspark.sql import SparkSession\nspark = SparkSession.builder.getOrCreate()\ndf = spark.read.text(\"data.txt\")\ndf.show()",
    "cluster_id": "spark-cluster-default"
  }'
```

### Create a Notebook

```bash
curl -X POST http://localhost:8000/api/v1/notebooks/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Notebook",
    "description": "Learning PySpark"
  }'
```

### Get System Metrics

```bash
curl http://localhost:8000/api/v1/monitoring/metrics
```

### WebSocket Connection (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/client-123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'job_update') {
    console.log('Job updated:', data.data);
  }
};
```

## Development

### Project Structure

- **main.py**: FastAPI application setup, middleware, and WebSocket endpoint
- **core/**: Core functionality (config, WebSocket manager)
- **models/**: Pydantic schemas for request/response validation
- **services/**: Business logic layer
- **api/**: API route handlers

### Adding New Endpoints

1. Define Pydantic schemas in `models/schemas.py`
2. Implement business logic in `services/`
3. Create route handler in `api/v1/endpoints/`
4. Register router in `api/v1/__init__.py`

### Testing

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

## Troubleshooting

### Cannot connect to Spark
- Ensure Spark service is running: `docker-compose ps spark`
- Check Spark master URL in environment variables
- Verify network connectivity: `docker network ls`

### WebSocket connection fails
- Check CORS settings in `main.py`
- Verify WebSocket URL format: `ws://` not `http://`
- Check firewall rules for port 8000

### Job execution fails
- Check Spark logs: `docker-compose logs spark`
- Verify code syntax
- Check available resources (memory, cores)

## Production Deployment

### Security Checklist
- [ ] Change `SECRET_KEY` to a random secure value
- [ ] Update all default passwords
- [ ] Enable authentication middleware
- [ ] Configure CORS with specific origins
- [ ] Use HTTPS/WSS for production
- [ ] Set up proper logging and monitoring
- [ ] Configure rate limiting
- [ ] Enable database connection pooling

### Performance Optimization
- Use Gunicorn/Uvicorn workers: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`
- Enable response caching
- Use connection pooling for databases
- Implement request rate limiting
- Monitor resource usage

## API Documentation

Full interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests
4. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [Your Repo URL]
- Documentation: [Your Docs URL]
