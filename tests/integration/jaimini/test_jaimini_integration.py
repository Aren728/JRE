"""Integration tests for JRE-018 Jaimini.

Verifies the full JaiminiReport against a known reference chart,
ensuring end-to-end correctness from inputs through to
the final Chara Dasha and Argala output.
"""

from __future__ import annotations

from jyotish import BodyId, RashiId, sign_lord_of

from jaimini.models import JaiminiReport, LagnaNature, classify_lagna_nature
from jaimini.service import JaiminiService
from tests.unit.jaimini.conftest import make_planet_state


# --------------------------------------------------------------------------- #
# Reference chart: Aries Lagna, all planets at known positions
# --------------------------------------------------------------------------- #

REFERENCE_PLANETS = (
    make_planet_state(BodyId.SUN, 10.0),       # Aries
    make_planet_state(BodyId.MOON, 33.0),      # Taurus
    make_planet_state(BodyId.MARS, 60.0),      # Gemini
    make_planet_state(BodyId.MERCURY, 95.0),   # Cancer
    make_planet_state(BodyId.JUPITER, 150.0),  # Virgo (150/30=5 = KANYA)
    make_planet_state(BodyId.VENUS, 210.0),    # Libra
    make_planet_state(BodyId.SATURN, 270.0),   # Capricorn
)


class TestReferenceChartAriesLagna:
    """Full integration test against a reference Aries-Lagna chart."""

    def test_full_report_structure(self) -> None:
        svc = JaiminiService()
        report = svc.calculate_jaimini(RashiId.MESHA, REFERENCE_PLANETS)

        assert isinstance(report, JaiminiReport)
        assert len(report.chara_dasha) == 12
        assert len(report.argala) == 12

    def test_chara_dasha_starts_from_correct_sign(self) -> None:
        # Aries Lagna → MOVABLE → start from 9th lord sign
        # 9th from Aries = Sagittarius, lord = Jupiter
        # Jupiter at 150.0 → Virgo (KANYA)
        svc = JaiminiService()
        report = svc.calculate_jaimini(RashiId.MESHA, REFERENCE_PLANETS)

        # First Chara Dasha period should start from Virgo (Jupiter's sign)
        assert report.chara_dasha[0].rashi == RashiId.KANYA

    def test_chara_dasha_lords_correct(self) -> None:
        svc = JaiminiService()
        report = svc.calculate_jaimini(RashiId.MESHA, REFERENCE_PLANETS)

        # Each period's lord should be the classical lord of its rashi
        for period in report.chara_dasha:
            assert period.lord == sign_lord_of(period.rashi)

    def test_chara_dasha_dates_sequential(self) -> None:
        svc = JaiminiService()
        report = svc.calculate_jaimini(RashiId.MESHA, REFERENCE_PLANETS)

        # Each period's start should equal the previous period's end
        for i in range(1, len(report.chara_dasha)):
            assert report.chara_dasha[i].start_utc == report.chara_dasha[i - 1].end_utc

    def test_argala_known_interventions(self) -> None:
        svc = JaiminiService()
        report = svc.calculate_jaimini(RashiId.MESHA, REFERENCE_PLANETS)

        # Find Aries argala result
        aries_argala = None
        for a in report.argala:
            if a.target_rashi == RashiId.MESHA:
                aries_argala = a
                break
        assert aries_argala is not None

        # 2nd from Aries = Taurus: Moon is in Taurus → intervenes
        assert BodyId.MOON in aries_argala.intervening_planets
        # 3rd from Aries = Gemini: Mars is in Gemini → obstructs
        assert BodyId.MARS in aries_argala.obstructing_planets

    def test_argala_all_12_rashis_present(self) -> None:
        svc = JaiminiService()
        report = svc.calculate_jaimini(RashiId.MESHA, REFERENCE_PLANETS)

        rashis = {a.target_rashi for a in report.argala}
        assert rashis == set(RashiId)

    def test_deterministic_output(self) -> None:
        svc = JaiminiService()
        r1 = svc.calculate_jaimini(RashiId.MESHA, REFERENCE_PLANETS)
        r2 = svc.calculate_jaimini(RashiId.MESHA, REFERENCE_PLANETS)
        assert r1.to_dict() == r2.to_dict()


class TestReferenceChartTaurusLagna:
    """Integration test for a Taurus (fixed) Lagna chart."""

    def test_starts_from_10th_lord_sign(self) -> None:
        # Taurus Lagna → FIXED → start from 10th lord sign
        # 10th from Taurus = Aquarius, lord = Saturn
        # Saturn at 270.0 → Capricorn (MAKARA)
        planets = (
            make_planet_state(BodyId.SATURN, 270.0),  # Capricorn
            make_planet_state(BodyId.JUPITER, 150.0),  # Virgo
        )
        svc = JaiminiService()
        report = svc.calculate_jaimini(RashiId.VRISHABHA, planets)

        assert report.chara_dasha[0].rashi == RashiId.MAKARA


class TestReferenceChartGeminiLagna:
    """Integration test for a Gemini (dual) Lagna chart."""

    def test_starts_from_11th_lord_sign(self) -> None:
        # Gemini Lagna → DUAL → start from 11th lord sign
        # 11th from Gemini = Aries, lord = Mars
        # Mars at 60.0 → Gemini (MITHUNA)
        planets = (
            make_planet_state(BodyId.MARS, 60.0),  # Gemini
            make_planet_state(BodyId.JUPITER, 150.0),  # Virgo
        )
        svc = JaiminiService()
        report = svc.calculate_jaimini(RashiId.MITHUNA, planets)

        assert report.chara_dasha[0].rashi == RashiId.MITHUNA
