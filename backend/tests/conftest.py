import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for API testing"""
    return TestClient(app)


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
