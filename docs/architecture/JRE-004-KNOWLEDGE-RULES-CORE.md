# JRE-004 — Classical Knowledge & Rule Engine: Architecture and Refined Specification

- Status: ARCHITECTED
- Version: 0.2.0 (refined from the JRE-004 request v0.1.0)
- Date: 2026-08-12
- Queue item: [JRE-004-CLASSICAL-KNOWLEDGE](../../orchestration/queue/JRE-004-CLASSICAL-KNOWLEDGE.md)
- Related decisions:
  [ADR-007 Knowledge Package Placement](../decisions/ADR-007-KNOWLEDGE-PACKAGE-PLACEMENT.md),
  [ADR-008 Source Registry and Provenance](../decisions/ADR-008-SOURCE-REGISTRY-PROVENANCE.md),
  [ADR-009 Rule Schema](../decisions/ADR-009-RULE-SCHEMA.md),
  [ADR-010 Tradition Profiles, Precedence, and Conflict Resolution](../decisions/ADR-010-TRADITION-PROFILES-PRECEDENCE-CONFLICT.md),
  [ADR-011 Synthesis Interface](../decisions/ADR-011-SYNTHESIS-INTERFACE.md)
- Upstream: [JRE-003 Specialist Spec](JRE-003-SPECIALIST-SPEC.md), [JRE-003 Data Contract](JRE-003-DATA-CONTRACT.md), [JSP-001 Core Specification](../../specifications/core/JSP-001.md)

> **Numbering note (supersedes JRE-003 spec §future informal naming):** the
> JRE-003 Specialist Spec's "future-compatibility" section informally listed
> "JRE-004 relationship engine / JRE-005 bhava engine / JRE-006 transit engine
> / JRE-007 eclipse engine" as consumer engines. Those capabilities already
> ship inside `jyotish` (PairGeometry, Bhava, transit events, eclipse
> interface). The user has assigned the next number to a different,
> higher-layer item — the **Classical Knowledge & Rule Engine** — tracked as
> `JRE-004-CLASSICAL-KNOWLEDGE`. The informal engine names from the JRE-003
> spec are **not** created as separate tasks; future interpretation engines
> (Yoga, Dasha, Drishti, Gochar, Nakshatra interpretation, multi-layer
> synthesis, prediction/confidence) will be numbered at REQUEST time starting
> at JRE-005+.

## 1. Purpose

This document refines the JRE-004 request ("Classical Knowledge & Rule
Engine") into an implementable design. JRE-004 sits **above** the merged
JRE-002 astronomical core and the JRE-003 Jyotish coordinate/state layer,
and **below** all future interpretation/synthesis engines (Yoga, Dasha,
Drishti, Gochar interpretation, Nakshatra interpretation, multi-layer
synthesis, prediction/confidence).

It is the authoritative handoff from the **Architect** to the **Specialist**
for the Knowledge (JSP-001 layer 3) and Rules (JSP-001 layer 5) capabilities:
a **machine-readable classical knowledge base** with full provenance, and the
**deterministic rule machinery** (registry, schema, tradition profiles, rule
precedence, conflict resolution, synthesis interface) that future engines
consume.

JRE-004 does **not** ingest texts, does **not** evaluate predictions, and
does **not** touch JRE-002 or JRE-003.

## 2. Scope

| Req | Capability | What JRE-004 provides |
|---|---|---|
| 1 | Source registry | Canonical, versioned registry of classical Jyotish sources: Bṛhat Parāśara Horā Śāstra (BPHS), Bṛhat Jātaka, Jātaka Pārijāta, Phaladīpikā, Sūrya Siddhānta / Vedāṅga-derived material, and later regional/classical sources. Each source: stable id, canonical name (IAST + common), author, period, language, lineage, editions/translations with bibliographic provenance |
| 2 | Rule schema | Declarative, machine-readable rule representation: id, domain/scope, condition (predicate over the pinned JRE-003 fact vocabulary), structured conclusion, authority, status, version. Rules are **data**, never code |
| 3 | Provenance system | Every rule carries a mandatory provenance chain: source → chapter → verse → edition/translation → translator/commentary lineage. Versioned catalogs with checksums; rules without provenance are rejected |
| 4 | Conflict-resolution mechanism | Deterministic, explicit policy for when rules from different sources disagree: precedence-winner or report-all-with-conflict-record. Conflicts are **recorded, never silent** |
| 5 | Tradition profiles | Named, versioned bundles: `bphs-classical`, `brihat-jataka`, `jataka-parijata`, `phaladeepika`, `surya-siddhanta-vedanga`, `regional-*`. Each profile: included sources, source priority order, default conflict policy, domain scope, passthrough config. No hidden defaults |
| 6 | Rule precedence | Deterministic total order over applicable rules within a profile: profile source priority → rule specificity → authority tier → rule version → rule id tiebreak |
| 7 | Synthesis interface | `KnowledgeService.synthesize(query, profile, config) -> SynthesisResult`: matched rules ordered by precedence, conflict records, provenance index, config snapshot. The sole consumption surface for future engines |

Additional (req. 1–7 cross-cutting):

- **Fact vocabulary pinning** — rule conditions reference a pinned,
  versioned vocabulary of JRE-003 output fields (`PlanetState`,
  `PairGeometry`, `Bhava`, `LagnaState`, `TransitEvent`, `EclipseEvent`).
  Conditions referencing unknown fields fail validation.
- **Configuration** — `config/knowledge.toml`: default profile, default
  conflict policy, catalog versions, checksum policy. Explicit, echoed.
- **Reproducibility** — identical `(query, profile version, rule catalog
  version, fact snapshot, config)` ⇒ bit-identical synthesis output.
- **Separation** — JRE-004 stores and retrieves classical **rules with
  provenance**; it never emits a prediction itself. Whether a rule's
  conclusion is a "prediction" is data authored by the Rules agent, not
  engine behavior.

## 3. Non-goals (mandatory separation)

JRE-004 MUST NOT:

- **Ingest texts.** No full-text corpus parsing, no OCR, no embedding of
  classical manuscripts into the engine. Rules are authored (by the Rules
  agent per the agents model) as structured data citing sources; the source
  registry holds bibliographic provenance, not prose.
- **Implement predictions.** The engine does not evaluate "good/bad",
  benefic/malefic, wealth/marriage/career/health outcomes, muhurta
  recommendations, or eclipse causation. It returns rules whose conditions
  match the supplied facts, ordered and annotated. Interpretation of those
  rules belongs to future engines.
- **Modify JRE-002 (`src/astronomy`) or JRE-003 (`src/jyotish`).** JRE-004
  consumes JRE-003's public output only. Static gates enforce this.
- **Import astronomy directly or use the ephemeris binding.**
  `knowledge` may import `jyotish` public API (for the fact vocabulary and
  types) but never `astronomy`, never `swisseph`, never `astronomy.swisseph`.
- **Use the network at runtime.** All catalogs are committed data.
- **Evaluate astrology.** Rule *conditions* may reference Jyotish facts
  (Rashi, Nakshatra, Bhava, aspects); that is the layer's purpose. But no
  module in `knowledge` may contain benefic/malefic/prediction logic — only
  data that future engines consume.

Reviewers must reject any change that turns a knowledge datum into a
prediction-producing code path, or that imports forbidden subsystems.

## 4. Design principles

1. **Rules are data, engine is machinery.** The rule engine implements
   registry, schema validation, provenance integrity, profile selection,
   precedence ordering, conflict recording, and synthesis — nothing else.
2. **Provenance-first.** A rule without a verifiable source reference is not
   a rule. Provenance is mandatory, versioned, checksummed, and echoed in
   every synthesis result.
3. **Explicit tradition.** Every synthesis runs inside a named, versioned
   tradition profile with an explicit source-priority order and conflict
   policy. There is no "unprofiled" interpretation and no hidden default.
4. **Deterministic conflict handling.** Conflicting rules never silently
   override one another: the resolution policy is explicit, and every
   suppression is recorded as a `ConflictRecord`.
5. **Fact vocabulary is pinned.** Conditions bind only to a versioned
   vocabulary of JRE-003 output fields, so rule catalogs remain stable across
   engine versions and future engines can validate their inputs.
6. **Consumption by contract.** Future engines (Yoga, Dasha, Drishti,
   Gochar, Nakshatra interpretation, multi-layer synthesis, prediction) use
   `KnowledgeService`'s public surface only; they never read catalog files
   directly.
7. **Determinism.** Pure functions over immutable, versioned catalogs — no
   clocks, no randomness, no network, no iteration-order dependence.
8. **No personal data.** JRE-004 has no birth-data concept at all. Its
   inputs are fact snapshots (already anonymized astronomy/Jyotish output),
   a query, and a profile. Personal data never enters the knowledge layer.

## 5. Module layout

Following the established scaffold conventions (`src/`, `config/`,
`datasets/`, `tests/{unit,integration,validation}/`):

```
src/
  knowledge/
    __init__.py          # Public API allow-list (KnowledgeService, models, enums, errors)
    models.py            # Pure data: enums + frozen dataclasses (stdlib only)
    errors.py            # KnowledgeError hierarchy
    sources.py           # Source registry: versioned catalog of classical sources
    provenance.py        # Provenance chains: normalization, integrity, checksums
    schema.py            # Rule schema: condition grammar + fact-vocabulary validation
    rules.py             # Rule catalog: load, validate, version, registry
    traditions.py        # Tradition profiles: definition, registry, source priority
    resolution.py        # Conflict detection + resolution policies
    precedence.py        # Deterministic rule precedence computation
    synthesis.py         # Synthesis engine: query -> ordered rules + conflicts
    config.py            # config/knowledge.toml -> KnowledgeConfig
    serialize.py         # result_to_json / from_dict (JSON Schema per DATA-CONTRACT)
    service.py           # KnowledgeService — deterministic facade

config/
  knowledge.toml         # Defaults: profile, conflict policy, catalog versions

datasets/
  knowledge/
    sources/             # Pinned source catalog + editions (JSON, checksummed)
    rules/               # Authored rule catalogs (JSON, versioned, checksummed)
    profiles/            # Tradition profile definitions (JSON, versioned)
    README.md            # Provenance, versions, licenses

tests/
  unit/knowledge/        # Pure logic: schema, precedence, conflict, provenance — no jyotish
  integration/knowledge/ # With JRE-003 facts: synthesis against real fact snapshots
  validation/knowledge/  # Independent cross-source validation harness (VALIDATOR)
```

Conventions:

- Package root `knowledge` (import name), versioned independently; a `jre.`
  namespace root is a later, separately-versioned refactor — never silent.
- `models.py` imports stdlib only (same rule as JRE-002/JRE-003).
- `knowledge` imports from `jyotish`'s **public API only** (models/enums for
  the fact vocabulary and types). It never imports `astronomy`, `swisseph`,
  or `astronomy.swisseph` (enforced by a static test).
- No `knowledge` module may import `inference`, `astrology`, `transits`,
  `dasha`, `calculations`, or `gochar` (future-engine namespaces).
- Rule catalogs are data files, validated against the schema at load time;
  invalid or unprovenanced rules fail loudly (never silently skipped).

## 6. Data contracts (design level)

Design-level models are specified here; the authoritative field-level
contract for CODING is
[JRE-004-DATA-CONTRACT.md](JRE-004-DATA-CONTRACT.md) v0.2.0 (the Specialist
may refine it to v0.3.0). All models are `@dataclass(frozen=True)`; enums are
`str`-based; JSON values are enum string values.

### 6.1 Enums (design level)

```python
class SourceStatus(StrEnum):        CANONICAL, SUPPLEMENTAL, REGIONAL, HISTORICAL
class RuleStatus(StrEnum):          ACTIVE, DEPRECATED, SUPERSEDED
class RuleDomain(StrEnum):          # extensible; authored catalogs may add values
    KARAKA, BHAVA_MEANING, DRISHTI, YOGA_DEFINITION, NAKSHATRA_CHARACTER,
    DASHA_APPLICATION, GOCHAR_SIGNIFICATION, ECLIPSE_SIGNIFICATION, GENERAL
class ConflictPolicy(StrEnum):      FIRST_WINS, REPORT_ALL
class ConditionOp(StrEnum):         EQ, NEQ, LT, LTE, GT, GTE, IN, NOT_IN, EXISTS
class ConditionCombiner(StrEnum):   ALL, ANY, NOT
```

> **Boundary:** `RuleDomain` values are *catalog labels*, not engine
> behavior. The engine never interprets a domain; it groups and orders rules
> by it. `DRISHTI`/`YOGA_DEFINITION`/`DASHA_APPLICATION`/… are legal *rule
> kinds* — the future engines consume them; JRE-004 merely ships them with
> provenance and precedence.

### 6.2 `KnowledgeConfig` (frozen dataclass) — explicit, echoed

| Field | Type | Default | Semantics |
|---|---|---|---|
| `default_profile_id` | `str` | `"bphs-classical"` | profile used when none supplied (explicit default) |
| `default_conflict_policy` | `ConflictPolicy` | `FIRST_WINS` | used when profile lacks a policy |
| `source_catalog_version` | `str \| None` | `None` | pin; mismatch ⇒ error |
| `rule_catalog_versions` | `dict[str, str]` | `{}` | per-catalog pins |
| `profile_catalog_version` | `str \| None` | `None` | pin |
| `enforce_provenance` | `bool` | `True` | reject rules without full provenance |
| `verify_checksums` | `bool` | `True` | verify catalog checksums at load |
| `max_rules_per_synthesis` | `int` | `200` | upper bound on returned rules (documented) |

### 6.3 Core models (design level)

```python
@dataclass(frozen=True)
class Source:                                    # req 1
    source_id: str                               # stable slug, e.g. "bphs"
    canonical_name: str                          # IAST, e.g. "Bṛhat Parāśara Horā Śāstra"
    common_name: str                             # e.g. "BPHS"
    author: str | None                           # e.g. "Parāśara (attrib.)"
    period: str | None                           # e.g. "~600–800 CE"
    language: str                                # e.g. "Sanskrit"
    lineage: tuple[str, ...]                     # tradition tags, e.g. ("parashari",)
    status: SourceStatus
    editions: tuple[Edition, ...]                # bibliographic provenance
    catalog_version: str

@dataclass(frozen=True)
class Edition:
    edition_id: str
    title: str
    translator: str | None
    publisher: str | None
    year: str | None
    language: str
    notes: str | None

@dataclass(frozen=True)
class ProvenanceRef:                             # req 3
    source_id: str
    chapter: str | None                          # e.g. "25" (verse-block or chapter)
    verse_start: str | None
    verse_end: str | None
    edition_id: str | None                       # which edition/translation is cited
    commentary: str | None                       # optional commentary lineage note

@dataclass(frozen=True)
class RuleCondition:                             # req 2
    combiner: ConditionCombiner | None           # None for a single atom
    op: ConditionOp | None                       # set for atoms
    path: str | None                             # fact-vocabulary path, e.g. "planet(MOON).rashi"
    value: object | None                         # literal, e.g. "VRISHABHA"
    children: tuple[RuleCondition, ...]          # for ALL/ANY/NOT

@dataclass(frozen=True)
class RuleConclusion:                            # structured, machine-readable
    kind: str                                    # e.g. "CLASSIFICATION" | "SIGNIFICATION" | "APPLICATION"
    statement: str                               # canonical, citation-grounded text
    structured: dict[str, object]                # optional keyed fields (no free-form predictions)

@dataclass(frozen=True)
class Rule:                                      # req 2
    rule_id: str                                 # stable, e.g. "bphs.25.12.1"
    domain: RuleDomain
    summary: str
    condition: RuleCondition                     # predicate over the fact vocabulary
    conclusion: RuleConclusion
    provenance: ProvenanceRef                    # primary source reference (mandatory)
    supporting_refs: tuple[ProvenanceRef, ...]   # additional citations (optional)
    conflicts_with: tuple[str, ...]              # authored conflict declarations (rule_ids)
    authority_tier: int                          # 1..5, authored strength (not computed)
    status: RuleStatus
    tradition_tags: tuple[str, ...]
    rule_version: str                            # semver of this rule datum

@dataclass(frozen=True)
class TraditionProfile:                          # req 5
    profile_id: str
    name: str
    version: str
    description: str
    included_sources: tuple[str, ...]            # source_ids
    source_priority: tuple[str, ...]             # explicit priority order (subset/permutation)
    conflict_policy: ConflictPolicy
    domains: tuple[RuleDomain, ...] | None       # None = all domains
    passthrough_config: dict[str, object]        # e.g. {"ayanamsa": "LAHIRI"} — never interpreted here

@dataclass(frozen=True)
class ConflictRecord:                            # req 4
    rule_a_id: str
    rule_b_id: str
    reason: str                                  # e.g. "same domain, contradictory conclusions"
    resolution: str                              # e.g. "a wins by profile priority" / "reported together"
    policy: ConflictPolicy

@dataclass(frozen=True)
class RuleQuery:                                 # req 7 input
    domain: RuleDomain | None
    fact_snapshot: dict[str, object]             # JRE-003 output (already anonymized facts)
    profile_id: str | None                       # None => KnowledgeConfig.default_profile_id
    include_suppressed: bool = False             # FIRST_WINS: also return suppressed rules?

@dataclass(frozen=True)
class SynthesisResult:                           # req 7 output
    query: RuleQuery                             # echo (fact snapshot echoed verbatim)
    profile: TraditionProfile                    # resolved profile (echo)
    matched_rules: tuple[Rule, ...]              # ordered by precedence
    suppressed_rules: tuple[Rule, ...]           # when FIRST_WINS and include_suppressed
    conflicts: tuple[ConflictRecord, ...]        # never empty if suppression happened
    provenance_index: dict[str, tuple[str, ...]] # rule_id -> provenance strings
    config: KnowledgeConfig                      # config snapshot
    search_metadata: SearchMetadata              # counts, versions (determinism echo)

@dataclass(frozen=True)
class SearchMetadata:
    algorithm: str                               # e.g. "profile-precedence-order"
    catalogs: dict[str, str]                     # catalog id -> version used
    rules_evaluated: int
    rules_matched: int
```

### 6.4 Fact vocabulary (pinned)

Rule conditions reference a versioned vocabulary of JRE-003 output paths:

| Path pattern | Resolves to | Example |
|---|---|---|
| `planet(<BODY>).rashi` | `PlanetState.rashi` | `planet(MOON).rashi == "VRISHABHA"` |
| `planet(<BODY>).nakshatra` | `PlanetState.nakshatra` | `planet(SUN).nakshatra == "ASHWINI"` |
| `planet(<BODY>).pada` | `PlanetState.pada` | `planet(MOON).pada == 1` |
| `planet(<BODY>).degree_in_rashi` | `PlanetState.degree_in_rashi` | `planet(JUPITER).degree_in_rashi < 5.0` |
| `planet(<BODY>).retrograde` | `PlanetState.retrograde` | `planet(MARS).retrograde == "RETROGRADE"` |
| `lagna.rashi` | `LagnaState.rashi` | `lagna.rashi == "KARKA"` |
| `lagna.nakshatra` | `LagnaState.nakshatra` | `lagna.nakshatra == "PUSHYA"` |
| `bhava(<N>).house_lord` | `Bhava.house_lord` | `bhava(9).house_lord == "JUPITER"` |
| `bhava(<N>).occupants` | `Bhava.occupants` | `bhava(7).occupants` contains `"VENUS"` |
| `pair(<A>,<B>).conjunction` | `PairGeometry.conjunction` | `pair(MOON,JUPITER).conjunction == true` |
| `pair(<A>,<B>).aspects` | `PairGeometry.aspects` | `pair(MARS,SATURN).aspects` exists kind `"OPPOSITION"` |
| `transit(<BODY>).kind` | `TransitEvent.kind` | `transit(JUPITER).kind == "RASHI_INGRESS"` |
| `eclipse.kind` / `eclipse.classification` | `EclipseEvent` fields | `eclipse.kind == "SOLAR"` |

- The vocabulary table itself is versioned (`FACT_VOCABULARY_VERSION`) and is
  part of the calculation identity.
- A rule whose condition references an unknown path or an invalid literal
  type is rejected at load (validation, not silent no-match).

## 7. Source registry (req 1, ADR-008)

`src/knowledge/sources.py` + `datasets/knowledge/sources/` provide a
canonical, versioned registry of classical sources:

- **Initial catalog** (authored at CODING/SPECIALIST as data, cited in
  `datasets/knowledge/sources/README.md`):
  - `bphs` — Bṛhat Parāśara Horā Śāstra (Parashari lineage)
  - `brihat-jataka` — Bṛhat Jātaka (Varāhamihira)
  - `jataka-parijata` — Jātaka Pārijāta (Vaidyanātha Dīkṣita)
  - `phaladeepika` — Phaladīpikā (Mantreśvara)
  - `surya-siddhanta` — Sūrya Siddhānta (Vedāṅga-derived astronomy)
  - `regional-*` — later regional/classical works (e.g. Kerala/Tamil/
    North-Indian lineages), each with lineage tags
- Each source: stable id, IAST + common name, author, period, language,
  lineage tags, status (canonical/supplemental/regional/historical), and
  edition list with full bibliographic fields.
- Catalog integrity: SHA-256 checksums per file, a `catalog_version`, and a
  README documenting provenance/version/license — mirroring the ephemeris and
  catalog discipline of JRE-002/ADR-001 and JRE-003/ADR-003.
- Registry functions: `get_source(id)`, `all_sources()`,
  `resolve_edition(source_id, edition_id)`; unknown ids raise typed errors.

## 8. Provenance system (req 3, ADR-008)

- Every `Rule` carries exactly one **primary** `ProvenanceRef` plus optional
  supporting refs. With `enforce_provenance=True` (default), a rule lacking a
  primary ref with at least a `source_id` fails catalog load.
- Provenance strings are canonical: `"BPHS ch.25 v.12 (tr. Sharma 2001)"`
  composed from the ref + resolved edition metadata. The
  `provenance_index` in `SynthesisResult` exposes every cited rule's full
  provenance string for audit.
- Checksums: `verify_checksums=True` validates catalogs at load; corruption
  raises a typed error rather than silently proceeding.

## 9. Rule schema (req 2, ADR-009)

- Rules are authored as JSON data files under `datasets/knowledge/rules/`
  (one catalog per domain or source), validated against the schema
  (`src/knowledge/schema.py`) at load.
- The condition grammar is the recursive `RuleCondition` tree
  (`ALL`/`ANY`/`NOT` combiners; typed atoms with `ConditionOp`), evaluated
  deterministically against the pinned fact vocabulary.
- `RuleConclusion.structured` is a plain dict; the engine treats it as opaque
  data. There is **no** conclusion evaluator — no code path converts a rule
  into an outcome, score, or recommendation.
- Rules are versioned individually (`rule_version`) and by catalog; a change
  to a rule is a versioned decision (JSP-001 versioning rule).

## 10. Tradition profiles (req 5, ADR-010)

- Profiles are defined as data under `datasets/knowledge/profiles/` and
  registered by `traditions.py`. A profile names its included sources, an
  **explicit source-priority order**, its conflict policy, an optional domain
  scope, and passthrough config (e.g. ayanamsa preference) that is *echoed
  but never interpreted* by JRE-004.
- Initial profiles (defaults explicit in `config/knowledge.toml`):
  - `bphs-classical` (default) — BPHS-centric, BPHS > Bṛhat Jātaka >
    Jātaka Pārijāta > Phaladīpikā
  - `brihat-jataka` — Varāhamihira-centric
  - `jataka-parijata`
  - `phaladeepika`
  - `surya-siddhanta-vedanga` — astronomy/chronology-oriented
  - `regional-*` — per regional lineage, with its own priority order
- A synthesis always resolves a profile; there is no unprofiled mode.

## 11. Rule precedence (req 6, ADR-010)

Within a resolved profile, applicable rules are totally ordered by the
deterministic key (higher first):

1. **Profile source priority** — rank of the rule's primary `source_id` in
   `TraditionProfile.source_priority`.
2. **Rule specificity** — number of condition atoms (more specific =
   higher).
3. **Authority tier** — authored `authority_tier` (1–5).
4. **Rule version** — newer `rule_version` first (semver compare).
5. **Rule id** — lexicographic tiebreak.

`precedence.py` implements this as a pure comparator over the matched set;
the algorithm name is echoed in `SearchMetadata.algorithm`.

## 12. Conflict resolution (req 4, ADR-010)

- **Conflict detection** (`resolution.py`): two ACTIVE rules in the same
  domain whose conditions can both match the snapshot AND whose conclusions
  contradict (explicit `conflicts_with` pairs authored in the catalog, or a
  structural contradiction of `structured` keys) produce a `ConflictRecord`.
- **Policies** (from the profile, or config default):
  - `FIRST_WINS` — the higher-precedence rule is kept; the other is placed in
    `suppressed_rules`; a `ConflictRecord` is always emitted (never silent).
  - `REPORT_ALL` — both rules are returned with a `ConflictRecord` noting the
    disagreement; nothing is suppressed.
- The policy, the participants, and the resolution reason are all explicit in
  output. There is no hidden override path.

## 13. Synthesis interface (req 7, ADR-011)

`KnowledgeService` public surface (the only surface future engines use):

```python
class KnowledgeService:
    def __init__(self, config: KnowledgeConfig | None = None) -> None
    def sources(self) -> tuple[Source, ...]                       # registry query
    def profiles(self) -> tuple[TraditionProfile, ...]            # profile registry query
    def get_profile(self, profile_id: str) -> TraditionProfile   # typed error if unknown
    def synthesize(self, query: RuleQuery) -> SynthesisResult     # req 7 core
    def rule_catalog_versions(self) -> dict[str, str]             # determinism echo
```

`KnowledgeService.synthesize`:

1. Resolve profile (`query.profile_id` or config default).
2. Filter ACTIVE rules by profile domains + tradition tags.
3. Evaluate each rule's condition against the pinned fact vocabulary on
   `query.fact_snapshot` (pure, deterministic).
4. Order matches by precedence (§11).
5. Detect conflicts (§12) and apply the policy.
6. Return `SynthesisResult` with full echo (query, profile, config),
   ordered rules, suppression/conflict records, provenance index, and search
   metadata.

No other module reads catalog files; catalogs are loaded once at
construction (immutable, checksummed).

## 14. Separation of concerns

- JRE-004 never imports `astronomy`, `swisseph`, `inference`, `astrology`,
  `transits`, `dasha`, `calculations`, or `gochar`.
- The engine contains no benefic/malefic, auspiciousness, or outcome logic.
  Interpretation vocabulary may appear **only** as authored data (rule
  summaries/conclusions) — the engine treats it as opaque.
- Future engines import `knowledge`'s public API; `knowledge` never imports
  them. Static tests enforce both directions.

## 15. Configuration (req: no hidden defaults)

`config/knowledge.toml` declares: default profile id, default conflict
policy, catalog version pins, provenance/checksum enforcement flags, and the
per-synthesis rule bound. `KnowledgeConfig` is immutable and echoed in every
`SynthesisResult`.

## 16. Reproducibility (req: determinism)

Identical `(RuleQuery incl. fact_snapshot, profile version, source catalog
version, rule catalog versions, KnowledgeConfig)` ⇒ bit-identical
`SynthesisResult`. Enforced by:

1. Pinned, checksummed catalogs (ADR-008); profile + catalog versions echoed.
2. Frozen dataclasses; config + search metadata echoed everywhere.
3. Pure condition evaluation and a pure precedence comparator; no clocks,
   randomness, or network.
4. Cross-process determinism test (TEST-PLAN §4).

## 17. Data: no personal data

JRE-004 has no `BirthData` concept. Its only data input is
`RuleQuery.fact_snapshot` — anonymized JRE-003 output that the caller already
holds. Nothing is stored, persisted, or written to disk by the library.

## 18. Future extensibility

Future engines consume `KnowledgeService.synthesize`:

- **Drishti** — consumes `pair(...)` aspects facts + `DRISHTI` domain rules.
- **Yoga** — consumes classification rules (`YOGA_DEFINITION`) over
  planet/rashi/bhava facts; adds no engine change.
- **Dasha** — consumes `DASHA_APPLICATION` rules over Moon nakshatra/pada.
- **Gochar/Nakshatra interpretation, multi-layer synthesis,
  prediction/confidence** — consume `SynthesisResult` unchanged; new rule
  catalogs and domains are data additions, not engine changes.
- New sources/profiles/rules are **data**: adding a classical text or a
  regional lineage requires no change to the engine — only a versioned
  catalog update.

## 19. Testability

Full matrix in [JRE-004-TEST-PLAN.md](JRE-004-TEST-PLAN.md). Highlights:

- Schema validation: every mandated field, unknown paths rejected, type
  mismatches rejected, unprovenanced rules rejected.
- Precedence: ordering by each key in §11; tiebreaks deterministic.
- Conflict: FIRST_WINS suppresses with a record; REPORT_ALL never suppresses;
  no silent overrides.
- Provenance: every rule resolves to a real source/edition; checksum
  corruption detected.
- Synthesis: golden catalogs → expected ordered rules; determinism
  in-process + cross-process (byte-identical JSON).
- Static gates: forbidden imports, no prediction code path, JRE-002/003
  untouched, no personal data.
- Independent validation: cross-check authored rule content against the
  cited classical texts where a verse-level reference is checkable
  (VALIDATOR).

## 20. Error taxonomy

| Error | Raised when |
|---|---|
| `KnowledgeError` | base class |
| `UnknownSourceError` | `source_id` not in the registry |
| `UnknownEditionError` | `edition_id` not resolvable for a source |
| `UnknownProfileError` | `profile_id` not registered |
| `RuleSchemaError` | a rule fails schema / vocabulary validation |
| `ProvenanceError` | rule without mandatory provenance (when enforced) |
| `CatalogIntegrityError` | checksum mismatch or version pin mismatch |
| `ConflictResolutionError` | malformed conflict declaration |
| `SynthesisError` | snapshot missing a field required by a matched condition |

All errors expose the offending value in `__str__`; the service never
swallows a catalog/provenance error into a result.

## 21. Runtime and packaging requirements

- Python 3.12; target host 2 cores / 4 GB RAM (unchanged).
- New runtime dependency: **none** (stdlib + `jyotish` public API only).
- `pyproject.toml` gains `knowledge` package and `tests/unit/knowledge`,
  `tests/integration/knowledge` testpaths at CODING time.
- Performance budget (informational): synthesis of ≤ 200 rules against a
  fact snapshot < 50 ms with warm catalogs.

## 22. Validation strategy (VALIDATOR)

- Independent cross-source validation: for a sample of rules with verse-level
  references, confirm the rule's conclusion matches the cited text (where the
  edition is publicly checkable) — documents JRE-004's provenance claims.
- Precedence/conflict behavior is validated by golden catalogs with hand-
  computed expected orders (pure logic, no external reference needed).
- The harness runs offline against committed reference excerpts
  (`datasets/validation/knowledge/`); no network.

## 23. Downstream handoff checklist (SPECIALIST)

- [ ] `models.py` exactly per DATA-CONTRACT v0.2.0 (or refined v0.3.0)
- [ ] Source registry with initial catalog (BPHS, Bṛhat Jātaka, Jātaka
      Pārijāta, Phaladīpikā, Sūrya Siddhānta, ≥1 regional) + editions +
      checksums (ADR-008)
- [ ] Rule schema + fact-vocabulary validation; authored example catalogs
      for ≥ 3 domains incl. `YOGA_DEFINITION` and `DRISHTI` (ADR-009)
- [ ] Tradition profiles: the 6 initial profiles with explicit priority
      orders (ADR-010)
- [ ] Precedence comparator + conflict detection/policies (ADR-010)
- [ ] `KnowledgeService` public surface + serialization per DATA-CONTRACT
- [ ] `config/knowledge.toml` (every default explicit)
- [ ] Error taxonomy §20; static gates (no forbidden imports, no prediction
      code path, JRE-002/003 untouched)
- [ ] Tests per TEST-PLAN matrix; validation dataset scaffold
- [ ] No modification of `src/astronomy` (JRE-002) or `src/jyotish` (JRE-003)

## 24. Unresolved questions (for Specialist / Architect)

1. **Rule catalog authoring scope** — how many authored rules must CODING
   ship to demonstrate the engine (vs. leaving content to the Rules agent)?
   Proposal: ≥ 3 example catalogs, each ≥ 5 rules, covering
   `YOGA_DEFINITION`, `DRISHTI`, `KARAKA`/`BHAVA_MEANING`.
2. **Conflict declaration mechanism** — structural contradiction detection
   vs. explicit `conflicts_with` pairs; Specialist to pin the exact rule (a
   hybrid is expected: explicit pairs primary, structural as validation).
3. **Fact-vocabulary extent** — whether `TransitEvent`/`EclipseEvent` paths
   are in the initial vocabulary or deferred (they affect catalog authoring).
4. **Profile passthrough scope** — whether `passthrough_config` should be
   validated against `JyotishConfig` fields or left opaque.
5. **IAST canonical forms** — pin the romanization for source names and rule
   conclusions (mirrors JRE-003's nakshatra romanization decision).
6. **Regional sources** — which specific regional/classical texts the
   initial `regional-*` profiles cover (Specialist proposes, Architect
   approves; e.g. Prasna Marga, Kerala school, Tamil classical works).

## 25. Change history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | — | Original JRE-004 request |
| 0.2.0 | 2026-08-12 | Architecture + refined specification (this document) |
