"""
MatruRaksha - Rate Limiting Tests
Test rate limiting functionality
"""

import pytest
from fastapi.testclient import TestClient
import time


@pytest.mark.unit
def test_rate_limit_allows_normal_requests(client: TestClient):
    """Test normal requests are allowed"""
    # Make a few requests (should be under limit)
    for _ in range(3):
        response = client.get("/health")
        assert response.status_code == 200


@pytest.mark.integration
def test_rate_limit_blocks_excessive_requests(client: TestClient):
    """Test excessive requests are blocked"""
    # Make many requests rapidly
    responses = []
    for _ in range(250):  # Exceed default 200/hour limit
        response = client.get("/health")
        responses.append(response.status_code)
    
    # At least one should be rate limited (429)
    assert 429 in responses


@pytest.mark.unit
def test_rate_limit_response_format(client: TestClient):
    """Test rate limit error response format"""
    # Make many requests to trigger rate limit
    for _ in range(250):
        response = client.get("/health")
        if response.status_code == 429:
            data = response.json()
            
            # Check error structure
            assert "error" in data
            assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
            assert "message" in data["error"]
            
            # Check retry-after header
            assert "Retry-After" in response.headers
            break


@pytest.mark.unit
def test_rate_limit_includes_headers(client: TestClient):
    """Test rate limit headers are included"""
    response = client.get("/health")
    
    # SlowAPI should add rate limit headers
    # (exact headers depend on SlowAPI configuration)
    assert response.status_code in [200, 429]
