# Phase F1: 50-Chart Cohort Statistical Evaluation

**Strictly Blind Evaluation — No Calibration or Tuning**

**Cohort Size:** 50 subjects | **Total Events:** 150

---

## Section 1: Core Statistical Metrics

| Metric | Value |
|--------|-------|
| **True Positives (TP)** | 85 |
| **False Positives (FP)** | 24 |
| **False Negatives (FN)** | 41 |
| **Precision** | 0.780 |
| **Recall** | 0.675 |
| **F1 Score** | 0.723 |
| **Hit Rate (TP/Total)** | 0.567 (85/150) |
| **95% Confidence Interval** | [0.487, 0.646] |

### Interpretation

- **Precision** (0.780): Of all events where the engine predicted a relevant yoga activation, 78.0% were actually relevant to the event domain.
- **Recall** (0.675): Of all events where a relevant yoga existed and was activated, the engine correctly identified 67.5%.
- **F1 Score** (0.723): Harmonic mean of precision and recall, balancing false positives and false negatives.
- **95% CI**: The true hit rate lies between 48.7% and 64.6% with 95% confidence (Wilson score interval).

---

## Section 2: Domain Breakdown

| Domain | Events | TP | FP | FN | Precision | Recall | F1 |
|--------|--------|----|----|-----|-----------|--------|-----|
| CAREER | 93 | 58 | 7 | 28 | 0.892 | 0.674 | 0.768 |
| HEALTH | 48 | 19 | 16 | 13 | 0.543 | 0.594 | 0.567 |
| MARRIAGE | 3 | 2 | 1 | 0 | 0.667 | 1.000 | 0.800 |
| MIGRATION | 6 | 6 | 0 | 0 | 1.000 | 1.000 | 1.000 |

---

## Section 3: Per-Subject Breakdown

| Subject | Events | TP | FP | FN | Precision | Recall | F1 |
|---------|--------|----|----|-----|-----------|--------|-----|
| Abraham Lincoln | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Ada Lovelace | 3 | 2 | 1 | 0 | 0.667 | 1.000 | 0.800 |
| Albert Einstein | 3 | 2 | 0 | 1 | 1.000 | 0.667 | 0.800 |
| Alexander von Humboldt | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Amelia Earhart | 3 | 2 | 1 | 0 | 0.667 | 1.000 | 0.800 |
| Andrew Carnegie | 3 | 0 | 2 | 1 | 0.000 | 0.000 | 0.000 |
| Anton Chekhov | 3 | 1 | 1 | 1 | 0.500 | 0.500 | 0.500 |
| Babe Ruth | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Benjamin Franklin | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Carl Jung | 3 | 1 | 2 | 0 | 0.333 | 1.000 | 0.500 |
| Charles Darwin | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Charles de Gaulle | 3 | 0 | 0 | 3 | 0.000 | 0.000 | 0.000 |
| Charlie Chaplin | 3 | 2 | 0 | 1 | 1.000 | 0.667 | 0.800 |
| Cornelius Vanderbilt | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Dwight Eisenhower | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Franz Liszt | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Gregor Mendel | 3 | 1 | 1 | 1 | 0.500 | 0.500 | 0.500 |
| Hans Christian Andersen | 3 | 2 | 1 | 0 | 0.667 | 1.000 | 0.800 |
| Henry Ford | 3 | 0 | 0 | 3 | 0.000 | 0.000 | 0.000 |
| Indira Gandhi | 3 | 2 | 0 | 1 | 1.000 | 0.667 | 0.800 |
| Isaac Newton | 3 | 1 | 1 | 1 | 0.500 | 0.500 | 0.500 |
| J.P. Morgan | 3 | 1 | 0 | 2 | 1.000 | 0.333 | 0.500 |
| Jackie Robinson | 3 | 1 | 0 | 2 | 1.000 | 0.333 | 0.500 |
| Jesse Owens | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Jim Thorpe | 3 | 0 | 3 | 0 | 0.000 | 0.000 | 0.000 |
| John D. Rockefeller | 3 | 1 | 1 | 1 | 0.500 | 0.500 | 0.500 |
| John F. Kennedy | 3 | 1 | 0 | 2 | 1.000 | 0.333 | 0.500 |
| Leo Tolstoy | 3 | 0 | 0 | 3 | 0.000 | 0.000 | 0.000 |
| Louis Pasteur | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Ludwig van Beethoven | 3 | 0 | 0 | 3 | 0.000 | 0.000 | 0.000 |
| Mahatma Gandhi | 3 | 0 | 3 | 0 | 0.000 | 0.000 | 0.000 |
| Margaret Thatcher | 3 | 2 | 0 | 1 | 1.000 | 0.667 | 0.800 |
| Marie Curie | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Mark Twain | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Max Planck | 3 | 2 | 1 | 0 | 0.667 | 1.000 | 0.800 |
| Mother Teresa | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Muhammad Ali | 3 | 2 | 1 | 0 | 0.667 | 1.000 | 0.800 |
| Nelson Mandela | 3 | 1 | 1 | 1 | 0.500 | 0.500 | 0.500 |
| Nikola Tesla | 3 | 2 | 1 | 0 | 0.667 | 1.000 | 0.800 |
| Otto von Bismarck | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Pablo Picasso | 3 | 0 | 0 | 3 | 0.000 | 0.000 | 0.000 |
| Pyotr Tchaikovsky | 3 | 2 | 0 | 1 | 1.000 | 0.667 | 0.800 |
| Queen Victoria | 3 | 2 | 0 | 1 | 1.000 | 0.667 | 0.800 |
| Rosalind Franklin | 3 | 0 | 0 | 3 | 0.000 | 0.000 | 0.000 |
| Sigmund Freud | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Steve Jobs | 3 | 1 | 0 | 2 | 1.000 | 0.333 | 0.500 |
| Vincent van Gogh | 3 | 2 | 1 | 0 | 0.667 | 1.000 | 0.800 |
| Werner Heisenberg | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Winston Churchill | 3 | 1 | 1 | 1 | 0.500 | 0.500 | 0.500 |
| Wolfgang Amadeus Mozart | 3 | 0 | 1 | 2 | 0.000 | 0.000 | 0.000 |

---

## Section 4: False Positive Analysis

**Total FPs: 24**

| Subject | Event | Domain | Detail |
|---------|-------|--------|--------|
| Wolfgang Amadeus Mozart | MOZART_MARRIAGE_1782 | MARRIAGE | Yoga activated but not relevant to domain/event |
| Nikola Tesla | TESLA_DEATH_1943 | HEALTH | Yoga activated but not relevant to domain/event |
| Isaac Newton | NEWTON_DEATH_1727 | HEALTH | Yoga activated but not relevant to domain/event |
| Amelia Earhart | EARHART_DISAPPEARANCE_1937 | HEALTH | Yoga activated but not relevant to domain/event |
| Winston Churchill | CHURCHILL_DEATH_1965 | HEALTH | Yoga activated but not relevant to domain/event |
| Nelson Mandela | MANDELA_DEATH_2013 | HEALTH | Yoga activated but not relevant to domain/event |
| Mahatma Gandhi | GANDHI_SALT_1930 | CAREER | Yoga activated but not relevant to domain/event |
| Mahatma Gandhi | GANDHI_INDEPENDENCE_1947 | CAREER | Yoga activated but not relevant to domain/event |
| Mahatma Gandhi | GANDHI_ASSASSINATION_1948 | HEALTH | Yoga activated but not relevant to domain/event |
| Gregor Mendel | MENDEL_DEATH_1884 | HEALTH | Yoga activated but not relevant to domain/event |
| Ada Lovelace | LOVELACE_DEATH_1852 | HEALTH | Yoga activated but not relevant to domain/event |
| Max Planck | PLANCK_DEATH_1947 | HEALTH | Yoga activated but not relevant to domain/event |
| Carl Jung | JUNG_COLLECTIVE_1916 | CAREER | Yoga activated but not relevant to domain/event |
| Carl Jung | JUNG_DEATH_1961 | HEALTH | Yoga activated but not relevant to domain/event |
| Vincent van Gogh | VANGOGH_DEATH_1890 | HEALTH | Yoga activated but not relevant to domain/event |
| Hans Christian Andersen | ANDERSEN_DEATH_1875 | HEALTH | Yoga activated but not relevant to domain/event |
| Anton Chekhov | CHEKHOV_CHERRY_1904 | CAREER | Yoga activated but not relevant to domain/event |
| John D. Rockefeller | ROCKEFELLER_DEATH_1937 | HEALTH | Yoga activated but not relevant to domain/event |
| Andrew Carnegie | CARNEGIE_STEEL_1892 | CAREER | Yoga activated but not relevant to domain/event |
| Andrew Carnegie | CARNEGIE_DEATH_1919 | HEALTH | Yoga activated but not relevant to domain/event |
| Muhammad Ali | ALI_DEATH_2016 | HEALTH | Yoga activated but not relevant to domain/event |
| Jim Thorpe | THORPE_OLYMPICS_1912 | CAREER | Yoga activated but not relevant to domain/event |
| Jim Thorpe | THORPE_NFL_1920 | CAREER | Yoga activated but not relevant to domain/event |
| Jim Thorpe | THORPE_DEATH_1953 | HEALTH | Yoga activated but not relevant to domain/event |

---

## Section 5: False Negative Analysis

**Total FNs: 41**

| Subject | Event | Domain | Detail |
|---------|-------|--------|--------|
| Albert Einstein | EINSTEIN_GENERAL_RELATIVITY_1915 | CAREER | No yoga activated during event |
| Wolfgang Amadeus Mozart | MOZART_DON_GIOVANNI_1787 | CAREER | No yoga activated during event |
| Wolfgang Amadeus Mozart | MOZART_DEATH_1791 | HEALTH | No yoga activated during event |
| Indira Gandhi | GANDHI_ASSASSINATION_1984 | HEALTH | No yoga activated during event |
| Isaac Newton | NEWTON_LUCASIAN_1669 | CAREER | No yoga activated during event |
| Steve Jobs | JOBS_APPLE_1976 | CAREER | No yoga activated during event |
| Steve Jobs | JOBS_OUSTED_1985 | CAREER | No yoga activated during event |
| Winston Churchill | CHURCHILL_PM_1940 | CAREER | No yoga activated during event |
| Nelson Mandela | MANDELA_PRESIDENT_1994 | CAREER | No yoga activated during event |
| John F. Kennedy | JFK_CUBAN_MISSILE_1962 | CAREER | No yoga activated during event |
| John F. Kennedy | JFK_ASSASSINATION_1963 | HEALTH | No yoga activated during event |
| Margaret Thatcher | THATCHER_FALKLANDS_1982 | CAREER | No yoga activated during event |
| Charles de Gaulle | DEGAULLE_LIBERATION_1944 | CAREER | No yoga activated during event |
| Charles de Gaulle | DEGAULLE_PRESIDENT_1959 | CAREER | No yoga activated during event |
| Charles de Gaulle | DEGAULLE_DEATH_1970 | HEALTH | No yoga activated during event |
| Queen Victoria | VICTORIA_DEATH_1901 | HEALTH | No yoga activated during event |
| Gregor Mendel | MENDEL_PUBLICATION_1866 | CAREER | No yoga activated during event |
| Rosalind Franklin | FRANKLIN_PHOTO51_1952 | CAREER | No yoga activated during event |
| Rosalind Franklin | FRANKLIN_DNA_1953 | CAREER | No yoga activated during event |
| Rosalind Franklin | FRANKLIN_DEATH_1958 | HEALTH | No yoga activated during event |
| Ludwig van Beethoven | BEETHOVEN_9TH_1824 | CAREER | No yoga activated during event |
| Ludwig van Beethoven | BEETHOVEN_MOONLIGHT_1802 | CAREER | No yoga activated during event |
| Ludwig van Beethoven | BEETHOVEN_DEATH_1827 | HEALTH | No yoga activated during event |
| Pablo Picasso | PICASSO_GUERNICA_1937 | CAREER | No yoga activated during event |
| Pablo Picasso | PICASSO_BLUE_1901 | CAREER | No yoga activated during event |
| Pablo Picasso | PICASSO_DEATH_1973 | HEALTH | No yoga activated during event |
| Leo Tolstoy | TOLSTOY_WAR_AND_PEACE_1869 | CAREER | No yoga activated during event |
| Leo Tolstoy | TOLSTOY_ANNA_KARENINA_1877 | CAREER | No yoga activated during event |
| Leo Tolstoy | TOLSTOY_DEATH_1910 | HEALTH | No yoga activated during event |
| Charlie Chaplin | CHAPLIN_GOLD_RUSH_1925 | CAREER | No yoga activated during event |
| Pyotr Tchaikovsky | TCHAIKOVSKY_SWAN_1877 | CAREER | No yoga activated during event |
| Anton Chekhov | CHEKHOV_DEATH_1904 | HEALTH | No yoga activated during event |
| Henry Ford | FORD_MODEL_T_1908 | CAREER | No yoga activated during event |
| Henry Ford | FORD_ASSEMBLY_1913 | CAREER | No yoga activated during event |
| Henry Ford | FORD_DEATH_1947 | HEALTH | No yoga activated during event |
| John D. Rockefeller | ROCKEFELLER_STD_1870 | CAREER | No yoga activated during event |
| Andrew Carnegie | CARNEGIE_GOSPEL_1889 | CAREER | No yoga activated during event |
| J.P. Morgan | MORGAN_PANIC_1907 | CAREER | No yoga activated during event |
| J.P. Morgan | MORGAN_DEATH_1913 | HEALTH | No yoga activated during event |
| Jackie Robinson | ROBINSON_BREAKS_COLOR_1947 | CAREER | No yoga activated during event |
| Jackie Robinson | ROBINSON_DEATH_1972 | HEALTH | No yoga activated during event |

---

## Section 6: Methodology

### Evaluation Framework
- **Strictly blind**: The engine has no access to ground-truth event outcomes during prediction generation.
- **No calibration**: All weights, thresholds, and logic are frozen from the pre-F1 architecture.
- **No post-hoc adjustments**: Results are reported exactly as the pipeline produces them.

### Classification Rules
- **TP (True Positive)**: A relevant yoga was activated by the active Dasha during the event window.
- **FP (False Positive)**: A yoga was activated but was not relevant to the event domain or involved planets.
- **FN (False Negative)**: No yoga was activated despite a relevant yoga existing in the chart.

### Confidence Interval
- **Method**: Wilson score interval (normal approximation).
- **Coverage**: 95% confidence level.
- **Rationale**: Wilson score is preferred over Wald interval for binomial proportions, especially when p is near 0 or 1.

### Pipeline Layers
1. **Layer 1 — Relationship Graph**: Structural detection (conjunctions, aspects, dispositorship, exchanges)
2. **Layer 1.5 — Chain Evaluator**: Multi-hop Kendra-Trikona chain impact
3. **Layer 2 — Modifiers**: 5-tier priority (combustion, debilitation, graha yuddha, retrograde, node taint)
4. **Layer 3 — Temporal**: Vimshottari Dasha multiplier (transit inactive)
5. **Layer 4 — Varga**: D9 (Navamsha) confirmation
