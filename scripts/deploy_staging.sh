#!/usr/bin/env bash
# Staging deployment for the JRE stack.
#
# Modes:
#   local  — deploy on this host (default; used by CI self-deploy or by hand)
#   ssh    — run this same script on a remote host over SSH
#
# CI usage (secrets optional — the job self-skips when unset):
#   DEPLOY_MODE=ssh SSH_HOST=staging.example.com SSH_USER=deploy \
#     scripts/deploy_staging.sh
#
# Manual local usage:
#   scripts/deploy_staging.sh

set -euo pipefail

MODE="${DEPLOY_MODE:-local}"
SSH_HOST="${SSH_HOST:-}"
SSH_USER="${SSH_USER:-}"
SSH_KEY_FILE="${SSH_KEY_FILE:-}"        # optional identity file
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.staging.yml}"
APP_DIR="${APP_DIR:-}"                  # remote repo path (ssh mode)
COMPOSE="docker compose -f ${COMPOSE_FILE}"

ssh_run() {
    if [ -n "$SSH_KEY_FILE" ]; then
        ssh -i "$SSH_KEY_FILE" -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
            "${SSH_USER}@${SSH_HOST}" "$@"
    else
        ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
            "${SSH_USER}@${SSH_HOST}" "$@"
    fi
}

deploy() (
    set -e
    cd "$1"

    # Disk guard: builds are the main disk consumer on this host, and the
    # weekly cron only runs Sundays — a mid-week build at low disk is how the
    # 2026-09-18 "No space left on device" incident happened. Trigger the
    # standard cleanup whenever free space drops below the threshold.
    # (docker_maintenance.sh deliberately avoids container/volume pruning.)
    FREE_GB=$(df -BG --output=avail / | tail -1 | tr -dc '0-9')
    if [ "${FREE_GB:-0}" -lt "${DEPLOY_MIN_FREE_GB:-4}" ]; then
        echo "[deploy] free disk ${FREE_GB}G < ${DEPLOY_MIN_FREE_GB:-4}G — running docker maintenance first"
        bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_maintenance.sh"
    fi

    echo "[deploy] $(date -Is) deploying $(git rev-parse --short HEAD)"

    # Deterministic code state: refusing non-ff pulls avoids deploying
    # divergent local history on the staging host.
    git fetch origin main
    git pull --ff-only origin main
    echo "[deploy] now at $(git rev-parse --short HEAD)"

    $COMPOSE up -d --build backend frontend

    # Wait for backend health (compose healthcheck gates the smoke tests).
    echo "[deploy] waiting for backend health..."
    for _ in $(seq 1 60); do
        [ "$(docker inspect -f '{{.State.Health.Status}}' jre-api-staging 2>/dev/null)" = "healthy" ] && break
        sleep 2
    done
    if [ "$(docker inspect -f '{{.State.Health.Status}}' jre-api-staging 2>/dev/null)" != "healthy" ]; then
        echo "[deploy] ERROR: backend unhealthy" >&2
        docker compose -f "$COMPOSE_FILE" ps >&2 || true
        docker logs jre-api-staging --tail 50 >&2 || true
        exit 1
    fi

    # Smoke tests mirror ci.yml's docker job.
    export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://jre_user:jre_staging_password@localhost:5432/jre_staging_db}"
    curl --fail --retry 5 --retry-delay 3 http://localhost:8000/api/v1/health
    echo
    curl --fail -s -X POST http://localhost:8000/api/v1/analyze \
        -H "Content-Type: application/json" \
        -d '{"date": "1995-10-24", "time": "14:30:00", "latitude": 13.0827, "longitude": 80.2707, "timezone": "Asia/Kolkata"}' \
        -o /dev/null
    echo "[deploy] smoke tests passed"

    # Schema: fail loudly if staging db is not at head (do NOT auto-upgrade —
    # migrations on the staging db are a reviewed, explicit step; see
    # docs/runbooks/database_migrations.md).
    docker exec jre-api-staging alembic upgrade head

    # Post-deploy guard: a cold rebuild can add several GB of build cache.
    # If the deploy ends below the threshold, reclaim immediately instead of
    # leaving the next build to run at dangerously low disk.
    FREE_GB=$(df -BG --output=avail / | tail -1 | tr -dc '0-9')
    if [ "${FREE_GB:-0}" -lt "${DEPLOY_MIN_FREE_GB:-4}" ]; then
        echo "[deploy] post-deploy disk ${FREE_GB}G < ${DEPLOY_MIN_FREE_GB:-4}G — reclaiming build cache"
        bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_maintenance.sh"
    fi

    echo "[deploy] $(date -Is) done: staging runs $(git rev-parse --short HEAD)"
)

case "$MODE" in
    local)
        if [ -n "$SSH_HOST" ]; then
            echo "[deploy] DEPLOY_MODE=local but SSH_HOST is set; doing a local deploy" >&2
        fi
        deploy "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
        ;;
    ssh)
        if [ -z "$SSH_HOST" ]; then
            echo "[deploy] DEPLOY_MODE=ssh requires SSH_HOST" >&2
            exit 1
        fi
        : "${APP_DIR:?APP_DIR must point at the repo on the remote host}"
        ssh_run "cd ${APP_DIR} && DEPLOY_MODE=local bash scripts/deploy_staging.sh"
        ;;
    *)
        echo "unknown DEPLOY_MODE: $MODE (use local|ssh)" >&2
        exit 1
        ;;
esac
