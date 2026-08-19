"""JRE-011 Bala integration tests.

End-to-end tests verifying:
- Full Shadbala computation for all planets
- Component sum equals total
- Minimum requirement checking
- Determinism across multiple calls
- Serialization round-trip
"""

from __future__ import annotations

import math

import pytest
from jyotish import BodyId

from bala.models import (
    BALA_PLANETS,
    VIRUPAS_PER_RUPA,
    BalaConfig,
    ShadbalaReport,
)
from bala.serialize import result_to_dict, result_to_json
from bala.service import BalaService
from tests.unit.bala.conftest import (
    make_all_planet_states,
    make_lagna_state,
    make_planet_state,
)


class TestFullShadbalaComputation:
    """Integration: compute Shadbala for all planets."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = BalaService(BalaConfig())
        self.states = make_all_planet_states()
        self.lagna = make_lagna_state(0.0)
        self.report = self.service.calculate_shadbala(
            self.states, self.lagna
        )

    def test_report_has_results(self) -> None:
        """Report should contain results for computed planets."""
        assert len(self.report.results) > 0

    def test_all_classical_planets_present(self) -> None:
        """All 7 classical planets + Rahu/Ketu should be computed."""
        computed = {r.planet for r in self.report.results}
        for planet in BALA_PLANETS:
            assert planet in computed, f"{planet} missing from report"

    def test_component_sum_equals_total(self) -> None:
        """Sum of six balas should equal total virupas."""
        for result in self.report.results:
            expected = (
                result.components.total_sthana
                + result.components.dig_bala
                + result.components.total_kala
                + result.components.cheshta_bala
                + result.components.naisargika_bala
                + result.components.drik_bala
            )
            assert math.isclose(
                result.total_virupas, expected, rel_tol=1e-10
            ), f"{result.planet}: expected {expected}, got {result.total_virupas}"

    def test_rupas_conversion(self) -> None:
        """Total rupas should equal virupas / 60."""
        for result in self.report.results:
            assert math.isclose(
                result.total_rupas,
                result.total_virupas / VIRUPAS_PER_RUPA,
                rel_tol=1e-10,
            )

    def test_ratio_positive(self) -> None:
        """Ratio should be positive for all planets."""
        for result in self.report.results:
            assert result.ratio > 0, f"{result.planet}: ratio={result.ratio}"

    def test_minimum_required_positive(self) -> None:
        """Minimum required should be positive for all planets."""
        for result in self.report.results:
            assert result.minimum_required > 0

    def test_system_is_shadbala(self) -> None:
        assert self.report.system.value == "SHADBALA"


class TestSthanaBalaIntegration:
    """Integration: verify Sthana Bala sub-components."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = BalaService()
        self.states = make_all_planet_states()
        self.lagna = make_lagna_state(0.0)
        self.report = self.service.calculate_shadbala(self.states, self.lagna)

    def test_uchcha_bala_range(self) -> None:
        """Uchcha Bala should be in [0, 60] for all planets."""
        for result in self.report.results:
            uchcha = result.components.sthana_bala.uchcha_bala
            assert 0.0 <= uchcha <= 60.0, (
                f"{result.planet}: uchcha_bala={uchcha}"
            )

    def test_kendradi_bala_values(self) -> None:
        """Kendradi Bala should be one of {0, 15, 30, 60}."""
        valid_values = {0.0, 15.0, 30.0, 60.0}
        for result in self.report.results:
            kendradi = result.components.sthana_bala.kendradi_bala
            assert kendradi in valid_values, (
                f"{result.planet}: kendradi_bala={kendradi}"
            )

    def test_drekkana_bala_range(self) -> None:
        """Drekkana Bala should be in [0, 15] for all planets."""
        for result in self.report.results:
            drekkana = result.components.sthana_bala.drekkana_bala
            assert 0.0 <= drekkana <= 15.0


class TestDigBalaIntegration:
    """Integration: verify Dig Bala computation."""

    def test_all_planets_have_dig_bala(self) -> None:
        """All planets should have Dig Bala computed."""
        service = BalaService()
        states = make_all_planet_states()
        lagna = make_lagna_state(0.0)
        report = service.calculate_shadbala(states, lagna)
        for result in report.results:
            assert result.components.dig_bala >= 0

    def test_dig_bala_range(self) -> None:
        """Dig Bala should be in [0, 60] for all planets."""
        service = BalaService()
        states = make_all_planet_states()
        lagna = make_lagna_state(0.0)
        report = service.calculate_shadbala(states, lagna)
        for result in report.results:
            assert 0.0 <= result.components.dig_bala <= 60.0


class TestDeterminismIntegration:
    """Integration: verify deterministic output."""

    def test_same_inputs_same_output(self) -> None:
        """Same inputs must produce byte-identical output."""
        service = BalaService()
        states = make_all_planet_states()
        lagna = make_lagna_state(0.0)

        report1 = service.calculate_shadbala(states, lagna)
        report2 = service.calculate_shadbala(states, lagna)

        assert len(report1.results) == len(report2.results)
        for r1, r2 in zip(report1.results, report2.results):
            assert r1.planet == r2.planet
            assert r1.total_virupas == r2.total_virupas
            assert r1.total_rupas == r2.total_rupas
            assert r1.ratio == r2.ratio

    def test_json_deterministic(self) -> None:
        """JSON serialization should be deterministic."""
        service = BalaService()
        states = make_all_planet_states()
        lagna = make_lagna_state(0.0)

        report1 = service.calculate_shadbala(states, lagna)
        report2 = service.calculate_shadbala(states, lagna)

        json1 = result_to_json(report1)
        json2 = result_to_json(report2)
        assert json1 == json2


class TestSerializationIntegration:
    """Integration: verify serialization round-trip."""

    def test_dict_round_trip(self) -> None:
        """Dict serialization should preserve all data."""
        service = BalaService()
        states = make_all_planet_states()
        lagna = make_lagna_state(0.0)
        report = service.calculate_shadbala(states, lagna)

        d = result_to_dict(report)
        assert isinstance(d, dict)
        assert "results" in d
        assert len(d["results"]) == len(report.results)

    def test_json_round_trip(self) -> None:
        """JSON serialization should produce valid JSON."""
        service = BalaService()
        states = make_all_planet_states()
        lagna = make_lagna_state(0.0)
        report = service.calculate_shadbala(states, lagna)

        json_str = result_to_json(report)
        import json
        parsed = json.loads(json_str)
        assert "results" in parsed


class TestBoundaryConditions:
    """Edge cases and boundary conditions."""

    def test_single_planet(self) -> None:
        """Shadbala should work with a single planet."""
        service = BalaService()
        sun = make_planet_state(BodyId.SUN, 100.0)
        lagna = make_lagna_state(0.0)
        report = service.calculate_shadbala((sun,), lagna)
        assert len(report.results) == 1
        assert report.results[0].planet == BodyId.SUN

    def test_no_lagna(self) -> None:
        """Shadbala should work without lagna (Dig Bala = 0)."""
        service = BalaService()
        states = make_all_planet_states()
        report = service.calculate_shadbala(states, lagna_state=None)
        for result in report.results:
            assert result.components.dig_bala == 0.0

    def test_custom_minimum_requirements(self) -> None:
        """Custom minimum requirements should be used."""
        config = BalaConfig(
            minimum_rupas={"SUN": 10.0, "MOON": 10.0, "MARS": 10.0,
                           "MERCURY": 10.0, "JUPITER": 10.0, "VENUS": 10.0,
                           "SATURN": 10.0, "RAHU": 10.0, "KETU": 10.0}
        )
        service = BalaService(config)
        states = make_all_planet_states()
        lagna = make_lagna_state(0.0)
        report = service.calculate_shadbala(states, lagna)
        for result in report.results:
            assert result.minimum_required == 10.0
