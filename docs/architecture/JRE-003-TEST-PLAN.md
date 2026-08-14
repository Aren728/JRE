# JRE-003 — Jyotish Coordinate and State Layer: Test Strategy

- Status: SPECIALIZED
- Version: 0.3.0 (supersedes the design-level test plan v0.2.0)
- Date: 2026-08-12
- Upstream: [JRE-003 Architecture §20, §23](JRE-003-JYOTISH-CORE.md),
  [JRE-003 Specialist Spec](JRE-003-SPECIALIST-SPEC.md),
  [Data Contract](JRE-003-DATA-CONTRACT.md),
  [ADR-003](../decisions/ADR-003-ZODIAC-MODE-CATALOG-VERSIONING.md),
  [ADR-005](../decisions/ADR-005-CONTINUOUS-TRANSIT-ENGINE.md),
  [ADR-006](../decisions/ADR-006-ECLIPSE-ENGINE-INTERFACE.md)

Ownership: QA authors and executes the full matrix. CODING ships the
happy-path subset (§16). VALIDATOR owns the independent-reference harness
(§12).

> **Supersession notice (v0.3.0):** specialist-resolved test additions:
> 1. **Eclipse `tret` layout pinning** (§13 new) — the binding's eclipse
>    return-tuple layout is empirically verified against NASA canon times
>    for the 1991-07-11 total solar and 1990-02-09 total lunar eclipses
>    (values recorded in the Specialist Spec §4.2).
> 2. **Sidereal house cusp flag policy** (§9) — assert the sidereal
>    ascendant from `houses_ex(FLG_SIDEREAL)` differs from
>    `tropical − ayanamsa` by < 0.01° (the ≈13″ frame-rotation difference is
>    expected and documented, not a bug).
> 3. **Pure whole-sign vs binding `'W'`** (§9) — the pure derivation must
>    equal the binding's `'W'` cusps (empirically ascendant-anchored).
> 4. **`position_type` passthrough** (§3, §2) — `JyotishConfig.position_type`
>    changes outputs when TRUE (geometric) vs APPARENT.

## 1. Test layers and directory layout

```
tests/
  unit/jyotish/          # pure logic — runs with NO swisseph import
  integration/jyotish/   # real astronomy (JRE-002) + houses/eclipse providers
  validation/jyotish/    # independent-reference harness (VALIDATOR)
```

- **Unit** must never import `swisseph`; a fixture-time guard fails the
  session otherwise (mirrors JRE-002's guard).
- **Integration** requires JRE-002's pinned deps and `.se1` files; skipped
  with a clear reason otherwise.
- **Validation** reads committed reference data offline; no network.

## 2. Requirement matrix (JRE-003 mandated tests, req. N)

| # | Requirement | File(s) | Key assertions |
|---|---|---|---|
| 1 | Rashi boundaries | `unit/.../test_rashi.py` | 0°→MESHA, 30°→VRISHABHA, 29.999°→MESHA; 360°≡0°; tropical vs sidereal frame per config |
| 2 | Nakshatra boundaries | `unit/.../test_nakshatra.py` | 0°→ASHWINI, 13°20′→BHARANI, 359.999°→REVATI; degree_in_nakshatra < 13°20′ |
| 3 | Pada boundaries | `unit/.../test_pada.py` | each 3°20′ arc → PADA_1..4; exact edge cases (3°20′k ± ε) |
| 4 | Exact conjunction | `integration/.../test_conjunction.py` | real near-conjunction instants; separation < orb ⇒ conjunct; exact distance preserved |
| 5 | Near-conjunction | `integration/.../test_conjunction.py` | separation just inside/outside orb boundary; orb echoed in result |
| 6 | Same-house wide-degree | `integration/.../test_geometry.py` | same_bhava/same_rashi true with 25° separation ⇒ **not** conjunct (ADR-004) |
| 7 | Retrograde motion | `integration/.../test_retrograde.py` | known retrograde windows ⇒ `RETROGRADE`; speed sign consistent (reuses JRE-002 validation dates) |
| 8 | Station points | `integration/.../test_transit_events.py` | STATION_RETROGRADE / STATION_DIRECT events within tolerance of published station dates |
| 9 | Transit ingress/egress | `integration/.../test_transit_events.py` | Rashi/Nakshatra/Pada ingress & egress times vs independent ephemeris data; retrograde re-crossing produces multiple events |
| 10 | Lagna | `integration/.../test_lagna.py` | ascendant classification vs published example charts; whole-sign bhava-1 = lagna sign |
| 11 | House transitions | `integration/.../test_houses.py` | WHOLE_SIGN vs EQUAL vs PLACIDUS produce distinct, self-consistent bhavas; no silent mixing; occupant spans |
| 12 | Timezone boundaries | `integration/.../test_timezone.py` | same instant across zones ⇒ identical facts; DST gap/ambiguous handled by astronomy layer, re-checked here |
| 13 | Eclipse events | `integration/.../test_eclipse.py` | known eclipses found in interval; classification + maximum time vs NASA catalog within tolerance (§12) |
| 14 | Deterministic repeated calcs | `integration/.../test_determinism.py` | in-process bit-equality; cross-process byte-equality (§4) |

Additional (req. A–M coverage):

- `test_planet_state.py` — every field of `PlanetState` populated, ranges
  correct, `longitude_used` follows `zodiac_mode`, metadata passthrough.
- `test_pair_geometry.py` — all 36 pairs computed; spherical identity
  `acos(cos) ≈ 0` for identical longitudes; normalized separation `[0,360)`.
- `test_aspects.py` — exact-angle aspects detected with correct
  `distance_from_exact_deg`; applying/separating from relative speeds.
- `test_bhavas.py` — occupants, lords, cusp nakshatra; chart-supplied
  `same_bhava` vs `None` in generic mode.
- `test_lagna_nakshatra.py` — lagna pada/lord/nakshatra correctness.
- `test_transit_reference_points.py` — LAGNA vs MOON vs SUN vs ASC numbering
  differ as expected; each explicit.
- `test_eclipse_data_only.py` — no significance/causation field exists in
  `EclipseEvent` output; `pre/post_event_interval_days` are plain numbers.
- `test_generic_individual.py` — generic call contains no birth data;
  individual call echoes birth snapshot only; both call the same core
  functions.

Specialist v0.3.0 additions:

- `test_position_type.py` — same instant with `position_type=APPARENT` vs
  `TRUE` yields different `longitude_used` (geometric vs apparent) while
  classification stays consistent within each frame; config echo carries
  `position_type` (req. J no-hidden-defaults).
- `test_eclipse_tret_layout.py` — for the pinned fixtures (1991-07-11 solar,
  1990-02-09 lunar), the adapter's contact mapping (§SPEC 4.2) reproduces
  NASA canon times within ±60 s; P1 ≤ P2 ≤ MAX ≤ P3 ≤ P4 ordering asserted.
- `test_sidereal_houses_flag.py` — sidereal ascendant via
  `houses_ex(FLG_SIDEREAL)` vs `tropical − ayanamsa`: `|Δ| < 0.01°`
  (documents the ≈13″ rotation difference; NOT bit-equality).
- `test_whole_sign_pure_vs_binding.py` — pure whole-sign cusps equal the
  binding's `'W'` cusps for a fixture set of dates/latitudes.

## 3. Config tests

- `test_config.py` (unit): `config/jyotish.toml` loads; every field
  round-trips; orb table complete for all `AspectKind`; invalid orbs →
  `InvalidOrbError`; `zodiac_mode=SIDEREAL` + `ayanamsa=None` rejected.
- `test_config_echo.py` (integration): config snapshot in every result
  equals the input config.

## 4. Determinism tests

- In-process: two identical requests → every float `==` (bit equality).
- Cross-process: child process computes the same request → byte-identical
  JSON (mirrors JRE-002's harness).
- Event search: same query twice (fresh cache) → identical event times to
  `transit_tolerance_jd`; `SearchMetadata` identical.
- Interleave configs (Lahiri→Raman→Lahiri; whole-sign→Placidus→whole-sign) →
  identical to isolated runs (per-call state discipline).

## 5. Boundary and edge-case tests

- Longitude wrap: planet at 0°/360°; crossing near 0° during retrograde.
- Sign spans: `degree_in_rashi` at 0.0 and 29.999…; pada at 3°20′ edges.
- Date/time edges: 1582-10-15 boundary (JRE-002 restriction), leap day,
  midnight, ±180° longitude, poles.
- DST gap/ambiguous instants (delegated to JRE-002; asserted at jyotish
  boundary).
- Empty `bodies=()` rejected; unknown house system → `UnsupportedHouseSystemError`;
  unknown reference → `UnsupportedReferencePointError`.

## 6. Fixtures and golden files

- `tests/fixtures/jyotish/requests.json` — generic/individual/transit/eclipse
  request catalog (varied zones, coordinates, configs).
- `tests/fixtures/jyotish/golden/` — committed `result_to_json` outputs with
  hex-float representation; `GOLDEN_VERSION` pins the producing environment
  (same policy as JRE-002 §6).
- Catalogs: rashi/nakshatra tables are pure data with checksums (ADR-003);
  catalog-version metadata tested.

## 7. Cross-process determinism harness

- Reuse JRE-002's `compute_once.py` pattern: a `scripts/jyotish/compute_once.py`
  reads request JSON → writes result JSON; the determinism test invokes it
  twice and compares bytes.

## 8. Static / structural tests

- `test_public_surface.py`: `jyotish.__all__` matches the architecture's
  allow-list exactly (no extra public names).
- `test_forbidden_imports.py`: no `astrology|knowledge|transits|dasha|
  calculations|rules|inference` import in `src/jyotish/**`; no
  `socket|requests|urllib|httpx` import (offline); `models.py` imports stdlib
  only; **`swisseph` binding imports confined to `jyotish/swisseph/`**
  (ADR-002); no import of `astronomy.swisseph`.
- `test_no_interpretation.py`: no interpretation vocabulary in
  `src/jyotish` **identifiers** (case-insensitive): `benefic`, `malefic`,
  `auspicious`, `predict`, `fortune`, `wealth`, `marriage`, `career`,
  `health`, `spiritual`, `muhurta`, `yoga` (as interpretation — conjunction
  fact fields use `conjunction`, never `yoga`), `dasha`, `gochar`,
  `drishti`. Rashi/Nakshatra/Bhava/Lagna/Pada/Eclipse vocabulary IS allowed
  (it is this layer's domain).
- `test_astronomy_unmodified.py`: asserts `src/astronomy` file set + public
  `__all__` are unchanged by JRE-003 (guards ADR-002's "JRE-002 untouched"
  rule).

## 9. Adapter correctness tests

- `test_house_cusps.py`: whole-sign derived from ascendant sign (pure);
  cusp systems from provider; sidereal cusps (`houses_ex` + `FLG_SIDEREAL`)
  consistent with JRE-002 sidereal positions (recorded caveat, architecture
  §25.4); `ascmc[0]` == ascendant.
- `test_eclipse_provider.py`: known solar + lunar eclipses found;
  classification matches NASA catalog; contact ordering sane
  (P1 ≤ P2 ≤ MAX ≤ P3 ≤ P4); `kind=None` returns both.
- `test_registry.py`: houses + eclipse registries register/get/default;
  unknown → typed error; frozen after first use.

## 10. Provider-independence tests

- Fake `HouseCuspProvider` and fake `EclipseProvider` registered in the
  jyotish registries → full pipeline works without the real binding
  (proves the core depends only on protocols, ADR-002).

## 11. Serialization tests

- `test_serialize.py`: JSON round-trips per DATA-CONTRACT §12; schema
  conformance for `PlanetState` (DATA-CONTRACT §11) and the other models;
  enums → strings; `Pada` → number; `None` → null; `-0.0 → 0.0`;
  microsecond timestamps round-trip; `birth_snapshot` echoes exactly.

## 12. Independent-reference validation (VALIDATOR)

Reference data committed at `datasets/validation/jyotish/` (no network at
run time):

| Domain | Independent source | Tolerance |
|---|---|---|
| Rashi/Nakshatra/Pada classification | Published Lahiri ephemeris positions (e.g. Indian Astronomical Ephemeris) for ≥ 6 dated instants | exact sign/nakshatra/pada match; ≤ 0.001° at boundaries |
| Lagna | Published example charts with computed ascendants (≥ 3 charts, varied latitudes) | ≤ 0.01° ascendant longitude |
| Houses | Published house tables / example charts for WHOLE_SIGN and one cusp system | WHOLE_SIGN exact; cusp ≤ 0.1° |
| Conjunction/aspect geometry | Independent spherical-math reimplementation + published conjunction lists | ≤ 1e-9 (pure math) / ≤ 0.05° vs published lists |
| Transit ingress/egress/station | Published ephemeris ingress/panchanga/station data (≥ 3 events per kind) | ≤ 15 min (0.0104 days) |
| Eclipse | NASA Five Millennium Canon of Eclipses (times + classification) | contact/maximum ≤ ±60 s; classification exact |
| Determinism | — (internal gate) | bit-identical |

- The harness computes through `JyotishService` and emits a per-domain
  report; the Architect fixes the tolerance budget after the first batch
  (same policy as JRE-002 §13).
- At least one retrograde window, one node position, one sidereal-known
  date, and one timezone-sensitive instant must be covered.

## 13. Performance smoke test

- `integration/.../test_performance.py`: single `PlanetState` set p95 < 10
  ms; event search < 200 position calls/event with memoization; eclipse
  search < 5 s for a 1-year window. Informational, not a hard CI gate
  (architecture §22).

## 14. Offline guarantee

- Covered structurally by §8 (no network imports). Integration tests run
  fully offline against bundled data; a conftest hook asserts `socket` is
  never called (mirrors JRE-002).

## 15. Tooling and commands

```
python -m pytest tests/unit/jyotish tests/integration/jyotish -q   # full gate (with astronomy paths)
python -m pytest tests/validation -q                                # VALIDATOR harness
ruff check src tests
mypy src/jyotish
```

- CI-format gate before CODING → QA: unit + integration + ruff + mypy green
  AND `src/astronomy` untouched (§8).

## 16. CODING happy-path subset (shipped with implementation)

- `test_rashi.py`, `test_nakshatra.py`, `test_pada.py` (core boundary cases)
- `test_planet_state.py`, `test_pair_geometry.py` (basic)
- `test_config.py`, `test_public_surface.py`, `test_forbidden_imports.py`
- `test_determinism.py` (in-process), `test_generic_individual.py`
- `test_house_cusps.py` + `test_lagna.py` (basic whole-sign)
- `test_position_type.py` (config passthrough, v0.3.0)

QA completes the remaining matrix (§2–§14).

## 17. Acceptance criteria for JRE-003 tests

1. All unit + integration tests green on a clean 3.12 environment with pinned
   deps and committed catalogs.
2. Determinism proven in-process and cross-process (bit equality; event times
   to tolerance).
3. All 14 mandated requirement tests present and green.
4. Independent-reference validation runs offline and reports within the fixed
   budget (incl. NASA eclipse catalog).
5. No interpretation vocabulary in `src/jyotish` identifiers; no
   `src/astronomy` modifications (static gates).
6. `BirthData` never persisted or embedded (static scan for birth fixtures
   beyond the catalog of synthetic test inputs).

## 18. Change history

| Version | Date | Change |
|---|---|---|
| 0.2.0 | 2026-08-12 | Architect test strategy |
| 0.3.0 | 2026-08-12 | Specialist refinement: supersession notice; eclipse `tret` layout pinning; sidereal house flag + whole-sign pure-vs-binding tests; `position_type` tests |
