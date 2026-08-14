"""Shared fixtures for the JRE-004 unit suite (no Swiss Ephemeris).

Builder functions live in ``_kb_helpers.py`` (imported by name from tests);
this conftest provides pytest fixtures only, so it never collides with the
other layers' ``conftest`` modules under the full test tree.
"""

from __future__ import annotations

import pytest

import knowledge


@pytest.fixture(scope="session")
def service() -> knowledge.KnowledgeService:
    """A fresh KnowledgeService wired to the committed catalogs."""
    return knowledge.KnowledgeService()
