# False Negative Analysis — 41 Cases

**Phase F2: Diagnostic Report**

---

## Section 1: FN Distribution

**Total False Negatives: 41**

| Category | Count | Percentage |
|----------|-------|------------|
| Formed but Not Activated (Dasha mismatch) | 28 | 68% |
| No Yogas Formed (coverage gap) | 9 | 22% |
| All Yogas Cancelled (modifier over-cancellation) | 4 | 10% |

### FN by Event Domain

| Domain | FN Count | Total Events | FN Rate |
|--------|----------|--------------|---------|
| CAREER | 28 | 93 | 30.1% |
| HEALTH | 13 | 48 | 27.1% |

### FN by Subject (Worst Performers)

| Subject | FN Count | Events | All FN? |
|---------|----------|--------|---------|
| Charles de Gaulle | 3 | 3 | ⚠️ YES |
| Rosalind Franklin | 3 | 3 | ⚠️ YES |
| Ludwig van Beethoven | 3 | 3 | ⚠️ YES |
| Pablo Picasso | 3 | 3 | ⚠️ YES |
| Leo Tolstoy | 3 | 3 | ⚠️ YES |
| Henry Ford | 3 | 3 | ⚠️ YES |
| Wolfgang Amadeus Mozart | 2 | 3 |  |
| Steve Jobs | 2 | 3 |  |
| John F. Kennedy | 2 | 3 |  |
| J.P. Morgan | 2 | 3 |  |
| Jackie Robinson | 2 | 3 |  |
| Albert Einstein | 1 | 3 |  |
| Indira Gandhi | 1 | 3 |  |
| Isaac Newton | 1 | 3 |  |
| Winston Churchill | 1 | 3 |  |

---

## Section 2: Per-FN Trace

### FN #1: Albert Einstein — EINSTEIN_GENERAL_RELATIVITY_1915

- **Event Date:** 1915-11-25 | **Domain:** CAREER
- **Active Dasha:** MOON/SUN/SATURN
- **All Yogas:** Vipareeta Raja(FORMED), Malavya(FORMED)
- **Expected Planets:** JUPITER, SATURN
- **Why FN:** Yogas formed (['Vipareeta Raja', 'Malavya']) but Dasha didn't activate them (MD=MOON)

### FN #2: Wolfgang Amadeus Mozart — MOZART_DON_GIOVANNI_1787

- **Event Date:** 1787-10-29 | **Domain:** CAREER
- **Active Dasha:** MARS/RAHU/VENUS
- **All Yogas:** Raja(WEAKENED), Dhana(CANCELLED)
- **Expected Planets:** JUPITER, MERCURY
- **Why FN:** Yogas formed (['Raja']) but not activated; others cancelled (['Dhana'])

### FN #3: Wolfgang Amadeus Mozart — MOZART_DEATH_1791

- **Event Date:** 1791-12-05 | **Domain:** HEALTH
- **Active Dasha:** MARS/VENUS/MARS
- **All Yogas:** Raja(WEAKENED), Dhana(CANCELLED)
- **Expected Planets:** RAHU, SATURN
- **Why FN:** Yogas formed (['Raja']) but not activated; others cancelled (['Dhana'])

### FN #4: Indira Gandhi — GANDHI_ASSASSINATION_1984

- **Event Date:** 1984-10-31 | **Domain:** HEALTH
- **Active Dasha:** JUPITER/SATURN/KETU
- **All Yogas:** Sunapha(WEAKENED), Sunapha(WEAKENED), Budhaditya(FORMED)
- **Expected Planets:** RAHU, SATURN
- **Why FN:** Yogas formed (['Sunapha', 'Sunapha', 'Budhaditya']) but Dasha didn't activate them (MD=JUPITER)

### FN #5: Isaac Newton — NEWTON_LUCASIAN_1669

- **Event Date:** 1669-10-29 | **Domain:** CAREER
- **Active Dasha:** MARS/RAHU/SATURN
- **All Yogas:** Raja(CANCELLED), Budhaditya(FORMED), Saraswati(CANCELLED)
- **Expected Planets:** JUPITER, SATURN
- **Why FN:** Yogas formed (['Budhaditya']) but not activated; others cancelled (['Raja', 'Saraswati'])

### FN #6: Steve Jobs — JOBS_APPLE_1976

- **Event Date:** 1976-04-01 | **Domain:** CAREER
- **Active Dasha:** VENUS/SATURN/VENUS
- **All Yogas:** Gajakesari(WEAKENED), Vipareeta Raja(FORMED), Dhana(WEAKENED), Anapha(WEAKENED)
- **Expected Planets:** JUPITER, MERCURY
- **Why FN:** Yogas formed (['Gajakesari', 'Vipareeta Raja', 'Dhana', 'Anapha']) but Dasha didn't activate them (MD=VENUS)

### FN #7: Steve Jobs — JOBS_OUSTED_1985

- **Event Date:** 1985-09-17 | **Domain:** CAREER
- **Active Dasha:** SUN/SATURN/RAHU
- **All Yogas:** Gajakesari(WEAKENED), Vipareeta Raja(FORMED), Dhana(WEAKENED), Anapha(WEAKENED)
- **Expected Planets:** RAHU, SATURN
- **Why FN:** Yogas formed (['Gajakesari', 'Vipareeta Raja', 'Dhana', 'Anapha']) but Dasha didn't activate them (MD=SUN)

### FN #8: Winston Churchill — CHURCHILL_PM_1940

- **Event Date:** 1940-05-10 | **Domain:** CAREER
- **Active Dasha:** JUPITER/RAHU/JUPITER
- **All Yogas:** Raja(FORMED), Dhana(WEAKENED), Anapha(FORMED)
- **Expected Planets:** JUPITER, SATURN
- **Why FN:** Yogas formed (['Raja', 'Dhana', 'Anapha']) but Dasha didn't activate them (MD=JUPITER)

### FN #9: Nelson Mandela — MANDELA_PRESIDENT_1994

- **Event Date:** 1994-05-10 | **Domain:** CAREER
- **Active Dasha:** JUPITER/VENUS/SATURN
- **All Yogas:** Sunapha(CANCELLED), Anapha(WEAKENED), Dhudhara(CANCELLED), Budhaditya(FORMED)
- **Expected Planets:** SUN, JUPITER
- **Why FN:** Yogas formed (['Anapha', 'Budhaditya']) but not activated; others cancelled (['Sunapha', 'Dhudhara'])

### FN #10: John F. Kennedy — JFK_CUBAN_MISSILE_1962

- **Event Date:** 1962-10-22 | **Domain:** CAREER
- **Active Dasha:** RAHU/MERCURY/MERCURY
- **All Yogas:** Gajakesari(WEAKENED), Raja(FORMED), Sunapha(CANCELLED)
- **Expected Planets:** MARS, SATURN
- **Why FN:** Yogas formed (['Gajakesari', 'Raja']) but not activated; others cancelled (['Sunapha'])

### FN #11: John F. Kennedy — JFK_ASSASSINATION_1963

- **Event Date:** 1963-11-22 | **Domain:** HEALTH
- **Active Dasha:** RAHU/MERCURY/MARS
- **All Yogas:** Gajakesari(WEAKENED), Raja(FORMED), Sunapha(CANCELLED)
- **Expected Planets:** RAHU, SATURN
- **Why FN:** Yogas formed (['Gajakesari', 'Raja']) but not activated; others cancelled (['Sunapha'])

### FN #12: Margaret Thatcher — THATCHER_FALKLANDS_1982

- **Event Date:** 1982-06-14 | **Domain:** CAREER
- **Active Dasha:** JUPITER/MERCURY/MERCURY
- **All Yogas:** Dhana(CANCELLED), Sasa(FORMED), Sunapha(WEAKENED), Anapha(WEAKENED), Dhudhara(WEAKENED)
- **Expected Planets:** MARS, SATURN
- **Why FN:** Yogas formed (['Sasa', 'Sunapha', 'Anapha', 'Dhudhara']) but not activated; others cancelled (['Dhana'])

### FN #13: Charles de Gaulle — DEGAULLE_LIBERATION_1944

- **Event Date:** 1944-08-25 | **Domain:** CAREER
- **Active Dasha:** RAHU/JUPITER/KETU
- **All Yogas:** Ruchaka(FORMED)
- **Expected Planets:** MARS, JUPITER
- **Why FN:** Yogas formed (['Ruchaka']) but Dasha didn't activate them (MD=RAHU)

### FN #14: Charles de Gaulle — DEGAULLE_PRESIDENT_1959

- **Event Date:** 1959-01-08 | **Domain:** CAREER
- **Active Dasha:** JUPITER/JUPITER/JUPITER
- **All Yogas:** Ruchaka(FORMED)
- **Expected Planets:** SUN, JUPITER
- **Why FN:** Yogas formed (['Ruchaka']) but Dasha didn't activate them (MD=JUPITER)

### FN #15: Charles de Gaulle — DEGAULLE_DEATH_1970

- **Event Date:** 1970-11-09 | **Domain:** HEALTH
- **Active Dasha:** JUPITER/MOON/SATURN
- **All Yogas:** Ruchaka(FORMED)
- **Expected Planets:** RAHU, SATURN
- **Why FN:** Yogas formed (['Ruchaka']) but Dasha didn't activate them (MD=JUPITER)

### FN #16: Queen Victoria — VICTORIA_DEATH_1901

- **Event Date:** 1901-01-22 | **Domain:** HEALTH
- **Active Dasha:** SATURN/SATURN/RAHU
- **All Yogas:** Raja(WEAKENED), Sunapha(WEAKENED), Sunapha(WEAKENED)
- **Expected Planets:** RAHU, SATURN
- **Why FN:** Yogas formed (['Raja', 'Sunapha', 'Sunapha']) but Dasha didn't activate them (MD=SATURN)

### FN #17: Gregor Mendel — MENDEL_PUBLICATION_1866

- **Event Date:** 1866-01-01 | **Domain:** CAREER
- **Active Dasha:** MARS/KETU/SATURN
- **All Yogas:** Dhana(FORMED), Sunapha(CANCELLED), Saraswati(FORMED), Amala(FORMED)
- **Expected Planets:** SATURN, MERCURY
- **Why FN:** Yogas formed (['Dhana', 'Saraswati', 'Amala']) but not activated; others cancelled (['Sunapha'])

### FN #18: Rosalind Franklin — FRANKLIN_PHOTO51_1952

- **Event Date:** 1952-05-01 | **Domain:** CAREER
- **Active Dasha:** MARS/MERCURY/VENUS
- **All Yogas:** Vipareeta Raja(FORMED)
- **Expected Planets:** SUN, MERCURY
- **Why FN:** Yogas formed (['Vipareeta Raja']) but Dasha didn't activate them (MD=MARS)

### FN #19: Rosalind Franklin — FRANKLIN_DNA_1953

- **Event Date:** 1953-04-25 | **Domain:** CAREER
- **Active Dasha:** MARS/KETU/JUPITER
- **All Yogas:** Vipareeta Raja(FORMED)
- **Expected Planets:** JUPITER, MERCURY
- **Why FN:** Yogas formed (['Vipareeta Raja']) but Dasha didn't activate them (MD=MARS)

### FN #20: Rosalind Franklin — FRANKLIN_DEATH_1958

- **Event Date:** 1958-04-16 | **Domain:** HEALTH
- **Active Dasha:** RAHU/RAHU/MARS
- **All Yogas:** Vipareeta Raja(FORMED)
- **Expected Planets:** RAHU, SATURN
- **Why FN:** Yogas formed (['Vipareeta Raja']) but Dasha didn't activate them (MD=RAHU)

### FN #21: Ludwig van Beethoven — BEETHOVEN_9TH_1824

- **Event Date:** 1824-05-07 | **Domain:** CAREER
- **Active Dasha:** RAHU/KETU/MARS
- **All Yogas:** Dhana(CANCELLED)
- **Expected Planets:** JUPITER, VENUS
- **Why FN:** All yogas cancelled (['Dhana'])

### FN #22: Ludwig van Beethoven — BEETHOVEN_MOONLIGHT_1802

- **Event Date:** 1802-01-01 | **Domain:** CAREER
- **Active Dasha:** MOON/SATURN/RAHU
- **All Yogas:** Dhana(CANCELLED)
- **Expected Planets:** MERCURY, VENUS
- **Why FN:** All yogas cancelled (['Dhana'])

### FN #23: Ludwig van Beethoven — BEETHOVEN_DEATH_1827

- **Event Date:** 1827-03-26 | **Domain:** HEALTH
- **Active Dasha:** RAHU/VENUS/SATURN
- **All Yogas:** Dhana(CANCELLED)
- **Expected Planets:** RAHU, SATURN
- **Why FN:** All yogas cancelled (['Dhana'])

### FN #24: Pablo Picasso — PICASSO_GUERNICA_1937

- **Event Date:** 1937-04-26 | **Domain:** CAREER
- **Active Dasha:** JUPITER/JUPITER/MOON
- **All Yogas:** —
- **Expected Planets:** SATURN, VENUS
- **Why FN:** No yogas formed in chart at all

### FN #25: Pablo Picasso — PICASSO_BLUE_1901

- **Event Date:** 1901-01-01 | **Domain:** CAREER
- **Active Dasha:** MOON/MOON/RAHU
- **All Yogas:** —
- **Expected Planets:** RAHU, VENUS
- **Why FN:** No yogas formed in chart at all

### FN #26: Pablo Picasso — PICASSO_DEATH_1973

- **Event Date:** 1973-04-08 | **Domain:** HEALTH
- **Active Dasha:** MERCURY/KETU/KETU
- **All Yogas:** —
- **Expected Planets:** RAHU, SATURN
- **Why FN:** No yogas formed in chart at all

### FN #27: Leo Tolstoy — TOLSTOY_WAR_AND_PEACE_1869

- **Event Date:** 1869-01-01 | **Domain:** CAREER
- **Active Dasha:** RAHU/RAHU/RAHU
- **All Yogas:** —
- **Expected Planets:** JUPITER, MERCURY
- **Why FN:** No yogas formed in chart at all

### FN #28: Leo Tolstoy — TOLSTOY_ANNA_KARENINA_1877

- **Event Date:** 1877-01-01 | **Domain:** CAREER
- **Active Dasha:** RAHU/MERCURY/MERCURY
- **All Yogas:** —
- **Expected Planets:** MERCURY, VENUS
- **Why FN:** No yogas formed in chart at all

### FN #29: Leo Tolstoy — TOLSTOY_DEATH_1910

- **Event Date:** 1910-11-20 | **Domain:** HEALTH
- **Active Dasha:** SATURN/VENUS/RAHU
- **All Yogas:** —
- **Expected Planets:** RAHU, SATURN
- **Why FN:** No yogas formed in chart at all

### FN #30: Charlie Chaplin — CHAPLIN_GOLD_RUSH_1925

- **Event Date:** 1925-08-16 | **Domain:** CAREER
- **Active Dasha:** MARS/SUN/VENUS
- **All Yogas:** Raja(WEAKENED), Vipareeta Raja(FORMED)
- **Expected Planets:** JUPITER, VENUS
- **Why FN:** Yogas formed (['Raja', 'Vipareeta Raja']) but Dasha didn't activate them (MD=MARS)

### FN #31: Pyotr Tchaikovsky — TCHAIKOVSKY_SWAN_1877

- **Event Date:** 1877-03-04 | **Domain:** CAREER
- **Active Dasha:** RAHU/RAHU/VENUS
- **All Yogas:** Gajakesari(WEAKENED), Raja(WEAKENED), Dhana(CANCELLED), Anapha(WEAKENED)
- **Expected Planets:** SATURN, VENUS
- **Why FN:** Yogas formed (['Gajakesari', 'Raja', 'Anapha']) but not activated; others cancelled (['Dhana'])

### FN #32: Anton Chekhov — CHEKHOV_DEATH_1904

- **Event Date:** 1904-07-15 | **Domain:** HEALTH
- **Active Dasha:** MARS/RAHU/MARS
- **All Yogas:** Gajakesari(FORMED), Raja(CANCELLED), Sunapha(FORMED), Budhaditya(CANCELLED)
- **Expected Planets:** RAHU, SATURN
- **Why FN:** Yogas formed (['Gajakesari', 'Sunapha']) but not activated; others cancelled (['Raja', 'Budhaditya'])

### FN #33: Henry Ford — FORD_MODEL_T_1908

- **Event Date:** 1908-10-01 | **Domain:** CAREER
- **Active Dasha:** MARS/SATURN/RAHU
- **All Yogas:** —
- **Expected Planets:** MERCURY, VENUS
- **Why FN:** No yogas formed in chart at all

### FN #34: Henry Ford — FORD_ASSEMBLY_1913

- **Event Date:** 1913-12-01 | **Domain:** CAREER
- **Active Dasha:** RAHU/RAHU/MERCURY
- **All Yogas:** —
- **Expected Planets:** SATURN, MERCURY
- **Why FN:** No yogas formed in chart at all

### FN #35: Henry Ford — FORD_DEATH_1947

- **Event Date:** 1947-04-07 | **Domain:** HEALTH
- **Active Dasha:** SATURN/SATURN/MERCURY
- **All Yogas:** —
- **Expected Planets:** RAHU, SATURN
- **Why FN:** No yogas formed in chart at all

### FN #36: John D. Rockefeller — ROCKEFELLER_STD_1870

- **Event Date:** 1870-01-10 | **Domain:** CAREER
- **Active Dasha:** MOON/MOON/MOON
- **All Yogas:** Raja(WEAKENED)
- **Expected Planets:** MERCURY, VENUS
- **Why FN:** Yogas formed (['Raja']) but Dasha didn't activate them (MD=MOON)

### FN #37: Andrew Carnegie — CARNEGIE_GOSPEL_1889

- **Event Date:** 1889-06-01 | **Domain:** CAREER
- **Active Dasha:** RAHU/JUPITER/RAHU
- **All Yogas:** Raja(CANCELLED)
- **Expected Planets:** JUPITER, MERCURY
- **Why FN:** All yogas cancelled (['Raja'])

### FN #38: J.P. Morgan — MORGAN_PANIC_1907

- **Event Date:** 1907-10-24 | **Domain:** CAREER
- **Active Dasha:** SATURN/SATURN/VENUS
- **All Yogas:** Sunapha(FORMED), Sunapha(FORMED), Neecha Bhanga(FORMED)
- **Expected Planets:** SATURN, VENUS
- **Why FN:** Yogas formed (['Sunapha', 'Sunapha', 'Neecha Bhanga']) but Dasha didn't activate them (MD=SATURN)

### FN #39: J.P. Morgan — MORGAN_DEATH_1913

- **Event Date:** 1913-03-31 | **Domain:** HEALTH
- **Active Dasha:** SATURN/KETU/SATURN
- **All Yogas:** Sunapha(FORMED), Sunapha(FORMED), Neecha Bhanga(FORMED)
- **Expected Planets:** RAHU, SATURN
- **Why FN:** Yogas formed (['Sunapha', 'Sunapha', 'Neecha Bhanga']) but Dasha didn't activate them (MD=SATURN)

### FN #40: Jackie Robinson — ROBINSON_BREAKS_COLOR_1947

- **Event Date:** 1947-04-15 | **Domain:** CAREER
- **Active Dasha:** MOON/KETU/JUPITER
- **All Yogas:** Raja(WEAKENED), Budhaditya(FORMED)
- **Expected Planets:** MARS, JUPITER
- **Why FN:** Yogas formed (['Raja', 'Budhaditya']) but Dasha didn't activate them (MD=MOON)

### FN #41: Jackie Robinson — ROBINSON_DEATH_1972

- **Event Date:** 1972-10-24 | **Domain:** HEALTH
- **Active Dasha:** RAHU/MOON/SATURN
- **All Yogas:** Raja(WEAKENED), Budhaditya(FORMED)
- **Expected Planets:** RAHU, SATURN
- **Why FN:** Yogas formed (['Raja', 'Budhaditya']) but Dasha didn't activate them (MD=RAHU)

---

## Section 3: Coverage Gap Analysis

### Charts with Zero Yoga Formations

These subjects have NO yogas detected by the engine. This represents a fundamental coverage gap.

**Henry Ford** — 3 FNs (all events)
- Lagna: MEENA
- Events: FORD_MODEL_T_1908, FORD_ASSEMBLY_1913, FORD_DEATH_1947
- Root cause: No classical yoga conditions met for this planetary configuration. The engine's yoga detectors don't cover this chart pattern.

**Leo Tolstoy** — 3 FNs (all events)
- Lagna: KANYA
- Events: TOLSTOY_WAR_AND_PEACE_1869, TOLSTOY_ANNA_KARENINA_1877, TOLSTOY_DEATH_1910
- Root cause: No classical yoga conditions met for this planetary configuration. The engine's yoga detectors don't cover this chart pattern.

**Pablo Picasso** — 3 FNs (all events)
- Lagna: KARKA
- Events: PICASSO_GUERNICA_1937, PICASSO_BLUE_1901, PICASSO_DEATH_1973
- Root cause: No classical yoga conditions met for this planetary configuration. The engine's yoga detectors don't cover this chart pattern.

### Charts with Yogas Cancelled by Modifier Pipeline

**Andrew Carnegie** — 1 FNs
- Cancelled yogas: Raja
- The modifier pipeline (combustion, debilitation, D9) cancelled yogas that might have been relevant

**Anton Chekhov** — 1 FNs
- Cancelled yogas: Budhaditya, Raja
- The modifier pipeline (combustion, debilitation, D9) cancelled yogas that might have been relevant

**Gregor Mendel** — 1 FNs
- Cancelled yogas: Sunapha
- The modifier pipeline (combustion, debilitation, D9) cancelled yogas that might have been relevant

**Isaac Newton** — 1 FNs
- Cancelled yogas: Saraswati, Raja
- The modifier pipeline (combustion, debilitation, D9) cancelled yogas that might have been relevant

**John F. Kennedy** — 2 FNs
- Cancelled yogas: Sunapha
- The modifier pipeline (combustion, debilitation, D9) cancelled yogas that might have been relevant

**Ludwig van Beethoven** — 3 FNs
- Cancelled yogas: Dhana
- The modifier pipeline (combustion, debilitation, D9) cancelled yogas that might have been relevant

**Margaret Thatcher** — 1 FNs
- Cancelled yogas: Dhana
- The modifier pipeline (combustion, debilitation, D9) cancelled yogas that might have been relevant

**Nelson Mandela** — 1 FNs
- Cancelled yogas: Dhudhara, Sunapha
- The modifier pipeline (combustion, debilitation, D9) cancelled yogas that might have been relevant

**Pyotr Tchaikovsky** — 1 FNs
- Cancelled yogas: Dhana
- The modifier pipeline (combustion, debilitation, D9) cancelled yogas that might have been relevant

**Wolfgang Amadeus Mozart** — 2 FNs
- Cancelled yogas: Dhana
- The modifier pipeline (combustion, debilitation, D9) cancelled yogas that might have been relevant

### Dasha Activation Mismatch Patterns

**28 events** had formed yogas but the Dasha didn't activate them.

Active Mahadasha Lords during FN events:

- MARS: 8 events
- JUPITER: 6 events
- RAHU: 6 events
- MOON: 3 events
- SATURN: 3 events
- VENUS: 1 events
- SUN: 1 events

**Root cause:** The Dasha activation fires only when the MD/AD/PD lord IS one of the yoga's involved planets. For many FN events, the Dasha lord is unrelated to any formed yoga's planets.

---

## Section 4: Systemic Patterns

### Pattern 1: No-Yoga Charts Are the Biggest Problem
- **9 events** (across 3 subjects) have zero yogas detected
- These are structural coverage gaps — the engine doesn't detect yogas for these chart configurations
- Subjects like Picasso, Tolstoy, Beethoven, de Gaulle, Ford, R. Franklin have 0 yogas formed

### Pattern 2: HEALTH Events Are Consistently Missed
- **13/41 FNs** are HEALTH events
- The engine has no HEALTH-specific yoga detection
- Death/crisis events are not predicted by classical yoga theory in the same way career events are
- The Dasha system does predict difficult periods through malefic Dasha lords, but the current activation logic only fires when the Dasha lord matches a yoga's planets

### Pattern 3: Dasha Activation Is Too Strict
- Many events have formed yogas but the Dasha lord doesn't match
- The current logic requires MD/AD/PD lord to BE one of the yoga's involved planets
- A looser activation (e.g., Dasha lord aspects or disposits a yoga planet) could recover some FNs
