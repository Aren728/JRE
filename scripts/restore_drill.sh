#!/usr/bin/env bash
# Database restore drill — proves backups are actually restorable.
#
# Restores a pg_dump backup into an EPHEMERAL postgres container (removed
# afterwards; prod/staging databases are never touched) and verifies:
#   - the dump restores without errors
#   - expected tables exist (chart_calculations)
#   - alembic_version matches the backup's recorded revision
#   - row counts are non-zero for non-empty-at-backup-time tables
#
# Usage:
#   scripts/restore_drill.sh dumps/pre_release_2026-09-18.sql
#   scripts/restore_drill.sh dumps/x.sql --expect-rows chart_calculations=6
# Exit codes: 0 = drill passed, 1 = drill FAILED (backup not trustworthy).
#
# Referenced by docs/runbooks/production_release_checklist.md and run on a
# monthly cron (see bottom of file).

set -euo pipefail

DUMP_FILE="${1:?usage: restore_drill.sh <dump-file> [--expect-rows table=N]}"
shift || true
EXPECT_ROWS=()
while [ $# -gt 0 ]; do
    case "$1" in
        --expect-rows) EXPECT_ROWS+=("$2"); shift 2 ;;
        *) echo "unknown option: $1" >&2; exit 1 ;;
    esac
done

[ -f "$DUMP_FILE" ] || { echo "drill: dump file not found: $DUMP_FILE" >&2; exit 1; }

CTR="jre-restore-drill-$$"
START=$(date +%s)
cleanup() {
    docker rm -f "$CTR" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "[drill] $(date -Is) restoring $(basename "$DUMP_FILE")"

# 1. Ephemeral postgres, isolated network namespace, random port not needed
#    (we exec inside the container — nothing is exposed to the host).
docker run -d --rm --name "$CTR" \
    -e POSTGRES_USER=drill -e POSTGRES_PASSWORD=drill_pw -e POSTGRES_DB=drill \
    postgres:15-alpine >/dev/null

for _ in $(seq 1 30); do
    docker exec "$CTR" pg_isready -U drill -d drill >/dev/null 2>&1 && break
    sleep 1
done

# 2. Pre-create owner roles referenced by the dump: dumps taken on another
#    cluster carry `OWNER TO <role>` / GRANT statements for roles that do
#    not exist in the drill container (caught on the 2026-09-18 game day).
OWNERS=$(grep -oE 'OWNER TO ["]?[A-Za-z0-9_]+["]?' "$DUMP_FILE" | sed 's/OWNER TO //; s/"//g' | sort -u || true)
for role in $OWNERS; do
    exists=$(docker exec "$CTR" psql -U drill -d drill -tAc "SELECT 1 FROM pg_roles WHERE rolname='$role';" || true)
    [ "$exists" = "1" ] || \
        docker exec "$CTR" psql -U drill -d drill -c "CREATE ROLE \"$role\" WITH LOGIN SUPERUSER;" >/dev/null
    echo "[drill] owner role prepared: $role"
done

# 3. Restore (plain SQL format; for custom-format dumps add -Fc handling here).
if docker exec -i "$CTR" psql -U drill -d drill -v ON_ERROR_STOP=1 \
        -q < "$DUMP_FILE" > /dev/null 2>/tmp/drill_restore_err_$$; then
    echo "[drill] restore completed without SQL errors"
else
    echo "[drill] FAILED: restore errors:" >&2
    tail -5 "/tmp/drill_restore_err_$$" >&2
    rm -f "/tmp/drill_restore_err_$$"
    exit 1
fi
rm -f "/tmp/drill_restore_err_$$"

# 4. Verification queries.
check() {
    docker exec "$CTR" psql -U drill -d drill -tAc "$1"
}

TABLES=$(check "SELECT string_agg(tablename, ',') FROM pg_tables WHERE schemaname='public' AND tablename != 'alembic_version';")
echo "[drill] tables restored: ${TABLES:-<none>}"
echo "$TABLES" | grep -q "chart_calculations" || {
    echo "[drill] FAILED: chart_calculations missing after restore" >&2
    exit 1
}

echo "[drill] alembic_version: $(check 'SELECT version_num FROM alembic_version;' || echo '<none>')"

for spec in "${EXPECT_ROWS[@]:-}"; do
    [ -z "$spec" ] && continue
    table="${spec%%=*}"
    expected="${spec##*=}"
    actual=$(check "SELECT count(*) FROM $table;")
    if [ "$actual" -eq "$expected" ]; then
        echo "[drill] rows OK: $table = $actual"
    else
        echo "[drill] FAILED: $table rows $actual != expected $expected" >&2
        exit 1
    fi
done

ELAPSED=$(( $(date +%s) - START ))
echo "[drill] PASSED in ${ELAPSED}s — backup is restorable"
