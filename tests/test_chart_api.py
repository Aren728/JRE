# tests/test_chart_api.py
"""Integration tests for chart calculation API endpoints.

Tests cover all three chart routes:
- POST /api/v1/chart
- GET /api/v1/chart/{id}
- GET /api/v1/charts

Tests use dependency overrides to handle database availability.
"""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.jrs.api.main import app
from src.jrs.db.models import ChartCalculation


def _create_mock_db_session(record_to_return: MagicMock = None) -> MagicMock:
    """Create a mock database session for testing."""
    mock_session = MagicMock(spec=Session)

    # Mock the query method to return an empty result set
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = record_to_return  # Return mock record if provided
    mock_filter.all.return_value = []  # Empty list for pagination
    mock_filter.count.return_value = 0 if record_to_return is None else 1  # No records
    mock_query.filter.return_value = mock_filter
    mock_query.offset.return_value.limit.return_value.all.return_value = []
    mock_query.offset.return_value.limit.return_value.count.return_value = 0
    mock_session.query.return_value = mock_query

    # Mock commit and refresh to set created_at on the record
    mock_now = MagicMock()
    mock_now.isoformat.return_value = "2026-09-10T18:30:00+00:00"
    
    def mock_refresh(record):
        """Mock refresh to set created_at on the record."""
        record.created_at = mock_now
        record.id = 1  # Set a default ID
        
    mock_session.refresh.side_effect = mock_refresh
    mock_session.commit.return_value = None
    mock_session.add.return_value = None

    return mock_session


def _create_mock_chart_record(chart_id: int = 1) -> MagicMock:
    """Create a mock ChartCalculation record."""
    mock_record = MagicMock(spec=ChartCalculation)
    mock_record.id = chart_id
    mock_record.query_date = "2026-09-10"
    mock_record.query_time = "18:30:00"
    mock_record.latitude = 24.8170
    mock_record.longitude = 93.9368
    mock_record.timezone = "Asia/Kolkata"
    mock_now = MagicMock()
    mock_now.isoformat.return_value = "2026-09-10T18:30:00+00:00"
    mock_record.created_at = mock_now
    return mock_record


# Dependency override for database session (empty)
def override_get_db_empty():
    """Override get_db dependency with a mock session (no records)."""
    mock_session = _create_mock_db_session()
    yield mock_session


# Dependency override for database session (with record)
def override_get_db_with_record():
    """Override get_db dependency with a mock session (returns mock record)."""
    mock_record = _create_mock_chart_record(chart_id=42)
    mock_session = _create_mock_db_session(record_to_return=mock_record)
    yield mock_session


# Apply override at module level for default (empty) case
app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def setup_dependency_overrides():
    """Set up dependency overrides before each test."""
    app.dependency_overrides.clear()
    # Use the empty override for tests that don't need a record
    app.dependency_overrides[__import__('src.jrs.db.session', fromlist=['get_db']).get_db] = override_get_db_empty
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


class TestCalculateAndStoreChart:
    """Tests for POST /api/v1/chart endpoint."""

    def test_calculate_chart_invalid_payload(self):
        """Test POST /api/v1/chart rejects invalid input."""
        # Missing required fields
        response = client.post("/api/v1/chart", json={})
        assert response.status_code == 422

        # Invalid date format
        response = client.post("/api/v1/chart", json={
            "query_date": "not-a-date",
            "query_time": "18:30:00",
            "latitude": 24.8170,
            "longitude": 93.9368,
            "timezone": "Asia/Kolkata"
        })
        assert response.status_code == 422

    def test_calculate_chart_valid_payload(self):
        """Test POST /api/v1/chart with valid payload returns success."""
        payload = {
            "query_date": "2026-09-10",
            "query_time": "18:30:00",
            "latitude": 24.8170,
            "longitude": 93.9368,
            "timezone": "Asia/Kolkata"
        }
        response = client.post("/api/v1/chart", json=payload)

        # Mock DB should return 200
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "astronomical_data" in data
        assert "id" in data
        assert "created_at" in data

        # Check D9 / D10 Presence
        sun_data = data["astronomical_data"]["planets"]["Sun"]
        assert "divisional" in sun_data
        assert "d9" in sun_data["divisional"]
        assert "d10" in sun_data["divisional"]
        assert sun_data["divisional"]["d9"]["sign"] is not None
        assert sun_data["divisional"]["d10"]["sign"] is not None

    def test_calculate_chart_all_planets_present(self):
        """Test that astronomical data contains all expected planets."""
        payload = {
            "query_date": "2026-09-10",
            "query_time": "18:30:00",
            "latitude": 24.8170,
            "longitude": 93.9368,
            "timezone": "Asia/Kolkata"
        }
        response = client.post("/api/v1/chart", json=payload)
        assert response.status_code == 200

        data = response.json()
        planets = data["astronomical_data"]["planets"]

        # Verify all expected planets are present
        expected_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars",
                           "Jupiter", "Saturn", "Rahu", "Ketu"]
        for planet in expected_planets:
            assert planet in planets, f"Missing planet: {planet}"

        # Verify each planet has divisional data
        for planet, details in planets.items():
            assert "divisional" in details
            assert "d9" in details["divisional"]
            assert "d10" in details["divisional"]

    def test_calculate_chart_divisional_signs_valid(self):
        """Test that D9 and D10 signs are valid zodiac signs."""
        payload = {
            "query_date": "2026-09-10",
            "query_time": "18:30:00",
            "latitude": 24.8170,
            "longitude": 93.9368,
            "timezone": "Asia/Kolkata"
        }
        response = client.post("/api/v1/chart", json=payload)
        assert response.status_code == 200

        data = response.json()
        planets = data["astronomical_data"]["planets"]

        # Verify D9 signs are valid zodiac signs
        valid_signs = [
            "Aries", "Taurus", "Gemini", "Cancer",
            "Leo", "Virgo", "Libra", "Scorpio",
            "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]

        for planet, details in planets.items():
            d9_sign = details["divisional"]["d9"]["sign"]
            d10_sign = details["divisional"]["d10"]["sign"]

            assert d9_sign in valid_signs, f"Invalid D9 sign for {planet}: {d9_sign}"
            assert d10_sign in valid_signs, f"Invalid D10 sign for {planet}: {d10_sign}"
            assert details["divisional"]["d9"]["sign_index"] in range(1, 13)
            assert details["divisional"]["d10"]["sign_index"] in range(1, 13)


class TestGetChartById:
    """Tests for GET /api/v1/chart/{chart_id} endpoint."""

    def test_get_chart_not_found(self):
        """Test GET /api/v1/chart/{id} returns 404 for non-existent chart."""
        response = client.get("/api/v1/chart/999999")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Chart record not found"

    def test_get_chart_by_id_success(self):
        """Test GET /api/v1/chart/{id} returns chart data when found."""
        # Override the db dependency to return a mock record
        app.dependency_overrides.clear()
        app.dependency_overrides[__import__('src.jrs.db.session', fromlist=['get_db']).get_db] = override_get_db_with_record

        try:
            response = client.get("/api/v1/chart/42")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 42
            assert data["query_date"] == "2026-09-10"  # Now a string
            assert data["query_time"] == "18:30:00"
            assert data["latitude"] == 24.8170
            assert data["longitude"] == 93.9368
            assert data["timezone"] == "Asia/Kolkata"
            assert data["created_at"] is not None  # ISO format string
            assert "T" in data["created_at"]  # ISO format contains T
        finally:
            app.dependency_overrides.clear()


class TestGetCharts:
    """Tests for GET /api/v1/charts endpoint."""

    def test_get_charts_pagination(self):
        """Test GET /api/v1/charts returns paginated results."""
        response = client.get("/api/v1/charts?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "results" in data
        assert "limit" in data
        assert "offset" in data
        assert data["limit"] == 5
        assert data["offset"] == 0
        assert isinstance(data["results"], list)

    def test_get_charts_default_pagination(self):
        """Test GET /api/v1/charts with default pagination values."""
        response = client.get("/api/v1/charts")
        assert response.status_code == 200
        data = response.json()

        # Default values from Query defaults
        assert data["limit"] == 10
        assert data["offset"] == 0
        assert isinstance(data["results"], list)
