<h1 align="center">
  DataHarbour
</h1>

<p align="center">
  A lightweight, containerized data engineering platform with a comprehensive REST API for local development.
</p>

## ✨ Overview

DataHarbour provides a powerful and effective environment for developing and running data processing jobs. It uses Docker Compose to orchestrate a stack of essential data engineering tools, including Apache Spark for processing, a FastAPI backend for job management, MinIO for object storage, and PostgreSQL for relational data.

The core of the platform is its comprehensive REST API, which allows for programmatic management of the entire data lifecycle—from data storage and cataloging to job execution and monitoring. This makes it an ideal environment for data engineers and developers who need a local, reproducible, and API-driven setup to build and test data pipelines and applications.

##  Core Components

- **🚀 FastAPI Backend**: A rich Python-based API to manage the entire platform.
- **🔥 Apache Spark**: A standalone Spark cluster (Master + Worker) for distributed data processing.
- **💾 MinIO**: An S3-compatible object storage service, perfect for a data lake setup.
- **🐘 PostgreSQL**: A powerful open-source relational database.
- **🐳 Docker Compose**: For easy, one-command setup and teardown of the entire environment.

## ⚡ API Capabilities

The FastAPI backend provides a powerful interface to control all aspects of the platform. Key features include:

-   **Storage Management**: Create, delete, and manage buckets and files in **MinIO**.
-   **Database Management**: Programmatically create and delete **PostgreSQL** databases and tables.
-   **Job Submission**: Upload and execute **Spark jobs**.
-   **Notebook Management**: Full CRUD (Create, Read, Update, Delete) and execution for **Jupyter Notebooks**.
-   **Data Catalog**: Inspect PostgreSQL databases, tables, and **Apache Iceberg** table metadata.
-   **Cluster Monitoring**: Get real-time status of the **Spark cluster**, including workers and applications.
-   **Dashboard Endpoints**: Get aggregated stats perfect for a monitoring UI.

**Explore all endpoints interactively via the [Swagger UI](http://localhost:8000/docs).**

## 🏗️ Project Structure

```
dataharbour/
├── backend/                # FastAPI Backend
│   ├── api/
│   ├── core/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
│
├── spark/                  # Spark Docker build context
│   ├── Dockerfile
│   └── spark-defaults.conf
│
├── workspace/              # Shared volume for data and jobs
│   ├── data/               # MinIO storage bucket
│   ├── jobs/               # Your Spark job scripts
│   └── notebooks/          # Jupyter notebooks
│
├── .env.example            # Environment variable template
├── docker-compose.yml      # Docker Compose configuration
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

## 🌐 Accessing Services

| Service | URL | Description |
| :--- | :--- | :--- |
| **FastAPI Docs** | http://localhost:8000/docs | Interactive API documentation (Swagger UI). |
| **Spark Master UI** | http://localhost:8080/ | Monitor Spark cluster and jobs. |
| **MinIO Console** | http://localhost:9000 | Manage data in object storage. |
| **PostgreSQL Port** | `localhost:5432` | Connect via a database client. |

Use the credentials from your `.env` file to log into MinIO and connect to PostgreSQL.

## 💻 How to Use

The primary way to interact with DataHarbour is through its REST API.

1.  **Open the [FastAPI Docs](http://localhost:8000/docs)** in your browser.
2.  **Explore the endpoints** for managing files, databases, notebooks, and jobs.
3.  **Use the "Try it out"** button on any endpoint to send requests directly from your browser.

For example, to submit a Spark job:
1.  Place your job script (e.g., `my_job.py`) in the `./workspace/jobs/` directory.
2.  Use the `/jobs/submit` endpoint in the Swagger UI to upload and run the script.

## ⚙️ Configuration

-   **Spark settings** can be modified in `spark/spark-defaults.conf`.
-   **Backend dependencies** are managed in `backend/requirements.txt`.
-   **Environment variables** for all services are controlled in the `.env` file.

## 🧹 Cleanup

To stop and remove all running containers, networks, and volumes:

```bash
docker-compose down -v
```
