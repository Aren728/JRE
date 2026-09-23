# Mypy Grandfather List — Burn-Down Plan

> **Recovery note (2026-09-23):** re-materialized from session context after
> the host-side deletion of the working tree. Restore to
> `docs/runbooks/mypy_burndown_plan.md`.

Companion to the `[[tool.mypy.overrides]]` grandfather list in
`pyproject.toml` (added during the 1.1.0rc1 CI hardening). That list
grandfathers **37 legacy modules / 146 strict errors** so `mypy --strict`
could become a hard CI gate immediately. This plan retires the list.

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

Snapshot at plan creation (full-deps venv, mypy 2.3.1, 434 files):

| Error code | Count | Typical fix |
|---|---|---|
| `type-arg` | 30 | Parameterize `dict`/`list`/`tuple` annotations |
| `no-any-return` | 21 | Annotate the local, or `cast()` at the boundary |
| `union-attr` | 20 | Narrow with `assert`/`isinstance` where the invariant holds |
| `arg-type` | 13 | Typed DTOs / `Protocol`s instead of raw dicts |
| `no-untyped-def` | 10 | Write the signature |
| `assignment` | 10 | Fix the annotation or the value |
| `type-var` / `misc` / `dict-item` | 24 | Mostly generic bounds + `Any` containment |
| others (`operator`, `return-value`, …) | 18 | Case-by-case |

Distribution: **the top 5 modules hold 82 errors (56%)**; 23 modules carry
only 1–2 each. The plan exploits that long tail first.

## Wave 1 — Tail sweep (23 modules, ~28 errors) · target: first 2 weeks

One or two errors per module, mostly mechanical annotations. Perfect
warm-up PRs; each removal is a tiny, reviewable diff.

Modules (errors): `jrs.yoga_evaluator.service` (1), `jrs.yoga_evaluator.evidence_service` (1),
`jrs.validation.storage` (1), `jrs.validation.runner` (1), `jrs.temporal.dasha_engine` (1),
`jrs.structural.models` (1), `jrs.services.ephemeris` (1), `jrs.prediction_engine.report_engine` (1),
`jrs.prediction_engine.overview_report_engine` (1), `jrs.prediction_engine.nakshatra_exchanges` (1),
`jrs.prediction_engine.gochar_predictions_engine` (1), `jrs.prediction_engine.deep_dasha` (1),
`jrs.parihara.remedy_engine` (1), `jrs.horoscope.gochar_engine` (1), `jrs.graph.nakshatra_service` (1),
`jrs.domains.yoga.service` (1), `jrs.advanced_charts.shadbala` (1), `jrs.advanced_charts.divisional` (1),
`jrs.prediction_engine.overview_engine` (2), `jrs.prediction_engine.gochar_transit` (2),
`jrs.engine.calculator` (2), `jrs.advanced_charts.ashtakavarga` (2), `astronomy.swisseph.provider` (2).

- **Acceptance:** 23 entries removed; histogram shows only the 14 remaining
  heavyweight modules; CI green.

## Wave 2 — Mid tier (9 modules, ~36 errors) · target: weeks 3–5

`jrs.services.divisional` (6), `jrs.cli` (5), `jrs.api.dependencies` (5),
`jrs.validation.datasets.loader` (4), `jrs.reporting.jatakam_book_generator` (4),
`jrs.reporting.pdf_generator` (3), `jrs.prediction_engine.parivartana` (3),
`jrs.graph.functional_lordship` (3), `jrs.deterministic_engine.i18n_loader` (3).

Pattern here: loader/CLI code handling untyped JSON. Expect the fixes to
introduce small typed models (dataclasses) at parse boundaries — which also
hardens runtime behavior (bad payloads fail loudly instead of leaking `Any`).

- **Acceptance:** 9 entries removed; any newly introduced DTOs get unit
  tests for their parse/validation paths.

## Wave 3 — Engine heavyweights (4 modules, ~40 errors) · target: weeks 6–8

`jrs.api.main` (14), `jrs.prediction_engine.panchang_engine` (9),
`jrs.deterministic_engine.esoteric_evaluator` (9),
`jrs.reporting.narrative_engines.timeline_engine` (8).

`api/main.py` is mostly FastAPI decorator typing + missing return
annotations on handlers (`no-untyped-def`, `type-arg` on response dicts).
Recommend converting handler returns to typed response models as they are
annotated — that doubles as OpenAPI quality improvement.

- **Acceptance:** 4 entries removed; FastAPI handlers returning response
  models where the conversion was trivial.

## Wave 4 — The boss: `jrs.validation.calibration.py` (42 errors) · target: weeks 9–10

29% of all debt in one file. Expect a `union-attr`/`type-arg` cluster
around calibration data structures. Strategy: type the data model first
(frozen dataclasses per calibration record), then let mypy narrow the
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
