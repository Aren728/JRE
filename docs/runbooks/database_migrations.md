# Database Migrations Runbook — Alembic

Single source of truth for applying schema changes. Read this before
touching any non-local database.

## Concepts

| Command | What it does | When to use |
|---|---|---|
| `alembic upgrade head` | **Executes** migration DDL up to head; records history in `alembic_version` | Databases where schema is managed *by* Alembic |
| `alembic stamp head` | **Only writes** `alembic_version = head`; executes **no DDL** | Databases whose schema already exists but predates Alembic |
| `alembic current` | Show which revision a database is at | Health check after any of the above |

Rule of thumb: **stamp when the tables are already there, upgrade when
they are not.** Stamping a database that is missing tables leaves it
"at head" with no schema; upgrading a database that already has the
tables fails with "table already exists" (safe — it aborts before
changing anything).

## Standard flow: fresh / Alembic-managed database

```bash
export DATABASE_URL="postgresql+psycopg://user:pass@host:5432/db"
alembic upgrade head          # applies DDL, records aef04248244b+
alembic current               # verify: shows the revision
```

Used by: CI (staging-ci.yml against the ephemeral postgres service),
fresh staging volumes, and (later) production after its initial setup.

## Exception flow: pre-existing database (one-time adoption)

Do this only when `alembic current` errors with "relation
alembic_version does not exist" **and** the tables already exist.

```bash
# 1. Confirm the schema really is present and matches the revision's target.
psql "$DATABASE_URL" -c "\d chart_calculations"

# 2. Take a snapshot before touching version state.
pg_dump "$DATABASE_URL" > pre_stamp_backup_$(date -Is).sql

# 3. Stamp WITHOUT executing DDL.
alembic stamp head

# 4. Verify: current shows head; upgrade is now a no-op.
alembic current        # -> aef04248244b (head)
alembic upgrade head   # -> no output, exit 0
```

Applied 2026-09-18 to the staging db (`jre_staging_db`): table existed
from pre-Alembic development, so it was stamped to `aef04248244b` instead
of upgraded; data was untouched (verified: row count unchanged).

## Making a new migration (schema changes)

```bash
# 1. Edit src/jrs/db/models.py, then autogenerate against a THROWAWAY db:
docker run -d --rm --name jre-mig-gen \
  -e POSTGRES_USER=jre_user -e POSTGRES_PASSWORD=jre_staging_password \
  -e POSTGRES_DB=jre_staging_db -p 55432:5432 postgres:15-alpine
export DATABASE_URL="postgresql+psycopg://jre_user:jre_staging_password@localhost:55432/jre_staging_db"

alembic revision --autogenerate -m "describe the change"

# 2. REVIEW the generated file — autogenerate misses server defaults and
#    can drop things unexpectedly. Edit by hand where needed.

# 3. Verify the full lifecycle on the throwaway db, then remove it:
alembic upgrade head
alembic downgrade base
alembic upgrade head
docker stop jre-mig-gen
```

`alembic/env.py` imports models via the **canonical `jrs.db.*` path** —
do not switch it to `src.jrs.db.*`: that creates a second module
instance with empty metadata and autogenerate emits nothing.

## Deployment wiring

- `scripts/deploy_staging.sh` runs `alembic upgrade head` after each
  staging deploy and fails loudly if the db cannot reach head. It never
  stamps automatically — stamping is always a reviewed, manual step.
- Production (when it exists): run `alembic upgrade head` in a
  maintenance window **after** `pg_dump`, and only after it has passed on
  staging. Never `stamp` production unless adopting a pre-Alembic schema
  (exception flow above).

## Health check

```bash
docker exec jre-api-staging alembic current   # staging: expect aef04248244b (head) or later
```
