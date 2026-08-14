# JRE-005 — Bhava / House Engine: Test Strategy

- Version: 0.2.0 (SPECIALIST)
- Date: 2026-08-14
- Status: SPECIALIST-COMPLETE
- Related: [architecture](JRE-005-BHAVA-CORE.md),
  [data contract](JRE-005-DATA-CONTRACT.md),
  [specialist spec](JRE-005-SPECIALIST-SPEC.md)

## 1. Test layers and directory layout

- `tests/unit/bhava/` — pure derivation tests with synthetic/fixture
  `NatalChart` inputs (no ephemeris required).
- `tests/integration/bhava/` — end-to-end via `BhavaService` against
  real JRE-003 charts (requires pysweph + bundled `.se1` files), plus
  determinism, cross-layer compatibility, and performance.
- `tests/fixtures/bhava/` — request catalog + golden `result_to_json`
  outputs (hex-float representation, `GOLDEN_VERSION` pin).
- `pyproject.toml` gains `tests/unit/bhava`, `tests/integration/bhava`
  at CODING time (build metadata only).

## 2. Requirement matrix (24 mandated design points)

| # | Requirement | Unit | Integration | Notes |
|---|---|---|---|---|
| 1 | Responsibility boundary | `test_bhava_static.py` | | no astronomy/knowledge/swisseph imports; no interpretation vocabulary |
| 2 | Inputs from JRE-003 | `test_errors.py`, `test_identity.py` | `test_bhava_synthesis_real.py` | consumes `NatalChart`/`TransitThroughHouses`; `InconsistentChartError` on malformed input |
| 3 | Outputs/data contracts | `test_bhava_models.py` | `test_bhava_schema_conformance.py` | shapes per DATA-CONTRACT |
| 4 | House identity semantics | `test_identity.py` | | `(house_system, house_number)` keying |
| 5 | Whole-sign vs cusp; multi-system | `test_identity.py` | `test_bhava_synthesis_real.py` | per-system analyses never mixed |
| 6 | House occupancy | `test_occupancy.py` | | occupancy echo + status |
| 7 | Planet-to-house | `test_planet_house.py` | | occupancy + fallback rule |
| 8 | House lord | `test_lordship.py` | | echo + aggregation |
| 9 | Sign lord | `test_lordship.py` | | echo of `sign_lord_of` |
| 10 | Bhava lord/occupancy rels | `test_lordship.py` | | own-house/own-sign/placement |
| 11 | Relative house | `test_relative_house.py`, `test_jre004_compat.py` | `test_jre004_oracle_real.py` | formula + JRE-004 equality |
| 12 | Ownership | `test_lordship.py` | | lorded signs/houses |
| 13 | Empty house | `test_occupancy.py` | | status, lists, count |
| 14 | Cusp/boundary | `test_cusps.py` | | boundary kind, proximity |
| 15 | Retrograde/node | `test_planet_house.py` | | echo + `is_node` |
| 16 | Aspect-to-house | `test_aspects.py` | | geometric echo only |
| 17 | Deterministic serialization | `test_bhava_serialize.py` | `test_bhava_golden.py` | round-trips + golden |
| 18 | Provenance | `test_bhava_provenance.py` | | derivation blocks, catalog pins |
| 19 | Error taxonomy | `test_errors.py` | | typed errors, value in `__str__` |
| 20 | Config authority | `test_bhava_config.py` | `test_bhava_config_echo.py` | TOML authority, echo |
| 21 | Determinism | `test_bhava_determinism.py` | `test_bhava_determinism_cross_process.py` | bit/byte identity |
| 22 | Performance | | `test_bhava_performance.py` | p95 < 5 ms single chart |
| 23 | Isolation | `test_bhava_static.py` | | gates below |
| 24 | Future compatibility | `test_future_surface.py` | | additive-extension invariants |

## 3. Config tests

- `config/bhava.toml` loads; every field round-trips; unknown house
  system → `InvalidBhavaConfigError`; orb ≤ 0 rejected; empty system set
  rejected; `reference_default` validated; config echo in every result
  equals the input.

## 4. Determinism tests

- In-process: same chart + config twice → every float `==` (bit
  equality); fact lists identical.
- Cross-process: child process computes the same analysis → byte-identical
  JSON (mirrors JRE-002/JRE-003 harness).
- Canonical ordering asserted (houses, bodies, references, categories).

## 5. Boundary and edge-case tests

- Lagna at 0°/30°/359.999°; body at rashi boundaries.
- House-12 wrap: cusp proximity across 360°.
- Category overlaps: house 6 → {DUSTHANA, UPACHAYA}; house 10 →
  {KENDRA, UPACHAYA}; house 1 → {KENDRA, TRIKONA}; canonical order
  asserted (`KENDRA, TRIKONA, DUSTHANA, UPACHAYA`).
- Whole-sign equivalence: relative house from LAGNA == absolute house
  for every body (property test over fixture charts).
- Multi-system: same birth under WHOLE_SIGN vs PLACIDUS — facts tagged
  by system; occupancy may differ; no cross-system mixing asserted.
- Empty-house: chart with empty houses → status/lists/count.
- Reference equalities: `ASC == LAGNA` rows; `relative_house(B, LAGNA)`
  == absolute house.
- Retrograde/stationary echo; Rahu/Ketu `is_node=True`, own-sign/own-house
  flags false for nodes (nodes lord no sign in the pinned catalog).

### 5a. Specialist-resolution tests (v0.2.0)

- **Cusp proximity (ADR-017)**: wrap-aware arc at 0°; inclusive boundary
  at exactly `orb`; a body exactly on a cusp is proximate to that cusp;
  body just beyond orb is not; config rejection of `orb ≤ 0` and
  `orb ≥ 30.0`; orb is one value per analysis (system-independent).
- **Categories (S2)**: membership sets for all 12 houses; overlaps
  pinned (1 → [KENDRA, TRIKONA]; 6 → [DUSTHANA, UPACHAYA]; 10 →
  [KENDRA, UPACHAYA]; 5 → [TRIKONA]; 12 → [DUSTHANA]); canonical
  serialization order.
- **Anchor frames (ADR-019)**: `ChartEcho.anchor_frame ==
  "HOUSE_OCCUPANCY"`; `SIGN_GRID_FRAME_SUPPORTED is False`;
  `ChartEcho.sign_grid_frame_supported is False`; a synthetic cusp
  chart (Placidus) shows occupancy-based (cusp-anchored) relative
  houses differing from naive sign counting for a chosen birth;
  `RelativeHouseFrame` unknown value → `InvalidBhavaConfigError`.
- **Unplaced body (ADR-018)**: synthetic chart with a body outside all
  spans → `UnplacedBodyError` under `RAISE`; under
  `WHOLE_SIGN_FALLBACK` the same chart yields a fact with
  `house_rule == "PLANET_HOUSE_WHOLE_SIGN_FALLBACK"` and the fallback
  inputs in `derivation.inputs` (never silent).
- **Tradition passthrough (ADR-020)**: `tradition_profile="x"` echoed in
  `ChartEcho` + `DerivationBlock`; unknown profile string accepted
  (echo-only, no error); computation identical with/without profile.
- **Gochar scope (ADR-021)**: `analyze_transit` echoes entry fields and
  derives natal-frame relative houses; transit facts tagged
  `frame: TRANSIT`; natal facts `frame: NATAL`; no transit-event
  computation in JRE-005 output; missing natal chart →
  `InvalidAnalysisRequestError`.

## 6. Fixtures and golden files

- `tests/fixtures/bhava/requests.json` — varied births (zones,
  coordinates) + house-system sets.
- `tests/fixtures/bhava/golden/` — committed `result_to_json` outputs
  with hex-float representation; `GOLDEN_VERSION` pins the environment.
- Fixture charts (synthetic `NatalChart` objects) for unit tests are
  constructed in code (no birth data in fixtures — privacy rule).

## 7. Cross-process determinism harness

Same pattern as JRE-002 §7/JRE-003 §7: serialize full
`HouseAnalysisResult` JSON in two fresh subprocesses; assert byte
identity. Config interleave (Lahiri↔Raman, WHOLE_SIGN↔PLACIDUS) shows
no state leakage.

## 8. Static / structural tests

- No `astronomy`, `knowledge`, `swisseph`, network, or
  personal-data-persistence imports in `src/bhava/`.
- No interpretation vocabulary in `src/bhava/` identifiers
  (benefic/malefic/yoga/dasha/prediction/auspicious — same scan policy
  as JRE-003 §8).
- Public surface: only `__all__` symbols importable; internal modules
  not re-exported.
- JRE-002/003/004 isolation: empty `git diff` over `src/astronomy`,
  `src/jyotish`, `src/knowledge` + their tests/config.

## 9. Provider-independence tests

- `BhavaService` works against a fake `JyotishService` (stubbed
  `NatalChart`) — derivation logic is decoupled from ephemeris.

## 10. Cross-layer compatibility tests

- **JRE-004 `relative_house` equality** (the key cross-layer contract,
  ADR-014): for fixture charts (WHOLE_SIGN and cusp systems), JRE-005's
  `relative_house_table` equals JRE-004's snapshot `relative_houses` for
  every body/reference. JRE-004 is **read-only**; the test imports
  JRE-004's `normalize_snapshot` as an oracle and never modifies it. For
  synthetic unplaced-body cases the comparison runs with
  `unplaced_body_behavior = WHOLE_SIGN_FALLBACK` (the JRE-004 robustness
  path).

## 11. Serialization tests

- JSON round-trips per DATA-CONTRACT §12: doubles identical; config
  round-trip; request round-trip; `-0.0 → 0.0`; `None` → `null`.

## 12. Independent-reference validation (VALIDATOR)

VALIDATOR independently verifies, for the areas mandated by the
SPECIALIST authorization:

- **House assignment** — re-derives each planet's house from published
  example charts (documented at VALIDATOR time; no fabricated
  citations) and from the JRE-003 golden outputs;
- **Lordship** — house/sign lords match the pinned `RASHI_LORDS` catalog
  echo for every house;
- **Relative-house calculations** — hand-computed `relative_house` for
  a sample of bodies/references matches the derived table (and the
  JRE-004 oracle);
- **Cusp boundaries** — `BoundaryKind` classification and half-open
  span semantics against the chart's cusps;
- **Multi-house-system separation** — per-system facts are internally
  consistent and never mixed (spot-check WHOLE_SIGN vs PLACIDUS);
- **Transit-house assignment** — `TransitHouseFact` entries match the
  JRE-003 `TransitThroughHouses` echoes;
- **Serialization** — round-trips per DATA-CONTRACT §12;
- **Determinism** — in-process + cross-process identity;
- plus the full matrix + gates (ruff, mypy over `src/bhava`, isolation,
  JRE-004 oracle equality).

## 13. Performance smoke test

- Single-chart analysis (one system): p95 < 5 ms (informational;
  JRE-003 chart computation excluded and documented). Multi-system
  scales linearly in system count. No I/O during analysis.

## 14. Offline guarantee

- `src/bhava` performs no network access at runtime; test scans imports
  and runs the analysis with network disabled.

## 15. Tooling and commands

- `pytest tests/unit/bhava tests/integration/bhava`
- `ruff check src tests`
- `mypy src/bhava` (strict; `jyotish` typed surface)
- Full suite: `pytest tests/unit tests/integration` (all JREs).

## 16. CODING happy-path subset (shipped with implementation)

- One chart, WHOLE_SIGN: derived houses, planet houses, ownership,
  relative house, empty houses, aspects, provenance.
- One chart, two systems: per-system analyses tagged, never mixed.
- Transit frame: gochar house facts.
- Config echo + serialization round-trip.
- Static gates.

## 17. Acceptance criteria

- All JRE-005 tests pass; full suite (all JREs) passes with zero
  regressions; ruff clean; mypy clean; cross-process determinism PASS;
  JRE-002/003/004 isolation PASS; JRE-004 `relative_house` equality PASS.

## 18. Change history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-08-14 | Architect test strategy (Status: ARCHITECT-COMPLETE) |
| 0.2.0 | 2026-08-14 | Specialist refinement: §5a resolution tests (six resolutions), §10 oracle-equalty details, §12 independent-reference checks for the eight mandated areas (Status: SPECIALIST-COMPLETE) |
