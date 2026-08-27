# RI-010G — ARCHITECTURE-IMPACT ASSESSMENT

## 1. Executive Summary

This report synthesizes findings from RI-010A through RI-010F (130+ evidence rules, 19 provenance hazards, 18 rejected claims) to produce a comprehensive architectural impact assessment. The assessment determines exact structural changes required across JRE (facts), JRS (interpretation), data models, and evaluation pipelines prior to implementation.

**Key decisions:**
1. **No new core engines required.** Existing services can be refactored cleanly within current boundaries.
2. **3 new service classes needed:** `VargaConfirmationService`, `TransitActivationService`, `ModifierEvaluationService`.
3. **2 existing services require significant refactoring:** `RelationshipGraphService` (exchange detection, directed edges) and `YogaEvaluatorService` (5-tier modifier pipeline, Varga separation).
4. **4-phase rollout** covering 130 rules across 8 weeks of implementation.

---

## 2. Graph Data Model & Service Refactoring

### 2.1 Current State: `RelationshipGraphService`

```
src/jrs/structural/
├── models.py          # PlanetRelationship (5 fields)
├── service.py         # RelationshipGraphService (4 detection steps)
```

**Current `PlanetRelationship` fields:**
- `planet_a: str`
- `planet_b: str`
- `relationship_type: RelationshipType`
- `strength_modifier: str`
- `is_active: bool`

**Current detection steps:**
1. Conjunction (same rashi)
2. Aspect (Parashari special aspects)
3. Dispositorship (A in B's sign)
4. Transit activation (transit-to-natal)

### 2.2 Required Changes

#### 2.2.1 Directed Aspect Edges

**Requirement:** Aspects are directed in classical texts (A aspects B ≠ B aspects A). Conjunctions and exchanges are undirected.

**Specification:**

```python
@dataclass(frozen=True)
class PlanetRelationship:
    planet_a: str
    planet_b: str
    relationship_type: RelationshipType
    is_directed: bool = False       # NEW: True for aspects (A→B ≠ B→A)
    is_war: bool = False            # NEW: True if within 1°
    war_victor: str | None = None   # NEW: Winner of planetary war
    strength_modifier: str = ""
    node_involvement: str | None = None  # NEW: "RAHU" or "KETU"
    is_active: bool = False
```

**Rules affected:** PA-001, PA-005, PA-006, MY-023

**Impact:** The `extract_relationships` method currently records aspects as undirected pairs. After refactoring:
- Conjunction edges: `is_directed=False`
- Aspect edges: `is_directed=True` (planet_a aspects planet_b)
- Exchange edges: `is_directed=False`
- Dispositor edges: `is_directed=True` (A in B's sign → B disposes A)

**Backward compatibility:** The `to_dict()` method must include `is_directed` in output. Existing consumers that don't check `is_directed` will see no change (conjunctions and exchanges remain undirected).

#### 2.2.2 Parivartana (Sign Exchange) Detection

**Requirement:** Exchange is one of the three qualifying relationships for Raja Yoga (BPHS Ch 41). Currently not detected.

**Specification:**

```python
# New detection step 5 in extract_relationships:
def _detect_exchanges(self, planets: dict) -> list[PlanetRelationship]:
    """Detect sign exchanges (Parivartana) between planet pairs."""
    exchanges = []
    for p1_name, p1_data in planets.items():
        p1_rashi_idx = _rashi_to_index(p1_data.get("rashi", ""))
        if p1_rashi_idx is None:
            continue
        p1_lord = _SIGN_LORDS.get(p1_rashi_idx + 1)
        if p1_lord is None or p1_lord not in planets:
            continue
        p2_name = p1_lord
        p2_data = planets[p2_name]
        p2_rashi_idx = _rashi_to_index(p2_data.get("rashi", ""))
        if p2_rashi_idx is None:
            continue
        p2_lord = _SIGN_LORDS.get(p2_rashi_idx + 1)
        if p2_lord == p1_name:
            # Exchange detected: P1 in P2's sign, P2 in P1's sign
            key = (min(p1_name, p2_name), max(p1_name, p2_name),
                   RelationshipType.CONJUNCTION)
            # Don't create exchange if conjunction already found
            # (exchange is stronger, but conjunction takes priority)
            exchanges.append(PlanetRelationship(
                planet_a=p1_name,
                planet_b=p2_name,
                relationship_type=RelationshipType.EXCHANGE,  # NEW enum value
                is_directed=False,
            ))
    return exchanges
```

**Rules affected:** PA-006, PA-013, PA-014

**New enum value needed:**

```python
class RelationshipType(StrEnum):
    ASPECT = "ASPECT"
    CONJUNCTION = "CONJUNCTION"
    EXCHANGE = "EXCHANGE"          # NEW
    DISPOSITOR = "DISPOSITOR"
    TRANSIT_ASPECT = "TRANSIT_ASPECT"
    TRANSIT_CONJUNCTION = "TRANSIT_CONJUNCTION"
```

**Priority rule:** If two planets are both conjunct AND in exchange, the conjunction takes precedence for formation detection (they are in the same sign). The exchange is recorded as metadata but does not create a separate edge.

#### 2.2.3 Dispositor Chain Truncation

**Requirement:** When a terminal lord is combust, the chain is "broken" (BPHS Ch 33 v.18).

**Specification:**

```python
def _trace_dispositor_chain(
    self, start_planet: str, planets: dict
) -> list[str]:
    """Trace dispositor chain from start_planet to terminal lord.

    Returns the chain of planets visited. Stops when:
    - Terminal lord found (planet in own sign)
    - Combust terminal lord found (chain broken)
    - Circular chain detected
    - Maximum depth reached (10 planets)
    """
    chain = [start_planet]
    visited = {start_planet}

    current = start_planet
    for _ in range(10):  # Max chain length
        current_rashi = _rashi_to_index(planets[current].get("rashi", ""))
        if current_rashi is None:
            break
        lord = _SIGN_LORDS.get(current_rashi + 1)
        if lord is None or lord not in planets:
            break

        # Check if terminal lord is combust → chain broken
        if planets[lord].get("combust", False):
            break  # BPHS Ch 33 v.18: "Combust lord cannot protect its sign"

        # Check if terminal lord is in own sign → chain ends
        lord_rashi = _rashi_to_index(planets[lord].get("rashi", ""))
        if lord_rashi is not None:
            lord_lord = _SIGN_LORDS.get(lord_rashi + 1)
            if lord_lord == lord:
                chain.append(lord)
                break  # Terminal lord found

        if lord in visited:
            break  # Circular chain
        visited.add(lord)
        chain.append(lord)
        current = lord

    return chain
```

**Rules affected:** MY-005, MY-006, MY-007, MY-008

**New field on `PlanetRelationship`:**

```python
@dataclass(frozen=True)
class PlanetRelationship:
    # ... existing fields ...
    chain_status: str = ""  # "INTACT", "BROKEN", "CIRCULAR", ""
    chain_broken_by: str = ""  # Planet that broke the chain (if combust)
```

---

## 3. Evaluation Pipeline Re-architecting

### 3.1 Current State: `YogaEvaluatorService`

**Current evaluation flow:**
```
evaluate_classical_yogas(jre_facts, transit_planet)
  → for each yoga rule:
      → check formation (Kendra-Trikona connection)
      → check combustion/debilitation (cancellation)
      → check nodal affliction (weakening)
      → check transit activation (manifestation)
  → return list[YogaEvaluation]
```

**Problems identified:**
1. Formation and cancellation conflated in single pass
2. No modifier priority hierarchy
3. No Varga confirmation separation
4. Transit activation mixed with formation

### 3.2 Required 5-Tier Modifier Pipeline

**Specification:**

```
Tier 1: COMBUSTION CHECK
  → If planet combust → CANCELLED (override all)
  → Exception: exaltation/own-sign offset (Phaladeepika Ch 1)

Tier 2: DEBILITATION / NEECHA BHANGA
  → If planet debilitated → CANCELLED
  → Unless Neecha Bhanga applies (7 rules: NB-001 through NB-007)
  → If Neecha Bhanga → RESTORED (treat as own sign)

Tier 3: GRAHA YUDDHA (Planetary War)
  → If planets within 1° → determine victor
  → Loser suppressed; winner dominates
  → Exception: benefic-malefic war changes balance

Tier 4: CHESHTA BALA (Retrogression)
  → Retrograde planet gains strength (60 virupas max)
  → Retrograde benefic = stronger benefic
  → Retrograde malefic = stronger malefic
  → Combustion overrides retrograde (Tier 1)

Tier 5: NODE TAINT (Rahu/Ketu)
  → Rahu/Ketu conjunct yoga planet → WEAKENED (not cancelled)
  → Results become unpredictable
  → Combustion overrides node (Tier 1)
```

**New service class:**

```python
class ModifierEvaluationService:
    """5-tier modifier priority evaluation for yoga-forming planets."""

    def evaluate_modifiers(
        self,
        yoga_planets: list[str],
        jre_facts: dict,
    ) -> ModifierReport:
        """Evaluate all modifiers for yoga-forming planets.

        Returns ModifierReport with:
        - status: FORMED / CANCELLED / WEAKENED
        - modifier_chain: list of applied modifiers
        - net_strength: 0.0 to 1.0
        - cancellation_reason: Optional[str]
        """
```

**New model:**

```python
@dataclass(frozen=True)
class ModifierReport:
    """Result of 5-tier modifier evaluation."""
    status: YogaStatus
    modifier_chain: tuple[str, ...]  # e.g., ("COMBUSTION", "RETROGRADE_BOOST")
    net_strength: float
    cancellation_reason: Optional[str] = None
    war_victor: Optional[str] = None
    node_afflicted: bool = False
```

**Rules affected:** MY-010 through MY-035 (all modifier rules)

### 3.3 Separation of D1 Formation from Varga Confirmation

**Specification:**

```
Step 1: D1 Formation (YogaEvaluatorService)
  → Check structural conditions (Kendra-Trikona, etc.)
  → Apply 5-tier modifier pipeline
  → Return YogaEvaluation (is_present, status, strength_modifier)

Step 2: Varga Confirmation (VargaConfirmationService)
  → Check D9 for all yogas
  → Check D10 for career yogas (Raja, Pancha Mahapurusha)
  → Check D7 for progeny yogas
  → Return VargaConfirmationReport (strength, vargottama, etc.)

Step 3: Combine (Evidence Layer)
  → YogaEvaluation + VargaConfirmationReport → Final assessment
  → Varga confirmation modifies strength, not formation
```

**New service class:**

```python
class VargaConfirmationService:
    """Varga-based confirmation of D1 yoga formations."""

    def confirm_yoga(
        self,
        yoga_evaluation: YogaEvaluation,
        d1_states: tuple[PlanetState, ...],
        d9_chart: VargaChart | None = None,
        d10_chart: VargaChart | None = None,
        d7_chart: VargaChart | None = None,
        lagna_num: int | None = None,
    ) -> VargaConfirmationReport:
        """Confirm a D1 yoga using divisional charts."""

    def check_vargottama(
        self,
        planet: str,
        d1_sign: str,
        d9_sign: str,
    ) -> bool:
        """Check if planet is Vargottama (same sign in D1 and D9)."""

    def compute_saptavargaja(
        self,
        planet: str,
        d1_to_d12_charts: dict[str, VargaChart],
    ) -> float:
        """Compute Saptavargaja Bala across 7 vargas."""
```

**New model:**

```python
@dataclass(frozen=True)
class VargaConfirmation:
    """Varga-based confirmation of a D1 yoga."""
    varga_id: str
    planet_positions: dict[str, str]
    planet_houses: dict[str, int]
    planet_dignities: dict[str, str]
    is_vargottama: bool
    kendra_trikona_count: int
    dusthana_count: int
    confirmation_strength: float  # 0.0 to 1.0

@dataclass(frozen=True)
class VargaConfirmationReport:
    """Complete Varga confirmation for a yoga."""
    d9_confirmation: VargaConfirmation | None = None
    d10_confirmation: VargaConfirmation | None = None
    d7_confirmation: VargaConfirmation | None = None
    overall_strength: YogaStrength = YogaStrength.MODERATE
    vargottama_planets: tuple[str, ...] = ()
    saptavargaja_scores: dict[str, float] = field(default_factory=dict)
```

**Rules affected:** VG-001 through VG-030

---

## 4. Temporal & Transit Layer Redesign

### 4.1 Current State: `TemporalEvidenceService`

**Current evaluation flow:**
```
calculate_event_window(candidate_event, natal_facts, dasha_periods, transits)
  → collect all triggers
  → find overlapping triggers
  → classify convergence level
  → return EventWindow
```

**Problems identified:**
1. Dasha-first hierarchy not enforced (all triggers treated equally)
2. No Vedha obstruction
3. No Tara Bala strength
4. Transit-to-transit not distinguished from transit-to-natal

### 4.2 Required Changes

#### 4.2.1 Dasha-First Hierarchy

**Specification:**

```python
class TransitActivationService:
    """Transit activation with Dasha-first hierarchy."""

    def evaluate_activation(
        self,
        natal_yogas: list[YogaEvaluation],
        dasha_lord: str,
        antardasha_lord: str,
        transit_positions: dict[str, str],
        transit_aspects_to_natal: list[PlanetRelationship],
    ) -> list[ActivationResult]:
        """Evaluate transit activation with Dasha-first priority.

        Algorithm:
        1. Check Dasha lord: is it a functional benefic for the yoga?
        2. Check Antardasha lord: is it a functional benefic?
        3. Check transit trigger: benefic conjoining/aspecting yoga planet?
        4. Apply Vedha obstruction masks
        5. Apply Tara Bala strength modification
        6. Return activation results
        """
```

**Updated `TemporalConfig`:**

```toml
[activation_type_weights]
DASHA = 1.0
ANTARDASHA = 0.8
TRANSIT = 0.5
VARGA = 0.7
ASHTAKAVARGA = 0.6
```

**Rules affected:** TA-002, TA-003, TA-005

#### 4.2.2 Vedha Obstruction Masks

**Specification:**

```python
@dataclass(frozen=True)
class VedhaRecord:
    """A single Vedha (obstruction) condition."""
    obstructed_planet: str
    obstructing_planet: str
    vedha_type: str  # "ASPECT", "CONJUNCTION", "NAKSHATRA"
    is_active: bool = True

class VedhaService:
    """Classical Gochara Vedha evaluation."""

    # Phaladeepika Ch 26, V. 8-12 Vedha pairs
    VEDHA_PAIRS: dict[str, str] = {
        "JUPITER": "SATURN",   # Saturn aspecting Jupiter's house
        "VENUS": "MARS",       # Mars aspecting Venus's house
        "MERCURY": "KETU",     # Ketu aspecting Mercury's house
        "MOON": "RAHU",        # Rahu/Ketu conjunction with Moon
        "SUN": "SATURN",       # Saturn aspecting Sun's house
    }

    def evaluate_vedha(
        self,
        transit_positions: dict[str, str],
        natal_positions: dict[str, str],
    ) -> list[VedhaRecord]:
        """Evaluate active Vedha obstructions."""

    def is_obstructed(
        self,
        planet: str,
        vedha_records: list[VedhaRecord],
    ) -> bool:
        """Check if a planet's transit results are obstructed."""
```

**Rules affected:** TA-015 through TA-019, TA-024, TA-025

#### 4.2.3 Tara Bala Strength Calculation

**Specification:**

```python
class TaraBalaService:
    """Nakshatra-based transit strength calculation."""

    def compute_tara_bala(
        self,
        transit_planet_nakshatra: int,
        natal_moon_nakshatra: int,
    ) -> float:
        """Compute Tara Bala strength.

        Returns:
            1.0 for favorable tara (even-numbered)
            0.5 for unfavorable tara (odd-numbered)
        """
        offset = (transit_planet_nakshatra - natal_moon_nakshatra) % 27
        tara_number = offset + 1
        if tara_number % 2 == 0:
            return 1.0  # Favorable
        return 0.5  # Unfavorable
```

**Rules affected:** TA-020, TA-021

### 4.3 New Model: `ActivationResult`

```python
@dataclass(frozen=True)
class ActivationResult:
    """Result of transit activation evaluation for a single yoga."""
    yoga_name: str
    is_activated: bool
    activation_source: str  # "DASHA+TRANSIT", "DASHA_ONLY", "TRANSIT_ONLY", "NONE"
    dasha_support: bool
    antardasha_support: bool
    transit_trigger: bool
    vedha_obstructed: bool
    tara_bala_strength: float
    net_activation_strength: float  # 0.0 to 1.0
```

---

## 5. Catalog & Rule Schema Updates

### 5.1 New Schema: 14-Field Metadata

Every rule in the JRS classical catalog must embed the following provenance metadata:

```json
{
  "rule_id": "KT-001",
  "claim": "Kendra lords + Trikona lords conjunction = Raja Yoga",
  "source_text": "BPHS",
  "chapter": "41",
  "verse_start": null,
  "verse_end": null,
  "edition_id": "Ganeshan-2019",
  "evidence_category": "SOURCE-PINNED CLASSICAL",
  "confidence_weight": 1.0,
  "printed_verification_status": "PENDING",
  "conflicting_sources": [],
  "resolution_strategy": "BPHS-primary",
  "implementation_priority": "P1",
  "notes": "Core Raja Yoga definition."
}
```

### 5.2 Schema Validation Rules

1. `rule_id` must be globally unique across all rule sets (KT, PA, MY, TA, VG).
2. `source_text` must be one of: `BPHS`, `Phaladeepika`, `Jataka Parijata`, `Saravali`, `Brihat Samhita`, `Jaimini Sutras`, `Uttara Kalamrita`.
3. `evidence_category` must be one of the 7 project buckets.
4. `confidence_weight` must be in range [0.0, 1.0].
5. `printed_verification_status` must be one of: `PENDING`, `VERIFIED`, `MODIFIED`, `REJECTED`.
6. Rules with `REJECTED` status must not be loaded into the engine catalog.

### 5.3 Confidence Weight → Engine Integration

The `confidence_weight` field should be used as a multiplier in the evidence convergence layer:

```python
# In ConvergenceService.assess_domain:
for record in evidence_records:
    rule_weight = get_rule_weight(record.rule_id)  # From catalog
    effective_weight = record.base_weight * rule_weight
    # ... convergence calculation
```

### 5.4 4-Phase Rollout Structure

| Phase | Rules | Engine Change | Files Modified | Estimated Effort |
|-------|-------|---------------|----------------|-----------------|
| **Phase 1** | KT-001–005, PA-001–012, MY-010–011 | Core formation + cancellation | structural/models.py, structural/service.py, yoga_evaluator/service.py | 2 weeks |
| **Phase 2** | PA-013–024, MY-005–009, TA-001–011 | Named yogas + transit activation | yoga_evaluator/service.py, temporal/service.py | 2 weeks |
| **Phase 3** | MY-012–035, TA-012–030 | Modifiers + Vedha/Tara Bala | New: modifier/service.py, vedha/service.py, tara/service.py | 2 weeks |
| **Phase 4** | VG-001–030 | Varga confirmation + Saptavargaja | New: varga_confirmation/service.py, bala/service.py | 2 weeks |

---

## 6. Decision Checklist

### 6.1 New Core Modules Required

| Module | Purpose | New/Refactored | Justification |
|--------|---------|----------------|---------------|
| `ModifierEvaluationService` | 5-tier modifier pipeline | **NEW** | Current `evaluate_formation` conflates formation and modifiers; separation required per RI-010C |
| `VargaConfirmationService` | D9/D10/D7 confirmation | **NEW** | Current `_check_d9_strength` is insufficient; full Varga confirmation required per RI-010E |
| `TransitActivationService` | Dasha-first transit evaluation | **NEW** | Current `TemporalEvidenceService` doesn't enforce Dasha hierarchy; dedicated service needed per RI-010D |
| `VedhaService` | Vedha obstruction masks | **NEW** | No existing implementation; classical requirement per RI-010D |
| `TaraBalaService` | Nakshatra-based strength | **NEW** | No existing implementation; classical requirement per RI-010D |
| `RelationshipGraphService` | Exchange detection, directed edges | **REFACTOR** | Existing service needs 3 new capabilities per RI-010B |
| `YogaEvaluatorService` | Separation of formation/modifiers | **REFACTOR** | Current single-pass evaluation insufficient per RI-010C |
| `TemporalEvidenceService` | Dasha-first weighting | **REFACTOR** | Current equal-weight triggers insufficient per RI-010D |
| `BalaService` | Full Saptavargaja Bala | **REFACTOR** | Current D1-only proxy insufficient per RI-010E |

### 6.2 Module Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                    JRE LAYER (Unchanged)                        │
│  JRE-003 (PlanetState) ─── JRE-008 (VargaChart) ─── JRE-010   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STRUCTURAL LAYER                             │
│  RelationshipGraphService (REFACTOR)                           │
│  → Exchange detection, directed edges, chain truncation        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FORMATION LAYER                              │
│  YogaEvaluatorService (REFACTOR)                               │
│  → D1 formation only (no modifiers, no transit)                │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ MODIFIER LAYER   │ │ VARGA LAYER      │ │ TRANSIT LAYER    │
│ (NEW)            │ │ (NEW)            │ │ (NEW)            │
│ ModifierEvalSvc  │ │ VargaConfSvc     │ │ TransitActivSvc  │
│ → 5-tier pipeline│ │ → D9/D10/D7      │ │ → Dasha-first    │
│                  │ │                  │ │ → Vedha/Tara     │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EVIDENCE LAYER                               │
│  ConvergenceService (REFACTOR)                                 │
│  → Combine formation + modifiers + varga + transit             │
│  → confidence_weight from catalog                              │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Final Recommendation

**RECOMMENDATION: Proceed with implementation.**

| Criterion | Assessment |
|-----------|------------|
| New engines required? | **No.** 5 new service classes within existing module boundaries. |
| JRE modifications? | **No.** All changes in JRS layer only. |
| Breaking changes? | **Minimal.** `PlanetRelationship` gains new fields with defaults; `YogaEvaluation` gains new fields with defaults. |
| Backward compatibility | **Maintained.** Existing consumers unaffected by new default fields. |
| Test coverage | **Required.** Each phase needs integration tests validating classical rules. |
| Estimated effort | **8 weeks** (2 weeks per phase). |

---

**FINAL DECISION:** READY FOR SOURCE-VERIFICATION
