# Roadmap — v1.2.0

> **Recovery note (2026-09-23):** re-materialized from session context after
> the host-side deletion of the working tree. Restore to
> `docs/ROADMAP_V1.2.0.md`.

Target cycle after `v1.1.0` final. Scope is anchored in the repo's own
backlog: the orchestration queue (JRE-002…007 merged, **JRE-008 varga**
next), ADR-026/029 (deferred gochar capabilities with additive-API
proposals), the Phase-4 3D viewer, and the deployment review
(`docs/runbooks/deployment_staging_verification_review.md`).

## M1 — Ship v1.1.0 final (week 1)

The rc already carries the spatial grid, geospatial, 3D viewer, and CI
hardening. Remaining gates:

- [ ] Push `main` + `v1.1.0-rc.1` (local-only after the working-tree loss);
      confirm the hardened pipeline is green on GitHub.
- [ ] Staging-CI parity fix: `postgres:16-alpine` service image (review F1).
- [ ] Nightly `pg_dump` + weekly `restore_drill.sh` cron (review F2) — or
      record the manual-only risk explicitly in the release checklist.
- [ ] Tag `v1.1.0`, strip `-rc.1` from `pyproject.toml`, re-pin the two
      health-endpoint tests, full pytest run.

## M2 — Production cutover (week 2)

Everything is rehearsed and measured (`production_cutover.md`, 2026-09-19):
~20–30 min window with warm caches, 10 evidence gates, rollback paths.

- [ ] Schedule the window after a fresh `scripts/preflight_prod.sh` run.
- [ ] Same-host sequence: final staging dump → stop staging (12s) →
      blue/green warm-up → dump-restore → `alembic upgrade head` →
      `tls_bootstrap.sh` → smoke → monitoring cron swap.
- [ ] Start `production_decommissioning.md` stabilization clock (≥ 7 days).

## M3 — JRE-008 varga engine (weeks 3–6) · the flagship

Divisional charts, per the layer contract in `JRE-007-RESEARCH-WORKER.md`:
JRE-008 consumes JRE-003 `PlanetState` facts via the opaque `chart_identity`
join — never JRE-007 directly, never new astronomy.

- [ ] Write the canonical spec doc first (`orchestration/queue/`), as with
      JRE-006/007: sign-per-varga mapping tables (D9 navamsa, D10 dasamsa,
      D7, D12, D24, D60), determinism statement, provenance echo.
- [ ] Engine in `src/varga/` (package exists, pre-queue): pure sign-mapping
      over echoed facts; frozen models + `to_dict`/`from_dict`; zero new
      ephemeris calls.
- [ ] Validation: score against `tests/fixtures/validation_charts/`
      (Mozart, Beethoven, Lincoln, Vanderbilt, Mandela…) and the case
      studies; golden-corpus style tests.
- [ ] API: additive `/api/v1/varga/{chart}` endpoints; the frontend
      feature flag `NEXT_PUBLIC_ENABLE_EXPERIMENTAL_VARGAS` already exists
      in the CI build — ship the UI behind it (varga selector in report
      tabs + a varga ring mode in the 3D scene via the exporter).

## M4 — Gochar completion: the three deferred capabilities (weeks 5–7)

ADR-026/029 recorded each deferral with an additive-API proposal; v1.2.0
approves and lands them:

1. `JyotishService.instant_chart(...)` — natal-free transit chart
   (transit lagna/houses at an instant). Unblocks "today's gochar chart".
2. `JyotishService.crossings_between(start, end, bodies, boundaries_deg, ...)`
   — generalizes the ADR-005 bisection to caller-supplied boundaries;
   enables natal-cusp house-ingress event timelines.
3. `JyotishService.aspect_events_between(...)` — separation root-finding
   over JRE-003-owned geometry for applying/exact/separating aspects
   (ADR-029 scope).

Each is a bounded JRE-003 additive correction: new public methods, no
behavior change, machine-testable limitation messages retired with tests.

## M5 — Spatial intelligence endpoints (week 7)

The v1.1.0 `spatial_grid` + `geospatial` packages are stdlib-only and
unwired. First consumer-facing surface:

- [ ] `/api/v1/geo/horizon` — solar declination + max-visible-declination
      + circumpolar regime for a location (kranti limits, refraction-aware).
- [ ] Grid snapshot endpoint for chart-locality analytics (cell occupancy
      JSON from `SpatialGridEngine`).
- [ ] Frontend: location quality panel on the evaluate page (declination
      horizon band rendered with the existing chart palette).

## M6 — Quality & ops track (continuous, weeks 1–10)

- **Mypy grandfather burn-down:** Waves 1–2 of
  `docs/runbooks/mypy_burndown_plan.md` (23 + 9 entries, ~64 errors) —
  the list must shrink, never grow.
- **Ruff debt shrink:** start peeling `src/jrs` exclusions once Waves 1–2
  land; widen `lint:studio` beyond the studio surface (per the CI note).
- **Ops review items (F3–F6):** release-checklist rollback commands
  updated to blue/green; `NEXT_PUBLIC_API_URL` baked-output verification in
  both deploy scripts; CI docker-smoke retry loop + frontend check
  (already restored in the hardened `ci.yml`); digest-pinned images + a
  scan step; alert dedup between health and cert watchdogs; parameterized
  container names in the health monitor.
- **Host capacity:** complete staging decommissioning after the 7-day
  gate — the 3G-RAM host has no headroom while staging co-runs.

## Milestone summary

| Milestone | Weeks | Gate |
|---|---|---|
| M1 v1.1.0 final | 1 | CI green on pushed main; backup cron live |
| M2 Cutover | 2 | 10/10 gates; monitoring on prod URL |
| M3 Varga | 3–6 | Golden-corpus parity; flag-gated UI |
| M4 Gochar additive APIs | 5–7 | ADR-026 limitation tests retired |
| M5 Spatial endpoints | 7 | New endpoints + UI panel |
| M6 Quality/ops | continuous | Grandfather list −32 entries by rc |
| **v1.2.0-rc.1** | ~10 | Full pipeline green, staging soak |
| **v1.2.0** | ~11 | Per release checklist |

## Out of scope for v1.2.0

Muhurta, Prashna, full synthesis/interpretation engines; multi-host
production (load balancing); auth/multi-tenancy. The separation-of-layers
discipline (each JRE-XXX computes nothing beyond its contract) continues to
outrank feature count.

## Risks

- **Cutover slips** → everything downstream still proceeds (M3–M5 are
  independent of it); only the monitoring/capacity items wait.
- **Varga validation shortfalls** → mapping tables are classical-text
  sensitive; budget a research spike before coding (the JRE-007 doc-first
  pattern exists precisely for this).
- **Debt burn slower than planned** → waves are sized small (1–2 errors
  per module in Wave 1); a slower burn delays only the lint-scope widening,
  never the feature gates.
