"""Source registry: versioned catalog of classical sources + edition resolution.

Implements ADR-008: the registry holds bibliographic provenance (never
prose). Every source carries at least one ``Edition`` record; a source with
no edition cannot be cited. Catalogs are JSON data under
``datasets/knowledge/sources/``, checksummed and version-pinned (SPEC §4).

Import direction is one-way: ``sources -> models, errors`` (no cycles).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import (
    CatalogIntegrityError,
    RuleSchemaError,
    UnknownEditionError,
    UnknownSourceError,
)
from .models import (
    Edition,
    Source,
    SourceStatus,
    read_catalog_file,
)

#: Version of the sources catalog format/contents (SPEC §4).
SOURCE_CATALOG_VERSION = "1.0.0"

DEFAULT_SOURCES_PATH: Path = Path("datasets/knowledge/sources/sources.json")

_SOURCE_ID_RE = r"^[a-z0-9][a-z0-9._-]*$"


class SourceRegistry:
    """Immutable registry of ``Source`` entries with edition resolution."""

    def __init__(self, sources: tuple[Source, ...], catalog_version: str) -> None:
        self._sources = sources
        self._catalog_version = catalog_version
        self._by_id = {source.source_id: source for source in sources}

    @property
    def catalog_version(self) -> str:
        """Version of the loaded sources catalog."""
        return self._catalog_version

    def all(self) -> tuple[Source, ...]:
        """All registered sources (catalog order)."""
        return self._sources

    def has(self, source_id: str) -> bool:
        """True iff ``source_id`` is registered."""
        return source_id in self._by_id

    def get(self, source_id: str) -> Source:
        """Resolve ``source_id``; raises ``UnknownSourceError`` otherwise."""
        try:
            return self._by_id[source_id]
        except KeyError as exc:
            raise UnknownSourceError(f"unknown source_id: {source_id!r}") from exc

    def resolve_edition(self, source_id: str, edition_id: str) -> Edition:
        """Resolve an edition for a source; raises typed errors otherwise."""
        source = self.get(source_id)
        for edition in source.editions:
            if edition.edition_id == edition_id:
                return edition
        raise UnknownEditionError(f"unknown edition_id {edition_id!r} for source {source_id!r}")

    def default_edition(self, source_id: str) -> Edition:
        """First edition of a source (used for display on whole-source refs)."""
        source = self.get(source_id)
        if not source.editions:
            raise UnknownEditionError(f"source {source_id!r} has no edition records")
        return source.editions[0]


def _parse_edition(data: dict[str, Any], source_id: str) -> Edition:
    try:
        edition_id = str(data["edition_id"])
        title = str(data["title"])
        translator = data.get("translator")
        publisher = data.get("publisher")
        year = data.get("year")
        language = str(data.get("language", "Sanskrit"))
        notes = data.get("notes")
    except (KeyError, TypeError) as exc:
        raise RuleSchemaError(f"malformed edition entry for source {source_id!r}: {exc!r}") from exc
    return Edition(
        edition_id=edition_id,
        title=title,
        translator=None if translator is None else str(translator),
        publisher=None if publisher is None else str(publisher),
        year=None if year is None else str(year),
        language=language,
        notes=None if notes is None else str(notes),
    )


def _parse_source(data: dict[str, Any]) -> Source:
    try:
        source_id = str(data["source_id"])
        canonical_name = str(data["canonical_name"])
        common_name = str(data.get("common_name", source_id))
        author = data.get("author")
        period = data.get("period")
        language = str(data.get("language", "Sanskrit"))
        lineage = tuple(str(tag) for tag in data.get("lineage", []))
        status = SourceStatus(str(data["status"]))
        catalog_version = str(data.get("catalog_version", SOURCE_CATALOG_VERSION))
        editions = tuple(_parse_edition(edition, source_id) for edition in data["editions"])
    except (KeyError, ValueError, TypeError) as exc:
        raise RuleSchemaError(f"malformed source entry: {exc!r}") from exc
    if not editions:
        raise RuleSchemaError(f"source {source_id!r} must carry at least one edition")
    return Source(
        source_id=source_id,
        canonical_name=canonical_name,
        common_name=common_name,
        author=None if author is None else str(author),
        period=None if period is None else str(period),
        language=language,
        lineage=lineage,
        status=status,
        editions=editions,
        catalog_version=catalog_version,
    )


def load_sources(
    path: str | Path | None = None,
    *,
    verify_checksums: bool = True,
    pin: str | None = None,
) -> SourceRegistry:
    """Load and validate the sources catalog.

    ``pin`` is an exact-match version pin; mismatch raises
    ``CatalogIntegrityError``. Checksum verification is on by default.
    """
    catalog_path = Path(path) if path is not None else DEFAULT_SOURCES_PATH
    try:
        document, digest = read_catalog_file(catalog_path)
    except OSError as exc:
        raise CatalogIntegrityError(f"cannot read catalog {catalog_path}: {exc}") from exc
    except ValueError as exc:
        raise CatalogIntegrityError(f"invalid JSON in catalog {catalog_path}: {exc}") from exc

    if verify_checksums:
        expected = document.get("checksum_sha256")
        if expected != digest:
            raise CatalogIntegrityError(
                f"checksum mismatch for {catalog_path}: expected {expected!r}, got {digest!r}"
            )

    catalog_id = document.get("catalog_id")
    if catalog_id != "sources":
        raise CatalogIntegrityError(
            f"catalog_id mismatch in {catalog_path}: expected 'sources', got {catalog_id!r}"
        )
    version = str(document.get("catalog_version", SOURCE_CATALOG_VERSION))
    if pin is not None and version != pin:
        raise CatalogIntegrityError(
            f"version-pin mismatch for {catalog_path}: expected {pin!r}, got {version!r}"
        )

    entries = document.get("entries", [])
    if not isinstance(entries, list) or not entries:
        raise CatalogIntegrityError(f"catalog {catalog_path} has no source entries")
    sources = tuple(_parse_source(entry) for entry in entries)
    return SourceRegistry(sources, catalog_version=version)
