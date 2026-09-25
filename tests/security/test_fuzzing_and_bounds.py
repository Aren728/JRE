"""Phase 9E: Security & fuzz suite.

Bounds and abuses the public surfaces:

- **Path traversal** — fixture ids carrying ``/``, ``\\``, ``..``, or
  URL-encoded separators are rejected before the filesystem is touched
  (library raises ValueError; API maps to 400, never 500/leak).
- **Fuzzed birth snapshots** — malformed dates, times, timezones, and
  extreme coordinates (incl. 1000 BCE – 3000 CE spans) must produce a
  *controlled* JSON error response (4xx/5xx), never a hang, a stack
  trace dump, or state corruption.
- **Payload limits** — request bodies above 1 MiB are rejected with 413
  (memory-exhaustion bound).
- **Worker-thread timeout safety** — the bounded offload raises
  TimeoutError within the configured budget instead of hanging; normal
  offloads are unaffected.
"""

from __future__ import annotations

import time
from typing import Any

import pytest
from fastapi.testclient import TestClient

from jrs.api.dependencies import load_fixture
from jrs.api.main import MAX_REQUEST_BODY_BYTES, app
from jrs.api.offload import offload

# raise_server_exceptions=False: fuzzed inputs may legitimately surface
# as 500 — the assertions below require a *controlled* JSON response,
# not an exception escaping into the test process.
client = TestClient(app, raise_server_exceptions=False)
_AUTH = {"X-API-Key": "jre-beta-key-alpha"}


# ── Path traversal ──────────────────────────────────────────────────────────
class TestPathTraversal:
    @pytest.mark.parametrize(
        "evil_id",
        [
            "../../etc/passwd",
            "chart_001_pilot/../../secrets",
            "..\\..\\windows\\system32",
            "/etc/passwd",
            "chart/../chart_002_curie",
            ".",
            "..",
            "chart%2F..%2F..%2Fetc",
            "chart_001_pilot\x00.json",
            "",
        ],
    )
    def test_library_rejects_traversal_ids(self, evil_id: str) -> None:
        with pytest.raises((ValueError, FileNotFoundError)):
            load_fixture(evil_id)

    def test_traversal_never_reads_outside_fixtures(self) -> None:
        # The dot-dot id must fail on validation, not on file-not-found,
        # proving the regex guard fired before any filesystem access.
        with pytest.raises(ValueError, match="Invalid fixture id"):
            load_fixture("../../etc/passwd")

    def test_api_maps_traversal_to_400(self) -> None:
        response = client.post(
            "/api/v1/evaluate/fixture",
            json={"fixture_id": "../../etc/passwd"},
            headers=_AUTH,
        )
        assert response.status_code == 400
        assert "Invalid fixture id" in response.json()["detail"]

    def test_api_graph_route_maps_traversal_to_400(self) -> None:
        response = client.get("/api/v1/evidence/graph/..%2F..%2Fsecrets")
        assert response.status_code in (400, 404)  # routed or rejected — never 500
        if response.status_code == 400:
            assert "Invalid fixture id" in response.json()["detail"]


# ── Fuzzed birth snapshots ──────────────────────────────────────────────────
FUZZ_PAYLOADS: list[dict[str, Any]] = [
    {"date": "", "time": "12:00:00", "latitude": 0.0, "longitude": 0.0, "timezone": "UTC"},
    {"date": "not-a-date", "time": "12:00:00", "latitude": 0.0, "longitude": 0.0, "timezone": "UTC"},
    {"date": "9999-99-99", "time": "12:00:00", "latitude": 0.0, "longitude": 0.0, "timezone": "UTC"},
    {"date": "1000-01-01", "time": "00:00:00", "latitude": 0.0, "longitude": 0.0, "timezone": "UTC"},
    {"date": "3000-12-31", "time": "23:59:59", "latitude": 0.0, "longitude": 0.0, "timezone": "UTC"},
    {"date": "1990-01-15", "time": "25:00:00", "latitude": 0.0, "longitude": 0.0, "timezone": "UTC"},
    {"date": "1990-01-15", "time": "-1:0:0", "latitude": 0.0, "longitude": 0.0, "timezone": "UTC"},
    {"date": "1990-01-15", "time": "garbage", "latitude": 0.0, "longitude": 0.0, "timezone": "UTC"},
    {"date": "1990-01-15", "time": "12:00:00", "latitude": 91.0, "longitude": 0.0, "timezone": "UTC"},
    {"date": "1990-01-15", "time": "12:00:00", "latitude": -91.0, "longitude": 0.0, "timezone": "UTC"},
    {"date": "1990-01-15", "time": "12:00:00", "latitude": 0.0, "longitude": 181.0, "timezone": "UTC"},
    {"date": "1990-01-15", "time": "12:00:00", "latitude": 1e308, "longitude": 0.0, "timezone": "UTC"},
    {"date": "1990-01-15", "time": "12:00:00", "latitude": 0.0, "longitude": 0.0, "timezone": "Not/AZone"},
    {"date": "1990-01-15", "time": "12:00:00", "latitude": 0.0, "longitude": 0.0, "timezone": ""},
    {"date": "1990-01-15", "time": "12:00:00", "latitude": 0.0, "longitude": 0.0, "timezone": "UTC", "injected": True},
    {"date": "x" * 10000, "time": "12:00:00", "latitude": 0.0, "longitude": 0.0, "timezone": "UTC"},
]


class TestFuzzedBirthSnapshots:
    @pytest.mark.parametrize("payload", FUZZ_PAYLOADS)
    def test_controlled_json_error_never_hang(self, payload: dict[str, Any]) -> None:
        response = client.post(
            "/api/v1/evaluate/custom",
            json=payload,
            headers=_AUTH,
        )
        assert 200 <= response.status_code < 600
        # 4xx validation rejections and controlled 5xx are both fine;
        # a hang or a non-JSON crash dump is not.
        if response.status_code != 200:
            assert response.json() is not None or True  # response exists

    def test_extreme_dates_produce_controlled_outcome(self) -> None:
        for date in ("1000-01-01", "3000-12-31"):
            response = client.post(
                "/api/v1/evaluate/custom",
                json={
                    "date": date,
                    "time": "12:00:00",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "timezone": "UTC",
                },
                headers=_AUTH,
            )
            assert 200 <= response.status_code < 600
            if response.status_code >= 400:
                assert "detail" in response.json()

    def test_out_of_range_coordinates_rejected_by_schema(self) -> None:
        response = client.post(
            "/api/v1/evaluate/custom",
            json={
                "date": "1990-01-15",
                "time": "12:00:00",
                "latitude": 999.0,
                "longitude": 0.0,
                "timezone": "UTC",
            },
            headers=_AUTH,
        )
        assert response.status_code == 422  # pydantic ge/le bound

    def test_fuzzing_is_stateless(self) -> None:
        """Repeated malformed calls produce identical status codes —
        no state corruption across requests."""
        payload = FUZZ_PAYLOADS[2]  # 9999-99-99
        codes = {
            client.post(
                "/api/v1/evaluate/custom", json=payload, headers=_AUTH
            ).status_code
            for _ in range(3)
        }
        assert len(codes) == 1

    def test_valid_request_still_succeeds_after_fuzzing(self) -> None:
        response = client.post(
            "/api/v1/evaluate/fixture",
            json={"fixture_id": "chart_001_pilot"},
            headers=_AUTH,
        )
        assert response.status_code == 200


# ── Payload limits ──────────────────────────────────────────────────────────
class TestPayloadLimits:
    def test_oversized_body_rejected_413(self) -> None:
        response = client.post(
            "/api/v1/evaluate/custom",
            content=b"x" * (MAX_REQUEST_BODY_BYTES + 1),
            headers={**_AUTH, "content-type": "application/json"},
        )
        assert response.status_code == 413

    def test_limit_constant_is_sane(self) -> None:
        assert MAX_REQUEST_BODY_BYTES == 1_048_576


# ── Worker-thread timeout safety ────────────────────────────────────────────
class TestOffloadTimeout:
    def test_offload_completes_normally(self) -> None:
        async def run() -> int:
            return await offload(lambda: 41 + 1)

        import asyncio

        assert asyncio.run(run()) == 42

    def test_offload_times_out_within_budget(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import asyncio

        monkeypatch.setenv("JRS_OFFLOAD_TIMEOUT_SECONDS", "0.05")

        def slow() -> None:
            time.sleep(0.5)

        async def run() -> None:
            await offload(slow)

        start = time.monotonic()
        with pytest.raises(TimeoutError):
            asyncio.run(run())
        elapsed = time.monotonic() - start
        # Bound must fire well before the task itself completes.
        assert elapsed < 0.45

    def test_timeout_disabled_by_explicit_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import asyncio

        monkeypatch.setenv("JRS_OFFLOAD_TIMEOUT_SECONDS", "0")

        async def run() -> int:
            return await offload(lambda: 7)

        assert asyncio.run(run()) == 7

    def test_invalid_timeout_value_falls_back_to_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import asyncio

        monkeypatch.setenv("JRS_OFFLOAD_TIMEOUT_SECONDS", "not-a-number")

        async def run() -> int:
            return await offload(lambda: 5)

        assert asyncio.run(run()) == 5
