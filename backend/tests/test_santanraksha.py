
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from main import app
from routes import santanraksha

client = TestClient(app)

MOCK_CHILD_ID = "test-child-id"

@pytest.fixture
def mock_supabase():
    with patch("routes.santanraksha.supabase") as mock:
        yield mock

@pytest.fixture
def mock_cache():
    with patch("routes.santanraksha.cache") as mock:
        mock.get.return_value = None
        yield mock

@pytest.fixture
def mock_access_control():
    # Mock the verify_child_access dependency
    with patch("routes.santanraksha.verify_child_access") as mock:
        mock.return_value = True
        yield mock

def test_get_standard_schedule(mock_cache):
    response = client.get("/api/santanraksha/vaccination/schedule/standard")
    assert response.status_code == 200
    data = response.json()
    assert "schedule" in data
    assert len(data["schedule"]) > 0
    assert data["source"] == "India NIS (National Immunization Schedule)"

def test_get_child_vaccinations(mock_supabase, mock_cache, mock_access_control):
    # Setup mock
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
        {"id": "1", "vaccine_name": "BCG", "status": "completed"}
    ]
    
    response = client.get(f"/api/santanraksha/vaccination/{MOCK_CHILD_ID}", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 200
    data = response.json()
    assert data["child_id"] == MOCK_CHILD_ID
    assert data["completed_count"] == 1
    assert data["cached"] == False

def test_record_growth(mock_supabase, mock_access_control):
    # Mock child info fetch
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
        {"id": MOCK_CHILD_ID, "birth_date": "2023-01-01T00:00:00", "gender": "male"}
    ]
    # Mock insert
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": "growth-id"}]
    
    payload = {
        "child_id": MOCK_CHILD_ID,
        "weight_kg": 10.0,
        "height_cm": 75.0,
        "head_circumference_cm": 45.0
    }
    
    response = client.post("/api/santanraksha/growth/record", json=payload, headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "z_scores" in data
    assert "growth_status" in data
