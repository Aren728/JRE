"""Local Swiss Ephemeris data file resolution and integrity (offline, pinned).

Only ``sepl_18.se1`` (planets) and ``semo_18.se1`` (Moon/nodes) are required
for the nine bodies — verified empirically during CODING; the ``se_18.se1``
"main" file is not needed for this scope (see datasets/ephemeris/README.md).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path

from ..errors import EphemerisDataError

#: Files required for SWIEPH mode (must be present; checksums pinned).
REQUIRED_EPHEMERIS_FILES: tuple[str, ...] = ("sepl_18.se1", "semo_18.se1")

#: SHA-256 checksums of the pinned data files (see datasets/ephemeris/README.md).
EXPECTED_CHECKSUMS: dict[str, str] = {
    "sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
    "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7",
}


def required_ephemeris_files() -> tuple[str, ...]:
    return REQUIRED_EPHEMERIS_FILES


def _candidate_paths(config_path: str | None) -> Iterable[Path]:
    if config_path:
        yield Path(config_path)
    yield Path("datasets/ephemeris")
    # Fall back to a repo-relative lookup from this file's location.
    here = Path(__file__).resolve()
    for _ in range(4):
        here = here.parent
        yield here / "datasets" / "ephemeris"


def resolve_ephemeris_path(config_path: str | None) -> Path | None:
    """Return the first existing directory containing the required files."""
    for candidate in _candidate_paths(config_path):
        if candidate.is_dir() and all(
            (candidate / name).is_file() for name in REQUIRED_EPHEMERIS_FILES
        ):
            return candidate
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_ephemeris_dir(path: Path, verify_checksums: bool = True) -> tuple[str, ...]:
    """Verify presence (and optionally checksums) of the required files.

    Returns the verified file names. Raises ``EphemerisDataError`` on any
    missing file or checksum mismatch.
    """
    missing = [name for name in REQUIRED_EPHEMERIS_FILES if not (path / name).is_file()]
    if missing:
        raise EphemerisDataError(
            f"ephemeris data files missing in {path}: {', '.join(missing)}"
        )
    if verify_checksums:
        mismatched = [
            name
            for name in REQUIRED_EPHEMERIS_FILES
            if _sha256(path / name) != EXPECTED_CHECKSUMS[name]
        ]
        if mismatched:
            raise EphemerisDataError(
                f"ephemeris data checksum mismatch in {path}: {', '.join(mismatched)}"
            )
    return REQUIRED_EPHEMERIS_FILES
