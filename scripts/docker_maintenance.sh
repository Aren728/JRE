#!/usr/bin/env bash
# Docker disk-space maintenance for the JRE host.
#
# Purpose: prevent "No space left on device" incidents (see 2026-09-18:
# build cache filled the disk and the staging db container could not start).
#
# What it deletes (safe):
#   - dangling build cache older than $BUILD_CACHE_KEEP_DAYS
#   - dangling (untagged) images
#   - build cache above the free-space target, oldest first
#
# What it NEVER deletes:
#   - named volumes (jre_postgres_data holds the staging database)
#   - tagged images, running or stopped containers
#
# Install (weekly, Sunday 04:17, low-traffic window; log lives under
# ~/.local/state so it survives /tmp cleanup):
#   crontab -e
#   17 4 * * 0  /home/abhyram/JRE/scripts/docker_maintenance.sh >> /home/abhyram/.local/state/jre/docker_maintenance.log 2>&1
#
# Dry run:  docker_maintenance.sh --dry-run

set -euo pipefail

BUILD_CACHE_KEEP_DAYS="${BUILD_CACHE_KEEP_DAYS:-168}"   # 1 week in hours
MIN_FREE_GB="${MIN_FREE_GB:-5}"                        # prune cache until this much is free
DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

run() {
    echo "[docker_maintenance] $*"
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "    (dry-run, skipped)"
    else
        "$@"
    fi
}

free_gb() {
    df -BG --output=avail / | tail -1 | tr -dc '0-9'
}

echo "[docker_maintenance] $(date -Is) start (dry-run=$DRY_RUN)"
echo "[docker_maintenance] disk before: $(free_gb)G free on /"

# 1. Stale dangling build cache (default: unused for a week).
run docker builder prune --force --filter "until=${BUILD_CACHE_KEEP_DAYS}h"

# 2. Dangling (untagged) images — leftover layers from rebuilds.
run docker image prune --force

# 3. If still below the free-space target, prune ALL unused build cache
#    (rebuildable; does not touch images/volumes/containers).
if [ "$(free_gb)" -lt "$MIN_FREE_GB" ]; then
    echo "[docker_maintenance] below ${MIN_FREE_GB}G free — pruning all build cache"
    run docker builder prune --force --all
fi

echo "[docker_maintenance] disk after: $(free_gb)G free on /"

# Alert hook: pipe the summary to Slack/webhook by setting ALERT_WEBHOOK_URL.
if [ -n "${ALERT_WEBHOOK_URL:-}" ] && [ "$(free_gb)" -lt "$MIN_FREE_GB" ]; then
    curl -fsS -m 10 -X POST -H 'Content-Type: application/json' \
        -d "{\"text\":\"[JRE host] disk still below ${MIN_FREE_GB}G after docker maintenance: $(free_gb)G free\"}" \
        "$ALERT_WEBHOOK_URL" || true
fi

echo "[docker_maintenance] $(date -Is) done"
