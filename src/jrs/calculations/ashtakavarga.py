"""JRS Phase 5B: Ashtakavarga Calculation Module.

Classical eight-fold bindu computation over 12 rashis, delegated from the
frozen benchmark's JRE facts (``planets`` + ``lagna``) into a
deterministic, machine-readable report:

- **Bhinna Ashtakavarga (BAV)** — per-sign point totals (0–8 Rekhas) for
  each of the 8 anchors: Sun through Saturn, plus the Lagna. Bindus are
  counted from the 8×8 classical benefic-places matrix (BPHS Ch 66,
  verses 43–68), where each contributing body gives at most one bindu per
  sign to each anchor.
- **Sarvashtakavarga (SAV)** — the column-wise sum of the seven planetary
  BAVs (0–56 Rekhas; total always 337). The Lagna BAV is computed and
  reported but excluded from the SAV, per BPHS.
- **Shodhana reductions** —
  * Trikona Shodhana: in each of the four trine rows (Mesha/Simha/
    Dhanusha, Vrishabha/Kanya/Makara, Mithuna/Tula/Kumbha, Karka/
    Vrishchika/Meena) all three signs are reduced to the row minimum.
  * Ekadhipatya Shodhana: for each same-lord sign pair (Mesha+Vrishchika
    = Mars, Vrishabha+Tula = Venus, Mithuna+Kanya = Mercury,
    Dhanusha+Meena = Jupiter, Makara+Kumbha = Saturn), when both signs
    are occupied, the higher bindu count is reduced to the lower; if
    equal, both are zeroed. When ``occupied_signs`` is omitted the
    unconditional variant applies (every pair treated as occupied).
- **Shodhita Pinda** — per anchor, computed from the anchor's reduced
  (Shodhita) BAV row: Rashi Pinda = Σ (bindus × Rashi multiplier);
  Graha Pinda = Σ over the seven planets of (bindus in the sign
  occupied by that planet × Graha multiplier); Shodhya Pinda = their sum.

Every emitted record carries ``FACT-ASHTA-*`` provenance ids so results
are traceable in the evidence graph (Phase 3) and hashable in the
golden-state contract (Phase 5B: 6th stage).

Determinism contract
--------------------
No I/O, no wall-clock, no randomness, and no unordered iteration: given
identical input facts, every function returns byte-identical output.
Total Rekha sums are asserted at import time so a corrupted classical
table fails loudly rather than silently skewing scores.

Feature flag
------------
``ashta_scoring_enabled()`` (default **False**, env override
``JRS_ASHTA_SCORING=1``) gates injection of the report into ``jre_facts``
for downstream scoring, so enabling this module cannot silently move the
frozen benchmark baseline (Micro-F1 = 0.7435).
"""

from __future__ import annotations

import os
from typing import Any

__all__ = [
    "ASHTAKAVARGA_STAGE_VERSION",
    "ANCHORS",
    "BINDU_MATRIX",
    "BENEFIC_TOTALS",
    "SIGN_MULTIPLIERS",
    "GRAHA_MULTIPLIERS",
    "RASHI_ORDER",
    "TRIKONA_GROUPS",
    "EKADHIPATYA_PAIRS",
    "PLANETARY_ANCHORS",
    "ashta_scoring_enabled",
    "compute_bav",
    "compute_sav",
    "trikona_shodhana",
    "ekadhipatya_shodhana",
    "compute_pinda",
    "compute_full_ashtakavarga",
    "ashtakavarga_to_dict",
]

#: Version of this calculation module (bump on semantic change; golden
#: fixtures regenerate with it).
ASHTAKAVARGA_STAGE_VERSION = "1.0.0"

RASHI_ORDER: tuple[str, ...] = (
    "MESHA",
    "VRISHABHA",
    "MITHUNA",
    "KARKA",
    "SIMHA",
    "KANYA",
    "TULA",
    "VRISHCHIKA",
    "DHANUSHA",
    "MAKARA",
    "KUMBHA",
    "MEENA",
)

#: The eight Ashtakavarga anchors: seven planets + Lagna (BPHS Ch 66).
ANCHORS: tuple[str, ...] = (
    "SUN",
    "MOON",
    "MARS",
    "MERCURY",
    "JUPITER",
    "VENUS",
    "SATURN",
    "LAGNA",
)

#: The seven planetary anchors contributing to the SAV (Lagna excluded).
PLANETARY_ANCHORS: tuple[str, ...] = ANCHORS[:7]

# ── Classical benefic-places matrix (BPHS Ch 66, v. 43–68) ──────────────────
# BINDU_MATRIX[anchor][body] = tuple of houses (1–12, counted from the
# anchor's own sign) that receive one bindu from that body.
#: BPHS 66.43–45 — Surya Ashtakavarga (total 48).
_SUN_ROWS: dict[str, tuple[int, ...]] = {
    "SUN": (1, 2, 4, 7, 8, 9, 10, 11),
    "MOON": (3, 6, 10, 11),
    "MARS": (1, 2, 4, 7, 8, 9, 10, 11),
    "MERCURY": (3, 5, 6, 9, 10, 11, 12),
    "JUPITER": (5, 6, 9, 11),
    "VENUS": (6, 7, 12),
    "SATURN": (1, 2, 4, 7, 8, 9, 10, 11),
    "LAGNA": (3, 4, 6, 10, 11, 12),
}
#: BPHS 66.46–48 — Chandra Ashtakavarga (total 49).
_MOON_ROWS: dict[str, tuple[int, ...]] = {
    "SUN": (3, 6, 7, 8, 10, 11),
    "MOON": (1, 3, 6, 7, 9, 10, 11),
    "MARS": (2, 3, 5, 6, 10, 11),
    "MERCURY": (1, 3, 4, 5, 7, 8, 10, 11),
    "JUPITER": (1, 2, 4, 7, 8, 10, 11),
    "VENUS": (3, 4, 5, 7, 9, 10, 11),
    "SATURN": (3, 5, 6, 11),
    "LAGNA": (3, 6, 10, 11),
}
#: BPHS 66.49–50 — Mangal Ashtakavarga (total 39).
_MARS_ROWS: dict[str, tuple[int, ...]] = {
    "SUN": (3, 5, 6, 10, 11),
    "MOON": (3, 6, 11),
    "MARS": (1, 2, 4, 7, 8, 10, 11),
    "MERCURY": (3, 5, 6, 11),
    "JUPITER": (6, 10, 11, 12),
    "VENUS": (6, 8, 11, 12),
    "SATURN": (1, 4, 7, 8, 9, 10, 11),
    "LAGNA": (1, 3, 6, 10, 11),
}
#: BPHS 66.51–52 — Budha Ashtakavarga (total 54).
_MERCURY_ROWS: dict[str, tuple[int, ...]] = {
    "SUN": (5, 6, 9, 11, 12),
    "MOON": (2, 4, 6, 8, 10, 11),
    "MARS": (1, 2, 4, 7, 8, 9, 10, 11),
    "MERCURY": (1, 3, 5, 6, 9, 10, 11, 12),
    "JUPITER": (6, 8, 11, 12),
    "VENUS": (1, 2, 3, 4, 5, 8, 9, 11),
    "SATURN": (1, 2, 4, 7, 8, 9, 10, 11),
    "LAGNA": (1, 2, 4, 6, 8, 10, 11),
}
#: BPHS 66.53–55 — Guru Ashtakavarga (total 56).
_JUPITER_ROWS: dict[str, tuple[int, ...]] = {
    "SUN": (1, 2, 3, 4, 7, 8, 9, 10, 11),
    "MOON": (2, 5, 7, 9, 11),
    "MARS": (1, 2, 4, 7, 8, 10, 11),
    "MERCURY": (1, 2, 4, 5, 6, 9, 10, 11),
    "JUPITER": (1, 2, 3, 4, 7, 8, 10, 11),
    "VENUS": (2, 5, 6, 9, 10, 11),
    "SATURN": (3, 5, 6, 12),
    "LAGNA": (1, 2, 4, 5, 6, 7, 9, 10, 11),
}
#: BPHS 66.56–58 — Shukra Ashtakavarga (total 52).
_VENUS_ROWS: dict[str, tuple[int, ...]] = {
    "SUN": (8, 11, 12),
    "MOON": (1, 2, 3, 4, 5, 8, 9, 11, 12),
    "MARS": (3, 4, 6, 9, 11, 12),
    "MERCURY": (3, 5, 6, 9, 11),
    "JUPITER": (5, 8, 9, 10, 11),
    "VENUS": (1, 2, 3, 4, 5, 8, 9, 10, 11),
    "SATURN": (3, 4, 5, 8, 9, 10, 11),
    "LAGNA": (1, 2, 3, 4, 5, 8, 9, 11),
}
#: BPHS 66.59–60 — Shani Ashtakavarga (total 39).
_SATURN_ROWS: dict[str, tuple[int, ...]] = {
    "SUN": (1, 2, 4, 7, 8, 10, 11),
    "MOON": (3, 6, 11),
    "MARS": (3, 5, 6, 10, 11, 12),
    "MERCURY": (6, 8, 9, 10, 11, 12),
    "JUPITER": (5, 6, 11, 12),
    "VENUS": (6, 11, 12),
    "SATURN": (3, 5, 6, 11),
    "LAGNA": (1, 3, 4, 6, 10, 11),
}
#: BPHS 66.65–68 — Lagna Ashtakavarga (reported, excluded from SAV).
_LAGNA_ROWS: dict[str, tuple[int, ...]] = {
    "SUN": (3, 4, 6, 10, 11, 12),
    "MOON": (3, 6, 10, 11, 12),
    "MARS": (1, 3, 6, 10, 11),
    "MERCURY": (1, 2, 4, 6, 8, 10, 11),
    "JUPITER": (1, 2, 4, 5, 6, 7, 9, 10, 11),
    "VENUS": (1, 2, 3, 4, 5, 8, 9, 11),
    "SATURN": (1, 3, 4, 6, 10, 11),
    "LAGNA": (3, 6, 10, 11),
}

#: BINDU_MATRIX[anchor][body] -> benefic houses (1-indexed, from anchor).
BINDU_MATRIX: dict[str, dict[str, tuple[int, ...]]] = {
    "SUN": _SUN_ROWS,
    "MOON": _MOON_ROWS,
    "MARS": _MARS_ROWS,
    "MERCURY": _MERCURY_ROWS,
    "JUPITER": _JUPITER_ROWS,
    "VENUS": _VENUS_ROWS,
    "SATURN": _SATURN_ROWS,
    "LAGNA": _LAGNA_ROWS,
}

#: Canonical per-anchor Rekha totals — import-time self-validation of the
#: classical matrix (Sun 48, Moon 49, Mars 39, Mercury 54, Jupiter 56,
#: Venus 52, Saturn 39; planetary SAV = 337).
BENEFIC_TOTALS: dict[str, int] = {
    "SUN": 48,
    "MOON": 49,
    "MARS": 39,
    "MERCURY": 54,
    "JUPITER": 56,
    "VENUS": 52,
    "SATURN": 39,
}

for _anchor in ANCHORS:
    _row_total = sum(len(houses) for houses in BINDU_MATRIX[_anchor].values())
    if _anchor in BENEFIC_TOTALS and _row_total != BENEFIC_TOTALS[_anchor]:
        raise RuntimeError(
            f"corrupt Ashtakavarga table: {_anchor} rows sum to {_row_total}, "
            f"expected {BENEFIC_TOTALS[_anchor]} (BPHS Ch 66)"
        )
if sum(BENEFIC_TOTALS.values()) != 337:
    raise RuntimeError(
        "corrupt Ashtakavarga table: planetary totals must sum to 337 "
        f"(got {sum(BENEFIC_TOTALS.values())})"
    )
del _anchor, _row_total

# ── Reduction constants ─────────────────────────────────────────────────────
#: Trikona (triplicity) rows: each starts at a fiery/earthy/airy/watery
#: sign and takes every 4th sign (1-5-9 pattern).
TRIKONA_GROUPS: tuple[tuple[str, str, str], ...] = tuple(
    (RASHI_ORDER[i], RASHI_ORDER[(i + 4) % 12], RASHI_ORDER[(i + 8) % 12])
    for i in range(4)
)

#: Same-lordship (Ekadhipatya) sign pairs — signs ruled by one planet:
#: Mars (Mesha+Vrishchika), Venus (Vrishabha+Tula), Mercury (Mithuna+Kanya),
#: Jupiter (Dhanusha+Meena), Saturn (Makara+Kumbha). Sun (Simha) and Moon
#: (Karka) are single-lorded and never pair.
EKADHIPATYA_PAIRS: tuple[tuple[str, str], ...] = (
    ("MESHA", "VRISHCHIKA"),  # Mars
    ("VRISHABHA", "TULA"),  # Venus
    ("MITHUNA", "KANYA"),  # Mercury
    ("DHANUSHA", "MEENA"),  # Jupiter
    ("MAKARA", "KUMBHA"),  # Saturn
)

#: Rashi (sign) multipliers for the Pinda computation, Mesha = 1 … Meena = 12.
SIGN_MULTIPLIERS: tuple[int, ...] = tuple(range(1, 13))

#: Graha (planet) multipliers for the Pinda computation (BPHS Ch 66).
GRAHA_MULTIPLIERS: dict[str, int] = {
    "SUN": 1,
    "MOON": 2,
    "MARS": 3,
    "MERCURY": 4,
    "JUPITER": 5,
    "VENUS": 6,
    "SATURN": 7,
}


# ── Feature flag ────────────────────────────────────────────────────────────
def ashta_scoring_enabled() -> bool:
    """Whether Ashtakavarga scoring is injected into ``jre_facts``.

    Default **False**: the frozen benchmark baseline (Micro-F1 = 0.7435)
    is unaffected. Set ``JRS_ASHTA_SCORING=1`` (truthy) to enable.
    """
    return os.environ.get("JRS_ASHTA_SCORING", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


# ── Computation ─────────────────────────────────────────────────────────────
def _sign_index(sign: str) -> int:
    return RASHI_ORDER.index(sign)


def _resolve_planet_signs(facts: dict[str, Any]) -> dict[str, str]:
    """Extract anchor signs from JRE facts.

    Returns a dict with all 8 anchors: the seven planets from
    ``facts["planets"][name]["rashi"]`` and ``"LAGNA"`` from
    ``facts["lagna"]``.

    Raises:
        ValueError: If any anchor's rashi is missing or unknown.
    """
    planets = facts.get("planets", {})
    resolved: dict[str, str] = {}
    for anchor in ANCHORS:
        if anchor == "LAGNA":
            sign = str(facts.get("lagna", ""))
        else:
            pdata = planets.get(anchor)
            if not isinstance(pdata, dict):
                raise ValueError(f"Ashtakavarga input missing planet facts: {anchor}")
            sign = str(pdata.get("rashi", ""))
        if sign not in RASHI_ORDER:
            raise ValueError(f"Ashtakavarga input has unknown rashi for {anchor}: {sign!r}")
        resolved[anchor] = sign
    return resolved


def compute_bav(anchor_signs: dict[str, str]) -> dict[str, tuple[int, ...]]:
    """Compute Bhinna Ashtakavarga for all 8 anchors.

    Args:
        anchor_signs: Mapping of all 8 anchor names to their rashi.

    Returns:
        Mapping anchor -> 12-length tuple of per-sign bindu counts
        (0–8 Rekhas each; row totals match ``BENEFIC_TOTALS``).
    """
    bav: dict[str, tuple[int, ...]] = {}
    for anchor in ANCHORS:
        anchor_idx = _sign_index(anchor_signs[anchor])
        per_sign = [0] * 12
        for body in ANCHORS:
            for house in BINDU_MATRIX[anchor][body]:
                # Houses are counted from the anchor's own sign.
                target_idx = (anchor_idx + house - 1) % 12
                per_sign[target_idx] += 1
        bav[anchor] = tuple(per_sign)
    return bav


def compute_sav(bav: dict[str, tuple[int, ...]]) -> tuple[int, ...]:
    """Compute Sarvashtakavarga: column-wise sum of the seven planetary
    BAVs (Lagna excluded, per BPHS). Each sign totals 0–56 Rekhas and the
    grand total is always 337."""
    totals = [0] * 12
    for anchor in PLANETARY_ANCHORS:
        for idx, bindus in enumerate(bav[anchor]):
            totals[idx] += bindus
    return tuple(totals)


def trikona_shodhana(row: tuple[int, ...]) -> tuple[int, ...]:
    """Trikona (triplicity) Shodhana over one 12-sign bindu row.

    In each trine row (Mesha/Simha/Dhanusha, Vrishabha/Kanya/Makara,
    Mithuna/Tula/Kumbha, Karka/Vrishchika/Meena) ALL THREE signs are
    reduced to the row's minimum bindu count (BPHS Ch 66: the least among
    them prevails across the trine).
    """
    reduced = list(row)
    for group in TRIKONA_GROUPS:
        idxs = [_sign_index(sign) for sign in group]
        row_min = min(row[i] for i in idxs)
        for i in idxs:
            reduced[i] = row_min
    return tuple(reduced)


def ekadhipatya_shodhana(
    row: tuple[int, ...],
    occupied_signs: frozenset[str] | None = None,
) -> tuple[int, ...]:
    """Ekadhipatya (single-lordship) Shodhana over one 12-sign bindu row.

    For each same-lord pair (see ``EKADHIPATYA_PAIRS``):
    - both signs occupied (or ``occupied_signs is None`` for the
      unconditional variant) and counts differ -> the higher is reduced
      to the lower;
    - both occupied and counts equal -> both reduced to zero;
    - otherwise -> unchanged.
    """
    reduced = list(row)
    for sign_a, sign_b in EKADHIPATYA_PAIRS:
        ia, ib = _sign_index(sign_a), _sign_index(sign_b)
        if occupied_signs is not None and not (
            sign_a in occupied_signs and sign_b in occupied_signs
        ):
            continue
        va, vb = reduced[ia], reduced[ib]
        if va == vb:
            reduced[ia] = 0
            reduced[ib] = 0
        else:
            higher, lower = (ia, ib) if va > vb else (ib, ia)
            reduced[higher] = reduced[lower]
    return tuple(reduced)


def compute_pinda(
    shodhita_bav: dict[str, tuple[int, ...]],
    planet_signs: dict[str, str],
) -> dict[str, dict[str, int]]:
    """Compute Shodhita Pinda per anchor from the reduced BAV rows.

    Rashi Pinda: Σ (shodhita bindus × Rashi multiplier) over the row.
    Graha Pinda: Σ over the seven planets of (shodhita bindus in the sign
    occupied by that planet × Graha multiplier) — position-dependent.
    Shodhya Pinda: Rashi + Graha.
    """
    pinda: dict[str, dict[str, int]] = {}
    for anchor in ANCHORS:
        row = shodhita_bav[anchor]
        rashi_pinda = sum(
            bindus * SIGN_MULTIPLIERS[idx] for idx, bindus in enumerate(row)
        )
        graha_pinda = 0
        for planet in PLANETARY_ANCHORS:
            occupied_idx = _sign_index(planet_signs[planet])
            graha_pinda += row[occupied_idx] * GRAHA_MULTIPLIERS[planet]
        pinda[anchor] = {
            "rashi_pinda": rashi_pinda,
            "graha_pinda": graha_pinda,
            "shodhya_pinda": rashi_pinda + graha_pinda,
        }
    return pinda


def compute_full_ashtakavarga(facts: dict[str, Any]) -> dict[str, Any]:
    """Full deterministic pipeline: BAV -> SAV -> Shodhana -> Pinda.

    Reductions are applied to each anchor's BAV row (Trikona first, then
    Ekadhipatya with occupancy from the seven planets' signs); the
    Shodhita SAV is the column sum of the seven reduced planetary rows.

    Args:
        facts: JRE facts with ``planets`` (each entry needs ``rashi``)
            and ``lagna`` (rashi name string).

    Returns:
        Report dict with bav, sav, shodhita_bav, shodhita_sav, pinda,
        anchor_signs, and per-record ``FACT-ASHTA-*`` provenance ids.
    """
    anchor_signs = _resolve_planet_signs(facts)
    bav = compute_bav(anchor_signs)
    sav = compute_sav(bav)

    occupied = frozenset(
        anchor_signs[planet] for planet in PLANETARY_ANCHORS
    )
    shodhita_bav: dict[str, tuple[int, ...]] = {}
    for anchor in ANCHORS:
        after_trikona = trikona_shodhana(bav[anchor])
        shodhita_bav[anchor] = ekadhipatya_shodhana(after_trikona, occupied)
    shodhita_sav = compute_sav(shodhita_bav)

    pinda = compute_pinda(shodhita_bav, anchor_signs)

    fact_ids: list[str] = [f"FACT-ASHTA-BAV-{anchor}" for anchor in ANCHORS]
    fact_ids.append("FACT-ASHTA-SAV")
    fact_ids.extend(f"FACT-ASHTA-PINDA-{anchor}" for anchor in ANCHORS)

    return {
        "version": ASHTAKAVARGA_STAGE_VERSION,
        "anchor_signs": {anchor: anchor_signs[anchor] for anchor in ANCHORS},
        "fact_ids": tuple(fact_ids),
        "bav": bav,
        "sav": sav,
        "shodhita_bav": shodhita_bav,
        "shodhita_sav": shodhita_sav,
        "pinda": pinda,
    }


def ashtakavarga_to_dict(report: dict[str, Any]) -> dict[str, Any]:
    """Serialize the report with JSON-safe types (tuples -> lists) and a
    canonical field order for hashing."""
    return {
        "version": report["version"],
        "anchor_signs": {k: report["anchor_signs"][k] for k in ANCHORS},
        "fact_ids": list(report["fact_ids"]),
        "bav": {k: list(report["bav"][k]) for k in ANCHORS},
        "sav": list(report["sav"]),
        "shodhita_bav": {k: list(report["shodhita_bav"][k]) for k in ANCHORS},
        "shodhita_sav": list(report["shodhita_sav"]),
        "pinda": {k: dict(report["pinda"][k]) for k in ANCHORS},
    }
