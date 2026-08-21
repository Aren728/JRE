"""Unit tests for JRE-018 Jaimini domain models."""

from __future__ import annotations

from jyotish import BodyId, PlanetState, RashiId, RetrogradeState, sign_lord_of

from jaimini.models import (
    ARGALA_INTERVENING_HOUSES,
    ARGALA_OBSTRUCTING_HOUSES,
    LagnaNature,
    ArgalaResult,
    CharaDashaPeriod,
    JaiminiReport,
    classify_lagna_nature,
    compute_argala,
    compute_chara_dasha_sequence,
    compute_starting_sign,
    get_planets_in_rashi,
    rashi_at_distance,
)
from tests.unit.jaimini.conftest import make_planet_state


# --------------------------------------------------------------------------- #
# Lagna nature classification
# --------------------------------------------------------------------------- #


class TestClassifyLagnaNature:
    def test_aries_is_movable(self) -> None:
        assert classify_lagna_nature(RashiId.MESHA) == LagnaNature.MOVABLE

    def test_cancer_is_movable(self) -> None:
        assert classify_lagna_nature(RashiId.KARKA) == LagnaNature.MOVABLE

    def test_libra_is_movable(self) -> None:
        assert classify_lagna_nature(RashiId.TULA) == LagnaNature.MOVABLE

    def test_capricorn_is_movable(self) -> None:
        assert classify_lagna_nature(RashiId.MAKARA) == LagnaNature.MOVABLE

    def test_taurus_is_fixed(self) -> None:
        assert classify_lagna_nature(RashiId.VRISHABHA) == LagnaNature.FIXED

    def test_leo_is_fixed(self) -> None:
        assert classify_lagna_nature(RashiId.SIMHA) == LagnaNature.FIXED

    def test_scorpio_is_fixed(self) -> None:
        assert classify_lagna_nature(RashiId.VRISHCHIKA) == LagnaNature.FIXED

    def test_aquarius_is_fixed(self) -> None:
        assert classify_lagna_nature(RashiId.KUMBHA) == LagnaNature.FIXED

    def test_gemini_is_dual(self) -> None:
        assert classify_lagna_nature(RashiId.MITHUNA) == LagnaNature.DUAL

    def test_virgo_is_dual(self) -> None:
        assert classify_lagna_nature(RashiId.KANYA) == LagnaNature.DUAL

    def test_sagittarius_is_dual(self) -> None:
        assert classify_lagna_nature(RashiId.DHANUSHA) == LagnaNature.DUAL

    def test_pisces_is_dual(self) -> None:
        assert classify_lagna_nature(RashiId.MEENA) == LagnaNature.DUAL

    def test_all_12_rashis_classified(self) -> None:
        for rashi in RashiId:
            nature = classify_lagna_nature(rashi)
            assert nature in (LagnaNature.MOVABLE, LagnaNature.FIXED, LagnaNature.DUAL)


# --------------------------------------------------------------------------- #
# Rashi helpers
# --------------------------------------------------------------------------- #


class TestRashiAtDistance:
    def test_distance_zero(self) -> None:
        assert rashi_at_distance(RashiId.MESHA, 0) == RashiId.MESHA

    def test_distance_one(self) -> None:
        assert rashi_at_distance(RashiId.MESHA, 1) == RashiId.VRISHABHA

    def test_distance_twelve_wraps(self) -> None:
        assert rashi_at_distance(RashiId.MESHA, 12) == RashiId.MESHA

    def test_distance_negative(self) -> None:
        assert rashi_at_distance(RashiId.MESHA, -1) == RashiId.MEENA

    def test_distance_nine(self) -> None:
        # Aries + 9 signs = Capricorn (index 9)
        assert rashi_at_distance(RashiId.MESHA, 9) == RashiId.MAKARA

    def test_distance_ten(self) -> None:
        # Aries + 10 signs = Aquarius (index 10)
        assert rashi_at_distance(RashiId.MESHA, 10) == RashiId.KUMBHA

    def test_distance_eleven(self) -> None:
        # Aries + 11 signs = Pisces (index 11)
        assert rashi_at_distance(RashiId.MESHA, 11) == RashiId.MEENA

    def test_full_cycle(self) -> None:
        for rashi in RashiId:
            assert rashi_at_distance(rashi, 12) == rashi


# --------------------------------------------------------------------------- #
# Get planets in rashi
# --------------------------------------------------------------------------- #


class TestGetPlanetsInRashi:
    def test_finds_planet_in_sign(self) -> None:
        states = (
            make_planet_state(BodyId.SUN, 10.0),  # Sun in Aries (0-30)
            make_planet_state(BodyId.MOON, 33.0),  # Moon in Taurus (30-60)
        )
        result = get_planets_in_rashi(states, RashiId.MESHA)
        assert result == (BodyId.SUN,)

    def test_multiple_planets_in_sign(self) -> None:
        states = (
            make_planet_state(BodyId.SUN, 5.0),
            make_planet_state(BodyId.MARS, 15.0),
            make_planet_state(BodyId.MOON, 33.0),
        )
        result = get_planets_in_rashi(states, RashiId.MESHA)
        assert BodyId.SUN in result
        assert BodyId.MARS in result
        assert BodyId.MOON not in result

    def test_no_planets_in_sign(self) -> None:
        states = (make_planet_state(BodyId.SUN, 10.0),)
        result = get_planets_in_rashi(states, RashiId.VRISHABHA)
        assert result == ()


# --------------------------------------------------------------------------- #
# Starting sign computation
# --------------------------------------------------------------------------- #


class TestComputeStartingSign:
    def test_movable_aries_lagna_9th_lord(self) -> None:
        # Aries Lagna, 9th from Aries = Sagittarius
        # Lord of Sagittarius = Jupiter
        # Jupiter in Taurus (50.0)
        states = (
            make_planet_state(BodyId.JUPITER, 50.0),
        )
        result = compute_starting_sign(
            lagna_rashi=RashiId.MESHA,
            lagna_nature=LagnaNature.MOVABLE,
            planet_states=states,
            start_house_offset=9,
        )
        # Jupiter at 50.0 is in Taurus (30-60)
        assert result == RashiId.VRISHABHA

    def test_fixed_taurus_lagna_10th_lord(self) -> None:
        # Taurus Lagna, 10th from Taurus = Aquarius
        # Lord of Aquarius = Saturn
        # Saturn in Libra (200.0)
        states = (
            make_planet_state(BodyId.SATURN, 200.0),
        )
        result = compute_starting_sign(
            lagna_rashi=RashiId.VRISHABHA,
            lagna_nature=LagnaNature.FIXED,
            planet_states=states,
            start_house_offset=10,
        )
        # Saturn at 200.0 is in Libra (210-240)? No, 200 is in Virgo (180-210)
        # Wait: 200 / 30 = 6.66, index 6 = TULA (Libra)? No.
        # RashiId list: MESHA(0), VRISHABHA(1), MITHUNA(2), KARKA(3),
        # SIMHA(4), KANYA(5), TULA(6), VRISHCHIKA(7), DHANUSHA(8),
        # MAKARA(9), KUMBHA(10), MEENA(11)
        # int(200/30) = 6, index 6 = TULA (Libra)
        assert result == RashiId.TULA

    def test_dual_gemini_lagna_11th_lord(self) -> None:
        # Gemini Lagna, 11th from Gemini = Aries
        # Lord of Aries = Mars
        # Mars in Cancer (95.0)
        states = (
            make_planet_state(BodyId.MARS, 95.0),
        )
        result = compute_starting_sign(
            lagna_rashi=RashiId.MITHUNA,
            lagna_nature=LagnaNature.DUAL,
            planet_states=states,
            start_house_offset=11,
        )
        # Mars at 95.0: int(95/30)=3, index 3 = KARKA (Cancer)
        assert result == RashiId.KARKA

    def test_lord_not_in_planet_states_falls_back(self) -> None:
        # If the lord planet isn't in the provided states, fall back to its natural sign
        states = (
            make_planet_state(BodyId.SUN, 10.0),
        )
        result = compute_starting_sign(
            lagna_rashi=RashiId.MESHA,
            lagna_nature=LagnaNature.MOVABLE,
            planet_states=states,
            start_house_offset=9,
        )
        # 9th from Aries = Sagittarius, lord = Jupiter
        # Jupiter not in states, fallback = Sagittarius itself
        assert result == RashiId.DHANUSHA


# --------------------------------------------------------------------------- #
# Chara Dasha sequence
# --------------------------------------------------------------------------- #


class TestComputeCharaDashaSequence:
    def test_returns_12_periods(self) -> None:
        result = compute_chara_dasha_sequence(
            starting_sign=RashiId.MESHA,
            period_years=7,
            natal_moon_rashi=RashiId.MESHA,
        )
        assert len(result) == 12

    def test_sequential_order(self) -> None:
        result = compute_chara_dasha_sequence(
            starting_sign=RashiId.MESHA,
            period_years=7,
            natal_moon_rashi=RashiId.MESHA,
        )
        for i in range(12):
            expected_idx = (0 + i) % 12
            expected_rashi = list(RashiId)[expected_idx]
            assert result[i].rashi == expected_rashi

    def test_starting_from_taurus(self) -> None:
        result = compute_chara_dasha_sequence(
            starting_sign=RashiId.VRISHABHA,
            period_years=7,
            natal_moon_rashi=RashiId.MESHA,
        )
        assert result[0].rashi == RashiId.VRISHABHA
        assert result[1].rashi == RashiId.MITHUNA
        assert result[11].rashi == RashiId.MESHA

    def test_lord_matches_rashi(self) -> None:
        result = compute_chara_dasha_sequence(
            starting_sign=RashiId.MESHA,
            period_years=7,
            natal_moon_rashi=RashiId.MESHA,
        )
        for period in result:
            assert period.lord == sign_lord_of(period.rashi)

    def test_period_duration(self) -> None:
        result = compute_chara_dasha_sequence(
            starting_sign=RashiId.MESHA,
            period_years=7,
            natal_moon_rashi=RashiId.MESHA,
        )
        # First period starts at epoch, lasts 7 years
        assert result[0].start_utc == "2000-01-01T00:00:00Z"
        assert result[0].end_utc == "2007-01-01T00:00:00Z"
        # Second period starts where first ended
        assert result[1].start_utc == "2007-01-01T00:00:00Z"
        assert result[1].end_utc == "2014-01-01T00:00:00Z"

    def test_deterministic(self) -> None:
        r1 = compute_chara_dasha_sequence(RashiId.MESHA, 7, RashiId.MESHA)
        r2 = compute_chara_dasha_sequence(RashiId.MESHA, 7, RashiId.MESHA)
        assert r1 == r2


# --------------------------------------------------------------------------- #
# Argala computation
# --------------------------------------------------------------------------- #


class TestComputeArgala:
    def test_no_planets_no_argala(self) -> None:
        states = (make_planet_state(BodyId.SUN, 10.0),)
        result = compute_argala(
            target_rashi=RashiId.MESHA,
            planet_states=states,
        )
        assert result.intervening_planets == ()
        assert result.obstructing_planets == ()

    def test_planet_in_2nd_house_intervenes(self) -> None:
        # Target: Aries. 2nd from Aries = Taurus.
        # Moon in Taurus (33.0)
        states = (make_planet_state(BodyId.MOON, 33.0),)
        result = compute_argala(
            target_rashi=RashiId.MESHA,
            planet_states=states,
        )
        assert BodyId.MOON in result.intervening_planets

    def test_planet_in_11th_house_intervenes(self) -> None:
        # Target: Aries. 11th from Aries = Aquarius.
        # Saturn in Aquarius (300.0)
        states = (make_planet_state(BodyId.SATURN, 300.0),)
        result = compute_argala(
            target_rashi=RashiId.MESHA,
            planet_states=states,
        )
        assert BodyId.SATURN in result.intervening_planets

    def test_planet_in_12th_house_obstructs(self) -> None:
        # Target: Aries. 12th from Aries = Pisces.
        # Jupiter in Pisces (340.0)
        states = (make_planet_state(BodyId.JUPITER, 340.0),)
        result = compute_argala(
            target_rashi=RashiId.MESHA,
            planet_states=states,
        )
        assert BodyId.JUPITER in result.obstructing_planets

    def test_planet_in_3rd_house_obstructs(self) -> None:
        # Target: Aries. 3rd from Aries = Gemini.
        # Mercury in Gemini (70.0)
        states = (make_planet_state(BodyId.MERCURY, 70.0),)
        result = compute_argala(
            target_rashi=RashiId.MESHA,
            planet_states=states,
        )
        assert BodyId.MERCURY in result.obstructing_planets

    def test_full_chart_argala(self) -> None:
        # Aries target with all planets at known positions
        # Rashi layout: MESHA(0), VRISHABHA(1), MITHUNA(2), KARKA(3),
        # SIMHA(4), KANYA(5), TULA(6), VRISHCHIKA(7), DHANUSHA(8),
        # MAKARA(9), KUMBHA(10), MEENA(11)
        states = (
            make_planet_state(BodyId.SUN, 10.0),      # Aries (0-30) → house 1
            make_planet_state(BodyId.MOON, 33.0),      # Taurus (30-60) → 2nd → intervenes
            make_planet_state(BodyId.MARS, 60.0),      # Gemini (60-90) → 3rd → obstructs
            make_planet_state(BodyId.MERCURY, 70.0),   # Gemini (60-90) → 3rd → obstructs
            make_planet_state(BodyId.JUPITER, 150.0),  # Virgo (150-180) → 6th → neither
            make_planet_state(BodyId.VENUS, 210.0),    # Scorpio (210-240) → 8th → neither
            make_planet_state(BodyId.SATURN, 270.0),   # Capricorn (270-300) → 10th → obstructs
        )
        result = compute_argala(
            target_rashi=RashiId.MESHA,
            planet_states=states,
        )
        # 2nd from Aries = Taurus: Moon intervenes
        assert BodyId.MOON in result.intervening_planets
        # 3rd from Aries = Gemini: Mars and Mercury obstruct
        assert BodyId.MARS in result.obstructing_planets
        assert BodyId.MERCURY in result.obstructing_planets
        # 10th from Aries = Capricorn: Saturn obstructs
        assert BodyId.SATURN in result.obstructing_planets
        # 4th from Aries = Cancer: no planets there
        # 5th from Aries = Leo: no planets there
        # 11th from Aries = Aquarius: no planets there

    def test_target_rashi_recorded(self) -> None:
        states = (make_planet_state(BodyId.SUN, 10.0),)
        result = compute_argala(
            target_rashi=RashiId.VRISHABHA,
            planet_states=states,
        )
        assert result.target_rashi == RashiId.VRISHABHA

    def test_deterministic(self) -> None:
        states = (
            make_planet_state(BodyId.SUN, 10.0),
            make_planet_state(BodyId.MOON, 33.0),
        )
        r1 = compute_argala(RashiId.MESHA, states)
        r2 = compute_argala(RashiId.MESHA, states)
        assert r1 == r2


# --------------------------------------------------------------------------- #
# Serialization
# --------------------------------------------------------------------------- #


class TestCharaDashaPeriodToDict:
    def test_to_dict(self) -> None:
        p = CharaDashaPeriod(
            rashi=RashiId.MESHA,
            start_utc="2000-01-01T00:00:00Z",
            end_utc="2007-01-01T00:00:00Z",
            lord=BodyId.MARS,
        )
        d = p.to_dict()
        assert d["rashi"] == "MESHA"
        assert d["lord"] == "MARS"


class TestArgalaResultToDict:
    def test_to_dict(self) -> None:
        r = ArgalaResult(
            target_rashi=RashiId.MESHA,
            intervening_planets=(BodyId.MOON,),
            obstructing_planets=(BodyId.MERCURY,),
        )
        d = r.to_dict()
        assert d["target_rashi"] == "MESHA"
        assert d["intervening_planets"] == ["MOON"]
        assert d["obstructing_planets"] == ["MERCURY"]


class TestJaiminiReportToDict:
    def test_to_dict(self) -> None:
        report = JaiminiReport(
            chara_dasha=(),
            argala=(),
        )
        d = report.to_dict()
        assert "chara_dasha" in d
        assert "argala" in d
