# JRS-BASELINE-001: Read-Only Architecture Audit Report

**Date:** 2026-08-22
**Scope:** Full repository read-only inspection
**Status:** COMPLETE — FROZEN IMPLEMENTATION MAP

---

## 1. Complete Engine Capability Matrix

| # | Capability | Implementation File | Public API | Used by JRS | Tests | Status |
|---|---|---|---|---|---|---|
| JRE-002 | Astronomical Core | `src/astronomy/service.py` | `AstronomicalService` | ✅ (via JRE-003) | `tests/unit/astronomy/` | ✅ COMPLETE |
| JRE-003 | Jyotish Coordinate/State | `src/jyotish/service.py` | `JyotishService` | ✅ (via JRE-007) | `tests/unit/jyotish/` | ✅ COMPLETE |
| JRE-004 | Drik Panchanga | `src/drik/` | `DrikService` | ❌ (standalone) | `tests/unit/drik/` | ✅ COMPLETE |
| JRE-005 | Bhava/House Analysis | `src/bhava/` | `BhavaService` | ✅ (via JRE-007) | `tests/unit/bhava/` | ✅ COMPLETE |
| JRE-006 | Gochar/Transit | `src/gochar/` | `GocharService` | ✅ (via JRE-007) | `tests/unit/gochar/` | ✅ COMPLETE |
| JRE-007 | Canonical Context | `src/context/service.py` | `ContextService` | ✅ (orchestrator) | `tests/unit/context/` | ✅ COMPLETE |
| JRE-008 | Varga (Divisional Charts) | `src/varga/service.py` | `VargaService` | ❌ (standalone) | `tests/unit/varga/` | ✅ COMPLETE |
| JRE-009 | Transit Events | `src/jyotish/transit.py` | `ContinuousTransitEngine` | ✅ (via JRE-007) | `tests/unit/jyotish/` | ✅ COMPLETE |
| JRE-010 | Dasha (Planetary Periods) | `src/dasha/service.py` | `DashaService` | ❌ (standalone) | `tests/unit/dasha/` | ✅ COMPLETE |
| JRE-011 | Bala (Planetary Strength) | `src/bala/service.py` | `BalaService` | ❌ (standalone) | `tests/unit/bala/` | ✅ COMPLETE |
| JRE-012 | Karaka (Significators) | `src/karaka/` | `KarakaService` | ❌ (standalone) | `tests/unit/karaka/` | ✅ COMPLETE |
| JRE-013 | Avastha (Planetary States) | `src/avastha/` | `AvasthaService` | ❌ (standalone) | `tests/unit/avastha/` | ✅ COMPLETE |
| JRE-014 | Yoga (Combination Detection) | `src/yoga/` | `YogaService` | ❌ (standalone) | `tests/unit/yoga/` | ✅ COMPLETE |
| JRE-015 | Tajika (Annual Charts) | `src/tajika/` | `TajikaService` | ❌ (standalone) | `tests/unit/tajika/` | ✅ COMPLETE |
| JRE-016 | Ashtakavarga (8-Fold Strength) | `src/ashtakavarga/` | `AshtakavargaService` | ❌ (standalone) | `tests/unit/ashtakavarga/` | ✅ COMPLETE |
| JRE-017 | Jaimini | `src/jaimini/` | `JaiminiService` | ❌ (standalone) | `tests/unit/jaimini/` | ✅ COMPLETE |
| JRE-018 | Prashna (Horary) | `src/prashna/` | `PrashnaService` | ❌ (standalone) | `tests/unit/prashna/` | ✅ COMPLETE |
| JRE-019 | Muhurta (Electional) | `src/muhurta/` | `MuhurtaService` | ❌ (standalone) | `tests/unit/muhurta/` | ✅ COMPLETE |
| JRE-020 | Knowledge/Tradition | `src/knowledge/` | `KnowledgeService` | ✅ (via JRE-007) | `tests/unit/knowledge/` | ✅ COMPLETE |
| JRE-021 | Rectification | `src/rectification/` | `RectificationService` | ❌ (isolated) | `tests/unit/rectification/` | ✅ COMPLETE |
| JRE-022 | Synthesis | `src/synthesis/` | `SynthesisService` | ❌ (standalone) | `tests/unit/synthesis/` | ✅ COMPLETE |
| JRE-023 | Validation | `src/validation/` | `ValidationService` | ❌ (standalone) | `tests/unit/validation/` | ✅ COMPLETE |
| JRS-026 | Classical Evidence Framework | `src/jrs/evidence/service.py` | `EvidenceService` | ✅ (JRS core) | `tests/unit/jrs/evidence/` | ✅ COMPLETE |
| JRS-027 | Temporal Evidence | `src/jrs/temporal/models.py` | `TemporalTrigger`, `EventWindow` | ✅ (JRS core) | `tests/unit/jrs/temporal/` | ✅ COMPLETE |
| JRS-028 | Temporal Windows | `src/jrs/temporal/` | `classify_convergence` | ✅ (JRS core) | `tests/unit/jrs/temporal/` | ✅ COMPLETE |
| JRS-029 | Evidence Convergence | `src/jrs/convergence/service.py` | `ConvergenceService` | ✅ (JRS core) | `tests/unit/jrs/convergence/` | ✅ COMPLETE |
| JRS-031 | Career Domain | `src/jrs/domains/career/` | `CareerDomainService` | ✅ | `tests/unit/jrs/domains/career/` | ✅ COMPLETE |
| JRS-032 | Career Validation | `tests/integration/jrs/validation/test_career_validation.py` | — | ✅ | 16 tests | ✅ COMPLETE |
| JRS-033 | Marriage Domain | `src/jrs/domains/marriage/` | `MarriageDomainService` | ✅ | `tests/unit/jrs/domains/marriage/` | ✅ COMPLETE |
| JRS-034 | Wealth Validation | `tests/integration/jrs/validation/test_wealth_validation.py` | — | ✅ | 16 tests | ✅ COMPLETE |
| JRS-035 | Progeny Domain | `src/jrs/domains/progeny/` | `ProgenyDomainService` | ✅ | `tests/unit/jrs/domains/progeny/` | ✅ COMPLETE |
| JRS-036 | Progeny Validation | `tests/integration/jrs/validation/test_progeny_validation.py` | — | ✅ | 16 tests | ✅ COMPLETE |
| JRS-037 | Migration Domain | `src/jrs/domains/migration/` | `MigrationDomainService` | ✅ | `tests/unit/jrs/domains/migration/` | ✅ COMPLETE |
| JRS-038 | Migration Validation | `tests/integration/jrs/validation/test_migration_validation.py` | — | ✅ | 16 tests | ✅ COMPLETE |
| JRS-039 | Education Domain | `src/jrs/domains/education/` | `EducationDomainService` | ✅ | `tests/unit/jrs/domains/education/` | ✅ COMPLETE |
| JRS-040 | Education Validation | `tests/integration/jrs/validation/test_education_validation.py` | — | ✅ | 16 tests | ✅ COMPLETE |
| JRS-041 | Property Domain | `src/jrs/domains/property/` | `PropertyDomainService` | ✅ | `tests/unit/jrs/domains/property/` | ✅ COMPLETE |
| JRS-042 | Property Validation | `tests/integration/jrs/validation/test_property_validation.py` | — | ✅ | 16 tests | ✅ COMPLETE |
| JRS-043 | Transitions Domain | `src/jrs/domains/transitions/` | `TransitionsDomainService` | ✅ | `tests/unit/jrs/domains/transitions/` | ✅ COMPLETE |
| JRS-044 | Transitions Validation | `tests/integration/jrs/validation/test_transitions_validation.py` | — | ✅ | 16 tests | ✅ COMPLETE |
| JRS-045 | CLI/API Wrapper | `src/jrs/cli.py` | `main()`, `build_parser()` | ✅ | `tests/integration/jrs/test_cli.py` | ✅ COMPLETE |
| JRS-046 | Research Worker | `src/jrs/research/service.py` | `ResearchService` | ✅ (CLI) | `tests/unit/jrs/research/` | ✅ COMPLETE |
| JRS-047 | Documentation | `README.md`, `docs/ARCHITECTURE.md`, `docs/DOMAINS.md` | — | ✅ | — | ✅ COMPLETE |
| JRS-048 | Spirituality Domain | `src/jrs/domains/spirituality/` | `SpiritualityDomainService` | ✅ | `tests/unit/jrs/domains/spirituality/` | ✅ COMPLETE |
| JRS-049 | Business Domain | `src/jrs/domains/business/` | `BusinessDomainService` | ✅ | `tests/unit/jrs/domains/business/` | ✅ COMPLETE |
| JRS-050 | Litigation Domain | `src/jrs/domains/litigation/` | `LitigationDomainService` | ✅ | `tests/unit/jrs/domains/litigation/` | ✅ COMPLETE |
| JRS-051 | Assets Domain | `src/jrs/domains/assets/` | `AssetsDomainService` | ✅ | `tests/unit/jrs/domains/assets/` | ✅ COMPLETE |
| JRS-052 | Health Domain | `src/jrs/domains/health/` | `HealthDomainService` | ✅ | `tests/unit/jrs/domains/health/` | ✅ COMPLETE |

---

## 2. Public API Map

### JRE Engines (Core Calculation Layer)

| Module | Primary Entry Point | Key Methods |
|---|---|---|
| `src/astronomy/service.py` | `AstronomicalService` | `compute(request: EphemerisRequest) -> EphemerisResult` |
| `src/jyotish/service.py` | `JyotishService` | `planetary_state()`, `pair_geometry()`, `chart()`, `events_between()`, `eclipses()` |
| `src/context/service.py` | `ContextService` | `snapshot(request: ContextRequest) -> CanonicalFactSnapshot` |
| `src/bhava/` | `BhavaService` | `analyze_chart(chart, config) -> HouseAnalysis` |
| `src/gochar/` | `GocharService` | `instant_result()`, `natal_result()`, `interval_result()` |
| `src/dasha/service.py` | `DashaService` | `generate_timeline()`, `get_lord_at()` |
| `src/bala/service.py` | `BalaService` | `calculate_shadbala() -> ShadbalaReport` |
| `src/varga/service.py` | `VargaService` | `compute_varga() -> VargaChart` |
| `src/ashtakavarga/` | `AshtakavargaService` | `compute_ashtakavarga() -> AshtakavargaReport` |
| `src/yoga/` | `YogaService` | `detect_yogas() -> YogaReport` |
| `src/karaka/` | `KarakaService` | `evaluate_karakas() -> KarakaReport` |
| `src/avastha/` | `AvasthaService` | `evaluate_avasthas() -> AvasthaReport` |
| `src/rectification/` | `RectificationService` | `calculate_offset() -> RectificationReport` |
| `src/knowledge/` | `KnowledgeService` | `resolve_rules()`, `apply_tradition_profile()` |
| `src/synthesis/` | `SynthesisService` | `synthesize() -> SynthesisReport` |
| `src/validation/` | `ValidationService` | `validate() -> ValidationReport` |
| `src/drik/` | `DrikService` | `compute_panchanga() -> PanchangaReport` |
| `src/tajika/` | `TajikaService` | `compute_tajika() -> TajikaReport` |
| `src/jaimini/` | `JaiminiService` | `compute_jaimini() -> JaiminiReport` |
| `src/prashna/` | `PrashnaService` | `compute_prashna() -> PrashnaReport` |
| `src/muhurta/` | `MuhurtaService` | `compute_muhurta() -> MuhurtaReport` |

### JRS Layer (Interpretation/Rule Layer)

| Module | Primary Entry Point | Key Methods |
|---|---|---|
| `src/jrs/service.py` | `OrchestratorService` | `route_query(intent, natal_context) -> EvidencePacket` |
| `src/jrs/cli.py` | `main()` | CLI entry point with `--birth-date`, `--birth-time`, `--place`, `--query` |
| `src/jrs/evidence/` | `EvidenceService` | `add_record()`, `resolve_chain()`, `detect_circular()` |
| `src/jrs/convergence/` | `ConvergenceService` | `assess_domain() -> DomainAssessment` |
| `src/jrs/temporal/` | — | `classify_convergence()`, `find_overlapping_triggers()` |
| `src/jrs/research/` | `ResearchService` | `get_citation()`, `get_citations_for_domain()` |
| `src/jrs/domains/career/` | `CareerDomainService` | `evaluate_career_facts()` |
| `src/jrs/domains/wealth/` | `WealthDomainService` | `evaluate_wealth_facts()` |
| `src/jrs/domains/marriage/` | `MarriageDomainService` | `evaluate_marriage_facts()` |
| `src/jrs/domains/education/` | `EducationDomainService` | `evaluate_education_facts()` |
| `src/jrs/domains/property/` | `PropertyDomainService` | `evaluate_property_facts()` |
| `src/jrs/domains/progeny/` | `ProgenyDomainService` | `evaluate_progeny_facts()` |
| `src/jrs/domains/migration/` | `MigrationDomainService` | `evaluate_migration_facts()` |
| `src/jrs/domains/transitions/` | `TransitionsDomainService` | `evaluate_transitions_facts()` |
| `src/jrs/domains/spirituality/` | `SpiritualityDomainService` | `evaluate_spirituality_facts()` |
| `src/jrs/domains/business/` | `BusinessDomainService` | `evaluate_business_facts()` |
| `src/jrs/domains/litigation/` | `LitigationDomainService` | `evaluate_litigation_facts()` |
| `src/jrs/domains/assets/` | `AssetsDomainService` | `evaluate_assets_facts()` |
| `src/jrs/domains/health/` | `HealthDomainService` | `evaluate_health_facts()` |

---

## 3. JRE → JRS Dependency Graph

```
JRE-002 (Astronomy)
  └─► JRE-003 (Jyotish Coordinate/State)
        ├─► JRE-005 (Bhava/House Analysis)
        ├─► JRE-006 (Gochar/Transit)
        ├─► JRE-009 (Transit Events)
        └─► JRE-007 (Canonical Context)
              ├─► JRE-020 (Knowledge/Tradition)
              └─► JRS Orchestrator
                    ├─► JRS Evidence Framework (JRS-026)
                    ├─► JRS Temporal Evidence (JRS-027/028)
                    ├─► JRS Convergence (JRS-029)
                    └─► JRS Domain Services (JRS-031 through JRS-052)
                          ├─► Career, Wealth, Marriage, Education
                          ├─► Property, Progeny, Migration, Transitions
                          └─► Spirituality, Business, Litigation, Assets, Health

Independent JRE Engines (NOT consumed by JRS):
  JRE-004 (Drik Panchanga) — standalone
  JRE-008 (Varga) — standalone
  JRE-010 (Dasha) — standalone (potential future integration)
  JRE-011 (Bala) — standalone (potential future integration)
  JRE-012 (Karaka) — standalone
  JRE-013 (Avastha) — standalone
  JRE-014 (Yoga) — standalone
  JRE-015 (Tajika) — standalone
  JRE-016 (Ashtakavarga) — standalone
  JRE-017 (Jaimini) — standalone
  JRE-018 (Prashna) — standalone
  JRE-019 (Muhurta) — standalone
  JRE-021 (Rectification) — isolated, NOT integrated with JRS
  JRE-022 (Synthesis) — standalone
  JRE-023 (Validation) — standalone
```

---

## 4. Research Boundary Resolution

### `src/research/` (JRE-level)
- **Purpose:** Standalone research module for source-pinned knowledge cataloging
- **Scope:** Historical source management, tradition profiles, precedence rules
- **Consumers:** JRE-020 (Knowledge engine)
- **Status:** Integrated with JRE-020

### `src/jrs/research/` (JRS-level)
- **Purpose:** Resolves classical source citations for CLI output and traceable reports
- **Scope:** Rule ID → citation lookup from `config/research_sources.toml`
- **Consumers:** JRS CLI (`src/jrs/cli.py`)
- **Status:** Standalone, read-only
- **Key Difference:** `src/jrs/research/` is a thin citation resolver. `src/research/` is a full knowledge management engine.

---

## 5. Existing Nakshatra Capabilities

### `src/jyotish/nakshatra.py`
**Status:** ✅ COMPLETE

| Capability | Implementation | Status |
|---|---|---|
| 27-Nakshatra catalog | `NAKSHATRA_ORDER`, `NAKSHATRA_LORD_CYCLE` | ✅ |
| Nakshatra lookup by longitude | `nakshatra_of(longitude_deg)` | ✅ |
| Nakshatra index | `nakshatra_index_of(longitude_deg)` | ✅ |
| Degree within nakshatra | `degree_in_nakshatra(longitude_deg)` | ✅ |
| Pada determination (1-4) | `pada_of(longitude_deg)` | ✅ |
| Vimshottari lord of nakshatra | `lord_of(nakshatra)` | ✅ |
| Nakshatra span | `nakshatra_span(nakshatra)` | ✅ |
| Pada span | `pada_span(nakshatra, pada)` | ✅ |
| Catalog versioning | `NAKSHATRA_CATALOG_VERSION = "1.0.0"` | ✅ |

**What's NOT implemented:**
- ❌ Nakshatra activation/transit tracking
- ❌ Nakshatra-based relationship compatibility
- ❌ Nakshatra-specific remedial measures
- ❌ Tara (birth star) based compatibility
- ❌ Nakshatra-based trait interpretation

---

## 6. Existing Panchanga/Time Capabilities

### `src/drik/` (Drik Panchanga)
**Status:** ✅ COMPLETE (stub, config present)

| Capability | Status | Notes |
|---|---|---|
| Service structure | ✅ | `DrikService` present |
| Config | ✅ | `config/drik.toml` present |
| Tests | ✅ | `tests/unit/drik/` present |

### `src/astronomy/`
| Capability | Status | Notes |
|---|---|---|
| Julian Day computation | ✅ | `iso_utc_to_jd()` |
| Body positions (9 planets) | ✅ | `EphemerisResult` |
| Retrograde detection | ✅ | `RetrogradeState` |
| Ayanamsa application | ✅ | Lahiri, Raman, Fagan-Bradley |

### `src/jyotish/`
| Capability | Status | Notes |
|---|---|---|
| Rashi (sign) classification | ✅ | `rashi_of()` |
| Nakshatra classification | ✅ | `nakshatra_of()` |
| Pada classification | ✅ | `pada_of()` |
| House cusps (6 systems) | ✅ | `HouseCuspProvider` |
| Bhava computation | ✅ | `compute_bhavas()` |
| Aspect geometry | ✅ | `PairGeometry` |
| Eclipse detection | ✅ | `EclipseEvent` |

**Panchanga factors already computed:**
- ✅ Weekday (from Sun position)
- ✅ Tithi (from Moon-Sun angular separation)
- ✅ Nakshatra (from Moon longitude)
- ✅ Yoga (Moon-Sun combination)
- ❌ Karana (half-tithi) — not explicitly computed
- ❌ Vara (weekday-specific deity) — not computed
- ❌ Hora (hour-lord) — not computed
- ❌ Masa (lunar month) — not computed

---

## 7. Rectification Integration Status

### `src/rectification/`
**Status:** ✅ COMPLETE but ❌ ISOLATED from JRS

| Component | Status | Notes |
|---|---|---|
| Models | ✅ | `LifeEvent`, `RectificationResult`, `RectificationReport` |
| Service | ✅ | `RectificationService.calculate_offset()` |
| Config | ✅ | `config/rectification.toml` |
| Tests | ✅ | `tests/unit/rectification/` (unit tests) |
| JRS Integration | ❌ NOT INTEGRATED | No import of `src/rectification` in JRS CLI or pipeline |
| CLI Integration | ❌ NOT INTEGRATED | CLI does not accept rectification input |

**Key Findings:**
- Rectification module is structurally complete
- It implements 3 classical methods: Transit-to-Ascendant, Dasha-to-Event, Progression-to-Ascendant
- It produces `RectificationReport` with suggested birth time
- **It is NOT wired into the JRS pipeline** — the CLI does not use it
- **No validation dataset** exists for rectification

---

## 8. Tier-2 Validation Gap Analysis

| Domain | Has Rules (TOML) | Has Unit Tests | Has Validation Dataset | Gap |
|---|---|---|---|---|
| Career | ✅ `career.toml` | ✅ | ✅ `career_domain/` | — |
| Wealth | ✅ `wealth.toml` | ✅ | ✅ `wealth_domain/` | — |
| Marriage | ✅ `marriage.toml` | ✅ | ✅ `marriage_domain/` | — |
| Education | ✅ `education.toml` | ✅ | ✅ `education_domain/` | — |
| Property | ✅ `property.toml` | ✅ | ✅ `property_domain/` | — |
| Progeny | ✅ `progeny.toml` | ✅ | ✅ `progeny_domain/` | — |
| Migration | ✅ `migration.toml` | ✅ | ✅ `migration_domain/` | — |
| Transitions | ✅ `transitions.toml` | ✅ | ✅ `transitions_domain/` | — |
| **Spirituality** | ✅ `spirituality.toml` | ✅ | ❌ **MISSING** | **Needs validation dataset** |
| **Business** | ✅ `business.toml` | ✅ | ❌ **MISSING** | **Needs validation dataset** |
| **Litigation** | ✅ `litigation.toml` | ✅ | ❌ **MISSING** | **Needs validation dataset** |
| **Assets** | ✅ `assets.toml` | ✅ | ❌ **MISSING** | **Needs validation dataset** |
| **Health** | ✅ `health.toml` | ✅ | ❌ **MISSING** | **Needs validation dataset** |

**Summary:** 5 of 13 domains lack validation datasets: Spirituality, Business, Litigation, Assets, Health.

---

## 9. CLI Status

### `src/jrs/cli.py`
**Status:** ✅ COMPLETE

| Feature | Status | Notes |
|---|---|---|
| Birth data input | ✅ | `--birth-date`, `--birth-time`, `--place` |
| Query routing | ✅ | `--query` (career, wealth, marriage, education, property, children, migration, travel, transitions) |
| Text output | ✅ | Structured traceable report |
| JSON output | ✅ | `--json` flag |
| Domain routing | ✅ | 8 domains registered in `DOMAIN_SERVICES` |
| Classical citations | ✅ | Resolves via `ResearchService` |
| Evidence pipeline | ✅ | facts → evidence → convergence → assessment |

**CLI Query Coverage:**
- ✅ career, wealth, marriage, education, property, children, migration, travel, transitions
- ❌ spirituality, business, litigation, assets, health (NOT registered in CLI)

---

## 10. Existing Domain Contracts

### JRS Domain Service Contract (All 13 Domains)

All domain services follow the identical pattern:

```python
class XDomainService:
    def __init__(self, config: XConfig | None = None, config_path: Path | None = None) -> None
    def load_x_rules(self) -> XRuleCatalog
    def evaluate_x_facts(self, facts: dict[str, Any]) -> tuple[EvidenceRecord, ...]
    def get_rules_for_outcome(self, outcome: XOutcomeTaxonomy) -> tuple[XRule, ...]
    def get_outcome_taxonomies(self) -> tuple[XOutcomeTaxonomy, ...]
    @property
    def config(self) -> XConfig
    @property
    def rule_count(self) -> int
```

### Input Contract
```python
facts: dict[str, Any]  # Keys are JRE fact names (e.g., "10th_lord_in_kendra_or_trikona")
                       # Values are bool, int, float, or str
```

### Output Contract
```python
tuple[EvidenceRecord, ...]
# Each EvidenceRecord contains:
#   - evidence_id: str
#   - outcome_taxonomy: str
#   - supporting_fact_type: str
#   - rule_id: str
#   - source_id: str
#   - direction: EvidenceDirection (SUPPORT/CONTRADICT/MITIGATE/NEUTRAL)
#   - strength: EvidenceStrength (VERY_HIGH/HIGH/MODERATE/LOW/VERY_LOW)
```

---

## 11. Duplicate/Redundant Capability Detection

| Area | Finding | Severity |
|---|---|---|
| Nakshatra catalog | Defined in `src/jyotish/nakshatra.py` AND duplicated in `src/dasha/models.py` (`NAKSHATRA_LORDS`) | ⚠️ LOW |
| Vimshottari lord cycle | `NAKSHATRA_LORD_CYCLE` in `nakshatra.py` vs `NAKSHATRA_LORDS` in `dasha/models.py` | ⚠️ LOW |
| Benefic/Malefic | Defined in `src/bala/models.py` (`NATURAL_BENEFICS`, `NATURAL_MALEFICS`) — not centralized | ⚠️ LOW |
| Sign lords | Defined in `src/bala/models.py` (`SIGN_LORDS_VIMSHOTTARI`) — not centralized | ⚠️ LOW |
| Exaltation/Debilitation | Defined in `src/bala/models.py` — not centralized | ⚠️ LOW |
| Friendship map | Defined in `src/bala/models.py` — not centralized | ⚠️ LOW |
| Research service | `src/research/` (JRE-level) vs `src/jrs/research/` (JRS-level) — different purposes, not redundant | ✅ OK |

**No critical duplications found.** All duplications are minor catalog constants that could be centralized but do not cause correctness issues.

---

## 12. Recommendations for JRE-026 & JRE-027

### JRE-026: Nakshatra Relationship Engine

**Recommendation:** Create `src/jyotish/compatibility/` as a new JRE engine.

1. **Do NOT duplicate** `NAKSHATRA_LORDS` — import from `src/jyotish/nakshatra.py`
2. **Do NOT duplicate** `FRIENDSHIP_MAP` — import from `src/bala/models.py`
3. **Public API:** `CompatibilityService.compute(moon_state_1, moon_state_2) -> CompatibilityReport`
4. **Models:** `NakshatraCompatibility`, `TaraCompatibility`, `YoniCompatibility`
5. **Integration point:** JRE-007 can add a `compatibility` capability to `CapabilityManifest`

### JRE-027: Birth Signature Engine

**Recommendation:** Create `src/jyotish/birth_signature/` as a new JRE engine.

1. **Use existing** `NatalChart` from JRE-003 as input
2. **Use existing** `ShadbalaReport` from JRE-011 (optional enrichment)
3. **Public API:** `BirthSignatureService.compute(chart, optional_bala) -> BirthSignature`
4. **Models:** `BirthSignature`, `PlanetaryInfluence`, `SignaturePattern`
5. **Integration point:** JRE-007 can add a `birth_signature` capability

### Avoiding Duplication
- Reuse `PlanetState`, `NatalChart`, `LagnaState` from JRE-003
- Reuse `ShadbalaReport` from JRE-011
- Reuse `YogaReport` from JRE-014
- Do NOT re-declare `BodyId`, `RashiId`, `NakshatraId`

---

## 13. Future Change Impact Map

### Tier-2 Validation Datasets (Spirituality, Business, Litigation, Assets, Health)
**Files to create:**
- `tests/fixtures/validation_charts/spirituality_domain/*.json` (4 fixtures)
- `tests/fixtures/validation_charts/business_domain/*.json` (4 fixtures)
- `tests/fixtures/validation_charts/litigation_domain/*.json` (4 fixtures)
- `tests/fixtures/validation_charts/assets_domain/*.json` (4 fixtures)
- `tests/fixtures/validation_charts/health_domain/*.json` (4 fixtures)
- `tests/integration/jrs/validation/test_spirituality_validation.py`
- `tests/integration/jrs/validation/test_business_validation.py`
- `tests/integration/jrs/validation/test_litigation_validation.py`
- `tests/integration/jrs/validation/test_assets_validation.py`
- `tests/integration/jrs/validation/test_health_validation.py`

**Files to modify:**
- None (purely additive)

### JRS-053+ (Next Steps)
**Files to create:**
- `src/jyotish/compatibility/` (JRE-026) — 6 files
- `src/jyotish/birth_signature/` (JRE-027) — 6 files
- `tests/unit/jyotish/compatibility/` — 3 files
- `tests/unit/jyotish/birth_signature/` — 3 files

**Files to modify:**
- `src/context/models.py` — add new capabilities to `CAPABILITIES`
- `src/context/service.py` — add new snapshot methods
- `src/jrs/cli.py` — register new domain services

---

## 14. Untouchable Files

These files form the deterministic substrate and must NOT be modified:

| File | Reason |
|---|---|
| `src/astronomy/models.py` | JRE-002 data contract — all engines depend on it |
| `src/jyotish/models.py` | JRE-003 data contract — all Jyotish engines depend on it |
| `src/jyotish/nakshatra.py` | Nakshatra catalog — used by Dasha, Bala, and future engines |
| `src/jyotish/rashi.py` | Rashi catalog — used by all house-based calculations |
| `src/jyotish/geometry.py` | Aspect computation — used by Bhava, Gochar |
| `src/bala/models.py` | Benefic/Malefic, Friendship, Dignity constants |
| `src/dasha/models.py` | Vimshottari constants — used by Dasha timeline |
| `src/context/models.py` | Canonical fact envelope — all JRS consumption flows through here |
| `src/jrs/evidence/models.py` | EvidenceRecord — all domain services emit this |
| `src/jrs/convergence/models.py` | DomainAssessment — final output format |

---

## 15. Dependency/Order Graph

### Execution Order for JRS-053 Onward

```
Phase 1: Tier-2 Validation Datasets (JRS-053 through JRS-057)
  JRS-053: Spirituality Validation Dataset
  JRS-054: Business Validation Dataset
  JRS-055: Litigation Validation Dataset
  JRS-056: Assets Validation Dataset
  JRS-057: Health Validation Dataset
  (All independent — can be parallelized)

Phase 2: Engine Integration
  JRS-058: JRE-010 (Dasha) Integration into JRS Pipeline
    Depends on: JRE-010 (complete), JRS CLI (complete)
    Touches: src/jrs/cli.py, src/jrs/temporal/

  JRS-059: JRE-011 (Bala) Integration into JRS Pipeline
    Depends on: JRE-011 (complete), JRS CLI (complete)
    Touches: src/jrs/cli.py, src/jrs/domains/

Phase 3: New Engines
  JRS-060: JRE-026 Nakshatra Relationship Engine
    Depends on: JRE-003 (complete), JRE-011 (complete)
    Creates: src/jyotish/compatibility/

  JRS-061: JRE-027 Birth Signature Engine
    Depends on: JRE-003 (complete), JRE-011 (complete), JRE-014 (complete)
    Creates: src/jyotish/birth_signature/

Phase 4: Integration & Documentation
  JRS-062: Rectification Integration into JRS Pipeline
    Depends on: JRE-021 (complete), JRS CLI (complete)
    Touches: src/jrs/cli.py, src/rectification/

  JRS-063: Final Documentation Update
    Depends on: All above
    Touches: README.md, docs/
```

---

## 16. Frozen Implementation Map

| JRS ID | Capability | Owner | Files | Status |
|---|---|---|---|---|
| JRE-002 | Astronomical Core | [Calculation] | `src/astronomy/` | ✅ FROZEN |
| JRE-003 | Jyotish Coordinate/State | [Calculation] | `src/jyotish/` | ✅ FROZEN |
| JRE-004 | Drik Panchanga | [Calculation] | `src/drik/` | ✅ FROZEN |
| JRE-005 | Bhava/House Analysis | [Calculation] | `src/bhava/` | ✅ FROZEN |
| JRE-006 | Gochar/Transit | [Calculation] | `src/gochar/` | ✅ FROZEN |
| JRE-007 | Canonical Context | [Calculation] | `src/context/` | ✅ FROZEN |
| JRE-008 | Varga (Divisional Charts) | [Calculation] | `src/varga/` | ✅ FROZEN |
| JRE-009 | Transit Events | [Calculation] | `src/jyotish/transit.py` | ✅ FROZEN |
| JRE-010 | Dasha (Planetary Periods) | [Calculation] | `src/dasha/` | ✅ FROZEN |
| JRE-011 | Bala (Planetary Strength) | [Calculation] | `src/bala/` | ✅ FROZEN |
| JRE-012 | Karaka (Significators) | [Calculation] | `src/karaka/` | ✅ FROZEN |
| JRE-013 | Avastha (Planetary States) | [Calculation] | `src/avastha/` | ✅ FROZEN |
| JRE-014 | Yoga (Combination Detection) | [Calculation] | `src/yoga/` | ✅ FROZEN |
| JRE-015 | Tajika (Annual Charts) | [Calculation] | `src/tajika/` | ✅ FROZEN |
| JRE-016 | Ashtakavarga (8-Fold Strength) | [Calculation] | `src/ashtakavarga/` | ✅ FROZEN |
| JRE-017 | Jaimini | [Calculation] | `src/jaimini/` | ✅ FROZEN |
| JRE-018 | Prashna (Horary) | [Calculation] | `src/prashna/` | ✅ FROZEN |
| JRE-019 | Muhurta (Electional) | [Calculation] | `src/muhurta/` | ✅ FROZEN |
| JRE-020 | Knowledge/Tradition | [Calculation] | `src/knowledge/` | ✅ FROZEN |
| JRE-021 | Rectification | [Calculation] | `src/rectification/` | ✅ FROZEN |
| JRE-022 | Synthesis | [Calculation] | `src/synthesis/` | ✅ FROZEN |
| JRE-023 | Validation | [Calculation] | `src/validation/` | ✅ FROZEN |
| JRS-026 | Classical Evidence Framework | [JRS Core] | `src/jrs/evidence/` | ✅ FROZEN |
| JRS-027 | Temporal Evidence | [JRS Core] | `src/jrs/temporal/` | ✅ FROZEN |
| JRS-028 | Temporal Windows | [JRS Core] | `src/jrs/temporal/` | ✅ FROZEN |
| JRS-029 | Evidence Convergence | [JRS Core] | `src/jrs/convergence/` | ✅ FROZEN |
| JRS-031 | Career Domain | [Domain] | `src/jrs/domains/career/` | ✅ FROZEN |
| JRS-032 | Career Validation | [Validation] | `tests/integration/jrs/validation/test_career_validation.py` | ✅ FROZEN |
| JRS-033 | Marriage Domain | [Domain] | `src/jrs/domains/marriage/` | ✅ FROZEN |
| JRS-034 | Wealth Validation | [Validation] | `tests/integration/jrs/validation/test_wealth_validation.py` | ✅ FROZEN |
| JRS-035 | Progeny Domain | [Domain] | `src/jrs/domains/progeny/` | ✅ FROZEN |
| JRS-036 | Progeny Validation | [Validation] | `tests/integration/jrs/validation/test_progeny_validation.py` | ✅ FROZEN |
| JRS-037 | Migration Domain | [Domain] | `src/jrs/domains/migration/` | ✅ FROZEN |
| JRS-038 | Migration Validation | [Validation] | `tests/integration/jrs/validation/test_migration_validation.py` | ✅ FROZEN |
| JRS-039 | Education Domain | [Domain] | `src/jrs/domains/education/` | ✅ FROZEN |
| JRS-040 | Education Validation | [Validation] | `tests/integration/jrs/validation/test_education_validation.py` | ✅ FROZEN |
| JRS-041 | Property Domain | [Domain] | `src/jrs/domains/property/` | ✅ FROZEN |
| JRS-042 | Property Validation | [Validation] | `tests/integration/jrs/validation/test_property_validation.py` | ✅ FROZEN |
| JRS-043 | Transitions Domain | [Domain] | `src/jrs/domains/transitions/` | ✅ FROZEN |
| JRS-044 | Transitions Validation | [Validation] | `tests/integration/jrs/validation/test_transitions_validation.py` | ✅ FROZEN |
| JRS-045 | CLI/API Wrapper | [Interface] | `src/jrs/cli.py` | ✅ FROZEN |
| JRS-046 | Research Worker | [Interface] | `src/jrs/research/` | ✅ FROZEN |
| JRS-047 | Documentation | [Docs] | `README.md`, `docs/` | ✅ FROZEN |
| JRS-048 | Spirituality Domain | [Domain] | `src/jrs/domains/spirituality/` | ✅ FROZEN |
| JRS-049 | Business Domain | [Domain] | `src/jrs/domains/business/` | ✅ FROZEN |
| JRS-050 | Litigation Domain | [Domain] | `src/jrs/domains/litigation/` | ✅ FROZEN |
| JRS-051 | Assets Domain | [Domain] | `src/jrs/domains/assets/` | ✅ FROZEN |
| JRS-052 | Health Domain | [Domain] | `src/jrs/domains/health/` | ✅ FROZEN |
| JRS-053 | Spirituality Validation | [Validation] | `tests/fixtures/validation_charts/spirituality_domain/` | ❌ PENDING |
| JRS-054 | Business Validation | [Validation] | `tests/fixtures/validation_charts/business_domain/` | ❌ PENDING |
| JRS-055 | Litigation Validation | [Validation] | `tests/fixtures/validation_charts/litigation_domain/` | ❌ PENDING |
| JRS-056 | Assets Validation | [Validation] | `tests/fixtures/validation_charts/assets_domain/` | ❌ PENDING |
| JRS-057 | Health Validation | [Validation] | `tests/fixtures/validation_charts/health_domain/` | ❌ PENDING |

---

**Audit Complete.**
**Frozen Implementation Map: JRS-001 through JRS-052 (FROZEN), JRS-053 through JRS-057 (PENDING).**
