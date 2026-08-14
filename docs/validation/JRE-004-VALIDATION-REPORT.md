# JRE-004 — Classical Knowledge & Rule Engine: Validation Report

- **Stage**: VALIDATOR
- **Date**: 2026-08-12
- **Validator principle applied**: the authored rule catalogs were NOT
  accepted because their provenance chains resolve internally. Every rule
  citation was independently checked against the actual published text of the
  cited edition (downloaded full texts of R. Santhanam's BPHS, V. Subrahmanya
  Sastri's Bṛhat Jātaka, V. Subrahmanya Sastri's Jātaka Pārijāta, the
  panchanga.lv Phaladīpikā PDF, and B.V. Raman's Praśna Mārgam). A citation
  counts as verified only when the cited chapter/verse actually contains the
  claimed rule.
- **Local material**: `datasets/validation/knowledge/` is **empty** — the
  reference excerpts mandated by TEST-PLAN §12 / SPEC §20 were never
  committed. Independent full texts were therefore fetched from archive.org
  etc. for this report. The committed excerpts must still be added at
  `datasets/validation/knowledge/` for reproducible future validation.

# Validation Summary

| Area | Result |
|---|---|
| Rule citations vs cited texts (16 rules) | **FAIL** — 14 INCORRECT, 2 NOT VERIFIED, 0 VERIFIED |
| Rule semantics (condition ↔ citation) | **FAIL** — Gaja-Kesari / Sakata conditions do not match the cited verses |
| Source registry metadata | **PASS (with 2 findings)** — 7 sources real; 2 edition records questionable |
| Provenance mechanics | **PASS** — canonical strings, completeness, checksums, enforcement all correct |
| Tradition profiles vs SPEC §14 | **PASS** — all 7 match the spec table exactly |
| Credibility/weight constants vs SPEC §10.2/§22.2 | **PASS (finding)** — formulas exact; constants are pinned proposals per spec |
| Architecture isolation | **PASS** — JRE-002/JRE-003 untouched; import graph acyclic; no prediction logic |
| Test suite + lint + types | **PASS** — 857 passed; ruff clean; mypy clean (3 packages) |

---

# 1. Rule citation validation (mandatory #1)

**Verdict: FAIL.** Verified against the actual cited-edition texts:

## 1.1 BPHS citations (Santhanam ed., archive.org full text)

| Rule | Authored citation | Actual location | Verdict |
|---|---|---|---|
| `bphs.gajakesari.1` | ch. 25 v. 12 | Gaja-Kesari is **ch. 36 v. 3–4** ("Should Jupiter be in an angle from the ascendant or from the Moon… Gaja Kesari yoga is caused"). Ch. 25 is "Effects of Non-Luminous Planets" (upagrahas). | **INCORRECT** |
| `bphs.budhaditya.2` | ch. 25 v. 24 | Ch. 25 is upagrahas; **Budha-Aditya is not in the Santhanam BPHS at all** (no Sun-Mercury yoga by this name in the full text). | **INCORRECT** |
| `bphs.mars-opposition.1` | ch. 26 v. 4 | Ch. 26 v. 2–5 state the planetary-aspect rules (all planets aspect the 7th fully; Saturn 3/10, Jupiter 5/9, Mars 4/8). v. 4 falls inside v. 2–5. | **AMBIGUOUS** — chapter right, verse only loosely right, content (opposition = 7th aspect) present |
| `bphs.jupiter-trine.2` | ch. 26 v. 8 | v. 6–8 are "ASPECTUAL EVALUATIONS" (Drishti Kona arithmetic). Jupiter's 5th/9th (trine) aspect is in v. 2–5 and v. 12. | **INCORRECT** (verse) |
| `bphs.karaka.jupiter.1` | ch. 3 v. 1 | Ch. 3 = "Planetary Characters"; v. 12–13 are the karaka-style governances (Sun soul, Moon mind…). House significators incl. Jupiter = 5th (progeny) / 9th (fortunes) are **ch. 32 v. 31–34**. | **INCORRECT** (chapter) |
| `bphs.karaka.venus.2` | ch. 3 v. 2 | Venus = 7th-house significator (wife) is ch. 32 v. 31–34; "arts" is not in ch. 3. | **INCORRECT** (chapter) |
| `bphs.bhava-9.3` | ch. 12 v. 8 | Ch. 12 = "Effects of First House"; v. 8 is "Child Birth". Ninth-house effects are **ch. 20 v. 1–2** ("Should Jupiter be in the 9th house… one will be extremely fortunate"). | **INCORRECT** (chapter + verse) |

## 1.2 Bṛhat Jātaka citations (Sastri ed., archive.org full text)

| Rule | Authored citation | Actual location | Verdict |
|---|---|---|---|
| `brihat-jataka.sakata.3` | ch. 20 v. 3 | Ch. XX = "Effect of Planets in the several Bhavas". **Sakata is a Nabhasa/Akriti yoga in ch. XII**: "Sakata… All planets should be in the 1st and the 7th houses" (opposition), NOT "Moon in 6/8/12 from lagna". | **INCORRECT** (chapter + content) |
| `brihat-jataka.saturn-aspect.3` | ch. 11 v. 9 | Ch. XI = Rajayogas. Planetary aspects = **ch. XIX** (aspects on the Moon in the 12 rasis, v. 1–3). | **INCORRECT** (chapter) |
| `brihat-jataka.seventh-lord.4` | ch. 9 v. 5 | Ch. IX = "On Ashtakavargas". Effects of planets in the 7th house are in **ch. XX** (Jupiter in the several houses v. 7, Venus v. 8). | **INCORRECT** (chapter) |

## 1.3 Jātaka Pārijāta citations (Sastri ed., archive.org full text)

| Rule | Authored citation | Actual location | Verdict |
|---|---|---|---|
| `jataka-parijata.gajakesari.5` | ch. 8 v. 6 | Gaja-Kesari is **Adhyaya VII sloka 116**: "When Jupiter occupies a kendra from the Moon… Again if the Moon be aspected by planets, Venus, Jupiter and Mercury without being depressed or obscured by the Sun." Ch. VIII v. 6 is Trigraha (3 planets in one bhava). | **INCORRECT** (chapter + verse) |
| `jataka-parijata.sextile.5` | ch. 12 v. 4 | Adhyaya XII = "Effects of the 3rd bhava". **No Venus-Jupiter sextile rule exists in JP**; the only "sextile" mention is a translator's note about Western principles in the Samudra/Chakra Akriti yogas. "Sextile" as such is a Western aspect concept. | **INCORRECT** (no such rule) |

## 1.4 Phaladīpikā citations (Mantreśvara, panchanga.lv PDF)

| Rule | Authored citation | Actual location | Verdict |
|---|---|---|---|
| `phaladeepika.direct-aspect.4` | ch. 2 v. 7 | Ch. 2 aspect verse (~v. 23 in this edition): "All planets cast a quarter glance at the 3rd and 10th, half at the 5th and 9th, three-quarters at the 4th and 8th, full at the 7th." **This directly contradicts the rule** "Bodies neither conjunct nor opposed do not directly aspect one another" — Phaladīpikā explicitly gives partial aspects. | **INCORRECT** (content contradicts source + wrong verse) |
| `phaladeepika.gajakesari.exc.4` | ch. 6 v. 12 | Ch. 6 v. 12 = AMALA yoga effects. Kesari (Gaja-Kesari) is **v. 14** ("the Moon is in a Kendra position to Jupiter"); Sakata is also v. 14 (Moon in 12/8/6 from Jupiter, cancelled if Moon in kendra from lagna). **No "combust Moon cancels Gaja-Kesari" verse exists.** | **INCORRECT** (wrong verse + content not found) |

## 1.5 Praśna Mārgam citations (B.V. Raman ed., archive.org full text)

| Rule | Authored citation | Actual content at that verse | Verdict |
|---|---|---|---|
| `prasna-marga.moon-lagna.6` | ch. 1 v. 9 | Ch. 1 stanza 9 = "Astrology can also be divided into two, viz., Pramana and Phala…" — no movable-sign-Moon rule. | **NOT VERIFIED** — no matching verse found |
| `prasna-marga.chandra-venus.5` | ch. 3 v. 11 | Ch. 3 stanza 11 = Kunda/Lagna Sphuta correction arithmetic; Chandra-Lagna content in the text concerns the 18 longevity yogas, not Venus in the 7th from Chandra Lagna. | **NOT VERIFIED** — no matching verse found |

## 1.6 Rule-semantics check (mandatory #4)

- **Gaja-Kesari (BPHS)**: the authored condition "Moon in a kendra (1/4/7/10) from lagna" omits Jupiter entirely. The cited verse (36.3–4) requires **Jupiter** in an angle from the ascendant or Moon, conjunct/aspected by a benefice, free of debilitation/combustion. The authored rule describes a different combination.
- **Gaja-Kesari (JP)**: authored "Moon conjunct Jupiter" is a subset of JP's actual "Jupiter in a kendra from the Moon" (conjunction is the 1st-from relationship, which IS a kendra), so the condition is a narrow-but-compatible reading; the citation is still wrong.
- **Sakata (BJ)**: authored "Moon in 6/8/12 from lagna, not retrograde" matches neither BJ (Akriti yoga: all planets in 1st & 7th) nor Phaladīpikā (Moon in 12/8/6 **from Jupiter**, cancelled if Moon in kendra from lagna). The "not retrograde" clause has no source found.
- **Combust-Moon exception**: no classical source found for "a combust Moon in the 1st house cancels Gaja-Kesari" at the cited location or anywhere in Phaladīpikā ch. 6.
- **Budha-Aditya**: the content (Sun-Mercury conjunction) is the well-known yoga, but the citation "BPHS ch. 25 v. 24" is fabricated — no such verse; not in the Santhanam BPHS.
- **Direct-aspect rule**: content contradicts Phaladīpikā (which assigns partial aspects), so the rule as written inverts the source.

**Consequence**: 14 of 16 citations are INCORRECT and 2 are NOT VERIFIED; 0 are VERIFIED. The two "flagship" catalogs (yoga/drishti/karaka) rest on mislocated or non-existent verses. The `conflicts_with` pair (Gaja-Kesari Y1↔Y5) and the `exception_for` chain (Y4→Y1) are therefore built on rules whose cited basis is wrong — the conflict/exception *machinery* is sound, but the underlying authored content is not.

---

# 2. Bibliographic validation (mandatory #2)

| Source | Record | Verdict |
|---|---|---|
| BPHS (Santhanam 2001) | Real; archive.org full text confirms translator/publisher/preface 1984, edition consistent | **VERIFIED** |
| Bṛhat Jātaka (Bhat 1995) | Real (Motilal Banarsidass); Sastri's edition confirms content | **VERIFIED** |
| Jātaka Pārijāta (Iyer 2003) | **Finding**: the standard JP English translation is V. Subrahmanya Sastri (Ranjan); N.P. Subramania Iyer is associated with *Kalaprakasika* and Lawley publications. The "N.P. Subramania Iyer 2003, Ranjan" JP record is **QUESTIONABLE** — no corroborating bibliographic source found. | **UNVERIFIED / QUESTIONABLE** |
| Phaladīpikā (Santhanam 2001) | Santhanam's translation exists; the panchanga.lv text used here is a different rendering | **VERIFIED (title)** — exact 2001 Ranjan details not independently confirmed |
| Sūrya Siddhānta (Burgess 1860 / Gangooly 1935) | Real, canonical editions | **VERIFIED** |
| Praśna Mārgam (Raman 1990) | Real (B.V. Raman translation, IBH/Ranjan printings) | **VERIFIED** |
| Sārāvalī (Santhanam 1999) | Real (Santhanam translation of Kalyana Varma's Saravali, Ranjan); some printings dated 1992 | **VERIFIED (translator/publisher)** — year 1999 not independently confirmed |

**Findings**: (F-2a) Jātaka Pārijāta edition record questionable; (F-2b) two edition years not independently confirmed. Source names/periods/authors are all consistent with standard bibliographies.

---

# 3. Provenance validation (mandatory #3)

- Canonical strings: format `"BPHS ch.25 v.12 (tr. R. Santhanam 2001)"` correct per SPEC §5.1; all 16 rules render deterministically.
- Completeness: all 16 rules are `full` (source+chapter+verse+edition) — mechanically correct, but **the referenced verse content does not match** for 14 of them (finding F-1).
- Source IDs: all 7 resolve; edition IDs: all resolve to the owning source.
- Checksums: all 4 catalogs verify (SHA-256 canonicalization correct); a tampered catalog is rejected (`CatalogIntegrityError`).
- Provenance enforcement: `enforce_provenance=True` rejects missing edition when chapter/verse present; `enforce_provenance=False` path tested.
- **Verdict: PASS** for mechanics; the content-level failure is F-1.

---

# 4. Tradition/profile validation (mandatory #5)

All 7 profiles match the SPEC §14 table exactly (source priority order, conflict policy, domains=None, passthrough allow-list). Default profile `bphs-classical` as specified. **PASS.**

---

# 5. Credibility review (mandatory #6)

- Constants in config: 0.55 / 0.30 / 0.15; completeness levels 1.0 / 0.85 / 0.7 / 0.5 — exactly as pinned in SPEC §10.2.
- Independent reimplementation: `credibility = round(0.55·(4/5) + 0.30·1.0 + 0.15·min(4/5,1), 4) = 0.86` matches engine output exactly; `effective_weight` and precedence-key echoes match.
- Per SPEC §22.2 these constants are **pinned proposals** that Validator/Architect may tune as a versioned decision; they never affect rule selection.
- **Verdict: PASS — no change made** (as instructed). Observation only: the constants are reasonable, unverifiable as "true" weights, and clearly documented as tunable metadata.

---

# 6. Architecture/isolation validation (mandatory #7)

- `git diff --name-only -- src` empty → JRE-002 (tracked) untouched; static gates pin JRE-002/JRE-003 file sets + `__all__` (green).
- Import graph: acyclic across 14 `knowledge` modules; `knowledge` imports only `jyotish` public API; no `astronomy`/`swisseph` imports.
- No network imports; no personal-data concepts; no prediction logic (identifier/comment scans clean).
- Determinism: in-process bit-equality + cross-process byte-equality green; catalog version pins (incl. `fact_vocabulary`) echoed.
- **Verdict: PASS.**

---

# 7. Tests / lint / types (mandatory #8)

- `pytest tests/unit tests/integration` → **857 passed**
- `ruff check src tests` → all checks passed
- `mypy` → `src/knowledge` (14), `src/astronomy` (13), `src/jyotish` (19): all clean

---

# 8. Findings and severity

| ID | Severity | Finding |
|---|---|---|
| F-1 | **BLOCKING** | 14 of 16 rule citations are INCORRECT against the cited editions (tables §1.1–§1.4); 2 NOT VERIFIED (§1.5); 0 verified. Affects all three rule catalogs. |
| F-2 | BLOCKING | Rule *content* diverges from the cited verses for Gaja-Kesari (BPHS + JP), Sakata, the combust-Moon exception, the direct-aspect rule, and Budha-Aditya (§1.6). |
| F-3 | MEDIUM | `datasets/validation/knowledge/` is empty; SPEC §20 / TEST-PLAN §12 require committed reference excerpts. This report's full texts were fetched externally and are not yet committed. |
| F-4 | MEDIUM | Jātaka Pārijāta edition record (`subramania-2003`) is questionable — no corroborating bibliography found; the standard JP translation is V. S. Sastri. |
| F-5 | LOW | Two edition years (Phaladīpikā 2001, Sārāvalī 1999) not independently confirmed. |
| F-6 | LOW | Credibility constants remain pinned proposals (SPEC §22.2) — acceptable per spec, flagged for the record. |

# 9. Corrections made

None. Per the VALIDATOR mandate, citations were not silently rewritten to
appear correct. The engine implementation, provenance mechanics, profiles,
and configuration were all confirmed correct and were not modified.

# 10. Recommendation

**DO NOT MERGE.**

The `knowledge` engine (schema, provenance, precedence, conflict/exception
machinery, profiles, synthesis, determinism) is sound and passes all tests.
However, the authored rule catalogs — the payload of this engine — cite
chapters/verses that do not contain the claimed rules (F-1) and encode
conditions that diverge from the cited texts (F-2). Re-authoring the three
rule catalogs against the committed reference excerpts (to be added per
F-3), re-checksumming, and re-running QA/VALIDATOR is required before merge.
