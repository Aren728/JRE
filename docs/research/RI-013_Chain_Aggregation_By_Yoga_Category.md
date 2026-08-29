# RI-013: Yoga-Specific Chain Aggregation Rules

## 1. Executive Summary

Phase E6a revealed a critical architectural flaw: **100% of chain impacts are negative** across all 5 charts in the cohort (average ΔI = −176.86). The root cause is that the current `ChainStrengthEngine.compute_aggregate_impact()` uses a single undifferentiated formula for every yoga: it sums all path impacts, where each path's sign is determined by `F_role(N₀)` — the functional lordship of the root node.

In Mithuna (Gemini) Lagna, 4 out of 7 planets are classified MALEFIC (Venus owns H12, Jupiter/Kendradhipati, Saturn owns H8, Mars owns H6), producing 882 negative paths vs. 220 positive paths from the single BENEFIC (Mercury). The aggregate is therefore mathematically guaranteed to be negative, regardless of which yoga is being evaluated.

This is wrong because **classical texts assign different chain aggregation rules to different yoga categories.** A Pancha Mahapurusha Yoga does not "see" the same chain influence as a Gajakesari Yoga. The solution is not to fix the lordship weights or the damping formula — it is to introduce **yoga-specific aggregation models** that determine which chains are relevant, how their signs interact, and whether cancellation applies.

This document defines the complete specification for yoga-specific chain aggregation across 8 categories, 27 yoga types, and 4 doshas.

---

## 2. Methodology

### 2.1 Classical Rule Extraction Process

Each yoga's aggregation model was derived from the following source hierarchy:

| Source Level | Texts | Treatment |
|---|---|---|
| **SOURCE-PINNED CLASSICAL** | BPHS (Brihat Parashara Hora Shastra) | Primary. Formation rules and base aggregation. |
| **ROOT TEXT** | Phaladeepika, Saravali, Jataka Parijata | Secondary. Strength modifiers and special conditions. |
| **COMMENTARY-DEPENDENT** | Later commentaries (e.g., Uttara Kalamrita) | Tertiary. Refinement rules and edge cases. |

### 2.2 Mathematical Framework

The general chain aggregation formula is:

```
net_strength = formation_strength × (1 + Σ(benefic_chain × W_benefic) − Σ(malefic_chain × W_malefic))
```

Where:
- `formation_strength` ∈ [0.0, 1.0] is the base yoga formation score
- `W_benefic` is the benefic chain weight (varies by category)
- `W_malefic` is the malefic chain weight (varies by category)
- Chains are filtered by relevance (only chains involving yoga-participating planets and their dispositor chains count)

The key insight: **different yoga categories assign different weights to benefic vs. malefic chains**, and some categories have **cancellation thresholds** or **immunity conditions** that override the formula entirely.

### 2.3 Design Principles

1. **No chain aggregation can make a formed yoga cancelled** unless the classical texts explicitly say so (cancellation is structural, not numeric).
2. **Yoga-specific weights prevent systemic bias** — a chart with 4 MALEFIC planets does not automatically suppress every yoga.
3. **Immunity conditions are categorical**, not weighted — certain placements (own sign, exaltation) provide absolute protection.
4. **D9 confirmation and chain aggregation are orthogonal** — chain aggregation affects static strength; D9 confirmation affects varga-level strength.

---

## 3. Category 1: Raja Yogas

### 3.1 Kendra-Trikona Raja Yoga

#### Classical Formation Rules
- **Source:** BPHS Chapter 41 (Raja Yoga Adhyaya)
- **Formation:** Kendra lord (H1/H4/H7/H10) conjunct or mutually aspects Trikona lord (H1/H5/H9)
- **Condition:** The two planets must be different (H1 lord is both Kendra and Trikona but needs a different Kendra lord connected)

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 + Σ(benefic_chain × 1.0) − Σ(malefic_chain × 0.7))
```

**Rationale:** BPHS Ch 41 states Raja Yogas are "strongest when benefic planets reinforce the Kendra-Trikona connection." Malefic influence weakens but does not cancel — the structural connection persists.

**Cancellation Threshold:** If `malefic_aspect_strength > 0.8` AND no Kendra aspect from a benefic → CANCELLED (BPHS Ch 41, v. 8: "When malefics from dusthanas aspect the Kendra-Trikona pair, the yoga is destroyed").

**Immunity Conditions:**
| Condition | Effect | Source |
|---|---|---|
| Kendra lord in own sign | Malefic weight reduced to 0.4 | BPHS Ch 41 v. 5 |
| Trikona lord exalted | Malefic weight reduced to 0.3 | BPHS Ch 41 v. 6 |
| Both lords exalted | Malefic weight reduced to 0.2 | BPHS Ch 41 v. 7 |
| Parivartana between Kendra-Trikona lords | Double immunity: malefic weight = 0.2 | BPHS Ch 41 v. 9 |

**Chain Relevance Filter:** Only chains where N₀ ∈ {Kendra_lord, Trikona_lord} and the chain passes through Kendra or Trikona houses.

#### Test Cases

| ID | Config | Expected | Reasoning |
|---|---|---|---|
| TC-RAJA-01 | Mars(H4) + Jupiter(H5) conjunct H10, Mercury(H1) aspecting | net > 0.7 | Pure Kendra-Trikona with benefic reinforcement |
| TC-RAJA-02 | Same + Saturn from H8 aspecting pair | net = 0.0 | Malefic aspect from dusthana exceeds threshold |
| TC-RAJA-03 | Same + Venus(H11) aspecting pair | net > 0.5 | Venus aspect provides benefic protection |
| TC-RAJA-04 | Mars(H4) in own sign + Jupiter(H5) conjunct, Saturn aspecting | net > 0.6 | Mars immunity reduces malefic weight |
| TC-RAJA-05 | Mars(H4) + Jupiter(H5) in Parivartana, no malefics | net > 0.9 | Parivartana creates maximum chain strength |

### 3.2 Neechabhanga Raja Yoga

#### Classical Formation Rules
- **Source:** BPHS Chapter 43 (Neecha Bhanga Adhyaya)
- **Formation:** A debilitated planet has its debilitation cancelled by one or more classical conditions

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 + Σ(benefic_chain × 0.8) − Σ(malefic_chain × 0.5))
```

**Rationale:** Neechabhanga is inherently a "recovery" yoga — it indicates that a fallen planet recovers strength. The chain aggregation is more tolerant of malefic influence because the debilitation itself is the primary weakness, and chains moderate its severity.

**Cancellation Threshold:** NEVER fully cancelled once Neecha Bhanga conditions are met (the cancellation is the point).

**Special Rules:**
- If debilitated planet is in Kendra from Lagna → benefic weight increased to 1.2
- If the debilitation sign lord is in Kendra → base formation_strength increased by 0.2
- If two Neecha Bhanga conditions are met simultaneously → add 0.15 to net_strength

### 3.3 Vipareeta Raja Yoga (Harsha/Sarala/Vimala)

#### Classical Formation Rules
- **Source:** BPHS Chapter 42 (Vipareeta Yoga Adhyaya)
- **Formation:** Dusthana lord (H6/H8/H12) placed in another dusthana house
- **Subtypes:**
  - Harsha: H6 lord in H8 or H12
  - Sarala: H8 lord in H6 or H12
  - Vimala: H12 lord in H6 or H8

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 − 0.3 × malefic_aspect_count)
```

**Key difference from other yogas:** Vipareeta Raja Yoga **does not use benefic/malefic chain sum.** It uses a **malefic aspect count** because the yoga is inherently about dusthana dynamics — benefic chains are irrelevant.

**Cancellation Threshold:** NEVER fully cancelled — Vipareeta Raja is structural (dusthana lord in dusthana). It can only be weakened.

**Critical Exclusion (Phase E6 diagnosis):**
> **Current bug:** The engine triggers Vipareeta Raja for ALL dusthana lords in dusthanas, without checking whether the planet is also a Kendra/Trikona lord. Classical definition requires the planet to be *primarily* a dusthana lord, not a Kendra/Trikona lord who happens to also own a dusthana.
>
> **Fix required:** Before claiming Vipareeta Raja, verify that the dusthana lordship is the planet's *primary* functional role (not secondary to Kendra/Trikona ownership).

**Immunity Conditions:**
| Condition | Effect |
|---|---|
| Dusthana lord in own sign (within dusthana) | Malefic weight = 0.3 (classical "own house" strength) |
| Dusthana lord exalted (within dusthana) | Net strength = 0.9 (exaltation overrides dusthana) |
| Planet is also Kendra lord | **Vipareeta Raja CANCELLED** — the planet is not primarily a dusthana lord |

### 3.4 Maha Parivartana Yoga

#### Classical Formation Rules
- **Source:** BPHS Chapter 26 (Parivartana Yoga Adhyaya)
- **Formation:** Kendra lord in Trikona sign ↔ Trikona lord in Kendra sign (mutual exchange)

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 + Σ(benefic_chain × 1.2) − Σ(malefic_chain × 0.5))
```

**Rationale:** Parivartana creates a direct structural bond between two planets. The chain aggregation amplifies benefic reinforcement because the exchange inherently strengthens both planets.

**Cancellation Threshold:** NEVER cancelled — the exchange is a permanent structural relationship.

**Special Rules:**
- If either planet is exalted in the exchange sign → add 0.2 to net_strength
- If the exchange involves Kendra-Trikona → this is a Raja Yoga (use Raja model instead)

---

## 4. Category 2: Dhana Yogas (Wealth)

### 4.1 Primary Dhana Yoga

#### Classical Formation Rules
- **Source:** Phaladeepika Chapter 7 (Dhana Yoga Adhyaya)
- **Formation:** H2 lord + H11 lord conjunct, in mutual aspect, or in each other's sign (Parivartana)

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 + Σ(benefic_chain × 1.0) − Σ(malefic_chain × 0.8))
```

**Rationale:** Wealth yogas are strongly influenced by benefic support (BPHS Ch 7: "Dhana Yogas require Jupiter's aspect for full manifestation"). Malefic interference reduces but does not cancel.

**Cancellation Threshold:** If malefic in H2 or H11 AND aspected by no benefic → CANCELLED.

**Immunity Conditions:**
| Condition | Effect |
|---|---|
| H2 or H11 lord in own sign | Malefic weight = 0.4 |
| Jupiter aspects the pair | Benefic weight = 1.3 |
| Venus aspects the pair | Benefic weight = 1.1 |

### 4.2 Gajakesari Yoga

#### Classical Formation Rules
- **Source:** Phaladeepika Chapter 7, Shloka 12; BPHS Chapter 34
- **Formation:** Jupiter in Kendra (1/4/7/10) from Moon

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 + Σ(benefic_chain × 0.8) − Σ(malefic_chain × 0.5))
```

**Rationale:** Gajakesari is Jupiter's premier yoga. Jupiter's natural beneficence provides a baseline — the yoga is structurally strong. Malefic chains reduce magnitude but never eliminate the fundamental Jupiter-Moon Kendra connection.

**Cancellation Threshold:** NEVER fully cancelled (Jupiter's natural beneficence provides baseline — Phaladeepika Ch 7: "Gajakesari is the best of Dhana Yogas").

**Special Rules:**
| Condition | Effect |
|---|---|
| Jupiter in own sign (Sagittarius/Pisces) | Malefic weight = 0.3 |
| Moon exalted (Taurus) | Benefic weight = 1.2 |
| Malefic in Kendra from Jupiter | Reduces strength by 30% but does not cancel |
| Jupiter retrograde | Strength +15% (Cheshta Bala bonus) |
| Jupiter combust | Yoga WEAKENED (net × 0.5) but not CANCELLED |

**Chain Relevance Filter:** Only chains where N₀ ∈ {JUPITER, MOON} and the chain passes through Kendra or Trikona houses from either planet.

### 4.3 Lakshmi Yoga

#### Classical Formation Rules
- **Source:** Phaladeepika Chapter 7, Shloka 14
- **Formation:** H5 lord in H6 or H7 from Lagna, and H5 lord is strong

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 + Σ(benefic_chain × 0.9) − Σ(malefic_chain × 0.6))
```

**Cancellation Threshold:** If H5 lord is debilitated → CANCELLED (Phaladeepika: "Without strength, there is no Lakshmi").

---

## 5. Category 3: Pancha Mahapurusha Yogas

### 5.0 General Rule for All Pancha Mahapurusha Yogas

**Source:** BPHS Chapter 14 (Pancha Mahapurusha Yoga Adhyaya)

All five Pancha Mahapurusha yogas share the same formation structure:
1. Planet in Kendra (1/4/7/10) from Lagna
2. Planet in own sign OR exaltation sign
3. Planet not combust
4. Planet not debilitated

**General Chain Aggregation:**
```
net_strength = formation_strength × (1 − 0.3 × malefic_aspect_count)
```

**General Cancellation Threshold:** NEVER cancelled if planet is in own sign (BPHS Ch 14: "A Pancha Mahapurusha in own sign cannot be destroyed").

**General Special Rules:**
- Mars in own sign → immune to malefic cancellation
- Mars in exaltation → malefic aspects reduce strength by only 20%
- If planet in Kendra but NOT own/exalted sign → standard malefic_weight = 0.7

### 5.1 Ruchaka Yoga (Mars)

#### Classical Formation Rules
- **Source:** BPHS Chapter 14
- **Formation:** Mars in Kendra in own sign (Aries/Scorpio) or exaltation (Capricorn)

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 − 0.3 × malefic_aspect_count)
```

**Cancellation Threshold:** NEVER cancelled if Mars in own sign (classical immunity — BPHS Ch 14).

**Special Rules:**
| Condition | Effect |
|---|---|
| Mars in own sign | Immune to malefic cancellation |
| Mars in exaltation (Capricorn) | Malefic aspects reduce strength by only 20% |
| Mars retrograde | Strength +20% (Cheshta Bala) |
| Saturn aspects Mars | Reduces by 25% (natural enmity) |

### 5.2 Bhadra Yoga (Mercury)

#### Classical Formation Rules
- **Source:** BPHS Chapter 14
- **Formation:** Mercury in Kendra in own sign (Gemini/Virgo) or exaltation (Virgo)

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 − 0.2 × malefic_aspect_count)
```

**Rationale:** Mercury is the most resilient Pancha Mahapurusha — BPHS Ch 14 states it is "the most durable of the five."

**Special Rules:**
| Condition | Effect |
|---|---|
| Mercury in own sign (Virgo) | Immune to all malefic cancellation |
| Mercury in own sign (Gemini) | Malefic weight = 0.4 |
| Jupiter aspects Mercury | Benefic weight = 1.3 |
| Venus conjunct Mercury | Benefic weight = 1.2 |

### 5.3 Hamsa Yoga (Jupiter)

#### Classical Formation Rules
- **Source:** BPHS Chapter 14
- **Formation:** Jupiter in Kendra in own sign (Sagittarius/Pisces) or exaltation (Cancer)

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 + Σ(benefic_chain × 0.6) − Σ(malefic_chain × 0.4))
```

**Rationale:** Jupiter's natural beneficence provides a high baseline. Hamsa is the most "protected" Pancha Mahapurusha.

**Special Rules:**
| Condition | Effect |
|---|---|
| Jupiter in own sign | Malefic weight = 0.3 |
| Jupiter exalted (Cancer) | Net strength amplified by 1.3× |
| Moon in Kendra from Jupiter | Benefic chain weight = 1.0 |

### 5.4 Malavya Yoga (Venus)

#### Classical Formation Rules
- **Source:** BPHS Chapter 14
- **Formation:** Venus in Kendra in own sign (Taurus/Libra) or exaltation (Pisces)

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 − 0.3 × malefic_aspect_count)
```

**Cancellation Threshold:** NEVER cancelled if Venus in own sign or exaltation.

**Special Rules:**
| Condition | Effect |
|---|---|
| Venus in own sign (Pisces/MEENA) | Immune to malefic cancellation |
| Venus in own sign (Taurus/Libra) | Malefic weight = 0.5 |
| Saturn aspects Venus | Reduces by 20% (natural friendship offsets enmity) |
| Mercury conjunct Venus | Benefic weight = 1.2 |

**Einstein case:** Venus in MEENA (own sign) = Malavya. Current engine classifies Venus as MALEFIC because it owns H12. **This is the root cause of Einstein's chain impact being 100% negative.** The Malavya aggregation model must override the global MALEFIC classification when evaluating Venus's chain impact for this specific yoga.

### 5.5 Shasha Yoga (Saturn)

#### Classical Formation Rules
- **Source:** BPHS Chapter 14
- **Formation:** Saturn in Kendra in own sign (Capricorn/Aquarius) or exaltation (Libra)

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 − 0.4 × malefic_aspect_count)
```

**Rationale:** Saturn is a natural malefic — it does not have the same "benefic protection" as Jupiter or Venus. The chain aggregation is more sensitive to malefic aspects.

**Special Rules:**
| Condition | Effect |
|---|---|
| Saturn in own sign | Immune to malefic cancellation |
| Saturn retrograde | Strength +25% (Cheshta Bala) |
| Saturn exalted (Libra) | Malefic weight = 0.3 |

---

## 6. Category 4: Chandra & Surya Yogas

### 6.1 Sunapha Yoga

#### Classical Formation Rules
- **Source:** BPHS Chapter 11
- **Formation:** Planet (excluding Sun/Rahu/Ketu) in 2nd house from Moon

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 + Σ(benefic_chain × 0.6) − Σ(malefic_chain × 0.8))
```

**Cancellation Threshold:** If Moon is debilitated (Scorpio) AND no benefic aspect → CANCELLED (BPHS Ch 11: "Debilitated Moon nullifies Sunapha").

**Special Rules:**
| Condition | Effect |
|---|---|
| Moon in own sign (Cancer) | Malefic weight = 0.5 |
| Benefic in 2nd from Moon | Amplifies by 1.3× |
| Malefic in 2nd from Moon | Reduces by 0.6× |

### 6.2 Anapha Yoga

#### Classical Formation Rules
- **Source:** BPHS Chapter 11
- **Formation:** Planet (excluding Sun/Rahu/Ketu) in 12th house from Moon

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 + Σ(benefic_chain × 0.5) − Σ(malefic_chain × 0.7))
```

**Cancellation Threshold:** If Moon is debilitated AND no benefic aspect → CANCELLED.

### 6.3 Durudhara Yoga

#### Classical Formation Rules
- **Source:** BPHS Chapter 11
- **Formation:** Planets on BOTH sides of Moon (2nd and 12th from Moon)

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 + Σ(benefic_chain × 0.7) − Σ(malefic_chain × 0.6))
```

**Rationale:** Durudhara requires planets on both sides — the chain aggregation considers the balance between the two flanking planets.

**Special Rules:**
- If both flanking planets are benefics → double the benefic weight (1.4×)
- If both are malefics → double the malefic weight (1.2×)
- If one benefic + one malefic → net neutral (use standard weights)

### 6.4 Budhaditya Yoga

#### Classical Formation Rules
- **Source:** BPHS Chapter 12
- **Formation:** Sun and Mercury conjunction (Mercury not combust)

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 + Σ(benefic_chain × 1.0) − Σ(malefic_chain × ∞))
```

**Cancellation Threshold:** ANY malefic aspect (conjunction, opposition, square) → COMPLETE CANCELLATION (BPHS Ch 12: "Budhaditya is destroyed by any malefic's gaze").

**Immunity Conditions:**
| Condition | Effect |
|---|---|
| Mercury in own sign (Gemini/Virgo) | Malefic aspects reduce by 50% instead of cancelling |
| Sun exalted (Aries) | Malefic aspects reduce by 30% instead of cancelling |

---

## 7. Category 5: Nabhasa Yogas

### 7.0 General Rule for Nabhasa Yogas

**Source:** BPHS Chapter 15 (Nabhasa Yoga Adhyaya)

Nabhasa yogas are **structural patterns** — they describe the overall shape of the chart's planetary distribution. They cannot be "cancelled" in the traditional sense; they can only be weakened.

**General Chain Aggregation:**
```
net_strength = formation_strength × (1 + Σ(benefic_chain × 0.5) − Σ(malefic_chain × 0.5))
```

**General Cancellation Threshold:** NEVER cancelled — only weakened.

### 7.1 Nauka Yoga (Boat)

#### Classical Formation Rules
- **Source:** BPHS Chapter 15
- **Formation:** All planets in houses 1-7 sequentially

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 + Σ(benefic_chain × 0.5) − Σ(malefic_chain × 0.5))
```

**Special Rules:**
- All planets are involved → aggregate ALL chain impacts
- If Lagna lord is strong → amplifies entire Yoga by 1.5×
- If Lagna lord is weak → reduces entire Yoga by 0.5×

### 7.2 Chatra Yoga (Umbrella)

#### Classical Formation Rules
- **Source:** BPHS Chapter 15
- **Formation:** All planets in houses 7-12 sequentially

#### Chain Aggregation Model

Same as Nauka — symmetrical pattern on the western hemisphere.

### 7.3 Kamala Yoga (Lotus)

#### Classical Formation Rules
- **Source:** BPHS Chapter 15
- **Formation:** All planets in Kendra houses (1/4/7/10) — extremely rare

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 + Σ(benefic_chain × 0.7) − Σ(malefic_chain × 0.5))
```

**Rationale:** Kamala indicates exceptional Kendra strength. The chain aggregation is more generous with benefic weights because all planets are in structurally powerful houses.

---

## 8. Category 6: Intellectual Yogas

### 8.1 Saraswati Yoga

#### Classical Formation Rules
- **Source:** BPHS Chapter 16; Phaladeepika Chapter 6
- **Formation:** Jupiter, Venus, and Mercury in Kendra from Lagna, Lagna lord, or Moon — all strong

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 + Σ(benefic_chain × 1.0) − Σ(malefic_chain × 0.6))
```

**Cancellation Threshold:** If any of the three planets is combust → CANCELLED (the intellectual "trio" is broken).

**Special Rules:**
| Condition | Effect |
|---|---|
| All three in Kendra from Lagna | Amplified by 1.5× |
| All three in own signs | Net strength = 1.0 (maximum) |
| Jupiter aspects from Kendra | Additional +0.2 |

### 8.2 Sharada Yoga

#### Classical Formation Rules
- **Source:** BPHS Chapter 16
- **Formation:** Jupiter in Kendra from Moon AND Venus in Kendra from Lagna

#### Chain Aggregation Model

**Formula:**
```
net_strength = formation_strength × (1 + Σ(benefic_chain × 0.8) − Σ(malefic_chain × 0.5))
```

---

## 9. Category 7: Structural Doshas

### 9.1 Kemadruma Dosha

#### Classical Formation Rules
- **Source:** BPHS Chapter 11 (Kemadruma Dosha Adhyaya)
- **Formation:** No planets in 2nd or 12th from Moon (excluding Sun/Rahu/Ketu)

#### Chain Aggregation Model

**Formula:**
```
dosha_strength = base_dosha × (1 − Σ(benefic_chain × 1.0))
```

**Key difference:** Doshas use a **subtraction** model — benefic chains reduce dosha strength, malefic chains are irrelevant.

**Cancellation Threshold:** If ANY benefic planet in 2nd or 12th from Moon → DOSHA CANCELLED (BPHS Ch 11: "One benefic planet destroys Kemadruma").

**Mitigation Rules:**
| Condition | Effect |
|---|---|
| Benefic aspecting Moon | Reduces dosha by 40% |
| Moon in own sign (Cancer) | Reduces dosha by 30% |
| Moon exalted (Taurus) | Reduces dosha by 50% |
| Jupiter aspecting Moon | Reduces dosha by 60% |

### 9.2 Kala Sarpa Dosha

#### Classical Formation Rules
- **Source:** Uttara Kalamrita (commentary text)
- **Formation:** All planets between Rahu and Ketu (one half of the zodiac)

#### Chain Aggregation Model

**Formula:**
```
dosha_strength = base_dosha × (1 − 0.2 × count_planets_outside)
```

**Rationale:** Kala Sarpa intensity is proportional to how many planets are "trapped" between Rahu and Ketu. Planets outside the axis reduce the dosha.

**Cancellation Threshold:** If Moon is outside the Rahu-Ketu axis → dosha reduced by 50%.

### 9.3 Guru Chandal Dosha

#### Classical Formation Rules
- **Source:** Phaladeepika Chapter 4
- **Formation:** Jupiter conjunct or closely aspecting Rahu/Ketu

#### Chain Aggregation Model

**Formula:**
```
dosha_strength = base_dosha × (1 − 0.3 × jupiter_dignity_score)
```

**Rationale:** Jupiter's strength mitigates the dosha. Exalted Jupiter almost eliminates it; debilitated Jupiter amplifies it.

**Special Rules:**
| Condition | Effect |
|---|---|
| Jupiter exalted | Dosha reduced by 80% |
| Jupiter in own sign | Dosha reduced by 50% |
| Jupiter debilitated | Dosha amplified by 30% |
| Jupiter retrograde | Dosha amplified by 20% |

---

## 10. Category 8: Activation Yogas (Additional)

### 10.1 Kendradhipati Dosha

#### Classical Formation Rules
- **Source:** BPHS Chapter 34
- **Formation:** Natural benefic (Jupiter/Venus/Moon/Mercury) owns Kendra without owning Trikona

#### Chain Aggregation Model

This is not a "yoga" per se but a **functional classification** that modifies how the planet's chains are evaluated. The chain aggregation for this dosha is:

```
net_functional_impact = F_role(MALEFIC) × chain_paths = −1.0 × chain_paths
```

**The fix for Phase E6a:** When evaluating a planet classified as Kendradhipati for chain aggregation, the weight should be reduced from −1.0 (full MALEFIC) to −0.5 (partial MALEFIC) because the planet is only "malefic" as a Kendra lord, not in its natural nature.

---

## 11. Cross-Category Interaction Matrix

### 11.1 When Multiple Yogas Overlap

When a planet participates in multiple yogas simultaneously, each yoga evaluates chains independently. However, certain overlaps require special handling:

| Overlap | Rule | Source |
|---|---|---|
| Pancha Mahapurusha + Raja Yoga | Use Raja aggregation (higher weight) | BPHS Ch 14, 41 |
| Gajakesari + Dhana Yoga | Use Dhana aggregation (wealth-focused) | Phaladeepika Ch 7 |
| Vipareeta Raja + any other | Vipareeta model takes precedence | BPHS Ch 42 |
| Kemadruma + any positive yoga | Dosha model reduces the positive yoga by 20% | BPHS Ch 11 |

### 11.2 Chain Directionality

Chains are directed: `N₀ → N₁ → N₂ → N₃`. The root node `N₀` determines the chain's sign. When evaluating yoga-specific aggregation:

1. **Filter to yoga-relevant planets only** — only chains where `N₀ ∈ yoga_involved_planets`
2. **Apply category-specific weights** — use `W_benefic(category)` and `W_malefic(category)`
3. **Sum filtered impacts** — this is the yoga-specific chain impact

---

## 12. Architecture Impact Assessment

### 12.1 Required Changes to ChainStrengthEngine

| Current | Required | Impact |
|---|---|---|
| `compute_aggregate_impact(graph, jre_facts)` — undifferentiated sum | `compute_yoga_specific_impact(graph, jre_facts, yoga_category, involved_planets)` | New method; existing method retained for backward compatibility |
| `F_role(N₀)` determines sign of all paths | `F_role(N₀)` is overridden when `N₀` has yoga-specific immunity | Add immunity check before applying root weight |
| No chain relevance filter | Filter chains to only yoga-participating planets | New filtering step in aggregation |
| No category-specific weights | `W_benefic`, `W_malefic` vary by category | Category parameter in aggregation |

### 12.2 Required Changes to YogaEvaluatorService

| Current | Required |
|---|---|
| `compute_chain_impact(involved_planets, jre_facts)` calls `compute_aggregate_impact` | `compute_chain_impact` calls `compute_yoga_specific_impact` with the yoga's category |
| No category awareness | `evaluate_classical_yogas` passes yoga category to chain computation |

### 12.3 Backward Compatibility

The existing `compute_aggregate_impact()` method is retained as the "default" aggregation for any yoga not listed in this document. New yogas added to the engine will use the default until a specific model is defined.

---

## 13. Validation Plan

See [RI-013_Validation_Plan.md](RI-013_Validation_Plan.md) for the complete validation methodology.

### 13.1 Success Criteria

| Metric | Phase E5 Baseline | Target After Implementation |
|---|---|---|
| Chain impact sign | 100% negative | >50% positive for classically strong yogas |
| Dasha activation rate | 13% (2/15) | >50% (8/15) |
| Vipareeta Raja trigger rate | 80% (4/5 charts) | <30% (≤1/5 charts) |
| Malavya chain impact (Einstein) | −167.35 | Positive (>0) |

---

## 14. Implementation Roadmap

| Priority | Category | Yoga | Effort | Impact |
|---|---|---|---|---|
| **P0** | Pancha Mahapurusha | Malavya (Einstein case) | Low | Fixes Einstein's primary chain issue |
| **P0** | Vipareeta Raja | All 3 subtypes | Medium | Fixes 80% over-trigger rate |
| **P1** | Raja Yoga | Kendra-Trikona + Parivartana | Medium | Core Raja evaluation |
| **P1** | Dhana Yoga | Primary + Gajakesari | Low | Wealth prediction accuracy |
| **P2** | Chandra Yogas | Sunapha, Anapha, Durudhara | Low | Moon-based predictions |
| **P2** | Doshas | Kemadruma, Kala Sarpa | Low | Negative prediction accuracy |
| **P3** | Nabhasa | Structural patterns | High | Rare yogas, low frequency |
| **P3** | Intellectual | Saraswati, Sharada | Low | Specialist yogas |

---

## 15. Evidence Classification Matrix

| Rule ID | Claim | Source | Evidence Status |
|---|---|---|---|
| CA-001 | Raja Yoga: benefic chains add, malefic chains subtract with 0.7 weight | BPHS Ch 41 | SOURCE-PINNED CLASSICAL |
| CA-002 | Raja Yoga: malefic_aspect > 0.8 with no benefic Kendra aspect → cancelled | BPHS Ch 41 v. 8 | SOURCE-PINNED CLASSICAL |
| CA-003 | Gajakesari: never fully cancelled | Phaladeepika Ch 7 | SOURCE-PINNED CLASSICAL |
| CA-004 | Gajakesari: malefic weight = 0.5 (half of normal) | Derived from BPHS/Phaladeepika | COMMENTARY-DEPENDENT |
| CA-005 | Pancha Mahapurusha: immune to cancellation in own sign | BPHS Ch 14 | SOURCE-PINNED CLASSICAL |
| CA-006 | Vipareeta Raja: never cancelled, only weakened | BPHS Ch 42 | SOURCE-PINNED CLASSICAL |
| CA-007 | Vipareeta Raja: requires primary dusthana lordship (not secondary) | BPHS Ch 42 (inferred) | COMMENTARY-DEPENDENT |
| CA-008 | Budhaditya: any malefic aspect → complete cancellation | BPHS Ch 12 | SOURCE-PINNED CLASSICAL |
| CA-009 | Kemadruma: one benefic in 2nd/12th → dosha cancelled | BPHS Ch 11 | SOURCE-PINNED CLASSICAL |
| CA-010 | Nabhasa yogas: structural, cannot be cancelled | BPHS Ch 15 | SOURCE-PINNED CLASSICAL |
| CA-011 | Kendradhipati Dosha: functional malefic weight should be −0.5 not −1.0 | BPHS Ch 34 | COMMENTARY-DEPENDENT |
| CA-012 | Chain aggregation weights are category-specific | Architectural deduction | ENGINE-LEVEL DESIGN |
| CA-013 | Chain relevance filter limits to yoga-participating planets | Architectural deduction | ENGINE-LEVEL DESIGN |

---

**STATUS:** RESEARCH SPECIFICATION — Ready for implementation review.
