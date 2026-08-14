"""Conflict declaration tests (TEST-PLAN "Additional coverage").

Asymmetric ``conflicts_with`` declarations and ``exception_for`` referencing
unknown targets are rejected at catalog load with typed errors.
"""

from __future__ import annotations

import pytest
from _kb_helpers import write_catalog

from knowledge.errors import ConflictResolutionError, RuleSchemaError
from knowledge.rules import load_rule_catalogs
from knowledge.sources import load_sources


def _rule(rule_id: str, conflicts: list[str], exception_for: list[str]) -> dict:
    return {
        "rule_id": rule_id,
        "domain": "GENERAL",
        "summary": rule_id,
        "condition": {
            "combiner": None,
            "op": "EXISTS",
            "path": "planet(MOON).rashi",
            "value": None,
            "children": [],
        },
        "conclusion": {"kind": "CLASSIFICATION", "statement": rule_id, "structured": {}},
        "provenance": {
            "source_id": "bphs",
            "chapter": "1",
            "verse_start": "1",
            "edition_id": "santhanam-2001",
        },
        "supporting_refs": [],
        "conflicts_with": conflicts,
        "exception_for": exception_for,
        "authority_tier": 2,
        "status": "ACTIVE",
        "tradition_tags": [],
        "rule_version": "1.0.0",
    }


def test_asymmetric_conflicts_with_rejected(tmp_path):
    path = write_catalog(
        tmp_path,
        "rules:asym",
        [_rule("a.1", ["b.1"], []), _rule("b.1", [], [])],
    )
    with pytest.raises(ConflictResolutionError):
        load_rule_catalogs(paths=[path], registry=load_sources())


def test_self_conflicts_with_rejected(tmp_path):
    path = write_catalog(tmp_path, "rules:self", [_rule("a.1", ["a.1"], [])])
    with pytest.raises(ConflictResolutionError):
        load_rule_catalogs(paths=[path], registry=load_sources())


def test_exception_for_unknown_target_rejected(tmp_path):
    path = write_catalog(tmp_path, "rules:unk", [_rule("a.1", [], ["ghost.9"])])
    with pytest.raises(RuleSchemaError):
        load_rule_catalogs(paths=[path], registry=load_sources())


def test_exception_for_self_rejected(tmp_path):
    # a self-targeting exception is a 1-cycle -> ConflictResolutionError
    path = write_catalog(tmp_path, "rules:selfexc", [_rule("a.1", [], ["a.1"])])
    with pytest.raises(ConflictResolutionError):
        load_rule_catalogs(paths=[path], registry=load_sources())
