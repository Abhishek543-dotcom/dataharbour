import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_get_dashboard_stats(client: TestClient):
    """Test dashboard statistics endpoint"""
    response = client.get("/api/v1/dashboard/stats")

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    assert "total_notebooks" in data
    assert "total_jobs" in data
    assert "active_clusters" in data
    assert "running_jobs" in data
    assert "completed_jobs" in data
    assert "failed_jobs" in data

    # Check data types
    assert isinstance(data["total_notebooks"], int)
    assert isinstance(data["total_jobs"], int)


@pytest.mark.unit
def test_get_dashboard_trends(client: TestClient):
    """Test dashboard trends endpoint"""
    response = client.get("/api/v1/dashboard/trends")

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    assert "labels" in data
    assert "completed" in data
    assert "failed" in data

    # Check data types
    assert isinstance(data["labels"], list)
    assert isinstance(data["completed"], list)
    assert isinstance(data["failed"], list)

    # Check array lengths match
    assert len(data["labels"]) == len(data["completed"])
    assert len(data["labels"]) == len(data["failed"])


@pytest.mark.unit
def test_get_dashboard_overview(client: TestClient):
    """Test dashboard overview endpoint"""
    response = client.get("/api/v1/dashboard/overview")

    assert response.status_code == 200
    data = response.json()

    # Check required sections
    assert "stats" in data
    assert "trends" in data
    assert "timestamp" in data
