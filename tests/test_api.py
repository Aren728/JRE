"""
Integration tests for FastAPI endpoint /api/v1/analyze
"""

from fastapi.testclient import TestClient

from src.jrs.api.main import app

client = TestClient(app)


def test_analyze_endpoint_success():
    """Verify /api/v1/analyze endpoint accepts valid payload and returns 200 OK."""
    payload = {
        "date": "1995-10-24",
        "time": "14:30:00",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "timezone": "Asia/Kolkata",
    }

    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()

    # Validate Core Alignment
    assert "core_alignment" in data
    assert data["core_alignment"]["ascendant_sign"] == "Kumbha"
    assert data["core_alignment"]["moon_nakshatra"] == "Swati"

    # Validate Planets list
    assert "planets" in data
    assert len(data["planets"]) == 9

    # Validate Active Dasha
    assert "active_dasha" in data
    assert data["active_dasha"]["mahadasha"] == "Jupiter"

    # Validate Synthesis Markdown string
    assert "synthesis_markdown" in data
    assert len(data["synthesis_markdown"]) > 50


def test_analyze_endpoint_invalid_payload():
    """Verify API returns 422 Unprocessable Entity on missing required fields."""
    payload = {
        "date": "1995-10-24",
        # Missing time, latitude, longitude, timezone
    }

    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422
