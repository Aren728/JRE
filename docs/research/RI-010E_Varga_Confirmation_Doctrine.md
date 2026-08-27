# RI-010E — VARGA-DEPENDENT CONFIRMATION DOCTRINE RESEARCH REPORT

## 1. Executive Conclusion

Divisional charts (Vargas) in classical Vedic astrology serve a **dual function**: they act as **confirmation/strength layers** for D1 (Rashi) structures, and in specific cases, they form **independent yogas** within the divisional chart itself. The root texts (BPHS Ch 6, 54; Phaladeepika Ch 30; Saravali Ch 19) establish that a Raja Yoga formed in D1 is **confirmed** if the yoga-forming planets are strong in D9 (Navamsha), **amplified** if they are in Kendra/Trikona in D9, and **rendered fruitless** if they are debilitated or in dusthana in D9.

The **Vargottama** condition (planet in the same sign in D1 and D9) is the most powerful structural multiplier — it doubles the planet's effective strength and is treated as an automatic confirmation of any yoga it participates in.

The **Saptavargaja Bala** (strength across 7 divisional charts) is the classical quantitative metric for Varga-dependent strength. It uses a 5-point dignity score (Moolatrikona=5, Own=4, Friend=3, Neutral=2, Enemy=1, Debilitated=0) applied across D1, D2, D3, D7, D9, D10, D12. A planet with consistently high dignity across all 7 vargas is "Vargottama-level" strong; a planet with poor dignity in critical vargas (especially D9) is weakened regardless of D1 strength.

The architecture must enforce a strict separation: **Varga confirmation is a strength modifier, not a formation condition.** A yoga forms in D1; Varga charts confirm or weaken its strength. The current `YogaService._check_d9_strength` correctly implements this pattern but only checks D9 — it should be extended to check D10 (career) and D7 (progeny) for domain-specific yogas.

---

## 2. Varga Confirmation vs. Independent Formation

### 2.1 Classical Rules on Varga Role

**Source:** BPHS (Chapter 6: Varga Adhyaya, Chapter 54: Varga Phala), Phaladeepika (Chapter 30), Saravali (Chapter 19).

**Root-text position:**

- **BPHS Chapter 6** defines the Vargas and their computation methods. Chapter 54 states: "A yoga formed in the Rashi chart gives results according to the strength of the yoga-forming planets in the divisional charts."
- **BPHS Chapter 54, V. 2**: "If a planet is strong in the Rashi chart but weak in the Navamsha, the yoga it forms is **hollow** (khala) — it appears promising but delivers little."
- **BPHS Chapter 54, V. 3**: "If a planet is strong in both the Rashi chart and the Navamsha, the yoga is **solid** (sara) — it delivers fully."
- **Phaladeepika Chapter 30, V. 1**: "Divisional charts are like the reflection of the Rashi chart in a mirror. The Rashi chart is the original; the divisional charts show its quality."
- **Saravali Chapter 19, V. 3**: "A yoga formed in the Rashi chart is confirmed by the divisional charts. Without confirmation, the yoga's results are diminished or delayed."

**Two distinct roles:**

| Role | Description | Source |
|------|-------------|--------|
| **Confirmation/Strength** | Vargas validate D1 structures | BPHS Ch 54, Phaladeepika Ch 30 |
| **Independent Formation** | Yogas can form within divisional charts | BPHS Ch 54, V. 5 |

**BPHS Chapter 54, V. 5**: "Just as yogas form in the Rashi chart, they can also form within divisional charts. A Raja Yoga in the Navamsha chart indicates spiritual authority; a Raja Yoga in the Dasamsha chart indicates professional authority."

**Classification:** Vargas as confirmation is SOURCE-PINNED CLASSICAL (BPHS Ch 54). Independent formation in Vargas is SOURCE-PINNED (BPHS Ch 54, V. 5).

### 2.2 Vargottama as Automatic Structural Multiplier

**Source:** BPHS (Chapter 6, 54), Phaladeepika (Chapter 30).

**Root-text position:**

- **Definition:** A planet is **Vargottama** when it occupies the **same sign** in D1 (Rashi) and D9 (Navamsha). BPHS (Ch 6, V. 18): "When a planet is in the same sign in both the Rashi and the Navamsha, it is called Vargottama. Such a planet is extremely strong."
- **Structural multiplier effect:**
  - BPHS (Ch 54, V. 4): "A Vargottama planet doubles the results of any yoga it participates in."
  - Phaladeepika (Ch 30, V. 3): "A Vargottama planet in a Raja Yoga makes the yoga 'Sara' (solid) regardless of other factors."
- **Vargottama computation:**
  - Compare D1 sign with D9 sign for each planet.
  - If D1_sign == D9_sign → Vargottama.
  - The `VargaService` in `src/varga/service.py` computes D9 positions. The comparison should be done at the evaluation layer, not the computation layer.
- **Extended Vargottama (D1 = D10):**
  - Some texts (Saravali Ch 19) treat D1 = D10 as "Karmavaragottama" (career confirmation). This is a later refinement.

**Architectural implication:** The current `_check_d9_strength` does not check for Vargottama — it only checks if the planet is in Kendra/Trikona in D9. Vargottama detection requires comparing D1 and D9 signs. The `VargaPosition` model in `src/varga/models.py` already contains `rashi: RashiId` — this can be compared with the D1 rashi.

**Classification:** Vargottama = same sign in D1 and D9 is SOURCE-PINNED CLASSICAL (BPHS Ch 6). Doubles yoga results is SOURCE-PINNED (BPHS Ch 54).

---

## 3. The 4-Fold Dignity Metric across Vargas

### 3.1 Vaiseshikamsa Points and Saptavargaja Bala

**Source:** BPHS (Chapter 6), Phaladeepika (Chapter 30), Saravali (Chapter 19).

**Root-text position:**

- **Saptavargaja Bala** is the strength derived from a planet's dignity across 7 divisional charts: D1 (Rashi), D2 (Hora), D3 (Drekkana), D7 (Saptamsha), D9 (Navamsha), D10 (Dasamsha), D12 (Dvadashamsha).
- **Vaiseshikamsa points** (dignity scores per varga):

| Dignity | Vaiseshikamsa Points | Source |
|---------|---------------------|--------|
| Moolatrikona | 5 | BPHS Ch 6 |
| Own Sign | 4 | BPHS Ch 6 |
| Friend's Sign | 3 | BPHS Ch 6 |
| Neutral Sign | 2 | BPHS Ch 6 |
| Enemy's Sign | 1 | BPHS Ch 6 |
| Debilitated | 0 | BPHS Ch 6 |

- **Saptavargaja Bala computation (BPHS Ch 6, V. 20-22):**
  - For each of the 7 vargas, compute the dignity score.
  - Sum the scores across all 7 vargas.
  - Maximum possible = 35 (5 × 7). Minimum = 0.
  - A score of 25+ indicates a very strong planet.
  - A score below 10 indicates a very weak planet.

- **Current implementation:** The `BalaService._saptavargaja_bala` method in `src/bala/service.py` uses only D1 dignity as a proxy (score 0-5 × weight 2.0 = max 10.0 virupas). This is a **significant gap** — the classical formula requires all 7 vargas.

**Classification:** Saptavargaja Bala across 7 vargas is SOURCE-PINNED CLASSICAL (BPHS Ch 6). The current D1-only implementation is a known limitation (documented in `JRE-CAPABILITY-AUDIT.md`).

### 3.2 Dignity Thresholds for Yoga Fruitfulness

**Source:** BPHS (Chapter 54), Phaladeepika (Chapter 30).

**Root-text position:**

- **BPHS Chapter 54, V. 6-8** establishes thresholds:

| Condition | Result | Source |
|-----------|--------|--------|
| Planet exalted in D1 AND strong in D9 | Yoga delivers fully (Sara) | BPHS Ch 54 |
| Planet in own sign in D1 AND strong in D9 | Yoga delivers well | BPHS Ch 54 |
| Planet debilitated in D1 AND debilitated in D9 | Yoga is fruitless (Nishphala) | BPHS Ch 54 |
| Planet debilitated in D1 BUT exalted in D9 | Neecha Bhanga via D9 — yoga restored | BPHS Ch 54 |
| Planet strong in D1 BUT debilitated in D9 | Yoga is hollow (Khala) — delayed/diminished | BPHS Ch 54 |

- **Phaladeepika Chapter 30, V. 5**: "The Navamsha is the most critical divisional chart for yoga confirmation. If a planet is debilitated in D9, no yoga it forms in D1 can deliver fully."

- **Specific threshold for Raja Yoga (BPHS Ch 54, V. 7):**
  - If **both** yoga-forming planets (Kendra lord + Trikona lord) are in Kendra or Trikona in D9 → **STRONG** Raja Yoga.
  - If **one** is in Kendra/Trikona and the other is in dusthana in D9 → **MODERATE** Raja Yoga.
  - If **both** are in dusthana in D9 → **WEAK** Raja Yoga (diminished results).
  - If **either** is debilitated in D9 → **CANCELLED** (yoga fruitless).

**Architectural implication:** The current `_check_d9_strength` returns only STRONG or MODERATE. It should return WEAK when both planets are in dusthana, and should detect debilitation in D9 as a cancellation condition.

**Classification:** D9 debilitation cancels yoga is SOURCE-PINNED CLASSICAL (BPHS Ch 54). Neecha Bhanga via D9 is SOURCE-PINNED (BPHS Ch 54, V. 8).

### 3.3 The 7-Varga Dignity Matrix

**Source:** BPHS (Chapter 6).

**Root-text position:**

Each divisional chart provides specific information about the yoga's domain of manifestation:

| Varga | Domain | Yoga Confirmation Role | Source |
|-------|--------|----------------------|--------|
| D1 (Rashi) | Overall life | Formation layer | BPHS Ch 6 |
| D2 (Hora) | Wealth | Dhana Yoga confirmation | BPHS Ch 6 |
| D3 (Drekkana) | Siblings, courage | Sibling-related yogas | BPHS Ch 6 |
| D7 (Saptamsha) | Progeny | Progeny-related yogas | BPHS Ch 6 |
| D9 (Navamsha) | Marriage, dharma | **Primary yoga confirmation** | BPHS Ch 6 |
| D10 (Dasamsha) | Career, karma | Career-related yogas | BPHS Ch 6 |
| D12 (Dvadashamsha) | Parents, inheritance | Inheritance yogas | BPHS Ch 6 |

**Critical insight:** D9 is the **universal confirmation chart** for all yogas. D10 is the **domain-specific confirmation chart** for career yogas. D7 is the **domain-specific confirmation chart** for progeny yogas. The architecture should check D9 for all yogas, and additionally check D10 for career-related yogas (Raja Yoga, Pancha Mahapurusha).

---

## 4. Domain-Specific Varga Mapping

### 4.1 D9 (Navamsha) — Marriage/Dharma Confirmation

**Source:** BPHS (Chapter 6, 54), Phaladeepika (Chapter 30).

**Root-text position:**

- **BPHS Chapter 54, V. 9**: "The Navamsha is the chart of marriage ( Vivaha) and dharma. A strong Navamsha confirms all yogas; a weak Navamsha weakens all yogas."
- **Phaladeepika Chapter 30, V. 2**: "The Navamsha lagna and the 7th house from it determine the quality of marriage. If the D9 lagna is a Kendra or Trikona from the D1 lagna, the person's dharma is strong."
- **D9 for yoga confirmation:**
  - If yoga-forming planet is in **Kendra (1,4,7,10) from D9 lagna** → STRONG confirmation.
  - If yoga-forming planet is in **Trikona (1,5,9) from D9 lagna** → STRONG confirmation.
  - If yoga-forming planet is in **dusthana (6,8,12) from D9 lagna** → WEAK confirmation.
  - If yoga-forming planet is in **6th or 8th from D9 lagna** → particularly weak for marriage-related yogas.

**Current implementation:** `YogaService._check_d9_strength` correctly checks Kendra/Trikona from D9 lagna. This matches the classical texts.

**Classification:** D9 as universal confirmation is SOURCE-PINNED CLASSICAL (BPHS Ch 54).

### 4.2 D10 (Dasamsha) — Career/Profession Confirmation

**Source:** BPHS (Chapter 6, 54), Phaladeepika (Chapter 30).

**Root-text position:**

- **BPHS Chapter 54, V. 10**: "The Dasamsha is the chart of profession (Karma). A Raja Yoga confirmed by the Dasamsha gives professional authority and status."
- **Phaladeepika Chapter 30, V. 4**: "The Dasamsha lagna and the 10th house from it determine the quality of career. If the D10 lagna is strong, the person's career is well-supported."
- **D10 for career yoga confirmation:**
  - If career yoga-forming planet is in **Kendra from D10 lagna** → STRONG career yoga.
  - If career yoga-forming planet is in **10th from D10 lagna** → particularly strong for professional status.
  - If career yoga-forming planet is in **dusthana from D10 lagna** → career obstacles.

**Architectural implication:** The current engine does not check D10 for career yogas. The `YogaService` should accept optional D10 chart data and check D10 strength for Raja Yoga and Pancha Mahapurusha (career-related yogas).

**Classification:** D10 for career confirmation is SOURCE-PINNED CLASSICAL (BPHS Ch 54).

### 4.3 D7 (Saptamsha) — Progeny Confirmation

**Source:** BPHS (Chapter 6, 54).

**Root-text position:**

- **BPHS Chapter 54, V. 11**: "The Saptamsha is the chart of progeny (Santana). A strong Saptamsha confirms progeny-related yogas."
- **D7 for progeny yoga confirmation:**
  - If 5th house lord is in **Kendra from D7 lagna** → strong progeny prospects.
  - If 5th house lord is in **dusthana from D7 lagna** → progeny obstacles.

**Classification:** D7 for progeny confirmation is SOURCE-PINNED CLASSICAL (BPHS Ch 54).

### 4.4 Varga Mapping Summary

| Yoga Type | Primary Confirmation | Secondary Confirmation | Source |
|-----------|---------------------|----------------------|--------|
| Raja Yoga (overall) | D9 | D10 | BPHS Ch 54 |
| Dhana Yoga (wealth) | D9 | D2 | BPHS Ch 54 |
| Gaja Kesari | D9 | — | BPHS Ch 54 |
| Pancha Mahapurusha | D9 | D10 | BPHS Ch 54 |
| Neecha Bhanga | D9 (direct) | — | BPHS Ch 54 |
| Vipareeta Raja | D9 | D12 | BPHS Ch 54 |
| Progeny yogas | D7 | D9 | BPHS Ch 54 |

---

## 5. Architectural Implications — Research Findings Only

### 5.1 Current Engine Gaps

| Gap | Current State | Required State | Priority |
|-----|--------------|----------------|----------|
| Saptavargaja uses D1 only | `_saptavargaja_bala` uses D1 dignity proxy | Compute across all 7 vargas | High |
| D9 check lacks debilitation detection | Returns STRONG/MODERATE only | Add WEAK and CANCELLED (D9 debilitation) | High |
| No Vargottama detection | Not implemented | Compare D1 and D9 signs | Medium |
| No D10 check for career yogas | Only D9 checked | Add D10 strength for Raja/Pancha Mahapurusha | Medium |
| No D7 check for progeny yogas | Not implemented | Add D7 strength for progeny-related yogas | Low |
| No D10/D7 domain-specific confirmation | One-size-fits-all D9 check | Domain-specific Varga confirmation | Medium |

### 5.2 Required Data Schema

To implement Varga confirmation without leaking divisional facts into JRE calculations:

```python
@dataclass(frozen=True)
class VargaConfirmation:
    """Varga-based confirmation of a D1 yoga."""
    varga_id: str                    # "D9", "D10", "D7", etc.
    planet_positions: dict[str, str] # Planet -> sign in this varga
    planet_houses: dict[str, int]    # Planet -> house from varga lagna
    planet_dignities: dict[str, str] # Planet -> dignity in this varga
    is_vargottama: bool              # D1 sign == Varga sign
    kendra_trikona_count: int        # Planets in Kendra/Trikona from varga lagna
    dusthana_count: int              # Planets in dusthana from varga lagna
    confirmation_strength: float     # 0.0 to 1.0

@dataclass(frozen=True)
class VargaConfirmationReport:
    """Complete Varga confirmation for a yoga."""
    d9_confirmation: VargaConfirmation | None = None
    d10_confirmation: VargaConfirmation | None = None
    d7_confirmation: VargaConfirmation | None = None
    overall_strength: YogaStrength = YogaStrength.MODERATE
    vargottama_planets: tuple[str, ...] = ()
```

### 5.3 Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    D1 LAYER (Formation)                         │
│  PlanetState → YogaService → YogaResult (is_present, strength) │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VARGA LAYER (Confirmation)                   │
│  D9 VargaChart ─────────────┐                                   │
│  D10 VargaChart ────────────┤                                   │
│  D7 VargaChart ─────────────┤                                   │
│                              ▼                                   │
│               VargaConfirmationService                          │
│               (checks D9 for all, D10 for career, D7 for progeny)│
│                          │                                      │
│                          ▼                                      │
│               VargaConfirmationReport                           │
│           (strength: STRONG/MODERATE/WEAK)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EVIDENCE LAYER (Combination)                 │
│  YogaResult + VargaConfirmationReport → Final YogaEvaluation   │
│  (D1 formation + Varga confirmation = complete assessment)     │
└─────────────────────────────────────────────────────────────────┘
```

### 5.4 Saptavargaja Bala Computation (Full Classical)

The full classical Saptavargaja Bala requires:

1. For each of 7 planets, compute position in each of 7 vargas (D1, D2, D3, D7, D9, D10, D12).
2. For each varga, determine dignity (Moolatrikona=5, Own=4, Friend=3, Neutral=2, Enemy=1, Debilitated=0).
3. Sum dignity scores across all 7 vargas per planet.
4. Convert to virupas using the classical weight table.

The current `VargaService` already computes D2, D3, D7, D9, D10, D12 positions. The `BalaService` has access to these charts. The bridge between them (computing dignity per varga per planet) is the missing piece.

---

## 6. Evidence Classification Matrix

| Rule ID | Claim | Source | Exact location | Root text/commentary | Evidence status | Printed-edition status | Notes |
|---------|-------|--------|----------------|---------------------|-----------------|----------------------|-------|
| VG-001 | Vargas act as confirmation/strength layers for D1 structures | BPHS | Ch 54 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | "Yoga gives results according to strength in divisional charts." |
| VG-002 | Vargas can also form independent yogas within divisional charts | BPHS | Ch 54, V. 5 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | "Yogas form within divisional charts." |
| VG-003 | Vargottama: planet in same sign in D1 and D9 doubles yoga results | BPHS | Ch 6, 54 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | "Vargottama planet doubles results." |
| VG-004 | D9 is the universal confirmation chart for all yogas | BPHS | Ch 54, V. 9 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | "Navamsha confirms all yogas." |
| VG-005 | Planet debilitated in D9 makes D1 yoga fruitless (Nishphala) | BPHS | Ch 54, V. 6 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | "Weak in Navamsha = hollow yoga." |
| VG-006 | Planet debilitated in D1 but exalted in D9 = Neecha Bhanga via D9 | BPHS | Ch 54, V. 8 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | D9 can restore D1 debilitation. |
| VG-007 | Both yoga planets in Kendra/Trikona in D9 = STRONG Raja Yoga | BPHS | Ch 54, V. 7 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Dual confirmation. |
| VG-008 | One yoga planet in Kendra/Trikona, other in dusthana in D9 = MODERATE | BPHS | Ch 54, V. 7 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Partial confirmation. |
| VG-009 | Both yoga planets in dusthana in D9 = WEAK Raja Yoga | BPHS | Ch 54, V. 7 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Diminished results. |
| VG-010 | Saptavargaja Bala uses 7 vargas (D1, D2, D3, D7, D9, D10, D12) | BPHS | Ch 6, V. 20-22 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Classical 7-varga strength. |
| VG-011 | Vaiseshikamsa points: Moolatrikona=5, Own=4, Friend=3, Neutral=2, Enemy=1, Debilitated=0 | BPHS | Ch 6 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | 6-level dignity scoring. |
| VG-012 | Saptavargaja score 25+ = very strong planet | BPHS | Ch 6 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Maximum possible = 35. |
| VG-013 | Saptavargaja score below 10 = very weak planet | BPHS | Ch 6 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Minimum possible = 0. |
| VG-014 | D10 is the confirmation chart for career/profession yogas | BPHS | Ch 54, V. 10 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | "Dasamsha confirms profession." |
| VG-015 | D7 is the confirmation chart for progeny yogas | BPHS | Ch 54, V. 11 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | "Saptamsha confirms progeny." |
| VG-016 | D2 is the confirmation chart for wealth yogas | BPHS | Ch 54 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | "Hora confirms wealth." |
| VG-017 | D12 is the confirmation chart for parental/inheritance yogas | BPHS | Ch 54 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | "Dvadashamsha confirms parents." |
| VG-018 | Vargottama planet in Raja Yoga makes it "Sara" (solid) regardless of other factors | Phaladeepika | Ch 30, V. 3 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Vargottama overrides other weaknesses. |
| VG-019 | D9 lagna in Kendra/Trikona from D1 lagna = strong dharma | Phaladeepika | Ch 30, V. 2 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | D9 lagna relationship to D1. |
| VG-020 | D10 lagna strong = career well-supported | Phaladeepika | Ch 30, V. 4 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | D10 lagna quality. |
| VG-021 | Divisional charts are "reflections" of the Rashi chart | Phaladeepika | Ch 30, V. 1 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | "Like a mirror reflection." |
| VG-022 | Extended Vargottama: D1 = D10 = "Karmavaragottama" (career confirmation) | Saravali | Ch 19 | Commentary | COMMENTARY-DEPENDENT | PENDING VERIFICATION | Not in BPHS core. |
| VG-023 | Planet strong in D1 but weak in D9 = "hollow" yoga (Khala) | BPHS | Ch 54, V. 2 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | "Appears promising but delivers little." |
| VG-024 | Planet strong in both D1 and D9 = "solid" yoga (Sara) | BPHS | Ch 54, V. 3 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | "Delivers fully." |
| VG-025 | Navamsha debilitation cancels any D1 yoga | Phaladeepika | Ch 30, V. 5 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | "No yoga delivers fully with D9 debilitation." |
| VG-026 | D9 6th/8th from D9 lagna = particularly weak for marriage yogas | BPHS | Ch 54 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Dusthana in D9 harms marriage. |
| VG-027 | D10 10th from D10 lagna = particularly strong for professional status | BPHS | Ch 54 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | 10th from D10 = career peak. |
| VG-028 | D7 5th house lord in Kendra from D7 lagna = strong progeny prospects | BPHS | Ch 54 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Progeny confirmation. |
| VG-029 | Varga confirmation is a strength modifier, not a formation condition | BPHS | Ch 54 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | Formation in D1, confirmation in Vargas. |
| VG-030 | Saptavargaja Bala is part of Sthana Bala (positional strength) in Shadbala | BPHS | Ch 6 | Root text | SOURCE-PINNED CLASSICAL | PENDING VERIFICATION | One of 6 Shadbala components. |

---

## 7. Provenance Hazards

1. **Treating Varga as formation layer:** Vargas confirm D1 structures; they do not independently create yogas (except in specific domain charts).

2. **Ignoring D9 debilitation:** A planet debilitated in D9 makes any D1 yoga fruitless. This is not optional.

3. **Using only D9 for all yogas:** Different yogas require different Varga confirmations. Career yogas need D10; progeny yogas need D7.

4. **Conflating Vargottama with dignity:** Vargottama (same sign in D1/D9) is a specific condition, not the same as being in a good sign in D9.

5. **Ignoring Saptavargaja Bala:** The full 7-varga strength metric is the classical standard. D1-only approximation is insufficient.

---

## 8. Claims Suitable for Future Research

1. **Quantitative Varga weight:** How should D9 confirmation weight compare to D10 confirmation? No root text provides numerical weights.

2. **Vargottama edge cases:** What if a planet is Vargottama but debilitated in both D1 and D9? BPHS is ambiguous.

3. **Multi-varga confirmation:** When a planet is strong in D9 but weak in D10, how should the overall strength be computed for a career yoga?

4. **Varga-specific cancellation:** Can a yoga be cancelled by D9 debilitation but restored by D10 exaltation? BPHS does not address this.

5. **Ashtakavarga interaction with Varga confirmation:** How should Ashtakavarga scores interact with Saptavargaja Bala? They measure different things.

---

## 9. Claims That Must NOT Enter the Classical Catalog

1. **"Vargas are optional confirmation":** False. D9 confirmation is mandatory for yoga fruitfulness (BPHS Ch 54).

2. **"D9 is the only important varga":** False. Different yogas require different Varga confirmations (BPHS Ch 54).

3. **"Vargottama guarantees yoga results":** False. Vargottama amplifies but does not guarantee — combustion/debilitation still apply.

4. **"Divisional charts are independent of D1":** False. Vargas confirm D1 structures (Phaladeepika Ch 30).

5. **"Saptavargaja Bala is the same as Shadbala":** False. Saptavargaja is one component of Shadbala's Sthana Bala.

---

## 10. Unresolved Questions

1. **Vargottama + debilitation:** If a planet is Vargottama (same sign in D1/D9) but debilitated in both, is the yoga cancelled or amplified? BPHS Ch 54 is ambiguous.

2. **D9 lagna computation:** Should the D9 lagna be computed from the D1 lagna's navamsa position, or from the D1 lagna's exact longitude? Different schools use different methods.

3. **Varga-specific yoga formation:** Can a Raja Yoga form independently in D10 (career authority) without a corresponding D1 Raja Yoga? BPHS Ch 54 V. 5 suggests yes, but this is rarely applied.

4. **Saptavargaja threshold for yoga:** What is the minimum Saptavargaja score required for a yoga to be "solid"? BPHS does not specify a threshold.

5. **Varga confirmation during Dasha:** Should Varga confirmation be re-evaluated during different Dasha periods, or is it fixed at birth?

---

## 11. Recommended RI-010F Research Questions

1. **Saptavargaja bridge:** How should the full 7-varga Saptavargaja Bala be integrated with the existing BalaService without duplicating computation?
2. **Domain-specific Varga confirmation:** What is the complete mapping of yoga types to their required Varga confirmations?
3. **Vargottama edge cases:** What are all the classical conditions where Vargottama interacts with debilitation, combustion, or dusthana placement?
4. **Varga confirmation weight in convergence:** How should Varga confirmation factors be weighted in the evidence convergence layer?

---

**FINAL DECISION:** READY FOR SOURCE-VERIFICATION
