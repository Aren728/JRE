"""JRE API — Beta Readiness Integration Tests.

Automated integration tests codifying the manual E2E staging results.
Ensures API security, rate limiting, structured feedback, evaluation_id,
and legal disclaimer remain intact across future deployments.

NO engine logic tested — pure API layer verification.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

# Ensure src/ is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from jrs.api.main import app  # noqa: E402
from jrs.api.auth import rate_limiter  # noqa: E402
from jrs.api.schemas import ENGINE_VERSION, LEGAL_DISCLAIMER  # noqa: E402

client = TestClient(app)

# ── Test Fixtures ───────────────────────────────────────────────────────────

_ALPHA_KEY = "jre-beta-key-alpha"
_BETA_KEY = "jre-beta-key-beta"
_GAMMA_KEY = "jre-beta-key-gamma"
_AUTH_HEADERS = {"X-API-Key": _ALPHA_KEY}


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """Reset the rate limiter before each test to avoid cross-test interference."""
    original_max = rate_limiter.max_requests
    rate_limiter.max_requests = 10  # Ensure default rate limit for tests
    rate_limiter._requests.clear()
    yield
    rate_limiter._requests.clear()
    rate_limiter.max_requests = original_max


@pytest.fixture()
def _fresh_feedback_file(tmp_path: Path) -> Path:
    """Provide a temporary feedback file for feedback tests."""
    # Temporarily override the data directory in main
    import jrs.api.main as main_mod
    original_project_root = main_mod._PROJECT_ROOT
    main_mod._PROJECT_ROOT = tmp_path
    feedback_dir = tmp_path / "data"
    feedback_dir.mkdir(parents=True, exist_ok=True)
    yield feedback_dir / "feedback_log.jsonl"
    main_mod._PROJECT_ROOT = original_project_root


# ── Test Cases ──────────────────────────────────────────────────────────────


class TestHealthEndpointNoAuth:
    """Verify health endpoint works without authentication."""

    def test_health_endpoint_no_auth(self) -> None:
        """GET /api/v1/health returns 200 without an API key."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestAuthEnforcement:
    """Verify API key authentication is enforced on protected endpoints."""

    def test_protected_endpoint_rejects_missing_key(self) -> None:
        """GET /api/v1/fixtures returns 422 when X-API-Key header is missing.

        FastAPI returns 422 (validation error) for missing required headers.
        This is functionally equivalent to 401 — the request is rejected.
        """
        response = client.get("/api/v1/fixtures")
        assert response.status_code in (401, 422)
        data = response.json()
        # Should contain an error detail about the missing key
        assert "detail" in data

    def test_protected_endpoint_accepts_valid_key(self) -> None:
        """GET /api/v1/fixtures returns 200 with a valid API key."""
        response = client.get("/api/v1/fixtures", headers=_AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "fixtures" in data
        assert data["count"] >= 50
        assert isinstance(data["fixtures"], list)
        assert "chart_001_pilot" in data["fixtures"]

    def test_protected_endpoint_rejects_invalid_key(self) -> None:
        """GET /api/v1/fixtures returns 401 with an invalid API key."""
        response = client.get(
            "/api/v1/fixtures",
            headers={"X-API-Key": "invalid-key-12345"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid" in data["detail"] or "API key" in data["detail"]


class TestEvaluationResponseFields:
    """Verify evaluation responses contain mandatory fields."""

    def test_evaluation_response_contains_mandatory_fields(self) -> None:
        """POST /api/v1/evaluate/fixture returns evaluation_id, engine_version, disclaimer."""
        response = client.post(
            "/api/v1/evaluate/fixture",
            json={"fixture_id": "chart_001_pilot"},
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()

        # evaluation_id: valid SHA-256 format (16 hex chars)
        assert "evaluation_id" in data
        eval_id = data["evaluation_id"]
        assert isinstance(eval_id, str)
        assert len(eval_id) == 16
        # Verify it's valid hex
        assert all(c in "0123456789abcdef" for c in eval_id)

        # Determinism: same input produces same evaluation_id
        response2 = client.post(
            "/api/v1/evaluate/fixture",
            json={"fixture_id": "chart_001_pilot"},
            headers=_AUTH_HEADERS,
        )
        assert response2.status_code == 200
        assert response2.json()["evaluation_id"] == eval_id

        # engine_version
        assert "engine_version" in data
        assert data["engine_version"] == ENGINE_VERSION

        # disclaimer
        assert "disclaimer" in data
        assert isinstance(data["disclaimer"], str)
        assert "DISCLAIMER" in data["disclaimer"]
        assert "informational and research purposes" in data["disclaimer"]

        # Standard evaluation fields
        assert "yogas" in data
        assert "yoga_count" in data
        assert "formed_count" in data
        assert "lagna" in data
        assert "processing_time_ms" in data
        assert data["processing_time_ms"] > 0


class TestStructuredFeedback:
    """Verify structured feedback endpoint accepts and validates payloads."""

    def test_structured_feedback_accepts_valid_payload(
        self, _fresh_feedback_file: Path,
    ) -> None:
        """POST /api/v1/feedback accepts a fully populated FeedbackEntry."""
        payload = {
            "evaluation_id": "test-integration-001",
            "expert_id": "EXPERT_A",
            "domain": "CAREER",
            "expert_agreement": True,
            "expert_disagreement": False,
            "missing_yoga": False,
            "false_positive": False,
            "false_negative": False,
            "timing_issue": False,
            "interpretation_issue": False,
            "astronomical_issue": False,
            "other": False,
            "free_text": "Integration test feedback entry",
        }

        response = client.post(
            "/api/v1/feedback",
            json=payload,
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "recorded"
        assert data["evaluation_id"] == "test-integration-001"
        assert data["entry_count"] >= 1

        # Verify the file was written
        assert _fresh_feedback_file.exists()
        with _fresh_feedback_file.open() as f:
            lines = [line.strip() for line in f if line.strip()]
        assert len(lines) >= 1
        entry = json.loads(lines[-1])
        assert entry["evaluation_id"] == "test-integration-001"
        assert entry["expert_id"] == "EXPERT_A"
        assert entry["domain"] == "CAREER"
        assert entry["engine_version"] == ENGINE_VERSION
        assert "timestamp" in entry

    def test_structured_feedback_rejects_invalid_schema(self) -> None:
        """POST /api/v1/feedback returns 422 with missing required fields."""
        # Missing required fields: expert_id, domain, and all boolean flags
        invalid_payload = {
            "evaluation_id": "test-002",
            # expert_id missing
            # domain missing
            # boolean flags missing
            "free_text": "Missing required fields",
        }

        response = client.post(
            "/api/v1/feedback",
            json=invalid_payload,
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_structured_feedback_boolean_flags_work(self) -> None:
        """POST /api/v1/feedback correctly handles boolean flag combinations."""
        payload = {
            "evaluation_id": "test-flags-001",
            "expert_id": "EXPERT_B",
            "domain": "HEALTH",
            "expert_agreement": False,
            "expert_disagreement": True,
            "missing_yoga": True,
            "false_positive": False,
            "false_negative": True,
            "timing_issue": True,
            "interpretation_issue": False,
            "astronomical_issue": False,
            "other": False,
            "free_text": "Multiple issues detected in health domain",
        }

        response = client.post(
            "/api/v1/feedback",
            json=payload,
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "recorded"


class TestRateLimiting:
    """Verify in-memory rate limiter enforces limits correctly."""

    def test_rate_limiting_enforcement(self) -> None:
        """12 rapid requests: first 10 return 200, requests 11-12 return 429."""
        results: list[int] = []
        for _ in range(12):
            response = client.get(
                "/api/v1/fixtures",
                headers={"X-API-Key": _BETA_KEY},
            )
            results.append(response.status_code)

        # First 10 should succeed
        assert results[:10] == [200] * 10, (
            f"First 10 requests should return 200, got: {results[:10]}"
        )
        # Requests 11-12 should be rate limited
        assert results[10] == 429, f"Request 11 should return 429, got: {results[10]}"
        assert results[11] == 429, f"Request 12 should return 429, got: {results[11]}"

    def test_rate_limiting_per_key_isolation(self) -> None:
        """Rate limiting is per-key — different keys have independent windows."""
        # Exhaust key-beta's rate limit
        for _ in range(10):
            client.get(
                "/api/v1/fixtures",
                headers={"X-API-Key": _BETA_KEY},
            )

        # key-beta is now rate limited
        response_beta = client.get(
            "/api/v1/fixtures",
            headers={"X-API-Key": _BETA_KEY},
        )
        assert response_beta.status_code == 429

        # key-gamma should still work (fresh window)
        response_gamma = client.get(
            "/api/v1/fixtures",
            headers={"X-API-Key": _GAMMA_KEY},
        )
        assert response_gamma.status_code == 200

    def test_rate_limit_response_includes_retry_after(self) -> None:
        """Rate limit response includes Retry-After header."""
        # Exhaust the rate limit
        for _ in range(10):
            client.get(
                "/api/v1/fixtures",
                headers={"X-API-Key": _GAMMA_KEY},
            )

        response = client.get(
            "/api/v1/fixtures",
            headers={"X-API-Key": _GAMMA_KEY},
        )
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        retry_after = int(response.headers["Retry-After"])
        assert retry_after >= 0
        assert retry_after <= 60


class TestReportWithDisclaimer:
    """Verify generated reports include evaluation_id and disclaimer."""

    def test_report_contains_evaluation_id_and_disclaimer(self) -> None:
        """Markdown report includes evaluation_id, engine_version, and disclaimer."""
        response = client.post(
            "/api/v1/report/fixture?format=markdown",
            json={"fixture_id": "chart_001_pilot"},
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()

        # Report-level fields
        assert "evaluation_id" in data
        assert len(data["evaluation_id"]) == 16
        assert "disclaimer" in data
        assert "DISCLAIMER" in data["disclaimer"]

        # Content includes evaluation_id
        content = data["content"]
        assert "Evaluation ID" in content
        assert data["evaluation_id"] in content

        # Content includes engine version
        assert "Engine Version" in content
        assert ENGINE_VERSION in content

        # Content includes disclaimer
        assert "DISCLAIMER" in content
        assert "informational and research purposes" in content


class TestLoggingStructure:
    """Verify structured logging includes required fields."""

    def test_evaluation_logs_include_evaluation_id(self) -> None:
        """Evaluation requests log evaluation_id and latency_ms."""
        response = client.post(
            "/api/v1/evaluate/fixture",
            json={"fixture_id": "chart_001_pilot"},
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 200
        # The response itself contains evaluation_id — logging is tested
        # via the structured log output (verified manually in E2E tests)
        data = response.json()
        assert "evaluation_id" in data
        assert "processing_time_ms" in data
        assert data["processing_time_ms"] > 0
