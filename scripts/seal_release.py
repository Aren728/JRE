#!/usr/bin/env python3
"""Phase 9F: Seal the JRE 1.0.0-rc1 release manifest.

Freezes the full release manifest into
``releases/v1.0.0-rc1.json``:

- git commit (HEAD) and worktree-cleanliness;
- Python / OS versions and the Swiss Ephemeris engine build hash;
- database schema version (alembic head revision);
- API schema hash (canonical OpenAPI 3.1 document);
- frontend source content hash (deterministic stand-in for the build
  hash: sorted sha256 over tracked frontend sources — the Next build
  output itself is non-deterministic by design);
- golden-state aggregate hash (all 50 Stage 1-9 manifests);
- benchmark seal hash (JRE-BENCH-001.json) and locked-dependency hash.

``--check`` recomputes every component against the sealed file; any
drift fails (the manifest is immutable once sealed — a new release
candidate gets a new file).

Usage::

    python scripts/seal_release.py             # write the seal
    python scripts/seal_release.py --check     # verify live == sealed
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

RELEASE_SCHEMA_VERSION = "1.0.0"
RELEASES_DIR = REPO_ROOT / "releases"
DEFAULT_RELEASE_ID = "v1.0.0"

# Frontend directories hashed for the source-content seal (build output
# is intentionally excluded: Next.js embeds non-deterministic ids).
FRONTEND_SEED_DIRS: tuple[str, ...] = (
    "app",
    "components",
    "config",
    "lib",
    "__tests__",
)
FRONTEND_SEED_FILES: tuple[str, ...] = (
    "package.json",
    "package-lock.json",
    "tsconfig.json",
    "next.config.ts",
    "jest.config.js",
    "jest.setup.ts",
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _git(args: list[str]) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, cwd=REPO_ROOT, check=True
    ).stdout.strip()


def _git_commit() -> dict[str, Any]:
    commit = _git(["rev-parse", "HEAD"])
    dirty = bool(_git(["status", "--porcelain"]).strip())
    return {"commit": commit, "worktree_clean": not dirty}


def _swisseph() -> dict[str, Any]:
    import swisseph as swe

    module_file = sys.modules.get("swisseph").__file__ or ""
    return {
        "version": str(swe.version),
        "module": "swisseph",
        "build_sha256": _sha256_file(Path(module_file)) if module_file else "",
    }


def _alembic_head() -> str:
    """Resolve the alembic head revision by scanning migration files."""
    versions_dir = REPO_ROOT / "alembic" / "versions"
    revisions: dict[str, str] = {}
    down_refs: set[str] = set()
    for path in versions_dir.glob("*.py"):
        revision = down = None
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("revision"):
                revision = line.split("=", 1)[1].strip().strip("\"'")
            elif line.startswith("down_revision"):
                down = line.split("=", 1)[1].strip().strip("\"'")
        if revision:
            revisions[revision] = path.name
            if down and down != "None":
                down_refs.add(down)
    heads = sorted(set(revisions) - down_refs)
    return heads[0] if len(heads) == 1 else ",".join(heads)


def _api_schema_hash() -> str:
    from fastapi.openapi.utils import get_openapi

    from jrs.api.main import API_DESCRIPTION, API_TITLE, API_VERSION, app

    schema = get_openapi(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        routes=app.routes,
    )
    canonical = json.dumps(schema, sort_keys=True, separators=(",", ":"))
    return _sha256_bytes(canonical.encode("utf-8"))


def _frontend_hash() -> dict[str, Any]:
    hasher = hashlib.sha256()
    files: list[Path] = []
    frontend = REPO_ROOT / "frontend"
    for seed_dir in FRONTEND_SEED_DIRS:
        base = frontend / seed_dir
        if base.exists():
            files.extend(sorted(p for p in base.rglob("*") if p.is_file()))
    for seed_file in FRONTEND_SEED_FILES:
        path = frontend / seed_file
        if path.exists():
            files.append(path)
    for path in sorted(files):
        rel = path.relative_to(frontend).as_posix()
        hasher.update(rel.encode("utf-8"))
        hasher.update(_sha256_file(path).encode("utf-8"))
    return {
        "source_content_sha256": hasher.hexdigest(),
        "files_hashed": len(files),
        "note": (
            "deterministic source-tree seal; the Next.js build output "
            "embeds non-deterministic ids by design"
        ),
    }


def _golden_states_hash() -> dict[str, Any]:
    golden_dir = REPO_ROOT / "tests" / "fixtures" / "golden_states"
    manifests = sorted(golden_dir.glob("chart_*.json"))
    hasher = hashlib.sha256()
    for path in manifests:
        hasher.update(_sha256_file(path).encode("utf-8"))
    return {
        "manifest_count": len(manifests),
        "aggregate_sha256": hasher.hexdigest(),
    }


def build_seal(release_id: str = DEFAULT_RELEASE_ID) -> dict[str, Any]:
    from jrs.api.schemas import ENGINE_VERSION

    requirements = REPO_ROOT / "requirements.txt"
    bench_seal = REPO_ROOT / "benchmarks" / "JRE-BENCH-001.json"

    return {
        "release_id": release_id,
        "schema_version": RELEASE_SCHEMA_VERSION,
        "status": "SEALED",
        "engine_version": ENGINE_VERSION,
        "git": _git_commit(),
        "environment": {
            "python": platform.python_version(),
            "os": f"{platform.system()} {platform.release()} {platform.machine()}",
            "swisseph": _swisseph(),
        },
        "database": {"schema_version": _alembic_head(), "migrations": "alembic"},
        "api": {"openapi_3_1_sha256": _api_schema_hash()},
        "frontend": _frontend_hash(),
        "artifacts": {
            "golden_states": _golden_states_hash(),
            "benchmark_seal_sha256": (
                _sha256_file(bench_seal) if bench_seal.exists() else ""
            ),
            "requirements_sha256": (
                _sha256_file(requirements) if requirements.exists() else ""
            ),
        },
        "reproducibility_audit": {
            "tool": "scripts/audit_clean_reproduce.py",
            "target": "Stage 1-9 golden hashes + bit-for-bit benchmark 71/31/18 @ 0.7435",
        },
        "sealed_by": "scripts/seal_release.py",
    }


def _seal_path(release_id: str) -> Path:
    return RELEASES_DIR / f"{release_id}.json"


def verify_seal(release_id: str = DEFAULT_RELEASE_ID) -> list[str]:
    failures: list[str] = []
    sealed = json.loads(_seal_path(release_id).read_text(encoding="utf-8"))
    live = build_seal(release_id)

    # Content sections: strict equality (these are pure hashes of
    # artifact content and must match exactly).
    for key in ("environment", "database", "api", "frontend", "artifacts"):
        if sealed.get(key) != live[key]:
            failures.append(f"section drift: {key}")

    # Git section: self-reference rule. Sealing the manifest necessarily
    # creates a commit AFTER the recorded one, so the sealed commit must
    # be HEAD or an ancestor of HEAD — i.e. the released code is contained
    # in the current history — rather than equal to HEAD.
    sealed_commit = (sealed.get("git") or {}).get("commit", "")
    if sealed_commit != live["git"]["commit"]:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", sealed_commit, "HEAD"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        if ancestor.returncode != 0:
            failures.append(
                f"git drift: sealed commit {sealed_commit[:12]} is not HEAD "
                f"nor an ancestor of it"
            )
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seal / verify a release manifest.")
    parser.add_argument("--check", action="store_true", help="verify live == sealed")
    parser.add_argument(
        "--release-id",
        default=DEFAULT_RELEASE_ID,
        help=(
            "Release id to seal/verify (default: v1.0.0). Existing seals "
            "(e.g. v1.0.0-rc1) stay verifiable via their own id."
        ),
    )
    args = parser.parse_args(argv)

    seal_path = _seal_path(args.release_id)

    if args.check:
        failures = verify_seal(args.release_id)
        if failures:
            print("RELEASE SEAL: FAIL", file=sys.stderr)
            for f in failures:
                print(f"  - {f}", file=sys.stderr)
            return 1
        print(f"RELEASE SEAL: PASS ({args.release_id} matches live repository state)")
        return 0

    seal = build_seal(args.release_id)
    if not seal["git"]["worktree_clean"]:
        print(
            "WARNING: worktree is dirty — the seal records HEAD but uncommitted "
            "changes are not covered by it.",
            file=sys.stderr,
        )
    RELEASES_DIR.mkdir(parents=True, exist_ok=True)
    seal_path.write_text(
        json.dumps(seal, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Sealed {args.release_id}: {seal_path}")
    print(f"  git: {seal['git']['commit'][:12]} | alembic: {seal['database']['schema_version']}")
    print(f"  api sha256: {seal['api']['openapi_3_1_sha256'][:16]}…")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
