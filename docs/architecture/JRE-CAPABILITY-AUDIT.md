# JRE Capability Audit

> **Generated:** 2026-08-18
> **Scope:** JRE-002 through JRE-009 public APIs mapped against 12 future engines
> **Purpose:** Identify gaps, dependencies, and architectural risks before JRE-010 design

---

## 1. Executive Summary

The JRE platform has established a **strong foundational stack** across eight modules (JRE-002–JRE-009) covering raw astronomy, Jyotish classification, classical knowledge, house analysis, transit state, canonical context, divisional charts, and research. The architecture enforces strict separation of concerns: each layer computes its facts deterministically, echoes lower-layer outputs verbatim, and never interprets or predicts.

**Current readiness is high for positional/factual engines** (Drishti, Ashtakavarga, Tajika) but has **structural gaps for interpretive engines** (Dasha, Yoga, Bala, Avastha, Karaka) that require new computational sublayers. Two future engines (Prashna, Muhurta) need query-time chart casting, which depends on a thin adapter over existing `JyotishService` capabilities.

**Key finding:** The `KnowledgeService` synthesis pipeline (JRE-004) is the critical integration point — it provides rule resolution, conflict handling, and provenance for all interpretive engines. Future engines should consume `SynthesisResult` rather than re-implementing rule logic.

---

## 2. Current Capability Matrix

### 2.1 JRE-002 — Astronomy Core (`src/astronomy/`)

| Public API | Type | Output | Consumers |
|---|---|---|---|
| `AstronomicalService.compute(request)` | Service | `EphemerisResult` | JRE-003 |
| `EphemerisRequest` | Request | Date, time, tz, coords, bodies, config | — |
| `EphemerisResult` | Result | `tuple[BodyPosition, ...]` + metadata | JRE-003 |
| `BodyPosition` | Model | Tropical/sidereal longitude, latitude, distance, speed, retrograde | JRE-003 |
| `CalculationConfig` | Config | Ayanamsa, ephemeris mode, position type, node type | JRE-003 |
| `BodyId` | Enum | SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN, RAHU, KETU | All layers |
| `RetrogradeState` | Enum | DIRECT, RETROGRADE, STATIONARY | All layers |
| `Ayanamsa` | Enum | LAHIRI, RAMAN, FAGAN_BRADLEY | JRE-003, JRE-008 |

**Role:** Provider-independent, deterministic astronomical position engine. No Jyotish interpretation.

### 2.2 JRE-003 — Jyotish Coordinate & State (`src/jyotish/`)

| Public API | Type | Output | Consumers |
|---|---|---|---|
| `JyotishService.planetary_state(request)` | Service | `tuple[PlanetState, ...]` | JRE-005, JRE-006, JRE-007, JRE-008 |
| `JyotishService.position_at(request)` | Service | Single-instant `PlanetState` tuple | JRE-006 |
| `JyotishService.state_series(query)` | Service | Sampled `tuple[PlanetState, ...]` over interval | JRE-006 |
| `JyotishService.events_between(query)` | Service | `tuple[TransitEvent, ...]` (bisection) | JRE-006, JRE-007 |
| `JyotishService.pair_geometry(b1, b2, ...)` | Service | `PairGeometry` | JRE-005, JRE-006, JRE-007 |
| `JyotishService.chart(birth)` | Service | `NatalChart` | JRE-005, JRE-007 |
| `JyotishService.eclipses(query)` | Service | `tuple[EclipseEvent, ...]` | JRE-007 |
| `PlanetState` | Model | Rashi, nakshatra, pada, DMS, retrograde, speed | JRE-008 |
| `PairGeometry` | Model | Separation, conjunction, `tuple[AspectRelationship, ...]` | JRE-005, JRE-006 |
| `AspectRelationship` | Model | Kind, exact angle, separation, orb, applying/separating | JRE-005 |
| `NatalChart` | Model | Birth snapshot, lagna, bhavas, planet states | JRE-005, JRE-007 |
| `TransitEvent` | Model | Body, kind, julian day, boundary, reached | JRE-006, JRE-007 |
| `RashiId` | Enum | 12 signs (MESHA–MEENA) | All layers |
| `NakshatraId` | Enum | 27 nakshatras | All layers |
| `AspectKind` | Enum | 7 aspect types | JRE-005 |
| `HouseSystem` | Enum | 6 house systems | JRE-005, JRE-007, JRE-008 |
| `BirthData` | Model | Date, time, timezone, lat/lon | JRE-005, JRE-006, JRE-007 |
| `rashi_of()`, `degree_in_rashi()` | Pure | Longitude → sign classification | JRE-008 |
| `nakshatra_of()`, `pada_of()` | Pure | Longitude → nakshatra classification | Future |
| `sign_lord_of()` | Pure | Sign → lord mapping | JRE-005 |
| `angular_separation_deg()` | Pure | Angular distance | JRE-005 |
| `pair_geometry()` | Pure | Geometric relationship between two bodies | JRE-005, JRE-006 |

**Role:** Deterministic Jyotish facts. No benefic/malefic, no yoga, no dasha, no interpretation.

### 2.3 JRE-004 — Classical Knowledge & Rules (`src/knowledge/`)

| Public API | Type | Output | Consumers |
|---|---|---|---|
| `KnowledgeService.synthesize(query)` | Service | `SynthesisResult` | Future interpretive engines |
| `KnowledgeService.sources()` | Query | `tuple[Source, ...]` | Diagnostics |
| `KnowledgeService.profiles()` | Query | `tuple[TraditionProfile, ...]` | Configuration |
| `enrich_snapshot(snapshot, facts)` | Pure | Snapshot with `nature`, `dignity`, `combusted` | Future engines |
| `derive_nature(facts, body)` | Pure | `"BENEFIC"` / `"MALEFIC"` / `"MIXED"` | Future engines |
| `derive_dignity(facts, body, rashi)` | Pure | Exalted/Debilited/Own/Friend/Enemy/Neutral | Future engines |
| `derive_combusted(facts, body, retro, sep)` | Pure | `bool` | Future engines |
| `derive_aspect_strength(facts, aspecter, house)` | Pure | Strength label or `None` | Future engines |
| `FactsRegistry` | Registry | Nature, dignity tables, combustion, friendship, aspects | `enrich_snapshot` |
| `RuleRegistry` | Registry | Authoritative rule catalogs | `synthesize` |
| `SourceRegistry` | Registry | Classical source bibliography | `synthesize` |
| `ProfileRegistry` | Registry | Tradition profiles with priority | `synthesize` |
| `SynthesisResult` | Result | Matched/suppressed rules, conflicts, provenance | Future engines |
| `RuleQuery` | Request | Domain, fact snapshot, profile | `synthesize` |

**Role:** Classical rule resolution with full provenance. Rules are data, never code.

### 2.4 JRE-005 — Bhava / House Engine (`src/bhava/`)

| Public API | Type | Output | Consumers |
|---|---|---|---|
| `BhavaService.analyze_chart(birth, config)` | Service | `HouseAnalysisResult` | JRE-007 |
| `BhavaService.analyze_transit(birth, transit, ...)` | Service | `TransitHouseAnalysis` | JRE-006, JRE-007 |
| `HouseAnalysisResult` | Result | `tuple[HouseAnalysis, ...]` per house system | JRE-007 |
| `HouseAnalysis` | Result | Derived houses, planet facts, ownership, aspects | JRE-007 |
| `DerivedHouseFact` | Fact | Per-house: lord, occupancy, categories, boundaries | JRE-007 |
| `PlanetHouseFact` | Fact | Per-planet: house number, lord, sign lord, retrograde | Future |
| `HouseOwnershipFact` | Fact | Per-planet: lorded signs and houses | Future |
| `TransitHouseAnalysis` | Result | Transit-to-natal house facts | JRE-006, JRE-007 |
| `HouseCategory` | Enum | KENDRA, TRIKONA, DUSTHANA, UPACHAYA | Future |
| `OccupancyStatus` | Enum | OCCUPIED, EMPTY | Future |

**Role:** Derived house computational state with full provenance. No interpretation.

### 2.5 JRE-006 — Gochar / Transit Engine (`src/gochar/`)

| Public API | Type | Output | Consumers |
|---|---|---|---|
| `GocharService.instant(request)` | Service | `GocharInstantResult` | JRE-007 |
| `GocharService.natal(request)` | Service | `GocharNatalResult` | JRE-007 |
| `GocharService.interval(request)` | Service | `GocharIntervalResult` | JRE-007 |
| `GocharInstantResult` | Result | Planet states + pair geometry (no birth) | JRE-007 |
| `GocharNatalResult` | Result | Transit-to-natal house analysis + aspects | JRE-007 |
| `GocharIntervalResult` | Result | Event stream + state samples + optional house series | JRE-007 |

**Role:** Composes and echoes JRE-003/JRE-005 transit facts. No interpretation.

### 2.6 JRE-007 — Canonical Context & Fact Snapshot (`src/context/`)

| Public API | Type | Output | Consumers |
|---|---|---|---|
| `ContextService.snapshot_instant(request)` | Service | `CanonicalFactSnapshot` | All future engines |
| `ContextService.snapshot_natal(request)` | Service | `CanonicalFactSnapshot` | All future engines |
| `ContextService.snapshot_interval(request)` | Service | `CanonicalFactSnapshot` | All future engines |
| `ContextService.snapshot_eclipses(request)` | Service | `CanonicalFactSnapshot` | All future engines |
| `CanonicalContext` | Model | Context id, purpose, chart identity, capabilities | All future engines |
| `CanonicalFactSnapshot` | Model | Provenance-bearing envelope of all lower-layer facts | All future engines |
| `FactEnvelope` | Model | Single fact with identity + provenance | All future engines |
| `CapabilityManifest` | Model | Available/requested capability states | All future engines |
| `ContextConfig` | Config | Time precision, house system, tradition profile | All future engines |

**Role:** Composition layer assembling lower-layer facts into a provenance-bearing envelope.

### 2.7 JRE-008 — Varga / Divisional Charts (`src/varga/`)

| Public API | Type | Output | Consumers |
|---|---|---|---|
| `VargaService.compute_varga_chart(request)` | Service | `VargaChart` | Future engines |
| `VARGA_REGISTRY` | Registry | 14 frozen varga definitions (D2–D60) | `compute_varga_chart` |
| `VargaChart` | Result | `tuple[VargaPosition, ...]` + identities | Future engines |
| `VargaPosition` | Fact | Body, source state, division index, varga sign | Future engines |
| `VargaDefinition` | Model | Division number, calculation method, source citations | Registry |

**Role:** Deterministic divisional chart computation from JRE-003 `PlanetState` facts.

### 2.8 JRE-009 — Research Worker (`src/research/`)

| Public API | Type | Output | Consumers |
|---|---|---|---|
| `ResearchWorker.execute_task(task)` | Service | `ResearchReport` | Orchestration queue |
| `ResearchTask` | Request | Query, target concepts, source directories | Queue consumer |
| `ResearchReport` | Result | Evidence items, summary, provenance | Queue consumer |
| `Evidence` | Fact | Source file, excerpt, line number, context | — |

**Role:** Local text/markdown evidence search with deterministic provenance.

---

## 3. Future Engine Requirements

### 3.1 Dasha (Planetary Period Systems)

Dasha systems (Vimshottari, Yogini, etc.) compute planetary period sequences, sub-periods, and transitions from a natal chart. They determine which planet "rules" a given time span.

| Requirement | Description | Priority |
|---|---|---|
| Birth data | `BirthData` (date, time, timezone, coordinates) | Required |
| Nakshatra of Moon | `PlanetState.nakshatra` for MOON at birth | Required |
| Moon longitude | `PlanetState.longitude_used` for MOON | Required |
| Period sequences | Vimshottari period years per planet | **GAP** |
| Sub-period computation | Bhukti (sub-period) hierarchy within dasa | **GAP** |
| Transition dates | From natal date, compute period boundaries | **GAP** |
| Transit overlay | Which transits activate during which periods | Optional (JRE-006) |
| Knowledge integration | `DASHA_APPLICATION` rule domain (JRE-004) | Available |

### 3.2 Drishti (Aspect Analysis)

Drishti extends JRE-003's geometric aspects with interpretive analysis — strength computation, applying/separating timing, and doctrinal classification.

| Requirement | Description | Priority |
|---|---|---|
| Pair geometry | `PairGeometry` with aspects | Available |
| Applying/separating | `ApplyingSeparating` state | Available |
| Orb configuration | Configurable aspect orbs | Available |
| Aspect strength | Classical strength labels (JRE-004 `derive_aspect_strength`) | Available |
| Transit-to-natal aspects | `GocharNatalResult.transit_to_natal_aspects` | Available |
| Strength scoring | Numeric strength calculation (orb-based weighting) | **GAP** |
| Special aspects | Saturn 3rd/10th, Jupiter 5th/9th, Mars 4th/8th | Partial (JRE-004 `special_aspects`) |
| Drishti rule domain | `DRISHTI` rule domain in JRE-004 | Available |

### 3.3 Karaka (Significators)

Karaka doctrine assigns natural significators to planets, houses, and combinations. It bridges positional facts with classical meaning.

| Requirement | Description | Priority |
|---|---|---|
| Natural benefic/malefic | `derive_nature()` from JRE-004 | Available |
| Planet significators | Classical karaka tables per planet | **GAP** |
| House significators | Classical karaka tables per house | **GAP** |
| Atmakaraka | Highest-degree planet (requires planet states) | Available (JRE-003) |
| amatyakaraka | Second-highest degree planet | Available (JRE-003) |
| Karaka rule domain | `KARAKA` rule domain in JRE-004 | Available |

### 3.4 Avastha (Planetary States)

Avastha classifies planetary states based on nakshatra pada, degree, and relative position — determining whether a planet is "sleeping," "infant," "youthful," "old," etc.

| Requirement | Description | Priority |
|---|---|---|
| Planet states | `PlanetState` with nakshatra, pada, degree | Available |
| Nakshatra pada | `PlanetState.pada` | Available |
| Avastha classification rules | Naabhasa/Deeptadi/Janma-adi avasthas | **GAP** |
| Dignity integration | Exaltation/debilitation affects avastha | Available (JRE-004) |
| Avastha catalog | Classical avastha tables | **GAP** |

### 3.5 Yoga (Combinations & Patterns)

Yoga detection identifies specific planetary combinations that produce classical results — conjunctions, aspects, house placements, and dignity patterns.

| Requirement | Description | Priority |
|---|---|---|
| Conjunction detection | `PairGeometry.conjunction` | Available |
| Aspect relationships | `PairGeometry.aspects` | Available |
| House placement | `PlanetHouseFact` from JRE-005 | Available |
| Dignity | `derive_dignity()` from JRE-004 | Available |
| Combustion | `derive_combusted()` from JRE-004 | Available |
| Yoga definition rules | `YOGA_DEFINITION` rule domain | Available |
| Yoga pattern engine | Pattern matching over combinations | **GAP** |
| Strength scoring | Which yogas are "operative" vs "cancelled" | **GAP** |
| Knowledge synthesis | `SynthesisResult` with YOGA_DEFINITION domain | Available |

### 3.6 Bala / Shadbala (Strength Calculation)

Shadbala computes six-fold planetary strength: Sthana, Diga, Kaala, Drik, Naisargika, and Cheshtabala — each requiring distinct computation.

| Requirement | Description | Priority |
|---|---|---|
| Dignity (Sthana Bala) | `derive_dignity()` from JRE-004 | Available |
| Direction (Diga Bala) | Planet's directional strength by house | **GAP** |
| Temporal (Kaala Bala) | Day/night, hora, Ayana strengths | **GAP** |
| Aspect (Drik Bala) | Aspect strength from JRE-004 | Partial |
| Natural (Naisargika) | Fixed natural strength order | **GAP** |
| Motional (Cheshtabala) | Retrograde/speed-based strength | Available (JRE-003) |
| Saptavargaja Bala | Strength across 7 divisional charts | Partial (JRE-008 varga positions) |
| Shadbala total | Sum of six sub-strengths | **GAP** |
| Bala thresholds | Minimum required strength (Iighta, etc.) | **GAP** |

### 3.7 Ashtakavarga (Eight-Factor Scoring)

Ashtakavarga computes a scoring matrix based on eight factors (7 planets + lagna), counting benefic aspects received by each sign from each of the eight reference points.

| Requirement | Description | Priority |
|---|---|---|
| Seven planets + lagna | 8 reference points | Available (JRE-003 + lagna) |
| Aspect positions | `FactsRegistry.aspect_strength_positions` | Available (JRE-004) |
| Special aspects | `FactsRegistry.special_aspects` (Saturn/Jupiter/Mars) | Available (JRE-004) |
| Sign-lord mapping | `sign_lord_of()` from JRE-003 | Available |
| Bhinna Ashtakavarga | Per-planet scoring matrix | **GAP** |
| Sarvashtakavarga | Summed scoring matrix | **GAP** |
| Prastara AV | Tabular AV computation | **GAP** |
| Result interpretation thresholds | Strength analysis thresholds | **GAP** |

### 3.8 Tajika (Annual Transit Analysis)

Tajika analyzes annual solar return charts and monthly/weekly transit patterns for event prediction.

| Requirement | Description | Priority |
|---|---|---|
| Annual return chart | Solar return chart (new birth chart at Sun return) | **GAP** |
| Transit-to-natal aspects | `GocharNatalResult.transit_to_natal_aspects` | Available |
| Applying/separating | `ApplyingSeparating` in aspects | Available |
| YOGI/AIYEKA systems | Tajika-specific lot computation | **GAP** |
| Monthly/weekly factors | Periodic transit analysis | Available (JRE-006 interval) |
| Ithashala/Tajika aspects | Aspect-strength with orb decay | **GAP** |

### 3.9 Jaimini (Jaimini Karaka System)

Jaimini uses a distinct karaka system (chara karakas) and special aspects (rashi drishti) different from Parashari.

| Requirement | Description | Priority |
|---|---|---|
| Chara karakas | Atmakaraka through Darakaraka by degree | Available (JRE-003 degrees) |
| Rashi drishti | Sign-to-sign aspects (not planet-to-planet) | **GAP** |
| Karakamsha | Navamsa (D9) of Atmakaraka | Partial (JRE-008 D9) |
| Upapada | 12th-from-AL computation | **GAP** |
| Jaimini rules | `JAIMINI` domain (if added to JRE-004) | **GAP** |

### 3.10 Prashna (Horary Questions)

Prashna casts a chart for the moment a question is asked and analyzes it independently of birth data.

| Requirement | Description | Priority |
|---|---|---|
| Query-time chart casting | `JyotishService.chart()` for arbitrary time | Available |
| Planetary states | `JyotishService.planetary_state()` for query time | Available |
| House analysis | `BhavaService.analyze_chart()` for query time | Available |
| Lagna analysis | `JyotishService.chart().lagna` | Available |
| Prashna-specific rules | Prana, Hora, Drekkana special charts | **GAP** |
| significator of querent | Ascendant lord + 1st house | Available |
| Question classification | Classification by query topic | **GAP** |

### 3.11 Muhurta (Electional Astrology)

Muhurta selects auspicious time windows by analyzing planetary and lunar conditions.

| Requirement | Description | Priority |
|---|---|---|
| Date/time selection | `JyotishService.planetary_state()` for candidates | Available |
| Lunar phase | Nakshatra of MOON | Available |
| Tithi | Lunar day (derived from Sun-Moon longitude) | **GAP** |
| Karana | Half-tithi | **GAP** |
| Yoga (Samyoga) | Sun-Moon longitudinal combination | **GAP** |
| Day lord | Weekday ruling planet | **GAP** |
| Muhurta-specific rules | Muhurta rule domain (if added to JRE-004) | **GAP** |
| Inauspicious periods | Rahu Kalam, Yamagandam | **GAP** |

### 3.12 Rectification (Birth Time Verification)

Rectification adjusts birth time by matching predicted events against known life events.

| Requirement | Description | Priority |
|---|---|---|
| Birth data variations | Multiple `BirthData` candidates | Available (JRE-007 V1) |
| Chart comparison | `NatalChart` for each candidate | Available |
| Transit event matching | `GocharIntervalResult` events | Available |
| Life event timeline | Known events as reference points | **GAP** |
| Lagna sensitivity | Lagna degree vs life events | Available |
| Candidate scoring | Which candidate best matches events | **GAP** |

---

## 4. Gap Analysis

### 4.1 Structural Gaps (New Sublayers Required)

| Gap | Description | Affects | Effort |
|---|---|---|---|
| **Dasha computation engine** | Period sequence generation, sub-period hierarchy, transition calculation | Dasha, Tajika | High |
| **Strength computation framework** | Sthana/Diga/Kaala/Drik/Naisargika/Cheshtabala sublayers | Bala, Ashtakavarga | High |
| **Yoga pattern engine** | Combinatorial pattern matching over planet/house/aspect configurations | Yoga | Medium |
| **Tajika lot computation** | Annual return chart, Ithashala, Yogi/Aiyeka systems | Tajika | Medium |
| **Jaimini rashi drishti** | Sign-to-sign aspect system distinct from Parashari | Jaimini | Medium |
| **Muhurta sublayer** | Tithi, Karana, Yoga (Samyoga), day lord, inauspicious periods | Muhurta | Medium |
| **Karaka tables** | Planet/house significator catalog in JRE-004 facts | Karaka | Low |
| **Avastha classification** | Naabhasa/Deeptadi/Janma-adi avastha tables and rules | Avastha | Low |

### 4.2 Data Gaps (Missing Facts or Catalogs)

| Gap | Description | Affects | Effort |
|---|---|---|---|
| **Vimshottari period years** | 120-year cycle: planet-period mapping | Dasha | Low |
| **Shadbala subfactor tables** | Directional, temporal, natural strength constants | Bala | Low |
| **Ashtakavarga scoring tables** | Benefic aspect positions per reference planet | Ashtakavarga | Low |
| **Muhurta electional rules** | Auspicious/inauspicious time factors | Muhurta | Low |
| **Karaka catalog** | Planet/house significator definitions | Karaka | Low |
| **Avastha classification tables** | Avastha conditions and labels | Avastha | Low |
| **Tithi/Karana/Yoga definitions** | Lunar day computations | Muhurta | Low |
| **Jaimini rashi drishti rules** | Sign aspect mapping | Jaimini | Low |

### 4.3 API Exposure Gaps

| Gap | Description | Affects | Effort |
|---|---|---|---|
| **`JyotishService.pair_geometry()` batch** | Need all-pairs geometry in one call (currently per-pair) | Drishti, Ashtakavarga, Yoga | Low |
| **Transit-to-natal aspect timing** | Applying/separating state at transit instant | Drishti, Tajika | Low |
| **Nakshatra lord lookup** | `lord_of()` exists but not surfaced via `PlanetState` | Dasha, Avastha | None (available) |
| **D9 (Navamsa) chart** | Already computed by JRE-008 `VARGA_REGISTRY["D9"]` | Jaimini | None (available) |
| **Benefic/malefic at house level** | `PlanetHouseFact` exists but needs benefic/malefic echo | Yoga, Bala | Low |

### 4.4 Integration Gaps

| Gap | Description | Affects | Effort |
|---|---|---|---|
| **Knowledge→Engine bridge** | Future engines need `enrich_snapshot` before rule evaluation | All interpretive | Low |
| **Context snapshot enrichment** | `CanonicalFactSnapshot` needs enriched facts for interpretation | All interpretive | Medium |
| **Research→Knowledge bridge** | `ResearchWorker` output needs ingestion into fact snapshots | Research-informed | Medium |
| **Varga→Bala bridge** | Bala needs Saptavargaja Bala across 7 varga charts | Bala | Low |

---

## 5. Dependency Graph

### 5.1 Current Layer Dependencies

```
JRE-002 (astronomy)
    └── JRE-003 (jyotish)
            ├── JRE-004 (knowledge)
            │       └── [rule resolution for all future interpretive engines]
            ├── JRE-005 (bhava)
            │       └── JRE-006 (gochar)
            └── JRE-008 (varga)

JRE-007 (context) ← composes JRE-003 + JRE-005 + JRE-006 + JRE-003(eclipses)
JRE-009 (research) ← independent (local file search)
```

### 5.2 Future Engine Dependencies

```
                    ┌─────────────────────────────────────────────┐
                    │           JRE-007 (CanonicalContext)        │
                    │     ┌─────────────────────────────────┐     │
                    │     │  CanonicalFactSnapshot           │     │
                    │     │  ┌──────────┐  ┌─────────────┐  │     │
                    │     │  │ JRE-003  │  │ JRE-005     │  │     │
                    │     │  │ Planet   │  │ House       │  │     │
                    │     │  │ States + │  │ Analysis +  │  │     │
                    │     │  │ Geometry │  │ Transit     │  │     │
                    │     │  └──────────┘  └─────────────┘  │     │
                    │     │  ┌──────────┐  ┌─────────────┐  │     │
                    │     │  │ JRE-006  │  │ JRE-003     │  │     │
                    │     │  │ Gochar   │  │ Eclipses    │  │     │
                    │     │  └──────────┘  └─────────────┘  │     │
                    │     └─────────────────────────────────┘     │
                    │  ┌──────────────────────────────────────┐   │
                    │  │  JRE-004 (KnowledgeService)           │   │
                    │  │  enrich_snapshot + synthesize         │   │
                    │  └──────────────────────────────────────┘   │
                    │  ┌──────────────────────────────────────┐   │
                    │  │  JRE-008 (VargaService)               │   │
                    │  │  Divisional charts (D9, D10, D24…)    │   │
                    │  └──────────────────────────────────────┘   │
                    └─────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
              ┌─────┴─────┐   ┌──────┴──────┐   ┌──────┴──────┐
              │ DASHA      │   │ DRISHTI     │   │ YOGA        │
              │ (period    │   │ (aspect     │   │ (pattern    │
              │  engine)   │   │  analysis)  │   │  detection) │
              └────────────┘   └─────────────┘   └─────────────┘
              ┌────────────┐   ┌─────────────┐   ┌─────────────┐
              │ BALA       │   │ ASHTAKAVARGA│   │ KARAKA      │
              │ (strength  │   │ (scoring    │   │ (significator│
              │  calc)     │   │  matrix)    │   │  tables)    │
              └────────────┘   └─────────────┘   └─────────────┘
              ┌────────────┐   ┌─────────────┐   ┌─────────────┐
              │ AVASTHA    │   │ TAJIKA      │   │ JAIMINI     │
              │ (planetary │   │ (annual     │   │ (chara      │
              │  states)   │   │  transit)   │   │  karaka)    │
              └────────────┘   └─────────────┘   └─────────────┘
              ┌────────────┐   ┌─────────────┐
              │ PRASHNA    │   │ MUHURTA     │
              │ (horary    │   │ (electional │
              │  chart)    │   │  timing)    │
              └────────────┘   └─────────────┘
              ┌────────────────────────────────┐
              │ RECTIFICATION                  │
              │ (birth time verification)      │
              │ → consumes ALL other engines   │
              └────────────────────────────────┘
```

### 5.3 Data Flow: Interpretive Engine Pattern

All interpretive future engines follow the same integration pattern:

```
1. BirthData / QueryTime
       ↓
2. JRE-003 → PlanetStates + Geometry
       ↓
3. JRE-005 → HouseAnalysis (optional)
       ↓
4. JRE-007 → CanonicalFactSnapshot
       ↓
5. JRE-004 → enrich_snapshot (nature, dignity, combustion)
       ↓
6. JRE-004 → synthesize (domain-specific rules)
       ↓
7. [Future Engine] → Interpretation Result
```

---

## 6. Recommendations for JRE-010

### 6.1 Priority Ranking

| Rank | Engine | Rationale |
|---|---|---|
| **1** | **Dasha** | Foundational temporal framework; most engines need period context |
| **2** | **Drishti** | Extends existing JRE-003/JRE-005 aspects; high reuse |
| **3** | **Yoga** | Pattern detection over existing data; high interpretive value |
| **4** | **Karaka** | Low-effort catalog addition to JRE-004; enables meaning layer |
| **5** | **Bala** | Strength framework needed for multiple engines |
| **6** | **Ashtakavarga** | Scoring matrix; builds on Bala + Drishti |
| **7** | **Avastha** | Classification engine; depends on Bala and dignity |
| **8** | **Tajika** | Annual transit; depends on Dasha + Drishti |
| **9** | **Jaimini** | Parallel system; depends on D9 + chara karakas |
| **10** | **Prashna** | Horary; mostly adapter over existing APIs |
| **11** | **Muhurta** | Electional; needs new lunar-factor sublayer |
| **12** | **Rectification** | Meta-engine; consumes all others |

### 6.2 Recommended JRE-010 Scope

**JRE-010 should implement Dasha (Vimshottari) as the foundational temporal engine.** Rationale:

1. **Most other engines need Dasha context** — Yoga strength, Drishti activation, and interpretation all depend on "when is this planet active?"
2. **Clean data dependency** — only requires `PlanetState.nakshatra` for MOON (already available from JRE-003) plus a well-defined period table (120-year cycle).
3. **No structural gaps** — the Vimshottari period table is a closed, deterministic mapping; no new computational paradigm is needed.
4. **Foundation for Tajika** — Tajika's annual analysis builds on Dasha periods.
5. **Enables the "interpretation bridge"** — with Dasha + KnowledgeService, the first full interpretation engine becomes possible.

### 6.3 Pre-JRE-010 Work

Before starting any future engine, the following preparatory work should be completed:

1. **Add `all_pairs_geometry` to `JyotishService`** — batch all-pairs computation (currently per-pair) for Drishti/Ashtakavarga/Yoga efficiency.
2. **Extend `enrich_snapshot` with house-level facts** — `PlanetHouseFact` should include benefic/malefic echo for Yoga and Bala.
3. **Create `DRISHTI` domain rules in JRE-004** — pre-author Drishti-related rules for KnowledgeService synthesis.
4. **Add Dasha rule domain to JRE-004** — `DASHA_APPLICATION` already exists; needs authored rules for Vimshottari interpretation.

---

## Appendix A: Module Version Summary

| Module | Package | Version | Tests |
|---|---|---|---|
| JRE-002 | `astronomy` | 0.3.0 | Unit + Integration |
| JRE-003 | `jyotish` | 0.3.2 | Unit + Integration |
| JRE-004 | `knowledge` | 0.5.0 | Unit + Integration |
| JRE-005 | `bhava` | 0.2.0 | Unit + Integration |
| JRE-006 | `gochar` | 0.2.0 | Unit + Integration |
| JRE-007 | `context` | 0.1.0 | Unit + Integration |
| JRE-008 | `varga` | 0.1.0 | Unit + Integration |
| JRE-009 | `research` | 0.1.0 | Unit + Integration |

## Appendix B: Future Engine ↔ Available API Matrix

| Future Engine | JRE-002 | JRE-003 | JRE-004 | JRE-005 | JRE-006 | JRE-007 | JRE-008 | JRE-009 |
|---|---|---|---|---|---|---|---|---|
| **Dasha** | — | ★★ | ● | — | — | ★ | — | — |
| **Drishti** | — | ★★★ | ★★ | ★★ | ★ | ★ | — | — |
| **Karaka** | — | ★ | ★★★ | ● | — | ★ | — | ● |
| **Avastha** | — | ★★★ | ★★ | — | — | ★ | ● | — |
| **Yoga** | — | ★★★ | ★★ | ★★ | — | ★ | ● | — |
| **Bala** | — | ★★ | ★★★ | ★ | — | ★ | ★ | — |
| **Ashtakavarga** | — | ★★ | ★★★ | ★ | — | ★ | — | — |
| **Tajika** | — | ★★★ | ★★ | ★★ | ★★ | ★★ | — | — |
| **Jaimini** | — | ★★ | ★★ | — | — | ★ | ★★ | — |
| **Prashna** | — | ★★★ | ★ | ★★ | — | ★ | — | — |
| **Muhurta** | — | ★★★ | — | — | — | ★ | — | — |
| **Rectification** | — | ★★★ | ★★ | ★★ | ★★ | ★★★ | ★ | — |

**Legend:** ★★★ = Primary input, ★★ = Significant input, ★ = Supplementary input, ● = Optional/supplementary, — = Not needed

## Appendix C: Cross-Cutting Concerns

### C.1 Determinism

Every future engine MUST produce byte-identical output for identical inputs (pinned catalog versions, pinned ephemeris versions). This is enforced by:
- Domain-separated SHA-256 identity (JRE-007 pattern)
- No wall-clock data, no randomness, no environment-dependent state
- Deterministic serialization (declaration order, enum values, `-0.0 → 0.0`)

### C.2 Provenance

Every fact produced by future engines MUST carry a provenance chain traceable to:
- Input data (birth data, query parameters)
- Astronomical computation (provider, ephemeris version)
- Normalization (catalog versions)
- Derived computation (algorithm identity, inputs)
- Doctrine/rule (source, chapter, verse, edition)
- Future inference (engine version, algorithm)

### C.3 Import Boundaries

Future engines MUST respect the one-way import graph:
```
astronomy ← jyotish ← {knowledge, bhava, gochar, varga, context} ← {future engines}
```
No circular imports. No direct `astronomy`/`swisseph` access from future engines.

### C.4 Separation of Facts and Interpretation

Future engines that perform interpretation MUST:
1. Consume facts from JRE-003/JRE-005/JRE-006/JRE-007/JRE-008
2. Enrich via JRE-004 `enrich_snapshot`
3. Resolve rules via JRE-004 `synthesize`
4. Produce result models with embedded provenance
5. Never compute positions, cusps, or coordinate facts themselves
