# Swiss Ephemeris data files (bundled)

These files provide the deterministic, offline, high-precision ephemeris data
for the JRE-002 astronomical core (SWIEPH mode).

## Files

| File | Purpose | Size (bytes) | SHA-256 |
|---|---|---|---|
| `sepl_18.se1` | Planets (Sun, Mercury, Venus, Mars, Jupiter, Saturn) | 484,061 | `ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66` |
| `semo_18.se1` | Moon (and lunar nodes) | 1,304,771 | `1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7` |

## Provenance

- Source: official Swiss Ephemeris public GitHub repository
  `aloistr/swisseph`, folder `ephe`
  (per https://www.astro.com/ftp/swisseph/ephe/ "Download location of files").
- Downloaded 2026-08-11 (CODING stage, build-time step — never at runtime).
- File headers: `SWISSEPH 3`, "Created for Astrodienst in Switzerland
  2026/05/26, based on JPL Ephemeris DE441."
- Ephemeris version (data set): `18`.

## Why `se_18.se1` is not bundled

The standard distribution also ships `se_18.se1` (the "main" file) and
`seas_18.se1` (asteroids). Verified empirically during CODING: none of the nine
bodies (Sun, Moon, five planets, Rahu, Ketu from mean/true lunar node) require
`se_18.se1` or `seas_18.se1` — `swe.calc_ut(..., FLG_SWIEPH)` succeeds for all
nine with only `sepl_18.se1` + `semo_18.se1`, with the SWIEPH bit set in
`retflag` (mode integrity confirmed). Bundling them is deferred until a future
task needs them (e.g., house cusps or asteroids). This is a recorded deviation
from the Specialist spec v0.3.0 §5, which listed `se_18.se1`.

## Verification

Checksums above are asserted by `astronomy.swisseph.ephemeris` on first use of
a data path (unless disabled for performance). Recompute with:

```
sha256sum datasets/ephemeris/*.se1
```

## Licensing

The Swiss Ephemeris data files are copyright Astrodienst and are free for
private and astrological use. **Commercial redistribution requires a license
from Astrodienst** (see https://www.astro.com/swisseph/swephinfo_e.htm).
The `pysweph` Python bindings are AGPL-3.0. Review licensing before any public
or commercial distribution of this repository.
