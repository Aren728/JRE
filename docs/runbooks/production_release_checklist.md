# Production Release Execution Checklist

Standard order of operations for shipping a release to the production
host. Companion docs: `database_migrations.md` (migration + dry-run
detail), `docker-compose.prod.yml` (runtime template),
`scripts/deploy_staging.sh` (deploy pattern this extends).

Fill in per release: **release commit** `____________`, **executor**
`____________`, **window** `____________`.

## 0. Pre-deployment (T-1 day)

- [ ] Release commit is on `main` with **both CI workflows green**
      (check: GitHub Actions on the exact SHA, not "latest run").
- [ ] `alembic check` passed in staging-ci (no model/migration drift).
- [ ] Changelog reviewed for **schema changes** → if any, a migration
      revision exists and was verified on a throwaway db
      (`upgrade head` → `downgrade base` → `upgrade head`).
- [ ] Staging deploy verified: `scripts/deploy_staging.sh` ran clean,
      smoke tests passed, `alembic current` shows the expected head.
- [ ] Host disk ≥ 8G free (`df -h /`); if not, run
      `scripts/docker_maintenance.sh` and re-check.
- [ ] Database backup taken **and restore-tested**:
      `pg_dump "$DATABASE_URL" > dumps/pre_release_$(date -Is).sql`
      then `scripts/restore_drill.sh <dump> --expect-rows <table>=<n>`
      (automates the scratch restore + verification; ~5s on this dataset).
      Note: dumps taken with owner roles from another cluster need the
      drill's role pre-creation — `pg_dump --no-owner` avoids it entirely
      and is preferred for future backups.

## 1. Pre-flight on the release window

- [ ] Announce maintenance window; confirm no in-flight traffic.
- [ ] `docker compose -f docker-compose.prod.yml --env-file .env.prod pull`
      (or `build --no-cache` for a first release).
- [ ] Confirm `.env.prod` values: `DATABASE_URL` starts with
      `postgresql+psycopg://`, required vars all set
      (`config` must render with zero warnings).
- [ ] Env audit passes:
      `scripts/audit_prod_env.sh .env.prod` — fails on missing required
      vars, wrong driver scheme, fallback/local tokens (localhost,
      postgres:postgres, changeme, staging leftovers), or a password
      under 12 chars. Exit 1 blocks the release.

## 2. Dry-run verifications (never skip on prod)

- [ ] `docker compose --env-file .env.prod -f docker-compose.prod.yml config`
      exits 0.
- [ ] Alembic SQL preview matches intent:
      `run --rm backend alembic upgrade head --sql` (no DB connection).
- [ ] Full dry-run per `database_migrations.md` § Pre-release dry-run
      against a throwaway env file/project (`-p jre-prodtest`), including
      `alembic check` → "No new upgrade operations detected."

## 3. Deployment

- [ ] `up -d` the stack; wait for backend healthcheck `healthy`.
- [ ] `run --rm backend alembic upgrade head` (migrations are NEVER
      automatic). Expect the new revisions to apply; abort on any error —
      transactional DDL leaves the db at the prior revision.
- [ ] `run --rm backend alembic check` → no new operations.
- [ ] Smoke: `/api/v1/health` returns the release version;
      `POST /api/v1/analyze` returns 200 with planets + synthesis.

## 4. Rollback triggers (execute when any of these fire)

| Trigger | Action |
|---|---|
| `alembic upgrade head` errors mid-run | Stop. Do not retry blindly — inspect, `downgrade` only with a verified plan |
| Health check unhealthy after deploy | `down -v` is FORBIDDEN (destroys data); `down` (keep volume), redeploy previous release commit |
| Smoke test fails | Redeploy previous commit; migrations that already applied may stay if backwards-compatible |
| Data corruption suspected | Restore the pre-release `pg_dump` into a scratch db, diff, then decide; never restore over prod without a second fresh dump |
| Disk < 1G at any point | `down` (keep volumes), run `docker_maintenance.sh`, reassess |

Rollback rule of thumb: **roll back code freely; roll back schema only
with a verified `downgrade` or a verified restore.**

## Measured timings (game day 2026-09-18, isolated jre-gameday env)

| Phase | Measured | Notes |
|---|---|---|
| Phase 1 pre-flight | < 1s | incl. env audit blocking a naive env (exit 1) |
| Phase 2 build (warm cache) | ~1s | cold cache adds ~2–5 min per image |
| Phase 2 full dry-run | ~5.5 min | build-dominated; sql preview + upgrade + check seconds |
| Phase 3 deploy → healthy | ~2s | after images exist |
| **Rollback (image swap, same db)** | **~6s** | detection → swap → health green |
| Restore drill (fresh ephemeral db) | ~5s | first real run FAILED on missing owner role — fixed in drill script |

Realistic planning estimate for a production release on this host:
**~15 min with warm caches, ~25–30 min cold**, plus the maintenance
window for traffic coordination.

## 5. Post-deployment

- [ ] `alembic current` shows the expected revision `(head)`.
- [ ] Watch logs 10 minutes (`docker compose logs -f backend`) for
      recurring tracebacks.
- [ ] Update this document's per-release fields; note any deviation from
      the checklist and why.
