import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def _create_project_helper():
    response = client.post("/api/projects", json={
        "project_name": "API Test Project",
        "requirement": "Build a test app"
    })
    return response.json()["project_id"]

def test_create_project():
    response = client.post("/api/projects", json={
        "project_name": "API Test Project",
        "requirement": "Build a test app"
    })
    assert response.status_code == 200
    data = response.json()
    assert "project_id" in data
    assert data["status"] == "created"

def test_get_project_status():
    pid = _create_project_helper()
    response = client.get(f"/api/projects/{pid}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == pid
    assert data["workflow_status"] == "pending"

def test_start_workflow_and_get_artifacts():
    # Note: Workflow runs in background, we'll just test the endpoint returns 200
    pid = _create_project_helper()
    
    # Run
    response = client.post(f"/api/projects/{pid}/run")
    assert response.status_code == 200
    assert response.json()["status"] == "running"
    
    # Status should now be running or completed (TestClient runs background tasks inline)
    status = client.get(f"/api/projects/{pid}/status")
    assert status.json()["workflow_status"] in ["running", "completed"]
    
    # Artifacts (will be empty initially)
    artifacts = client.get(f"/api/projects/{pid}/artifacts")
    assert artifacts.status_code == 200
    assert "artifacts" in artifacts.json()

def test_path_traversal_protection():
    pid = _create_project_helper()
    # Try to access a file outside the project dir
    response = client.get(f"/api/projects/{pid}/files?path=../../../etc/passwd")
    # Our API should block this
    assert response.status_code == 403
