"""JRE API — Unit tests for FastAPI endpoints.

Tests the API layer without modifying any engine logic.
Uses fastapi.testclient.TestClient for synchronous testing.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure src/ is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from jrs.api.main import app  # noqa: E402

client = TestClient(app)


# ── Health Endpoint ─────────────────────────────────────────────────────────


class TestHealthEndpoint:
    """Tests for GET /api/v1/health."""

    def test_health_returns_200(self) -> None:
        """Health endpoint returns 200 with healthy status."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"

    def test_health_response_schema(self) -> None:
        """Health response matches expected schema."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert isinstance(data["status"], str)
        assert isinstance(data["version"], str)


# ── Fixtures Endpoint ───────────────────────────────────────────────────────


class TestFixturesEndpoint:
    """Tests for GET /api/v1/fixtures."""

    def test_list_fixtures_returns_200(self) -> None:
        """Fixtures endpoint returns 200 with fixture list."""
        response = client.get("/api/v1/fixtures")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "fixtures" in data
        assert data["count"] >= 50  # We have 50+ fixtures
        assert isinstance(data["fixtures"], list)

    def test_list_fixtures_contains_chart_001(self) -> None:
        """Fixture list contains chart_001_pilot."""
        response = client.get("/api/v1/fixtures")
        data = response.json()
        assert "chart_001_pilot" in data["fixtures"]


# ── Fixture Evaluation Endpoint ─────────────────────────────────────────────


class TestEvaluateFixtureEndpoint:
    """Tests for POST /api/v1/evaluate/fixture."""

    def test_evaluate_fixture_chart_001(self) -> None:
        """Evaluating chart_001_pilot returns yogas with 200 status."""
        response = client.post(
            "/api/v1/evaluate/fixture",
            json={"fixture_id": "chart_001_pilot"},
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "subject" in data
        assert "lagna" in data
        assert "yogas" in data
        assert "yoga_count" in data
        assert "formed_count" in data
        assert "processing_time_ms" in data

        # Einstein's chart should have Malavya yoga
        yoga_names = [y["yoga_name"] for y in data["yogas"]]
        assert "Malavya" in yoga_names, (
            f"Expected Malavya yoga in Einstein's chart, got: {yoga_names}"
        )

        # Verify yoga result structure
        malavya = next(y for y in data["yogas"] if y["yoga_name"] == "Malavya")
        assert malavya["status"] == "FORMED"
        assert malavya["category"] == "PANCHAMAHAPURUSHA"
        assert "VENUS" in malavya["involved_planets"]
        assert isinstance(malavya["static_strength"], float)
        assert isinstance(malavya["domains"], list)

    def test_evaluate_fixture_chart_002(self) -> None:
        """Evaluating chart_002_curie returns yogas."""
        response = client.post(
            "/api/v1/evaluate/fixture",
            json={"fixture_id": "chart_002_curie"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == "Marie Curie"
        assert data["yoga_count"] > 0

    def test_evaluate_fixture_with_json_extension(self) -> None:
        """Fixture ID with .json extension is handled gracefully."""
        response = client.post(
            "/api/v1/evaluate/fixture",
            json={"fixture_id": "chart_001_pilot.json"},
        )
        assert response.status_code == 200

    def test_evaluate_fixture_not_found(self) -> None:
        """Non-existent fixture returns 404."""
        response = client.post(
            "/api/v1/evaluate/fixture",
            json={"fixture_id": "chart_999_nonexistent"},
        )
        assert response.status_code == 404

    def test_evaluate_fixture_response_times(self) -> None:
        """Response includes processing time in milliseconds."""
        response = client.post(
            "/api/v1/evaluate/fixture",
            json={"fixture_id": "chart_001_pilot"},
        )
        data = response.json()
        assert data["processing_time_ms"] > 0
        assert data["processing_time_ms"] < 10000  # Should complete in < 10s


# ── Custom Birth Data Endpoint ──────────────────────────────────────────────


class TestEvaluateCustomEndpoint:
    """Tests for POST /api/v1/evaluate/custom."""

    def test_evaluate_custom_valid_data(self) -> None:
        """Evaluating custom birth data returns yogas with 200 status."""
        response = client.post(
            "/api/v1/evaluate/custom",
            json={
                "date": "1990-01-15",
                "time": "14:30:00",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "timezone": "America/New_York",
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "subject" in data
        assert data["subject"] == "Custom"
        assert "lagna" in data
        assert "yogas" in data
        assert "yoga_count" in data
        assert "processing_time_ms" in data
        assert data["processing_time_ms"] > 0

    def test_evaluate_custom_different_location(self) -> None:
        """Evaluating birth data from different location."""
        response = client.post(
            "/api/v1/evaluate/custom",
            json={
                "date": "1947-08-15",
                "time": "12:00:00",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "timezone": "Asia/Kolkata",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["lagna"] != ""  # Should have a lagna
        assert isinstance(data["yogas"], list)

    def test_evaluate_custom_invalid_date(self) -> None:
        """Invalid birth data returns 422 or 500."""
        response = client.post(
            "/api/v1/evaluate/custom",
            json={
                "date": "not-a-date",
                "time": "14:30:00",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "timezone": "America/New_York",
            },
        )
        # Should return error (422 for validation or 500 for computation)
        assert response.status_code in (422, 500)

    def test_evaluate_custom_missing_fields(self) -> None:
        """Missing required fields returns 422."""
        response = client.post(
            "/api/v1/evaluate/custom",
            json={
                "date": "1990-01-15",
                # Missing time, latitude, longitude, timezone
            },
        )
        assert response.status_code == 422

    def test_evaluate_custom_yoga_structure(self) -> None:
        """Yoga results have correct structure."""
        response = client.post(
            "/api/v1/evaluate/custom",
            json={
                "date": "1990-01-15",
                "time": "14:30:00",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "timezone": "America/New_York",
            },
        )
        data = response.json()
        for yoga in data["yogas"]:
            assert "yoga_name" in yoga
            assert "status" in yoga
            assert yoga["status"] in ("FORMED", "WEAKENED", "CANCELLED")
            assert "category" in yoga
            assert "static_strength" in yoga
            assert "involved_planets" in yoga
            assert isinstance(yoga["involved_planets"], list)


# ── OpenAPI Schema ──────────────────────────────────────────────────────────


class TestOpenAPI:
    """Tests for API documentation endpoints."""

    def test_docs_available(self) -> None:
        """Swagger UI is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema(self) -> None:
        """OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/api/v1/health" in schema["paths"]
        assert "/api/v1/evaluate/fixture" in schema["paths"]
        assert "/api/v1/evaluate/custom" in schema["paths"]
