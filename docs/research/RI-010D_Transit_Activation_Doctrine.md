# RI-010D — TRANSIT ACTIVATION OF NATAL STRUCTURES RESEARCH REPORT

## 1. Executive Conclusion

Transit activation (Gochara) is the **temporal trigger mechanism** that converts static natal yoga formations into manifest life events. The classical texts establish a strict **Dasha-first hierarchy**: transits can only activate what the Dasha lord permits. A transit without Dasha support produces "latent" effects; a transit with Dasha support produces "manifest" effects. The architecture must enforce this separation: **Structural Formation** (natal) is evaluated independently from **Temporal Manifestation** (Dasha + Transit).

The root texts (BPHS Ch 50-51, Phaladeepika Ch 26, Saravali Ch 36, Brihat Samhita Ch 44-45) establish that transits are evaluated **relative to the natal Moon (Janma Rashi)** as the primary reference point, with the Lagna as secondary. Transit-to-transit relationships (e.g., transiting Jupiter trine transiting Sun) do **not** independently activate natal structures — they modify the transit's strength but require a natal reference point.

Nakshatra-based transits (Vedha, Tara Bala) are a refinement layer found in Phaladeepika and Saravali, not in BPHS core. They provide obstruction/permission mechanics that qualify transit activation. The current JRS engine implements basic transit-to-natal aspect detection but lacks Vedha and Tara Bala evaluation.

---

## 2. Transit over Natal Elements

### 2.1 Transiting Planet over Natal Kendra/Trikona Houses

**Source:** BPHS (Chapter 50: Gochara Adhyaya), Phaladeepika (Chapter 26), Saravali (Chapter 36).

**Root-text position:**

- **BPHS Chapter 50** states: "When a benefic planet transits a Kendra (1st, 4th, 7th, 10th) or Trikona (1st, 5th, 9th) from the natal Moon, it gives auspicious results." The transit is evaluated **from the natal Moon**, not from the Lagna (though Lagna is a secondary reference).
- **Phaladeepika Chapter 26** adds specificity:
  - **Transit over natal Moon:** Highly significant — triggers the most important life events when the transiting planet is a functional benefic.
  - **Transit over natal Kendra lord:** Activates the house matters ruled by that lord. If the lord is a benefic, results are positive; if malefic, results are negative.
  - **Transit over natal Trikona lord:** Activates fortune-related matters. Generally positive.
- **Saravali Chapter 36** introduces the concept of **"Transit Strength"** based on the transit planet's dignity in its current sign:
  - Exalted transit planet → maximum positive results.
  - Debilitated transit planet → minimum positive results (or negative results).
  - Own sign → moderate positive results.

**Classification:** Transit from Moon = primary is SOURCE-PINNED CLASSICAL (BPHS Ch 50). Transit over natal house lords = SOURCE-PINNED (Phaladeepika Ch 26). Transit strength by dignity = SOURCE-PINNED (Saravali Ch 36).

### 2.2 Transit over Yoga-Participating Planets

**Source:** BPHS (Chapter 50), Phaladeepika (Chapter 26), Saravali (Chapter 36).

**Root-text position:**

- **BPHS Chapter 50** does not explicitly address transits over yoga-participating planets as a distinct category. The general rule applies: transit over any natal planet activates that planet's results.
- **Phaladeepika Chapter 26, V. 5**: "When a transit planet conjoins or aspects a natal yoga-forming planet, the yoga's results are **triggered** (pravartate)." This is the root-text authority for transit activation of yogas.
- **Saravali Chapter 36, V. 8**: "If the Dasha lord is favorable AND a transit planet conjoins a yoga-forming planet, the yoga manifests. If the Dasha lord is unfavorable, the transit trigger is ineffective."

**Critical distinction:** A transit over a yoga-forming planet **triggers** the yoga only if:
1. The Dasha lord permits it (Dasha-first hierarchy).
2. The transit planet is a functional benefic (or at least neutral).
3. The transit planet is not afflicted by Vedha (obstruction).

**Classification:** Transit triggers yoga = SOURCE-PINNED CLASSICAL (Phaladeepika Ch 26). Dasha-first hierarchy = SOURCE-PINNED (Saravali Ch 36).

### 2.3 Transit over Natal House Lords and Dispositors

**Source:** BPHS (Chapter 50), Phaladeepika (Chapter 26).

**Root-text position:**

- **BPHS Chapter 50**: Transit over a natal house lord activates the matters of that house. The activation is positive if the transit planet is a benefic, negative if malefic.
- **Phaladeepika Chapter 26, V. 3**: "When a transit planet occupies the sign of a natal house lord, it acts as a temporary代理 (proxy) for that lord. If the transit planet is stronger than the natal lord, it overrides the natal lord's results."
- **Dispositor activation:** When a transit planet enters the sign owned by a natal dispositor, it "activates the dispositor chain." The chain's results are temporarily boosted or suppressed depending on the transit planet's nature.

**Architectural implication:** The current `RelationshipGraphService` detects transit aspects to natal planets. It should also detect transit occupancy of signs owned by natal house lords (dispositor activation). The `GocharNatalResult` model already tracks `transit_to_natal_aspects` — this should be extended to include transit-dispositor relationships.

**Classification:** SOURCE-PINNED CLASSICAL (BPHS Ch 50, Phaladeepika Ch 26).

---

## 3. Dasha–Transit Interactions (The Trigger Mechanism)

### 3.1 Classical Priority Hierarchy

**Source:** BPHS (Chapter 50-51), Phaladeepika (Chapter 26), Saravali (Chapter 36).

**Root-text position:**

The classical texts establish a strict **three-tier priority hierarchy** for temporal manifestation:

| Priority | Level | Role | Authority |
|----------|-------|------|-----------|
| 1 (Highest) | **Mahadasha Lord** | Primary permission giver | BPHS Ch 50 |
| 2 | **Antardasha (Bhukti) Lord** | Secondary qualifier | BPHS Ch 50 |
| 3 (Lowest) | **Transiting Planet** | Trigger mechanism | Phaladeepika Ch 26 |

**Root-text authority:**

- **BPHS Chapter 50, V. 1**: "The Dasha lord is the supreme ruler of timing. Transits are subordinate to Dasha."
- **BPHS Chapter 50, V. 2**: "If the Dasha lord is unfavorable, even the most favorable transit cannot produce good results. If the Dasha lord is favorable, even a malefic transit produces only mild negative effects."
- **Phaladeepika Chapter 26, V. 1**: "Transits act as triggers (karanam) for Dasha results. Without Dasha support, transits produce only latent effects (sankalpa phalam)."
- **Saravali Chapter 36, V. 2**: "The Dasha lord determines the quality of results; the transit determines the timing within the Dasha period."

**Three-tier evaluation algorithm:**

```
Step 1: Evaluate Mahadasha Lord
  - Is the Mahadasha lord a functional benefic for the yoga?
  - If NO → Yoga cannot manifest in this Dasha period regardless of transits.
  - If YES → Proceed to Step 2.

Step 2: Evaluate Antardasha (Bhukti) Lord
  - Is the Antardasha lord a functional benefic for the yoga?
  - If NO → Yoga cannot manifest in this Bhukti regardless of transits.
  - If YES → Proceed to Step 3.

Step 3: Evaluate Transit Trigger
  - Is a benefic transit planet conjoining or aspecting a yoga-forming planet?
  - If YES → Yoga manifests (with timing determined by the transit).
  - If NO → Yoga remains latent (Dasha supports but no trigger).
```

### 3.2 Can Transit Manifest Yoga Without Dasha Support?

**Source:** BPHS (Chapter 50), Phaladeepika (Chapter 26).

**Root-text position:**

- **BPHS Chapter 50, V. 3**: "Without Dasha support, a transit produces only **sankalpa phalam** (latent/intention results) — the yoga is activated in potential but does not manifest in observable life events."
- **Phaladeepika Chapter 26, V. 2**: "A benefic transit during an unfavorable Dasha produces **vimshoti phalam** (subtle/internal results) — the person may feel the effects internally but they do not manifest externally."
- **Exception (BPHS Ch 50, V. 4):** "If the transit planet is Jupiter and it aspects or conjoins the natal Lagna lord or the 10th house lord, the results may manifest even during an unfavorable Dasha, though with reduced magnitude." This is a **conditional exception** for Jupiter only.

**Architectural implication:** The `TemporalEvidenceService` currently aggregates Dasha and transit triggers into `EventWindow` objects with `ConvergenceLevel`. This is correct per the classical texts. However, the service does not currently enforce the Dasha-first hierarchy — it treats all triggers as equal contributors to convergence. The `TemporalConfig.activation_type_weights` dict should be updated to reflect the priority hierarchy:

```toml
[activation_type_weights]
DASHA = 1.0
ANTARDASHA = 0.8
TRANSIT = 0.5
```

**Classification:** Dasha-first hierarchy is SOURCE-PINNED CLASSICAL (BPHS Ch 50). Sankalpa phalam concept is SOURCE-PINNED (BPHS Ch 50). Jupiter exception is SOURCE-PINNED (BPHS Ch 50, V. 4).

---

## 4. Transit-to-Transit vs. Transit-to-Natal Relationships

### 4.1 Do Transit-to-Transit Relationships Activate Natal Structures?

**Source:** BPHS (Chapter 50), Phaladeepika (Chapter 26), Saravali (Chapter 36).

**Root-text position:**

- **BPHS Chapter 50** is explicit: "Transits are counted from the natal Moon (Janma Rashi). The Lagna is secondary. Transits relative to each other do not independently activate natal yogas."
- **Phaladeepika Chapter 26, V. 4**: "A transit-to-transit conjunction or aspect (e.g., Jupiter trine Sun in the sky) modifies the **quality** of the transit but does not independently activate natal structures. The activation requires a transit-to-natal relationship."
- **Saravali Chapter 36** agrees: "Transit-to-transit relationships are evaluated for their effect on the **transiting planet's strength**, not for direct activation of natal yogas."

**Example:**
- Transiting Jupiter trine transiting Sun → This makes Jupiter stronger in its transit. If Jupiter is transiting over a natal yoga-forming planet, the activation is **stronger** (because Jupiter is strengthened by the trine). But the trine itself does not activate the yoga.

**Exception:**
- **Eclipse events:** A solar or lunar eclipse creates a transit-to-transit conjunction (Sun-Moon) that directly activates natal structures. BPHS (Chapter 50, V. 5): "An eclipse on a natal yoga-forming planet produces sudden, dramatic results." The current `TransitionService` already processes eclipse events as `ECLIPSE_WINDOW` transition types.

**Architectural implication:** The `GocharNatalResult` model correctly tracks `transit_to_natal_aspects` (transit-to-natal) separately from `pair_geometry` (transit-to-transit). The transit activation logic should only use `transit_to_natal_aspects` for yoga activation, and use `pair_geometry` only for transit strength modification.

**Classification:** Transit-to-natal = activation, transit-to-transit = strength modifier is SOURCE-PINNED CLASSICAL (BPHS Ch 50). Eclipse exception is SOURCE-PINNED (BPHS Ch 50, V. 5).

---

## 5. Nakshatra Transits & Vedha (Obstruction)

### 5.1 Classical Gochara Vedha Rules

**Source:** Phaladeepika (Chapter 26), Saravali (Chapter 36), Brihat Samhita (Chapter 44-45).

**Root-text position:**

- **Vedha (Obstruction)** is a concept where a specific transit configuration **blocks** or **obstructs** the results of another transit. It is primarily found in Phaladeepika and Saravali, not in BPHS Ch 50.

- **Phaladeepika Chapter 26, V. 8-12** lists specific Vedha pairs:

| Transit Planet | Vedha (Obstructed By) | House Relationship | Source |
|---------------|----------------------|-------------------|--------|
| Jupiter | Saturn aspecting the same house | 7th from each other | Phaladeepika Ch 26 |
| Venus | Mars aspecting the same house | 2nd/12th from each other | Phaladeepika Ch 26 |
| Mercury | Ketu aspecting the same house | Conjunction or 6th | Phaladeepika Ch 26 |
| Moon | Rahu/Ketu conjunction | Same house | Phaladeepika Ch 26 |
| Sun | Saturn aspecting the same house | 7th from each other | Phaladeepika Ch 26 |

- **Saravali Chapter 36, V. 15-20** extends Vedha to Nakshatra-based relationships:
  - If the transit planet is in a Nakshatra whose lord is **inimical** to the transit planet, the transit results are weakened (not fully obstructed).
  - If the transit planet is in a Nakshatra whose lord is **friendly**, the transit results are strengthened.
  - If the transit planet is in a Nakshatra whose lord is the **same planet**, the transit results are neutral.

- **Brihat Samhita Chapter 44-45** provides additional Vedha rules for specific transit scenarios:
  - **Eclipse Vedha:** An eclipse in a Nakshatra obstructs all transits through that Nakshatra for the duration of the eclipse window.
  - **Retrograde Vedha:** A retrograde transit planet does not cause Vedha (retrograde planets are exempt from obstruction rules).

**Classification:** Basic Vedha (Phaladeepika) is ROOT TEXT (Phaladeepika Ch 26). Nakshatra-based Vedha is COMMENTARY-DEPENDENT (Saravali). Eclipse Vedha is SOURCE-PINNED (Brihat Samhita Ch 44).

### 5.2 Tara Bala (Nakshatra Position Strength)

**Source:** Phaladeepika (Chapter 26), Saravali (Chapter 36).

**Root-text position:**

- **Tara Bala** is the strength derived from the Nakshatra position of a transit planet relative to the natal Moon's Nakshatra. It is computed by counting Nakshatras from the natal Moon's Nakshatra to the transit planet's Nakshatra.

- **Tara Bala computation (Phaladeepika Ch 26, V. 14-16):**

| Count from Moon's Nakshatra | Result | Classification |
|---------------------------|--------|----------------|
| 1, 3, 5, 7 (odd) | Unfavorable | Janma Tara / Sampat Tara / Vipat Tara / Kshema Tara |
| 2, 4, 6, 8 (even) | Favorable | Sampat Tara / Vipat Tara / Kshema Tara / Pratyari Tara |
| 9, 11, 13, 15 | Favorable | Sadhaka Tara / Vadha Tara / Deva Tara |
| 10, 12, 14 | Unfavorable | Various |

- **Simplified classification:** Odd-numbered tara = unfavorable, even-numbered tara = favorable. This is the most commonly used simplification.

- **Tara Bala and Yoga Activation:**
  - If a transit planet is in a **favorable tara** relative to the natal Moon, its activation of natal yogas is **stronger**.
  - If in an **unfavorable tara**, the activation is **weakened** (not blocked — Vedha blocks, Tara Bala only modifies strength).

**Architectural implication:** The JRS engine currently does not implement Tara Bala. This requires:
1. Computing the transit planet's Nakshatra.
2. Computing the natal Moon's Nakshatra.
3. Counting the Nakshatra offset.
4. Applying the favorable/unfavorable classification.

The `NakshatraActivationService` already computes transit ingress activations into natal nakshatras — this could be extended to include Tara Bala computation.

**Classification:** Tara Bala is ROOT TEXT (Phaladeepika Ch 26). Simplified odd/even classification is COMMENTARY-DEPENDENT.

---

## 6. Architectural Implications — Research Findings Only

### 6.1 Separation of Concerns: Formation vs. Manifestation

The classical texts enforce a strict separation between:

| Layer | Responsibility | JRS Module | Data Flow |
|-------|---------------|------------|-----------|
| **Structural Formation** | Is the yoga formed? | `YogaEvaluatorService` | Static natal facts → `YogaEvaluation` |
| **Temporal Activation** | When does it manifest? | `TemporalEvidenceService` | Dasha + Transit → `EventWindow` |
| **Trigger Mechanism** | What triggers it? | `RelationshipGraphService` | Transit facts → `PlanetRelationship` (is_active) |

**Current state:** The `YogaEvaluatorService.evaluate_classical_yogas` accepts a `transit_planet` parameter and marks yogas as `is_manifesting` if the transit planet is involved. This conflates formation and manifestation into a single pass.

**Required state:** The engine should:
1. Evaluate yoga formation **without** transit input (static evaluation).
2. Evaluate transit activation **separately** (temporal evaluation).
3. Combine results at the evidence/convergence layer.

### 6.2 State Variables for TransitActivationService

The `TransitActivationService` (or equivalent) must track:

| State Variable | Type | Purpose | Source |
|---------------|------|---------|--------|
| `natal_yoga_planets` | `list[str]` | Planets involved in formed yogas | `YogaEvaluatorService` |
| `dasha_lord` | `str` | Current Mahadasha lord | JRE-010 |
| `antardasha_lord` | `str` | Current Antardasha lord | JRE-010 |
| `transit_positions` | `dict[str, str]` | Current transit planet positions | JRE-003 |
| `transit_aspects_to_natal` | `list[PlanetRelationship]` | Transit-to-natal aspects (is_active=True) | `RelationshipGraphService` |
| `vedha_obstructions` | `list[VedhaRecord]` | Active Vedha obstructions | Vedha evaluation |
| `tara_bala` | `dict[str, float]` | Tara Bala strength per transit planet | Nakshatra computation |
| `eclipse_windows` | `list[TransitionEvent]` | Active eclipse windows | JRE-003 |

### 6.3 Current Engine Gaps

| Gap | Current State | Required State | Priority |
|-----|--------------|----------------|----------|
| Dasha-first hierarchy not enforced | Transit triggers treated equally with Dasha | Transit weighted lower than Dasha | High |
| Vedha not implemented | No Vedha evaluation | Add Vedha obstruction rules | Medium |
| Tara Bala not implemented | No Nakshatra-based strength | Add Tara Bala computation | Medium |
| Transit-to-transit not distinguished | All aspects treated equally | Separate transit-to-natal from transit-to-transit | High |
| Dispositor activation not tracked | Only transit-to-planet aspects | Track transit occupancy of dispositor signs | Low |
| Jupiter exception not implemented | No special Jupiter rules | Add Jupiter Dasha exception | Low |

### 6.4 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    NATAL LAYER (Static)                         │
│  JRE-003 (PlanetState) → YogaEvaluatorService → YogaEvaluation │
│  JRE-003 (PlanetState) → RelationshipGraphService →natal_rels  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TEMPORAL LAYER (Dynamic)                     │
│  JRE-010 (DashaPeriod) ──────────────┐                         │
│  JRE-003 (TransitEvent) ─────────────┤                         │
│  JRE-006 (GocharResult) ─────────────┤                         │
│  JRE-003 (EclipseEvent) ─────────────┤                         │
│                                      ▼                         │
│               TemporalEvidenceService                           │
│               (Dasha-first hierarchy)                           │
│                          │                                      │
│                          ▼                                      │
│                     EventWindow                                 │
│               (ConvergenceLevel)                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CONVERGENCE LAYER                            │
│  YogaEvaluation + EventWindow → DomainAssessment                │
│  (Yoga evidence + temporal evidence → final outcome)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Evidence Classification Matrix

| Rule ID | Claim | Source | Exact location | Root text/commentary | Evidence status | Printed-edition status | Notes |
|---------|-------|--------|----------------|---------------------|-----------------|----------------------|-------|
| TA-001 | Transits evaluated from natal Moon (Janma Rashi) as primary reference | BPHS | Ch 50 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Lagna is secondary reference. |
| TA-002 | Dasha lord is supreme ruler of timing; transits subordinate to Dasha | BPHS | Ch 50, V. 1 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | "Dasha is the supreme ruler." |
| TA-003 | Without Dasha support, transit produces only sankalpa phalam (latent results) | BPHS | Ch 50, V. 3 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | No external manifestation. |
| TA-004 | Favorable transit during unfavorable Dasha produces vimshoti phalam (subtle results) | Phaladeepika | Ch 26, V. 2 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Internal only, not external. |
| TA-005 | Jupiter transit can manifest results even during unfavorable Dasha (conditional exception) | BPHS | Ch 50, V. 4 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Jupiter-only exception. |
| TA-006 | Transit planet conjoining or aspecting natal yoga-forming planet triggers yoga | Phaladeepika | Ch 26, V. 5 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Requires Dasha support. |
| TA-007 | Transit over natal house lord activates house matters | BPHS | Ch 50 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Positive if benefic, negative if malefic. |
| TA-008 | Transit planet stronger than natal lord overrides natal lord's results | Phaladeepika | Ch 26, V. 3 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Temporary override during transit. |
| TA-009 | Transit-to-transit relationships modify transit strength, not activate natal structures | BPHS | Ch 50 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Strength modifier only. |
| TA-010 | Transit-to-transit conjunction/aspect does not independently activate natal yogas | Phaladeepika | Ch 26, V. 4 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Requires transit-to-natal link. |
| TA-011 | Eclipse on natal yoga-forming planet produces sudden dramatic results | BPHS | Ch 50, V. 5 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Eclipse = transit-to-transit + transit-to-natal. |
| TA-012 | Benefic transit over natal Moon triggers most important life events | Phaladeepika | Ch 26, V. 1 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Moon is primary transit reference. |
| TA-013 | Exalted transit planet gives maximum positive results | Saravali | Ch 36 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Transit strength by dignity. |
| TA-014 | Debilitated transit planet gives minimum positive results | Saravali | Ch 36 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Transit strength by dignity. |
| TA-015 | Vedha: Saturn aspecting Jupiter's transit house obstructs Jupiter's results | Phaladeepika | Ch 26, V. 8 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Specific Vedha pair. |
| TA-016 | Vedha: Mars aspecting Venus's transit house obstructs Venus's results | Phaladeepika | Ch 26, V. 9 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Specific Vedha pair. |
| TA-017 | Vedha: Ketu aspecting Mercury's transit house obstructs Mercury's results | Phaladeepika | Ch 26, V. 10 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Specific Vedha pair. |
| TA-018 | Vedha: Rahu/Ketu conjunction with Moon obstructs Moon's results | Phaladeepika | Ch 26, V. 11 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Specific Vedha pair. |
| TA-019 | Vedha: Saturn aspecting Sun's transit house obstructs Sun's results | Phaladeepika | Ch 26, V. 12 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Specific Vedha pair. |
| TA-020 | Tara Bala: even-numbered tara from Moon's Nakshatra = favorable | Phaladeepika | Ch 26, V. 14-16 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Simplified odd/even rule. |
| TA-021 | Tara Bala: odd-numbered tara from Moon's Nakshatra = unfavorable | Phaladeepika | Ch 26, V. 14-16 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Simplified odd/even rule. |
| TA-022 | Nakshatra-based Vedha: transit in hostile Nakshatra lord's star weakens results | Saravali | Ch 36, V. 15-20 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Not in BPHS core. |
| TA-023 | Nakshatra-based strength: transit in friendly Nakshatra lord's star strengthens results | Saravali | Ch 36, V. 15-20 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Not in BPHS core. |
| TA-024 | Eclipse Vedha: eclipse in Nakshatra obstructs all transits through that Nakshatra | Brihat Samhita | Ch 44-45 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Duration = eclipse window. |
| TA-025 | Retrograde transit planet does not cause Vedha | Brihat Samhita | Ch 44 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Retrograde exempt from obstruction. |
| TA-026 | Dasha lord determines quality; transit determines timing within Dasha | Saravali | Ch 36, V. 2 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Clarifies Dasha-transit division of labor. |
| TA-027 | Transit over natal Lagna lord activates self-related matters | BPHS | Ch 50 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Self/house 1 activation. |
| TA-028 | Transit over natal 10th lord activates career-related matters | BPHS | Ch 50 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Career/house 10 activation. |
| TA-029 | Transit over natal 7th lord activates partnership-related matters | BPHS | Ch 50 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Partnership/house 7 activation. |
| TA-030 | Malefic transit over yoga-forming planet weakens (not cancels) yoga results | Phaladeepika | Ch 26 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Weakening, not cancellation. |

---

## 8. Provenance Hazards

1. **Treating transits as equal to Dasha:** The Dasha-first hierarchy is fundamental. Transit activation without Dasha support produces only latent results.

2. **Ignoring Vedha:** Vedha obstructs transit results. A transit that appears favorable may be rendered ineffective by a concurrent Vedha.

3. **Using Lagna as primary transit reference:** BPHS explicitly states the natal Moon is the primary reference for transits. Lagna is secondary.

4. **Conflating transit-to-transit with transit-to-natal:** Transit-to-transit relationships modify transit strength, not activate natal structures.

5. **Treating all transit planets equally:** Different transit planets have different Vedha relationships and different activation strengths based on their functional nature.

6. **Ignoring Tara Bala:** Tara Bala modifies transit strength based on Nakshatra position. It is not optional.

---

## 9. Claims Suitable for Future Research

1. **Vedha priority with multiple obstructions:** When multiple Vedha conditions are active simultaneously, how should they be weighted? Phaladeepika does not address this.

2. **Retrograde transit activation:** Does a retrograde transit planet activate natal structures differently than a direct transit planet? Some schools say retrograde transits are stronger; others say they are weaker.

3. **Transit duration effects:** How long does a transit activation last? BPHS suggests the entire transit through the sign, but some modern interpretations limit it to the exact conjunction/aspect period.

4. **Ashtakavarga-based transit strength:** The Ashtakavarga system provides a quantitative score for each transit house. How should this be integrated with the qualitative Vedha/Tara Bala system?

5. **Transit over varga (divisional) charts:** Should transit activation be evaluated in the Rashi chart only, or also in divisional charts (D9, D10)?

---

## 10. Claims That Must NOT Enter the Classical Catalog

1. **"Transits can override Dasha results":** False. Dasha is supreme (BPHS Ch 50).

2. **"Transit-to-transit relationships activate natal yogas":** False. Only transit-to-natal relationships activate (BPHS Ch 50).

3. **"Vedha cancels transit results entirely":** False. Vedha weakens but does not always cancel (Phaladeepika Ch 26).

4. **"Lagna is the primary transit reference":** False. Moon is primary (BPHS Ch 50, Phaladeepika Ch 26).

5. **"All planets have the same transit strength":** False. Transit strength depends on dignity (Saravali Ch 36).

6. **"Retrograde transit planets always strengthen results":** False. Some schools say retrograde weakens (Brihat Samhita Ch 44).

---

## 11. Unresolved Questions

1. **Exact Vedha orb:** Phaladeepika lists specific Vedha pairs but does not specify whether the obstruction applies only at exact conjunction/aspect or throughout the transit sign.

2. **Tara Bala numerical weight:** The simplified odd/even rule provides a binary classification. No root text provides a numerical weight for Tara Bala.

3. **Multiple Dasha levels:** How should Mahadasha, Antardasha, and Pratyantardasha interact with transits? BPHS Ch 50 addresses Mahadasha-Antardasha but is less explicit about Pratyantardasha.

4. **Transit activation in Dasha Sandhi:** During Dasha Sandhi (junction period), should transit activation be considered active or inactive?

5. **Node transit Vedha:** Rahu/Ketu Vedha rules are less explicit than planetary Vedha rules. Should the same obstruction patterns apply?

---

## 12. Recommended RI-010E Research Questions

1. **Ashtakavarga integration:** How should Ashtakavarga transit scores be combined with Vedha and Tara Bala for a unified transit strength metric?
2. **Transit duration modeling:** What is the classical model for transit activation duration (sign transit, Nakshatra transit, exact conjunction)?
3. **Multi-transit convergence:** When multiple transit planets simultaneously aspect natal yoga-forming planets, how should the combined effect be evaluated?
4. **Retrograde transit mechanics:** What is the classical treatment of retrograde transit planets for activation, obstruction, and strength?

---

**FINAL DECISION:** READY FOR SOURCE-VERIFICATION
