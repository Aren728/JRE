# JRE-002 — Astronomical Core: Architecture and Refined Specification

- Status: ARCHITECTED
- Version: 0.2.0 (refined from JRE-002 request v0.1.0)
- Date: 2026-08-11
- Related decisions: [ADR-001 Ephemeris Provider](../decisions/ADR-001-EPHEMERIS-PROVIDER.md)
- Base specification: [JSP-001 Core Specification](../../specifications/core/JSP-001.md)

## 1. Purpose

This document refines the JRE-002 request ("Astronomical Core") into an
implementable design. It defines the module layout, public data contracts,
provider abstraction, determinism contract, error taxonomy, and the testing and
validation strategy. It is the authoritative handoff from the **Architect** to
the **Astronomy Specialist** and downstream stages (CODING, QA, VALIDATOR).

## 2. Scope

Compute, for **Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu**,
given a validated input set:

| Output field | Definition |
|---|---|
| Ecliptic longitude | Tropical and (when ayanamsa configured) sidereal, degrees `[0, 360)` |
| Ecliptic latitude | Degrees `[-90, 90]` (Moon, planets; ~0 for Sun) |
| Distance | Astronomical units (heliocentric correction not required) |
| Speed | Longitude speed (deg/day) — base for retrograde state; latitude & distance speed where available |
| Apparent/true state | Which position type was computed (default apparent) |
| Retrograde/direct | Derived from sign of longitude speed; explicit enum |
| Timestamp used | The exact UTC instant the calculation ran at (plus original local input) |
| Ephemeris provider | Stable provider identifier + version metadata |
| Calculation configuration | Immutable snapshot of every setting that affects the output |

## 3. Non-goals (mandatory separation)

The astronomical layer MUST NOT perform any astrological interpretation. It
must not determine or expose:

- Benefic/malefic status, house meaning, yoga, dasha result
- Wealth, marriage, career, prediction, gochar interpretation

These belong to later modules (Classification, Knowledge, Calculation, Rules,
Dynamic State, Inference). Reviewers must reject any pull request that mixes
interpretation into `src/astronomy/`.

## 4. Design principles

1. **Determinism**: identical input → bit-identical output. No randomness, no
   wall-clock dependence, no process-global mutable state in the service layer.
2. **Provider independence**: the core depends on the `EphemerisProvider`
   abstraction only; concrete engines are adapters.
3. **Explicit configuration**: every setting that influences output travels in
   an immutable `CalculationConfig` and is echoed back in the result.
4. **Validation at the boundary**: inputs are validated once, at the service
   boundary, with typed errors.
5. **Testability**: no network, no clock, no hidden state — every function
   accepts its inputs explicitly.

## 5. Module layout

Following the existing scaffold (`src/`, `tests/{unit,integration,validation}/`,
`config/`, `datasets/`):

```
src/
  astronomy/
    __init__.py          # Public API re-exports (AstronomicalService, models)
    models.py            # BodyId, BodyPosition, EphemerisRequest, CalculationConfig,
                         # EphemerisResult, ProviderMetadata, ProviderRun, RetrogradeState,
                         # Ayanamsa, EphemerisMode, PositionType, NodeType
    errors.py            # EphemerisError, InvalidTimestampError, InvalidCoordinatesError,
                         # UnsupportedProviderError, EphemerisDataError
    time.py              # Timezone-aware input normalization -> UTC Julian Day
    provider.py          # EphemerisProvider (Protocol) + ProviderRegistry
    service.py           # AstronomicalService — deterministic facade, input validation
    config.py            # Loads config/astronomy.toml into CalculationConfig defaults
    swisseph/
      __init__.py        # Public adapter surface (get_provider())
      provider.py        # SwissEphemerisProvider implements EphemerisProvider
      constants.py       # swe flags/body constants; MODE_* configuration mapping
      ephemeris.py       # Local .se1 file resolution, version/checksum metadata

config/
  astronomy.toml         # Defaults: ayanamsa=Lahiri, mode=SWIEPH, node=MEAN, ...

datasets/
  ephemeris/
    README.md            # File list, versions, SHA-256 checksums, licensing
    se_18.se1, sepl_18.se1, semo_18.se1   (pinned, committed)
  validation/
    astronomy/
      reference_positions.csv   # Independent reference positions for VALIDATOR

tests/
  unit/astronomy/        # Per the matrix in §11
  integration/astronomy/
  validation/astronomy/
```

Conventions:

- Package root is `astronomy` (matches the existing `src/` skeleton; a
  namespace root such as `jre.` may be introduced in a later, separately
  versioned refactor — no silent change).
- No `astronomy` module may import from `astrology`, `knowledge`, or any other
  layer.
- The asteroid data file `seas_18.se1` is intentionally NOT bundled: none of
  the nine bodies require it (`se_18.se1` core, `sepl_18.se1` planets,
  `semo_18.se1` Moon). Add it only if asteroid support is introduced later.

## 6. Data contracts

> **Superseded at implementation level by v0.3.0.** The models below remain
> the design-level contract, but the authoritative field-level contract for
> CODING is [JRE-002-DATA-CONTRACT.md](JRE-002-DATA-CONTRACT.md) and
> [JRE-002-SPECIALIST-SPEC.md](JRE-002-SPECIALIST-SPEC.md), which add
> `EphemerisRequest.provider_id` and split per-call `ProviderRun` from
> provider-stable `ProviderMetadata`.

All models are `@dataclass(frozen=True)` in `models.py`. Serialization to JSON
must be exact (repr-based float formatting via `float.__repr__` round-trip).

```python
class BodyId(str, Enum):
    SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN, RAHU, KETU

class RetrogradeState(str, Enum):
    DIRECT, RETROGRADE, STATIONARY

class Ayanamsa(str, Enum):
    LAHIRI, RAMAN, FAGAN_BRADLEY          # extensible; maps to swe.SIDM_*

class EphemerisMode(str, Enum):
    SWIEPH, MOSEPH

class PositionType(str, Enum):
    APPARENT, TRUE

class NodeType(str, Enum):
    MEAN, TRUE
```

```python
@dataclass(frozen=True)
class CalculationConfig:
    ayanamsa: Ayanamsa | None = Ayanamsa.LAHIRI
    ephemeris_mode: EphemerisMode = EphemerisMode.SWIEPH
    position_type: PositionType = PositionType.APPARENT
    node_type: NodeType = NodeType.MEAN
    ephemeris_path: str | None = None     # resolved to datasets/ephemeris
    allow_fallback: bool = True           # SWIEPH -> MOSEPH fallback allowed
    # any future setting that can change output MUST be added here (versioned)
```

```python
@dataclass(frozen=True)
class EphemerisRequest:
    date: date              # local civil date
    time: time              # local civil time (seconds precision)
    timezone: str           # IANA zone name, e.g. "Asia/Kolkata"
    latitude: float         # degrees, [-90, 90]
    longitude: float        # degrees, [-180, 180]
    bodies: tuple[BodyId, ...] | None = None   # None = all nine
    config: CalculationConfig = CalculationConfig()
```

```python
@dataclass(frozen=True)
class BodyPosition:
    body: BodyId
    longitude_tropical: float          # deg [0,360)
    longitude_sidereal: float | None   # None when ayanamsa not configured
    latitude: float                    # deg [-90,90]
    distance_au: float
    speed_longitude: float             # deg/day
    speed_latitude: float              # deg/day
    speed_distance: float              # AU/day
    retrograde: RetrogradeState        # from speed_longitude sign (+ eps tolerance)
    position_type: PositionType
    ayanamsa_value: float | None       # deg, ayanamsa applied (or None)
```

```python
@dataclass(frozen=True)
class ProviderMetadata:                # provider-stable (per provider, not per call)
    provider_id: str                   # e.g. "swisseph.pysweph"
    library_name: str                  # "pysweph" (swisseph binding)
    library_version: str
    ephemeris_version: str             # pinned .se1 data version, e.g. "18"

class ProviderRun:                     # per-call outcome of a provider
    positions: tuple[BodyPosition, ...]
    ephemeris_mode: EphemerisMode      # actual mode used (SWIEPH or fallback MOSEPH)
    ephemeris_files: tuple[str, ...]   # files actually used (or () for MOSEPH)
```

```python
@dataclass(frozen=True)
class EphemerisResult:
    request_snapshot: EphemerisRequest   # echo of the exact input
    timestamp_utc_iso: str               # the UT instant computed, ISO 8601
    timestamp_local_iso: str             # original local civil input, ISO 8601
    julian_day_ut: float                 # deterministic JD used
    positions: tuple[BodyPosition, ...]  # stable order per BodyId
    provider: ProviderMetadata
    config: CalculationConfig            # the config actually applied
```

## 7. Time and coordinates

- **Input**: local civil date + time + IANA timezone (`zoneinfo` stdlib).
- **Normalization** (`time.py`): local time → aware datetime → UTC via
  `datetime.astimezone(timezone.utc)`. The resulting exact UTC instant is what
  is computed; both UTC and local ISO strings are stored in the result.
- **Ambiguous local times** (DST fall-back): resolved with `fold=0` (first
  occurrence), fixed for determinism. **Nonexistent local times** (DST
  spring-forward gap): raise `InvalidTimestampError`.
- **Julian Day**: UTC datetime → Julian Day using Swiss Ephemeris conventions
  (`swe.utc_to_jd` with `swe.GREG_CAL`, or equivalent deterministic path).
  Leap seconds are handled by the library; the chosen path must be documented
  and versioned in the adapter.
- **Validation**: `latitude ∈ [-90, 90]`, `longitude ∈ [-180, 180]`, timezone
  must resolve in IANA database, datetime must be within the ephemeris coverage
  range (13201 BC – AD 17191 for the bundled files). Violations raise typed
  errors (§9) **before** any provider call.
- **Boundary policy**: positions at exactly `0°`/`360°` longitude are
  normalized to `[0, 360)`; `-0.0` is normalized to `0.0`.

## 8. Provider abstraction

```python
class EphemerisProvider(Protocol):
    provider_id: str
    metadata: ProviderMetadata           # provider-stable metadata
    def compute(self, jd_ut: float, bodies: tuple[BodyId, ...],
                config: CalculationConfig) -> ProviderRun: ...
```

- **Ownership split (authoritative).** The SERVICE owns all validation, time
  normalization, Julian Day computation, and assembly of `EphemerisResult`
  (request snapshot, ISO timestamps, config echo, provider metadata).
  Providers are pure position engines: they receive an already-validated JD,
  the requested bodies, and the config, and return `ProviderRun`. Providers
  never see raw requests, never validate, and never touch clocks, timezones,
  or calendars.
- `ProviderRegistry` maps `provider_id` → provider instance and exposes
  `default()` (the Swiss Ephemeris adapter). The service calls only the
  Protocol. Adding a provider means writing one adapter + one registration,
  with no changes to `service.py` or `models.py`.
- `SwissEphemerisProvider` behavior:
  - Sets ephemeris path to the pinned local files (`swe.set_ephe_path`).
  - Computes with `swe.calc_ut(jd, swe.<BODY>, SEFLG_SWIEPH | SEFLG_SPEED)`
    in standard mode; `SEFLG_MOSEPH | SEFLG_SPEED` in fallback mode.
  - Applies `swe.set_sid_mode(...)` and `SEFLG_SIDEREAL` for sidereal output;
    `SEFLG_TRUEPOS` only for `position_type=PositionType.TRUE`.
  - Rahu/Ketu from `swe.MEAN_NODE` / `swe.TRUE_NODE` per config.
  - Retrograde from sign of `speed_longitude`; `|speed| < ε` (e.g.
    `< 1e-9` deg/day) → `STATIONARY`.
  - **Fallback rule (not silent).** If SWIEPH data files are absent,
    unreadable, or fail their checksum, and `config.allow_fallback` is true,
    the provider retries with MOSEPH and returns `ProviderRun` with
    `ephemeris_mode=MOSEPH` and `ephemeris_files=()`. If `allow_fallback` is
    false, it raises `EphemerisDataError`.
  - All `swe.*` global state is set per-call from the immutable config (never
    assumed), so calls cannot interfere.

## 9. Error taxonomy

| Error | Raised when |
|---|---|
| `InvalidTimestampError` | date/time/timezone malformed, unrepresentable local time, or outside ephemeris coverage |
| `InvalidCoordinatesError` | latitude/longitude out of range or non-finite |
| `UnsupportedProviderError` | requested provider_id not registered |
| `EphemerisDataError` | required `.se1` files absent, unreadable, or failing checksum, AND `allow_fallback=false`; with fallback enabled the provider retries in MOSEPH and records the mode (never silent) |
| `EphemerisError` | any other provider failure (base class for the above) |

All errors expose the offending input value in `__str__`. The service must
never swallow provider errors into a position.

## 10. Determinism contract

Given identical `(EphemerisRequest date/time, timezone, coordinates,
CalculationConfig, ephemeris data version, provider version)`, the service
MUST produce bit-identical floats. Enforced by:

1. Pinned, checksummed local `.se1` files (no runtime network).
2. Fixed flag sets per mode; no ambient library state (per-call `set_*`).
3. Immutable frozen config echoed in every result.
4. Pure functions only — no `time.time()`, no `random`, no parallelism inside
   the service.
5. A regression test that computes the same request twice and asserts exact
   equality (§11.8).

## 11. Testing strategy (maps to JRE-002 requirements)

Unit (`tests/unit/astronomy/`), integration (`tests/integration/astronomy/`),
validation (`tests/validation/astronomy/`). QA owns authoring; CODING ships
stubs with the core happy-path tests.

| # | Requirement | Where | Assertion |
|---|---|---|---|
| 1 | Valid birth timestamp | `test_valid_input.py` (unit + integration) | Nine bodies, all fields finite, ranges correct |
| 2 | Invalid timestamp | `test_invalid_timestamp.py` | `InvalidTimestampError` for garbage/out-of-coverage dates |
| 3 | Invalid coordinates | `test_invalid_coordinates.py` | `InvalidCoordinatesError` for lat/lon out of range |
| 4 | Timezone handling | `test_timezone.py` | Same instant, different zones → identical positions; same local time, different zones → different positions |
| 5 | Boundary conditions | `test_boundaries.py` | Equator/poles, ±180° longitude, midnight, leap day, longitude normalization `[0,360)` |
| 6 | Retrograde planet | `test_retrograde.py` | Known retrograde window (e.g. historical Mars/Mercury) → `RETROGRADE`; speed sign consistent; a known station date → `STATIONARY` (ε policy validated against a real reference) |
| 7 | Provider metadata | `test_provider_metadata.py` | `ProviderMetadata` + config snapshot present, stable `provider_id`, mode recorded |
| 8 | Repeated calculation | `test_determinism.py` | Two identical requests → bit-identical floats |

Additional:

- Fallback precision: SWIEPH vs MOSEPH within tolerance (e.g. ≤ 0.1 arcsec
  for planets) — documents the fallback trade-off, does not assert equality.
- Fallback engagement: with a fenced (unavailable) ephemeris path and
  `allow_fallback=true`, the provider returns `ephemeris_mode=MOSEPH`;
  with `allow_fallback=false`, `EphemerisDataError` is raised.
- Node modes: mean vs true node differ; both deterministic.
- Provider registry: registering a fake provider and computing through it
  (proves the core is provider-independent).

## 12. Runtime and packaging requirements

- Python 3.12; package metadata added at CODING stage:
  `pyproject.toml` (setuptools or hatchling), runtime dependency pinned
  `pysweph==2.10.3.6`, dev extras `pytest`, `ruff`, `mypy`.
- Target host: 2 cores / 4 GB RAM. Single-shot planet computation is
  negligible; no caching required in this phase (may be added later, versioned).
- `config/astronomy.toml` supplies defaults; every request may override.
- `datasets/ephemeris/README.md` documents file provenance, versions,
  checksums, and Swiss Ephemeris licensing.

## 13. Validation strategy (VALIDATOR stage)

- Build `datasets/validation/astronomy/reference_positions.csv` from an
  **independent** source: NASA JPL Horizons queries (and/or published
  astronomical almanac values) for ≥ 6 dated instants spanning at least one
  retrograde window and one node position.
- Validation asserts positions within a documented tolerance budget. The
  budget accounts for frame/model differences between references (ICRS vs
  ecliptic-of-date, apparent vs true, JPL Horizons output conventions); the
  initial proposed budget (≤ 0.01° longitude for planets vs. Horizons) is
  reviewed against the first reference batch and fixed in the CSV by the
  Architect before it is treated as authoritative.
- The validation harness is separate from unit/integration tests and lives in
  `tests/validation/astronomy/`.

## 14. Downstream handoff checklist

Deliverable status for the SPECIALIST (Astronomy) and subsequent stages:

- [ ] Provider abstraction (`provider.py`, `registry`) implemented
- [ ] `SwissEphemerisProvider` with SWIEPH standard / MOSEPH fallback
- [ ] Data contracts (`models.py`) exactly as §6
- [ ] Time normalization + boundary validation (`time.py`, service boundary)
- [ ] Error taxonomy (§9)
- [ ] `config/astronomy.toml` + loader
- [ ] Pinned ephemeris files under `datasets/ephemeris/` + README + checksums
- [ ] Unit tests for requirements 1–8 (with QA review)
- [ ] `pyproject.toml` with pinned `pysweph`
- [ ] Documentation: module docstrings, `src/astronomy/README.md`
- [ ] Validation dataset + harness scaffold for VALIDATOR
- [ ] No astrological interpretation anywhere in the layer (§3 gate)

## 15. Change history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | — | Original JRE-002 request |
| 0.2.0 | 2026-08-11 | Architecture + refined specification (this document) |
