# ADR-028 — Gochar Provenance: Source-Layer Echo with No Environment-Dependent Data

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-006 Gochar / Continuous Transit Engine](../architecture/JRE-006-GOCHAR-TRANSIT-ENGINE.md)
- Supersedes: nothing (extends ADR-016 provenance discipline to the gochar layer)
- Decision maker: Architect

## Context

JRE-006 results wrap echoes from JRE-002 (via JRE-003), JRE-003, and
JRE-005. Consumers must be able to trace every fact to its source layer
and pinned versions — and determinism forbids provenance fields that
vary between runs (wall-clock time, randomness, process identity,
environment).

## Decision

1. **`GocharProvenance` on every externally observable result** with:
   - `derivation_id` (stable, e.g. `"gochar.instant.v1"`) and
     `derivation_version`;
   - `source_layers` — ordered tuple of layers actually consumed;
   - `jyotish_version`, `bhava_version`, `gochar_version`;
   - `ephemeris_version` — echoed from JRE-003 provider metadata;
   - `catalog_versions` — rashi/nakshatra catalog versions echoed;
   - `input_echo` — interval bounds, bodies, reference point, house
     system, sample step, aspect flag;
   - `algorithm` — the derivation/echo method label.
2. **No environment-dependent data**: no timestamps of the derivation
   run, no random values, no process IDs, no `os.environ` values, no
   hostnames. Provenance is a pure function of the query and the pinned
   versions.
3. **Echo semantics**: provenance records *which* upstream layer
   produced each echoed value (e.g. `"echo-jre003-events-bisection"`,
   `"derive-transit-houses-jre005"`); JRE-006 never claims to have
   computed what it echoed.
4. **Machine-testable**: the provenance-hygiene static scan rejects
   `time(`, `random`, `getpid`, `environ` in provenance construction;
   determinism tests include provenance in the byte-compare.

Rationale:

- Traceability without breaking the determinism contract; mirrors the
  JRE-005 DerivationBlock discipline (ADR-016) with a gochar-specific
  field set.

Rejected alternatives:

- **Omitting provenance** — violates the architecture principle that
  every externally observable state be traceable; rejected.
- **Including derivation wall-clock time** — breaks byte determinism;
  rejected.

## Consequences

- DATA-CONTRACT §4.1 pins the field set; determinism tests byte-compare
  full serialized results including provenance.
- The provenance-hygiene static scan is part of the CODING/QA gates.

## References

- [JRE-006 architecture core §12, §17](../architecture/JRE-006-GOCHAR-TRANSIT-ENGINE.md)
- [JRE-006 data contract §4.1](../architecture/JRE-006-DATA-CONTRACT.md)
- [ADR-016](../decisions/ADR-016-DERIVED-FACT-PROVENANCE.md)
