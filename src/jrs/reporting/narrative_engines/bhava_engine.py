"""JRE Reporting — Bhava Narrative Engine.

Deep, classical analysis of all 12 houses (Bhavas). For each house,
synthesizes the house lord's dignity, occupying planets, conjunctions,
aspecting planets, and karakas into professional astrological prose.

NO engine logic — pure narrative generation from existing facts.
"""

from __future__ import annotations

from typing import Any

# ══════════════════════════════════════════════════════════════════════════════
# House Data Definitions
# ══════════════════════════════════════════════════════════════════════════════

_BHAVA_DATA: dict[int, dict[str, Any]] = {
    1: {
        "name": "Lagna (Ascendant)",
        "domain": "Physical Constitution, Personality & Self",
        "signifies": (
            "Body, appearance, temperament, vitality, general health, "
            "childhood environment, overall life direction, and self-expression"
        ),
        "karakas": ["Sun", "Mars"],
        "nature": "Kendra & Trikona",
        "element": "Fire (initiative)",
    },
    2: {
        "name": "Dhana Bhava",
        "domain": "Wealth, Family & Speech",
        "signifies": (
            "Accumulated wealth, family lineage, food, speech, early education, "
            "jewelry, right eye, moral values, and financial capacity"
        ),
        "karakas": ["Jupiter", "Mercury"],
        "nature": "Maraka",
        "element": "Earth (accumulation)",
    },
    3: {
        "name": "Sahaja Bhava",
        "domain": "Courage, Siblings & Communication",
        "signifies": (
            "Younger siblings, courage, self-effort, short journeys, "
            "communication, writing, arms, and entrepreneurial ability"
        ),
        "karakas": ["Mars", "Mercury"],
        "nature": "Upachaya",
        "element": "Air (expression)",
    },
    4: {
        "name": "Sukha Bhava",
        "domain": "Home, Happiness & Mother",
        "signifies": (
            "Mother, home, property, land, vehicles, education, emotional "
            "peace, chest, comforts, and ancestral heritage"
        ),
        "karakas": ["Moon", "Mercury"],
        "nature": "Kendra & Moksha",
        "element": "Earth (stability)",
    },
    5: {
        "name": "Putra Bhava",
        "domain": "Children, Intelligence & Past Merit",
        "signifies": (
            "Children, creative intelligence, romance, speculation, "
            "education, past life merit (Purva Punya), stomach, and counseling"
        ),
        "karakas": ["Jupiter", "Sun"],
        "nature": "Trikona",
        "element": "Fire (creativity)",
    },
    6: {
        "name": "Ripu Bhava",
        "domain": "Enemies, Disease & Service",
        "signifies": (
            "Enemies, diseases, debts, legal disputes, service, "
            "maternal uncle, daily routine, and competitive ability"
        ),
        "karakas": ["Mars", "Saturn"],
        "nature": "Dusthana & Upachaya",
        "element": "Earth (conflict)",
    },
    7: {
        "name": "Kalatra Bhava",
        "domain": "Marriage, Partnership & Public",
        "signifies": (
            "Spouse, business partnerships, public dealings, sexual organs, "
            "travel, diplomacy, and legal contracts"
        ),
        "karakas": ["Venus", "Mercury"],
        "nature": "Kendra & Maraka",
        "element": "Air (relationship)",
    },
    8: {
        "name": "Ayur Bhava",
        "domain": "Longevity, Obstacles & Transformation",
        "signifies": (
            "Longevity, obstacles, hidden matters, inheritance, insurance, "
            "occult sciences, chronic disease, spouse's wealth, and surgery"
        ),
        "karakas": ["Saturn", "Mars"],
        "nature": "Dusthana & Moksha",
        "element": "Water (transformation)",
    },
    9: {
        "name": "Dharma Bhava",
        "domain": "Fortune, Philosophy & Father",
        "signifies": (
            "Father, fortune, religion, philosophy, higher learning, "
            "long-distance travel, pilgrimage, and spiritual wisdom"
        ),
        "karakas": ["Jupiter", "Sun"],
        "nature": "Trikona & Dharma",
        "element": "Fire (wisdom)",
    },
    10: {
        "name": "Karma Bhava",
        "domain": "Career, Status & Authority",
        "signifies": (
            "Career, profession, reputation, authority, government, "
            "social status, karma, knees, and worldly achievements"
        ),
        "karakas": ["Saturn", "Sun"],
        "nature": "Kendra & Kendradhipati",
        "element": "Air (achievement)",
    },
    11: {
        "name": "Labha Bhava",
        "domain": "Gains, Income & Aspirations",
        "signifies": (
            "Income, gains, fulfillment of desires, elder siblings, "
            "friends, community, left ear, and social networks"
        ),
        "karakas": ["Jupiter", "Mercury"],
        "nature": "Upachaya & Trishadaya",
        "element": "Air (networks)",
    },
    12: {
        "name": "Vyaya Bhava",
        "domain": "Losses, Liberation & Foreign Lands",
        "signifies": (
            "Expenses, losses, foreign lands, sleep, dreams, moksha "
            "(liberation), left eye, hospitalization, and spiritual detachment"
        ),
        "karakas": ["Saturn", "Ketu"],
        "nature": "Dusthana & Moksha",
        "element": "Water (dissolution)",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# Narrative Templates
# ══════════════════════════════════════════════════════════════════════════════

_DIGNITY_TEXT: dict[str, str] = {
    "Exalted": "operating at peak strength with exceptional blessings",
    "Moolatrikona": "deeply comfortable and functionally powerful",
    "Own Sign": "naturally strong and self-sufficient",
    "Friendly": "well-placed and cooperative",
    "Neutral": "moderate and context-dependent",
    "Enemy": "placed in a hostile environment with potential friction",
    "Debilitated": "significantly weakened, requiring supportive conditions",
}

_ASPECT_GENERIC: dict[str, str] = {
    "MARS": "Mars's dynamic and protective energy creates an assertive influence",
    "JUPITER": "Jupiter's expansive and benevolent wisdom brings protective blessings",
    "SATURN": "Saturn's disciplining and structuring force adds karmic weight and endurance",
    "VENUS": "Venus's harmonious and aesthetic influence softens and beautifies",
    "MERCURY": "Mercury's analytical and communicative intelligence adds intellectual sharpness",
    "SUN": "Sun's authoritative and illuminating presence commands attention",
    "MOON": "Moon's emotional and intuitive sensitivity creates a nurturing influence",
}


class BhavaNarrativeEngine:
    """Generates deep, classical narratives for all 12 Bhavas."""

    def __init__(self, jre_facts: dict[str, Any]) -> None:
        self.facts = jre_facts
        self.planets = jre_facts.get("planets", {})
        self.house_lords = jre_facts.get("house_lords", {})
        self.dignity_map = jre_facts.get("dignity_map", {})
        self.aspects = jre_facts.get("drishti_matrix", [])
        self.shadbala = jre_facts.get("shadbala", {})
        self.av = jre_facts.get("ashtakavarga", {})

    def generate_all_bhavas(self) -> list[dict[str, Any]]:
        """Generate narratives for all 12 bhavas.

        Returns:
            List of bhava analysis dicts with house number, title,
            narrative text, strength assessment, and key indicators.
        """
        results: list[dict[str, Any]] = []

        for house_num in range(1, 13):
            analysis = self._analyze_bhava(house_num)
            if analysis:
                results.append(analysis)

        return results

    def _analyze_bhava(self, house_num: int) -> dict[str, Any]:
        """Analyze a single bhava in depth."""
        bhava = _BHAVA_DATA.get(house_num)
        if not bhava:
            return {}

        # 1. House Lord analysis
        lord_planet = self.house_lords.get(house_num, "")
        lord_data = self.planets.get(lord_planet, {})
        lord_house = lord_data.get("house", 0)
        lord_dignity = self.dignity_map.get(lord_planet, "Neutral")
        lord_shadbala = self.shadbala.get(lord_planet, {}).get("total_rupas", 30)

        # 2. Occupying planets
        occupants: list[dict[str, Any]] = []
        for pname, pdata in self.planets.items():
            if pname in ("RAHU", "KETU"):
                continue
            if pdata.get("house") == house_num:
                occupants.append(
                    {
                        "name": pname,
                        "dignity": self.dignity_map.get(pname, "Neutral"),
                        "retrograde": pdata.get("retrograde", False),
                        "combust": pdata.get("combust", False),
                        "shadbala": self.shadbala.get(pname, {}).get("total_rupas", 30),
                    }
                )

        # 3. Aspecting planets
        aspected_by: list[dict[str, Any]] = []
        for asp in self.aspects:
            if asp.get("target_house") == house_num:
                aspected_by.append(
                    {
                        "name": asp["source"],
                        "aspect_type": asp.get("aspect_type", ""),
                    }
                )

        # 4. Ashtakavarga score
        sav_score = self.av.get("sav", {}).get(house_num, 0)

        # 5. Generate narrative
        narrative = self._build_narrative(
            house_num,
            bhava,
            lord_planet,
            lord_dignity,
            lord_house,
            lord_shadbala,
            occupants,
            aspected_by,
            sav_score,
        )

        return {
            "house": house_num,
            "name": bhava["name"],
            "domain": bhava["domain"],
            "signifies": bhava["signifies"],
            "nature": bhava["nature"],
            "lord": lord_planet,
            "lord_dignity": lord_dignity,
            "lord_house": lord_house,
            "lord_shadbala": lord_shadbala,
            "occupants": occupants,
            "aspected_by": aspected_by,
            "sav_score": sav_score,
            "narrative": narrative,
        }

    def _build_narrative(
        self,
        house_num: int,
        bhava: dict[str, Any],
        lord_planet: str,
        lord_dignity: str,
        lord_house: int,
        lord_shadbala: float,
        occupants: list[dict[str, Any]],
        aspected_by: list[dict[str, Any]],
        sav_score: int,
    ) -> str:
        """Build the classical narrative for a single bhava."""
        paragraphs: list[str] = []

        # Opening — house significance
        paragraphs.append(
            f"The {_ordinal(house_num)} house ({bhava['name']}) governs "
            f"{bhava['signifies'].lower()}."
        )

        # House Lord placement
        if lord_planet:
            dignity_text = _DIGNITY_TEXT.get(lord_dignity, "in a neutral state")
            if lord_house == house_num:
                paragraphs.append(
                    f"The house lord {lord_planet} occupies its own house, "
                    f"{dignity_text}. This is a strong placement indicating "
                    f"natural expressiveness of this bhava's significations."
                )
            elif lord_house > 0:
                paragraphs.append(
                    f"The house lord {lord_planet} is placed in the "
                    f"{_ordinal(lord_house)} house, {dignity_text}. "
                    f"This directs the bhava's energies toward the domain "
                    f"of the {_ordinal(lord_house)} house."
                )
                # Check if lord is in a dusthana (6, 8, 12)
                if lord_house in (6, 8, 12):
                    paragraphs.append(
                        f"Placement of the house lord in a dusthana house "
                        f"({_ordinal(lord_house)}) can indicate challenges "
                        f"in this bhava's domain, though it may also "
                        f"create Vipareeta Raja Yoga patterns."
                    )
                elif lord_house in (1, 4, 7, 10):
                    paragraphs.append(
                        f"Placement in a Kendra house ({_ordinal(lord_house)}) "
                        f"strengthens the bhava's expression through angular "
                        f"dynamism."
                    )
                elif lord_house in (5, 9):
                    paragraphs.append(
                        f"Placement in a Trikona house ({_ordinal(lord_house)}) "
                        f"blesses this bhava with Dharma and fortune."
                    )

        # Occupying planets
        if occupants:
            occ_names = [o["name"] for o in occupants]
            if len(occupants) == 1:
                occ = occupants[0]
                occ_dignity = _DIGNITY_TEXT.get(occ["dignity"], "in a neutral state")
                retro_note = " (retrograde)" if occ["retrograde"] else ""
                combust_note = " (combust)" if occ["combust"] else ""
                paragraphs.append(
                    f"{occ['name']} occupies this house, {occ_dignity}"
                    f"{retro_note}{combust_note}. Its natural karaka "
                    f"significations blend with the bhava's domain, "
                    f"creating a focused expression of energy."
                )
            else:
                paragraphs.append(
                    f"The conjunction of {', '.join(occ_names)} in this house "
                    f"creates a complex interplay of planetary energies. "
                    f"The combined influence shapes how the bhava's "
                    f"significations manifest in the native's life."
                )
        else:
            lord_name = lord_planet if lord_planet else "its ruling planet"
            paragraphs.append(
                f"This house is unoccupied. The condition of its ruling "
                f"planet ({lord_name}) will determine the outcomes of "
                f"this domain."
            )

        # Aspects
        if aspected_by:
            asp_names = [a["name"] for a in aspected_by]
            paragraphs.append(
                f"This house receives aspects from {', '.join(asp_names)}. "
                f"Each aspecting planet modifies the bhava's expression "
                f"according to its natural nature and functional relationship "
                f"with the house lord."
            )

        # Ashtakavarga
        if sav_score > 0:
            if sav_score >= 30:
                av_assessment = "indicating strong supportive energy"
            elif sav_score >= 25:
                av_assessment = "indicating moderate supportive energy"
            elif sav_score >= 20:
                av_assessment = "indicating average supportive energy"
            else:
                av_assessment = "indicating limited supportive energy, requiring conscious effort"
            paragraphs.append(
                f"The Ashtakavarga score for this house is {sav_score} bindus, {av_assessment}."
            )

        # Karakas
        karakas = bhava.get("karakas", [])
        if karakas:
            paragraphs.append(
                f"The natural karakas (significators) for this house are "
                f"{', '.join(karakas)}. Their placement and dignity in the "
                f"chart further modify the bhava's expression."
            )

        return " ".join(paragraphs)


def _ordinal(n: int) -> str:
    """Convert integer to ordinal string."""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"
