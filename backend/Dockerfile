FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    default-jdk \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app /app/app

# Copy Alembic configuration and migrations
COPY alembic.ini /app/
COPY alembic /app/alembic

# Create data directories
RUN mkdir -p /data/notebooks /data/logs

# Expose port
EXPOSE 8000

# Run the application
CMD ["sh", "-c", "echo 'Waiting for PostgreSQL...' && sleep 10 && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
