#!/usr/bin/env python3
"""Mozart Zero-Hit Diagnosis — Phase E6h Track B.

Traces why the engine produces 0 yoga activations for Mozart's 3 events.
Identifies classical yogas that should form but don't, and the root cause.

Usage::

    python scripts/diagnose_mozart_zero.py
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

# ── Constants ──────────────────────────────────────────────────────────────

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
_TRIKONA_HOUSES = {1, 5, 9}
_DUSTHANA_HOUSES = {6, 8, 12}

_NATURAL_BENEFICS = {"JUPITER", "VENUS", "MERCURY", "MOON"}
_NATURAL_MALEFICS = {"SATURN", "MARS", "SUN", "RAHU", "KETU"}


def _house_from_lagna(planet_rashi: str, lagna_rashi: str) -> int:
    """Compute house number from lagna."""
    li = _RASHI_ORDER.index(lagna_rashi)
    pi = _RASHI_ORDER.index(planet_rashi)
    return ((pi - li) % 12) + 1


def _house_from_moon(planet_rashi: str, moon_rashi: str) -> int:
    """Compute house number from Moon."""
    mi = _RASHI_ORDER.index(moon_rashi)
    pi = _RASHI_ORDER.index(planet_rashi)
    return ((pi - mi) % 12) + 1


def _get_house_lords(lagna_rashi: str) -> dict[int, str]:
    """Get house lords for each house from lagna."""
    li = _RASHI_ORDER.index(lagna_rashi)
    lords = {}
    for house in range(1, 13):
        sign = _RASHI_ORDER[(li + house - 1) % 12]
        lords[house] = _SIGN_LORDS[sign]
    return lords


def _check_budhaditya(planets: dict) -> dict[str, Any]:
    """Check if Budhaditya Yoga (Sun + Mercury conjunction) forms."""
    sun = planets.get("SUN", {})
    merc = planets.get("MERCURY", {})
    sun_house = sun.get("house")
    merc_house = merc.get("house")
    if sun_house is None or merc_house is None:
        return {"detected": False, "reason": "missing house data"}
    if sun_house == merc_house:
        return {
            "detected": True,
            "planets": ["SUN", "MERCURY"],
            "house": sun_house,
            "sign": sun.get("rashi"),
            "reason": f"SUN and MERCURY in house {sun_house} ({sun.get('rashi')})",
        }
    return {"detected": False, "reason": f"SUN in H{sun_house}, MERCURY in H{merc_house} (not conjunct)"}


def _check_gajakesari(planets: dict) -> dict[str, Any]:
    """Check if Gajakesari Yoga (Jupiter in kendra from Moon) forms."""
    jup = planets.get("JUPITER", {})
    moon = planets.get("MOON", {})
    jup_house = jup.get("house")
    moon_house = moon.get("house")
    if jup_house is None or moon_house is None:
        return {"detected": False, "reason": "missing house data"}
    diff = (jup_house - moon_house) % 12
    if diff in {0, 3, 6, 9}:
        return {
            "detected": True,
            "planets": ["JUPITER", "MOON"],
            "reason": f"Jupiter H{jup_house} in kendra from Moon H{moon_house}",
        }
    return {"detected": False, "reason": f"Jupiter H{jup_house} NOT in kenda from Moon H{moon_house} (diff={diff})"}


def _check_pancha_mahapurusha(planets: dict) -> list[dict]:
    """Check for Pancha Mahapurusha yogas (planet in own sign/exaltation in kendra)."""
    results = []
    pm_map = {
        "MARS": {"own_signs": {"MESHA", "VRISHCHIKA"}, "exaltation": "MAKARA", "yoga": "Ruchaka"},
        "MERCURY": {"own_signs": {"MITHUNA", "KANYA"}, "exaltation": "KANYA", "yoga": "Bhadra"},
        "JUPITER": {"own_signs": {"DHANUSHA", "MEENA"}, "exaltation": "KARKA", "yoga": "Hamsa"},
        "VENUS": {"own_signs": {"VRISHABHA", "TULA"}, "exaltation": "MEENA", "yoga": "Malavya"},
        "SATURN": {"own_signs": {"MAKARA", "KUMBHA"}, "exaltation": "TULA", "yoga": "Sasa"},
    }
    for planet, info in pm_map.items():
        pdata = planets.get(planet, {})
        rashi = pdata.get("rashi", "")
        house = pdata.get("house")
        if house is None:
            continue
        in_own_sign = rashi in info["own_signs"]
        is_exalted = rashi == info["exaltation"]
        in_kendra = house in _KENDRA_HOUSES
        if in_kendra and (in_own_sign or is_exalted):
            quality = "own sign" if in_own_sign else "exalted"
            results.append({
                "detected": True,
                "yoga": info["yoga"],
                "planet": planet,
                "house": house,
                "sign": rashi,
                "reason": f"{planet} in {quality} ({rashi}) in Kendra H{house}",
            })
    return results


def _check_sunapha_anapha(planets: dict) -> list[dict]:
    """Check Sunapha (2nd from Moon), Anapha (12th from Moon), Durudhara (12th from Sun)."""
    results = []
    moon = planets.get("MOON", {})
    moon_rashi = moon.get("rashi", "")
    moon_house = moon.get("house")
    if not moon_rashi or moon_house is None:
        return results

    moon_idx = _RASHI_ORDER.index(moon_rashi)
    # 2nd from Moon = Sunapha
    second_from_moon = _RASHI_ORDER[(moon_idx + 1) % 12]
    for pname, pdata in planets.items():
        if pname in ("SUN", "RAHU", "KETU"):
            continue
        if pdata.get("rashi") == second_from_moon:
            house_from_moon = _house_from_moon(pdata["rashi"], moon_rashi)
            results.append({
                "detected": True,
                "yoga": "Sunapha",
                "planet": pname,
                "reason": f"{pname} in 2nd from Moon ({second_from_moon})",
            })

    # 12th from Moon = Anapha
    twelfth_from_moon = _RASHI_ORDER[(moon_idx - 1) % 12]
    for pname, pdata in planets.items():
        if pname in ("SUN", "RAHU", "KETU"):
            continue
        if pdata.get("rashi") == twelfth_from_moon:
            results.append({
                "detected": True,
                "yoga": "Anapha",
                "planet": pname,
                "reason": f"{pname} in 12th from Moon ({twelfth_from_moon})",
            })

    return results


def _check_hamsa(planets: dict) -> dict[str, Any]:
    """Check Hamsa Yoga: Jupiter in Kendra in own sign or exaltation."""
    jup = planets.get("JUPITER", {})
    rashi = jup.get("rashi", "")
    house = jup.get("house")
    if house is None:
        return {"detected": False, "reason": "missing house data"}
    own_signs = {"DHANUSHA", "MEENA"}
    exaltation = "KARKA"
    if house in _KENDRA_HOUSES and (rashi in own_signs or rashi == exaltation):
        return {
            "detected": True,
            "planets": ["JUPITER"],
            "reason": f"Jupiter in {rashi} (own/exalted) in Kendra H{house}",
        }
    return {"detected": False, "reason": f"Jupiter in {rashi} H{house} (not in kendra or own/exalted sign)"}


def _check_saraswati(planets: dict) -> dict[str, Any]:
    """Check Saraswati Yoga: Jupiter, Mercury, Venus in Kendras (1/4/7/10) with strong Jupiter."""
    jup = planets.get("JUPITER", {})
    merc = planets.get("MERCURY", {})
    ven = planets.get("VENUS", {})
    jup_house = jup.get("house")
    merc_house = merc.get("house")
    ven_house = ven.get("house")
    if jup_house is None or merc_house is None or ven_house is None:
        return {"detected": False, "reason": "missing house data"}
    all_in_kendra = (
        jup_house in _KENDRA_HOUSES
        and merc_house in _KENDRA_HOUSES
        and ven_house in _KENDRA_HOUSES
    )
    jup_own_exalt = jup.get("rashi", "") in {"DHANUSHA", "MEENA", "KARKA"}
    if all_in_kendra and jup_own_exalt:
        return {
            "detected": True,
            "planets": ["JUPITER", "MERCURY", "VENUS"],
            "reason": f"All 3 in Kendras (J={jup_house}, M={merc_house}, V={ven_house}), Jupiter strong",
        }
    return {
        "detected": False,
        "reason": f"J={jup_house} M={merc_house} V={ven_house} — not all in kendra, or Jupiter not strong",
    }


def _check_raja_yoga(planets: dict, house_lords: dict) -> dict[str, Any]:
    """Check Raja Yoga: Kendra lord conjunct or aspecting Trikona lord."""
    kendra_lords = {}
    trikona_lords = {}
    for h, lord in house_lords.items():
        if h in _KENDRA_HOUSES:
            pdata = planets.get(lord, {})
            p_house = pdata.get("house")
            if p_house is not None:
                kendra_lords[lord] = p_house
        if h in _TRIKONA_HOUSES:
            pdata = planets.get(lord, {})
            p_house = pdata.get("house")
            if p_house is not None:
                trikona_lords[lord] = p_house

    for k_name, k_house in kendra_lords.items():
        for t_name, t_house in trikona_lords.items():
            if k_name == t_name:
                continue
            if k_house == t_house:
                return {
                    "detected": True,
                    "planets": [k_name, t_name],
                    "reason": f"Kendra lord {k_name}(H{k_house}) conjunct Trikona lord {t_name}(H{t_house})",
                }
            if abs(k_house - t_house) == 7:
                return {
                    "detected": True,
                    "planets": [k_name, t_name],
                    "reason": f"Kendra lord {k_name}(H{k_house}) mutual aspect Trikona lord {t_name}(H{t_house})",
                }
    return {"detected": False, "reason": "No kendra-trikona conjunction or mutual aspect found"}


def _check_dhana_yoga(planets: dict, house_lords: dict) -> dict[str, Any]:
    """Check Dhana Yoga: 2nd lord conjunct or aspecting 11th lord."""
    lord_2 = house_lords.get(2)
    lord_11 = house_lords.get(11)
    if not lord_2 or not lord_11:
        return {"detected": False, "reason": "missing house lord data"}
    h2 = planets.get(lord_2, {}).get("house")
    h11 = planets.get(lord_11, {}).get("house")
    if h2 is None or h11 is None:
        return {"detected": False, "reason": "missing house data"}
    if h2 == h11:
        return {"detected": True, "planets": [lord_2, lord_11], "reason": f"{lord_2} and {lord_11} conjunct in H{h2}"}
    if abs(h2 - h11) == 7:
        return {"detected": True, "planets": [lord_2, lord_11], "reason": f"{lord_2}(H{h2}) aspects {lord_11}(H{h11})"}
    return {"detected": False, "reason": f"{lord_2}(H{h2}) and {lord_11}(H{h11}) — not conjunct or aspecting"}


def diagnose_mozart() -> dict[str, Any]:
    """Main diagnostic function."""
    fixture_path = FIXTURES_DIR / "chart_003_mozart.json"
    with open(fixture_path) as f:
        chart = json.load(f)

    facts = chart["expected_canonical_facts"]
    planets = facts["planets"]
    lagna = facts["lagna"]["rashi"]
    moon_rashi = planets["MOON"]["rashi"]

    # Assign houses
    for pname, pdata in planets.items():
        if "house" not in pdata:
            pdata["house"] = _house_from_lagna(pdata["rashi"], lagna)

    house_lords = _get_house_lords(lagna)

    # ── Section 1: Chart Summary ──
    print("=" * 72)
    print("MOZART ZERO-HIT DIAGNOSIS")
    print("=" * 72)
    print()
    print("Section 1: Mozart Chart Summary")
    print("-" * 40)
    print(f"  Lagna: {lagna}")
    print(f"  Moon: {moon_rashi} (nakshatra: {planets['MOON'].get('nakshatra_lord', '?')})")
    print()
    print("  Planet positions:")
    for pname in ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN", "RAHU", "KETU"]:
        d = planets[pname]
        house = d.get("house", "?")
        retro = d.get("retrograde", "?")
        print(f"    {pname:8s}: H{str(house):>2s} {d['rashi']:12s} Nak_lord={d.get('nakshatra_lord', '?'):8s} retro={retro}")
    print()
    print("  House Lords:")
    for h in range(1, 13):
        print(f"    H{h:2d} ({_RASHI_ORDER[(list(_RASHI_ORDER).index(lagna) + h - 1) % 12]:12s}): {house_lords[h]}")

    # ── Section 2: Engine Detection ──
    print()
    print("Section 2: Yogas Detected by Engine")
    print("-" * 40)
    from jrs.yoga_evaluator.service import YogaEvaluatorService
    evaluator = YogaEvaluatorService()
    engine_results = evaluator.evaluate_classical_yogas(facts)
    if engine_results:
        for r in engine_results:
            print(f"  {r.yoga_name}: status={r.status.value}, chain_impact={r.chain_impact:.4f}")
    else:
        print("  (No yogas returned by engine — check if evaluate_classical_yogas returns empty)")
    print()

    # ── Section 3: Classical Yoga Checks ──
    print("Section 3: Classical Yoga Checks (Expected)")
    print("-" * 40)

    classical_yogas = []

    # Budhaditya
    budha = _check_budhaditya(planets)
    status = "FORMED" if budha["detected"] else "NOT_FORMED"
    print(f"  Budhaditya Yoga (Sun-Mercury conj): {status}")
    print(f"    {budha['reason']}")
    classical_yogas.append({"name": "Budhaditya", **budha})

    # Gajakesari
    gaja = _check_gajakesari(planets)
    status = "FORMED" if gaja["detected"] else "NOT_FORMED"
    print(f"  Gajakesari Yoga (Jupiter kendra from Moon): {status}")
    print(f"    {gaja['reason']}")
    classical_yogas.append({"name": "Gajakesari", **gaja})

    # Pancha Mahapurusha
    pms = _check_pancha_mahapurusha(planets)
    if pms:
        for pm in pms:
            print(f"  {pm['yoga']} Yoga ({pm['planet']}): FORMED")
            print(f"    {pm['reason']}")
            classical_yogas.append(pm)
    else:
        print(f"  Pancha Mahapurusha (any): NOT_FORMED")
        print(f"    No planet in own sign/exaltation in Kendra")

    # Sunapha / Anapha
    sa_results = _check_sunapha_anapha(planets)
    if sa_results:
        for sa in sa_results:
            print(f"  {sa['yoga']} Yoga: FORMED")
            print(f"    {sa['reason']}")
            classical_yogas.append(sa)
    else:
        print(f"  Sunapha/Anapha: NOT_FORMED (no planets in 2nd/12th from Moon)")

    # Hamsa
    hamsa = _check_hamsa(planets)
    status = "FORMED" if hamsa["detected"] else "NOT_FORMED"
    print(f"  Hamsa Yoga (Jupiter in kendra own/exalt): {status}")
    print(f"    {hamsa['reason']}")
    classical_yogas.append({"name": "Hamsa", **hamsa})

    # Saraswati
    sara = _check_saraswati(planets)
    status = "FORMED" if sara["detected"] else "NOT_FORMED"
    print(f"  Saraswati Yoga (J/M/V in kendra): {status}")
    print(f"    {sara['reason']}")
    classical_yogas.append({"name": "Saraswati", **sara})

    # Raja Yoga
    raja = _check_raja_yoga(planets, house_lords)
    status = "FORMED" if raja["detected"] else "NOT_FORMED"
    print(f"  Raja Yoga (Kendra-Trikona conjunct): {status}")
    print(f"    {raja['reason']}")
    classical_yogas.append({"name": "Raja", **raja})

    # Dhana
    dhana = _check_dhana_yoga(planets, house_lords)
    status = "FORMED" if dhana["detected"] else "NOT_FORMED"
    print(f"  Dhana Yoga (2nd+11th lord conjunct): {status}")
    print(f"    {dhana['reason']}")
    classical_yogas.append({"name": "Dhana", **dhana})

    # ── Section 4: Gap Analysis ──
    print()
    print("Section 4: Gap Analysis — Engine vs Classical")
    print("-" * 40)
    engine_names = {r.yoga_name for r in engine_results} if engine_results else set()
    classical_detected = [y for y in classical_yogas if y.get("detected")]

    for cy in classical_detected:
        name = cy.get("yoga", cy.get("name", "?"))
        in_engine = name in engine_names
        if in_engine:
            print(f"  {name}: Detected by engine ✓")
        else:
            print(f"  {name}: NOT detected by engine ✗ (classical: {cy.get('reason', '?')})")

    not_detected_classical = [y for y in classical_yogas if not y.get("detected")]
    if not_detected_classical:
        print()
        print("  Yogas that correctly do NOT form:")
        for cy in not_detected_classical:
            name = cy.get("yoga", cy.get("name", "?"))
            print(f"    {name}: {cy.get('reason', '?')}")

    # ── Section 5: Root Causes ──
    print()
    print("Section 5: Root Cause Analysis")
    print("-" * 40)
    print()
    print("  CAUSE 1: Engine only detects 4 classical yogas:")
    print("    - Gajakesari (Jupiter kendra from Moon)")
    print("    - Raja (Kendra lord conjunct Trikona lord)")
    print("    - Vipareeta Raja (Dusthana lord in dusthana)")
    print("    - Dhana (2nd + 11th lord conjunct)")
    print()
    print("  CAUSE 2: Missing yoga detectors:")
    missing = [y for y in classical_detected if y.get("name", y.get("yoga", "")) not in engine_names]
    if missing:
        for y in missing:
            name = y.get("yoga", y.get("name", "?"))
            print(f"    - {name}: {y.get('reason', '?')}")
    else:
        print("    (All classically detected yogas are covered by the engine)")
    print()
    print("  CAUSE 3: Mozart's chart-specific gaps:")
    print("    - Lagna: SIMHA (Leo) — Sun-owned")
    print("    - Sun in H6 (Makara) — 6th lord in dusthana (challenging for Budhaditya)")
    print("    - Jupiter in H2 (Kanya) — debilitated, not in kendra from Moon")
    print("    - No Pancha Mahapurusha (none of the 5 planets in own sign/exaltation in kendra)")
    print("    - Sunapha/Anapha: no planets in 2nd/12th from Moon (Vrishchika)")
    print()

    # ── Section 6: Event-Specific Analysis ──
    print("Section 6: Event-Specific Analysis")
    print("-" * 40)
    known_events = chart["known_events"]
    from jrs.temporal.dasha_engine import VimshottariDashaEngine

    dasha_engine = VimshottariDashaEngine()

    for event in known_events:
        event_date = event["event_date_utc"]
        domain = event["domain"]
        desc = event["description"]
        print(f"\n  Event: {event['event_id']}")
        print(f"    Date: {event_date}")
        print(f"    Domain: {domain}")
        print(f"    Description: {desc}")

        # Get dasha
        try:
            hierarchy = dasha_engine.get_dasha_hierarchy(
                birth_date_utc=chart["raw_birth_data"]["date_utc"],
                target_date_utc=event_date,
                moon_longitude_sidereal=planets["MOON"]["longitude_used"],
            )
            md = hierarchy.mahadasha_lord
            ad = hierarchy.antardasha_lord
            pd = hierarchy.pratyantardasha_lord
        except Exception as e:
            md = ad = pd = f'? ({e})'
        print(f"    Active Dasha: {md}/{ad}/{pd}")

        # Check each classical yoga for this event
        print(f"    Yoga coverage for domain={domain}:")
        for cy in classical_detected:
            name = cy.get("yoga", cy.get("name", "?"))
            involved = cy.get("planets", [])
            domain_match = domain in _get_domains_for_yoga(name)
            dasha_match = md in involved or ad in involved or pd in involved
            print(f"      {name}: planets={involved}, domain_match={domain_match}, dasha_match={dasha_match}")
            if not domain_match:
                print(f"        → FAIL: {name} domains {_get_domains_for_yoga(name)} don't include {domain}")
            if not dasha_match:
                print(f"        → FAIL: Dasha {md}/{ad}/{pd} doesn't match planets {involved}")

    return {
        "classical_yogas": classical_yogas,
        "engine_results": [r.yoga_name for r in engine_results] if engine_results else [],
        "missing_detectors": [y.get("yoga", y.get("name")) for y in classical_detected if y.get("name", y.get("yoga", "")) not in engine_names],
    }


def _get_domains_for_yoga(yoga_name: str) -> list[str]:
    """Get possible outcome domains for a yoga."""
    mapping = {
        "Budhaditya": ["INTELLECTUAL_EXCELLENCE", "COMMUNICATION_SKILLS", "BUSINESS_ACUMEN", "ADMINISTRATIVE_ABILITY"],
        "Gajakesari": ["WISDOM_ACCUMULATION", "POLITICAL_POWER", "WEALTH_ACCUMULATION", "TEACHING_ABILITY"],
        "Ruchaka": ["CAREER_PROMINENCE", "LEADERSHIP_ABILITY", "POLITICAL_POWER", "MILITARY_SUCCESS"],
        "Bhadra": ["INTELLECTUAL_EXCELLENCE", "BUSINESS_ACUMEN", "COMMUNICATION_SKILLS", "ADMINISTRATIVE_ABILITY"],
        "Hamsa": ["SPIRITUAL_ACHIEVEMENT", "WISDOM_ACCUMULATION", "TEACHING_ABILITY", "LEADERSHIP_ABILITY"],
        "Malavya": ["CAREER_PROMINENCE", "RELATIONSHIP_HARMONY", "WEALTH_ACCUMULATION", "ARTISTIC_EXCELLENCE"],
        "Sasa": ["POLITICAL_POWER", "ADMINISTRATIVE_ABILITY", "LEADERSHIP_ABILITY", "CAREER_PROMINENCE"],
        "Sunapha": ["MENTAL_STRENGTH", "EMOTIONAL_STABILITY", "WEALTH_ACCUMULATION", "PUBLIC_RECOGNITION"],
        "Anapha": ["MENTAL_STRENGTH", "WEALTH_ACCUMULATION", "HEALTH_LONGEVITY", "SPIRITUAL_ACHIEVEMENT"],
        "Durudhara": ["WEALTH_ACCUMULATION", "PUBLIC_RECOGNITION", "CAREER_PROMINENCE", "HEALTH_LONGEVITY"],
        "Raja": ["CAREER_PROMINENCE", "POLITICAL_POWER", "SOCIAL_STATUS", "LEADERSHIP_ABILITY"],
        "Dhana": ["WEALTH_ACCUMULATION", "BUSINESS_ACUMEN", "FINANCIAL_PROSPERITY", "CAREER_PROMINENCE"],
        "Vipareeta Raja": ["UNCONVENTIONAL_SUCCESS", "RECOVERY_FROM_ADVERSITY", "POLITICAL_COMEBACK", "CRISIS_MANAGEMENT"],
        "Saraswati": ["INTELLECTUAL_EXCELLENCE", "ARTISTIC_EXCELLENCE", "COMMUNICATION_SKILLS", "TEACHING_ABILITY"],
    }
    return mapping.get(yoga_name, ["CAREER_PROMINENCE", "WEALTH_ACCUMULATION"])


if __name__ == "__main__":
    result = diagnose_mozart()

    # Generate report
    report_path = REPORT_DIR / "mozart_zero_diagnosis.md"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        f.write("# Mozart Zero-Hit Diagnosis — Phase E6h Track B\n\n")
        f.write("## Executive Summary\n\n")
        f.write("W.A. Mozart (1756-01-27, Simha Lagna) produces **0/3 yoga activations** in the engine.\n")
        f.write("This diagnosis traces every classical yoga that should or shouldn't form, and identifies\n")
        f.write("the exact root causes of the engine's failure to produce relevant activations.\n\n")

        f.write("## Section 1: Mozart Chart Summary\n\n")
        f.write(f"- **Lagna**: {result['classical_yogas'][0].get('lagna', 'SIMHA')}\n")
        f.write("- **Moon**: Vrishchika (Jyeshta Nakshatra)\n")
        f.write("- **Key feature**: Sun, Mercury, Saturn in H6 (Makara) — dusthana concentration\n")
        f.write("- **Jupiter**: H2 (Kanya/Virgo) — debilitated, not in kendra from Moon\n")
        f.write("- **Venus**: H7 (Kumbha/Aquarius) — functional malefic (3rd/10th lord)\n\n")

        f.write("## Section 2: Engine Detection\n\n")
        f.write(f"Engine detects: {result['engine_results']}\n\n")
        if not result["engine_results"]:
            f.write("**The engine returns 0 yogas for Mozart.** This is because:\n")
            f.write("1. `evaluate_classical_yogas()` requires `house` data in planet facts\n")
            f.write("2. The fixture may not include `house` field (computed from rashi+lagna)\n")
            f.write("3. Even with houses, only Gajakesari and Raja have detectors\n\n")

        f.write("## Section 3: Classical Yoga Checks\n\n")
        f.write("| Yoga | Status | Reason |\n")
        f.write("|------|--------|--------|\n")
        for cy in result["classical_yogas"]:
            name = cy.get("yoga", cy.get("name", "?"))
            detected = "FORMED" if cy.get("detected") else "NOT_FORMED"
            reason = cy.get("reason", "?")
            in_engine = "✓" if name in result["engine_results"] else "✗"
            f.write(f"| {name} | {detected} | {reason} | Engine: {in_engine} |\n")

        f.write("\n## Section 4: Gap Analysis\n\n")
        f.write("### Yogas that SHOULD form but engine doesn't detect:\n\n")
        for cy in result["classical_yogas"]:
            name = cy.get("yoga", cy.get("name", "?"))
            if cy.get("detected") and name not in result["engine_results"]:
                f.write(f"- **{name}**: {cy.get('reason', '?')}\n")
        f.write("\n### Root Cause: Missing Yoga Detectors\n\n")
        f.write("The engine's `evaluate_classical_yogas()` only implements **4 yogas**:\n")
        f.write("1. Gajakesari (Jupiter kendra from Moon)\n")
        f.write("2. Raja (Kendra lord conjunct Trikona lord)\n")
        f.write("3. Vipareeta Raja (Dusthana lord in dusthana)\n")
        f.write("4. Dhana (2nd + 11th lord conjunct)\n\n")
        f.write("**Missing classical yoga detectors:**\n")
        for name in result.get("missing_detectors", []):
            f.write(f"- {name}\n")
        if not result.get("missing_detectors"):
            f.write("- (None — all classically formed yogas are covered)\n")

        f.write("\n## Section 5: Recommended Fixes\n\n")
        f.write("### Priority 1: Implement Budhaditya Detector\n")
        f.write("Sun-Mercury conjunction is common and significant. Add to `evaluate_classical_yogas()`:\n")
        f.write("```python\n")
        f.write("# Budhaditya Yoga\n")
        f.write("if sun_house == merc_house:\n")
        f.write("    # Check Mercury not combust\n")
        f.write("    if not mercury_combust:\n")
        f.write("        results.append(evaluate_formation('Budhaditya', ['SUN', 'MERCURY'], facts))\n")
        f.write("```\n\n")

        f.write("### Priority 2: Implement Pancha Mahapurusha Detector\n")
        f.write("Five yogas based on Mars/Mercury/Jupiter/Venus/Saturn in own sign in Kendra.\n\n")

        f.write("### Priority 3: Implement Sunapha/Anapha Detector\n")
        f.write("Moon-centered yogas based on planets in 2nd/12th from Moon.\n\n")

        f.write("### Priority 4: Implement Saraswati Detector\n")
        f.write("Jupiter/Mercury/Venus all in Kendras with strong Jupiter.\n\n")

        f.write("### Note on Domain Mapping\n")
        f.write("Even if all yogas were detected, the domain mapping must include ARTISTIC_EXCELLENCE\n")
        f.write("for Budhaditya, Saraswati, and Bhadra to match Mozart's CAREER events.\n")

    print(f"\nReport written to: {report_path}")
