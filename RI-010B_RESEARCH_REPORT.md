# RI-010B: MULTI-PLANET ASPECT/YOGA RELATIONSHIP RESEARCH — RESEARCH REPORT

> **Status:** Research Only — No Implementation
> **Date:** 2026-08-25
> **Awaiting:** Human review before proceeding to RI-010C

---

## Executive Summary

This report presents a source-critical research pass on classical multi-planet yoga formations and aspect relationships as described in the foundational texts of Jyotish. It covers conjunctions (Yuti), mutual aspects (Drishti), exchanges (Parivartana), dispositorship (Swakshetra), named classical yogas, and the rules for constructing meaningful aspect graphs.

**Key Finding:** The existing JRE-012 (Drik) engine computes a basic aspect graph with standard and special aspects, and JRE-013 (Yoga) detects structural connections (conjunction, aspect, exchange). However, the classical texts describe a much richer framework including aspect strength gradation (1/4, 1/2, 3/4, full), Parivartana classification (Maha/Kahala/Dainya), dispositor chains, Neecha Bhanga conditions, and multi-planet relationship hierarchies that are NOT yet captured.

---

## Section A: Conjunction (Yuti)

### A.1 Classical Definition

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Two or more planets in the same Rashi = conjunction (Yuti) | BPHS Ch.3 | CLASSICAL_PRIMARY | Sign-based, not degree-based in Parashari system |
| Conjunction is sign-based (same Rashi), not degree-based | Parashari system | CLASSICAL_PRIMARY | Different from Western degree-based conjunctions |
| Planets in same sign do NOT aspect each other | BPHS Ch.26 | CLASSICAL_PRIMARY | Conjunction replaces aspect for same-sign planets |
| Conjunction merges energies of involved planets | BPHS Ch.3 | CLASSICAL_PRIMARY | "Joining and departing from each other" |

### A.2 Multi-Planet Conjunctions

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| 3+ planets in same sign = multi-planet conjunction | BPHS Ch.3 | CLASSICAL_PRIMARY | Complex interaction; strongest planet dominates |
| Planet closest to other planets in conjunction is strongest | BPHS Ch.3 | COMMENTARY_DEPENDENT | Degree-based proximity within sign |
| Planet in exaltation/own sign dominates conjunction | BPHS Ch.3 | CLASSICAL_PRIMARY | Dignity determines influence hierarchy |

### A.3 Conjunction with Lagna

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Planet conjunct Lagna lord in Lagna = strong influence | BPHS Ch.33 | CLASSICAL_PRIMARY | Lagna conjunction amplifies planet's effects |
| Lagna lord in conjunction with benefic = auspicious | BPHS Ch.33 | CLASSICAL_PRIMARY | Benefic conjunction enhances native |
| Lagna lord in conjunction with malefic = challenging | BPHS Ch.33 | CLASSICAL_PRIMARY | Malefic conjunction creates obstacles |

### A.4 Benefic/Malefic Conjunction Effects

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Benefic + benefic conjunction = highly auspicious | BPHS Ch.3 | CLASSICAL_PRIMARY | Both planets reinforce positive results |
| Malefic + malefic conjunction = doubly challenging | BPHS Ch.3 | CLASSICAL_PRIMARY | Both planets reinforce negative results |
| Benefic + malefic conjunction = cancellation/modification | BPHS Ch.3 | CLASSICAL_PRIMARY | Malefic weakens benefic; benefic softens malefic |
| Planet's nature modified by conjunction partner | BPHS Ch.3 | CLASSICAL_PRIMARY | "Joining and departing" changes effects |

### A.5 Conjunction Involving Rahu/Ketu

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Rahu conjunct benefic → Rahu amplifies benefic results | BPHS Ch.3 | CLASSICAL_PRIMARY | Rahu acts as amplifier, not inherent good/bad |
| Rahu conjunct malefic → Rahu amplifies malefic results | BPHS Ch.3 | CLASSICAL_PRIMARY | Rahu magnifies the conjunction partner's nature |
| Ketu conjunct planet → Ketu spiritualizes results | BPHS Ch.3 | CLASSICAL_PRIMARY | Ketu redirects material expression toward spiritual |
| Rahu/Ketu in same sign as planet = conjunction | BPHS Ch.3 | CLASSICAL_PRIMARY | Even though nodes are "shadow planets" |
| Rahu/Ketu do NOT cast aspects in Parashari | BPHS Ch.26 | CLASSICAL_PRIMARY | Nodes have no aspects (though some texts mention Rahu 5/9) |

### A.6 Strength Requirements for Conjunction Effects

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Dignity of conjunct planets determines strength | BPHS Ch.3 | CLASSICAL_PRIMARY | Exaltation > own sign > friend > neutral > enemy > debilitation |
| Combustion weakens conjunct planet | BPHS Ch.3 | CLASSICAL_PRIMARY | Planet within combustion orb of Sun loses capacity |
| Retrograde modifies conjunction effects | BPHS Ch.3 | COMMENTARY_DEPENDENT | Retrograde planet acts stronger than direct in some contexts |
| Shadbala strength affects conjunction results | BPHS Ch.3 | COMMENTARY_DEPENDENT | Detailed strength system is later tradition |

### A.7 Orb Considerations in Classical Doctrine

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Parashari conjunction is sign-based (no orb) | BPHS Ch.3 | CLASSICAL_PRIMARY | Same Rashi = conjunction, regardless of degrees |
| Degree-based proximity affects strength within sign | BPHS Ch.3 | COMMENTARY_DEPENDENT | Closer planets in same sign interact more strongly |
| Classical texts do NOT specify degree orbs for conjunction | BPHS Ch.3 | CLASSICAL_PRIMARY | Orb system is Western; Parashari uses sign boundaries |

---

## Section B: Mutual Aspect (Drishti)

### B.1 Full Aspect Doctrine

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| ALL planets aspect the 7th house (180°) with full strength | BPHS Ch.26 | CLASSICAL_PRIMARY | Universal 7th aspect |
| Planets do NOT aspect 2nd, 6th, 8th, 12th from their sign | BPHS Ch.26 | CLASSICAL_PRIMARY | Only specific house offsets receive aspects |
| Planets in same sign do NOT aspect each other | BPHS Ch.26 | CLASSICAL_PRIMARY | Conjunction replaces aspect |

### B.2 Special Aspects

| Planet | Special Aspects | Strength | Source | Classification |
|--------|----------------|----------|--------|----------------|
| Mars | 4th and 8th | Full (100%) | BPHS Ch.26 | CLASSICAL_PRIMARY |
| Jupiter | 5th and 9th | Full (100%) | BPHS Ch.26 | CLASSICAL_PRIMARY |
| Saturn | 3rd and 10th | Full (100%) | BPHS Ch.26 | CLASSICAL_PRIMARY |
| Sun, Moon, Mercury, Venus | None (only 7th) | — | BPHS Ch.26 | CLASSICAL_PRIMARY |

### B.3 Aspect Strength Gradation (Parashari)

| Aspect Position | Strength | Source | Notes |
|-----------------|----------|--------|-------|
| 3rd and 10th house | 1/4 (quarter) | BPHS Ch.26 v.2-5 | Weakest aspect |
| 5th and 9th house | 1/2 (half) | BPHS Ch.26 v.2-5 | Moderate aspect |
| 4th and 8th house | 3/4 (three-quarter) | BPHS Ch.26 v.2-5 | Strong aspect |
| 7th house | Full (100%) | BPHS Ch.26 v.2-5 | Strongest aspect |

**Note:** This gradation applies to ALL planets' aspects on these positions. Special aspects (Mars 4/8, Jupiter 5/9, Saturn 3/10) override the gradation and cast FULL aspects on those positions.

### B.4 Aspect Strength by Planet Type

| Planet | 3rd/10th | 5th/9th | 4th/8th | 7th | Source |
|--------|----------|---------|---------|-----|--------|
| Saturn | 1/4 | 1/4 | 1/2 | 3/4 | BPHS Ch.26 |
| Jupiter | 3/4 | Full | 1/4 | 1/2 | BPHS Ch.26 |
| Mars | 1/2 | 3/4 | Full | 1/4 | BPHS Ch.26 |
| Sun/Moon/Mercury/Venus | 1/4 | 1/2 | 3/4 | Full | BPHS Ch.26 |

### B.5 Mutual Aspect Rules

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Mutual aspect (both aspect each other) = strong connection | BPHS Ch.26 | CLASSICAL_PRIMARY | "Major Sambandha" — one of five major associations |
| Mutual 7th aspect = strongest mutual connection | BPHS Ch.26 | CLASSICAL_PRIMARY | Full strength on both sides |
| One-way aspect = moderate connection | BPHS Ch.26 | COMMENTARY_DEPENDENT | Support flows in one direction only |
| Aspect strength differs by direction (A→B ≠ B→A) | BPHS Ch.26 | CLASSICAL_PRIMARY | Asymmetrical — Mars in Aries aspects Capricorn at 4th (full) but Saturn in Capricorn aspects Aries at 3rd (full for Saturn's special) |

### B.6 Aspect Chains

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| A→B→C = valid yoga structure when chain is unbroken | BPHS Ch.26 | COMMENTARY_DEPENDENT | Each link must satisfy classical predicates |
| Chain broken if intermediate planet combust/debilitated | BPHS Ch.26 | COMMENTARY_DEPENDENT | Weak link breaks the chain |
| Chain strengthened if intermediate planet dignified | BPHS Ch.26 | COMMENTARY_DEPENDENT | Strong link amplifies the chain |

### B.7 Benefic Aspect vs Malefic Aspect

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Benefic aspect = auspicious results | BPHS Ch.26 | CLASSICAL_PRIMARY | Jupiter, Venus, Mercury, waxing Moon aspects |
| Malefic aspect = challenging results | BPHS Ch.26 | CLASSICAL_PRIMARY | Saturn, Mars, Sun, waning Moon, Rahu aspects |
| Aspect of planet on own sign strengthens house | BPHS Ch.26 | CLASSICAL_PRIMARY | No harm to own sign's indications |
| Benefic owning evil bhavas becomes tainted | BPHS Ch.26 | CLASSICAL_PRIMARY | Functional malefic even though natural benefic |

### B.8 Aspect from/to Kendra/Trikona

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Aspect from Kendra lord to Trikona house = Raja Yoga | BPHS Ch.33 | CLASSICAL_PRIMARY | Structural yoga formation |
| Aspect from benefic to Kendra = strengthens | BPHS Ch.33 | CLASSICAL_PRIMARY | Kendra receives benefic influence |
| Aspect from malefic to Trikona = weakens | BPHS Ch.33 | CLASSICAL_PRIMARY | Trikona receives malefic influence |

### B.9 Aspect Modification by Dignity/State

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Exalted planet's aspect is strongest | BPHS Ch.26 | CLASSICAL_PRIMARY | Maximum capacity to influence |
| Debilitated planet's aspect is weakest | BPHS Ch.26 | CLASSICAL_PRIMARY | Reduced capacity |
| Combust planet's aspect is weakened | BPHS Ch.26 | CLASSICAL_PRIMARY | Sun's proximity diminishes |
| Retrograde planet's aspect is enhanced | BPHS Ch.26 | COMMENTARY_DEPENDENT | Retrograde acts as if exalted |

---

## Section C: Exchange (Parivartana)

### C.1 Classical Definition

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Planet A in sign owned by B, AND Planet B in sign owned by A = Parivartana | BPHS Ch.26 | CLASSICAL_PRIMARY | Mutual exchange of signs |
| Exchange is equivalent to conjunction in strength | BPHS Ch.26 | CLASSICAL_PRIMARY | One of five major Sambandhas |
| Exchange creates binding between two planets | BPHS Ch.26 | CLASSICAL_PRIMARY | Stronger than aspect alone |

### C.2 Three Types of Parivartana

| Type | Condition | Effect | Source | Classification |
|------|-----------|--------|--------|----------------|
| **Maha Parivartana** | Exchange between Kendra (1,4,7,10) and Trikona (1,5,9) lords | Highly auspicious — produces Raja Yoga | BPHS Ch.26, Phaladeepika | CLASSICAL_PRIMARY |
| **Kahala Parivartana** | Exchange between 2nd, 5th, 9th, 11th lords (not Kendra-Trikona) | Auspicious — produces wealth and prosperity | BPHS Ch.26 | CLASSICAL_PRIMARY |
| **Dainya Parivartana** | Exchange involving 6th, 8th, 12th lords with any house lord | Challenging — produces difficulties | BPHS Ch.26 | CLASSICAL_PRIMARY |

### C.3 Exchange Involving Kendra Lords

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Kendra lord exchanged with Trikona lord = Maha Parivartana | BPHS Ch.33 | CLASSICAL_PRIMARY | Most powerful exchange |
| Kendra lord exchanged with Kendra lord = Kahala | BPHS Ch.26 | CLASSICAL_PRIMARY | Strong but not Raja Yoga |
| Kendra lord exchanged with Dusthana lord = Dainya | BPHS Ch.26 | CLASSICAL_PRIMARY | Kendra lord tainted by Dusthana association |

### C.4 Exchange Involving Trikona Lords

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Trikona lord exchanged with Kendra lord = Maha Parivartana | BPHS Ch.33 | CLASSICAL_PRIMARY | Same as above (bidirectional) |
| Trikona lord exchanged with Trikona lord = Kahala | BPHS Ch.26 | CLASSICAL_PRIMARY | Auspicious but limited scope |
| Trikona lord exchanged with Dusthana lord = Dainya | BPHS Ch.26 | CLASSICAL_PRIMARY | Fortune undermined by Dusthana |

### C.5 Exchange Involving Lagna Lord

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Lagna lord exchanged with Kendra/Trikona lord = powerful Raja Yoga | BPHS Ch.33 | CLASSICAL_PRIMARY | Lagna lord is both Kendra and Trikona |
| Lagna lord exchanged with 10th lord = Raja Yoga | BPHS Ch.33 | CLASSICAL_PRIMARY | Self + career connection |
| Lagna lord exchanged with 9th lord = Raja Yoga | BPHS Ch.33 | CLASSICAL_PRIMARY | Self + fortune connection |

### C.6 Exchange Strength Based on Dignity

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Both planets in exaltation in exchanged signs = maximum strength | BPHS Ch.26 | CLASSICAL_PRIMARY | Highest dignity in exchange |
| One planet debilitated in exchanged sign = weakened exchange | BPHS Ch.26 | CLASSICAL_PRIMARY | Neecha Bhanga can restore |
| Both planets in own signs (mutual reception) = very strong | BPHS Ch.26 | CLASSICAL_PRIMARY | Each planet fully empowered |

### C.7 Exchange Cancellation Conditions

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Exchange cancelled if one planet combust | BPHS Ch.26 | CLASSICAL_PRIMARY | Combustion breaks the exchange bond |
| Exchange weakened if one planet retrograde | BPHS Ch.26 | COMMENTARY_DEPENDENT | Retrograde modifies exchange effects |
| Exchange broken if planets too far apart in sign | BPHS Ch.26 | COMMENTARY_DEPENDENT | Some texts require close degrees |

### C.8 Multiple Simultaneous Exchanges

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Multiple exchanges = cumulative effect | BPHS Ch.26 | CLASSICAL_PRIMARY | Each exchange adds connection strength |
| Chain of exchanges (A↔B↔C) = extended connection | BPHS Ch.26 | COMMENTARY_DEPENDENT | Less powerful than direct exchange |

### C.9 Exchange vs Simple Aspect Distinction

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Exchange is stronger than aspect alone | BPHS Ch.26 | CLASSICAL_PRIMARY | "Major Sambandha" classification |
| Exchange creates mutual ownership binding | BPHS Ch.26 | CLASSICAL_PRIMARY | Deeper connection than aspect |
| Exchange + aspect = extremely strong connection | BPHS Ch.26 | CLASSICAL_PRIMARY | Combined Sambandhas |

---

## Section D: Dispositorship (Swakshetra)

### D.1 Classical Definition

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Planet A in sign owned by Planet B → B is dispositor of A | BPHS Ch.3 | CLASSICAL_PRIMARY | Dispositor = sign lord of occupied sign |
| Dispositorship is the "chain of command" | BPHS Ch.3 | COMMENTARY_DEPENDENT | Modern interpretation of classical concept |

### D.2 Dispositor Chain

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| A in B's sign, B in C's sign = chain A→B→C | BPHS Ch.3 | CLASSICAL_PRIMARY | Follow the sign lords |
| Chain terminates when planet in own sign (final dispositor) | BPHS Ch.3 | CLASSICAL_PRIMARY | Planet ruling its own sign stops the chain |
| Final dispositor has tremendous power | BPHS Ch.3 | COMMENTARY_DEPENDENT | Modern synthesis; classical texts emphasize dignity |
| Chain can cycle back (A→B→C→A) | BPHS Ch.3 | CLASSICAL_PRIMARY | Circular chains possible |

### D.3 Dispositor + Disposited Relationship Strength

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Dispositor in exaltation = strong influence on disposited planet | BPHS Ch.3 | CLASSICAL_PRIMARY | Strong dispositor empowers dependent |
| Dispositor debilitated = weak influence on disposited planet | BPHS Ch.3 | CLASSICAL_PRIMARY | Weak dispositor undermines dependent |
| Dispositor combust = diminished influence | BPHS Ch.3 | CLASSICAL_PRIMARY | Sun's proximity weakens dispositor |

### D.4 Mutual Reception (Swakshetra Yoga)

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| A in B's sign AND B in A's sign = mutual reception | BPHS Ch.26 | CLASSICAL_PRIMARY | This IS Parivartana (exchange) |
| Mutual reception = strongest dispositorship bond | BPHS Ch.26 | CLASSICAL_PRIMARY | Both planets simultaneously dispositor and disposit |
| Same-sign mutual reception = each planet disposes itself | BPHS Ch.26 | CLASSICAL_PRIMARY | Trivial case (planet in own sign) |

### D.5 Dispositor Dignity Modification

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Dispositor's dignity modifies all planets it disposes | BPHS Ch.3 | CLASSICAL_PRIMARY | Chain influence carries dignity effects |
| Multiple planets disposited by same planet = shared influence | BPHS Ch.3 | CLASSICAL_PRIMARY | Dispositor becomes "final authority" for those planets |
| Dispositor in Kendra/Trikona = strong dispositor | BPHS Ch.3 | CLASSICAL_PRIMARY | House placement affects dispositor power |

---

## Section E: Named Classical Yogas

### E.1 Raja Yogas (Kendra-Trikona Combinations)

| Yoga | Condition | Source | Classification |
|------|-----------|--------|----------------|
| Basic Raja Yoga | Kendra lord connected to Trikona lord (conjunction/aspect/exchange) | BPHS Ch.33 | CLASSICAL_PRIMARY |
| Maha Raja Yoga | Lagna lord + 10th lord connected in Kendra/Trikona | BPHS Ch.33 | CLASSICAL_PRIMARY |
| Amala Raja Yoga | Natural benefic in 10th from Lagna or Moon | Phaladeepika Ch.6 | CLASSICAL_PRIMARY |
| Viparita Raja Yoga | Dusthana lords (6/8/12) exchange or conjoin | BPHS Ch.33 | CLASSICAL_PRIMARY |
| Neecha Bhanga Raja Yoga | Debilitated planet's weakness cancelled by classical conditions | Phaladeepika Ch.7 | CLASSICAL_PRIMARY |

### E.2 Dhana Yogas (Wealth Combinations)

| Yoga | Condition | Source | Classification |
|------|-----------|--------|----------------|
| Basic Dhana Yoga | 2nd lord connected to 11th lord | BPHS Ch.33 | CLASSICAL_PRIMARY |
| Extended Dhana Yoga | 2nd, 5th, 9th, 11th lords interconnected | Phaladeepika Ch.6 | CLASSICAL_PRIMARY |
| Lakshmi Yoga | 9th lord + Venus in own/exaltation in Trikona/Kendra | Phaladeepika Ch.6 | CLASSICAL_PRIMARY |
| Dhana Yoga with Kendra connection | 2nd/11th lords also ruling Kendra | BPHS Ch.33 | CLASSICAL_PRIMARY |

### E.3 Neecha Bhanga (Cancellation of Debilitation)

| Condition | Source | Classification | Notes |
|-----------|--------|----------------|-------|
| 1. Planet in exaltation aspects debilitated planet | Phaladeepika Ch.7 | CLASSICAL_PRIMARY | Exalted planet's aspect restores |
| 2. Planet in own sign aspects debilitated planet | Phaladeepika Ch.7 | CLASSICAL_PRIMARY | Own-sign planet's aspect restores |
| 3. Debilitated planet's dispositor is in Kendra from Lagna/Moon | Phaladeepika Ch.7 | CLASSICAL_PRIMARY | Strong dispositor cancels |
| 4. Debilitated planet is in Kendra from Lagna/Moon | Phaladeepika Ch.7 | CLASSICAL_PRIMARY | Kendra placement cancels |
| 5. Debilitated planet's dispositor aspects it | Phaladeepika Ch.7 | CLASSICAL_PRIMARY | Dispositor's aspect restores |
| 6. Planet exalted in Navamsa (D9) | Phaladeepika Ch.7 | COMMENTARY_DEPENDENT | Divisional chart confirmation |
| 7. Retrograde debilitated planet | BPHS Ch.3 | COMMENTARY_DEPENDENT | Retrograde restores strength |

### E.4 Vipareeta Raja Yoga

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Lords of 6, 8, 12 conjoin or exchange = Vipareeta Raja Yoga | BPHS Ch.33 | CLASSICAL_PRIMARY | Dusthana lords neutralize each other |
| Only conjunction or exchange (not aspect) counts | BPHS Ch.33 | CLASSICAL_PRIMARY | Stronger connection required |
| Results come through obstacles, crises, unconventional paths | BPHS Ch.33 | CLASSICAL_PRIMARY | Not straightforward success |

### E.5 Specific Planetary Combination Yogas

| Yoga | Planets | Condition | Source | Classification |
|------|---------|-----------|--------|----------------|
| Gajakesari | Jupiter + Moon | Jupiter in Kendra from Moon | BPHS Ch.33 | CLASSICAL_PRIMARY |
| Pancha Mahapurusha (Ruchaka) | Mars | Mars in own sign/exaltation in Kendra | BPHS Ch.33 | CLASSICAL_PRIMARY |
| Pancha Mahapurusha (Bhadra) | Mercury | Mercury in own sign/exaltation in Kendra | BPHS Ch.33 | CLASSICAL_PRIMARY |
| Pancha Mahapurusha (Hamsa) | Jupiter | Jupiter in own sign/exaltation in Kendra | BPHS Ch.33 | CLASSICAL_PRIMARY |
| Pancha Mahapurusha (Malavya) | Venus | Venus in own sign/exaltation in Kendra | BPHS Ch.33 | CLASSICAL_PRIMARY |
| Pancha Mahapurusha (Sasa) | Saturn | Saturn in own sign/exaltation in Kendra | BPHS Ch.33 | CLASSICAL_PRIMARY |
| Saraswati | Venus + Jupiter + Mercury | All in Kendra/Trikona/2nd; Jupiter dignified | Phaladeepika Ch.6 | CLASSICAL_PRIMARY |
| Srikantha | Lagna lord + Sun + Moon | All in Kendra/Trikona in exaltation/own/friendly | Phaladeepika Ch.6 | CLASSICAL_PRIMARY |

### E.6 Yoga Cancellation Conditions

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Yoga cancelled if key planet debilitated | BPHS Ch.33 | CLASSICAL_PRIMARY | Weak planet cannot deliver |
| Yoga cancelled if key planet combust | BPHS Ch.33 | CLASSICAL_PRIMARY | Combustion destroys capacity |
| Yoga cancelled if in Dusthana | BPHS Ch.33 | CLASSICAL_PRIMARY | Malefic house traps yoga energy |
| Yoga modified if malefic aspects yoga planets | BPHS Ch.33 | CLASSICAL_PRIMARY | Malefic interference weakens |
| Neecha Bhanga can restore cancelled yoga | Phaladeepika Ch.7 | CLASSICAL_PRIMARY | Cancellation can be cancelled |

### E.7 Yoga Strength Hierarchies

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Yogakaraka involvement > normal Kendra-Trikona | Phaladeepika Ch.6 | CLASSICAL_PRIMARY | Built-in Raja Yoga |
| Conjunction/Exchange > Mutual Aspect > One-way Aspect | BPHS Ch.33 | COMMENTARY_DEPENDENT | Connection type hierarchy |
| Both planets exalted > one exalted > both own sign | BPHS Ch.33 | CLASSICAL_PRIMARY | Dignity hierarchy |
| Yoga in Kendra/Trikona > Yoga in Upachaya > Yoga in Dusthana | BPHS Ch.33 | CLASSICAL_PRIMARY | House placement hierarchy |

### E.8 Multiple Yoga Interactions

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| Multiple Raja Yogas = cumulative effect | BPHS Ch.33 | CLASSICAL_PRIMARY | Each yoga adds power |
| Raja Yoga + Dhana Yoga = wealth and power | BPHS Ch.33 | CLASSICAL_PRIMARY | Combined results |
| Vipareeta Raja Yoga + normal Raja Yoga = mixed results | BPHS Ch.33 | COMMENTARY_DEPENDENT | Conflicting signals |

---

## Section F: Aspect Graph Construction Rules

### F.1 What Constitutes a Meaningful Relationship Chain

| Rule | Source | Classification | Notes |
|------|--------|----------------|-------|
| A→B valid if: conjunction, mutual aspect, or exchange | BPHS Ch.26 | CLASSICAL_PRIMARY | Three primary connection types |
| A→B→C valid if: each link satisfies classical predicates | BPHS Ch.26 | COMMENTARY_DEPENDENT | Chain must be unbroken |
| Chain valid only if intermediate planet is dignified | BPHS Ch.26 | COMMENTARY_DEPENDENT | Weak intermediate breaks chain |
| Chain valid only if intermediate planet not combust | BPHS Ch.26 | CLASSICAL_PRIMARY | Combustion breaks chain |

### F.2 Classical Predicates for Valid Yoga Structure

| Predicate | Source | Classification | Notes |
|-----------|--------|----------------|-------|
| Planets must be connected (not isolated) | BPHS Ch.33 | CLASSICAL_PRIMARY | Connection required |
| At least one connection must be Kendra-Trikona | BPHS Ch.33 | CLASSICAL_PRIMARY | For Raja Yoga specifically |
| Connection type must be conjunction, aspect, or exchange | BPHS Ch.26 | CLASSICAL_PRIMARY | Three valid types |
| Planets must not be combust | BPHS Ch.3 | CLASSICAL_PRIMARY | Combustion invalidates |
| Planets must not be debilitated (unless Neecha Bhanga) | BPHS Ch.3 | CLASSICAL_PRIMARY | Weakness invalidates |

### F.3 What Breaks an Aspect Chain

| Factor | Source | Classification | Notes |
|--------|--------|----------------|-------|
| Combustion of intermediate planet | BPHS Ch.3 | CLASSICAL_PRIMARY | Chain broken |
| Debilitation of intermediate planet (without Neecha Bhanga) | BPHS Ch.3 | CLASSICAL_PRIMARY | Chain weakened |
| Malefic aspect on intermediate planet | BPHS Ch.3 | CLASSICAL_PRIMARY | Chain tainted |
| Dusthana placement of conjunction | BPHS Ch.3 | CLASSICAL_PRIMARY | Chain trapped |
| Intercepted sign (some systems) | BPHS Ch.3 | UNSUPPORTED | Not in Parashari system |

### F.4 What Strengthens an Aspect Chain

| Factor | Source | Classification | Notes |
|--------|--------|----------------|-------|
| Dignity of all planets in chain | BPHS Ch.3 | CLASSICAL_PRIMARY | Strength amplification |
| Kendra/Trikona involvement | BPHS Ch.33 | CLASSICAL_PRIMARY | Power houses enhance |
| Benefic aspects on chain planets | BPHS Ch.3 | CLASSICAL_PRIMARY | Benefic influence strengthens |
| Mutual exchange within chain | BPHS Ch.26 | CLASSICAL_PRIMARY | Strongest bond |
| Yogakaraka planet in chain | Phaladeepika Ch.6 | CLASSICAL_PRIMARY | Built-in Raja Yoga |

---

## Section G: Architectural Impact Assessment

### G.1 Existing JRE Capabilities

| Capability | JRE Module | Covers | Missing |
|------------|------------|--------|---------|
| Standard aspect computation (7th house) | JRE-012 (drik/models.py) | ✅ DEFAULT_ASPECT_HOUSES with 7th for all planets | — |
| Special aspects (Mars 4/8, Jupiter 5/9, Saturn 3/10) | JRE-012 (drik/models.py) | ✅ Mars: (4,7,8), Jupiter: (5,7,9), Saturn: (3,7,10) | — |
| Aspect direction (applying/separating) | JRE-012 (drik/models.py) | ✅ AspectDirection enum with APPLYING/SEPARATING/EXACT | — |
| Aspect orb detection | JRE-012 (drik/models.py) | ✅ DEFAULT_ORB_DEG = 6.0, orb_deg field | — |
| Conjunction detection (same sign) | JRE-003 (jyotish/models.py) | ✅ PairGeometry.same_rashi, conjunction fields | — |
| Exchange detection | JRE-013 (yoga/service.py) | ✅ ConnectionType.EXCHANGE in _detect_connection | — |
| Basic Raja Yoga detection | JRE-013 (yoga/service.py) | ✅ _eval_raja method | — |
| Basic Dhana Yoga detection | JRE-013 (yoga/service.py) | ✅ _eval_dhana method | — |
| Connection map building | JRE-013 (yoga/service.py) | ✅ _build_connection_map method | — |
| Strength modifier from Shadbala | JRE-013 (yoga/service.py) | ✅ _compute_strength method | — |
| Natural benefic/malefic classification | Knowledge layer | ✅ PLANET_NATURES in schema.py | — |
| Dignity states | Knowledge layer | ✅ DIGNITY_STATES in schema.py | — |
| Aspect strength (quarter/half/three-quarter/full) | Knowledge layer | ✅ ASPECT_POSITION_STRENGTHS in schema.py | — |
| Special aspect positions | Knowledge layer | ✅ SPECIAL_ASPECT_POSITIONS in schema.py | — |
| Pair fact vocabulary | Knowledge layer | ✅ pair(<A>,<B>).conjunction/aspects/aspect_strength | — |

### G.2 Capabilities NOT Present (Gaps)

| Gap | Description | Priority |
|-----|-------------|----------|
| **Aspect strength gradation in JRE-012** | DrikResult does not include strength (1/4, 1/2, 3/4, full) — only the knowledge layer computes it at rule evaluation time | HIGH |
| **Parivartana classification** | No distinction between Maha/Kahala/Dainya Parivartana | HIGH |
| **Dispositor chain computation** | No logic to trace sign lord chains | MEDIUM |
| **Final dispositor identification** | No logic to find planet in own sign that terminates chains | MEDIUM |
| **Neecha Bhanga detection** | No logic to detect debilitation cancellation (7 conditions) | HIGH |
| **Multi-planet conjunction hierarchy** | No logic to determine which planet dominates in 3+ conjunction | MEDIUM |
| **Aspect chain validity** | No logic to validate A→B→C chains | MEDIUM |
| **Combustion detection** | No logic to detect planet combustion | HIGH |
| **Retrograde modification of aspects** | No logic to modify aspect results based on retrograde status | MEDIUM |
| **Yoga cancellation detection** | No logic to detect when yoga conditions are cancelled | HIGH |
| **Yoga strength hierarchy** | No logic to rank multiple yogas by strength | LOW |
| **Aspect direction asymmetry** | JRE-012 treats aspects as symmetric; classical texts are asymmetric | MEDIUM |

### G.3 JRS Knowledge Only Findings

| Finding | Type | Notes |
|---------|------|-------|
| Five major Sambandhas (exchange, mutual aspect, dispositorship, square, trine) | Interpretive/Doctrinal | Classification framework |
| Aspect quality determined by aspecting planet's nature | Interpretive/Doctrinal | Benefic aspects good, malefic aspects evil |
| Yogakaraka concept | Interpretive/Doctrinal | Planet ruling both Kendra and Trikona |
| Chain of command through dispositorship | Interpretive/Doctrinal | Hierarchical influence model |

---

## Section H: Four-Fold Distinction Mapping

| Configuration | Primary Source | Classification | Four-Fold Category | Existing JRE? | Requires Relationship Graph? |
|---------------|----------------|----------------|---------------------|---------------|------------------------------|
| Conjunction = same sign | BPHS Ch.3 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-003) | No |
| 7th aspect = full for all planets | BPHS Ch.26 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-012) | No |
| Mars special aspects 4/8 | BPHS Ch.26 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-012) | No |
| Jupiter special aspects 5/9 | BPHS Ch.26 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-012) | No |
| Saturn special aspects 3/10 | BPHS Ch.26 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-012) | No |
| Aspect strength gradation (1/4, 1/2, 3/4, full) | BPHS Ch.26 v.2-5 | CLASSICAL_PRIMARY | YOGA_STRENGTH | Partial (knowledge layer only) | No |
| Exchange = Parivartana | BPHS Ch.26 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-013) | No |
| Maha Parivartana (Kendra-Trikona exchange) | BPHS Ch.26 | CLASSICAL_PRIMARY | YOGA_FORMATION | No | No |
| Kahala Parivartana (2/5/9/11 exchange) | BPHS Ch.26 | CLASSICAL_PRIMARY | YOGA_FORMATION | No | No |
| Dainya Parivartana (Dusthana exchange) | BPHS Ch.26 | CLASSICAL_PRIMARY | YOGA_FORMATION | No | No |
| Dispositor = sign lord of occupied sign | BPHS Ch.3 | CLASSICAL_PRIMARY | YOGA_FORMATION | No | **Yes** |
| Dispositor chain tracing | BPHS Ch.3 | CLASSICAL_PRIMARY | YOGA_FORMATION | No | **Yes** |
| Final dispositor identification | BPHS Ch.3 | COMMENTARY_DEPENDENT | YOGA_FORMATION | No | **Yes** |
| Mutual reception = exchange | BPHS Ch.26 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-013) | No |
| Benefic aspect = auspicious | BPHS Ch.26 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | No |
| Malefic aspect = challenging | BPHS Ch.26 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | No |
| Exalted planet's aspect strongest | BPHS Ch.26 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | No |
| Debilitated planet's aspect weakest | BPHS Ch.26 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | No |
| Combustion weakens aspect | BPHS Ch.3 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | No |
| Retrograde enhances aspect | BPHS Ch.26 | COMMENTARY_DEPENDENT | YOGA_STRENGTH | No | No |
| Neecha Bhanga (7 conditions) | Phaladeepika Ch.7 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | No |
| Raja Yoga = Kendra-Trikona connection | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-013) | No |
| Dhana Yoga = 2nd-11th connection | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-013) | No |
| Gajakesari = Jupiter in Kendra from Moon | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-013) | No |
| Pancha Mahapurusha = planet in own sign in Kendra | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_FORMATION | No | No |
| Vipareeta Raja Yoga = Dusthana lords exchange/conjoin | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_FORMATION | Yes (JRE-013) | No |
| Aspect chain A→B→C validity | BPHS Ch.26 | COMMENTARY_DEPENDENT | YOGA_FORMATION | No | **Yes** |
| Chain broken by combustion/debilitation | BPHS Ch.3 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | **Yes** |
| Chain strengthened by dignity/Kendra-Trikona | BPHS Ch.3 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | **Yes** |
| Multiple yogas cumulative | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_STRENGTH | No | No |
| Dasha timing for yoga manifestation | BPHS Ch.33 | COMMENTARY_DEPENDENT | YOGA_MANIFESTATION | No | No |
| Raja Yoga outcome = power, authority | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_OUTCOME | No (JRS only) | No |
| Dhana Yoga outcome = wealth | BPHS Ch.33 | CLASSICAL_PRIMARY | YOGA_OUTCOME | No (JRS only) | No |

---

## Section I: Explicit Exclusion List

### I.1 Modern Interpretations (NOT Classical)

| Concept | Why Excluded | Source of Exclusion |
|---------|--------------|---------------------|
| "Conjunction orb in degrees" | Parashari uses sign-based conjunction, not degree-based orbs | BPHS Ch.3 |
| "Sextile aspect = positive" | Western aspect; not in classical Jyotish | BPHS Ch.26 |
| "Square aspect = challenging" | Western aspect; not in classical Jyotish | BPHS Ch.26 |
| "Quincunx/inconjunct = adjustment" | Western aspect; not in classical Jyotish | BPHS Ch.26 |
| "Semi-sextile = minor tension" | Western aspect; not in classical Jyotish | BPHS Ch.26 |

### I.2 Pop-Astrology Claims (NOT Supported)

| Concept | Why Excluded | Source of Exclusion |
|---------|--------------|---------------------|
| "Mercury retrograde = communication issues" | No classical basis for this specific claim | BPHS mentions retrograde but not "communication issues" |
| "Full Moon conjunction = emotional intensity" | No classical basis | BPHS describes Moon phases for timing |
| "Saturn return = maturity" | Modern pop-astrology | Classical texts describe Saturn periods as challenging |
| "Rahu/Ketu = karmic debt" | New Age interpretation | Classical texts describe them as malefics |

### I.3 Modern System Inventions (NOT Classical)

| Concept | Why Excluded | Source of Exclusion |
|---------|--------------|---------------------|
| Chiron (asteroid) aspects | Not in classical Jyotish | BPHS uses traditional 7 planets only |
| Pluto aspects | Not in classical Jyotish | Classical texts use traditional 7 planets |
| North Node/South Node aspects | Modern overlay | Classical texts describe Rahu/Ketu as malefics |
| Uranus/Neptune aspects | Not in classical Jyotish | Classical texts use traditional 7 planets |

### I.4 Unsupported Hellenistic Fringe

| Concept | Why Excluded | Source of Exclusion |
|---------|--------------|---------------------|
| "Void of Course Moon" | Not in classical Indian texts | Hellenistic concept not adopted in Jyotish |
| "Antiscia" | Not used in classical Jyotish | Hellenistic technique |
| "Arabic Parts" | Not in classical Indian texts | Islamic astrology influence |
| "Decan/dodecatemoria" | Not in classical Parashari | Hellenistic division system |

### I.5 Tajika System (Different Tradition)

| Concept | Why Excluded | Source of Exclusion |
|---------|--------------|---------------------|
| Tajika aspects (applying/separating by degree) | Different system from Parashari | Tajika Neelakanthi |
| Tajika aspect classification (openly friendly/inimical) | Different framework | Tajika system |
| Varshaphal (annual chart) aspects | Different application | Tajika system |

### I.6 Jaimini System (Different Tradition)

| Concept | Why Excluded | Source of Exclusion |
|---------|--------------|---------------------|
| Jaimini sign aspects (chara/sthira/dvisvabhava) | Different system from Parashari | Jaimini Sutras |
| Jaimini karakas (Atmakaraka etc.) | Different framework | Jaimini Sutras |
| Argala/obstruction system | Jaimini-specific technique | Jaimini Sutras |

---

## Summary of Findings

### What the Classical Texts Explicitly State

1. **Conjunction is sign-based** — same Rashi, no degree orb
2. **All planets aspect the 7th** with full strength; special aspects for Mars (4/8), Jupiter (5/9), Saturn (3/10)
3. **Aspect strength varies** by position: 1/4 at 3rd/10th, 1/2 at 5th/9th, 3/4 at 4th/8th, full at 7th
4. **Exchange (Parivartana)** has three types: Maha (Kendra-Trikona), Kahala (auspicious houses), Dainya (Dusthana)
5. **Dispositorship** follows sign lord chains; final dispositor in own sign has power
6. **Neecha Bhanga** has 7 classical conditions for debilitation cancellation
7. **Five major Sambandhas**: exchange, mutual aspect, dispositorship, square, trine
8. **Aspect chains** valid when intermediate planets dignified and not combust
9. **Yoga strength** depends on dignity, house placement, and benefic/malefic modification

### What is NOT Explicitly Stated (Requiring Interpretation)

1. **Degree-based proximity within sign** — classical texts use sign boundaries
2. **Chain of command through dispositorship** — modern synthesis
3. **Aspect direction asymmetry** — some texts imply it but not fully formalized
4. **Yoga strength hierarchy** — implied but not explicitly ranked
5. **Multi-planet conjunction dominance** — mentioned but not systematized

### Architectural Impact

The existing JRE engines correctly implement the **structural detection** (YOGA_FORMATION) but lack:
- **YOGA_STRENGTH** modifications (dignity, combustion, retrograde, aspect gradation)
- **Parivartana classification** (Maha/Kahala/Dainya)
- **Dispositor chain** computation
- **Neecha Bhanga** detection
- **Combustion** detection
- **Aspect chain validity** checking

These gaps represent the difference between "connections exist" and "connections produce meaningful results."

---

## Recommendation

**DO NOT proceed to RI-010C (implementation) until:**

1. This research report is reviewed and approved
2. The architectural gaps are prioritized
3. The four-fold distinction framework is validated against the JRE/JRS separation
4. The exclusion list is confirmed as comprehensive
5. The relationship graph requirement (for dispositor chains and aspect chains) is evaluated

**Next Step:** Human review of this report before any implementation decisions.
