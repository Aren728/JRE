#!/usr/bin/env bash
# Pre-flight audit of the production env file (default: .env.prod).
#
# Fails (exit 1) when any of the following hold:
#   - file missing, or a required variable is unset/empty
#   - DATABASE_URL does not use the postgresql+psycopg:// scheme
#     (bare postgresql:// selects psycopg2, which is not installed)
#   - any value contains a forbidden token: localhost / 127.0.0.1 /
#     postgres:postgres / changeme / example / staging /
#     jre_staging_password / prod_test_pw / angle brackets
#   - POSTGRES_PASSWORD is shorter than 12 characters
#
# Usage:
#   scripts/audit_prod_env.sh [env-file]        # default .env.prod
# Exit codes: 0 = audit passed, 1 = violations found.
#
# Referenced by docs/runbooks/production_release_checklist.md (phase 1).

set -euo pipefail

ENV_FILE="${1:-.env.prod}"
FAILURES=0

fail() { echo "  ✗ $*"; FAILURES=$((FAILURES + 1)); }
pass() { echo "  ✓ $*"; }

if [ ! -f "$ENV_FILE" ]; then
    echo "audit: env file not found: $ENV_FILE"
    exit 1
fi
echo "audit: $ENV_FILE"

FORBIDDEN='localhost|127\.0\.0\.1|postgres:postgres|changeme|CHANGEME|example|jre_staging_password|prod_test_pw|<|>'

# Collect KEY=VALUE pairs (comments and blank lines skipped).
declare -A VALUES=()
while IFS='=' read -r key value; do
    [ -z "$key" ] && continue
    case "$key" in \#*) continue ;; esac
    VALUES["$key"]="$value"
done < <(grep -v '^[[:space:]]*$' "$ENV_FILE")

# 1. Required variables present and non-empty.
echo "required variables:"
for var in POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB DATABASE_URL; do
    val="${VALUES[$var]:-}"
    if [ -z "$val" ]; then
        fail "$var is missing or empty"
    else
        pass "$var is set"
    fi
done

# 2. DATABASE_URL scheme.
url="${VALUES[DATABASE_URL]:-}"
echo "driver scheme:"
if [[ "$url" == postgresql+psycopg://* ]]; then
    pass "DATABASE_URL uses postgresql+psycopg:// (psycopg 3)"
else
    fail "DATABASE_URL must start with postgresql+psycopg:// (got: ${url%%@*}...)"
fi

# 3. Forbidden tokens in any value (hostnames, default creds, staging leftovers).
echo "forbidden tokens:"
matched=0
for key in "${!VALUES[@]}"; do
    val="${VALUES[$key]}"
    if echo "$val" | grep -Eq "$FORBIDDEN"; then
        # Name the variable and the token class, never the secret value.
        token=$(echo "$val" | grep -Eo "$FORBIDDEN" | head -1)
        fail "$key contains forbidden token: $token"
        matched=1
    fi
done
[ "$matched" -eq 0 ] && pass "no forbidden tokens found"

# 4. Password strength floor.
echo "credentials:"
pw="${VALUES[POSTGRES_PASSWORD]:-}"
if [ -n "$pw" ] && [ "${#pw}" -lt 12 ]; then
    fail "POSTGRES_PASSWORD shorter than 12 characters (${#pw})"
else
    [ -n "$pw" ] && pass "POSTGRES_PASSWORD length ${#pw} ≥ 12"
fi

echo "audit result:"
if [ "$FAILURES" -gt 0 ]; then
    echo "  FAILED with $FAILURES violation(s)"
    exit 1
fi
echo "  PASSED"
