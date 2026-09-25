"""Phase 9D: Prediction lineage & auditability tracer.

Exposes a direct backward-chain API: any prediction id (``P-xxx``)
maps to its full supporting chain, from the final rule verdict down to
the exact ephemeris raw floats:

    Rule ──► Dasha Gate ──► Transit ──► Varga ──► Yoga ──► SAV ──►
    Natal Longitudes

Each layer records what the pipeline used, whether the supporting
report was present (flag-gated Phase 5B/5C/5D/5E reports), and the
canonical detail payload. Layers whose report was not injected (flag
off) are reported as ``available: false`` with the enabling flag named,
so an audit can distinguish "not used" from "used".

Pure module: no I/O, no wall-clock — the same inputs always produce the
same lineage payload. The Observatory UI and the API route
(``GET /api/v1/lineage/{fixture_id}``) consume this directly, enabling
single-click inspection from an export PDF statement down to the raw
floats.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "LINEAGE_SCHEMA_VERSION",
    "LINEAGE_LAYERS",
    "trace_prediction",
]

LINEAGE_SCHEMA_VERSION = "1.0.0"

#: Ordered chain layers, shallowest (final verdict) to deepest (raw
#: ephemeris floats). Order is part of the contract.
LINEAGE_LAYERS: tuple[str, ...] = (
    "PREDICTION",
    "RULE",
    "DASHA_GATE",
    "TRANSIT",
    "VARGA",
    "YOGA",
    "SAV",
    "NATAL_LONGITUDES",
)

#: Flag-gated report -> enabling environment variable (audit hint when
#: a layer's report was not injected at fact-extraction time).
_REPORT_FLAG_HINTS: dict[str, str] = {
    "ashtakavarga": "JRS_ASHTA_SCORING",
    "gochara": "JRS_GOCHARA_SCORING",
    "multi_varga": "JRS_VARGA_SCORING",
    "dasha_transit": "JRS_DASHA_TRANSIT_SCORING",
}


def _report(facts: dict[str, Any], key: str) -> dict[str, Any] | None:
    value = facts.get(key)
    return value if isinstance(value, dict) else None


def _unavailable(report_key: str) -> dict[str, Any]:
    return {
        "available": False,
        "reason": (
            f"report '{report_key}' not injected at fact-extraction time "
            f"(enable {_REPORT_FLAG_HINTS[report_key]})"
        ),
        "summary": "unavailable",
        "details": {},
    }


def _dasha_gate_layer(facts: dict[str, Any]) -> dict[str, Any]:
    report = _report(facts, "dasha_transit")
    if report is None:
        return _unavailable("dasha_transit")
    window = report.get("dasha_window", {})
    return {
        "available": True,
        "summary": (
            f"{window.get('mahadasha', '?')}/{window.get('antardasha', '?')}/"
            f"{window.get('pratyantardasha', '?')} — "
            f"{report.get('summary', {}).get('authorized', 0)} authorized"
        ),
        "details": {
            "window": {
                "mahadasha": window.get("mahadasha"),
                "antardasha": window.get("antardasha"),
                "pratyantardasha": window.get("pratyantardasha"),
                "start_date": window.get("start_date"),
                "end_date": window.get("end_date"),
                "fact_ids": list(window.get("fact_ids", ())),
            },
            "decisions": {
                body: {
                    "decision": entry.get("decision"),
                    "authorized_by": entry.get("authorized_by"),
                    "relationship": entry.get("relationship"),
                }
                for body, entry in report.get("planets", {}).items()
            },
            "epoch_utc": report.get("epoch_utc"),
        },
    }


def _transit_layer(facts: dict[str, Any]) -> dict[str, Any]:
    report = _report(facts, "gochara")
    if report is None:
        return _unavailable("gochara")
    return {
        "available": True,
        "summary": (
            f"mean TQS {report.get('mean_tqs')} — "
            f"{(report.get('aggregate_band') or {}).get('label', '?')}"
        ),
        "details": {
            "epoch_utc": report.get("epoch_utc"),
            "tqs_basis": report.get("tqs_basis"),
            "aggregate_band": report.get("aggregate_band"),
            "planets": {
                body: {
                    "transit_rashi": entry.get("transit_rashi"),
                    "house_from_moon": entry.get("house_from_moon"),
                    "tqs": entry.get("tqs"),
                    "band": (entry.get("band") or {}).get("label"),
                    "vedha_obstructed": entry.get("vedha_obstructed"),
                    "effective_multiplier": entry.get("effective_multiplier"),
                    "fact_id": entry.get("fact_id"),
                }
                for body, entry in report.get("planets", {}).items()
            },
        },
    }


def _varga_layer(facts: dict[str, Any]) -> dict[str, Any]:
    report = _report(facts, "multi_varga")
    if report is None:
        return _unavailable("multi_varga")
    return {
        "available": True,
        "summary": (
            f"vargottama: "
            f"{sorted(b for b, v in (report.get('vargottama') or {}).items() if v) or 'none'}"
        ),
        "details": {
            "version": report.get("version"),
            "placements": {
                body: {
                    div: (place or {}).get("sign")
                    for div, place in (per_body or {}).items()
                }
                for body, per_body in (report.get("placements") or {}).items()
            },
            "vargottama": report.get("vargottama"),
            "navamsha_dignity": report.get("navamsha_dignity"),
            "d10_dignity": report.get("d10_dignity"),
            "career_anchor": report.get("career_anchor"),
        },
    }


def _yoga_layer(yoga_evals: list[Any]) -> dict[str, Any]:
    evaluations = [
        {
            "yoga_name": getattr(ev, "yoga_name", ""),
            "status": str(getattr(getattr(ev, "status", None), "value", "")),
            "chain_impact": getattr(ev, "chain_impact", None),
            "dynamic_strength": getattr(ev, "dynamic_strength", None),
            "dasha_multiplier": getattr(ev, "dasha_multiplier", None),
            "transit_multiplier": getattr(ev, "transit_multiplier", None),
            "cancellation_reason": getattr(ev, "cancellation_reason", None),
        }
        for ev in yoga_evals
    ]
    formed = sum(1 for e in evaluations if e["status"] == "FORMED")
    return {
        "available": True,
        "summary": f"{len(evaluations)} yogas evaluated, {formed} formed",
        "details": {"evaluations": evaluations},
    }


def _sav_layer(facts: dict[str, Any]) -> dict[str, Any]:
    report = _report(facts, "ashtakavarga")
    if report is None:
        return _unavailable("ashtakavarga")
    return {
        "available": True,
        "summary": f"SAV total {sum(report.get('sav') or [])} "
        f"(Shodhita {sum(report.get('shodhita_sav') or [])})",
        "details": {
            "version": report.get("version"),
            "sav": list(report.get("sav") or []),
            "shodhita_sav": list(report.get("shodhita_sav") or []),
            "pinda": report.get("pinda"),
            "fact_ids": list(report.get("fact_ids") or []),
        },
    }


def _natal_longitudes_layer(facts: dict[str, Any]) -> dict[str, Any]:
    """The deepest layer: exact sidereal longitudes (the ephemeris raw
    floats, canonicalized to the repo-wide round-6 contract)."""
    longitudes = {
        body: round(float(pdata["longitude"]), 6)
        for body, pdata in sorted(facts.get("planets", {}).items())
        if isinstance(pdata.get("longitude"), (int, float))
    }
    return {
        "available": True,
        "summary": f"{len(longitudes)} bodies",
        "details": {
            "longitudes": longitudes,
            "rashi": {
                body: pdata.get("rashi")
                for body, pdata in sorted(facts.get("planets", {}).items())
                if pdata.get("rashi")
            },
            "lagna": facts.get("lagna"),
            "lagna_sign": facts.get("lagna_sign"),
            "moon_nakshatra": facts.get("moon_nakshatra"),
            "moon_nakshatra_degree": (
                round(float(facts["moon_nakshatra_degree"]), 6)
                if isinstance(facts.get("moon_nakshatra_degree"), (int, float))
                else None
            ),
        },
    }


def _rule_layer(graph_dict: dict[str, Any]) -> dict[str, Any]:
    rules = [
        {
            "node_id": node["node_id"],
            "rule_id": (node.get("payload") or {}).get("rule_id"),
            "yoga_name": (node.get("payload") or {}).get("yoga_name"),
            "status": (node.get("payload") or {}).get("status"),
        }
        for node in graph_dict.get("nodes", [])
        if node.get("node_type") == "RULE"
    ]
    return {
        "available": True,
        "summary": f"{len(rules)} classical rules",
        "details": {"rules": rules},
    }


def trace_prediction(
    prediction_id: str,
    jre_facts: dict[str, Any],
    yoga_evals: list[Any],
    graph_dict: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the full backward lineage for one prediction id.

    Args:
        prediction_id: The ``P-...`` id stamped on the evaluation.
        jre_facts: JRE facts as produced by ``build_jre_facts`` (with
            whatever flag-gated reports were injected).
        yoga_evals: Yoga evaluations for the same facts.
        graph_dict: Optional evidence-graph dict (``graph.to_dict()``)
            built with the same prediction id; supplies the RULE layer
            and the deterministic graph id.

    Returns:
        Canonical lineage payload: ordered chain layers
        (PREDICTION → RULE → DASHA_GATE → TRANSIT → VARGA → YOGA → SAV
        → NATAL_LONGITUDES), each with availability, summary, and
        detail payload.
    """
    layers: dict[str, dict[str, Any]] = {
        "PREDICTION": {
            "available": True,
            "summary": prediction_id,
            "details": {
                "prediction_id": prediction_id,
                "graph_id": (graph_dict or {}).get("graph_id"),
            },
        },
        "RULE": (
            _rule_layer(graph_dict)
            if isinstance(graph_dict, dict)
            else {
                "available": False,
                "reason": "evidence graph not supplied",
                "summary": "unavailable",
                "details": {},
            }
        ),
        "DASHA_GATE": _dasha_gate_layer(jre_facts),
        "TRANSIT": _transit_layer(jre_facts),
        "VARGA": _varga_layer(jre_facts),
        "YOGA": _yoga_layer(yoga_evals),
        "SAV": _sav_layer(jre_facts),
        "NATAL_LONGITUDES": _natal_longitudes_layer(jre_facts),
    }

    return {
        "schema_version": LINEAGE_SCHEMA_VERSION,
        "prediction_id": prediction_id,
        "graph_id": (graph_dict or {}).get("graph_id"),
        "chain_order": list(LINEAGE_LAYERS),
        "chain": {layer: layers[layer] for layer in LINEAGE_LAYERS},
    }
