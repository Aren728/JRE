def generate_karmic_blueprint(chart_data: dict) -> str:
    lagna = chart_data.get("lagna", "Unknown")
    moon_sign = chart_data.get("moon_sign", "Unknown")
    moon_nakshatra = chart_data.get("moon_nakshatra", "Unknown")
    nakshatra_ruler = chart_data.get("nakshatra_ruler", "Unknown")

    # ── Parihara remedies section (wired from jrs.parihara.remedy_engine) ──
    remedies_part = ""
    remedies = chart_data.get("remedies")
    if isinstance(remedies, dict) and remedies:
        lines: list[str] = ["", "# Part 5: Your Remedial Roadmap (Parihara)", ""]
        assessment = remedies.get("overall_assessment", "")
        if assessment:
            lines.append(
                f"Overall chart balance reads as **{assessment}** — these measures support "
                "the afflicted placements identified above."
            )
            lines.append("")
        afflicted = remedies.get("afflicted_planets", [])
        if afflicted:
            lines.append("## Strengthening the Afflicted Planets")
            for item in afflicted:
                planet = item.get("planet", "")
                bits = [f"- **{planet}** ({item.get('affliction', '')})"]
                if item.get("mantra"):
                    bits.append(f"Mantra: {item['mantra']}")
                if item.get("gemstone"):
                    bits.append(f"Gemstone: {item['gemstone']}")
                if item.get("temple"):
                    bits.append(f"Temple: {item['temple']}")
                lines.append(" — ".join(bits))
            lines.append("")
        doshas = remedies.get("doshas", [])
        detected = [d for d in doshas if d.get("status") == "DETECTED"]
        if detected:
            lines.append("## Doshas Detected")
            for d in detected:
                lines.append(f"- **{d.get('name', '')}** ({d.get('severity', '')}): {d.get('description', '')}")
                if d.get("remedy"):
                    lines.append(f"  - Remedy: {d['remedy']}")
            lines.append("")
        if remedies.get("disclaimer"):
            lines.append(f"> {remedies['disclaimer']}")
        remedies_part = "\n".join(lines)

    # PART 1: DYNAMIC OVERVIEW (From Knowledge Base)
    part1 = f"""# Part 1: Your Psychological & Karmic Blueprint

## 🌌 The Core Alignment: The Anchor and the Deep Ocean
Your personality is not a collection of isolated traits; it is a living, breathing ecosystem. Your outward approach to the world is governed by a {lagna} Ascendant (Lagna), meaning your conscious mind operates with sharp precision, analytical depth, and a natural instinct to organize, heal, and improve your surroundings. 

However, beneath this grounded, analytical exterior lies an incredibly vast, mystical, and complex inner world driven by your Moon in {moon_nakshatra} Nakshatra.

This creates a fascinating, powerful internal polarity:
- **The Outer Self ({lagna})**: Craves order, logic, clarity, and tangible results. You present yourself to the world as dependable, observant, and highly capable of managing chaos.
- **The Inner Self ({moon_nakshatra})**: Operates in the deep, unseen waters of the subconscious. This Nakshatra—ruled by {nakshatra_ruler}—endows you with an old-soul wisdom, a powerful intuition, and a quiet, subterranean intensity.
"""

    # PART 2: MACRO-TO-MICRO ROADMAP (Static Educational Text from KB)
    part2 = """
# Part 2: The Macro-to-Micro Roadmap (From D1 to D60)
Vedic astrology uses "Harmonic Divisional Charts" (Vargas). Imagine taking a single 30-degree sign in your main chart and slicing it under a microscope. 

| Chart | Name | Domain of Life | What it Actually Reveals |
|---|---|---|---|
| D1 | Rashi | The Physical Reality | Your physical body, external environment, and the structural "deck of cards" you have been dealt. |
| D9 | Navamsha | The Soul & Inner Marriage | The single most important sub-chart. Reveals inner subconscious alignment and true potential after age 30. |
| D60 | Shashtiamsha | The Ultimate Karmic Debt | The final word on your destiny. Maps past-life choices that created your current life's twists of fate. |
"""

    # PART 3: 3-STEP SYNTHESIS (Static Educational Text from KB)
    part3 = """
# Part 3: Connecting the Dots (The 3-Step Synthesis System)
To get an absolute grasp of your reality, you must stack these layers together.

**Step 1: The Promise (The D1 Outline)**  
Look at your main D1 chart. If a planet is placed poorly, it indicates a physical theme that will show up in your environment. It sets the boundary lines of your life.

**Step 2: The Core Capacity (The D9 Filter)**  
Check the exact same planet in your D9 Navamsha chart. If an afflicted planet from D1 becomes exalted in D9, your soul possesses the internal intelligence to master the chaos.

**Step 3: The Root Cause (The D60 Resolution)**  
Look at the same planet in your D60 chart. It reveals why you carry this specific struggle or gift from past lives.
"""

    # PART 4: LIVING INTEGRATION (Static Educational Text from KB)
    part4 = """
# Part 4: Your Living Integration Strategy
You do not need to constantly consult an astrologer. Your life itself tells you which chart is currently active:
- **D1:** When your external life changes (new job, relocation, physical illness).
- **D9:** When your inner desires shift (seeking deep intimacy, existential void).
- **D60:** When you experience unprovoked, repeating patterns (sudden betrayal, unexplained luck).

Your charts are not a sentence; they are a cosmic diagnostic map. You possess the absolute clarity needed to navigate your life with awareness, confidence, and total self-reliance.
"""

    return part1 + part2 + part3 + part4 + remedies_part
