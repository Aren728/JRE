"""JRE-011 BalaService unit tests.

Tests for individual Bala formulas and the service facade.
"""

from __future__ import annotations

import math

import pytest
from jyotish import BodyId, RetrogradeState

from bala.models import (
    BALA_PLANETS,
    EXALTATION_DEGREES,
    DEBILITATION_DEGREES,
    VIRUPAS_PER_RUPA,
    BalaConfig,
    ShadbalaReport,
)
from bala.service import BalaService
from tests.unit.bala.conftest import (
    make_all_planet_states,
    make_lagna_state,
    make_planet_state,
    make_sun_state,
    make_moon_state,
    make_mars_state,
    make_mercury_state,
    make_jupiter_state,
    make_venus_state,
    make_saturn_state,
    make_rahu_state,
    make_ketu_state,
)


class TestBalaServiceInit:
    """Test BalaService construction."""

    def test_default_config(self) -> None:
        service = BalaService()
        assert service.config.version == "0.1.0"

    def test_custom_config(self) -> None:
        config = BalaConfig(max_depth=2)
        service = BalaService(config)
        assert service.config.max_depth == 2


class TestUchchaBala:
    """Test Uchcha Bala (Exaltation Strength) computation."""

    def test_at_exaltation(self) -> None:
        """Planet at exaltation point should get 60 virupas."""
        service = BalaService()
        sun = make_sun_state(EXALTATION_DEGREES[BodyId.SUN])
        result = service.calculate_shadbala(
            planet_states=(sun,),
            lagna_state=make_lagna_state(EXALTATION_DEGREES[BodyId.SUN]),
        )
        sun_result = result.result_for(BodyId.SUN)
        assert sun_result is not None
        assert math.isclose(
            sun_result.components.sthana_bala.uchcha_bala,
            60.0, abs_tol=0.1
        )

    def test_at_debilitation(self) -> None:
        """Planet at debilitation point should get ~0 virupas."""
        service = BalaService()
        sun = make_sun_state(DEBILITATION_DEGREES[BodyId.SUN])
        result = service.calculate_shadbala(
            planet_states=(sun,),
            lagna_state=make_lagna_state(DEBILITATION_DEGREES[BodyId.SUN]),
        )
        sun_result = result.result_for(BodyId.SUN)
        assert sun_result is not None
        assert math.isclose(
            sun_result.components.sthana_bala.uchcha_bala,
            0.0, abs_tol=0.1
        )

    def test_at_partial_uchcha(self) -> None:
        """Planet between exaltation and debilitation gets partial uchcha."""
        service = BalaService()
        # Sun at Scorpio 10° = 280° — past debilitation, partial uchcha
        sun = make_sun_state(280.0)
        result = service.calculate_shadbala(
            planet_states=(sun,),
            lagna_state=make_lagna_state(280.0),
        )
        sun_result = result.result_for(BodyId.SUN)
        assert sun_result is not None
        uchcha = sun_result.components.sthana_bala.uchcha_bala
        assert 0.0 < uchcha < 60.0


class TestDigBala:
    """Test Dig Bala (Directional Strength) computation."""

    def test_at_peak_house(self) -> None:
        """Planet at its peak house should get ~60 virupas."""
        service = BalaService()
        # Sun's peak is house 10. With Aries ascendant (house 1 = 0°),
        # house 10 is Capricorn (270°).
        sun = make_sun_state(270.0)
        lagna = make_lagna_state(0.0)
        result = service.calculate_shadbala(
            planet_states=(sun,),
            lagna_state=lagna,
        )
        sun_result = result.result_for(BodyId.SUN)
        assert sun_result is not None
        assert math.isclose(sun_result.components.dig_bala, 60.0, abs_tol=1.0)

    def test_at_opposite_house(self) -> None:
        """Planet opposite its peak house should get ~0 virupas."""
        service = BalaService()
        # Sun's peak is house 10. Opposite is house 4 (Cancer, 90°).
        sun = make_sun_state(90.0)
        lagna = make_lagna_state(0.0)
        result = service.calculate_shadbala(
            planet_states=(sun,),
            lagna_state=lagna,
        )
        sun_result = result.result_for(BodyId.SUN)
        assert sun_result is not None
        assert math.isclose(sun_result.components.dig_bala, 0.0, abs_tol=1.0)

    def test_without_lagna(self) -> None:
        """Without lagna, dig bala should be 0."""
        service = BalaService()
        sun = make_sun_state(100.0)
        result = service.calculate_shadbala(
            planet_states=(sun,),
            lagna_state=None,
        )
        sun_result = result.result_for(BodyId.SUN)
        assert sun_result is not None
        assert sun_result.components.dig_bala == 0.0


class TestKalaBala:
    """Test Kala Bala (Temporal Strength) computation."""

    def test_nathonnatha_day_planet(self) -> None:
        """Day planet should get 30 virupas nathonnatha bala."""
        service = BalaService()
        sun = make_sun_state(100.0)
        result = service.calculate_shadbala(
            planet_states=(sun,),
            lagna_state=make_lagna_state(0.0),
        )
        sun_result = result.result_for(BodyId.SUN)
        assert sun_result is not None
        assert sun_result.components.kala_bala.nathonnatha_bala == 30.0

    def test_paksha_bala_full_moon(self) -> None:
        """Benefic at full moon should get 60 virupas paksha bala."""
        service = BalaService()
        jupiter = make_jupiter_state(100.0)
        result = service.calculate_shadbala(
            planet_states=(jupiter,),
            lagna_state=make_lagna_state(0.0),
            moon_phase_fraction=0.5,
        )
        jupiter_result = result.result_for(BodyId.JUPITER)
        assert jupiter_result is not None
        assert jupiter_result.components.kala_bala.paksha_bala == 60.0

    def test_paksha_bala_new_moon(self) -> None:
        """Malefic at new moon should get 60 virupas paksha bala."""
        service = BalaService()
        mars = make_mars_state(100.0)
        result = service.calculate_shadbala(
            planet_states=(mars,),
            lagna_state=make_lagna_state(0.0),
            moon_phase_fraction=0.0,
        )
        mars_result = result.result_for(BodyId.MARS)
        assert mars_result is not None
        assert mars_result.components.kala_bala.paksha_bala == 60.0


class TestCheshtaBala:
    """Test Cheshta Bala (Motional Strength) computation."""

    def test_retrograde_gets_full(self) -> None:
        """Retrograde planet should get 60 virupas."""
        service = BalaService()
        sun = make_planet_state(
            BodyId.SUN, 100.0, retrograde=RetrogradeState.RETROGRADE
        )
        result = service.calculate_shadbala(
            planet_states=(sun,),
            lagna_state=make_lagna_state(0.0),
        )
        sun_result = result.result_for(BodyId.SUN)
        assert sun_result is not None
        assert sun_result.components.cheshta_bala == 60.0

    def test_stationary_gets_zero(self) -> None:
        """Stationary planet should get 0 virupas."""
        service = BalaService()
        sun = make_planet_state(
            BodyId.SUN, 100.0, retrograde=RetrogradeState.STATIONARY
        )
        result = service.calculate_shadbala(
            planet_states=(sun,),
            lagna_state=make_lagna_state(0.0),
        )
        sun_result = result.result_for(BodyId.SUN)
        assert sun_result is not None
        assert sun_result.components.cheshta_bala == 0.0

    def test_direct_speed_proportional(self) -> None:
        """Direct planet's cheshta bala should be proportional to speed."""
        service = BalaService()
        sun_slow = make_planet_state(BodyId.SUN, 100.0, speed=7.5)
        sun_fast = make_planet_state(BodyId.SUN, 100.0, speed=15.0)
        result_slow = service.calculate_shadbala(
            planet_states=(sun_slow,),
            lagna_state=make_lagna_state(0.0),
        )
        result_fast = service.calculate_shadbala(
            planet_states=(sun_fast,),
            lagna_state=make_lagna_state(0.0),
        )
        slow = result_slow.result_for(BodyId.SUN)
        fast = result_fast.result_for(BodyId.SUN)
        assert slow is not None
        assert fast is not None
        assert slow.components.cheshta_bala < fast.components.cheshta_bala


class TestNaisargikaBala:
    """Test Naisargika Bala (Natural Strength) computation."""

    def test_sun_is_strongest(self) -> None:
        """Sun should have highest natural strength."""
        service = BalaService()
        states = make_all_planet_states()
        result = service.calculate_shadbala(
            planet_states=states,
            lagna_state=make_lagna_state(0.0),
        )
        sun_result = result.result_for(BodyId.SUN)
        moon_result = result.result_for(BodyId.MOON)
        assert sun_result is not None
        assert moon_result is not None
        assert sun_result.components.naisargika_bala > moon_result.components.naisargika_bala

    def test_values_from_config(self) -> None:
        """Natural strengths should match config values."""
        config = BalaConfig()
        service = BalaService(config)
        sun = make_sun_state(100.0)
        result = service.calculate_shadbala(
            planet_states=(sun,),
            lagna_state=make_lagna_state(0.0),
        )
        sun_result = result.result_for(BodyId.SUN)
        assert sun_result is not None
        assert math.isclose(
            sun_result.components.naisargika_bala, 60.0, abs_tol=0.01
        )


class TestIshtaKashtaPhala:
    """Test Ishta and Kashta Phala computation."""

    def test_ishta_formula(self) -> None:
        """Ishta = (Cheshta + Drik + Naisargika) / 3."""
        service = BalaService()
        sun = make_sun_state(100.0)
        result = service.calculate_shadbala(
            planet_states=(sun,),
            lagna_state=make_lagna_state(0.0),
        )
        sun_result = result.result_for(BodyId.SUN)
        assert sun_result is not None
        expected = (
            sun_result.components.cheshta_bala
            + sun_result.components.drik_bala
            + sun_result.components.naisargika_bala
        ) / 3.0
        assert math.isclose(
            sun_result.ishta_kashta.ishta_phala, expected, rel_tol=1e-10
        )

    def test_kashta_formula(self) -> None:
        """Kashta = (Sthana + Dig + Kala) / 3."""
        service = BalaService()
        sun = make_sun_state(100.0)
        result = service.calculate_shadbala(
            planet_states=(sun,),
            lagna_state=make_lagna_state(0.0),
        )
        sun_result = result.result_for(BodyId.SUN)
        assert sun_result is not None
        expected = (
            sun_result.components.total_sthana
            + sun_result.components.dig_bala
            + sun_result.components.total_kala
        ) / 3.0
        assert math.isclose(
            sun_result.ishta_kashta.kashta_phala, expected, rel_tol=1e-10
        )


class TestTotalShadbala:
    """Test total Shadbala computation."""

    def test_total_is_sum_of_six(self) -> None:
        """Total virupas should be sum of all six balas."""
        service = BalaService()
        sun = make_sun_state(100.0)
        result = service.calculate_shadbala(
            planet_states=(sun,),
            lagna_state=make_lagna_state(0.0),
        )
        sun_result = result.result_for(BodyId.SUN)
        assert sun_result is not None
        expected = (
            sun_result.components.total_sthana
            + sun_result.components.dig_bala
            + sun_result.components.total_kala
            + sun_result.components.cheshta_bala
            + sun_result.components.naisargika_bala
            + sun_result.components.drik_bala
        )
        assert math.isclose(sun_result.total_virupas, expected, rel_tol=1e-10)
        assert math.isclose(
            sun_result.total_rupas,
            sun_result.total_virupas / VIRUPAS_PER_RUPA,
            rel_tol=1e-10,
        )

    def test_ratio_computed(self) -> None:
        """Ratio should be total_rupas / minimum_required."""
        service = BalaService()
        sun = make_sun_state(100.0)
        result = service.calculate_shadbala(
            planet_states=(sun,),
            lagna_state=make_lagna_state(0.0),
        )
        sun_result = result.result_for(BodyId.SUN)
        assert sun_result is not None
        expected_ratio = sun_result.total_rupas / sun_result.minimum_required
        assert math.isclose(sun_result.ratio, expected_ratio, rel_tol=1e-10)


class TestValidation:
    """Test request validation."""

    def test_empty_planet_states(self) -> None:
        service = BalaService()
        from bala.errors import InvalidBalaRequestError
        with pytest.raises(InvalidBalaRequestError):
            service.calculate_shadbala(planet_states=())

    def test_non_tuple_input(self) -> None:
        service = BalaService()
        from bala.errors import InvalidBalaRequestError
        with pytest.raises(InvalidBalaRequestError):
            service.calculate_shadbala(planet_states=[make_sun_state()])  # type: ignore[arg-type]
