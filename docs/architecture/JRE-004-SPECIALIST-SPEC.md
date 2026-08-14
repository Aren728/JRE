# JRE-004 — Classical Knowledge & Rule Engine: Specialist Implementation Specification

- Status: SPECIALIZED
- Version: 0.4.0 (supersedes v0.3.0; clarification pass resolves remaining
  specification ambiguities — see the notice block)
- Date: 2026-08-12
- Author: Knowledge/Rules Specialist
- Upstream: [JRE-004 Architecture v0.2.0](JRE-004-KNOWLEDGE-RULES-CORE.md),
  [ADR-007](../decisions/ADR-007-KNOWLEDGE-PACKAGE-PLACEMENT.md),
  [ADR-008](../decisions/ADR-008-SOURCE-REGISTRY-PROVENANCE.md),
  [ADR-009](../decisions/ADR-009-RULE-SCHEMA.md),
  [ADR-010](../decisions/ADR-010-TRADITION-PROFILES-PRECEDENCE-CONFLICT.md),
  [ADR-011](../decisions/ADR-011-SYNTHESIS-INTERFACE.md),
  [JSP-001 Core Specification](../../specifications/core/JSP-001.md)

This is the **implementable** specification for the Classical Knowledge &
Rule Engine. Where it conflicts with the architecture document, this document
wins (both are versioned; changes are recorded in §31). It is the contract
for CODING, QA and VALIDATOR.

> **Supersession notice (read first):**
> 1. **`ResolvedRule` wraps every matched/suppressed rule.** The architecture
>    returned bare `Rule` objects in `SynthesisResult.matched_rules`. The
>    Specialist adds `ResolvedRule(rule, precedence_key, effective_weight,
>    credibility, applicability, status_note)` so every result carries its
>    own ordering/weighting/confidence metadata (request: scoring/weighting,
>    confidence model). `SynthesisResult.matched_rules` and
>    `.suppressed_rules` are now `tuple[ResolvedRule, ...]` (§11).
> 2. **Rules gain an `exception_for` field** (request: conflicts/exceptions).
>    A rule may declare `exception_for: tuple[rule_id, ...]` — when it
>    matches, it **overrides** the listed base rules regardless of normal
>    precedence, and the override is recorded in a `ConflictRecord` with
>    `resolution="exception"` (§9). This is the "exceptions" mechanism; it is
>    distinct from conflicts (same-priority disagreement).
> 3. **Fact-vocabulary path set is pinned and expanded with a
>    `relative_house` path** (resolves architecture §24.3). Conditions may
>    reference `bhava(<BODY>).relative_house` (the natal house number of a
>    body relative to the lagna reference) and `transit(<BODY>).kind` /
>    `eclipse.kind` — all resolvable from JRE-003 outputs (§7).
> 4. **Scoring/weighting and confidence are deterministic metadata, not
>    interpretation.** `effective_weight` and `credibility` are pure
>    functions of (authority_tier, specificity, source-priority rank,
>    provenance completeness, rule_version) with pinned formulas (§10). They
>    never feed rule *selection* (selection is condition matching +
>    precedence only) and they are never "predictions". This keeps the hard
>    no-prediction boundary while satisfying the request's
>    scoring/weighting/confidence deliverables.
> 5. **Passthrough profile config is validated, not opaque** (resolves
>    architecture §24.4): `TraditionProfile.passthrough_config` may contain
>    only a pinned allow-list of `JyotishConfig` field names with
>    type-validated values (§14). It is echoed, never interpreted.
>
> **Clarification-pass supersessions (v0.4.0, read next):**
> 6. **Default profile is fully configurable** (§13, §14.2): the default is
>    `KnowledgeConfig.default_profile_id`, resolved at query time by
>    `query.profile_id` → config default → `UnknownProfileError`. Changing
>    the default never changes a previously-echoed result's identity (the
>    resolved profile version is part of the output).
> 7. **Credibility/weight constants are configuration, not hard-coded
>    assumptions** (§10, §13): the coefficients and provenance-completeness
>    levels move into `KnowledgeConfig` (pinned defaults, validated). The
>    formulas are unchanged in shape but read from config, so tuning is a
>    versioned config decision — and still never affects rule *selection*.
> 8. **Bibliographic provenance is mandatory for every imported rule** (§4,
>    §5): each source carries ≥ 1 `Edition` record; a rule's primary
>    `ProvenanceRef` must resolve to a source **with at least one edition**,
>    and `edition_id` is **required** whenever `chapter` or `verse_start` is
>    present (§5.2). Missing → `ProvenanceError`.
> 9. **`RuleDomain` expansion is additive and versioned** (§7.1): new values
>    are appended to the enum; every new value requires a `DOMAIN_REQUIREMENTS`
>    entry and a spec bump; existing rules and catalogs are unaffected.
> 10. **`relative_house` has an explicit reference parameter** (§6.2): the
>    path is `relative_house(<BODY>, <REF>)` with `<REF> ∈ {LAGNA, MOON, SUN,
>    ASC}` (mirroring JRE-003's `TransitReferencePoint`). The v0.3.0
>    `bhava(<BODY>).relative_house` (lagna-implicit) is superseded.
> 11. **Conflicting rules are never deleted** (§9.3): conflict resolution is
>    a per-synthesis decision; both rules remain in the catalog unchanged;
>    suppression is ephemeral and always recorded.
> 12. **Three-way separation** (source data / deterministic engine /
>    synthesis output) and **non-proof guarantee** (§23): catalogs never
>    contain computed values; engine code never contains rules; and
>    `credibility`/`effective_weight` are relative evidence metadata — the
>    engine never presents them as empirical proof of prediction accuracy.

## 1. Python package architecture

- **Python**: 3.12 only (target host: Linux, 2 cores, ~4 GB RAM).
- **Layout**: src-layout, same `pyproject.toml` as JRE-002/JRE-003. JRE-004
  adds the `knowledge` package and the
  `tests/{unit,integration,validation}/knowledge` testpaths at CODING time
  (build metadata only — no JRE-002/JRE-003 code changes).
- **Import name**: `knowledge`. A `jre.` namespace root remains a later,
  separately-versioned refactor (unchanged).
- **Public surface**: `knowledge/__init__.py` exports ONLY
  `KnowledgeService`, the models/enums from DATA-CONTRACT §1–§8, the
  registries (`get_source`, `get_profile`, catalog readers), and the public
  errors. An explicit `__all__` enforces this (tested).
- **Versioning**: `knowledge.__version__` == spec version `0.4.0`. Catalog
  versions are separate constants (`SOURCE_CATALOG_VERSION`,
  `PROFILE_CATALOG_VERSION`, per-rule-catalog versions) — see §5.
- **Imports**: `knowledge` imports from `jyotish`'s **public API only**
  (models/enums for the fact vocabulary: `PlanetState`, `PairGeometry`,
  `Bhava`, `LagnaState`, `TransitEvent`, `EclipseEvent`, `BodyId`, enums).
  It never imports `astronomy`, `swisseph`, `astronomy.swisseph`,
  `inference`, `astrology`, `transits`, `dasha`, `calculations`, `gochar`,
  or `rules` (enforced by a static test — ADR-007).

## 2. Module boundaries

Every file, one responsibility, no cycles:

| File | Responsibility | Imports (allowed) |
|---|---|---|
| `src/knowledge/__init__.py` | Public API allow-list | its own modules only |
| `src/knowledge/models.py` | All dataclasses + enums. **Pure data; stdlib only** | stdlib |
| `src/knowledge/errors.py` | `KnowledgeError` hierarchy | — |
| `src/knowledge/sources.py` | Source registry: catalog + edition resolution | `models`, `errors` |
| `src/knowledge/provenance.py` | Provenance chains: canonical strings, integrity, checksums | `models`, `sources`, `errors` |
| `src/knowledge/schema.py` | Rule schema: condition grammar + fact-vocabulary validation | `models`, `errors` |
| `src/knowledge/rules.py` | Rule catalogs: load, validate, version, registry | `models`, `schema`, `provenance`, `errors` |
| `src/knowledge/traditions.py` | Tradition profiles: definition, registry, source priority | `models`, `errors` |
| `src/knowledge/resolution.py` | Conflict/exception detection + policies | `models`, `traditions`, `errors` |
| `src/knowledge/precedence.py` | Deterministic rule precedence + weight/credibility | `models`, `traditions` |
| `src/knowledge/synthesis.py` | Synthesis engine: query -> ordered ResolvedRules + conflicts | `models`, `rules`, `traditions`, `resolution`, `precedence`, `schema`, `errors` |
| `src/knowledge/config.py` | `config/knowledge.toml` → `KnowledgeConfig` | stdlib `tomllib`, `models` |
| `src/knowledge/serialize.py` | `result_to_json` / `from_dict` per DATA-CONTRACT §9 | `models` |
| `src/knowledge/service.py` | `KnowledgeService` facade | everything above |

Rules:

- Import direction is one-way: `service → synthesis → {rules, traditions,
  resolution, precedence} → models`; `provenance → sources → models`;
  `schema → models`. No cycles.
- `models.py` must not import `jyotish` (it is pure); `schema.py` and
  `synthesis.py` import `jyotish` models only for vocabulary typing
  (allowed — ADR-007).
- Catalog files are data; loaded through `rules.py`/`sources.py`/
  `traditions.py` only. No other module reads `datasets/knowledge/`.

## 3. Data models — authoritative field sets

Authoritative field-level contract: [DATA-CONTRACT v0.3.0](JRE-004-DATA-CONTRACT.md).
Key refinements (superseding the architecture's design-level models):

### 3.1 `Rule` (frozen dataclass) — final

| Field | Type | Constraint |
|---|---|---|
| `rule_id` | `str` | stable; regex `^[a-z0-9][a-z0-9._-]*$` |
| `domain` | `RuleDomain` | enum value |
| `summary` | `str` | non-empty |
| `condition` | `RuleCondition` | schema-valid (unknown path/type ⇒ `RuleSchemaError`) |
| `conclusion` | `RuleConclusion` | kind + statement + opaque `structured` dict |
| `provenance` | `ProvenanceRef` | primary ref; `source_id` must resolve (when enforced) |
| `supporting_refs` | `tuple[ProvenanceRef, ...]` | optional |
| `conflicts_with` | `tuple[str, ...]` | rule_ids; **symmetry enforced** at load (a↔b) |
| `exception_for` | `tuple[str, ...]` | rule_ids this rule overrides when it matches (§9) |
| `authority_tier` | `int` | 1..5, authored |
| `status` | `RuleStatus` | ACTIVE/DEPRECATED/SUPERSEDED |
| `tradition_tags` | `tuple[str, ...]` | profile-matching tags |
| `rule_version` | `str` | semver |

### 3.2 `RuleCondition` (frozen dataclass) — final grammar

- Atom: `combiner is None`, `op ∈ ConditionOp`, `path` non-null, `value`
  typed per vocabulary, `children == ()`.
- Combiner: `op is None`, `path is None`, `children != ()`; `NOT` has
  exactly one child.
- `EXISTS` op: `value is None` (presence test only).

### 3.3 `ResolvedRule` (frozen dataclass) — NEW (supersession #1)

| Field | Type | Semantics |
|---|---|---|
| `rule` | `Rule` | the resolved rule |
| `precedence_key` | `tuple[object, ...]` | exact comparator tuple from §8 (echoed for audit) |
| `effective_weight` | `float` | pinned formula §10.1 |
| `credibility` | `float` | pinned formula §10.2 (evidence metadata, NOT prediction) |
| `applicability` | `bool` | condition evaluated true against the snapshot |
| `status_note` | `str \| None` | e.g. `"suppressed by X"`, `"exception overrides Y"`, `None` |

### 3.4 `SynthesisResult` — refined

`matched_rules: tuple[ResolvedRule, ...]`, `suppressed_rules:
tuple[ResolvedRule, ...]`, plus (unchanged) `query`, `profile`,
`conflicts`, `provenance_index`, `config`, `search_metadata`.

## 4. Source registry (initial catalog)

`datasets/knowledge/sources/sources.json` — `catalog_id: "sources"`,
`SOURCE_CATALOG_VERSION = "1.0.0"` (constant in `sources.py`). Initial
entries (canonical IAST pinned per architecture §24.5 resolution):

| source_id | canonical_name | common | author | period | language | lineage | status |
|---|---|---|---|---|---|---|---|
| `bphs` | Bṛhat Parāśara Horā Śāstra | BPHS | Parāśara (attrib.) | ~600–800 CE | Sanskrit | `parashari` | CANONICAL |
| `brihat-jataka` | Bṛhat Jātaka | — | Varāhamihira | ~505–587 CE | Sanskrit | `parashari` | CANONICAL |
| `jataka-parijata` | Jātaka Pārijāta | — | Vaidyanātha Dīkṣita | ~1300–1400 CE | Sanskrit | `parashari` | CANONICAL |
| `phaladeepika` | Phaladīpikā | — | Mantreśvara | ~1200–1300 CE | Sanskrit | `parashari` | CANONICAL |
| `surya-siddhanta` | Sūrya Siddhānta | — | (ancient, attrib.) | ~400–1000 CE | Sanskrit | `vedanga` | HISTORICAL |
| `prasna-marga` | Praśna Mārgam | — | Pānakkāttu Śaṅkaran Nampūtiri | ~1649 CE | Sanskrit/Malayalam | `kerala` | REGIONAL |
| `saravali` | Sārāvalī | — | Kalyāṇavarman | ~1200 CE | Sanskrit | `north-indian` | REGIONAL |

Each entry carries an `editions` list (≥ 1): `edition_id`, `title`,
`translator`, `publisher`, `year`, `language`, `notes`. CODING must provide
real bibliographic records for the editions it cites (checksummed).

**Bibliographic provenance is mandatory (supersession #8):**

- Every `Source` in the registry must have `len(editions) >= 1`. A source
  with no edition record cannot be cited (validation at load).
- A `ProvenanceRef` must resolve to a source that **has at least one
  edition**; a `source_id` that resolves but the source has zero editions ⇒
  `ProvenanceError`.
- `edition_id` is **required** on a `ProvenanceRef` whenever `chapter` or
  `verse_start` is set (§5.2); missing ⇒ `ProvenanceError`. Whole-source
  attributions (`chapter=None`) may omit `edition_id` but still resolve the
  source's default edition for display.
- `provenance.py` exposes `resolve_bibliography(ref) -> Source + Edition`
  used for the canonical string and for VALIDATOR's offline cross-check.

**Regional-source resolution (architecture §24.6):** initial `regional-*`
profiles use `prasna-marga` (Kerala) and `saravali` (North Indian). A
`SourceStatus=REGIONAL` entry is required for every `regional-*` profile's
priority list. Additional regional texts are data additions (no engine
change).

## 5. Provenance (canonical strings, integrity)

### 5.1 Canonical provenance string

`canonical_provenance(ref, source) -> str`:

- Full: `"{COMMON} ch.{chapter} v.{verse_start}{-v.{verse_end}} (tr. {translator} {year})"`
  e.g. `"BPHS ch.25 v.12 (tr. Santhanam 2001)"`.
- Chapter-only (verse `None`): `"BPHS ch.25 (tr. {translator} {year})"`
  (edition still resolved).
- Source-only (chapter `None`): `"BPHS"` (edition omitted; a whole-source
  attribution may cite the source without pinning a verse).
- Edition resolved through `sources.resolve_edition(source_id,
  edition_id)`; unknown `edition_id` ⇒ `UnknownEditionError`.
- **Bibliographic completeness levels** (used by §10.2) are derived from the
  resolved ref: `full` = source+chapter+verse+edition; `verse` =
  source+chapter+verse (edition omitted only when chapter is None is not the
  case); `chapter` = source+chapter; `source` = source only. A ref that
  fails to resolve or lacks a required `edition_id` (per §4) never reaches
  this function — it fails at load.

### 5.2 Integrity

- `provenance_index`: `{rule_id: tuple[canonical strings]}` (primary first,
  then supporting) — deterministic order.
- `verify_checksums=True` (default): SHA-256 over each catalog file at load;
  mismatch ⇒ `CatalogIntegrityError` with the file path and expected/actual.
- `enforce_provenance=True` (default): a rule whose primary ref has an
  unresolvable `source_id` ⇒ `ProvenanceError`. Missing chapter/verse is
  allowed only when `chapter is None` explicitly (whole-source attribution).
- Version pins in `KnowledgeConfig` are checked at load; mismatch ⇒
  `CatalogIntegrityError`.

## 6. Rule schema and applicability conditions

### 6.1 Condition evaluation semantics

`evaluate(condition, snapshot, vocab) -> bool` — pure, deterministic:

- Atom `EQ/NEQ/LT/LTE/GT/GTE/IN/NOT_IN`: resolve `path` in `snapshot`
  (via `vocab`), compare with the literal (`EQ/NEQ` value equality; ordering
  ops numeric or enum-ordered strings; `IN/NOT_IN` membership). Missing
  snapshot key ⇒ atom is **False** (no match) — never an exception.
- Atom `EXISTS`: True iff the path resolves to a non-null value.
- `ALL`: all children True (empty ⇒ True). `ANY`: any child True (empty ⇒
  False). `NOT`: child False.

### 6.2 Fact vocabulary (pinned, v1.0.0) — resolves architecture §24.3

`FACT_VOCABULARY` table (version constant `FACT_VOCABULARY_VERSION =
"1.0.0"` in `schema.py`):

| Path | Snapshot source (JRE-003 output) | Value type |
|---|---|---|
| `planet(<BODY>).rashi` | `PlanetState.rashi` | `RashiId` string |
| `planet(<BODY>).nakshatra` | `PlanetState.nakshatra` | `NakshatraId` string |
| `planet(<BODY>).pada` | `PlanetState.pada` | int 1–4 |
| `planet(<BODY>).degree_in_rashi` | `PlanetState.degree_in_rashi` | float |
| `planet(<BODY>).retrograde` | `PlanetState.retrograde` | `RetrogradeState` string |
| `lagna.rashi` | `LagnaState.rashi` | `RashiId` string |
| `lagna.nakshatra` | `LagnaState.nakshatra` | `NakshatraId` string |
| `lagna.pada` | `LagnaState.pada` | int 1–4 |
| `bhava(<N>).house_lord` | `Bhava.house_lord` | `BodyId` string |
| `bhava(<N>).occupants` | `Bhava.occupants` | list of `BodyId` strings |
| `relative_house(<BODY>, <REF>)` | natal house number of the body relative to reference `<REF>` | int 1–12 |
| `pair(<A>,<B>).conjunction` | `PairGeometry.conjunction` | bool |
| `pair(<A>,<B>).separation_deg` | `PairGeometry.separation_deg` | float |
| `pair(<A>,<B>).aspects` | `PairGeometry.aspects` (kinds present) | list of `AspectKind` strings |
| `transit(<BODY>).kind` | `TransitEvent.kind` values in interval | list of `TransitEventKind` strings |
| `eclipse.kind` | `EclipseEvent.kind` values in interval | list of `EclipseKind` strings |
| `eclipse.classification` | `EclipseEvent.classification` values | list of `EclipseClassification` strings |

- Path grammar: `planet(...)`, `lagna`, `bhava(...)`, `relative_house(...)`,
  `pair(...)`, `transit(...)`, `eclipse` — validated by `schema.py` with a
  parser; a malformed path or unknown field ⇒ `RuleSchemaError` at catalog
  load.
- **`relative_house(<BODY>, <REF>)` reference scope (supersession #10):**
  `<REF>` must be one of `LAGNA` (default when the rule omits it for
  backward-authored catalogs — pinned, not inferred), `MOON` (Chandra
  lagna), `SUN` (Surya lagna), or `ASC` (cusp-based). The reference value is
  **part of the path**, so two rules differing only in reference are distinct
  conditions. Future reference points (e.g. `ARUDHA`, `Ghati`, or a
  house-cusp anchor) are **additive vocabulary additions**: append the value
  to the `<REF>` enum, extend snapshot normalization (§6.3) to compute the
  relative house for that anchor from the same JRE-003 `NatalChart`, and
  bump `FACT_VOCABULARY_VERSION`. Existing rules are unaffected. Unknown
  `<REF>` ⇒ `RuleSchemaError` at load.
- Multi-value paths (`pair(...).aspects`, `transit(...).kind`,
  `eclipse.kind`) evaluate as list membership: `EQ` = the list contains the
  value; `IN` = any of the literal values is in the list; `EXISTS` = list
  non-empty.

### 6.3 Snapshot normalization (JRE-003 interface, req: interfaces)

`synthesis.normalize_snapshot(jyotish_outputs) -> dict` accepts the JRE-003
public outputs and produces the `fact_snapshot` dict:

- `tuple[PlanetState, ...]` → `{"planets": [{body, rashi, nakshatra, pada,
  degree_in_rashi, retrograde}], "pairs": [...]}` (pairs from
  `pair_geometry` when provided; otherwise computed by the caller).
- `NatalChart` → adds `{"lagna": {...}, "bhavas": [{house_number,
  house_lord, occupants}], "relative_houses": {body: house}}`.
- `tuple[TransitEvent, ...]` → `{"transits": {body: [kinds]}}`.
- `EclipseEvent` set → `{"eclipses": {"kinds": [...], "classifications":
  [...]}}`.
- The caller may also pass a pre-built dict (opaque round-trip). Mixed input
  is validated; unknown objects ⇒ `SynthesisError`.

### 6.4 Domain-section requirements

Each `RuleDomain` declares the snapshot sections its conditions may touch
(`DOMAIN_REQUIREMENTS` in `schema.py`): `YOGA_DEFINITION`/`KARAKA`/
`BHAVA_MEANING` require `planets` (+ optionally `bhavas`/`lagna`);
`DRISHTI` requires `pairs`; `DASHA_APPLICATION`/`NAKSHATRA_CHARACTER`
require `planets` with nakshatra data; `GOCHAR_SIGNIFICATION` requires
`transits`; `ECLIPSE_SIGNIFICATION` requires `eclipses`; `GENERAL` requires
`planets`. A query whose domain requirements are not met by the snapshot ⇒
`SynthesisError` (deterministic, at query validation).

## 7. Rule catalogs and versioning

- Rule catalogs: `datasets/knowledge/rules/<catalog>.json`, each with
  `catalog_id` (e.g. `rules:yoga`), `catalog_version` (semver), and
  checksum.
- **CODING authoring scope** (resolves architecture §24.1): ship ≥ 3
  catalogs, each ≥ 5 ACTIVE rules: `rules:yoga` (`YOGA_DEFINITION`),
  `rules:drishti` (`DRISHTI`), `rules:karaka` (`KARAKA`/`BHAVA_MEANING`).
  Content is authored data citing the §4 editions; rules must exercise all
  ops/combiners and at least one `conflicts_with` pair and one
  `exception_for` chain (to prove the machinery).
- `rules.py` loads + validates all catalogs at construction; version pins in
  `KnowledgeConfig.rule_catalog_versions` enforced.
- **Conflict-declaration validation** (resolves architecture §24.2):
  `conflicts_with` must be symmetric (a lists b ⇒ b lists a) — asymmetry ⇒
  `ConflictResolutionError`. `exception_for` targets must exist and share
  the rule's `domain` — unknown target or domain mismatch ⇒
  `RuleSchemaError`.

## 8. Rule precedence (deterministic total order)

`precedence.py` — pure comparator over the matched ACTIVE rules in a
profile. Key (higher first):

1. `source_priority_rank` — index of the rule's primary `source_id` in
   `TraditionProfile.source_priority` (lower index = higher priority).
2. `specificity` — count of **atoms** in the condition tree (more = higher).
3. `authority_tier` (1–5, higher = higher).
4. `rule_version` — semver, newer first.
5. `rule_id` — lexicographic ascending (tiebreak).

`precedence_key` on `ResolvedRule` = `(source_priority_rank, -specificity,
-authority_tier, -semver_tuple(rule_version), rule_id)` (negated numeric
fields so Python's ascending tuple sort yields higher-first). The algorithm
name in `SearchMetadata.algorithm` = `"profile-precedence-order"`.

## 9. Conflicts and exceptions

### 9.1 Conflicts (same-priority disagreement)

- Detection (`resolution.py`): for matched ACTIVE rules, pair a rule A with
  each rule in `A.conflicts_with` that also matched. (Structural
  contradiction detection is NOT used for suppression — the architecture's
  §24.2 hybrid is resolved as: **explicit pairs primary; structural
  contradiction is a load-time validation warning only**, recorded in the
  catalog load log, never auto-suppressing.)
- `FIRST_WINS` (profile policy or config default): the higher-precedence
  rule is kept in `matched_rules`; the lower moves to `suppressed_rules`
  with `status_note="suppressed by <id>"`; a `ConflictRecord` is always
  emitted.
- `REPORT_ALL`: both remain in `matched_rules`; a `ConflictRecord` with
  `resolution="reported together"` is emitted; nothing is suppressed.

### 9.2 Exceptions (overrides)

- A rule E with `exception_for=(B1, B2)` that matches **overrides** every
  matched base rule Bi in the same profile scope, regardless of normal
  precedence: Bi moves to `suppressed_rules` with
  `status_note="overridden by exception <E.id>"`; a `ConflictRecord` with
  `resolution="exception"` is emitted naming E and Bi.
- If multiple matching exceptions target the same base rule, the
  higher-precedence exception wins (using §8 ordering among the exceptions);
  the loser is suppressed with `status_note` recording the exception
  conflict. `REPORT_ALL` does not change exception semantics — exceptions
  always override (they are authored overrides); the record is still emitted.
- `exception_for` cycles (E1 overrides E2 and E2 overrides E1) ⇒
  `ConflictResolutionError` at load.

## 10. Scoring / weighting / confidence model (deterministic metadata)

### 10.1 `effective_weight` (display/ordering scalar)

`effective_weight = round(authority_tier + 0.5*specificity + 0.05*(N_sources
− source_priority_rank), 4)` where `N_sources` = length of the profile's
`source_priority`. The formula **increases with each precedence factor of
§8** (higher tier, higher specificity, and higher source-priority rank each
raise the weight), but it is a **display/ordering scalar only**: it is not
guaranteed to reproduce `matched_rules` order (the §8 key is lexicographic
and factor-dominant; the scalar mixes factors with different coefficients).
Consumers must use `matched_rules` order for semantics.

### 10.2 `credibility` (evidence confidence, NOT prediction)

`credibility = round(0.55·(authority_tier/5) + 0.30·provenance_completeness
+ 0.15·min(specificity/5, 1.0), 4) ∈ [0, 1]` where
`provenance_completeness` = 1.0 (source+chapter+verse+edition),
0.85 (source+chapter+verse), 0.7 (source+chapter), 0.5 (source only).

- Credibility measures **attribution and condition quality**, never
  real-world outcome likelihood. Docstring + static gate: no engine code may
  present `credibility` as prediction confidence (identifier/comment gate in
  TEST-PLAN §8).
- `SynthesisResult.search_metadata` gains `credibility_summary = {mean, min,
  max, n}` over matched rules (deterministic).

## 11. Synthesis interface (`KnowledgeService`)

```python
class KnowledgeService:
    def __init__(self, config: KnowledgeConfig | None = None) -> None: ...
    def sources(self) -> tuple[Source, ...]
    def profiles(self) -> tuple[TraditionProfile, ...]
    def get_profile(self, profile_id: str) -> TraditionProfile   # UnknownProfileError
    def synthesize(self, query: RuleQuery) -> SynthesisResult
    def rule_catalog_versions(self) -> dict[str, str]
```

`synthesize` pipeline (deterministic):

1. Resolve profile (`query.profile_id` or config default) →
   `UnknownProfileError` if unknown.
2. Validate query: domain-section requirements (§6.4) against the snapshot →
   `SynthesisError`; `include_suppressed` honored.
3. Filter ACTIVE rules: profile `domains` scope + `tradition_tags` overlap +
   `included_sources` contains the rule's primary source.
4. Evaluate conditions (§6.1) → matched set (deterministic, no short-circuit
   across rules — every rule's condition is evaluated; `rules_evaluated`
   counts them).
5. Apply exceptions (§9.2), then conflicts (§9.1) per profile policy.
6. Order `matched_rules` by §8; compute `ResolvedRule` metadata (§10).
7. Build `provenance_index`, `search_metadata` (catalog versions,
   `rules_evaluated`, `rules_matched`, `credibility_summary`), echo
   `query`/`profile`/`config`.

Determinism: identical `(query, profile version, source/rule/profile catalog
versions, config)` ⇒ byte-identical JSON (cross-process tested).

## 12. Interfaces with JRE-003 / JRE-005 / JRE-006 / JRE-007

### 12.1 JRE-003 (upstream facts)

- `knowledge` consumes JRE-003's **public outputs only**:
  `PlanetState`, `PairGeometry`, `NatalChart`, `TransitEvent`,
  `EclipseEvent`, and the `jyotish` enums. No astronomy calls, no swisseph.
- Fact snapshot normalization: §6.3. The vocabulary (§6.2) is the contract;
  a JRE-003 model change is a versioned vocabulary change
  (`FACT_VOCABULARY_VERSION` bump) — never silent.
- Birth data never enters `knowledge`: snapshots are already-anonymized
  facts (architecture §17).

### 12.2 JRE-005 / JRE-006 / JRE-007 (future consumer engines)

The numbering note in the architecture header stands: future engines are
numbered at REQUEST time starting at JRE-005+. The **consumer contract** for
all of them (defined now, ADR-011):

- Each future engine imports `knowledge`'s public API and calls
  `KnowledgeService.synthesize(RuleQuery(domain=<its domain>,
  fact_snapshot=<normalized JRE-003 output>, profile_id=<explicit>))`.
- It consumes `SynthesisResult`: `matched_rules` (ordered `ResolvedRule`s
  with provenance + weight + credibility), `conflicts`,
  `suppressed_rules`, `provenance_index`, `profile`, `config`.
- Expected initial mappings (confirmed at each engine's REQUEST):
  - JRE-005 (e.g. Yoga engine) → `domain=YOGA_DEFINITION`,
    catalogs `rules:yoga`.
  - JRE-006 (e.g. Dasha engine) → `domain=DASHA_APPLICATION` +
    `NAKSHATRA_CHARACTER`, catalogs `rules:dasha-*`.
  - JRE-007 (e.g. Drishti/Gochar engine) → `domain=DRISHTI` +
    `GOCHAR_SIGNIFICATION` + `ECLIPSE_SIGNIFICATION`, catalogs
    `rules:drishti`, `rules:gochar`.
- Guarantees: engines never read catalog files; new domains/catalogs are
  **data additions** (a new `RuleDomain` value is a versioned enum addition
  requiring a spec bump, but no engine rewrite); JRE-004 never imports them.

## 13. Configuration

`config/knowledge.toml`:

```toml
default_profile_id = "bphs-classical"
default_conflict_policy = "FIRST_WINS"
source_catalog_version = ""
rule_catalog_versions = {}
profile_catalog_version = ""
enforce_provenance = true
verify_checksums = true
max_rules_per_synthesis = 200
```

- Empty-string pins mean "unpinned" (loaded catalog versions are still
  echoed). Pins enforce exact-match (mismatch ⇒ `CatalogIntegrityError`).
- Validation at load: `max_rules_per_synthesis > 0`; enum fields valid;
  `default_profile_id` exists in the profile catalog
  (`UnknownProfileError` at construction).

## 14. Tradition profiles

`datasets/knowledge/profiles/profiles.json` — `PROFILE_CATALOG_VERSION =
"1.0.0"`. Initial profiles (explicit source priority, ADR-010):

| profile_id | name | source_priority | conflict_policy |
|---|---|---|---|
| `bphs-classical` (default) | BPHS Classical | `bphs, brihat-jataka, jataka-parijata, phaladeepika` | FIRST_WINS |
| `brihat-jataka` | Bṛhat Jātaka | `brihat-jataka, bphs, jataka-parijata, phaladeepika` | FIRST_WINS |
| `jataka-parijata` | Jātaka Pārijāta | `jataka-parijata, brihat-jataka, phaladeepika, bphs` | FIRST_WINS |
| `phaladeepika` | Phaladīpikā | `phaladeepika, jataka-parijata, brihat-jataka, bphs` | FIRST_WINS |
| `surya-siddhanta-vedanga` | Sūrya Siddhānta / Vedāṅga | `surya-siddhanta` (alone) | REPORT_ALL |
| `regional-kerala` | Kerala (Praśna) | `prasna-marga, bphs, phaladeepika` | FIRST_WINS |
| `regional-north-indian` | North Indian (Sārāvalī) | `saravali, bphs, brihat-jataka` | FIRST_WINS |

- `domains=None` = all domains (all initial profiles). `passthrough_config`
  allow-list (resolution of architecture §24.4): `ayanamsa`, `house_system`,
  `node_model`, `zodiac_mode`, `position_type` — values validated against
  `jyotish` enum types (e.g. `ayanamsa: "LAHIRI"`); unknown field or bad
  value ⇒ `InvalidConfigError`-family error.

## 15. Serialization

- `serialize.py`: `result_to_json`/`result_to_dict` for `SynthesisResult`,
  `Source` set, `TraditionProfile` set; input parsers
  (`rule_query_from_dict`, `config_from_dict`, `provenance_from_dict`).
- Conventions identical to JRE-002/JRE-003: UTF-8, snake_case, enum →
  string, tuple → array, `None` → null, floats via round-trip repr,
  `-0.0 → 0.0`. `fact_snapshot` opaque byte round-trip.
- JSON Schemas per DATA-CONTRACT §10 (`additionalProperties: false`).

## 16. Determinism and the calculation identity

Identical `(RuleQuery incl. fact_snapshot, profile version, source catalog
version, rule catalog versions, FACT_VOCABULARY_VERSION, KnowledgeConfig)`
⇒ bit-identical `SynthesisResult`. `SearchMetadata.catalogs` echoes all
versions; `credibility_summary` and `rules_evaluated` are pure functions of
the inputs.

## 17. Error taxonomy (`errors.py`)

| Error | Raised when |
|---|---|
| `KnowledgeError` | base class |
| `UnknownSourceError` | `source_id` not in the registry |
| `UnknownEditionError` | `edition_id` unresolvable for a source |
| `UnknownProfileError` | `profile_id` not registered |
| `RuleSchemaError` | rule fails schema / vocabulary validation |
| `ProvenanceError` | rule without mandatory provenance (when enforced) |
| `CatalogIntegrityError` | checksum or version-pin mismatch |
| `ConflictResolutionError` | asymmetric `conflicts_with`, `exception_for` cycle, malformed declaration |
| `SynthesisError` | snapshot missing a domain-required section; snapshot normalization failure |

All errors expose the offending value in `__str__`.

## 18. Static / structural gates

1. `test_public_surface.py` — `knowledge.__all__` matches the allow-list.
2. `test_forbidden_imports.py` — no `astronomy|swisseph|inference|
   astrology|transits|dasha|calculations|gochar|rules`; no
   `socket|requests|urllib|httpx`; `models.py` stdlib-only; `knowledge`
   imports `jyotish` public API only.
3. `test_no_prediction.py` — no conclusion-evaluation code path; no engine
   code presents `credibility`/`effective_weight` as outcome likelihood
   (identifier/comment scan); `RuleConclusion.structured` opaque.
4. `test_astronomy_unmodified.py` + `test_jyotish_unmodified.py` —
   `src/astronomy` and `src/jyotish` file sets + `__all__` unchanged.
5. `test_no_personal_data.py` — no birth-data concept in `src/knowledge`.
6. `test_no_network.py` — conftest asserts `socket` never called.

## 19. Performance budget (informational)

- Catalog load (sources + profiles + 3 rule catalogs): < 100 ms.
- Synthesis of ≤ 200 rules against a snapshot: p95 < 50 ms.
- No multiprocessing; catalogs immutable after construction.

## 20. Validation strategy (VALIDATOR)

| Domain | Reference | Assertion |
|---|---|---|
| Rule content vs cited text | Committed excerpts of the §4 editions (e.g. BPHS ch. 25) | rule `conclusion.statement` agrees with the standard reading of the cited verse |
| Source registry metadata | Standard bibliographies | name/author/period consistent |
| Precedence/conflict/exception behavior | Hand-computed golden orders | exact match |
| Weight/credibility | Independent reimplementation of §10 formulas | exact match |
| Fact vocabulary | Real JRE-003 result payloads | every path resolves; types match |

Offline; committed under `datasets/validation/knowledge/`.

## 21. CODING handoff checklist

- [ ] `pyproject.toml` adds `knowledge` package + `tests/*/knowledge`
      testpaths (build metadata only; JRE-002/JRE-003 untouched).
- [ ] Implement in order: `models.py` (DATA-CONTRACT v0.3.0) → `errors.py` →
      `sources.py` → `provenance.py` → `schema.py` → `rules.py` →
      `traditions.py` → `resolution.py` → `precedence.py` → `synthesis.py` →
      `config.py` → `serialize.py` → `service.py`.
- [ ] Author data: `datasets/knowledge/sources/sources.json` (7 sources +
      editions, checksummed), `profiles/profiles.json` (7 profiles),
      `rules/rules:yoga.json`, `rules:drishti.json`, `rules:karaka.json`
      (the ≥ 3 catalogs, ≥ 5 rules each, incl. ≥ 1 `conflicts_with` pair
      and ≥ 1 `exception_for` chain).
- [ ] Ship CODING happy-path tests (TEST-PLAN §14).
- [ ] Gate before QA: `pytest tests/unit tests/integration`,
      `ruff check src tests`, `mypy src/knowledge`; static gates §18 green;
      `src/astronomy` + `src/jyotish` untouched.
- [ ] Do NOT implement: text ingestion, prediction/interpretation logic,
      rule-authoring tools, network access, anything in JRE-002/JRE-003.

## 22. Unresolved questions (for Architect/Validator)

1. **Default profile** — `bphs-classical` is the explicit default; Validator
   confirms the priority order against published tradition summaries.
2. **Credibility constants** — the 0.55/0.30/0.15 weights and completeness
   levels (§10.2) are pinned proposals; Validator/Architect may tune them as
   a versioned decision (they never affect rule *selection*).
3. **Edition records** — exact bibliographic details for the §4 editions to
   be finalized by CODING with real-world records (checksummed).
4. **Domain enum growth** — new `RuleDomain` values for future engines are
   versioned enum additions (spec bump); confirmed at each engine's REQUEST.
5. **`relative_house` reference** — defined as natal house relative to
   LAGNA (default reference); a future engine needing Moon/Sun reference
   adds a vocabulary path (versioned).

## 23. Change history

| Version | Date | Change |
|---|---|---|
| 0.2.0 | 2026-08-12 | Architecture (design level) |
| 0.3.0 | 2026-08-12 | Specialist implementation spec (this document); supersessions in the notice block |
