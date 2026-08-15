"""Provenance tests (TEST-PLAN §2 row 19, SPEC §9.1, ADR-028).

Every result carries a ``GocharProvenance`` with a stable derivation id,
pinned derivation/package/catalog/ephemeris versions, an input echo, and
the algorithm label. No environment-dependent data (wall-clock, random,
PIDs, environment).
"""

from __future__ import annotations

from gochar import (
    GocharConfig,
    GocharInstantRequest,
    GocharIntervalRequest,
    GocharNatalRequest,
    GocharService,
    build_provenance,
)
from jyotish import BirthData, BodyId

BIRTH = BirthData(
    date="1990-06-15",
    time="10:00:00",
    timezone="Asia/Kolkata",
    latitude=28.6139,
    longitude=77.2090,
)


def test_build_provenance_fields() -> None:
    prov = build_provenance(
        derivation_id="gochar.instant.v1",
        source_layers=("JRE-002", "JRE-003"),
        input_echo={"instant_utc_iso": "2026-06-15T12:00:00.000000Z", "bodies": ["SUN"]},
        algorithm="echo-jre003-planetary-state",
        ephemeris_version="18",
        config=GocharConfig(),
    )
    assert prov.derivation_id == "gochar.instant.v1"
    assert prov.derivation_version == "0.2.0"
    assert prov.source_layers == ("JRE-002", "JRE-003")
    assert prov.gochar_version == "0.2.0"
    assert prov.jyotish_version
    assert prov.bhava_version
    assert prov.ephemeris_version == "18"
    assert set(prov.catalog_versions) == {"rashi", "nakshatra"}
    assert prov.algorithm == "echo-jre003-planetary-state"


def test_instant_provenance_source_layers(fake_service) -> None:
    svc = GocharService(fake_service)
    result = svc.analyze_instant(
        GocharInstantRequest(
            instant_utc_iso="2026-06-15T12:00:00.000000Z", bodies=(BodyId.SUN,)
        )
    )
    assert result.provenance.source_layers == ("JRE-002", "JRE-003")
    assert result.provenance.derivation_id == "gochar.instant.v1"


def test_natal_provenance_source_layers(fake_service) -> None:
    svc = GocharService(fake_service)
    result = svc.analyze_natal(
        GocharNatalRequest(
            birth=BIRTH,
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=(BodyId.SUN,),
        )
    )
    assert result.provenance.source_layers == ("JRE-002", "JRE-003", "JRE-005")
    assert result.provenance.derivation_id == "gochar.natal.v1"
    assert result.provenance.algorithm == "derive-transit-houses-jre005+echo-jre003-pair-geometry"


def test_interval_provenance_source_layers(fake_service) -> None:
    svc = GocharService(fake_service)
    result = svc.analyze_interval(
        GocharIntervalRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-06-15T00:00:00.000000Z",
            bodies=(BodyId.SUN,),
        )
    )
    assert result.provenance.source_layers == ("JRE-002", "JRE-003")
    assert result.provenance.derivation_id == "gochar.interval.v1"
    assert result.provenance.algorithm == (
        "echo-jre003-events-bisection+echo-jre003-state-series"
    )


def test_interval_natal_provenance_algorithm(fake_service) -> None:
    svc = GocharService(fake_service)
    result = svc.analyze_interval(
        GocharIntervalRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-06-03T00:00:00.000000Z",
            bodies=(BodyId.SUN,),
            natal_anchor=BIRTH,
            config=GocharConfig(natal_house_series=True, sample_step_hours=24.0),
        )
    )
    assert result.provenance.source_layers == ("JRE-002", "JRE-003", "JRE-005")
    assert result.provenance.algorithm.endswith("+derive-transit-houses-jre005")
    assert result.provenance.input_echo["natal_house_series"] is True


def test_provenance_input_echo_contents(fake_service) -> None:
    svc = GocharService(fake_service)
    result = svc.analyze_interval(
        GocharIntervalRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-06-15T00:00:00.000000Z",
            bodies=(BodyId.MOON, BodyId.SUN),
            config=GocharConfig(reference_point="MOON", sample_step_hours=12.0),
        )
    )
    echo = result.provenance.input_echo
    assert echo["start_utc_iso"] == "2026-06-01T00:00:00.000000Z"
    assert echo["end_utc_iso"] == "2026-06-15T00:00:00.000000Z"
    assert echo["bodies"] == ["SUN", "MOON"]  # canonical order
    assert echo["reference_point"] == "MOON"
    assert echo["house_system"] == "WHOLE_SIGN"
    assert echo["sample_step_hours"] == 12.0
    assert echo["aspect_echo"] is True
    assert echo["natal_house_series"] is False


def test_provenance_is_deterministic(fake_service) -> None:
    svc = GocharService(fake_service)
    req = GocharInstantRequest(
        instant_utc_iso="2026-06-15T12:00:00.000000Z", bodies=(BodyId.SUN,)
    )
    a = svc.analyze_instant(req).provenance
    b = svc.analyze_instant(req).provenance
    assert a == b
    assert a.input_echo == b.input_echo
    assert a.catalog_versions == b.catalog_versions
