"""Static / surface tests for src/ashtakavarga."""

from __future__ import annotations

import importlib
import importlib.util

import pytest

_SUBMODULES = [
    "config",
    "errors",
    "models",
    "serialize",
    "service",
]


@pytest.mark.parametrize("module_name", _SUBMODULES)
def test_all_modules_importable(module_name: str) -> None:
    mod = importlib.import_module(f"ashtakavarga.{module_name}")
    assert mod is not None


def test_package_importable() -> None:
    import ashtakavarga
    assert hasattr(ashtakavarga, "__version__")
    assert ashtakavarga.__version__ == "0.1.0"


class TestNoInterpretation:
    """Verify the ashtakavarga module performs no interpretation."""

    FORBIDDEN_TERMS = [
        "auspicious",
        "inauspicious",
        "benefic",
        "malefic",
        "prediction",
        "forecast",
        "will give",
        "causes",
    ]

    def test_no_interpretation_in_models(self) -> None:
        """Models must not contain interpretation logic."""
        import ashtakavarga.models as mod
        source = importlib.util.find_spec(mod.__name__).origin
        assert source is not None
        with open(source) as f:
            content = f.read().lower()
        for term in self.FORBIDDEN_TERMS:
            assert term not in content, f"Interpretation term '{term}' found in models.py"

    def test_no_interpretation_in_service(self) -> None:
        """Service must not contain interpretation logic."""
        import ashtakavarga.service as mod
        source = importlib.util.find_spec(mod.__name__).origin
        assert source is not None
        with open(source) as f:
            content = f.read().lower()
        for term in self.FORBIDDEN_TERMS:
            assert term not in content, f"Interpretation term '{term}' found in service.py"
