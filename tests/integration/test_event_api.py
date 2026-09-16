"""
tests/integration/test_event_api.py

Integration test suite for the JRE/JRS v1.0.0 API layer.
Tests the POST /api/v1/events/evaluate endpoint using FastAPI's TestClient.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from jrs.api.main import app

client = TestClient(app)


# --- Test Fixtures & Synthetic Payloads ---


@pytest.fixture
def valid_chart_data():
    """Provides a standard synthetic chart payload for Tier 1 evaluation."""
    return {
        "planets": {
            "Sun": {"house": 1, "sign": "Aries", "degree": 12.5},
            "Jupiter": {"house": 1, "sign": "Aries", "degree": 15.2},
            "Saturn": {"house": 10, "sign": "Capricorn", "degree": 8.1},
            "Mars": {"house": 4, "sign": "Cancer", "degree": 22.0},
        }
    }


@pytest.fixture
def valid_event_context():
    """Provides valid Dasha event context parameters for Tier 2 filtering."""
    return {
        "event_date": "2026-09-12",
        "dasha_lord": "Jupiter",
        "bhukti_lord": "Sun",
        "pratyantardasha_lord": "Saturn",
    }


# --- Endpoint Integration Tests ---


def test_evaluate_event_context_success(valid_chart_data, valid_event_context):
    """
    Tests successful execution of the /api/v1/events/evaluate endpoint
    with a valid chart and event context.
    """
    payload = {
        "chart_data": valid_chart_data,
        "event_context": valid_event_context,
    }

    response = client.post("/api/v1/events/evaluate", json=payload)

    assert response.status_code == 200
    data = response.json()

    # Validate response schema keys
    assert "tier1_total_tokens" in data
    assert "tier2_filtered_tokens_count" in data
    assert "suppressed_tokens_count" in data
    assert "active_dasha_rulers" in data
    assert "event_tokens" in data
    assert "filtered_composite_detections" in data

    # Verify Dasha ruler parsing (order is not guaranteed)
    assert set(data["active_dasha_rulers"]) == {"Jupiter", "Sun", "Saturn"}
    assert isinstance(data["filtered_composite_detections"], list)


def test_evaluate_event_context_without_pratyantardasha(
    valid_chart_data, valid_event_context
):
    """Tests endpoint execution when optional pratyantardasha_lord is omitted."""
    del valid_event_context["pratyantardasha_lord"]
    payload = {
        "chart_data": valid_chart_data,
        "event_context": valid_event_context,
    }

    response = client.post("/api/v1/events/evaluate", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert set(data["active_dasha_rulers"]) == {"Jupiter", "Sun"}


def test_evaluate_event_context_empty_chart(valid_event_context):
    """
    Tests edge case where chart_data contains no planetary positions.
    Should return 200 with 0 tokens.
    """
    payload = {
        "chart_data": {"planets": {}},
        "event_context": valid_event_context,
    }

    response = client.post("/api/v1/events/evaluate", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["tier1_total_tokens"] == 0
    assert data["tier2_filtered_tokens_count"] == 0
    assert data["suppressed_tokens_count"] == 0
    assert data["filtered_composite_detections"] == []


def test_evaluate_event_context_missing_required_fields():
    """
    Tests request validation error (HTTP 422) when mandatory fields are missing.
    """
    # Missing event_context entirely
    payload = {
        "chart_data": {"planets": {}},
    }

    response = client.post("/api/v1/events/evaluate", json=payload)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_evaluate_event_context_invalid_event_context_schema(valid_chart_data):
    """
    Tests request validation error (HTTP 422) when event_context is missing
    required dasha_lord.
    """
    payload = {
        "chart_data": valid_chart_data,
        "event_context": {
            "event_date": "2026-09-12",
            # Missing dasha_lord and bhukti_lord
        },
    }

    response = client.post("/api/v1/events/evaluate", json=payload)

    assert response.status_code == 422


def test_health_check_endpoint():
    """Verifies that the /api/v1/health endpoint returns 200 OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
