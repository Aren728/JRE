"""Unit tests for AvasthaService classical formulas."""

from __future__ import annotations

from jyotish import BodyId, RashiId

from avastha.models import (
    JagradadiState,
    DeeptadiState,
    DEFAULT_EXALTATION_SIGNS,
    DEFAULT_DEBILITATION_SIGNS,
    DEFAULT_OWN_SIGNS,
    compute_jagradadi,
    compute_deeptadi,
)
from avastha.service import AvasthaService
from tests.unit.avastha.conftest import make_sun_state, make_moon_state, make_planet_state


class TestComputeJagradadi:
    """Jagradadi depends on degree within a rashi."""

    def test_0_degrees_is_jagrat(self) -> None:
        assert compute_jagradadi(0.0) == JagradadiState.JAGRAT

    def test_3_degrees_is_jagrat(self) -> None:
        assert compute_jagradadi(3.0) == JagradadiState.JAGRAT

    def test_6_degrees_is_swapna(self) -> None:
        # Exactly at boundary: 6.0 >= jagrat_end (6.0) → swapna
        assert compute_jagradadi(6.0) == JagradadiState.SWAPNA

    def test_10_degrees_is_swapna(self) -> None:
        assert compute_jagradadi(10.0) == JagradadiState.SWAPNA

    def test_18_degrees_is_sushupti(self) -> None:
        # Exactly at boundary: 18.0 >= swapna_end (18.0) → sushupti
        assert compute_jagradadi(18.0) == JagradadiState.SUSHUPTI

    def test_25_degrees_is_sushupti(self) -> None:
        assert compute_jagradadi(25.0) == JagradadiState.SUSHUPTI

    def test_near_30_boundary(self) -> None:
        assert compute_jagradadi(29.999) == JagradadiState.SUSHUPTI

    def test_wraps_around_30(self) -> None:
        # 33.0 % 30.0 = 3.0 → jagrat
        assert compute_jagradadi(33.0) == JagradadiState.JAGRAT


class TestComputeDeeptadi:
    """Deeptadi depends on rashi placement."""

    def test_exaltation(self) -> None:
        # Sun is exalted in Aries (MESHA)
        assert compute_deeptadi(BodyId.SUN, RashiId.MESHA) == DeeptadiState.DEEPTA

    def test_debilitation(self) -> None:
        # Sun is debilitated in Libra (TULA)
        assert compute_deeptadi(BodyId.SUN, RashiId.TULA) == DeeptadiState.KSHOBHITA

    def test_own_sign(self) -> None:
        # Sun's own sign is Leo (SIMHA)
        assert compute_deeptadi(BodyId.SUN, RashiId.SIMHA) == DeeptadiState.SWASTHA

    def test_friendly_sign(self) -> None:
        # Sun is friendly in Aries, but that's also exaltation → test different
        # Mercury friendly in Taurus (VRISHABHA)
        assert compute_deeptadi(BodyId.MERCURY, RashiId.VRISHABHA) == DeeptadiState.PRASANTA

    def test_enemy_sign(self) -> None:
        # Sun enemy in Tula, but Tula is also debilitation → test different
        # Jupiter enemy in Mithuna
        assert compute_deeptadi(BodyId.JUPITER, RashiId.MITHUNA) == DeeptadiState.KSHUDHITA

    def test_neutral_default(self) -> None:
        # Sun in Gemini (MITHUNA) — neutral
        assert compute_deeptadi(BodyId.SUN, RashiId.MITHUNA) == DeeptadiState.DEENA


class TestAvasthaServiceCalculate:
    """Integration of Jagradadi + Deeptadi through the service."""

    def test_perfect_state(self) -> None:
        svc = AvasthaService()
        # Sun exalted in Aries at 3° → Jagrat + Deepta
        state = make_sun_state(3.0)
        report = svc.calculate_avasthas((state,))
        result = report.result_for(BodyId.SUN)
        assert result is not None
        assert result.jagradadi == JagradadiState.JAGRAT
        assert result.deeptadi == DeeptadiState.DEEPTA
        # multiplier = 1.0 × 1.0 = 1.0
        assert abs(result.multiplier - 1.0) < 1e-9

    def test_worst_state(self) -> None:
        svc = AvasthaService()
        # Sun debilitated in Libra at 20° → Sushupti + Kshobhita
        state = make_sun_state(200.0)  # 20° Libra
        report = svc.calculate_avasthas((state,))
        result = report.result_for(BodyId.SUN)
        assert result is not None
        assert result.jagradadi == JagradadiState.SUSHUPTI
        assert result.deeptadi == DeeptadiState.KSHOBHITA
        # multiplier = 0.5 × 0.25 = 0.125
        assert abs(result.multiplier - 0.125) < 1e-9

    def test_multi_planet(self) -> None:
        svc = AvasthaService()
        sun = make_sun_state(3.0)
        moon = make_moon_state(33.0)
        report = svc.calculate_avasthas((sun, moon))
        assert len(report.results) == 2
        assert report.result_for(BodyId.SUN) is not None
        assert report.result_for(BodyId.MOON) is not None

    def test_multiplier_always_non_negative(self) -> None:
        svc = AvasthaService()
        for degree in [0.0, 3.0, 10.0, 20.0, 29.0]:
            state = make_sun_state(degree)
            report = svc.calculate_avasthas((state,))
            result = report.result_for(BodyId.SUN)
            assert result is not None
            assert result.multiplier >= 0.0

    def test_baladi_none_in_v1(self) -> None:
        svc = AvasthaService()
        state = make_sun_state(3.0)
        report = svc.calculate_avasthas((state,))
        result = report.result_for(BodyId.SUN)
        assert result is not None
        assert result.baladi is None
