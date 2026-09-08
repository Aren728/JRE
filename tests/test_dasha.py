"""
Unit tests for src/jrs/engine/dasha.py
"""

from datetime import datetime

import pytest
from src.jrs.engine.dasha import calculate_vimshottari_dasha


def test_calculate_vimshottari_dasha_keys():
    """Verify Vimshottari Dasha output contains all required keys."""
    # Moon in Swati Nakshatra (~186° longitude)
    res = calculate_vimshottari_dasha(
        moon_longitude=186.5,
        birth_date_str="1995-10-24",
        target_date=datetime(2026, 9, 8),
    )

    assert "mahadasha" in res
    assert "antardasha" in res
    assert "pratyantardasha" in res
    assert "start_date" in res
    assert "end_date" in res


def test_calculate_vimshottari_dasha_date_formatting():
    """Verify returned start and end dates follow YYYY-MM-DD format."""
    res = calculate_vimshottari_dasha(
        moon_longitude=201.08,
        birth_date_str="1995-10-24",
        target_date=datetime(2026, 9, 8),
    )

    # Validate ISO date strings
    start_dt = datetime.strptime(res["start_date"], "%Y-%m-%d")
    end_dt = datetime.strptime(res["end_date"], "%Y-%m-%d")

    assert start_dt < end_dt


def test_calculate_vimshottari_dasha_consistency():
    """Verify Dasha period output remains deterministic for fixed inputs."""
    res1 = calculate_vimshottari_dasha(186.5, "1995-10-24", datetime(2026, 9, 8))
    res2 = calculate_vimshottari_dasha(186.5, "1995-10-24", datetime(2026, 9, 8))

    assert res1 == res2
