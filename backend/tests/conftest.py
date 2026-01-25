"""
MatruRaksha - Test Configuration
Pytest fixtures and test utilities
"""

import pytest
import os
from typing import Generator
from fastapi.testclient import TestClient

# Set test environment
os.environ["TESTING"] = "true"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test-key"
os.environ["GEMINI_API_KEY"] = "test-key"


@pytest.fixture(scope="session")
def test_app():
    """
    Create a test FastAPI application
    """
    # Import after setting environment variables
    from main import app
    return app


@pytest.fixture(scope="function")
def client(test_app) -> Generator:
    """
    Create a test client for making requests
    """
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def mock_supabase(mocker):
    """
    Mock Supabase client for testing
    """
    mock_client = mocker.Mock()
    mock_table = mocker.Mock()
    mock_client.table.return_value = mock_table
    
    # Mock common operations
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.execute.return_value = mocker.Mock(data=[])
    
    return mock_client


@pytest.fixture(scope="function")
def mock_gemini(mocker):
    """
    Mock Gemini AI client for testing
    """
    mock_client = mocker.Mock()
    mock_models = mocker.Mock()
    mock_response = mocker.Mock()
    
    mock_response.text = "Test AI response"
    mock_models.generate_content.return_value = mock_response
    mock_client.models = mock_models
    
    return mock_client


@pytest.fixture(scope="function")
def sample_mother_data():
    """
    Sample mother data for testing
    """
    return {
        "id": "test-mother-123",
        "name": "Test Mother",
        "phone": "+919876543210",
        "age": 28,
        "gravida": 2,
        "parity": 1,
        "bmi": 22.5,
        "location": "Test City",
        "preferred_language": "en",
        "due_date": "2026-06-01"
    }


@pytest.fixture(scope="function")
def sample_risk_assessment():
    """
    Sample risk assessment data for testing
    """
    return {
        "mother_id": "test-mother-123",
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "heart_rate": 75,
        "blood_glucose": 95.0,
        "hemoglobin": 12.5,
        "proteinuria": 0,
        "edema": 0,
        "headache": 0,
        "vision_changes": 0,
        "epigastric_pain": 0,
        "vaginal_bleeding": 0,
        "notes": "Test assessment"
    }
