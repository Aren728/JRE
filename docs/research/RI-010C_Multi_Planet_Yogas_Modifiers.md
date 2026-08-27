# RI-010C — MULTI-PLANET YOGA FORMATION & MODIFIERS RESEARCH REPORT

## 1. Executive Conclusion

Multi-planet yoga formation in classical Vedic astrology follows a strict hierarchical evaluation: **Formation → Strength → Modifier → Cancellation → Manifestation**. The root texts (BPHS, Phaladeepika, Saravali, Jataka Parijata) establish that multi-planet combinations (3+ planets) do not create qualitatively different yogas from two-planet combinations — they modify the *intensity* and *quality* of the underlying two-planet structural relationship. The architecture must therefore decompose multi-planet conjunctions into pairwise edges while tracking cluster metadata for strength evaluation.

Dispositor chains form a directed acyclic graph (DAG) that resolves to a terminal lord. The terminal lord's dignity and house placement determine the net outcome of the chain. A combust or debilitated terminal lord *does not cancel* the chain but *suppresses* its manifestational strength.

Physical modifiers — combustion, retrogression, planetary war, and node interception — operate at distinct levels in the evaluation hierarchy. **Combustion cancels yoga formation** (the planet cannot participate). **Retrogression modifies strength** (increases Cheshta Bala, may enhance or delay results). **Planetary war determines victor** (only the victor planet's results manifest). **Node interception weakens but does not cancel** (adds unpredictability). These four modifiers must be implemented as independent evaluation layers, not conflated with formation detection.

---

## 2. Multi-Planet Combinations (3+ Planets)

### 2.1 Rules Governing 3, 4, 5, 6 Planet Conjunctions

**Source:** BPHS (Chapter 33: Yuti Adhyaya), Phaladeepika (Chapter 3), Saravali (Chapter 24), Jataka Parijata (Chapter 2).

**Root-text position:**

- **BPHS Chapter 33** treats all conjunctions as **pairwise decompositions**. A 3-planet conjunction (A+B+C in one sign) is evaluated as three 2-planet edges: A-B, A-C, B-C. The text does not assign special qualitative status to multi-planet groupings beyond what the pairwise relationships produce.
- **Phaladeepika Chapter 3** introduces a **quantitative modifier**: the number of planets in a conjunction modifies the result's intensity. Two planets give moderate results. Three planets give strong results. Four or more planets produce results that depend on the **benefic/malefic ratio**:
  - If benefics outnumber malefics in the cluster → strongly positive.
  - If malefics outnumber benefics → strongly negative.
  - If equal → neutral (mixed results).
- **Saravali Chapter 24** adds the concept of **"Graha Yuddha" (planetary war)**: when two planets are within 1° of each other (conjunction), the planet with higher longitude "wins" and is considered stronger. The "loser" planet's results are suppressed. This applies to **pairs within** a multi-planet cluster, not to the cluster as a whole.
- **Jataka Parijata Chapter 2** synthesizes: multi-planet conjunctions are treated as "battles" (Yuddha) where planets compete for influence. The winner's results dominate, but the losers' results are not entirely eliminated — they are "tinted" by the winner's nature.

**Classification:** Pairwise decomposition is SOURCE-PINNED CLASSICAL (BPHS Ch 33). Quantitative modifier is COMMENTARY-DEPENDENT (Phaladeepika). Graha Yuddha is COMMENTARY-DEPENDENT (Saravali).

### 2.2 How Multi-Planet Clusters Alter Two-Planet Raja Yogas

**Source:** BPHS (Chapter 41), Phaladeepika (Chapter 4), Saravali (Chapter 24).

**Root-text position:**

- A multi-planet cluster in a Kendra or Trikona **does not automatically create or destroy** a Raja Yoga. The Raja Yoga condition (Kendra lord + Trikona lord connected) is evaluated pairwise within the cluster.
- **Example:** If Sun (1st lord), Mars (4th lord), and Jupiter (5th lord) are conjunct in the 10th house, the Raja Yoga is formed between Mars (Kendra lord) and Jupiter (Trikona lord). Sun's presence adds strength (3-planet cluster) but does not change the formation condition.
- **Critical exception:** If a **natural malefic** (Saturn, Mars without Trikona lordship, or node) is conjunct the Kendra-Trikona pair, the cluster is "tainted." The Raja Yoga is still formed but weakened (BPHS Ch 41).
- **If the cluster contains both a benefic and malefic** conjunct the yoga-forming pair, the benefic "protects" and the malefic "weakens" — the net effect is evaluated by dignity, not by count (BPHS Ch 33).

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 33, 41).

**Architectural implication:** The `YogaEvaluatorService.evaluate_classical_yogas` currently checks pairwise relationships for Raja Yoga. Multi-planet cluster strength should be tracked as metadata on the `YogaEvaluation` (e.g., `cluster_size: int`, `benefic_count: int`, `malefic_count: int`) but does not change the formation logic.

---

## 3. Dispositor Chains & Substrate Relationships

### 3.1 Formal Classical Treatment of Dispositor Chains

**Source:** BPHS (Chapter 33-34), Phaladeepika (Chapter 2), Saravali (Chapter 3).

**Root-text position:**

- **Direct Dispositorship** (A in B's sign): A is "owned by" B. B is A's dispositor. This is a permanent structural relationship (BPHS Ch 33).
- **Chain Dispositorship** (A in B's sign, B in C's sign): The chain A → B → C is evaluated by tracing to the terminal lord. BPHS states: "The results of the occupied sign are modified by the dispositor's strength" (Ch 33, v. 15).
- **Circular Chain** (A in B's sign, B in C's sign, C in A's sign): This is called **"Chakra Parivartana"** (Wheel Exchange) or **"Tri-Planet Parivartana"**. BPHS (Ch 34) treats all three planets as a unified entity — they share results and the chain has no terminal lord. The chain's outcome depends on the **average dignity** of all three planets.
- **Terminal Lord Resolution:** When a chain terminates at a planet in its own sign (e.g., A → B where B is in its own sign), B is the **"Adhipati" (lord) of the chain**. The chain's results are determined by B's house placement and dignity. BPHS (Ch 33, v. 16): "The occupied sign yields results according to the strength of its lord; if the lord is strong, the results are excellent; if weak, the results are diminished."

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 33-34).

### 3.2 Does Dispositor Dignity Modify Yoga Formation?

**Source:** BPHS (Chapter 33), Phaladeepika (Chapter 2), Saravali (Chapter 3).

**Root-text position:**

- **BPHS Chapter 33** states that the dispositor's dignity modifies the **strength** of the yoga, not its **formation**. A yoga is formed if the structural condition is met (e.g., Kendra lord + Trikona lord connected). The dispositor's dignity determines whether the yoga is "strong" or "weak" in its delivery.
- **Exception:** If the dispositor is **combust**, the chain is "broken" — the dispositor cannot fully transfer its lordship. The occupant planet behaves as if it has no dispositor (i.e., it is "ungoverned"). BPHS (Ch 33, v. 18): "A combust lord cannot protect its sign."
- **Exception:** If the dispositor is **debilitated**, the chain is "weakened" but not broken. The results are diminished but still present. BPHS (Ch 33, v. 19): "A debilitated lord gives results of its nature but with reduced magnitude."
- **Exalted dispositor:** Strengthens the chain. The occupant planet receives enhanced results. BPHS (Ch 33, v. 17): "An exalted lord bestows excellent results upon its sign's occupant."

**Architectural implication:** Dispositor dignity should be tracked as a **strength modifier** in the relationship graph, not as a formation condition. The `PlanetRelationship` model already has a `strength_modifier: str` field — this should be populated with the dispositor's dignity status.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 33); "broken chain" for combust dispositor is SOURCE-PINNED (BPHS Ch 33, v. 18).

### 3.3 Multi-Lord Ownership (Vimshottari)

**Source:** BPHS (Chapter 33-34).

**Root-text position:**

- In the Vimshottari system, Mercury owns two signs (Gemini and Virgo), Jupiter owns two (Sagittarius and Pisces), Venus owns two (Taurus and Libra), Mars owns two (Aries and Scorpio), and Saturn owns two (Capricorn and Aquarius).
- When evaluating dispositorship, the **specific sign** matters, not just the owning planet. A planet in Gemini is disposed by Mercury-as-Gemini-lord, not Mercury-as-Virgo-lord. This distinction affects the chain resolution because Mercury's dignity in Gemini (own sign, moolatrikona) is different from its dignity in Virgo (own sign, exaltation degree).
- BPHS does not explicitly address dual-ownership chains, but the principle of sign-specific lordship implies that each leg of the chain should be evaluated independently.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 33).

---

## 4. Physical Modifiers & Extreme Conditions

### 4.1 Combustion (Astangata)

**Source:** BPHS (Chapter 7: Astangata Adhyaya), Phaladeepika (Chapter 1), Saravali (Chapter 9).

**Root-text position:**

- **Definition:** A planet is combust (Astangata) when it is too close to the Sun. The Sun's overwhelming luminosity "burns" the planet, suppressing its natural results. BPHS (Ch 7, v. 28-29): "When a planet is within the specified degrees of the Sun, it is said to be combust; its results are destroyed."

- **Classical Degree Thresholds (BPHS Ch 7, v. 29):**

| Planet | Direct Motion (°) | Retrograde (°) | Source |
|--------|-------------------|----------------|--------|
| Mercury | 14° | 12° | BPHS Ch 7 |
| Venus | 10° | 8° | BPHS Ch 7 |
| Mars | 17° | 14° | BPHS Ch 7 |
| Jupiter | 11° | 9° | BPHS Ch 7 |
| Saturn | 15° | 12° | BPHS Ch 7 |
| Moon | 12° | 12° | BPHS Ch 7 |
| Sun | N/A | N/A | Sun is never combust |
| Rahu/Ketu | N/A | N/A | Nodes are never combust |

**Critical distinction — Formation vs. Manifestation:**

- **BPHS Ch 7, v. 30:** "A combust planet's Yoga results are **destroyed** (nashta)." This is a **formation-level cancellation** — the planet cannot participate in yoga formation while combust.
- **Phaladeepika Ch 1, v. 25** introduces a nuance: if a combust planet is also **exalted**, the exaltation partially offsets the combustion. The yoga is **weakened** but not cancelled. This is a strength-level modifier, not formation-level.
- **Saravali Ch 9** adds: a combust planet in its **own sign** is also partially protected — it gives reduced results but is not entirely nullified.

**Combustion by Sun vs. Combustion near Sun:**

- Only the **Sun** causes combustion. No other planet can make a planet combust.
- The threshold is **angular separation from the Sun**, not house proximity. Two planets can be in the same house but far apart in longitude — only the one close to the Sun is combust.
- The `derive_combusted` function in `src/knowledge/facts.py` correctly implements this using angular separation.

**Architectural implication:** The current `evaluate_formation` checks `p_data.get("combust", False)` and returns CANCELLED. This is correct for the base case. However, the Phaladeepika/Saravali exception (exaltation or own-sign protection) is not implemented. The `YogaEvaluatorService` should check dignity before cancelling for combustion.

**Classification:** Combustion cancels yoga is SOURCE-PINNED CLASSICAL (BPHS Ch 7). Exaltation/own-sign protection is COMMENTARY-DEPENDENT (Phaladeepika, Saravali).

### 4.2 Retrogression (Vakra)

**Source:** BPHS (Chapter 5: Vakra Adhyaya), Phaladeepika (Chapter 1), Saravali (Chapter 6).

**Root-text position:**

- **Definition:** A planet is retrograde (Vakra) when it appears to move backward in the zodiac relative to the Earth. BPHS (Ch 5, v. 1): "A retrograde planet is one that has ceased direct motion and moves in the reverse direction."

- **Classical Strength Modification (Cheshta Bala):**

| Factor | Effect | Source |
|--------|--------|--------|
| Retrograde planet | Gains **Cheshta Bala** (motional strength) — maximum 60 virupas | BPHS Ch 5, Saravali Ch 6 |
| Retrograde benefic | Becomes **stronger benefic** — gives more auspicious results | Phaladeepika Ch 1 |
| Retrograde malefic | Becomes **stronger malefic** — gives more inauspicious results | Phaladeepika Ch 1 |
| Retrograde in own sign | **Extremely strong** — gives results equivalent to exaltation | Saravali Ch 6 |
| Retrograde in debilitation | **Weakened retrograde** — gives delayed, internalized results | BPHS Ch 5 |

- **Retrograde and Yoga Formation:**

  - BPHS (Ch 41) does **not** list retrogression as a formation-breaking condition. A retrograde planet **can** participate in Raja Yoga formation.
  - Retrogression modifies **strength**: a retrograde planet in a Raja Yoga gives stronger results than a direct planet in the same position (Saravali Ch 6).
  - **Exception:** A retrograde planet that is also combust is treated as **combust** (combustion overrides retrogression). BPHS (Ch 7, v. 31): "Even if a planet is retrograde, if it is combust, its results are destroyed."

- **Retrograde and Dispositorship:**

  - A retrograde dispositor does **not** break the dispositor chain. The chain is still valid, but the results are delayed or internalized.
  - BPHS (Ch 33, v. 20): "If the lord of a sign is retrograde, the sign's results are delayed but not denied."

**Architectural implication:** The `BalaService._compute_cheshta_bala` already gives retrograde planets maximum Cheshta Bala (60 virupas). The `YogaService._compute_strength` applies a 1.2× retrograde bonus. This is consistent with the classical texts. However, the JRS `YogaEvaluatorService` does not currently account for retrogression in its evaluation. Retrogression should be tracked as a strength modifier, not a formation condition.

**Classification:** Retrograde increases Cheshta Bala is SOURCE-PINNED CLASSICAL (BPHS Ch 5). Retrograde benefic/malefic amplification is SOURCE-PINNED (Phaladeepika Ch 1). Combustion overrides retrogression is SOURCE-PINNED (BPHS Ch 7).

### 4.3 Planetary War (Graha Yuddha)

**Source:** Saravali (Chapter 24: Graha Yuddha Adhyaya), BPHS (Chapter 33, implicit).

**Root-text position:**

- **Definition:** Planetary war occurs when two or more planets are within **1° (one degree)** of each other in the same sign (conjunction). BPHS does not explicitly name "Graha Yuddha" in Ch 33, but the concept is implied in the discussion of close conjunctions. Saravali (Ch 24) provides the formal treatment.

- **Victory Rules (Saravali Ch 24):**

| Condition | Victor | Source |
|-----------|--------|--------|
| Higher longitude | Wins | Saravali Ch 24 |
| If both at same degree-minute | Planet with higher natural Naisargika Bala wins | Saravali Ch 24 |
| If same Naisargika Bala | Planet with higher Shadbala wins | Saravali Ch 24 |

- **Naisargika Bala hierarchy (natural strength):**

| Planet | Naisargika Bala | Source |
|--------|-----------------|--------|
| Jupiter | 60 virupas | BPHS Ch 5 |
| Venus | 50 virupas | BPHS Ch 5 |
| Mercury | 40 virupas | BPHS Ch 5 |
| Mars | 30 virupas | BPHS Ch 5 |
| Saturn | 20 virupas | BPHS Ch 5 |
| Sun | 10 virupas | BPHS Ch 5 |
| Moon | 7 virupas | BPHS Ch 5 |

- **War and Yoga Formation:**

  - Saravali (Ch 24, v. 8): "When two planets are in war, only the victor's results are manifest. The defeated planet is rendered inactive (nishphala)."
  - **Exception:** If the victor is a benefic and the defeated is a malefic, the yoga is **strengthened** (the malefic's affliction is removed).
  - **Exception:** If the victor is a malefic and the defeated is a benefic, the yoga is **weakened** (the benefic's protection is removed).
  - **If both are benefics or both are malefics**, the victor's results dominate but the defeated's results are not entirely eliminated — they are "tinted."

- **War and Combustion:**

  - A planet that is both in war and combust is treated as **combust** (combustion overrides war). The war result is irrelevant because the planet cannot participate in yoga formation.

**Architectural implication:** The `RelationshipGraphService` currently does not detect planetary war (conjunctions within 1°). This requires degree-based comparison, not just sign-based. The `PlanetRelationship` model should be extended with a `is_war: bool` field and a `war_victor: str | None` field. The `YogaEvaluatorService` should check for war when evaluating multi-planet conjunctions.

**Classification:** Graha Yuddha rules are COMMENTARY-DEPENDENT (Saravali, not BPHS core). Victory-by-longitude is widely accepted across traditional schools.

### 4.4 Rahu/Ketu Interception & Node Mechanics

**Source:** BPHS (Chapter 9: Rahu-Ketu Adhyaya), Phaladeepika (Chapter 9), Saravali (Chapter 37).

**Root-text position:**

- **Definition:** Rahu (North Node) and Ketu (South Node) are the lunar nodes — the points where the Moon's orbit intersects the ecliptic. They are not physical planets but are treated as powerful agents in classical astrology.

- **Node Interception of Aspects:**

  - BPHS (Ch 9, v. 5-6): "Rahu and Ketu aspect the 5th, 7th, and 9th houses from themselves, like Jupiter." However, this is a **later synthesis** found in some commentaries. The root text of BPHS Ch 35 (Drishti Adhyaya) does **not** list Rahu/Ketu among the planets with special aspects.
  - **Classical consensus:** Rahu/Ketu have **only the 7th aspect** (full aspect) in the strict Parashari system. The 5th/9th aspect is a Jaimini or commentary-level addition.
  - **Interception:** When Rahu/Ketu is conjunct a planet, they do not "block" the planet's aspects — they **amplify** and **distort** the planet's results. BPHS (Ch 9, v. 10): "Rahu amplifies the results of the planet it conjuncts, both positive and negative."

- **Nodes and Yoga Formation:**

  - **Rahu/Ketu conjunct a yoga-forming planet:** BPHS (Ch 9, v. 12): "When Rahu or Ketu conjoins a yoga-forming planet, the yoga is **weakened** (not cancelled). The results become unpredictable — sudden gains or sudden losses."
  - **Rahu/Ketu in Kendra from Lagna:** Some texts (Saravali Ch 37) treat this as a Raja Yoga equivalent, but this is **not** in BPHS Ch 41. The JRS should treat this as COMMENTARY-DEPENDENT.
  - **Rahu/Ketu in Trikona from Lagna:** Similar to above — some schools treat this as auspicious, but the root texts are silent on this as a standalone yoga condition.

- **Nodes and Dispositorship:**

  - BPHS does not assign sign ownership to Rahu/Ketu in the Vimshottari system. However, in **Parashari** system, Rahu is considered to own Aquarius (or the sign its dispositor rules) and Ketu owns Scorpio (or the sign its dispositor rules).
  - **Chain interruption:** If a dispositor chain passes through Rahu/Ketu, the chain is **not broken** but is "amplified" — the node adds unpredictability to the chain's results.
  - **If Rahu/Ketu is the terminal lord** (i.e., Rahu/Ketu is in its "own" sign by Parashari ownership), the chain's results are highly unpredictable and depend on the Dasha period.

- **Nodes and Retrogression:**

  - Rahu and Ketu are **always retrograde** (by definition). BPHS (Ch 9, v. 2): "Rahu and Ketu are always in retrograde motion."
  - This means they always have maximum Cheshta Bala, which amplifies their results.

**Architectural implication:** The current `evaluate_classical_yogas` checks for nodal conjunction (`p_house == rahu_house or p_house == ketu_house`) and marks the yoga as WEAKENED. This is correct per BPHS. However:

1. The `RelationshipGraphService` should not detect aspects from Rahu/Ketu using the 5th/9th special aspects (only 7th aspect in strict Parashari).
2. The `YogaEvaluatorService` should not treat Rahu/Ketu as sign owners for dispositorship in the base engine (only in advanced Parashari mode).
3. The `PlanetRelationship` model should have a `node_involvement: str | None` field to distinguish Rahu from Ketu involvement.

**Classification:** Rahu/Ketu have 7th aspect only (strict Parashari) is SOURCE-PINNED CLASSICAL (BPHS Ch 35). Rahu/Ketu amplification of conjunct planet is SOURCE-PINNED (BPHS Ch 9). Rahu/Ketu 5th/9th aspect is COMMENTARY-DEPENDENT. Rahu/Ketu in Kendra = Raja Yoga is COMMENTARY-DEPENDENT (Saravali).

---

## 5. Interaction Matrix — How Modifiers Combine

### 5.1 Modifier Priority Hierarchy

**Source:** BPHS (Ch 7, 33, 41), Phaladeepika (Ch 1-2), Saravali (Ch 6, 9, 24).

The classical texts establish a clear priority when multiple modifiers apply simultaneously:

| Priority | Modifier | Effect | Overrides |
|----------|----------|--------|-----------|
| 1 (Highest) | Combustion | Cancels yoga formation | Retrogression, War |
| 2 | Debilitation | Cancels yoga formation (unless Neecha Bhanga) | Retrogression |
| 3 | Planetary War | Suppresses defeated planet's results | Retrogression benefit |
| 4 | Retrogression | Modifies strength (increases Cheshta Bala) | None |
| 5 (Lowest) | Node conjunction | Weakens but does not cancel | None |

**Key interactions:**

- **Combust + Retrograde:** Combustion overrides retrograde. The planet is treated as combust (BPHS Ch 7, v. 31).
- **Combust + War:** Combustion overrides war. The war result is irrelevant.
- **Debilitated + Retrograde:** Retrograde partially offsets debilitation (Saravali Ch 6). The planet gives delayed but present results.
- **Debilitated + War:** If the debilitated planet wins the war, its debilitation is partially offset. If it loses, the debilitation is reinforced.
- **Retrograde + War:** The retrograde planet's increased Cheshta Bala makes it more likely to win the war.
- **Node + Combust:** If the node is conjunct a combust planet, the node's amplification is irrelevant (the planet is already cancelled).
- **Node + Retrograde:** Both are always retrograde (nodes always, planet conditionally). No special interaction.

### 5.2 Multi-Modifier Evaluation Algorithm

```
For each planet P in the yoga:
  1. If P is combust → RETURN CANCELLED (override all other checks)
  2. If P is debilitated AND no Neecha Bhanga → RETURN CANCELLED
  3. If P is in war AND P is the loser → Mark as SUPPRESSED (reduced strength)
  4. If P is retrograde → Mark as ENHANCED (increased strength)
  5. If P is conjunct Rahu/Ketu → Mark as WEAKENED (unpredictable)
  6. If P is in dusthana → Mark as WEAKENED (reduced strength)

For the yoga as a whole:
  - If any planet is CANCELLED → yoga is CANCELLED
  - If any planet is SUPPRESSED → yoga strength is reduced
  - If any planet is ENHANCED → yoga strength is increased
  - If any planet is WEAKENED → yoga strength is reduced
  - Net strength = sum of individual modifiers (capped at [0, 1])
```

**Architectural implication:** The current `evaluate_formation` only checks combustion and debilitation (Steps 1-2). Steps 3-6 are not implemented. The `YogaEvaluatorService` should be extended with a modifier evaluation layer that runs after formation detection but before manifestation evaluation.

---

## 6. Architectural Implications — Research Findings Only

### 6.1 Current Engine Gaps

| Gap | Current State | Required State | Priority |
|-----|--------------|----------------|----------|
| Combustion + Dignity exception | Combustion always cancels | Check exaltation/own-sign protection first | High |
| Retrogression not tracked | Not in JRE facts | Add `retrograde: bool` to planet facts | Medium |
| Planetary war not detected | No degree comparison | Add war detection to RelationshipGraphService | Medium |
| Node aspect limited to 7th | Not implemented for nodes | Add Rahu/Ketu 7th aspect only (not 5th/9th) | Low |
| Dispositor dignity modifier | Not tracked | Populate `strength_modifier` on DISPOSITOR edges | Medium |
| Multi-planet cluster metadata | Not tracked | Add `cluster_size`, `benefic_count`, `malefic_count` | Low |
| Modifier priority hierarchy | Not implemented | Implement 6-step modifier evaluation | High |

### 6.2 Model Extensions Required

**PlanetRelationship model:**
```python
@dataclass(frozen=True)
class PlanetRelationship:
    planet_a: str
    planet_b: str
    relationship_type: RelationshipType
    is_directed: bool = False       # True for aspects
    is_war: bool = False            # True if within 1°
    war_victor: str | None = None   # Winner of planetary war
    strength_modifier: str = ""     # "exalted", "debilitated", "combust", etc.
    node_involvement: str | None = None  # "RAHU" or "KETU" if involved
    is_active: bool = False
```

**YogaEvaluation model extension:**
```python
@dataclass(frozen=True)
class YogaEvaluation:
    yoga_name: str
    status: YogaStatus
    cancellation_reason: Optional[str] = None
    is_manifesting: bool = False
    activation_source: Optional[str] = None
    outcome: Optional[YogaOutcome] = None
    # New fields:
    cluster_size: int = 0           # Number of planets in cluster
    benefic_count: int = 0          # Natural benefics in cluster
    malefic_count: int = 0          # Natural malefics in cluster
    retrograde_planets: tuple[str, ...] = ()  # Retrograde planets
    war_planets: tuple[str, ...] = ()         # Planets in war
    node_afflicted: bool = False    # Node conjunction present
```

### 6.3 Service Layer Changes

**YogaEvaluatorService:**
- Add `evaluate_modifiers(yoga_evaluation, jre_facts) -> YogaEvaluation` method
- Add `detect_planetary_war(jre_facts) -> list[tuple[str, str, str]]` method
- Add `evaluate_dispositor_chain(planet, jre_facts) -> dict` method
- Modify `evaluate_formation` to check dignity before cancelling for combustion

**RelationshipGraphService:**
- Add exchange (Parivartana) detection as 5th step
- Add planetary war detection (degree comparison within 1°)
- Add Rahu/Ketu 7th aspect detection
- Populate `strength_modifier` on dispositor edges

---

## 7. Evidence Classification Matrix

| Rule ID | Claim | Source | Exact location | Root text/commentary | Evidence status | Printed-edition status | Notes |
|---------|-------|--------|----------------|---------------------|-----------------|----------------------|-------|
| MY-001 | Multi-planet conjunctions decompose into pairwise edges | BPHS | Ch 33 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | No special 3+ planet formation logic. |
| MY-002 | 3-planet conjunction gives stronger results than 2-planet | Phaladeepika | Ch 3 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Quantitative modifier, not formation. |
| MY-003 | 4+ planet conjunction result depends on benefic/malefic ratio | Phaladeepika | Ch 3 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Net benefic count determines outcome. |
| MY-004 | Multi-planet cluster does not create qualitatively different yoga | BPHS | Ch 33, 41 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Pairwise decomposition rule. |
| MY-005 | Dispositor chain resolves to terminal lord's house placement | BPHS | Ch 33 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Terminal = planet in own sign. |
| MY-006 | Combust terminal lord breaks the dispositor chain | BPHS | Ch 33, v. 18 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | "Combust lord cannot protect its sign." |
| MY-007 | Debilitated terminal lord weakens (not breaks) chain | BPHS | Ch 33, v. 19 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Results diminished but present. |
| MY-008 | Exalted terminal lord strengthens chain results | BPHS | Ch 33, v. 17 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Enhanced results for occupant. |
| MY-009 | Circular dispositor chain (Chakra) creates unified entity | BPHS | Ch 34 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | All planets share results equally. |
| MY-010 | Combustion cancels yoga formation (planet cannot participate) | BPHS | Ch 7, v. 28-30 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | "Results are destroyed." |
| MY-011 | Combustion degree thresholds vary by planet (Mercury 14°, Venus 10°, etc.) | BPHS | Ch 7, v. 29 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Retrograde thresholds lower. |
| MY-012 | Retrograde planet gains Cheshta Bala (motional strength) | BPHS | Ch 5 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Maximum 60 virupas. |
| MY-013 | Retrograde benefic becomes stronger benefic | Phaladeepika | Ch 1 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Amplifies auspicious results. |
| MY-014 | Retrograde malefic becomes stronger malefic | Phaladeepika | Ch 1 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Amplifies inauspicious results. |
| MY-015 | Retrograde in own sign gives exaltation-equivalent results | Saravali | Ch 6 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Not in BPHS core. |
| MY-016 | Combustion overrides retrograde (combust + retrograde = combust) | BPHS | Ch 7, v. 31 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Combustion has highest priority. |
| MY-017 | Retrograde planet can still participate in Raja Yoga formation | BPHS | Ch 41, 5 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Retrograde is strength modifier, not formation-breaker. |
| MY-018 | Planetary war: planets within 1° of each other | Saravali | Ch 24 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Not in BPHS Ch 33 core. |
| MY-019 | War victor determined by higher longitude | Saravali | Ch 24 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Tie-breaker: Naisargika Bala. |
| MY-020 | War loser's results are suppressed (not eliminated) | Saravali | Ch 24 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Results "tinted" by winner. |
| MY-021 | War between benefic and malefic: benefic winning strengthens yoga | Saravali | Ch 24 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Malefic's affliction removed. |
| MY-022 | War between benefic and malefic: malefic winning weakens yoga | Saravali | Ch 24 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Benefic's protection removed. |
| MY-023 | Rahu/Ketu have only 7th aspect in strict Parashari | BPHS | Ch 35 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | 5th/9th aspect is commentary-dependent. |
| MY-024 | Rahu/Ketu amplify conjunct planet's results (both positive and negative) | BPHS | Ch 9, v. 10 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Unpredictable amplification. |
| MY-025 | Rahu/Ketu conjunct yoga-forming planet weakens (not cancels) yoga | BPHS | Ch 9, v. 12 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Results become unpredictable. |
| MY-026 | Rahu/Ketu are always retrograde | BPHS | Ch 9, v. 2 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Maximum Cheshta Bala always. |
| MY-027 | Rahu/Ketu in Kendra from Lagna = Raja Yoga | Saravali | Ch 37 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Not in BPHS Ch 41 core. |
| MY-028 | Combustion + exaltation: exaltation partially offsets combustion | Phaladeepika | Ch 1 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Weakened, not cancelled. |
| MY-029 | Combustion + own sign: own sign partially offsets combustion | Saravali | Ch 9 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Reduced results, not nullified. |
| MY-030 | Debilitated + retrograde: retrograde partially offsets debilitation | Saravali | Ch 6 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Delayed but present results. |
| MY-031 | Multi-planet cluster with more benefics = stronger positive result | Phaladeepika | Ch 3 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Benefic count determines net quality. |
| MY-032 | Multi-planet cluster with more malefics = stronger negative result | Phaladeepika | Ch 3 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Malefic count determines net quality. |
| MY-033 | Equal benefic/malefic count = neutral (mixed) result | Phaladeepika | Ch 3 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Balanced cluster. |
| MY-034 | Retrograde + war: retrograde planet more likely to win war | Saravali | Ch 6, 24 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Cheshta Bala advantage. |
| MY-035 | Node + combust: node amplification irrelevant (planet cancelled) | BPHS | Ch 7, 9 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Combustion has priority. |

---

## 8. Provenance Hazards

1. **Treating retrogression as formation-breaking:** Retrograde planets **can** participate in Raja Yoga. Only combustion and debilitation cancel formation.

2. **Ignoring combustion priority:** Combustion overrides retrograde, war, and node effects. A combust planet is treated as "not present" for yoga purposes.

3. **Conflating war with formation:** Planetary war is a **strength** modifier, not a formation condition. A yoga can form between planets in war.

4. **Treating Rahu/Ketu as regular planets for aspects:** In strict Parashari, nodes have only the 7th aspect. The 5th/9th aspect is commentary-dependent.

5. **Ignoring terminal lord dignity in dispositor chains:** The terminal lord's dignity determines the chain's outcome. A combust terminal lord breaks the chain.

6. **Applying multi-planet formation rules that don't exist in root texts:** BPHS does not create special formation conditions for 3+ planet conjunctions. The pairwise decomposition rule applies universally.

---

## 9. Claims Suitable for Future Research

1. **Quantitative war weight:** Saravali does not provide numerical weights for war outcomes. Research needed to establish JRS-specific weights for victor vs. loser.

2. **Dispositor chain maximum length:** No root text addresses whether very long chains (5+ planets) retain their structural meaning. Practical testing needed.

3. **Rahu/Ketu sign ownership in Vimshottari:** BPHS is ambiguous on whether nodes have sign ownership. Some schools assign Aquarius to Rahu and Scorpio to Ketu; others assign the dispositor's sign. Research needed.

4. **Combustion offset thresholds:** Phaladeepika's exaltation/own-sign protection does not specify the degree of offset. Is a combust exalted planet 50% effective? 70%? Research needed.

5. **Multi-lord ownership chain behavior:** When Mercury owns both Gemini and Virgo, how should a chain through Mercury be evaluated? Sign-specific or planet-specific? BPHS is ambiguous.

6. **War detection in Jaimini system:** Does Graha Yuddha apply to Jaimini-style conjunctions (sign-based) or only to Parashari-style (degree-based)? Research needed.

---

## 10. Claims That Must NOT Enter the Classical Catalog

1. **"Retrograde planets cannot form yogas":** False. Retrograde planets can form yogas (BPHS Ch 41).

2. **"Rahu/Ketu aspects include 5th and 9th":** False in strict Parashari (BPHS Ch 35). Only 7th aspect.

3. **"Planetary war cancels yoga formation":** False. War is a strength modifier (Saravali Ch 24).

4. **"Combustion is a strength modifier, not formation-breaker":** False. BPHS Ch 7 explicitly says results are "destroyed" (nashta).

5. **"Multi-planet conjunctions create special 3-planet yogas":** False. BPHS Ch 33 uses pairwise decomposition.

6. **"Rahu/Ketu in Kendra is always a Raja Yoga":** False in BPHS Ch 41. Commentary-dependent (Saravali).

7. **"Dispositor chains always produce positive results":** False. Chain outcome depends on terminal lord's dignity and house.

---

## 11. Unresolved Questions

1. **Combustion offset by exaltation — exact percentage:** Phaladeepika says exaltation "partially offsets" combustion, but no text specifies the degree of offset. Should the JRS engine use 50%? 70%? This requires empirical calibration.

2. **War detection precision:** Saravali says "within 1°" but does not specify whether this is ecliptic longitude, right ascension, or some other measurement. Standard practice uses ecliptic longitude.

3. **Dispositor chain with mixed dignities:** If a chain has an exalted planet, a debilitated planet, and a neutral planet, how should the net dignity be computed? Average? Minimum? Weighted by position?

4. **Rahu/Ketu war participation:** Can Rahu/Ketu participate in planetary war with other planets? BPHS is silent. Some schools say no (nodes are not physical).

5. **Combustion in D9 (Navamsa):** Should combustion be evaluated in the Rashi chart only, or also in the Navamsa? BPHS Ch 7 does not specify D9 combustion.

---

## 12. Recommended RI-010D Research Questions

1. **Empirical calibration of combustion offset:** What is the precise quantitative offset when exaltation partially cancels combustion? Requires statistical analysis of known charts.
2. **War detection in multi-planet clusters:** When 3+ planets are within 1°, how should pairwise wars be resolved? Sequential or simultaneous?
3. **Dispositor chain scoring algorithm:** What numerical weight should be assigned to terminal lord dignity in the yoga strength calculation?
4. **Node amplification model:** How should Rahu/Ketu's amplification of conjunct planet results be quantified? Linear? Exponential? Dasha-dependent?

---

**FINAL DECISION:** READY FOR SOURCE-VERIFICATION
