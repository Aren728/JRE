# Deployment & Staging Verification — Review

Audit of the deploy/verification toolchain as of **2026-09-23**, against the
state at tag `v1.1.0-rc.1` (commit `64b6c9f`). Scope: the paths between
"CI is green" and "production serves the new version" — staging deploy,
verification gates, release checklist, and cutover readiness.

> **Recovery note (2026-09-23):** this file is the sole survivor of the
> original working tree; re-materialized here from session context after
> the host-side deletion. Restore to `docs/runbooks/`.

Verdict up front: **the discipline is production-grade** (evidence-checked
go/no-go gates, measured game-day timings, auto-rollback, drill-backed
backups), but the review found **2 real gaps, 4 stale-doc drifts, and 3
improvement opportunities**. None block a v1.1.0 final release if the
pre-release actions below are done.

## Toolchain inventory (what exists and what it guarantees)

| Stage | Mechanism | Guarantee |
|---|---|---|
| CI quality gates | `ci.yml`: sync guard → ruff → mypy strict → xfail_strict probe → pytest (5500) → parallel frontend (tsc, lint:studio, jest, next build) → docker staging build + smoke → Playwright E2E | A green SHA is tested, typed, linted, and boots in a container |
| Staging CI | `staging-ci.yml`: postgres service → migrations → `alembic check` drift gate → pytest | Model/migration parity on every push |
| Staging deploy | `scripts/deploy_staging.sh` — blue/green, pre-switch smoke on idle IP, migrations pre-switch, graceful nginx reload, post-switch smoke with auto-rollback | Zero-downtime; a bad build never receives traffic |
| Prod deploy | `scripts/deploy_prod_bluegreen.sh` — same pattern + **migration gate** (refuses to switch unless idle color is at alembic head) | Staging-only auto-migrate never leaks to prod |
| Release | `production_release_checklist.md` — env audit (`audit_prod_env.sh`), migration dry-runs, verified backups (`restore_drill.sh`), rollback trigger table | Evidence-checked, not memory-checked |
| Cutover | `production_cutover.md` — 10 gates (G1–G10), rehearsed end-to-end 2026-09-19 with measured timings | Known duration (~20–30 min warm), known failure modes |
| Runtime watch | `staging_health_monitor.sh` (cron 1 min + webhook), `certbot_renew.sh` (12h) | Detection within a minute; TLS never lapses |

The blueprint is sound. The findings below are about **execution readiness**,
not design.

## Findings

### F1 — Staging CI validates migrations against the wrong Postgres major (HIGH)

`staging-ci.yml` pins its service container to **`postgres:15-alpine`**; the
staging stack, both prod compose files, and the cutover runbook all run
**`postgres:16-alpine`**. Two consequences:

- The `alembic upgrade head` + `alembic check` drift gate in CI can pass on
  15 and then fail (or silently differ) on 16 — the exact class of surprise
  the gate exists to prevent.
- The checklist's "restore drill" and CI's migration run never exercise the
  same server version production uses.

**Fix (one line):** change the service image to `postgres:16-alpine` in
`staging-ci.yml`. Also consider pinning the stack images by digest in a
follow-up so "16-alpine" means the same bytes everywhere.

### F2 — Automated backups exist only as a *manual checklist item* (HIGH)

Every backup reference in the toolchain is executor-driven: the release
checklist says "take a pg_dump", the cutover says "final dump in the window",
and `deploy_prod_bluegreen.sh` prints "pg_dump first" as a reminder. There is
**no scheduled dump and no verification cron**. A skipped or failed manual
dump is invisible until the moment a rollback needs it.

**Fix:** cron a nightly `pg_dump --no-owner --clean --if-exists` into
`dumps/` with retention, and run `restore_drill.sh` weekly on the newest
dump (the drill is ~5s measured). Wire a webhook alert on drill failure the
same way `staging_health_monitor.sh` does. Until this lands, the "verified
backup" gate is only as reliable as human memory at 2 a.m.

### F3 — Stale doc drift (MEDIUM, 4 items)

- `production_release_checklist.md` phase 1/2 still reference
  `docker-compose.prod.yml` (legacy single-color) as the primary path, while
  the cutover runbook and `production_decommissioning.md` make blue/green
  the production target. Rollback commands citing legacy container names
  (`jre-backend-1`) will be wrong after cutover.
- `staging_prod_parity_review.md` "Re-verify before production cutover"
  checkbox list is unchecked but its items are all actually satisfied
  (config renders, dry-run on HEAD, cutover decision recorded = blue/green
  ported). Tick them or re-date the review.
- `production_cutover.md` Phase 5 monitoring note says container-name
  diagnostics "adjust later" — before the first prod deploy, make
  `staging_health_monitor.sh` container names env-configurable
  (`jre-proxy-1`/`jre-api-*` are staging names; prod is `jre-prod-*`).
- `production_decommissioning.md` retirement of staging will delete the
  staging health cron — schedule the replacement prod cron in the same
  window, not "days later", or there is a monitoring blind spot.

### F4 — `NEXT_PUBLIC_API_URL` is baked at build with no output verification (MEDIUM)

The frontend bakes `NEXT_PUBLIC_API_URL` into the bundle at build time; the
runbooks correctly warn about it, but nothing *verifies* the baked value.
Staging's deploy rebuilds the frontend with compose, and CI builds with
`http://localhost:8000` — for staging same-origin `http://localhost/api` is
expected, but if the build arg ever drifts, every browser call fails while
all backend-side smokes stay green (the smoke script's frontend check is
SSR-only).

**Fix:** add one grep-based post-build check to `deploy_staging.sh` /
`deploy_prod_bluegreen.sh`:
`docker run --rm <frontend-image> sh -c "grep -ro 'NEXT_PUBLIC_API_URL[^,]*' .next | head -1"`
and assert it matches the environment's expected origin. Cheap insurance
against a silent, hard-to-debug class of outage.

### F5 — CI's docker smoke uses fixed sleeps and no frontend check (LOW)

`ci.yml` `docker-compose-check` does `sleep 10` then curls the backend.
Works today (healthcheck-gated startup), but `sleep`-based readiness is
flaky by nature under runner load. Prefer a retry loop on the health
endpoint (the E2E job already does `--retry-connrefused` — copy that
pattern), and add a frontend HTTP 200 check so the staging-image build of
the frontend is actually proven, not just built.

### F6 — Timings and thresholds are one-host data (LOW, accepted)

All measured timings (2s healthy, 6s rollback, 12s stop) come from the
2026-09-18/19 game days on the single 3G-RAM host. That host **is**
production per the hosting decision, so the numbers stand; but re-measure
after any hardware/instance change, and note the RAM ceiling: the full
prod stack (~2G) + anything else on the box leaves no headroom for
on-host debugging during an incident. The decommissioning of staging
(days after cutover) is also a *capacity* fix, not just hygiene.

## Pre-v1.1.0-final gate (do these before removing the `rc` suffix)

1. F1: bump `staging-ci.yml` to `postgres:16-alpine`; confirm green run.
2. F2: land nightly-dump + weekly-drill cron (or accept and record the
   manual-only risk explicitly in the release checklist).
3. F3 (first bullet): update release-checklist rollback commands to the
   blue/green compose file and container names.
4. Run `scripts/preflight_prod.sh <domain>` once for fresh GO evidence if
   the cutover window is to be scheduled this cycle.
5. Rehearsal timing table already current (2026-09-19) — no action.

## Post-release improvements (v1.2.0 candidates)

- Digest-pinned images + `docker scout`/`trivy` scan step in CI.
- Alert deduplication between the health watchdog and the cert watchdog
  (both webhook the same endpoint; a proxy outage would fire both).
- `restore_drill.sh --expect-rows` wiring into the nightly backup cron's
  success criterion, so backup validity — not just existence — is the
  monitored property.
