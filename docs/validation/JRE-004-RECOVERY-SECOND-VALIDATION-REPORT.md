# JRE-004 Recovery — Second VALIDATOR Report (natural_friendship correction)

**Date:** 2026-08-13 · **Verdict: VALIDATOR PASS** · **MERGE remains blocked** (awaits explicit authorization).

## 1. Background

The first recovery VALIDATOR pass reported a **FAIL**: the committed
`natural_friendship` table in `datasets/knowledge/facts/facts.json` was
incorrect for 6 of 7 planets against BPHS ch. 3 v. 55 (Santhanam ed.) — the
planet itself was listed in its own friends (Moon even as its own enemy), and
both-conflict cases (including exaltation-lord conflicts) were not resolved
to NEUTRAL, directly contradicting the edition's own worked example ("Saturn
becomes equal to Mars"). The defect corrupted the derived `dignity` fact path
for Moon-in-Tula, Mars-in-Kumbha and Venus-in-Dhanusha. The queue was
regressed to a correction-required state.

## 2. Correction applied (within approved scope; no contract change)

| File | Change |
|---|---|
| `datasets/knowledge/facts/facts.json` | `natural_friendship` rows corrected to the verified verse-55 reading; notes updated; checksum recomputed |
| `datasets/validation/knowledge/bphs-3-49-55-dignities.md` | reading note updated (self-exclusion; both→NEUTRAL incl. exaltation-lord conflicts) |
| `tests/unit/knowledge/test_facts.py` | value-level regression tests added (see §5) |

No FACT_VOCABULARY change. No `src/knowledge` engine change. No rule-catalog
change. No JRE-002 / JRE-003 change.

## 3. Corrected values (verified reading)

Friends = lords of the 2nd/4th/5th/8th/9th/12th from the planet's
moolatrikona **plus** the lord of its exaltation sign; enemies = lords of the
3rd/6th/7th/10th/11th; a planet on both lists is **NEUTRAL** (incl.
exaltation-lord conflicts); the planet itself is never listed.

| Planet | Friends | Enemies | Neutral |
|---|---|---|---|
| SUN | MOON, MARS, JUPITER | VENUS, SATURN | MERCURY |
| MOON | SUN, MERCURY | — | MARS, JUPITER, VENUS, SATURN |
| MARS | SUN, MOON, JUPITER | MERCURY | VENUS, SATURN |
| MERCURY | SUN, VENUS | MOON | MARS, JUPITER, SATURN |
| JUPITER | SUN, MOON, MARS | MERCURY, VENUS | SATURN |
| VENUS | MERCURY, SATURN | SUN, MOON | MARS, JUPITER |
| SATURN | MERCURY, VENUS | SUN, MOON, MARS | JUPITER |

## 4. Independent verification (this pass)

1. **Facts checksum** — recomputed with the project's canonical
   serialization (`canonical_catalog_json`): **OK** (`6668dc62…`).
2. **All 7 rows** — independently recomputed from the verse-55 reading and
   compared against the committed table: **all match** (SUN..SATURN OK).
3. **Pre-correction values would fail** the new full-table regression test on
   6/7 rows (the SUN row was already correct); the structural tests
   (self-exclusion, both→NEUTRAL, asymmetry) catch regressions independently
   of the full-table assertion.
4. **Rule catalogs untouched** — all three rule-catalog checksums still
   validate; 16 rules: **12 ACTIVE + 4 INACTIVE** (unchanged). The 12 ACTIVE
   citations remain VERIFIED; the 4 research rules remain INACTIVE and
   cannot fire.
5. **No new defects** — full matrix below.

## 5. Regression tests added (value-level, non-tautological)

- `test_natural_friendship_values_match_verse_55` — full-table assertion
  against an independently encoded `FRIENDSHIP_EXPECTED` literal.
- `test_natural_friendship_self_excluded` — no planet in its own lists.
- `test_natural_friendship_mutual_friendship` — SUN↔MOON, VENUS↔MERCURY.
- `test_natural_friendship_mutual_enmity` — SUN↔SATURN, SUN↔VENUS.
- `test_natural_friendship_asymmetry` — Venus enemy of Moon but Moon neutral
  to Venus; Mercury friend of Sun but Sun neutral to Mercury.
- `test_natural_friendship_mercury_moon_one_sided` — Mercury enemy of Moon,
  Moon friend of Mercury, Moon has no enemies.
- `test_natural_friendship_both_conflict_resolves_neutral` — Moon↔Venus,
  Mars↔Saturn (worked example), Venus↔Jupiter (exaltation-lord conflicts),
  Jupiter↔Saturn (2nd+11th).
- `test_natural_friendship_exaltation_lord_friend_when_unconflicted` — Sun↔Mars,
  Saturn↔Venus, Jupiter↔Moon.

## 6. Full matrix (after correction)

- `pytest tests/unit tests/integration` — **897 passed** (was 889; +8 new
  value-level tests)
- `ruff check src tests` — **clean**
- `mypy src/astronomy src/jyotish src/knowledge` — **no issues (47 files)**
- Cross-process determinism — **PASS**
- Golden v2.0.0 / serialization / catalog-integrity / vocabulary — **PASS**
- Performance tests — **PASS** (limits unchanged)
- `git diff -- src/astronomy` and `-- src/jyotish` — **empty** (untouched)

## 7. Verdict

**VALIDATOR PASS.** The sole remaining blocking defect is resolved with
verified values, a correct checksum, and protective value-level regression
tests. No fabricated knowledge remains active. JRE-002 and JRE-003 are
untouched. MERGE is **not** authorized and was not performed.
