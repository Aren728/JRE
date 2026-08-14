"""Provenance chains: canonical strings, bibliographic resolution, integrity.

Implements SPEC §5: every rule carries a primary ``ProvenanceRef`` plus
optional supporting refs. Provenance strings are canonicalized
deterministically (e.g. ``"BPHS ch.25 v.12 (tr. Santhanam 2001)"``) and
exposed in every ``SynthesisResult.provenance_index``. Completeness levels
(full/verse/chapter/source) feed the deterministic credibility formula
(SPEC §10.2).

Import direction is one-way: ``provenance -> models, sources, errors``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .errors import ProvenanceError
from .models import (
    Edition,
    ProvenanceRef,
    Rule,
    Source,
    provenance_completeness_level,
)

if TYPE_CHECKING:
    from .sources import SourceRegistry

__all__ = [
    "canonical_provenance",
    "completeness_level",
    "provenance_index",
    "provenance_strings",
    "resolve_bibliography",
]


def resolve_bibliography(ref: ProvenanceRef, registry: SourceRegistry) -> tuple[Source, Edition]:
    """Resolve a ref to its ``(Source, Edition)`` records.

    The source must carry at least one edition (SPEC §4 supersession #8);
    an ``edition_id`` resolves through the registry (``UnknownEditionError``
    propagates); otherwise the source's default edition is used for display.
    """
    source = registry.get(ref.source_id)
    if not source.editions:
        raise ProvenanceError(
            f"source {ref.source_id!r} has no edition records and cannot be cited"
        )
    if ref.edition_id is not None:
        edition = registry.resolve_edition(ref.source_id, ref.edition_id)
    else:
        edition = source.editions[0]
    return source, edition


#: re-export of the pure completeness helper (lives in ``models`` so
#: ``precedence`` can consume it without an import cycle)
completeness_level = provenance_completeness_level


def canonical_provenance(ref: ProvenanceRef, source: Source, edition: Edition) -> str:
    """Deterministic canonical provenance string (SPEC §5.1).

    - Full: ``"BPHS ch.25 v.12 (tr. Santhanam 2001)"``
    - Chapter-only: ``"BPHS ch.25 (tr. Santhanam 2001)"``
    - Source-only: ``"BPHS"`` (edition omitted).
    """
    if ref.chapter is None:
        return source.common_name
    parts = [source.common_name, f"ch.{ref.chapter}"]
    if ref.verse_start is not None:
        verse = f"v.{ref.verse_start}"
        if ref.verse_end is not None:
            verse += f"-v.{ref.verse_end}"
        parts.append(verse)
    label = " ".join(parts)
    attribution = [item for item in (edition.translator, edition.year) if item]
    if attribution:
        label += f" (tr. {' '.join(attribution)})"
    return label


def provenance_strings(rule: Rule, registry: SourceRegistry) -> tuple[str, ...]:
    """Canonical provenance strings for a rule: primary first, then supporting."""
    strings: list[str] = []
    primary_source, primary_edition = resolve_bibliography(rule.provenance, registry)
    strings.append(canonical_provenance(rule.provenance, primary_source, primary_edition))
    for ref in rule.supporting_refs:
        source, edition = resolve_bibliography(ref, registry)
        strings.append(canonical_provenance(ref, source, edition))
    return tuple(strings)


def provenance_index(
    rules: tuple[Rule, ...], registry: SourceRegistry
) -> dict[str, tuple[str, ...]]:
    """``{rule_id: (canonical strings)}`` for the given rules (SPEC §5.2)."""
    return {rule.rule_id: provenance_strings(rule, registry) for rule in rules}
