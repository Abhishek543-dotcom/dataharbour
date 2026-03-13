import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Set test environment variables before importing app
os.environ["ENABLE_RATE_LIMITING"] = "false"
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.main import app
from app.db.base import Base
from app.db.session import get_db

import sqlalchemy.dialects.sqlite.base as sqlite_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

# Patch SQLite to support UUID and JSONB since we are using PostgreSQL types in db_models
class StringUUID(sqlite_base.SQLiteTypeCompiler):
    def visit_UUID(self, type_, **kw):
        return "VARCHAR(36)"

    def visit_JSONB(self, type_, **kw):
        return "JSON"

# Overriding the SQLite dialect to handle these postgres-specific columns
sqlite_base.SQLiteTypeCompiler.visit_UUID = StringUUID.visit_UUID
sqlite_base.SQLiteTypeCompiler.visit_JSONB = StringUUID.visit_JSONB

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    """Test client for API testing"""
    # Create tables before tests
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    # Drop tables after tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_spark_session(mocker):
    """Mock Spark session for testing"""
    mock = mocker.patch('app.services.spark_service.SparkSession')
    return mock

@pytest.fixture
def sample_job_data():
    """Sample job data for testing"""
    return {
        "name": "Test Job",
        "code": "print('Hello Spark')",
        "cluster_id": "spark-cluster-default"
    }

@pytest.fixture
def sample_notebook_data():
    """Sample notebook data for testing"""
    return {
        "name": "Test Notebook",
        "description": "A test notebook"
    }

@pytest.fixture
def sample_cluster_data():
    """Sample cluster data for testing"""
    return {
        "name": "Test Cluster",
        "worker_nodes": 2,
        "cores_per_node": 2,
        "memory_per_node": "2g"
    }
