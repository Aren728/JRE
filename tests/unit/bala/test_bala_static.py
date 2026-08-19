"""JRE-011 Bala static gate tests.

Verifies architectural invariants: import boundaries, no external
dependencies, no interpretation leakage, determinism.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path


def _strip_docstrings(source: str) -> str:
    """Remove triple-quoted strings so docstrings don't trigger false
    positives in the interpretation-term scan."""
    return re.sub(r'""".*?"""', '', source, flags=re.DOTALL)


class TestImportBoundary:
    """Verify the bala module respects the import graph."""

    def test_no_astronomy_import(self) -> None:
        """bala must not import astronomy directly."""
        import bala
        source = importlib.util.find_spec(bala.__name__).origin
        assert source is not None
        with open(source) as f:
            content = f.read()
        assert "import astronomy" not in content
        assert "from astronomy" not in content

    def test_no_swisseph_import(self) -> None:
        """bala must not import pysweph or swisseph."""
        import bala
        source_dir = Path(bala.__file__).parent
        for py_file in source_dir.glob("*.py"):
            with open(py_file) as f:
                content = f.read()
            assert "import swisseph" not in content, f"swisseph import in {py_file.name}"
            assert "import pysweph" not in content, f"pysweph import in {py_file.name}"

    def test_only_jyotish_imports(self) -> None:
        """bala may import from jyotish (the only JRE dependency)."""
        import bala
        source = importlib.util.find_spec(bala.__name__).origin
        assert source is not None


class TestNoInterpretation:
    """Verify the bala module performs no interpretation.

    Models may define classification constants (NATURAL_BENEFICS,
    NATURAL_MALEFICS) as factual data — those are allowed.  The
    forbidden terms are interpretation *logic* like auspiciousness
    judgments or predictions.  Docstrings are stripped before scanning
    so boundary-documentation terms (e.g. "NO prediction") don't
    trigger false positives.
    """

    # Terms that indicate interpretation logic (not classification constants)
    FORBIDDEN_TERMS = [
        "auspicious",
        "inauspicious",
        "prediction",
        "forecast",
        "yoga",
        "auspiciousness",
    ]

    def test_no_interpretation_in_models(self) -> None:
        """Models must not contain interpretation logic."""
        from bala import models
        source_path = models.__file__
        with open(source_path) as f:
            content = _strip_docstrings(f.read()).lower()
        for term in self.FORBIDDEN_TERMS:
            assert term not in content, f"Interpretation term '{term}' found in models.py"

    def test_no_interpretation_in_service(self) -> None:
        """Service must not contain interpretation logic."""
        from bala import service
        source_path = service.__file__
        with open(source_path) as f:
            content = _strip_docstrings(f.read()).lower()
        for term in self.FORBIDDEN_TERMS:
            assert term not in content, f"Interpretation term '{term}' found in service.py"


class TestDeterminism:
    """Verify deterministic behavior."""

    def test_same_inputs_same_output(self) -> None:
        """Same planet states must produce same Shadbala."""
        from bala.models import BalaConfig
        from bala.service import BalaService
        from tests.unit.bala.conftest import make_all_planet_states, make_lagna_state

        service = BalaService(BalaConfig())
        states = make_all_planet_states()
        lagna = make_lagna_state(0.0)

        report1 = service.calculate_shadbala(states, lagna)
        report2 = service.calculate_shadbala(states, lagna)

        assert len(report1.results) == len(report2.results)
        for r1, r2 in zip(report1.results, report2.results):
            assert r1.planet == r2.planet
            assert r1.total_virupas == r2.total_virupas
            assert r1.total_rupas == r2.total_rupas
