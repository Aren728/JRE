"""Instant GENERIC echo tests (TEST-PLAN §2 row 6, SPEC §10).

``GocharInstantResult`` echoes JRE-003 ``planetary_state`` output verbatim
(canonical body order filtered to requested bodies) plus the optional
``jyotish.all_pairs`` geometry echo, the ``config_echo`` block, and full
provenance. No birth data appears anywhere.
"""

from __future__ import annotations

from gochar import GocharConfig, GocharInstantRequest, GocharService, result_to_dict
from jyotish import BodyId


def _svc(fake_service):
    return GocharService(fake_service)


def test_instant_states_echo_canonical_order(fake_service) -> None:
    svc = _svc(fake_service)
    req = GocharInstantRequest(
        instant_utc_iso="2026-06-15T12:00:00.000000Z",
        bodies=(BodyId.MOON, BodyId.SUN),  # deliberately out of canonical order
    )
    result = svc.analyze_instant(req)
    # Canonical JRE-003 order (SUN, MOON), filtered to requested bodies.
    assert [state.body.value for state in result.planet_states] == ["SUN", "MOON"]
    assert result.instant_utc_iso == "2026-06-15T12:00:00.000000Z"
    assert "planetary_state" in fake_service.calls


def test_instant_echoes_states_verbatim(fake_service) -> None:
    svc = _svc(fake_service)
    req = GocharInstantRequest(
        instant_utc_iso="2026-06-15T12:00:00.000000Z", bodies=(BodyId.SUN,)
    )
    result = svc.analyze_instant(req)
    state = result.planet_states[0]
    assert state.body is BodyId.SUN
    assert state.rashi is not None
    assert state.nakshatra is not None
    assert state.pada is not None


def test_instant_pair_geometry_echo(fake_service) -> None:
    svc = _svc(fake_service)
    req = GocharInstantRequest(
        instant_utc_iso="2026-06-15T12:00:00.000000Z",
        bodies=(BodyId.SUN, BodyId.MOON, BodyId.MARS),
    )
    result = svc.analyze_instant(req)
    assert result.pair_geometry is not None
    assert len(result.pair_geometry) == 3  # C(3,2)
    # Pairs in canonical order (JRE-003 all_pairs).
    assert [g.first.value for g in result.pair_geometry] == ["SUN", "SUN", "MOON"]
    assert [g.second.value for g in result.pair_geometry] == ["MOON", "MARS", "MARS"]


def test_instant_aspect_echo_disabled(fake_service) -> None:
    svc = _svc(fake_service)
    req = GocharInstantRequest(
        instant_utc_iso="2026-06-15T12:00:00.000000Z",
        bodies=(BodyId.SUN, BodyId.MOON),
        config=GocharConfig(aspect_echo=False),
    )
    result = svc.analyze_instant(req)
    assert result.pair_geometry is None
    assert result.config_echo["aspect_echo"] is False


def test_instant_config_echo(fake_service) -> None:
    svc = _svc(fake_service)
    req = GocharInstantRequest(
        instant_utc_iso="2026-06-15T12:00:00.000000Z",
        bodies=(BodyId.SUN,),
        config=GocharConfig(reference_point="MOON", house_system="PLACIDUS"),
    )
    result = svc.analyze_instant(req)
    assert result.config_echo == {
        "reference_point": "MOON",
        "house_system": "PLACIDUS",
        "aspect_echo": True,
    }


def test_instant_contains_no_birth_data(fake_service) -> None:
    svc = _svc(fake_service)
    req = GocharInstantRequest(
        instant_utc_iso="2026-06-15T12:00:00.000000Z", bodies=(BodyId.SUN,)
    )
    result = svc.analyze_instant(req)
    payload = result_to_dict(result)
    assert "birth_snapshot" not in payload
    assert "birth" not in payload


def test_instant_provenance(fake_service) -> None:
    svc = _svc(fake_service)
    req = GocharInstantRequest(
        instant_utc_iso="2026-06-15T12:00:00.000000Z", bodies=(BodyId.SUN,)
    )
    result = svc.analyze_instant(req)
    prov = result.provenance
    assert prov.derivation_id == "gochar.instant.v1"
    assert prov.source_layers == ("JRE-002", "JRE-003")
    assert prov.gochar_version == "0.2.0"
    assert prov.algorithm == "echo-jre003-planetary-state+echo-jre003-pair-geometry"
    assert prov.input_echo["bodies"] == ["SUN"]
    assert prov.catalog_versions["rashi"]
    assert prov.catalog_versions["nakshatra"]
    assert prov.ephemeris_version


def test_instant_no_geometry_algorithm(fake_service) -> None:
    svc = _svc(fake_service)
    req = GocharInstantRequest(
        instant_utc_iso="2026-06-15T12:00:00.000000Z",
        bodies=(BodyId.SUN,),
        config=GocharConfig(aspect_echo=False),
    )
    result = svc.analyze_instant(req)
    assert result.provenance.algorithm == "echo-jre003-planetary-state"
