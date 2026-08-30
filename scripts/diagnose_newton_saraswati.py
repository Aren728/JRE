#!/usr/bin/env python3
"""Phase E6j Part A: Newton Saraswati Trace.

Traces Saraswati Yoga through every pipeline layer for Newton's chart
to identify the exact cancellation root cause.

Usage::

    python scripts/diagnose_newton_saraswati.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

FIXTURES_DIR = _PROJECT_ROOT / "tests" / "fixtures" / "validation_charts"
REPORT_DIR = _PROJECT_ROOT / "reports"

_RASHI_ORDER = [
    "MESHA", "VRISHABHA", "MITHUNA", "KARKA", "SIMHA", "KANYA",
    "TULA", "VRISHCHIKA", "DHANUSHA", "MAKARA", "KUMBHA", "MEENA",
]

_SIGN_LORDS = {
    "MESHA": "MARS", "VRISHABHA": "VENUS", "MITHUNA": "MERCURY",
    "KARKA": "MOON", "SIMHA": "SUN", "KANYA": "MERCURY",
    "TULA": "VENUS", "VRISHCHIKA": "MARS", "DHANUSHA": "JUPITER",
    "MAKARA": "SATURN", "KUMBHA": "SATURN", "MEENA": "JUPITER",
}

_KENDRA_HOUSES = {1, 4, 7, 10}
_DUSTHANA_HOUSES = {6, 8, 12}

_EXALTATION_SIGNS = {
    "SUN": "MESHA", "MOON": "VRISHABHA", "MARS": "MAKARA",
    "MERCURY": "KANYA", "JUPITER": "KARKA", "VENUS": "MEENA", "SATURN": "TULA",
}

_OWN_SIGNS = {
    "SUN": {"SIMHA"}, "MOON": {"KARKA"}, "MARS": {"MESHA", "VRISHCHIKA"},
    "MERCURY": {"MITHUNA", "KANYA"}, "JUPITER": {"DHANUSHA", "MEENA"},
    "VENUS": {"VRISHABHA", "TULA"}, "SATURN": {"MAKARA", "KUMBHA"},
}

_DEBILITATION_SIGNS = {
    "SUN": "TULA", "MOON": "VRISHCHIKA", "MARS": "KARKA",
    "MERCURY": "MEENA", "JUPITER": "MAKARA", "VENUS": "KANYA", "SATURN": "MESHA",
}


def _get_modifier_info(planets: dict, planet: str, rashi_num: int) -> dict[str, Any]:
    """Get all modifier-relevant info for a planet."""
    pdata = planets.get(planet, {})
    rashi = pdata.get("rashi", "")
    house = pdata.get("house", 0)
    combust = pdata.get("combust", False)
    debilitated = pdata.get("debilitated", False)
    retrograde = pdata.get("retrograde", False)
    longitude = pdata.get("longitude_used") or pdata.get("longitude", 0)

    # Check exaltation / own sign / debilitation
    is_exalted = rashi == _EXALTATION_SIGNS.get(planet, "")
    is_own_sign = rashi in _OWN_SIGNS.get(planet, set())
    is_debilitated_classical = rashi == _DEBILITATION_SIGNS.get(planet, "")

    # Node conjunction check
    rahu_house = planets.get("RAHU", {}).get("house", 0)
    ketu_house = planets.get("KETU", {}).get("house", 0)
    node_conjunct = (house == rahu_house) or (house == ketu_house)

    # Node 7th aspect check
    node_aspect = False
    for n_house in [rahu_house, ketu_house]:
        if isinstance(n_house, int) and n_house > 0:
            aspect_house = (n_house + 6) % 12
            if aspect_house == 0:
                aspect_house = 12
            if aspect_house == house:
                node_aspect = True
                break

    # Dusthana placement
    in_dusthana = house in _DUSTHANA_HOUSES

    return {
        "planet": planet,
        "rashi": rashi,
        "house": house,
        "longitude": longitude,
        "combust": combust,
        "debilitated": debilitated,
        "retrograde": retrograde,
        "is_exalted": is_exalted,
        "is_own_sign": is_own_sign,
        "is_debilitated_classical": is_debilitated_classical,
        "node_conjunct": node_conjunct,
        "node_aspect": node_aspect,
        "in_dusthana": in_dusthana,
    }


def diagnose_newton_saraswati() -> dict[str, Any]:
    """Main diagnostic function."""
    fixture_path = FIXTURES_DIR / "chart_006_newton.json"
    with open(fixture_path) as f:
        chart = json.load(f)

    facts = chart["expected_canonical_facts"]
    planets = facts["planets"]

    print("=" * 72)
    print("NEWTON SARASWATI TRACE — Phase E6j Part A")
    print("=" * 72)
    print()

    # ── Section 1: Chart Summary ──
    print("Section 1: Newton Chart Summary")
    print("-" * 40)
    lagna = facts["lagna"]
    print(f"  Lagna: {lagna['rashi']} ({lagna['ascendant_longitude_deg']:.2f}°)")
    print()
    for pname in ["JUPITER", "MERCURY", "VENUS", "SUN", "MOON", "MARS", "SATURN", "RAHU", "KETU"]:
        d = planets[pname]
        house = d.get("house", "?")
        retro = d.get("retrograde", "?")
        print(f"  {pname:8s}: H{str(house):>2s} {d['rashi']:12s} retro={retro}")

    # ── Section 2: Saraswati Formation Check ──
    print()
    print("Section 2: Saraswati Formation Conditions")
    print("-" * 40)

    jup = planets.get("JUPITER", {})
    merc = planets.get("MERCURY", {})
    ven = planets.get("VENUS", {})

    _SARASWATI_HOUSES = {1, 2, 4, 5, 7, 9, 10, 11}
    jup_house = jup.get("house", 0)
    merc_house = merc.get("house", 0)
    ven_house = ven.get("house", 0)

    all_in_range = all(h in _SARASWATI_HOUSES for h in [jup_house, merc_house, ven_house])
    jup_rashi = jup.get("rashi", "")
    jup_strong = jup_house in _KENDRA_HOUSES or jup_rashi in {"DHANUSHA", "MEENA", "KARKA"}

    print(f"  JUPITER:  H{jup_house} {jup_rashi}")
    print(f"  MERCURY:  H{merc_house} {merc.get('rashi', '')}")
    print(f"  VENUS:    H{ven_house} {ven.get('rashi', '')}")
    print()
    print(f"  All in Saraswati houses (1/2/4/5/7/9/10/11): {all_in_range}")
    print(f"  Jupiter strong (Kendra or own/exalt): {jup_strong}")
    print(f"  Saraswati FORMED: {all_in_range and jup_strong}")

    # ── Section 3: Modifier Analysis for Each Planet ──
    print()
    print("Section 3: Modifier Analysis (5-Tier Pipeline)")
    print("-" * 40)

    results = {}
    for pname in ["JUPITER", "MERCURY", "VENUS"]:
        info = _get_modifier_info(planets, pname, 0)
        results[pname] = info

        print(f"\n  {pname}:")
        print(f"    Rashi: {info['rashi']}")
        print(f"    House: {info['house']}")
        print(f"    Longitude: {info['longitude']:.2f}°")
        print(f"    Combust: {info['combust']}")
        print(f"    Debilitated: {info['debilitated']}")
        print(f"    Retrograde: {info['retrograde']}")
        print(f"    Exalted: {info['is_exalted']}")
        print(f"    Own sign: {info['is_own_sign']}")
        print(f"    Classical debilitated: {info['is_debilitated_classical']}")
        print(f"    Node conjunct: {info['node_conjunct']}")
        print(f"    Node aspect: {info['node_aspect']}")
        print(f"    In dusthana: {info['in_dusthana']}")

        # Predict modifier outcome
        if info['combust']:
            if info['is_exalted'] or info['is_own_sign']:
                print(f"    → COMBUSTION_OFFSET (WEAKENED, 0.5x)")
            else:
                print(f"    → COMBUSTION (CANCELLED)")
        elif info['debilitated'] or info['is_debilitated_classical']:
            print(f"    → DEBILITATION (CANCELLED unless Neecha Bhanga)")
        elif info['in_dusthana']:
            print(f"    → DUSTHANA_PLACEMENT (WEAKENED, 0.5x)")
        elif info['node_conjunct']:
            print(f"    → NODE_CONJUNCTION_TAINT (WEAKENED, 0.7x)")
        elif info['node_aspect']:
            print(f"    → NODE_ASPECT_TAINT (WEAKENED, 0.85x)")
        else:
            print(f"    → FORMED (no modifiers)")

    # ── Section 4: Actual Engine Run ──
    print()
    print("Section 4: Actual Engine Evaluation")
    print("-" * 40)

    from jrs.yoga_evaluator.service import YogaEvaluatorService
    from jrs.yoga_evaluator.modifier_service import ModifierEvaluationService

    svc = YogaEvaluatorService()
    eval_results = svc.evaluate_classical_yogas(facts)

    saraswati_found = False
    for r in eval_results:
        if r.yoga_name == "Saraswati":
            saraswati_found = True
            print(f"  Saraswati status: {r.status.value}")
            print(f"  Chain impact: {r.chain_impact}")
            print(f"  Cancellation reason: {r.cancellation_reason}")
            if r.modifier_report:
                print(f"  Modifier overall status: {r.modifier_report.overall_status.value}")
                print(f"  Modifier overall strength: {r.modifier_report.overall_strength:.4f}")
                for pr in r.modifier_report.planet_results:
                    chain = [m.value for m in pr.modifier_chain] if pr.modifier_chain else []
                    print(f"    {pr.planet}: status={pr.status.value} strength={pr.net_strength:.4f} "
                          f"combust={pr.is_combust} deb={pr.is_debilitated} chain={chain}")
                    if pr.cancellation_reason:
                        print(f"      Reason: {pr.cancellation_reason}")

    if not saraswati_found:
        print("  Saraswati NOT found in engine results!")
        print("  Running modifier evaluation manually...")
        mod_svc = ModifierEvaluationService()
        mod_report = mod_svc.evaluate_modifiers(["JUPITER", "MERCURY", "VENUS"], facts)
        print(f"  Modifier overall status: {mod_report.overall_status.value}")
        print(f"  Modifier overall strength: {mod_report.overall_strength:.4f}")
        for pr in mod_report.planet_results:
            chain = [m.value for m in pr.modifier_chain] if pr.modifier_chain else []
            print(f"    {pr.planet}: status={pr.status.value} strength={pr.net_strength:.4f} "
                  f"combust={pr.is_combust} deb={pr.is_debilitated} chain={chain}")
            if pr.cancellation_reason:
                print(f"      Reason: {pr.cancellation_reason}")

    # ── Section 5: Verdict ──
    print()
    print("Section 5: Verdict")
    print("-" * 40)

    if saraswati_found:
        r = next(r for r in eval_results if r.yoga_name == "Saraswati")
        if r.status.value == "CANCELLED":
            reason = r.cancellation_reason or "unknown"
            print(f"  Saraswati is CANCELLED")
            print(f"  Cancellation reason: {reason}")
            if "combust" in reason.lower():
                print(f"  → This is CLASSICALLY JUSTIFIED (BPHS Ch 7: combust planet results destroyed)")
            elif "dusthana" in reason.lower():
                print(f"  → SUSPICIOUS: Dusthana placement is NOT a classical cancellation for Saraswati")
            elif "debilitated" in reason.lower():
                print(f"  → Check if Neecha Bhanga applies")
            else:
                print(f"  → UNKNOWN: needs further research")
        else:
            print(f"  Saraswati is {r.status.value} (not cancelled)")
    else:
        print("  Saraswati was not detected by the engine at all")
        print("  This means the formation check or modifier pipeline prevented it")

    return {
        "saraswati_found": saraswati_found,
        "jupiter_info": results.get("JUPITER", {}),
        "mercury_info": results.get("MERCURY", {}),
        "venus_info": results.get("VENUS", {}),
    }


if __name__ == "__main__":
    result = diagnose_newton_saraswati()

    # Write report
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "newton_saraswati_trace.md"

    with open(report_path, "w") as f:
        f.write("# Newton Saraswati Trace — Phase E6j Part A\n\n")
        f.write("## Executive Summary\n\n")

        jup = result.get("jupiter_info", {})
        merc = result.get("mercury_info", {})
        ven = result.get("venus_info", {})

        f.write(f"Newton's Saraswati Yoga involves Jupiter (H{jup.get('house')}, {jup.get('rashi')}), "
                f"Mercury (H{merc.get('house')}, {merc.get('rashi')}), "
                f"and Venus (H{ven.get('house')}, {ven.get('rashi')}).\n\n")

        if result.get("saraswati_found"):
            f.write("**Saraswati was detected by the engine** but cancelled by the modifier pipeline.\n")
        else:
            f.write("**Saraswati was NOT detected** by the engine (formation or modifier check prevented it).\n")

        f.write("\n## Modifier Analysis\n\n")
        f.write("| Planet | House | Rashi | Combust | Debilitated | Node Conj | Dusthana | Predicted Modifier |\n")
        f.write("|--------|-------|-------|---------|-------------|-----------|----------|--------------------|\n")
        for pname, info in [("Jupiter", jup), ("Mercury", merc), ("Venus", ven)]:
            house = info.get("house", "?")
            rashi = info.get("rashi", "?")
            combust = info.get("combust", False)
            deb = info.get("debilitated", False)
            node = info.get("node_conjunct", False)
            dust = info.get("in_dusthana", False)
            predicted = "FORMED"
            if combust:
                predicted = "CANCELLED (or WEAKENED if own/exalt)"
            elif deb:
                predicted = "CANCELLED (unless Neecha Bhanga)"
            elif dust:
                predicted = "WEAKENED (dusthana)"
            elif node:
                predicted = "WEAKENED (node taint)"
            f.write(f"| {pname} | H{house} | {rashi} | {combust} | {deb} | {node} | {dust} | {predicted} |\n")

        f.write("\n## Root Cause\n\n")
        f.write("See console output above for the detailed layer-by-layer trace.\n")
        f.write("The cancellation reason will be listed in the engine evaluation section.\n")

    print(f"\nReport written to: {report_path}")
