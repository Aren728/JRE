"""Synthesizes chart parameters into structured Markdown output.

This module formats calculated alignment, planet, and dasha objects
into a complete Markdown blueprint report.
"""

from typing import Any


def generate_synthesis_report(core_alignment: Any, planets: list[Any], dasha: Any) -> str:
    """Format calculated data objects into a complete Markdown report.

    Args:
        core_alignment: CoreAlignment model instance.
        planets: List of PlanetAnalysis model instances.
        dasha: DashaPeriod model instance.

    Returns:
        Markdown string representing the synthesis blueprint.
    """
    md = []
    md.append("### Part 1: Your Psychological & Karmic Blueprint\n")
    md.append(
        f"#### 🌌 Core Alignment: {core_alignment.ascendant_sign} "
        f"Ascendant & {core_alignment.moon_nakshatra} Moon\n"
    )
    md.append(f"{core_alignment.psychological_summary}\n\n")

    md.append("---\n")
    md.append("### Part 2: Macro-to-Micro Varga Matrix (D1, D9, D60)\n")
    md.append("| Planet | D1 Rashi | D9 Navamsha | D60 Shashtiamsha | Functional Role |\n")
    md.append("| :--- | :--- | :--- | :--- | :--- |\n")

    for p in planets:
        md.append(
            f"| **{p.planet_name}** | "
            f"{p.d1.sign} (H{p.d1.house}) | "
            f"{p.d9.sign} (H{p.d9.house}) | "
            f"{p.d60.sign if p.d60 else 'N/A'} | "
            f"{p.functional_role} |\n"
        )

    md.append(
        f"\n**Active Dasha Period:** "
        f"{dasha.mahadasha} - {dasha.antardasha} "
        f"(until {dasha.end_date})"
    )

    return "".join(md)
