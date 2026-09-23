#!/usr/bin/env bash
# Mypy grandfather-list debt histogram.
#
# The gated pyproject.toml hides grandfathered strict-mypy errors by design
# (see docs/runbooks/mypy_burndown_plan.md). This script strips the
# [[tool.mypy.overrides]] grandfather block into a temp config, runs mypy,
# and prints the TRUE remaining debt: per-module and per-error-code counts.
#
# Usage: scripts/mypy_debt_histogram.sh
# Requires: mypy (pip install mypy==2.3.1) and the runtime deps importable.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_CONFIG="$(mktemp /tmp/jre-mypy-nogf.XXXXXX.toml)"
TMP_REPORT="$(mktemp /tmp/jre-mypy-report.XXXXXX.txt)"
trap 'rm -f "$TMP_CONFIG" "$TMP_REPORT"' EXIT

# Strip everything from the grandfather-list comment to EOF (the overrides
# are the last block in pyproject.toml).
awk '/Legacy strict-mypy grandfather list/{exit} {print}' \
    "$REPO_ROOT/pyproject.toml" > "$TMP_CONFIG"

# Resolve mypy: MYPY_BIN override, then PATH, then `python3 -m mypy`
# (PEP 668 user installs). Fails with instructions if none work.
if [ -n "${MYPY_BIN:-}" ]; then
    MYPY=($MYPY_BIN)
elif command -v mypy >/dev/null 2>&1; then
    MYPY=(mypy)
elif python3 -c "import mypy" >/dev/null 2>&1; then
    MYPY=(python3 -m mypy)
else
    echo "error: mypy not found. Install it (pip install mypy==2.3.1) or" >&2
    echo "       point MYPY_BIN at it, e.g.: MYPY_BIN=/path/to/venv/bin/mypy" >&2
    exit 1
fi

MYPYPATH="$REPO_ROOT/src" "${MYPY[@]}" --config-file "$TMP_CONFIG" > "$TMP_REPORT" 2>&1 || true
tail -1 "$TMP_REPORT"

echo
echo "=== per error code ==="
grep "error:" "$TMP_REPORT" | grep -o "\[[a-z-]*\]$" | sort | uniq -c | sort -rn || true

echo
echo "=== per module ==="
grep "error:" "$TMP_REPORT" | cut -d: -f1 | sort | uniq -c | sort -rn || true
