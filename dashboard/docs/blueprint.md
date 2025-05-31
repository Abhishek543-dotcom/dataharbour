# **App Name**: DataHarbour

## Core Features:

- Header Bar: Display platform name, logged-in user, and auto-refresh toggle in the header bar.
- Service Control Panel: Show containers (Jupyter, Spark, Airflow, PostgreSQL, MinIO, NGINX) with status, start/stop/restart controls, and CPU/Memory usage.
- Logs Viewer: Enable live tail + filter/search of logs from Loki with a service selection dropdown.
- Metrics Panel: Display CPU, RAM, Disk, Network usage metrics and Spark job performance stats using Grafana or Prometheus.
- Airflow DAG Monitor: List Airflow DAGs with their status, last run, duration, and manual trigger/pause buttons.
- Spark Job Tracker: Provide a table of recent Spark jobs (from PostgreSQL) showing status, runtime, and output path.
- MinIO File Browser: Optionally provide a MinIO file browser to navigate datasets and output files, with preview/download capabilities.
- Backup Status: Display last successful backup timestamp, next scheduled backup, and a manual restore button.
- Alert Center: List active alerts from Prometheus with severity levels and links to related logs/metrics.

## Style Guidelines:

- Use a modern, responsive design via React and Tailwind CSS.
- Maintain a centralized, secure, and user-friendly interface.