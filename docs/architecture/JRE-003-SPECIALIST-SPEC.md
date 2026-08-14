# JRE-003 — Jyotish Coordinate and State Layer: Specialist Implementation Specification

- Status: SPECIALIZED
- Version: 0.3.0 (supersedes the design-level detail of the architecture doc v0.2.0)
- Date: 2026-08-12
- Author: Jyotish Specialist
- Upstream: [JRE-003 Architecture v0.2.0](JRE-003-JYOTISH-CORE.md),
  [ADR-002](../decisions/ADR-002-HOUSE-ECLIPSE-ADAPTER-PLACEMENT.md),
  [ADR-003](../decisions/ADR-003-ZODIAC-MODE-CATALOG-VERSIONING.md),
  [ADR-004](../decisions/ADR-004-CONJUNCTION-ASPECT-SEMANTICS.md),
  [ADR-005](../decisions/ADR-005-CONTINUOUS-TRANSIT-ENGINE.md),
  [ADR-006](../decisions/ADR-006-ECLIPSE-ENGINE-INTERFACE.md),
  [JSP-001 Core Specification](../../specifications/core/JSP-001.md)

This is the **implementable** specification for the Jyotish coordinate and
state layer. Where it conflicts with the architecture document, this document
wins (both are versioned; changes are recorded in §31). It is the contract for
CODING, QA and VALIDATOR.

> **Supersession notice (read first):**
> 1. **The binding exposes named `ECL_*` constants and a separate
>    `ecltype` parameter** (empirically verified with pysweph 2.10.03: the
>    `swisseph` module has `ECL_CENTRAL`, `ECL_TOTAL`, `ECL_ALLTYPES_SOLAR`,
>    etc.). ADR-006's assumption that raw C `SEFLG_ECL_*` values are required
>    is **superseded**: the adapter uses the named constants (with the raw
>    values recorded in `constants.py` for reference only). See §22.
> 2. **`swe.houses(..., 'W')` IS ascendant-anchored whole-sign** in the
>    pinned binding: cusp₁ is the start of the sign containing the ascendant
>    (verified at two latitudes). The architecture §9 caveat is superseded;
>    whole-sign bhavas are still derived in **pure code** (§13.2), and a test
>    asserts the pure derivation equals the binding's `'W'` cusps.
> 3. **Sidereal house cusps differ from `tropical − ayanamsa` by ≈ 13″**
>    (verified: asc 119.53192587° via `FLG_SIDEREAL` vs 119.53549237° via
>    tropical−ayanamsa). The frame rotation does **not** commute with the
>    spherical house computation. Lagna/cusps MUST use `houses_ex` with
>    `FLG_SIDEREAL` in sidereal mode (§13.3). This resolves architecture §25.4.
> 4. **`JyotishConfig` gains `position_type`** (passthrough to astronomy) so
>    the "no hidden defaults" rule (requirement J) covers apparent-vs-true —
>    the architecture's field list omitted it.
> 5. **`TransitThroughHouses` carries a `birth_snapshot` echo** (mirrors
>    `NatalChart`; requirement L's audit rule).

## 1. Python package architecture

- **Python**: 3.12 only (target host: Linux, 2 cores, ~4 GB RAM).
- **Layout**: src-layout, same `pyproject.toml` as JRE-002. JRE-003 adds the
  `jyotish` and `jyotish.swisseph` packages and the
  `tests/{unit,integration,validation}/jyotish` testpaths at CODING time
  (build metadata only — no JRE-002 code changes).
- **Import name**: `jyotish`. A `jre.` namespace root remains a later,
  separately-versioned refactor (unchanged from JRE-002).
- **Public surface**: `jyotish/__init__.py` exports ONLY
  `JyotishService`, the models/enums from DATA-CONTRACT §1–§9, the registries
  and protocols (`HouseCuspProvider`, `EclipseProvider`,
  `get_house_provider`, `get_eclipse_provider`), and the public errors. An
  explicit `__all__` enforces this (tested).
- **Versioning**: `jyotish.__version__` == spec version `0.3.0`. Catalog
  versions are separate constants (`RASHI_CATALOG_VERSION`,
  `NAKSHATRA_CATALOG_VERSION`, both `"1.0.0"` initially) — see §7.
- **Imports**: `jyotish` imports from `astronomy`'s **public API only**
  (`AstronomicalService`, `EphemerisResult`, `BodyPosition`, `BodyId`,
  `CalculationConfig`, `Ayanamsa`, `NodeType`, `PositionType`,
  `EphemerisMode`, `RetrogradeState`, `ProviderMetadata`, errors,
  serializers). It never imports `astronomy.swisseph`. The `swisseph`
  binding may be imported only from `jyotish/swisseph/*` (enforced by a
  static test). No `jyotish` module imports `astrology`, `knowledge`,
  `transits`, `dasha`, `calculations`, `rules`, or `inference`.

## 2. Module boundaries

Every file, one responsibility, no cycles:

| File | Responsibility | Imports (allowed) |
|---|---|---|
| `src/jyotish/__init__.py` | Public API allow-list | its own modules only |
| `src/jyotish/models.py` | All dataclasses + enums. **Pure data; stdlib only** | stdlib |
| `src/jyotish/errors.py` | `JyotishError` hierarchy | — |
| `src/jyotish/rashi.py` | Rashi catalog (12): names, boundaries, lords, version | stdlib |
| `src/jyotish/nakshatra.py` | Nakshatra catalog (27): names, rulers, 4 pada boundaries, version | stdlib |
| `src/jyotish/dms.py` | Degrees → DMS (round-half-even policy) | `models` |
| `src/jyotish/position.py` | `BodyPosition` → `PlanetState` derivation (classification) | `models`, `rashi`, `nakshatra`, `dms`, astronomy models |
| `src/jyotish/geometry.py` | PairGeometry: separation, conjunction, aspects, applying/separating | `models`, `nakshatra`, `rashi`, astronomy models |
| `src/jyotish/houses.py` | `HouseCuspProvider` protocol + registry + **pure whole-sign derivation** | `models`, `rashi`, `nakshatra`, `errors` |
| `src/jyotish/lagna.py` | `LagnaState` derivation from ascendant longitude | `position`, `models` |
| `src/jyotish/transit.py` | `ContinuousTransitEngine` (event search + memo) | `position`, `models`, `errors` |
| `src/jyotish/eclipse.py` | `EclipseProvider` protocol + registry | `models`, `errors` |
| `src/jyotish/config.py` | `config/jyotish.toml` → `JyotishConfig` | stdlib `tomllib`, `models` |
| `src/jyotish/serialize.py` | `result_to_json` / `from_dict` per DATA-CONTRACT §12 | `models` |
| `src/jyotish/service.py` | `JyotishService` facade (generic + individual) | everything above |
| `src/jyotish/swisseph/__init__.py` | `get_house_provider()`, `get_eclipse_provider()` factories | adapter modules |
| `src/jyotish/swisseph/constants.py` | hsys codes, `ECL_*` named constants (raw values for reference), `_JULDAY`-style helpers if needed | `swisseph` binding only |
| `src/jyotish/swisseph/houses.py` | `SwissEphemerisHouseCuspProvider` | constants, models, houses protocol |
| `src/jyotish/swisseph/eclipse.py` | `SwissEphemerisEclipseProvider` | constants, models, eclipse protocol, astronomy public API |

Rules:

- Import direction is one-way: `service → everything`; adapters are reached
  only through registries; `jyotish` core never imports `jyotish.swisseph`.
- `models.py`, `rashi.py`, `nakshatra.py`, `dms.py` must not import
  `astronomy` (they are pure); `position.py`/`geometry.py` import astronomy
  models only for `BodyId`/`RetrogradeState` reuse (allowed).
- The `swisseph` binding may be referenced **only** from the three
  `jyotish/swisseph/*` modules (static test).

## 3. Provider abstraction

### 3.1 House cusps

```python
class HouseCuspProvider(Protocol):
    provider_id: str
    metadata: HouseProviderMetadata

    def compute_cusps(self, jd_ut: float, latitude: float, longitude: float,
                      house_system: HouseSystem, config: JyotishConfig
                      ) -> HouseCuspResult: ...
```

- `HouseCuspResult` = `(cusps: tuple[float, ...], ascendant_deg: float,
  mc_deg: float)` in the `longitude_used` frame (`[0, 360)`), per
  DATA-CONTRACT §7.
- **WHOLE_SIGN is NOT handled by the adapter** — it is a pure derivation in
  `houses.py` (§13.2). The adapter handles `EQUAL, PLACIDUS, KOCH,
  REGIOMONTANUS, CAMPANUS`.
- `HouseProviderMetadata` = `(provider_id, library_name, library_version,
  ephemeris_version)` — same shape as astronomy's `ProviderMetadata`.
- `HouseCuspRegistry`: `register(provider)`, `get(provider_id)`,
  `get_for(house_system) -> HouseCuspProvider | None` (returns the pure
  whole-sign provider for `WHOLE_SIGN`, else the registered cusp provider).
  Frozen after first use (same discipline as astronomy's registry).

### 3.2 Eclipses

```python
class EclipseProvider(Protocol):
    provider_id: str
    def find_eclipses(self, jd_start: float, jd_end: float,
                      kind: EclipseKind | None,
                      config: JyotishConfig) -> tuple[EclipseEvent, ...]: ...
```

- `kind=None` searches both solar and lunar (each with its own `ecltype`;
  results merged, sorted by `maximum_jd_ut`).
- Deterministic: identical interval + config ⇒ identical events and times.

## 4. Swiss Ephemeris adapter boundary

### 4.1 Houses adapter (`jyotish/swisseph/houses.py`)

1. **Frame flag**: `swe.FLG_SWIEPH` for tropical mode; `swe.FLG_SWIEPH |
   swe.FLG_SIDEREAL` when `config.zodiac_mode == SIDEREAL` (§13.3).
2. **Ayanamsa**: when sidereal, `swe.set_sid_mode(<sid_mode>, 0.0, 0.0)`
   from `config.ayanamsa` (LAHIRI→`SIDM_LAHIRI`, RAMAN→`SIDM_RAMAN`,
   FAGAN_BRADLEY→`SIDM_FAGAN_BRADLEY`) **before** every `houses_ex` call;
   then the returned cusps/asc are already in the sidereal frame. The ayanamsa
   value applied is read via `swe.get_ayanamsa_ut(jd_ut)` and returned in
   `HouseCuspResult.ayanamsa_value` (echo).
3. **hsys codes** (in `constants.py`, no magic elsewhere):
   `EQUAL→b'E'`, `PLACIDUS→b'P'`, `KOCH→b'K'`, `REGIOMONTANUS→b'R'`,
   `CAMPANUS→b'C'`. `'W'` is never requested from the binding (pure code).
4. **Call**: `cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, hsys, flags)`.
   `cusps` is a 13-tuple with `cusps[0] == 0.0` (unused); **cusps[1..12] are
   the house cusps**; `ascmc[0]` is the ascendant and `ascmc[1]` the MC
   (verified empirically). Normalize every value to `[0, 360)`.
5. **Whole-sign**: never calls the binding; see §13.2.
6. **Global state discipline**: every `swe.set_*` is executed from the
   immutable config on every call under the module `threading.Lock` (the
   binding keeps process-global state — same pattern as JRE-002 §4.8).

### 4.2 Eclipse adapter (`jyotish/swisseph/eclipse.py`)

Empirically verified binding surface (pysweph 2.10.03) — this supersedes
ADR-006's "raw constants required" premise:

| Function | Signature | Return |
|---|---|---|
| `sol_eclipse_when_glob` | `(tjdut, flags=FLG_SWIEPH, ecltype=0, backwards=False)` | `(res, tret)` — `res` bitflags; `tret` tuple of 10 floats |
| `sol_eclipse_how` | `(tjdut, geopos, flags)` | `(retflags, attr)` |
| `sol_eclipse_where` | `(tjdut, flags)` | `(retflags, geopos, attr)` |
| `lun_eclipse_when` | `(tjdut, flags=FLG_SWIEPH, ecltype=0, backwards=False)` | `(retflag, tret)` |
| `lun_eclipse_how` | `(tjdut, geopos, flags)` | `(retflag, attr)` |

Named constants in `constants.py` (all exist on the binding; raw hex values
recorded beside them for reference):
`ECL_CENTRAL=1, ECL_NONCENTRAL=2, ECL_TOTAL=4, ECL_ANNULAR=8,
ECL_PARTIAL=16, ECL_ANNULAR_TOTAL=32, ECL_PENUMBRAL=64,
ECL_ALLTYPES_SOLAR=63, ECL_ALLTYPES_LUNAR=84`.

**Solar `tret` layout** (verified against the 1991-07-11 total solar eclipse;
matches NASA canon):
`tret[0]` = maximum; `tret[1]` = eclipse at local apparent noon;
`tret[2]` = P1 (partial begin); `tret[3]` = P4 (partial end);
`tret[4]` = P2/U2 (totality begin); `tret[5]` = P3/U3 (totality end);
`tret[6]` = center-line begin; `tret[7]` = center-line end.

**Lunar `tret` layout** (verified against the 1990-02-09 total lunar eclipse;
matches NASA canon):
`tret[0]` = maximum; `tret[2]` = P1 (partial begin); `tret[3]` = P4 (partial
end); `tret[4]` = U2 (umbral begin); `tret[5]` = U3 (umbral end);
`tret[6]` = penumbral begin; `tret[7]` = penumbral end. `tret[1]` unused.

**Classification** (from `res`/`retflag` bits): solar — `ANNULAR_TOTAL`→
`HYBRID`, else `TOTAL` (bit 4), `ANNULAR` (bit 8), `PARTIAL` (bit 16);
lunar — `TOTAL` (bit 4), `PARTIAL` (bit 16), `PENUMBRAL` (bit 64). `res==0`
⇒ no eclipse found.

**Magnitude**: solar → `sol_eclipse_where` `attr[0]` (fraction of solar
diameter covered, = NASA magnitude per binding docs); lunar →
`lun_eclipse_how` `attr[0]` (umbral magnitude; verified 1.0749 for
1990-02-09, matching NASA's 1.075). Geopos for `*_how`/`*_where` is
`(0.0, 0.0, 0.0)` (global search — the functions accept any location).

**Geographic visibility**: solar only — `sol_eclipse_where` returns a
`geopos` 10-tuple: `[0]`=central-line longitude, `[1]`=central-line latitude
(verified: 1991-07-11 central point ≈ -105.2°, 22.0°); populate
`GeographicVisibility(central path)`. Lunar → `None`.

**Search loop** (deterministic): `jd = jd_start`; repeatedly call
`when_glob(jd, FLG_SWIEPH, ecltype, False)`; stop when `res == 0` or
`tret[0] > jd_end`; else record the event at `tret[0]`, set
`jd = tret[0] + 0.5` days (move past this event), and continue. For
`kind=None`, run both solar and lunar passes with their own `ecltype`
(`ECL_ALLTYPES_SOLAR` / `ECL_ALLTYPES_LUNAR`) and merge by time.

**Contact selection**: solar — `P1=tret[2]`, `P2=tret[4]` (present only for
central events; else omitted), `MAX=tret[0]`, `P3=tret[5]` (central only),
`P4=tret[3]`. Lunar — `P1=tret[2]`, `U2=tret[4]` (total only), `MAX=tret[0]`,
`U3=tret[5]` (total only), `P4=tret[3]`; penumbral begin/end `tret[6]/[7]`
carried as `phase="PENUMBRAL_BEGIN"/"PENUMBRAL_END"` when nonzero.
Ordering asserted by tests: P1 ≤ P2 ≤ MAX ≤ P3 ≤ P4.

**pre/post intervals**: solar — `pre = MAX − P1`, `post = P4 − MAX` (or from
the first/last available contact). Lunar — `pre = MAX − penumbral_begin`,
`post = penumbral_end − MAX` (falling back to P1/P4 if penumbral times are
zero). These are **data** describing the event's temporal extent — no
significance is implied (ADR-006).

**Node and Sun/Moon positions at maximum**: computed by calling
`JyotishService`'s position path at `tret[0]` for `RAHU`/`KETU` and
`SUN`/`MOON` with the same config (reuses JRE-002 astronomy — no duplicate
math). Positions are sidereal/tropical per `zodiac_mode`.

## 5. Sidereal coordinates: precision, ayanamsa, normalization, rounding

1. **Internal precision**: IEEE-754 doubles (Python `float`). **No rounding
   or truncation at any computation boundary.** Planetary longitudes are used
   exactly as returned by JRE-002 (which guarantees `longitude_sidereal =
   normalize(longitude_tropical − ayanamsa_value)`; JRE-002 §12).
2. **Ayanamsa application**: entirely delegated to JRE-002 (the astronomy
   core sets the sid mode, computes the ayanamsa value per instant, and
   derives the sidereal longitude). JRE-003 never re-derives ayanamsa. The
   ayanamsa value is **not** recomputed here; `PlanetState` does not carry it
   (it is on `BodyPosition.ayanamsa_value`, echoed in the config snapshot).
3. **`longitude_used`**: `longitude_sidereal` when
   `zodiac_mode == SIDEREAL`, else `longitude_tropical`. Both raw longitudes
   are always present on `PlanetState`. `zodiac_mode=SIDEREAL` with
   `ayanamsa=None` is rejected at the service boundary (`JyotishError`):
   the sidereal frame must always be computable (ADR-003).
4. **Normalization**: all longitudes normalized to `[0, 360)` via
   `lon % 360`, with `-0.0 → 0.0`. Boundary `360° ≡ 0°`.
5. **Rounding policy**: rounding exists in exactly one place — DMS display
   (`dms.py`, round-half-even at `coordinate_precision`). **DMS never feeds
   classification or geometry.** Classification uses the unrounded double.
6. **Classification boundary handling**: `rashi = floor(lon/30)`,
   `nakshatra = floor(lon/(360/27))`, `pada = floor(deg_in_nak/(360/108))`.
   A longitude **exactly at a boundary** (e.g. 0.0, 30.0, 13°20′) belongs to
   the **higher-index** bucket (floor semantics) — so `0.0 → MESHA` (index
   0), `30.0 → VRISHABHA` (index 1), `13°20′ → BHARANI`. This is
   deterministic and documented; tests pin every boundary (§10 TEST-PLAN).

## 6. Rashi model (12)

Pure data in `rashi.py`:

| Index | RashiId | Span (deg) | Lord (BodyId) |
|---|---|---|---|
| 0 | MESHA | 0 – 30 | MARS |
| 1 | VRISHABHA | 30 – 60 | VENUS |
| 2 | MITHUNA | 60 – 90 | MERCURY |
| 3 | KARKA | 90 – 120 | MOON |
| 4 | SIMHA | 120 – 150 | SUN |
| 5 | KANYA | 150 – 180 | MERCURY |
| 6 | TULA | 180 – 210 | VENUS |
| 7 | VRISHCHIKA | 210 – 240 | MARS |
| 8 | DHANUSHA | 240 – 270 | JUPITER |
| 9 | MAKARA | 270 – 300 | SATURN |
| 10 | KUMBHA | 300 – 330 | SATURN |
| 11 | MEENA | 330 – 360 | JUPITER |

- Span = `[index*30, (index+1)*30)` — **exact 30° arcs**, derived from the
  index, never hard-coded per-sign (ADR-003: boundaries from arc constants).
- Lords: classical Parasari assignment (Brihat Parashara Hora Shastra ch. 4;
  Varahamihira's Brihat Jataka ch. 1 for the same scheme) — documented in the
  module docstring as `RASHI_SOURCE` and versioned via
  `RASHI_CATALOG_VERSION`.
- `rashi_of(lon) -> RashiId` = `RashiId(int(lon // 30))`.
- `degree_in_rashi(lon) -> float` = `lon − 30*floor(lon/30)` ∈ `[0, 30)`.
- `rashi_span(RashiId) -> (start, end)` and `lord_of(RashiId) -> BodyId`.

## 7. Nakshatra model (27)

Pure data in `nakshatra.py` — the complete catalog, never a subset:

| idx | NakshatraId | Span start (deg) | Ruler |
|---|---|---|---|
| 0 | ASHWINI | 0°00′ | KETU |
| 1 | BHARANI | 13°20′ | VENUS |
| 2 | KRITTIKA | 26°40′ | SUN |
| 3 | ROHINI | 40°00′ | MOON |
| 4 | MRIGASHIRA | 53°20′ | MARS |
| 5 | ARDRA | 66°40′ | RAHU |
| 6 | PUNARVASU | 80°00′ | JUPITER |
| 7 | PUSHYA | 93°20′ | SATURN |
| 8 | ASHLESHA | 106°40′ | MERCURY |
| 9 | MAGHA | 120°00′ | KETU |
| 10 | PURVA_PHALGUNI | 133°20′ | VENUS |
| 11 | UTTARA_PHALGUNI | 146°40′ | SUN |
| 12 | HASTA | 160°00′ | MOON |
| 13 | CHITRA | 173°20′ | MARS |
| 14 | SWATI | 186°40′ | RAHU |
| 15 | VISHAKHA | 200°00′ | JUPITER |
| 16 | ANURADHA | 213°20′ | SATURN |
| 17 | JYESHTHA | 226°40′ | MERCURY |
| 18 | MULA | 240°00′ | KETU |
| 19 | PURVA_ASHADHA | 253°20′ | VENUS |
| 20 | UTTARA_ASHADHA | 266°40′ | SUN |
| 21 | SHRAVANA | 280°00′ | MOON |
| 22 | DHANISHTHA | 293°20′ | MARS |
| 23 | SHATABHISHA | 306°40′ | RAHU |
| 24 | PURVA_BHADRAPADA | 320°00′ | JUPITER |
| 25 | UTTARA_BHADRAPADA | 333°20′ | SATURN |
| 26 | REVATI | 346°40′ | MERCURY |

- **Arc constants** (exact, derived — never per-sign hand values):
  `NAKSHATRA_ARC = 360/27` deg (13°20′); `PADA_ARC = NAKSHATRA_ARC/4`
  (3°20′). Start of nakshatra *k* = `k * NAKSHATRA_ARC`.
- **Ruler cycle**: the classical 9-planet sequence
  `KETU, VENUS, SUN, MOON, MARS, RAHU, JUPITER, SATURN, MERCURY` repeated 3
  times over the 27 — `lord(k) = CYCLE[k % 9]`. Source: the Vimshottari ruler
  order as taught in Brihat Parashara Hora Shastra ch. 46 and the classical
  nakshatra tradition; romanization scheme = common Sanskrit transliteration
  (IAST-lite: `ASHWINI`, `KRITTIKA`, `JYESHTHA`, `SHATABHISHA`,
  `PURVA_BHADRAPADA`, `UTTARA_BHADRAPADA`, …). Pinned in
  `NAKSHATRA_SOURCE` docstring; `NAKSHATRA_CATALOG_VERSION = "1.0.0"`.
- **Pada boundaries**: four padas per nakshatra, each `PADA_ARC` wide:
  pada 1 = `[start, start+3°20′)`, …, pada 4 = `[start+10°, end)`.
- **Functions**: `nakshatra_of(lon) -> NakshatraId` =
  `NakshatraId(int(lon // NAKSHATRA_ARC))`; `degree_in_nakshatra(lon) =
  lon % NAKSHATRA_ARC`; `pada_of(lon) -> Pada` =
  `Pada(int((lon % NAKSHATRA_ARC) // PADA_ARC) + 1)`;
  `lord_of(NakshatraId) -> BodyId`; `pada_span(NakshatraId, Pada) ->
  (start, end)`.

## 8. DMS representation (`dms.py`)

- `DmsValue(degrees: int, minutes: int, seconds: float, sign: int)` from an
  unrounded longitude/latitude.
- **Rounding policy**: round-half-even at `coordinate_precision` decimal
  seconds (`round(seconds, coordinate_precision)` — Python's banker's
  rounding is round-half-even). `coordinate_precision ∈ [0, 3]` (validated at
  config load; out of range → `InvalidOrbError`-family
  `InvalidConfigError`).
- **Format** (display only): `"{sign}{d}°{mm:02d}'{ss:0<width}.{p}f\""` —
  seconds padded to `coordinate_precision` decimals. E.g.
  `143°15'32.4"` at precision 1. Never feeds calculations.
- Edge: `minutes` rolls over when seconds reach 60.0 after rounding
  (`59.9997 → 60.0 → minutes+1, seconds=0.0`), and degrees roll over at 360.

## 9. Planetary state derivation (`position.py`)

`derive_planet_state(body_pos: BodyPosition, config: JyotishConfig,
timestamp_utc_iso, julian_day_ut, provider_id, ephemeris_version) ->
PlanetState`:

1. `lon_used = body_pos.longitude_sidereal if config.zodiac_mode ==
   SIDEREAL else body_pos.longitude_tropical` (validate not None for SIDEREAL
   — the service boundary already rejected `ayanamsa=None`).
2. Classify via §6/§7 pure functions **on the unrounded double**.
3. Carry `latitude`, `speed_longitude`, `retrograde` (astronomy passthrough).
4. Attach `timestamp_utc_iso`, `julian_day_ut`, `provider_id`,
   `ephemeris_version` (from the astronomy `EphemerisResult` envelope).
5. `dms` = `DmsValue.from_degrees(lon_used, config.coordinate_precision)`.

`PlanetState` fields and JSON shape: DATA-CONTRACT §4.

## 10. Planet-to-planet geometry (`geometry.py`)

For every unordered pair `(a, b)` with `a` before `b` in canonical `BodyId`
order (SUN…KETU): C(9,2) = 36 pairs.

1. **Absolute angular separation** (great-circle on the ecliptic sphere,
   latitude included; ADR-004):
   `sep = acos(sin β1·sin β2 + cos β1·cos β2·cos(λ1 − λ2))`, clamped to
   `[0, 180]`. Clamp the acos argument to `[−1, 1]` before `acos` (fp safety).
2. **Normalized separation** (ecliptic arc mod 360):
   `(λ2 − λ1) % 360 ∈ [0, 360)` on `longitude_used`.
3. **Same Rashi**: `rashi_of(λ1) == rashi_of(λ2)` on `longitude_used`.
4. **Same Bhava**: only when a natal chart is supplied (individual mode);
   computed by locating each body in the natal bhavas (§14) —
   `start ≤ lon < end` per bhava span. `None` in generic mode.
5. **Conjunction** (ADR-004): `conjunction = (sep ≤ conjunction_orb_deg)`;
   `conjunction_distance_deg = sep` (exact, always preserved). Two bodies in
   the same house 25° apart are **not** conjunct; two bodies 2° apart in
   different houses **are**.
6. **Aspects**: for each `AspectKind` with ideal angle θ and orb o from
   `config.aspect_orbs_deg`:
   `distance_from_exact = min(|sep − θ|, 360 − |sep − θ|)` (circular), and
   `within_orb = distance_from_exact ≤ o`. The full set of 7 kinds is always
   evaluated; `PairGeometry.aspects` carries all of them (complete facts —
   consumers filter `within_orb`). Data contract §5.
   Ideal angles: CONJUNCTION 0, SEMISEXTILE 30, SEXTILE 60, SQUARE 90,
   TRINE 120, QUINCUNX 150, OPPOSITION 180.
7. **Applying/separating** (deterministic, ADR-004): the rate of change of
   the **ecliptic-arc** separation drives the decision (longitude speeds are
   the only speed data). For pair `(a, b)` with longitudes λ1, λ2 and speeds
   v1, v2:
   - Signed short-way difference `δ = wrap180((λ2 − λ1) mod 360 − θ)` where
     `wrap180(x) = ((x + 180) mod 360) − 180 ∈ (−180, 180]`.
   - The separation is decreasing (APPLYING) iff
     `sign(δ) * (v2 − v1) < 0`; increasing (SEPARATING) iff `> 0`; `NONE`
     when `|v2 − v1| ≤ ε` (ε = `station_speed_epsilon`) or
     `|δ| ≈ 0` (exact aspect, within `1e-9` deg).
   - Rationale: for a fixed ideal angle, the circular distance to exactness
     changes at rate `sign(δ)·(v2−v1)` (near the ideal, δ is the signed
     offset). This is a closed-form, deterministic rule — no sampling, no
     clocks (supersedes any sampling-based alternative).
8. **Orb echo**: `orb_config = {"conjunction": orb, "aspects": {kind: orb}}`
   from config; `config_snapshot` = the full config.

## 11. Lagna (`lagna.py`)

`derive_lagna(ascendant_deg, config, provider_meta) -> LagnaState`:

1. Normalize ascendant to `[0, 360)`; classify exactly as a planet
   (rashi, degree in rashi, nakshatra, nakshatra lord, pada, degree in
   nakshatra, DMS) — reuse `position.py` helpers on the ascendant longitude
   (the ascendant is treated as a longitude point, not a body).
2. `bhava_relationship` = the `Bhava` with `house_number == 1` (supplied by
   the caller — the chart service binds it after computing bhavas).
3. `house_system` echoed from config.

## 12. House systems (`houses.py`)

### 12.1 Protocol & registry

```python
class HouseCuspProvider(Protocol):
    provider_id: str
    metadata: HouseProviderMetadata
    def compute_cusps(self, jd_ut, latitude, longitude,
                      house_system, config) -> HouseCuspResult: ...

class HouseCuspRegistry:
    def register(self, provider): ...
    def get(self, provider_id): ...            # UnsupportedHouseSystemError if absent
    def get_for(self, house_system) -> HouseCuspProvider | None
```

`HouseCuspResult`: `(cusps: tuple[float, ...]  # 12, in longitude_used frame,
[0,360); ascendant_deg: float; mc_deg: float; ayanamsa_value: float | None;
provider: HouseProviderMetadata)`.

### 12.2 WHOLE_SIGN — pure derivation (never the binding)

- House 1 = the sign containing the ascendant; house *n* = the *n*-th
  subsequent sign. Cusps = sign boundaries:
  `cusp_h = ((asc_sign_index + h − 1) mod 12) * 30` for `h = 1..12`.
- Empirically verified equal to the binding's `'W'` cusps (supersession
  notice #2); a test asserts this for a fixture set (TEST-PLAN §9).
- Sidereal whole-sign uses the **sidereal** ascendant (from the sidereal
  house computation §13.3), so cusps are sidereal sign boundaries.

### 12.3 Cusp systems (EQUAL, PLACIDUS, KOCH, REGIOMONTANUS, CAMPANUS)

- Delegated to the registered `HouseCuspProvider` (initial: swisseph
  adapter §4.1). House *h* spans `[cusp_h, cusp_{h+1})` with wrap at 360°
  (house 12 wraps through 0°). Each span is mapped to its Rashi
  (the sign of the cusp — documented convention: house = sign of its cusp;
  cusp spans that cross a sign boundary have occupants assigned by span
  containment, not by sign).
- `HouseSystem` values are explicit and never mixed: one chart uses one
  system; results from different systems are never combined (ADR-002).
- Unregistered/unknown system → `UnsupportedHouseSystemError`.

## 13. Bhava computation and sidereal cusps

### 13.1 `compute_bhavas(cusp_result, planet_states, config) -> tuple[Bhava, ...]`

For each house 1..12:
- `start_deg`, `end_deg` from cusps (whole-sign: sign boundaries; cusp
  systems: cusp spans), in the `longitude_used` frame.
- `rashi` = `rashi_of(start_deg)`; `house_lord` = `lord_of(rashi)`.
- `occupants` = bodies whose `longitude_used ∈ [start, end)` (wrap-aware:
  house 12 checks `[start,360) ∪ [0,end)`); `occupant_states` = their full
  `PlanetState`s, canonical order.
- `aspects` = aspect relationships between **each occupant and the house
  cusp point** (start_deg treated as a point) for the 7 kinds using the
  geometry engine (§10) — "cusp-based aspects where applicable". Empty when
  no occupants.
- `nakshatra` = `nakshatra_of(start_deg)` (of the cusp point).

### 13.2 Whole-sign derivation (pure, no binding)

Per §12.2. The lagna anchors house 1; all 12 bhavas follow the signs.

### 13.3 Sidereal cusp flag policy (resolution of architecture §25.4)

- **Sidereal mode**: cusps/ascendant computed with
  `swe.houses_ex(jd, lat, lon, hsys, FLG_SWIEPH | FLG_SIDEREAL)` after
  `set_sid_mode(config.ayanamsa)`. The returned values are already sidereal.
- **Tropical mode**: `swe.houses_ex(..., FLG_SWIEPH)` (no sidereal flag).
- **Do NOT derive sidereal cusps as `tropical − ayanamsa`**: empirically the
  two disagree by ≈ 13″ (supersession notice #3) because the ayanamsa
  rotation does not commute with the spherical house computation. The
  binding's `FLG_SIDEREAL` path is authoritative and matches published
  references (VALIDATOR).
- A cross-check test asserts `|sidereal_asc_FLG − (tropical_asc − ayanamsa)|
  < 0.01°` (documents the ≈13″ scale; not a bit-equality like positions).

## 14. Natal chart and transit-through-houses (individual mode)

### 14.1 `NatalChart`

Built by the service from birth data + config:
1. Compute the birth instant's astronomy result (one `AstronomicalService`
   call for all nine bodies, canonical order).
2. Compute house cusps at the birth instant (per `house_system`), then
   bhavas (§13.1) and lagna (§11).
3. `birth_snapshot` = exact echo of `BirthData` (never stored/persisted).
4. `provider_metadata` = astronomy `ProviderMetadata` + house-provider
   metadata (distinct providers, both echoed).

### 14.2 `TransitThroughHouses`

For a transit instant against a natal chart:
- For each transiting planet (canonical order), compute `HouseTransitEntry`:
  - `natal_house_number` per the explicit reference point:
    - `LAGNA` (default): house number of the natal bhava span containing the
      transit longitude (whole-sign: relative to the lagna sign).
    - `MOON` / `SUN`: house number relative to the natal Moon's / Sun's sign
      (chandra/surya lagna) — whole-sign-style relative numbering:
      `((transit_rashi_index − anchor_rashi_index) mod 12) + 1`.
    - `ASC`: cusp-based — locate the transit longitude in the natal cusp
      spans (non-whole-sign systems).
    - Any other value → `UnsupportedReferencePointError`.
  - `natal_house_lord`, `natal_occupants`, `natal_house_rashi` from that
    bhava.
  - `aspects_to_natal` = geometry of the transit body vs **each** natal
    occupant (all 7 aspect kinds, §10).
- `transit_instant_utc_iso`; `birth_snapshot` echo (supersession notice #5);
  `config` echo.
- The three interpretations (LAGNA / MOON / SUN) are distinct outputs —
  nothing is "interpreted" (requirement F).

## 15. Continuous transit engine (`transit.py`)

### 15.1 Position memoization

- Process-scoped LRU, **bounded at 10 000 entries** (ADR-005; constant in
  code, not runtime config — determinism must not depend on cache state).
- Key: exact tuple `(julian_day_ut, bodies, calculation_identity)` where
  `calculation_identity` is the hash of every config field that affects
  positions (§18). Pure memo of a pure function ⇒ determinism unaffected.
- **`SearchMetadata.position_calls`** is defined as the number of **distinct
  memo keys evaluated** by the search — a pure function of the algorithm and
  target function, identical across runs regardless of warm/cold cache
  (resolves ADR-005's "position-call count" determinism concern). The raw
  cache-hit count is never exposed.

### 15.2 Event search algorithm (ADR-005, fixed)

For a body's `longitude_used(t)` and speed `v(t)` (from `position_at`):

1. **Boundaries**: Rashi at `k·30°` (k=0..11); Nakshatra at
   `k·NAKSHATRA_ARC`; Pada at `k·PADA_ARC` (k=1..107, excluding 0).
2. **Unwrapped longitude**: `λ*(t) = λ(t) + 360·n` chosen so successive
   samples are continuous (`|λ*(t_{i+1}) − λ*(t_i)| < 180`); wrap-around at
   0°/360° is handled by unwrapping, never by losing events.
3. **Sampling**: fixed step `transit_sample_step_hours = 6.0` (config).
   For ingress/egress: `f(t) = λ*(t) − boundary`. Sign change of `f`
   between consecutive samples ⇒ event candidate (retrograde re-crossings
   each produce their own event — a body may enter, leave, re-enter a sign
   within one interval; every crossing is emitted).
4. **Stations**: `f(t) = v(t)`; sign change ⇒ station candidate.
   STATION_RETROGRADE when v goes + → −; STATION_DIRECT when − → +.
5. **Bisection**: on each isolated candidate interval, bisect to
   `transit_tolerance_jd = 1e-4` days (≈ 8.6 s), capped at 60 iterations.
   Non-convergence → `TransitSearchError` (never silent approximation).
6. **Event classification**: at the root, `λ*` determines `reached`
   (Rashi/Nakshatra/Pada) and `boundary_deg`; crossing direction
   (`λ*` increasing/decreasing) maps to INGRESS vs EGRESS; `direction` =
   the body's `RetrogradeState` at the crossing. STATION events have
   `boundary_deg=None`, `reached=None`.
7. **Determinism**: fixed step, tolerance, iteration cap; no clocks, no
   randomness; `SearchMetadata` echoes algorithm/step/tolerance/iterations/
   position_calls on every event.

### 15.3 API

- `position_at(jd_ut, bodies, config) -> tuple[PlanetState, ...]` (memoized).
- `events_between(start_jd, end_jd, bodies, kinds, config) ->
  tuple[TransitEvent, ...]` — sorted by `event_julian_day_ut`; events
  exactly at `start_jd`/`end_jd` are included (closed interval).
- `state_series(start_jd, end_jd, step_days, bodies, config) ->
  tuple[PlanetState, ...]` — for interval state snapshots.

## 16. Generic vs individual modes (service)

- **Generic**: `JyotishService.planetary_state(date, time, timezone,
  latitude, longitude, bodies=None, config=None) -> tuple[PlanetState, ...]`
  and `pair_geometry(...) -> tuple[PairGeometry, ...]`. No birth data
  anywhere.
- **Individual**: `JyotishService.chart(birth: BirthData, config=None) ->
  NatalChart`; `JyotishService.transit_through_houses(birth, transit_date,
  transit_time, transit_timezone, reference=LAGNA, config=None) ->
  TransitThroughHouses`.
- Both modes call the same `position.py`/`geometry.py`/`houses.py` core —
  one deterministic engine (requirement L).
- `BirthData` is request input only; echoed as `birth_snapshot`; never
  stored, written to disk, or embedded in fixtures (static test).

## 17. Eclipse interface & data contract

- Protocol §3.2; adapter §4.2; `EclipseEvent`/`EclipseContact`/
  `GeographicVisibility` models: DATA-CONTRACT §9.
- `JyotishService.eclipses(start_utc_iso, end_utc_iso, kind=None,
  config=None) -> tuple[EclipseEvent, ...]` — converts ISO UTC instants to
  JD via the pure JD helper (§23), delegates to the registry eclipse
  provider.
- **Data-only boundary**: no field, enum, or message implies an effect on
  wealth/health/events. `pre/post_event_interval_days` are plain numbers
  (static test).

## 18. Determinism and the calculation identity

Identical `(input, timestamp, location, timezone, ayanamsa, provider,
ephemeris version, configuration, catalog version)` ⇒ **bit-identical**
output. The **calculation identity** (what must match for identical results)
is the full `JyotishConfig` (§19) **plus** the astronomy
`CalculationConfig` passthrough fields and the catalog versions:

- `JyotishConfig` fields (all), including `position_type`,
  `conjunction_orb_deg`, `aspect_orbs_deg`, `station_speed_epsilon`,
  `transit_sample_step_hours`, `transit_tolerance_jd`, `house_system`,
  `zodiac_mode`, `ayanamsa`, `node_model`, `provider_id`,
  `ephemeris_version` pin.
- Astronomy passthrough: `ayanamsa`, `node_type`, `position_type`,
  `ephemeris_mode=SWIEPH`, `position_type` default APPARENT, fixed
  `allow_fallback=True` (bundled `.se1` files guarantee SWIEPH; the actual
  mode is echoed in astronomy's `ProviderRun`).
- **`timezone` and `coordinate_precision` are presentation-only** and do NOT
  change facts (they change local ISO echo and DMS display only). This is
  documented so consumers understand why two configs with different
  `timezone` produce identical positions.
- Catalog versions (`RASHI_CATALOG_VERSION`, `NAKSHATRA_CATALOG_VERSION`)
  are part of the identity; a change is a versioned decision (ADR-003).

Enforced by: pinned deps and `.se1` files (JRE-002), frozen dataclasses,
pure functions, fixed search parameters, no clocks/random/network, and
in-process + cross-process determinism tests (TEST-PLAN §4).

## 19. `JyotishConfig` (supersedes DATA-CONTRACT §2 field set)

| Field | Type | Default | Semantics |
|---|---|---|---|
| `zodiac_mode` | `ZodiacMode` | `SIDEREAL` | classification frame (ADR-003) |
| `ayanamsa` | `Ayanamsa \| None` | `LAHIRI` | passthrough; `None`+SIDEREAL rejected |
| `house_system` | `HouseSystem` | `WHOLE_SIGN` | never mixed (ADR-002) |
| `node_model` | `NodeType` | `MEAN` | Rahu/Ketu source |
| `position_type` | `PositionType` | `APPARENT` | **added v0.3.0**; passthrough (req. J) |
| `provider_id` | `str \| None` | `None` | astronomy provider; `None` ⇒ default |
| `ephemeris_version` | `str \| None` | `None` | optional pin; mismatch ⇒ `ProviderCompatibilityError` |
| `timezone` | `str` | `"UTC"` | presentation only |
| `coordinate_precision` | `int` | `1` | DMS seconds decimals (0–3) |
| `conjunction_orb_deg` | `float` | `8.0` | conjunction orb (ADR-004) |
| `aspect_orbs_deg` | `dict[AspectKind, float]` | table below | per-kind orbs |
| `station_speed_epsilon` | `float` | `1e-9` | matches astronomy |
| `transit_sample_step_hours` | `float` | `6.0` | event-search step |
| `transit_tolerance_jd` | `float` | `1e-4` | event-search tolerance |

Default orb table (versioned in `config/jyotish.toml`, confirmed against
common Jyotish convention; ADR-004 §Consequences):

```json
{ "CONJUNCTION": 8.0, "OPPOSITION": 8.0, "TRINE": 7.0, "SQUARE": 7.0,
  "SEXTILE": 5.0, "QUINCUNX": 4.0, "SEMISEXTILE": 2.0 }
```

- `config/jyotish.toml` declares every default (no hidden defaults, req. J);
  `JyotishConfig` is immutable and echoed in every result.
- Validation at load: orb values > 0 (`InvalidOrbError`); aspect table
  complete for all 7 kinds; `coordinate_precision ∈ [0,3]`;
  `conjunction_orb_deg` consistent with `aspect_orbs_deg["CONJUNCTION"]`
  (equal — enforced, `InvalidOrbError` if not); unknown enum values →
  `InvalidConfigError`.

## 20. Error taxonomy (`errors.py`)

| Error | Raised when |
|---|---|
| `JyotishError` | base class |
| `InvalidBirthDataError` | birth data malformed / out of range (validated at service boundary) |
| `InvalidConfigError` | config field invalid (precision range, unknown enum, etc.) |
| `InvalidOrbError` | orb values non-positive / inconsistent / kind unknown |
| `UnsupportedHouseSystemError` | `house_system` not registered with any provider |
| `UnsupportedReferencePointError` | `TransitReferencePoint` unknown |
| `TransitSearchError` | event search fails to converge within iteration cap |
| `EclipseError` | eclipse provider failure (binding/data) |
| `ProviderCompatibilityError` | astronomy/house provider metadata mismatches the `ephemeris_version` pin |

All errors expose the offending value in `__str__`. The service never
swallows a provider error into a fact; astronomy errors
(`InvalidTimestampError`, `InvalidCoordinatesError`, `UnsupportedProviderError`,
`EphemerisDataError`, `EphemerisError`) propagate unchanged.

## 21. Serialization

- `serialize.py` provides `result_to_json`/`result_to_dict` for every
  top-level result (`PlanetState` set, `PairGeometry` set, `NatalChart`,
  `TransitThroughHouses`, `TransitEvent` set, `EclipseEvent` set) plus input
  parsers (`planetary_request_from_dict`, `birth_from_dict`,
  `transit_query_from_dict`, `eclipse_query_from_dict`,
  `config_from_dict`). Input parsers validate on construction (typed errors).
- Conventions: JSON UTF-8, snake_case keys, enum → string value, `Pada` →
  number, tuple → array, `None` → `null`, floats via Python's round-trip
  repr (identical double on decode). `-0.0 → 0.0`. Round-trip tested.
- JSON Schemas: DATA-CONTRACT §11 (normative, `additionalProperties: false`).

## 22. Constants (`jyotish/swisseph/constants.py`)

- hsys bytes (§4.1) and the `ECL_*` named constants (§4.2) with raw hex
  values recorded beside each for auditability. No magic numbers in adapter
  code. Supersession: ADR-006's "raw values required" is corrected — the
  binding exposes named constants; the raw values remain documented for
  reference and for future binding changes.

## 23. Time handling

- All instant math is in **UTC** via JD (UT) floats. The service converts
  civil `(date, time, timezone)` inputs exactly as JRE-002 does (delegates to
  `AstronomicalService`, which owns local→UTC normalization, fold policy, and
  the pure JD formula; JRE-002 §8–§9).
- For transit/eclipse queries that take ISO UTC instants, `serialize.py`
  parses ISO 8601 `Z` and converts to JD with a **pure** JD formula
  (JRE-002's documented Meeus formula, §9.3 of the astronomy spec) — the
  same formula the astronomy core uses, cross-checked in tests against
  `swe.utc_to_jd` (mirrors JRE-002 §9.4). `jyotish` implements this pure
  helper in `transit.py`/`eclipse.py` callers (or a shared private helper in
  `service.py`) — **no new module**; it is not the astronomy one (which is
  internal to JRE-002).
- `timezone` in `JyotishConfig` is presentation-only (§18). Event times are
  always UTC ISO `Z`.

## 24. Performance budget (2 cores / 4 GB RAM)

- Single 9-body `PlanetState` set (incl. one astronomy call): **p95 < 10 ms**.
- Event search: **≤ 200 distinct position evaluations per event** with
  memoization (measured via `SearchMetadata.position_calls`).
- Eclipse search over a 1-year window: **< 5 s** (informational, not a gate).
- Memoization LRU bound 10 000 entries keeps RSS bounded; no multiprocessing.

## 25. Validation strategy (VALIDATOR)

Independent references (committed under `datasets/validation/jyotish/`,
offline):

| Domain | Reference | Tolerance |
|---|---|---|
| Rashi/Nakshatra/Pada classification | Published Lahiri ephemeris positions (≥ 6 dated instants) | exact sign/nakshatra/pada match; ≤ 0.001° at boundaries |
| Lagna | Published example charts with computed ascendants (≥ 3, varied latitudes) | ≤ 0.01° ascendant longitude |
| Houses | Published house tables / example charts (WHOLE_SIGN + one cusp system) | whole-sign exact; cusp ≤ 0.1° |
| Conjunction/aspect geometry | Independent spherical-math reimplementation + published conjunction lists | ≤ 1e-9 (pure math); ≤ 0.05° vs lists |
| Transit ingress/egress/station | Published ephemeris/panchanga/station data (≥ 3 per kind) | ≤ 15 min (0.0104 d) |
| Eclipse | NASA Five Millennium Canon of Eclipses (times + classification) | ≤ ±60 s; classification exact |
| Determinism | internal gate | bit-identical |

- At least one retrograde window, one node position, one sidereal-known
  date, one timezone-sensitive instant.
- The harness computes through `JyotishService`; the Architect fixes the
  tolerance budget after the first batch (policy unchanged).

## 26. Static / structural gates

1. `test_public_surface.py` — `jyotish.__all__` matches the allow-list.
2. `test_forbidden_imports.py` — no `astrology|knowledge|transits|dasha|
   calculations|rules|inference`; no `socket|requests|urllib|httpx`; no
   `astronomy.swisseph`; `swisseph` imports confined to `jyotish/swisseph/`;
   `models.py` stdlib-only.
3. `test_no_interpretation.py` — no interpretation vocabulary in
   `src/jyotish` identifiers (list in TEST-PLAN §8).
4. `test_astronomy_unmodified.py` — `src/astronomy` file set + `__all__`
   unchanged.
5. `test_no_network.py` — conftest asserts `socket` never called.

## 27. Future compatibility (M)

Future layers consume JRE-003's public surface only:

- **JRE-004 relationship engine** → `PairGeometry`, `AspectRelationship`.
- **JRE-005 bhava engine** → `NatalChart.bhavas`, `Bhava`.
- **JRE-006 transit engine** → `TransitEvent`, `TransitThroughHouses`,
  `ContinuousTransitEngine`.
- **JRE-007 eclipse engine** → `EclipseProvider`, `EclipseEvent`.
- **Varga** → `longitude_used` + pada math (§7 arc constants).
- **Drishti** → `PairGeometry` exact angles (rule tables live in the future
  Rules layer, ADR-004).
- **Dasha** → Moon's `NakshatraId` + `degree_in_nakshatra`.
- **Yoga/Gochar/Nakshatra interpretation, synthesis, prediction** →
  `PlanetState`, `NatalChart`, `TransitEvent` (facts only).

None require changes to `jyotish` internals; `jyotish` never imports them.

## 28. Non-goals (separation of concerns)

JRE-003 MUST NOT implement or expose: benefic/malefic, good/bad,
auspiciousness, wealth/marriage/career/health/spiritual prediction, Yoga
interpretation, Dasha results, Gochar interpretation, Nakshatra
interpretation, Muhurta, sign-based drishti rule tables, or any claim that
an eclipse causes anything. Reviewers must reject any such vocabulary or
logic in `src/jyotish`.

## 29. CODING handoff checklist

- [ ] `pyproject.toml` adds `jyotish` + `jyotish.swisseph` packages and
      `tests/{unit,integration,validation}/jyotish` testpaths (build
      metadata only; JRE-002 untouched).
- [ ] Implement in order: `models.py` (DATA-CONTRACT v0.3.0, exactly) →
      `errors.py` → `rashi.py` → `nakshatra.py` → `dms.py` → `position.py` →
      `geometry.py` → `houses.py` (pure whole-sign) → `lagna.py` →
      `transit.py` → `eclipse.py` (protocol/registry) → `config.py` →
      `serialize.py` → `service.py` → `swisseph/` (constants → houses →
      eclipse).
- [ ] Ship CODING happy-path tests (TEST-PLAN §16).
- [ ] Gate before QA: `pytest tests/unit tests/integration`,
      `ruff check src tests`, `mypy src/jyotish`; static gates §26 green;
      `src/astronomy` untouched.
- [ ] Do NOT implement: interpretation, drishti tables, topocentric,
      caching beyond the bounded memo, network access, anything in JRE-002.
- [ ] Record the empirical binding facts (§4.1–§4.2) as code comments with
      the verification dates; the eclipse `tret` layout must be re-pinned by
      a test against NASA canon values.

## 30. Unresolved questions (for Architect/Validator)

1. **Default orb table** — values proposed (§19) reflect common Jyotish
   convention; Validator confirms against published conjunction lists before
   they are fixed (TEST-PLAN §12).
2. **Eclipse magnitude source** — solar magnitude via `sol_eclipse_where`
   `attr[0]` (NASA convention per binding docs); Validator confirms against
   the NASA canon magnitudes.
3. **Sidereal cusp tolerance** — the ≈13″ difference (§13.3) is inherent to
   the frame rotation; the published-reference tolerance for lagna (≤ 0.01°)
   absorbs it, but Validator should confirm.
4. **Romanization** — IAST-lite pinned in §7; a future consumer needing
   diacritics does so at presentation, not in the catalog.
5. **Birth time precision** — sub-second birth times accepted (delegated to
   astronomy); no special handling.
6. **Topocentric houses** — explicitly out of scope (geocentric); a future
   versioned extension.

## 31. Change history

| Version | Date | Change |
|---|---|---|
| 0.2.0 | 2026-08-12 | Architecture (design level) |
| 0.3.0 | 2026-08-12 | Specialist implementation spec (this document); supersessions in the notice block |
