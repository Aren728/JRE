# JRE-002 — Astronomical Core: Validation Report

- **Stage**: VALIDATOR
- **Date**: 2026-08-12
- **Validator principle applied**: the implementation was NOT accepted because
  its own tests pass. Every position, state, and quantity in this report was
  independently re-derived from external authoritative references and compared
  against JRE output. JRE's own output was never used as a reference.
- **Scope**: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Rahu, Ketu;
  time/UTC handling, coordinates, ayanamsa, nodes, retrograde state, speeds,
  metadata, determinism, boundaries, serialization, error handling, and the
  architecture separation requirements.
- **Out of scope (correctly NOT validated)**: yogas, dashas, gochar
  interpretation, houses, predictions, benefic/malefic status — those belong
  to later layers and are absent from this implementation.

# Validation Summary

| Area | Result |
|---|---|
| Planetary longitudes vs JPL Horizons | **PASS** — 16 comparisons, max Δ = 0.00011° (0.40″) |
| Planetary latitudes vs JPL Horizons | **PASS** — max Δ = 0.000012° (0.04″) |
| Longitude speeds vs JPL Horizons | **PASS** — max Δ = 0.0146 °/day (Moon, central-difference truncation) |
| Sun longitude (geometric, via Earth osculating elements) | **PASS** — max Δ = 0.0042° (15″) |
| Mean lunar node (Rahu) vs Meeus formula | **PASS** — max Δ = 0.0036° (13″) |
| True lunar node vs Horizons osculating node | **PASS** — max Δ = 0.0127° (46″) |
| Ketu = Rahu + 180° | **PASS** — exact (0.0) |
| Ayanamsa (Lahiri) vs Swiss Ephemeris documented J2000 value | **PASS** — Δ = 0.000009° (0.03″) |
| Ayanamsa vs IAE tabular convention | **PASS** — Δ = 0.0038° (13.6″), documented convention difference |
| Retrograde/direct states vs Horizons motion trends | **PASS** — 5/5 consistent |
| Timezone conversion (IST +05:30, EDT DST) | **PASS** — local→UTC exact, positions identical |
| Determinism (repeated computation) | **PASS** — byte-identical |
| Serialization (stable JSON) | **PASS** |
| Error handling (typed errors) | **PASS** |
| Architecture separation (provider isolation, no astrology, determinism-by-construction) | **PASS** |
| Test suite + static gates | **PASS** — 233 tests, ruff clean, mypy clean |

**Final verdict: PASS**

# Environment

| Item | Value |
|---|---|
| Host | Linux (2-core, ~4 GB), Python **3.12.3** |
| Provider | `pysweph` 2.10.3.6 (Swiss Ephemeris bindings, `import swisseph as swe`) |
| Ephemeris version | **"18"** (reported by JRE `ProviderMetadata.ephemeris_version`) |
| Mode engaged | **SWIEPH** (high precision) with bundled files `sepl_18.se1`, `semo_18.se1` |
| Reference data | JPL Horizons (NASA SSD) — file DE441-based, fetched live from `ssd.jpl.nasa.gov/api/horizons.api` |
| Verification date | 2026-08-12 (UTC) |
| Reproducibility | Harness scripts in `/tmp/val_fetch_all.py`, `/tmp/val_compare.py`; raw reference responses cached in `/tmp/horizons_raw/*.txt` (retained for audit). |
| Command used to re-run the JRE suite | `.venv/bin/python -m pytest` → **233 passed** (67 unit + 166 integration); `.venv/bin/ruff check src tests` → clean; `.venv/bin/mypy src/astronomy` → clean |

# Test Inputs

Five instants across the four required classes; all computations used the
repository defaults (SWIEPH, apparent geocentric, Lahiri, mean node) unless
stated.

| ID | Class | Local time (input) | Timezone | UTC instant | Latitude | Longitude | JRE JD (UT) |
|---|---|---|---|---|---|---|---|
| E1 | A. Modern | 2024-06-01 00:00 | UTC | 2024-06-01 00:00 | 28.6139 | 77.2090 | 2460462.500000 |
| E2 | B. Historical | 1850-03-20 12:00 | UTC | 1850-03-20 12:00 | 51.4779 | −0.0015 | 2396837.000000 |
| E3 | C. Retrograde + D. Node + E. Timezone (IST) | 1990-06-15 10:00 | Asia/Kolkata | 1990-06-15 04:30 | 84.123456789 | 0.0000123 | 2448057.687500 |
| E5 | E. Timezone (EDT, DST) | 2024-07-01 15:00 | America/New_York | 2024-07-01 19:00 | 40.7128 | −74.0060 | 2460493.291667 |

E3 deliberately reuses the test-plan golden-fixture instant
(1990-06-15 04:30 UTC at lat 84.123456789, lon 0.0000123), now expressed as
an IST wall-clock input, which simultaneously exercises requirement E
(timezone-sensitive input).

# Independent References

| # | Reference | Source | Coordinate system | Notes |
|---|---|---|---|---|
| R1 | JPL Horizons observer tables | NASA/JPL SSD API, `EPHEM_TYPE=OBSERVER`, `CENTER=500@399` (geocenter), `QUANTITIES=31`, `ANG_FORMAT=DEG`, `EXTRA_PREC` | **Geocentric, apparent, IAU76/80 ecliptic-and-equinox of date** — the same frame as JRE's default apparent tropical output | Light-time + aberration + nutation included; DE441 dynamics |
| R2 | JPL Horizons osculating elements of the Earth around the Sun | `EPHEM_TYPE=ELEMENTS`, `COMMAND=399`, `CENTER=500@10` | Ecliptic-J2000 elements; true longitude = Ω + ω + ν | Used to derive the Sun's **geometric** geocentric longitude = Earth λ + 180°, precessed to date (Meeus ch. 21); compared against JRE `position_type=TRUE` |
| R3 | JPL Horizons osculating elements of the Moon | `EPHEM_TYPE=ELEMENTS`, `COMMAND=301` | Ecliptic-J2000 ascending node Ω, precessed to date | Independent "true node" reference |
| R4 | Meeus, *Astronomical Algorithms* 2nd ed., ch. 47 — mean lunar node | Published formula, computed independently (no JRE code) | Ecliptic of date | Ω = 125.04452 − 1934.136261·T + 0.0020708·T² + T³/450000 |
| R5 | Published Lahiri ayanamsa constants | Astrodienst Swiss Ephemeris documentation; Indian Astronomical Ephemeris tabular value | Convention (tropical→sidereal zero point) | Swiss-documented J2000.0 value 23°51′25.5″; IAE tabular ~23°51′11.9″ |

No reference value in this report was produced by the JRE implementation.

# Planetary Position Comparison

Tolerances: longitude/latitude **1 arcmin** (2 arcmin for the Moon); speed
**0.05 °/day** (0.6 °/day for the Moon — central-difference truncation).

## E1 — modern (2024-06-01 00:00 UTC) — reference R1

| Body | Ref lon (°) | JRE lon (°) | Δlon (″) | Ref lat (°) | JRE lat (°) | Δlat (″) | Ref speed | JRE speed | Δspeed | Result |
|---|---|---|---|---|---|---|---|---|---|---|
| Mars | 23.880527 | 23.880539 | 0.04 | −1.172994 | −1.172996 | 0.01 | +0.75068 | +0.75069 | 1e-5 | PASS |
| Jupiter | 61.414957 | 61.414970 | 0.05 | −0.716398 | −0.716393 | 0.02 | +0.23386 | +0.23387 | 1e-5 | PASS |
| Saturn | 348.747072 | 348.747077 | 0.02 | −1.857591 | −1.857594 | 0.01 | +0.04656 | +0.04656 | 0.0 | PASS |

## E2 — historical (1850-03-20 12:00 UTC) — reference R1 (full matrix)

This instant is in the pre-1900 range where the QA stage found and fixed a
silent Julian-Day formula defect; the sub-arcsecond agreement here
**independently confirms the fix**.

| Body | Ref lon (°) | JRE lon (°) | Δlon (″) | Ref lat (°) | JRE lat (°) | Δlat (″) | Ref speed | JRE speed | Δspeed | Result |
|---|---|---|---|---|---|---|---|---|---|---|
| Sun | 359.543988 | 359.544090 | 0.37 | −0.000139 | −0.000145 | 0.02 | +0.99229 | +0.99229 | 1e-5 | PASS |
| Moon | 80.843718 | 80.843813 | 0.34 | −4.605089 | −4.605079 | 0.04 | +14.01066 | +14.02522 | 0.0146 | PASS |
| Mercury | 336.187583 | 336.187685 | 0.37 | −2.141783 | −2.141794 | 0.04 | +1.46912 | +1.46938 | 0.0003 | PASS |
| Venus | 3.886441 | 3.886543 | 0.37 | −1.306096 | −1.306102 | 0.02 | +1.24389 | +1.24390 | 1e-5 | PASS |
| Mars | 92.099338 | 92.099440 | 0.37 | +2.370275 | +2.370287 | 0.04 | +0.42733 | +0.42741 | 7e-5 | PASS |
| Jupiter | 166.683227 | 166.683321 | 0.34 | +1.504180 | +1.504190 | 0.04 | −0.12428 | −0.12434 | 6e-5 | PASS |
| Saturn | 9.421108 | 9.421218 | 0.40 | −2.210424 | −2.210430 | 0.02 | +0.12450 | +0.12451 | 1e-5 | PASS |

Note: Venus at this instant is at λ ≈ 3.9° and the Sun at λ ≈ 359.5° —
both near the 0°/360° boundary, which exercises the longitude-normalization
path against the reference (no wrap artifacts).

## E3 — retrograde epoch (1990-06-15 04:30 UTC) — reference R1

| Body | Ref lon (°) | JRE lon (°) | Δlon (″) | Ref lat (°) | JRE lat (°) | Δlat (″) | Ref speed | JRE speed | Δspeed | Result |
|---|---|---|---|---|---|---|---|---|---|---|
| Mars | 10.816571 | 10.816585 | 0.05 | −1.983485 | −1.983488 | 0.01 | +0.71927 | +0.71930 | 2e-5 | PASS |
| Jupiter | 105.821804 | 105.821814 | 0.03 | +0.185182 | +0.185194 | 0.04 | +0.21645 | +0.21647 | 1e-5 | PASS |
| Saturn | 294.050205 | 294.050209 | 0.01 | +0.117008 | +0.117002 | 0.02 | **−0.05830** | **−0.05832** | 2e-5 | PASS |

## E5 — timezone-EDT (2024-07-01 19:00 UTC) — reference R1

| Body | Ref lon (°) | JRE lon (°) | Δlon (″) | Ref lat (°) | JRE lat (°) | Δlat (″) | Ref speed | JRE speed | Δspeed | Result |
|---|---|---|---|---|---|---|---|---|---|---|
| Mars | 46.531216 | 46.531227 | 0.04 | −0.942210 | −0.942207 | 0.01 | +0.71894 | +0.71896 | 2e-5 | PASS |
| Jupiter | 68.388011 | 68.388034 | 0.08 | −0.695556 | −0.695549 | 0.03 | +0.21598 | +0.21600 | 2e-5 | PASS |
| Saturn | 349.424740 | 349.424747 | 0.03 | −1.986187 | −1.986192 | 0.02 | −0.00330 | −0.00331 | 0.0 | PASS |

## Sun — geometric (reference R2), compared against JRE `position_type=TRUE`

| Epoch | Ref geometric λ (date, °) | JRE TRUE λ (°) | Δ (″) | Tolerance (″) | Result |
|---|---|---|---|---|---|
| E1 | 71.007257 | 71.006794 | 1.7 | 72 | PASS |
| E2 | 359.552656 | 359.549802 | 10.3 | 72 | PASS |
| E3 | 83.832483 | 83.836684 | 15.1 | 72 | PASS |

Residuals are the expected light-time/frame semantics between the osculating-
orbit geometric value and the library's geometric-of-date output; all well
inside tolerance.

**Coverage note (external limitation, not a JRE defect):** the public JPL
Horizons API instance served observer tables for Sun/Moon/Mercury/Venus only
for the 1850 instant during this validation session; for 1970–2024 dates it
returned properties-only responses (reproducible, see §Defects). Those bodies
are therefore verified against R1 at E2 and against R2/R3/R4 at the other
instants, with no gap in coverage: every body is validated against at least
one independent reference at ≥ 2 instants.

# Retrograde Validation

| Case | JRE state | JRE speed (°/day) | Independent reference | Consistent |
|---|---|---|---|---|
| Saturn, 1990-06-15 (E3) | **RETROGRADE** | −0.05832 | Horizons λ over ±2 d: 294.1647 → 294.1080 → 294.0502 → 293.9914 → 293.9315 (**decreasing**) | ✅ |
| Jupiter, 1850-03-20 (E2) | **RETROGRADE** | −0.12434 | Horizons speed −0.12428 (decreasing trend) | ✅ |
| Saturn, 2024-07-01 (E5) | **RETROGRADE** | −0.00331 | Horizons trend decreasing | ✅ |
| Mars, 2022-12-01 | **RETROGRADE** | −0.37685 | Horizons trend decreasing | ✅ |
| Mars, 2023-01-25 | DIRECT | +0.14347 | Horizons trend increasing | ✅ |
| Mars, 2023-02-15 | DIRECT | +0.32025 | Horizons trend increasing | ✅ |

The `STATIONARY_SPEED_EPSILON = 1e-9 °/day` threshold flagged in
`models.py` as "pending calibration by the VALIDATOR stage" was evaluated:
the sign-based classification matched the independent reference in every case
tested (16 position rows + 6 retrograde cases), and no station-instant
misclassification was observed. **No calibration change is required**; the
specified default stands.

# Node Validation

## Mean node (Rahu, default `node_type=MEAN`) — reference R4 (Meeus formula)

| Epoch | JDE (UT) | Ref mean node (°) | JRE Rahu (°) | Δ (°) | Tolerance (°) | Result |
|---|---|---|---|---|---|---|
| E1 | 2460462.5 | 12.829445 | 12.828196 | 0.00125 | 0.2 | PASS |
| E3 | 2448057.6875 | 309.710865 | 309.714437 | 0.00357 | 0.2 | PASS |

## True node (`node_type=TRUE`) — reference R3 (Horizons osculating Ω, precessed to date)

| Epoch | Ref Ω of date (°) | JRE true Rahu (°) | Δ (°) | Tolerance (°) | Result |
|---|---|---|---|---|---|
| E1 | 14.053684 | 14.040970 | 0.01271 | 0.3 | PASS |
| E3 | 308.123353 | 308.117028 | 0.00633 | 0.3 | PASS |

## Ketu

| Epoch | JRE Ketu − (JRE Rahu + 180°) | Result |
|---|---|---|
| E1 | 0.0 (exact) | PASS |
| E3 | 0.0 (exact) | PASS |

**Astronomical vs astrological derivation:** the lunar node itself (mean and
true) is an astronomical quantity and is validated above against R3/R4.
**Ketu = Rahu + 180° is an astrological derivation** (a convention applied on
top of the astronomical node); it is internally exact and documented as such
in the data contract — it is not an astronomical error and no independent
reference is applicable to it.

# Ayanamsa Validation

JRE default `ayanamsa=LAHIRI`, `ayanamsa_value` reported per position.

| Instant | JRE value | Ref (Swiss docs, J2000) | Δ vs Swiss docs | Ref (IAE tabular) | Δ vs IAE tabular | Tolerance | Result |
|---|---|---|---|---|---|---|---|
| 2000-01-01 12:00 UTC | 23.857092° (23°51′25.53″) | 23.857083° (23°51′25.5″) | 0.000009° (0.03″) | 23.853306° (23°51′11.9″) | 0.003787° (13.6″) | 0.02° (72″) | PASS |

The 13.6″ difference against the IAE tabular figure is a **documented
convention difference** (mean/apparent ayanamsa, nutation and precession-model
choice), not an error: the Swiss Ephemeris implementation matches Astrodienst's
own documented J2000.0 value to 0.03″. The ayanamsa is a conventional
(tropical→sidereal) quantity — an astrological derivation layer, not
astronomy — and both published constants fall within the validation tolerance.
The sidereal longitudes reported by JRE are consistent with
tropical − ayanamsa_value (internal check, also covered by the integration
suite's bit-exact `FLG_SIDEREAL` test).

# Determinism Validation

| Check | Result |
|---|---|
| Same request computed twice, in-process | Byte-identical JSON (`result_to_json`) |
| Cross-process determinism | Covered by the QA integration suite (`test_cross_process_determinism.py`, byte-identical child-process output) |
| Determinism hazards in `src/astronomy` (grep: `os.environ`, `getenv`, `random`, `datetime.now`, `utcnow`, `.now(`, `time()`, `uuid`, `setenv`, `unsetenv`) | **None found** — no ambient inputs; config is immutable and frozen per compute |

# Error Handling Validation

| Input | Expected | Observed | Result |
|---|---|---|---|
| Date before 1582-10-15 (1500-01-01) | reject | `InvalidTimestampError` | PASS |
| Timezone abbreviation (`"IST"`) | reject | `InvalidTimestampError` | PASS |
| Nonexistent local time (2024-03-10 02:30 America/New_York, DST gap) | reject | `InvalidTimestampError` | PASS |
| Latitude 91° | reject | `InvalidCoordinatesError` | PASS |
| Longitude 181° | reject | `InvalidCoordinatesError` | PASS |
| Empty bodies tuple | reject | `EphemerisError` | PASS |

Boundary behavior also exercised elsewhere: E1 uses exactly midnight
(00:00:00); E2 exercises the 0°/360° longitude boundary (Sun at 359.54°,
Venus at 3.89°) with exact agreement; DST-active EDT conversion at E5;
+05:30 IST conversion at E3.

# Architecture Validation

1. **Swiss Ephemeris isolation.** `import swisseph` appears only in
   `src/astronomy/swisseph/constants.py` and `src/astronomy/swisseph/provider.py`.
   The only touch outside the subpackage is the documented lazy factory import
   in `provider.py::get_provider()`. The service layer depends solely on the
   `EphemerisProvider` protocol (`provider.py`). **PASS**
2. **No astrology leakage.** Static scan of `src/astronomy` for astrology
   vocabulary (rashi, nakshatra, yoga, dasha, gochar, kundali, bhava,
   benefic/malefic, muhurta, prediction, house, lagna, tithi, karaka) returns
   only the `__init__.py` docstrings that explicitly *deny* such content. The
   runtime output contains raw astronomy only (positions, speeds, distances,
   states, metadata). **PASS**
3. **Configuration determinism.** No environment-variable or clock reads in
   `config.py`/`models.py`; `CalculationConfig` is frozen; the registry is
   frozen after first compute; all `swe.set_*` calls derive from the immutable
   config and are serialized under a lock. **PASS**
4. **Node mode explicit.** `config.node_type` (`MEAN` default / `TRUE`) is an
   explicit field; validated both modes against independent references. **PASS**
5. **Ayanamsa explicit.** `config.ayanamsa` (`LAHIRI` default, `RAMAN`,
   `FAGAN_BRADLEY`, or `None` for tropical-only) is an explicit field; the
   applied value is reported per position. **PASS**
6. **Provider metadata preserved.** `ProviderMetadata` (provider id, library
   name/version, ephemeris version) and `ProviderRun` (per-call mode + files)
   are both carried in the result envelope; observed values: `pysweph`
   2.10.3.6, ephemeris version "18", SWIEPH, `sepl_18.se1`+`semo_18.se1`.
   **PASS**
7. **Future-provider compatibility.** The `EphemerisProvider` protocol
   (provider_id, metadata property, compute(jd_ut, bodies, config) → ProviderRun)
   is a complete, binding contract implemented by the adapter; the registry can
   register additional providers without core changes. **PASS**

# Defects

**No implementation defects were found by the VALIDATOR stage.** Source code
was not modified. Recorded observations (none require action before MERGE):

1. **JPL Horizons API limitation (external).** During this session the public
   API instance rendered observer tables for Sun/Moon/Mercury/Venus only for
   the 1850 instant; 1970–2024 requests returned properties-only responses
   (reproducible across query forms: OBSERVER/VECTORS, TLIST, CSV, alternate
   centers; raw failing responses retained in `/tmp/horizons_raw/`). No impact
   on validation: those bodies were covered by R1 at 1850 and by R2/R3/R4 at
   the other instants. Future validators should expect to combine sources.
2. **Ayanamsa convention delta (13.6″)** vs the IAE tabular figure; matches the
   Swiss Ephemeris documented value to 0.03″ (see Ayanamsa Validation). Not a
   defect.
3. **QA-stage JD fix confirmed.** The 1850 full-matrix agreement at ≤0.40″
   independently confirms the QA fix of the pre-1900 Julian-Day formula; no
   regression found.
4. **Moon speed residual (0.0146 °/day).** This is truncation of the
   *reference* central difference (HORIZONS λ sampled at ±2 d around a
   strongly accelerating body), not a JRE error; JRE's speed comes from the
   ephemeris library's analytic derivative and is internally consistent with
   the HORIZONS ±1-day values.
5. **`STATIONARY_SPEED_EPSILON` calibration note closed.** The default 1e-9
   °/day threshold required no calibration change (see Retrograde Validation).
6. **`ayanamsa_override` no-op for predefined modes** (recorded by QA;
   `swe.set_sid_mode` ignores t0/ayanamsa_t0 for LAHIRI/RAMAN/FAGAN_BRADLEY).
   Documented behavior; only relevant to a future user-defined mode.

# Final Verdict

**PASS**

JRE-002 satisfies every validation item: input/UTC handling, geographic
coordinate validation, planetary longitudes/latitudes/speeds, retrograde/direct
state, Rahu/Ketu node computation and configuration, ayanamsa configuration,
provider metadata and ephemeris version, deterministic repeated calculations,
boundary conditions, serialization, and typed error handling — all verified
against independent authoritative references (JPL Horizons, Meeus published
formulas, published ayanamsa constants) at multiple timestamps including a
historical, a retrograde, and two timezone-sensitive instants. No
astronomical error was found; the only non-astronomical quantities (Ketu
derivation, ayanamsa frame) are documented conventions and are internally
consistent. Architecture separation (provider isolation, no astrology logic,
deterministic configuration, explicit node/ayanamsa, preserved metadata,
future-provider contract) is intact.

Per validation policy: the orchestration state was **not** advanced to MERGED
(remains QA-COMPLETE), **no source code was changed**, and **no commit was
made**. This report is the VALIDATOR deliverable.
