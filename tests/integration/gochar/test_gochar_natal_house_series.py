"""Interval natal-frame house series tests (TEST-PLAN row 16, SPEC §12.3).

``natal_house_series=true`` with a ``natal_anchor`` yields per-sample
natal-frame house facts (JRE-005 echo) in ascending sample-JD order with
canonical bodies per sample; without an anchor it raises.
"""

from __future__ import annotations

import json

import pytest

from gochar import (
    GocharConfig,
    GocharIntervalRequest,
    InvalidGocharRequestError,
    result_to_json,
)
from jyotish import BodyId


def test_natal_house_series_gated_on_anchor(gochar_service, birth) -> None:
    """SPEC §8 / DC §5 — natal_house_series=true requires a natal anchor."""
    req = GocharIntervalRequest(
        start_utc_iso="2026-06-01T00:00:00.000000Z",
        end_utc_iso="2026-06-03T00:00:00.000000Z",
        bodies=(BodyId.SUN,),
        config=GocharConfig(natal_house_series=True),
    )
    with pytest.raises(InvalidGocharRequestError, match="natal_anchor"):
        gochar_service.analyze_interval(req)


def test_natal_house_series_echo(gochar_service, birth) -> None:
    """TEST-PLAN row 16 — per-sample natal-frame house facts in ascending
    sample-JD order, canonical bodies per sample."""
    req = GocharIntervalRequest(
        start_utc_iso="2026-06-01T00:00:00.000000Z",
        end_utc_iso="2026-06-03T00:00:00.000000Z",
        bodies=(BodyId.SUN, BodyId.MOON),
        natal_anchor=birth,
        config=GocharConfig(natal_house_series=True, sample_step_hours=24.0),
    )
    result = gochar_service.analyze_interval(req)
    assert result.natal_house_series is not None
    payload = json.loads(result_to_json(result))["natal_house_series"]
    # One TransitHouseAnalysis per daily sample (2026-06-01..03).
    assert len(payload) == 3
    instants = [s["transit_instant_utc_iso"] for s in payload]
    assert instants == sorted(instants)
    # Each entry is a full JRE-005 analysis echo (provenance-bearing).
    assert payload[0]["transit_facts"]
    assert payload[0]["chart_echo"]["house_system"] == "WHOLE_SIGN"
    # Canonical transit body order per sample: SUN then MOON.
    bodies = [f["body"] for f in payload[0]["transit_facts"]]
    assert bodies[:2] == ["SUN", "MOON"]


def test_natal_house_series_disabled_by_default(gochar_service, birth) -> None:
    req = GocharIntervalRequest(
        start_utc_iso="2026-06-01T00:00:00.000000Z",
        end_utc_iso="2026-06-03T00:00:00.000000Z",
        bodies=(BodyId.SUN,),
        natal_anchor=birth,
    )
    result = gochar_service.analyze_interval(req)
    assert result.natal_house_series is None
