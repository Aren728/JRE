# JRE-004 — Classical Knowledge & Rule Engine: Data Contract

- Status: SPECIALIZED
- Version: 0.3.0 (supersedes the design-level data contract v0.2.0)
- Date: 2026-08-12
- Upstream: [JRE-004 Architecture §6](JRE-004-KNOWLEDGE-RULES-CORE.md),
  [JRE-004 Specialist Spec](JRE-004-SPECIALIST-SPEC.md),
  [ADR-008](../decisions/ADR-008-SOURCE-REGISTRY-PROVENANCE.md),
  [ADR-009](../decisions/ADR-009-RULE-SCHEMA.md),
  [ADR-010](../decisions/ADR-010-TRADITION-PROFILES-PRECEDENCE-CONFLICT.md),
  [ADR-011](../decisions/ADR-011-SYNTHESIS-INTERFACE.md)

This document is the **field-level contract** for JRE-004's models. It
defines every enum, dataclass, JSON shape, and round-trip guarantee that
CODING must implement. Consumers (future interpretation engines) and QA test
against it.

> **Supersession notice (v0.3.0):** the Specialist adds `ResolvedRule`
> (wraps every matched/suppressed rule with `precedence_key`,
> `effective_weight`, `credibility`, `applicability`, `status_note`),
> `Rule.exception_for` (exceptions mechanism, SPEC §9.2), the
> `relative_house` fact-vocabulary path (SPEC §6.2), validated
> `passthrough_config` (SPEC §14), and the deterministic
> weight/credibility formulas (SPEC §10). `SynthesisResult.matched_rules`
> and `.suppressed_rules` are now `tuple[ResolvedRule, ...]`. These
> supersede the v0.2.0 field sets.

## 0. Conventions

- All models are `@dataclass(frozen=True)` (immutable, hashable).
- Enums are `str`-based; JSON value = enum string value.
- Tuples serialize as JSON arrays; `None` as `null`.
- Floats: IEEE-754 doubles, serialized with Python's round-trip repr — the
  JSON number decodes to the identical double.
- `fact_snapshot` is opaque to serialization: it round-trips as the JSON
  object the caller supplied (itself a JRE-003 result payload).
- Catalog files (sources, rules, profiles) are JSON documents under
  `datasets/knowledge/`, each carrying `catalog_version` and a checksum
  manifest.

## 1. Enums (string values are the JSON values)

| Enum | Values |
|---|---|
| `SourceStatus` | `CANONICAL`, `SUPPLEMENTAL`, `REGIONAL`, `HISTORICAL` |
| `RuleStatus` | `ACTIVE`, `DEPRECATED`, `SUPERSEDED` |
| `RuleDomain` | `KARAKA`, `BHAVA_MEANING`, `DRISHTI`, `YOGA_DEFINITION`, `NAKSHATRA_CHARACTER`, `DASHA_APPLICATION`, `GOCHAR_SIGNIFICATION`, `ECLIPSE_SIGNIFICATION`, `GENERAL` |
| `ConflictPolicy` | `FIRST_WINS`, `REPORT_ALL` |
| `ConditionOp` | `EQ`, `NEQ`, `LT`, `LTE`, `GT`, `GTE`, `IN`, `NOT_IN`, `EXISTS` |
| `ConditionCombiner` | `ALL`, `ANY`, `NOT` |

Reused from `jyotish` (never redefined): `RashiId`, `NakshatraId`, `Pada`,
`RetrogradeState`, `AspectKind`, `TransitEventKind`, `EclipseKind`,
`EclipseClassification`, `Bhava`, `PlanetState`, `PairGeometry`,
`LagnaState`, `TransitEvent`, `EclipseEvent` — referenced only as
vocabulary types in conditions and result fields.

## 2. `KnowledgeConfig` (frozen dataclass)

| Field | Type | Default | Constraint / semantics |
|---|---|---|---|
| `default_profile_id` | `str` | `"bphs-classical"` | must exist in the profile catalog |
| `default_conflict_policy` | `ConflictPolicy` | `FIRST_WINS` | used when a profile omits the field |
| `source_catalog_version` | `str \| None` | `None` | pin; mismatch ⇒ `CatalogIntegrityError` |
| `rule_catalog_versions` | `dict[str, str]` | `{}` | per-catalog pins (catalog id → version) |
| `profile_catalog_version` | `str \| None` | `None` | pin |
| `enforce_provenance` | `bool` | `True` | reject rules without mandatory provenance |
| `verify_checksums` | `bool` | `True` | verify catalog checksums at load |
| `max_rules_per_synthesis` | `int` | `200` | upper bound on returned rules |

JSON shape:

```json
{
  "default_profile_id": "bphs-classical",
  "default_conflict_policy": "FIRST_WINS",
  "source_catalog_version": null,
  "rule_catalog_versions": {},
  "profile_catalog_version": null,
  "enforce_provenance": true,
  "verify_checksums": true,
  "max_rules_per_synthesis": 200
}
```

## 3. `Source` / `Edition` (frozen dataclasses) — source registry

### 3.1 `Source`

| Field | Type | Semantics |
|---|---|---|
| `source_id` | `str` | stable slug, e.g. `"bphs"` |
| `canonical_name` | `str` | IAST name, e.g. `"Bṛhat Parāśara Horā Śāstra"` |
| `common_name` | `str` | e.g. `"BPHS"` |
| `author` | `str \| None` | attributions allowed, e.g. `"Parāśara (attrib.)"` |
| `period` | `str \| None` | e.g. `"~600–800 CE"` |
| `language` | `str` | e.g. `"Sanskrit"` |
| `lineage` | `list[str]` | tradition tags, e.g. `["parashari"]` |
| `status` | `SourceStatus` | classification |
| `editions` | `list[Edition]` | bibliographic provenance |
| `catalog_version` | `str` | semver of the catalog entry |

### 3.2 `Edition`

| Field | Type | Semantics |
|---|---|---|
| `edition_id` | `str` | stable slug within the source |
| `title` | `str` | full title of the edition/translation |
| `translator` | `str \| None` | translator/editor |
| `publisher` | `str \| None` | publisher |
| `year` | `str \| None` | publication year |
| `language` | `str` | edition language |
| `notes` | `str \| None` | free note (opaque) |

JSON shape:

```json
{
  "source_id": "bphs",
  "canonical_name": "Bṛhat Parāśara Horā Śāstra",
  "common_name": "BPHS",
  "author": "Parāśara (attrib.)",
  "period": "~600–800 CE",
  "language": "Sanskrit",
  "lineage": ["parashari"],
  "status": "CANONICAL",
  "editions": [
    { "edition_id": "sharma-2001", "title": "Brihat Parashara Hora Shastra",
      "translator": "R. Santhanam", "publisher": "Ranjan", "year": "2001",
      "language": "English", "notes": null }
  ],
  "catalog_version": "1.0.0"
}
```

## 4. `RuleCondition` (frozen dataclass) — typed predicate tree

| Field | Type | Semantics |
|---|---|---|
| `combiner` | `ConditionCombiner \| None` | `None` ⇒ this node is an atom |
| `op` | `ConditionOp \| None` | set for atoms |
| `path` | `str \| None` | fact-vocabulary path (validated) |
| `value` | `object \| None` | typed literal |
| `children` | `list[RuleCondition]` | for `ALL`/`ANY`/`NOT` |

Validation rules:

- Atom: `combiner is None`, `op` and `path` set, `children == []`.
- Combiner: `op is None`, `path is None`, ≥ 1 child; `NOT` exactly 1 child.
- `path` must resolve in `FACT_VOCABULARY` with a type-compatible `value`
  (e.g. `planet(MOON).rashi` → `RashiId` string; `bhava(7).occupants` →
  `IN`/`NOT_IN` with `BodyId` strings).
- Unknown path, bad literal type, or malformed tree ⇒ `RuleSchemaError` at
  load.

JSON shape:

```json
{ "combiner": "ALL", "op": null, "path": null, "value": null, "children": [
  { "combiner": null, "op": "EQ", "path": "planet(MOON).rashi",
    "value": "VRISHABHA", "children": [] },
  { "combiner": null, "op": "EQ", "path": "planet(SUN).nakshatra",
    "value": "ASHWINI", "children": [] }
] }
```

## 5. `Rule` / `RuleConclusion` / `ProvenanceRef` / `ResolvedRule` (frozen dataclasses)

### 5.1 `RuleConclusion`

| Field | Type | Semantics |
|---|---|---|
| `kind` | `str` | label, e.g. `"CLASSIFICATION"`, `"SIGNIFICATION"`, `"APPLICATION"` |
| `statement` | `str` | canonical, citation-grounded text |
| `structured` | `object` | keyed dict; **opaque to the engine** (no evaluator) |

### 5.2 `ProvenanceRef`

| Field | Type | Semantics |
|---|---|---|
| `source_id` | `str` | must resolve in the source registry |
| `chapter` | `str \| None` | chapter / adhyāya ref |
| `verse_start` | `str \| None` | verse/shloka ref start |
| `verse_end` | `str \| None` | verse/shloka ref end |
| `edition_id` | `str \| None` | which edition/translation is cited |
| `commentary` | `str \| None` | optional commentary-lineage note |

### 5.3 `Rule`

| Field | Type | Semantics |
|---|---|---|
| `rule_id` | `str` | stable, e.g. `"bphs.25.12.1"` |
| `domain` | `RuleDomain` | consumption group |
| `summary` | `str` | one-line human summary (data, not engine logic) |
| `condition` | `RuleCondition` | predicate over the fact vocabulary |
| `conclusion` | `RuleConclusion` | structured content (opaque) |
| `provenance` | `ProvenanceRef` | primary ref (mandatory) |
| `supporting_refs` | `list[ProvenanceRef]` | additional citations |
| `conflicts_with` | `list[str]` | authored conflict declarations: rule_ids this rule contradicts (ADR-010); **symmetry enforced** at load |
| `exception_for` | `list[str]` | **v0.3.0**: rule_ids this rule overrides when it matches (SPEC §9.2); cycle ⇒ `ConflictResolutionError` |
| `authority_tier` | `int` | 1–5, authored strength |
| `status` | `RuleStatus` | ACTIVE / DEPRECATED / SUPERSEDED |
| `tradition_tags` | `list[str]` | profile-matching tags |
| `rule_version` | `str` | semver of this rule datum |

JSON shape:

```json
{
  "rule_id": "bphs.25.12.1",
  "domain": "YOGA_DEFINITION",
  "summary": "Moon in a kendra from lagna forms a Gaja-Kesari yoga",
  "condition": {
    "combiner": "ANY", "op": null, "path": null, "value": null,
    "children": [
      { "combiner": null, "op": "IN", "path": "bhava(1).occupants", "value": ["MOON"], "children": [] },
      { "combiner": null, "op": "IN", "path": "bhava(4).occupants", "value": ["MOON"], "children": [] },
      { "combiner": null, "op": "IN", "path": "bhava(7).occupants", "value": ["MOON"], "children": [] },
      { "combiner": null, "op": "IN", "path": "bhava(10).occupants", "value": ["MOON"], "children": [] }
    ]
  },
  "conclusion": {
    "kind": "CLASSIFICATION",
    "statement": "Gaja-Kesari yoga (per BPHS ch. 25)",
    "structured": { "yoga_id": "GAJA_KESARI", "classical_name": "Gaja-Kesari" }
  },
  "provenance": { "source_id": "bphs", "chapter": "25", "verse_start": "12",
                  "verse_end": null, "edition_id": "sharma-2001",
                  "commentary": null },
  "supporting_refs": [],
  "conflicts_with": [],
  "exception_for": [],
  "authority_tier": 4,
  "status": "ACTIVE",
  "tradition_tags": ["parashari"],
  "rule_version": "1.0.0"
}
```

> **Boundary:** the `conclusion.structured.yoga_id` and `classical_name` are
> data. The engine does not evaluate, score, or interpret them — future Yoga
> engines consume `SynthesisResult` and apply their own semantics.

## 6. `TraditionProfile` (frozen dataclass)

| Field | Type | Semantics |
|---|---|---|
| `profile_id` | `str` | stable slug |
| `name` | `str` | display name |
| `version` | `str` | profile version (part of identity) |
| `description` | `str` | purpose/scope note |
| `included_sources` | `list[str]` | source ids allowed |
| `source_priority` | `list[str]` | explicit order (subset/permutation) |
| `conflict_policy` | `ConflictPolicy` | explicit policy |
| `domains` | `list[RuleDomain] \| None` | `None` = all domains |
| `passthrough_config` | `object` | echoed, never interpreted |

JSON shape:

```json
{
  "profile_id": "bphs-classical",
  "name": "BPHS Classical",
  "version": "1.0.0",
  "description": "BPHS-centric Parashari synthesis",
  "included_sources": ["bphs", "brihat-jataka", "jataka-parijata", "phaladeepika"],
  "source_priority": ["bphs", "brihat-jataka", "jataka-parijata", "phaladeepika"],
  "conflict_policy": "FIRST_WINS",
  "domains": null,
  "passthrough_config": { "ayanamsa": "LAHIRI" }
}
```

## 7. `RuleQuery` / `ResolvedRule` / `SynthesisResult` / `ConflictRecord` / `SearchMetadata`

### 7.0 `ResolvedRule` (frozen dataclass) — v0.3.0 NEW

| Field | Type | Semantics |
|---|---|---|
| `rule` | `Rule` | the resolved rule |
| `precedence_key` | `list` | comparator tuple from SPEC §8, echoed for audit |
| `effective_weight` | `float` | deterministic scalar (SPEC §10.1) — display/ordering metadata only |
| `credibility` | `float` | evidence confidence in `[0,1]` (SPEC §10.2) — **never** outcome likelihood |
| `applicability` | `bool` | condition evaluated true against the snapshot |
| `status_note` | `str \| None` | e.g. `"suppressed by X"`, `"exception overrides Y"`, `null` |

JSON shape:

```json
{
  "rule": { "rule_id": "bphs.25.12.1", "domain": "YOGA_DEFINITION", "...": "..." },
  "precedence_key": [0, -4, -4, [-1, 0, 0], "bphs.25.12.1"],
  "effective_weight": 6.2,
  "credibility": 0.86,
  "applicability": true,
  "status_note": null
}
```

### 7.1 `RuleQuery` (input)

| Field | Type | Semantics |
|---|---|---|
| `domain` | `RuleDomain \| None` | `None` = all domains in profile scope |
| `fact_snapshot` | `object` | JRE-003 output dict (echoed verbatim) |
| `profile_id` | `str \| None` | `None` ⇒ config default |
| `include_suppressed` | `bool` | `FIRST_WINS`: include suppressed rules in output? |

### 7.2 `ConflictRecord`

| Field | Type | Semantics |
|---|---|---|
| `rule_a_id` | `str` | higher-precedence participant |
| `rule_b_id` | `str` | other participant |
| `reason` | `str` | why they conflict |
| `resolution` | `str` | what happened (winner / reported together) |
| `policy` | `ConflictPolicy` | policy in force |

### 7.3 `SearchMetadata`

| Field | Type | Semantics |
|---|---|---|
| `algorithm` | `str` | `"profile-precedence-order"` |
| `catalogs` | `object` | `{catalog_id: version}` used |
| `rules_evaluated` | `int` | conditions evaluated |
| `rules_matched` | `int` | matched after precedence |
| `credibility_summary` | `object` | **v0.3.0** `{mean, min, max, n}` over matched rules |

### 7.4 `SynthesisResult`

| Field | Type | Semantics |
|---|---|---|
| `query` | `RuleQuery` | echo (fact_snapshot verbatim) |
| `profile` | `TraditionProfile` | resolved profile (echo) |
| `matched_rules` | `list[ResolvedRule]` | **v0.3.0**; ordered by precedence |
| `suppressed_rules` | `list[ResolvedRule]` | **v0.3.0**; only when suppressed (FIRST_WINS / exceptions) + `include_suppressed` |
| `conflicts` | `list[ConflictRecord]` | every suppression/disagreement/exception override |
| `provenance_index` | `object` | `{rule_id: [provenance strings]}` |
| `config` | `KnowledgeConfig` | config snapshot |
| `search_metadata` | `SearchMetadata` | determinism echo incl. `credibility_summary` |

JSON shape (abridged):

```json
{
  "query": { "domain": "YOGA_DEFINITION", "profile_id": "bphs-classical",
             "include_suppressed": false,
             "fact_snapshot": { "planets": [ { "body": "MOON", "rashi": "VRISHABHA" } ],
                                "lagna": { "rashi": "KARKA" } } },
  "profile": { "profile_id": "bphs-classical", "version": "1.0.0",
               "conflict_policy": "FIRST_WINS", "source_priority": ["bphs", "..."],
               "included_sources": ["bphs", "..."], "domains": null,
               "passthrough_config": { "ayanamsa": "LAHIRI" } },
  "matched_rules": [ { "rule": { "rule_id": "bphs.25.12.1", "domain": "YOGA_DEFINITION",
                                   "status": "ACTIVE", "rule_version": "1.0.0" },
                       "precedence_key": [0, -4, -4, [-1, 0, 0], "bphs.25.12.1"],
                       "effective_weight": 6.2, "credibility": 0.86,
                       "applicability": true, "status_note": null } ],
  "suppressed_rules": [],
  "conflicts": [],
  "provenance_index": { "bphs.25.12.1": ["BPHS ch.25 v.12 (tr. Santhanam 2001)"] },
  "config": { "default_profile_id": "bphs-classical",
              "default_conflict_policy": "FIRST_WINS" },
  "search_metadata": { "algorithm": "profile-precedence-order",
                       "catalogs": { "sources": "1.0.0", "rules:yoga": "1.0.0",
                                     "profiles": "1.0.0" },
                       "rules_evaluated": 42, "rules_matched": 3,
                       "credibility_summary": { "mean": 0.78, "min": 0.6,
                                                 "max": 0.86, "n": 3 } }
}
```

## 8. Fact vocabulary (pinned, versioned)

`FACT_VOCABULARY_VERSION = "1.0.0"` is part of the calculation identity. The
authoritative typed path table (incl. the v0.3.0 `relative_house` path) is
SPEC §6.2. Path grammar: `planet(<BODY>)`, `lagna`, `bhava(<N>)`,
`bhava(<BODY>)`, `pair(<A>,<B>)`, `transit(<BODY>)`, `eclipse`. The
snapshot normalization contract (JRE-003 outputs → `fact_snapshot`) is
SPEC §6.3.

## 9. Round-trip guarantees

- `json.loads(result_to_json(r))` → identical doubles/strings/enums for
  every field.
- `RuleQuery.fact_snapshot` round-trips byte-for-byte (opaque object).
- Catalog JSON documents load and validate; invalid ones raise typed errors.
- Tests cover all of the above (TEST-PLAN §5).

## 10. JSON Schema (normative excerpt — `Rule`)

The full schema ships with CODING. Every object sets
`additionalProperties: false`. Excerpt:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Rule",
  "type": "object",
  "additionalProperties": false,
  "required": ["rule_id","domain","summary","condition","conclusion",
    "provenance","supporting_refs","conflicts_with","exception_for",
    "authority_tier","status","tradition_tags","rule_version"],
  "properties": {
    "rule_id": { "type": "string" },
    "domain": { "enum": ["KARAKA","BHAVA_MEANING","DRISHTI","YOGA_DEFINITION",
                "NAKSHATRA_CHARACTER","DASHA_APPLICATION","GOCHAR_SIGNIFICATION",
                "ECLIPSE_SIGNIFICATION","GENERAL"] },
    "summary": { "type": "string" },
    "condition": { "$ref": "#/$defs/RuleCondition" },
    "conclusion": {
      "type": "object", "additionalProperties": false,
      "required": ["kind","statement","structured"],
      "properties": { "kind": { "type": "string" },
                      "statement": { "type": "string" },
                      "structured": { "type": "object" } }
    },
    "provenance": { "$ref": "#/$defs/ProvenanceRef" },
    "supporting_refs": { "type": "array", "items": { "$ref": "#/$defs/ProvenanceRef" } },
    "conflicts_with": { "type": "array", "items": { "type": "string" } },
    "exception_for": { "type": "array", "items": { "type": "string" } },
    "authority_tier": { "type": "integer", "minimum": 1, "maximum": 5 },
    "status": { "enum": ["ACTIVE","DEPRECATED","SUPERSEDED"] },
    "tradition_tags": { "type": "array", "items": { "type": "string" } },
    "rule_version": { "type": "string" }
  },
  "$defs": {
    "ProvenanceRef": {
      "type": "object", "additionalProperties": false,
      "required": ["source_id"],
      "properties": { "source_id": { "type": "string" },
                      "chapter": { "type": ["string","null"] },
                      "verse_start": { "type": ["string","null"] },
                      "verse_end": { "type": ["string","null"] },
                      "edition_id": { "type": ["string","null"] },
                      "commentary": { "type": ["string","null"] } }
    },
    "RuleCondition": {
      "type": "object", "additionalProperties": false,
      "required": ["combiner","op","path","value","children"],
      "properties": {
        "combiner": { "enum": ["ALL","ANY","NOT"] },
        "op": { "enum": ["EQ","NEQ","LT","LTE","GT","GTE","IN","NOT_IN","EXISTS"] },
        "path": { "type": ["string","null"] },
        "value": {},
        "children": { "type": "array", "items": { "$ref": "#/$defs/RuleCondition" } }
      }
    }
  }
}
```

## 11. Catalog file format

Every catalog file (sources, rules, profiles) is a JSON document:

```json
{
  "catalog_id": "rules:yoga",
  "catalog_version": "1.0.0",
  "schema_version": "0.2.0",
  "source_citation": "Authored from BPHS ch. 25 (ed. sharma-2001)",
  "checksum_sha256": "…",
  "entries": [ { "rule_id": "bphs.25.12.1", "…": "…" } ]
}
```

## 12. Change history

| Version | Date | Change |
|---|---|---|
| 0.2.0 | 2026-08-12 | Architect data contract |
| 0.3.0 | 2026-08-12 | Specialist refinement: `ResolvedRule` wrapper with precedence/weight/credibility; `Rule.exception_for`; `relative_house` vocabulary path; validated `passthrough_config`; `credibility_summary`; supersession notice |
