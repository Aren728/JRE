"""Static gate 3: no prediction code path in the engine (SPEC §18, ADR-009).

- No module evaluates rule conclusions (``RuleConclusion.structured`` keys
  are never read — the engine treats them as opaque data).
- No engine identifier presents ``credibility``/``effective_weight`` as
  outcome likelihood (identifier scan only; authored rule *data* under
  ``datasets/knowledge/`` may legitimately carry interpretation vocabulary).
- No benefic/malefic/auspicious identifiers anywhere in ``src/knowledge``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import knowledge

SRC = Path(knowledge.__file__).resolve().parent

#: Identifiers that would turn metadata into interpretation logic.
FORBIDDEN_IDENTIFIERS = (
    "predict",
    "likelihood",
    "forecast",
    "outcome",
    "benefic",
    "malefic",
    "auspicious",
)


def _identifiers(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            names.append(node.name)
        elif isinstance(node, ast.arg):
            names.append(node.arg)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
    return names


def test_no_prediction_identifiers_in_engine_code():
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for name in _identifiers(tree):
            lowered = name.lower()
            for word in FORBIDDEN_IDENTIFIERS:
                assert word not in lowered, (
                    f"{path.name} uses prediction/interpretation identifier {name!r}"
                )


def test_structured_conclusion_is_opaque():
    """No code reads keys of ``RuleConclusion.structured`` (ADR-009)."""
    for path in SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "structured[" not in text, f"{path.name} reads conclusion structured keys"
        assert "structured.get" not in text, f"{path.name} reads conclusion structured keys"


def test_conclusion_evaluator_absent():
    """The engine has a condition evaluator only — never a conclusion evaluator."""
    for path in SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "conclusion" not in path.name.lower()
        assert "evaluate(rule.conclusion" not in text
