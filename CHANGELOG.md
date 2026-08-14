# Changelog

All notable changes to JRE are recorded here, per orchestration stage.

## Unreleased

### JRE-003 — Additive Public API: `BodyId` / `RetrogradeState` exports (second JRE-005 blocker resolution)

- Exposed the existing canonical types `BodyId` and `RetrogradeState`
  through the public `jyotish` root (`__all__`) — an API-surface
  correction only: the exported objects ARE `astronomy.models.BodyId` /
  `astronomy.models.RetrogradeState` (identity verified), definitions,
  enum values, and serialization unchanged. Enables JRE-005 to annotate
  body-identity and retrograde fields without importing internals.
- Bumped `jyotish.__version__` `0.3.1 → 0.3.2` (second additive patch).
- Added focused tests `tests/unit/jyotish/test_public_types.py` (6
  tests): attribute presence, `__all__` membership, canonical-type
  identity, enum values, member sets. Public-surface allow-lists synced
  in the JRE-003 static test and the JRE-004 isolation gate
  (`tests/unit/knowledge/test_jyotish_unmodified.py` — the only
  authorized JRE-004 change). No JRE-005 implementation added.

### JRE-003 — Additive Public API: `jyotish.sign_lord_of` (JRE-005 blocker resolution)

- Added `jyotish.sign_lord_of(rashi) -> BodyId` to the JRE-003 public API
  (`__all__`): a disambiguated public accessor for the pinned rashi-lord
  catalog, delegating exactly to the existing `jyotish.rashi.lord_of` /
  `RASHI_LORDS` (no behavior change, no catalog change, no new
  dependencies). The public namespace already exports the nakshatra
  `lord_of`, hence the unambiguous name.
- Bumped `jyotish.__version__` `0.3.0 → 0.3.1` (additive, backward-
  compatible patch; the project `pyproject.toml` version is untouched per
  convention). `RASHI_CATALOG_VERSION` unchanged (catalog data unchanged).
- Added focused unit tests `tests/unit/jyotish/test_sign_lord.py` (8
  tests): all 12 rashis resolve; values equal the `RASHI_LORDS` source of
  truth; delegation to the existing `lord_of`; valid-string coercion;
  invalid input keeps the existing `KeyError` convention; `__all__`
  export present; determinism; classical spot checks. The public-surface
  allow-list test was updated to include the new symbol.
- Purpose: unblock JRE-005 CODING (sign-lordship echoes and the ownership
  projection require the rashi-lord catalog through the public API). No
  JRE-005 implementation was added.

### JRE-005 — Bhava / House Engine (Specialist stage)

- Pinned the implementation-ready contract v0.2.0 from the architect
  baseline: resolved all six open questions with ADR-017..021 and
  refined the four architecture documents in lockstep.
- **Cusp-proximity orb** ([ADR-017](docs/decisions/ADR-017-CUSP-PROXIMITY-ORB.md)):
  pinned `3.0°` default, one config value per analysis (system-
  independent), wrap-aware shortest-arc math, inclusive boundary,
  validation `0 < orb < 30.0`, documented as a modern computational
  convention (no fabricated citation).
- **House categories**: sorted membership sets in canonical enum order
  with overlaps preserved (1 → KENDRA+TRIKONA, 6 → DUSTHANA+UPACHAYA,
  10 → KENDRA+UPACHAYA); no primary label.
- **Anchor frames** ([ADR-019](docs/decisions/ADR-019-ANCHOR-FRAMES-RELATIVE-HOUSE.md)):
  pinned `HOUSE_OCCUPANCY` frame (cusp-anchored in cusp systems, never
  silently whole-sign); `ASC ≡ LAGNA` JRE-004 pin; sign-grid anchoring
  deferred and machine-testable (`SIGN_GRID_FRAME_SUPPORTED = False`,
  `ChartEcho.sign_grid_frame_supported`, enum error).
- **Gochar scope v0.2.0** ([ADR-021](docs/decisions/ADR-021-GOCHAR-DERIVED-FACTS-SCOPE.md)):
  `TransitHouseFact` (frame TRANSIT) — echo of `TransitThroughHouses`
  entries + natal-frame relative house; natal chart required; no transit
  events/interpretation.
- **Tradition passthrough** ([ADR-020](docs/decisions/ADR-020-TRADITION-PROFILE-PASSTHROUGH.md)):
  `tradition_profile: str | None` validated passthrough, echo +
  provenance only, no computation change in v0.2.0.
- **Unplaced bodies** ([ADR-018](docs/decisions/ADR-018-UNPLACED-BODY-SEMANTICS.md)):
  no silent fallback — `unplaced_body_behavior` (`RAISE` default →
  `UnplacedBodyError`; explicit `WHOLE_SIGN_FALLBACK` labeled per body).
- Pinned: complete `BhavaConfig` schema, all enums, error taxonomy,
  house-number/system/whole-sign/cusp semantics, occupancy, lordship,
  ownership, relative-house formula + reference semantics, aspect-to-
  house geometric echo, provenance/`DerivationBlock`/`ChartEcho`,
  catalog/version handling, serialization + JSON Schema, deterministic
  ordering, config authority, validation, performance, isolation, and
  the exact CODING handoff contract (spec §34).
- Advanced [JRE-005 queue item](orchestration/queue/JRE-005-BHAVA-ENGINE.md)
  to SPECIALIST-COMPLETE (CODING status reserved for CODING). No
  implementation, no src/ changes; JRE-002/003/004 untouched.

### JRE-005 — Bhava / House Engine (Architect stage)

- Added [architecture and refined specification](docs/architecture/JRE-005-BHAVA-CORE.md)
  v0.1.0: the derived bhava/house analytical layer consuming JRE-003
  `NatalChart`/`TransitThroughHouses` outputs — module layout
  (`src/bhava/`), the four-way layer split (JRE-002 astronomy / JRE-003
  coordinate state / JRE-005 derived house state / JRE-004 rules),
  house identity `(house_system, house_number)` semantics, whole-sign vs
  cusp bhavas, multi-house-system views, occupancy, planet-to-house,
  house/sign lordship, bhava-lord relationships, canonical relative-house
  calculations, ownership tables, empty-house semantics, cusp/boundary
  facts, retrograde/node echo, geometric aspect-to-house aggregation,
  deterministic serialization, derived-fact provenance, error taxonomy,
  `config/bhava.toml` authority, determinism/performance/isolation
  requirements, and future compatibility (Dasha/Gochar/Drishti/Yoga/
  Varga/Synthesis).
- Added [data contract](docs/architecture/JRE-005-DATA-CONTRACT.md)
  v0.1.0: `BhavaConfig`, `HouseAnalysisResult`/`HouseAnalysis`,
  `DerivedHouseFact`, `PlanetHouseFact`, `HouseOwnershipFact`,
  `RelativeHouseFact`, `AspectToHouseFact`, `DerivationBlock`, JSON
  shapes + Schema, round-trip guarantees.
- Added [specialist implementation spec draft](docs/architecture/JRE-005-SPECIALIST-SPEC.md)
  v0.1.0 (baseline for the SPECIALIST stage): normative formulas
  (absolute/relative house, categories as membership sets, lordship,
  occupancy, cusp proximity, aspect aggregation, gochar frame), public
  API, error taxonomy, config authority, derivation-id constants,
  CODING handoff checklist, open questions.
- Added [test strategy](docs/architecture/JRE-005-TEST-PLAN.md) v0.1.0:
  24-point requirement matrix, cross-process determinism harness,
  JRE-004 `relative_house` cross-layer equality test, static/isolation
  gates, golden fixtures, independent-reference validation, performance
  smoke.
- Added [ADR-013](docs/decisions/ADR-013-BHAVA-LAYER-BOUNDARY.md)
  (derived-fact layer consuming JRE-003, never recomputing it),
  [ADR-014](docs/decisions/ADR-014-RELATIVE-HOUSE-CANONICAL.md)
  (canonical JRE-004-compatible `relative_house` derivation),
  [ADR-015](docs/decisions/ADR-015-MULTI-HOUSE-SYSTEM-VIEWS.md)
  (per-system JRE-003 charts, never mixed), and
  [ADR-016](docs/decisions/ADR-016-DERIVED-FACT-PROVENANCE.md)
  (provenance on every derived fact).
- Advanced [JRE-005 queue item](orchestration/queue/JRE-005-BHAVA-ENGINE.md)
  from REQUESTED to ARCHITECT-COMPLETE (SPECIALIST/CODING statuses
  reserved; no implementation, no tests, no src/ changes).

### JRE-004 — Classical Knowledge & Rule Engine (Recovery Defect Correction)

- **Second VALIDATOR PASS** — the blocking `natural_friendship` defect
  (wrong values vs BPHS ch. 3 v. 55 for 6/7 planets) is corrected and
  independently re-verified: all 7 rows match the verse-55 reading (self
  excluded; both-conflicts → NEUTRAL incl. exaltation-lord conflicts);
  facts checksum recomputed; value-level regression tests added (full-table
  assertion + self-exclusion + mutual friendship/enmity + asymmetry +
  both-conflict → NEUTRAL + exaltation-lord friend-when-unconflicted).
- Rule catalogs untouched: 12 ACTIVE citations remain VERIFIED; 4 research
  rules remain INACTIVE. Gates: **897 passed**, ruff clean, mypy clean
  (47 files), determinism/performance/integrity PASS, JRE-002/JRE-003
  isolation confirmed. MERGE remains blocked.

### JRE-004 — Classical Knowledge & Rule Engine (Recovery VALIDATOR stage)

- **VALIDATOR PASS** — the recovery resolves every blocking finding of the
  original FAIL. All 10 committed evidence excerpts verified as genuine
  quotes against the actual edition texts; all 12 ACTIVE rule citations
  supported by their excerpts (12 VERIFIED, 4 INACTIVE NOT VERIFIED,
  0 INCORRECT).
- VALIDATOR corrections (data/docs only, no contract change):
  (a) `jataka-parijata.gajakesari.5` second form now also enforces the Moon
  not-debilitated limb (JP Adhyāya VII sloka 116, "without being depressed
  or obscured by the Sun"); (b) `bphs.karaka.jupiter.1` conclusion completed
  to the full significator set (2/5/9/11, BPHS ch. 32 v. 31-34);
  (c) `bphs.bhava-9.3` conclusion scoped per BPHS ch. 20 v. 1-2;
  (d) Phaladīpikā `kapoor-2001` year reverted to unknown — "2001" is not
  supported (scan undated, Ranjan printings attested 2004+) — sources
  catalog v1.0.2; (e) ADR-012 wording fix + the doctrine conformance test it
  describes. Rule checksums recomputed; golden regenerated (sources echo
  1.0.2).
- Gates: **889 passed**; ruff clean; mypy clean (47 files); cross-process
  determinism + golden v2.0.0 + tampered-checksum/wrong-pin rejection PASS;
  performance unchanged; JRE-002/JRE-003 isolation confirmed; 4 INACTIVE
  rules confirmed unable to fire even when conditions match.
- Full evidence: [recovery validation report](docs/validation/JRE-004-RECOVERY-VALIDATION-REPORT.md).
- Advanced [JRE-004 queue item](orchestration/queue/JRE-004-CLASSICAL-KNOWLEDGE.md)
  to VALIDATOR-COMPLETE (recovery). MERGE not started.

### JRE-004 — Classical Knowledge & Rule Engine (Recovery QA stage)

- QA independently re-ran the full matrix and focused probes against the
  recovery implementation. **Result: PASS.**
- Full suite **887 passed**; ruff clean; mypy clean (47 files); in-process
  + cross-process determinism PASS; performance limits unchanged
  (synthesis p95 < 50 ms, catalog load < 100 ms).
- Verified: all five FACT_VOCABULARY v1.1.0 path families (categorical
  values not orderable; directional aspect strength; invalid literals and
  out-of-vocabulary rule paths rejected); facts-layer boundary (stdlib +
  knowledge imports only, one ADR-007-sanctioned `jyotish` touch;
  derived facts pure; no prediction); facts catalog tables vs committed
  evidence incl. the combustion retrograde correction; 16-rule disposition
  (12 ACTIVE + 4 INACTIVE, INACTIVE never participates); Gaja-Kesari/Sakata
  distinct formulations, Y1↔Y5 conflict, verified Sakata cancellation;
  provenance (corrected editions resolve, full completeness, enforcement);
  golden v2.0.0 + catalog/version echo; tampered-checksum and wrong-pin
  rejection for all four catalog types; JRE-002/JRE-003 isolation
  (`git diff` empty).
- **One QA correction**: Phaladīpikā `kapoor-2001` edition record `year`
  was null (evidence says 2001) — set `year: "2001"`, re-computed the
  sources catalog checksum. No engine change; full suite re-run green.
- Advanced [JRE-004 queue item](orchestration/queue/JRE-004-CLASSICAL-KNOWLEDGE.md)
  to QA-COMPLETE (recovery) — VALIDATOR not started.

### JRE-004 — Classical Knowledge & Rule Engine (Recovery CODING stage)

- Implemented the approved recovery of the VALIDATOR FAIL (14/16 rule
  citations incorrect): additive **FACT_VOCABULARY 1.0.0 → 1.1.0** per
  [ADR-012](docs/decisions/ADR-012-FACT-VOCABULARY-DERIVED-FACTS.md) —
  `relative_house(<BODY>, <REF>)` refs extended to all nine grahas; new
  derived-fact paths `planet(<BODY>).nature`/`.dignity`/`.combusted` and
  `pair(<A>,<B>).aspect_strength` (directional, classical ¼/½/¾/full
  doctrine).
- Added a **JRE-004 facts layer** (`src/knowledge/facts.py`) and the
  versioned, checksummed, provenance-pinned facts catalog
  (`datasets/knowledge/facts/facts.json` v1.0.0): benefic/malefic (BPHS
  ch. 3 v. 11), exaltation/debilitation/moolatrikona/own signs/friendship
  (ch. 3 v. 49–55, ch. 4), combustion degrees (ch. 7 v. 28–29), aspect
  doctrine (ch. 26 v. 2–5, Phaladīpikā ch. 2 v. 23). Derived from JRE-003
  outputs in snapshot normalization — **JRE-003 unchanged**.
- Re-authored the rule catalogs (`rules:yoga/drishti/karaka` v1.1.0)
  using only VALIDATOR-verified evidence: corrected Gaja-Kesari variants
  (BPHS ch. 36 v. 3–4 vs Jātaka Pārijāta Adhyāya VII sloka 116) with the
  Y1↔Y5 conflict preserved, Phaladīpikā Kesari/Sakata + Sakata
  cancellation as a verified `exception_for`, corrected karaka/bhava
  citations; **removed** the fabricated combust-Moon exception and the
  unsupported sextile rule; **4 rules held INACTIVE (NEEDS-RESEARCH)**
  with unverified citations preserved in `provenance.commentary`.
- Corrected edition records (`sources.json` v1.0.1): Jātaka Pārijāta →
  V. Subrahmanya Sastri 1932, Phaladīpikā → Dr. G. S. Kapoor 2001.
- Committed legally compliant **validation evidence** (short excerpts +
  locators + licensing limitation) at
  `datasets/validation/knowledge/` (TEST-PLAN §12); regenerated the
  synthesis golden fixture (v2.0.0); added `test_facts.py` (23 tests).
- Gates: **887 passed**; ruff clean; mypy clean (47 files); in-process +
  cross-process determinism PASS; performance unchanged;
  JRE-002/JRE-003 isolation PASS.

### JRE-004 — Classical Knowledge & Rule Engine (VALIDATOR stage)

- VALIDATOR independently checked all 16 authored rule citations against
  the actual published texts of the cited editions (Santhanam BPHS, Sastri
  Bṛhat Jātaka and Jātaka Pārijāta, panchanga.lv Phaladīpikā, Raman Praśna
  Mārgam — full texts fetched from archive.org / panchanga.lv because
  `datasets/validation/knowledge/` was never populated).
- **Verdict: FAIL** — 14/16 rule citations INCORRECT, 2 NOT VERIFIED, 0
  VERIFIED. Flagged findings: Gaja-Kesari is BPHS ch. 36 v. 3–4 (Jupiter in
  a kendra from the Moon), not ch. 25 v. 12; the combust-Moon exception
  cites Phaladīpikā ch. 6 v. 12 which is the Amala verse; Sakata is Moon in
  6/8/12 from Jupiter, not from lagna; both Praśna Mārgam citations are
  calculation/division verses; Budha-Aditya and Moon-Venus-in-7th-from-
  Chandra-Lagna found nowhere in the cited texts.
- Added [validation report](docs/validation/JRE-004-VALIDATION-REPORT.md)
  with per-citation evidence tables (VERIFIED / NOT VERIFIED / INCORRECT /
  AMBIGUOUS) and severity ratings. **Recommendation: DO NOT MERGE** until
  the authored rule data is re-authored.
- Provenance mechanics, tradition profiles (SPEC §14), credibility formula
  (§10.2), architecture isolation (JRE-002/003 untouched), determinism,
  and the full test matrix all PASS; the blocking defects are confined to
  authored rule content.
- No corrections made: citations were not silently rewritten (STRICT RULE);
  correction is deferred to a re-authoring decision within JRE-004 scope.

### JRE-004 — Classical Knowledge & Rule Engine (QA stage)

- QA verified the implementation against specialist spec v0.4.0, data
  contract v0.3.0, and test plan v0.3.0; **result: PASS**.
- Full suite green: **857 passed** (706 pre-existing + 151 knowledge: 138
  unit + 13 integration); ruff clean; mypy clean (14 knowledge files);
  JRE-002/JRE-003 untouched (empty `git diff` under `src/`).
- Fixed within CODING scope: `SearchMetadata.catalogs` now echoes
  `fact_vocabulary` version (SPEC §16); `conflicts_with` self-declarations
  rejected at load as malformed (SPEC §17).
- Added QA-matrix tests: catalog integrity, conflict declarations, generic
  rule semantics, envelope schema conformance (Rule/Source/TraditionProfile/
  SynthesisResult), golden fixture (hex-float, `GOLDEN_VERSION` 1.0.0),
  fact-vocabulary resolution against real JRE-003 payloads (incl.
  `relative_house`), config echo, performance smoke.
- VALIDATOR handoff: 7 sources + 16 rule citations are authored data
  pending offline cross-check (SPEC §20); credibility constants and
  completeness levels per SPEC §22.2.
- Advanced [JRE-004 queue item](orchestration/queue/JRE-004-CLASSICAL-KNOWLEDGE.md)
  from CODING to QA-COMPLETE (VALIDATOR/MERGE intentionally not started).

### JRE-004 — Classical Knowledge & Rule Engine (CODING stage)

- Implemented the `knowledge` package per specialist spec v0.4.0: pure data
  models + enums (`models.py`, stdlib-only), error taxonomy (`errors.py`),
  source registry with edition resolution (`sources.py`, ADR-008), provenance
  canonical strings + integrity (`provenance.py`), pinned fact vocabulary
  v1.0.0 + condition grammar validation + pure evaluation (`schema.py`),
  rule catalog load/validate/registry with `conflicts_with` symmetry and
  `exception_for` cycle rejection (`rules.py`), tradition profiles with
  validated passthrough (`traditions.py`, ADR-010), conflict/exception
  resolution (`resolution.py`), deterministic precedence + weight/credibility
  metadata (`precedence.py`, SPEC §8/§10), synthesis pipeline +
  JRE-003 snapshot normalization (`synthesis.py`, §6.3/§11), validated
  `KnowledgeConfig` (`config.py` + `config/knowledge.toml`), serialization
  (`serialize.py`), and the `KnowledgeService` facade (`service.py`,
  ADR-011). `knowledge.__version__ = "0.4.0"`.
- Authored catalogs: 7 sources with real bibliographic edition records
  (`datasets/knowledge/sources/sources.json`), 7 tradition profiles
  (`profiles/profiles.json`), 16 rules across `rules:yoga`, `rules:drishti`,
  `rules:karaka` (≥ 1 `conflicts_with` pair, one `exception_for` chain); all
  SHA-256 checksummed and version-pinned, verified at load (§5.2/§7).
- Extended `pyproject.toml` with the `knowledge` package and
  `tests/{unit,integration}/knowledge` testpaths (build metadata only;
  JRE-002/JRE-003 untouched).
- Removed the empty untracked root `knowledge/` scaffold dir (it shadowed
  the new package via namespace-package resolution).
- **Quality gates green**: `pytest tests/unit tests/integration`
  **831 passed** (125 new knowledge tests incl. CODING happy-path subset +
  static gates §18: public surface, forbidden imports, no prediction,
  astronomy/jyotish unmodified, no personal data, no network; cross-process
  determinism via subprocess byte-identity); `ruff check src tests` clean;
  `mypy src/knowledge` clean (14 files). Performance smoke (informational):
  catalog load ~5 ms, synthesis mean ~0.43 ms (SPEC §19 budgets 100/50 ms).
- Advanced [JRE-004 queue item](orchestration/queue/JRE-004-CLASSICAL-KNOWLEDGE.md)
  from SPECIALIZED to CODING (QA status reserved for QA).

### JRE-004 — Classical Knowledge & Rule Engine (Specialist stage)

- Added [specialist implementation specification](docs/architecture/JRE-004-SPECIALIST-SPEC.md)
  v0.3.0: implementable rule schema (typed condition grammar over a pinned
  fact vocabulary incl. `relative_house`), provenance/source mapping with
  canonical strings + checksums, deterministic rule precedence (source
  priority → specificity → authority tier → version → id), conflicts
  (`conflicts_with` symmetry, FIRST_WINS/REPORT_ALL) and exceptions
  (`exception_for` overrides recorded as `resolution="exception"`),
  applicability-condition semantics, scoring/weighting and confidence model
  (`ResolvedRule` with `effective_weight` + `credibility` — deterministic
  metadata that never affect rule selection and are never predictions),
  interfaces with JRE-003 (snapshot normalization) and JRE-005/006/007
  (consumer contract: `KnowledgeService.synthesize` only), and CODING
  handoff.
- Refined [data contract](docs/architecture/JRE-004-DATA-CONTRACT.md) to
  v0.3.0: `ResolvedRule` wrapper, `Rule.exception_for`, `relative_house`
  vocabulary path, validated `passthrough_config`, `credibility_summary`,
  JSON shapes + Schema updates.
- Refined [test plan](docs/architecture/JRE-004-TEST-PLAN.md) to v0.3.0:
  exceptions, weight/credibility, snapshot normalization, precedence-key
  echo, vocabulary expansion.
- Initial catalogs specified: 7 sources (BPHS, Bṛhat Jātaka, Jātaka
  Pārijāta, Phaladīpikā, Sūrya Siddhānta, Praśna Mārgam, Sārāvalī), 7
  profiles (incl. `regional-kerala`, `regional-north-indian`), ≥ 3 rule
  catalogs at CODING.
- Advanced [JRE-004 queue item](orchestration/queue/JRE-004-CLASSICAL-KNOWLEDGE.md)
  from ARCHITECTED to SPECIALIZED (CODING status reserved for CODING).

### JRE-004 — Classical Knowledge & Rule Engine (Architect stage)

- Added [JRE-004 architecture and refined specification](docs/architecture/JRE-004-KNOWLEDGE-RULES-CORE.md)
  v0.2.0: module layout (`src/knowledge/`), source registry, provenance
  system, rule schema over a pinned JRE-003 fact vocabulary, tradition
  profiles, deterministic rule precedence, conflict-resolution policies,
  synthesis interface (`KnowledgeService`), configuration, determinism
  contract, error taxonomy, testing matrix, validation strategy, and
  specialist handoff checklist.
- Added [JRE-004 data contract](docs/architecture/JRE-004-DATA-CONTRACT.md)
  v0.2.0: field-level models (Source/Edition, RuleCondition, Rule,
  TraditionProfile, RuleQuery, SynthesisResult), JSON shapes + Schema,
  catalog file format, fact-vocabulary table, round-trip guarantees.
- Added [JRE-004 test strategy](docs/architecture/JRE-004-TEST-PLAN.md)
  v0.2.0: requirement matrix for all 7 mandated capabilities plus
  determinism/static/no-prediction gates and independent cross-source
  validation.
- Added [ADR-007](docs/decisions/ADR-007-KNOWLEDGE-PACKAGE-PLACEMENT.md)
  (`knowledge` package placement + import boundary),
  [ADR-008](docs/decisions/ADR-008-SOURCE-REGISTRY-PROVENANCE.md)
  (source registry + mandatory provenance, no text ingestion),
  [ADR-009](docs/decisions/ADR-009-RULE-SCHEMA.md) (rules as typed data,
  no conclusion evaluator),
  [ADR-010](docs/decisions/ADR-010-TRADITION-PROFILES-PRECEDENCE-CONFLICT.md)
  (tradition profiles, precedence, recorded conflict resolution), and
  [ADR-011](docs/decisions/ADR-011-SYNTHESIS-INTERFACE.md) (synthesis
  consumer contract).
- Numbering note: JRE-004 supersedes the informal "JRE-004…JRE-007 engine"
  names in the JRE-003 specialist spec's future-compatibility section; the
  initial classical sources are BPHS, Bṛhat Jātaka, Jātaka Pārijāta,
  Phaladīpikā, Sūrya Siddhānta/Vedāṅga, plus later regional sources.
- Advanced [JRE-004 queue item](orchestration/queue/JRE-004-CLASSICAL-KNOWLEDGE.md)
  from REQUESTED to ARCHITECTED (SPECIALIST status reserved for SPECIALIST).

### JRE-003 — Jyotish Coordinate and State Layer (QA stage)

- QA reviewed the Architect/Specialist/Coding deliverables and ran the full
  automated matrix plus independent runtime probes; **result: PASS**.
- Full suite green: **706 passed** (233 astronomy + 425 unit jyotish + 48
  integration jyotish); ruff clean; mypy clean (32 files); JRE-002 untouched.
- Verified mandates: same-house ≠ conjunction (12°/28° Aries share a rashi
  with exact 16° separation and are not conjunct); longitude never
  prematurely rounded before Rashi/Nakshatra/Pada/geometry; all 12 rashi +
  27 nakshatra + 108 pada boundaries deterministic and bit-identical across
  repeats; unknown birth time yields candidate event intervals (never an
  invented instant; malformed birth data raises `InvalidBirthDataError`);
  generic mode operates with no personal data; individual mode derives
  transit-through-houses from the natal state with explicit reference
  points; no interpretation vocabulary, no network imports, `swisseph`
  confined to `jyotish/swisseph/`.
- Reference checks: eclipse maxima vs NASA canon (1991-07-11 solar ≤ 90 s,
  1990-02-09 lunar ≤ 180 s), lagna vs binding ascendant < 0.01°, Jupiter
  sidereal MESHA ingress 2011-05-08, Sun 12 rashi ingresses/year, Moon
  nakshatra cadence, station events, cross-process determinism.
- Observation (no code change): the CODING handoff text said "281
  integration tests"; the collected integration count is 48 (documentation
  discrepancy only).
- Advanced [JRE-003 queue item](orchestration/queue/JRE-003-JYOTISH-CORE.md)
  from CODING-COMPLETE to QA-COMPLETE (VALIDATOR/MERGE intentionally not
  started).

### JRE-003 — Jyotish Coordinate and State Layer (CODING stage)

- Implemented the `jyotish` package per specialist spec v0.3.0: pure
  versioned catalogs (`rashi.py`, `nakshatra.py` — all 12 rashis, 27
  nakshatras, 108 padas, classical rulers), `dms.py`, classification
  (`position.py`), exact-angular geometry (`geometry.py` per ADR-004),
  houses/lagna (`houses.py`, `lagna.py` with pure whole-sign derivation),
  continuous transit engine (`transit.py` per ADR-005: deterministic
  bisection, bounded memoization, retrograde re-crossings), eclipse interface
  + adapter (`eclipse.py`, `jyotish/swisseph/eclipse.py` per ADR-006),
  validated configuration (`config.py` + `config/jyotish.toml`),
  serialization, and the `JyotishService` facade serving GENERIC and
  INDIVIDUAL modes from one engine.
- Added `src/jyotish/swisseph/` adapters (constants, houses, eclipse) — the
  only place the binding is imported (static gate enforced); sidereal cusps
  via `houses_ex(FLG_SIDEREAL)`; eclipse `ECL_*` named constants.
- Extended `pyproject.toml` with `jyotish`/`jyotish.swisseph` packages and
  `tests/*/jyotish` testpaths (no new dependencies).
- **Fixed defects**: invalid TOML `null` values in `config/jyotish.toml`;
  nakshatra/pada boundary float drift (exact multiplication form); eclipse
  adapter zero-slot crash on penumbral lunar eclipses; config error-message
  bug for unknown aspect kinds; `all_pairs` `same_bhava` threading.
- Shipped 425 unit tests (all 12 rashi, all 27 nakshatra and 108 pada
  boundaries, exact/wide conjunction, aspects, applying/separating, houses,
  lagna, transit events incl. retrograde re-crossings and stations, config
  validation, serialization, static gates) and 281 integration tests (lagna
  vs binding, houses vs binding cusps, real transit events, eclipses vs NASA
  canon times, determinism incl. cross-process, timezone, Rahu/Ketu, generic/
  individual separation, no-interpretation runtime scans).
- Quality gates green: `pytest` **706 passed**; `ruff` all checks passed;
  `mypy` no issues (32 files); JRE-002 untouched.
- Advanced [JRE-003 queue item](orchestration/queue/JRE-003-JYOTISH-CORE.md)
  from SPECIALIZED to CODING-COMPLETE (QA status reserved for QA).

### JRE-003 — Jyotish Coordinate and State Layer (Specialist stage)

- Added [specialist implementation specification](docs/architecture/JRE-003-SPECIALIST-SPEC.md)
  v0.3.0: exact computational rules (sidereal coordinates, ayanamsa,
  normalization, rounding policy), complete 12-Rashi and 27-Nakshatra
  catalogs with classical rulers and pada boundaries (BPHS/Brihat Jataka
  citation, versioned), DMS policy, planetary state derivation, exact-angular
  planet-to-planet geometry with closed-form applying/separating, pure
  whole-sign + cusp house systems, lagna, bhava computation, sidereal cusp
  flag policy, natal chart + transit-through-houses with explicit reference
  points, continuous transit engine (deterministic event search, memoized,
  retrograde re-crossings), generic/individual modes, Rahu/Ketu rules,
  eclipse interface + adapter with empirically pinned binding facts,
  precision tiers, calculation identity, error taxonomy, serialization,
  static gates, validation strategy, future-compatibility, and CODING handoff.
- Refined [data contract](docs/architecture/JRE-003-DATA-CONTRACT.md) to
  v0.3.0: `position_type` added to `JyotishConfig`, `birth_snapshot` echo on
  `TransitThroughHouses`, `PairGeometry.aspects` carries all seven kinds.
- Refined [test plan](docs/architecture/JRE-003-TEST-PLAN.md) to v0.3.0:
  eclipse `tret` layout pinning vs NASA canon, sidereal-house flag and
  whole-sign pure-vs-binding tests, `position_type` tests.
- Advanced [JRE-003 queue item](orchestration/queue/JRE-003-JYOTISH-CORE.md)
  from ARCHITECTED to SPECIALIZED (CODING status reserved for CODING).

### JRE-003 — Jyotish Coordinate and State Layer (Architect stage)

- Added [JRE-003 architecture and refined specification](docs/architecture/JRE-003-JYOTISH-CORE.md)
  v0.2.0: module layout (`src/jyotish/`), data contracts, classification
  rules, exact-angular geometry, bhava/lagna, continuous transit model,
  eclipse-engine interface, configuration, determinism contract, error
  taxonomy, testing matrix, validation strategy, and specialist handoff
  checklist.
- Added [JRE-003 data contract](docs/architecture/JRE-003-DATA-CONTRACT.md)
  v0.2.0: field-level model specs (PlanetState, PairGeometry, Bhava,
  LagnaState, NatalChart, TransitEvent, EclipseEvent), JSON shapes and
  Schema, example payloads, round-trip guarantees.
- Added [JRE-003 test strategy](docs/architecture/JRE-003-TEST-PLAN.md)
  v0.2.0: requirement matrix for all 14 mandated tests (rashi/nakshatra/pada
  boundaries, conjunction, retrograde, stations, ingress/egress, lagna,
  houses, timezone, eclipses, determinism) plus independent-validation
  strategy (published Lahiri tables, published charts, NASA eclipse canon).
- Added [ADR-002](docs/decisions/ADR-002-HOUSE-ECLIPSE-ADAPTER-PLACEMENT.md)
  (house/eclipse adapters live in `jyotish`, JRE-002 untouched),
  [ADR-003](docs/decisions/ADR-003-ZODIAC-MODE-CATALOG-VERSIONING.md)
  (explicit zodiac mode, sidereal default, versioned catalogs),
  [ADR-004](docs/decisions/ADR-004-CONJUNCTION-ASPECT-SEMANTICS.md)
  (exact-angular conjunction/aspect semantics),
  [ADR-005](docs/decisions/ADR-005-CONTINUOUS-TRANSIT-ENGINE.md)
  (deterministic event search + memoization), and
  [ADR-006](docs/decisions/ADR-006-ECLIPSE-ENGINE-INTERFACE.md)
  (eclipse interface, initial provider, data-only boundary).
- Advanced [JRE-003 queue item](orchestration/queue/JRE-003-JYOTISH-CORE.md)
  from REQUESTED to ARCHITECTED with specialist handoff checklist.

### JRE-002 — Astronomical Core (MERGE stage)

- VALIDATOR independently verified planetary positions against JPL Horizons
  and published Meeus/node constants: **Final verdict PASS** — no
  implementation defects, no blocking validation issues.
- MERGE performed the controlled merge: pre-commit gates (diff/status review,
  validation report present, QA/Validator recorded results, unrelated-change
  scan, private-data scan, astrology-logic scan, architecture conformance) all
  passed; final suite **233 passed** (67 unit + 166 integration), ruff and
  mypy clean.
- Advanced [JRE-002 queue item](orchestration/queue/JRE-002-ASTRONOMICAL-CORE.md)
  from QA-COMPLETE to MERGED in a single commit:
  `Implement JRE-002 deterministic astronomical core`.

### JRE-002 — Astronomical Core (Architect stage)

- Added [ADR-001](docs/decisions/ADR-001-EPHEMERIS-PROVIDER.md): adopt
  `pysweph` (Swiss Ephemeris bindings) as the initial ephemeris provider;
  SWIEPH high-precision mode with bundled local `.se1` files as standard,
  MOSEPH as deterministic fallback, no runtime network dependency.
- Added
  [JRE-002 architecture and refined specification](docs/architecture/JRE-002-ASTRONOMICAL-CORE.md)
  v0.2.0: module layout, data contracts, provider abstraction, time/coordinate
  handling, error taxonomy, determinism contract, testing matrix, validation
  strategy.
- Advanced [JRE-002 queue item](orchestration/queue/JRE-002-ASTRONOMICAL-CORE.md)
  from REQUESTED to ARCHITECTED with specialist handoff checklist.

### JRE-002 — Astronomical Core (CODING stage)

- Implemented the `astronomy` package per the specialist spec v0.3.0:
  `time.py` (IANA-only local->UTC + pure Julian Day), `coordinates.py`,
  `models.py`, `serialize.py`, `config.py`, `provider.py` registry,
  `service.py` facade, and the `swisseph` adapter (SWIEPH standard with
  bundled `.se1` files, MOSEPH fallback, checksum verification, per-call
  state discipline under a lock, Rahu/Ketu from lunar node, ayanamsa modes).
- Shipped happy-path unit tests per test plan §16.

### JRE-002 — Astronomical Core (QA stage)

- QA inspected every module, verified package structure, provider init,
  timezone handling, invalid-input errors, ayanamsa configuration, all nine
  bodies, Rahu/Ketu derivation, longitude normalization, retrograde windows,
  determinism (in-process and cross-process), provider metadata, stable JSON
  serialization, error handling, and boundary cases.
- **Fixed defect**: the pure Julian Day formula in `time.py` drifted by 1–3
  days for accepted pre-1900 dates (up to +7 days by 3000 AD); replaced with
  the canonical proleptic-Gregorian algorithm, now bit-exact vs
  `swe.julday` over 1583–3000.
- **Fixed test defects**: `test_time.py` leap-day JD value (2451604.5 →
  2451604.0), `test_config.py` repo-root off-by-one, `test_static.py`
  stdlib allow-list missing `__future__`.
- Brought the §35 CI gate to green: ruff (88 → 0 errors) and mypy
  (25 → 0 errors, incl. `swisseph` stubless import override and read-only
  `metadata` Protocol property).
- Added the QA integration suite (166 tests): valid input, timezone,
  invalid input, ayanamsa, Rahu/Ketu, boundaries, retrograde windows,
  determinism, provider metadata, serialization, JD cross-check vs
  `swe.julday`/`swe.utc_to_jd`, fallback + checksum corruption, no
  interpretation, cross-process determinism.
- Advanced [JRE-002 queue item](orchestration/queue/JRE-002-ASTRONOMICAL-CORE.md)
  from CODING to QA-COMPLETE (VALIDATOR/MERGE intentionally not started).

### JRE-002 — Astronomical Core (Specialist stage)

- Added [specialist implementation specification](docs/architecture/JRE-002-SPECIALIST-SPEC.md)
  v0.3.0: package architecture, module boundaries, provider abstraction,
  Swiss Ephemeris adapter boundary, data models, time/UTC/JD rules,
  tropical/sidereal separation, ayanamsa interface, Rahu/Ketu representation,
  retrograde/velocity semantics, precision, metadata, flags, determinism,
  error model, validation strategy, test architecture, external reference
  validation, future-provider compatibility, performance/offline constraints,
  caching decision, astronomy/astrology API boundary, serialization format,
  consumer contract for the Gochar and Kundali engines, and CODING handoff.
- Added [data contract](docs/architecture/JRE-002-DATA-CONTRACT.md) v0.3.0:
  field-level model specs, validation rules, JSON Schema, example payload.
- Added [test plan](docs/architecture/JRE-002-TEST-PLAN.md) v0.3.0:
  requirement matrix, determinism/fallback/static gates, golden fixtures,
  external-reference validation harness and tolerance policy.
- Advanced [JRE-002 queue item](orchestration/queue/JRE-002-ASTRONOMICAL-CORE.md)
  from ARCHITECTED to SPECIALIZED (CODING status reserved for CODING).
