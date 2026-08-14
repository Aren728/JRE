# JRE-003 — Jyotish Coordinate and State Layer: Architecture and Refined Specification

- Status: ARCHITECTED
- Version: 0.2.0 (refined from the JRE-003 request v0.1.0)
- Date: 2026-08-12
- Related decisions:
  [ADR-001 Ephemeris Provider](../decisions/ADR-001-EPHEMERIS-PROVIDER.md),
  [ADR-002 House/Eclipse Adapter Placement](../decisions/ADR-002-HOUSE-ECLIPSE-ADAPTER-PLACEMENT.md),
  [ADR-003 Zodiac Mode and Catalog Versioning](../decisions/ADR-003-ZODIAC-MODE-CATALOG-VERSIONING.md),
  [ADR-004 Conjunction and Aspect Semantics](../decisions/ADR-004-CONJUNCTION-ASPECT-SEMANTICS.md),
  [ADR-005 Continuous Transit Engine](../decisions/ADR-005-CONTINUOUS-TRANSIT-ENGINE.md),
  [ADR-006 Eclipse Engine Interface](../decisions/ADR-006-ECLIPSE-ENGINE-INTERFACE.md)
- Upstream: [JRE-002 Specialist Spec](JRE-002-SPECIALIST-SPEC.md), [JRE-002 Data Contract](JRE-002-DATA-CONTRACT.md), [JSP-001 Core Specification](../../specifications/core/JSP-001.md)

## 1. Purpose

This document refines the JRE-003 request ("Deterministic Jyotish Coordinate
and State Layer") into an implementable design. JRE-003 sits **above** the
merged JRE-002 astronomical core and **below** all future interpretation
engines (Gochar interpretation, Kundali analysis, Dasha, Yoga, prediction).
It consumes raw astronomical state from `astronomy` and produces
**machine-readable Jyotish facts**: zodiacal classification, planet-to-planet
geometry, bhavas, lagna, continuous transit state, and the eclipse-engine
interface.

JRE-003 must serve both operating modes of JSP-001 with **one deterministic
calculation engine**:

- **GENERIC MODE** — transit analysis independent of any person's birth chart:
  `instant → planetary state`.
- **INDIVIDUAL MODE** — Kundali analysis from supplied birth data:
  `birth data + instant → natal/transit relationship state`.

It is the authoritative handoff from the **Architect** to the **Jyotish
Specialist** and downstream stages (CODING, QA, VALIDATOR).

## 2. Scope

JRE-003 computes, for the nine JRE-002 bodies (Sun, Moon, Mars, Mercury,
Jupiter, Venus, Saturn, Rahu, Ketu), the deterministic facts in the following
capability areas (mapped to the request's requirements A–N):

| Req | Capability | What JRE-003 produces |
|---|---|---|
| A | Planetary position state | Per body: absolute longitude (tropical + sidereal), latitude, DMS, Rashi, degree in Rashi, Nakshatra, Nakshatra lord, Pada, exact degree in Nakshatra, motion/speed, retrograde/direct, timestamp, provider metadata |
| B | Planet-to-planet geometry | Per pair: absolute angular separation, normalized separation, same-Rashi, same-Bhava (chart supplied), conjunction state + exact conjunction distance, aspect relationships + exact aspect distance, applying/separating, orb/config metadata |
| C | Bhava relationships | With birth-chart/location info: house number, boundary, Rashi, house lord, occupants, planetary aspects, planetary degrees, Nakshatra relationships where applicable; explicit house-system support |
| D | Lagna | Ascendant longitude, Rashi, exact degree, Nakshatra, Nakshatra lord, Pada, Bhava relationship |
| E | Continuous transit model | Continuous per-planet state (not "Jupiter = Sagittarius"); queries: Rashi/Nakshatra/Pada ingress & egress times, station (retrograde/direct) times, exact degree at an instant, full interval state |
| F | Transit through houses | Individual Kundali: transit planet → current state → natal house traversed, natal house lord, relevant natal planets, relationships/aspects; reference points explicit (Lagna / Moon / others) |
| G | Nakshatra model | All 27 Nakshatras deterministically: name, start/end longitude, ruler, four Pada boundaries, Pada mapping, exact longitude math (full catalog, not examples) |
| H | Eclipse engine interface | Defined provider interface for solar/lunar eclipse facts: contact/maximum/end times where available, geometry, classification, geographic visibility where available, associated planetary/node positions, pre/post event intervals **as data** |
| I | Separation of concerns | No benefic/malefic, good/bad, wealth, marriage, career, health, spiritual prediction, Yoga, Dasha, or Gochar interpretation — facts only |
| J | Configuration | Explicit machine-readable: ayanamsa, zodiac mode, house system, node model, ephemeris provider, ephemeris version, timezone, coordinate precision, conjunction/aspect orbs — no hidden defaults |
| K | Reproducibility | Identical input + timestamp + location + configuration + ephemeris version ⇒ identical output (bit-identical) |
| L | Generic vs individual data | Birth data is request input only — never embedded in the engine; generic and individual pipelines share the same core |
| M | Future extensibility | Vargas, Drishti, Dasha, Yoga, Gochar/Nakshatra interpretation, multi-layer synthesis, prediction consume JRE-003 output without modifying it |
| N | Testability | Boundary, conjunction, retrograde, station, ingress/egress, lagna, house-transition, timezone, eclipse, determinism tests + independent validation |

## 3. Non-goals (mandatory separation)

JRE-003 MUST NOT perform astrological interpretation. It must not determine
or expose:

- Benefic/malefic status, good/bad, auspicious/inauspicious
- Wealth, marriage, career, health, spiritual outcome or any prediction
- Yoga interpretation (a conjunction fact is data; calling it a "Yoga" is not)
- Dasha results or periods
- Gochar interpretation (what a transit "means")
- Nakshatra interpretation (what a nakshatra "means")
- Muhurta / electional guidance
- Sign-based drishti **rule tables** (classical 5th/7th/9th-style aspect rules
  belong to the future Rules layer; JRE-003 supplies the exact angular
  geometry those rules operate on — see [ADR-004])

Reviewers must reject any change that mixes interpretation vocabulary or
logic into `src/jyotish/`.

## 4. Design principles

1. **Facts, not meanings.** Every output is a machine-readable astronomical/
   geometric fact with its units, frame, and configuration echoed.
2. **One engine, two modes.** Generic and individual pipelines call the same
   deterministic core; birth data is an input, never engine state.
3. **Continuous first.** The primary representation is the continuous
   longitude state; discrete buckets (Rashi/Nakshatra/Pada) are derived
   classifications, never the primary fact.
4. **Explicit configuration.** Every materially significant choice (zodiac
   mode, house system, ayanamsa, node model, orbs, precision) is explicit in
   an immutable `JyotishConfig` and echoed in output. No hidden defaults.
5. **Exact geometry preserved.** Conjunction and aspects are defined from
   exact angular separation, never from "same house" alone
   ([ADR-004]).
6. **Determinism.** Pure functions, pinned data tables, fixed search
   algorithms — no clocks, no randomness, no network, no iteration-order
   dependence.
7. **Provider discipline.** JRE-003 talks to JRE-002's `astronomy` public API
   for all planetary positions. The two astronomical capabilities JRE-002 did
   not ship — house cusps and eclipse timing — are behind JRE-003's own
   provider protocols with isolated adapters ([ADR-002]).
8. **Extensibility without rewrite.** Future layers import JRE-003's public
   surface; JRE-003 never imports them.

## 5. Module layout

Following the established scaffold conventions (`src/`, `config/`, `datasets/`,
`tests/{unit,integration,validation}/`):

```
src/
  jyotish/
    __init__.py          # Public API allow-list (JyotishService, models, enums, errors)
    models.py            # Pure data: enums + frozen dataclasses (no swe, no astronomy)
    errors.py            # JyotishError hierarchy
    rashi.py             # Rashi catalog (12): names, boundaries, lords — pure data
    nakshatra.py         # Nakshatra catalog (27): names, rulers, 4 pada boundaries — pure data
    dms.py               # Degrees → DMS (explicit rounding policy) — pure
    position.py          # BodyPosition → PlanetState derivation (rashi/nakshatra/pada/DMS)
    geometry.py          # PairGeometry: separation, conjunction, aspects, applying/separating
    lagna.py             # Lagna from ascendant longitude (pure derivation)
    houses.py            # Bhava computation + HouseCuspProvider protocol + registry
    transit.py           # ContinuousTransitEngine: event search + interval state
    eclipse.py           # EclipseProvider protocol + EclipseEvent model
    config.py            # config/jyotish.toml → JyotishConfig
    serialize.py         # result_to_json / from_dict (JSON Schema per DATA-CONTRACT)
    service.py           # JyotishService — deterministic facade (both modes)
    swisseph/
      __init__.py        # get_provider() factories (houses, eclipses)
      constants.py       # swe hsys codes + SEFLG_ECL_* raw values (documented, no magic elsewhere)
      houses.py          # SwissEphemerisHouseCuspProvider
      eclipse.py         # SwissEphemerisEclipseProvider

config/
  jyotish.toml           # Defaults: zodiac_mode, house_system, ayanamsa, node_model,
                         # orb table, coordinate precision — every default explicit

datasets/
  jyotish/               # Pinned catalogs (rashi/nakshatra tables) + checksums, if not
                         # inlined as pure data; validation references for VALIDATOR

tests/
  unit/jyotish/          # Pure logic: catalogs, DMS, geometry, classification — no swe
  integration/jyotish/   # Real astronomy + houses/eclipse providers
  validation/jyotish/    # Independent-reference harness (VALIDATOR)
```

Conventions:

- Package root `jyotish` (import name), versioned independently of
  `astronomy`; a `jre.` namespace root is a later, separately-versioned
  refactor — never silent.
- `models.py` imports stdlib only (same rule as JRE-002).
- `jyotish` imports from `astronomy`'s **public API only**
  (`AstronomicalService`, `EphemerisResult`, `BodyPosition`, enums, errors).
  It never imports `astronomy.swisseph`.
- The `swisseph` binding may be referenced only from `jyotish/swisseph/*`
  (enforced by a static test, TEST-PLAN §8).
- No `jyotish` module may import `astrology`, `knowledge`, `transits`,
  `calculations`, `dasha`, `rules`, or `inference`.

## 6. Data contracts

Design-level models are specified here; the authoritative field-level
contract for CODING is
[JRE-003-DATA-CONTRACT.md](JRE-003-DATA-CONTRACT.md) v0.2.0 (the Specialist
may refine it to v0.3.0, as JRE-002 did). All models are
`@dataclass(frozen=True)`. Enums are `str`-based; JSON values are the enum
string values. Angles in degrees; speeds in deg/day; times ISO 8601 (UTC `Z`)
plus Julian Day (UT).

### 6.1 Enums (design level)

```python
class ZodiacMode(StrEnum):        SIDEREAL, TROPICAL          # default SIDEREAL
class HouseSystem(StrEnum):       WHOLE_SIGN, EQUAL, PLACIDUS, KOCH, REGIOMONTANUS, CAMPANUS
class NakshatraId(StrEnum):       ASHWINI ... REVATI           # all 27
class RashiId(StrEnum):           MESHA ... MEENA              # all 12
class AspectKind(StrEnum):        CONJUNCTION, OPPOSITION, TRINE, SQUARE, SEXTILE,
                                  QUINCUNX, SEMISEXTILE        # exact-degree aspects
class ApplyingSeparating(StrEnum):APPLYING, SEPARATING, NONE
class TransitEventKind(StrEnum):  RASHI_INGRESS, RASHI_EGRESS, NAKSHATRA_INGRESS,
                                  NAKSHATRA_EGRESS, PADA_INGRESS, PADA_EGRESS,
                                  STATION_RETROGRADE, STATION_DIRECT
class TransitReferencePoint(StrEnum): LAGNA, MOON, SUN, ASC     # extensible
class EclipseKind(StrEnum):       SOLAR, LUNAR
class EclipseClassification(StrEnum): TOTAL, PARTIAL, ANNULAR, HYBRID, PENUMBRAL
class Pada(IntEnum):              PADA_1..PADA_4
```

Reused from `astronomy` (imported, not redefined): `BodyId`,
`RetrogradeState`, `Ayanamsa`, `NodeType`, `PositionType`, `EphemerisMode`.

### 6.2 `JyotishConfig` (frozen dataclass) — explicit, echoed

| Field | Type | Default | Semantics |
|---|---|---|---|
| `zodiac_mode` | `ZodiacMode` | `SIDEREAL` | which longitude feeds classification (ADR-003) |
| `ayanamsa` | `Ayanamsa \| None` | `Ayanamsa.LAHIRI` | passthrough to astronomy |
| `house_system` | `HouseSystem` | `WHOLE_SIGN` | explicit; never mixed (ADR-002) |
| `node_model` | `NodeType` | `NodeType.MEAN` | passthrough to astronomy |
| `provider_id` | `str \| None` | `None` | astronomy provider selection |
| `ephemeris_version` | `str \| None` | `None` | optional pin check against provider metadata |
| `timezone` | `str` | `"UTC"` | presentation zone for event/local times (facts stay UTC) |
| `coordinate_precision` | `int` | `1` | DMS seconds decimal places (0–3) |
| `conjunction_orb_deg` | `float` | `8.0` | conjunction orb (documented default; ADR-004) |
| `aspect_orbs_deg` | `dict[AspectKind, float]` | explicit table | per-kind orbs; all values in `jyotish.toml` |
| `station_speed_epsilon` | `float` | `1e-9` | matches astronomy's stationary threshold |

### 6.3 Core output models (design level)

```python
@dataclass(frozen=True)
class DmsValue:
    degrees: int; minutes: int; seconds: float; sign: int
    def format(self, precision: int) -> str          # e.g. "143°15'32.4\""

@dataclass(frozen=True)
class PlanetState:                                    # requirement A + E (continuous)
    body: BodyId
    longitude_tropical: float; longitude_sidereal: float
    longitude_used: float                             # per zodiac_mode
    dms: DmsValue                                     # of longitude_used
    rashi: RashiId; degree_in_rashi: float            # [0, 30)
    nakshatra: NakshatraId; nakshatra_lord: BodyId
    pada: Pada; degree_in_nakshatra: float            # [0, 13°20')
    latitude: float; speed_longitude: float
    retrograde: RetrogradeState
    timestamp_utc_iso: str; julian_day_ut: float
    provider_id: str; ephemeris_version: str

@dataclass(frozen=True)
class PairGeometry:                                   # requirement B
    first: BodyId; second: BodyId
    separation_deg: float                             # absolute angular separation [0,180]
    normalized_separation_deg: float                  # mod-360 along ecliptic [0,360)
    same_rashi: bool
    same_bhava: bool | None                           # None when no chart supplied
    conjunction: bool                                 # separation <= orb (exact distance kept)
    conjunction_distance_deg: float                   # == separation when conjunct
    aspects: tuple[AspectRelationship, ...]
    orb_config: dict[str, float]                      # echo of orbs applied
    config_snapshot: JyotishConfig

@dataclass(frozen=True)
class AspectRelationship:                             # requirement B
    kind: AspectKind
    exact_angle_deg: float                            # ideal angle for kind
    separation_deg: float                             # actual
    distance_from_exact_deg: float                    # |sep - ideal| (mod applied)
    within_orb: bool
    orb_deg: float
    applying_separating: ApplyingSeparating           # from relative speeds

@dataclass(frozen=True)
class Bhava:                                          # requirement C
    house_number: int                                 # 1..12
    start_deg: float; end_deg: float                  # boundary (longitude_used frame)
    rashi: RashiId
    house_lord: BodyId
    occupants: tuple[BodyId, ...]
    occupant_states: tuple[PlanetState, ...]
    aspects: tuple[AspectRelationship, ...]           # to occupants (cusp-based where applicable)
    nakshatra: NakshatraId | None                     # of house cusp, where applicable

@dataclass(frozen=True)
class LagnaState:                                     # requirement D
    ascendant_longitude_deg: float
    dms: DmsValue
    rashi: RashiId; degree_in_rashi: float
    nakshatra: NakshatraId; nakshatra_lord: BodyId
    pada: Pada; degree_in_nakshatra: float
    bhava_relationship: Bhava | None                  # 1st house binding
    house_system: HouseSystem
```

### 6.4 Natal chart and transit outputs (individual mode)

```python
@dataclass(frozen=True)
class NatalChart:                                     # individual mode core
    birth_snapshot: BirthData                         # echo only — never engine state
    lagna: LagnaState
    bhavas: tuple[Bhava, ...]                         # 12, per house_system
    planet_states: tuple[PlanetState, ...]            # canonical BodyId order
    config: JyotishConfig
    provider_metadata: tuple[ProviderMetadata, ...]   # astronomy + house cusp provider

@dataclass(frozen=True)
class TransitThroughHouses:                           # requirement F
    reference: TransitReferencePoint                  # LAGNA / MOON / SUN / ASC
    transit_instant_utc_iso: str
    planet_states: tuple[PlanetState, ...]            # transit positions
    entries: tuple[HouseTransitEntry, ...]            # per planet
    config: JyotishConfig

@dataclass(frozen=True)
class HouseTransitEntry:
    body: BodyId
    natal_house_number: int                           # natal house traversed
    natal_house_lord: BodyId
    natal_occupants: tuple[BodyId, ...]
    aspects_to_natal: tuple[AspectRelationship, ...]  # transit body vs natal planets
    natal_house_rashi: RashiId
```

### 6.5 Transit events (continuous model)

```python
@dataclass(frozen=True)
class TransitEvent:                                   # requirement E
    body: BodyId
    kind: TransitEventKind
    event_julian_day_ut: float
    event_utc_iso: str
    boundary_deg: float | None                        # crossed longitude (ingress/egress)
    reached: RashiId | NakshatraId | Pada | None      # what was entered/left
    direction: RetrogradeState                        # crossing direction (motion state)
    search_metadata: SearchMetadata                   # algorithm/tolerance/iterations (determinism)

@dataclass(frozen=True)
class SearchMetadata:
    algorithm: str                                    # e.g. "bisection-on-monotonic-segments"
    sample_step_hours: float
    tolerance_jd: float
    iterations: int
    position_calls: int                               # memoized astronomy compute count
```

### 6.6 Eclipse facts (interface + data)

```python
class EclipseProvider(Protocol):                      # requirement H
    provider_id: str
    def find_eclipses(self, jd_start: float, jd_end: float,
                      kind: EclipseKind | None,
                      config: JyotishConfig) -> tuple[EclipseEvent, ...]: ...

@dataclass(frozen=True)
class EclipseEvent:
    kind: EclipseKind                                 # SOLAR | LUNAR
    classification: EclipseClassification             # TOTAL/PARTIAL/ANNULAR/HYBRID/PENUMBRAL
    maximum_jd_ut: float; maximum_utc_iso: str
    contacts: tuple[EclipseContact, ...]              # first/second/third/fourth where available
    magnitude: float
    node_positions: tuple[PlanetState, ...]           # Rahu/Ketu at maximum
    solar_lunar_positions: tuple[PlanetState, ...]    # Sun/Moon at maximum
    geographic_visibility: GeographicVisibility | None  # where available
    pre_event_interval_days: float                    # DATA — window before max
    post_event_interval_days: float                   # DATA — window after max
    provider_id: str; ephemeris_version: str

@dataclass(frozen=True)
class EclipseContact:
    phase: str                                        # e.g. "P1","P2","MAX","P3","P4"/"U1".."U4"
    julian_day_ut: float; utc_iso: str

@dataclass(frozen=True)
class GeographicVisibility:
    latitude_deg: float; longitude_deg: float         # path/center where available
    description: str                                  # e.g. "central path"
```

## 7. Planetary position and classification (A, G)

- **Source**: `AstronomicalService.compute` (JRE-002). JRE-003 never
  recomputes astronomy.
- **Zodiac mode** (ADR-003): classification uses `longitude_sidereal` when
  `zodiac_mode == SIDEREAL` (default), `longitude_tropical` otherwise. The
  chosen value is stored as `longitude_used`; both raw longitudes are always
  present.
- **Rashi** (pure): `rashi = floor(lon_used / 30)` mapped to `RashiId`;
  `degree_in_rashi = lon_used mod 30`. Catalog from `rashi.py` (pinned,
  versioned): 12 signs, Mesha at 0°, classical lords
  (Mesha=Mars … Meena=Jupiter).
- **Nakshatra** (pure): 27 arcs of 13°20′ starting at 0° sidereal;
  `nakshatra = floor(lon_used / (360/27))`; `degree_in_nakshatra = lon_used
  mod 13°20′`. Catalog from `nakshatra.py`: all 27 names, classical rulers
  (Ashwini=Ketu … Revati=Mercury), four pada boundaries each of 3°20′
  (pad(a) = `floor(degree_in_nakshatra / 3°20′) + 1`). Full catalog — never
  a subset of examples.
- **DMS** (`dms.py`): deterministic conversion with explicit rounding policy
  (round-half-even at `coordinate_precision` decimal seconds); DMS is
  presentational and never feeds calculations.
- **Retrograde/direct/stationary**: passthrough of JRE-002's
  `BodyPosition.retrograde` (speed sign vs `station_speed_epsilon`).
- **Metadata**: provider_id + ephemeris_version passthrough on every
  `PlanetState`.

## 8. Planet-to-planet geometry (B, ADR-004)

For every unordered pair of requested bodies (`C(n,2)`, n ≤ 9 → ≤ 36 pairs):

- **Absolute angular separation** (great-circle on the ecliptic sphere,
  including latitude):
  `sep = acos(sin β1 sin β2 + cos β1 cos β2 cos(λ1 − λ2))` in `[0, 180]`.
- **Normalized separation** (ecliptic arc mod 360): `(λ2 − λ1) mod 360` in
  `[0, 360)`.
- **Same-Rashi**: `floor(λ1/30) == floor(λ2/30)` on `longitude_used`.
- **Same-Bhava**: only when a chart is supplied; computed against the natal
  bhavas in `longitude_used` frame; `None` in generic mode.
- **Conjunction**: `separation ≤ conjunction_orb_deg` — defined by **exact
  angular distance**, never by house/rashi equality alone. The exact
  distance is preserved (`conjunction_distance_deg`).
- **Aspects** (exact-degree kinds with per-kind orbs): a pair is checked
  against each `AspectKind` ideal angle; `distance_from_exact_deg` is the
  exact distance from the ideal, `within_orb` records the orb decision, and
  the orb used is explicit.
- **Applying/separating**: sign of the time-derivative of the separation,
  computed deterministically from the two bodies' `speed_longitude`:
  separation decreasing → APPLYING; increasing → SEPARATING. `NONE` when
  undetermined (e.g. exact aspect).
- Classical sign-based drishti rule tables (5th/7th/9th etc.) are **not**
  computed here — they are rules for the future Rules layer operating on
  these exact-angular facts (ADR-004).

## 9. Bhava relationships (C)

- **House cusps**: from `HouseCuspProvider` (ADR-002). For cusp-based systems
  (EQUAL, PLACIDUS, KOCH, REGIOMONTANUS, CAMPANUS) cusps come from the
  provider. For **WHOLE_SIGN** (Jyotish default) bhavas are derived purely
  from the ascendant: house 1 = the sign containing the ascendant, house n =
  the next sign. (Caveat for the Specialist: Swiss Ephemeris's `'W'` cusps
  are sign boundaries, NOT ascendant-anchored whole-sign bhavas — verify and
  derive whole-sign in pure code.)
- **Per bhava**: house number, boundary (start/end in `longitude_used`
  frame), Rashi, house lord (ruler of that Rashi from the pinned catalog),
  occupants (bodies whose `longitude_used` falls in the span), their
  `PlanetState`s, aspects to occupants, and the cusp's Nakshatra where
  applicable.
- **Explicit systems, never mixed**: the house system used is a `JyotishConfig`
  field and is echoed on every chart; results from different systems are
  never combined (ADR-002).

## 10. Lagna (D)

- Ascendant longitude from the house-cusp provider (`ascmc[0]`,
  `FLG_SIDEREAL` when `zodiac_mode == SIDEREAL`), converted to the
  `longitude_used` frame and normalized to `[0, 360)`.
- `LagnaState` carries the full classification: Rashi, exact degree,
  Nakshatra, Nakshatra lord, Pada, degree in Nakshatra, DMS, and the
  Bhava-1 binding (whole-sign: the lagna sign; cusp systems: cusp-1).
- In individual mode, the lagna anchors the house numbering used by
  `TransitThroughHouses` when `reference == LAGNA` (default for Kundali).

## 11. Continuous transit model (E, ADR-005)

The system never represents a transit as a bare bucket ("Jupiter =
Sagittarius"). The primary object is the continuous `PlanetState`; buckets
are derived. `ContinuousTransitEngine` answers:

- **Position at instant**: `position_at(jd) -> PlanetState` (one astronomy
  compute, memoized).
- **Rashi/Nakshatra/Pada ingress & egress**: when did the body's
  `longitude_used` cross each boundary?
- **Station**: when did speed change sign (station-retrograde /
  station-direct)?
- **Exact degree at an instant**: `position_at`.
- **Interval state**: `events_between(start_jd, end_jd, kinds, bodies) ->
  tuple[TransitEvent, ...]` and/or sampled `PlanetState` series.

Search algorithm (deterministic, ADR-005):

1. Sample `f(t) = longitude_used(t) − boundary` (or speed) at a fixed step
   (default 6 h, configurable, versioned).
2. Find sign changes → isolate monotonic segments; handle **retrograde
   re-crossings** (a body may enter, leave, and re-enter the same sign in one
   interval — every sign change is an event).
3. Bisect each segment to `tolerance_jd` (default 1e-4 days ≈ 8.6 s,
   versioned).
4. Determinism: fixed step, fixed tolerance, fixed iteration cap, no wall
   clock; `SearchMetadata` echoes the exact parameters on every event.

**Memoization** (justified per JRE-002 spec §30's documented revisit
condition — JRE-003 is exactly the "consumer that batches many instants"):
a process-scoped cache keyed by the exact `(julian_day_ut, bodies,
CalculationConfig)` tuple; pure-memo of a pure function, so determinism is
unaffected. Cache is a versioned decision (ADR-005).

## 12. Transit through houses (F)

Individual mode: for a transit instant against a natal chart:

- For each transiting planet: its current `PlanetState` (continuous) → natal
  house traversed (`natal_house_number`), natal house lord, natal occupants,
  and geometric `AspectRelationship`s to natal planets.
- **Reference points** are explicit and distinct:
  - `LAGNA` (default for Kundali): natal house numbering anchored on the
    natal lagna sign.
  - `MOON`: numbering anchored on the natal Moon's sign (chandra lagna).
  - `SUN`: anchored on the natal Sun's sign (surya lagna).
  - `ASC`: cusp-based numbering from the natal ascendant cusp (non-whole-sign
    systems).
  - Extensible via `TransitReferencePoint`.
- The three interpretations of the same transit fact (relative to Lagna /
  Moon / Sun) are distinct outputs; nothing is "interpreted".

## 13. Nakshatra model (G)

`nakshatra.py` is a complete, pinned, versioned catalog of all 27
Nakshatras — deterministic data + pure functions:

- **name** (canonical romanization, e.g. `ASHWINI` … `REVATI`), **start** and
  **end** longitude (13°20′ arcs from 0° sidereal), **ruler** (classical
  nakshatra lord cycle of 9), **four pada boundaries** (each 3°20′), **pada
  mapping** (`floor(deg_in_nak / 3°20′) + 1`), and **exact longitude
  math** (`start + k*13°20′`).
- The catalog is sourced from a documented classical reference (specialist to
  pin the citation and romanization scheme), checksummed if stored as a data
  file, and versioned like ephemeris data — any change is a versioned
  decision (ADR-003).

## 14. Eclipse engine interface (H, ADR-006)

- **Interface**: `EclipseProvider.find_eclipses(jd_start, jd_end, kind,
  config)` returning deterministic `EclipseEvent`s. Data only.
- **Initial provider** (`jyotish/swisseph/eclipse.py`): the pinned binding
  exposes `sol_eclipse_when_glob`, `sol_eclipse_where`, `lun_eclipse_when`,
  `sol_eclipse_how`, `lun_eclipse_how` — but NOT the `SEFLG_ECL_*` named
  constants; the documented raw values (e.g. `0x8000` LIGHT, `0x10000`
  CENTRAL, `0x20000` PENUMBRA) are defined once in
  `jyotish/swisseph/constants.py` with their C-header citation
  (empirically verified working with the pinned binding v2.10.03).
- **Outputs**: contact/maximum/end times where available, eclipse geometry
  (magnitude), astronomical classification (total/partial/annular/hybrid/
  penumbral), geographic visibility where available, associated Sun/Moon and
  node positions at maximum, and pre/post event intervals **as data** — never
  as causation ("an eclipse causes X" is forbidden).
- **Determinism**: same interval + config → identical events and times;
  binding-level determinism is already guaranteed by ADR-001 (pinned
  ephemeris, no network).
- **Validation**: independent comparison against the NASA Five Millennium
  Canon of Eclipses (times + classification), TEST-PLAN §12.

## 15. Separation of concerns (I)

`jyotish` outputs machine-readable facts. Forbidden anywhere in
`src/jyotish` identifiers, enums, fields, or logic:

- benefic/malefic, auspicious/inauspicious, good/bad
- prediction, fortune, wealth, marriage, career, health, spiritual outcome
- Yoga (as interpretation), Dasha, Gochar interpretation, Nakshatra
  interpretation, Muhurta
- sign-based drishti rule tables (future Rules layer)

Enforcement: static test on `src/jyotish` identifiers + public-surface test
+ code-review gate (TEST-PLAN §8).

## 16. Configuration (J)

`config/jyotish.toml` declares every default; `JyotishConfig` is immutable
and echoed in every result. No default for a materially significant choice is
implicit. The full set: zodiac mode, ayanamsa, house system, node model,
ephemeris provider + version, timezone (presentation), coordinate precision,
conjunction orb, per-aspect orbs, station epsilon, transit search
step/tolerance. See DATA-CONTRACT §2.

## 17. Reproducibility (K)

Identical `(birth/transit input, timestamp, location, JyotishConfig,
ephemeris version, catalog version)` ⇒ bit-identical output. Enforced by:

1. Pinned catalogs + checksums (ADR-003); pinned astronomy + binding
   versions (ADR-001).
2. Frozen dataclasses; config + `SearchMetadata` echoed everywhere.
3. Fixed search algorithm parameters (ADR-005); no clocks/random/network.
4. Memoization is a pure memo of a pure function (ADR-005).
5. Cross-process determinism test (TEST-PLAN §4).

## 18. Generic vs individual data (L)

- **Generic**: `JyotishService.planetary_state(instant, bodies, config)` →
  `PlanetState` set (optionally `PairGeometry`). No birth data anywhere.
- **Individual**: `JyotishService.chart(birth: BirthData, config)` →
  `NatalChart`; `JyotishService.transit_through_houses(birth, instant,
  reference, config)` → `TransitThroughHouses`.
- `BirthData` (date, time, timezone, latitude, longitude) is **request input
  only**. It is echoed as `birth_snapshot` for audit, never stored by the
  engine, never written to any persistent store, never embedded in code or
  fixtures. Both modes run through the same core functions.

## 19. Future extensibility (M)

Future modules — Vargas (D-1/D-2/…/D-60 division), Drishti rules, Dasha,
Yoga, Gochar interpretation, Nakshatra interpretation, multi-layer synthesis,
prediction/confidence — consume JRE-003's public surface:

- Varga division needs `longitude_used` + pada boundaries (available).
- Drishti needs `PairGeometry` exact angles (available).
- Dasha needs Moon's Nakshatra + exact degree (available).
- Interpretation layers need `PlanetState` + `TransitEvent` + `NatalChart`
  (available).

Adding them requires no change to `jyotish` internals — the public
allow-list, config, and data contracts are the contract.

## 20. Testability (N)

Full matrix in [JRE-003-TEST-PLAN.md](JRE-003-TEST-PLAN.md). Highlights:

- Rashi/Nakshatra/Pada **boundary** cases (0°/30°, 0°/13°20′, pada edges).
- Exact conjunction, near-conjunction (inside/outside orb), same-house but
  wide-degree (must NOT be conjunct).
- Retrograde motion and station points (event search around real stations).
- Transit ingress/egress incl. retrograde re-crossings; timezone-boundary
  instants.
- Lagna + house transitions; whole-sign vs cusp-system consistency.
- Eclipse events vs NASA catalog; determinism in-process + cross-process.
- Independent validation of classifications and geometry against published
  references (VALIDATOR).

## 21. Error taxonomy

| Error | Raised when |
|---|---|
| `JyotishError` | base class |
| `InvalidBirthDataError` | birth data malformed/out of range (validated at service boundary) |
| `UnsupportedHouseSystemError` | `house_system` not registered with any provider |
| `UnsupportedReferencePointError` | `TransitReferencePoint` unknown |
| `InvalidOrbError` | orb values non-positive / aspect kind unknown |
| `TransitSearchError` | event search fails to converge within iteration cap |
| `EclipseError` | eclipse provider failure (binding/data) |
| `ProviderCompatibilityError` | astronomy provider metadata mismatches `ephemeris_version` pin |

All errors expose the offending value in `__str__`; the service never
swallows a provider error into a fact.

## 22. Runtime and packaging requirements

- Python 3.12; target host 2 cores / 4 GB RAM (unchanged).
- New runtime dependency: **none**. JRE-003 uses `astronomy` (pinned
  `pysweph==2.10.3.6`, `tzdata`) and stdlib only.
- `pyproject.toml` gains `jyotish` + `jyotish.swisseph` packages and
  `tests/unit/jyotish`, `tests/integration/jyotish` testpaths at CODING time.
- Performance budget: single `PlanetState` set ≤ 10 ms; event search ≤ 200
  calls / event with memoization; eclipse search ≤ 5 s for a 1-year window
  (informational, not a hard gate).

## 23. Validation strategy (VALIDATOR)

- Independent references, committed as `datasets/validation/jyotish/`:
  - Published rashi/nakshatra/pada boundary tables (e.g. Indian
    Astronomical Ephemeris Lahiri positions) for classification.
  - Published example charts with computed lagna/bhava values.
  - NASA Five Millennium Canon of Eclipses for eclipse times/classification.
  - Published ingress/egress/station times from ephemerides/panchangas.
- The harness computes through `JyotishService` and asserts within a
  documented tolerance budget fixed by the Architect against the first batch
  (same policy as JRE-002 §13).
- Eclipse tolerance example: contact times within ±60 s, classification
  exact; classification boundaries within ±0.05°.

## 24. Downstream handoff checklist (SPECIALIST)

- [ ] `models.py` exactly per DATA-CONTRACT v0.2.0 (or refined v0.3.0)
- [ ] Pinned rashi/nakshatra catalogs with citation + checksums (ADR-003)
- [ ] `dms.py`, `position.py` (classification), `geometry.py` (ADR-004)
- [ ] `HouseCuspProvider` protocol + swisseph adapter + whole-sign pure
      derivation (ADR-002); registry
- [ ] `EclipseProvider` protocol + swisseph adapter with documented raw
      `SEFLG_ECL_*` constants (ADR-006)
- [ ] `ContinuousTransitEngine` with memoization (ADR-005)
- [ ] `JyotishService` generic + individual entry points; `BirthData` never
      persisted
- [ ] `config/jyotish.toml` (every default explicit)
- [ ] Error taxonomy §21; serialization per DATA-CONTRACT §8–§9
- [ ] Static gates: public surface, no interpretation vocabulary, no
      forbidden imports (TEST-PLAN §8)
- [ ] Tests per TEST-PLAN matrix; independent validation dataset scaffold
- [ ] No modification of `src/astronomy` (JRE-002 untouched)

## 25. Unresolved questions (for Specialist / Architect)

1. **Nakshatra romanization** — canonical scheme (IAST vs common) and the
   exact classical source for names/rulers; to be pinned by the Specialist
   with a citation (ADR-003).
2. **Default orbs** — `conjunction_orb_deg=8.0` and the per-aspect orb table
   are proposed defaults; the Specialist should confirm against Jyotish
   convention and record as versioned config (ADR-004).
3. **Eclipse search horizon** — `find_eclipses` interval bounds and the
   default provider's behavior outside the ephemeris coverage range; also
   whether `sol_eclipse_where` geographic output is included in the initial
   CODING scope or deferred (ADR-006).
4. **Sidereal house cusps** — `houses_ex(..., FLG_SIDEREAL)` uses the
   configured ayanamsa; the Specialist must verify cusp consistency with
   JRE-002 sidereal positions and record the flag policy.
5. **Timezone presentation** — event times are UTC facts; confirm the
   `timezone` config field's scope (presentation only) with the Gochar/Kundali
   consumer contracts.
6. **Memoization lifetime** — process-scoped cache TTL/eviction policy
   (bounded size) to be specified at CODING time without affecting
   determinism (ADR-005).

## 26. Change history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | — | Original JRE-003 request |
| 0.2.0 | 2026-08-12 | Architecture + refined specification (this document) |
