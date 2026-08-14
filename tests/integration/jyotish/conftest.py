"""Shared fixtures for the JRE-003 integration suite.

These tests require ``pysweph`` and the bundled ``.se1`` data files (mirrors
the JRE-002 integration conftest). If unavailable the suite skips with a
clear reason (Test plan §1).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from jyotish.models import BirthData
from jyotish.service import JyotishService

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "datasets" / "ephemeris"

pytest.importorskip("swisseph", reason="pysweph is not installed; integration tests skipped")

if not (DATA_DIR / "sepl_18.se1").is_file() or not (DATA_DIR / "semo_18.se1").is_file():
    pytest.skip(
        "bundled Swiss Ephemeris data files (datasets/ephemeris/*.se1) not found; "
        "integration tests skipped",
        allow_module_level=True,
    )


@pytest.fixture
def service() -> JyotishService:
    """A fresh JyotishService wired to the real Swiss Ephemeris providers."""
    return JyotishService()


def make_birth(
    date: str = "1990-06-15",
    time: str = "10:00:00",
    timezone: str = "Asia/Kolkata",
    latitude: float = 28.6139,
    longitude: float = 77.2090,
) -> BirthData:
    """Build birth data; pass overrides for other fixtures."""
    from jyotish.models import BirthData

    return BirthData(
        date=date,
        time=time,
        timezone=timezone,
        latitude=latitude,
        longitude=longitude,
    )
