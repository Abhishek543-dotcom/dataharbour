# DataHarbour

A lightweight, containerized data engineering platform with a comprehensive REST API for local development.

## ✨ Overview

DataHarbour provides a powerful and effective environment for developing and running data processing jobs. It uses Docker Compose to orchestrate a stack of essential data engineering tools, including Apache Spark for processing, a FastAPI backend for job management, MinIO for object storage, and PostgreSQL for relational data.

The core of the platform is its comprehensive REST API, which allows for programmatic management of the entire data lifecycle—from data storage and cataloging to job execution and monitoring. This makes it an ideal environment for data engineers and developers who need a local, reproducible, and API-driven setup to build and test data pipelines and applications.

## 🏗️ Project Structure

```
dataharbour/
├── backend/                # FastAPI Backend
│   ├── api/
│   ├── core/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── spark/                  # Spark Docker build context
│   ├── Dockerfile
│   └── spark-defaults.conf
├── workspace/              # Shared volume for data and jobs
│   ├── data/               # MinIO storage bucket
│   ├── jobs/               # Your Spark job scripts
│   └── notebooks/          # Jupyter notebooks
├── .env.example            # Environment variable template
├── docker-compose.yml      # Docker Compose configuration
├── test_apis.py           # Comprehensive API test script
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- A tool to make API requests, like `curl` or Postman.

### 1. Configure Environment

First, create a `.env` file from the example template. This will store your credentials.

```bash
cp .env.example .env
```

You can leave the default values for a quick start, but it's recommended to change the passwords for any real work.

### 2. Start the Platform

Launch all services using Docker Compose.

```bash
docker-compose up -d
```

The services will start in the background. You can check their status with `docker-compose ps`.

### 3. Verify Deployment

Check that the FastAPI backend is running and explore the API documentation:

```
Navigate to http://localhost:8000/docs in your browser.
```

This will open the interactive Swagger UI, where you can see all available endpoints and try them out directly.

## 🧪 Testing the APIs

DataHarbour includes a comprehensive test script to verify that all API endpoints are working correctly.

### Run the API Test Suite

After starting the services, run the test script:

```bash
python3 test_apis.py
```

Or make it executable and run directly:

```bash
chmod +x test_apis.py
./test_apis.py
```

The script will:
- Check if the API service is running
- Test all endpoints systematically
- Report which endpoints are working (PASS), failing (FAIL), or skipped (SKIP)
- Provide a detailed summary at the end

### Test Results Interpretation

- **✅ PASS**: Endpoint is working correctly
- **❌ FAIL**: Endpoint returned an error or is not accessible
- **⏭️ SKIP**: Test was skipped (e.g., due to missing dependencies or prerequisites)

### Custom Base URL

If your API is running on a different URL, you can specify it:

```bash
python3 test_apis.py http://localhost:8080
```

## 🌐 Accessing Services

Once running, you can access the following services:

- **FastAPI Backend**: http://localhost:8000
  - API Documentation: http://localhost:8000/docs
  - Alternative Docs: http://localhost:8000/redoc

- **MinIO Console**: http://localhost:9000
  - Default credentials: minioadmin / minioadmin

- **Spark Master UI**: http://localhost:8080

- **PostgreSQL**: localhost:5432
  - Default credentials: postgres / postgres

## 🛑 Stopping the Platform

To stop all services:

```bash
docker-compose down
```

To stop and remove all data volumes:

```bash
docker-compose down -v
```

## 📚 API Endpoints

The FastAPI backend provides endpoints for:

- **Storage Management**: Create buckets, upload/download files in MinIO
- **Database Management**: Create/delete PostgreSQL databases and tables
- **Job Submission**: Upload and manage Spark jobs
- **Notebook Management**: CRUD operations and execution for Jupyter notebooks
- **Data Catalog**: Browse PostgreSQL and Iceberg table metadata
- **Cluster Monitoring**: Real-time Spark cluster status
- **Dashboard Stats**: Summary statistics for monitoring UI

## 🔧 Development

### Adding New Endpoints

1. Add your endpoint logic in `backend/api/routes.py`
2. Update the test script in `test_apis.py` to include tests for new endpoints
3. Rebuild the backend: `docker-compose build backend`

### Modifying Spark Configuration

Edit `spark/spark-defaults.conf` and rebuild the Spark images:

```bash
docker-compose build spark-master spark-worker
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite: `python3 test_apis.py`
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.