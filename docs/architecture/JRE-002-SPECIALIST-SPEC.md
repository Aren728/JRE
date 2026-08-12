# JRE-002 — Astronomical Core: Specialist Implementation Specification

- Status: SPECIALIZED
- Version: 0.3.0 (supersedes the design-level detail of the architecture doc v0.2.0)
- Date: 2026-08-11
- Author: Astronomy Specialist
- Upstream: [JRE-002 Architecture v0.2.0](JRE-002-ASTRONOMICAL-CORE.md), [ADR-001](../decisions/ADR-001-EPHEMERIS-PROVIDER.md), [JSP-001 Core Specification](../../specifications/core/JSP-001.md)

This is the **implementable** specification for the astronomical core. Where it
conflicts with the architecture document, this document wins (both are
versioned; changes are recorded in §36). It is the contract for CODING, QA and
VALIDATOR.

> **Supersession notice (read first):** the module layout and data models in
> the architecture document v0.2.0 (§5–§6) are superseded at implementation
> level by this spec and by
> [JRE-002-DATA-CONTRACT.md](JRE-002-DATA-CONTRACT.md) v0.3.0, which add
> `EphemerisRequest.provider_id` and split per-call `ProviderRun` from
> provider-stable `ProviderMetadata`. CODING MUST implement against the 0.3.0
> documents.

## 1. Python package architecture

- **Python**: 3.12 only (target host: Linux, 2 cores, ~4 GB RAM).
- **Layout**: src-layout. `pyproject.toml` at the repository root, distribution
  name `jre`, package discovery under `src/` (`[tool.setuptools] package-dir =
  {"" = "src"}`). Only the `astronomy` package exists in this task.
- **Import name**: `astronomy` (per scaffold + architecture decision; a `jre.`
  namespace root is a later, separately-versioned refactor — never silent).
- **Public surface**: `astronomy/__init__.py` exports ONLY
  `AstronomicalService`, `EphemerisRequest`, `EphemerisResult`, `BodyId`,
  `CalculationConfig`, `Ayanamsa`, `EphemerisMode`, `PositionType`, `NodeType`,
  `RetrogradeState`, and the public errors. An explicit `__all__` enforces this
  (tested, see TEST-PLAN §8).
- **Versioning**: `astronomy.__version__` == spec version `0.3.0`. Package
  version is bumped only by an explicit versioned decision.
- **No astrological package may be created or imported by this task.** No
  `astrology/`, `transits/`, `knowledge/` code, data or imports.

## 2. Module boundaries

Every file, one responsibility, no cycles:

| File | Responsibility | Imports (allowed) |
|---|---|---|
| `src/astronomy/__init__.py` | Public API allow-list | its own modules only |
| `src/astronomy/models.py` | All dataclasses + enums. **Pure data; zero imports beyond stdlib.** No `swe` reference anywhere | stdlib |
| `src/astronomy/errors.py` | Error hierarchy | — |
| `src/astronomy/time.py` | Local→UTC normalization; pure Julian Day; fold policy | stdlib `zoneinfo`, `datetime` |
| `src/astronomy/coordinates.py` | Geographic validation + normalization (pure) | stdlib, `models`, `errors` |
| `src/astronomy/provider.py` | `EphemerisProvider` Protocol, `ProviderRegistry`, `get_provider()` | `models`, `errors` |
| `src/astronomy/config.py` | Loads `config/astronomy.toml` → `CalculationConfig` | stdlib `tomllib`, `models` |
| `src/astronomy/service.py` | `AstronomicalService`: validate → normalize → JD → provider → assemble result | everything above |
| `src/astronomy/serialize.py` | `result_to_json`, `request_from_dict`, `config_from_dict` (JSON schema per DATA-CONTRACT) | `models` |
| `src/astronomy/swisseph/__init__.py` | `get_provider()` (adapter factory) | adapter modules |
| `src/astronomy/swisseph/constants.py` | Named `swe` constants and mappings (no magic numbers in other files) | `swisseph` binding only |
| `src/astronomy/swisseph/ephemeris.py` | `.se1` path resolution, version + SHA-256 metadata, readiness check | stdlib, `errors` |
| `src/astronomy/swisseph/provider.py` | `SwissEphemerisProvider` (the only file importing `swisseph` for positions) | constants, ephemeris, models, provider protocol |

Rules:

- **Import direction is one-way**: `service → provider → swisseph`. No module
  in `astronomy` may import `astrology`, `knowledge`, `transits`, `calculations`,
  `dasha`, or `inference` (enforced by a static test).
- `models.py` must not import `time`, `provider`, or `service` (keeps the data
  contract dependency-free for consumers).
- The `swisseph` binding (`import swisseph as swe`) may be referenced **only**
  from the three `swisseph/*` modules. Consumers never see it.

## 3. Provider abstraction

```python
# provider.py
class EphemerisProvider(Protocol):
    provider_id: str
    metadata: ProviderMetadata

    def compute(self, jd_ut: float, bodies: tuple[BodyId, ...],
                config: CalculationConfig) -> ProviderRun: ...
```

- **Ownership split (authoritative).** The service owns: input validation,
  time normalization, Julian Day computation, and assembly of
  `EphemerisResult`. Providers are pure position engines: in →
  `(jd_ut, bodies, config)`; out → `ProviderRun`. Providers never see raw
  requests, never validate, never use clocks/timezones/calendars.
- `ProviderRegistry`:
  - `register(provider: EphemerisProvider) -> None`
  - `get(provider_id: str) -> EphemerisProvider` (raises
    `UnsupportedProviderError`)
  - `default() -> EphemerisProvider` (the Swiss Ephemeris adapter; override via
    `AstronomicalService(provider_id=...)`)
  - Registry is process-scoped, populated at first use; it is read-only after
    first `compute()` (guard against mid-flight mutation).
- `provider_id` values are stable strings, e.g. `"swisseph.pysweph"`.
- **Provider contract** (any future provider must): return a `ProviderRun`
  with positions in `BodyId` canonical order, honor `CalculationConfig`
  semantics (mode/ayanamsa/position type), be deterministic for identical
  inputs, never silently fall back (record the actual mode), and raise
  `EphemerisError` subclasses for failures. No provider may perform
  astrological interpretation.

## 4. Swiss Ephemeris provider boundary

The adapter (`swisseph/provider.py`) is the ONLY production code touching the
binding. Precise behavior:

1. **Ephemeris path**: `swe.set_ephe_path(config.ephemeris_path)` — resolved
   once per provider instance to the pinned `datasets/ephemeris/` directory
   (default), recorded in metadata.
2. **Flags** (see §21 for the full matrix):
   - Standard: `SEFLG_SWIEPH | SEFLG_SPEED`
   - Fallback: `SEFLG_MOSEPH | SEFLG_SPEED`
   - `SEFLG_TRUEPOS` added only when `position_type == PositionType.TRUE`
   - Sidereal is NOT passed as a flag: see §12 derivation decision.
3. **Body calls**: `swe.calc_ut(jd_ut, swe.<BODY>, flags)` per body; returns
   `(xx, retflag)`. `retflag` MUST contain the requested ephemeris flag; if it
   does not (e.g. SWIEPH unavailable), treat as data failure (§23 rule).
4. **Ayanamsa**: per call, `swe.set_sid_mode(sid_mode, t0, ayanamsa_t0)` from
   config (§13), then `ayanamsa_value = swe.get_ayanamsa_ut(jd_ut)`.
5. **Nodes**: RAHU/KETU from `swe.MEAN_NODE` (default) or `swe.TRUE_NODE`
   (per config); see §15.
6. **Retrograde/stationary**: derived from `speed_longitude` (§16).
7. **Mode integrity**: the mode actually used is recorded in
   `ProviderRun.ephemeris_mode`; files used in `ProviderRun.ephemeris_files`
   (empty tuple for MOSEPH). Fallback is never silent (§22).
8. **Global state discipline**: every `swe.set_*` call is executed from the
   immutable request config on every call. A module-level `threading.Lock`
   serializes adapter calls (the C library keeps process-global state); the
   service is otherwise single-threaded.
9. **No caching inside the adapter** (see §30).

## 5. Input data model

`EphemerisRequest` (frozen dataclass; full field spec in DATA-CONTRACT §1):

- `date: datetime.date` — local civil date.
- `time: datetime.time` — local civil time; precision ≥ 1 second is accepted
  and preserved exactly (sub-second components are legal, never rounded).
- `timezone: str` — IANA zone name.
- `latitude: float`, `longitude: float` — degrees (§10).
- `bodies: tuple[BodyId, ...] | None` — `None` means all nine (§14).
- `config: CalculationConfig` — immutable defaults from
  `config/astronomy.toml`, overridable per request.
- `provider_id: str | None` — registry selection; `None` → default.

Rejected inputs raise typed errors (§23) before any provider call.

## 6. Output astronomical data model

- `BodyPosition` — per-body raw astronomical state (§DATA-CONTRACT §3).
- `ProviderRun` — per-call provider outcome (§DATA-CONTRACT §5).
- `EphemerisResult` — the full service envelope (§DATA-CONTRACT §6).

All outputs are raw astronomy: longitude, latitude, distance, velocities,
retrograde state, ayanamsa value, timestamps, metadata. **No** rashi,
nakshatra, house, yoga, dasha, benefic/malefic, or prediction field exists or
may be added.

## 7. Timestamp representation

- **Internal instant**: a `datetime.datetime` in UTC (aware), microsecond
  precision, derived exactly from inputs.
- **`timestamp_utc_iso`**: ISO 8601, `Z` suffix, e.g. `"1990-06-15T04:30:00Z"`;
  includes microseconds only when nonzero. This is the instant computed.
- **`timestamp_local_iso`**: ISO 8601 with numeric offset from the IANA zone,
  e.g. `"1990-06-15T10:00:00+05:30"` — unambiguous echo of the civil input.
- **`julian_day_ut`**: the exact JD (double) of the UTC instant, computed by
  the pure algorithm in §9. This is the value handed to the provider.
- **No rounding** of the instant anywhere; the double JD is the calculation
  key, the ISO strings are audit metadata.

## 8. Timezone handling

- IANA names only, via `zoneinfo.ZoneInfo`. Accept `"UTC"` and `"Etc/GMT*"`;
  reject abbreviations (`"IST"`, `"PST"`, `"EST"`) and POSIX strings →
  `InvalidTimestampError`.
- Unknown/unresolvable zone name → `InvalidTimestampError`.
- **Ambiguous local times** (DST fall-back): `fold=0` (first occurrence).
  Fixed; never guesswork.
- **Nonexistent local times** (DST spring-forward gap): `InvalidTimestampError`.
- `tzdata` (IANA database) is pinned as a runtime dependency so zone resolution
  is identical across hosts (determinism, §22).

## 9. UTC conversion rules

1. Build naive local datetime from `date + time` with
   `ZoneInfo(timezone)`; apply `fold=0`; catch the nonexistent-time error and
   translate to `InvalidTimestampError`.
2. Convert: `dt_utc = dt_local.astimezone(timezone.utc)` — exact; the local
   offset is applied, not assumed.
3. **Julian Day (pure, provider-independent)**: `time.py` implements the
   documented Gregorian JD formula (Meeus, *Astronomical Algorithms*, Ch. 7):

   ```
   JD = 367Y − floor(7·(Y + floor((M+9)/12))/4) + floor(275·M/9)
        + D + 1721013.5 + (h + m/60 + s/3600)/24
   ```

   with `Y, M, D` from the UTC datetime. The result is a UT Julian Day for
   the civil UTC instant (leap seconds not applied — consistent with how
   `swe.calc_ut` interprets UT JDs; ΔT is applied internally by the library).
4. **Cross-check requirement**: a test asserts the pure JD agrees with
   `swe.utc_to_jd(y, mo, d, h, mi, s, swe.GREG_CAL)[2]` (`jd_ut`) within
   `1e-6` days across a fixture set (TEST-PLAN §9). This anchors the pure
   algorithm to Swiss Ephemeris conventions without coupling `time.py` to the
   binding.
5. Coverage: the ephemeris files cover 13201 BC – AD 17191, but the pure JD
   formula is **proleptic-Gregorian only**. To keep JD conversion exact and
   unambiguous, the accepted input range is **1582-10-15 onward** (the
   Gregorian calendar reform). Earlier civil dates (Julian calendar) raise
   `InvalidTimestampError` with a message stating the restriction; Julian
   calendar support is a deferred, separately-versioned extension
   (§36). The transition boundary is tested (TEST-PLAN §5).

## 10. Geographic coordinate validation

- `latitude ∈ [-90, 90]`, `longitude ∈ [-180, 180]`; both must be finite
  (reject `NaN`, `±Inf`).
- Precision: values are used exactly as provided (no rounding); the model
  documents geodetic convention (WGS-84-style latitude/longitude in decimal
  degrees) for future topocentric use.
- Violations raise `InvalidCoordinatesError` with the offending value in
  `__str__`.
- Validation lives in `coordinates.py` (pure) and is invoked once, at the
  service boundary, before any provider call.

## 11. Coordinate reference conventions

- **Frame**: ecliptic coordinates of date (tropical zodiac), geocentric,
  **apparent** by default (light-time, aberration and nutation applied by the
  library). `PositionType.TRUE` adds `SEFLG_TRUEPOS` (geometric, uncorrected).
- **Longitude**: degrees in `[0, 360)`, measured eastward from the vernal
  equinox (tropical) or from the sidereal zero point (sidereal, §12).
- **Latitude**: ecliptic latitude, degrees, `+` = north of the ecliptic.
- **Distance**: astronomical units (AU).
- **Speeds**: degrees/day (longitude, latitude) and AU/day (distance).
- Boundary normalization: `0° == 360° → 0°`; `-0.0 → 0.0` everywhere.
- Topocentric positions are explicitly out of scope (future, versioned).

## 12. Tropical/sidereal separation

- **Decision**: the provider computes **tropical** positions only (no
  `SEFLG_SIDEREAL` flag), obtains the ayanamsa value for the instant via
  `swe.get_ayanamsa_ut(jd_ut)`, and derives

  ```
  longitude_sidereal = normalize(longitude_tropical − ayanamsa_value, 0, 360)
  ```

  Rationale: one `calc_ut` call per body keeps speed/longitude self-consistent;
  the library guarantees sidereal = tropical − ayanamsa, so the derivation is
  bit-equivalent to `SEFLG_SIDEREAL` (proved by a cross-check test, TEST-PLAN
  §9). Both longitudes are returned; `longitude_sidereal` and
  `ayanamsa_value` are `None` when `config.ayanamsa is None`.
- The ayanamsa value is **astronomical data**, not interpretation. Rashi /
  nakshatra assignment (division of longitude into 30°/13°20′ arcs) belongs to
  consumers and is forbidden here.

## 13. Ayanamsa configuration interface

```python
class Ayanamsa(str, Enum):
    LAHIRI = "LAHIRI"            # -> swe.SIDM_LAHIRI
    RAMAN = "RAMAN"              # -> swe.SIDM_RAMAN
    FAGAN_BRADLEY = "FAGAN_BRADLEY"  # -> swe.SIDM_FAGAN_BRADLEY
```

- `CalculationConfig.ayanamsa: Ayanamsa | None = Ayanamsa.LAHIRI`;
  `None` disables sidereal output (tropical only).
- `CalculationConfig.ayanamsa_override: tuple[float, float] | None = None` —
  optional `(t0, ayanamsa_t0)` passed to `swe.set_sid_mode` for custom
  ayanamsa definitions; `None` → pass `(0.0, 0.0)` (library built-in
  definition for the selected mode).
- Default (Lahiri) and every mode must be covered by tests; the ayanamsa value
  used is echoed in `BodyPosition.ayanamsa_value` and the config snapshot.

## 14. Planet identifier model

```python
class BodyId(str, Enum):
    SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN, RAHU, KETU
```

- Canonical order = declaration order above; `EphemerisResult.positions` is
  always in this order (dedupe if `bodies` repeats).
- Mapping (in `swisseph/constants.py`, no magic numbers elsewhere):
  `SUN→swe.SUN, MOON→swe.MOON, MARS→swe.MARS, MERCURY→swe.MERCURY,
  JUPITER→swe.JUPITER, VENUS→swe.VENUS, SATURN→swe.SATURN,
  RAHU→swe.MEAN_NODE|swe.TRUE_NODE (per config), KETU→derived (see §15)`.

## 15. Rahu/Ketu representation

- **Rahu** = the lunar node specified by `config.node_type` (`MEAN` default,
  `TRUE` optional): one `swe.calc_ut` call on `swe.MEAN_NODE` or
  `swe.TRUE_NODE`.
- **Ketu** = `normalize(node_longitude + 180, 0, 360)`; latitude = node
  latitude (0 in ecliptic frame); speed = node speed; retrograde state = node
  retrograde state.
- Node positions carry the same `position_type`/ayanamsa semantics as planets.
- Retrograde classification is the same sign-based rule as planets — no
  special-casing of nodes (the mean node is retrograde in longitude most of
  the time; the rule still applies).

## 16. Retrograde/direct calculation

- `speed_longitude` from the library (`xx[3]`, `SEFLG_SPEED`).
- Classification (in `models` as a pure function of speed):

  ```
  speed < −ε  → RETROGRADE
  speed > +ε  → DIRECT
  else        → STATIONARY
  ```

- Default `ε = 1e-9` deg/day is a **starting value pending calibration**.
  Calibration (TEST-PLAN §12) measures the speed **noise floor** around real
  station dates (e.g. via SWIEPH vs MOSEPH spread and consecutive-instant
  speed deltas) and sets ε above that floor; the final value is recorded in
  the documentation and changes only by a versioned decision.
- Consumers never re-derive retrograde state from raw speed themselves; they
  read `BodyPosition.retrograde`.

## 17. Planetary velocity representation

- `speed_longitude: float` — deg/day (primary; drives retrograde).
- `speed_latitude: float` — deg/day.
- `speed_distance: float` — AU/day.
- Units are part of the data contract (never implied); JSON schema documents
  them (DATA-CONTRACT §3).

## 18. Precision and numeric representation

- All numerics are IEEE-754 doubles (Python `float`).
- No rounding or truncation at any boundary — determinism requires identical
  bits (§22). Floats serialize via Python's shortest round-trip repr
  (`json.dumps` default), so JSON preserves the exact double value.
- Expected source precision: SWIEPH ~0.001 arcsec for planets; MOSEPH
  ~0.1 arcsec. These are informational, not asserted in unit tests (tolerance
  policy lives in validation, TEST-PLAN §12).
- Fixed-point/Decimal output formats are a consumer concern, not the core's.

## 19. Ephemeris version metadata

- Pinned data files (committed): `se_18.se1`, `sepl_18.se1`, `semo_18.se1`
  (ephemeris version `"18"`). `seas_18.se1` intentionally not bundled.
- `datasets/ephemeris/README.md` lists file names, source, version, SHA-256
  checksums, and Swiss Ephemeris licensing.
- `ephemeris.py` verifies file presence (and checksums on first use — cheap,
  one pass) and reports `ephemeris_version` into `ProviderMetadata`.
- Any ephemeris data change (version bump) is a **versioned decision** that
  changes output and therefore the metadata — never silent (JSP-001
  versioning rule).

## 20. Provider metadata

```python
class ProviderMetadata:               # provider-stable
    provider_id: str                  # "swisseph.pysweph"
    library_name: str                 # "pysweph" (binding name: swisseph)
    library_version: str              # e.g. "2.10.3.6"
    ephemeris_version: str            # e.g. "18"
```

- Per-call mode/files live in `ProviderRun` (`ephemeris_mode`,
  `ephemeris_files`), NOT in `ProviderMetadata` (they vary by call when
  fallback engages).
- Filled at provider construction (library version queried from the binding);
  immutable thereafter.

## 21. Calculation flags

Central table in `swisseph/constants.py` (named constants; numeric values are
defined by the binding and MUST NOT be hardcoded elsewhere):

| Config state | Flag combination |
|---|---|
| Standard, apparent | `SEFLG_SWIEPH | SEFLG_SPEED` |
| Standard, true | `SEFLG_SWIEPH | SEFLG_SPEED | SEFLG_TRUEPOS` |
| Fallback, apparent | `SEFLG_MOSEPH | SEFLG_SPEED` |
| Fallback, true | `SEFLG_MOSEPH | SEFLG_SPEED | SEFLG_TRUEPOS` |
| Sidereal | derived, no `SEFLG_SIDEREAL` (§12) |

- `retflag` from each `calc_ut` is checked: if the requested ephemeris flag
  bit is absent, the mode did not engage → treat as data failure (§23),
  never accept silently.
- Flag set is identical across all bodies in one call batch (determinism).

## 22. Determinism requirements

Identical `(EphemerisRequest inputs, CalculationConfig, ephemeris data
version+files, library version, tzdata version)` ⇒ **bit-identical** floats.

Enforced by:

1. Pinned runtime deps: `pysweph==2.10.3.6`, pinned `tzdata`, pinned `.se1`
   files with checksums.
2. Per-call `swe.set_*` from immutable config; adapter serialized by a lock —
   no ambient/global state leakage between calls.
3. Frozen dataclasses everywhere; config echoed in every result.
4. Pure functions only in `time.py`, `coordinates.py`, `models.py`,
   `serialize.py`; the service never calls `time.time()`, `random`, or
   threads.
5. No network at runtime (§29).
6. Regression tests: same-process double compute (bit equality) and
   cross-process determinism (TEST-PLAN §7).

## 23. Error model

```python
class EphemerisError(Exception): ...            # base
class InvalidTimestampError(EphemerisError): ...
class InvalidCoordinatesError(EphemerisError): ...
class UnsupportedProviderError(EphemerisError): ...
class EphemerisDataError(EphemerisError): ...
```

- Raised-when table is authoritative in the architecture doc §9; additions
  here:
  - `retflag` missing the requested ephemeris bit → `EphemerisDataError`
    (data/mode integrity), with fallback per §4.7.
  - `EphemerisDataError` also when files absent/unreadable/checksum-fail and
    `allow_fallback=false`.
  - Every error message includes the offending value(s).
- The service never swallows provider errors into a `BodyPosition`; errors
  propagate to the caller with their original type.

## 24. Validation strategy

- **Two independent tracks**:
  1. **Internal consistency** (integration tests, QA): determinism, mode
     fallback behavior, node modes, flag integrity, JD cross-check, SWIEPH vs
     MOSEPH agreement bounds.
  2. **External reference** (VALIDATOR): positions vs NASA JPL Horizons (and/or
     published almanac values) per TEST-PLAN §12, with the documented
     tolerance policy owned by the Architect.
- The external dataset is committed as `datasets/validation/astronomy/
  reference_positions.csv` (schema in TEST-PLAN §13); no network at runtime or
  during validation runs.

## 25. Test architecture

Full matrix, fixtures, and acceptance criteria: [JRE-002-TEST-PLAN](JRE-002-TEST-PLAN.md).
In brief:

- `tests/unit/astronomy/` — pure logic, no `swe` needed (models, errors, time,
  coordinates, serialization, registry with fake provider, `__all__`).
- `tests/integration/astronomy/` — real Swiss Ephemeris (valid input,
  timezone, boundaries, retrograde, fallback, determinism, metadata).
- `tests/validation/astronomy/` — external reference harness (VALIDATOR).
- CODING ships the happy-path tests; QA completes the matrix.

## 26. External-reference validation strategy

- ≥ 6 instants spanning: one retrograde window, one node position, one
  sidereal-known date, plus normal dates; independent source = NASA JPL
  Horizons (geocentric, apparent, ecliptic-of-date longitude/latitude).
- Tolerance budget accounts for frame/model differences (ICRS vs
  ecliptic-of-date, apparent conventions); initial proposed budget
  ≤ 0.01° longitude for planets — reviewed against the first batch by the
  Architect and then fixed.
- Full detail in TEST-PLAN §12–§14.

## 27. Future-provider compatibility

- A new provider = new subpackage + adapter implementing `EphemerisProvider`
  + `Registry.register(...)`. `models.py`, `service.py`, `serialize.py`,
  `config.py` are untouched (verify with the fake-provider test, TEST-PLAN
  §10).
- The provider contract (§3) is the only interface a new provider must satisfy.
- Provider selection is explicit via `EphemerisRequest.provider_id` /
  `AstronomicalService(provider_id=...)` — no magic auto-detection.

## 28. Performance constraints (2 cores / 4 GB RAM)

- Budget: a 9-body request must complete **p95 < 50 ms** including first-call
  initialization (ephemeris path + checksum verification, done once per
  provider instance). Steady-state single calls: ~1–10 ms. No multiprocessing.
- Memory: the `.se1` files are memory-mapped/streamed by the library; RSS
  increase must stay < 50 MB for the astronomy package.
- Concurrency: the adapter serializes on a module lock; the service is
  otherwise lock-free. No threads spawned.
- A performance smoke test (TEST-PLAN §15) asserts the budget on the target
  profile; it is informational, not a hard CI gate.

## 29. Offline operation requirements

- **Zero network at runtime.** All data is local: `.se1` files (committed),
  `tzdata` (installed package), config (committed).
- The `.se1` files are fetched **once at build/setup time** (documented in
  `datasets/ephemeris/README.md`); runtime never downloads anything.
- Startup does not ping any service; no telemetry.
- Offline operation is verified structurally: a static test asserts no
  network imports (`urllib`, `requests`, `socket`) anywhere in
  `src/astronomy/` (TEST-PLAN §8).

## 30. Caching strategy

- **Decision: no caching in this phase.** A single 9-body request is
  sub-millisecond-to-millisecond (§28); caching adds state, invalidation
  surface, and determinism risk for negligible gain.
- Revisit condition (documented, future): if a consumer (e.g. the Gochar
  engine) requests many distinct instants, add a process-scoped memo keyed by
  exact `(jd_ut, bodies, config)` tuple hash, as a **versioned** extension —
  never an invisible optimization.

## 31. API boundary between astronomy and astrology

- `astronomy` exports ONLY the public surface in §1. Nothing astrological:
  no houses, rashis, nakshatras, yogas, dashas, gochar, benefic/malefic,
  predictions — not as fields, methods, enums, or helper functions.
- Derived Jyotish quantities (rashi = `floor(lon_sidereal/30)+1`, nakshatra =
  `floor(lon_sidereal/(360/27))+1`, varga division, dasha from Moon position,
  transit comparison) belong to consumers and are computed from core output —
  never inside `astronomy`.
- Enforcement:
  - Explicit `__all__` + public-surface test.
  - Static "forbidden import" test (no `astrology|knowledge|transits|dasha|
    calculations|inference` imports; no `socket|requests|urllib` imports).
  - Code review gate: any PR adding interpretation vocabulary to `astronomy`
    is rejected (architecture §3).

## 32. Serialization format

- JSON, UTF-8, snake_case keys, enum → string value, tuple → array, `None` →
  `null`, floats via Python's round-trip repr.
- Exact JSON Schema and example payloads: [JRE-002-DATA-CONTRACT §8–§9](JRE-002-DATA-CONTRACT.md).
- Provided by `serialize.py`:
  - `result_to_json(result: EphemerisResult) -> str`
  - `request_from_dict(d: dict) -> EphemerisRequest` (validates on
    construction)
  - `config_from_dict(d: dict) -> CalculationConfig`
- Serialization round-trips exactly: `json.loads(result_to_json(r))` preserves
  every double (§18). Round-trip tested.

## 33. Consumer contract (the two future engines)

**Both consumers MUST use the same core and never reimplement planetary
calculations** (JSP-001 Mode A/Mode B; JRE-002 requirement):

- **A. Generic Gochar Engine** (future, `src/transits/`): requests current
  positions via `AstronomicalService.compute` (any instant, default config);
  derives rashi/nakshatra transit from `longitude_sidereal`; performs generic
  12-Rashi / 27-Nakshatra analysis. Uses only the §1 public API.
- **B. Individual Kundali Engine** (future, `src/astrology/`): requests natal
  positions via the same `AstronomicalService.compute`; derives lagna/rashi/
  nakshatra/varga/dasha/gochar from core output. Uses only the §1 public API.
- Both engines import `astronomy`; neither imports `swisseph`. The
  fake-provider test (§25) proves consumers can compute through the core
  without the real engine.
- **Noted dependency for B (out of JRE-002 scope)**: lagna requires the
  ascendant/house cusps, which need `swe.houses` — an astronomical *houses
  extension* that is a separate future task (recorded in §36). Kundali's other
  derivations need only JRE-002 positions.

## 34. Dependency requirements (for the future CODING agent)

Runtime (pin at CODING time, record in pyproject):

- `pysweph==2.10.3.6` (Swiss Ephemeris bindings; import name `swisseph`).
- `tzdata` — pinned to the latest stable release at CODING time (IANA data;
  required for deterministic `zoneinfo`).

Dev (documented, not installed by this stage):

- `pytest` (≥ 8), `ruff`, `mypy`; `coverage` optional.

Data/build artifacts:

- `.se1` files `se_18.se1`, `sepl_18.se1`, `semo_18.se1` committed under
  `datasets/ephemeris/` with `README.md` (provenance, version, SHA-256,
  Swiss Ephemeris licensing).
- `config/astronomy.toml` with defaults
  (`ayanamsa = "LAHIRI"`, `ephemeris_mode = "SWIEPH"`,
  `position_type = "APPARENT"`, `node_type = "MEAN"`,
  `allow_fallback = true`, `ephemeris_path = "datasets/ephemeris"`).

## 35. Handoff instructions for CODING

1. Create `pyproject.toml` (src-layout, package `astronomy`, pins per §34) and
   a dev environment. **No other package.**
2. Implement in this order: `models.py` (DATA-CONTRACT §1–§6, exactly) →
   `errors.py` → `coordinates.py` → `time.py` (pure JD + fold rules) →
   `provider.py` (Protocol + Registry) → `config.py` (TOML loader) →
   `serialize.py` → `service.py` (validation + assembly) → `swisseph/*`
   (constants → ephemeris → provider).
3. Commit the ephemeris files + README (build-time fetch only, §29).
4. Ship happy-path tests (TEST-PLAN §16 list); QA completes the matrix.
5. Gate before handoff to QA: `pytest tests/unit tests/integration`,
   `ruff check src tests`, `mypy src/astronomy`; all green. Static tests
   (public surface, forbidden imports) green.
6. Do NOT implement: houses, rashis, nakshatras, yogas, dashas, gochar,
   benefic/malefic, predictions, topocentric, caching, any network call.
7. Do NOT bump versions or change data contracts without a versioned
   decision (JSP-001).

## 36. Unresolved questions (for Architect/Validator)

1. **Stationary ε calibration** — method is fixed (noise-floor measurement,
   TEST-PLAN §12); the resulting value (expected ≥ 1e-6 deg/day, above the
   Moon's speed noise) is a versioned decision.
2. **`tzdata` exact pin** — chosen at CODING time; must be recorded in
   pyproject and metadata.
3. **Validation tolerance** — proposed ≤ 0.01° longitude vs. Horizons;
   Architect reviews against the first reference batch before it is fixed.
4. **Custom ayanamsa** — `ayanamsa_override` interface is specified; its
   acceptance criteria (t0/ayanamsa_t0 semantics) need Validator confirmation
   against a known reference.
5. **Kundali ascendant** — lagna needs house cusps/ascendant
   (`swe.houses`), an astronomical extension outside JRE-002; a separate
   future task must be created before the Kundali engine can start.
6. **Threading** — the adapter lock is specified; confirm the 2-core target
   never needs concurrent astronomy calls (gochar polling cadence), else
   revisit.
7. **Pre-1582 (Julian calendar) dates** — deliberately out of scope; the
   pure JD formula is Gregorian-only. Revisit only if historical charts
   require it (then a versioned Julian branch + swe cross-check is needed).

## 37. Change history

| Version | Date | Change |
|---|---|---|
| 0.2.0 | 2026-08-11 | Architecture (design level) |
| 0.3.0 | 2026-08-11 | Specialist implementation spec (this document) |
