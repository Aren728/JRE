"""JRE-014 Karaka integration tests.

End-to-end tests verifying:
- Full KarakaReport computation for all types
- Chara Karaka ranking against known positions
- Serialization round-trip
- Determinism across multiple calls
"""

from __future__ import annotations

import json

import pytest
from jyotish import BodyId

from karaka.models import (
    KarakaCategory,
    KarakaConfig,
    KarakaReport,
    KarakaType,
)
from karaka.serialize import result_to_dict, result_to_json
from karaka.service import KarakaService
from tests.unit.karaka.conftest import make_classical_planets, make_planet_state


class TestFullKarakaReport:
    """Integration: compute full KarakaReport."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = KarakaService()
        self.states = make_classical_planets()
        self.result = self.service.calculate_karakas(self.states)

    def test_has_naisargika(self) -> None:
        nais = self.result.karakas_by_type(KarakaType.NAISARGIKA)
        assert len(nais) == 7

    def test_has_sthira(self) -> None:
        sthi = self.result.karakas_by_type(KarakaType.STHIRA)
        assert len(sthi) >= 7

    def test_has_chara(self) -> None:
        chara = self.result.karakas_by_type(KarakaType.CHARA)
        assert len(chara) == 7

    def test_all_assignments_have_valid_category(self) -> None:
        for a in self.result.assignments:
            assert isinstance(a.category, KarakaCategory)

    def test_all_assignments_have_valid_planet(self) -> None:
        for a in self.result.assignments:
            assert isinstance(a.planet, BodyId)

    def test_strength_modifier_in_range(self) -> None:
        for a in self.result.assignments:
            assert 0.0 <= a.strength_modifier <= 1.0


class TestCharaRanking:
    """Integration: verify Chara Karaka ranking against known positions."""

    def test_ak_is_highest_degree(self) -> None:
        """Planet with highest degree-in-sign should be Atmakaraka."""
        service = KarakaService()
        # Venus at 357° = 27° in sign (highest)
        states = (
            make_planet_state(BodyId.SUN, 100.0),    # 10°
            make_planet_state(BodyId.MOON, 33.0),    # 3°
            make_planet_state(BodyId.MARS, 200.0),   # 20°
            make_planet_state(BodyId.MERCURY, 165.0), # 15°
            make_planet_state(BodyId.JUPITER, 95.0),  # 5°
            make_planet_state(BodyId.VENUS, 357.0),   # 27°
            make_planet_state(BodyId.SATURN, 250.0),  # 10°
        )
        result = service.calculate_karakas(states)
        chara = result.karakas_by_type(KarakaType.CHARA)
        ak = [a for a in chara if a.category == KarakaCategory.ATMA]
        assert len(ak) == 1
        assert ak[0].planet == BodyId.VENUS
        assert ak[0].rank == 1

    def test_dk_is_lowest_degree(self) -> None:
        """Planet with lowest degree-in-sign should be Darakaraka."""
        service = KarakaService()
        states = (
            make_planet_state(BodyId.SUN, 100.0),    # 10°
            make_planet_state(BodyId.MOON, 33.0),    # 3°
            make_planet_state(BodyId.MARS, 200.0),   # 20°
            make_planet_state(BodyId.MERCURY, 165.0), # 15°
            make_planet_state(BodyId.JUPITER, 95.0),  # 5°
            make_planet_state(BodyId.VENUS, 357.0),   # 27°
            make_planet_state(BodyId.SATURN, 250.0),  # 10°
        )
        result = service.calculate_karakas(states)
        chara = result.karakas_by_type(KarakaType.CHARA)
        dk = [a for a in chara if a.category == KarakaCategory.DARA]
        assert len(dk) == 1
        assert dk[0].planet == BodyId.MOON  # 3° is lowest
        assert dk[0].rank == 7


class TestDeterminismIntegration:
    def test_same_inputs_same_output(self) -> None:
        service = KarakaService()
        states = make_classical_planets()

        r1 = service.calculate_karakas(states)
        r2 = service.calculate_karakas(states)

        assert len(r1.assignments) == len(r2.assignments)
        for a1, a2 in zip(r1.assignments, r2.assignments):
            assert a1.category == a2.category
            assert a1.planet == a2.planet
            assert a1.rank == a2.rank

    def test_json_deterministic(self) -> None:
        service = KarakaService()
        states = make_classical_planets()

        r1 = service.calculate_karakas(states)
        r2 = service.calculate_karakas(states)

        assert result_to_json(r1) == result_to_json(r2)


class TestSerializationIntegration:
    def test_dict_round_trip(self) -> None:
        service = KarakaService()
        states = make_classical_planets()
        result = service.calculate_karakas(states)

        d = result_to_dict(result)
        assert isinstance(d, dict)
        assert "assignments" in d
        assert len(d["assignments"]) == len(result.assignments)

    def test_json_round_trip(self) -> None:
        service = KarakaService()
        states = make_classical_planets()
        result = service.calculate_karakas(states)

        json_str = result_to_json(result)
        parsed = json.loads(json_str)
        assert "assignments" in parsed


class TestBoundaryConditions:
    def test_single_planet(self) -> None:
        """Single planet should still produce naisargika (all 7) and chara (1)."""
        service = KarakaService()
        sun = make_planet_state(BodyId.SUN, 0.0)
        result = service.calculate_karakas((sun,))
        # Naisargika maps all 7 classical planets regardless of chart
        nais = result.karakas_by_type(KarakaType.NAISARGIKA)
        assert len(nais) == 7
        # Chara only ranks planets actually in the chart
        chara = result.karakas_by_type(KarakaType.CHARA)
        assert len(chara) == 1
        assert chara[0].planet == BodyId.SUN

    def test_custom_chara_count(self) -> None:
        """Custom chara_planet_count should limit Chara assignments."""
        config = KarakaConfig(chara_planet_count=3)
        service = KarakaService(config)
        states = make_classical_planets()
        result = service.calculate_karakas(states)
        chara = result.karakas_by_type(KarakaType.CHARA)
        assert len(chara) == 3
