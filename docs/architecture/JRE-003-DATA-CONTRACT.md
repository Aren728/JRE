# JRE-003 — Jyotish Coordinate and State Layer: Data Contract

- Status: SPECIALIZED
- Version: 0.3.0 (supersedes the design-level data contract v0.2.0)
- Date: 2026-08-12
- Upstream: [JRE-003 Architecture §6](JRE-003-JYOTISH-CORE.md),
  [JRE-003 Specialist Spec](JRE-003-SPECIALIST-SPEC.md),
  [ADR-002](../decisions/ADR-002-HOUSE-ECLIPSE-ADAPTER-PLACEMENT.md),
  [ADR-004](../decisions/ADR-004-CONJUNCTION-ASPECT-SEMANTICS.md),
  [JRE-002 Data Contract](JRE-002-DATA-CONTRACT.md)

This document is the **field-level contract** for JRE-003's models. It defines
every enum, dataclass, JSON shape, JSON Schema, and round-trip guarantee that
CODING must implement. Consumers (future Gochar / Kundali engines) and QA test
against it.

> **Supersession notice (v0.3.0):** `JyotishConfig` gains `position_type`
> (§2) so the "no hidden defaults" rule covers apparent-vs-true positions;
> `TransitThroughHouses` gains a `birth_snapshot` echo (§8.3) mirroring
> `NatalChart` (requirement L audit rule); the `aspects` list in
> `PairGeometry` carries **all seven** kinds (complete facts, consumers
> filter `within_orb`); the JSON Schema section (§11) is extended to cover
> the additional models. These supersede the v0.2.0 field sets.

## 0. Conventions

- All models are `@dataclass(frozen=True)` (hashable, immutable).
- Enums are `str`-based; JSON value = enum string value. `Pada` is an
  `IntEnum` with values 1–4 (serialized as number).
- Tuples serialize as JSON arrays; `None` as `null`.
- Floats: IEEE-754 doubles, serialized with Python's round-trip repr — the
  JSON number decodes to the identical double.
- All angles in degrees; speeds in deg/day; distances in AU; times ISO 8601
  (UTC, `Z` suffix) plus Julian Day (UT, `float`).
- Longitude normalization: `[0, 360)`; `-0.0 → 0.0`.
- "`longitude_used`" = the longitude selected by `zodiac_mode`
  (sidereal by default; ADR-003).
- `body` fields use `astronomy.BodyId` values
  (`SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN, RAHU, KETU`).

## 1. Enums (string values are the JSON values)

| Enum | Values |
|---|---|
| `ZodiacMode` | `SIDEREAL`, `TROPICAL` |
| `HouseSystem` | `WHOLE_SIGN`, `EQUAL`, `PLACIDUS`, `KOCH`, `REGIOMONTANUS`, `CAMPANUS` |
| `RashiId` | `MESHA`, `VRISHABHA`, `MITHUNA`, `KARKA`, `SIMHA`, `KANYA`, `TULA`, `VRISHCHIKA`, `DHANUSHA`, `MAKARA`, `KUMBHA`, `MEENA` |
| `NakshatraId` | `ASHWINI`, `BHARANI`, `KRITTIKA`, `ROHINI`, `MRIGASHIRA`, `ARDRA`, `PUNARVASU`, `PUSHYA`, `ASHLESHA`, `MAGHA`, `PURVA_PHALGUNI`, `UTTARA_PHALGUNI`, `HASTA`, `CHITRA`, `SWATI`, `VISHAKHA`, `ANURADHA`, `JYESHTHA`, `MULA`, `PURVA_ASHADHA`, `UTTARA_ASHADHA`, `SHRAVANA`, `DHANISHTHA`, `SHATABHISHA`, `PURVA_BHADRAPADA`, `UTTARA_BHADRAPADA`, `REVATI` |
| `AspectKind` | `CONJUNCTION`, `OPPOSITION`, `TRINE`, `SQUARE`, `SEXTILE`, `QUINCUNX`, `SEMISEXTILE` |
| `ApplyingSeparating` | `APPLYING`, `SEPARATING`, `NONE` |
| `TransitEventKind` | `RASHI_INGRESS`, `RASHI_EGRESS`, `NAKSHATRA_INGRESS`, `NAKSHATRA_EGRESS`, `PADA_INGRESS`, `PADA_EGRESS`, `STATION_RETROGRADE`, `STATION_DIRECT` |
| `TransitReferencePoint` | `LAGNA`, `MOON`, `SUN`, `ASC` |
| `EclipseKind` | `SOLAR`, `LUNAR` |
| `EclipseClassification` | `TOTAL`, `PARTIAL`, `ANNULAR`, `HYBRID`, `PENUMBRAL` |
| `Pada` (IntEnum) | 1, 2, 3, 4 |

Reused from `astronomy` (never redefined): `BodyId`, `RetrogradeState`
(`DIRECT/RETROGRADE/STATIONARY`), `Ayanamsa`, `NodeType`, `PositionType`,
`EphemerisMode`, `ProviderMetadata`.

## 2. `JyotishConfig` (frozen dataclass)

| Field | Type | Default | Constraint / semantics |
|---|---|---|---|
| `zodiac_mode` | `ZodiacMode` | `SIDEREAL` | classification frame (ADR-003) |
| `ayanamsa` | `Ayanamsa \| None` | `Ayanamsa.LAHIRI` | passthrough to astronomy |
| `house_system` | `HouseSystem` | `WHOLE_SIGN` | explicit; never mixed (ADR-002) |
| `node_model` | `NodeType` | `NodeType.MEAN` | Rahu/Ketu source, passthrough |
| `position_type` | `PositionType` | `PositionType.APPARENT` | **v0.3.0**: apparent vs true geometric passthrough (req. J, no hidden defaults) |
| `provider_id` | `str \| None` | `None` | astronomy provider; `None` ⇒ default |
| `ephemeris_version` | `str \| None` | `None` | optional pin; mismatch ⇒ `ProviderCompatibilityError` |
| `timezone` | `str` | `"UTC"` | presentation zone only; facts stay UTC |
| `coordinate_precision` | `int` | `1` | DMS seconds decimal places, 0–3 |
| `conjunction_orb_deg` | `float` | `8.0` | conjunction orb (ADR-004) |
| `aspect_orbs_deg` | `dict[AspectKind, float]` | see below | per-kind orb table |
| `station_speed_epsilon` | `float` | `1e-9` | stationary threshold (matches astronomy) |
| `transit_sample_step_hours` | `float` | `6.0` | event-search sampling step (ADR-005) |
| `transit_tolerance_jd` | `float` | `1e-4` | event-search bisection tolerance (ADR-005) |

Default `aspect_orbs_deg` (all explicit in `config/jyotish.toml`):

```json
{
  "CONJUNCTION": 8.0, "OPPOSITION": 8.0, "TRINE": 7.0, "SQUARE": 7.0,
  "SEXTILE": 5.0, "QUINCUNX": 4.0, "SEMISEXTILE": 2.0
}
```

JSON shape:

```json
{
  "zodiac_mode": "SIDEREAL",
  "ayanamsa": "LAHIRI",
  "house_system": "WHOLE_SIGN",
  "node_model": "MEAN",
  "position_type": "APPARENT",
  "provider_id": null,
  "ephemeris_version": null,
  "timezone": "UTC",
  "coordinate_precision": 1,
  "conjunction_orb_deg": 8.0,
  "aspect_orbs_deg": { "CONJUNCTION": 8.0, "OPPOSITION": 8.0, "TRINE": 7.0,
                       "SQUARE": 7.0, "SEXTILE": 5.0, "QUINCUNX": 4.0,
                       "SEMISEXTILE": 2.0 },
  "station_speed_epsilon": 1e-9,
  "transit_sample_step_hours": 6.0,
  "transit_tolerance_jd": 0.0001
}
```

## 3. `DmsValue` (frozen dataclass)

| Field | Type | Semantics |
|---|---|---|
| `degrees` | `int` | whole degrees `[0, 360)` |
| `minutes` | `int` | `[0, 60)` |
| `seconds` | `float` | rounded per `coordinate_precision` |
| `sign` | `int` | `+1`/`-1` (for latitude); longitude always `+1` |

Format string: `"{sign}{degrees}°{minutes:02d}'{seconds:04.1f}\""` at
precision 1 (policy: round-half-even, deterministic). DMS is presentational
only — calculations never use it.

## 4. `PlanetState` (frozen dataclass) — continuous per-body fact

| Field | Type | Semantics |
|---|---|---|
| `body` | `BodyId` | which body |
| `longitude_tropical` | `float` | deg `[0,360)`, ecliptic-of-date (astronomy passthrough) |
| `longitude_sidereal` | `float` | deg `[0,360)` (astronomy passthrough; may be `None` if ayanamsa None — see note) |
| `longitude_used` | `float` | `longitude_sidereal` or `longitude_tropical` per `zodiac_mode` |
| `dms` | `DmsValue` | DMS of `longitude_used` |
| `rashi` | `RashiId` | `RashiId(floor(longitude_used / 30))` |
| `degree_in_rashi` | `float` | `longitude_used mod 30` |
| `nakshatra` | `NakshatraId` | `NakshatraId(floor(longitude_used / (360/27)))` |
| `nakshatra_lord` | `BodyId` | ruler from pinned catalog |
| `pada` | `Pada` | `floor((longitude_used mod 13°20′) / 3°20′) + 1` |
| `degree_in_nakshatra` | `float` | `longitude_used mod 13°20′` |
| `latitude` | `float` | deg, ecliptic latitude (astronomy passthrough) |
| `speed_longitude` | `float` | deg/day (astronomy passthrough) |
| `retrograde` | `RetrogradeState` | astronomy passthrough |
| `timestamp_utc_iso` | `str` | the computed instant, ISO 8601 `Z` |
| `julian_day_ut` | `float` | exact JD used |
| `provider_id` | `str` | astronomy provider id |
| `ephemeris_version` | `str` | astronomy ephemeris version |

> Note on `longitude_sidereal`/`longitude_tropical`: the astronomy core
> returns `longitude_sidereal=None` when `ayanamsa is None`. Because the
> Jyotish layer's default `zodiac_mode=SIDEREAL` requires a sidereal frame,
> `JyotishConfig.ayanamsa=None` combined with `zodiac_mode=SIDEREAL` is
> rejected at the service boundary (`JyotishError`) — an explicit frame must
> always be computable.

JSON shape:

```json
{
  "body": "MOON",
  "longitude_tropical": 150.123456789,
  "longitude_sidereal": 126.123456889,
  "longitude_used": 126.123456889,
  "dms": { "degrees": 126, "minutes": 7, "seconds": 24.4, "sign": 1 },
  "rashi": "SIMHA",
  "degree_in_rashi": 6.123456889,
  "nakshatra": "PURVA_PHALGUNI",
  "nakshatra_lord": "VENUS",
  "pada": 2,
  "degree_in_nakshatra": 3.123456889,
  "latitude": 4.5,
  "speed_longitude": 12.19,
  "retrograde": "DIRECT",
  "timestamp_utc_iso": "1990-06-15T04:30:00Z",
  "julian_day_ut": 2448057.6875,
  "provider_id": "swisseph.pysweph",
  "ephemeris_version": "18"
}
```

## 5. `AspectRelationship` (frozen dataclass)

| Field | Type | Semantics |
|---|---|---|
| `kind` | `AspectKind` | which exact-degree aspect |
| `exact_angle_deg` | `float` | ideal angle for kind (0/60/90/120/150/180) |
| `separation_deg` | `float` | actual absolute separation |
| `distance_from_exact_deg` | `float` | `min(|sep − ideal|, 360 − |sep − ideal|)` |
| `within_orb` | `bool` | `distance_from_exact_deg ≤ orb_deg` |
| `orb_deg` | `float` | the orb applied (from config) |
| `applying_separating` | `ApplyingSeparating` | from relative speeds (ADR-004) |

## 6. `PairGeometry` (frozen dataclass) — planet-to-planet fact

| Field | Type | Semantics |
|---|---|---|
| `first` | `BodyId` | canonical-order lower body |
| `second` | `BodyId` | canonical-order higher body |
| `separation_deg` | `float` | absolute angular separation `[0,180]` incl. latitude |
| `normalized_separation_deg` | `float` | `(λ2 − λ1) mod 360`, `[0,360)` |
| `same_rashi` | `bool` | `floor(λ1/30) == floor(λ2/30)` on `longitude_used` |
| `same_bhava` | `bool \| None` | chart supplied ⇒ natal-bhava equality; else `None` |
| `conjunction` | `bool` | `separation_deg ≤ conjunction_orb_deg` |
| `conjunction_distance_deg` | `float` | exact separation (== separation_deg) |
| `aspects` | `list[AspectRelationship]` | all kinds checked; `within_orb` entries |
| `orb_config` | `object` | `{"conjunction": 8.0, "aspects": {...}}` echo |
| `config_snapshot` | `JyotishConfig` | full config echo |

JSON shape:

```json
{
  "first": "JUPITER",
  "second": "SATURN",
  "separation_deg": 4.2,
  "normalized_separation_deg": 4.2,
  "same_rashi": true,
  "same_bhava": true,
  "conjunction": true,
  "conjunction_distance_deg": 4.2,
  "aspects": [
    {
      "kind": "CONJUNCTION",
      "exact_angle_deg": 0.0,
      "separation_deg": 4.2,
      "distance_from_exact_deg": 4.2,
      "within_orb": true,
      "orb_deg": 8.0,
      "applying_separating": "SEPARATING"
    }
  ],
  "orb_config": { "conjunction": 8.0, "aspects": { "CONJUNCTION": 8.0 } },
  "config_snapshot": { "zodiac_mode": "SIDEREAL", "house_system": "WHOLE_SIGN" }
}
```

## 7. `Bhava`, `LagnaState`, `NatalChart` (individual mode)

### 7.1 `Bhava`

| Field | Type | Semantics |
|---|---|---|
| `house_number` | `int` | 1..12 |
| `start_deg` | `float` | boundary start (`longitude_used` frame) |
| `end_deg` | `float` | boundary end |
| `rashi` | `RashiId` | sign associated with the house |
| `house_lord` | `BodyId` | ruler of `rashi` (pinned catalog) |
| `occupants` | `list[BodyId]` | bodies in span |
| `occupant_states` | `list[PlanetState]` | full states of occupants |
| `aspects` | `list[AspectRelationship]` | cusp-based aspects where applicable |
| `nakshatra` | `NakshatraId \| None` | cusp nakshatra where applicable |

### 7.2 `LagnaState`

| Field | Type | Semantics |
|---|---|---|
| `ascendant_longitude_deg` | `float` | `longitude_used` frame, `[0,360)` |
| `dms` | `DmsValue` | DMS of ascendant |
| `rashi` / `degree_in_rashi` | `RashiId` / `float` | classification |
| `nakshatra` / `nakshatra_lord` | `NakshatraId` / `BodyId` | classification |
| `pada` / `degree_in_nakshatra` | `Pada` / `float` | classification |
| `bhava_relationship` | `Bhava \| None` | the 1st-house binding |
| `house_system` | `HouseSystem` | explicit echo |

### 7.3 `BirthData` (input — echo only)

| Field | Type | Constraint |
|---|---|---|
| `date` | `str` (ISO date) | civil local date |
| `time` | `str` (ISO time) | civil local time |
| `timezone` | `str` | IANA zone |
| `latitude` | `float` | `[-90, 90]` |
| `longitude` | `float` | `[-180, 180]` |

> **Privacy rule (requirement L):** `BirthData` appears only as request input
> and as `birth_snapshot` echo in `NatalChart`. It is never stored by the
> engine, never written to disk by the library, and never embedded in code or
> test fixtures.

### 7.4 `NatalChart`

| Field | Type | Semantics |
|---|---|---|
| `birth_snapshot` | `BirthData` | exact echo of input |
| `lagna` | `LagnaState` | ascendant classification |
| `bhavas` | `list[Bhava]` | 12 houses per `house_system` |
| `planet_states` | `list[PlanetState]` | canonical `BodyId` order |
| `config` | `JyotishConfig` | config echo |
| `provider_metadata` | `list[ProviderMetadata]` | astronomy + house-cusp providers |

## 8. Transit outputs (requirements E, F)

### 8.1 `TransitEvent`

| Field | Type | Semantics |
|---|---|---|
| `body` | `BodyId` | which body |
| `kind` | `TransitEventKind` | event type |
| `event_julian_day_ut` | `float` | event instant |
| `event_utc_iso` | `str` | event instant ISO `Z` |
| `boundary_deg` | `float \| None` | crossed longitude (ingress/egress kinds) |
| `reached` | `str \| None` | `RashiId`/`NakshatraId`/`Pada` reached |
| `direction` | `RetrogradeState` | motion state at crossing |
| `search_metadata` | `SearchMetadata` | determinism echo |

### 8.2 `SearchMetadata`

| Field | Type | Semantics |
|---|---|---|
| `algorithm` | `str` | `"bisection-on-monotonic-segments"` |
| `sample_step_hours` | `float` | from config |
| `tolerance_jd` | `float` | from config |
| `iterations` | `int` | bisection iterations used |
| `position_calls` | `int` | memoized astronomy compute calls |

### 8.3 `TransitThroughHouses` / `HouseTransitEntry`

`TransitThroughHouses`: `reference` (`TransitReferencePoint`),
`transit_instant_utc_iso`, `planet_states`, `entries`
(`list[HouseTransitEntry]`), `config`, and (v0.3.0) `birth_snapshot`
(`BirthData` echo — audit rule, requirement L).

`HouseTransitEntry`:

| Field | Type | Semantics |
|---|---|---|
| `body` | `BodyId` | transiting body |
| `natal_house_number` | `int` | natal house traversed (per `reference`) |
| `natal_house_lord` | `BodyId` | lord of that natal house |
| `natal_occupants` | `list[BodyId]` | natal planets in that house |
| `aspects_to_natal` | `list[AspectRelationship]` | transit body vs each natal occupant |
| `natal_house_rashi` | `RashiId` | sign of the traversed house |

## 9. Eclipse facts (requirement H)

### 9.1 `EclipseContact`

| Field | Type | Semantics |
|---|---|---|
| `phase` | `str` | `P1/P2/P3/P4` (partial contacts) or `U1..U4` (umbral) or `MAX` |
| `julian_day_ut` | `float` | contact instant |
| `utc_iso` | `str` | contact instant ISO `Z` |

### 9.2 `EclipseEvent`

| Field | Type | Semantics |
|---|---|---|
| `kind` | `EclipseKind` | `SOLAR` / `LUNAR` |
| `classification` | `EclipseClassification` | astronomical class |
| `maximum_jd_ut` | `float` | time of greatest eclipse |
| `maximum_utc_iso` | `str` | ISO `Z` |
| `contacts` | `list[EclipseContact]` | available contact times |
| `magnitude` | `float` | eclipse magnitude (fraction) |
| `node_positions` | `list[PlanetState]` | Rahu/Ketu at maximum |
| `solar_lunar_positions` | `list[PlanetState]` | Sun/Moon at maximum |
| `geographic_visibility` | `GeographicVisibility \| None` | where available |
| `pre_event_interval_days` | `float` | **data**: window before max (e.g. partial-phase start offset) |
| `post_event_interval_days` | `float` | **data**: window after max |
| `provider_id` | `str` | eclipse provider id |
| `ephemeris_version` | `str` | ephemeris version |

> The `pre_/post_event_interval_days` fields are astronomical data describing
> the temporal extent of the event phases. JRE-003 makes no statement about
> what an eclipse "means" (ADR-006).

### 9.3 `GeographicVisibility`

| Field | Type | Semantics |
|---|---|---|
| `latitude_deg` | `float` | path/center latitude where available |
| `longitude_deg` | `float` | path/center longitude where available |
| `description` | `str` | e.g. `"central path"`, `"visible from …"` |

## 10. Service input shapes (JSON)

`request_from_dict` / `birth_from_dict` / `transit_query_from_dict` validate
at the service boundary before any provider call.

Generic planetary state:

```json
{
  "date": "2024-06-01", "time": "00:00:00", "timezone": "UTC",
  "latitude": 0.0, "longitude": 0.0,
  "bodies": null,
  "config": { "zodiac_mode": "SIDEREAL", "ayanamsa": "LAHIRI",
               "position_type": "APPARENT" },
  "provider_id": null
}
```

> The generic `planetary_state` requires date/time/timezone + location because
> it delegates to `AstronomicalService`; the location is unused for geocentric
> positions but is required by the astronomy contract. (Consumers that know a
> raw JD may use the lower-level `position_at(jd, bodies, config)` entry.)

Individual chart:

```json
{
  "birth": { "date": "1990-06-15", "time": "10:00:00",
             "timezone": "Asia/Kolkata", "latitude": 28.6139, "longitude": 77.209 },
  "config": { "zodiac_mode": "SIDEREAL", "house_system": "WHOLE_SIGN" }
}
```

Transit query (events):

```json
{
  "start_utc_iso": "2024-01-01T00:00:00Z",
  "end_utc_iso": "2024-12-31T00:00:00Z",
  "bodies": ["JUPITER"],
  "kinds": ["RASHI_INGRESS", "RASHI_EGRESS", "STATION_RETROGRADE", "STATION_DIRECT"],
  "config": { "transit_sample_step_hours": 6.0, "transit_tolerance_jd": 0.0001 }
}
```

Transit through houses:

```json
{
  "birth": { "date": "1990-06-15", "time": "10:00:00", "timezone": "Asia/Kolkata",
             "latitude": 28.6139, "longitude": 77.209 },
  "transit": { "date": "2024-06-01", "time": "00:00:00", "timezone": "UTC",
               "latitude": 0.0, "longitude": 0.0 },
  "reference": "LAGNA",
  "config": { "house_system": "WHOLE_SIGN" }
}
```

Eclipse query:

```json
{
  "start_utc_iso": "2024-01-01T00:00:00Z",
  "end_utc_iso": "2024-12-31T00:00:00Z",
  "kind": null,
  "config": {}
}
```

## 11. JSON Schema (normative excerpt — `PlanetState`)

The full schema ships with CODING. Every object sets
`additionalProperties: false`. Excerpt:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PlanetState",
  "type": "object",
  "additionalProperties": false,
  "required": ["body","longitude_tropical","longitude_sidereal","longitude_used",
    "dms","rashi","degree_in_rashi","nakshatra","nakshatra_lord","pada",
    "degree_in_nakshatra","latitude","speed_longitude","retrograde",
    "timestamp_utc_iso","julian_day_ut","provider_id","ephemeris_version"],
  "properties": {
    "body": { "enum": ["SUN","MOON","MARS","MERCURY","JUPITER","VENUS","SATURN","RAHU","KETU"] },
    "longitude_tropical": { "type": "number" },
    "longitude_sidereal": { "type": "number" },
    "longitude_used": { "type": "number" },
    "dms": {
      "type": "object", "additionalProperties": false,
      "required": ["degrees","minutes","seconds","sign"],
      "properties": { "degrees": {"type":"integer"}, "minutes": {"type":"integer"},
                      "seconds": {"type":"number"}, "sign": {"type":"integer"} }
    },
    "rashi": { "enum": ["MESHA","VRISHABHA","MITHUNA","KARKA","SIMHA","KANYA",
                        "TULA","VRISHCHIKA","DHANUSHA","MAKARA","KUMBHA","MEENA"] },
    "degree_in_rashi": { "type": "number" },
    "nakshatra": { "enum": ["ASHWINI","BHARANI","KRITTIKA","ROHINI","MRIGASHIRA",
      "ARDRA","PUNARVASU","PUSHYA","ASHLESHA","MAGHA","PURVA_PHALGUNI",
      "UTTARA_PHALGUNI","HASTA","CHITRA","SWATI","VISHAKHA","ANURADHA","JYESHTHA",
      "MULA","PURVA_ASHADHA","UTTARA_ASHADHA","SHRAVANA","DHANISHTHA",
      "SHATABHISHA","PURVA_BHADRAPADA","UTTARA_BHADRAPADA","REVATI"] },
    "nakshatra_lord": { "enum": ["SUN","MOON","MARS","MERCURY","JUPITER","VENUS","SATURN","RAHU","KETU"] },
    "pada": { "enum": [1, 2, 3, 4] },
    "degree_in_nakshatra": { "type": "number" },
    "latitude": { "type": "number" },
    "speed_longitude": { "type": "number" },
    "retrograde": { "enum": ["DIRECT","RETROGRADE","STATIONARY"] },
    "timestamp_utc_iso": { "type": "string" },
    "julian_day_ut": { "type": "number" },
    "provider_id": { "type": "string" },
    "ephemeris_version": { "type": "string" }
  }
}
```

## 12. Round-trip guarantees

- `json.loads(result_to_json(r))` → identical doubles for every numeric field.
- `birth_from_dict(json.loads(json.dumps(birth.to_dict())))` equals `birth`.
- `config_from_dict` round-trips every `JyotishConfig` field including the
  orb table.
- Tests cover all of the above (TEST-PLAN §6).

## 13. Change history

| Version | Date | Change |
|---|---|---|
| 0.2.0 | 2026-08-12 | Architect data contract |
| 0.3.0 | 2026-08-12 | Specialist refinement: `position_type` added to `JyotishConfig`; `birth_snapshot` echo added to `TransitThroughHouses`; `PairGeometry.aspects` carries all seven kinds; supersession notice |
