#!/usr/bin/env bash
# Disk-trend alert for the JRE host.
#
# Appends a WARNING line to the maintenance log when free disk on / is
# below ALERT_THRESHOLD_GB in TWO CONSECUTIVE recorded runs (the daily
# 08:02 dry-run writes one "disk after" line per day), so a single spike
# never alerts but a real downward trend does.
#
# Set ALERT_WEBHOOK_URL to also push the warning to Slack/Mattermost.
# Cron (wired via && after the daily dry-run, so it parses a fresh log):
#   2 8 * * 1-6  docker_maintenance.sh --dry-run >> <log> 2>&1 \
#                && disk_trend_alert.sh >> <log> 2>&1

set -euo pipefail

LOG_PATH="${LOG_PATH:-/home/abhyram/.local/state/jre/docker_maintenance.log}"
ALERT_THRESHOLD_GB="${ALERT_THRESHOLD_GB:-5}"
HOST_TAG="${HOST_TAG:-JRE host}"

last_two_free_gb() {
    grep -o 'disk after: [0-9]\+G free' "$LOG_PATH" 2>/dev/null \
        | grep -o '[0-9]\+' | tail -2
}

readarray -t readings < <(last_two_free_gb)
count=${#readings[@]}

if [ "$count" -lt 2 ]; then
    # Not enough history yet — nothing to conclude.
    exit 0
fi

prev=${readings[0]}
last=${readings[1]}

if [ "$prev" -lt "$ALERT_THRESHOLD_GB" ] && [ "$last" -lt "$ALERT_THRESHOLD_GB" ]; then
    msg="WARNING [${HOST_TAG}]: free disk below ${ALERT_THRESHOLD_GB}G in two consecutive runs (${prev}G -> ${last}G). Run scripts/docker_maintenance.sh and inspect docker system df."
    echo "$msg"
    if [ -n "${ALERT_WEBHOOK_URL:-}" ]; then
        curl -fsS -m 10 -X POST -H 'Content-Type: application/json' \
            -d "{\"text\":\"$msg\"}" "$ALERT_WEBHOOK_URL" || true
    fi
fi
