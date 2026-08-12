# ADR-001 — Ephemeris Provider Library and Computation Modes

- Status: ACCEPTED
- Date: 2026-08-11
- Related task: [JRE-002 Astronomical Core](../architecture/JRE-002-ASTRONOMICAL-CORE.md)
- Decision maker: Architect

## Context

JRE-002 requires a deterministic astronomical calculation layer for the Sun, Moon,
the five classical planets, Rahu and Ketu. The layer must:

- produce identical output for identical (timestamp, coordinates, timezone,
  ephemeris version, configuration) input;
- expose a provider abstraction so future ephemeris providers can be added
  without rewriting the core;
- run on low-resource Linux hosts (2 CPU cores, ~4 GB RAM, Python 3.12);
- have **no network dependency at runtime**.

## Decision

### 1. Library: `pysweph` (Swiss Ephemeris bindings)

Adopt [`pysweph`](https://pypi.org/project/pysweph/) as the initial provider's
ephemeris engine — the actively maintained community continuation of the Swiss
Ephemeris Python bindings.

Rationale:

- Swiss Ephemeris is the de facto standard, validated ephemeris for Jyotisha:
  precision based on NASA DE431/DE441, coverage 13201 BC – AD 17191, native
  support for sidereal mode and ayanamsa.
- `pysweph` (latest: 2.10.3.6) supports Python 3.8–3.13 including our target
  3.12, ships prebuilt Linux wheels (manylinux), and is under active
  maintenance with live documentation.
- The original `pyswisseph` package is unmaintained: last release 2.10.3.2
  (2023-06), documentation site offline since mid-2025, no modern packaging
  guarantees.
- `pysweph` keeps the identical import surface (`import swisseph as swe`),
  which confines the compatibility risk to a single adapter module.

Rejected alternatives:

- `pyswisseph` — unmaintained; no reliable packaging for current Python.
- `skyfield` + JPL `.bsp` — astronomy-grade, but a different computation model;
  sidereal/ayanamsa support would have to be hand-rolled, increasing validation
  surface.
- `flatlib` / `pymeeus` — lower precision or non-validated for the Jyotisha
  use-case; do not meet the "validated ephemeris" requirement.

### 2. Computation modes

Standard mode — **SWIEPH (high precision)**

- Compute with the Swiss Ephemeris data files (`.se1`) bundled locally,
  version-pinned, and verified by checksum.
- Ephemeris files are resolved from a deterministic, local path under
  `datasets/ephemeris/`; they are fetched once at build/setup time, never at
  runtime.

Fallback mode — **MOSEPH (Moshier approximation)**

- Used only when the high-precision data files are absent, unreadable, or fail
  their integrity check.
- Same input contract, same output contract, same determinism guarantee;
  the `ProviderRun.ephemeris_mode` and `ProviderMetadata` in the result record
  which mode produced the output, so results are always reproducible and
  auditable. Fallback is never silent.

This gives HIGH PRECISION as the standard, STANDARD-as-default semantics, and a
deterministic FALLBACK — with no network dependency at runtime in either mode.

### 3. Default calculation settings (overridable per request)

- Positions: **apparent geocentric ecliptic** coordinates (library default:
  light-time, aberration and nutation corrected).
- Speeds: always computed (`SEFLG_SPEED`) — required for speed and
  retrograde/direct state.
- Ayanamsa: **Lahiri (Chitrapaksha)** as default, configurable to any
  `swe.SIDM_*` mode (e.g. Raman, Fagan-Bradley). Sidereal longitudes are
  derived from tropical longitudes via `swe.set_sid_mode` + `SEFLG_SIDEREAL`;
  the ayanamsa value used is included in the output.
- Lunar node: **mean node** (`swe.MEAN_NODE`) as the standard for Rahu/Ketu,
  configurable to true node (`swe.TRUE_NODE`).
- Geocentric positions (topocentric becomes a later, explicitly-versioned
  option).

## Consequences

- The provider abstraction must be implemented *before* the Swiss Ephemeris
  adapter so that future providers (e.g. Moshier-only, JPL, or custom) slot in
  without core changes.
- Determinism is a property of the whole chain: pinned ephemeris file versions,
  fixed flags, explicit config objects, and no dependence on process-global
  mutable state in the service layer.
- `datasets/ephemeris/` must document file names, versions, and SHA-256
  checksums.
- Licensing: the Swiss Ephemeris `.se1` data files are free for private and
  astrological use; commercial redistribution requires a license from
  Astrodienst. The `pysweph` bindings are AGPL-3.0. Document this in
  `datasets/ephemeris/README.md` and the distribution metadata before any
  public release.
- Breaking changes in `pysweph` vs. `pyswisseph` (e.g. house-cusp tuple
  layout) are confined to the adapter module; the astronomical core does not
  use house cusps.

## References

- [JRE-002 task specification](../architecture/JRE-002-ASTRONOMICAL-CORE.md)
- [JSP-001 Core Specification](../../specifications/core/JSP-001.md)
- Swiss Ephemeris: https://www.astro.com/swisseph/swephinfo_e.htm
