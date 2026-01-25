"""
MatruRaksha - Health Check Tests
Test health check endpoints
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_health_check_returns_200(client: TestClient):
    """Test basic health check returns 200"""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["service"] == "MatruRaksha API"


@pytest.mark.unit
def test_health_check_response_structure(client: TestClient):
    """Test health check response has correct structure"""
    response = client.get("/health")
    data = response.json()
    
    # Check required fields
    assert "status" in data
    assert "timestamp" in data
    assert "service" in data
    assert "version" in data


@pytest.mark.unit
def test_readiness_check_endpoint_exists(client: TestClient):
    """Test readiness check endpoint exists"""
    response = client.get("/health/ready")
    
    # Should return either 200 (ready) or 503 (not ready)
    assert response.status_code in [200, 503]


@pytest.mark.unit
def test_readiness_check_response_structure(client: TestClient):
    """Test readiness check has correct response structure"""
    response = client.get("/health/ready")
    data = response.json()
    
    assert "status" in data
    assert "timestamp" in data
    assert "checks" in data
    
    # Checks should include core services
    checks = data["checks"]
    assert "database" in checks


@pytest.mark.integration
def test_health_check_with_correlation_id(client: TestClient):
    """Test health check includes correlation ID"""
    correlation_id = "test-correlation-123"
    
    response = client.get(
        "/health",
        headers={"X-Correlation-ID": correlation_id}
    )
    
    # Check correlation ID in response headers
    assert "X-Correlation-ID" in response.headers
    # Should either return the same ID or generate a new one
    assert response.headers["X-Correlation-ID"]
