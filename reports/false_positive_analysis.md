# False Positive Analysis — 24 Cases

**Phase F2: Diagnostic Report**

---

## Section 1: FP Distribution

**Total False Positives: 24**

| Category | Count | Percentage |
|----------|-------|------------|
| Domain Mismatch — Yoga fires for wrong domain | 24 | 100% |

### FP by Event Domain

| Domain | FP Count | Total Events | FP Rate |
|--------|----------|--------------|---------|
| HEALTH | 16 | 48 | 33.3% |
| CAREER | 7 | 93 | 7.5% |
| MARRIAGE | 1 | 3 | 33.3% |

### FP by Yoga Type

| Yoga | FP Count | Notes |
|------|----------|-------|
| Raja | 12 | Relevant domains: {'CAREER'} |
| Dhana | 6 | Relevant domains: {'CAREER', 'WEALTH'} |
| Budhaditya | 5 | Relevant domains: {'CAREER', 'EDUCATION'} |
| Sunapha | 4 | Relevant domains: {'CAREER', 'WEALTH'} |
| Gajakesari | 3 | Relevant domains: {'CAREER', 'WEALTH'} |
| Saraswati | 2 | Relevant domains: {'CAREER', 'EDUCATION'} |
| Neecha Bhanga | 2 | Relevant domains: {'CAREER'} |
| Amala | 1 | Relevant domains: {'CAREER', 'WEALTH'} |
| Dhudhara | 1 | Relevant domains: {'CAREER', 'WEALTH'} |
| Malavya | 1 | Relevant domains: {'CAREER', 'ARTISTIC'} |
| Anapha | 1 | Relevant domains: {'CAREER', 'WEALTH'} |

---

## Section 2: Per-FP Trace

### FP #1: Wolfgang Amadeus Mozart — MOZART_MARRIAGE_1782

- **Event Date:** 1782-08-04 | **Domain:** MARRIAGE
- **Active Dasha:** MOON/MERCURY/MERCURY
- **Activated Yoga(s):** Dhana
- **Top Yoga:** Raja (status: WEAKENED, dynamic: 0.4)
- **Expected Planets:** VENUS
- **All Yogas in Chart:** Raja(WEAKENED), Dhana(CANCELLED)
- **Why FP:** Yoga ['Dhana'] fires for MARRIAGE event but is not relevant to that domain

### FP #2: Nikola Tesla — TESLA_DEATH_1943

- **Event Date:** 1943-01-07 | **Domain:** HEALTH
- **Active Dasha:** SATURN/MERCURY/MARS
- **Activated Yoga(s):** Raja, Dhana, Budhaditya
- **Top Yoga:** Gajakesari (status: WEAKENED, dynamic: 1.0)
- **Expected Planets:** RAHU, SATURN
- **All Yogas in Chart:** Gajakesari(WEAKENED), Raja(WEAKENED), Dhana(CANCELLED), Budhaditya(FORMED)
- **Why FP:** Yoga ['Raja', 'Dhana', 'Budhaditya'] fires for HEALTH event but is not relevant to that domain

### FP #3: Isaac Newton — NEWTON_DEATH_1727

- **Event Date:** 1727-03-31 | **Domain:** HEALTH
- **Active Dasha:** SATURN/JUPITER/SATURN
- **Activated Yoga(s):** Raja, Saraswati
- **Top Yoga:** Raja (status: CANCELLED, dynamic: 1.0)
- **Expected Planets:** RAHU, SATURN
- **All Yogas in Chart:** Raja(CANCELLED), Budhaditya(FORMED), Saraswati(CANCELLED)
- **Why FP:** Yoga ['Raja', 'Saraswati'] fires for HEALTH event but is not relevant to that domain

### FP #4: Amelia Earhart — EARHART_DISAPPEARANCE_1937

- **Event Date:** 1937-07-02 | **Domain:** HEALTH
- **Active Dasha:** MARS/RAHU/VENUS
- **Activated Yoga(s):** Raja, Amala
- **Top Yoga:** Gajakesari (status: CANCELLED, dynamic: 0.4)
- **Expected Planets:** SATURN, RAHU
- **All Yogas in Chart:** Gajakesari(CANCELLED), Raja(CANCELLED), Dhana(WEAKENED), Budhaditya(WEAKENED), Amala(FORMED)
- **Why FP:** Yoga ['Raja', 'Amala'] fires for HEALTH event but is not relevant to that domain

### FP #5: Winston Churchill — CHURCHILL_DEATH_1965

- **Event Date:** 1965-01-24 | **Domain:** HEALTH
- **Active Dasha:** MERCURY/VENUS/VENUS
- **Activated Yoga(s):** Raja, Dhana
- **Top Yoga:** Anapha (status: FORMED, dynamic: 1.0)
- **Expected Planets:** RAHU, SATURN
- **All Yogas in Chart:** Raja(FORMED), Dhana(WEAKENED), Anapha(FORMED)
- **Why FP:** Yoga ['Raja', 'Dhana'] fires for HEALTH event but is not relevant to that domain

### FP #6: Nelson Mandela — MANDELA_DEATH_2013

- **Event Date:** 2013-12-05 | **Domain:** HEALTH
- **Active Dasha:** SATURN/MARS/MERCURY
- **Activated Yoga(s):** Sunapha, Dhudhara, Budhaditya
- **Top Yoga:** Sunapha (status: CANCELLED, dynamic: 1.0)
- **Expected Planets:** RAHU, SATURN
- **All Yogas in Chart:** Sunapha(CANCELLED), Anapha(WEAKENED), Dhudhara(CANCELLED), Budhaditya(FORMED)
- **Why FP:** Yoga ['Sunapha', 'Dhudhara', 'Budhaditya'] fires for HEALTH event but is not relevant to that domain

### FP #7: Mahatma Gandhi — GANDHI_SALT_1930

- **Event Date:** 1930-04-06 | **Domain:** CAREER
- **Active Dasha:** RAHU/VENUS/MOON
- **Activated Yoga(s):** Gajakesari, Raja
- **Top Yoga:** Gajakesari (status: CANCELLED, dynamic: 0.4)
- **Expected Planets:** MARS, JUPITER
- **All Yogas in Chart:** Gajakesari(CANCELLED), Raja(CANCELLED)
- **Why FP:** Yoga ['Gajakesari', 'Raja'] fires for CAREER event but is not relevant to that domain

### FP #8: Mahatma Gandhi — GANDHI_INDEPENDENCE_1947

- **Event Date:** 1947-08-15 | **Domain:** CAREER
- **Active Dasha:** JUPITER/MOON/JUPITER
- **Activated Yoga(s):** Gajakesari
- **Top Yoga:** Gajakesari (status: CANCELLED, dynamic: 0.4)
- **Expected Planets:** SUN, JUPITER
- **All Yogas in Chart:** Gajakesari(CANCELLED), Raja(CANCELLED)
- **Why FP:** Yoga ['Gajakesari'] fires for CAREER event but is not relevant to that domain

### FP #9: Mahatma Gandhi — GANDHI_ASSASSINATION_1948

- **Event Date:** 1948-01-30 | **Domain:** HEALTH
- **Active Dasha:** JUPITER/MOON/MERCURY
- **Activated Yoga(s):** Gajakesari, Raja
- **Top Yoga:** Gajakesari (status: CANCELLED, dynamic: 0.4)
- **Expected Planets:** RAHU, SATURN
- **All Yogas in Chart:** Gajakesari(CANCELLED), Raja(CANCELLED)
- **Why FP:** Yoga ['Gajakesari', 'Raja'] fires for HEALTH event but is not relevant to that domain

### FP #10: Gregor Mendel — MENDEL_DEATH_1884

- **Event Date:** 1884-01-06 | **Domain:** HEALTH
- **Active Dasha:** RAHU/MOON/RAHU
- **Activated Yoga(s):** Sunapha
- **Top Yoga:** Sunapha (status: CANCELLED, dynamic: 1.0)
- **Expected Planets:** RAHU, SATURN
- **All Yogas in Chart:** Dhana(FORMED), Sunapha(CANCELLED), Saraswati(FORMED), Amala(FORMED)
- **Why FP:** Yoga ['Sunapha'] fires for HEALTH event but is not relevant to that domain

### FP #11: Ada Lovelace — LOVELACE_DEATH_1852

- **Event Date:** 1852-11-27 | **Domain:** HEALTH
- **Active Dasha:** MOON/JUPITER/MOON
- **Activated Yoga(s):** Raja
- **Top Yoga:** Raja (status: FORMED, dynamic: 0.4)
- **Expected Planets:** RAHU, SATURN
- **All Yogas in Chart:** Raja(FORMED), Budhaditya(FORMED)
- **Why FP:** Yoga ['Raja'] fires for HEALTH event but is not relevant to that domain

### FP #12: Max Planck — PLANCK_DEATH_1947

- **Event Date:** 1947-10-04 | **Domain:** HEALTH
- **Active Dasha:** SATURN/KETU/VENUS
- **Activated Yoga(s):** Sunapha
- **Top Yoga:** Gajakesari (status: CANCELLED, dynamic: 1.0)
- **Expected Planets:** RAHU, SATURN
- **All Yogas in Chart:** Gajakesari(CANCELLED), Vipareeta Raja(FORMED), Dhana(WEAKENED), Ruchaka(FORMED), Sunapha(CANCELLED)
- **Why FP:** Yoga ['Sunapha'] fires for HEALTH event but is not relevant to that domain

### FP #13: Carl Jung — JUNG_COLLECTIVE_1916

- **Event Date:** 1916-11-01 | **Domain:** CAREER
- **Active Dasha:** MARS/RAHU/RAHU
- **Activated Yoga(s):** Sunapha
- **Top Yoga:** Gajakesari (status: CANCELLED, dynamic: 1.0)
- **Expected Planets:** JUPITER, MERCURY
- **All Yogas in Chart:** Gajakesari(CANCELLED), Raja(WEAKENED), Sunapha(CANCELLED), Amala(FORMED)
- **Why FP:** Yoga ['Sunapha'] fires for CAREER event but is not relevant to that domain

### FP #14: Carl Jung — JUNG_DEATH_1961

- **Event Date:** 1961-06-06 | **Domain:** HEALTH
- **Active Dasha:** SATURN/MERCURY/SUN
- **Activated Yoga(s):** Raja
- **Top Yoga:** Gajakesari (status: CANCELLED, dynamic: 1.0)
- **Expected Planets:** RAHU, SATURN
- **All Yogas in Chart:** Gajakesari(CANCELLED), Raja(WEAKENED), Sunapha(CANCELLED), Amala(FORMED)
- **Why FP:** Yoga ['Raja'] fires for HEALTH event but is not relevant to that domain

### FP #15: Vincent van Gogh — VANGOGH_DEATH_1890

- **Event Date:** 1890-07-29 | **Domain:** HEALTH
- **Active Dasha:** RAHU/RAHU/VENUS
- **Activated Yoga(s):** Malavya, Saraswati
- **Top Yoga:** Anapha (status: WEAKENED, dynamic: 1.0)
- **Expected Planets:** RAHU, SATURN
- **All Yogas in Chart:** Raja(FORMED), Hamsa(WEAKENED), Malavya(FORMED), Anapha(WEAKENED), Anapha(WEAKENED), Neecha Bhanga(WEAKENED), Saraswati(WEAKENED)
- **Why FP:** Yoga ['Malavya', 'Saraswati'] fires for HEALTH event but is not relevant to that domain

### FP #16: Hans Christian Andersen — ANDERSEN_DEATH_1875

- **Event Date:** 1875-08-04 | **Domain:** HEALTH
- **Active Dasha:** JUPITER/SATURN/SATURN
- **Activated Yoga(s):** Neecha Bhanga
- **Top Yoga:** Sunapha (status: WEAKENED, dynamic: 1.0)
- **Expected Planets:** RAHU, SATURN
- **All Yogas in Chart:** Sunapha(WEAKENED), Neecha Bhanga(CANCELLED)
- **Why FP:** Yoga ['Neecha Bhanga'] fires for HEALTH event but is not relevant to that domain

### FP #17: Anton Chekhov — CHEKHOV_CHERRY_1904

- **Event Date:** 1904-01-17 | **Domain:** CAREER
- **Active Dasha:** MARS/RAHU/MERCURY
- **Activated Yoga(s):** Raja, Budhaditya
- **Top Yoga:** Gajakesari (status: FORMED, dynamic: 1.0)
- **Expected Planets:** JUPITER, VENUS
- **All Yogas in Chart:** Gajakesari(FORMED), Raja(CANCELLED), Sunapha(FORMED), Budhaditya(CANCELLED)
- **Why FP:** Yoga ['Raja', 'Budhaditya'] fires for CAREER event but is not relevant to that domain

### FP #18: John D. Rockefeller — ROCKEFELLER_DEATH_1937

- **Event Date:** 1937-05-23 | **Domain:** HEALTH
- **Active Dasha:** SATURN/RAHU/MARS
- **Activated Yoga(s):** Raja
- **Top Yoga:** Raja (status: WEAKENED, dynamic: 0.4)
- **Expected Planets:** RAHU, SATURN
- **All Yogas in Chart:** Raja(WEAKENED)
- **Why FP:** Yoga ['Raja'] fires for HEALTH event but is not relevant to that domain

### FP #19: Andrew Carnegie — CARNEGIE_STEEL_1892

- **Event Date:** 1892-01-01 | **Domain:** CAREER
- **Active Dasha:** RAHU/SATURN/JUPITER
- **Activated Yoga(s):** Raja
- **Top Yoga:** Raja (status: CANCELLED, dynamic: 0.4)
- **Expected Planets:** SATURN, VENUS
- **All Yogas in Chart:** Raja(CANCELLED)
- **Why FP:** Yoga ['Raja'] fires for CAREER event but is not relevant to that domain

### FP #20: Andrew Carnegie — CARNEGIE_DEATH_1919

- **Event Date:** 1919-08-11 | **Domain:** HEALTH
- **Active Dasha:** SATURN/SATURN/VENUS
- **Activated Yoga(s):** Raja
- **Top Yoga:** Raja (status: CANCELLED, dynamic: 0.4)
- **Expected Planets:** RAHU, SATURN
- **All Yogas in Chart:** Raja(CANCELLED)
- **Why FP:** Yoga ['Raja'] fires for HEALTH event but is not relevant to that domain

### FP #21: Muhammad Ali — ALI_DEATH_2016

- **Event Date:** 2016-06-03 | **Domain:** HEALTH
- **Active Dasha:** SATURN/MERCURY/KETU
- **Activated Yoga(s):** Anapha, Neecha Bhanga, Budhaditya
- **Top Yoga:** Raja (status: CANCELLED, dynamic: 1.0)
- **Expected Planets:** RAHU, SATURN
- **All Yogas in Chart:** Raja(CANCELLED), Dhana(FORMED), Anapha(CANCELLED), Neecha Bhanga(CANCELLED), Budhaditya(FORMED)
- **Why FP:** Yoga ['Anapha', 'Neecha Bhanga', 'Budhaditya'] fires for HEALTH event but is not relevant to that domain

### FP #22: Jim Thorpe — THORPE_OLYMPICS_1912

- **Event Date:** 1912-07-13 | **Domain:** CAREER
- **Active Dasha:** MOON/MOON/RAHU
- **Activated Yoga(s):** Dhana
- **Top Yoga:** Dhana (status: CANCELLED, dynamic: None)
- **Expected Planets:** MARS, JUPITER
- **All Yogas in Chart:** Dhana(CANCELLED), Budhaditya(WEAKENED)
- **Why FP:** Yoga ['Dhana'] fires for CAREER event but is not relevant to that domain

### FP #23: Jim Thorpe — THORPE_NFL_1920

- **Event Date:** 1920-08-20 | **Domain:** CAREER
- **Active Dasha:** MOON/VENUS/MOON
- **Activated Yoga(s):** Dhana
- **Top Yoga:** Dhana (status: CANCELLED, dynamic: None)
- **Expected Planets:** MARS, SATURN
- **All Yogas in Chart:** Dhana(CANCELLED), Budhaditya(WEAKENED)
- **Why FP:** Yoga ['Dhana'] fires for CAREER event but is not relevant to that domain

### FP #24: Jim Thorpe — THORPE_DEATH_1953

- **Event Date:** 1953-03-28 | **Domain:** HEALTH
- **Active Dasha:** JUPITER/MERCURY/MARS
- **Activated Yoga(s):** Dhana, Budhaditya
- **Top Yoga:** Dhana (status: CANCELLED, dynamic: None)
- **Expected Planets:** RAHU, SATURN
- **All Yogas in Chart:** Dhana(CANCELLED), Budhaditya(WEAKENED)
- **Why FP:** Yoga ['Dhana', 'Budhaditya'] fires for HEALTH event but is not relevant to that domain

---

## Section 3: Systemic Patterns

### Pattern 1: HEALTH Domain FP Dominance
- **16/24 FPs** are HEALTH events
- Most death/health events have yogas activated that are career-relevant (e.g., Gajakesari, Raja) but not health-relevant
- The pipeline correctly activates yogas during the Dasha, but the yoga's domain relevance doesn't match HEALTH
- **Root cause:** Career yogas (Raja, Gajakesari) naturally fire during any event when the Dasha lord matches. For HEALTH events, the expected pattern is that NO career yoga should be active — but the Dasha alignment is coincidental.

### Pattern 2: Overly Broad Yoga Domain Relevance
- Many yogas (Gajakesari, Raja, Dhana) are classified as relevant to CAREER, which is overly broad
- This causes FPs when these yogas activate for CAREER events where the specific subject experienced failure or death
- **Root cause:** The `_DOMAIN_RELEVANCE` mapping and yoga outcome domain definitions are too permissive

### Pattern 3: Dasha Coincidence
- In 24 FPs, the Dasha lord happens to match a yoga's involved planet, triggering activation regardless of the event's actual nature
- This is expected behavior — the Dasha system fires based on planetary periods, not event outcomes
