"""JRE-012 Drik static gate tests.

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
        import drik
        source = importlib.util.find_spec(drik.__name__).origin
        assert source is not None
        with open(source) as f:
            content = f.read()
        assert "import astronomy" not in content
        assert "from astronomy" not in content

    def test_no_swisseph_import(self) -> None:
        import drik
        source_dir = Path(drik.__file__).parent
        for py_file in source_dir.glob("*.py"):
            with open(py_file) as f:
                content = f.read()
            assert "import swisseph" not in content
            assert "import pysweph" not in content


class TestNoInterpretation:
    """Verify the drik module performs no interpretation.

    Docstrings are stripped before scanning so boundary-documentation
    terms don't trigger false positives.
    """

    FORBIDDEN_TERMS = [
        "auspicious",
        "inauspicious",
        "prediction",
        "forecast",
        "yoga",
        "auspiciousness",
    ]

    def test_no_interpretation_in_models(self) -> None:
        from drik import models
        source_path = models.__file__
        with open(source_path) as f:
            content = _strip_docstrings(f.read()).lower()
        for term in self.FORBIDDEN_TERMS:
            assert term not in content, f"Interpretation term '{term}' found in models.py"

    def test_no_interpretation_in_service(self) -> None:
        from drik import service
        source_path = service.__file__
        with open(source_path) as f:
            content = _strip_docstrings(f.read()).lower()
        for term in self.FORBIDDEN_TERMS:
            assert term not in content, f"Interpretation term '{term}' found in service.py"


class TestDeterminism:
    def test_same_inputs_same_output(self) -> None:
        from drik.service import DrikService
        from tests.unit.drik.conftest import make_planet_state
        from jyotish import BodyId

        service = DrikService()
        sun = make_planet_state(BodyId.SUN, 0.0)
        moon = make_planet_state(BodyId.MOON, 180.0)

        r1 = service.calculate_aspects((sun, moon))
        r2 = service.calculate_aspects((sun, moon))

        assert len(r1.aspects) == len(r2.aspects)
        for a1, a2 in zip(r1.aspects, r2.aspects):
            assert a1.source_planet == a2.source_planet
            assert a1.target_planet == a2.target_planet
            assert a1.orb_deg == a2.orb_deg
