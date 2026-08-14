"""Shared fixtures for the JRE-004 integration suite.

These tests require ``pysweph`` and the bundled ``.se1`` data files (mirrors
the JRE-002/JRE-003 integration conftests). They exercise ``knowledge``
against *real* JRE-003 fact snapshots. If unavailable the suite skips with a
clear reason (TEST-PLAN §1).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import knowledge
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


@pytest.fixture(scope="session")
def knowledge_service() -> knowledge.KnowledgeService:
    """A fresh KnowledgeService wired to the committed knowledge catalogs."""
    return knowledge.KnowledgeService()


@pytest.fixture(scope="session")
def jyotish_service() -> JyotishService:
    """A fresh JyotishService wired to the real Swiss Ephemeris providers."""
    return JyotishService()


@pytest.fixture(scope="session")
def birth() -> BirthData:
    return BirthData(
        date="1990-06-15",
        time="10:00:00",
        timezone="Asia/Kolkata",
        latitude=28.6139,
        longitude=77.2090,
    )
