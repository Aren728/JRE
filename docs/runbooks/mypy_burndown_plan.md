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
| **After Batch 3.0 (this update)** | **10** | **88** |

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

### Batch 3.1 — Small typed fixes (4 modules, 30 errors) · next up

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

### Batch 3.2 — Mid tier (5 modules, 17 errors)

- `jrs.reporting.jatakam_book_generator` (4), `jrs.reporting.pdf_generator`
  (3, incl. 1 import-not-found), `jrs.prediction_engine.parivartana` (3),
  `jrs.graph.functional_lordship` (3 × return-value: `tuple[FunctionalRole,
  str]` vs `str | None` at lines ~200–210), `jrs.deterministic_engine.
  i18n_loader` (3).

Pattern: loader/CLI code handling untyped JSON — introduce small typed
models (frozen dataclasses) at parse boundaries where annotations alone
don't suffice; hardens runtime behavior (bad payloads fail loudly).

- **Acceptance:** 5 entries removed; any new DTOs get unit tests for their
  parse/validation paths.

### Batch 3.3 — The boss: `jrs.validation.calibration` (42 errors) · solo

29% of remaining debt in one file: 17 union-attr, 8 type-var, 8 misc,
6 operator, 3 arg-type — one `MetricEvaluation | None` cluster at lines
~121–239 plus `min`/`max` over `float | None`. Strategy: type the data
model first (frozen dataclasses per calibration record), narrow the
`None` branches where the invariant holds, then let mypy narrow the
callers. Do it last, alone, with the module's tests open.

- **Acceptance:** final entry removed → the entire
  `[[tool.mypy.overrides]]` grandfather block (this section and the list)
  is deleted from `pyproject.toml`. `mypy` gate then covers 100% of the
  codebase with zero exemptions besides `swisseph` stubs.

## Tracking

- Tick progress by re-running `scripts/mypy_debt_histogram.sh` at the start
  of each week; the per-module table is the burndown chart.
- CI enforces "never grows" structurally: adding a module to the list is a
  reviewable diff, and the histogram makes the cost visible in review.
