"""Derivation tests (TEST-PLAN §2 row 4-9, SPEC §3/§16).

V1 boundary: no candidate expansion, no uncertainty metadata, no
missing-section model — only chart identity, civil-UTC validation,
canonical body order, the six-stage provenance chain (actual provenance
separated from reserved future stages), and the pure snapshot assembly
(``natal_chart`` echoed verbatim, never reconstructed).
"""

from __future__ import annotations

import pytest
from tests.unit.bhava.conftest import make_birth
from tests.unit.context.conftest import make_event

from bhava import BhavaConfig, derive_house_analysis
from context import (
    ContextConfig,
    assemble_snapshot,
    build_provenance,
    canonical_bodies,
    chart_identity,
    civil_split,
)
from context.errors import InvalidContextRequestError
from jyotish import (
    BirthData,
    BodyId,
    JyotishConfig,
)

BIRTH = make_birth()


def test_chart_identity_deterministic_and_sensitive() -> None:
    jyotish_cfg = JyotishConfig()
    bhava_cfg = BhavaConfig()
    catalogs = {"rashi": "1.0.0", "nakshatra": "1.0.0"}

    a = chart_identity(
        birth=BIRTH,
        jyotish_config=jyotish_cfg,
        bhava_config=bhava_cfg,
        catalog_versions=catalogs,
    )
    b = chart_identity(
        birth=BIRTH,
        jyotish_config=jyotish_cfg,
        bhava_config=bhava_cfg,
        catalog_versions=catalogs,
    )
    assert a == b  # deterministic
    assert len(a) == 64  # sha256 hex

    other_birth = BirthData(
        date="1991-07-16", time="11:30:00", timezone="Asia/Kolkata",
        latitude=19.076, longitude=72.8777,
    )
    assert chart_identity(
        birth=other_birth,
        jyotish_config=jyotish_cfg,
        bhava_config=bhava_cfg,
        catalog_versions=catalogs,
    ) != a
    assert chart_identity(
        birth=BIRTH,
        jyotish_config=JyotishConfig(house_system=JyotishConfig().house_system),
        bhava_config=bhava_cfg,
        catalog_versions={"rashi": "2.0.0", "nakshatra": "1.0.0"},
    ) != a
    same = chart_identity(
        birth=BIRTH,
        jyotish_config=jyotish_cfg,
        bhava_config=bhava_cfg,
        catalog_versions=catalogs,
    )
    assert same == a


def test_build_provenance_chain() -> None:
    prov = build_provenance(
        birth=BIRTH,
        ephemeris_version="18",
        jyotish_config=JyotishConfig(),
        has_house_analysis=True,
        has_gochar=False,
        tradition_profile=None,
        catalog_versions={"rashi": "1.0.0", "nakshatra": "1.0.0"},
        context_config=ContextConfig(),
        algorithm="assemble-natal-v1",
    )
    stages = [s.stage for s in prov.stages]
    # Without a tradition profile, no DOCTRINE_RULE stage is claimed —
    # JRE-007 performs no doctrine evaluation (SPEC §16).
    assert stages == [
        "INPUT", "ASTRONOMICAL", "NORMALIZATION", "DERIVED", "FUTURE_INFERENCE",
    ]
    assert prov.source_layers == ("JRE-002", "JRE-003", "JRE-005")
    assert prov.assembly_algorithm == "assemble-natal-v1"
    assert prov.snapshot_version == "0.1.0"
    derived = [s for s in prov.stages if s.stage == "DERIVED"]
    assert [s.layer_id for s in derived] == ["JRE-005"]
    # No stage falsely claims JRE-004 production.
    assert all(s.layer_id != "JRE-004" for s in prov.stages)
    # FUTURE_INFERENCE is a reserved placeholder, never a producer.
    future = [s for s in prov.stages if s.stage == "FUTURE_INFERENCE"][0]
    assert future.layer_id is None
    assert future.algorithm == "reserved"


def test_build_provenance_gochar_and_tradition() -> None:
    prov = build_provenance(
        birth=None,
        ephemeris_version="18",
        jyotish_config=JyotishConfig(),
        has_house_analysis=False,
        has_gochar=True,
        tradition_profile="bphs-classical",
        catalog_versions={"rashi": "1.0.0", "nakshatra": "1.0.0"},
        context_config=ContextConfig(),
        algorithm="assemble-instant-v1",
    )
    assert prov.source_layers == ("JRE-002", "JRE-003", "JRE-006")
    derived = [s for s in prov.stages if s.stage == "DERIVED"]
    assert [s.layer_id for s in derived] == ["JRE-006"]
    # DOCTRINE_RULE appears only because a profile was actually applied.
    doctrine = [s for s in prov.stages if s.stage == "DOCTRINE_RULE"][0]
    assert doctrine.layer_id == "JRE-004"
    assert doctrine.version == "bphs-classical"
    future = [s for s in prov.stages if s.stage == "FUTURE_INFERENCE"][0]
    assert future.layer_id is None
    assert future.algorithm == "reserved"


def test_civil_split() -> None:
    date, time = civil_split("2026-06-15T12:00:00.000000Z")
    assert date.isoformat() == "2026-06-15"
    assert time.isoformat() == "12:00:00"
    with pytest.raises(InvalidContextRequestError):
        civil_split("2026-06-15")  # date-only rejected
    with pytest.raises(InvalidContextRequestError):
        civil_split("2026-06-15T12:00:00+05:30")  # non-UTC rejected


def test_canonical_bodies() -> None:
    assert canonical_bodies((BodyId.MOON, BodyId.SUN)) == (BodyId.SUN, BodyId.MOON)
    assert canonical_bodies((BodyId.SUN, BodyId.SUN)) == (BodyId.SUN,)
    assert canonical_bodies(()) == ()


def test_assemble_snapshot_instant(fake_jyotish) -> None:
    from jyotish import PlanetState

    states = fake_jyotish.planetary_state(
        __import__("datetime").date(2026, 6, 15),
        __import__("datetime").time(12, 0, 0),
        "UTC", 0.0, 0.0, (BodyId.SUN, BodyId.MOON), JyotishConfig(),
    )
    snapshot = assemble_snapshot(
        birth=None,
        time_precision="EXACT",
        planet_states=states,
        pair_geometry=(),
        jyotish_config=JyotishConfig(),
        bhava_config=BhavaConfig(),
        context_config=ContextConfig(),
        algorithm="assemble-instant-v1",
    )
    assert snapshot.natal_chart is None
    assert snapshot.planet_states == states
    assert snapshot.pair_geometry == ()
    assert snapshot.house_analyses is None
    assert snapshot.transit_events is None
    assert snapshot.state_samples is None
    assert snapshot.eclipses is None
    assert snapshot.provenance.source_layers == ("JRE-002", "JRE-003")
    assert isinstance(snapshot.planet_states, tuple)
    assert all(isinstance(s, PlanetState) for s in snapshot.planet_states)


def test_assemble_snapshot_natal(fake_jyotish) -> None:
    from tests.unit.bhava.conftest import make_whole_sign_chart

    chart = make_whole_sign_chart()
    house_analysis = derive_house_analysis(chart, config=BhavaConfig())
    snapshot = assemble_snapshot(
        birth=BIRTH,
        time_precision="EXACT",
        planet_states=chart.planet_states,
        natal_chart=chart,
        pair_geometry=(),
        house_analysis=house_analysis,
        jyotish_config=JyotishConfig(),
        bhava_config=BhavaConfig(),
        context_config=ContextConfig(),
        algorithm="assemble-natal-v1",
    )
    # The snapshot holds the exact JRE-003 chart value — never a
    # reconstructed replacement (SPEC §2/§23).
    assert snapshot.natal_chart == chart
    assert snapshot.natal_chart.bhavas == chart.bhavas
    assert snapshot.natal_chart.lagna == chart.lagna
    assert snapshot.house_analyses == (house_analysis,)
    assert snapshot.planet_states == chart.planet_states
    assert snapshot.provenance.source_layers == ("JRE-002", "JRE-003", "JRE-005")


def test_assemble_snapshot_natal_chart_echo_preserves_provider_metadata() -> None:
    """NatalChart provider metadata must never be dropped: the echo is the
    lower-layer object/value, not a reconstruction (SPEC §23)."""
    from dataclasses import replace

    from tests.unit.bhava.conftest import make_whole_sign_chart

    from astronomy.models import ProviderMetadata

    chart = make_whole_sign_chart()
    chart = replace(
        chart,
        provider_metadata=(
            ProviderMetadata(
                provider_id="swe.test",
                library_name="pysweph",
                library_version="2.10",
                ephemeris_version="18",
            ),
        ),
    )
    house_analysis = derive_house_analysis(chart, config=BhavaConfig())
    snapshot = assemble_snapshot(
        birth=BIRTH,
        time_precision="EXACT",
        planet_states=chart.planet_states,
        natal_chart=chart,
        house_analysis=house_analysis,
        jyotish_config=JyotishConfig(),
        bhava_config=BhavaConfig(),
        context_config=ContextConfig(),
        algorithm="assemble-natal-v1",
    )
    assert snapshot.natal_chart == chart
    assert snapshot.natal_chart.provider_metadata == chart.provider_metadata
    assert len(snapshot.natal_chart.provider_metadata) == 1
    assert snapshot.natal_chart.provider_metadata[0].provider_id == "swe.test"


def test_assemble_snapshot_interval(fake_jyotish) -> None:
    events = (make_event(),)
    snapshot = assemble_snapshot(
        birth=None,
        time_precision="EXACT",
        planet_states=(),
        transit_events=events,
        state_samples=(),
        jyotish_config=JyotishConfig(),
        bhava_config=BhavaConfig(),
        context_config=ContextConfig(),
        algorithm="assemble-interval-v1",
    )
    assert snapshot.transit_events == events
    assert snapshot.state_samples == ()
    assert snapshot.natal_chart is None
    assert snapshot.house_analyses is None


def test_assemble_snapshot_eclipses(fake_jyotish) -> None:
    from dataclasses import replace

    from jyotish import EclipseClassification, EclipseEvent, EclipseKind

    event = EclipseEvent(
        kind=EclipseKind.SOLAR,
        classification=None,
        maximum_jd_ut=2460462.0,
        maximum_utc_iso="2026-06-15T00:00:00.000000Z",
        contacts=(),
        magnitude=0.5,
        node_positions=(),
        solar_lunar_positions=(),
        geographic_visibility=None,
        pre_event_interval_days=1.0,
        post_event_interval_days=1.0,
        provider_id="fake.eclipse",
        ephemeris_version="18",
    )
    event = replace(event, classification=EclipseClassification.PARTIAL)
    snapshot = assemble_snapshot(
        birth=None,
        time_precision="EXACT",
        planet_states=(),
        eclipses=(event,),
        jyotish_config=JyotishConfig(),
        bhava_config=BhavaConfig(),
        context_config=ContextConfig(),
        algorithm="assemble-eclipses-v1",
    )
    assert snapshot.eclipses == (event,)
    assert snapshot.transit_events is None
    assert snapshot.pair_geometry is None


def test_assemble_snapshot_validates_precision() -> None:
    with pytest.raises(InvalidContextRequestError):
        assemble_snapshot(
            birth=None,
            time_precision="BOGUS",
            planet_states=(),
            jyotish_config=JyotishConfig(),
            bhava_config=BhavaConfig(),
            context_config=ContextConfig(),
            algorithm="assemble-instant-v1",
        )
