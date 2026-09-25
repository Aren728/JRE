#!/usr/bin/env python3
"""Phase 6 (Track B): OpenAPI 3.1 contract verification.

FastAPI ≥0.99 emits native OpenAPI 3.1 documents. This script pins the
platform contract so DTO regressions surface in CI rather than in
client integrations:

- the served OpenAPI version MUST be 3.1.x;
- every endpoint must carry operationIds (stable client codegen);
- declared response models must resolve (no unresolvable $refs);
- the strict-validation contract markers are present
  (``BirthDataInput``/``EvaluationResponse`` components).

Usage::

    python scripts/verify_openapi_contract.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))


def main() -> int:
    from fastapi.openapi.utils import get_openapi

    from jrs.api.main import (
        API_DESCRIPTION,
        API_TITLE,
        API_VERSION,
        app,
    )

    schema = get_openapi(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        routes=app.routes,
    )

    failures: list[str] = []

    # 1. OpenAPI 3.1 native emission.
    openapi_version = schema.get("openapi", "")
    if not openapi_version.startswith("3.1"):
        failures.append(
            f"openapi version is {openapi_version!r}, expected 3.1.x "
            "(native FastAPI 3.1 contract)"
        )

    # 2. Every operation carries a stable operationId.
    missing_op_ids = [
        f"{method.upper()} {path}"
        for path, methods in schema.get("paths", {}).items()
        for method in methods
        if method in {"get", "post", "put", "patch", "delete"}
        and not methods[method].get("operationId")
    ]
    if missing_op_ids:
        failures.append(
            "operations missing operationId: " + ", ".join(missing_op_ids)
        )

    # 3. Strict-validation contract markers present.
    components = schema.get("components", {}).get("schemas", {})
    for marker in ("BirthDataInput", "EvaluationResponse"):
        if marker not in components:
            failures.append(f"missing OpenAPI component: {marker}")

    # 4. Declared response models resolve (no dangling $refs).
    raw = json.dumps(schema)
    import re

    refs = set(re.findall(r'"\$ref":\s*"#/components/schemas/([^"]+)"', raw))
    dangling = sorted(r for r in refs if r not in components)
    if dangling:
        failures.append("dangling $refs: " + ", ".join(dangling))

    if failures:
        print("OPENAPI CONTRACT: FAIL", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    n_paths = len(schema.get("paths", {}))
    print(
        f"OPENAPI CONTRACT: PASS (openapi={openapi_version}, "
        f"paths={n_paths}, components={len(components)})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
