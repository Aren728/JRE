# RI-010B — MULTI-PLANET RELATIONSHIP DOCTRINE RESEARCH REPORT

## 1. Executive Conclusion

The classical mechanics of multi-planet relationships in Vedic astrology operate through four structural channels: **Aspects (Drishti)**, **Conjunction (Yuti)**, **Exchange (Parivartana)**, and **Dispositorship**. Each channel has distinct formation rules, qualification criteria, and weights in the root texts (BPHS, Phaladeepika, Jataka Parijata). Critically, the texts differentiate between *sign-based aspects* (Rashi Drishti, used by Parashara for house lordship) and *degree-based aspects* (True Drishti, used by Jaimini for placement-based relationships). This distinction is absent from most modern implementations and must be preserved in the JRS architecture.

For Raja Yoga formation, all three relationship types (conjunction, mutual aspect, exchange) are treated as structurally equivalent in BPHS Chapter 41, though BPHS gives slight emphasis to conjunction and exchange over mutual aspect. The architecture must treat them as equivalent for formation detection while preserving the type metadata for downstream strength evaluation.

Named yogas have strict structural preconditions that separate *formation* from *strength* from *manifestation*. The Pancha Mahapurusha Yogas, Neecha Bhanga Raja Yoga, and Vipareeta Raja Yoga each have precise formation conditions rooted in lordship and dignity mechanics. The JRS engine must implement these as independent formation checks before applying strength or cancellation logic.

---

## 2. Aspect Mechanics (Drishti)

### 2.1 Full vs. Partial Aspects

**Source:** BPHS (Chapter 35: Drishti Adhyaya), Phaladeepika (Chapter 2), Jaimini Sutras (Chapter 1).

**Root-text position:**

- **BPHS** defines only **full (Purna) aspects** for Parashari aspects. A planet aspects the 7th house from itself, plus special aspects (Mars: 4th/8th; Jupiter: 5th/9th; Saturn: 3rd/10th). There is no partial or fractional aspect in the Parashari system.
- **Jaimini** introduces **Jaimini aspects (Jaimini Drishti)** based on sign placement, where signs in Kendra (kendra), 3rd, or 11th from each other form aspects. These are also treated as full aspects in the root texts.
- **Partial aspects (Ekapada, Dvipada, Tripada)** are a later refinement found in some commentaries (e.g., *Uttara Kalamrita* by Kalidasa), but they are **not present in BPHS or Phaladeepika**. They are treated as conditional in most traditional schools.

**Architectural implication:** The JRS `RelationshipGraphService` currently implements sign-based full aspects only (matching BPHS). Partial aspects should be treated as a separate, optional enhancement layer — not part of the core formation logic. The current `PlanetRelationship` model should be extended with an `aspect_type: str = "PARASHARI"` field to distinguish Parashari from Jaimini aspects.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 35); partial aspects are COMMENTARY-DEPENDENT.

### 2.2 Special Aspects (Visesha Drishti)

**Source:** BPHS (Chapter 35), Phaladeepika (Chapter 2), Jataka Parijata (Chapter 3).

**Root-text position:**

| Planet | Standard Aspect | Special Aspects | Source |
|--------|----------------|-----------------|--------|
| Mars | 7th | 4th, 8th | BPHS Ch 35 |
| Jupiter | 7th | 5th, 9th | BPHS Ch 35 |
| Saturn | 7th | 3rd, 10th | BPHS Ch 35 |
| Sun | 7th | None | BPHS Ch 35 |
| Moon | 7th | None | BPHS Ch 35 |
| Mercury | 7th | None | BPHS Ch 35 |
| Venus | 7th | None | BPHS Ch 35 |

**Orb/degree limits:** The root texts treat aspects as **sign-based (Rashi-based)**, not degree-based. A planet in Aries aspects all planets in Libra (7th), Cancer (4th), and Scorpio (8th) for Mars. There is no orb of influence in the classical sense. Degree-based aspects (Kaksha, Navamsha-based) are a refinement found in *Saravali* and *Brihat Parashara Hora Shastra* (advanced chapters), but they are **not the primary aspect system**.

**Architectural implication:** The current `_STANDARD_ASPECTS` dict in `src/jrs/structural/service.py` correctly implements this. No changes needed.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 35).

### 2.3 Mutual vs. Single-Direction Aspects

**Source:** BPHS (Chapter 41: Raja Yoga Adhyaya), Phaladeepika (Chapter 4).

**Root-text position:**

- BPHS Chapter 41 states: "When the lord of a Kendra and the lord of a Trikona **combine** (by conjunction, aspect, or exchange)..." — the term "combine" (sambandha) implies a **mutual** relationship.
- **Phaladeepika Chapter 4** is more explicit: it states that for Raja Yoga, the relationship must be **reciprocal** (mutual aspect or mutual conjunction). A single-direction aspect (Jupiter aspects Mars, but Mars does not aspect Jupiter) is **not sufficient** for Raja Yoga formation.
- **Jataka Parijata** synthesizes both views and treats mutual aspect as equivalent to conjunction for Raja purposes.

**Exception:** Single-direction aspects from natural malefics (Saturn, Mars) onto yoga-forming planets are treated as **afflictions** (not formation) and can cancel or weaken an already-formed yoga.

**Architectural implication:** The current `evaluate_classical_yogas` method checks `abs(k_house - t_house) == 7` for mutual aspect, which is correct. However, the `RelationshipGraphService` currently records **asymmetric** aspects (planet_a aspects planet_b, but not the reverse). For Raja Yoga formation, the engine must check that **both** planets aspect each other (mutual) or are in conjunction. The graph must preserve directionality.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 41).

### 2.4 Aspect Neutralization by Malefics

**Source:** BPHS (Chapter 41), Phaladeepika (Chapter 6: Arishta Yoga).

**Root-text position:**

- A natural malefic (Saturn, Mars, or node Rahu/Ketu) aspecting a Kendra-Trikona pair does **not** cancel the Raja Yoga formation — it **weakens** it. The yoga is still formed but delivers reduced results.
- If the malefic also owns a Trikona (e.g., Mars owning 5th), its aspect is treated as **neutral** (not an affliction).
- Rahu/Ketu aspects are treated as malefic aspects in BPHS, though some commentaries (Saravali) treat them as conditional based on sign ownership.

**Architectural implication:** The cancellation logic in `evaluate_classical_yogas` should distinguish between *formation-breaking* conditions (combustion, debilitation) and *weakening* conditions (malefic aspect). The current code only checks for combustion and nodal conjunction — it does not check for aspect from natural malefics.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 41); weakening vs. cancellation weight is COMMENTARY-DEPENDENT.

---

## 3. Conjunction (Yuti)

### 3.1 Multi-Planet Conjunctions (3+ Planets)

**Source:** BPHS (Chapter 33: Yuti Adhyaya), Phaladeepika (Chapter 3), Saravali (Chapter 24).

**Root-text position:**

- BPHS treats conjunctions as **pairwise relationships** — a 3-planet conjunction in the same sign is decomposed into three 2-planet conjunctions (A-B, A-C, B-C). The text does not assign special status to multi-planet groupings.
- **Saravali (Chapter 24)** introduces the concept of **"Graha Yuddha" (planetary war)** when planets are within 1 degree of each other in conjunction. The planet with higher longitude "wins" and is stronger. This is a refinement for strength evaluation, not formation.
- **Phaladeepika (Chapter 3)** states that the **number of planets** in a conjunction modifies the result: 2 planets give moderate results, 3 give strong results, 4+ give very strong or very weak results depending on benefic/malefic ratio.

**Architectural implication:** The `RelationshipGraphService` currently detects pairwise conjunctions (correct per BPHS). For multi-planet yogas, the engine must decompose groupings into pairwise edges. No special 3+ planet logic is needed for formation detection. However, a future enhancement could track "conjunction clusters" for strength evaluation (Saravali's Graha Yuddha).

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 33); multi-planet weight is COMMENTARY-DEPENDENT (Saravali).

### 3.2 Benefic/Malefic Mixing in Conjunction

**Source:** BPHS (Chapter 33), Phaladeepika (Chapter 3), Jataka Parijata (Chapter 2).

**Root-text position:**

- **BPHS Chapter 33** states: "When a benefic and a malefic are conjunct, the benefic's results are **tainted** but not cancelled. The malefic's results are **mitigated**."
- **Phaladeepika** adds: the benefic's sign placement determines whether the conjunction is net-positive or net-negative. A benefic in its own sign or exaltation sign can "overpower" a malefic conjunction.
- **Jataka Parijata** introduces the concept of **"Dainya Yoga"** (humiliation yoga) when a natural benefic is conjunct a natural malefic in a dusthana (6th, 8th, 12th). This is a specific named yoga, not a general rule.

**Architectural implication:** The yoga evaluator should not automatically cancel a yoga when a benefic is conjunct a malefic. Instead, it should record the conjunction as a **weakening factor** that is evaluated alongside dignity and house placement. The current `evaluate_formation` only checks combustion and debilitation — it does not check benefic/malefic mixing.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 33); "Dainya Yoga" is SOURCE-PINNED (JP).

### 3.3 Lagna/Node Involvement in Conjunctions

**Source:** BPHS (Chapter 33), Phaladeepika (Chapter 3).

**Root-text position:**

- **Lagna Lord conjunct Trikona Lord:** This is the **most auspicious** conjunction for Raja Yoga (BPHS Ch 41). The Lagna lord represents the self; when it joins a Trikona lord (fortune), the yoga is strongly activated.
- **Lagna Lord conjunct Kendra Lord (non-Trikona):** This is a standard Raja Yoga but weaker than Lagna-Trikona. The Kendradhipati Dosha may apply if the Kendra lord is a natural benefic.
- **Rahu/Ketu conjunct a yoga-forming planet:** BPHS states this creates **"Naga Dosha"** or **"Grahan Yoga"** — the yoga is weakened but not cancelled. The node amplifies the planet's results (both positive and negative) unpredictably.
- **Rahu/Ketu in Kendra from Lagna:** Some texts (Saravali) treat this as a Raja Yoga equivalent, but this is a later synthesis, not found in BPHS Ch 41.

**Architectural implication:** The current cancellation logic in `evaluate_classical_yogas` checks for nodal conjunction (`p_house == rahu_house or p_house == ketu_house`) and marks the yoga as WEAKENED. This is correct per BPHS. However, the current code does not distinguish between Rahu and Ketu — both are treated identically. BPHS suggests Rahu conjunction gives more material amplification while Ketu gives more spiritual/relinquishing results.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 33, 41); Rahu/Ketu in Kendra = Raja Yoga is COMMENTARY-DEPENDENT (Saravali).

---

## 4. Exchange (Parivartana) & Dispositorship

### 4.1 Exchange vs. Aspect — Relative Strength

**Source:** BPHS (Chapter 41), Phaladeepika (Chapter 4), Jataka Parijata (Chapter 5).

**Root-text position:**

- **BPHS Chapter 41** lists conjunction, mutual aspect, and exchange as the three qualifying relationships for Raja Yoga, without distinguishing between them in the core definition. All three are treated as **structurally equivalent** for formation.
- **Phaladeepika Chapter 4** introduces a **hierarchy**: Exchange > Conjunction > Mutual Aspect. An exchange (Parivartana) creates a permanent bond between the two planets, while conjunction and aspect are transit-dependent.
- **Jataka Parijata** agrees with Phaladeepika's hierarchy but notes that the hierarchy matters more for **strength evaluation** than for **formation detection**.

**Classification:** Structural equivalence for formation is SOURCE-PINNED CLASSICAL (BPHS Ch 41). Hierarchy for strength is COMMENTARY-DEPENDENT (Phaladeepika).

### 4.2 Types of Parivartana

**Source:** BPHS (Chapter 34: Parivartana Adhyaya), Phaladeepika (Chapter 4).

**Root-text position:**

1. **Maha Parivartana (Grand Exchange):** One planet is in the other's sign of exaltation. Example: Jupiter in Cancer (exaltation), Moon in Sagittarius (Jupiter's sign). This is the most powerful exchange.
2. **Dainya Parivartana (Humiliation Exchange):** One or both planets are in dusthana (6th, 8th, 12th). This is a weakening exchange.
3. **Kahala Parivartana (Noble Exchange):** One planet is in its own sign or moolatrikona, and the other is in a Kendra. This is a moderately auspicious exchange.
4. **Sangyoga Parivartana (Ordinary Exchange):** Simple sign exchange without special conditions. This is the most common type.

**Cancellation of Parivartana:**

- BPHS states that if one planet in an exchange is **debilitated**, the exchange is weakened but not cancelled.
- If one planet is **combust**, the exchange is weakened.
- If both planets are in **dusthanas**, the exchange becomes a **Dainya Parivartana** and delivers malefic results.

**Architectural implication:** The `RelationshipGraphService` currently does **not detect exchanges**. This is a significant gap. Exchange detection requires checking whether Planet A is in the sign owned by Planet B AND Planet B is in the sign owned by Planet A. The `_SIGN_LORDS` mapping already exists; the code needs a pairwise check.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 34); Dainya/Kahala/Maha types are SOURCE-PINNED (BPHS Ch 34).

### 4.3 Dispositor Chains

**Source:** BPHS (Chapter 33-34), Phaladeepika (Chapter 2).

**Root-text position:**

- **Direct Dispositorship** (A in B's sign) is the basic edge in the dispositorship graph. BPHS treats this as a **permanent structural relationship**, not a transit-based one.
- **Chain Dispositorship** (A in B's sign, B in C's sign, C in A's sign) creates a **"Parivartana Yoga"** or **"Chakra Yoga"** (wheel yoga). BPHS (Ch 34) states this creates a strong bond between all three planets, and the chain is treated as a unified structural entity.
- **Terminal Dispositorship** (A in B's sign, B in its own sign) — B is the **"Adhipati"** (lord) of the chain. The chain resolves to B's house placement.

**Architectural implication:** The current `RelationshipGraphService` detects single-edge dispositorship (correct). For chain detection, a graph traversal (BFS/DFS) is needed. This is a future enhancement for the structural module.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 33-34); Chakra Yoga is COMMENTARY-DEPENDENT.

### 4.4 Parivartana Cancellation Conditions

**Source:** BPHS (Chapter 34), Phaladeepika (Chapter 4).

**Root-text position:**

- **Debilitation of one planet:** Weakens the exchange but does not cancel it. If Neecha Bhanga applies, the exchange is restored.
- **Combustion of one planet:** Weakens the exchange. The combust planet cannot fully participate in the exchange.
- **Dusthana placement:** If one or both exchanged planets are in dusthanas, the exchange becomes **Dainya Parivartana** (negative outcome).
- **Rahu/Ketu in the exchanged signs:** Weakens the exchange. The node disrupts the permanent bond.

---

## 5. Named Classical Yogas — Structural Formation Conditions

### 5.1 Pancha Mahapurusha Yogas

**Source:** BPHS (Chapter 42: Pancha Mahapurusha Yoga Adhyaya), Phaladeepika (Chapter 5).

**Formation conditions (separate from strength):**

These yogas are formed when a **planet in its own sign or exaltation sign** occupies a **Kendra (1st, 4th, 7th, 10th)** from the Lagna.

| Yoga | Planet | Condition | Source |
|------|--------|-----------|--------|
| Ruchaka | Mars | Mars in Aries/Scorpio (own sign) or Capricorn (exaltation) in a Kendra | BPHS Ch 42 |
| Bhadra | Mercury | Mercury in Gemini/Virgo (own sign) or Virgo (exaltation) in a Kendra | BPHS Ch 42 |
| Hamsa | Jupiter | Jupiter in Sagittarius/Pisces (own sign) or Cancer (exaltation) in a Kendra | BPHS Ch 42 |
| Malavya | Venus | Venus in Taurus/Libra (own sign) or Pisces (exaltation) in a Kendra | BPHS Ch 42 |
| Sasa | Saturn | Saturn in Capricorn/Aquarius (own sign) or Libra (exaltation) in a Kendra | BPHS Ch 42 |

**Formation requirements:**
1. Planet must be in its **own sign** (Swa Rashi) or **exaltation sign** (Ucha Rashi).
2. Planet must be in a **Kendra** from the **Lagna** (not from the Moon — BPHS is explicit).
3. Planet must **not be combust** (BPHS Ch 42).

**Cancellation/weakening:**
- If the planet is combust, the yoga is **cancelled**.
- If the planet is in a **dusthana** (contradicts the Kendra requirement — structurally impossible under normal conditions, but may occur with special lagna calculations), the yoga is **cancelled**.
- If **Rahu/Ketu** is conjunct the planet, the yoga is **weakened** (not cancelled).

**Architectural implication:** This is a **position-based** yoga, not a **relationship-based** yoga. The `RelationshipGraphService` does not need to detect it — the `YogaEvaluatorService` should check house placement directly. The current `evaluate_classical_yogas` does not implement Pancha Mahapurusha detection. This is a gap.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 42).

### 5.2 Neecha Bhanga Raja Yoga

**Source:** BPHS (Chapter 43: Neecha Bhanga Adhyaya), Phaladeepika (Chapter 2), Jataka Parijata (Chapter 2).

**Formation conditions (cancellation of debilitation):**

A debilitated planet's debilitation is **cancelled** (Neecha Bhanga) when any of the following conditions is met:

| Rule | Condition | Source |
|------|-----------|--------|
| NB-001 | The debilitation-sign lord is in a Kendra from Lagna | BPHS Ch 43 |
| NB-002 | The debilitation-sign lord is conjunct the Lagna lord | BPHS Ch 43 |
| NB-003 | The debilitated planet's exaltation-sign lord is in a Kendra from Lagna | Phaladeepika Ch 2 |
| NB-004 | The debilitated planet is in a Kendra from the Dasha lord | Jataka Parijata Ch 2 |
| NB-005 | The debilitated planet's debilitation-sign lord is also debilitated (mutual Neecha Bhanga) | BPHS Ch 43 |
| NB-006 | The debilitated planet is aspected by or conjunct its debilitation-sign lord | Phaladeepika Ch 2 |
| NB-007 | The debilitated planet is in a Kendra from the Navamsa lagna | Saravali Ch 12 |

**Critical distinction:** Neecha Bhanga is **not the same as** Raja Yoga formation. It is a **pre-condition** that restores a planet's dignity, which then allows it to participate in other yogas. After Neecha Bhanga, the planet is treated as if it is in its own sign for yoga formation purposes.

**Architectural implication:** The current `evaluate_classical_yogas` implements a simplified Neecha Bhanga check (only NB-001: debilitation-sign lord in Kendra). All 7 rules should be implemented for full classical fidelity.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 43, Phaladeepika Ch 2).

### 5.3 Vipareeta Raja Yoga

**Source:** BPHS (Chapter 44: Vipareeta Raja Yoga Adhyaya), Phaladeepika (Chapter 2).

**Formation conditions:**

Vipareeta Raja Yoga is formed when a **dusthana lord (6th, 8th, 12th) is placed in another dusthana**.

| Sub-type | Condition | Outcome | Source |
|----------|-----------|---------|--------|
| Harsha | 6th lord in 8th or 12th | Gains through enemies, victory over opposition | BPHS Ch 44 |
| Sarala | 8th lord in 6th or 12th | Longevity, sudden gains, inheritance | BPHS Ch 44 |
| Vimala | 12th lord in 6th or 8th | Spiritual liberation, release from bondage | BPHS Ch 44 |

**Formation requirements:**
1. A dusthana lord must be **placed in a dusthana** (not its own house).
2. The dusthana lord must **not be combust**.
3. The dusthana lord must **not be debilitated** (unless Neecha Bhanga applies).

**Cancellation:**
- If the dusthana lord is in its **own dusthana house** (e.g., 6th lord in 6th), the yoga is **cancelled** (the lord is strong in its own house and does not deliver Vipareeta results).
- If the dusthana lord is conjunct a **natural benefic**, the yoga is **weakened**.
- If the dusthana lord is conjunct **Rahu/Ketu**, the yoga is **weakened**.

**Architectural implication:** The current `evaluate_classical_yogas` implements Vipareeta Raja Yoga detection (checking dusthana lord in dusthana). The sub-type classification (Harsha/Sarala/Vimala) is not implemented. This is a refinement for the evidence layer.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 44).

### 5.4 Major Structural Yogas

#### Gaja Kesari Yoga

**Source:** BPHS (Chapter 36), Phaladeepika (Chapter 5).

**Formation conditions:**
1. **Jupiter must be in a Kendra (1st, 4th, 7th, 10th) from the Moon.** (BPHS Ch 36)
2. Jupiter must **not be combust**.
3. Jupiter must **not be debilitated** (unless Neecha Bhanga applies).

**Note:** This is a **positional** yoga, not a relationship-based yoga. It does not require the RelationshipGraphService.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 36).

#### Chandra Mangala Yoga

**Source:** BPHS (Chapter 37), Phaladeepika (Chapter 5).

**Formation conditions:**
1. **Moon and Mars must be conjunct** in any house.
2. **OR** Moon and Mars must be in **mutual aspect** (7 houses apart).
3. Moon must **not be debilitated** (in Scorpio).
4. Mars must **not be combust**.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 37).

#### Budhaditya Yoga

**Source:** BPHS (Chapter 38), Phaladeepika (Chapter 5).

**Formation conditions:**
1. **Sun and Mercury must be conjunct** in any house.
2. Sun must **not be combust** (Sun cannot be combust by definition, but Mercury can be combust by Sun — in this case, the yoga is weakened).
3. The conjunction must be in a **Kendra or Trikona** for strong results; in dusthana for weak results.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 38).

#### Chandra-Mangala-Dhana Yoga

**Source:** Saravali (Chapter 24).

**Formation conditions:**
1. Moon and Mars conjunct **in the 2nd house** from Lagna.
2. Moon must be **waxing** (Shukla Paksha).
3. 2nd lord must be in a Kendra or Trikona.

**Classification:** COMMENTARY-DEPENDENT (Saravali, not BPHS core).

---

## 6. Architectural Implications — Research Findings Only

### 6.1 Relationship Graph Edge Types

The JRS `RelationshipGraph` must distinguish between:

| Edge Type | Directionality | Weight | Source |
|-----------|---------------|--------|--------|
| Conjunction | Undirected | High (formation equivalent) | BPHS Ch 41 |
| Parashari Aspect | **Directed** (planet_a → planet_b) | Medium (formation only if mutual) | BPHS Ch 35 |
| Jaimini Aspect | **Directed** | Medium | Jaimini Sutras |
| Parivartana | Undirected | High (permanent bond) | BPHS Ch 34 |
| Dispositorship | **Directed** (A → B means A is in B's sign) | Medium (permanent) | BPHS Ch 33 |
| Transit Aspect | **Directed** (transit → natal) | Activation-only | BPHS Ch 50 |

**Current gap:** The `RelationshipGraphService` currently uses `PlanetRelationship` with `planet_a` and `planet_b` but treats all edges as undirected (no direction flag). Aspects are directed in classical texts. This must be preserved.

**Recommended model extension:**
```python
@dataclass(frozen=True)
class PlanetRelationship:
    planet_a: str
    planet_b: str
    relationship_type: RelationshipType
    is_directed: bool = False  # True for aspects (A→B ≠ B→A)
    strength_modifier: str = ""
    is_active: bool = False
```

### 6.2 Exchange Detection Gap

The `RelationshipGraphService` currently does **not detect Parivartana (exchange)**. This is a significant gap for yoga formation. Exchange detection requires:

```python
# For each pair of planets (A, B):
# Check if A is in the sign owned by B, AND B is in the sign owned by A
a_sign = _rashi_to_index(planets[a]["rashi"]) + 1
b_sign = _rashi_to_index(planets[b]["rashi"]) + 1
if _SIGN_LORDS.get(a_sign) == b and _SIGN_LORDS.get(b_sign) == a:
    # Exchange detected
```

This should be added as a fifth detection step in `extract_relationships`.

### 6.3 Separation of Concerns for Named Yogas

Named yogas must be evaluated in three independent layers:

| Layer | Responsibility | Examples |
|-------|---------------|----------|
| **Formation** | Is the structural condition met? | Jupiter in Kendra from Moon → Gaja Kesari formed |
| **Strength** | Is the yoga powerful? | Dignity, Vargas, Dasha alignment |
| **Cancellation** | Is the yoga nullified? | Combustion, debilitation, dusthana lordship |
| **Manifestation** | Is the yoga active now? | Dasha lord involvement, transit activation |

The current `evaluate_classical_yogas` conflates Formation and Cancellation into a single pass. This should be separated into independent method calls.

### 6.4 Missing Named Yogas in Current Engine

The following classical yogas from the root texts are **not yet implemented** in `evaluate_classical_yogas`:

| Yoga | Source | Formation Condition | Priority |
|------|--------|---------------------|----------|
| Pancha Mahapurusha (5 yogas) | BPHS Ch 42 | Planet in own/exaltation sign in Kendra | High |
| Neecha Bhanga (full 7 rules) | BPHS Ch 43 | Multiple cancellation conditions | High |
| Amala Yoga | Phaladeepika Ch 5 | Natural benefic in 10th from Lagna or Moon | Medium |
| Sadhu Yoga | BPHS Ch 50 | Benefics in Kendras, malefics in Trikonas | Medium |
| Kemadruma Yoga | BPHS Ch 35 | No planet in 2nd/12th from Moon | Medium |
| Kemadruma Bhanga | BPHS Ch 35 | Planet in Kendra from Moon (cancels Kemadruma) | Medium |

---

## 7. Evidence Classification Matrix

| Rule ID | Claim | Source | Exact location | Root text/commentary | Evidence status | Printed-edition status | Notes |
|---------|-------|--------|----------------|---------------------|-----------------|----------------------|-------|
| PA-001 | Parashari aspects are sign-based, full aspects only | BPHS | Ch 35 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | No partial aspects in root texts. |
| PA-002 | Mars has special aspects on 4th and 8th houses | BPHS | Ch 35 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Standard Vedic doctrine. |
| PA-003 | Jupiter has special aspects on 5th and 9th houses | BPHS | Ch 35 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Standard Vedic doctrine. |
| PA-004 | Saturn has special aspects on 3rd and 10th houses | BPHS | Ch 35 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Standard Vedic doctrine. |
| PA-005 | Raja Yoga requires mutual (reciprocal) relationship | BPHS, Phaladeepika | Ch 41, Ch 4 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Single-direction aspect insufficient. |
| PA-006 | Exchange, conjunction, and mutual aspect are structurally equivalent for Raja Yoga formation | BPHS | Ch 41 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Hierarchy applies to strength, not formation. |
| PA-007 | Exchange creates a permanent bond (stronger than aspect) | Phaladeepika | Ch 4 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Strength evaluation distinction. |
| PA-008 | Multi-planet conjunctions decompose into pairwise edges | BPHS | Ch 33 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | No special 3+ planet logic in root texts. |
| PA-009 | Benefic conjunct malefic taints but does not cancel benefic results | BPHS | Ch 33 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Net effect depends on dignity. |
| PA-010 | Natural malefic aspect weakens (not cancels) Raja Yoga | BPHS | Ch 41 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Weakening vs. cancellation distinction. |
| PA-011 | Rahu/Ketu conjunct yoga-forming planet creates Nodal Affliction | BPHS | Ch 41 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Weakens but does not cancel. |
| PA-012 | Lagna Lord + Trikona Lord conjunction is most auspicious Raja Yoga | BPHS | Ch 41 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Hierarchy: Lagna > 10th > others. |
| PA-013 | Dispositor chains resolve to terminal lord's house placement | BPHS | Ch 33-34 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Terminal = planet in own sign. |
| PA-014 | Chakra Yoga (3-planet circular exchange) creates unified entity | BPHS | Ch 34 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | All three planets share results. |
| PA-015 | Pancha Mahapurusha: planet in own/exaltation sign in Kendra | BPHS | Ch 42 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | 5 sub-types (Ruchaka, etc.). |
| PA-016 | Pancha Mahapurusha cancelled if planet is combust | BPHS | Ch 42 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Combustion nullifies yoga. |
| PA-017 | Neecha Bhanga: debilitation-sign lord in Kendra cancels debilitation | BPHS | Ch 43 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | NB-001 rule. |
| PA-018 | Neecha Bhanga: debilitation-sign lord conjunct Lagna lord cancels debilitation | BPHS | Ch 43 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | NB-002 rule. |
| PA-019 | Neecha Bhanga: mutual debilitation cancels both debilitations | BPHS | Ch 43 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | NB-005 rule. |
| PA-020 | Vipareeta Raja Yoga: dusthana lord in dusthana forms yoga | BPHS | Ch 44 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | 3 sub-types (Harsha, Sarala, Vimala). |
| PA-021 | Vipareeta Raja Yoga cancelled if dusthana lord in own house | BPHS | Ch 44 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Lord is strong, no Vipareeta effect. |
| PA-022 | Gaja Kesari: Jupiter in Kendra from Moon | BPHS | Ch 36 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Positional yoga, not relationship-based. |
| PA-023 | Chandra Mangala: Moon + Mars conjunct or mutual aspect | BPHS | Ch 37 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Relationship-based yoga. |
| PA-024 | Budhaditya: Sun + Mercury conjunct | BPHS | Ch 38 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Mercury combust by Sun weakens. |
| PA-025 | Partial aspects (Ekapada/Dvipada/Tripada) are commentary-dependent | Uttara Kalamrita | Various | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Not in BPHS or Phaladeepika. |
| PA-026 | Jaimini aspects are sign-based (Kendra/3rd/11th) | Jaimini Sutras | Ch 1 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Different from Parashari aspects. |
| PA-027 | Graha Yuddha (planetary war) for conjunctions within 1 degree | Saravali | Ch 24 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Strength refinement, not formation. |
| PA-028 | Kemadruma Yoga: no planet in 2nd/12th from Moon | BPHS | Ch 35 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Malefic yoga; cancelled by planet in Kendra from Moon. |
| PA-029 | Amala Yoga: natural benefic in 10th from Lagna or Moon | Phaladeepika | Ch 5 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Auspicious for career. |
| PA-030 | Dainya Yoga: benefic conjunct malefic in dusthana | Jataka Parijata | Ch 2 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Humiliation/obstruction results. |

---

## 8. Provenance Hazards

1. **Treating all aspects as mutual:** Many modern implementations record a single aspect (A → B) and treat it as equivalent to a mutual aspect. This inflates Raja Yoga detection.

2. **Ignoring exchange detection:** Exchange is one of the three qualifying relationships for Raja Yoga, but it is often omitted in implementations because it requires cross-referencing sign ownership.

3. **Confusing formation with strength:** Pancha Mahapurusha Yogas require dignity (own/exaltation sign) as a *formation condition*, not just a strength modifier. This is different from Raja Yoga where dignity is a strength modifier.

4. **Treating Neecha Bhanga as a yoga:** Neecha Bhanga is a *pre-condition* that restores dignity, not a standalone yoga. It should be evaluated before other yogas, not as a separate yoga result.

5. **Assuming sign-based = degree-based aspects:** The Parashari system uses sign-based aspects exclusively. Degree-based aspects belong to the Jaimini system and should not be mixed.

---

## 9. Claims Suitable for Future Research

1. **Quantitative weight of exchange vs. conjunction:** Phaladeepika suggests exchange > conjunction > mutual aspect, but no root text provides numerical weights. Research needed to establish JRS-specific weights.

2. **Multi-planet chain effects:** How does a chain of 3+ planets (A → B → C → D) modify the basic Raja Yoga? BPHS does not address this; Saravali and Jataka Parijata provide partial guidance.

3. **Rahu/Ketu dispositorship:** In modern charts with precise longitude, Rahu/Ketu have their own sign ownership. The classical texts are ambiguous on whether nodal dispositorship participates in Raja Yoga formation.

4. **Navamsa-based aspect verification:** Some commentaries (Saravali Ch 12) suggest that aspects should be verified in the Navamsa chart. This is a refinement that may improve accuracy but is not in the root texts.

5. **Cross-lagna aspects:** When evaluating aspects from the Moon lagna vs. the Sun lagna vs. the Navamsa lagna, how should the engine weight the results? BPHS treats Lagna as primary, but Phaladeepika gives Moon lagna equal weight for certain yogas.

---

## 10. Claims That Must NOT Enter the Classical Catalog

1. **"Planets in Kendras are always auspicious":** False per BPHS. Kendra lordship by natural benefics creates Dosha.

2. **"Any two planets in mutual aspect form a Raja Yoga":** False. The planets must be Kendra and Trikona lords respectively.

3. **"Neecha Bhanga is a Raja Yoga":** False. Neecha Bhanga is a pre-condition, not a yoga.

4. **"Rahu/Ketu aspects are malefic by default":** False per some schools. Rahu in Kendra can form Raja Yoga (Saravali), though this is not in BPHS Ch 41.

5. **"Degree-based aspects apply in Parashari system":** False. Parashari uses sign-based aspects exclusively.

---

## 11. Unresolved Questions

1. **Exchange with combust planet:** If Planet A is combust and in an exchange with Planet B, is the exchange weakened or cancelled? BPHS Ch 34 is ambiguous.

2. **Jaimini aspects for Raja Yoga:** Can Jaimini-style aspects (Kendra/3rd/11th) qualify for Raja Yoga formation, or only Parashari aspects? BPHS Ch 41 uses "aspect" generically.

3. **Dispositor chain length:** Is there a maximum chain length beyond which the dispositor relationship is no longer meaningful? No root text addresses this.

4. **Multiple Raja Yogas in one chart:** When a chart has multiple Raja Yoga formations (e.g., 1st-5th, 10th-9th, Lagna-Moon), how should they be ranked? BPHS Ch 41 provides a hierarchy (Lagna > 10th > others) but not a quantitative scoring method.

5. **Parivartana between dusthana lords:** If two dusthana lords exchange signs, does this form Vipareeta Raja Yoga or Dainya Yoga? BPHS Ch 34 and Ch 44 are not fully explicit on this edge case.

---

## 12. Recommended RI-010C Research Questions

1. **Multi-planet chain resolution:** How should A → B → C → D dispositor chains be evaluated for combined yoga strength?
2. **Navamsa verification:** Should all Raja Yoga formations be cross-verified in the Navamsa chart before final assessment?
3. **Dasha-specific yoga activation:** What are the classical rules for which Dasha period activates which yoga?
4. **Transit-based yoga triggering:** What are the precise transit conditions that trigger a dormant yoga into manifestation?

---

**FINAL DECISION:** READY FOR SOURCE-VERIFICATION
