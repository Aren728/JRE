"""Service composition tests (normative specification §16-§17, §19).

``VargaService.compute_varga_chart`` produces the standalone deterministic
``VargaChart``: canonical body ordering, per-position provenance tracing
JRE-003 input -> definition -> method -> position, domain-separated
identities, and an optional opaque JRE-007 join reference. Different
methods never merge.
"""

from __future__ import annotations

import pytest
from tests.unit.varga.conftest import make_state

from jyotish import BodyId, RashiId
from varga import (
    VargaService,
    canonical_body_order,
    compute_varga_position,
    get_varga_definition,
    varga_chart_identity,
    varga_definition_identity,
    varga_position_identity,
)
from varga.errors import InvalidVargaRequestError


def _states():
    return (
        make_state(RashiId.MESHA, 5.0, body=BodyId.SUN),
        make_state(RashiId.MAKARA, 13.4166666667, body=BodyId.MOON),
        make_state(RashiId.SIMHA, 25.0, body=BodyId.MARS),
    )


def test_compute_varga_chart_basic() -> None:
    svc = VargaService()
    chart = svc.compute_varga_chart(_states(), "D9")
    assert chart.varga_id == "D9"
    assert chart.method_id == "d9-bphs-v1"
    assert len(chart.positions) == 3
    # Canonical body order: SUN, MOON, MARS.
    assert [p.body for p in chart.positions] == [BodyId.SUN, BodyId.MOON, BodyId.MARS]
    assert chart.varga_chart_identity
    assert chart.varga_definition_identity
    assert chart.context_chart_identity is None
    assert len(chart.varga_chart_identity) == 64


def test_canonical_body_order_deterministic() -> None:
    states = _states()
    assert canonical_body_order(states[::-1]) == canonical_body_order(states)
    assert [p.body for p in canonical_body_order(states)] == [
        BodyId.SUN, BodyId.MOON, BodyId.MARS,
    ]
    # Duplicates are deduplicated.
    dup = canonical_body_order(states + states[:1])
    assert len(dup) == 3


def test_context_chart_identity_join_reference() -> None:
    svc = VargaService()
    chart = svc.compute_varga_chart(
        _states(), "D9", context_chart_identity="deadbeef" * 8
    )
    assert chart.context_chart_identity == "deadbeef" * 8
    # The join reference is a source-chart identity and therefore part of
    # the chart identity (spec §16: identity changes when the source chart
    # identity changes) — but it never reaches the per-position facts.
    plain = svc.compute_varga_chart(_states(), "D9")
    assert chart.varga_chart_identity != plain.varga_chart_identity
    assert chart.positions == plain.positions


def test_invalid_context_identity_rejected() -> None:
    svc = VargaService()
    with pytest.raises(InvalidVargaRequestError):
        svc.compute_varga_chart(_states(), "D9", context_chart_identity="")
    with pytest.raises(InvalidVargaRequestError):
        svc.compute_varga_chart(_states(), "D9", context_chart_identity=123)  # type: ignore[arg-type]


def test_empty_states_rejected() -> None:
    svc = VargaService()
    with pytest.raises(InvalidVargaRequestError):
        svc.compute_varga_chart((), "D9")
    with pytest.raises(InvalidVargaRequestError):
        svc.compute_varga_chart(("not-a-state",), "D9")  # type: ignore[arg-type]


def test_unknown_varga_and_method_rejected() -> None:
    svc = VargaService()
    with pytest.raises(InvalidVargaRequestError):
        svc.compute_varga_chart(_states(), "D27")
    with pytest.raises(InvalidVargaRequestError):
        svc.compute_varga_chart(_states(), "D9", method_id="d9-bogus-v1")


def test_provenance_chain_complete() -> None:
    svc = VargaService()
    chart = svc.compute_varga_chart(_states(), "D60")
    for position in chart.positions:
        provenance = position.provenance
        # JRE-003 input -> definition -> method -> position.
        assert provenance.source_state_id == position.source_state_id
        assert provenance.varga_method_id == "d60-bphs-v1"
        assert provenance.varga_definition_version == chart.definition_version
        assert provenance.source_citations  # source-cited
        assert provenance.provider_id == "fake.astronomy"
        assert provenance.ephemeris_version == "18"
        assert provenance.boundary_convention.value == "HALF_OPEN_LOW"
        assert provenance.tradition_profile is None
        # No wall-clock / randomness in provenance.
        assert "time" not in provenance.to_dict()
        assert "random" not in provenance.to_dict()


def test_d20_method_variants_never_merge() -> None:
    svc = VargaService()
    states = (make_state(RashiId.SIMHA, 25.0),)
    bphs = svc.compute_varga_chart(states, "D20")
    variant = svc.compute_varga_chart(states, "D20", method_id="d20-saravali-variant-v1")
    assert bphs.method_id == "d20-bphs-v1"
    assert variant.method_id == "d20-saravali-variant-v1"
    assert bphs.varga_chart_identity != variant.varga_chart_identity
    assert bphs.positions[0].position_id != variant.positions[0].position_id
    assert bphs.positions[0].varga_sign != variant.positions[0].varga_sign


def test_identities_sensitive_to_calculation_inputs() -> None:
    state = make_state(RashiId.MESHA, 5.0)
    base = compute_varga_position(state, get_varga_definition("D9"))
    other_degree = compute_varga_position(
        make_state(RashiId.MESHA, 5.5), get_varga_definition("D9")
    )
    other_varga = compute_varga_position(state, get_varga_definition("D20"))
    assert base.position_id != other_degree.position_id
    assert base.position_id != other_varga.position_id
    assert varga_position_identity(base) == base.position_id


def test_chart_identity_changes_with_varga_and_method() -> None:
    svc = VargaService()
    d9 = svc.compute_varga_chart(_states(), "D9")
    d16 = svc.compute_varga_chart(_states(), "D16")
    assert d9.varga_chart_identity != d16.varga_chart_identity
    assert varga_chart_identity(d9) == d9.varga_chart_identity


def test_definition_identity_changes_with_method_version() -> None:
    a = varga_definition_identity(get_varga_definition("D9"))
    b = varga_definition_identity(get_varga_definition("D16"))
    assert a != b
    assert len(a) == 64


def test_determinism_across_services() -> None:
    a = VargaService().compute_varga_chart(_states(), "D30")
    b = VargaService().compute_varga_chart(_states(), "D30")
    assert a.to_dict() == b.to_dict()
    assert a.varga_chart_identity == b.varga_chart_identity
