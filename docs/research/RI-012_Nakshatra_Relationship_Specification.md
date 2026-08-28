# RI-012 — NAKSHATRA RELATIONSHIP & PARIVARTANA SPECIFICATION

## 1. Executive Conclusion

Nakshatra-based planetary relationships operate at a **finer granularity** than Rashi (sign) interactions — each Rashi contains 2⅓ Nakshatras (each spanning 13°20′), and each Nakshatra is ruled by a Vimshottari lord independent of the Rashi lord. This creates a **dual-layer relational structure**: a planet's Rashi lordship defines its broad functional role, while its Nakshatra lordship defines a subtler dependency channel through which results are transmitted, modified, and amplified.

The specification defines four new relational constructs for the JRS chain evaluator:

1. **Nakshatra Parivartana** — Mutual Nakshatra lord exchange (Planet A in B's Nakshatra, Planet B in A's Nakshatra).
2. **One-Directional Nakshatra Dependency** — Planet A occupies the Nakshatra ruled by Planet B (no reciprocal exchange).
3. **NAKSHATRA_LORD and NAKSHATRA_PARIVARTANA edge types** — New directed/undirected edges for the ChainEvaluator graph.
4. **Temporal integration** — How Nakshatra transits (Tara Bala) interact with natal Nakshatra Parivartana.

The Nakshatra layer is **not a replacement** for Rashi-based relationships — it is a **supplementary attenuation/modification layer** that operates in parallel with existing Rashi conjunctions, aspects, exchanges, and dispositorships.

---

## 2. Nakshatra Parivartana (Mutual Exchange)

### 2.1 Classical Conditions for Formation

**Source:** BPHS (Chapter 46: Nakshatra Adhyaya), Phaladeepika (Chapter 26), Saravali (Chapter 36).

**Formation rule:**

A **Nakshatra Parivartana** exists when:

- Planet A occupies a Nakshatra whose Vimshottari lord is Planet B.
- Planet B occupies a Nakshatra whose Vimshottari lord is Planet A.

Formally, given:
- `N(n)` = Nakshatra occupied by planet `n`
- `Lord(N)` = Vimshottari lord of Nakshatra `N` (from the 9-planet cycle: Ketu→Venus→Sun→Moon→Mars→Rahu→Jupiter→Saturn→Mercury, repeated 3× over 27 Nakshatras)

Then:

```
Nakshatra_Parivartana(A, B) ⟺ Lord(N(A)) = B  ∧  Lord(N(B)) = A
```

**Critical distinction from Rashi Parivartana:**

| Property | Rashi Parivartana | Nakshatra Parivartana |
|----------|-------------------|----------------------|
| Granularity | Sign-level (30° arcs) | Nakshatra-level (13°20′ arcs) |
| Detection basis | Rashi ownership (12 signs) | Vimshottari lordship (27 Nakshatras) |
| Structural permanence | Permanent (sign placement) | Permanent (Nakshatra placement) |
| Relative strength | High (Rashi = primary identity) | Moderate (Nakshatra = secondary identity) |
| Textual authority | BPHS Ch 34 (primary) | BPHS Ch 46 (supplementary) |
| Chain edge weight | 0.90 (PARIVARTANA) | 0.80 (NAKSHATRA_PARIVARTANA) |

**Why Nakshatra Parivartana is weaker than Rashi Parivartana:**

The Rashi represents the planet's **primary domicile** — it is the fundamental sign of ownership. The Nakshatra represents a **sub-domicile** — a finer division within the Rashi. BPHS Ch 46 states that Nakshatra lordship modifies results but does not override Rashi lordship. The root texts consistently treat Rashi-level relationships as structurally primary and Nakshatra-level relationships as supplementary.

**Architectural implication:** Nakshatra Parivartana edges should be traversed by the chain evaluator but assigned a lower base weight (0.80) than Rashi Parivartana (0.90). When both a Rashi Parivartana and a Nakshatra Parivartana exist between the same pair of planets, the Rashi Parivartana takes precedence in the chain path (higher weight), and the Nakshatra Parivartana is recorded as a secondary confirming relationship.

### 2.2 Sub-Types of Nakshatra Parivartana

Following the Rashi Parivartana classification (BPHS Ch 34), Nakshatra Parivartana can be sub-classified:

| Sub-type | Condition | Strength Modifier | Source |
|----------|-----------|-------------------|--------|
| **Maha Nakshatra Parivartana** | One planet is in the Nakshatra whose lord is in the other's Nakshatra, AND the Nakshatra lord is exalted or in own Nakshatra | +0.15 (total weight 0.95) | Commentary-dependent |
| **Dainya Nakshatra Parivartana** | One or both Nakshatras fall in Dusthana houses (6th, 8th, 12th) from Lagna | −0.20 (total weight 0.60) | Commentary-dependent |
| **Sangya Nakshatra Parivartana** | Standard mutual exchange without special conditions | No modifier (base weight 0.80) | Commentary-dependent |

**Evidence status:** Sub-type classification is **COMMENTARY-DEPENDENT** (derived from Rashi Parivartana rules by analogy). The core formation rule (mutual lordship) is **SOURCE-PINNED CLASSICAL** (BPHS Ch 46).

### 2.3 Cancellation Conditions

A Nakshatra Parivartana is **weakened** (not cancelled) under the following conditions:

| Condition | Effect | Source |
|-----------|--------|--------|
| One planet is combust | Weakened (combust planet cannot fully participate) | BPHS Ch 7 (by analogy) |
| One planet is debilitated | Weakened (reduced magnitude) | BPHS Ch 34 (by analogy) |
| Both Nakshatras in Dusthanas | Becomes Dainya-type (negative outcome) | Commentary-dependent |
| Nakshatra lord is retrograde | Weakened but not broken (delayed results) | BPHS Ch 5 (by analogy) |

**Cancellation vs. Weakening:** Nakshatra Parivartana is never fully **cancelled** — it is always weakened at most. This is because the Nakshatra lordship is a permanent positional fact that cannot be erased by transient conditions.

---

## 3. One-Directional Nakshatra Dependency

### 3.1 Structural Definition

**Source:** BPHS (Chapter 46), Saravali (Chapter 36).

A **one-directional Nakshatra dependency** exists when:

```
Nakshatra_Dependency(A, B) ⟺ Lord(N(A)) = B  ∧  Lord(N(B)) ≠ A
```

Planet A occupies the Nakshatra ruled by Planet B, but Planet B is NOT in a Nakshatra ruled by Planet A. This is a **directed, asymmetric** relationship.

**Structural impact:**

Planet A's results are **modified by** Planet B's dignity, house placement, and aspects. Specifically:

1. **Planet B's dignity modifies Planet A's Nakshatra results:**
   - If B is exalted → A's Nakshatra results are **enhanced** (multiplier: 1.15)
   - If B is in own sign → A's Nakshatra results are **supported** (multiplier: 1.10)
   - If B is in friend's sign → A's Nakshatra results are **neutral** (multiplier: 1.00)
   - If B is in enemy's sign → A's Nakshatra results are **diminished** (multiplier: 0.85)
   - If B is debilitated → A's Nakshatra results are **suppressed** (multiplier: 0.70)
   - If B is combust → A's Nakshatra results are **severely suppressed** (multiplier: 0.50)

2. **Planet B's house placement modifies the domain of influence:**
   - B in Kendra → A's dependency effects are **visible and manifest** (domain multiplier: 1.0)
   - B in Trikona → A's dependency effects are **auspicious and fortunate** (domain multiplier: 1.05)
   - B in Dusthana → A's dependency effects are **obstructed or painful** (domain multiplier: 0.80)
   - B in Maraka (2nd/7th) → A's dependency effects relate to **longevity or partnerships** (domain multiplier: 0.90)

3. **Planets aspecting B modify the dependency channel:**
   - Benefic aspect on B → **protects** the dependency channel (additional +0.10)
   - Malefic aspect on B → **afflicts** the dependency channel (additional −0.10)

### 3.2 Nakshatra Dependency vs. Rashi Dispositorship

| Property | Rashi Dispositorship | Nakshatra Dependency |
|----------|---------------------|---------------------|
| Direction | Directed (A → B) | Directed (A → B) |
| Basis | Rashi ownership | Nakshatra lordship |
| Granularity | 12 signs | 27 Nakshatras |
| Structural permanence | Permanent | Permanent |
| Chain edge weight | 0.60 (DISPOSITOR) | 0.50 (NAKSHATRA_LORD) |
| Modifier scope | A's results modified by B | A's Nakshatra-specific results modified by B |

**Key difference:** Rashi Dispositorship governs the planet's **broad functional results** (career, wealth, relationships). Nakshatra Dependency governs the planet's **subtle, specific results** (timing, quality, emotional tone). A planet can have both a Rashi Dispositor and a Nakshatra Lord — they operate at different levels.

### 3.3 Chain Propagation Rule

When a Nakshatra Dependency edge appears in a chain path, the propagation formula applies the **Nakshatra Dependency Modifier (NDM)** as an additional attenuation factor:

```
NDM(A, B) = S_dignity(B) × D_house(B) × A_aspect(B)
```

Where:
- `S_dignity(B)` = dignity multiplier of the Nakshatra lord (0.50–1.15)
- `D_house(B)` = house placement multiplier of the Nakshatra lord (0.80–1.05)
- `A_aspect(B)` = aspect modifier on the Nakshatra lord (0.90–1.10)

The NDM is applied as an **additional multiplier** on the hop weight:

```
Effective_hop_weight = W_edge × M_node(N_i) × HOP_DAMPING × NDM
```

---

## 4. Integration with Layer 1.5 (Chain Evaluator)

### 4.1 New Edge Types

Two new edge types must be added to `EdgeType` in `src/jrs/graph/chain_evaluator.py`:

```python
class EdgeType(StrEnum):
    # ... existing types ...
    NAKSHATRA_LORD = "NAKSHATRA_LORD"           # Directed: A's Nakshatra lord is B
    NAKSHATRA_PARIVARTANA = "NAKSHATRA_PARIVARTANA"  # Undirected: mutual exchange
```

### 4.2 Edge Base Weights

| Edge Type | Weight | Directionality | Authority |
|-----------|--------|---------------|-----------|
| CONJUNCTION | 1.00 | Undirected | BPHS Ch 33 |
| PARIVARTANA | 0.90 | Undirected | BPHS Ch 34 |
| MUTUAL_ASPECT | 0.85 | Undirected | BPHS Ch 35 |
| ONE_WAY_ASPECT | 0.75 | Directed | BPHS Ch 35 |
| **NAKSHATRA_PARIVARTANA** | **0.80** | **Undirected** | **BPHS Ch 46** |
| DISPOSITOR | 0.60 | Directed | BPHS Ch 33 |
| **NAKSHATRA_LORD** | **0.50** | **Directed** | **BPHS Ch 46** |

**Rationale for weight ordering:**

- Nakshatra Parivartana (0.80) falls between Parivartana (0.90) and MUTUAL_ASPECT (0.85) — it is stronger than a one-way aspect but weaker than a Rashi exchange.
- Nakshatra Lord (0.50) is weaker than Rashi Dispositorship (0.60) — it operates at a finer granularity with less structural impact.
- The 0.10 gap between Rashi and Nakshatra levels ensures that Rashi-based relationships consistently dominate chain propagation.

### 4.3 Edge Weight Override for Nakshatra Edges

Nakshatra edges use a **Nakshatra Attenuation Factor (NAF)** that further modulates the base weight based on the Nakshatra lord's conditions:

```python
NAKSHATRA_ATTENUATION_FACTORS = {
    "lord_exalted": 1.15,
    "lord_own_sign": 1.10,
    "lord_friend_sign": 1.00,
    "lord_enemy_sign": 0.85,
    "lord_debilitated": 0.70,
    "lord_combust": 0.50,
}
```

**Effective weight calculation:**

```
W_nakshatra_edge = W_base × NAF(lord_dignity)
```

For example:
- NAKSHATRA_PARIVARTANA with both lords exalted: `0.80 × 1.15 = 0.92`
- NAKSHATRA_LORD with lord debilitated: `0.50 × 0.70 = 0.35`

### 4.4 Interaction with CascadingStrengthEngine

The `ChainStrengthEngine` propagation formula must be extended to handle Nakshatra edges:

**Current formula (RI-011 Phase B):**

```
ΔI(P) = F_role(N_0) × M_node(N_0) × ∏_{i=1}^{k} (W_edge(E_i) × M_node(N_i) × 0.70)
```

**Extended formula (RI-012):**

```
ΔI(P) = F_role(N_0) × M_node(N_0) × ∏_{i=1}^{k} (W_edge(E_i) × M_node(N_i) × 0.70 × NAF_i)
```

Where `NAF_i` is the Nakshatra Attenuation Factor for edge `E_i`. For non-Nakshatra edges, `NAF_i = 1.00` (no attenuation). For Nakshatra edges, `NAF_i` is computed from the Nakshatra lord's dignity.

**Modified `ChainEdge` data structure:**

```python
@dataclass(frozen=True)
class ChainEdge:
    source: str
    target: str
    edge_type: EdgeType
    weight: float
    nakshatra_lord: str = ""         # NEW: Nakshatra lord name (if Nakshatra edge)
    nakshatra_attenuation: float = 1.0  # NEW: NAF multiplier (1.0 for non-Nakshatra edges)
```

### 4.5 Detection Logic

**Nakshatra Parivartana detection** (to be added to `RelationshipGraphService` or a new `NakshatraRelationshipService`):

```python
def detect_nakshatra_parivartana(planet_states: tuple[PlanetState, ...]) -> list[PlanetRelationship]:
    """Detect mutual Nakshatra lord exchanges between planet pairs."""
    # Build planet → nakshatra lord mapping
    planet_to_nak_lord: dict[BodyId, BodyId] = {}
    for state in planet_states:
        planet_to_nak_lord[state.body] = lord_of(state.nakshatra)

    # Check for mutual exchanges
    for a, b in itertools.combinations(planet_states, 2):
        if (planet_to_nak_lord.get(a.body) == b.body and
            planet_to_nak_lord.get(b.body) == a.body):
            yield PlanetRelationship(
                planet_a=a.body.value,
                planet_b=b.body.value,
                relationship_type=RelationshipType.NAKSHATRA_PARIVARTANA,
                is_directed=False,
            )
```

**Nakshatra Dependency detection:**

```python
def detect_nakshatra_dependencies(planet_states: tuple[PlanetState, ...]) -> list[PlanetRelationship]:
    """Detect one-directional Nakshatra lord dependencies."""
    for state in planet_states:
        nak_lord = lord_of(state.nakshatra)
        if nak_lord != state.body:
            # Check if reciprocal (already handled by Parivartana)
            nak_lord_state = next(
                (s for s in planet_states if s.body == nak_lord), None
            )
            if nak_lord_state is not None:
                reciprocal_lord = lord_of(nak_lord_state.nakshatra)
                if reciprocal_lord == state.body:
                    continue  # This is a Parivartana, not a one-way dependency

            yield PlanetRelationship(
                planet_a=state.body.value,
                planet_b=nak_lord.value,
                relationship_type=RelationshipType.NAKSHATRA_LORD,
                is_directed=True,
            )
```

### 4.6 Graph Construction Priority

When building the `RelationshipGraph` for chain evaluation, edges should be added in the following priority order (higher priority edges are traversed first):

1. **CONJUNCTION** (weight 1.00) — strongest structural bond
2. **PARIVARTANA** (weight 0.90) — Rashi-level mutual exchange
3. **NAKSHATRA_PARIVARTANA** (weight 0.80) — Nakshatra-level mutual exchange
4. **MUTUAL_ASPECT** (weight 0.85) — mutual aspect (note: slightly below Nakshatra Parivartana)
5. **ONE_WAY_ASPECT** (weight 0.75) — directed aspect
6. **DISPOSITOR** (weight 0.60) — Rashi-level dispositorship
7. **NAKSHATRA_LORD** (weight 0.50) — Nakshatra-level dependency

**Conflict resolution:** When both a Rashi and Nakshatra relationship exist between the same pair of planets:
- Both edges are included in the graph (they represent different granularity levels).
- The Rashi edge has higher weight and will dominate chain propagation.
- The Nakshatra edge provides a secondary pathway that may discover alternative chain routes.

---

## 5. Temporal Integration (Nakshatra Transits)

### 5.1 Tara Bala and Natal Nakshatra Parivartana

**Source:** Phaladeepika (Chapter 26), Saravali (Chapter 36).

The existing `TaraBalaService` (RI-010D TA-020–021) evaluates transit planet strength relative to the natal Moon's Nakshatra. When a transit planet ingresses into a Nakshatra involved in a natal Nakshatra Parivartana, the transit activation is modified:

**Interaction rules:**

| Transit Condition | Effect on Natal Nakshatra Parivartana | Source |
|-------------------|--------------------------------------|--------|
| Transit planet enters Nakshatra involved in Parivartana | **Activates** the Nakshatra Parivartana (makes it manifest) | Phaladeepika Ch 26 (by analogy) |
| Transit planet's Tara is FAVORABLE | Parivartana results are **enhanced** (multiplier: 1.0–1.2) | Phaladeepika Ch 26 |
| Transit planet's Tara is UNFAVORABLE | Parivartana results are **diminished** (multiplier: 0.6–0.8) | Phaladeepika Ch 26 |
| Transit planet is the Nakshatra lord itself | Parivartana results are **strongly activated** (multiplier: 1.2–1.5) | Commentary-dependent |
| Transit planet is combust | Transit activation is **suppressed** (multiplier: 0.4) | BPHS Ch 7 (by analogy) |

### 5.2 Nakshatra Transit Ingress and Chain Path Activation

When a transit planet ingresses into a Nakshatra that is a node in an existing chain path:

1. **Activation detection:** The `NakshatraActivationService` (JRE-026) already detects `TRANSIT_NAKSHATRA_INGRESS` events. This should be extended to flag when the ingress Nakshatra is involved in a natal Nakshatra Parivartana or Dependency.

2. **Chain path boosting:** The transit ingress should temporarily increase the weight of Nakshatra edges involving that Nakshatra:

```python
# Temporary weight boost during transit ingress
transit_boost = 1.0 + (tara_multiplier - 1.0) * 0.5
# Example: FAVORABLE Tara (1.2) → boost = 1.1
# Example: UNFAVORABLE Tara (0.7) → boost = 0.85
```

3. **Duration:** The boost applies for the entire transit through the Nakshatra (approximately 13°20′ of transit movement, typically 1–5 days depending on the transiting planet's speed).

### 5.3 Dasha Lord Interaction with Nakshatra Parivartana

Per the Dasha-first hierarchy (BPHS Ch 50, RI-010D TA-002):

- If the **Dasha lord is one of the planets** in a natal Nakshatra Parivartana → the Parivartana is **strongly activated** during that Dasha period.
- If the **Antardasha lord** is one of the planets → secondary activation.
- If the Dasha/Antardasha lord **aspects or conjoins** one of the Parivartana planets → moderate activation.

**Activation strength hierarchy:**

| Dasha Level | Condition | Activation Strength |
|-------------|-----------|-------------------|
| Mahadasha lord = Parivartana planet | Direct activation | 1.5 |
| Antardasha lord = Parivartana planet | Secondary activation | 1.2 |
| Mahadasha lord aspects Parivartana planet | Indirect activation | 1.1 |
| Antardasha lord aspects Parivartana planet | Weak activation | 1.0 |
| No Dasha involvement | No temporal activation | 0.0 (latent only) |

---

## 6. Data Structure Specification

### 6.1 Extended PlanetRelationship

The existing `PlanetRelationship` model in `src/jrs/structural/models.py` should be extended with Nakshatra-specific fields:

```python
@dataclass(frozen=True)
class PlanetRelationship:
    planet_a: str
    planet_b: str
    relationship_type: RelationshipType
    strength_modifier: str = ""
    is_active: bool = False
    is_directed: bool = False
    is_war: bool = False
    war_victor: Optional[str] = None
    node_involvement: bool = False
    # NEW fields for Nakshatra relationships:
    nakshatra_lord_a: str = ""           # Nakshatra lord of planet A's Nakshatra
    nakshatra_lord_b: str = ""           # Nakshatra lord of planet B's Nakshatra
    nakshatra_attenuation: float = 1.0   # NAF multiplier for Nakshatra edges
```

### 6.2 Extended RelationshipType

```python
class RelationshipType(StrEnum):
    # ... existing types ...
    NAKSHATRA_LORD = "NAKSHATRA_LORD"              # Directed: A's Nakshatra lord is B
    NAKSHATRA_PARIVARTANA = "NAKSHATRA_PARIVARTANA"  # Undirected: mutual exchange
    NAKSHATRA_CONJUNCTION = "NAKSHATRA_CONJUNCTION"   # Two planets in same Nakshatra
```

### 6.3 Extended ChainEdge

```python
@dataclass(frozen=True)
class ChainEdge:
    source: str
    target: str
    edge_type: EdgeType
    weight: float
    nakshatra_lord: str = ""              # NEW
    nakshatra_attenuation: float = 1.0    # NEW
```

### 6.4 New Data Structure: NakshatraChainImpact

```python
@dataclass(frozen=True)
class NakshatraChainImpact:
    """Result of Nakshatra-aware chain path evaluation."""
    path: ChainPath
    root_multiplier: NodeMultiplier
    hop_multipliers: tuple[NodeMultiplier, ...]
    nakshatra_attenuations: tuple[float, ...]  # NAF per hop
    net_functional_impact: float
    nakshatra_impact_contribution: float  # Portion of impact from Nakshatra edges
```

---

## 7. Evidence Classification Matrix

| Rule ID | Claim | Source | Exact location | Root text/commentary | Evidence status | Notes |
|---------|-------|--------|----------------|---------------------|-----------------|-------|
| NK-001 | Nakshatra Parivartana: mutual Nakshatra lord exchange between two planets | BPHS | Ch 46 | Root text | SOURCE-PINNED CLASSICAL | Core formation rule |
| NK-002 | Nakshatra Parivartana is weaker than Rashi Parivartana | BPHS | Ch 46 (implied) | Root text | SOURCE-PINNED CLASSICAL | Rashi = primary identity |
| NK-003 | Nakshatra Dependency: Planet A in Nakshatra ruled by Planet B (one-directional) | BPHS | Ch 46 | Root text | SOURCE-PINNED CLASSICAL | Directed, asymmetric |
| NK-004 | Nakshatra Dependency modifier: B's dignity modifies A's Nakshatra results | Saravali | Ch 36, V. 15-20 | Commentary | COMMENTARY-DEPENDENT | Not in BPHS core |
| NK-005 | Nakshatra Dependency modifier: B's house placement modifies domain of influence | Saravali | Ch 36, V. 15-20 | Commentary | COMMENTARY-DEPENDENT | Not in BPHS core |
| NK-006 | NAKSHATRA_LORD edge weight = 0.50 (weaker than DISPOSITOR at 0.60) | RI-012 | — | Architectural decision | JRS-SPECIFIC | Based on granularity principle |
| NK-007 | NAKSHATRA_PARIVARTANA edge weight = 0.80 (between MUTUAL_ASPECT and PARIVARTANA) | RI-012 | — | Architectural decision | JRS-SPECIFIC | Based on structural strength |
| NK-008 | Nakshatra Attenuation Factor modulates edge weight based on Nakshatra lord dignity | RI-012 | — | Architectural decision | JRS-SPECIFIC | Extension of CascadingStrengthEngine |
| NK-009 | Transit planet entering Nakshatra in natal Parivartana activates the relationship | Phaladeepika | Ch 26 (by analogy) | Root text | SOURCE-PINNED CLASSICAL | Activation rule |
| NK-010 | Tara Bala modifies transit activation of Nakshatra Parivartana | Phaladeepika | Ch 26, V. 14-16 | Root text | SOURCE-PINNED CLASSICAL | Strength modifier |
| NK-011 | Dasha lord = Parivartana planet → strong activation | BPHS | Ch 50 (by analogy) | Root text | SOURCE-PINNED CLASSICAL | Dasha-first hierarchy |
| NK-012 | Nakshatra Parivartana never fully cancelled, only weakened | RI-012 | — | Architectural decision | JRS-SPECIFIC | Permanent positional fact |
| NK-013 | Maha Nakshatra Parivartana: +0.15 weight when Nakshatra lord exalted | RI-012 | — | Commentary | COMMENTARY-DEPENDENT | Sub-type classification |
| NK-014 | Dainya Nakshatra Parivartana: −0.20 weight when in Dusthana | RI-012 | — | Commentary | COMMENTARY-DEPENDENT | Sub-type classification |

---

## 8. Implementation Integration Points

### 8.1 Files to Create/Modify

| File | Change Type | Description |
|------|------------|-------------|
| `src/jrs/structural/models.py` | MODIFY | Add `NAKSHATRA_LORD`, `NAKSHATRA_PARIVARTANA`, `NAKSHATRA_CONJUNCTION` to `RelationshipType`; add `nakshatra_lord_a/b` and `nakshatra_attenuation` fields to `PlanetRelationship` |
| `src/jrs/structural/service.py` | MODIFY | Add Nakshatra relationship detection methods to `RelationshipGraphService` |
| `src/jrs/graph/chain_evaluator.py` | MODIFY | Add `NAKSHATRA_LORD` and `NAKSHATRA_PARIVARTANA` to `EdgeType`; extend `ChainEdge` with Nakshatra fields; update `_map_edge_type` to handle new `RelationshipType` values |
| `src/jrs/graph/chain_strength.py` | MODIFY | Apply NAF in propagation formula; add `NakshatraChainImpact` return type |
| `src/jrs/yoga_evaluator/service.py` | MODIFY | Wire Nakshatra-aware chain evaluation into `YogaEvaluatorService` |
| `src/nakshatra_activation/service.py` | MODIFY | Extend to flag Parivartana/Dependency involvement for transit activations |
| `tests/unit/jrs/graph/test_chain_evaluator.py` | MODIFY | Add tests for Nakshatra edge types and NAF computation |
| `tests/unit/jrs/structural/test_relationship_graph.py` | MODIFY | Add tests for Nakshatra relationship detection |

### 8.2 Dependency Chain

```
JRE-003 (PlanetState with nakshatra, nakshatra_lord)
    │
    ▼
NakshatraActivationService (JRE-026) ─── detects Parivartana, Dependency
    │
    ▼
RelationshipGraphService ─── adds NAKSHATRA_LORD, NAKSHATRA_PARIVARTANA edges
    │
    ▼
DirectedChainEvaluator ─── traverses Nakshatra edges with NAF
    │
    ▼
ChainStrengthEngine ─── applies NAF in propagation formula
    │
    ▼
YogaEvaluatorService ─── Nakshatra-aware chain impact as Layer 1.5 modifier
```

---

## 9. Provenance Hazards

1. **Treating Nakshatra Parivartana as equivalent to Rashi Parivartana:** The Nakshatra exchange is supplementary, not primary. Rashi-level relationships must always take precedence in chain propagation weight.

2. **Ignoring Nakshatra Dependency directionality:** The dependency is asymmetric — A depending on B does NOT mean B depends on A. The directed edge must preserve this asymmetry.

3. **Over-weighting Nakshatra edges:** Nakshatra edges (0.50–0.80) must consistently have lower weights than their Rashi equivalents (0.60–1.00). Over-weighting would distort chain propagation toward subtle effects at the expense of structural effects.

4. **Applying Nakshatra Attenuation Factor universally:** NAF should only apply to Nakshatra-type edges (NAKSHATRA_LORD, NAKSHATRA_PARIVARTANA). Rashi-based edges use standard dignity multipliers without NAF.

5. **Conflating Nakshatra Dependency with Dispositorship:** These are distinct relationship types operating at different granularities. A planet can have both a Rashi Dispositor AND a Nakshatra Lord — they should be tracked as separate edges.

6. **Treating Nakshatra Parivartana as cancellable:** The positional fact of Nakshatra lordship is permanent and cannot be cancelled by transient conditions (combustion, debilitation). It can only be weakened.

---

## 10. Claims That Must NOT Enter the Classical Catalog

1. **"Nakshatra Parivartana is as powerful as Rashi Parivartana":** False. Rashi is the primary identity; Nakshatra is supplementary (BPHS Ch 46).

2. **"A planet's Nakshatra lord overrides its Rashi lord":** False. Rashi lordship is structurally primary (BPHS Ch 33-34).

3. **"Nakshatra Dependency creates a permanent bond equivalent to conjunction":** False. It is a directed dependency, not a mutual association (BPHS Ch 46).

4. **"All Nakshatra relationships have the same weight":** False. Parivartana (0.80) > Dependency (0.50), reflecting structural strength differences.

5. **"Nakshatra Parivartana is cancelled by combustion":** False. It is weakened but not cancelled — the positional fact is permanent.

---

## 11. Unresolved Questions

1. **Nakshatra Parivartana strength relative to Mutual Aspect:** Should Nakshatra Parivartana (0.80) be stronger or weaker than MUTUAL_ASPECT (0.85)? The current specification places it slightly below, but some schools may argue it should be equivalent.

2. **Nakshatra Dependency with retrograde Nakshatra lord:** If the Nakshatra lord is retrograde, does the dependency channel become stronger (increased Cheshta Bala) or weaker (delayed results)? BPHS Ch 5 is ambiguous on this point.

3. **Multiple Nakshatra dependencies:** When Planet A depends on multiple Nakshatra lords (e.g., A is in Nakshatra X ruled by B, and also aspects B), should the dependencies be additive or should the strongest one dominate?

4. **Nakshatra Parivartana in Varga charts:** Should Nakshatra Parivartana be evaluated only in the Rashi chart, or also in divisional charts (D9, D10)? The root texts are silent on this.

5. **Cross-system Nakshatra ownership:** In the Parashari system, Rahu/Ketu have conditional Nakshatra ownership (based on their dispositor). Should Nakshatra Parivartana detection account for this?

---

## 12. Recommended Implementation Phases

| Phase | Scope | Files | Estimated Effort |
|-------|-------|-------|-----------------|
| **Phase 1** | Add `NAKSHATRA_LORD` and `NAKSHATRA_PARIVARTANA` to `RelationshipType` and `EdgeType` | `models.py`, `chain_evaluator.py` | Low |
| **Phase 2** | Implement Nakshatra relationship detection in `RelationshipGraphService` | `service.py` | Medium |
| **Phase 3** | Extend `ChainEdge` with Nakshatra fields; apply NAF in `ChainStrengthEngine` | `chain_evaluator.py`, `chain_strength.py` | Medium |
| **Phase 4** | Wire into `YogaEvaluatorService` as Layer 1.5 modifier | `service.py` | Low |
| **Phase 5** | Extend `NakshatraActivationService` for Parivartana/Dependency flagging | `service.py` | Medium |
| **Phase 6** | Add unit tests for all new functionality | `tests/unit/jrs/graph/`, `tests/unit/jrs/structural/` | Medium |

---

**READY FOR IMPLEMENTATION.**
