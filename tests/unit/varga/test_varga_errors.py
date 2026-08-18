"""Error taxonomy tests (normative specification §19, §26).

Typed errors only: no raw ``ValueError``/``KeyError`` escapes the public
surface for malformed configuration, malformed requests, or invalid
definitions.
"""

from __future__ import annotations

import pytest
from tests.unit.varga.conftest import make_raw_state, make_state

from jyotish import BodyId, RashiId
from varga import (
    InvalidVargaConfigError,
    InvalidVargaRequestError,
    VargaComputationError,
    VargaError,
    VargaService,
    compute_varga_position,
    get_varga_definition,
    validate_schema,
)
from varga.serialize import schema_for


def test_error_hierarchy() -> None:
    assert issubclass(InvalidVargaConfigError, VargaError)
    assert issubclass(InvalidVargaRequestError, VargaError)
    assert issubclass(VargaComputationError, VargaError)


def test_message_preserved() -> None:
    assert str(InvalidVargaConfigError("bad config")) == "bad config"
    assert str(InvalidVargaRequestError("bad request")) == "bad request"


def test_no_raw_valueerror_escapes_surface() -> None:
    # Config.
    with pytest.raises(VargaError):
        VargaService().config.__class__(default_zodiac_mode="BOGUS")  # type: ignore[arg-type]
    with pytest.raises(VargaError):
        from varga import VargaConfig

        VargaConfig(default_boundary_convention="NOPE")
    # Request.
    with pytest.raises(VargaError):
        VargaService().compute_varga_chart((), "D9")
    with pytest.raises(VargaError):
        VargaService().compute_varga_chart((make_state(),), "D27")
    # Derivation input range.
    with pytest.raises(VargaError):
        compute_varga_position(make_raw_state(30.0), get_varga_definition("D9"))
    with pytest.raises(VargaError):
        compute_varga_position(make_raw_state(-1.0), get_varga_definition("D9"))
    # Schema.
    with pytest.raises(VargaError):
        validate_schema({"surprise": 1}, schema_for("VargaChart"))
    with pytest.raises(VargaError):
        schema_for("BOGUS")


def test_out_of_range_degree_typed_error() -> None:
    for degree in (30.0, 30.0001, -0.0001, -5.0, 99.0):
        with pytest.raises(InvalidVargaRequestError):
            compute_varga_position(
                make_raw_state(degree), get_varga_definition("D60")
            )


def test_duplicate_body_deduplicated() -> None:
    svc = VargaService()
    states = (make_state(RashiId.MESHA, 5.0, body=BodyId.SUN),) * 3
    chart = svc.compute_varga_chart(states, "D9")
    assert len(chart.positions) == 1
