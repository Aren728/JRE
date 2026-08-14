"""Source registry tests (TEST-PLAN requirement 1, SPEC §4)."""

from __future__ import annotations

import pytest

import knowledge
from knowledge.errors import UnknownEditionError, UnknownSourceError
from knowledge.sources import SOURCE_CATALOG_VERSION, load_sources


def test_all_sources_present(service):
    source_ids = [source.source_id for source in service.sources()]
    for expected in (
        "bphs",
        "brihat-jataka",
        "jataka-parijata",
        "phaladeepika",
        "surya-siddhanta",
        "prasna-marga",
        "saravali",
    ):
        assert expected in source_ids


def test_source_fields_typed(service):
    sources = {source.source_id: source for source in service.sources()}
    source = sources["bphs"]
    assert source.canonical_name == "Bṛhat Parāśara Horā Śāstra"
    assert source.common_name == "BPHS"
    assert source.status is knowledge.SourceStatus.CANONICAL
    assert source.lineage == ("parashari",)
    assert source.catalog_version == SOURCE_CATALOG_VERSION


def test_every_source_has_at_least_one_edition(service):
    for source in service.sources():
        assert len(source.editions) >= 1, source.source_id


def test_edition_fields(service):
    sources = {source.source_id: source for source in service.sources()}
    edition = sources["bphs"].editions[0]
    assert edition.edition_id == "santhanam-2001"
    assert edition.translator == "R. Santhanam"
    assert edition.year == "2001"
    assert edition.language == "English"


def test_get_unknown_source():
    registry = load_sources()
    assert not registry.has("nope")
    with pytest.raises(UnknownSourceError):
        registry.get("nope")


def test_resolve_edition():
    registry = load_sources()
    edition = registry.resolve_edition("bphs", "sharma-1998")
    assert edition.translator == "Girish Chand Sharma"
    with pytest.raises(UnknownEditionError):
        registry.resolve_edition("bphs", "unknown-edition")


def test_default_edition():
    registry = load_sources()
    assert registry.default_edition("bphs").edition_id == "santhanam-2001"


def test_source_catalog_version(service):
    assert service.rule_catalog_versions() is not None
    assert len(service.sources()) == 7
