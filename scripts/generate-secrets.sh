#!/bin/bash

# Script to generate secure random passwords and secrets
# Usage: ./scripts/generate-secrets.sh

echo "🔐 Generating secure secrets for DataHarbour..."
echo ""

# Function to generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Function to generate random secret key
generate_secret() {
    openssl rand -hex 32
}

echo "# Auto-generated secrets - $(date)"
echo "# IMPORTANT: Keep this file secure and never commit to git!"
echo ""

echo "# PostgreSQL"
echo "POSTGRES_USER=dataharbour_admin"
echo "POSTGRES_PASSWORD=$(generate_password)"
echo ""

echo "# MinIO"
echo "MINIO_ROOT_USER=dataharbour_minio"
echo "MINIO_ROOT_PASSWORD=$(generate_password)"
echo ""

echo "# Airflow"
echo "AIRFLOW_USERNAME=dataharbour_airflow"
echo "AIRFLOW_PASSWORD=$(generate_password)"
echo "AIRFLOW__WEBSERVER__SECRET_KEY=$(generate_secret)"
echo ""

echo "# Jupyter"
echo "JUPYTER_TOKEN=$(generate_password)"
echo ""

echo "# pgAdmin"
echo "PGADMIN_DEFAULT_EMAIL=admin@dataharbour.local"
echo "PGADMIN_DEFAULT_PASSWORD=$(generate_password)"
echo ""

echo "# Backend API"
echo "BACKEND_SECRET_KEY=$(generate_secret)"
echo ""

echo ""
echo "✅ Secrets generated successfully!"
echo ""
echo "📝 To use these secrets:"
echo "   1. Copy the output above"
echo "   2. Paste into your .env file"
echo "   3. Keep .env file secure and add to .gitignore"
echo ""
echo "⚠️  NEVER commit .env to git!"
