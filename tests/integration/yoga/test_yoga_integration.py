"""JRE-013 Yoga integration tests.

End-to-end tests verifying:
- Full YogaReport computation for multiple yoga rules
- Gajakesari detection across all Kendra positions
- Serialization round-trip
- Determinism across multiple calls
"""

from __future__ import annotations

import json

import pytest
from jyotish import BodyId, RashiId

from yoga.models import (
    YogaConfig,
    YogaId,
    YogaReport,
    YogaResult,
)
from yoga.serialize import result_to_dict, result_to_json
from yoga.service import YogaService
from tests.unit.yoga.conftest import (
    make_gajakesari_chart,
    make_planet_state,
)


class TestFullYogaReport:
    """Integration: compute YogaReport for a realistic chart."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = YogaService()
        self.states = (
            make_planet_state(BodyId.SUN, 100.0),
            make_planet_state(BodyId.MOON, 0.0),
            make_planet_state(BodyId.MARS, 45.0),
            make_planet_state(BodyId.MERCURY, 115.0),
            make_planet_state(BodyId.JUPITER, 90.0),
            make_planet_state(BodyId.VENUS, 85.0),
            make_planet_state(BodyId.SATURN, 320.0),
        )
        self.result = self.service.identify_yogas(
            self.states, lagna_sign=RashiId.MESHA
        )

    def test_result_has_all_yogas(self) -> None:
        assert len(self.result.results) == 4

    def test_all_results_are_yoga_result(self) -> None:
        for r in self.result.results:
            assert isinstance(r, YogaResult)

    def test_all_have_valid_yoga_id(self) -> None:
        for r in self.result.results:
            assert isinstance(r.yoga_id, YogaId)

    def test_strength_modifier_in_range(self) -> None:
        for r in self.result.results:
            assert 0.0 <= r.strength_modifier <= 1.0

    def test_evidence_is_tuple_of_strings(self) -> None:
        for r in self.result.results:
            assert isinstance(r.evidence, tuple)
            for e in r.evidence:
                assert isinstance(e, str)

    def test_gajakesari_present(self) -> None:
        """Jupiter at 90 (Cancer), Moon at 0 (Aries) — 4th from Moon."""
        gaja = self.result.result_for(YogaId.GAJAKESARI_YOGA)
        assert gaja is not None
        assert gaja.is_present is True


class TestGajakesariAllKendras:
    """Integration: verify Gajakesari for all 4 Kendra positions."""

    @pytest.mark.parametrize("offset,expected", [
        (1, True),    # 1st house (same sign)
        (90, True),   # 4th house
        (180, True),  # 7th house
        (270, True),  # 10th house
        (30, False),  # 2nd house (not Kendra)
        (60, False),  # 3rd house (not Kendra)
        (120, False), # 5th house (not Kendra)
        (150, False), # 6th house (not Kendra)
        (210, False), # 8th house (not Kendra)
        (240, False), # 9th house (not Kendra)
        (300, False), # 11th house (not Kendra)
        (330, False), # 12th house (not Kendra)
    ])
    def test_gajakesari_kendra(self, offset: int, expected: bool) -> None:
        service = YogaService()
        moon = make_planet_state(BodyId.MOON, 0.0)
        jupiter = make_planet_state(BodyId.JUPITER, float(offset))
        result = service.identify_yogas(
            (moon, jupiter), lagna_sign=RashiId.MESHA
        )
        gaja = result.result_for(YogaId.GAJAKESARI_YOGA)
        assert gaja is not None
        assert gaja.is_present is expected


class TestDeterminismIntegration:
    """Integration: verify deterministic output."""

    def test_same_inputs_same_output(self) -> None:
        service = YogaService()
        states = make_gajakesari_chart()

        r1 = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        r2 = service.identify_yogas(states, lagna_sign=RashiId.MESHA)

        assert len(r1.results) == len(r2.results)
        for a1, a2 in zip(r1.results, r2.results):
            assert a1.yoga_id == a2.yoga_id
            assert a1.is_present == a2.is_present
            assert a1.strength_modifier == a2.strength_modifier

    def test_json_deterministic(self) -> None:
        service = YogaService()
        states = make_gajakesari_chart()

        r1 = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        r2 = service.identify_yogas(states, lagna_sign=RashiId.MESHA)

        assert result_to_json(r1) == result_to_json(r2)


class TestSerializationIntegration:
    """Integration: verify serialization round-trip."""

    def test_dict_round_trip(self) -> None:
        service = YogaService()
        states = make_gajakesari_chart()
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)

        d = result_to_dict(result)
        assert isinstance(d, dict)
        assert "results" in d
        assert len(d["results"]) == len(result.results)

    def test_json_round_trip(self) -> None:
        service = YogaService()
        states = make_gajakesari_chart()
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)

        json_str = result_to_json(result)
        parsed = json.loads(json_str)
        assert "results" in parsed


class TestBoundaryConditions:
    def test_single_planet(self) -> None:
        """Single planet should produce all-absent yoga report."""
        service = YogaService()
        sun = make_planet_state(BodyId.SUN, 0.0)
        result = service.identify_yogas((sun,), lagna_sign=RashiId.MESHA)
        assert len(result.results) == 4
        assert all(not r.is_present for r in result.results)

    def test_no_lagna(self) -> None:
        """Without lagna, house-based yogas cannot be evaluated."""
        service = YogaService()
        states = make_gajakesari_chart()
        result = service.identify_yogas(states, lagna_sign=None)
        # Gajakesari doesn't need lagna, but Raja/Dhana/Viparita do
        gaja = result.result_for(YogaId.GAJAKESARI_YOGA)
        assert gaja is not None
        assert gaja.is_present is True
        raja = result.result_for(YogaId.RAJA_YOGA)
        assert raja is not None
        assert raja.is_present is False

    def test_custom_enabled_yogas(self) -> None:
        """Only enabled yogas should be evaluated."""
        config = YogaConfig(enabled_yogas=(YogaId.GAJAKESARI_YOGA,))
        service = YogaService(config)
        states = make_gajakesari_chart()
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        assert len(result.results) == 1
        assert result.results[0].yoga_id == YogaId.GAJAKESARI_YOGA
