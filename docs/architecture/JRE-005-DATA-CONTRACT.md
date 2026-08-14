# JRE-005 — Bhava / House Engine: Data Contract

- Version: 0.2.0 (SPECIALIST)
- Date: 2026-08-14
- Status: SPECIALIST-COMPLETE (field-level contract for the derived
  bhava/house layer; normative at CODING). Supersedes v0.1.0: enums
  extended, `BhavaConfig` refined (v0.2.0 fields), `ChartEcho` and
  transit models added, `reference_default` removed.
- Related: [architecture](JRE-005-BHAVA-CORE.md),
  [test plan](JRE-005-TEST-PLAN.md),
  [JRE-003 data contract](JRE-003-DATA-CONTRACT.md) (inherited shapes),
  [JRE-004 data contract](JRE-004-DATA-CONTRACT.md) (consumed semantics)

## 0. Conventions

- JSON UTF-8; snake_case keys; enums serialize as their string values
  (`IntEnum` as ints); tuples serialize as arrays; `None` → `null`.
- Floats: IEEE-754 doubles, serialized with Python's round-trip repr —
  `json.loads` decodes the identical double. `-0.0 → 0.0`.
- All angles in degrees in the `longitude_used` frame of the JRE-003
  chart consumed; normalized to `[0, 360)`.
- JRE-003 fact values appear in JRE-005 output **only as echoes**,
  marked `echoed_from` (ADR-016). JRE-005 never recomputes them.
- Ordering is canonical: houses 1–12; bodies in JRE-003 canonical order
  (SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN, RAHU, KETU);
  references in enum order (LAGNA, MOON, SUN, ASC); categories sorted.
- Versioning mirrors JRE-002/JRE-003/JRE-004: `GOLDEN_VERSION` pins the
  producing environment for golden fixtures.

## 1. Enums (string values are the JSON values)

| Enum | Members | Notes |
|---|---|---|
| `OccupancyStatus` | `OCCUPIED`, `EMPTY` | derived from `Bhava.occupants` |
| `BoundaryKind` | `SIGN_BOUNDARY`, `COMPUTED_CUSP` | echo classification of the cusp |
| `HouseCategory` | `KENDRA`, `TRIKONA`, `DUSTHANA`, `UPACHAYA` | membership set, canonical enum order, not a single label |
| `RelativeHouseFrame` | `HOUSE_OCCUPANCY` | sole member in v0.2.0; extension additive/versioned (ADR-019) |
| `UnplacedBodyBehavior` | `RAISE`, `WHOLE_SIGN_FALLBACK` | ADR-018; default `RAISE` (no silent fallback) |
| `FactFrame` | `NATAL`, `TRANSIT` | fact-set tag; natal and transit facts never merged |
| `DerivationId` | see specialist spec §23.1 | stable string constants for provenance |

Reused from JRE-003 (imported, never redefined): `HouseSystem`,
`RashiId`, `NakshatraId`, `Pada`, `BodyId`, `RetrogradeState`,
`TransitReferencePoint` (LAGNA/MOON/SUN/ASC), `Bhava`, `LagnaState`,
`PlanetState`, `AspectRelationship`, `BirthData`, `NatalChart`,
`TransitThroughHouses`, `HouseTransitEntry`.

## 2. `BhavaConfig` (frozen dataclass)

| Field | Type | Default | Semantics |
|---|---|---|---|
| `cusp_proximity_orb_deg` | `float` | `3.0` | orb for cusp-proximate bodies (ADR-017) |
| `house_systems` | `tuple[HouseSystem, ...]` | `(WHOLE_SIGN,)` | systems to analyze; one JRE-003 chart per system (ADR-015) |
| `include_empty_houses` | `bool` | `True` | materialize empty/occupied summaries |
| `unplaced_body_behavior` | `UnplacedBodyBehavior` | `RAISE` | ADR-018; no silent fallback |
| `tradition_profile` | `str \| None` | `None` | validated passthrough, echo-only (ADR-020) |
| `anchor_frame` | `RelativeHouseFrame` | `HOUSE_OCCUPANCY` | explicit frame echo (ADR-019) |
| `derivation_version` | `str` | `"0.2.0"` | provenance pin (ADR-016) |

- Declared in full by `config/bhava.toml` (no hidden defaults; TOML has
  no null, so `tradition_profile` is omitted → `None`); TOML is
  authoritative; `load_config()` validates (`InvalidBhavaConfigError`
  for unknown enum, orb outside `(0, 30.0)`, empty/duplicate/unknown
  system set, bad profile string).
- `to_dict()` / `from_dict()` round-trip every field (missing key →
  field default; explicit `null` → `None` where the type allows).

## 3. `DerivedHouseFact` (per house)

| Field | Type | Semantics |
|---|---|---|
| `house_system` | `HouseSystem` | the system this fact belongs to (ADR-015) |
| `house_number` | `int` | 1..12 (echo of `Bhava.house_number`) |
| `rashi` | `RashiId` | echo of `Bhava.rashi` |
| `lord` | `BodyId` | echo of `Bhava.house_lord` |
| `occupancy_status` | `OccupancyStatus` | derived (`OCCUPIED` iff occupants non-empty) |
| `occupants` | `list[BodyId]` | echo of `Bhava.occupants` |
| `categories` | `list[HouseCategory]` | **membership set** (sorted): kendra 1/4/7/10, trikona 1/5/9, dusthana 6/8/12, upachaya 3/6/10/11; empty list for none |
| `start_deg` / `end_deg` | `float` | echo of `Bhava.start_deg/end_deg` |
| `boundary_kind` | `BoundaryKind` | `SIGN_BOUNDARY` if `start_deg == rashi_span(rashi)[0]`, else `COMPUTED_CUSP` |
| `cusp_nakshatra` | `NakshatraId \| None` | echo of `Bhava.nakshatra` |
| `cusp_proximate_bodies` | `list[BodyId]` | bodies within `cusp_proximity_orb_deg` of either cusp (derived, wrap-aware) |
| `aspects_received` | `list[AspectToHouseFact]` | geometric echo aggregation (§7) |
| `lord_placement` | `PlanetHouseFact \| None` | where the house's lord is placed (derived) |
| `derivation` | `DerivationBlock` | provenance (§9) |

## 4. `PlanetHouseFact` (per planet)

| Field | Type | Semantics |
|---|---|---|
| `house_system` | `HouseSystem` | system tag |
| `body` | `BodyId` | planet/nodes |
| `house_number` | `int` | absolute house (occupancy; whole-sign fallback, rule id recorded) |
| `house_rule` | `str` | `"PLANET_HOUSE_OCCUPANCY"` or `"PLANET_HOUSE_WHOLE_SIGN_FALLBACK"` |
| `rashi` | `RashiId` | echo of `PlanetState.rashi` |
| `degree_in_rashi` | `float` | echo |
| `retrograde` | `RetrogradeState` | echo of `PlanetState.retrograde` |
| `is_node` | `bool` | `body ∈ {RAHU, KETU}` |
| `sign_lord` | `BodyId` | echo of `jyotish.sign_lord_of(rashi)` |
| `house_lord` | `BodyId` | lord of the occupied house (echo) |
| `own_sign` | `bool` | derived: `sign_lord == body` |
| `own_house` | `bool` | derived: `house_lord == body` |
| `relative_house_by_reference` | `dict[str, int]` | `relative_house(B, R)` for each reference R (ADR-014 formula) |
| `derivation` | `DerivationBlock` | provenance |

## 5. `HouseOwnershipFact` (per planet)

| Field | Type | Semantics |
|---|---|---|
| `house_system` | `HouseSystem` | system tag |
| `body` | `BodyId` | owner |
| `lorded_signs` | `list[RashiId]` | signs lords (echo of JRE-003 catalog lordship) |
| `lorded_houses` | `list[int]` | houses in this system whose `house_lord == body` (derived aggregation) |
| `derivation` | `DerivationBlock` | provenance |

## 6. `RelativeHouseFact` (chart-level table row)

| Field | Type | Semantics |
|---|---|---|
| `house_system` | `HouseSystem` | system tag |
| `body` | `BodyId` | subject |
| `reference` | `TransitReferencePoint` | anchor (`LAGNA`, `MOON`, `SUN`, `ASC`) |
| `reference_absolute_house` | `int` | absolute house of the anchor (1 for LAGNA) |
| `relative_house_number` | `int` | `((house_of[B] − house_of[R]) mod 12) + 1` |
| `derivation` | `DerivationBlock` | provenance (`id: "RELATIVE_HOUSE"`) |

`ASC` rows equal `LAGNA` rows in the whole-sign frame (JRE-004
compatibility pin, ADR-014); both are emitted so consumers need not
infer it.

## 7. `AspectToHouseFact` (geometric echo)

| Field | Type | Semantics |
|---|---|---|
| `house_system` | `HouseSystem` | system tag |
| `house_number` | `int` | receiving house |
| `target` | `str` | `"CUSP"` or occupant `BodyId` value |
| `source_body` | `BodyId` | aspecting planet |
| `kind` | `AspectKind` | echo of `AspectRelationship.kind` |
| `exact_angle_deg` | `float` | echo |
| `distance_from_exact_deg` | `float` | echo |
| `within_orb` | `bool` | echo |
| `applying_separating` | `ApplyingSeparating` | echo |
| `derivation` | `DerivationBlock` | provenance (`id: "ASPECT_TO_HOUSE_AGGREGATION"`) |

## 7a. `TransitHouseFact` (frame TRANSIT) and `TransitHouseAnalysis`

`TransitHouseFact` (v0.2.0, ADR-021) — one per transiting body:

| Field | Type | Semantics |
|---|---|---|
| `frame` | `FactFrame` | `TRANSIT` |
| `body` | `BodyId` | transiting planet |
| `natal_house_number` | `int` | echo of `HouseTransitEntry.natal_house_number` |
| `natal_house_rashi` | `RashiId` | echo of entry |
| `natal_house_lord` | `BodyId` | echo of entry |
| `natal_occupants` | `list[BodyId]` | echo of entry |
| `aspects_to_natal` | `list[dict]` | echo of entry aspects (geometric) |
| `relative_house_by_reference` | `dict[str, int]` | derived in the natal frame (§11.2) |
| `derivation` | `DerivationBlock` | `id: "TRANSIT_HOUSE_ECHO"` / `"TRANSIT_RELATIVE_HOUSE"` |

`TransitHouseAnalysis` (top level for `analyze_transit`):

| Field | Type | Semantics |
|---|---|---|
| `birth_snapshot` | `BirthData` | echo |
| `config` | `BhavaConfig` | echo |
| `transit_instant_utc_iso` | `str` | echo of the transit call |
| `reference` | `TransitReferencePoint` | echo of the transit call |
| `transit_facts` | `list[TransitHouseFact]` | canonical body order |
| `chart_echo` | `ChartEcho` | natal chart echo |
| `golden_version` | `str` | environment pin |

## 8. `HouseAnalysis` (per house system)

| Field | Type | Semantics |
|---|---|---|
| `house_system` | `HouseSystem` | one system per analysis (ADR-015) |
| `chart_echo` | `ChartEcho` | jyotish config echo, provider metadata, catalog versions |
| `derived_houses` | `list[DerivedHouseFact]` | 12 rows, house_number order |
| `planet_house_facts` | `list[PlanetHouseFact]` | canonical body order |
| `ownership_facts` | `list[HouseOwnershipFact]` | canonical body order |
| `relative_house_table` | `dict[str, dict[str, int]]` | `{ref: {body: house}}` mirroring JRE-004's `relative_houses` shape |
| `relative_house_facts` | `list[RelativeHouseFact]` | explicit rows |
| `aspects_to_houses` | `list[AspectToHouseFact]` | aggregated geometric aspects |
| `empty_house_numbers` | `list[int]` | derived (when `include_empty_houses`) |
| `occupied_house_numbers` | `list[int]` | derived |
| `empty_house_count` | `int` | derived |
| `derivation` | `DerivationBlock` | provenance for the analysis |
| `chart_echo` | `ChartEcho` | §8a echo block |

## 8a. `ChartEcho` (per analysis, v0.2.0)

| Field | Type | Semantics |
|---|---|---|
| `house_system` | `HouseSystem` | the analysis system |
| `jyotish_config` | `dict` | echo of the chart's `JyotishConfig` |
| `provider_metadata` | `list[dict]` | echo of `NatalChart.provider_metadata` |
| `rashi_catalog_version` | `str` | JRE-003 `RASHI_CATALOG_VERSION` |
| `nakshatra_catalog_version` | `str` | JRE-003 `NAKSHATRA_CATALOG_VERSION` |
| `anchor_frame` | `RelativeHouseFrame` | `HOUSE_OCCUPANCY` |
| `sign_grid_frame_supported` | `bool` | `false` (deferred capability, ADR-019) |
| `cusp_proximity_orb_deg` | `float` | echo of config |
| `unplaced_body_behavior` | `str` | echo of config |
| `tradition_profile` | `str \| None` | echo of config (ADR-020) |
| `derivation_version` | `str` | echo of config |
| `golden_version` | `str` | environment pin |

## 9. `DerivationBlock` (provenance, ADR-016)

| Field | Type | Semantics |
|---|---|---|
| `id` | `str` | stable derivation id (e.g. `"RELATIVE_HOUSE"`) |
| `derivation_version` | `str` | from `BhavaConfig.derivation_version` |
| `inputs` | `list[str]` | input fact ids consumed (e.g. `["chart.bhavas", "chart.lagna"]`) |
| `source_catalog_versions` | `dict[str, str]` | `{"rashi": <RASHI_CATALOG_VERSION>, "nakshatra": <NAKSHATRA_CATALOG_VERSION>}` from JRE-003 exports |
| `house_system` | `HouseSystem` | system tag |

Echoed JRE-003 fields on fact models carry an `echoed_from` string
(e.g. `"bhava.house_lord"`) in addition to `derivation`.

## 10. `HouseAnalysisResult` (top level)

| Field | Type | Semantics |
|---|---|---|
| `birth_snapshot` | `BirthData` | exact echo of input (privacy rule of JRE-003 §7.3 inherited) |
| `config` | `BhavaConfig` | echo |
| `analyses` | `list[HouseAnalysis]` | one per `house_systems` entry, same order as config |
| `golden_version` | `str` | environment pin |

Service input shapes (JSON):

```json
{
  "birth": { "date": "1990-06-15", "time": "10:00:00",
             "timezone": "Asia/Kolkata", "latitude": 28.6139, "longitude": 77.209 },
  "house_systems": ["WHOLE_SIGN", "PLACIDUS"],
  "references": ["LAGNA", "MOON", "SUN", "ASC"],
  "config": { "cusp_proximity_orb_deg": 3.0, "unplaced_body_behavior": "RAISE" }
}
```

Transit analysis:

```json
{
  "transit": { "birth": { "date": "1990-06-15", "time": "10:00:00",
                "timezone": "Asia/Kolkata", "latitude": 28.6139, "longitude": 77.209 },
               "transit_instant_utc_iso": "2024-06-01T00:00:00Z", "reference": "LAGNA" },
  "natal_chart": { }  // opaque — supplied by the caller as the JRE-003 NatalChart
}
```

`analysis_request_from_dict` / `transit_request_from_dict` validate on
construction (typed errors): unknown `house_system` →
`InvalidBhavaConfigError`; unknown reference → `UnsupportedReferenceError`;
malformed birth → JRE-003 `InvalidBirthDataError` propagates.

## 11. JSON Schema (normative excerpt — `DerivedHouseFact`)

Every object sets `additionalProperties: false`. Excerpt:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DerivedHouseFact",
  "type": "object",
  "additionalProperties": false,
  "required": ["house_system", "house_number", "rashi", "lord",
    "occupancy_status", "occupants", "categories", "start_deg", "end_deg",
    "boundary_kind", "cusp_nakshatra", "cusp_proximate_bodies",
    "aspects_received", "lord_placement", "derivation"],
  "properties": {
    "house_system": { "enum": ["WHOLE_SIGN","EQUAL","PLACIDUS","KOCH","REGIOMONTANUS","CAMPANUS"] },
    "house_number": { "type": "integer", "minimum": 1, "maximum": 12 },
    "rashi": { "enum": ["MESHA","VRISHABHA","MITHUNA","KARKA","SIMHA","KANYA",
                        "TULA","VRISHCHIKA","DHANUSHA","MAKARA","KUMBHA","MEENA"] },
    "lord": { "enum": ["SUN","MOON","MARS","MERCURY","JUPITER","VENUS","SATURN","RAHU","KETU"] },
    "occupancy_status": { "enum": ["OCCUPIED","EMPTY"] },
    "occupants": { "type": "array", "items": { "$ref": "#/$defs/BodyId" } },
    "categories": { "type": "array", "items": { "enum": ["KENDRA","TRIKONA","DUSTHANA","UPACHAYA"] } },
    "start_deg": { "type": "number" },
    "end_deg": { "type": "number" },
    "boundary_kind": { "enum": ["SIGN_BOUNDARY","COMPUTED_CUSP"] },
    "cusp_nakshatra": { "oneOf": [{ "$ref": "#/$defs/NakshatraId" }, { "type": "null" }] },
    "cusp_proximate_bodies": { "type": "array", "items": { "$ref": "#/$defs/BodyId" } },
    "aspects_received": { "type": "array", "items": { "$ref": "#/$defs/AspectToHouseFact" } },
    "lord_placement": { "oneOf": [{ "$ref": "#/$defs/PlanetHouseFact" }, { "type": "null" }] },
    "derivation": { "$ref": "#/$defs/DerivationBlock" }
  }
}
```

## 12. Round-trip guarantees

- `json.loads(result_to_json(result))` → identical doubles for every
  numeric field (round-trip repr).
- `analysis_request_from_dict(json.loads(json.dumps(request)))` equals
  the request.
- `BhavaConfig.from_dict(BhavaConfig().to_dict())` equals the config;
  missing-key vs explicit-`null` semantics follow JRE-003 §12.
- Tests cover all of the above (TEST-PLAN §11).

## 13. Change history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-08-14 | Architect data contract (Status: ARCHITECT-COMPLETE) |
| 0.2.0 | 2026-08-14 | Specialist refinement: `RelativeHouseFrame`/`UnplacedBodyBehavior`/`FactFrame` enums; `BhavaConfig` v0.2.0 fields (`reference_default` removed, `unplaced_body_behavior`/`tradition_profile`/`anchor_frame` added); `ChartEcho` §8a; `TransitHouseFact`/`TransitHouseAnalysis` §7a; transit request shape (Status: SPECIALIST-COMPLETE) |
