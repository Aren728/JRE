"""Catalog integrity tests (TEST-PLAN "Additional coverage", ADR-008).

Checksum + version-pin enforcement: corrupted or version-mismatched catalog
documents must fail load with ``CatalogIntegrityError``.
"""

from __future__ import annotations

import json

import pytest
from _kb_helpers import write_catalog

from knowledge.errors import CatalogIntegrityError
from knowledge.rules import load_rule_catalogs
from knowledge.sources import load_sources


def _document(path) -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def test_corrupted_checksum_fails(tmp_path):
    """A catalog whose checksum no longer matches its content must fail load."""
    path = write_catalog(
        tmp_path,
        "rules:corrupt",
        [
            {
                "rule_id": "c.1",
                "domain": "GENERAL",
                "summary": "c",
                "condition": {
                    "combiner": None,
                    "op": "EXISTS",
                    "path": "planet(MOON).rashi",
                    "value": None,
                    "children": [],
                },
                "conclusion": {"kind": "CLASSIFICATION", "statement": "c", "structured": {}},
                "provenance": {
                    "source_id": "bphs",
                    "chapter": "1",
                    "verse_start": "1",
                    "edition_id": "santhanam-2001",
                },
                "supporting_refs": [],
                "conflicts_with": [],
                "exception_for": [],
                "authority_tier": 2,
                "status": "ACTIVE",
                "tradition_tags": [],
                "rule_version": "1.0.0",
            }
        ],
    )
    doc = _document(path)
    # tamper with the content without recomputing the checksum
    doc["summary"] = "tampered"
    path.write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
    with pytest.raises(CatalogIntegrityError):
        load_rule_catalogs(paths=[path], registry=load_sources())


def test_version_pin_mismatch_fails(tmp_path):
    """A catalog version that violates the config pin must fail load."""
    from knowledge.config import load_config

    path = write_catalog(
        tmp_path,
        "rules:pin",
        [
            {
                "rule_id": "p.1",
                "domain": "GENERAL",
                "summary": "p",
                "condition": {
                    "combiner": None,
                    "op": "EXISTS",
                    "path": "planet(MOON).rashi",
                    "value": None,
                    "children": [],
                },
                "conclusion": {"kind": "CLASSIFICATION", "statement": "p", "structured": {}},
                "provenance": {
                    "source_id": "bphs",
                    "chapter": "1",
                    "verse_start": "1",
                    "edition_id": "santhanam-2001",
                },
                "supporting_refs": [],
                "conflicts_with": [],
                "exception_for": [],
                "authority_tier": 2,
                "status": "ACTIVE",
                "tradition_tags": [],
                "rule_version": "1.0.0",
            }
        ],
        version="9.9.9",
    )
    config = load_config()
    pins = {**config.rule_catalog_versions, "rules:pin": "1.0.0"}
    with pytest.raises(CatalogIntegrityError):
        load_rule_catalogs(paths=[path], registry=load_sources(), pins=pins)


def test_committed_catalogs_pass_integrity():
    """The committed catalogs verify under the committed config pins."""
    from knowledge.config import load_config
    from knowledge.facts import load_facts

    config = load_config()
    sources = load_sources(
        verify_checksums=config.verify_checksums,
        pin=config.source_catalog_version,
    )
    rules = load_rule_catalogs(
        registry=sources,
        verify_checksums=config.verify_checksums,
        enforce_provenance=config.enforce_provenance,
        pins=config.rule_catalog_versions,
    )
    assert len(rules.all()) >= 15
    facts = load_facts(
        verify_checksums=config.verify_checksums,
        pin=config.facts_catalog_version,
    )
    assert facts.catalog_version == "1.0.0"


def test_facts_catalog_checksum_mismatch_detected(tmp_path):
    """A tampered facts catalog fails load with ``CatalogIntegrityError``."""
    from knowledge.facts import DEFAULT_FACTS_PATH, load_facts

    path = tmp_path / "facts.json"
    path.write_bytes(DEFAULT_FACTS_PATH.read_bytes())
    document = json.loads(path.read_text(encoding="utf-8"))
    document["entries"][0]["values"]["SUN"] = "BENEFIC"  # tamper without recomputing
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(CatalogIntegrityError):
        load_facts(path)


def test_facts_catalog_version_pin_mismatch():
    from knowledge.facts import load_facts

    with pytest.raises(CatalogIntegrityError):
        load_facts(pin="9.9.9")
