# JRE-002 — Astronomical Core: Test Plan

- Status: SPECIALIZED
- Version: 0.3.0
- Date: 2026-08-11
- Upstream: [Specialist Spec §24–§26, §35](JRE-002-SPECIALIST-SPEC.md),
  [Data Contract](JRE-002-DATA-CONTRACT.md)

Ownership: QA authors and executes the full matrix. CODING ships the
happy-path subset (§16). VALIDATOR owns the external-reference harness (§12).

## 1. Test layers and directory layout

```
tests/
  unit/astronomy/          # pure logic — runs with NO Swiss Ephemeris installed
  integration/astronomy/   # real Swiss Ephemeris (pysweph + .se1 files)
  validation/astronomy/    # external-reference harness (VALIDATOR)
```

- **Unit** must never import `swisseph`; a fixture-time guard fails the
  session if `swisseph` is imported by any unit test.
- **Integration** requires the bundled `.se1` files and `pysweph==2.10.3.6`;
  skipped with a clear reason if the environment lacks them.

## 2. Requirement matrix (JRE-002 mandated tests)

| # | Requirement | File(s) | Key assertions |
|---|---|---|---|
| 1 | Valid birth timestamp | `unit/.../test_valid_input.py`, `integration/.../test_valid_input.py` | Nine bodies returned in canonical order; every float finite; longitude `[0,360)`; latitude `[-90,90]`; `retrograde ∈ enum`; `position_type` echoes config |
| 2 | Invalid timestamp | `unit/.../test_invalid_timestamp.py` | `InvalidTimestampError` for: nonexistent zone, abbreviation zone, DST-gap local time, out-of-coverage (year boundary via constant check) |
| 3 | Invalid coordinates | `unit/.../test_invalid_coordinates.py` | `InvalidCoordinatesError` for lat 91, lon −181, `NaN`, `±Inf` |
| 4 | Timezone handling | `unit` + `integration/.../test_timezone.py` | Same UTC instant written in two zones → **identical** positions; same local wall time in two zones → different positions; offset echoed in `timestamp_local_iso` |
| 5 | Boundary conditions | `integration/.../test_boundaries.py` | Equator/poles; longitude ±180 and 0/360 normalization; midnight; leap day (2000-02-29, 1900-02-29 invalid); longitude normalization `[0,360)`; `-0.0 → 0.0` |
| 6 | Retrograde planet | `integration/.../test_retrograde.py` | Known retrograde window (historical Mars/Mercury dates) → `RETROGRADE` and speed sign negative; a known station date → `STATIONARY` (calibrates ε, §12) |
| 7 | Provider metadata | `integration/.../test_provider_metadata.py` | `ProviderMetadata` stable (`provider_id`, library + ephemeris versions); `ProviderRun.ephemeris_mode` records actual mode; config snapshot present |
| 8 | Repeated calculation | `integration/.../test_determinism.py` | Same request twice (same process) → bit-identical floats; separate processes → identical (see §7) |

## 3. Determinism tests

- `test_determinism.py`:
  - Two identical requests in-process → every float `==` (bit equality).
  - Cross-process: run a child `python -c` script that writes
    `result_to_json` output; compare byte-for-byte with parent-process output.
  - Interleave two different configs (Lahiri then RAMAN then Lahiri) →
    results identical to isolated runs (proves per-call state discipline).
- Golden fixtures (see §6) guard against library-upgrade drift.

## 4. Fallback tests

- `test_fallback.py` (integration):
  - With a fenced/nonexistent `ephemeris_path` and `allow_fallback=true` →
    result succeeds with `ProviderRun.ephemeris_mode == MOSEPH`,
    `ephemeris_files == ()`; `retflag` integrity maintained.
  - With `allow_fallback=false` → `EphemerisDataError`.
  - Checksum corruption: flip a byte in a temp copy of a `.se1` file →
    fallback or error per config (never silent success).
- Precision characterization (not an assertion of equality):
  - SWIEPH vs MOSEPH for the same instant: planets within ≤ 0.1 arcsec;
    recorded in a report for documentation.

## 5. Time and coordinate tests

- `test_time.py` (unit): pure JD formula vs known JD values
  (e.g. J2000.0 = 2451545.0 for 2000-01-01T12:00:00Z); Gregorian-only;
  midnight and leap-year cases; fold=0 resolution.
- `test_jd_crosscheck.py` (integration): pure JD vs
  `swe.utc_to_jd(y, mo, d, h, mi, s, swe.GREG_CAL)[2]` within `1e-6` days over
  a fixture set spanning 1900–2100 (DST and non-DST zones, leap days).
- `test_coordinates.py` (unit): pure validation rules per DATA-CONTRACT §7.
- Coverage-boundary note: accepted dates are ≥ 1582-10-15 (proleptic
  Gregorian — Specialist Spec §9.5); earlier civil dates raise
  `InvalidTimestampError`. `test_gregorian_transition.py`: 1582-10-15
  accepted, 1582-10-04 rejected, and the pure JD for 1582-10-15 agrees with
  `swe.utc_to_jd` within 1e-6 days. (Python `datetime` years 1–9999 are all
  inside the `.se1` coverage, so the coverage constant itself is tested as a
  pure boundary function.)

## 6. Fixtures and golden files

- `tests/fixtures/astronomy/requests.json` — a catalog of valid requests
  (varied zones: `Asia/Kolkata`, `America/New_York`, `Europe/London`,
  `Pacific/Auckland`, `UTC`; varied coordinates incl. equator, poles, ±180).
- `tests/fixtures/astronomy/golden/` — committed `result_to_json` outputs for
  a fixed library + data version, stored with **hex-float** representation
  (`float.hex()`) to survive repr changes; a `GOLDEN_VERSION` constant pins
  the producing environment.
- Golden comparison asserts exact hex equality. Regenerating goldens is an
  explicit, versioned act (never automatic).

## 7. Cross-process determinism harness

- A script `scripts/astronomy/compute_once.py` reads a request JSON from
  stdin and writes the result JSON to stdout (added at CODING stage).
- The determinism test invokes it twice in separate subprocesses and compares
  bytes. This also serves as a CLI smoke test for consumers.

## 8. Static / structural tests

- `test_public_surface.py`: `astronomy.__all__` matches §1 of the Specialist
  Spec exactly; no extra public names.
- `test_forbidden_imports.py`: no `astrology|knowledge|transits|dasha|
  calculations|inference` import in `src/astronomy/**`; no
  `socket|requests|urllib` import (offline guarantee); `models.py` imports
  only stdlib.
- `test_no_interpretation.py`: asserts no interpretation vocabulary
  (`rashi`, `nakshatra`, `yoga`, `dasha`, `gochar`, `benefic`, `malefic`,
  `house`, `prediction`) appears in `src/astronomy/**` identifiers or public
  docstrings (case-insensitive, excluding the string "gochar engine"
  reference in consumer-contract docs — kept only in docs, not code).

## 9. Adapter correctness tests

- `test_sidereal_equivalence.py`: tropical − ayanamsa (our derivation) ==
  `SEFLG_SIDEREAL` call within `1e-12` deg, over the fixture catalog —
  anchors the §12 decision of the Specialist Spec.
- `test_flag_integrity.py`: `retflag` contains the requested ephemeris bit
  for every body in every mode.
- `test_node_modes.py`: mean vs true node differ; both deterministic; Ketu =
  node + 180° exactly (mod 360); Ketu latitude == node latitude; node speeds
  equal.
- `test_ayanamsa_modes.py`: LAHIRI/RAMAN/FAGAN_BRADLEY each produce stable,
  ordered ayanamsa values; `ayanamsa=None` ⇒ `longitude_sidereal is None` and
  `ayanamsa_value is None`.

## 10. Provider-independence tests

- `test_fake_provider.py` (unit): a stub provider registered in the registry;
  full `EphemerisRequest` → `EphemerisResult` pipeline works without the real
  engine; service assembly (timestamps, JD, snapshots) verified against the
  stub's `ProviderRun`.
- `test_registry.py`: register/get/default; unknown `provider_id` →
  `UnsupportedProviderError`; registry frozen after first compute.
- `test_body_ordering.py`: `bodies` given as a shuffled subset returns
  positions in canonical `BodyId` order, deduplicated (Specialist Spec §14).
- `test_empty_bodies.py`: `bodies=()` raises `EphemerisError`
  (`"bodies must not be empty"`).

## 11. Serialization tests

- `test_serialize.py`: JSON round-trips per DATA-CONTRACT §10; JSON Schema
  conformance (validate example payloads against the schema in
  DATA-CONTRACT §8 using a schema validator); enums serialize as strings;
  `None` → `null`; `-0.0 → 0.0`; microsecond timestamps round-trip.

## 12. External-reference validation (VALIDATOR)

- **Source**: NASA JPL Horizons, geocentric apparent ecliptic-of-date
  longitude (and latitude where relevant), independently queried at
  validation-authoring time; plus published almanac spot-checks.
- **Dataset**: `datasets/validation/astronomy/reference_positions.csv` —
  committed; no network at runtime or during validation runs.

CSV schema:

```csv
instant_utc,longitude_deg,latitude_deg,body,reference,notes
1990-06-15T04:30:00Z,84.123456789,0.0000123,SUN,JPL_HORIZONS,retrograde_window_mars
```

- **Instants**: ≥ 6, spanning: one retrograde window (e.g. Mars), one node
  position, one sidereal-known date, plus 3 normal dates.
- **Tolerance policy**: initial proposed budget ≤ 0.01° longitude for planets
  vs. Horizons, accounting for frame/model differences (ICRS vs
  ecliptic-of-date, apparent conventions). The Architect reviews the first
  batch and **fixes** the budget in the CSV before it is authoritative.
- **Harness**: `tests/validation/astronomy/test_reference_positions.py`
  reads the CSV, computes each instant through `AstronomicalService`, asserts
  within budget, and emits a per-body report. Runs offline.
- **Retrograde cross-check**: at least one instant inside a known retrograde
  window asserts `RetrogradeState.RETROGRADE`.
- **Stationary `ε` calibration (method)**: pick 2–3 real station dates (e.g.
  Mercury and Mars stations); for each, compute speeds at hourly instants
  across ±3 days and measure the noise floor (max |Δspeed| between adjacent
  instants, and SWIEPH vs MOSEPH spread). Set `ε` strictly above the largest
  observed noise floor (expected ≥ 1e-6 deg/day) so normal motion can never
  classify `STATIONARY`; record the chosen `ε` as a versioned decision
  (Specialist Spec §16, §36.1).

## 13. Performance smoke test

- `integration/.../test_performance.py`: 9-body request, p95 < 50 ms incl.
  first-call init; RSS delta < 50 MB. Informational — reported, not a hard CI
  gate (Specialist Spec §28).

## 14. Offline guarantee

- Covered structurally by §8 (no network imports). Additionally the
  integration suite runs with `PYTHONHTTPSVERIFY`-independent, local-only
  data; no test may open a socket. A conftest hook asserts `socket` is never
  called during unit+integration runs.

## 15. Tooling and commands

Documented for QA/CODING (installed only at CODING stage, per orchestration):

```
python -m pytest tests/unit tests/integration -q          # full gate
python -m pytest tests/validation -q                       # VALIDATOR harness
ruff check src tests
mypy src/astronomy
```

- CI-format gate: unit + integration + ruff + mypy must be green before
  CODING → QA handoff (Specialist Spec §35.5).

## 16. CODING happy-path subset (shipped with implementation)

- `test_valid_input.py` (unit + integration, nine bodies)
- `test_invalid_timestamp.py`, `test_invalid_coordinates.py` (core cases)
- `test_timezone.py` (basic), `test_determinism.py` (in-process)
- `test_provider_metadata.py`, `test_public_surface.py`,
  `test_forbidden_imports.py`, `test_fake_provider.py`

QA completes the remaining matrix (§2–§14).

## 17. Acceptance criteria for JRE-002 tests

1. All unit + integration tests green on a clean 3.12 environment with the
   pinned deps and committed `.se1` files.
2. Determinism proven in-process and cross-process (bit equality).
3. All 8 mandated requirement tests present and green.
4. External-reference validation runs offline and reports within the fixed
   budget.
5. No interpretation vocabulary in `src/astronomy` (static gate).

## 18. Change history

| Version | Date | Change |
|---|---|---|
| 0.3.0 | 2026-08-11 | Specialist test plan (this document) |
