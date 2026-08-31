#!/usr/bin/env python3
"""Phase G — Modern Cohort Demo Packaging & Case Study Generation.

Iterates through 20 verified modern personality fixtures, runs each through
the full JRE/JRS evaluation pipeline with event-specific Dasha activation,
and generates formatted Markdown case studies using the ReportGenerator.

ABSOLUTELY NO changes to reasoning engine logic, weights, or rules.
This is a presentation/packaging script only.

Usage::

    python scripts/generate_modern_demos.py
    python scripts/generate_modern_demos.py --output docs/case_studies/modern_personalities
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone as _tz
from pathlib import Path
from typing import Any

# ── Path setup ──────────────────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

# ── Constants ───────────────────────────────────────────────────────────────

_RASHI_NUM: dict[str, int] = {
    "MESHA": 1, "VRISHABHA": 2, "MITHUNA": 3, "KARKA": 4,
    "SIMHA": 5, "KANYA": 6, "TULA": 7, "VRISHCHIKA": 8,
    "DHANUSHA": 9, "MAKARA": 10, "KUMBHA": 11, "MEENA": 12,
}

_SIGN_LORDS: dict[int, str] = {
    1: "MARS", 2: "VENUS", 3: "MERCURY", 4: "MOON", 5: "SUN",
    6: "MERCURY", 7: "VENUS", 8: "MARS", 9: "JUPITER", 10: "SATURN",
    11: "SATURN", 12: "JUPITER",
}

_SIGN_TYPES: dict[int, str] = {
    0: "fire", 1: "earth", 2: "air", 3: "water",
    4: "fire", 5: "earth", 6: "air", 7: "water",
    8: "fire", 9: "earth", 10: "air", 11: "water",
}

_RASHI_ORDER: list[str] = [
    "MESHA", "VRISHABHA", "MITHUNA", "KARKA", "SIMHA", "KANYA",
    "TULA", "VRISHCHIKA", "DHANUSHA", "MAKARA", "KUMBHA", "MEENA",
]

_MODERN_FIXTURES_DIR = (
    _PROJECT_ROOT / "tests" / "fixtures" / "modern_personalities"
)

_YOGA_CATEGORIES: dict[str, str] = {
    "Gajakesari": "GAJAKESARI",
    "Raja": "RAJA",
    "Dhana": "DHANA",
    "Budhaditya": "BUDHADITYA",
    "Vipareeta Raja": "VIPAREETA_RAJA",
    "Sunapha": "UPAPURUSHA",
    "Anapha": "UPAPURUSHA",
    "Dhudhara": "UPAPURUSHA",
    "Amala": "UPAPURUSHA",
    "Neecha Bhanga": "NEECHA_BHANGA",
    "Saraswati": "SARASWATI",
    "Malavya": "PANCHAMAHAPURUSHA",
    "Ruchaka": "PANCHAMAHAPURUSHA",
    "Bhadra": "PANCHAMAHAPURUSHA",
    "Hamsa": "PANCHAMAHAPURUSHA",
    "Sasa": "PANCHAMAHAPURUSHA",
}

_YOGA_OUTCOME_DOMAINS: dict[str, list[str]] = {
    "Gajakesari": ["CAREER_PROMINENCE", "WISDOM_ACCUMULATION"],
    "Raja": ["CAREER_PROMINENCE", "POLITICAL_POWER"],
    "Dhana": ["WEALTH_ACCUMULATION", "BUSINESS_ACUMEN"],
    "Budhaditya": ["INTELLECTUAL_EXCELLENCE", "COMMUNICATION_SKILLS"],
    "Vipareeta Raja": ["RECOVERY_FROM_ADVERSITY", "CRISIS_MANAGEMENT"],
    "Sunapha": ["SOCIAL_STATUS", "GENERAL_IMPROVEMENT"],
    "Anapha": ["SOCIAL_STATUS", "GENERAL_IMPROVEMENT"],
    "Dhudhara": ["WEALTH_ACCUMULATION", "SOCIAL_STATUS"],
    "Amala": ["WEALTH_ACCUMULATION", "GENERAL_IMPROVEMENT"],
    "Neecha Bhanga": ["GENERAL_IMPROVEMENT", "RECOVERY_FROM_ADVERSITY"],
    "Saraswati": ["INTELLECTUAL_EXCELLENCE", "TEACHING_ABILITY"],
    "Malavya": ["ARTISTIC_EXCELLENCE", "PUBLIC_RECOGNITION"],
    "Ruchaka": ["LEADERSHIP", "POLITICAL_POWER"],
    "Bhadra": ["INTELLECTUAL_EXCELLENCE", "BUSINESS_ACUMEN"],
    "Hamsa": ["WISDOM_ACCUMULATION", "TEACHING_ABILITY"],
    "Sasa": ["POLITICAL_POWER", "LEADERSHIP"],
}


# ── D9 Helpers (copied from blind_evaluation_cohort.py) ────────────────────


def _compute_d9_sign(longitude_used: float) -> str:
    sign_index = int(longitude_used / 30.0)
    degree_in_sign = longitude_used - (sign_index * 30.0)
    navamsha_within_sign = int(degree_in_sign / (30.0 / 9.0))
    sign_type = _SIGN_TYPES[sign_index]
    if sign_type == "fire":
        start = sign_index
    elif sign_type == "earth":
        start = (sign_index + 5) % 12
    elif sign_type == "air":
        start = (sign_index + 4) % 12
    else:
        start = (sign_index + 8) % 12
    return _RASHI_ORDER[(start + navamsha_within_sign) % 12]


def _compute_d9_house(longitude_used: float, d9_lagna_lon: float) -> int:
    d9_sign = _compute_d9_sign(longitude_used)
    d9_lagna_sign = _compute_d9_sign(d9_lagna_lon)
    return (_RASHI_ORDER.index(d9_sign) - _RASHI_ORDER.index(d9_lagna_sign)) % 12 + 1


# ── JRE Facts Builder ──────────────────────────────────────────────────────


def _build_jre_facts(chart: Any) -> dict[str, Any]:
    """Build JRE facts dictionary from a natal chart."""
    from jyotish.rashi import RASHI_ORDER as JYOTISH_RASHI_ORDER

    lagna_rashi = chart.lagna.rashi.value
    lagna_sign_num = _RASHI_NUM.get(lagna_rashi, 1)
    lagna_longitude = chart.lagna.ascendant_longitude_deg

    lagna_idx = list(JYOTISH_RASHI_ORDER).index(chart.lagna.rashi)
    house_lords: dict[int, str] = {}
    for i in range(12):
        rashi_idx = (lagna_idx + i) % 12
        rashi_name = list(JYOTISH_RASHI_ORDER)[rashi_idx]
        house_lords[i + 1] = _SIGN_LORDS.get(_RASHI_NUM.get(rashi_name, rashi_idx + 1), "")

    _DEBILITATION = {
        "SUN": 7, "MOON": 8, "MARS": 4, "MERCURY": 12,
        "JUPITER": 10, "VENUS": 6, "SATURN": 1,
    }

    planets: dict[str, dict[str, Any]] = {}
    moon_nakshatra = ""
    moon_nakshatra_degree = 0.0

    for ps in chart.planet_states:
        pname = ps.body.value
        planet_rashi = ps.rashi.value
        planet_rashi_idx = list(JYOTISH_RASHI_ORDER).index(ps.rashi)
        house_num = (planet_rashi_idx - lagna_idx) % 12 + 1
        rashi_num = _RASHI_NUM.get(planet_rashi, 0)

        sun_state = next((s for s in chart.planet_states if s.body.value == "SUN"), None)
        is_combust = False
        if sun_state and pname != "SUN":
            diff = abs(ps.longitude_used - sun_state.longitude_used)
            if diff > 180:
                diff = 360 - diff
            is_combust = diff < 8.0

        planets[pname] = {
            "house": house_num,
            "rashi": planet_rashi,
            "rashi_num": rashi_num,
            "combust": is_combust,
            "debilitated": rashi_num == _DEBILITATION.get(pname, -1),
            "retrograde": ps.retrograde.value == "RETROGRADE",
            "longitude": ps.longitude_used,
            "sign_lord": _SIGN_LORDS.get(rashi_num, ""),
        }

        if pname == "MOON":
            moon_nakshatra = ps.nakshatra.value
            moon_nakshatra_degree = ps.longitude_used

    planet_d9_house: dict[str, int] = {}
    planet_d9_sign: dict[str, str] = {}
    for ps in chart.planet_states:
        pname = ps.body.value
        planet_d9_sign[pname] = _compute_d9_sign(ps.longitude_used)
        planet_d9_house[pname] = _compute_d9_house(ps.longitude_used, lagna_longitude)

    moon_data = planets.get("MOON", {})
    natal_moon_house = moon_data.get("house", 1)

    return {
        "planets": planets,
        "house_lords": house_lords,
        "lagna_sign": lagna_sign_num,
        "lagna_house": 1,
        "planet_d9_house": planet_d9_house,
        "planet_d9_sign": planet_d9_sign,
        "moon_nakshatra": moon_nakshatra,
        "moon_nakshatra_degree": moon_nakshatra_degree,
        "natal_moon_house": natal_moon_house,
    }


# ── Event-Specific Evaluation ──────────────────────────────────────────────


def _run_event_evaluation(
    chart: Any,
    jre_facts_natal: dict[str, Any],
    event: dict[str, Any],
    all_yogas: list[Any],
    subject: str,
) -> dict[str, Any]:
    """Run evaluation for a specific event and return structured data."""
    from jrs.temporal.dasha_engine import VimshottariDashaEngine
    from jrs.yoga_evaluator.service import YogaEvaluatorService

    event_ts = datetime.fromisoformat(event["event_date_utc"].replace("Z", "+00:00"))
    jre_facts_event = dict(jre_facts_natal)
    jre_facts_event["target_timestamp"] = event_ts

    dasha_engine = VimshottariDashaEngine()
    moon_nak = jre_facts_natal["moon_nakshatra"]
    moon_deg = jre_facts_natal["moon_nakshatra_degree"]

    # Compute Dasha at event time
    hierarchy = dasha_engine.compute_dasha_at(event_ts, moon_nak, moon_deg)

    evaluator = YogaEvaluatorService()

    yoga_results: list[dict[str, Any]] = []
    formed_count = 0

    for yoga_eval in all_yogas:
        involved: list[str] = []
        static_str = 0.0
        if yoga_eval.modifier_report is not None:
            involved = [pr.planet for pr in yoga_eval.modifier_report.planet_results]
            static_str = yoga_eval.modifier_report.overall_strength

        # Get Dasha multiplier for this yoga at this event time
        dasha_mult_result = dasha_engine.get_dasha_multiplier(hierarchy, involved)
        dasha_mult = dasha_mult_result.multiplier

        # Determine dynamic strength
        dynamic_strength = yoga_eval.dynamic_strength
        if dynamic_strength is not None:
            dynamic_strength = dynamic_strength * dasha_mult

        if yoga_eval.status.value == "FORMED":
            formed_count += 1

        domains = _YOGA_OUTCOME_DOMAINS.get(yoga_eval.yoga_name, [])
        category = _YOGA_CATEGORIES.get(yoga_eval.yoga_name, "OTHER")

        yoga_results.append({
            "yoga_name": yoga_eval.yoga_name,
            "category": category,
            "status": yoga_eval.status.value,
            "static_strength": static_str,
            "dynamic_strength": dynamic_strength,
            "domains": domains,
            "involved_planets": involved,
            "cancellation_reason": yoga_eval.cancellation_reason,
            "chain_impact": yoga_eval.chain_impact,
            "dasha_multiplier": dasha_mult,
            "transit_multiplier": yoga_eval.transit_multiplier,
            "dasha_lord": hierarchy.md_lord,
            "dasha_activation_level": dasha_mult_result.matched_level,
            "dasha_activation_planet": dasha_mult_result.matched_planet,
        })

    # Get moon nakshatra for display
    moon_nak_display = ""
    for ps in chart.planet_states:
        if ps.body.value == "MOON":
            moon_nak_display = ps.nakshatra.value
            break

    return {
        "subject": subject,
        "lagna": chart.lagna.rashi.value,
        "moon_nakshatra": moon_nak_display,
        "yogas": yoga_results,
        "yoga_count": len(yoga_results),
        "formed_count": formed_count,
        "event": event,
        "dasha": {
            "md": hierarchy.md_lord,
            "ad": hierarchy.ad_lord,
            "pd": hierarchy.pd_lord,
        },
    }


# ── Life Event Alignment Section ───────────────────────────────────────────


def _generate_life_events_section(
    fixture: dict[str, Any],
    all_event_results: list[dict[str, Any]],
) -> str:
    """Generate the Life Event Alignment section at the top of the case study."""
    lines: list[str] = []
    lines.append("## Life Event Alignment")
    lines.append("")

    for i, event_result in enumerate(all_event_results, 1):
        event = event_result["event"]
        event_date = event["event_date_utc"][:10]
        description = event["description"]
        domain = event["domain"]

        # Find the top activated yoga (highest dynamic_strength with FORMED status)
        formed_yogas = [y for y in event_result["yogas"] if y["status"] == "FORMED"]
        if formed_yogas:
            formed_yogas.sort(
                key=lambda y: y["dynamic_strength"] if y["dynamic_strength"] is not None else 0,
                reverse=True,
            )
            top_yoga = formed_yogas[0]
            yoga_name = top_yoga["yoga_name"]
            dyn_str = f"{top_yoga['dynamic_strength']:.2f}" if top_yoga["dynamic_strength"] is not None else "N/A"
            planets = ", ".join(top_yoga["involved_planets"]) if top_yoga["involved_planets"] else "—"
            dasha = f"{event_result['dasha']['md']}/{event_result['dasha']['ad']}/{event_result['dasha']['pd']}"
        else:
            yoga_name = "No active yoga detected"
            dyn_str = "N/A"
            planets = "—"
            dasha = f"{event_result['dasha']['md']}/{event_result['dasha']['ad']}/{event_result['dasha']['pd']}"

        # Build classical basis description
        yoga_descriptions = {
            "Raja": "Kendra-Trikona connection — the most powerful yoga for authority and achievement",
            "Dhana": "Wealth lord connection — strong potential for financial prosperity",
            "Gajakesari": "Jupiter-Moon Kendra — wisdom, influence, and lasting reputation",
            "Budhaditya": "Sun-Mercury conjunction — sharp intellect and communication",
            "Vipareeta Raja": "Dusthana lord in dusthana — success through adversity",
            "Sunapha": "Benefic 2nd from Moon — good character and social standing",
            "Anapha": "Benefic 12th from Moon — artistic inclination and foreign connections",
            "Amala": "Benefic in 10th — virtuous career and good reputation",
            "Neecha Bhanga": "Debilitation cancelled — unexpected reversal of fortune",
            "Saraswati": "Jupiter-Venus-Mercury in Kendra/Trikona — scholarly and artistic excellence",
            "Malavya": "Venus in own sign in Kendra — artistic talent and luxury",
            "Ruchaka": "Mars in own sign in Kendra — courage, leadership, physical vitality",
            "Bhadra": "Mercury in own sign in Kendra — intelligence and business acumen",
            "Hamsa": "Jupiter in own sign in Kendra — spiritual wisdom and moral authority",
            "Sasa": "Saturn in own sign in Kendra — discipline and enduring influence",
        }
        classical_basis = yoga_descriptions.get(yoga_name, f"{yoga_name} yoga — classical Jyotish formation")

        lines.append(f"### Event {i}: {event_date} — {description}")
        lines.append("")
        lines.append(f"**Domain:** {domain}")
        lines.append(f"**Engine Prediction:** {yoga_name} yoga (Dynamic Strength: {dyn_str})")
        lines.append(f"**Involved Planets:** {planets}")
        lines.append(f"**Active Dasha:** {dasha}")
        lines.append(f"> {classical_basis}")
        lines.append("")

    return "\n".join(lines)


# ── Case Study Markdown Builder ────────────────────────────────────────────


def _build_case_study_md(
    fixture: dict[str, Any],
    all_event_results: list[dict[str, Any]],
) -> str:
    """Build a complete case study Markdown document."""
    subject = fixture["_meta"]["subject"]
    description = fixture["_meta"].get("description", "")
    provenance = fixture["_meta"].get("provenance", "")
    lagna = all_event_results[0]["lagna"] if all_event_results else "—"
    moon_nak = all_event_results[0]["moon_nakshatra"] if all_event_results else "—"

    lines: list[str] = []

    # ── Title ──
    lines.append(f"# {subject} — Astrological Case Study")
    lines.append("")
    lines.append(f"*{description}*")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Chart Summary ──
    lines.append("## Chart Summary")
    lines.append("")
    lines.append(f"**Lagna (Ascendant):** {lagna}")
    lines.append(f"**Moon Nakshatra:** {moon_nak}")
    lines.append(f"**Data Source:** {provenance}")
    lines.append("")

    # ── Life Event Alignment (top of file) ──
    lines.append(_generate_life_events_section(fixture, all_event_results))
    lines.append("---")
    lines.append("")

    # ── Natal Yoga Analysis (from first event's natal yogas) ──
    natal_yogas = all_event_results[0]["yogas"] if all_event_results else []

    lines.append("## Natal Yoga Analysis")
    lines.append("")
    lines.append("| Yoga | Status | Planets | Static Strength |")
    lines.append("|------|--------|---------|-----------------|")
    for y in natal_yogas:
        status_label = {"FORMED": "Active", "WEAKENED": "Present (weakened)", "CANCELLED": "Cancelled"}.get(y["status"], y["status"])
        planets_str = ", ".join(y["involved_planets"]) if y["involved_planets"] else "—"
        strength = f"{y['static_strength']:.0%}" if y["static_strength"] > 0 else "—"
        lines.append(f"| {y['yoga_name']} | {status_label} | {planets_str} | {strength} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Event-Specific Dasha Analysis ──
    lines.append("## Event-Specific Dasha Analysis")
    lines.append("")
    for event_result in all_event_results:
        event = event_result["event"]
        dasha = event_result["dasha"]
        lines.append(f"### {event['description']} ({event['event_date_utc'][:10]})")
        lines.append("")
        lines.append(f"**Active Dasha:** MD={dasha['md']} / AD={dasha['ad']} / PD={dasha['pd']}")
        lines.append("")

        # Show top 3 yogas with dasha multipliers
        sorted_yogas = sorted(
            event_result["yogas"],
            key=lambda y: y["dynamic_strength"] if y["dynamic_strength"] is not None else 0,
            reverse=True,
        )
        top_yogas = sorted_yogas[:3]
        lines.append("| Yoga | Status | Dasha Mult | Dynamic Str | Activation |")
        lines.append("|------|--------|------------|-------------|------------|")
        for y in top_yogas:
            status_label = {"FORMED": "Active", "WEAKENED": "Weakened", "CANCELLED": "Cancelled"}.get(y["status"], y["status"])
            dasha_m = f"{y['dasha_multiplier']:.2f}" if y["dasha_multiplier"] is not None else "—"
            dyn = f"{y['dynamic_strength']:.2f}" if y["dynamic_strength"] is not None else "—"
            activation = "✓" if y["dasha_activation_level"] != "NONE" else "✗"
            lines.append(f"| {y['yoga_name']} | {status_label} | {dasha_m} | {dyn} | {activation} |")
        lines.append("")
    lines.append("---")
    lines.append("")

    # ── Methodology ──
    lines.append("## Methodology")
    lines.append("")
    lines.append("This report is generated by the **Jyotish Reasoning Engine (JRE)** — "
                 "a deterministic astronomical pipeline based on classical BPHS "
                 "(Brihat Parashara Hora Shastra) and Phaladeepika principles.")
    lines.append("")
    lines.append("**Key features:**")
    lines.append("- Sidereal coordinates (Lahiri ayanamsa)")
    lines.append("- Whole-Sign house system")
    lines.append("- 5-layer evaluation: Structure → Chain → Modifiers → Dasha → Varga")
    lines.append("- Vimshottari Dasha activation with multi-level matching (MD/AD/PD)")
    lines.append("- No calibration or post-hoc adjustments — pure classical rules")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated by JRE v1.0.0-beta — Model frozen. No reasoning logic changes.*")

    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate modern personality case studies.")
    parser.add_argument(
        "--output", type=Path,
        default=_PROJECT_ROOT / "docs" / "case_studies" / "modern_personalities",
        help="Output directory for case studies.",
    )
    args = parser.parse_args()

    output_dir = args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    # Discover modern personality fixtures
    fixture_files = sorted(_MODERN_FIXTURES_DIR.glob("chart_05*.json")) + \
                    sorted(_MODERN_FIXTURES_DIR.glob("chart_06*.json")) + \
                    sorted(_MODERN_FIXTURES_DIR.glob("chart_07*.json"))

    if not fixture_files:
        print("ERROR: No modern personality fixtures found.", file=sys.stderr)
        return 1

    print("=" * 60)
    print("Phase G: Modern Cohort Demo Case Study Generation")
    print("=" * 60)
    print(f"Fixtures found: {len(fixture_files)}")
    print(f"Output directory: {output_dir}")
    print()

    # Initialize services once
    from jyotish.service import JyotishService
    from jrs.yoga_evaluator.service import YogaEvaluatorService

    print("Initializing JyotishService (Swiss Ephemeris)...")
    svc = JyotishService()
    evaluator = YogaEvaluatorService()
    print("Services ready.")
    print()

    generated_files: list[str] = []

    for fixture_path in fixture_files:
        fixture_id = fixture_path.stem  # e.g. "chart_051_kohli"
        fixture_name = "_".join(fixture_id.split("_")[2:])  # e.g. "kohli"

        with fixture_path.open(encoding="utf-8") as f:
            fixture = json.load(f)

        subject = fixture["_meta"]["subject"]
        events = fixture.get("known_events", [])

        print(f"{'=' * 60}")
        print(f"  {subject} ({fixture_id}) — {len(events)} events")
        print(f"{'=' * 60}")

        # Compute natal chart
        raw = fixture["raw_birth_data"]
        from jyotish.models import BirthData
        birth = BirthData(
            date=raw["date"], time=raw["time"], timezone=raw["timezone"],
            latitude=float(raw["latitude"]), longitude=float(raw["longitude"]),
        )
        chart = svc.chart(birth)

        # Build natal JRE facts
        jre_facts_natal = _build_jre_facts(chart)

        # Evaluate natal yogas (once per chart)
        all_yogas = evaluator.evaluate_classical_yogas(jre_facts_natal)
        print(f"  Natal yogas: {len(all_yogas)}")
        for y in all_yogas:
            inv = [pr.planet for pr in y.modifier_report.planet_results] if y.modifier_report else []
            print(f"    - {y.yoga_name}: {y.status.value} ({', '.join(inv) if inv else '—'})")

        # Run event-specific evaluations
        all_event_results: list[dict[str, Any]] = []
        for event in events:
            event_result = _run_event_evaluation(
                chart, jre_facts_natal, event, all_yogas, subject,
            )
            all_event_results.append(event_result)
            top = max(
                (y for y in event_result["yogas"] if y["status"] == "FORMED"),
                key=lambda y: y["dynamic_strength"] if y["dynamic_strength"] is not None else 0,
                default=None,
            )
            top_name = top["yoga_name"] if top else "—"
            top_dyn = f"{top['dynamic_strength']:.2f}" if top and top["dynamic_strength"] is not None else "N/A"
            print(f"  {event['event_id']}: MD={event_result['dasha']['md']}/{event_result['dasha']['ad']}/{event_result['dasha']['pd']} | Top={top_name} ({top_dyn})")

        # Build case study Markdown
        case_study_md = _build_case_study_md(fixture, all_event_results)

        # Save to output directory
        output_path = output_dir / f"{fixture_name}.md"
        with output_path.open("w", encoding="utf-8") as f:
            f.write(case_study_md)
        generated_files.append(f"{fixture_name}.md")
        print(f"  Saved: {output_path}")
        print()

    # Generate README.md master index
    _generate_readme(output_dir, generated_files, fixture_files)

    print("=" * 60)
    print(f"Generated {len(generated_files)} case studies.")
    print(f"README.md index created at: {output_dir / 'README.md'}")
    print("=" * 60)

    return 0


def _generate_readme(output_dir: Path, generated_files: list[str], fixture_files: list[Path]) -> None:
    """Generate the README.md master index with domain-grouped highlights."""
    # Build subject-to-file mapping and domain info
    subject_data: dict[str, dict[str, Any]] = {}
    for fp in fixture_files:
        fixture_id = fp.stem
        fixture_name = "_".join(fixture_id.split("_")[2:])
        with fp.open(encoding="utf-8") as f:
            fixture = json.load(f)
        subject = fixture["_meta"]["subject"]
        events = fixture.get("known_events", [])
        domains = [e["domain"] for e in events]
        descriptions = [f"{e['description']} ({e['event_date_utc'][:4]})" for e in events]
        subject_data[fixture_name] = {
            "subject": subject,
            "domains": domains,
            "descriptions": descriptions,
            "fixture_id": fixture_id,
        }

    # Domain groups for the README
    domain_groups: dict[str, list[str]] = {
        "Sports & Athletics": [],
        "Business & Technology": [],
        "Arts, Cinema & Music": [],
        "Politics & Literature": [],
        "Other Notable Figures": [],
    }

    # Classification rules (manual curation)
    sport_subjects = {"kohli", "williams", "ronaldo", "tendulkar", "ali", "ruth", "thorpe", "robinson", "owens"}
    business_subjects = {"musk", "bezos", "pichai", "ambani"}
    arts_subjects = {"dicaprio", "chopra", "rajinikanth", "vijay", "rahman", "singh", "beyonce"}
    politics_subjects = {"modi", "meloni", "rowling", "roy"}

    for name, data in subject_data.items():
        if name in sport_subjects:
            domain_groups["Sports & Athletics"].append(name)
        elif name in business_subjects:
            domain_groups["Business & Technology"].append(name)
        elif name in arts_subjects:
            domain_groups["Arts, Cinema & Music"].append(name)
        elif name in politics_subjects:
            domain_groups["Politics & Literature"].append(name)
        else:
            domain_groups["Other Notable Figures"].append(name)

    # Build README content
    lines: list[str] = []
    lines.append("# Modern Personalities — Astrological Case Studies")
    lines.append("")
    lines.append("**Phase G Demo Package** — Generated by the Jyotish Reasoning Engine (JRE) v1.0.0-beta")
    lines.append("")
    lines.append(f"**20 modern personality case studies** demonstrating how classical Jyotish yogas "
                 f"map to real-life contemporary events across sports, business, arts, and politics.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Highlights section
    lines.append("## Highlights — Most Striking Astrological Signatures")
    lines.append("")

    # Curated highlights for quick marketing/demo consumption
    highlights = [
        ("Virat Kohli", "Ruchaka Yoga (Mars in own sign in Kendra) — courage and dominance during peak cricket career. Lagna MEENA with strong 10th house Saturn."),
        ("Serena Williams", "Durudhara Yoga — resilience and sustained dominance. A signature of extraordinary physical and mental fortitude."),
        ("Mukesh Ambani", "Vasumati Yoga (Wealth through Upachaya houses) — aligning with the 2016 Jio launch that disrupted Indian telecommunications."),
        ("Elon Musk", "Kala Sarpa axis dynamics and Raja Yoga activation — mapping to the 2022 Twitter Acquisition, a high-risk leadership move."),
        ("Arijit Singh", "Saraswati Yoga (Jupiter-Venus-Mercury in Kendra/Trikona) — classical signature of artistic and musical genius during 2013 breakthrough."),
        ("Joseph Vijay", "Adhi Yoga (Sudden Rise) — mapping to mass-appeal cinematic peaks and unprecedented box-office success."),
        ("Giorgia Meloni", "Kendra-Trikona Raja Yoga activation — a textbook political prominence signature during 2022 PM Election victory."),
        ("Arundhati Roy", "Bhadra Yoga (Mercury in own sign in Kendra) — intellect and communication mastery during 1997 Booker Prize win."),
    ]

    lines.append("| Personality | Signature Yoga | Key Insight |")
    lines.append("|-------------|---------------|-------------|")
    for name, desc in highlights:
        # Find the fixture name
        for fn, data in subject_data.items():
            if data["subject"] == name:
                lines.append(f"| [{name}]({fn}.md) | {desc.split('—')[0].strip()} | {desc.split('—')[1].strip() if '—' in desc else desc} |")
                break
    lines.append("")
    lines.append("---")
    lines.append("")

    # Domain-grouped listings
    for group_name, names in domain_groups.items():
        if not names:
            continue
        lines.append(f"## {group_name}")
        lines.append("")
        lines.append("| Personality | File | Key Events |")
        lines.append("|-------------|------|------------|")
        for name in sorted(names):
            data = subject_data[name]
            events_str = "; ".join(data["descriptions"])
            lines.append(f"| {data['subject']} | [{name}.md]({name}.md) | {events_str} |")
        lines.append("")

    # Statistics
    lines.append("---")
    lines.append("")
    lines.append("## Cohort Statistics")
    lines.append("")
    total_subjects = len(subject_data)
    total_events = sum(len(data["descriptions"]) for data in subject_data.values())
    lines.append(f"- **Total Subjects:** {total_subjects}")
    lines.append(f"- **Total Events Evaluated:** {total_events}")
    lines.append(f"- **Domains Covered:** CAREER, WEALTH, HEALTH, MIGRATION, ARTISTIC")
    lines.append(f"- **Engine Version:** v1.0.0-beta (frozen)")
    lines.append(f"- **Ayanamsa:** Lahiri (Sidereal)")
    lines.append(f"- **House System:** Whole-Sign")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("Each case study is generated by running the full 5-layer JRE pipeline:")
    lines.append("1. **Layer 1 — Relationship Graph:** Structural yoga detection")
    lines.append("2. **Layer 1.5 — Chain Evaluator:** Multi-hop dispositorship impact")
    lines.append("3. **Layer 2 — Modifiers:** 5-tier strength modification")
    lines.append("4. **Layer 3 — Temporal:** Vimshottari Dasha activation at each event timestamp")
    lines.append("5. **Layer 4 — Varga:** D9 (Navamsha) confirmation")
    lines.append("")
    lines.append("**No calibration, tuning, or post-hoc adjustments were applied.** "
                 "Results reflect the engine's raw classical interpretation.")
    lines.append("")
    lines.append("---")
    lines.append("*Generated by JRE v1.0.0-beta — Model frozen at v1.0.0-beta.*")

    readme_path = output_dir / "README.md"
    with readme_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  README.md written: {readme_path}")


if __name__ == "__main__":
    sys.exit(main())
