"""QA requirement 13: deterministic repeated calculations.

Identical input must produce bit-identical output, including when different
configurations are interleaved (proves per-call state discipline of the
provider, which owns process-global C-library state).
"""

from __future__ import annotations

from tests.integration.astronomy.conftest import make_request

from astronomy.models import Ayanamsa, CalculationConfig


def test_same_request_twice_bit_identical(service):
    first = service.compute(make_request())
    second = service.compute(make_request())
    assert first.positions == second.positions
    assert first.to_dict() == second.to_dict()


def test_interleaved_configs_do_not_leak_state(service):
    lahir = CalculationConfig(ayanamsa=Ayanamsa.LAHIRI)
    raman = CalculationConfig(ayanamsa=Ayanamsa.RAMAN)

    isolated_lahiri = service.compute(make_request(config=lahir))
    service.compute(make_request(config=raman))
    # Interleave: lahir, raman, lahir again.
    service.compute(make_request(config=lahir))
    service.compute(make_request(config=raman))
    re_lahiri = service.compute(make_request(config=lahir))

    assert re_lahiri.positions == isolated_lahiri.positions
    assert re_lahiri.to_dict() == isolated_lahiri.to_dict()
    assert re_lahiri.config.ayanamsa is Ayanamsa.LAHIRI


def test_repeated_calls_do_not_grow(service):
    """The registry freezes after the first compute; calls stay stable."""
    first = service.compute(make_request())
    registry_ids = service.registry.provider_ids
    for _ in range(5):
        service.compute(make_request())
    assert service.registry.provider_ids == registry_ids
    assert service.compute(make_request()).positions == first.positions
