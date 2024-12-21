# DataHarbour: A Data Processing Platform

DataHarbour is a data processing platform designed for efficient data transformation, analysis, and job scheduling. This document provides an overview of the project's architecture, technology stack, and structure.

## Technology Stack

DataHarbour utilizes a modern, scalable architecture leveraging a combination of open-source and cloud-based technologies:

- **Frontend:** HTML, CSS, JavaScript (with the Monaco Editor for interactive notebooks)
- **Backend:** Flask (Python) - RESTful API, notebook management, job scheduling.
- **Database:** PostgreSQL - Stores metadata, job details, execution history.
- **Big Data Processing:** Apache Spark with PySpark - Distributed data processing and analysis.
- **Storage:** MinIO (or cloud-based alternative) - Object storage for data (including Delta files).
- **Job Scheduling:** Celery with Redis - Distributed task queue for background job execution.
- **Containerization:** Docker - Consistent application packaging and execution across environments.
- **Orchestration:** Docker Compose - Manages multiple Docker services.
- **Testing:** pytest (Python) - Unit and integration testing.

## Project Structure

The project is organized into several key directories:
```plaintext
dataharbour/
├── frontend/                  // Frontend (HTML, CSS, JavaScript)
│   ├── index.html /others     // Main HTML page
│   ├── styles.css             // Main CSS stylesheet
│   ├── scripts.js             // Main JavaScript file
│   ├── monaco-editor/         // Integrated Monaco Editor (if self-hosted)
│   └── components/            // Optional: Separate JS files for better organization
│       └── editor.js          // Script for editor logic
├── backend/                   // Backend (Flask)
│   ├── app.py                 // Main Flask application
│   ├── api/                   // API endpoints (Flask blueprints)
│   │   ├── workspace.py       // API endpoints for workspace
│   │   ├── compute.py         // API endpoints for compute
│   │   ├── workflows.py       // API endpoints for workflows
│   │   └── __init__.py        // Blueprint initialization
│   ├── notebooks/             // Notebook handling logic
│   │   └── notebook_handler.py// Notebook management code
│   ├── jobs/                  // Job scheduling logic (Celery)
│   │   ├── job_worker.py      // Celery task worker
│   │   ├── celeryconfig.py    // Celery configuration
│   │   └── __init__.py        // Job scheduling init
│   ├── extensions/            // Flask extensions (e.g., authentication, database)
│   │   ├── auth.py            // Authentication logic
│   │   ├── db.py              // Database initialization
│   │   └── __init__.py        // Extensions init
│   ├── config.py              // Flask configuration
│   ├── logging_config.py      // Centralized logging configuration
│   └── tests/                 // Testing folder for backend
│       ├── test_api.py        // API unit tests
│       ├── test_jobs.py       // Job scheduling tests
│       └── test_db.py         // Database tests
├── spark/                     // Spark (PySpark) code
│   ├── transformations.py     // Data transformation scripts
│   ├── analysis.py            // Data analysis scripts
│   └── README.md              // Documentation for Spark scripts
├── minio/                     // MinIO configuration (if not using cloud MinIO)
│   └── config.json            // MinIO configuration file
├── postgresql/                // PostgreSQL schema and scripts
│   ├── schema.sql             // Database schema
│   └── seed_data.sql          // Optional: Initial data for testing
├── docker/                    // Dockerfiles and Compose file
│   ├── Dockerfile.frontend    // For frontend
│   ├── Dockerfile.backend     // For backend
│   ├── Dockerfile.spark       // For Spark
│   ├── Dockerfile.minio       // For MinIO
│   ├── Dockerfile.postgres    // For PostgreSQL
│   ├── Dockerfile.redis       // For Redis
│   └── docker-compose.yml     // Orchestration
├── .github/                   // GitHub Actions for CI/CD
│   └── workflows/
│       └── ci_cd.yml          // Workflow for CI/CD
├── tests/                     // Root folder for testing
│   ├── test_frontend.py       // Frontend unit tests (if required)
│   ├── test_integration.py    // Integration tests
│   └── test_system.py         // System-level tests
├── requirements.txt           // Project dependencies
├── README.md                  // Project overview and setup instructions
└── .env.example               // Example environment variables for the project

```
## Detailed Folder Instructions:

**frontend/**: Contains all the client-side code responsible for the user interface. The `components` folder is optional but recommended for larger projects to separate UI components. If using a CDN for Monaco, remove the `monaco-editor` folder and include the CDN links directly in `index.html`.

**backend/**: This directory houses the Flask-based backend API. Each subdirectory handles a specific aspect of the application's backend logic. Note that the `tests` subdirectory under `backend` contains unit tests for the backend components.

**spark/**: This folder contains PySpark scripts for data transformations and analysis. The `README.md` file should document the scripts' functionality and usage.

**minio/**: If you're self-hosting MinIO, this directory should contain the configuration files. If you are using a cloud-based MinIO service, this folder can be omitted.

**postgresql/**: This contains SQL scripts for setting up the PostgreSQL database schema and optionally populating it with initial data.

**docker/**: This folder contains the Dockerfiles required to create Docker images for each service and the `docker-compose.yml` file to orchestrate them.

**.github/workflows**: This folder contains the configuration files for GitHub Actions CI/CD pipeline.

**tests/**: Contains integration and system tests that cover the interactions between multiple components.

**requirements.txt**: List all the necessary Python packages for the backend and Spark.

**.env.example**: Provides examples of environment variables (database credentials, API keys). **Create a `.env` file based on this example, but never commit the actual `.env` file to version control.**

## Getting Started

1. **Clone the repository:** `git clone [repository URL]`
2. **Create a virtual environment:** `python3 -m venv venv`
3. **Activate the virtual environment:** `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows)
4. **Install dependencies:** `pip install -r requirements.txt`
5. **Set up the database:** Create the PostgreSQL database and run `schema.sql` and `seed_data.sql` (if applicable).
6. **Configure environment variables:** Create a `.env` file based on `.env.example`, filling in the appropriate values.
7. **Run Docker Compose:** `docker-compose up -d`
8. **(Optional) Run tests:** `pytest`

This README provides a high-level overview. Each subdirectory may have its own `README.md` file with more specific instructions. Remember to carefully review the Dockerfile instructions and the configuration files for each service. Always start with a small set of core features and progressively expand your functionality.
