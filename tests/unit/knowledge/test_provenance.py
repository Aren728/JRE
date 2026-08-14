"""Provenance tests (TEST-PLAN requirement 3, SPEC §5)."""

from __future__ import annotations

import json

import pytest
from _kb_helpers import write_catalog

from knowledge.errors import (
    CatalogIntegrityError,
    ProvenanceError,
    UnknownEditionError,
)
from knowledge.models import (
    ProvenanceRef,
    Source,
    SourceStatus,
    provenance_completeness_level,
)
from knowledge.provenance import canonical_provenance, resolve_bibliography
from knowledge.rules import load_rule_catalogs
from knowledge.sources import SourceRegistry, load_sources


def test_canonical_provenance_full(service):
    sources = {source.source_id: source for source in service.sources()}
    ref = ProvenanceRef(
        source_id="bphs", chapter="25", verse_start="12", edition_id="santhanam-2001"
    )
    edition = sources["bphs"].editions[0]
    assert canonical_provenance(ref, sources["bphs"], edition) == (
        "BPHS ch.25 v.12 (tr. R. Santhanam 2001)"
    )


def test_canonical_provenance_verse_range(service):
    sources = {source.source_id: source for source in service.sources()}
    ref = ProvenanceRef(
        source_id="bphs",
        chapter="25",
        verse_start="12",
        verse_end="14",
        edition_id="santhanam-2001",
    )
    edition = sources["bphs"].editions[0]
    assert canonical_provenance(ref, sources["bphs"], edition) == (
        "BPHS ch.25 v.12-v.14 (tr. R. Santhanam 2001)"
    )


def test_canonical_provenance_chapter_and_source_only(service):
    sources = {source.source_id: source for source in service.sources()}
    chapter_ref = ProvenanceRef(source_id="bphs", chapter="25", edition_id="santhanam-2001")
    assert canonical_provenance(chapter_ref, sources["bphs"], sources["bphs"].editions[0]) == (
        "BPHS ch.25 (tr. R. Santhanam 2001)"
    )
    source_ref = ProvenanceRef(source_id="bphs")
    assert canonical_provenance(source_ref, sources["bphs"], sources["bphs"].editions[0]) == "BPHS"


def test_completeness_levels():
    full = ProvenanceRef(
        source_id="bphs", chapter="25", verse_start="12", edition_id="santhanam-2001"
    )
    verse = ProvenanceRef(source_id="bphs", chapter="25", verse_start="12")
    chapter = ProvenanceRef(source_id="bphs", chapter="25")
    source_only = ProvenanceRef(source_id="bphs")
    assert provenance_completeness_level(full) == "full"
    assert provenance_completeness_level(verse) == "verse"
    assert provenance_completeness_level(chapter) == "chapter"
    assert provenance_completeness_level(source_only) == "source"


def test_resolve_bibliography_errors():
    registry = load_sources()
    with pytest.raises(UnknownEditionError):
        resolve_bibliography(
            ProvenanceRef(source_id="bphs", chapter="25", verse_start="12", edition_id="nope"),
            registry,
        )
    empty_registry = SourceRegistry(
        (
            Source(
                source_id="ghost",
                canonical_name="Ghost",
                common_name="Ghost",
                author=None,
                period=None,
                language="Sanskrit",
                lineage=(),
                status=SourceStatus.CANONICAL,
                editions=(),
                catalog_version="1.0.0",
            ),
        ),
        "1.0.0",
    )
    with pytest.raises(ProvenanceError):
        resolve_bibliography(ProvenanceRef(source_id="ghost"), empty_registry)


def test_provenance_index_in_result(service):
    from _kb_helpers import yoga_snapshot

    from knowledge.models import RuleDomain, RuleQuery

    query = RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION,
        fact_snapshot=yoga_snapshot(),
        profile_id="bphs-classical",
    )
    result = service.synthesize(query)
    assert result.provenance_index["bphs.gajakesari.1"] == (
        "BPHS ch.36 v.3-v.4 (tr. R. Santhanam 2001)",
    )


def test_checksum_mismatch_detected(tmp_path):
    path = write_catalog(tmp_path, "sources", [])
    document = json.loads(path.read_text(encoding="utf-8"))
    document["entries"] = [
        {
            "source_id": "bphs",
            "canonical_name": "BPHS",
            "common_name": "BPHS",
            "status": "CANONICAL",
            "editions": [],
        }
    ]
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(CatalogIntegrityError):
        load_sources(path)


def test_version_pin_mismatch():
    with pytest.raises(CatalogIntegrityError):
        load_sources(pin="9.9.9")


def test_enforce_provenance_rejects_unknown_source(tmp_path):
    rules_path = write_catalog(
        tmp_path,
        "rules:test",
        [
            {
                "rule_id": "test.unprovenanced.1",
                "domain": "GENERAL",
                "summary": "rule citing an unknown source",
                "condition": {
                    "combiner": None,
                    "op": "EXISTS",
                    "path": "planet(MOON).rashi",
                    "value": None,
                    "children": [],
                },
                "conclusion": {"kind": "CLASSIFICATION", "statement": "x", "structured": {}},
                "provenance": {"source_id": "ghost"},
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
    with pytest.raises(ProvenanceError):
        load_rule_catalogs(paths=[rules_path], registry=load_sources())
