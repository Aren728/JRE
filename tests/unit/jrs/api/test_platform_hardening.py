"""Phase 6 (Track B): Platform hardening contract tests.

Covers the three Track B deliverables:

- strict Pydantic DTOs (``extra="forbid"`` on birth-data input, range
  validation on the chart request);
- native OpenAPI 3.1 emission with stable operationIds and resolvable
  contract components;
- the async offload path that keeps blocking ephemeris/pipeline work
  off the event loop without changing endpoint signatures.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from jrs.api.main import _offload, app
from jrs.api.schemas import BirthDataInput, ChartRequest

client = TestClient(app)
_AUTH = {"X-API-Key": "jre-beta-key-alpha"}

_CANONICAL_BIRTH = {
    "date": "1990-01-15",
    "time": "14:30:00",
    "latitude": 40.7128,
    "longitude": -74.006,
    "timezone": "America/New_York",
}


# ── Strict DTOs ─────────────────────────────────────────────────────────────
class TestStrictDTOs:
    def test_birth_data_input_rejects_unknown_fields(self) -> None:
        with pytest.raises(ValidationError):
            BirthDataInput(**_CANONICAL_BIRTH, nonsense_field=1)

    def test_birth_data_input_accepts_canonical_payload(self) -> None:
        parsed = BirthDataInput(**_CANONICAL_BIRTH)
        assert parsed.language == "en"
        assert parsed.time == "14:30:00"

    def test_chart_request_range_validation(self) -> None:
        with pytest.raises(ValidationError):
            ChartRequest(
                query_date="1990-01-15",
                query_time="12:00:00",
                latitude=95.0,  # out of range
                longitude=0.0,
                timezone="UTC",
            )

    def test_chart_request_accepts_valid_payload(self) -> None:
        parsed = ChartRequest(
            query_date="1990-01-15",
            query_time="12:00:00",
            latitude=28.6139,
            longitude=77.209,
            timezone="Asia/Kolkata",
        )
        assert parsed.query_date.year == 1990

    def test_endpoint_rejects_unknown_fields_with_422(self) -> None:
        response = client.post(
            "/api/v1/evaluate/custom",
            json={**_CANONICAL_BIRTH, "nonsense_field": 1},
            headers=_AUTH,
        )
        assert response.status_code == 422


# ── OpenAPI 3.1 contract ────────────────────────────────────────────────────
class TestOpenAPI31:
    @staticmethod
    def _schema() -> dict:
        return app.openapi()

    def test_openapi_version_is_3_1(self) -> None:
        assert self._schema()["openapi"].startswith("3.1")

    def test_all_operations_carry_operation_ids(self) -> None:
        schema = self._schema()
        missing = [
            f"{method.upper()} {path}"
            for path, methods in schema["paths"].items()
            for method in methods
            if method in {"get", "post", "put", "patch", "delete"}
            and not methods[method].get("operationId")
        ]
        assert missing == []

    def test_contract_components_resolvable(self) -> None:
        schema = self._schema()
        components = schema["components"]["schemas"]
        for marker in ("BirthDataInput", "EvaluationResponse", "ChartRequest"):
            assert marker in components, marker

    def test_no_dangling_refs(self) -> None:
        import json
        import re

        schema = self._schema()
        raw = json.dumps(schema)
        refs = set(
            re.findall(r'"\$ref":\s*"#/components/schemas/([^"]+)"', raw)
        )
        dangling = refs - set(schema["components"]["schemas"])
        assert dangling == set()


# ── Async offload ───────────────────────────────────────────────────────────
class TestAsyncOffload:
    def test_offload_returns_value_with_type_inference(self) -> None:
        async def run() -> int:
            return await _offload(lambda a, b: a + b, 2, 3)

        assert asyncio.run(run()) == 5

    def test_offload_preserves_exceptions(self) -> None:
        def boom() -> None:
            raise ValueError("boom")

        async def run() -> None:
            await _offload(boom)

        with pytest.raises(ValueError, match="boom"):
            asyncio.run(run())

    def test_evaluate_fixture_end_to_end(self) -> None:
        response = client.post(
            "/api/v1/evaluate/fixture",
            json={"fixture_id": "chart_001_pilot", "language": "en"},
            headers=_AUTH,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["evaluation_id"]
        assert body["lagna"]
        assert isinstance(body["yogas"], list)
