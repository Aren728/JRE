"""JRE-010 Dasha models and computation unit tests.

Tests the pure derivation helpers: balance calculation, Vimshottari
constants, period generation, and timeline construction.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest
from jyotish import BodyId, NakshatraId, Pada

from dasha.errors import InvalidDashaRequestError
from dasha.models import (
    DASHA_VERSION,
    NAKSHATRA_LORDS,
    NAKSHATRA_SPAN_DEG,
    VIMSHOTTARI_CYCLE_YEARS,
    VIMSHOTTARI_ORDER,
    VIMSHOTTARI_YEARS,
    DashaConfig,
    DashaPeriod,
    DashaSystem,
    DashaTimeline,
    compute_antardasha_order,
    compute_balance_at_birth,
)
from tests.unit.dasha.conftest import NAKSHATRA_START, make_moon_state


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #


class TestVimshottariConstants:
    """Verify the Vimshottari constant tables are correct."""

    def test_cycle_is_120_years(self) -> None:
        assert VIMSHOTTARI_CYCLE_YEARS == 120

    def test_years_sum_to_120(self) -> None:
        assert sum(VIMSHOTTARI_YEARS.values()) == 120

    def test_all_nine_planets_present(self) -> None:
        assert len(VIMSHOTTARI_YEARS) == 9
        for body in BodyId:
            assert body in VIMSHOTTARI_YEARS, f"{body} missing from VIMSHOTTARI_YEARS"

    def test_order_is_9_planets(self) -> None:
        assert len(VIMSHOTTARI_ORDER) == 9

    def test_order_starts_with_ketu(self) -> None:
        assert VIMSHOTTARI_ORDER[0] == BodyId.KETU

    def test_order_ends_with_mercury(self) -> None:
        assert VIMSHOTTARI_ORDER[-1] == BodyId.MERCURY

    def test_nakshatra_lords_cover_all_27(self) -> None:
        assert len(NAKSHATRA_LORDS) == 27

    def test_nakshatra_span_is_correct(self) -> None:
        assert math.isclose(NAKSHATRA_SPAN_DEG, 360.0 / 27.0, rel_tol=1e-10)

    def test_known_nakshatra_lords(self) -> None:
        """Verify a sample of well-known Nakshatra-lord mappings."""
        assert NAKSHATRA_LORDS[NakshatraId.ASHWINI] == BodyId.KETU
        assert NAKSHATRA_LORDS[NakshatraId.ROHINI] == BodyId.MOON
        assert NAKSHATRA_LORDS[NakshatraId.MAGHA] == BodyId.KETU
        assert NAKSHATRA_LORDS[NakshatraId.MULA] == BodyId.KETU
        assert NAKSHATRA_LORDS[NakshatraId.REVATI] == BodyId.MERCURY

    def test_version_is_set(self) -> None:
        assert DASHA_VERSION == "0.1.0"


# --------------------------------------------------------------------------- #
# Balance computation
# --------------------------------------------------------------------------- #


class TestBalanceAtBirth:
    """Test the Vimshottari balance-at-birth calculation."""

    def test_start_of_nakshatra_pada1(self) -> None:
        """At the very start of a nakshatra (degree 0, pada 1),
        the balance should be 100% of the lord's period."""
        balance = compute_balance_at_birth(
            NakshatraId.ASHWINI, Pada.PADA_1, 0.0
        )
        # KETU = 7 years, at 0% elapsed → 7.0
        assert math.isclose(balance, 7.0, rel_tol=1e-10)

    def test_end_of_nakshatra_pada4(self) -> None:
        """Near the end of the last pada, balance approaches 0."""
        nak_span = NAKSHATRA_SPAN_DEG
        balance = compute_balance_at_birth(
            NakshatraId.ASHWINI, Pada.PADA_4, nak_span - 0.01
        )
        # KETU = 7 years, nearly 100% elapsed → very small
        assert 0.0 < balance < 0.1

    def test_midpoint_of_pada1(self) -> None:
        """At the midpoint of pada 1 (25% elapsed), balance = 75% of lord."""
        pada_span = NAKSHATRA_SPAN_DEG / 4.0
        balance = compute_balance_at_birth(
            NakshatraId.ASHWINI, Pada.PADA_1, pada_span / 2.0
        )
        # KETU = 7 years, 12.5% elapsed → 7 * 0.875 = 6.125
        assert math.isclose(balance, 7.0 * 0.875, rel_tol=1e-10)

    def test_boundary_pada1_to_pada2(self) -> None:
        """At the exact boundary of pada 1/2."""
        pada_span = NAKSHATRA_SPAN_DEG / 4.0
        balance = compute_balance_at_birth(
            NakshatraId.ASHWINI, Pada.PADA_2, 0.0
        )
        # Pada 2, degree 0 → 25% elapsed → 7 * 0.75 = 5.25
        assert math.isclose(balance, 7.0 * 0.75, rel_tol=1e-10)

    def test_rohini_pada1(self) -> None:
        """Moon in Rohini (MOON lord, 10 years)."""
        balance = compute_balance_at_birth(
            NakshatraId.ROHINI, Pada.PADA_1, 0.0
        )
        assert math.isclose(balance, 10.0, rel_tol=1e-10)

    def test_balance_is_positive(self) -> None:
        """Balance should always be positive for valid inputs."""
        for nak in NakshatraId:
            for pada in [Pada.PADA_1, Pada.PADA_2, Pada.PADA_3, Pada.PADA_4]:
                balance = compute_balance_at_birth(nak, pada, 0.0)
                assert balance > 0.0, f"Balance for {nak}/{pada} should be positive"

    def test_balance_never_exceeds_lord_years(self) -> None:
        """Balance should never exceed the lord's total Vimshottari period."""
        for nak in NakshatraId:
            lord = NAKSHATRA_LORDS[nak]
            max_years = VIMSHOTTARI_YEARS[lord]
            for pada in [Pada.PADA_1, Pada.PADA_2, Pada.PADA_3, Pada.PADA_4]:
                balance = compute_balance_at_birth(nak, pada, 0.0)
                assert balance <= max_years + 1e-10, (
                    f"Balance {balance} exceeds lord years {max_years} for {nak}/{pada}"
                )


# --------------------------------------------------------------------------- #
# Antardasha order
# --------------------------------------------------------------------------- #


class TestAntardashaOrder:
    """Test the Antardasha sequence generation."""

    def test_ketu_starts_with_ketu(self) -> None:
        order = compute_antardasha_order(BodyId.KETU)
        assert order[0] == BodyId.KETU

    def test_moon_starts_with_moon(self) -> None:
        order = compute_antardasha_order(BodyId.MOON)
        assert order[0] == BodyId.MOON

    def test_order_length_is_9(self) -> None:
        for body in BodyId:
            order = compute_antardasha_order(body)
            assert len(order) == 9

    def test_order_cycles_correctly_from_mercury(self) -> None:
        """Mercury → Ketu → Venus → Sun → ..."""
        order = compute_antardasha_order(BodyId.MERCURY)
        assert order == (
            BodyId.MERCURY, BodyId.KETU, BodyId.VENUS, BodyId.SUN,
            BodyId.MOON, BodyId.MARS, BodyId.RAHU, BodyId.JUPITER,
            BodyId.SATURN,
        )

    def test_all_planets_appear_exactly_once(self) -> None:
        order = compute_antardasha_order(BodyId.SUN)
        assert len(set(order)) == 9


# --------------------------------------------------------------------------- #
# DashaPeriod model
# --------------------------------------------------------------------------- #


class TestDashaPeriod:
    """Test the DashaPeriod dataclass."""

    def test_depth_1(self) -> None:
        p = DashaPeriod(
            start_utc=datetime(2000, 1, 1, tzinfo=timezone.utc),
            end_utc=datetime(2007, 1, 1, tzinfo=timezone.utc),
            mahadasha_lord=BodyId.KETU,
        )
        assert p.depth == 1
        assert p.duration == timedelta(days=7 * 365 + 2)  # approx

    def test_depth_2(self) -> None:
        p = DashaPeriod(
            start_utc=datetime(2000, 1, 1, tzinfo=timezone.utc),
            end_utc=datetime(2002, 1, 1, tzinfo=timezone.utc),
            mahadasha_lord=BodyId.MOON,
            antardasha_lord=BodyId.MARS,
        )
        assert p.depth == 2

    def test_depth_3(self) -> None:
        p = DashaPeriod(
            start_utc=datetime(2000, 1, 1, tzinfo=timezone.utc),
            end_utc=datetime(2000, 6, 1, tzinfo=timezone.utc),
            mahadasha_lord=BodyId.MOON,
            antardasha_lord=BodyId.MARS,
            pratyantardasha_lord=BodyId.RAHU,
        )
        assert p.depth == 3

    def test_to_dict(self) -> None:
        p = DashaPeriod(
            start_utc=datetime(2000, 1, 1, tzinfo=timezone.utc),
            end_utc=datetime(2007, 1, 1, tzinfo=timezone.utc),
            mahadasha_lord=BodyId.KETU,
        )
        d = p.to_dict()
        assert d["mahadasha_lord"] == "KETU"
        assert d["antardasha_lord"] is None
        assert d["pratyantardasha_lord"] is None


# --------------------------------------------------------------------------- #
# DashaConfig model
# --------------------------------------------------------------------------- #


class TestDashaConfig:
    """Test the DashaConfig dataclass."""

    def test_defaults(self) -> None:
        c = DashaConfig()
        assert c.version == "0.1.0"
        assert c.default_system == DashaSystem.VIMSHOTTARI
        assert c.max_depth == 3

    def test_to_dict_roundtrip(self) -> None:
        c = DashaConfig()
        d = c.to_dict()
        assert d["version"] == "0.1.0"
        assert d["default_system"] == "VIMSHOTTARI"

    def test_from_dict(self) -> None:
        d = {
            "version": "0.2.0",
            "default_system": "VIMSHOTTARI",
            "max_depth": 2,
            "vimshottari_years": {"KETU": 7, "VENUS": 20, "SUN": 6, "MOON": 10,
                                  "MARS": 7, "RAHU": 18, "JUPITER": 16, "SATURN": 19, "MERCURY": 17},
        }
        c = DashaConfig.from_dict(d)
        assert c.version == "0.2.0"
        assert c.max_depth == 2


# --------------------------------------------------------------------------- #
# DashaTimeline model
# --------------------------------------------------------------------------- #


class TestDashaTimeline:
    """Test the DashaTimeline dataclass."""

    def test_to_dict(self) -> None:
        tl = DashaTimeline(
            birth_nakshatra=NakshatraId.ROHINI,
            birth_pada=Pada.PADA_1,
            balance_at_birth=10.0,
            system=DashaSystem.VIMSHOTTARI,
            periods=(),
        )
        d = tl.to_dict()
        assert d["birth_nakshatra"] == "ROHINI"
        assert d["birth_pada"] == 1
        assert d["balance_at_birth"] == 10.0
