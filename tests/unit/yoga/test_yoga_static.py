"""JRE-013 Yoga static gate tests.

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
        import yoga
        source = importlib.util.find_spec(yoga.__name__).origin
        assert source is not None
        with open(source) as f:
            content = f.read()
        assert "import astronomy" not in content
        assert "from astronomy" not in content

    def test_no_swisseph_import(self) -> None:
        import yoga
        source_dir = Path(yoga.__file__).parent
        for py_file in source_dir.glob("*.py"):
            with open(py_file) as f:
                content = f.read()
            assert "import swisseph" not in content
            assert "import pysweph" not in content


class TestNoInterpretation:
    """Verify the yoga module performs no interpretation.

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
        from yoga import models
        source_path = models.__file__
        with open(source_path) as f:
            content = _strip_docstrings(f.read()).lower()
        for term in self.FORBIDDEN_TERMS:
            assert term not in content, f"Interpretation term '{term}' found in models.py"

    def test_no_interpretation_in_service(self) -> None:
        from yoga import service
        source_path = service.__file__
        with open(source_path) as f:
            content = _strip_docstrings(f.read()).lower()
        for term in self.FORBIDDEN_TERMS:
            assert term not in content, f"Interpretation term '{term}' found in service.py"


class TestDeterminism:
    def test_same_inputs_same_output(self) -> None:
        from yoga.service import YogaService
        from tests.unit.yoga.conftest import make_gajakesari_chart
        from jyotish import RashiId

        service = YogaService()
        states = make_gajakesari_chart()

        r1 = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        r2 = service.identify_yogas(states, lagna_sign=RashiId.MESHA)

        assert len(r1.results) == len(r2.results)
        for a1, a2 in zip(r1.results, r2.results):
            assert a1.yoga_id == a2.yoga_id
            assert a1.is_present == a2.is_present
            assert a1.strength_modifier == a2.strength_modifier
