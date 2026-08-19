"""JRE-014 Karaka static gate tests.

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
    return re.sub(r'\"\"\".*?\"\"\"', '', source, flags=re.DOTALL)


class TestImportBoundary:
    def test_no_astronomy_import(self) -> None:
        import karaka
        source = importlib.util.find_spec(karaka.__name__).origin
        assert source is not None
        with open(source) as f:
            content = f.read()
        assert "import astronomy" not in content
        assert "from astronomy" not in content

    def test_no_swisseph_import(self) -> None:
        import karaka
        source_dir = Path(karaka.__file__).parent
        for py_file in source_dir.glob("*.py"):
            with open(py_file) as f:
                content = f.read()
            assert "import swisseph" not in content
            assert "import pysweph" not in content


class TestNoInterpretation:
    """Verify the karaka module performs no interpretation.

    Docstrings are stripped before scanning.
    """

    FORBIDDEN_TERMS = [
        "auspicious",
        "inauspicious",
        "prediction",
        "forecast",
        "wealth",
        "prosperity",
        "fortune",
    ]

    def test_no_interpretation_in_models(self) -> None:
        from karaka import models
        source_path = models.__file__
        with open(source_path) as f:
            content = _strip_docstrings(f.read()).lower()
        for term in self.FORBIDDEN_TERMS:
            assert term not in content, f"Interpretation term '{term}' found in models.py"

    def test_no_interpretation_in_service(self) -> None:
        from karaka import service
        source_path = service.__file__
        with open(source_path) as f:
            content = _strip_docstrings(f.read()).lower()
        for term in self.FORBIDDEN_TERMS:
            assert term not in content, f"Interpretation term '{term}' found in service.py"


class TestDeterminism:
    def test_same_inputs_same_output(self) -> None:
        from karaka.service import KarakaService
        from tests.unit.karaka.conftest import make_classical_planets

        service = KarakaService()
        states = make_classical_planets()

        r1 = service.calculate_karakas(states)
        r2 = service.calculate_karakas(states)

        assert len(r1.assignments) == len(r2.assignments)
        for a1, a2 in zip(r1.assignments, r2.assignments):
            assert a1.category == a2.category
            assert a1.planet == a2.planet
            assert a1.karaka_type == a2.karaka_type
            assert a1.rank == a2.rank
