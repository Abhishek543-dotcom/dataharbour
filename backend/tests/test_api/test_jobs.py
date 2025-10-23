import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_create_job(client: TestClient, sample_job_data):
    """Test job creation"""
    response = client.post("/api/v1/jobs/", json=sample_job_data)

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    assert "id" in data
    assert "name" in data
    assert "status" in data
    assert data["name"] == sample_job_data["name"]


@pytest.mark.unit
def test_get_all_jobs(client: TestClient):
    """Test getting all jobs"""
    response = client.get("/api/v1/jobs/")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)


@pytest.mark.unit
def test_get_job_details(client: TestClient, sample_job_data):
    """Test getting job details"""
    # Create a job first
    create_response = client.post("/api/v1/jobs/", json=sample_job_data)
    job_id = create_response.json()["id"]

    # Get job details
    response = client.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == job_id
    assert "logs" in data or "status" in data


@pytest.mark.unit
def test_get_nonexistent_job(client: TestClient):
    """Test getting non-existent job"""
    response = client.get("/api/v1/jobs/nonexistent-job-id")

    assert response.status_code == 404


@pytest.mark.unit
def test_filter_jobs_by_status(client: TestClient):
    """Test filtering jobs by status"""
    response = client.get("/api/v1/jobs/?status=completed")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # All returned jobs should have completed status
    for job in data:
        assert job["status"] == "completed"


@pytest.mark.integration
@pytest.mark.slow
def test_kill_running_job(client: TestClient, sample_job_data):
    """Test killing a running job"""
    # Create a job
    create_response = client.post("/api/v1/jobs/", json=sample_job_data)
    job_id = create_response.json()["id"]

    # Try to kill it
    response = client.post(f"/api/v1/jobs/{job_id}/kill")

    # Should succeed or fail depending on job state
    assert response.status_code in [200, 400, 404]


@pytest.mark.unit
def test_create_job_invalid_data(client: TestClient):
    """Test creating job with invalid data"""
    invalid_data = {
        "name": "",  # Empty name
        "code": "print('test')"
    }

    response = client.post("/api/v1/jobs/", json=invalid_data)

    # Should return validation error
    assert response.status_code in [400, 422]
