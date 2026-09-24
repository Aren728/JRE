# Mypy Grandfather List — Burn-Down Plan

> **Recovery note (2026-09-23):** re-materialized from session context after
> the host-side deletion of the working tree. Restore to
> `docs/runbooks/mypy_burndown_plan.md`.

Companion to the `[[tool.mypy.overrides]]` grandfather list in
`pyproject.toml` (added during the 1.1.0rc1 CI hardening). That list
grandfathers legacy modules so `mypy --strict` could become a hard CI gate
immediately. This plan retires the list.

**Rules of engagement (non-negotiable):**

1. The list must **shrink, never grow**. New modules are never added; a
   touched legacy module is expected to lose its entry in the same PR.
2. Removing an entry: fix every error in that module under strict mode,
   verify with the debt histogram (below) that the module reports zero,
   delete its line from the override list, and confirm `mypy` (gated
   config) is still green.
3. Never weaken the global `strict = true` to chase a module.

## Measuring the debt

The gated config hides grandfathered errors by design. To see the true
debt, strip the override block and re-run:

```bash
scripts/mypy_debt_histogram.sh          # per-module + per-error-code counts
```

### Current baseline (2026-09-24, local mypy 1.9.0)

| Milestone | Modules grandfathered | True strict errors |
|---|---|---|
| Plan creation (CI mypy 2.3.1) | 37 | 146 (est.) |
| After Wave 1 (api.main, cli, api.dependencies, services.divisional un-grandfathered; jyotish PEP 695 backport) | 33 | — |
| After Wave 2 (bhava PEP 695 backport; gochar/context/tajika/prashna/varga StrEnum-inference fixes; core 100% clean) | 33 | 115 |
| After Batch 3.0 (tail sweep: 22 fixed + `validation.storage` free removal) | 10 | 88 |
| After Batch 3.1 (timeline_engine, panchang_engine, esoteric_evaluator, datasets.loader) | 6 | 58 |
| After Batch 3.2 (functional_lordship, parivartana, jatakam_book_generator, pdf_generator, i18n_loader) | 1 | 42 |
| **After Batch 3.3 (this update: calibration.py) — LIST RETIRED** | **0** | **0** |

**Baseline correction:** earlier drafts recorded "136 errors across 33
modules". The authoritative histogram re-sum is **115 errors across 32
files** at the post-Wave-2 state; the 136 figure was an over-count of the
first histogram. Use 115 → 88 as the Wave 3 reference numbers.

**Known mypy 1.9.0 quirk used by several Wave 2/3 fixes:** for a `StrEnum`,
`mypy 1.9` infers `str` elements for `tuple(EnumCls)` / `list(EnumCls)` and
`set[str]` for `set(EnumCls)`. Fixes are explicit annotations/casts pinning
the enum type — runtime no-ops. CI pins mypy 2.3.1; re-run the histogram
there before executing the remaining batches.

### Free removal

`jrs.validation.storage` measured **zero** strict errors (runbook estimate
was 1) and was removed from the list with no code change in Batch 3.0.

## Batch roadmap (measured counts, local mypy 1.9.0)

### Batch 3.0 — Tail sweep · ✅ DONE (2026-09-24)

23 grandfathered entries removed (22 fixed + `validation.storage` free):

- 17 single-error modules: `jrs.yoga_evaluator.service`,
  `jrs.yoga_evaluator.evidence_service`, `jrs.validation.runner`,
  `jrs.temporal.dasha_engine`, `jrs.structural.models`,
  `jrs.services.ephemeris`, `jrs.prediction_engine.report_engine`,
  `jrs.prediction_engine.overview_report_engine`,
  `jrs.prediction_engine.nakshatra_exchanges`,
  `jrs.prediction_engine.gochar_predictions_engine`,
  `jrs.prediction_engine.deep_dasha`, `jrs.parihara.remedy_engine`,
  `jrs.horoscope.gochar_engine`, `jrs.graph.nakshatra_service`,
  `jrs.domains.yoga.service`, `jrs.advanced_charts.shadbala`,
  `jrs.advanced_charts.divisional`
- 5 two-error modules: `jrs.prediction_engine.overview_engine`,
  `jrs.prediction_engine.gochar_transit`, `jrs.engine.calculator`,
  `jrs.advanced_charts.ashtakavarga`, `astronomy.swisseph.provider`
- Plus free removal: `jrs.validation.storage`

Fix patterns: bare `dict`/`tuple` parameterization, `json.load` return
annotations at boundaries, `swe.*` untyped-return pins (`julday`,
`utcoffset` None-guard), `set`→`frozenset` at `frozenset[str]` params,
`max/min(key=dict.get)` → lambda, `callable` → `Callable[[float], float]`,
`bool | YogaEvaluation` union narrowing (rename + isinstance), tuple-pair
`tuple[str, ...]` → `tuple[str, str]` pinning, dead `cast` removal,
`str | None` re-binding fix via loop-variable rename.

- **Acceptance met:** gated `mypy` green (434 files), full test suite green
  (5,497 passed), all touched modules runtime-imported and spot-checked.

### Batch 3.1 — Small typed fixes (4 modules, 30 errors) · ✅ DONE (2026-09-24)

Actual fixes applied (30 measured errors, all cleared):

- `jrs.reporting.narrative_engines.timeline_engine` (8 × dict-item): as
  planned — `_DECADE_THEMES` re-annotated `dict[str, dict[str, str]]` →
  `dict[str, str]`. The nested value type was simply wrong (each entry is a
  prose string); the symbol has no other indexing sites, so zero risk.
- `jrs.prediction_engine.panchang_engine` (9 × type-arg): `PanchangData`
  fields `tithi/nakshatra/yoga: Dict` → `Dict[str, Any]`; the six compute
  helpers (`compute_tithi`, `compute_nakshatra`, `compute_yoga`,
  `compute_sun_times`, `compute_moon_times`, `compute_muhurtas`) →
  `Dict[str, Any]` returns.
- `jrs.deterministic_engine.esoteric_evaluator` (10 incl. 1 straggler):
  `register_rule` → `Callable[[Any], Any]` decorator signature (fixes the
  untyped-def + bare-Callable pair); `_get_planet_nakshatra`/
  `_get_planet_longitude` no-any-return sites pinned via typed locals
  instead of casting; straggler: `get_rule_scope` returned `Any` from the
  `Dict[str, Dict[str, Any]]` registry — pinned with `scope: RuleScope =`.
- `jrs.validation.datasets.loader` (4 × type-arg): the four serializer /
  deserializer helpers parameterized `dict` → `dict[str, Any]`.

- **Acceptance met:** 4 entries removed; gated mypy green (434 files);
  loader round-trip + panchang + registry smoke-tested at runtime; full
  suite 5,497 passed (one unrelated flake on the first run did not
  reproduce).

- `jrs.reporting.narrative_engines.timeline_engine` (8 × dict-item): one
  dict literal annotated `dict[str, dict[str, str]]` holding 8 plain `str`
  values — retype the annotation to `dict[str, str]` (or nest properly).
  One-line fix, zero logic risk.
- `jrs.validation.datasets.loader` (4 × type-arg): bare `dict`/`list`.
- `jrs.prediction_engine.panchang_engine` (9 × type-arg): bare
  `dict`/`list` parameterization.
- `jrs.deterministic_engine.esoteric_evaluator` (9: 6 no-any-return,
  2 no-untyped-def, 1 type-arg): annotate returns; pin `Any` boundaries.

- **Acceptance:** 4 entries removed; gated mypy green; unit tests for the
  loader parse path still pass.

### Batch 3.2 — Mid tier (5 modules, 16 errors) · ✅ DONE (2026-09-24)

Actual fixes applied (16 measured errors, all cleared):

- `jrs.graph.functional_lordship` (3 × return-value): the three
  `_check_*` helpers return `(None, None)` on miss, so the dispatcher now
  guards `if role is not None and desc is not None:` — encodes the
  both-or-neither invariant and narrows both union elements. No casts.
- `jrs.prediction_engine.parivartana` (3 × arg-type): same
  StrEnum/`tuple(sorted(...))` → `tuple[str, ...]` inference quirk as
  previous batches; pinned `pair_typed: tuple[str, str]` at the three
  `seen.add` sites.
- `jrs.deterministic_engine.i18n_loader` (3 × no-any-return): typed local
  on the `_load_json` return plus two `data[token]` index returns.
- `jrs.reporting.pdf_generator` (3): `occupants` var-annotated;
  `weasyprint` import guarded with `# type: ignore[import-not-found]`
  (untyped third-party, same policy as pysweph); `write_pdf()` bytes
  pinned via typed local.
- `jrs.reporting.jatakam_book_generator` (4): `_yoga_card` parameter
  annotated as `YogaResult` (from `jrs.api.schemas`, already imported
  type family); `weasyprint` + `write_pdf` handled as above; line-599
  fix became a **rename**: the inner remedy loop shadowed the outer
  loop's `pname: str` / `reasons: list[str]` with a joined `str` —
  renamed to `aff_planet` / `aff_reasons` (behavior-identical f-string
  output).

- **Acceptance met:** 5 entries removed (list: 6 → 1); gated mypy green;
  targeted `mypy --strict` pass on the 5 files: 0 errors; pytest
  `tests/unit/jrs/` 2,530 passed; all 5 modules smoke-imported.

### Batch 3.3 — The boss: `jrs.validation.calibration` (42 errors) · ✅ DONE (2026-09-24)

The predicted "type the data model first" strategy was unnecessary — the
42 errors collapsed into **3 root causes**, all fixed with narrowing and
dead-code removal (no new DTOs, no casts):

1. `_compute_timing_iou` (15 errors): `if None in (p_s, p_e, a_s, a_e)`
   does not narrow optionals — replaced with an explicit four-way
   `is None` chain (identical semantics).
2. Dead first confusion-matrix block (12 errors): a `tp/fp/fn/tn`
   computation guarded by `_LAYER_THRESHOLD` was immediately overwritten
   by the real one (the "Actually..." comment proved it dead) — deleted.
3. Narrowing across comprehension boundary (~15 errors): `successful`
   was filtered on `r.metric_evaluation is not None` but `evaluations`
   extracted the field in a *separate* comprehension, so mypy could not
   carry the narrowing — merged into one comprehension
   (`evaluations = [r.metric_evaluation for r in ... if ... is not None]`),
   the `not evaluations` early-return swapped in, and the downstream
   `list[MetricEvaluation | None]` arg-type errors vanished.

- **Acceptance MET:** final entry removed → the entire
  `[[tool.mypy.overrides]]` grandfather block is deleted from
  `pyproject.toml` (replaced by a retirement note). `mypy` gate covers
  100% of the codebase with zero exemptions besides `swisseph` stubs.
  Verified: gated mypy green (434 files), targeted strict pass on
  calibration.py clean, IoU smoke values unchanged (1.0 / 0.0 / 0.0),
  full suite 5,497 passed.

## Post-retirement state (2026-09-24)

- `pyproject.toml` carries no `ignore_errors` override anywhere; the only
  remaining `[[tool.mypy.overrides]]` is the intentional `swisseph`
  missing-stubs carve-out.
- Regression risk: the burndown was executed and verified on **mypy
  1.9.0** (local). CI pins **mypy 2.3.1** — one CI run should confirm the
  stricter 2.3.1 reports no new findings on the touched modules.

## Tracking

- Tick progress by re-running `scripts/mypy_debt_histogram.sh` at the start
  of each week; the per-module table is the burndown chart.
- CI enforces "never grows" structurally: adding a module to the list is a
  reviewable diff, and the histogram makes the cost visible in review.
