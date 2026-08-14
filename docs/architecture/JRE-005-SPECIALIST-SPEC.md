# JRE-005 — Bhava / House Engine: Specialist Implementation Specification

- Version: 0.2.0 (SPECIALIST — implementation-ready)
- Date: 2026-08-14
- Status: SPECIALIST-COMPLETE. This document is the **normative,
  implementation-ready contract** for CODING. It supersedes the
  architect draft (v0.1.0) where they conflict (supersession notices
  inline). The architecture ([JRE-005-BHAVA-CORE.md](JRE-005-BHAVA-CORE.md)),
  data contract ([JRE-005-DATA-CONTRACT.md](JRE-005-DATA-CONTRACT.md)),
  and test plan ([JRE-005-TEST-PLAN.md](JRE-005-TEST-PLAN.md)) are
  updated to v0.2.0 in lockstep.

## 1. Purpose

Pin the implementable contract for the derived bhava/house layer: exact
derivation formulas, complete schemas, enums, error types, validation
rules, ordering, serialization, determinism, performance, isolation, and
the coding handoff. Everything is a computational definition; there is
no interpretation, no rule evaluation, no prediction.

## 2. Supersessions of the architect draft (v0.1.0 → v0.2.0)

| # | Draft (0.1.0) | Specialist resolution (0.2.0) |
|---|---|---|
| S1 | `BhavaConfig.reference_default: "LAGNA"` | **Removed.** The API takes an explicit `references` tuple defaulting to **all four** references `(LAGNA, MOON, SUN, ASC)`. No hidden default reference. |
| S2 | Categories "sorted list" (order unspecified) | Pinned canonical order: enum declaration order `KENDRA, TRIKONA, DUSTHANA, UPACHAYA`. |
| S3 | `ASC == LAGNA` "whole-sign frame" (loose) | Pinned as the **`HOUSE_OCCUPANCY` anchor frame**: ASC = the chart's house-1 (ascendant cusp) house in the chart's own house system; sign-grid anchoring is a machine-testable deferred capability (§11.4, ADR-019). |
| S4 | Cusp proximity "3.0°, tradition-variable" (loose) | Pinned: wrap-aware shortest-arc math, inclusive boundary, `0 < orb < 30.0` validation, one config value per analysis (system-independent), documented modern convention (ADR-017). |
| S5 | Unplaced body: "whole-sign fallback (robustness pin)" | Pinned: **no silent fallback**. `unplaced_body_behavior` config: `RAISE` (default, `UnplacedBodyError`) or explicit `WHOLE_SIGN_FALLBACK` (provenance-labeled per body) (ADR-018). |
| S6 | Tradition profile: "defer or validated passthrough" | Pinned: `tradition_profile: str \| None` validated passthrough, **echoed** in `ChartEcho` and `DerivationBlock`, **no computation change in v0.2.0** (ADR-020). |
| S7 | Gochar scope: "house number + relative house" (loose) | Pinned in §22: `TransitHouseFact` — echo of `TransitThroughHouses` entries + natal-frame relative house; no transit interpretation; requires the natal chart input (ADR-021). |
| S8 | `derive.py` internal functions | Public derivation functions exposed and unit-testable (§4); service is a thin facade. |

## 3. Dependency boundary (normative, static-gated)

- `src/bhava/` imports **only** the `jyotish` public API
  (`src/jyotish/__init__.py` exports) and the standard library.
- Forbidden: `astronomy.*` (direct), `knowledge.*`, `swisseph`,
  network (`requests`/`urllib`/socket), any persistence API.
- Reused from JRE-003 (imported, never redefined): `HouseSystem`,
  `RashiId`, `NakshatraId`, `Pada`, `BodyId`, `RetrogradeState`,
  `TransitReferencePoint`, `AspectKind`, `ApplyingSeparating`,
  `AspectRelationship`, `Bhava`, `LagnaState`, `PlanetState`,
  `BirthData`, `NatalChart`, `TransitThroughHouses`,
  `HouseTransitEntry`, `JyotishConfig`, `HouseCuspProvider` (not
  instantiated), `bhava_containing_longitude`, `rashi_of`,
  `sign_lord_of`, `RASHI_ORDER`, `RASHI_CATALOG_VERSION`,
  `NAKSHATRA_CATALOG_VERSION`, `JyotishService` (facade use).
- JRE-005 never constructs `AstronomicalService` and never imports
  `jyotish.swisseph`.
- JRE-004 is **read-only compatibility oracle only**: the cross-layer
  test imports `knowledge.synthesis.normalize_snapshot` as an oracle;
  JRE-005 production code never imports `knowledge`.

## 4. Module layout (normative)

```
src/bhava/
    __init__.py        # public API; __all__ (mirror jyotish pattern)
    models.py          # enums + BhavaConfig + fact models (stdlib + jyotish public API re-exports)
    errors.py          # BhavaError family
    config.py          # load_config (config/bhava.toml authority) + validate(BhavaConfig)
    derive.py          # pure derivation functions (public, unit-testable)
    service.py         # BhavaService facade (consumes JyotishService)
    serialize.py       # result_to_json/result_to_dict, analysis_request_from_dict,
                       # transit_request_from_dict
```

`bhava.__version__ == "0.2.0"` (mirrors `BhavaConfig.derivation_version`
default).

## 5. Public API (`__all__`, pinned)

- **Service**: `BhavaService` with
  - `analyze(birth: BirthData, house_systems=None, references=None,
    config=None) -> HouseAnalysisResult` — computes one JRE-003 chart
    per system (ADR-015) and derives natal facts.
  - `analyze_chart(chart: NatalChart, references=None, config=None)
    -> HouseAnalysis` — derive from an existing chart (no chart call).
  - `analyze_transit(transit: TransitThroughHouses, natal_chart:
    NatalChart, references=None, config=None) -> TransitHouseAnalysis`
    — gochar-frame facts (§22).
- **Config**: `load_config`, `validate`, `BhavaConfig`.
- **Models**: `HouseAnalysisResult`, `HouseAnalysis`,
  `TransitHouseAnalysis`, `DerivedHouseFact`, `PlanetHouseFact`,
  `HouseOwnershipFact`, `RelativeHouseFact`, `AspectToHouseFact`,
  `TransitHouseFact`, `DerivationBlock`, `ChartEcho`.
- **Enums**: `OccupancyStatus`, `BoundaryKind`, `HouseCategory`,
  `RelativeHouseFrame`, `UnplacedBodyBehavior`, `FactFrame`.
- **Constants**: `SIGN_GRID_FRAME_SUPPORTED = False` (machine-testable
  deferred capability, §11.4).
- **Errors**: `BhavaError`, `InvalidAnalysisRequestError`,
  `InvalidBhavaConfigError`, `InconsistentChartError`,
  `UnplacedBodyError`, `UnsupportedReferenceError`.
- **Serialization**: `result_to_json`, `result_to_dict`,
  `analysis_request_from_dict`, `transit_request_from_dict`.

## 6. Enums (string values are the JSON values; IntEnum → ints)

| Enum | Members (declaration order = canonical sort order) |
|---|---|
| `OccupancyStatus` | `OCCUPIED`, `EMPTY` |
| `BoundaryKind` | `SIGN_BOUNDARY`, `COMPUTED_CUSP` |
| `HouseCategory` | `KENDRA`, `TRIKONA`, `DUSTHANA`, `UPACHAYA` |
| `RelativeHouseFrame` | `HOUSE_OCCUPANCY` (sole member in v0.2.0; extension is additive and versioned) |
| `UnplacedBodyBehavior` | `RAISE`, `WHOLE_SIGN_FALLBACK` |
| `FactFrame` | `NATAL`, `TRANSIT` |

Canonical sort order for serialization: enum declaration order (bodies,
houses, references, categories, aspects use the JRE-003 canonical
orders, §30).

## 7. `BhavaConfig` (frozen dataclass — complete schema)

| Field | Type | Default | Validation | Semantics |
|---|---|---|---|---|
| `cusp_proximity_orb_deg` | `float` | `3.0` | `0 < orb < 30.0` | cusp-proximity half-width (ADR-017) |
| `house_systems` | `tuple[HouseSystem, ...]` | `(WHOLE_SIGN,)` | non-empty; every member known; no duplicates | per-system analyses (ADR-015) |
| `include_empty_houses` | `bool` | `True` | — | materialize empty/occupied summaries |
| `unplaced_body_behavior` | `UnplacedBodyBehavior` | `RAISE` | enum member | §18 (ADR-018) |
| `tradition_profile` | `str \| None` | `None` | `None` or non-empty string | validated passthrough, echo-only (ADR-020) |
| `anchor_frame` | `RelativeHouseFrame` | `HOUSE_OCCUPANCY` | enum member | explicit frame echo (§11) |
| `derivation_version` | `str` | `"0.2.0"` | non-empty string | provenance pin (ADR-016) |

`config/bhava.toml` (normative; TOML is authoritative; missing file →
validated defaults):

```toml
[bhava]
cusp_proximity_orb_deg = 3.0
house_systems = ["WHOLE_SIGN"]
include_empty_houses = true
unplaced_body_behavior = "RAISE"
anchor_frame = "HOUSE_OCCUPANCY"
derivation_version = "0.2.0"
# tradition_profile is intentionally omitted (TOML has no null) — None default.
```

- `to_dict()`/`from_dict()` round-trip every field (missing key →
  field default; explicit `null` → `None` where the type allows).
- `validate(BhavaConfig)` raises `InvalidBhavaConfigError` with the
  offending value in `__str__`. Unknown enum values anywhere →
  `InvalidBhavaConfigError`.

## 8. Inputs and invariants

`analyze_chart(chart)` validates the input `NatalChart`:

- Exactly 12 `bhavas`, house numbers exactly `{1..12}` (no gaps/dups) —
  else `InconsistentChartError`.
- `chart.lagna` present with `rashi` and `house_system` — else
  `InconsistentChartError`.
- `planet_states` non-empty, canonical body order, unique bodies — else
  `InconsistentChartError`.
- `chart.config.house_system` must be one of `BhavaConfig.house_systems`
  when deriving that system — else `InvalidBhavaConfigError`.
- JRE-003 errors from delegated calls (e.g.
  `UnsupportedHouseSystemError`) **propagate unchanged**.

`analyze(birth, ...)` additionally validates birth data by delegation
(JRE-003 `InvalidBirthDataError` propagates).

## 9. House-number semantics (normative)

- Identity: `(house_system, house_number)`, `house_number ∈ {1..12}`
  (ADR-015).
- House 1 is anchored by the ascendant in every system: WHOLE_SIGN —
  the lagna rashi; cusp systems — the ascendant cusp opens house 1
  (JRE-003 semantics).
- Spans are **half-open `[start, end)`** in the `longitude_used` frame
  (wrap-aware for house 12): a longitude exactly at `start` belongs to
  the house opening there; a longitude exactly at `end` belongs to the
  next house. This matches JRE-003's `compute_bhavas` occupancy exactly
  (JRE-005 echoes occupancy, never re-derives spans).
- Whole-sign spans: `[rashi_start, rashi_start + 30)` with
  `BoundaryKind.SIGN_BOUNDARY`. Cusp spans: provider cusps with
  `BoundaryKind.COMPUTED_CUSP`; `Bhava.rashi` is the sign containing the
  cusp point (JRE-003 echo).

## 10. Whole-sign semantics (pinned)

- Whole-sign house of a body = `((rashi_index(rashi(body)) −
  rashi_index(rashi(lagna))) mod 12) + 1` using `RASHI_ORDER`.
- Used in exactly two places, both explicit:
  1. `PLANET_HOUSE_WHOLE_SIGN_FALLBACK` — only when
     `unplaced_body_behavior == WHOLE_SIGN_FALLBACK` (§18);
  2. the JRE-004-compatible fallback **inside** the occupancy frame is
     the same arithmetic but is never applied silently (gated by the
     same config).
- `BoundaryKind.SIGN_BOUNDARY` when `bhava.start_deg ==
  rashi_span(rashi)[0]` (exact float equality on `30 * index` values —
  deterministic).

## 11. Reference-point semantics and anchor frames (ADR-019)

### 11.1 Anchor frame (normative)

`anchor_frame == HOUSE_OCCUPANCY` (sole supported frame in v0.2.0):

- Absolute house `house_of[B]` = the body's bhava house in the chart's
  house system (occupancy), else the labeled fallback (§18).
- `house_of[LAGNA] = 1` by construction (house 1 = ascendant-anchored in
  every system).
- **In cusp-based systems this is genuinely cusp-anchored**: house
  numbers come from the chart's cusp bhavas, not from the sign grid.
  There is no silent reuse of whole-sign counting for placed bodies.
- References resolve as: `LAGNA` → 1; `MOON`/`SUN` → `house_of[body]`
  in the same frame; `ASC` → 1 (identical to `LAGNA` — the JRE-004 pin).

### 11.2 Relative-house formula (normative, ADR-014)

```
relative_house(B, R) = ((house_of[B] − house_of[R]) mod 12) + 1
```

### 11.3 JRE-004 compatibility (normative contract)

For every body B and reference R ∈ {LAGNA, MOON, SUN, ASC} and every
house system, JRE-005's value must equal JRE-004's
`normalize_snapshot(chart)["relative_houses"][R][B]`. JRE-004 is
**read-only**; the cross-layer test (TEST-PLAN §10) asserts equality
using JRE-004 as oracle. When `unplaced_body_behavior == RAISE`,
charts with an unplaced body fail before the comparison (real JRE-003
charts have none — spans partition the ecliptic); the oracle test runs
with `WHOLE_SIGN_FALLBACK` for synthetic unplaced cases.

### 11.4 Deferred capability: sign-grid anchoring (machine-testable)

- The **sign-grid frame** (relative house counted by sign from a
  reference rashi, independent of house occupancy — a classical
  counting convention) is **NOT supported in v0.2.0**.
- Machine-testable limitation:
  - `RelativeHouseFrame` has only `HOUSE_OCCUPANCY`; requesting any
    other frame → `InvalidBhavaConfigError` (unknown enum).
  - Module constant `SIGN_GRID_FRAME_SUPPORTED = False` is part of the
    public API.
  - `ChartEcho.sign_grid_frame_supported: false` is present on every
    result.
  - Tests pin the constant, the echo, and the enum error (TEST-PLAN §5).
- Extending the enum + flipping the flag later is an additive, versioned
  change (bump `FACT_VOCABULARY_VERSION` analog: `derivation_version`);
  it does not alter the `HOUSE_OCCUPANCY` contract or JRE-004 equality.

## 12. Occupancy rules (normative)

- `occupants(h)` = echo of `Bhava.occupants` (never re-derived).
- `occupancy_status(h) = OCCUPIED if occupants(h) else EMPTY`.
- Summaries: `empty_house_numbers`, `occupied_house_numbers` (ascending
  house order), `empty_house_count` — materialized when
  `include_empty_houses` (per-house status is always present).

## 13. Planet-house derivation (normative)

```
house_of[b]  = first h in 1..12 with b ∈ occupants(h)      # PLANET_HOUSE_OCCUPANCY
             | whole_sign_house(b) if none                  # §18 gated
house_rule[b] = "PLANET_HOUSE_OCCUPANCY" | "PLANET_HOUSE_WHOLE_SIGN_FALLBACK"
```

- `PlanetHouseFact` per body: `house_number`, `house_rule`, `rashi`,
  `degree_in_rashi`, `retrograde`, `is_node` (`body ∈ {RAHU, KETU}`),
  `sign_lord`, `house_lord`, `own_sign`, `own_house`,
  `relative_house_by_reference`, `derivation`. (No `frame` field — the
  field-level contract is DATA-CONTRACT §4; natal facts are the
  `HouseAnalysis` fact set, structurally separate from `frame: TRANSIT`
  `TransitHouseFact` rows per ADR-021.)
- `own_sign = (sign_lord == body)`; `own_house = (house_lord == body)`
  where `house_lord` is the lord of the occupied house.

## 14. House-lord derivation (normative)

- Echo: `DerivedHouseFact.lord = Bhava.house_lord` (`echoed_from:
  "bhava.house_lord"`).
- Aggregation: `lorded_houses(body) = sorted({h | bhava[h].house_lord
  == body})` (house order, ascending).
- `lord_placement(h)` = the `PlanetHouseFact` of `bhava[h].house_lord`
  (`None` when the lord is the body itself? no — always present; the
  lord is always one of the nine bodies). Present always; `None` only in
  the impossible case the lord body is absent from the chart (guarded by
  `InconsistentChartError` at input validation).

## 15. Sign-lord derivation (normative)

- `sign_lords: dict[RashiId, BodyId]` = `{r: sign_lord_of(r) for r in
  RASHI_ORDER}` — a **projection echo** of JRE-003's pinned catalog
  (`source_catalog_versions.rashi` provenance). Never re-authored.
- `lorded_signs(body) = [r for r in RASHI_ORDER if sign_lords[r] ==
  body]` (zodiacal order).

## 16. Ownership semantics (normative)

`HouseOwnershipFact` per body: `body`, `lorded_signs`, `lorded_houses`,
`derivation`. Derived purely from §14/§15 echoes. No karaka
(significator) assignments — bhava karakatva is interpretive and
deferred (research §33).

## 17. House categories (normative, resolution S2)

```
KENDRA   ⊇ {1, 4, 7, 10}
TRIKONA  ⊇ {1, 5, 9}
DUSTHANA ⊇ {6, 8, 12}
UPACHAYA ⊇ {3, 6, 10, 11}
categories(h) = [c for c in (KENDRA, TRIKONA, DUSTHANA, UPACHAYA) if h ∈ members(c)]
```

- Representation: **sorted membership set** (array in canonical enum
  order; possibly empty). Overlaps preserved: 1 → [KENDRA, TRIKONA];
  6 → [DUSTHANA, UPACHAYA]; 10 → [KENDRA, UPACHAYA]; 5 → [TRIKONA];
  12 → [DUSTHANA]. No primary label, no implied significance.
- The category *meanings* (strength/difficulty/growth) are interpretive
  and are NOT emitted (research §33).

## 18. Unplaced-body behavior (normative, ADR-018)

- A body is **unplaced** when no bhava's half-open span contains its
  `longitude_used` (possible only for provider cusp systems; JRE-003's
  ecliptic partition normally prevents it — the guard protects against
  inconsistent inputs and extreme-latitude cusp pathologies).
- `unplaced_body_behavior == RAISE` (default): **no fallback**; raise
  `UnplacedBodyError` (message includes body id, longitude_used, and
  house system) — serialization never produces a fabricated house.
- `unplaced_body_behavior == WHOLE_SIGN_FALLBACK` (explicit opt-in):
  the whole-sign house is used **and labeled** on the fact
  (`house_rule = "PLANET_HOUSE_WHOLE_SIGN_FALLBACK"`; `derivation.inputs`
  records the fallback inputs; never silent).
- Default RAISE is safe for real JRE-003 charts (spans partition the
  ecliptic); the fallback exists for explicit cross-layer parity with
  JRE-004's robustness path in synthetic cases.

## 19. Cusp proximity (normative, ADR-017)

```
arc(a, b)      = min(|a − b|, 360 − |a − b|)          # shortest arc, wrap-aware
near_cusp(b, h) = arc(longitude_used(b), start(h)) ≤ orb
               or arc(longitude_used(b), end(h)) ≤ orb
cusp_proximate(h) = [b for b in occupants(h) if near_cusp(b, h)]   # body order
```

- Boundary behavior: **inclusive** at exactly `orb`; a body exactly on a
  cusp (`arc == 0`) is cusp-proximate to that cusp (it is an occupant of
  the house opening there per §9 half-open semantics).
- The orb is **one configuration value per analysis** (system-independent:
  it measures distance to cusp points regardless of their source;
  house-system-specific cusp *positions* come from JRE-003). It is a
  **modern computational convention** — no classical verse pins a
  numeric orb (research §33) — hence the explicit config knob, default
  `3.0°`, no hidden default.
- Validation: `0 < orb < 30.0` (an orb ≥ 30° would make every body
  cusp-proximate to some cusp in whole-sign — degenerate).

## 20. Aspect-to-house geometric echo (normative)

- `aspects_received(h)` = echo of `Bhava.aspects` (cusp-to-occupant)
  plus, for each occupant, the pair aspects from other bodies
  (`PairGeometry.aspects` — supplied by the caller or computed by the
  service via JRE-003 `pair_geometry`).
- `AspectToHouseFact`: `house_system`, `house_number`, `target`
  (`"CUSP"` or occupant body), `source_body`, `kind`, `exact_angle_deg`,
  `distance_from_exact_deg`, `within_orb`, `applying_separating`,
  `derivation` (`id: "ASPECT_TO_HOUSE_AGGREGATION"`).
- JRE-005 adds **no aspect kinds and no aspect rules**; sign-based
  drishti doctrine is explicitly deferred to the future Drishti engine
  (this aggregation is that engine's geometric input surface).

## 21. Empty-house semantics (normative)

Per §12. `include_empty_houses` gates summaries only; per-house
`OccupancyStatus` is always present. No interpretive meaning attached
("empty ⇒ weak" is a rules-layer judgement, not a fact).

## 22. Transit-house behavior — Gochar scope v0.2.0 (normative, ADR-021)

JRE-005 consumes from JRE-003 `TransitThroughHouses`:

- `reference` (the transit call's reference — echoed),
- `transit_instant_utc_iso` (echoed),
- `entries` — per transiting body: `natal_house_number`,
  `natal_house_rashi`, `natal_house_lord`, `natal_occupants`,
  `aspects_to_natal` (all echoed),
- `planet_states` (transiting states — only `body` and
  `longitude_used` are read for anchoring),
- `birth_snapshot` (echo), `config` (echo).

`analyze_transit(transit, natal_chart, ...)` produces
`TransitHouseAnalysis`:

- `TransitHouseFact` per transiting body (`frame: TRANSIT`):
  - echoed entry fields (`natal_house_number`, `natal_house_rashi`,
    `natal_house_lord`, `natal_occupants`, `aspects_to_natal`) with
    `echoed_from: "transit_through_houses.entries"`;
  - derived `relative_house_by_reference` computed **in the natal
    frame**: absolute house of the transiting body = the natal bhava
    whose span contains its `longitude_used` (`bhava_containing_longitude`,
    JRE-003 public API), with the same §18 fallback gating; relative
    house per reference via the §11.2 formula. The natal chart is a
    required input (the `TransitThroughHouses` result does not embed
    the natal bhavas).
- `TransitHouseAnalysis`: `birth_snapshot` echo, `config` echo,
  `transit_instant_utc_iso` echo, `reference` echo,
  `transit_facts` (canonical body order), `chart_echo` (natal),
  `golden_version`.

Explicitly NOT in scope: transit *events* (ingress/egress/stations —
JRE-003 owns them), transit-event interpretation, "what the transit
means" — any such statement is a prediction and is forbidden. Natal
facts (`frame: NATAL`) and transit facts (`frame: TRANSIT`) are separate
fact sets and are never merged.

## 23. Provenance / `DerivationBlock` (normative, ADR-016)

| Field | Type | Semantics |
|---|---|---|
| `id` | `str` | stable derivation id (§23.1) |
| `derivation_version` | `str` | `BhavaConfig.derivation_version` |
| `inputs` | `list[str]` | input fact ids consumed (e.g. `["chart.bhavas", "chart.lagna"]`) |
| `source_catalog_versions` | `dict[str, str]` | `{"rashi": <RASHI_CATALOG_VERSION>, "nakshatra": <NAKSHATRA_CATALOG_VERSION>}` read from JRE-003 public exports |
| `house_system` | `HouseSystem` | system tag |

Echoed JRE-003 fields additionally carry `echoed_from` (e.g.
`"bhava.house_lord"`, `"transit_through_houses.entries"`).

### 23.1 Derivation ids (stable constants)

`PLANET_HOUSE_OCCUPANCY`, `PLANET_HOUSE_WHOLE_SIGN_FALLBACK`,
`RELATIVE_HOUSE`, `HOUSE_CATEGORIES`, `HOUSE_OCCUPANCY_STATUS`,
`SIGN_LORD`, `HOUSE_LORD_ECHO`, `OWNERSHIP`, `OWN_SIGN`, `OWN_HOUSE`,
`CUSP_BOUNDARY_KIND`, `CUSP_PROXIMITY`, `ASPECT_TO_HOUSE_AGGREGATION`,
`LORD_PLACEMENT`, `EMPTY_HOUSE_SUMMARY`, `SIGN_LORD_TABLE`,
`TRANSIT_HOUSE_ECHO`, `TRANSIT_RELATIVE_HOUSE`. New derivations append;
existing ids never change semantics.

## 24. `ChartEcho` (normative)

| Field | Type | Semantics |
|---|---|---|
| `house_system` | `HouseSystem` | the analysis system |
| `jyotish_config` | `dict` | echo of the chart's `JyotishConfig` (to_dict) |
| `provider_metadata` | `list[dict]` | echo of `NatalChart.provider_metadata` |
| `rashi_catalog_version` | `str` | JRE-003 `RASHI_CATALOG_VERSION` |
| `nakshatra_catalog_version` | `str` | JRE-003 `NAKSHATRA_CATALOG_VERSION` |
| `anchor_frame` | `RelativeHouseFrame` | `HOUSE_OCCUPANCY` |
| `sign_grid_frame_supported` | `bool` | `false` (machine-testable limitation, §11.4) |
| `cusp_proximity_orb_deg` | `float` | echo of config |
| `unplaced_body_behavior` | `str` | echo of config |
| `tradition_profile` | `str \| None` | echo of config (ADR-020) |
| `derivation_version` | `str` | echo of config |
| `golden_version` | `str` | environment pin |

## 25. Catalog/version handling (normative)

- JRE-005 owns **no catalogs**. All catalog data (rashi lords, order,
  nakshatra) is read from JRE-003's public exports and echoed with
  provenance.
- `source_catalog_versions` is read at analysis time from the JRE-003
  exports; a JRE-003 catalog change is a versioned decision (ADR-003)
  that JRE-005 observes and echoes — never adapts to implicitly.
- `GOLDEN_VERSION` pins the environment for golden fixtures.

## 26. Serialization and JSON Schema (normative)

- Conventions (inherited): snake_case keys; enums → string values
  (`IntEnum` → ints); tuples → arrays; `None` → `null`; floats via
  Python's round-trip repr (`-0.0 → 0.0`); JSON UTF-8.
- `result_to_json`/`result_to_dict` for `HouseAnalysisResult`,
  `HouseAnalysis`, `TransitHouseAnalysis`, and every fact model.
- Input parsers validate on construction (typed errors):
  `analysis_request_from_dict` (birth + house_systems + references +
  config), `transit_request_from_dict` (transit + natal chart refs).
- Round-trip: `json.loads(result_to_json(r))` preserves every double;
  request round-trips.
- JSON Schema ships at CODING with `additionalProperties: false` for
  every object (normative excerpt in DATA-CONTRACT §11).

## 27. Deterministic ordering (normative)

| Collection | Order |
|---|---|
| houses | 1..12 ascending |
| bodies | JRE-003 canonical: SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN, RAHU, KETU |
| references | JRE-003 `TransitReferencePoint` declaration order: LAGNA, MOON, SUN, ASC |
| categories | enum declaration order: KENDRA, TRIKONA, DUSTHANA, UPACHAYA |
| aspects | JRE-003 `AspectKind` declaration order, then source body |
| house systems | order as given in `BhavaConfig.house_systems` (preserved, not sorted) |
| `relative_house_table` | dict keyed by reference (declaration order), body order inside |

## 28. Configuration authority (normative)

- `config/bhava.toml` declares every default (§7); TOML is
  authoritative; missing file → validated defaults; no env overrides.
- `BhavaConfig` immutable; echoed on every result (`config` field).
- Unknown enum values in TOML/JSON → `InvalidBhavaConfigError`.

## 29. Error taxonomy (normative)

| Error | Raised when | `__str__` contains |
|---|---|---|
| `BhavaError` | base class | — |
| `InvalidAnalysisRequestError` | malformed request (bad birth, empty `references`, unknown fields) | offending field |
| `InvalidBhavaConfigError` | config invalid (unknown enum, orb out of range, empty/dup/unknown system set, bad profile string) | offending value |
| `InconsistentChartError` | input chart violates invariants (§8) | offending value (e.g. "11 bhavas") |
| `UnplacedBodyError` | body unplaced and `unplaced_body_behavior == RAISE` (§18) | body id, longitude, system |
| `UnsupportedReferenceError` | reference not in {LAGNA, MOON, SUN, ASC} | offending value |

JRE-003 errors propagate unchanged from delegated calls (never wrapped
into a fact).

## 30. Performance constraints (normative)

- Pure arithmetic over one `NatalChart`; the dominant cost is the
  delegated JRE-003 chart computation (excluded from the budget and
  documented).
- Single-chart analysis (one system): **p95 < 5 ms** on the reference
  hardware (informational).
- Multi-system: linear in `len(house_systems)`.
- No I/O at analysis time; no network; no clocks.
- Performance smoke test (TEST-PLAN §13).

## 31. Isolation constraints (normative)

- Import gates (§3) enforced by static tests.
- No interpretation vocabulary in `src/bhava` identifiers (same scan
  policy as JRE-003 §8: benefic/malefic/yoga/dasha/gochar/prediction/
  auspicious).
- JRE-002/JRE-003/JRE-004 byte-for-byte unchanged (git-diff isolation
  at every stage).
- `pyproject.toml` gains `bhava` + `tests/*/bhava` at CODING (build
  metadata only; no new dependencies).
- No personal-data persistence: `birth_snapshot` echoes are request
  scope only (JRE-003 privacy rule inherited).

## 32. Tradition-profile passthrough (normative, ADR-020)

- `BhavaConfig.tradition_profile: str | None` — validated passthrough
  (None or non-empty string). JRE-005 does **not** look up JRE-004
  profiles, does not parse them, and **does not change computation** in
  v0.2.0 (all computation uses the pinned defaults).
- The value is echoed in `ChartEcho.tradition_profile` and in every
  `DerivationBlock` (provenance-bearing): every result records the
  profile it was computed under, so a future version that makes
  tradition-specific choices (category tables, orbs, counting frames)
  does so explicitly and versioned, never silently.
- Passing an unknown profile string is valid (echo-only); it must not
  raise. This keeps the hook orthogonal to JRE-004's profile semantics.

## 33. Research: computational vs tradition-specific vs interpretive

| Concept | Classification | Source / note |
|---|---|---|
| Rashi lordship table | **computational** (pinned catalog) | JRE-003 `RASHI_LORDS`, cited to Brihat Parashara Hora Shastra ch. 4 / Brihat Jataka ch. 1 (pinned by JRE-003; echoed, not re-cited) |
| House categories (kendra/trikona/dusthana/upachaya) | **computational membership** (house-number arithmetic) | Classical categories attested in the bhava tradition (e.g. BPHS bhava chapters, Phaladīpikā); JRE-005 emits only membership, **not** their interpretive significance (strength/difficulty/growth) |
| Relative-house counting ("nth from lagna/Moon/Sun") | **computational** (frame pinned by ADR-014/019) | Classical counting convention; the occupancy-frame formula is pinned for JRE-004 compatibility |
| Cusp proximity ("bhava sandhi") | **computational**, orb = modern convention | Classical texts describe the concept of cusp junction without a numeric orb; no verse is cited for 3.0° — the value is an explicit config knob (ADR-017) |
| Whole-sign vs cusp bhavas | **computational** (house-system selection) | Classical norm (whole-sign) vs regional cusp practice; both explicit via `house_systems` (ADR-015) |
| Drishti/aspect doctrine | **interpretive rule** | deferred to future Drishti engine; JRE-005 echoes geometry only |
| Bhava karakatva / bala / yoga / dasha | **interpretive rule** | deferred to JRE-004/future layers; never computed by JRE-005 |
| Jaimini chara-karaka / pada bhava | **tradition-specific variation** | distinct tradition with its own computational rules; noted for future work, **not** adopted silently |

No citations are fabricated: the only sourced catalog is JRE-003's
pinned `RASHI_LORDS`; everything else is labeled as modern convention or
deferred classical material.

## 34. CODING handoff contract (normative)

CODING must implement, against this spec and the v0.2.0 data contract,
in `src/bhava/` only:

1. Models/enums/config per §6–§7; serialization per §26; errors per §29.
2. Pure derivations per §9–§22 (each a public function with the
   normative formula).
3. `BhavaService` facade per §5; JRE-003 delegation via public API only.
4. `config/bhava.toml` per §7; `pyproject.toml` gains `bhava` +
   `tests/*/bhava` (build metadata only).
5. Happy-path tests (TEST-PLAN §16) + static gates (§31) + determinism
   harness.
6. **No** interpretation vocabulary, **no** JRE-004 imports, **no**
   modifications to JRE-002/003/004.

CODING acceptance gates: full suite green (all JREs), ruff clean, mypy
clean (`src/bhava` strict), cross-process determinism PASS,
JRE-004 `relative_house` oracle equality PASS (TEST-PLAN §10),
JRE-002/003/004 isolation PASS.

## 35. Change history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-08-14 | Architect draft baseline |
| 0.2.0 | 2026-08-14 | Specialist pinning: six resolutions (S1–S8 supersession table), full schemas, normative formulas, ADR-017..021, CODING handoff contract (Status: SPECIALIST-COMPLETE) |
