"""
SantanRaksha - Child Health API Tests
These tests require proper mocking or a real database connection.
Marked as integration tests.
"""

import pytest
import os

# Set test environment BEFORE importing app
os.environ["TESTING"] = "true"
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("GEMINI_API_KEY", "test-key")

MOCK_CHILD_ID = "test-child-id"


@pytest.mark.integration
@pytest.mark.skip(reason="Requires live Supabase connection or complex mocking")
def test_get_standard_schedule():
    """Test getting standard vaccination schedule - requires database"""
    pass


@pytest.mark.integration
@pytest.mark.skip(reason="Requires live Supabase connection or complex mocking")
def test_get_child_vaccinations():
    """Test getting child vaccinations - requires database"""
    pass


@pytest.mark.integration
@pytest.mark.skip(reason="Requires live Supabase connection or complex mocking")
def test_record_growth():
    """Test recording growth measurement - requires database"""
    pass
