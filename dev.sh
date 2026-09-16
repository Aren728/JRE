#!/usr/bin/env bash
set -e

# Make sure we run from the script's directory
cd "$(dirname "$0")"

# Activate virtualenv if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

echo "Starting Backend on http://127.0.0.1:8000..."
python -m uvicorn src.jrs.api.main:app --reload --port 8000 &

echo "Starting Frontend on http://localhost:3000..."
(cd frontend && npm run dev) &

wait