# ADR-003 — Sidereal Default, Explicit Zodiac Mode, and Versioned Catalogs

- Status: ACCEPTED
- Date: 2026-08-12
- Related task: [JRE-003 Jyotish Coordinate and State Layer](../architecture/JRE-003-JYOTISH-CORE.md)
- Decision maker: Architect

## Context

Jyotish classification (Rashi, Nakshatra, Pada) is a pure function of a
longitude. JRE-002 returns both tropical and sidereal longitudes, so JRE-003
must decide which frame feeds classification. Separately, the Rashi and
Nakshatra catalogs (names, boundaries, rulers, pada arcs) are fixed classical
data that must be pinned and versioned for reproducibility (requirement K)
and must be complete — not examples (requirement G).

## Decision

### 1. Zodiac mode is an explicit config field; sidereal is the default

- `JyotishConfig.zodiac_mode: ZodiacMode = SIDEREAL`.
- Classification always uses the frame named by `zodiac_mode`
  (`longitude_used` = sidereal by default, tropical when explicitly
  requested).
- `zodiac_mode=SIDEREAL` with `ayanamsa=None` is rejected at the service
  boundary (an explicit sidereal frame must always be computable).
- The choice is echoed in every result.

Rationale: Jyotisha operates on the sidereal zodiac (Lahiri ayanamsa is the
JRE-002 default). But "sidereal" is a materially significant choice, and
tropical analysis is a legitimate future consumer request — the frame must
never be silently assumed. Defaulting sidereal while making the mode explicit
satisfies both the tradition and the "no hidden defaults" requirement (J).

### 2. Catalogs are complete, pinned, versioned data

- `rashi.py`: all 12 signs — name, start/end longitude (30° arcs from 0°
  sidereal), classical lord (Mesha=Mars … Meena=Jupiter).
- `nakshatra.py`: all 27 Nakshatras — name, start/end longitude (13°20′ arcs
  from 0° sidereal), classical ruler (Ashwini=Ketu … Revati=Mercury), four
  pada boundaries (3°20′ each), pada mapping, exact longitude math.
- Catalogs are pure data with a documented classical source citation
  (romanization scheme and source pinned by the Specialist; see
  architecture §25.1).
- If stored as data files under `datasets/jyotish/`, they carry SHA-256
  checksums and a README (provenance, version, license) — same discipline as
  the ephemeris files (ADR-001).
- Any catalog change (name, boundary, ruler, source) is a **versioned
  decision** that changes output and therefore the metadata — never silent
  (JSP-001 versioning rule; mirrors astronomy's ephemeris-version rule).

Rationale: reproducibility requires the classification inputs to be as
immutable as the ephemeris; completeness requires the full 27/12 tables, with
the boundary math derived from the arc constants (13°20′, 3°20′, 30°), not
from a hand-written list of example values.

## Consequences

- Classification output is bit-deterministic across catalog versions because
  the catalog version is part of the contract and echoed in metadata.
- A tropical-mode consumer can use the same engine with
  `zodiac_mode=TROPICAL`; Rashi/Nakshatra assignments then reflect the
  tropical frame explicitly.
- The Specialist must produce the canonical romanization + citation and add
  catalog-version metadata to results before CODING.
- Validation compares classification against independent published tables
  (TEST-PLAN §12).

## References

- [JRE-003 Architecture §7, §13, §16, §17](../architecture/JRE-003-JYOTISH-CORE.md)
- [JSP-001 Versioning](../../specifications/core/JSP-001.md)
