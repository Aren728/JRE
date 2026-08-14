# JRE-004 Recovery — VALIDATOR Report

- Date: 2026-08-13
- Scope: re-validation of the JRE-004 recovery after the original VALIDATOR
  FAIL (14/16 incorrect citations) and the recovery CODING/QA stages.
- Verdict: **VALIDATOR PASS**

The original VALIDATOR's three blocking defect classes are all resolved:
(1) all 12 ACTIVE rule citations point to verified locations supported by
committed evidence excerpts; (2) the two semantic defects (Gaja-Kesari and
Sakata definitions) are corrected to the verified classical readings;
(3) the fabricated Y4→Y1 combust-Moon exception is removed. The four
NEEDS-RESEARCH rules remain INACTIVE with honest, unverified commentary — no
fabricated replacement citations.

## 1. Citation validation table (16 rules)

Every citation was re-checked **against the actual published edition texts**
(Santhanam BPHS, Sastri Bṛhat Jātaka / Jātaka Pārijāta, Kapoor Phaladīpikā,
Raman Praśna Mārgam — the downloaded full texts) **and** against the committed
evidence excerpts at `datasets/validation/knowledge/`. All 10 excerpt files
were verified as genuine quotes (normalized/fragment substring matches against
the primary texts; the 3 with OCR artifacts or deliberate `...` elisions were
verified fragment-by-fragment). A citation was never accepted merely because
its source ID resolves or its chapter/verse is syntactically valid.

| Rule | Citation | Verse content vs rule | Verdict |
|---|---|---|---|
| `bphs.gajakesari.1` (Y1) | BPHS ch. 36 v. 3-4 | Jupiter in angle from lagna or Moon, conjunct/aspected by benefice, avoiding debilitation/combustion/inimical sign — rule encodes all limbs (kendra from lagna **or** Moon; benefic conjunction or aspect; not combust; dignity excludes DEBILITATED/ENEMY) | **VERIFIED** |
| `jataka-parijata.gajakesari.5` (Y5) | JP Adhyāya VII sloka 116 | (1) Jupiter kendra from Moon; (2) Moon aspected by Venus/Jupiter/Mercury, "without being depressed or obscured by the Sun" — rule encodes both arms; **VALIDATOR correction:** the second arm now also enforces the not-debilitated limb | **VERIFIED** (after correction) |
| `phaladeepika.kesari.7` | Phaladīpikā ch. 6 (following v. 14) | "Moon in a Kendra position to Jupiter" — rule: `relative_house(MOON, JUPITER) ∈ {1,4,7,10}` | **VERIFIED** |
| `phaladeepika.sakata.3` | Phaladīpikā ch. 6 (following v. 14) | "Moon in the 12th, 8th or 6th house from Jupiter" — rule matches, correct reference body (Jupiter, not lagna) | **VERIFIED** |
| `phaladeepika.sakata-cancellation.8` | Phaladīpikā ch. 6 (following v. 14) | "cancelled if the Moon be in a Kendra position from the Ascendant (lagna)" — rule: Moon kendra from LAGNA, declared `exception_for` Sakata | **VERIFIED** |
| `bphs.mars-opposition.1` | BPHS ch. 26 v. 2-5 | "All planets aspect the 7th fully" — opposition = full 7th aspect | **VERIFIED** |
| `bphs.jupiter-aspect.2` | BPHS ch. 26 v. 2-5 | Jupiter special full aspects on 5th/9th — rule matches | **VERIFIED** |
| `bphs.saturn-aspect.3` | BPHS ch. 26 v. 2-5 | Saturn special full aspects on 3rd/10th — rule matches | **VERIFIED** |
| `phaladeepika.aspect-strength.4` | Phaladīpikā ch. 2 (note following v. 23) | ¼ on 3rd/10th, ½ on 5th/9th, ¾ on 4th/8th, full on 7th — rule matches | **VERIFIED** |
| `bphs.karaka.jupiter.1` | BPHS ch. 32 v. 31-34 | Significator list: Jupiter = 2nd, 5th, 9th, 11th — **VALIDATOR correction:** conclusion completed to the full set | **VERIFIED** (after correction) |
| `bphs.karaka.venus.2` | BPHS ch. 32 v. 31-34 | Venus = 7th — rule matches | **VERIFIED** |
| `bphs.bhava-9.3` | BPHS ch. 20 v. 1-2 | Jupiter in the 9th contributes fortune; **VALIDATOR correction:** conclusion scoped explicitly (the verse's "extremely fortunate" also requires 9th lord in angle + strong ascendant lord) | **VERIFIED** (after correction) |
| `bphs.budhaditya.2` | (BPHS ch. 25 v. 24 retained) | No Sun-Mercury "Budha-Aditya" yoga found in the text — **INACTIVE**, commentary records the research status | NOT VERIFIED (INACTIVE) |
| `prasna-marga.moon-lagna.6` | (PM ch. 1 v. 9 retained) | Ch. 1 v. 9 is the Pramana/Phala divisions — **INACTIVE**, commentary records the mismatch | NOT VERIFIED (INACTIVE) |
| `prasna-marga.chandra-venus.5` | (PM ch. 3 v. 11 retained) | Ch. 3 v. 11 is Lagna Sphuta/Kunda — **INACTIVE**, commentary records the mismatch | NOT VERIFIED (INACTIVE) |
| `brihat-jataka.seventh-lord.4` | (BJ ch. 9 v. 5 retained) | Ch. IX is Ashtakavarga — **INACTIVE**, commentary records the mismatch | NOT VERIFIED (INACTIVE) |

Result: **12 VERIFIED ACTIVE, 4 NOT-VERIFIED INACTIVE, 0 INCORRECT.**

## 2. Bibliographic validation

- **PASS with one VALIDATOR correction.** All 7 source records are real
  works. Jātaka Pārijāta translator corrected to V. Subrahmanya Sastri 1932
  (consistent with the 1932 translation used and bibliographies). Phaladīpikā
  translator corrected to Dr. G. S. Kapoor — **confirmed by the scan's title
  page** ("English Translation, Commentary and annotation by Dr. G. S.
  Kapoor"). Ranjan Publications confirmed by multiple bibliographies.
- **Correction:** the QA-set `year: "2001"` for `kapoor-2001` is **not
  supported** — the verification scan is undated and Ranjan printings are
  attested from 2004 onward (2004/2005/2014/2017). The year was reverted to
  unknown with a notes explanation (sources catalog v1.0.2) and the two
  Phaladīpikā evidence headers updated accordingly. This removes an
  unsupported bibliographic claim (STRICT RULE: no fabricated verification).

## 3. Provenance

- Canonical strings resolve for all 16 rules; corrected editions echo
  correctly ("Jataka Parijata ch.7 v.116 (tr. V. Subrahmanya Sastri 1932)",
  "Phaladeepika ch.6 v.14 (tr. Dr. G. S. Kapoor)").
- All 16 rules at "full" completeness; per-fact provenance for all 10 facts
  tables (source/chapter/verse/edition). Unknown-edition and unknown-source
  references rejected at load. Checksums enforced (tampered copies rejected).

## 4. Tradition / profiles

Unchanged from the original VALIDATOR PASS: all 7 profiles match SPEC §14
(priorities + conflict policies); the Y1↔Y5 Gaja-Kesari conflict is resolved
by profile source-priority under FIRST_WINS and is recorded, never silent.

## 5. Credibility review

0.55/0.30/0.15 constants unchanged and consistent with SPEC §22.2; formula
matches §10.2 (Y1: 0.89 verified). Reported as a domain-review item only; not
changed (specification-compliant).

## 6. Gaja-Kesari / Sakata (highest-priority semantic check)

- **Distinct formulations preserved**: BPHS ch. 36 (Jupiter kendra from lagna
  or Moon + benefic conjunction/aspect + dignity/combustion limits), Jātaka
  Pārijāta VII.116 (two forms), Phaladīpikā Kesari (Moon kendra from Jupiter)
  and Sakata (Moon 6/8/12 from Jupiter). No collapse into one definition.
- **Y1↔Y5 conflict** symmetric and functional (both fire on the shared
  Jupiter-kendra-from-Moon case; profile picks one winner, recorded).
- **Fabricated Y4→Y1 exception: gone** (no such rule; no exception targeting
  Y1).
- **Sakata reference body: Jupiter** (correct per Phaladīpikā).
- **Cancellation**: encoded only where the text supports it (Moon in kendra
  from the lagna cancels Sakata; no other cancellation invented).
- **VALIDATOR correction:** Y5 second form now also requires the Moon
  not-debilitated (the sloka's "without being depressed or obscured by the
  Sun"), closing a rule-vs-verse overreach found during re-validation.

## 7. Architecture / isolation

- `git diff` on `src/astronomy` and `src/jyotish`: **empty** — JRE-002 and
  JRE-003 untouched by the recovery.
- Dependency direction verified: knowledge imports stdlib + the one
  ADR-007-sanctioned `jyotish` public-API touch (synthesis normalization);
  no astronomy/swisseph imports; no reverse dependencies.
- No prediction logic (static gate); deterministic behavior (in-process +
  cross-process byte identity).
- ADR-012 accurately describes the implementation (minor wording fix applied:
  config pin key is unpinned by default, not pinned to 1.0.0; conformance
  test asserting schema constants == facts tables added to match the ADR's
  stated design).

## 8. Tests / lint / types

- **pytest: 889 passed** (unit + integration).
- **ruff: clean**; **mypy: clean** (47 files, strict).
- Cross-process determinism, golden v2.0.0, catalog/version echo, tampered-
  checksum rejection, and wrong-pin rejection all verified. Performance
  limits unchanged (synthesis p95 < 50 ms, catalog load < 100 ms).

## 9. Findings

| # | Finding | Severity | Disposition |
|---|---|---|---|
| 1 | Y5 second form omitted the not-debilitated limb the sloka requires | Moderate (rule-vs-verse overreach) | **Corrected** (condition + regression test) |
| 2 | `karaka.jupiter.1` conclusion listed 5th/9th only; its own evidence file maps 2/5/9/11 | Low (data completeness) | **Corrected** (conclusion + significations) |
| 3 | `bhava-9.3` conclusion attributed "extremely fortunate" to Jupiter-in-9th alone | Low (fidelity) | **Corrected** (conclusion scoped per verse) |
| 4 | Phaladīpikā `kapoor-2001` year "2001" (QA-set) unsupported by evidence | Low (bibliographic) | **Corrected** (year → unknown, sources v1.0.2) |
| 5 | ADR-012 stated the facts pin as "1.0.0" and claimed a doctrine conformance test that did not exist | Low (docs) | **Corrected** (wording + added conformance test) |

All corrections are data/documentation-only, within the approved JRE-004
scope; none alters the specialist contract (grammar, precedence, conflict
semantics, synthesis pipeline unchanged) and none weakens a test — one
regression test was added.

## 10. Final recommendation

**MERGE-READY** after MERGE authorization. All original blocking findings
resolved; JRE-002/JRE-003 isolated; all tests/lint/types/determinism green;
the four research rules remain inactive; no fabricated knowledge remains
active.
