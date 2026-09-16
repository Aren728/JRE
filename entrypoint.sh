#!/bin/sh
set -e

echo "ephemeris check:"
ls -1 datasets/ephemeris/*.se1

PROJECT_VERSION=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
echo "package version from pyproject.toml: $PROJECT_VERSION"

uvicorn src.jrs.api.main:app --host 0.0.0.0 --port 8000 &
APP_PID=$!

sleep 8

HEALTH=$(curl -fsSL http://localhost:8000/api/v1/health)
echo "health response:"
echo "$HEALTH"

HEALTH_VERSION=$(echo "$HEALTH" | python -c "import sys,json; print(json.load(sys.stdin)['version'])")
if [ "$HEALTH_VERSION" != "$PROJECT_VERSION" ]; then
  echo "version mismatch: $HEALTH_VERSION vs $PROJECT_VERSION"
  exit 1
fi

echo "staging smoke test passed"
wait $APP_PID
