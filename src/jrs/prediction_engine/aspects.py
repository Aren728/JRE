"""Aspect Matrix (Drishti) Engine — Vedic planetary aspects & special aspects.

Two categories of aspects are computed:

  1. **HOUSE ASPECTS (Bhava Drishti)** — Every planet aspects specific houses
     from its position, regardless of whether another planet occupies that house.
     ALL planets aspect the 7th house. Mars additionally aspects 4th and 8th.
     Jupiter additionally aspects 5th and 9th. Saturn additionally aspects
     3rd and 10th. Rahu/Ketu additionally aspect 5th and 9th.

  2. **PLANETARY ASPECTS (Graha Drishti)** — When a planet occupies a house
     that is aspected by another planet, that creates a direct planetary
     aspect between the two planets.

Conjunctions (Yuti) are NOT aspects and are NOT included here.

Reference: BPHS Ch 44, Phaladeepika Ch 18.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── Sign order (zodiacal, Mesha = 0) ─────────────────────────────────────────

SIGN_ORDER: tuple[str, ...] = (
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

# ── Special aspect rules (planet → extra houses aspected) ────────────────────
# The universal 7th aspect is NOT listed here — every planet has it.

SPECIAL_ASPECTS: dict[str, tuple[int, ...]] = {
    "MARS": (4, 8),
    "JUPITER": (5, 9),
    "SATURN": (3, 10),
    "RAHU": (5, 9),
    "KETU": (5, 9),
}

# ── House names for display ──────────────────────────────────────────────────

HOUSE_NAMES: dict[int, str] = {
    1: "Self / Identity",
    2: "Wealth / Family",
    3: "Courage / Siblings",
    4: "Home / Mother",
    5: "Creativity / Children",
    6: "Enemies / Disease",
    7: "Partnerships / Marriage",
    8: "Transformation / Longevity",
    9: "Fortune / Dharma",
    10: "Career / Status",
    11: "Gains / Aspirations",
    12: "Losses / Liberation",
}


# ── Data structures ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AspectEntry:
    """A single aspect — either HOUSE_ASPECT or PLANET_ASPECT.

    Attributes:
        aspect_category: "HOUSE_ASPECT" (Bhava Drishti) or "PLANET_ASPECT" (Graha Drishti).
        aspecter: The planet casting the aspect.
        aspected: The planet receiving the aspect (empty string for HOUSE_ASPECT).
        aspect_type: '7th', '4th', '5th', '8th', '9th', '3rd', '10th'.
        source_house: House the aspecter occupies (from Lagna).
        target_house: House being aspected.
        strength: Aspect strength (0.0 – 1.0).
        is_conjunction: Always False (conjunctions are not aspects).
        narrative: Human-readable explanation.
    """

    aspect_category: str
    aspecter: str
    aspected: str
    aspect_type: str
    source_house: int
    target_house: int
    strength: float
    is_conjunction: bool  # Always False
    narrative: str

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "aspect_category": self.aspect_category,
            "aspecter": self.aspecter,
            "aspected": self.aspected,
            "aspect_type": self.aspect_type,
            "source_house": self.source_house,
            "target_house": self.target_house,
            "strength": round(self.strength, 4),
            "is_conjunction": False,
            "narrative": self.narrative,
        }
        return d


@dataclass(frozen=True)
class PlanetAspectSummary:
    """Summary of all aspects received by a single planet."""

    planet: str
    total_aspects: int
    strongest_aspecter: str
    strongest_strength: float
    aspects: tuple[AspectEntry, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "planet": self.planet,
            "total_aspects": self.total_aspects,
            "strongest_aspecter": self.strongest_aspecter,
            "strongest_strength": round(self.strongest_strength, 4),
            "aspects": [a.to_dict() for a in self.aspects],
        }


@dataclass(frozen=True)
class AspectMatrixResult:
    """Complete aspect matrix for all planets."""

    all_aspects: tuple[AspectEntry, ...]
    planet_summaries: tuple[PlanetAspectSummary, ...]
    total_aspects: int
    exact_aspects: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "all_aspects": [a.to_dict() for a in self.all_aspects],
            "planet_summaries": [s.to_dict() for s in self.planet_summaries],
            "total_aspects": self.total_aspects,
            "exact_aspects": self.exact_aspects,
        }


# ── Engine ───────────────────────────────────────────────────────────────────


class AspectMatrixEngine:
    """Compute the full Vedic aspect matrix: House Aspects + Planetary Aspects."""

    ALL_PLANETS: tuple[str, ...] = (
        "SUN",
        "MOON",
        "MARS",
        "MERCURY",
        "JUPITER",
        "VENUS",
        "SATURN",
        "RAHU",
        "KETU",
    )

    def compute(
        self,
        planet_signs: dict[str, str],
        lagna: str,
        varga: str = "D1",
    ) -> AspectMatrixResult:
        """Compute the full aspect matrix.

        Args:
            planet_signs: Mapping of planet → sign name.
            lagna: Lagna sign name.
            varga: Divisional chart type (D1, D9, D10, etc.) for labeling.

        Returns:
            AspectMatrixResult with house aspects, planetary aspects, and summaries.
        """
        # Step 1: Calculate which house each planet is in (relative to Lagna)
        planet_houses: dict[str, int] = {}
        lagna_idx = SIGN_ORDER.index(lagna) if lagna in SIGN_ORDER else 0

        for planet in self.ALL_PLANETS:
            if planet in planet_signs:
                sign = planet_signs[planet]
                sign_idx = SIGN_ORDER.index(sign) if sign in SIGN_ORDER else 0
                house = ((sign_idx - lagna_idx) % 12) + 1
                planet_houses[planet] = house

        # Step 2: Build reverse mapping: house → list of planets in that house
        house_planets: dict[int, list[str]] = {}
        for planet, house in planet_houses.items():
            if house not in house_planets:
                house_planets[house] = []
            house_planets[house].append(planet)

        # Step 3: Generate all aspect entries
        all_entries: list[AspectEntry] = []
        house_aspect_count = 0
        planet_aspect_count = 0

        for aspecter in self.ALL_PLANETS:
            if aspecter not in planet_houses:
                continue

            source_house = planet_houses[aspecter]
            aspect_types = self._get_aspect_types(aspecter)

            for aspect_offset in aspect_types:
                target_house = ((source_house + aspect_offset - 1) % 12) + 1
                target_planets = house_planets.get(target_house, [])
                type_label = self._aspect_type_label(aspect_offset)
                house_name = HOUSE_NAMES.get(target_house, "")

                # Always generate a HOUSE_ASPECT entry
                house_narrative = (
                    f"{aspecter} from House {source_house} {type_label} "
                    f"House {target_house}" + (f" ({house_name})" if house_name else "")
                )
                all_entries.append(
                    AspectEntry(
                        aspect_category="HOUSE_ASPECT",
                        aspecter=aspecter,
                        aspected="",
                        aspect_type=f"{aspect_offset}th",
                        source_house=source_house,
                        target_house=target_house,
                        strength=0.9 if aspect_offset == 7 else 0.75,
                        is_conjunction=False,
                        narrative=house_narrative,
                    )
                )
                house_aspect_count += 1

                # If planets occupy the target house, also generate PLANET_ASPECT entries
                for aspected in target_planets:
                    if aspected == aspecter:
                        continue

                    planet_narrative = (
                        f"{aspecter} from House {source_house} {type_label} "
                        f"{aspected} in House {target_house}"
                    )
                    all_entries.append(
                        AspectEntry(
                            aspect_category="PLANET_ASPECT",
                            aspecter=aspecter,
                            aspected=aspected,
                            aspect_type=f"{aspect_offset}th",
                            source_house=source_house,
                            target_house=target_house,
                            strength=0.9 if aspect_offset == 7 else 0.75,
                            is_conjunction=False,
                            narrative=planet_narrative,
                        )
                    )
                    planet_aspect_count += 1

        # Sort: PLANET_ASPECT first (by strength desc), then HOUSE_ASPECT (by source_house asc)
        all_entries.sort(
            key=lambda e: (
                0 if e.aspect_category == "PLANET_ASPECT" else 1,
                -e.strength if e.aspect_category == "PLANET_ASPECT" else e.source_house,
            )
        )

        # Build per-planet summaries (only from PLANET_ASPECT entries)
        planet_aspects = [e for e in all_entries if e.aspect_category == "PLANET_ASPECT"]
        summaries = self._build_summaries(planet_aspects)

        exact_count = sum(1 for e in all_entries if e.strength >= 0.9)

        print(
            f"ASPECT ENGINE DEBUG: Calculated {house_aspect_count} House Aspects "
            f"and {planet_aspect_count} Planetary Aspects "
            f"({len(all_entries)} total aspects) for {varga} chart."
        )

        return AspectMatrixResult(
            all_aspects=tuple(all_entries),
            planet_summaries=tuple(summaries),
            total_aspects=len(all_entries),
            exact_aspects=exact_count,
        )

    @staticmethod
    def _aspect_type_label(offset: int) -> str:
        """Human-readable label for the aspect type."""
        labels: dict[int, str] = {
            3: "gives special 3rd aspect to",
            4: "gives special 4th aspect to",
            5: "gives special 5th aspect to",
            7: "aspects",
            8: "gives special 8th aspect to",
            9: "gives special 9th aspect to",
            10: "gives special 10th aspect to",
        }
        return labels.get(offset, f"gives {offset}th aspect to")

    @staticmethod
    def _get_aspect_types(planet: str) -> list[int]:
        """Return all house offsets this planet aspects."""
        base = [7]  # Universal 7th aspect
        if planet in SPECIAL_ASPECTS:
            base.extend(SPECIAL_ASPECTS[planet])
        return base

    def _build_summaries(
        self,
        planet_aspects: list[AspectEntry],
    ) -> list[PlanetAspectSummary]:
        """Build per-planet summaries for PLANET_ASPECT entries received."""
        summaries: list[PlanetAspectSummary] = []
        for planet in self.ALL_PLANETS:
            received = [a for a in planet_aspects if a.aspected == planet]
            if not received:
                summaries.append(
                    PlanetAspectSummary(
                        planet=planet,
                        total_aspects=0,
                        strongest_aspecter="",
                        strongest_strength=0.0,
                        aspects=(),
                    )
                )
                continue
            strongest = max(received, key=lambda a: a.strength)
            summaries.append(
                PlanetAspectSummary(
                    planet=planet,
                    total_aspects=len(received),
                    strongest_aspecter=strongest.aspecter,
                    strongest_strength=strongest.strength,
                    aspects=tuple(received),
                )
            )
        return summaries


# ── Gochar (Transit) Aspects ────────────────────────────────────────────────


def compute_gochar_aspects(
    transit_positions: dict[str, str],
    natal_positions: dict[str, str],
    natal_lagna: str,
) -> AspectMatrixResult:
    """Compute Gochar (Transit) aspects — how transiting planets aspect natal houses and planets.

    Args:
        transit_positions: Current transit positions {planet: sign}.
        natal_positions: Natal chart positions {planet: sign}.
        natal_lagna: Natal Lagna sign.

    Returns:
        AspectMatrixResult with transit-to-natal aspects.
    """
    engine = AspectMatrixEngine()
    all_entries: list[AspectEntry] = []

    lagna_idx = SIGN_ORDER.index(natal_lagna) if natal_lagna in SIGN_ORDER else 0

    # Build house positions for natal planets
    natal_houses: dict[str, int] = {}
    for planet, sign in natal_positions.items():
        if sign in SIGN_ORDER:
            sign_idx = SIGN_ORDER.index(sign)
            natal_houses[planet] = ((sign_idx - lagna_idx) % 12) + 1

    # For each transiting planet, check aspects to natal houses and planets
    for t_planet, t_sign in transit_positions.items():
        if t_sign not in SIGN_ORDER:
            continue
        t_idx = SIGN_ORDER.index(t_sign)
        t_house = ((t_idx - lagna_idx) % 12) + 1

        # Get aspect types for this transiting planet
        aspect_types = engine._get_aspect_types(t_planet)

        for aspect_offset in aspect_types:
            target_house = ((t_house + aspect_offset - 1) % 12) + 1
            type_label = engine._aspect_type_label(aspect_offset)

            # House aspect
            house_narrative = (
                f"Transit {t_planet} from House {t_house} {type_label} House {target_house} (Natal)"
            )
            all_entries.append(
                AspectEntry(
                    aspect_category="HOUSE_ASPECT",
                    aspecter=f"Transit {t_planet}",
                    aspected="",
                    aspect_type=f"{aspect_offset}th",
                    source_house=t_house,
                    target_house=target_house,
                    strength=0.9 if aspect_offset == 7 else 0.75,
                    is_conjunction=False,
                    narrative=house_narrative,
                )
            )

            # Check if any natal planet is in the target house
            for n_planet, n_house in natal_houses.items():
                if n_house == target_house:
                    planet_narrative = (
                        f"Transit {t_planet} from House {t_house} {type_label} "
                        f"Natal {n_planet} in House {target_house}"
                    )
                    all_entries.append(
                        AspectEntry(
                            aspect_category="PLANET_ASPECT",
                            aspecter=f"Transit {t_planet}",
                            aspected=f"Natal {n_planet}",
                            aspect_type=f"{aspect_offset}th",
                            source_house=t_house,
                            target_house=target_house,
                            strength=0.9 if aspect_offset == 7 else 0.75,
                            is_conjunction=False,
                            narrative=planet_narrative,
                        )
                    )

    all_entries.sort(
        key=lambda e: (
            0 if e.aspect_category == "PLANET_ASPECT" else 1,
            -e.strength if e.aspect_category == "PLANET_ASPECT" else e.source_house,
        )
    )

    planet_aspects = [e for e in all_entries if e.aspect_category == "PLANET_ASPECT"]
    summaries = engine._build_summaries(planet_aspects)
    exact_count = sum(1 for e in all_entries if e.strength >= 0.9)

    print(f"GOCHAR ASPECTS DEBUG: Calculated {len(all_entries)} transit-to-natal aspects.")

    return AspectMatrixResult(
        all_aspects=tuple(all_entries),
        planet_summaries=tuple(summaries),
        total_aspects=len(all_entries),
        exact_aspects=exact_count,
    )
