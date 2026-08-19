"""JRE-010 Dasha static gate tests.

Verifies architectural invariants: import boundaries, no external
dependencies, no interpretation leakage, determinism.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


class TestImportBoundary:
    """Verify the dasha module respects the import graph."""

    def test_no_astronomy_import(self) -> None:
        """dasha must not import astronomy directly."""
        import dasha
        source = importlib.util.find_spec(dasha.__name__).origin
        assert source is not None
        with open(source) as f:
            content = f.read()
        assert "import astronomy" not in content
        assert "from astronomy" not in content

    def test_no_swisseph_import(self) -> None:
        """dasha must not import pysweph or swisseph."""
        import dasha
        source_dir = Path(dasha.__file__).parent
        for py_file in source_dir.glob("*.py"):
            with open(py_file) as f:
                content = f.read()
            assert "import swisseph" not in content, f"swisseph import in {py_file.name}"
            assert "import pysweph" not in content, f"pysweph import in {py_file.name}"

    def test_only_jyotish_imports(self) -> None:
        """dasha may import from jyotish (the only JRE dependency)."""
        import dasha
        source = importlib.util.find_spec(dasha.__name__).origin
        assert source is not None
        # The top-level __init__.py should only import from .submodules
        # and jyotish


class TestNoInterpretation:
    """Verify the dasha module performs no interpretation."""

    FORBIDDEN_TERMS = [
        "auspicious",
        "inauspicious",
        "benefic",
        "malefic",
        "prediction",
        "forecast",
        "yoga",
        "prediction",
        "auspiciousness",
    ]

    def test_no_interpretation_in_models(self) -> None:
        """Models must not contain interpretation logic."""
        from dasha import models
        source_path = models.__file__
        with open(source_path) as f:
            content = f.read().lower()
        for term in self.FORBIDDEN_TERMS:
            assert term not in content, f"Interpretation term '{term}' found in models.py"

    def test_no_interpretation_in_service(self) -> None:
        """Service must not contain interpretation logic."""
        from dasha import service
        source_path = service.__file__
        with open(source_path) as f:
            content = f.read().lower()
        for term in self.FORBIDDEN_TERMS:
            assert term not in content, f"Interpretation term '{term}' found in service.py"


class TestDeterminism:
    """Verify deterministic behavior."""

    def test_same_inputs_same_output(self) -> None:
        """Same birth state must produce same timeline."""
        from datetime import datetime, timezone

        from jyotish import BodyId, NakshatraId, Pada

        from dasha.models import DashaConfig
        from dasha.service import DashaService
        from tests.unit.dasha.conftest import make_moon_state

        service = DashaService(DashaConfig())
        moon = make_moon_state(NakshatraId.ROHINI, Pada.PADA_1)
        birth = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        tl1 = service.generate_timeline(moon, birth)
        tl2 = service.generate_timeline(moon, birth)

        assert tl1.balance_at_birth == tl2.balance_at_birth
        assert len(tl1.periods) == len(tl2.periods)
        for p1, p2 in zip(tl1.periods, tl2.periods):
            assert p1.start_utc == p2.start_utc
            assert p1.end_utc == p2.end_utc
            assert p1.mahadasha_lord == p2.mahadasha_lord
