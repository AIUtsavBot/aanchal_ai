
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from main import app
from routes import postnatal

client = TestClient(app)

# Mock data
MOCK_MOTHER_ID = "test-mother-id"
MOCK_CHILD_ID = "test-child-id"

@pytest.fixture
def mock_supabase():
    with patch("routes.postnatal.supabase") as mock:
        yield mock

@pytest.fixture
def mock_cache():
    with patch("routes.postnatal.cache") as mock:
        mock.get.return_value = None
        yield mock

def test_get_mother_assessments(mock_supabase, mock_cache):
    # Setup mock
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
        {"id": "1", "assessment_type": "mother_postnatal", "created_at": "2024-01-01"}
    ]
    
    response = client.get(f"/api/postnatal/mother/{MOCK_MOTHER_ID}/assessments")
    assert response.status_code == 200
    data = response.json()
    assert data["mother_id"] == MOCK_MOTHER_ID
    assert len(data["assessments"]) == 1
    assert data["cached"] == False

def test_create_mother_assessment(mock_supabase):
    # Setup mock
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": "new-id"}]
    
    payload = {
        "mother_id": MOCK_MOTHER_ID,
        "days_postpartum": 5,
        "temperature": 98.6,
        "blood_pressure_systolic": 120,
        "blood_pressure_diastolic": 80,
        "fever": False
    }
    
    response = client.post("/api/postnatal/mother/assessment", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["assessment_id"] == "new-id"
    assert data["risk_level"] == "low"

def test_high_risk_assessment(mock_supabase):
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": "risk-id"}]
    
    payload = {
        "mother_id": MOCK_MOTHER_ID,
        "fever": True,
        "excessive_bleeding": True, # 2 danger signs = high risk
        "foul_discharge": False
    }
    
    response = client.post("/api/postnatal/mother/assessment", json=payload)
    assert response.status_code == 200
    assert response.json()["risk_level"] == "high"
