"""Unit tests for JRE-018 JaiminiService."""

from __future__ import annotations

import pytest

from jyotish import BodyId, PlanetState, RashiId

from jaimini.errors import InvalidJaiminiRequestError
from jaimini.models import JaiminiReport
from jaimini.service import JaiminiService
from tests.unit.jaimini.conftest import make_planet_state


class TestJaiminiServiceBasic:
    def test_movable_lagna(self) -> None:
        planets = (
            make_planet_state(BodyId.SUN, 10.0),
            make_planet_state(BodyId.MOON, 33.0),
            make_planet_state(BodyId.MARS, 60.0),
            make_planet_state(BodyId.MERCURY, 90.0),
            make_planet_state(BodyId.JUPITER, 150.0),
            make_planet_state(BodyId.VENUS, 210.0),
            make_planet_state(BodyId.SATURN, 270.0),
        )
        svc = JaiminiService()
        report = svc.calculate_jaimini(RashiId.MESHA, planets)
        assert isinstance(report, JaiminiReport)
        assert len(report.chara_dasha) == 12
        assert len(report.argala) == 12

    def test_fixed_lagna(self) -> None:
        planets = (
            make_planet_state(BodyId.SUN, 10.0),
            make_planet_state(BodyId.MOON, 33.0),
            make_planet_state(BodyId.MARS, 60.0),
            make_planet_state(BodyId.MERCURY, 90.0),
            make_planet_state(BodyId.JUPITER, 150.0),
            make_planet_state(BodyId.VENUS, 210.0),
            make_planet_state(BodyId.SATURN, 270.0),
        )
        svc = JaiminiService()
        report = svc.calculate_jaimini(RashiId.VRISHABHA, planets)
        assert isinstance(report, JaiminiReport)
        assert len(report.chara_dasha) == 12

    def test_dual_lagna(self) -> None:
        planets = (
            make_planet_state(BodyId.SUN, 10.0),
            make_planet_state(BodyId.MOON, 33.0),
            make_planet_state(BodyId.MARS, 60.0),
            make_planet_state(BodyId.MERCURY, 90.0),
            make_planet_state(BodyId.JUPITER, 150.0),
            make_planet_state(BodyId.VENUS, 210.0),
            make_planet_state(BodyId.SATURN, 270.0),
        )
        svc = JaiminiService()
        report = svc.calculate_jaimini(RashiId.MITHUNA, planets)
        assert isinstance(report, JaiminiReport)
        assert len(report.chara_dasha) == 12

    def test_deterministic(self) -> None:
        planets = (
            make_planet_state(BodyId.SUN, 10.0),
            make_planet_state(BodyId.MOON, 33.0),
        )
        svc = JaiminiService()
        r1 = svc.calculate_jaimini(RashiId.MESHA, planets)
        r2 = svc.calculate_jaimini(RashiId.MESHA, planets)
        assert r1.to_dict() == r2.to_dict()

    def test_chara_dasha_sequential(self) -> None:
        planets = (
            make_planet_state(BodyId.SUN, 10.0),
            make_planet_state(BodyId.MOON, 33.0),
            make_planet_state(BodyId.MARS, 60.0),
            make_planet_state(BodyId.MERCURY, 90.0),
            make_planet_state(BodyId.JUPITER, 150.0),
            make_planet_state(BodyId.VENUS, 210.0),
            make_planet_state(BodyId.SATURN, 270.0),
        )
        svc = JaiminiService()
        report = svc.calculate_jaimini(RashiId.MESHA, planets)
        rashis = [p.rashi for p in report.chara_dasha]
        rashi_list = list(RashiId)
        start_idx = rashi_list.index(rashis[0])
        for i in range(12):
            expected = rashi_list[(start_idx + i) % 12]
            assert rashis[i] == expected

    def test_all_rashis_covered_in_chara_dasha(self) -> None:
        planets = (
            make_planet_state(BodyId.SUN, 10.0),
            make_planet_state(BodyId.MOON, 33.0),
            make_planet_state(BodyId.MARS, 60.0),
            make_planet_state(BodyId.MERCURY, 90.0),
            make_planet_state(BodyId.JUPITER, 150.0),
            make_planet_state(BodyId.VENUS, 210.0),
            make_planet_state(BodyId.SATURN, 270.0),
        )
        svc = JaiminiService()
        report = svc.calculate_jaimini(RashiId.MESHA, planets)
        rashis = {p.rashi for p in report.chara_dasha}
        assert rashis == set(RashiId)

    def test_all_rashis_covered_in_argala(self) -> None:
        planets = (
            make_planet_state(BodyId.SUN, 10.0),
            make_planet_state(BodyId.MOON, 33.0),
            make_planet_state(BodyId.MARS, 60.0),
            make_planet_state(BodyId.MERCURY, 90.0),
            make_planet_state(BodyId.JUPITER, 150.0),
            make_planet_state(BodyId.VENUS, 210.0),
            make_planet_state(BodyId.SATURN, 270.0),
        )
        svc = JaiminiService()
        report = svc.calculate_jaimini(RashiId.MESHA, planets)
        argala_rashis = {a.target_rashi for a in report.argala}
        assert argala_rashis == set(RashiId)


class TestJaiminiServiceValidation:
    def test_empty_planet_states_raises(self) -> None:
        svc = JaiminiService()
        with pytest.raises(InvalidJaiminiRequestError):
            svc.calculate_jaimini(RashiId.MESHA, ())

    def test_invalid_lagna_rashi_raises(self) -> None:
        svc = JaiminiService()
        with pytest.raises(InvalidJaiminiRequestError):
            svc.calculate_jaimini("NOT_A_RASHI", (make_planet_state(BodyId.SUN, 10.0),))
