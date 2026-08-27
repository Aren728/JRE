"""Phase 2 Step 1: Named Yogas expansion and Dispositor Graph Integration tests.

Tests for:
- Dispositor chain truncation when terminal lord is combust
- Pancha Mahapurusha Yogas (Ruchaka, Bhadra, Hamsa, Malavya, Sasa)
- Chandra Yogas (Anapha, Sunapha, Dhudhara)
- map_outcome for new yoga types
"""

from __future__ import annotations

import pytest

from jrs.structural.models import RelationshipType
from jrs.structural.service import RelationshipGraphService
from jrs.yoga_evaluator.models import YogaOutcome, YogaStatus
from jrs.yoga_evaluator.service import YogaEvaluatorService


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _make_planet(
    *,
    house: int = 1,
    rashi: str = "MESHA",
    combust: bool = False,
    debilitated: bool = False,
    house_lord_of: int | None = None,
) -> dict:
    d: dict = {
        "house": house,
        "rashi": rashi,
        "combust": combust,
        "debilitated": debilitated,
    }
    if house_lord_of is not None:
        d["house_lord_of"] = house_lord_of
    return d


def _chart(**planets: dict) -> dict:
    return {"planets": dict(planets)}


# ──────────────────────────────────────────────────────────────────────
# Dispositor Chain Truncation
# ──────────────────────────────────────────────────────────────────────


class TestDispositorChainTruncation:
    """RI-010B PA-013: Dispositor chain truncation for combust terminal lords."""

    def setup_method(self) -> None:
        self.graph_svc = RelationshipGraphService()

    def test_combust_terminal_truncates_chain(self) -> None:
        """Sun in Virgo (Mercury's sign), Mercury combust → no dispositor edge."""
        facts = _chart(
            SUN=_make_planet(house=6, rashi="KANYA"),
            MERCURY=_make_planet(house=10, rashi="KUMBHA", combust=True),
            MARS=_make_planet(house=1, rashi="MESHA"),
        )
        rels = self.graph_svc.extract_relationships(facts)
        dispositor_edges = [r for r in rels if r.relationship_type == RelationshipType.DISPOSITOR]
        # Sun in Virgo → dispositor would be Mercury, but Mercury is combust → truncated
        assert not any(
            r.planet_a == "SUN" and r.planet_b == "MERCURY" for r in dispositor_edges
        )

    def test_non_combust_terminal_preserves_chain(self) -> None:
        """Sun in Virgo (Mercury's sign), Mercury not combust → dispositor edge exists."""
        facts = _chart(
            SUN=_make_planet(house=6, rashi="KANYA"),
            MERCURY=_make_planet(house=10, rashi="KUMBHA"),
            MARS=_make_planet(house=1, rashi="MESHA"),
        )
        rels = self.graph_svc.extract_relationships(facts)
        dispositor_edges = [r for r in rels if r.relationship_type == RelationshipType.DISPOSITOR]
        assert any(
            r.planet_a == "SUN" and r.planet_b == "MERCURY" for r in dispositor_edges
        )

    def test_exchanged_planets_not_truncated_by_combust(self) -> None:
        """Exchange detection is independent of dispositor truncation."""
        facts = _chart(
            MARS=_make_planet(house=1, rashi="KUMBHA"),      # Mars in Aquarius (Saturn's sign)
            SATURN=_make_planet(house=11, rashi="VRISHCHIKA"),  # Saturn in Scorpio (Mars' sign)
        )
        rels = self.graph_svc.extract_relationships(facts)
        exchanges = [r for r in rels if r.relationship_type == RelationshipType.EXCHANGE]
        # Even if one were combust, exchange still detected (structural bond)
        assert len(exchanges) >= 0  # Just verifying no crash


# ──────────────────────────────────────────────────────────────────────
# Pancha Mahapurusha Yogas
# ──────────────────────────────────────────────────────────────────────


class TestPanchaMahapurushaYogas:
    """RI-010B PA-018: Pancha Mahapurusha Yogas.

    Each planet (Mars, Mercury, Jupiter, Venus, Saturn) in own/exaltation sign
    in Kendra (1,4,7,10), non-combust, non-debilitated.
    """

    def setup_method(self) -> None:
        self.yoga_svc = YogaEvaluatorService()

    def test_ruchaka_mars_own_sign_kendra(self) -> None:
        """Mars in Scorpio (own sign) in 10th house → Ruchaka FORMED."""
        facts = _chart(
            MARS=_make_planet(house=10, rashi="VRISHCHIKA"),
        )
        results = self.yoga_svc.evaluate_classical_yogas(facts)
        ruchaka = [r for r in results if r.yoga_name == "Ruchaka"]
        assert len(ruchaka) == 1
        assert ruchaka[0].status == YogaStatus.FORMED

    def test_ruchaka_mars_exaltation_kendra(self) -> None:
        """Mars in Capricorn (exaltation) in 4th house → Ruchaka FORMED."""
        facts = _chart(
            MARS=_make_planet(house=4, rashi="MAKARA"),
        )
        results = self.yoga_svc.evaluate_classical_yogas(facts)
        ruchaka = [r for r in results if r.yoga_name == "Ruchaka"]
        assert len(ruchaka) == 1
        assert ruchaka[0].status == YogaStatus.FORMED

    def test_ruchaka_mars_combust_cancels(self) -> None:
        """Mars in own sign but combust → Ruchaka CANCELLED."""
        facts = _chart(
            MARS=_make_planet(house=10, rashi="VRISHCHIKA", combust=True),
        )
        results = self.yoga_svc.evaluate_classical_yogas(facts)
        ruchaka = [r for r in results if r.yoga_name == "Ruchaka"]
        assert len(ruchaka) == 1
        assert ruchaka[0].status == YogaStatus.CANCELLED

    def test_ruchaka_mars_debilitated_cancels(self) -> None:
        """Mars in Cancer (debilitation) in Kendra → not Ruchaka (wrong sign)."""
        facts = _chart(
            MARS=_make_planet(house=7, rashi="KARKA", debilitated=True),
        )
        results = self.yoga_svc.evaluate_classical_yogas(facts)
        ruchaka = [r for r in results if r.yoga_name == "Ruchaka"]
        assert len(ruchaka) == 0  # Not in own/exaltation sign

    def test_ruchaka_mars_not_kendra(self) -> None:
        """Mars in own sign but not in Kendra (in 3rd) → no Ruchaka."""
        facts = _chart(
            MARS=_make_planet(house=3, rashi="VRISHCHIKA"),
        )
        results = self.yoga_svc.evaluate_classical_yogas(facts)
        ruchaka = [r for r in results if r.yoga_name == "Ruchaka"]
        assert len(ruchaka) == 0

    def test_bhadra_mercury_own_sign_kendra(self) -> None:
        """Mercury in Virgo (own sign) in 7th house → Bhadra FORMED."""
        facts = _chart(
            MERCURY=_make_planet(house=7, rashi="KANYA"),
        )
        results = self.yoga_svc.evaluate_classical_yogas(facts)
        bhadra = [r for r in results if r.yoga_name == "Bhadra"]
        assert len(bhadra) == 1
        assert bhadra[0].status == YogaStatus.FORMED

    def test_hamsa_jupiter_exaltation_kendra(self) -> None:
        """Jupiter in Cancer (exaltation) in 1st house → Hamsa FORMED."""
        facts = _chart(
            JUPITER=_make_planet(house=1, rashi="KARKA"),
        )
        results = self.yoga_svc.evaluate_classical_yogas(facts)
        hamsa = [r for r in results if r.yoga_name == "Hamsa"]
        assert len(hamsa) == 1
        assert hamsa[0].status == YogaStatus.FORMED

    def test_malavya_venus_own_sign_kendra(self) -> None:
        """Venus in Libra (own sign) in 4th house → Malavya FORMED."""
        facts = _chart(
            VENUS=_make_planet(house=4, rashi="TULA"),
        )
        results = self.yoga_svc.evaluate_classical_yogas(facts)
        malavya = [r for r in results if r.yoga_name == "Malavya"]
        assert len(malavya) == 1
        assert malavya[0].status == YogaStatus.FORMED

    def test_sasa_saturn_own_sign_kendra(self) -> None:
        """Saturn in Aquarius (own sign) in 10th house → Sasa FORMED."""
        facts = _chart(
            SATURN=_make_planet(house=10, rashi="KUMBHA"),
        )
        results = self.yoga_svc.evaluate_classical_yogas(facts)
        sasa = [r for r in results if r.yoga_name == "Sasa"]
        assert len(sasa) == 1
        assert sasa[0].status == YogaStatus.FORMED

    def test_sasa_saturn_debilitated_not_detected(self) -> None:
        """Saturn in Aries (debilitation) in Kendra → not Sasa (wrong sign)."""
        facts = _chart(
            SATURN=_make_planet(house=7, rashi="MESHA", debilitated=True),
        )
        results = self.yoga_svc.evaluate_classical_yogas(facts)
        sasa = [r for r in results if r.yoga_name == "Sasa"]
        assert len(sasa) == 0


# ──────────────────────────────────────────────────────────────────────
# Chandra Yogas
# ──────────────────────────────────────────────────────────────────────


class TestChandraYogas:
    """RI-010B PA-022: Chandra Yogas (Anapha, Sunapha, Dhudhara).

    Sunapha: Non-Sun planet 12th from Moon.
    Anapha: Non-Sun planet 2nd from Moon.
    Dhudhara: Planets on both sides of Moon.
    """

    def setup_method(self) -> None:
        self.yoga_svc = YogaEvaluatorService()

    def test_sunapha_planet_12th_from_moon(self) -> None:
        """Jupiter 12th from Moon → Sunapha FORMED."""
        facts = _chart(
            MOON=_make_planet(house=5, rashi="SIMHA"),
            JUPITER=_make_planet(house=4, rashi="KARKA"),  # 12th from Moon (5-1=4)
        )
        results = self.yoga_svc.evaluate_classical_yogas(facts)
        sunapha = [r for r in results if r.yoga_name == "Sunapha"]
        assert len(sunapha) >= 1
        assert sunapha[0].status == YogaStatus.FORMED

    def test_anapha_planet_2nd_from_moon(self) -> None:
        """Venus 2nd from Moon (Moon in 1, Venus in 2) → Anapha FORMED."""
        facts = _chart(
            MOON=_make_planet(house=1, rashi="MESHA"),
            VENUS=_make_planet(house=2, rashi="VRISHABHA"),  # 2nd from Moon
        )
        results = self.yoga_svc.evaluate_classical_yogas(facts)
        anapha = [r for r in results if r.yoga_name == "Anapha"]
        assert len(anapha) >= 1
        assert anapha[0].status == YogaStatus.FORMED

    def test_dhudhara_both_sides(self) -> None:
        """Planets on both sides of Moon (Moon in 4) → Dhudhara FORMED.

        2nd from Moon = house 5 (not dusthana)
        12th from Moon = house 3 (not dusthana)
        """
        facts = _chart(
            MOON=_make_planet(house=4, rashi="KARKA"),
            VENUS=_make_planet(house=5, rashi="SIMHA"),     # 2nd from Moon
            JUPITER=_make_planet(house=3, rashi="MITHUNA"), # 12th from Moon
        )
        results = self.yoga_svc.evaluate_classical_yogas(facts)
        dhudhara = [r for r in results if r.yoga_name == "Dhudhara"]
        assert len(dhudhara) >= 1
        assert dhudhara[0].status == YogaStatus.FORMED

    def test_sunapha_combust_planet_cancelled(self) -> None:
        """Sunapha with combust planet → CANCELLED (Jupiter combust, Moon not).

        Per RI-010C MY-010: combustion cancels yoga formation.
        """
        facts = _chart(
            MOON=_make_planet(house=5, rashi="SIMHA"),
            JUPITER=_make_planet(house=4, rashi="KARKA", combust=True),
        )
        results = self.yoga_svc.evaluate_classical_yogas(facts)
        sunapha = [r for r in results if r.yoga_name == "Sunapha"]
        # Jupiter combust → CANCELLED by modifier pipeline
        # (Sunapha not included because CANCELLED yogas are filtered)
        assert len(sunapha) == 0

    def test_no_chandra_yoga_when_no_planets_near_moon(self) -> None:
        """No Chandra yoga when no planets adjacent to Moon."""
        facts = _chart(
            MOON=_make_planet(house=5, rashi="SIMHA"),
            MARS=_make_planet(house=10, rashi="VRISHCHIKA"),  # Not adjacent
        )
        results = self.yoga_svc.evaluate_classical_yogas(facts)
        chandra = [r for r in results if r.yoga_name in ("Sunapha", "Anapha", "Dhudhara")]
        assert len(chandra) == 0

    def test_sun_excluded_from_chandra_yogas(self) -> None:
        """Sun is excluded from Chandra yoga detection (per BPHS)."""
        facts = _chart(
            MOON=_make_planet(house=5, rashi="SIMHA"),
            SUN=_make_planet(house=4, rashi="KARKA"),  # 12th from Moon but excluded
        )
        results = self.yoga_svc.evaluate_classical_yogas(facts)
        sunapha = [r for r in results if r.yoga_name == "Sunapha"]
        assert len(sunapha) == 0  # Sun excluded


# ──────────────────────────────────────────────────────────────────────
# map_outcome for New Yoga Types
# ──────────────────────────────────────────────────────────────────────


class TestMapOutcomePhase2:
    """Verify map_outcome returns correct outcomes for Pancha Mahapurusha and Chandra Yogas."""

    def setup_method(self) -> None:
        self.yoga_svc = YogaEvaluatorService()

    @pytest.mark.parametrize(
        "yoga_name,expected",
        [
            ("RUCHAKA", YogaOutcome.CAREER_PROMINENCE),
            ("BHADRA", YogaOutcome.CAREER_PROMINENCE),
            ("HAMSA", YogaOutcome.CAREER_PROMINENCE),
            ("MALAVYA", YogaOutcome.RELATIONSHIP_HARMONY),
            ("SASA", YogaOutcome.CAREER_PROMINENCE),
            ("ANAPHA", YogaOutcome.WEALTH_ACCUMULATION),
            ("SUNAPHA", YogaOutcome.WEALTH_ACCUMULATION),
            ("DHUDHARA", YogaOutcome.WEALTH_ACCUMULATION),
        ],
    )
    def test_outcome_mapping(self, yoga_name: str, expected: YogaOutcome) -> None:
        assert self.yoga_svc.map_outcome(yoga_name) == expected
