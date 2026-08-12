# JRE-002 — Astronomical Core

Status: MERGED
Priority: CRITICAL

## Objective

Create the deterministic astronomical calculation layer of JRE.

## Required Inputs

- Date
- Time
- Latitude
- Longitude
- Timezone
- Ayanamsa configuration

## Required Initial Outputs

For:

- Sun
- Moon
- Mars
- Mercury
- Jupiter
- Venus
- Saturn
- Rahu
- Ketu

calculate:

- Ecliptic longitude
- Latitude where applicable
- Apparent/required astronomical state
- Instantaneous speed where available
- Retrograde/direct state
- Timestamp used
- Ephemeris provider
- Calculation configuration

## Separation Requirement

The astronomical layer MUST NOT perform astrological interpretation.

It must not determine:

- Benefic/malefic status
- House meaning
- Yoga
- Dasha result
- Wealth
- Marriage
- Career
- Prediction

## Provider Architecture

Create an abstraction allowing multiple astronomical providers.

Initial provider:

- Swiss Ephemeris or equivalent validated ephemeris library

Future providers must be capable of being added without rewriting the core.

## Determinism

Identical:

- input timestamp
- coordinates
- timezone
- ephemeris version
- configuration

must produce identical astronomical output.

## Testing Requirements

Tests must include:

1. Valid birth timestamp.
2. Invalid timestamp.
3. Invalid coordinates.
4. Timezone handling.
5. Boundary conditions.
6. Retrograde planet.
7. Provider metadata.
8. Repeated calculation producing identical output.

## Validation

The validator must independently verify selected planetary positions against an external astronomical reference.

## Deliverables

- Specification refinement
- Python implementation
- Automated tests
- Provider abstraction
- Documentation
- Validation report

## Restrictions

Do not implement:
- predictions
- Jyotish interpretations
- Yogas
- Dasha
- Gochar interpretation

Those belong to later modules.

---

## Architect Decision (2026-08-11) — Status: ARCHITECTED

The Architect has reviewed this request. Design decisions and the refined
specification are authoritative; the original requirements above remain in
force.

### Decisions

1. **Ephemeris library: `pysweph`** (active Swiss Ephemeris bindings,
   Python 3.12 wheels, `import swisseph as swe`).
   See [ADR-001](../../docs/decisions/ADR-001-EPHEMERIS-PROVIDER.md).
2. **Computation modes**: SWIEPH high-precision with deterministic bundled
   local `.se1` files as STANDARD; MOSEPH as deterministic FALLBACK. No
   network dependency at runtime.
3. **Defaults**: apparent geocentric positions, speed always computed,
   ayanamsa Lahiri (configurable), Rahu/Ketu from mean node (true node
   configurable).

### Refined specification

The full design — module layout, data contracts, provider abstraction, time
handling, error taxonomy, determinism contract, testing matrix, validation
strategy — is in
[docs/architecture/JRE-002-ASTRONOMICAL-CORE.md](../../docs/architecture/JRE-002-ASTRONOMICAL-CORE.md)
(version 0.2.0).

### Handoff to SPECIALIST (Astronomy agent)

Proceed to the SPECIALIST stage with the refined specification as the input.
Required downstream deliverables and the completion checklist are listed in
section 14 of the architecture document. The astronomy agent's task inbox is
`agents/astronomy/tasks/`.

---

## Specialist Decision (2026-08-11) — Status: SPECIALIZED

The Astronomy specialist has produced the implementable specification.

### Deliverables

1. [Specialist implementation spec v0.3.0](../../docs/architecture/JRE-002-SPECIALIST-SPEC.md)
   — all 32 mandated design points, consumer contract for the Gochar and
   Kundali engines, CODING dependency and handoff requirements, unresolved
   questions.
2. [Data contract v0.3.0](../../docs/architecture/JRE-002-DATA-CONTRACT.md) —
   exact field-level models and JSON Schema for requests and results.
3. [Test plan v0.3.0](../../docs/architecture/JRE-002-TEST-PLAN.md) — test
   layers, requirement matrix, determinism/fallback/static gates, and the
   external-reference validation strategy.

### Key specialist decisions (supersede design-level detail where they conflict)

- Pure provider-independent Julian Day computation in `time.py` (Meeus),
  cross-checked against `swe.utc_to_jd` ≤ 1e-6 days — keeps the core free of
  the swisseph binding.
- Sidereal longitude derived as tropical − ayanamsa (one `calc_ut` per body,
  bit-equivalent to `SEFLG_SIDEREAL`, proved by test).
- Rahu = mean/true lunar node per config; Ketu = node + 180° (derived, not
  computed).
- `ProviderRun` carries per-call mode/files; `ProviderMetadata` is
  provider-stable. Result envelope includes both.
- No caching in this phase; revisit only if a consumer batches many instants.
- `ephemeris_files`: only `se_18.se1`, `sepl_18.se1`, `semo_18.se1` are
  bundled.
- Kundali lagna needs house cusps (`swe.houses`) — a separate future task;
  recorded as an unresolved question.

### Handoff to CODING

Proceed to CODING with the specialist spec, data contract, and test plan.
CODING must create the `astronomy` package only, ship the happy-path tests,
and pass the §35 gate. Do NOT advance this queue item to CODING status by any
agent other than CODING.

### Change history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | — | Request created (Status: REQUESTED) |
| 0.2.0 | 2026-08-11 | Architect review complete (Status: ARCHITECTED) |
| 0.3.0 | 2026-08-11 | Specialist specification complete (Status: SPECIALIZED) |
| 0.4.0 | 2026-08-12 | CODING implemented `astronomy`; QA reviewed and tested the full matrix (Status: QA-COMPLETE) |
| 0.5.0 | 2026-08-12 | MERGE: validated implementation merged in a single commit (Status: MERGED) |

---

## QA Report (2026-08-12) — Status: QA-COMPLETE

The QA stage inspected every module of `src/astronomy/`, executed the full
unit + integration suite, and fixed the defects listed below. Full detail in
the QA report delivered with this handoff.

### QA result: PASS

- Test suite: 233 tests (67 unit + 166 integration), all passing.
- `ruff check src tests`: clean. `mypy src/astronomy` (strict): clean.
- Determinism verified in-process (bit-identical) and cross-process
  (byte-identical JSON).
- No astrological interpretation found in source or runtime output (static +
  integration gates).

### Defects found and fixed (documented)

1. **JD formula drift (implementation defect)** — the pure Julian Day formula
   in `src/astronomy/time.py` deviated from the library by 1–3 days for
   accepted pre-1900 dates and drifted up to +7 days by 3000 AD; it matched
   `swe.julday` only in 1900–2100. Replaced with the canonical proleptic-
   Gregorian algorithm; now bit-exact vs `swe.julday` across 1583–3000
   (verified over 3000+ points) and unchanged for modern dates.
2. **Leap-day test value wrong** — `test_time.py::test_leap_day` asserted JD
   `2451604.5` (the correct value is `2451604.0`); it passed only because of
   `pytest.approx`'s loose default tolerance. Corrected with `abs=1e-6`.
3. **`test_config.py` repo-root off-by-one** — `REPO_ROOT` used `parents[4]`
   instead of `parents[3]`, so the repo config test silently read a
   non-existent path.
4. **Static stdlib allow-list missing `__future__`** — `test_static.py`
   rejected `from __future__ import annotations` in `models.py`.
5. **CI gate not green at handoff** — ruff reported 88 errors and mypy 25
   (type-arg annotations, `swisseph` stubless import override, read-only
   `metadata` Protocol property, `StrEnum` modernization, line-lengths). All
   fixed; the §35 gate is now green.

### QA observations (no code change)

- `ayanamsa_override` is accepted but has no effect for the predefined
  ayanamsa modes (LAHIRI/RAMAN/FAGAN_BRADLEY); `swe.set_sid_mode` ignores
  `t0/ayanamsa_t0` for predefined modes. It only matters for a future
  user-defined (SIDM_USER) mode. Recorded in the data contract's semantics;
  not a defect for the current enum.
- `se_18.se1` is intentionally not bundled (documented deviation in
  `datasets/ephemeris/README.md`); verified all nine bodies compute in SWIEPH
  with only `sepl_18.se1` + `semo_18.se1`.
- `scripts/astronomy/compute_once.py` from the test plan §7 was not shipped by
  CODING; the cross-process determinism test runs an inline child process
  instead, covering the same requirement.

### Handoff to VALIDATOR / MERGE

QA is complete. The next stages (external-reference validation against
JPL Horizons and merge) are NOT to be started by the QA stage.

---

## Merge Decision (2026-08-12) — Status: MERGED

The MERGE agent reviewed the completed pipeline (REQUEST → ARCHITECT →
SPECIALIST → CODING → QA → VALIDATOR) and performed the controlled merge.

### Pre-merge verification (all passed)

1. `git diff` / `git status` inspected: changes are limited to JRE-002
   files — `src/astronomy/`, `tests/`, `config/`, `datasets/ephemeris/`,
   `pyproject.toml`, the JRE-002 architecture/data-contract/specialist/test-
   plan/validation docs, `CHANGELOG.md`, and this queue item.
2. Validation report present:
   [docs/validation/JRE-002-VALIDATION-REPORT.md](../../docs/validation/JRE-002-VALIDATION-REPORT.md)
   — **Final verdict: PASS** (independent JPL Horizons + Meeus references,
   no implementation defects, no blocking issues).
3. QA/Validator test result recorded and re-confirmed by a final run:
   **233 tests** (67 unit + 166 integration) passing; `ruff check src tests`
   clean; `mypy src/astronomy` clean.
4. No unrelated files or functionality introduced (only JRE-002 content;
   `src/jre.egg-info/` build artifact excluded via `.gitignore`).
5. No personal/private birth-chart data committed — test coordinates are the
   spec's public golden fixture and public city coordinates only.
6. No astrological prediction logic in `src/astronomy` (static scan clean;
   the only matches are explicit non-goal docstrings in `__init__.py`).
7. Source tree corresponds to the approved architecture (module layout in
   architecture doc §5 matches `src/astronomy/` exactly).
8. Ephemeris data files (`sepl_18.se1`, `semo_18.se1`) bundled with
   documented SHA-256 checksums for offline determinism (per ADR-001).

### Decision

Merge the complete JRE-002 implementation and its approved documentation,
tests, and configuration in a single commit:
`Implement JRE-002 deterministic astronomical core`.

Status advanced: **QA-COMPLETE → MERGED**.

---

## Handoff to CODING (historical)

CODING created the `astronomy` package (implemented 2026-08-11/12) and
shipped the happy-path unit tests; QA verified and completed the remaining
matrix per the test plan.
