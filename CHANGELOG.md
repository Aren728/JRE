# Changelog

All notable changes to JRE are recorded here, per orchestration stage.

## Unreleased

### JRE-002 — Astronomical Core (MERGE stage)

- VALIDATOR independently verified planetary positions against JPL Horizons
  and published Meeus/node constants: **Final verdict PASS** — no
  implementation defects, no blocking validation issues.
- MERGE performed the controlled merge: pre-commit gates (diff/status review,
  validation report present, QA/Validator recorded results, unrelated-change
  scan, private-data scan, astrology-logic scan, architecture conformance) all
  passed; final suite **233 passed** (67 unit + 166 integration), ruff and
  mypy clean.
- Advanced [JRE-002 queue item](orchestration/queue/JRE-002-ASTRONOMICAL-CORE.md)
  from QA-COMPLETE to MERGED in a single commit:
  `Implement JRE-002 deterministic astronomical core`.

### JRE-002 — Astronomical Core (Architect stage)

- Added [ADR-001](docs/decisions/ADR-001-EPHEMERIS-PROVIDER.md): adopt
  `pysweph` (Swiss Ephemeris bindings) as the initial ephemeris provider;
  SWIEPH high-precision mode with bundled local `.se1` files as standard,
  MOSEPH as deterministic fallback, no runtime network dependency.
- Added
  [JRE-002 architecture and refined specification](docs/architecture/JRE-002-ASTRONOMICAL-CORE.md)
  v0.2.0: module layout, data contracts, provider abstraction, time/coordinate
  handling, error taxonomy, determinism contract, testing matrix, validation
  strategy.
- Advanced [JRE-002 queue item](orchestration/queue/JRE-002-ASTRONOMICAL-CORE.md)
  from REQUESTED to ARCHITECTED with specialist handoff checklist.

### JRE-002 — Astronomical Core (CODING stage)

- Implemented the `astronomy` package per the specialist spec v0.3.0:
  `time.py` (IANA-only local->UTC + pure Julian Day), `coordinates.py`,
  `models.py`, `serialize.py`, `config.py`, `provider.py` registry,
  `service.py` facade, and the `swisseph` adapter (SWIEPH standard with
  bundled `.se1` files, MOSEPH fallback, checksum verification, per-call
  state discipline under a lock, Rahu/Ketu from lunar node, ayanamsa modes).
- Shipped happy-path unit tests per test plan §16.

### JRE-002 — Astronomical Core (QA stage)

- QA inspected every module, verified package structure, provider init,
  timezone handling, invalid-input errors, ayanamsa configuration, all nine
  bodies, Rahu/Ketu derivation, longitude normalization, retrograde windows,
  determinism (in-process and cross-process), provider metadata, stable JSON
  serialization, error handling, and boundary cases.
- **Fixed defect**: the pure Julian Day formula in `time.py` drifted by 1–3
  days for accepted pre-1900 dates (up to +7 days by 3000 AD); replaced with
  the canonical proleptic-Gregorian algorithm, now bit-exact vs
  `swe.julday` over 1583–3000.
- **Fixed test defects**: `test_time.py` leap-day JD value (2451604.5 →
  2451604.0), `test_config.py` repo-root off-by-one, `test_static.py`
  stdlib allow-list missing `__future__`.
- Brought the §35 CI gate to green: ruff (88 → 0 errors) and mypy
  (25 → 0 errors, incl. `swisseph` stubless import override and read-only
  `metadata` Protocol property).
- Added the QA integration suite (166 tests): valid input, timezone,
  invalid input, ayanamsa, Rahu/Ketu, boundaries, retrograde windows,
  determinism, provider metadata, serialization, JD cross-check vs
  `swe.julday`/`swe.utc_to_jd`, fallback + checksum corruption, no
  interpretation, cross-process determinism.
- Advanced [JRE-002 queue item](orchestration/queue/JRE-002-ASTRONOMICAL-CORE.md)
  from CODING to QA-COMPLETE (VALIDATOR/MERGE intentionally not started).

### JRE-002 — Astronomical Core (Specialist stage)

- Added [specialist implementation specification](docs/architecture/JRE-002-SPECIALIST-SPEC.md)
  v0.3.0: package architecture, module boundaries, provider abstraction,
  Swiss Ephemeris adapter boundary, data models, time/UTC/JD rules,
  tropical/sidereal separation, ayanamsa interface, Rahu/Ketu representation,
  retrograde/velocity semantics, precision, metadata, flags, determinism,
  error model, validation strategy, test architecture, external reference
  validation, future-provider compatibility, performance/offline constraints,
  caching decision, astronomy/astrology API boundary, serialization format,
  consumer contract for the Gochar and Kundali engines, and CODING handoff.
- Added [data contract](docs/architecture/JRE-002-DATA-CONTRACT.md) v0.3.0:
  field-level model specs, validation rules, JSON Schema, example payload.
- Added [test plan](docs/architecture/JRE-002-TEST-PLAN.md) v0.3.0:
  requirement matrix, determinism/fallback/static gates, golden fixtures,
  external-reference validation harness and tolerance policy.
- Advanced [JRE-002 queue item](orchestration/queue/JRE-002-ASTRONOMICAL-CORE.md)
  from ARCHITECTED to SPECIALIZED (CODING status reserved for CODING).
