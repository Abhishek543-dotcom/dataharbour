# DataHarbour API Quick Start Guide

## Getting Started

### Start the Backend

```bash
cd dataharbour
docker-compose up -d backend
```

### Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## Quick API Examples

### 1. Dashboard & Statistics

#### Get Dashboard Overview
```bash
curl http://localhost:8000/api/v1/dashboard/overview
```

**Response:**
```json
{
  "stats": {
    "total_notebooks": 5,
    "total_jobs": 12,
    "active_clusters": 1,
    "running_jobs": 2,
    "completed_jobs": 8,
    "failed_jobs": 2
  },
  "trends": {
    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "completed": [12, 19, 3, 5, 2, 3, 20],
    "failed": [1, 2, 0, 1, 0, 0, 2]
  }
}
```

---

### 2. Job Management

#### Submit a PySpark Job
```bash
curl -X POST http://localhost:8000/api/v1/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Word Count Example",
    "code": "from pyspark.sql import SparkSession\nspark = SparkSession.builder.appName(\"WordCount\").getOrCreate()\ndata = [(\"Hello\",), (\"World\",), (\"PySpark\",)]\ndf = spark.createDataFrame(data, [\"word\"])\ndf.show()\nprint(\"Job completed successfully!\")"
  }'
```

**Response:**
```json
{
  "id": "job_a1b2c3d4e5f6",
  "name": "Word Count Example",
  "status": "pending",
  "cluster": "Default Spark Cluster",
  "start_time": "2025-01-15T10:30:00",
  "spark_ui_url": "http://spark:4040/jobs/job?id=job_a1b2c3d4e5f6"
}
```

#### List All Jobs
```bash
curl http://localhost:8000/api/v1/jobs/
```

#### Filter Jobs by Status
```bash
curl "http://localhost:8000/api/v1/jobs/?status=running"
curl "http://localhost:8000/api/v1/jobs/?status=completed"
curl "http://localhost:8000/api/v1/jobs/?status=failed"
```

#### Search Jobs
```bash
curl "http://localhost:8000/api/v1/jobs/?search=word+count"
```

#### Get Job Details
```bash
curl http://localhost:8000/api/v1/jobs/job_a1b2c3d4e5f6
```

#### Get Job Logs
```bash
curl http://localhost:8000/api/v1/jobs/job_a1b2c3d4e5f6/logs
```

#### Kill a Running Job
```bash
curl -X POST http://localhost:8000/api/v1/jobs/job_a1b2c3d4e5f6/kill
```

#### Restart a Failed Job
```bash
curl -X POST http://localhost:8000/api/v1/jobs/job_a1b2c3d4e5f6/restart
```

---

### 3. Notebook Management

#### Create a Notebook
```bash
curl -X POST http://localhost:8000/api/v1/notebooks/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Analysis Notebook",
    "description": "Analyzing sales data with PySpark"
  }'
```

**Response:**
```json
{
  "id": "nb_x1y2z3a4b5c6",
  "name": "Data Analysis Notebook",
  "description": "Analyzing sales data with PySpark",
  "cells": [],
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:30:00",
  "path": "/data/notebooks/nb_x1y2z3a4b5c6.json"
}
```

#### List All Notebooks
```bash
curl http://localhost:8000/api/v1/notebooks/
```

#### Add a Cell to Notebook
```bash
curl -X POST http://localhost:8000/api/v1/notebooks/nb_x1y2z3a4b5c6/cells \
  -H "Content-Type: application/json" \
  -d '{
    "id": "cell_001",
    "cell_type": "code",
    "source": "from pyspark.sql import SparkSession\nspark = SparkSession.builder.getOrCreate()\nprint(\"Spark session created!\")"
  }'
```

#### Execute a Cell
```bash
curl -X POST http://localhost:8000/api/v1/notebooks/nb_x1y2z3a4b5c6/cells/cell_001/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello from PySpark!\")"}'
```

**Response:**
```json
{
  "output": "Hello from PySpark!\n",
  "execution_time": 0.45,
  "status": "success",
  "job_id": "job_c7d8e9f0a1b2"
}
```

#### Delete a Cell
```bash
curl -X DELETE http://localhost:8000/api/v1/notebooks/nb_x1y2z3a4b5c6/cells/cell_001
```

#### Export Notebook (Jupyter Format)
```bash
curl http://localhost:8000/api/v1/notebooks/nb_x1y2z3a4b5c6/export \
  -o my_notebook.ipynb
```

#### Import Notebook
```bash
curl -X POST http://localhost:8000/api/v1/notebooks/import \
  -F "file=@my_notebook.ipynb"
```

#### Delete Notebook
```bash
curl -X DELETE http://localhost:8000/api/v1/notebooks/nb_x1y2z3a4b5c6
```

---

### 4. Cluster Management

#### List All Clusters
```bash
curl http://localhost:8000/api/v1/clusters/
```

**Response:**
```json
[
  {
    "id": "spark-cluster-default",
    "name": "Default Spark Cluster",
    "status": "running",
    "master_url": "spark://spark:7077",
    "ui_url": "http://spark:4040",
    "worker_nodes": 2,
    "total_cores": 4,
    "total_memory": "4g",
    "created_at": "2025-01-15T09:00:00"
  }
]
```

#### Get Cluster Details
```bash
curl http://localhost:8000/api/v1/clusters/spark-cluster-default
```

#### Create New Cluster
```bash
curl -X POST http://localhost:8000/api/v1/clusters/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Large Cluster",
    "worker_nodes": 4,
    "cores_per_node": 4,
    "memory_per_node": "8g"
  }'
```

#### Delete Cluster
```bash
curl -X DELETE http://localhost:8000/api/v1/clusters/spark-cluster-abc123
```

---

### 5. Monitoring & Metrics

#### Get Current System Metrics
```bash
curl http://localhost:8000/api/v1/monitoring/metrics
```

**Response:**
```json
{
  "timestamp": "2025-01-15T10:35:00",
  "cpu_usage": 45.2,
  "memory_usage": 62.8,
  "disk_usage": 38.5,
  "network_in": 125.6,
  "network_out": 89.3
}
```

#### Get Metrics History (24 hours)
```bash
curl http://localhost:8000/api/v1/monitoring/metrics/history?hours=24
```

#### Get Service Health Status
```bash
curl http://localhost:8000/api/v1/monitoring/services
```

**Response:**
```json
[
  {
    "name": "spark",
    "status": "running",
    "uptime": "Running",
    "health_check": "healthy",
    "url": "http://spark:4040"
  },
  {
    "name": "jupyter",
    "status": "running",
    "uptime": "Running",
    "health_check": "healthy",
    "url": "http://jupyter:8888"
  }
]
```

#### Get Service Logs
```bash
# Get last 100 lines from Spark
curl http://localhost:8000/api/v1/monitoring/services/spark/logs?lines=100

# Get last 50 lines from Airflow
curl http://localhost:8000/api/v1/monitoring/services/airflow-webserver/logs?lines=50
```

#### Get Complete Monitoring Overview
```bash
curl http://localhost:8000/api/v1/monitoring/overview
```

---

### 6. WebSocket (Real-time Updates)

#### JavaScript Example
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/dashboard-client-1');

// Handle connection open
ws.onopen = () => {
  console.log('Connected to DataHarbour WebSocket');
};

// Handle incoming messages
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === 'job_update') {
    console.log('Job updated:', message.data);
    updateJobInUI(message.data);
  }
  else if (message.type === 'metrics_update') {
    console.log('Metrics updated:', message.data);
    updateMetricsChart(message.data);
  }
};

// Handle errors
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Handle connection close
ws.onclose = () => {
  console.log('Disconnected from WebSocket');
};
```

#### Python Example
```python
import asyncio
import websockets
import json

async def listen():
    uri = "ws://localhost:8000/ws/python-client-1"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data}")

asyncio.run(listen())
```

---

## Common Workflows

### Workflow 1: Submit and Monitor a Job

```bash
# 1. Submit job
JOB_ID=$(curl -s -X POST http://localhost:8000/api/v1/jobs/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Job", "code": "print(\"Hello\")"}' | jq -r '.id')

echo "Job ID: $JOB_ID"

# 2. Check job status
curl http://localhost:8000/api/v1/jobs/$JOB_ID

# 3. Get job logs
curl http://localhost:8000/api/v1/jobs/$JOB_ID/logs

# 4. If needed, kill the job
curl -X POST http://localhost:8000/api/v1/jobs/$JOB_ID/kill
```

### Workflow 2: Create and Execute Notebook

```bash
# 1. Create notebook
NOTEBOOK_ID=$(curl -s -X POST http://localhost:8000/api/v1/notebooks/ \
  -H "Content-Type: application/json" \
  -d '{"name": "My Notebook"}' | jq -r '.id')

echo "Notebook ID: $NOTEBOOK_ID"

# 2. Add a cell
curl -X POST http://localhost:8000/api/v1/notebooks/$NOTEBOOK_ID/cells \
  -H "Content-Type: application/json" \
  -d '{
    "id": "cell_1",
    "cell_type": "code",
    "source": "print(\"Hello from notebook!\")"
  }'

# 3. Execute the cell
curl -X POST http://localhost:8000/api/v1/notebooks/$NOTEBOOK_ID/cells/cell_1/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello from notebook!\")"}'

# 4. Export notebook
curl http://localhost:8000/api/v1/notebooks/$NOTEBOOK_ID/export -o notebook.ipynb
```

### Workflow 3: Monitor System Health

```bash
# Get all service statuses
curl http://localhost:8000/api/v1/monitoring/services | jq

# Check specific service
curl http://localhost:8000/api/v1/monitoring/services | jq '.[] | select(.name == "spark")'

# Get current metrics
curl http://localhost:8000/api/v1/monitoring/metrics | jq

# Get complete overview
curl http://localhost:8000/api/v1/monitoring/overview | jq
```

---

## Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Spark
SPARK_MASTER_URL=spark://spark:7077
SPARK_UI_URL=http://spark:4040

# Airflow
AIRFLOW_BASE_URL=http://airflow-webserver:8080
AIRFLOW_USERNAME=admin
AIRFLOW_PASSWORD=admin

# Jupyter
JUPYTER_BASE_URL=http://jupyter:8888

# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
POSTGRES_DB=airflow

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Security
SECRET_KEY=your-secret-key-change-in-production
```

---

## Troubleshooting

### API Returns 500 Error

**Check backend logs:**
```bash
docker-compose logs backend
```

**Restart backend:**
```bash
docker-compose restart backend
```

### Cannot Connect to Spark

**Verify Spark is running:**
```bash
docker-compose ps spark
```

**Check Spark logs:**
```bash
docker-compose logs spark
```

### Job Execution Fails

**Check job logs:**
```bash
curl http://localhost:8000/api/v1/jobs/{job_id}/logs
```

**Verify Spark cluster status:**
```bash
curl http://localhost:8000/api/v1/clusters/
```

### WebSocket Connection Issues

**Test with wscat:**
```bash
npm install -g wscat
wscat -c ws://localhost:8000/ws/test-client
```

---

## Testing Tips

### Using `httpie` (better than curl)
```bash
# Install httpie
pip install httpie

# Examples
http GET localhost:8000/api/v1/dashboard/stats
http POST localhost:8000/api/v1/jobs/ name="Test" code="print('Hello')"
```

### Using Postman

1. Import the OpenAPI spec from http://localhost:8000/docs
2. Create a Postman collection
3. Set base URL to `http://localhost:8000`
4. Start testing!

---

## Next Steps

1. ✅ Backend API is running
2. 🔄 Update frontend to use API calls (see TRACK1_IMPLEMENTATION.md)
3. 🔄 Test all endpoints
4. 🔄 Set up authentication
5. 🔄 Add monitoring and alerting

---

## Resources

- **API Documentation**: http://localhost:8000/docs
- **Backend README**: [backend/README.md](README.md)
- **Implementation Guide**: [TRACK1_IMPLEMENTATION.md](../TRACK1_IMPLEMENTATION.md)
- **GitHub**: [Your Repo URL]

Happy coding! 🚀
