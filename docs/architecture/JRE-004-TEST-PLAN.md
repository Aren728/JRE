# JRE-004 — Classical Knowledge & Rule Engine: Test Strategy

- Status: SPECIALIZED
- Version: 0.3.0 (supersedes the design-level test plan v0.2.0)
- Date: 2026-08-12
- Upstream: [JRE-004 Architecture §19, §22](JRE-004-KNOWLEDGE-RULES-CORE.md),
  [JRE-004 Specialist Spec](JRE-004-SPECIALIST-SPEC.md),
  [JRE-004 Data Contract](JRE-004-DATA-CONTRACT.md),
  [ADR-008](../decisions/ADR-008-SOURCE-REGISTRY-PROVENANCE.md),
  [ADR-009](../decisions/ADR-009-RULE-SCHEMA.md),
  [ADR-010](../decisions/ADR-010-TRADITION-PROFILES-PRECEDENCE-CONFLICT.md),
  [ADR-011](../decisions/ADR-011-SYNTHESIS-INTERFACE.md)

Ownership: QA authors and executes the full matrix. CODING ships the
happy-path subset (§14). VALIDATOR owns the independent cross-source harness
(§12).

> **Supersession notice (v0.3.0):** specialist-resolved test additions:
> 1. **Exceptions** — `exception_for` override chains (§9.2), cycle
>    rejection, record emission.
> 2. **Weight/credibility** — §10 formulas pinned by independent
>    reimplementation; `credibility` never asserted as prediction.
> 3. **Snapshot normalization** — JRE-003 outputs → `fact_snapshot`
>    (§6.3); domain-section requirement enforcement (§6.4).
> 4. **Precedence-key echo** — `ResolvedRule.precedence_key` matches §8
>    and the hand-computed golden order.
> 5. **Vocabulary expansion** — `relative_house` path resolution.

## 1. Test layers and directory layout

```
tests/
  unit/knowledge/          # pure logic — no jyotish import required
  integration/knowledge/   # synthesis against real JRE-003 fact snapshots
  validation/knowledge/    # independent cross-source validation (VALIDATOR)
```

- **Unit** must never import `swisseph`; a fixture-time guard fails the
  session otherwise (mirrors JRE-002/JRE-003).
- **Integration** requires JRE-002/JRE-003's pinned deps and committed
  catalogs; skipped with a clear reason otherwise.
- **Validation** reads committed reference excerpts offline; no network.

## 2. Requirement matrix (JRE-004 mandated tests)

| # | Requirement | File(s) | Key assertions |
|---|---|---|---|
| 1 | Source registry | `unit/.../test_sources.py` | all 5 named sources + ≥1 regional present; every field typed; `get_source`/`resolve_edition`; unknown id → `UnknownSourceError` |
| 2 | Rule schema | `unit/.../test_schema.py` | every mandated field; unknown vocabulary path → `RuleSchemaError`; wrong literal type → error; malformed tree → error; unprovenanced rule → `ProvenanceError` |
| 3 | Provenance | `unit/.../test_provenance.py` | canonical provenance string; `provenance_index` in result; checksum mismatch → `CatalogIntegrityError`; `enforce_provenance=False` allows explicit-None refs only |
| 4 | Conflict resolution | `unit/.../test_conflict.py` | `FIRST_WINS` suppresses + emits `ConflictRecord`; `REPORT_ALL` suppresses nothing; no silent override; malformed `conflicts_with` → `ConflictResolutionError` |
| 5 | Tradition profiles | `unit/.../test_profiles.py` | 6 initial profiles; priority orders explicit; unknown profile → `UnknownProfileError`; profile passthrough echoed |
| 6 | Rule precedence | `unit/.../test_precedence.py` | ordering by each key (source priority → specificity → tier → version → id); tiebreaks deterministic; algorithm echo |
| 7 | Synthesis interface | `integration/.../test_synthesis.py` | golden catalogs → expected ordered `ResolvedRule`s; envelope schema conformance; `include_suppressed`; query/profile/config echo; fact-snapshot byte round-trip |
| 8 | Determinism | `unit/.../test_determinism.py` | in-process bit-equality; cross-process byte-equality (JSON); catalog version pins echoed |
| 9 | Exceptions | `unit/.../test_exceptions.py` | `exception_for` overrides base rule; override recorded with `resolution="exception"`; exception-vs-exception precedence; cycle ⇒ `ConflictResolutionError` |
| 10 | Weight/credibility | `unit/.../test_weight_credibility.py` | §10 formulas match independent reimplementation; `credibility ∈ [0,1]`; `effective_weight` monotone with precedence; `credibility_summary` correct |
| 11 | Snapshot normalization | `integration/.../test_snapshot_normalize.py` | JRE-003 outputs → `fact_snapshot` shapes (SPEC §6.3); `relative_house` resolves; missing domain section ⇒ `SynthesisError` |

Additional coverage:

- `test_fact_vocabulary.py` — every vocabulary path (incl. v0.3.0
  `relative_house`) resolves against a real JRE-003 result payload;
  `FACT_VOCABULARY_VERSION` echoed in metadata.
- `test_no_prediction.py` — static scan: no engine module contains
  conclusion evaluation logic; `RuleConclusion.structured` is opaque
  (no code path reads its keys); no engine code presents
  `credibility`/`effective_weight` as outcome likelihood.
- `test_catalog_integrity.py` — checksum + version-pin enforcement;
  corrupted catalog fails load.
- `test_generic_rule_semantics.py` — a rule that matches / does not match a
  snapshot; `ANY`/`NOT` combiners; `EXISTS` op; boundary literals
  (`degree_in_rashi < 5.0`).
- `test_conflict_declarations.py` — asymmetric `conflicts_with` ⇒
  `ConflictResolutionError`; `exception_for` unknown target ⇒
  `RuleSchemaError`.

## 3. Config tests

- `test_config.py` (unit): `config/knowledge.toml` loads; every field
  round-trips; unknown profile id in config → error; pins enforce.
- `test_config_echo.py` (integration): config snapshot in `SynthesisResult`
  equals the input config.

## 4. Determinism tests

- In-process: identical query → identical `SynthesisResult` (bit equality).
- Cross-process: child process computes the same synthesis → byte-identical
  JSON (mirrors JRE-002's harness pattern).
- Same query with warm vs cold catalogs → identical (catalogs are immutable,
  loaded once).

## 5. Serialization tests

- `test_serialize.py`: JSON round-trips per DATA-CONTRACT §9; schema
  conformance for `Rule`, `Source`, `TraditionProfile`, `SynthesisResult`;
  enums → strings; `None` → null; `fact_snapshot` byte round-trip;
  provenance strings stable.

## 6. Static / structural tests

- `test_forbidden_imports.py`: no `astronomy|swisseph|inference|astrology|
  transits|dasha|calculations|gochar` import in `src/knowledge/**`; no
  `socket|requests|urllib|httpx` (offline); `models.py` stdlib only;
  `knowledge` imports `jyotish` public API only.
- `test_no_prediction.py`: no conclusion-evaluation code path (data is
  opaque); no benefic/malefic/auspicious **logic** (vocabulary may exist only
  inside authored rule data files, never in engine code).
- `test_astronomy_unmodified.py`: `src/astronomy` file set + public `__all__`
  unchanged (extends the JRE-003 guard to `src/jyotish`).
- `test_no_personal_data.py`: no birth-data concept anywhere in
  `src/knowledge`.

## 7. Offline guarantee

- Covered structurally by §6 (no network imports). Integration tests run
  fully offline against committed catalogs; a conftest hook asserts `socket`
  is never called (mirrors JRE-002).

## 8. Golden fixtures

- `tests/fixtures/knowledge/` — golden catalogs (sources, rules for ≥ 3
  domains, 6 profiles) with hand-computed expected precedence and conflict
  outcomes; golden `SynthesisResult` JSON with hex-float representation.
- `GOLDEN_VERSION` pins the producing environment (same policy as JRE-002).

## 9. Performance smoke test (informational)

- `integration/.../test_performance.py`: synthesis of ≤ 200 rules < 50 ms
  with warm catalogs. Not a hard CI gate.

## 10. Tooling and commands

```
python -m pytest tests/unit/knowledge tests/integration/knowledge -q
ruff check src tests
mypy src/knowledge
```

- CI-format gate before CODING → QA: unit + integration + ruff + mypy green
  AND `src/astronomy` + `src/jyotish` untouched (§6).

## 11. CODING happy-path subset (shipped with implementation)

- `test_sources.py`, `test_schema.py` (core), `test_provenance.py` (core),
  `test_precedence.py` (core), `test_profiles.py` (core),
  `test_exceptions.py` (basic override), `test_weight_credibility.py`
- `test_config.py`, `test_forbidden_imports.py`, `test_no_prediction.py`
- `test_determinism.py` (in-process), `test_synthesis.py` (basic golden)

## 12. Independent cross-source validation (VALIDATOR)

Reference data committed at `datasets/validation/knowledge/` (no network):

| Domain | Independent reference | Tolerance / assertion |
|---|---|---|
| Rule content vs cited text | Published editions (e.g. BPHS ch. 25 ed. Santhanam 2001) excerpted in committed reference notes | For a sample of rules with verse-level refs: the rule's `conclusion.statement` agrees with the cited verse's standard reading |
| Source registry metadata | Standard bibliographies | canonical name/author/period consistent for the named sources |
| Precedence/conflict behavior | Hand-computed golden orders | exact match (pure logic) |
| Fact vocabulary | Real JRE-003 result payloads | every path resolves; types match |

- The harness computes through `KnowledgeService` and emits a per-domain
  report; the Architect fixes the tolerance budget after the first batch.
- At least one rule from each of BPHS, Bṛhat Jātaka, Jātaka Pārijāta,
  Phaladīpikā, and a regional source must be covered.

## 13. Acceptance criteria for JRE-004 tests

1. All unit + integration tests green on a clean 3.12 environment with
   committed catalogs.
2. Determinism proven in-process and cross-process (bit/byte equality).
3. All 8 mandated requirement tests present and green.
4. Independent cross-source validation runs offline within the fixed budget.
5. No prediction code path and no forbidden imports (static gates); JRE-002
   and JRE-003 untouched.
6. No personal data anywhere in `src/knowledge`.

## 14. Change history

| Version | Date | Change |
|---|---|---|
| 0.2.0 | 2026-08-12 | Architect test strategy |
| 0.3.0 | 2026-08-12 | Specialist refinement: exceptions, weight/credibility, snapshot normalization, precedence-key echo, vocabulary expansion; supersession notice |
