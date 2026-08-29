# Hit Rate Plateau Diagnosis — Phase E6f

**Objective:** Trace why the hit rate is stuck at 13% across all 15 events.

---

## Section 1: Failure Mode Distribution

**Total events:** 15

| Category | Count | Percentage | Description |
|----------|-------|------------|-------------|
| HIT | 2 | 13% | HIT (relevant yoga activated) |
| A | 0 | 0% | A — No Yoga Detected |
| B | 0 | 0% | B — Yoga Detected but All Cancelled |
| C | 7 | 47% | C — Yoga Formed but Dasha Mismatch |
| D | 0 | 0% | D — Yoga Formed but Strength Too Low |
| E | 0 | 0% | E — Transit Layer Inactive |
| F | 6 | 40% | F — Domain/Planet Alignment Issue |

---

## Section 2: Per-Event Trace

### Albert Einstein

#### EINSTEIN_NOBEL_1921 — 1921-11-09 (CAREER) ❌
**Description:** Awarded the Nobel Prize in Physics for the photoelectric effect
**Active Dasha:** MARS / VENUS / SATURN
**Expected Planets:** SUN, JUPITER

**Failure Category:** F — Malavya ACTIVATED but yoga_domain=RELATIONSHIP_HARMONY is not in relevant_domains={'CAREER_PROMINENCE', 'GENERAL_IMPROVEMENT'} AND involved_planets=['VENUS'] don't match expected_planets=['SUN', 'JUPITER']

| Yoga | Status | Involved | Domain | Dynamic Str | Chain Impact | Dasha Mult | Activation |
|------|--------|----------|--------|-------------|--------------|------------|------------|
| Vipareeta Raja | FORMED | — | CAREER_PROMINENCE | — | — | 0.40 | DORMANT |
| Malavya | FORMED | VENUS | RELATIONSHIP_HARMONY | 1.0000 | 1.0000 | 1.25 | ACTIVATED (Dasha AD: VENUS) |

#### EINSTEIN_GENERAL_RELATIVITY_1915 — 1915-11-25 (CAREER) ❌
**Description:** Presented the general theory of relativity to the Prussian Academy of Sciences
**Active Dasha:** MOON / SUN / SATURN
**Expected Planets:** JUPITER, SATURN

**Failure Category:** C — Vipareeta Raja formed, domain=CAREER_PROMINENCE is relevant, but Dasha lords [MOON/SUN/SATURN] don't match involved_planets=[]

| Yoga | Status | Involved | Domain | Dynamic Str | Chain Impact | Dasha Mult | Activation |
|------|--------|----------|--------|-------------|--------------|------------|------------|
| Vipareeta Raja | FORMED | — | CAREER_PROMINENCE | — | — | 0.40 | DORMANT |
| Malavya | FORMED | VENUS | RELATIONSHIP_HARMONY | 1.0000 | 1.0000 | 0.40 | DORMANT |

#### EINSTEIN_VISAPR_1905 — 1905-06-01 (CAREER) ❌
**Description:** Annus Mirabilis — published four groundbreaking papers including special relativity and E=mc²
**Active Dasha:** SUN / VENUS / MOON
**Expected Planets:** MERCURY, SUN, JUPITER

**Failure Category:** F — Malavya ACTIVATED but yoga_domain=RELATIONSHIP_HARMONY is not in relevant_domains={'CAREER_PROMINENCE', 'GENERAL_IMPROVEMENT'} AND involved_planets=['VENUS'] don't match expected_planets=['MERCURY', 'SUN', 'JUPITER']

| Yoga | Status | Involved | Domain | Dynamic Str | Chain Impact | Dasha Mult | Activation |
|------|--------|----------|--------|-------------|--------------|------------|------------|
| Vipareeta Raja | FORMED | — | CAREER_PROMINENCE | — | — | 0.40 | DORMANT |
| Malavya | FORMED | VENUS | RELATIONSHIP_HARMONY | 1.0000 | 1.0000 | 1.25 | ACTIVATED (Dasha AD: VENUS) |


### Marie Curie

#### CURIE_NOBEL_1903 — 1903-12-10 (CAREER) ✅
**Description:** Awarded the Nobel Prize in Physics jointly with Pierre Curie and Henri Becquerel
**Active Dasha:** MOON / JUPITER / JUPITER
**Expected Planets:** SUN, JUPITER

| Yoga | Status | Involved | Domain | Dynamic Str | Chain Impact | Dasha Mult | Activation |
|------|--------|----------|--------|-------------|--------------|------------|------------|
| Gajakesari | WEAKENED | JUPITER, MOON | GENERAL_IMPROVEMENT | 1.0000 | 130.6527 | 1.50 | ACTIVATED (Dasha MD: MOON) |
| Raja | CANCELLED | MERCURY, VENUS | CAREER_PROMINENCE | 0.4000 | -89.0761 | 0.40 | DORMANT |

#### CURIE_NOBEL_1911 — 1911-12-10 (CAREER) ❌
**Description:** Awarded the Nobel Prize in Chemistry for discovery of radium and polonium
**Active Dasha:** MARS / RAHU / VENUS
**Expected Planets:** SUN, JUPITER

**Failure Category:** C — Gajakesari formed with matching planets ['JUPITER'] but Dasha lords [MARS/RAHU/VENUS] don't match involved_planets=['JUPITER', 'MOON']

| Yoga | Status | Involved | Domain | Dynamic Str | Chain Impact | Dasha Mult | Activation |
|------|--------|----------|--------|-------------|--------------|------------|------------|
| Gajakesari | WEAKENED | JUPITER, MOON | GENERAL_IMPROVEMENT | 1.0000 | 130.6527 | 0.40 | DORMANT |
| Raja | CANCELLED | MERCURY, VENUS | CAREER_PROMINENCE | 0.4000 | -89.0761 | 1.10 | ACTIVATED (Dasha PD: VENUS) |

#### CURIE_DEATH_1934 — 1934-07-04 (HEALTH) ❌
**Description:** Died of aplastic anemia caused by prolonged radiation exposure
**Active Dasha:** RAHU / MOON / VENUS
**Expected Planets:** SATURN, RAHU

**Failure Category:** C — Gajakesari ACTIVATED with Dasha AD: MOON but involved_planets=['JUPITER', 'MOON'] don't overlap expected_planets=['SATURN', 'RAHU']

| Yoga | Status | Involved | Domain | Dynamic Str | Chain Impact | Dasha Mult | Activation |
|------|--------|----------|--------|-------------|--------------|------------|------------|
| Gajakesari | WEAKENED | JUPITER, MOON | GENERAL_IMPROVEMENT | 1.0000 | 130.6527 | 1.25 | ACTIVATED (Dasha AD: MOON) |
| Raja | CANCELLED | MERCURY, VENUS | CAREER_PROMINENCE | 0.4000 | -89.0761 | 1.10 | ACTIVATED (Dasha PD: VENUS) |


### Wolfgang Amadeus Mozart

#### MOZART_MARRIAGE_1782 — 1782-08-04 (MARRIAGE) ❌
**Description:** Married Constanze Weber in St. Stephen's Cathedral, Vienna
**Active Dasha:** MOON / MERCURY / MERCURY
**Expected Planets:** VENUS

**Failure Category:** F — Raja formed but yoga_domain=CAREER_PROMINENCE not in relevant_domains={'RELATIONSHIP_HARMONY', 'GENERAL_IMPROVEMENT'}, Dasha [MOON/MERCURY/MERCURY] doesn't match involved_planets=['SATURN', 'SUN']

| Yoga | Status | Involved | Domain | Dynamic Str | Chain Impact | Dasha Mult | Activation |
|------|--------|----------|--------|-------------|--------------|------------|------------|
| Raja | WEAKENED | SATURN, SUN | CAREER_PROMINENCE | 0.4000 | -10.3713 | 0.40 | DORMANT |
| Dhana | CANCELLED | MERCURY, MERCURY | WEALTH_ACCUMULATION | — | — | 1.25 | ACTIVATED (Dasha AD: MERCURY) |

#### MOZART_DON_GIOVANNI_1787 — 1787-10-29 (CAREER) ❌
**Description:** Premiere of Don Giovanni in Prague — considered his career peak opera
**Active Dasha:** MARS / RAHU / VENUS
**Expected Planets:** MERCURY, JUPITER

**Failure Category:** C — Raja formed, domain=CAREER_PROMINENCE is relevant, but Dasha lords [MARS/RAHU/VENUS] don't match involved_planets=['SATURN', 'SUN']

| Yoga | Status | Involved | Domain | Dynamic Str | Chain Impact | Dasha Mult | Activation |
|------|--------|----------|--------|-------------|--------------|------------|------------|
| Raja | WEAKENED | SATURN, SUN | CAREER_PROMINENCE | 0.4000 | -10.3713 | 0.40 | DORMANT |
| Dhana | CANCELLED | MERCURY, MERCURY | WEALTH_ACCUMULATION | — | — | 0.40 | DORMANT |

#### MOZART_DEATH_1791 — 1791-12-05 (HEALTH) ❌
**Description:** Died at age 35 under mysterious circumstances; Requiem left unfinished
**Active Dasha:** MARS / VENUS / MARS
**Expected Planets:** SATURN, RAHU

**Failure Category:** C — Raja formed with matching planets ['SATURN'] but Dasha lords [MARS/VENUS/MARS] don't match involved_planets=['SATURN', 'SUN']

| Yoga | Status | Involved | Domain | Dynamic Str | Chain Impact | Dasha Mult | Activation |
|------|--------|----------|--------|-------------|--------------|------------|------------|
| Raja | WEAKENED | SATURN, SUN | CAREER_PROMINENCE | 0.4000 | -10.3713 | 0.40 | DORMANT |
| Dhana | CANCELLED | MERCURY, MERCURY | WEALTH_ACCUMULATION | — | — | 0.40 | DORMANT |


### Nikola Tesla

#### TESLA_US_MOVE_1884 — 1884-06-06 (MIGRATION) ❌
**Description:** Arrived in New York City with four cents, a prayer, and a letter of recommendation to Edison
**Active Dasha:** SUN / SATURN / SATURN
**Expected Planets:** RAHU

**Failure Category:** C — Gajakesari formed, domain=GENERAL_IMPROVEMENT is relevant, but Dasha lords [SUN/SATURN/SATURN] don't match involved_planets=['JUPITER', 'MOON']

| Yoga | Status | Involved | Domain | Dynamic Str | Chain Impact | Dasha Mult | Activation |
|------|--------|----------|--------|-------------|--------------|------------|------------|
| Gajakesari | WEAKENED | JUPITER, MOON | GENERAL_IMPROVEMENT | 1.0000 | 181.0124 | 0.40 | DORMANT |
| Raja | WEAKENED | MOON, MARS | CAREER_PROMINENCE | 0.4000 | -117.4160 | 0.40 | DORMANT |
| Dhana | CANCELLED | VENUS, SATURN | WEALTH_ACCUMULATION | — | — | 1.25 | ACTIVATED (Dasha AD: SATURN) |

#### TESLA_LAB_FIRE_1895 — 1895-03-13 (HEALTH) ✅
**Description:** Laboratory fire destroyed years of research notes, models, and financial backing
**Active Dasha:** MOON / KETU / SATURN
**Expected Planets:** SATURN, MARS

| Yoga | Status | Involved | Domain | Dynamic Str | Chain Impact | Dasha Mult | Activation |
|------|--------|----------|--------|-------------|--------------|------------|------------|
| Gajakesari | WEAKENED | JUPITER, MOON | GENERAL_IMPROVEMENT | 1.0000 | 181.0124 | 1.50 | ACTIVATED (Dasha MD: MOON) |
| Raja | WEAKENED | MOON, MARS | CAREER_PROMINENCE | 0.4000 | -117.4160 | 1.50 | ACTIVATED (Dasha MD: MOON) |
| Dhana | CANCELLED | VENUS, SATURN | WEALTH_ACCUMULATION | — | — | 1.10 | ACTIVATED (Dasha PD: SATURN) |

#### TESLA_DEATH_1943 — 1943-01-07 (HEALTH) ❌
**Description:** Died alone in Room 3327 of the New Yorker Hotel, age 86
**Active Dasha:** SATURN / MERCURY / MARS
**Expected Planets:** SATURN, RAHU

**Failure Category:** F — Raja ACTIVATED but yoga_domain=CAREER_PROMINENCE is not in relevant_domains={'GENERAL_IMPROVEMENT'} AND involved_planets=['MOON', 'MARS'] don't match expected_planets=['SATURN', 'RAHU']

| Yoga | Status | Involved | Domain | Dynamic Str | Chain Impact | Dasha Mult | Activation |
|------|--------|----------|--------|-------------|--------------|------------|------------|
| Gajakesari | WEAKENED | JUPITER, MOON | GENERAL_IMPROVEMENT | 1.0000 | 181.0124 | 0.40 | DORMANT |
| Raja | WEAKENED | MOON, MARS | CAREER_PROMINENCE | 0.4000 | -117.4160 | 1.10 | ACTIVATED (Dasha PD: MARS) |
| Dhana | CANCELLED | VENUS, SATURN | WEALTH_ACCUMULATION | — | — | 1.50 | ACTIVATED (Dasha MD: SATURN) |


### Indira Gandhi

#### GANDHI_PM_1966 — 1966-01-24 (CAREER) ❌
**Description:** Became the first (and to date only) female Prime Minister of India
**Active Dasha:** RAHU / RAHU / SUN
**Expected Planets:** JUPITER, SATURN

**Failure Category:** F — Sunapha ACTIVATED but yoga_domain=WEALTH_ACCUMULATION is not in relevant_domains={'CAREER_PROMINENCE', 'GENERAL_IMPROVEMENT'} AND involved_planets=['MOON', 'RAHU'] don't match expected_planets=['JUPITER', 'SATURN']

| Yoga | Status | Involved | Domain | Dynamic Str | Chain Impact | Dasha Mult | Activation |
|------|--------|----------|--------|-------------|--------------|------------|------------|
| Sunapha | CANCELLED | MOON, VENUS | WEALTH_ACCUMULATION | 1.0000 | -42.7013 | 0.40 | DORMANT |
| Sunapha | WEAKENED | MOON, RAHU | WEALTH_ACCUMULATION | 1.0000 | -40.9027 | 1.50 | ACTIVATED (Dasha MD: RAHU) |

#### GANDHI_WAR_1971 — 1971-12-16 (CAREER) ❌
**Description:** Led India to decisive victory in the Indo-Pakistani War of 1971; creation of Bangladesh
**Active Dasha:** RAHU / MERCURY / MERCURY
**Expected Planets:** MARS, SATURN

**Failure Category:** F — Sunapha ACTIVATED but yoga_domain=WEALTH_ACCUMULATION is not in relevant_domains={'CAREER_PROMINENCE', 'GENERAL_IMPROVEMENT'} AND involved_planets=['MOON', 'RAHU'] don't match expected_planets=['MARS', 'SATURN']

| Yoga | Status | Involved | Domain | Dynamic Str | Chain Impact | Dasha Mult | Activation |
|------|--------|----------|--------|-------------|--------------|------------|------------|
| Sunapha | CANCELLED | MOON, VENUS | WEALTH_ACCUMULATION | 1.0000 | -42.7013 | 0.40 | DORMANT |
| Sunapha | WEAKENED | MOON, RAHU | WEALTH_ACCUMULATION | 1.0000 | -40.9027 | 1.50 | ACTIVATED (Dasha MD: RAHU) |

#### GANDHI_ASSASSINATION_1984 — 1984-10-31 (HEALTH) ❌
**Description:** Assassinated by her Sikh bodyguards in New Delhi following Operation Blue Star
**Active Dasha:** JUPITER / SATURN / KETU
**Expected Planets:** SATURN, RAHU

**Failure Category:** C — Sunapha formed with matching planets ['RAHU'] but Dasha lords [JUPITER/SATURN/KETU] don't match involved_planets=['MOON', 'RAHU']

| Yoga | Status | Involved | Domain | Dynamic Str | Chain Impact | Dasha Mult | Activation |
|------|--------|----------|--------|-------------|--------------|------------|------------|
| Sunapha | CANCELLED | MOON, VENUS | WEALTH_ACCUMULATION | 1.0000 | -42.7013 | 0.40 | DORMANT |
| Sunapha | WEAKENED | MOON, RAHU | WEALTH_ACCUMULATION | 1.0000 | -40.9027 | 0.40 | DORMANT |


---

## Section 3: Dominant Bottleneck Identification

**Dominant failure category:** C — 7/15 events (47%)

**Interpretation:** C — Yoga Formed but Dasha Mismatch

### Dasha Mismatch Analysis (Category C)

For each Category C event, the chain of failure is:

- **EINSTEIN_GENERAL_RELATIVITY_1915** (Albert Einstein):
  - Yoga involved_planets: ['VENUS']
  - Fixture expected_planets: ['JUPITER', 'SATURN']
  - Overlap: NONE
  - Dasha lords: MOON/SUN/SATURN
  - Dasha lords in involved_planets: NONE

- **CURIE_NOBEL_1911** (Marie Curie):
  - Yoga involved_planets: ['JUPITER', 'MOON']
  - Fixture expected_planets: ['JUPITER', 'SUN']
  - Overlap: ['JUPITER']
  - Dasha lords: MARS/RAHU/VENUS
  - Dasha lords in involved_planets: NONE

- **CURIE_DEATH_1934** (Marie Curie):
  - Yoga involved_planets: ['JUPITER', 'MOON']
  - Fixture expected_planets: ['RAHU', 'SATURN']
  - Overlap: NONE
  - Dasha lords: RAHU/MOON/VENUS
  - Dasha lords in involved_planets: ['MOON']

- **MOZART_DON_GIOVANNI_1787** (Wolfgang Amadeus Mozart):
  - Yoga involved_planets: ['SATURN', 'SUN']
  - Fixture expected_planets: ['JUPITER', 'MERCURY']
  - Overlap: NONE
  - Dasha lords: MARS/RAHU/VENUS
  - Dasha lords in involved_planets: NONE

- **MOZART_DEATH_1791** (Wolfgang Amadeus Mozart):
  - Yoga involved_planets: ['SATURN', 'SUN']
  - Fixture expected_planets: ['RAHU', 'SATURN']
  - Overlap: ['SATURN']
  - Dasha lords: MARS/VENUS/MARS
  - Dasha lords in involved_planets: NONE

- **TESLA_US_MOVE_1884** (Nikola Tesla):
  - Yoga involved_planets: ['JUPITER', 'MARS', 'MOON']
  - Fixture expected_planets: ['RAHU']
  - Overlap: NONE
  - Dasha lords: SUN/SATURN/SATURN
  - Dasha lords in involved_planets: NONE

- **GANDHI_ASSASSINATION_1984** (Indira Gandhi):
  - Yoga involved_planets: ['MOON', 'RAHU']
  - Fixture expected_planets: ['RAHU', 'SATURN']
  - Overlap: ['RAHU']
  - Dasha lords: JUPITER/SATURN/KETU
  - Dasha lords in involved_planets: NONE

### Domain/Planet Alignment Analysis (Category F)

- **EINSTEIN_NOBEL_1921** (Albert Einstein): Malavya ACTIVATED but yoga_domain=RELATIONSHIP_HARMONY is not in relevant_domains={'CAREER_PROMINENCE', 'GENERAL_IMPROVEMENT'} AND involved_planets=['VENUS'] don't match expected_planets=['SUN', 'JUPITER']
- **EINSTEIN_VISAPR_1905** (Albert Einstein): Malavya ACTIVATED but yoga_domain=RELATIONSHIP_HARMONY is not in relevant_domains={'CAREER_PROMINENCE', 'GENERAL_IMPROVEMENT'} AND involved_planets=['VENUS'] don't match expected_planets=['MERCURY', 'SUN', 'JUPITER']
- **MOZART_MARRIAGE_1782** (Wolfgang Amadeus Mozart): Raja formed but yoga_domain=CAREER_PROMINENCE not in relevant_domains={'RELATIONSHIP_HARMONY', 'GENERAL_IMPROVEMENT'}, Dasha [MOON/MERCURY/MERCURY] doesn't match involved_planets=['SATURN', 'SUN']
- **TESLA_DEATH_1943** (Nikola Tesla): Raja ACTIVATED but yoga_domain=CAREER_PROMINENCE is not in relevant_domains={'GENERAL_IMPROVEMENT'} AND involved_planets=['MOON', 'MARS'] don't match expected_planets=['SATURN', 'RAHU']
- **GANDHI_PM_1966** (Indira Gandhi): Sunapha ACTIVATED but yoga_domain=WEALTH_ACCUMULATION is not in relevant_domains={'CAREER_PROMINENCE', 'GENERAL_IMPROVEMENT'} AND involved_planets=['MOON', 'RAHU'] don't match expected_planets=['JUPITER', 'SATURN']
- **GANDHI_WAR_1971** (Indira Gandhi): Sunapha ACTIVATED but yoga_domain=WEALTH_ACCUMULATION is not in relevant_domains={'CAREER_PROMINENCE', 'GENERAL_IMPROVEMENT'} AND involved_planets=['MOON', 'RAHU'] don't match expected_planets=['MARS', 'SATURN']

---

## Section 4: Recommended Next Actions

### Fix 1: Bridge Dasha-Planet Mismatch (Category C — 7/15 events)

The activation check requires the Dasha lord to be one of the yoga's *involved_planets*. But the fixture's expected_planets may reference planets that are relevant to the event's domain but are NOT the primary yoga participants.

**Surgical fix:** In the activation check, also consider planets that are:
- Functional lords of houses the yoga affects (e.g., 10th lord for career)
- Dispositor chain members of the yoga's primary planet
- Nakshatra lords of the yoga's primary planet

### Fix 2: Activate Transit Layer (Layer 3)

All transit multipliers are 1.0 (inactive). Adding ashtakavarga_scores and transit_houses to jre_facts would differentiate dynamic strengths and potentially activate yogas that are currently DORMANT.

### Fix 3: Expand Yoga Detection Scope

Some events have NO yogas detected (Category A) or only yogas with wrong domains (Category F). Consider adding detection for:
- Career-specific yogas (D10-based)
- Event-specific yogas (e.g., Mars-Saturn for accidents)
- Neecha Bhanga for debilitated planets in key houses

---

## Methodology

This diagnostic traces each of 15 events through the full 5-layer JRE pipeline, comparing the engine's output against the fixture's expected_planets. No calibration or tuning was applied.

### Failure Mode Categories:
- **A — No Yoga Detected:** Engine didn't detect any yoga for this event
- **B — Not Formed:** Yoga exists but formation conditions failed (cancellation)
- **C — Dasha Mismatch:** Yoga is strong but Dasha lord doesn't match participants
- **D — Strength Too Low:** Dynamic strength below activation threshold
- **E — Transit Inactive:** Layer 3 transit multiplier not contributing
- **F — Alignment Issue:** Fixture expected_planets doesn't match engine's yoga tracking