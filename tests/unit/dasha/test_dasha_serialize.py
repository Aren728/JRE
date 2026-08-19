"""JRE-010 Dasha serialization unit tests.

Tests deterministic JSON serialization and deserialization round-trips.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from jyotish import BodyId, NakshatraId, Pada

from dasha.models import (
    DashaConfig,
    DashaPeriod,
    DashaSystem,
    DashaTimeline,
)
from dasha.serialize import (
    dasha_config_from_dict,
    dasha_period_from_dict,
    dasha_timeline_from_dict,
    result_to_dict,
    result_to_json,
)


class TestResultToDict:
    """Test deterministic dict serialization."""

    def test_period_to_dict(self) -> None:
        p = DashaPeriod(
            start_utc=datetime(2000, 1, 1, tzinfo=timezone.utc),
            end_utc=datetime(2007, 1, 1, tzinfo=timezone.utc),
            mahadasha_lord=BodyId.KETU,
        )
        d = result_to_dict(p)
        assert d["mahadasha_lord"] == "KETU"
        assert d["antardasha_lord"] is None
        assert d["pratyantardasha_lord"] is None

    def test_config_to_dict(self) -> None:
        c = DashaConfig()
        d = result_to_dict(c)
        assert d["default_system"] == "VIMSHOTTARI"

    def test_timeline_to_dict(self) -> None:
        tl = DashaTimeline(
            birth_nakshatra=NakshatraId.ROHINI,
            birth_pada=Pada.PADA_1,
            balance_at_birth=10.0,
            system=DashaSystem.VIMSHOTTARI,
            periods=(),
        )
        d = result_to_dict(tl)
        assert d["birth_nakshatra"] == "ROHINI"


class TestResultToJson:
    """Test deterministic JSON serialization."""

    def test_period_json(self) -> None:
        p = DashaPeriod(
            start_utc=datetime(2000, 1, 1, tzinfo=timezone.utc),
            end_utc=datetime(2007, 1, 1, tzinfo=timezone.utc),
            mahadasha_lord=BodyId.KETU,
        )
        j = result_to_json(p)
        assert isinstance(j, str)
        assert "KETU" in j

    def test_json_is_deterministic(self) -> None:
        p = DashaPeriod(
            start_utc=datetime(2000, 1, 1, tzinfo=timezone.utc),
            end_utc=datetime(2007, 1, 1, tzinfo=timezone.utc),
            mahadasha_lord=BodyId.KETU,
        )
        j1 = result_to_json(p)
        j2 = result_to_json(p)
        assert j1 == j2


class TestDashaConfigFromDict:
    """Test config deserialization."""

    def test_roundtrip(self) -> None:
        c = DashaConfig()
        d = result_to_dict(c)
        c2 = dasha_config_from_dict(d)
        assert c2.version == c.version
        assert c2.default_system == c.default_system
        assert c2.max_depth == c.max_depth


class TestDashaPeriodFromDict:
    """Test period deserialization."""

    def test_roundtrip(self) -> None:
        p = DashaPeriod(
            start_utc=datetime(2000, 1, 1, tzinfo=timezone.utc),
            end_utc=datetime(2007, 1, 1, tzinfo=timezone.utc),
            mahadasha_lord=BodyId.KETU,
            antardasha_lord=BodyId.VENUS,
            pratyantardasha_lord=BodyId.SUN,
        )
        d = result_to_dict(p)
        p2 = dasha_period_from_dict(d)
        assert p2.mahadasha_lord == BodyId.KETU
        assert p2.antardasha_lord == BodyId.VENUS
        assert p2.pratyantardasha_lord == BodyId.SUN

    def test_depth1_roundtrip(self) -> None:
        p = DashaPeriod(
            start_utc=datetime(2000, 1, 1, tzinfo=timezone.utc),
            end_utc=datetime(2007, 1, 1, tzinfo=timezone.utc),
            mahadasha_lord=BodyId.KETU,
        )
        d = result_to_dict(p)
        p2 = dasha_period_from_dict(d)
        assert p2.antardasha_lord is None
        assert p2.pratyantardasha_lord is None


class TestDashaTimelineFromDict:
    """Test timeline deserialization."""

    def test_roundtrip_empty(self) -> None:
        tl = DashaTimeline(
            birth_nakshatra=NakshatraId.ROHINI,
            birth_pada=Pada.PADA_1,
            balance_at_birth=10.0,
            system=DashaSystem.VIMSHOTTARI,
            periods=(),
        )
        d = result_to_dict(tl)
        tl2 = dasha_timeline_from_dict(d)
        assert tl2.birth_nakshatra == NakshatraId.ROHINI
        assert tl2.birth_pada == Pada.PADA_1
        assert tl2.balance_at_birth == 10.0
        assert len(tl2.periods) == 0

    def test_roundtrip_with_periods(self) -> None:
        p = DashaPeriod(
            start_utc=datetime(2000, 1, 1, tzinfo=timezone.utc),
            end_utc=datetime(2007, 1, 1, tzinfo=timezone.utc),
            mahadasha_lord=BodyId.KETU,
        )
        tl = DashaTimeline(
            birth_nakshatra=NakshatraId.ROHINI,
            birth_pada=Pada.PADA_1,
            balance_at_birth=10.0,
            system=DashaSystem.VIMSHOTTARI,
            periods=(p,),
        )
        d = result_to_dict(tl)
        tl2 = dasha_timeline_from_dict(d)
        assert len(tl2.periods) == 1
        assert tl2.periods[0].mahadasha_lord == BodyId.KETU
