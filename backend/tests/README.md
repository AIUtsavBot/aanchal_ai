# MatruRaksha Backend Tests

This directory contains the test suite for the MatruRaksha backend.

## Test Structure

```
tests/
├── conftest.py           # Pytest fixtures and configuration
├── test_health.py        # Health check endpoint tests
├── test_validation.py    # Input validation tests
└── test_rate_limiting.py # Rate limiting tests
```

## Running Tests

### All Tests
```bash
cd backend
pytest
```

### Unit Tests Only
```bash
pytest -m unit
```

### Integration Tests Only
```bash
pytest -m integration
```

### With Coverage
```bash
pytest --cov=backend --cov-report=html
```

### Specific Test File
```bash
pytest tests/test_health.py
```

### Verbose Output
```bash
pytest -v
```

## Test Markers

- `@pytest.mark.unit` - Fast unit tests (no external dependencies)
- `@pytest.mark.integration` - Integration tests (may use real services)
- `@pytest.mark.slow` - Slow-running tests

## Coverage Goals

- **Phase 1 Target**: 30% coverage
- **Phase 4 Target**: 80% coverage

## Writing Tests

### Unit Test Example
```python
@pytest.mark.unit
def test_sanitize_text():
    dirty = "<script>alert('xss')</script>Hello"
    clean = sanitize_text(dirty)
    assert "Hello" in clean
    assert "<script>" not in clean
```

### Integration Test Example
```python
@pytest.mark.integration
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
```

## Fixtures Available

- `client` - TestClient for making API requests
- `mock_supabase` - Mocked Supabase client
- `mock_gemini` - Mocked Gemini AI client
- `sample_mother_data` - Sample mother data
- `sample_risk_assessment` - Sample risk assessment data
