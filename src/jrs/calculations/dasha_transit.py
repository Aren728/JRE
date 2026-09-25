"""Phase 5E: Dasha/Transit Permissive Activation engine.

Structural hierarchy (BPHS, dasha/gochara chapter):

    [ DASHA STATE ]  --authorizes--> timing window
                           │
                           ▼
                   [ PERMISSIVE GATE ]
                           ▲
    [ TRANSIT STATE ]  --materializes--> activation

A transit can never trigger an event prediction on its own: the active
Vimshottari Mahadasha/Antardasha/Pratyantardasha window must authorize
the planet first. This module evaluates that gate deterministically and
emits machine-readable gate facts plus the provenance relationship ids
``REL-DASHA-TRANSIT-AUTHORIZES`` / ``REL-DASHA-TRANSIT-BLOCKS``.

Authority semantics (classical, deliberately band-independent):

- A planet is **authoritative** for the window when it is the active
  Mahadasha lord (strongest), Antardasha lord, or Pratyantardasha lord.
- Transit *quality* (TQS band, vedha) modulates the authorized
  activation — it is gochara's job (Phase 5C) — but never substitutes
  for dasha authority. A planet whose transit band is AFFLICTED is
  still AUTHORIZED if its dasha lord rules the window; a planet with a
  SUPPORTIVE transit whose lords do not rule the window is BLOCKED.
- The active window is anchored to the same pure canonical engine the
  golden ``dasha`` stage uses (:func:`jrs.engine.dasha.calculate_vimshottari_dasha`)
  — never wall-clock: the evaluated instant is pinned to
  ``DASHA_TRANSIT_EPOCH`` (identical to ``GOCHARA_TRANSIT_EPOCH``), so
  identical inputs yield byte-identical reports.

Feature flag: ``dasha_transit_scoring_enabled()`` (default **False**,
env override ``JRS_DASHA_TRANSIT_SCORING``) gates injection of the gate
report into ``build_jre_facts`` so the frozen benchmark baseline
(Micro-F1 = 0.7435) cannot silently regress. The golden-state
``dasha_transit`` stage records the pure calculation report regardless
of the flag (same discipline as the ashtakavarga/gochara/multi_varga
stages).
"""

from __future__ import annotations

import datetime as dt
import os
from typing import Any

from jrs.engine.dasha import calculate_vimshottari_dasha
from jrs.engine.dasha import (
    NAKSHATRA_SPAN_DEG as _NAKSHATRA_SPAN_DEG,  # noqa: F401  (re-export symmetry)
)

__all__ = [
    "DASHA_TRANSIT_STAGE_VERSION",
    "DASHA_TRANSIT_EPOCH",
    "MIN_AD_WINDOW_DAYS",
    "MIN_PD_WINDOW_DAYS",
    "REL_DASHA_TRANSIT_AUTHORIZES",
    "REL_DASHA_TRANSIT_BLOCKS",
    "GOCHARA_PLANETS",
    "dasha_transit_scoring_enabled",
    "compute_dasha_transit",
    "dasha_transit_to_dict",
]

#: Version of the dasha_transit stage payload (bump on rule changes).
DASHA_TRANSIT_STAGE_VERSION = "1.0.0"

#: Pinned evaluation instant — never wall-clock (golden-state contract).
DASHA_TRANSIT_EPOCH = dt.datetime(2020, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc)

#: Minimum believable window lengths (guard against degenerate boundaries
#: at cycle edges). Windows shorter than these are still reported but
#: flagged via ``window_degenerate`` in the payload.
MIN_AD_WINDOW_DAYS = 3.0
MIN_PD_WINDOW_DAYS = 1.0

REL_DASHA_TRANSIT_AUTHORIZES = "REL-DASHA-TRANSIT-AUTHORIZES"
REL_DASHA_TRANSIT_BLOCKS = "REL-DASHA-TRANSIT-BLOCKS"

#: Bodies evaluated through the gate — the classical gochara planets,
#: matching the Phase 5C transit state exactly.
GOCHARA_PLANETS: tuple[str, ...] = (
    "SUN",
    "MOON",
    "MARS",
    "MERCURY",
    "JUPITER",
    "VENUS",
    "SATURN",
)

_ENV_VAR = "JRS_DASHA_TRANSIT_SCORING"
_TRUTHY = ("1", "true", "yes", "on")

_RASHI_ORDER: tuple[str, ...] = (
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


def dasha_transit_scoring_enabled() -> bool:
    """Feature-flag predicate (default False; env ``JRS_DASHA_TRANSIT_SCORING``).

    Follows the repo-wide convention: the frozen benchmark baseline is
    unaffected unless the operator explicitly enables the flag. Set
    ``JRS_DASHA_TRANSIT_SCORING=1`` (truthy) to enable.
    """
    return os.environ.get(_ENV_VAR, "").strip().lower() in _TRUTHY


def _whole_sign_house(planet_sign: str, anchor_sign: str) -> int:
    """Whole-sign house of ``planet_sign`` counted from ``anchor_sign``."""
    return (_RASHI_ORDER.index(planet_sign) - _RASHI_ORDER.index(anchor_sign)) % 12 + 1


def _transit_state(facts: dict[str, Any], body: str) -> dict[str, Any]:
    """Read the transit state for ``body`` from the Phase 5C report when
    present, otherwise fall back to a minimal whole-sign computation
    from the natal Moon sign with a NEUTRAL band (no TQS basis).
    """
    gochara_planets = facts.get("gochara", {}).get("planets", {})
    if isinstance(gochara_planets, dict) and body in gochara_planets:
        greport = gochara_planets[body]
        return {
            "basis": "gochara_report",
            "transit_rashi": greport.get("transit_rashi"),
            "house_from_moon": greport.get("house_from_moon"),
            "tqs": greport.get("tqs"),
            "band": (greport.get("band") or {}).get("label"),
            "vedha_obstructed": greport.get("vedha_obstructed"),
        }

    planets = facts.get("planets", {})
    natal_moon_sign = planets.get("MOON", {}).get("rashi")
    if body == "MOON":
        # The natal Moon is the gochara anchor itself — it has no transit
        # of its own. Report the natal anchor state (never raises).
        return {
            "basis": "natal_anchor",
            "transit_rashi": natal_moon_sign,
            "house_from_moon": 1,
            "tqs": None,
            "band": "NEUTRAL",
            "vedha_obstructed": False,
        }
    body_sign = planets.get(body, {}).get("rashi")
    if not body_sign:
        raise ValueError(f"facts missing rashi for body: {body}")
    return {
        "basis": "whole_sign_fallback",
        "transit_rashi": body_sign,
        "house_from_moon": (
            _whole_sign_house(body_sign, natal_moon_sign)
            if natal_moon_sign
            else None
        ),
        "tqs": None,
        "band": "NEUTRAL",
        "vedha_obstructed": False,
    }


def compute_dasha_transit(
    facts: dict[str, Any],
    birth_date: str,
    epoch: dt.datetime | None = None,
) -> dict[str, Any]:
    """Evaluate the permissive dasha/transit gate for one natal chart.

    Args:
        facts: Natal JRE facts (planets rashi/longitude; Phase 5C
            ``gochara`` report when the 5C flag is on).
        birth_date: Birth date string ``YYYY-MM-DD`` anchoring the
            Vimshottari cycle (the canonical engine's epoch reference).
        epoch: Evaluated instant (defaults to the pinned
            ``DASHA_TRANSIT_EPOCH``).

    Returns:
        Report dict with the active MD/AD/PD window, per-planet gate
        decisions, and ``FACT-DASHA-*`` provenance ids.
    """
    instant = epoch or DASHA_TRANSIT_EPOCH

    moon_longitude = facts.get("planets", {}).get("MOON", {}).get("longitude")
    if moon_longitude is None:
        raise ValueError("facts missing MOON longitude (required for Vimshottari)")

    # Active window from the canonical pure engine (pinned target date —
    # never wall-clock).
    window = calculate_vimshottari_dasha(
        moon_longitude=float(moon_longitude),
        birth_date_str=birth_date,
        target_date=instant.replace(tzinfo=None),
    )
    # The canonical engine returns title-case lords ("Venus"); normalize
    # to the uppercase body convention used across facts and gochara.
    mahadasha = str(window["mahadasha"]).strip().upper()
    antardasha = str(window["antardasha"]).strip().upper()
    pratyantardasha = str(window["pratyantardasha"]).strip().upper()

    window_start = dt.datetime.strptime(str(window["start_date"]), "%Y-%m-%d")
    window_end = dt.datetime.strptime(str(window["end_date"]), "%Y-%m-%d")
    window_days = (window_end - window_start).total_seconds() / 86400.0

    window_fact_ids = (
        f"FACT-DASHA-MD-{mahadasha}",
        f"FACT-DASHA-AD-{antardasha}",
        f"FACT-DASHA-PD-{pratyantardasha}",
    )
    authority: dict[str, str] = {
        mahadasha: "MD",
        antardasha: "AD",
        pratyantardasha: "PD",
    }

    planets_report: dict[str, dict[str, Any]] = {}
    gate_fact_ids: list[str] = []
    authorized_count = 0
    for body in GOCHARA_PLANETS:
        authorized_by = authority.get(body)
        decision = "AUTHORIZED" if authorized_by else "BLOCKED"
        if authorized_by:
            authorized_count += 1
        relationship = (
            REL_DASHA_TRANSIT_AUTHORIZES
            if authorized_by
            else REL_DASHA_TRANSIT_BLOCKS
        )
        fact_id = f"FACT-DASHA-TRANSIT-GATE-{body}"
        gate_fact_ids.append(fact_id)
        planets_report[body] = {
            "fact_id": fact_id,
            "dasha_authoritative": bool(authorized_by),
            "authorized_by": authorized_by,
            "decision": decision,
            "relationship": relationship,
            "transit_state": _transit_state(facts, body),
        }

    return {
        "version": DASHA_TRANSIT_STAGE_VERSION,
        "epoch_utc": instant.strftime("%Y-%m-%dT%H:%M:%S+0000"),
        "birth_date": birth_date,
        "gate_policy": {
            "authority": "dasha_window_only",
            "note": (
                "Transit quality modulates authorized activations (Phase 5C); "
                "it never substitutes for dasha authority."
            ),
            "min_ad_window_days": MIN_AD_WINDOW_DAYS,
            "min_pd_window_days": MIN_PD_WINDOW_DAYS,
        },
        "dasha_window": {
            "mahadasha": mahadasha,
            "antardasha": antardasha,
            "pratyantardasha": pratyantardasha,
            "start_date": str(window["start_date"]),
            "end_date": str(window["end_date"]),
            "duration_days": round(window_days, 6),
            "window_degenerate": window_days < MIN_PD_WINDOW_DAYS,
            "fact_ids": window_fact_ids,
        },
        "planets": planets_report,
        "summary": {
            "authorized": authorized_count,
            "blocked": len(GOCHARA_PLANETS) - authorized_count,
        },
        "fact_ids": tuple(window_fact_ids) + tuple(gate_fact_ids),
    }


def dasha_transit_to_dict(report: dict[str, Any]) -> dict[str, Any]:
    """Serialize the report with JSON-safe types and canonical order."""
    return {
        "version": report["version"],
        "epoch_utc": report["epoch_utc"],
        "birth_date": report["birth_date"],
        "gate_policy": dict(report["gate_policy"]),
        "dasha_window": {
            "mahadasha": report["dasha_window"]["mahadasha"],
            "antardasha": report["dasha_window"]["antardasha"],
            "pratyantardasha": report["dasha_window"]["pratyantardasha"],
            "start_date": report["dasha_window"]["start_date"],
            "end_date": report["dasha_window"]["end_date"],
            "duration_days": report["dasha_window"]["duration_days"],
            "window_degenerate": report["dasha_window"]["window_degenerate"],
            "fact_ids": list(report["dasha_window"]["fact_ids"]),
        },
        "planets": {
            body: {
                "fact_id": report["planets"][body]["fact_id"],
                "dasha_authoritative": report["planets"][body]["dasha_authoritative"],
                "authorized_by": report["planets"][body]["authorized_by"],
                "decision": report["planets"][body]["decision"],
                "relationship": report["planets"][body]["relationship"],
                "transit_state": dict(report["planets"][body]["transit_state"]),
            }
            for body in GOCHARA_PLANETS
        },
        "summary": dict(report["summary"]),
        "fact_ids": list(report["fact_ids"]),
    }
