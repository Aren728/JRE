"""QA requirement 8: ayanamsa configuration.

- LAHIRI / RAMAN / FAGAN_BRADLEY each produce stable values; the sidereal
  longitude is longitude_tropical - ayanamsa_value (within the documented
  deviation: the library applies the sidereal correction without nutation in
  longitude, so the two reconcile only to ~0.01 deg — see swisseph/provider.py).
- ayanamsa=None => longitude_sidereal is None and ayanamsa_value is None.
"""

from __future__ import annotations

import pytest
from tests.integration.astronomy.conftest import make_request

from astronomy.models import Ayanamsa, BodyId, CalculationConfig

# Documented tolerance for tropical - ayanamsa vs the library's FLG_SIDEREAL
# output (nutation-in-longitude deviation; ~0.01 deg expected).
SIDEREAL_RECONCILE_TOLERANCE_DEG = 0.05


def _sidereal_of(result, body=BodyId.SUN):
    return next(p for p in result.positions if p.body is body)


@pytest.mark.parametrize(
    "ayanamsa",
    [Ayanamsa.LAHIRI, Ayanamsa.RAMAN, Ayanamsa.FAGAN_BRADLEY],
)
def test_ayanamsa_modes_produce_sidereal(service, ayanamsa):
    result = service.compute(make_request(config=CalculationConfig(ayanamsa=ayanamsa)))
    sun = _sidereal_of(result)
    assert sun.longitude_sidereal is not None
    assert sun.ayanamsa_value is not None
    assert 0.0 <= sun.longitude_sidereal < 360.0
    assert 0.0 < sun.ayanamsa_value < 30.0  # any ayanamsa in the modern era
    # sidereal = tropical - ayanamsa (mod 360), within documented deviation
    diff = (sun.longitude_tropical - sun.ayanamsa_value - sun.longitude_sidereal) % 360.0
    assert min(diff, 360.0 - diff) < SIDEREAL_RECONCILE_TOLERANCE_DEG


def test_ayanamsa_none_means_tropical_only(service):
    result = service.compute(make_request(config=CalculationConfig(ayanamsa=None)))
    for pos in result.positions:
        assert pos.longitude_sidereal is None
        assert pos.ayanamsa_value is None


def test_ayanamsa_values_are_stable_across_calls(service):
    config = CalculationConfig(ayanamsa=Ayanamsa.LAHIRI)
    first = service.compute(make_request(config=config))
    second = service.compute(make_request(config=config))
    assert first.positions == second.positions


def test_ayanamsa_values_differ_by_mode(service):
    values = {}
    for ayanamsa in (Ayanamsa.LAHIRI, Ayanamsa.RAMAN, Ayanamsa.FAGAN_BRADLEY):
        result = service.compute(make_request(config=CalculationConfig(ayanamsa=ayanamsa)))
        values[ayanamsa] = _sidereal_of(result).ayanamsa_value
    assert values[Ayanamsa.LAHIRI] is not None
    assert values[Ayanamsa.RAMAN] is not None
    assert values[Ayanamsa.FAGAN_BRADLEY] is not None
    # Distinct modes must not all collapse to one value.
    assert len({round(v, 4) for v in values.values()}) > 1


def test_ayanamsa_override_accepted_and_deterministic(service):
    """swe.set_sid_mode ignores t0/ayanamsa_t0 for predefined modes (the
    override applies only to a user-defined SIDM_USER mode, which the current
    Ayanamsa enum does not expose). The contract here is that the override is
    accepted without error and the result stays internally consistent and
    deterministic."""
    config = CalculationConfig(
        ayanamsa=Ayanamsa.LAHIRI,
        ayanamsa_override=(2451545.0, 24.0),
    )
    first = service.compute(make_request(config=config))
    second = service.compute(make_request(config=config))
    assert first.positions == second.positions
    sun = _sidereal_of(first)
    # Still Lahiri-consistent: sidereal = tropical - ayanamsa (mod 360).
    diff = (sun.longitude_tropical - sun.ayanamsa_value - sun.longitude_sidereal) % 360.0
    assert min(diff, 360.0 - diff) < SIDEREAL_RECONCILE_TOLERANCE_DEG
