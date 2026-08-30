#!/usr/bin/env python3
"""Phase E6j Part B: Cohort-Wide Modifier Cancellation Audit.

For ALL 10 charts × ALL detected yogas:
- Records every yoga that formed
- Records which modifier (if any) cancelled it
- Categorizes each cancellation as Classically Justified, Suspicious, or Unknown

Usage::

    python scripts/audit_modifier_cancellations.py
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

# Classical cancellation rules (BPHS)
_CLASSICAL_CANCELLATIONS = {
    "COMBUSTION": "Classically justified — BPHS Ch 7: combust planet results destroyed",
    "COMBUSTION_OFFSET": "Classically justified — Phaladeepika: exaltation/own-sign offsets combustion",
    "DEBILITATION": "Classically justified — BPHS Ch 43: debilitation cancels yoga",
    "NEECHA_BHANGA": "Classically justified — BPHS Ch 43: Neecha Bhanga restores debilitation",
    "GRAHA_YUDDHA_DEFEATED": "Classically justified — Saravali Ch 24: defeated planet suppressed",
    "NODE_CONJUNCTION_TAINT": "Classically justified — BPHS Ch 9: node conjunction weakens",
    "NODE_ASPECT_TAINT": "Classically justified — BPHS Ch 9: node aspect weakens",
    "DUSTHANA_PLACEMENT": "Suspicious — Not a classical cancellation for most yogas",
    "CHESHTA_BALA": "Classically justified — BPHCh 5: retrograde affects strength",
}

# Yogas where dusthana placement IS classically relevant
_DUSTHANA_RELEVANT_YOGAS = {"Vipareeta Raja"}


def audit_all_charts() -> dict[str, Any]:
    """Audit all charts for modifier cancellations."""
    from jrs.yoga_evaluator.service import YogaEvaluatorService
    from jrs.yoga_evaluator.modifier_service import ModifierEvaluationService

    svc = YogaEvaluatorService()
    mod_svc = ModifierEvaluationService()

    all_cancellations = []
    all_formed = []
    all_survived = []

    chart_files = sorted(FIXTURES_DIR.glob("chart_*.json"))

    for chart_path in chart_files:
        with open(chart_path) as f:
            chart = json.load(f)

        facts = chart["expected_canonical_facts"]
        name = chart["_meta"]["subject"]

        # Run engine evaluation
        results = svc.evaluate_classical_yogas(facts)

        # Also run raw modifier check to see what WOULD have formed
        raw_planets = facts.get("planets", {})
        house_lords_raw = facts.get("house_lords", {})
        house_lords = {}
        for k, v in house_lords_raw.items():
            try:
                house_lords[int(k)] = v
            except (ValueError, TypeError):
                pass

        # Check what yogas the formation check would detect (before modifiers)
        # We do this by checking formation conditions directly
        formation_yogas = []

        # Gajakesari
        jup_house = raw_planets.get("JUPITER", {}).get("house")
        moon_house = raw_planets.get("MOON", {}).get("house")
        if isinstance(jup_house, int) and isinstance(moon_house, int):
            diff = (jup_house - moon_house) % 12
            if diff in {0, 3, 6, 9}:
                formation_yogas.append(("Gajakesari", ["JUPITER", "MOON"]))

        # Raja
        kendra_houses = {1, 4, 7, 10}
        trikona_houses = {1, 5, 9}
        kendra_lords_list = []
        trikona_lords_list = []
        for pname, pdata in raw_planets.items():
            house = pdata.get("house")
            if not isinstance(house, int):
                continue
            lord_of = pdata.get("house_lord_of", [])
            for h in lord_of:
                if h in kendra_houses:
                    kendra_lords_list.append((pname, house))
                if h in trikona_houses:
                    trikona_lords_list.append((pname, house))
        # Also from house_lords
        for h_num, lord in house_lords.items():
            if isinstance(h_num, int) and isinstance(lord, str):
                pdata = raw_planets.get(lord, {})
                house = pdata.get("house")
                if isinstance(house, int):
                    if h_num in kendra_houses:
                        kendra_lords_list.append((lord, house))
                    if h_num in trikona_houses:
                        trikona_lords_list.append((lord, house))
        seen_k = {}
        for pn, ph in kendra_lords_list:
            if pn not in seen_k:
                seen_k[pn] = ph
        seen_t = {}
        for pn, ph in trikona_lords_list:
            if pn not in seen_t:
                seen_t[pn] = ph
        for kn, kh in seen_k.items():
            for tn, th in seen_t.items():
                if kn == tn:
                    continue
                if kh == th or abs(kh - th) == 7:
                    formation_yogas.append(("Raja", [kn, tn]))
                    break
            else:
                continue
            break

        # Budhaditya
        sun = raw_planets.get("SUN", {})
        merc = raw_planets.get("MERCURY", {})
        sun_house = sun.get("house")
        merc_house = merc.get("house")
        if isinstance(sun_house, int) and isinstance(merc_house, int):
            if sun_house == merc_house and sun.get("rashi") == merc.get("rashi"):
                sun_lon = sun.get("longitude_used") or sun.get("longitude", 0)
                merc_lon = merc.get("longitude_used") or merc.get("longitude", 0)
                diff = abs(sun_lon - merc_lon)
                if diff > 180:
                    diff = 360 - diff
                if diff >= 8.0:
                    formation_yogas.append(("Budhaditya", ["SUN", "MERCURY"]))

        # Pancha Mahapurusha
        _PM_MAP = {
            "MARS": ("Ruchaka", {"MESHA", "VRISHCHIKA"}, "MAKARA"),
            "MERCURY": ("Bhadra", {"MITHUNA", "KANYA"}, "KANYA"),
            "JUPITER": ("Hamsa", {"DHANUSHA", "MEENA"}, "KARKA"),
            "VENUS": ("Malavya", {"VRISHABHA", "TULA"}, "MEENA"),
            "SATURN": ("Sasa", {"MAKARA", "KUMBHA"}, "TULA"),
        }
        for pname, (yname, own, exalt) in _PM_MAP.items():
            pdata = raw_planets.get(pname, {})
            house = pdata.get("house")
            rashi = pdata.get("rashi", "")
            if isinstance(house, int) and house in kendra_houses:
                if rashi in own or rashi == exalt:
                    formation_yogas.append((yname, [pname]))

        # Chandra Yogas
        moon_house_val = raw_planets.get("MOON", {}).get("house")
        if isinstance(moon_house_val, int):
            for pname, pdata in raw_planets.items():
                if pname in ("MOON", "SUN", "RAHU", "KETU"):
                    continue
                ph = pdata.get("house")
                if not isinstance(ph, int):
                    continue
                if (ph - moon_house_val) % 12 == 1:
                    formation_yogas.append(("Anapha", ["MOON", pname]))
                elif (moon_house_val - ph) % 12 == 1:
                    formation_yogas.append(("Sunapha", ["MOON", pname]))

        # Saraswati
        _SARASWATI_HOUSES = {1, 2, 4, 5, 7, 9, 10, 11}
        jh = raw_planets.get("JUPITER", {}).get("house")
        mh = raw_planets.get("MERCURY", {}).get("house")
        vh = raw_planets.get("VENUS", {}).get("house")
        if isinstance(jh, int) and isinstance(mh, int) and isinstance(vh, int):
            if all(h in _SARASWATI_HOUSES for h in [jh, mh, vh]):
                jup_rashi = raw_planets.get("JUPITER", {}).get("rashi", "")
                if jh in kendra_houses or jup_rashi in {"DHANUSHA", "MEENA", "KARKA"}:
                    formation_yogas.append(("Saraswati", ["JUPITER", "MERCURY", "VENUS"]))

        # Amala
        _AMALA_BENEFICS = {"JUPITER", "VENUS", "MERCURY", "MOON"}
        _AMALA_MALEFICS = {"SATURN", "MARS", "RAHU", "KETU"}
        for pname in _AMALA_BENEFICS:
            pdata = raw_planets.get(pname, {})
            ph = pdata.get("house")
            if isinstance(ph, int) and ph == 10:
                has_malefic = any(
                    raw_planets.get(mp, {}).get("house") == 10
                    for mp in _AMALA_MALEFICS
                )
                if not has_malefic:
                    formation_yogas.append(("Amala", [pname]))
                    break

        # Now compare formation vs engine results
        engine_names = {r.yoga_name for r in results}
        engine_details = {r.yoga_name: r for r in results}

        print(f"\n{'='*60}")
        print(f"  {name} ({chart_path.stem})")
        print(f"{'='*60}")
        print(f"  Formation yogas: {[y[0] for y in formation_yogas]}")
        print(f"  Engine yogas:    {[r.yoga_name for r in results]}")

        for fy_name, fy_planets in formation_yogas:
            entry = {
                "chart": name,
                "fixture": chart_path.stem,
                "yoga": fy_name,
                "involved_planets": fy_planets,
                "formed": True,
            }

            if fy_name in engine_names:
                r = engine_details[fy_name]
                entry["engine_status"] = r.status.value
                entry["cancellation_reason"] = r.cancellation_reason

                if r.status.value == "CANCELLED":
                    # Classify the cancellation
                    reason = r.cancellation_reason or ""
                    if "combust" in reason.lower():
                        entry["classification"] = "CLASSICALLY_JUSTIFIED"
                        entry["rule"] = "COMBUSTION"
                    elif "debilitated" in reason.lower():
                        entry["classification"] = "CLASSICALLY_JUSTIFIED"
                        entry["rule"] = "DEBILITATION"
                    elif "dusthana" in reason.lower():
                        if fy_name in _DUSTHANA_RELEVANT_YOGAS:
                            entry["classification"] = "CLASSICALLY_JUSTIFIED"
                            entry["rule"] = "DUSTHANA_PLACEMENT"
                        else:
                            entry["classification"] = "SUSPICIOUS"
                            entry["rule"] = "DUSTHANA_PLACEMENT"
                    elif "node" in reason.lower():
                        entry["classification"] = "CLASSICALLY_JUSTIFIED"
                        entry["rule"] = "NODE_TAINT"
                    else:
                        entry["classification"] = "UNKNOWN"
                        entry["rule"] = "UNKNOWN"
                    all_cancellations.append(entry)
                    print(f"    {fy_name}: CANCELLED — {reason} [{entry['classification']}]")
                elif r.status.value == "WEAKENED":
                    entry["classification"] = "SURVIVED_WEAKENED"
                    all_survived.append(entry)
                    print(f"    {fy_name}: WEAKENED — {r.cancellation_reason or 'modifier applied'}")
                else:
                    entry["classification"] = "SURVIVED"
                    all_survived.append(entry)
                    print(f"    {fy_name}: FORMED")
            else:
                entry["engine_status"] = "NOT_IN_ENGINE"
                entry["classification"] = "NOT_DETECTED"
                all_formed.append(entry)
                print(f"    {fy_name}: NOT DETECTED by engine")

    # ── Summary ──
    total_formed = len(all_cancellations) + len(all_survived)
    justifiable = sum(1 for c in all_cancellations if c["classification"] == "CLASSICALLY_JUSTIFIED")
    suspicious = sum(1 for c in all_cancellations if c["classification"] == "SUSPICIOUS")
    unknown = sum(1 for c in all_cancellations if c["classification"] == "UNKNOWN")
    survived = len(all_survived)

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Total yogas formed at Layer 1:  {total_formed}")
    print(f"  Classically justified cancellations: {justifiable}")
    print(f"  Suspicious cancellations:            {suspicious}")
    print(f"  Unknown cancellations:               {unknown}")
    print(f"  Survived to activation:              {survived}")

    return {
        "total_formed": total_formed,
        "cancellations": all_cancellations,
        "survived": all_survived,
        "not_detected": all_formed,
        "summary": {
            "justifiable": justifiable,
            "suspicious": suspicious,
            "unknown": unknown,
            "survived": survived,
        },
    }


if __name__ == "__main__":
    result = audit_all_charts()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "modifier_cancellation_audit.md"

    with open(report_path, "w") as f:
        f.write("# Modifier Cancellation Audit — Phase E6j Part B\n\n")
        f.write("## Executive Summary\n\n")

        s = result["summary"]
        total = result["total_formed"]
        f.write(f"Total yogas formed at Layer 1: **{total}**\n\n")
        f.write(f"| Category | Count | % |\n")
        f.write(f"|----------|-------|---|\n")
        f.write(f"| Classically justified cancellations | {s['justifiable']} | {s['justifiable']/max(total,1)*100:.0f}% |\n")
        f.write(f"| Suspicious cancellations | {s['suspicious']} | {s['suspicious']/max(total,1)*100:.0f}% |\n")
        f.write(f"| Unknown cancellations | {s['unknown']} | {s['unknown']/max(total,1)*100:.0f}% |\n")
        f.write(f"| Survived to activation | {s['survived']} | {s['survived']/max(total,1)*100:.0f}% |\n")

        f.write("\n## Suspicious Cancellations\n\n")
        suspicious = [c for c in result["cancellations"] if c["classification"] == "SUSPICIOUS"]
        if suspicious:
            f.write("| Chart | Yoga | Modifier | Reason |\n")
            f.write("|-------|------|----------|--------|\n")
            for c in suspicious:
                f.write(f"| {c['chart']} | {c['yoga']} | {c['rule']} | {c['cancellation_reason']} |\n")
        else:
            f.write("No suspicious cancellations found.\n")

        f.write("\n## All Cancellations Detail\n\n")
        f.write("| Chart | Yoga | Classification | Reason |\n")
        f.write("|-------|------|----------------|--------|\n")
        for c in result["cancellations"]:
            f.write(f"| {c['chart']} | {c['yoga']} | {c['classification']} | {c['cancellation_reason'] or 'N/A'} |\n")

        f.write("\n## Survived Yogas\n\n")
        f.write("| Chart | Yoga | Status |\n")
        f.write("|-------|------|--------|\n")
        for c in result["survived"]:
            f.write(f"| {c['chart']} | {c['yoga']} | {c['engine_status']} |\n")

    print(f"\nReport written to: {report_path}")

    # Also write JSON
    json_path = REPORT_DIR / "modifier_cancellation_audit.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"JSON data written to: {json_path}")
