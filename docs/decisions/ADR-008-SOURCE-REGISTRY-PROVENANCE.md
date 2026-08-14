# ADR-008 — Source Registry and Provenance

- Status: ACCEPTED
- Date: 2026-08-12
- Related task: [JRE-004 Classical Knowledge & Rule Engine](../architecture/JRE-004-KNOWLEDGE-RULES-CORE.md)
- Decision maker: Architect

## Context

JRE-004 must incorporate classical sources — Bṛhat Parāśara Horā Śāstra
(BPHS), Bṛhat Jātaka, Jātaka Pārijāta, Phaladīpikā, Sūrya Siddhānta /
Vedāṅga-derived material, and later regional/classical works — while the
request explicitly forbids ingesting texts. Rules must be attributable to a
verifiable locus (source → chapter → verse → edition/translation) so that
future engines and users can audit any conclusion.

## Decision

### 1. The source registry holds bibliographic provenance, not prose

- `datasets/knowledge/sources/` stores a versioned catalog of `Source`
  entries: stable id, canonical IAST + common name, author, period, language,
  lineage tags, status (canonical/supplemental/regional/historical), and a
  list of `Edition` records (title, translator, publisher, year, language).
- No manuscript text, no OCR output, no prose corpora. The registry tells you
  *what a source is and how it is cited*, never *what it says*.

### 2. Provenance is mandatory and structural

- Every `Rule` carries exactly one primary `ProvenanceRef`
  (`source_id` + chapter/verse + optional edition + optional commentary) and
  any number of supporting refs.
- With `enforce_provenance=True` (default), a rule whose primary ref lacks a
  resolvable `source_id` fails catalog load with `ProvenanceError`. Missing
  chapter/verse is allowed for whole-source attributions but must be explicit
  (a `None` is a visible, reviewable choice — not an omission).
- Provenance strings are canonicalized deterministically (e.g.
  `"BPHS ch.25 v.12 (tr. Sharma 2001)"`) and exposed in every
  `SynthesisResult.provenance_index`.

### 3. Catalogs are pinned, versioned, checksummed

- Source, rule, and profile catalogs carry a `catalog_version`; SHA-256
  checksums are verified at load when `verify_checksums=True` (default).
  Corruption or version-pin mismatch raises `CatalogIntegrityError` — never a
  silent fallback.
- Any catalog change is a versioned decision (JSP-001 versioning rule),
  mirroring ADR-003 for the rashi/nakshatra catalogs and ADR-001 for the
  ephemeris files.

Rationale:

- "Do not ingest texts" + "provenance" together demand a registry that is
  *complete for citation* and *empty of content*. Bibliographic records
  satisfy both.
- Mandatory provenance makes every rule auditable and prevents anonymous
  "tradition says" rules from entering the system.

Rejected alternatives:

- **Full-text ingestion with verse indexing** — explicitly prohibited by the
  request; licensing and fidelity risk without engine benefit.
- **Free-text provenance strings** — non-structural, unverifiable, and
  non-deterministic; conflicts with the data-contract discipline.

## Consequences

- CODING ships the initial source catalog (the 5 named sources + ≥1 regional
  lineage) with real bibliographic records and checksums.
- Rules without provenance cannot exist in a loaded catalog (tested).
- Validators can cross-check authored rule content against cited editions.

## References

- [JRE-004 Architecture §7–§8, §16](../architecture/JRE-004-KNOWLEDGE-RULES-CORE.md)
- [ADR-003 Catalog Versioning](../decisions/ADR-003-ZODIAC-MODE-CATALOG-VERSIONING.md)
- [ADR-001 Ephemeris Provider](../decisions/ADR-001-EPHEMERIS-PROVIDER.md)
