"""Integration tests for JRE-015 Avastha engine."""

from __future__ import annotations

from jyotish import BodyId

from avastha import AvasthaService, AvasthaReport
from avastha.models import JagradadiState, DeeptadiState
from tests.unit.avastha.conftest import make_sun_state, make_moon_state


class TestAvasthaIntegration:
    """Full Avastha computation against known reference states."""

    def test_all_planets_computed(self) -> None:
        svc = AvasthaService()
        states = (
            make_sun_state(10.0),
            make_moon_state(33.0),
        )
        report = svc.calculate_avasthas(states)
        assert len(report.results) == 2

    def test_sun_exalted_high_strength(self) -> None:
        svc = AvasthaService()
        # Sun at 3° Aries (exalted, jagrat)
        state = make_sun_state(3.0)
        report = svc.calculate_avasthas((state,))
        result = report.result_for(BodyId.SUN)
        assert result is not None
        assert result.jagradadi == JagradadiState.JAGRAT
        assert result.deeptadi == DeeptadiState.DEEPTA
        # multiplier = 1.0 * 1.0 = 1.0
        assert abs(result.multiplier - 1.0) < 1e-9

    def test_sun_debilitated_low_strength(self) -> None:
        svc = AvasthaService()
        # Sun at 20° Libra (debilitated, sushupti)
        state = make_sun_state(200.0)
        report = svc.calculate_avasthas((state,))
        result = report.result_for(BodyId.SUN)
        assert result is not None
        assert result.jagradadi == JagradadiState.SUSHUPTI
        assert result.deeptadi == DeeptadiState.KSHOBHITA
        # multiplier = 0.5 * 0.25 = 0.125
        assert abs(result.multiplier - 0.125) < 1e-9

    def test_deterministic_output(self) -> None:
        svc = AvasthaService()
        states = (make_sun_state(10.0),)
        r1 = svc.calculate_avasthas(states)
        r2 = svc.calculate_avasthas(states)
        assert r1.to_dict() == r2.to_dict()

    def test_report_to_dict_is_serializable(self) -> None:
        svc = AvasthaService()
        report = svc.calculate_avasthas((make_sun_state(10.0),))
        d = report.to_dict()
        assert isinstance(d, dict)
        assert "results" in d
