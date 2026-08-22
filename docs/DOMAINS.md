# JRS Domains — Tier 1 (v1.0)

JRS v1.0 ships with 8 validated domains, each implementing the full pipeline:
Domain Rules → Evidence Records → Convergence Assessment → Traceable Verdict.

Every domain has been validated against reference charts with known ground truth.

---

## 1. Wealth (`wealth`)

**Config**: `config/domains/wealth.toml` | **Rules**: 20 | **Service**: `WealthDomainService`

| Outcome Taxonomy | Description | Trigger Facts |
|-----------------|-------------|---------------|
| `WEALTH_ACCUMULATION` | Wealth through earned income | 2nd lord in 11th, Jupiter strong + 2nd/11th connection |
| `SUDDEN_FINANCIAL_LOSS` | Unexpected financial setback | Saturn afflicting 2nd lord, 2nd lord debilitated + Ketu |
| `INHERITANCE` | Inheritance received | 8th lord strong + 4th connection, Jupiter in 8th + benefic aspects |
| `DEBT_BURDEN` | Chronic debt issues | Saturn in 2nd + malefic, 6th lord connected to 2nd + Rahu |
| `BUSINESS_WEALTH` | Wealth from business | Mercury strong + 7th/10th connection |
| `SPECULATIVE_GAINS` | Gains from speculation | Rahu strong in 5th + Jupiter |
| `PROPERTY_WEALTH` | Real estate wealth | 4th lord strong + Mars connection |
| `MULTIPLE_INCOME_STREAMS` | Diversified income | 11th lord strong + Mercury/Jupiter |
| `FINANCIAL_STABILITY` | Stable finances | 2nd lord in Kendra or Trikona |
| `WEALTH_THROUGH_SPOUSE` | Spouse brings wealth | Venus strong in 7th + Jupiter aspect |
| `EARNING_DIFFICULTY` | Difficulty earning | 2nd lord combust + malefic |
| `FINANCIAL_RECOVERY` | Recovery from loss | Jupiter aspecting debilitated 2nd lord |
| `CHARITABLE_DISPOSITION` | Giving away wealth | Jupiter in 12th + Ketu |
| `UNEXPECTED_WINDFALL` | Sudden windfall | Jupiter in 8th + Rahu |

**Validation**: 4 reference charts (inheritance, business, debt, speculative loss) → 16 tests ✅

---

## 2. Career (`career`)

**Config**: `config/domains/career.toml` | **Rules**: 14 | **Service**: `CareerDomainService`

| Outcome Taxonomy | Description | Trigger Facts |
|-----------------|-------------|---------------|
| `CAREER_ASCENT` | Career rise | Multiple indicators |
| `GOVERNMENT_SERVICE` | Government/civil service | Sun-Saturn axis on 10th |
| `SUCCESSFUL_BUSINESS` | Business success | Mercury-Jupiter combination |
| `ENTREPRENEURSHIP` | Entrepreneurial success | 7th-10th connection |
| `CHANGE_OF_PROFESSION` | Career change | Multiple indicators |
| `FOREIGN_CAREER` | Career abroad | Rahu/12th indicators |
| `AUTHORITY_STATUS` | Position of authority | Sun strong + 10th |
| `PROFESSIONAL_STAGNATION` | Career stagnation | Saturn indicators |
| `LOSS_OF_EMPLOYMENT` | Job loss | Malefic indicators |
| `CREATIVE_CAREER` | Creative/artistic career | Venus-Mercury indicators |

**Validation**: 5 reference charts → 16 tests ✅

---

## 3. Marriage (`marriage`)

**Config**: `config/domains/marriage.toml` | **Rules**: 14 | **Service**: `MarriageDomainService`

| Outcome Taxonomy | Description | Trigger Facts |
|-----------------|-------------|---------------|
| `MARRIAGE_FORMATION` | Marriage timing | 7th lord in Kendra/Trikona, Venus strength |
| `MARITAL_HARMONY` | Happy marriage | Jupiter aspect on 7th |
| `DELAYED_MARRIAGE` | Late marriage | Saturn on 7th lord |
| `SEPARATION` | Separation/divorce | 6th/8th/12th house connections |
| `LOVE_MARRIAGE` | Love marriage | Venus strong + Rahu indicators |
| `ARRANGED_MARRIAGE` | Arranged marriage | Jupiter influence on 7th |
| `MARITAL_CONFLICT` | Marital discord | Mars affliction, Saturn aspects |
| `REMARRIAGE_AFTER_DIVORCE` | Second marriage | Multiple 7th house indicators |
| `LATE_MARRIAGE` | Marriage after 30+ | Saturn delay indicators |

**Validation**: 5 reference charts → 16 tests ✅

---

## 4. Progeny (`progeny`)

**Config**: `config/domains/progeny.toml` | **Rules**: 20 | **Service**: `ProgenyDomainService`

| Outcome Taxonomy | Description | Trigger Facts |
|-----------------|-------------|---------------|
| `EASY_CONCEPTION` | Smooth conception | Jupiter strong + 5th lord in Kendra |
| `DELAYED_PROGENY` | Delayed children | Saturn in 5th, 5th lord debilitated |
| `MULTIPLE_CHILDREN` | More than 2 children | Jupiter strong + benefic aspects on 5th |
| `CHALLENGES_WITH_CHILDREN` | Child-related issues | Malefic in 5th without benefic |
| `CHILDREN_SUCCESS` | Children achieve success | Jupiter strong + 5th lord in Kendra/Trikona |
| `ADOPTION_INDICATORS` | Adoption likely | 5th lord combust + Rahu |
| `MISCARRIAGE_RISK` | Pregnancy complications | Mars in 5th + malefic conjunction |
| `CHILDREN_EDUCATION` | Children's education | Mercury strong + Jupiter aspecting 5th |

**Validation**: 4 reference charts → 16 tests ✅

---

## 5. Migration (`migration`)

**Config**: `config/domains/migration.toml` | **Rules**: 14 | **Service**: `MigrationDomainService`

| Outcome Taxonomy | Description | Trigger Facts |
|-----------------|-------------|---------------|
| `FOREIGN_SETTLEMENT` | Permanent abroad | Rahu in 12th, 9th lord in 12th |
| `SHORT_TERM_TRAVEL` | Frequent travel | Mercury strong + 12th connection |
| `MIGRATION_DELAY` | Delayed migration | Saturn in 12th |
| `RETURN_TO_HOMELAND` | Return from abroad | Saturn in 12th + malefic |
| `CROSS_CULTURAL_SUCCESS` | Success in foreign culture | Jupiter strong + 12th connection |
| `VISA_OBSTACLES` | Visa problems | Saturn afflicting 12th lord |

**Validation**: 4 reference charts → 16 tests ✅

---

## 6. Education (`education`)

**Config**: `config/domains/education.toml` | **Rules**: 14 | **Service**: `EducationDomainService`

| Outcome Taxonomy | Description | Trigger Facts |
|-----------------|-------------|---------------|
| `HIGHER_EDUCATION` | Post-graduate studies | 4th lord in Kendra |
| `EARLY_EDUCATION_SUCCESS` | Academic excellence young | Mercury strong + 4th connection |
| `EDUCATION_DISRUPTION` | Study interruptions | Saturn in 4th, Rahu in 4th + malefic |
| `FOREIGN_EDUCATION` | Study abroad | 9th lord in 12th |
| `TECHNICAL_SKILLS` | STEM/technical aptitude | Mercury strong + Saturn aspect |
| `RESEARCH_ACADEMIA` | Academic/research career | Ketu in 4th + Jupiter, Saturn strong + 9th |

**Validation**: 4 reference charts → 16 tests ✅

---

## 7. Property (`property`)

**Config**: `config/domains/property.toml` | **Rules**: 14 | **Service**: `PropertyDomainService`

| Outcome Taxonomy | Description | Trigger Facts |
|-----------------|-------------|---------------|
| `PROPERTY_ACQUISITION` | Buying property | 4th lord strong, Mars strong + 4th |
| `REAL_ESTATE_WEALTH` | Profit from property | Venus strong in 4th |
| `DISPUTES_OVER_PROPERTY` | Legal property disputes | Mars afflicting 4th |
| `LOSS_OF_PROPERTY` | Losing property | 4th lord debilitated, Saturn afflicting |
| `MULTIPLE_PROPERTIES` | Owning several properties | Multiple planets in 4th, Jupiter strong |
| `FOREIGN_PROPERTY` | Property abroad | Rahu in 4th + 12th connection |

**Validation**: 4 reference charts → 16 tests ✅

---

## 8. Transitions (`transitions`)

**Config**: `config/domains/transitions.toml` | **Rules**: 14 | **Service**: `TransitionsDomainService`

| Outcome Taxonomy | Description | Trigger Facts |
|-----------------|-------------|---------------|
| `LIFE_PHASE_SHIFT` | Major life change | Saturn return, Jupiter-Ketu conjunction |
| `SUDDEN_UPHEAVAL` | Unexpected upheaval | Rahu-Ketu axis activated, eclipse effects |
| `GRADUAL_EVOLUTION` | Slow transformation | Saturn slow transit, Jupiter progressive |
| `CRISIS_RECOVERY` | Recovering from crisis | 8th house activations + benefic |
| `SPIRITUAL_AWAKENING` | Spiritual transformation | Ketu strong + Jupiter |
| `STATUS_CHANGE` | Social status change | 10th lord activated |

**Validation**: 4 reference charts → 16 tests ✅

---

## Cross-Domain Summary

| Metric | Value |
|--------|-------|
| Total domains | 8 |
| Total rules | 114 |
| Total outcomes | 68 unique taxonomies |
| Validation charts | 34 |
| Integration tests | 128 passing |
| Unit tests | 384 passing |
| CLI queries supported | 9 (career, wealth, marriage, education, property, children, migration, travel, transitions) |
