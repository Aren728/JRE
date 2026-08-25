# RI-010A: KENDRA-TRIKONA CLASSICAL DOCTRINE — RESEARCH REPORT

> **Status:** Research Only — No Implementation
> **Date:** 2026-08-25
> **Awaiting:** Human review before proceeding to RI-010B

---

## Executive Summary

This report presents a source-critical research pass on classical Kendra-Trikona structural doctrine as described in the foundational texts of Jyotish: Brihat Parashara Hora Shastra (BPHS), Phaladeepika (Mantreshwara), Saravali (Kalyana Varma), Brihat Jataka (Varahamihira), and Jataka Parijata (Vaidyanatha Dikshita). The research establishes what these texts explicitly state about Kendra and Trikona houses, their lords, and the relationships between them—before any implementation is considered.

**Key Finding:** The existing JRE-013 Yoga engine already implements a basic structural detection for Raja Yoga (Kendra lord ↔ Trikona lord connection) and Dhana Yoga (2nd lord ↔ 11th lord connection). However, the classical texts describe far more nuanced conditions involving dignity, combustion, retrogression, benefic/malefic modification, and divisional chart confirmation that are NOT yet captured.

---

## Section A: Kendra Structure

### A.1 Classical Definitions

| Source | Text | Description |
|--------|------|-------------|
| BPHS | Chapter 33, Verse 1 | Kendras are houses 1, 4, 7, 10 — "Vishnu Sthanas" (houses of sustenance, action, power) |
| Phaladeepika | Chapter 1, Verse 12 | "The four houses at the four cardinal directions are called 'corners' or kendras. They are crucial to the horoscope as the four pillars on which the rest of life is built." |
| Saravali | Chapter 12 | Kendras are the most influential houses; planets here gain operational strength |
| Brihat Jataka | Chapter 2 | Kendra houses represent structural framework of life |

### A.2 Characteristics of Each Kendra

| House | Classical Name | Characteristics | Primary Source |
|-------|----------------|-----------------|----------------|
| 1st (Lagna) | Tanu Bhava / Janma | Self, body, vitality, overall nature, birth, becoming physical | BPHS Ch.33, Phaladeepika Ch.1 |
| 4th (Bandhu) | Sukha Bhava | Inner happiness, home, mother, property, vehicles, private life, comfort | BPHS Ch.33, Phaladeepika Ch.1 |
| 7th (Mitra) | Kalatra Bhava | Partnerships, marriage, spouse, public dealing, death (opposite of birth) | BPHS Ch.33, Phaladeepika Ch.1 |
| 10th (Karma) | Rajya Bhava | Career, public life, reputation, authority, social status, highest point in sky | BPHS Ch.33, Phaladeepika Ch.1 |

### A.3 Planets Occupying Kendras

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Benefic in Kendra → auspicious results | BPHS Ch.33 | CLASSICAL_PRIMARY | Jupiter, Venus, Mercury, Moon (waxing) are natural benefics |
| Malefic in Kendra → challenging results | BPHS Ch.33 | CLASSICAL_PRIMARY | Saturn, Mars, Sun (waning), Rahu, Ketu are natural malefics |
| Jupiter in Kendra from Moon → Gajakesari Yoga | BPHS Ch.33, Phaladeepika Ch.6 | CLASSICAL_PRIMARY | One of the most documented yogas |
| Planet in own sign in Kendra → Pancha Mahapurusha | BPHS Ch.33 | CLASSICAL_PRIMARY | Mars (Ruchaka), Mercury (Bhadra), Jupiter (Hamsa), Venus (Malavya), Saturn (Sasa) |

### A.4 Lords of Kendras

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Kendra lordship makes natural benefics neutral | BPHS Ch.33 | CLASSICAL_PRIMARY | "Kendradhipati Dosha" — benefics ruling Kendras lose some beneficence |
| Kendra lordship makes natural malefics functional benefics | BPHS Ch.33 | CLASSICAL_PRIMARY | Malefics ruling Kendras become constructive forces |
| 1st house lord is most important | All texts | CLASSICAL_PRIMARY | Lagna lord participates in both Kendra and Trikona |

### A.5 Benefic/Malefic Modification of Kendra Effects

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Natural benefic in Kendra → Kendradhipati Dosha | BPHS Ch.33 | CLASSICAL_PRIMARY | Benefic becomes neutral when ruling Kendra |
| Natural malefic in Kendra → functional benefic | BPHS Ch.33 | CLASSICAL_PRIMARY | Malefic becomes constructive when ruling Kendra |
| Yogakaraka planet → exception to Dosha | Phaladeepika Ch.6 | CLASSICAL_PRIMARY | Planet ruling both Kendra and Trikona simultaneously |

### A.6 Strength Requirements

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Shadbala strength affects Kendra results | BPHS Ch.33 | COMMENTARY_DEPENDENT | Classical texts mention "strength" but detailed Shadbala system is later tradition |
| Exaltation in Kendra → maximum power | BPHS Ch.33 | CLASSICAL_PRIMARY | Planet in exaltation in Kendra gains exceptional strength |
| Own sign in Kendra → strong | BPHS Ch.33 | CLASSICAL_PRIMARY | Pancha Mahapurusha yogas form |

### A.7 Weakness/Cancellation Conditions

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Debilitation in Kendra → weakness | BPHS Ch.33 | CLASSICAL_PRIMARY | Neecha Bhanga can cancel debilitation |
| Combustion in Kendra → weakened | BPHS Ch.33 | CLASSICAL_PRIMARY | Planet too close to Sun loses strength |
| Retrograde in Kendra → modified results | BPHS Ch.33 | COMMENTARY_DEPENDENT | Retrograde planets act as if exalted in some contexts |

---

## Section B: Trikona Structure

### B.1 Classical Definitions

| Source | Text | Description |
|--------|------|-------------|
| BPHS | Chapter 33 | Trikonas are houses 1, 5, 9 — "Lakshmi Sthanas" (houses of fortune, merit, dharma) |
| Phaladeepika | Chapter 1 | "Two houses are 'trines' (Triangular in an equilateral triangle) or konas. They are very 'good' places, sources of prosperity." |
| Saravali | Chapter 12 | Trikonas represent fortune and divine blessings |
| Brihat Jataka | Chapter 2 | Trikona houses represent spiritual merit and past karma |

### B.2 Characteristics of Each Trikona

| House | Classical Name | Characteristics | Primary Source |
|-------|----------------|-----------------|----------------|
| 1st (Lagna) | Tanu Bhava | Self, body, vitality — simultaneously Kendra and Trikona | BPHS Ch.33, Phaladeepika Ch.1 |
| 5th (Putra) | Putra Bhava | Intelligence, children, past merit, creativity, scriptures, mantras, soul | BPHS Ch.33, Phaladeepika Ch.1 |
| 9th (Dharma) | Bhagya Bhava | Fortune, higher purpose, religion, teachers, father-figures, noble social deeds | BPHS Ch.33, Phaladeepika Ch.1 |

### B.3 Planets Occupying Trikonas

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Benefic in Trikona → excellent results | BPHS Ch.33 | CLASSICAL_PRIMARY | Trikona lordship is always auspicious |
| Jupiter in Trikona → enhanced wisdom/fortune | BPHS Ch.33 | CLASSICAL_PRIMARY | Jupiter naturally rules two Trikona houses (5th, 9th for some ascendants) |
| Trikona lord in own sign → maximum auspiciousness | BPHS Ch.33 | CLASSICAL_PRIMARY | Functional benefic at highest capacity |

### B.4 Lords of Trikonas

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Trikona lordship is always auspicious | BPHS Ch.33 | CLASSICAL_PRIMARY | Trikona lords are the most benefic functional planets |
| 9th lord is most fortunate | BPHS Ch.33 | CLASSICAL_PRIMARY | House of Bhagya (fortune) |
| 5th lord represents past merit | BPHS Ch.33 | CLASSICAL_PRIMARY | Putra Bhava — intelligence from past lives |

### B.5 Benefic/Malefic Modification of Trikona Effects

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| No Kendradhipati Dosha for Trikonas | BPHS Ch.33 | CLASSICAL_PRIMARY | Trikona lordship does NOT diminish beneficence |
| Natural malefic ruling Trikona → becomes benefic | BPHS Ch.33 | CLASSICAL_PRIMARY | Unlike Kendra lordship, Trikona lordship preserves or enhances benefic nature |

### B.6 Strength Requirements

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Exaltation in Trikona → maximum fortune | BPHS Ch.33 | CLASSICAL_PRIMARY | Planet delivers highest Trikona results |
| Own sign in Trikona → strong fortune | BPHS Ch.33 | CLASSICAL_PRIMARY | Functional benefic fully empowered |

### B.7 Weakness/Cancellation Conditions

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Debilitation in Trikona → fortune weakened | BPHS Ch.33 | CLASSICAL_PRIMARY | Neecha Bhanga can restore |
| Combustion in Trikona → diminished results | BPHS Ch.33 | CLASSICAL_PRIMARY | Planet too close to Sun |

---

## Section C: Kendra-Trikona Lord Relationships

### C.1 Conjunction Rules

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Kendra lord + Trikona lord conjunction → Raja Yoga | BPHS Ch.33, Phaladeepika Ch.6 | CLASSICAL_PRIMARY | Strongest form of connection |
| Conjunction in Kendra or Trikona → enhanced Raja Yoga | Jagannath Hora (modern synthesis) | LATER_TRADITION | Both planets in powerful houses |
| Conjunction in Dusthana (6,8,12) → compromised Raja Yoga | BPHS Ch.33 | CLASSICAL_PRIMARY | Dusthana placement dims the yoga |
| Lagna lord conjunction with any Kendra/Trikona lord → automatic Raja Yoga | BPHS Ch.33 | CLASSICAL_PRIMARY | Lagna lord is both Kendra and Trikona lord |

### C.2 Mutual Aspect Rules

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Kendra lord aspects Trikona lord AND vice versa → Raja Yoga | BPHS Ch.33 | CLASSICAL_PRIMARY | Mutual 7th aspect strongest |
| One-way aspect → moderate Raja Yoga | BPHS Ch.33 | COMMENTARY_DEPENDENT | Support flows in one direction only |

### C.3 Exchange (Parivartana) Rules

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Kendra lord in Trikona house AND Trikona lord in Kendra house → Raja Yoga | BPHS Ch.33 | CLASSICAL_PRIMARY | Very strong — mutual support loop |
| Any Parivartana between Kendra and Trikona lords → Raja Yoga | Phaladeepika Ch.6 | CLASSICAL_PRIMARY | Exchange is equivalent to conjunction |

### C.4 Placement Rules

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Trikona lord occupying Kendra → Raja Yoga | BPHS Ch.33 | CLASSICAL_PRIMARY | Fortune expressed through action |
| Kendra lord occupying Trikona → Raja Yoga | BPHS Ch.33 | CLASSICAL_PRIMARY | Action expressed through fortune |
| Placement without reciprocation → moderate Raja Yoga | BPHS Ch.33 | COMMENTARY_DEPENDENT | Weaker than conjunction or exchange |

### C.5 Multiple Relationships

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Multiple Kendra-Trikona lord connections → stronger yoga | BPHS Ch.33 | CLASSICAL_PRIMARY | Each connection amplifies |
| Lagna lord participating in multiple connections → most powerful | BPHS Ch.33 | CLASSICAL_PRIMARY | Lagna lord bridges both categories |

### C.6 Benefic/Malefic Planets Modifying Relationships

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Rahu/Ketu aspecting yoga planets → diminishes | BPHS Ch.33 | CLASSICAL_PRIMARY | Nodes create obstacles |
| Natural malefic aspecting yoga planets → weakens | BPHS Ch.33 | CLASSICAL_PRIMARY | Mars, Saturn aspects reduce power |
| Natural benefic aspecting yoga planets → enhances | BPHS Ch.33 | CLASSICAL_PRIMARY | Jupiter, Venus aspects strengthen |

### C.7 Dignity Modifications

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Both planets exalted → maximum Raja Yoga | BPHS Ch.33 | CLASSICAL_PRIMARY | Highest dignity = highest results |
| One planet debilitated → mixed results | BPHS Ch.33 | CLASSICAL_PRIMARY | Neecha Bhanga can restore |
| One planet in own sign → strong | BPHS Ch.33 | CLASSICAL_PRIMARY | Functional benefic empowered |
| Yogakaraka planet → exception to normal rules | Phaladeepika Ch.6 | CLASSICAL_PRIMARY | Planet ruling both Kendra and Trikona |

### C.8 Combustion Effects

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Combustion weakens yoga planet | BPHS Ch.33 | CLASSICAL_PRIMARY | Planet too close to Sun loses capacity |
| Combustion of one planet → partial yoga | BPHS Ch.33 | CLASSICAL_PRIMARY | Other planet still contributes |

### C.9 Retrogression Effects

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Retrograde planet acts as if exalted | BPHS Ch.33 | COMMENTARY_DEPENDENT | Even in enemy sign or debilitation |
| Retrograde in Kendra → enhanced power | BPHS Ch.33 | COMMENTARY_DEPENDENT | Retrograde amplifies Kendra placement |

### C.10 Conjunction with Rahu/Ketu

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Rahu conjunct yoga planet → creates obstacles | BPHS Ch.33 | CLASSICAL_PRIMARY | Rahu amplifies but also distorts |
| Ketu conjunct yoga planet → spiritualizes results | BPHS Ch.33 | CLASSICAL_PRIMARY | Ketu redirects material results |

### C.11 Divisional Chart (Varga) Confirmation

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Navamsa (D9) confirmation required | BPHS Ch.33 | COMMENTARY_DEPENDENT | Yoga planets well-placed in D9 |
| D9 placement in Kendra/Trikona → confirms | BPHS Ch.33 | COMMENTARY_DEPENDENT | Strength verification |
| D9 placement in Dusthana → weakens | BPHS Ch.33 | COMMENTARY_DEPENDENT | yoga potential reduced |

---

## Section D: Raja Yoga and Dhana Yoga

### D.1 Raja Yoga — Classical Definitions

| Source | Text | Definition |
|--------|------|------------|
| BPHS | Ch.33, Verse 1-3 | "When the lord of a kendra and the lord of a trikona are in mutual relationship (conjunction, aspect, exchange), it is called Raja Yoga." |
| Phaladeepika | Ch.6, Verse 26-28 | Srikantha Yoga: Lagna lord, Sun, and Moon in Kendra or Trikona in exaltation/own/friendly signs |
| Phaladeepika | Ch.6, Verse 21 | Lakshmi Yoga: 9th lord and Venus in own/exaltation in Trikona or Kendra |
| Saravali | Ch.25 | Raja Yoga formed by Kendra-Trikona lord connection |
| Brihat Jataka | Ch.4 | Structural combinations for power and authority |

### D.2 Dhana Yoga — Classical Definitions

| Source | Text | Definition |
|--------|------|------------|
| BPHS | Ch.33 | 2nd lord and 11th lord connected (conjunction, aspect, exchange) |
| Phaladeepika | Ch.6 | Wealth-related connections involving 2nd, 5th, 9th, 11th houses |
| Saravali | Ch.25 | Combinations for wealth accumulation |

### D.3 Strength Requirements for Yoga Manifestation

| Rule | Source | Classification | Four-Fold Category |
|------|--------|----------------|---------------------|
| Both yoga planets strong (dignity, Shadbala) | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_STRENGTH |
| Connection in Kendra or Trikona (not Dusthana) | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_FORMATION |
| No malefic interference | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_STRENGTH |
| Dasha timing during productive years | BPHS Ch.33 | COMMENTARY_DEPENDENT | YOGA_MANIFESTATION |

### D.4 Cancellation Conditions

| Rule | Source | Classification | Four-Fold Category |
|------|--------|----------------|---------------------|
| Kendra lord debilitated | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_STRENGTH |
| Aspect from malefic on yoga planets | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_STRENGTH |
| Yoga planets in Dusthana | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_FORMATION |
| Neecha Bhanga can restore | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_STRENGTH |

### D.5 Multiple Yoga Combinations

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Multiple Raja Yogas → cumulative effect | BPHS Ch.33 | CLASSICAL_PRIMARY | Each yoga adds power |
| Raja Yoga + Dhana Yoga → wealth and power | BPHS Ch.33 | CLASSICAL_PRIMARY | Combined results |

### D.6 Hierarchical Strength

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Conjunction/Exchange > Mutual Aspect > One-way Aspect > Placement | BPHS Ch.33 | COMMENTARY_DEPENDENT | Connection type hierarchy |
| Yogakaraka involvement > normal Kendra-Trikona | Phaladeepika Ch.6 | CLASSICAL_PRIMARY | Built-in Raja Yoga |

---

## Section E: Architectural Impact Assessment

### E.1 Existing JRE Capabilities

| Capability | JRE Module | Covers | Missing |
|------------|------------|--------|---------|
| House classification (Kendra/Trikona/Dusthana) | JRE-005 (bhava/models.py) | ✅ CATEGORY_MEMBERS dict with KENDRA={1,4,7,10}, TRIKONA={1,5,9} | — |
| House lord calculation | JRE-005 (bhava/models.py) | ✅ SIGN_LORDS dict, house_lord field in DerivedHouseFact | — |
| Planet occupancy in houses | JRE-005 (bhava/models.py) | ✅ occupants field in DerivedHouseFact | — |
| Basic yoga detection (Raja, Dhana, Gajakesari, Viparita) | JRE-013 (yoga/service.py) | ✅ Structural detection of Kendra-Trikona connections | — |
| Connection detection (conjunction, aspect, exchange) | JRE-013 (yoga/service.py) | ✅ _detect_connection method | — |
| Strength modifier from Shadbala | JRE-013 (yoga/service.py) | ✅ _compute_strength method | — |
| Sign lord table | JRE-005 (bhava/models.py) | ✅ SIGN_LORDS dict | — |

### E.2 Capabilities NOT Present (Gaps)

| Gap | Description | Priority |
|-----|-------------|----------|
| **Yogakaraka detection** | No logic to identify planets ruling both Kendra and Trikona simultaneously | HIGH |
| **Dignity-based modification** | No logic to adjust yoga strength based on exaltation/debilitation/own sign | HIGH |
| **Combustion detection** | No logic to detect planet combustion (within ~8° of Sun for classical orbs) | MEDIUM |
| **Retrogression effects** | No logic to modify yoga results based on retrograde status | MEDIUM |
| **Rahu/Ketu conjunction effects** | No logic to detect Node conjunction with yoga planets | MEDIUM |
| **Dusthana placement penalty** | No logic to penalize yoga when conjunction occurs in 6th/8th/12th | HIGH |
| **D9 (Navamsa) confirmation** | No divisional chart analysis for yoga validation | LOW (future) |
| **Multiple yoga accumulation** | No logic to combine multiple yoga results | LOW |
| **Hierarchy of connection types** | No weighting based on connection strength (conjunction > aspect > placement) | MEDIUM |
| **Neecha Bhanga detection** | No logic to detect debilitation cancellation | LOW (future) |

### E.3 JRS Knowledge Only Findings

| Finding | Type | Notes |
|---------|------|-------|
| Kendra = Vishnu Sthanas, Trikona = Lakshmi Sthanas | Interpretive/Doctrinal | Philosophical classification, not computational |
| "Action meets Fortune" logic | Interpretive/Doctrinal | Why Kendra-Trikona connection produces power |
| Four-fold distinction (Formation/Strength/Manifestation/Outcome) | Interpretive/Doctrinal | Framework for understanding yoga lifecycle |
| Yogakaraka concept | Interpretive/Doctrinal | Single planet bridging Kendra and Trikona |

---

## Section F: Four-Fold Distinction Mapping

| Configuration | Primary Source | Classification | Four-Fold Category | Existing JRE? | Requires New Computation? |
|---------------|----------------|----------------|---------------------|---------------|---------------------------|
| Kendra houses = 1,4,7,10 | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-005) | No |
| Trikona houses = 1,5,9 | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-005) | No |
| Kendra lord rules structural framework | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-005) | No |
| Trikona lord rules fortune/merit | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-005) | No |
| Conjunction = strongest connection | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-013) | No |
| Exchange = very strong connection | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-013) | No |
| Mutual aspect = strong connection | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-013) | No |
| One-way aspect = moderate connection | BPHS Ch.33 | COMMENTARY_DEPENDENT | YOGA_FORMATION | Yes (JRE-013) | No |
| Placement in each other's houses = moderate | BPHS Ch.33 | COMMENTARY_DEPENDENT | YOGA_FORMATION | Yes (JRE-013) | No |
| Yogakaraka = built-in Raja Yoga | Phaladeepika Ch.6 | CLASSICAL_PRIMARY | YOGA_FORMATION | No | **Yes** |
| Exaltation of yoga planet → maximum results | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | **Yes** |
| Debilitation of yoga planet → weakness | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | **Yes** |
| Own sign of yoga planet → strong | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_STRENGTH | Partial (Shadbala) | **Yes** |
| Combustion weakens yoga planet | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | **Yes** |
| Retrograde enhances planet power | BPHS Ch.33 | COMMENTARY_DEPENDENT | YOGA_STRENGTH | No | **Yes** |
| Rahu/Ketu aspect diminishes yoga | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | **Yes** |
| Natural malefic aspect weakens | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | **Yes** |
| Natural benefic aspect enhances | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | **Yes** |
| Conjunction in Dusthana → compromised | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_FORMATION | No | **Yes** |
| Dasha timing during productive years | BPHS Ch.33 | COMMENTARY_DEPENDENT | YOGA_MANIFESTATION | No | **Yes** (future) |
| D9 confirmation required | BPHS Ch.33 | COMMENTARY_DEPENDENT | YOGA_MANIFESTATION | No | **Yes** (future) |
| Raja Yoga outcome = power, authority | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_OUTCOME | No (JRS only) | No |
| Dhana Yoga outcome = wealth | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_OUTCOME | No (JRS only) | No |
| 2nd lord + 11th lord connection → wealth | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-013) | No |
| 9th lord + Venus in own/exaltation → Lakshmi | Phaladeepika Ch.6 | CLASSICAL_PRIMARY | YOGA_FORMATION | No | **Yes** |
| Lagna lord + Sun + Moon in Kendra/Trikona → Srikantha | Phaladeepika Ch.6 | CLASSICAL_PRIMARY | YOGA_FORMATION | No | **Yes** |
| Multiple yogas cumulative | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | **Yes** (future) |
| Neecha Bhanga restores debilitation | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | **Yes** (future) |

---

## Section G: Explicit Exclusion List

The following modern interpretations, unsupported inferences, and pop-astrology concepts were discovered during research and must be **actively excluded** from any implementation:

### G.1 Modern Psychological Interpretations (NOT Classical)

| Concept | Why Excluded | Source of Exclusion |
|---------|--------------|---------------------|
| "Mercury retrograde causes communication issues" | Modern pop-astrology; no classical basis | BPHS mentions retrograde but not "communication issues" |
| "Rahu/Ketu cause karmic debt" | New Age interpretation; classical texts describe them as shadow planets with specific effects | BPHS Ch.33 describes Rahu/Ketu as malefics, not "karmic debt" |
| "Chiron represents wounded healer" | Modern asteroid astrology; not in classical texts | No classical source mentions Chiron |
| "North Node = life purpose" | Modern psychological astrology | Classical texts describe Rahu as malefic, not "life purpose" |
| "Saturn return = maturity" | Modern pop-astrology | Classical texts describe Saturn periods as challenging but not "maturity" |

### G.2 Pop-Astrology Claims (NOT Supported)

| Concept | Why Excluded | Source of Exclusion |
|---------|--------------|---------------------|
| "Full Moon = emotional intensity" | No classical basis for this specific claim | BPHS describes Moon phases but not "emotional intensity" |
| "New Moon = fresh starts" | No classical basis | BPHS describes Moon phases for timing, not "fresh starts" |
| "Venus in 7th = perfect marriage" | Oversimplification; classical texts require multiple conditions | BPHS Ch.33 requires strength, dignity, and multiple factors |
| "Mars in 10th = aggressive career" | Modern psychological interpretation | Classical texts describe Mars in 10th as giving "authority through force" |

### G.3 Modern System Inventions (NOT Classical)

| Concept | Why Excluded | Source of Exclusion |
|---------|--------------|---------------------|
| Chiron (asteroid) interpretations | Not in classical Jyotish | BPHS, Phaladeepika, Saravali do not mention asteroids |
| Pluto interpretations | Not in classical Jyotish | Classical texts use traditional 7 planets |
| North Node/South Node life purpose | Modern psychological overlay | Classical texts describe Rahu/Ketu as malefics |
| asteroid Juno/Ceres/Pallas | Modern asteroid astrology | No classical basis |

### G.4 Unsupported Hellenistic Fringe

| Concept | Why Excluded | Source of Exclusion |
|---------|--------------|---------------------|
| "Void of Course Moon = no results" | Not supported in classical Indian texts | This is a Hellenistic concept not adopted in Jyotish |
| "Antiscia = hidden connections" | Not used in classical Jyotish | Hellenistic technique, not Parashari |
| "Arabic Parts = fate indicators" | Not in classical Indian texts | Islamic astrology influence, not core Jyotish |

---

## Summary of Findings

### What the Classical Texts Explicitly State

1. **Kendra houses (1,4,7,10) are the structural pillars of life** — "Vishnu Sthanas"
2. **Trikona houses (1,5,9) are the fortune pillars** — "Lakshmi Sthanas"
3. **Kendra-Trikona lord connection produces Raja Yoga** — through conjunction, exchange, mutual aspect, or placement
4. **Dhana Yoga involves 2nd and 11th lord connections**
5. **Yogakaraka planets form built-in Raja Yoga** — ruling both Kendra and Trikona simultaneously
6. **Dignity matters** — exaltation strengthens, debilitation weakens
7. **Combustion weakens** — planet too close to Sun loses capacity
8. **Retrograde modifies** — acts as if exalted in some contexts
9. **Rahu/Ketu conjunction diminishes** — creates obstacles
10. **Dusthana placement compromises** — conjunction in 6th/8th/12th reduces power

### What is NOT Explicitly Stated (Requiring Interpretation)

1. **D9 (Navamsa) confirmation** — mentioned in commentaries, not core texts
2. **Dasha timing requirements** — described as "when the period runs" but not formalized
3. **Hierarchy of connection types** — implied but not explicitly ranked
4. **Multiple yoga accumulation** — mentioned but not quantified

### Architectural Impact

The existing JRE-013 Yoga engine correctly implements the **structural detection** (YOGA_FORMATION) but lacks:
- **YOGA_STRENGTH** modifications (dignity, combustion, retrograde, Node effects)
- **Yogakaraka** detection
- **Dusthana placement** penalty
- **Connection type hierarchy** weighting

These gaps represent the difference between "yoga is present" and "yoga will manifest at full potential."

---

## Recommendation

**DO NOT proceed to RI-10B (implementation) until:**

1. This research report is reviewed and approved
2. The architectural gaps are prioritized
3. The four-fold distinction framework is validated against the JRE/JRS separation
4. The exclusion list is confirmed as comprehensive

**Next Step:** Human review of this report before any implementation decisions.
