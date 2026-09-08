"""Advanced Parivartana Yoga Engine — CosmicEngine Gold Standard.

Detects and classifies Parivartana (mutual exchange) yogas with full
psychological synthesis across four analytical layers:

  1. **Rasi Parivartana Analysis** — External Reality layer.
     Classifies exchanges as Maha (auspicious), Dainya (affliction),
     or Khala (volatility) based on house ownership involvement.

  2. **Nakshatra Parivartana Analysis** — Subconscious Mind layer.
     Detects mutual Nakshatra lord exchanges ("Subconscious Gateway Active")
     and evaluates Sarvatobhadra Vedha (structural friction / breakthrough).

  3. **Inter-Aspect Modifications** — Overriding Triggers layer.
     Checks if Jupiter purifies or if Rahu/Saturn/Ketu interfere with
     exchanging planets via their special aspects.

  4. **Final Synthesis** — Conclusive psychological and practical guidance.

Reference: BPHS Ch 26-27, Phaladeepika Ch 19, Sarvatobhadra Chakra texts.
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

# ── Natural sign lords ───────────────────────────────────────────────────────

SIGN_LORDS: dict[str, str] = {
    "MESHA": "MARS",
    "VRISHABHA": "VENUS",
    "MITHUNA": "MERCURY",
    "KARKA": "MOON",
    "SIMHA": "SUN",
    "KANYA": "MERCURY",
    "TULA": "VENUS",
    "VRISHCHIKA": "MARS",
    "DHANUSHA": "JUPITER",
    "MAKARA": "SATURN",
    "KUMBHA": "SATURN",
    "MEENA": "JUPITER",
}

# ── Exaltation / Debilitation signs ──────────────────────────────────────────

EXALTED_SIGN: dict[str, str] = {
    "SUN": "MESHA",
    "MOON": "VRISHABHA",
    "MARS": "MAKARA",
    "MERCURY": "KANYA",
    "JUPITER": "KARKA",
    "VENUS": "MEENA",
    "SATURN": "TULA",
}

DEBILITATED_SIGN: dict[str, str] = {
    "SUN": "TULA",
    "MOON": "VRISHCHIKA",
    "MARS": "KARKA",
    "MERCURY": "MEENA",
    "JUPITER": "MAKARA",
    "VENUS": "KANYA",
    "SATURN": "MESHA",
}

# ── Friendly / Enemy maps ────────────────────────────────────────────────────

_FRIENDLY: dict[str, frozenset[str]] = {
    "SUN": frozenset({"MOON", "MARS", "JUPITER"}),
    "MOON": frozenset({"SUN", "MERCURY"}),
    "MARS": frozenset({"SUN", "MOON", "JUPITER"}),
    "MERCURY": frozenset({"SUN", "VENUS"}),
    "JUPITER": frozenset({"SUN", "MOON", "MARS"}),
    "VENUS": frozenset({"MERCURY", "SATURN"}),
    "SATURN": frozenset({"MERCURY", "VENUS"}),
}

# ── House categories ─────────────────────────────────────────────────────────

MAHA_HOUSES: frozenset[int] = frozenset({1, 2, 4, 5, 7, 9, 10, 11})
KENDRA_HOUSES: frozenset[int] = frozenset({1, 4, 7, 10})
TRIKONA_HOUSES: frozenset[int] = frozenset({1, 5, 9})
DUSTHANA_HOUSES: frozenset[int] = frozenset({6, 8, 12})
KENDRA_TRIKONA: frozenset[int] = KENDRA_HOUSES | TRIKONA_HOUSES
UPACHAYA_HOUSES: frozenset[int] = frozenset({3, 6, 10, 11})

# ── Nakshatra constants ─────────────────────────────────────────────────────

NAKSHATRA_ORDER: tuple[str, ...] = (
    "ASHWINI",
    "BHARANI",
    "KRITTIKA",
    "ROHINI",
    "MRIGASHIRA",
    "ARDRA",
    "PUNARVASU",
    "PUSHA",
    "ASHLESHA",
    "MAGHA",
    "PURVA_PHALGUNI",
    "UTTARA_PHALGUNI",
    "HASTA",
    "CHITRA",
    "SWATI",
    "VISHAKHA",
    "ANURADHA",
    "JYESHTHA",
    "MULA",
    "PURVA_ASHADHA",
    "UTTARA_ASHADHA",
    "SHRAVANA",
    "DHANISHTA",
    "SHATABHISHA",
    "PURVA_BHADRAPADA",
    "UTTARA_BHADRAPADA",
    "REVATI",
)

NAKSHATRA_NAMES: dict[str, str] = {
    "ASHWINI": "Ashwini",
    "BHARANI": "Bharani",
    "KRITTIKA": "Krittika",
    "ROHINI": "Rohini",
    "MRIGASHIRA": "Mrigashira",
    "ARDRA": "Ardra",
    "PUNARVASU": "Punarvasu",
    "PUSHA": "Pushya",
    "ASHLESHA": "Ashlesha",
    "MAGHA": "Magha",
    "PURVA_PHALGUNI": "Purva Phalguni",
    "UTTARA_PHALGUNI": "Uttara Phalguni",
    "HASTA": "Hasta",
    "CHITRA": "Chitra",
    "SWATI": "Swati",
    "VISHAKHA": "Vishakha",
    "ANURADHA": "Anuradha",
    "JYESHTHA": "Jyeshtha",
    "MULA": "Mula",
    "PURVA_ASHADHA": "Purva Ashadha",
    "UTTARA_ASHADHA": "Uttara Ashadha",
    "SHRAVANA": "Shravana",
    "DHANISHTA": "Dhanishta",
    "SHATABHISHA": "Shatabhisha",
    "PURVA_BHADRAPADA": "Purva Bhadrapada",
    "UTTARA_BHADRAPADA": "Uttara Bhadrapada",
    "REVATI": "Revati",
}

NAKSHATRA_LORDS: dict[str, str] = {
    "ASHWINI": "Ketu",
    "BHARANI": "Venus",
    "KRITTIKA": "Sun",
    "ROHINI": "Moon",
    "MRIGASHIRA": "Mars",
    "ARDRA": "Rahu",
    "PUNARVASU": "Jupiter",
    "PUSHA": "Saturn",
    "ASHLESHA": "Mercury",
    "MAGHA": "Ketu",
    "PURVA_PHALGUNI": "Venus",
    "UTTARA_PHALGUNI": "Sun",
    "HASTA": "Moon",
    "CHITRA": "Mars",
    "SWATI": "Rahu",
    "VISHAKHA": "Jupiter",
    "ANURADHA": "Saturn",
    "JYESHTHA": "Mercury",
    "MULA": "Ketu",
    "PURVA_ASHADHA": "Venus",
    "UTTARA_ASHADHA": "Sun",
    "SHRAVANA": "Moon",
    "DHANISHTA": "Mars",
    "SHATABHISHA": "Rahu",
    "PURVA_BHADRAPADA": "Jupiter",
    "UTTARA_BHADRAPADA": "Saturn",
    "REVATI": "Mercury",
}

# ── Sarvatobhadra Vedha (Piercing) Lookup ───────────────────────────────────
# Key: (aspecting_nakshatra, aspected_nakshatra) → True if Vedha exists.
# These represent the classical "piercing" lines on the Sarvatobhadra Chakra
# that create structural friction or sudden breakthrough patterns.
# Reference: Sarvatobhadra Chakra traditional text.

SARVATOBHADRA_VEDHA: set[tuple[str, str]] = {
    ("ASHWINI", "ROHINI"),
    ("ASHWINI", "JYESHTHA"),
    ("ASHWINI", "REVATI"),
    ("BHARANI", "MRIGASHIRA"),
    ("BHARANI", "SWATI"),
    ("BHARANI", "PURVA_BHADRAPADA"),
    ("KRITTIKA", "ARDRA"),
    ("KRITTIKA", "VISHAKHA"),
    ("KRITTIKA", "UTTARA_BHADRAPADA"),
    ("ROHINI", "ASHWINI"),
    ("ROHINI", "ASHLESHA"),
    ("ROHINI", "REVATI"),
    ("MRIGASHIRA", "BHARANI"),
    ("MRIGASHIRA", "MAGHA"),
    ("MRIGASHIRA", "REVATI"),
    ("ARDRA", "KRITTIKA"),
    ("ARDRA", "PURVA_PHALGUNI"),
    ("ARDRA", "UTTARA_BHADRAPADA"),
    ("PUNARVASU", "UTTARA_PHALGUNI"),
    ("PUNARVASU", "HASTA"),
    ("PUNARVASU", "SHATABHISHA"),
    ("PUSHA", "CHITRA"),
    ("PUSHA", "SWATI"),
    ("PUSHA", "PURVA_BHADRAPADA"),
    ("ASHLESHA", "ROHINI"),
    ("ASHLESHA", "JYESHTHA"),
    ("ASHLESHA", "UTTARA_BHADRAPADA"),
    ("MAGHA", "MRIGASHIRA"),
    ("MAGHA", "SWATI"),
    ("MAGHA", "UTTARA_ASHADHA"),
    ("PURVA_PHALGUNI", "ARDRA"),
    ("PURVA_PHALGUNI", "VISHAKHA"),
    ("PURVA_PHALGUNI", "PURVA_BHADRAPADA"),
    ("UTTARA_PHALGUNI", "PUNARVASU"),
    ("UTTARA_PHALGUNI", "ANURADHA"),
    ("UTTARA_PHALGUNI", "SHATABHISHA"),
    ("HASTA", "PUNARVASU"),
    ("HASTA", "JYESHTHA"),
    ("HASTA", "UTTARA_ASHADHA"),
    ("CHITRA", "PUSHA"),
    ("CHITRA", "MULA"),
    ("CHITRA", "UTTARA_BHADRAPADA"),
    ("SWATI", "BHARANI"),
    ("SWATI", "MAGHA"),
    ("SWATI", "UTTARA_BHADRAPADA"),
    ("VISHAKHA", "KRITTIKA"),
    ("VISHAKHA", "PURVA_PHALGUNI"),
    ("VISHAKHA", "REVATI"),
    ("ANURADHA", "UTTARA_PHALGUNI"),
    ("ANURADHA", "DHANISHTA"),
    ("ANURADHA", "UTTARA_ASHADHA"),
    ("JYESHTHA", "ASHWINI"),
    ("JYESHTHA", "HASTA"),
    ("JYESHTHA", "PURVA_BHADRAPADA"),
    ("MULA", "CHITRA"),
    ("MULA", "SHRAVANA"),
    ("MULA", "UTTARA_BHADRAPADA"),
    ("PURVA_ASHADHA", "MAGHA"),
    ("PURVA_ASHADHA", "DHANISHTA"),
    ("PURVA_ASHADHA", "UTTARA_ASHADHA"),
    ("UTTARA_ASHADHA", "MAGHA"),
    ("UTTARA_ASHADHA", "ANURADHA"),
    ("UTTARA_ASHADHA", "SHRAVANA"),
    ("SHRAVANA", "MULA"),
    ("SHRAVANA", "PURVA_ASHADHA"),
    ("SHRAVANA", "REVATI"),
    ("DHANISHTA", "ANURADHA"),
    ("DHANISHTA", "SHATABHISHA"),
    ("DHANISHTA", "REVATI"),
    ("SHATABHISHA", "PUNARVASU"),
    ("SHATABHISHA", "MULA"),
    ("SHATABHISHA", "UTTARA_ASHADHA"),
    ("PURVA_BHADRAPADA", "BHARANI"),
    ("PURVA_BHADRAPADA", "ASHLESHA"),
    ("PURVA_BHADRAPADA", "PURVA_PHALGUNI"),
    ("UTTARA_BHADRAPADA", "KRITTIKA"),
    ("UTTARA_BHADRAPADA", "ASHLESHA"),
    ("UTTARA_BHADRAPADA", "SWATI"),
    ("REVATI", "ASHWINI"),
    ("REVATI", "MRIGASHIRA"),
    ("REVATI", "SHRAVANA"),
}

# ── Planet special aspect offsets (0-indexed from7) ──────────────────────────
# Jupiter aspects +4, +8; Mars aspects +3, +7; Saturn aspects +2, +9
# Rahu and Ketu: 7th aspect only (offset 0)

SPECIAL_ASPECT_OFFSETS: dict[str, tuple[int, ...]] = {
    "JUPITER": (4, 8),
    "MARS": (3, 7),
    "SATURN": (2, 9),
}


# ── Data structures ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ParivartanaPair:
    """One detected mutual exchange between two planets."""

    planet_a: str
    sign_a: str
    planet_b: str
    sign_b: str
    exchange_type: str
    house_a: int
    house_b: int
    strength: float
    neecha_bhanga: bool
    narrative: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "planet_a": self.planet_a,
            "sign_a": self.sign_a,
            "planet_b": self.planet_b,
            "sign_b": self.sign_b,
            "exchange_type": self.exchange_type,
            "house_a": self.house_a,
            "house_b": self.house_b,
            "strength": round(self.strength, 4),
            "neecha_bhanga": self.neecha_bhanga,
            "narrative": self.narrative,
        }


@dataclass(frozen=True)
class ParivartanaResult:
    """Aggregated result of Parivartana detection."""

    pairs: tuple[ParivartanaPair, ...]
    total_exchanges: int
    has_maha: bool
    has_dainya: bool
    parivartana_synthesis: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pairs": [p.to_dict() for p in self.pairs],
            "total_exchanges": self.total_exchanges,
            "has_maha": self.has_maha,
            "has_dainya": self.has_dainya,
            "parivartana_synthesis": self.parivartana_synthesis,
        }


# ── Engine ───────────────────────────────────────────────────────────────────


class ParivartanaEngine:
    """Advanced Parivartana engine — CosmicEngine Gold Standard.

    Processes Rasi exchanges, Nakshatra exchanges, Sarvatobhadra Vedha,
    and Inter-Aspect modifications to produce a 4-part psychological synthesis.
    """

    def detect(
        self,
        planet_signs: dict[str, str],
        lagna: str,
        dignity_map: dict[str, str] | None = None,
        planet_details: dict[str, dict[str, Any]] | None = None,
        aspect_entries: list[dict[str, Any]] | None = None,
    ) -> ParivartanaResult:
        """Detect all Parivartana Yogas and generate 4-part synthesis.

        Args:
            planet_signs: Mapping of planet → sign (e.g., {"SUN": "MESHA"}).
            lagna: Lagna sign name.
            dignity_map: Optional planet → dignity label mapping.
            planet_details: Optional planet detail dicts with longitude info.
            aspect_entries: Optional full aspect matrix entries for Inter-Aspect.

        Returns:
            ParivartanaResult with pairs and parivartana_synthesis.
        """
        lagna_idx = self._sign_index(lagna)
        dignity_map = dignity_map or {}
        planet_details = planet_details or {}
        aspect_entries = aspect_entries or []

        # Filter to classical planets only (exclude Rahu/Ketu)
        classical = [p for p in planet_signs if p not in ("RAHU", "KETU")]

        seen: set[tuple[str, str]] = set()
        pairs: list[ParivartanaPair] = []

        for i, p_a in enumerate(classical):
            sign_a = planet_signs[p_a].upper()
            lord_a = SIGN_LORDS.get(sign_a, "")
            for p_b in classical:
                if p_b == p_a:
                    continue
                sign_b = planet_signs[p_b].upper()
                lord_b = SIGN_LORDS.get(sign_b, "")

                # Mutual exchange: A in B's sign AND B in A's sign
                if lord_a == p_b and lord_b == p_a:
                    pair_key = tuple(sorted([p_a, p_b]))
                    if pair_key in seen:
                        continue
                    seen.add(pair_key)

                    house_a = self._house_from_lagna(sign_a, lagna_idx)
                    house_b = self._house_from_lagna(sign_b, lagna_idx)

                    exchange_type = self._classify_exchange(house_a, house_b)
                    neecha = self._check_neecha_bhanga(
                        p_a,
                        sign_a,
                        p_b,
                        sign_b,
                        dignity_map,
                    )
                    strength = self._compute_strength(
                        p_a,
                        sign_a,
                        house_a,
                        p_a in dignity_map and dignity_map[p_a],
                        p_b,
                        sign_b,
                        house_b,
                        p_b in dignity_map and dignity_map[p_b],
                        neecha,
                    )
                    narrative = self._build_narrative(
                        p_a,
                        sign_a,
                        house_a,
                        p_b,
                        sign_b,
                        house_b,
                        exchange_type,
                        neecha,
                        strength,
                    )

                    pairs.append(
                        ParivartanaPair(
                            planet_a=p_a,
                            sign_a=sign_a,
                            planet_b=p_b,
                            sign_b=sign_b,
                            exchange_type=exchange_type,
                            house_a=house_a,
                            house_b=house_b,
                            strength=round(strength, 4),
                            neecha_bhanga=neecha,
                            narrative=narrative,
                        )
                    )

        pairs.sort(key=lambda p: -p.strength)
        has_maha = any(p.exchange_type == "MAHA" for p in pairs)
        has_dainya = any(p.exchange_type == "DAINYA" for p in pairs)

        # ── Step 2: Nakshatra Parivartana ────────────────────────────────────
        nak_exchanges = self._detect_nakshatra_parivartana(planet_details, lagna)

        # ── Step 3: Sarvatobhadra Vedha ──────────────────────────────────────
        vedha_flags = self._detect_vedha(planet_details)

        # ── Step 4: Inter-Aspect Modifications ───────────────────────────────
        inter_aspects = self._detect_inter_aspect_modifications(
            pairs,
            planet_signs,
            lagna,
            aspect_entries,
        )

        # ── Step 5: Generate 4-part Synthesis ────────────────────────────────
        synthesis = self._generate_synthesis(
            pairs,
            nak_exchanges,
            vedha_flags,
            inter_aspects,
            planet_signs,
            lagna,
            dignity_map,
        )

        return ParivartanaResult(
            pairs=tuple(pairs),
            total_exchanges=len(pairs),
            has_maha=has_maha,
            has_dainya=has_dainya,
            parivartana_synthesis=synthesis,
        )

    # ── Rasi Classification ──────────────────────────────────────────────────

    @staticmethod
    def _classify_exchange(house_a: int, house_b: int) -> str:
        """Classify the Rasi exchange type per CosmicEngine spec.

        Maha (Auspicious): Both houses in {1,2,4,5,7,9,10,11}
        Dainya (Affliction): Either house in {6,8,12}
        Khala (Volatility): Either house == 3
        """
        a_dust = house_a in DUSTHANA_HOUSES
        b_dust = house_b in DUSTHANA_HOUSES

        # Dainya takes precedence — any Dusthana involvement
        if a_dust or b_dust:
            return "DAINYA"

        # Khala — 3rd house involvement
        if house_a == 3 or house_b == 3:
            return "KHALA"

        # Maha — both in Kendra/Trikona (houses 1,2,4,5,7,9,10,11)
        if house_a in MAHA_HOUSES and house_b in MAHA_HOUSES:
            return "MAHA"

        return "ORDINARY"

    # ── Strength scoring ─────────────────────────────────────────────────────

    @staticmethod
    def _compute_strength(
        p_a: str,
        sign_a: str,
        house_a: int,
        dign_a: str | bool,
        p_b: str,
        sign_b: str,
        house_b: int,
        dign_b: str | bool,
        neecha_bhanga: bool,
    ) -> float:
        """Compute Parivartana strength (0.0 – 1.0)."""
        score = 0.5

        # Both in own sign (strongest exchange)
        if dign_a == "Own Sign" and dign_b == "Own Sign":
            score += 0.25
        elif dign_a == "Own Sign" or dign_b == "Own Sign":
            score += 0.12

        # One planet exalted
        if dign_a == "Exalted" or dign_b == "Exalted":
            score += 0.15

        # One planet debilitated
        if dign_a == "Debilitated" or dign_b == "Debilitated":
            score -= 0.20

        # Planets in Kendra from each other
        diff = abs(house_a - house_b)
        if diff in (0, 3, 6, 9):
            score += 0.10

        # Neecha-bhanga bonus
        if neecha_bhanga:
            score += 0.15

        return max(0.0, min(1.0, score))

    @staticmethod
    def _check_neecha_bhanga(
        p_a: str,
        sign_a: str,
        p_b: str,
        sign_b: str,
        dignity_map: dict[str, str],
    ) -> bool:
        """Check if either planet's debilitation is cancelled by the exchange."""
        d_a = dignity_map.get(p_a, "")
        d_b = dignity_map.get(p_b, "")

        if d_a == "Debilitated":
            exalt_sign = EXALTED_SIGN.get(p_a, "")
            if sign_b == exalt_sign:
                return True
        if d_b == "Debilitated":
            exalt_sign = EXALTED_SIGN.get(p_b, "")
            if sign_a == exalt_sign:
                return True

        # Exchange itself cancels debilitation
        if d_a == "Debilitated" and sign_a in DEBILITATED_SIGN.values():
            return True
        if d_b == "Debilitated" and sign_b in DEBILITATED_SIGN.values():
            return True

        return False

    # ── Nakshatra Parivartana ────────────────────────────────────────────────

    def _detect_nakshatra_parivartana(
        self,
        planet_details: dict[str, dict[str, Any]],
        lagna: str,
    ) -> list[dict[str, str]]:
        """Detect mutual Nakshatra lord exchanges.

        A Nakshatra exchange occurs when Planet A is in a Nakshatra lorded
        by Planet B, AND Planet B is in a Nakshatra lorded by Planet A.

        Returns list of dicts with planet_a, planet_b, nakshatra_a, nakshatra_b,
        lord_a, lord_b, and the tag "Subconscious Gateway Active".
        """
        exchanges: list[dict[str, str]] = []

        # Compute Nakshatra for each planet
        planet_naks: dict[str, str] = {}
        for planet, details in planet_details.items():
            if planet in ("RAHU", "KETU"):
                continue
            nak = details.get("nakshatra", "")
            if not nak:
                # Compute from longitude
                sign = details.get("sign", "")
                degree = details.get("degree_in_sign", 0)
                if sign in SIGN_ORDER:
                    sign_idx = SIGN_ORDER.index(sign)
                    longitude = (sign_idx * 30.0) + degree
                    nak, _, _ = self._longitude_to_nakshatra(longitude)
            planet_naks[planet] = nak

        planets = [p for p in planet_naks if p not in ("RAHU", "KETU")]
        seen: set[tuple[str, str]] = set()

        for i, p_a in enumerate(planets):
            nak_a = planet_naks.get(p_a, "")
            lord_a = NAKSHATRA_LORDS.get(nak_a, "")
            for p_b in planets[i + 1 :]:
                nak_b = planet_naks.get(p_b, "")
                lord_b = NAKSHATRA_LORDS.get(nak_b, "")

                # Mutual Nakshatra exchange
                if lord_a == p_b and lord_b == p_a:
                    pair_key = tuple(sorted([p_a, p_b]))
                    if pair_key in seen:
                        continue
                    seen.add(pair_key)
                    exchanges.append(
                        {
                            "planet_a": p_a,
                            "planet_b": p_b,
                            "nakshatra_a": NAKSHATRA_NAMES.get(nak_a, nak_a),
                            "nakshatra_b": NAKSHATRA_NAMES.get(nak_b, nak_b),
                            "lord_a": lord_a,
                            "lord_b": lord_b,
                            "tag": "Subconscious Gateway Active",
                        }
                    )

        return exchanges

    # ── Sarvatobhadra Vedha Detection ────────────────────────────────────────

    def _detect_vedha(
        self,
        planet_details: dict[str, dict[str, Any]],
    ) -> list[dict[str, str]]:
        """Detect Sarvatobhadra Vedha (piercing) between planets.

        If Planet A's Nakshatra casts a Vedha on Planet B's Nakshatra,
        flag it as "Structural Friction / Sudden Breakthrough".

        Returns list of dicts with planet_a, planet_b, nakshatra_a,
        nakshatra_b, direction, and the structural friction tag.
        """
        flags: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()

        # Compute Nakshatras
        planet_naks: dict[str, str] = {}
        for planet, details in planet_details.items():
            if planet in ("RAHU", "KETU"):
                continue
            nak = details.get("nakshatra", "")
            if not nak:
                sign = details.get("sign", "")
                degree = details.get("degree_in_sign", 0)
                if sign in SIGN_ORDER:
                    sign_idx = SIGN_ORDER.index(sign)
                    longitude = (sign_idx * 30.0) + degree
                    nak, _, _ = self._longitude_to_nakshatra(longitude)
            planet_naks[planet] = nak

        planets = [p for p in planet_naks if planet_naks[p]]

        for i, p_a in enumerate(planets):
            nak_a = planet_naks[p_a]
            for p_b in planets[i + 1 :]:
                nak_b = planet_naks[p_b]

                # Check if Vedha exists in either direction
                vedha_ab = (nak_a, nak_b) in SARVATOBHADRA_VEDHA
                vedha_ba = (nak_b, nak_a) in SARVATOBHADRA_VEDHA

                if vedha_ab or vedha_ba:
                    pair_key = tuple(sorted([p_a, p_b]))
                    if pair_key in seen:
                        continue
                    seen.add(pair_key)

                    if vedha_ab and vedha_ba:
                        direction = "bidirectional"
                    elif vedha_ab:
                        direction = f"{p_a} pierces {p_b}"
                    else:
                        direction = f"{p_b} pierces {p_a}"

                    flags.append(
                        {
                            "planet_a": p_a,
                            "planet_b": p_b,
                            "nakshatra_a": NAKSHATRA_NAMES.get(nak_a, nak_a),
                            "nakshatra_b": NAKSHATRA_NAMES.get(nak_b, nak_b),
                            "direction": direction,
                            "tag": "Structural Friction / Sudden Breakthrough",
                        }
                    )

        return flags

    # ── Inter-Aspect Modifications ───────────────────────────────────────────

    def _detect_inter_aspect_modifications(
        self,
        pairs: list[ParivartanaPair],
        planet_signs: dict[str, str],
        lagna: str,
        aspect_entries: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Check if benefic or malefic planets aspect the exchanging planets.

        Jupiter aspects → "Benefic Intervention / Purification"
        Rahu/Ketu/Saturn aspects → "Malefic Interference / Loss of Restraint"

        Uses correct 0-indexed aspect math:
          Jupiter: +4, +8 (special) + 7th (universal)
          Mars: +3, +7 (special) + 7th (universal)
          Saturn: +2, +9 (special) + 7th (universal)
          Rahu/Ketu: 7th only

        Returns list of modification dicts.
        """
        modifications: list[dict[str, Any]] = []

        if not pairs:
            return modifications

        # Build planet → house mapping
        lagna_idx = self._sign_index(lagna)
        planet_houses: dict[str, int] = {}
        for planet, sign in planet_signs.items():
            planet_houses[planet] = self._house_from_lagna(sign.upper(), lagna_idx)

        # Collect all planets involved in exchanges
        exchanging_planets: set[str] = set()
        for pair in pairs:
            exchanging_planets.add(pair.planet_a)
            exchanging_planets.add(pair.planet_b)

        # Check each benefic/malefic for aspects on exchanging planets
        benefic_planets = {"JUPITER", "VENUS", "MERCURY", "MOON"}
        malefic_planets = {"RAHU", "KETU", "SATURN", "MARS"}

        for aspecter in list(benefic_planets | malefic_planets):
            if aspecter not in planet_houses:
                continue

            aspecter_house = planet_houses[aspecter]
            aspect_offsets = self._get_aspect_offsets(aspecter)

            for offset in aspect_offsets:
                # 0-indexed: target_house = (source_house + offset) mod 12
                target_house = ((aspecter_house + offset - 1) % 12) + 1

                for ex_planet in exchanging_planets:
                    if ex_planet not in planet_houses:
                        continue
                    if planet_houses[ex_planet] == target_house:
                        # This aspecter aspects this exchanging planet
                        is_benefic = aspecter in benefic_planets
                        modification = {
                            "aspecter": aspecter,
                            "aspected_planet": ex_planet,
                            "aspect_offset": offset,
                            "aspect_type": f"{'Special' if offset != 7 else '7th'}",
                        }

                        if is_benefic and aspecter == "JUPITER":
                            modification["tag"] = "Benefic Intervention / Purification"
                            modification["description"] = (
                                f"Jupiter's {offset}th aspect purifies the exchange energy "
                                f"involving {ex_planet}, elevating it toward dharmic expression. "
                                f"The exchange gains moral clarity and constructive direction."
                            )
                        elif aspecter in malefic_planets:
                            modification["tag"] = "Malefic Interference / Loss of Restraint"
                            modification["description"] = (
                                f"{aspecter}'s {offset}th aspect introduces turbulence into "
                                f"{ex_planet}'s exchange dynamics. The exchange energy becomes "
                                f"volatile, prone to sudden disruptions and loss of restraint."
                            )
                        else:
                            modification["tag"] = "Minor Aspect Influence"
                            modification["description"] = (
                                f"{aspecter}'s {offset}th aspect adds subtle coloring to "
                                f"{ex_planet}'s exchange pattern."
                            )

                        modifications.append(modification)

        return modifications

    @staticmethod
    def _get_aspect_offsets(planet: str) -> list[int]:
        """Get all house offsets this planet aspects (0-indexed from 7).

        Universal 7th aspect + special aspects.
        Jupiter: 7th + 4th + 8th → offsets [7, 4, 8]
        Mars: 7th + 3rd + 7th → offsets [7, 3, 7] (deduped to [7, 3])
        Saturn: 7th + 2nd + 9th → offsets [7, 2, 9]
        Rahu/Ketu: 7th only → offset [7]
        """
        offsets = [7]  # Universal 7th aspect
        if planet in SPECIAL_ASPECT_OFFSETS:
            offsets.extend(SPECIAL_ASPECT_OFFSETS[planet])
        return offsets

    # ── Narrative builder ────────────────────────────────────────────────────

    @staticmethod
    def _build_narrative(
        p_a: str,
        sign_a: str,
        house_a: int,
        p_b: str,
        sign_b: str,
        house_b: int,
        exchange_type: str,
        neecha_bhanga: bool,
        strength: float,
    ) -> str:
        """Build a human-readable narrative for the exchange."""
        type_desc = {
            "MAHA": "a powerful Maha Parivartana (Kendra-Trikona exchange)",
            "DAINYA": "a Dainya Parivartana (Dusthana involvement)",
            "KHALA": "a Khala Parivartana (3rd house volatility)",
            "ORDINARY": "an Ordinary Parivartana",
        }
        desc = type_desc.get(exchange_type, "a Parivartana")

        parts = [
            f"{p_a} in {sign_a} (House {house_a}) and {p_b} in {sign_b} (House {house_b}) form {desc}.",
        ]

        if neecha_bhanga:
            parts.append(
                "One planet's debilitation is cancelled through this exchange (Neecha-bhanga)."
            )

        if strength >= 0.7:
            parts.append(
                "This is a strong, benefic exchange that enhances the significations of both houses involved."
            )
        elif strength >= 0.4:
            parts.append(
                "This exchange has moderate strength and influences the connected domains."
            )
        else:
            parts.append("This is a weak exchange with limited practical impact.")

        return " ".join(parts)

    # ── 4-Part Synthesis Generator ───────────────────────────────────────────

    def _generate_synthesis(
        self,
        pairs: list[ParivartanaPair],
        nak_exchanges: list[dict[str, str]],
        vedha_flags: list[dict[str, str]],
        inter_aspects: list[dict[str, Any]],
        planet_signs: dict[str, str],
        lagna: str,
        dignity_map: dict[str, str],
    ) -> dict[str, str]:
        """Generate the 4-part structured synthesis output."""
        return {
            "rasi_analysis": self._synthesize_rasi(pairs, planet_signs, lagna, dignity_map),
            "nakshatra_analysis": self._synthesize_nakshatra(
                nak_exchanges, vedha_flags, planet_signs, lagna
            ),
            "inter_aspect_modifications": self._synthesize_inter_aspects(inter_aspects, pairs),
            "final_synthesis": self._synthesize_final(
                pairs, nak_exchanges, vedha_flags, inter_aspects, lagna
            ),
        }

    @staticmethod
    def _synthesize_rasi(
        pairs: list[ParivartanaPair],
        planet_signs: dict[str, str],
        lagna: str,
        dignity_map: dict[str, str],
    ) -> str:
        """Part 1: Rasi Parivartana Analysis — External Reality."""
        if not pairs:
            return (
                "External Reality: No Rasi Parivartana (mutual sign exchange) exists in this chart. "
                "The native's external reality is shaped by independent planetary placements without "
                "the binding reciprocity of an exchange yoga. Life events unfold through individual "
                "planetary dasha periods rather than through the locked-in dynamic of exchanged energies."
            )

        sections: list[str] = []

        for pair in pairs:
            p_a, p_b = pair.planet_a, pair.planet_b
            h_a, h_b = pair.house_a, pair.house_b

            if pair.exchange_type == "MAHA":
                analysis = (
                    f"MAHA PARIVARTANA ({p_a} in House {h_a} ↔ {p_b} in House {h_b}): "
                    f"This is a highly auspicious exchange. The houses {h_a} and {h_b} are "
                    f"mutually empowered, creating a self-reinforcing loop of prosperity. "
                    f"The native experiences tangible benefits in the domains governed by these "
                    f"houses — {p_a}'s significations flow freely into {p_b}'s territory and vice "
                    f"versa. In practical terms, this manifests as: career advancement that brings "
                    f"personal fulfillment, or domestic harmony that supports professional ambition. "
                    f"The exchange is{'particularly powerful' if pair.strength >= 0.7 else 'moderately active'} "
                    f"with a strength score of {pair.strength:.2f}."
                )
                if pair.neecha_bhanga:
                    analysis += (
                        " Additionally, Neecha-bhanga is active — one planet's debilitation is "
                        "cancelled, converting a potential weakness into an unexpected source of "
                        "strength. The native turns adversity into advantage through this exchange."
                    )
            elif pair.exchange_type == "DAINYA":
                analysis = (
                    f"DAINYA PARIVARTANA ({p_a} in House {h_a} ↔ {p_b} in House {h_b}): "
                    f"This exchange involves Dusthana (6th, 8th, or 12th) houses, creating "
                    f"a karmic bind between the native's struggles and their relational/structural "
                    f"patterns. The houses {h_a} and {h_b} are locked in a cycle of mutual "
                    f"affliction — one house's significations contaminate the other. In real life, "
                    f"this can manifest as: health problems that disrupt partnerships, enemies who "
                    f"rise through the native's own network, or hidden losses that erode "
                    f"foundational security. The native must consciously break this pattern through "
                    f"remedial measures.{' Despite Neecha-bhanga offering partial relief.' if pair.neecha_bhanga else ''}"
                )
            elif pair.exchange_type == "KHALA":
                analysis = (
                    f"KHALA PARIVARTANA ({p_a} in House {h_a} ↔ {p_b} in House {h_b}): "
                    f"This exchange involves the 3rd house, introducing volatility and restless "
                    f"energy into the exchange dynamic. The native experiences sudden fluctuations "
                    f"in the domains connected by houses {h_a} and {h_b}. Communication, courage, "
                    f"and siblings (3rd house themes) become entangled with the other house's "
                    f"significations, creating unpredictable outcomes. The native may find that "
                    f"bold action leads to unexpected results — sometimes breakthrough, sometimes "
                    f"breakdown. Consistency is the challenge; the key is to channel the 3rd house "
                    f"restlessness into disciplined creative expression."
                )
            else:
                analysis = (
                    f"ORDINARY PARIVARTANA ({p_a} in House {h_a} ↔ {p_b} in House {h_b}): "
                    f"This exchange connects houses {h_a} and {h_b} without the dramatic "
                    f"auspiciousness of Maha or the affliction of Dainya. It creates a subtle but "
                    f"persistent linking of life domains. The native may not consciously notice its "
                    f"effects, but it quietly shapes how the significations of these houses interact."
                )

            sections.append(analysis)

        header = (
            "External Reality: The chart contains "
            f"{len(pairs)} Rasi Parivartana exchange{'s' if len(pairs) > 1 else ''}. "
            "These mutual sign exchanges create binding karmic links between specific life "
            "domains, forcing the native to navigate intertwined destinies in those areas.\n\n"
        )

        return header + "\n\n".join(sections)

    @staticmethod
    def _synthesize_nakshatra(
        nak_exchanges: list[dict[str, str]],
        vedha_flags: list[dict[str, str]],
        planet_signs: dict[str, str],
        lagna: str,
    ) -> str:
        """Part 2: Nakshatra Parivartana Analysis — Subconscious Mind."""
        sections: list[str] = []

        # Nakshatra exchanges
        if nak_exchanges:
            for ex in nak_exchanges:
                sections.append(
                    f"SUBCONSCIOUS GATEWAY ACTIVE — {ex['planet_a']} in {ex['nakshatra_a']} "
                    f"(lorded by {ex['lord_a']}) ↔ {ex['planet_b']} in {ex['nakshatra_b']} "
                    f"(lorded by {ex['lord_b']}): This mutual Nakshatra exchange operates at the "
                    f"subconscious level, far below the surface awareness of the native. While "
                    f"Rasi exchanges shape external events, this Nakshatra-level bind creates an "
                    f"emotional bypass — the native unconsciously replays patterns from past-life "
                    f"karma through these two planets. {ex['planet_a']} and {ex['planet_b']} form "
                    f"a psychic circuit that feeds energy between the native's inner emotional world "
                    f"and their instinctive reactions. The native may find themselves inexplicably "
                    f"drawn to or repelled by situations that activate this pair. Dreams, intuitions, "
                    f"and gut feelings are strongly colored by this exchange. Meditation on the "
                    f"Nakshatra deities ({NAKSHATRA_NAMES.get(ex.get('nakshatra_a', ''), '')} and "
                    f"{NAKSHATRA_NAMES.get(ex.get('nakshatra_b', ''), '')}) can help the native "
                    f"consciously integrate these submerged energies."
                )
        else:
            sections.append(
                "No mutual Nakshatra lord exchanges detected. The native's subconscious "
                "emotional patterns operate through individual Nakshatra placements rather than "
                "through the tight psychic circuit of a Nakshatra exchange. This provides more "
                "flexibility in emotional processing but less depth of karmic bonding."
            )

        # Vedha flags
        if vedha_flags:
            for vedha in vedha_flags:
                sections.append(
                    f"STRUCTURAL FRICTION / SUDDEN BREAKTHROUGH — {vedha['nakshatra_a']} "
                    f"({vedha['planet_a']}) ↔ {vedha['nakshatra_b']} ({vedha['planet_b']}): "
                    f"The Sarvatobhadra Chakra reveals a Vedha (piercing) relationship between "
                    f"these Nakshatras ({vedha['direction']}). This creates a structural tension "
                    f"in the native's psyche — a persistent undercurrent of friction that, when "
                    f"unresolved, manifests as recurring obstacles in the life areas governed by "
                    f"these planets. However, Vedha is not purely destructive. It is the cosmic "
                    f"mechanism for breakthrough: the piercing force that breaks through stagnation. "
                    f"When the native consciously works with this energy (through mantra, tantra, "
                    f"or disciplined sadhana), the friction transforms into a catalyst for sudden "
                    f"awakening. The native's greatest breakthroughs will come precisely through "
                    f"the areas where they experience the most friction."
                )

        if not sections:
            return (
                "Subconscious Mind: No significant Nakshatra-level activations detected. "
                "The native's subconscious patterns are relatively unstructured at the Nakshatra "
                "layer, providing emotional fluidity without deep karmic binding."
            )

        header = (
            "Subconscious Mind: "
            f"{len(nak_exchanges)} Nakshatra exchange{'s' if len(nak_exchanges) != 1 else ''} "
            f"and {len(vedha_flags)} Vedha activation{'s' if len(vedha_flags) != 1 else ''} "
            f"detected. These operate beneath conscious awareness, shaping instinctive reactions "
            f"and emotional bypass patterns.\n\n"
        )

        return header + "\n\n".join(sections)

    @staticmethod
    def _synthesize_inter_aspects(
        inter_aspects: list[dict[str, Any]],
        pairs: list[ParivartanaPair],
    ) -> str:
        """Part 3: Inter-Aspect Modifications — Overriding Triggers."""
        if not inter_aspects:
            return (
                "Overriding Triggers: No significant planetary aspects modify the exchange "
                "dynamics. The Parivartana yogas operate in their natural state without external "
                "benefic purification or malefic interference. The native experiences the pure "
                "unmodified energy of their exchanges."
            )

        sections: list[str] = []
        benefic_mods = [m for m in inter_aspects if "Purification" in m.get("tag", "")]
        malefic_mods = [m for m in inter_aspects if "Malefic" in m.get("tag", "")]

        if benefic_mods:
            seen_pairs: set[tuple[str, str]] = set()
            for mod in benefic_mods:
                pair_key = (mod["aspecter"], mod["aspected_planet"])
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                sections.append(
                    f"BENEFIC INTERVENTION / PURIFICATION — {mod['aspecter']}'s "
                    f"{mod['aspect_offset']}th aspect on {mod['aspected_planet']}: "
                    f"{mod.get('description', '')} This is a divine safeguard — Jupiter's "
                    f"expansive, dharmic energy acts as a moral compass for the exchange, "
                    f"steering it toward constructive outcomes even when the underlying exchange "
                    f"type (Maha/Dainya/Khala) might otherwise produce turbulence. The native "
                    f"should trust their ethical instincts during periods when this Jupiterian "
                    f"influence is strongest (Jupiter Dasha, Jupiter transits through Kendra/Trikona)."
                )

        if malefic_mods:
            seen_pairs2: set[tuple[str, str]] = set()
            for mod in malefic_mods:
                pair_key = (mod["aspecter"], mod["aspected_planet"])
                if pair_key in seen_pairs2:
                    continue
                seen_pairs2.add(pair_key)
                sections.append(
                    f"MALEFIC INTERFERENCE / LOSS OF RESTRAINT — {mod['aspecter']}'s "
                    f"{mod['aspect_offset']}th aspect on {mod['aspected_planet']}: "
                    f"{mod.get('description', '')} This interference destabilizes the exchange, "
                    f"making it prone to sudden eruptions of karmic intensity. The native may "
                    f"experience unexpected crises in the life areas governed by the afflicted "
                    f"exchange. Caution is advised during {mod['aspecter']}'s Dasha/AD periods "
                    f"and when {mod['aspecter']} transits sensitive houses. Conscious awareness "
                    f"of this interference pattern is the first step toward mitigating its effects."
                )

        if not sections:
            return (
                "Overriding Triggers: Minor planetary aspects are present but none reach the "
                "threshold of significant modification. The exchange dynamics remain largely "
                "unmodified by external planetary interference."
            )

        header = (
            "Overriding Triggers: "
            f"{len(benefic_mods)} benefic modification{'s' if len(benefic_mods) != 1 else ''} "
            f"and {len(malefic_mods)} malefic interference{'s' if len(malefic_mods) != 1 else ''} "
            f"detected. These planetary aspects override or modify the natural exchange energy.\n\n"
        )

        return header + "\n\n".join(sections)

    @staticmethod
    def _synthesize_final(
        pairs: list[ParivartanaPair],
        nak_exchanges: list[dict[str, str]],
        vedha_flags: list[dict[str, str]],
        inter_aspects: list[dict[str, Any]],
        lagna: str,
    ) -> str:
        """Part 4: Final Synthesis — Conclusive guidance."""
        has_maha = any(p.exchange_type == "MAHA" for p in pairs)
        has_dainya = any(p.exchange_type == "DAINYA" for p in pairs)
        has_khala = any(p.exchange_type == "KHALA" for p in pairs)
        has_jup_purification = any("Purification" in m.get("tag", "") for m in inter_aspects)
        has_malefic_interference = any("Malefic" in m.get("tag", "") for m in inter_aspects)

        parts: list[str] = []

        # Overall assessment
        if has_maha and not has_dainya:
            parts.append(
                "Final Synthesis: The chart is blessed with powerful Maha Parivartana exchanges "
                "that create self-reinforcing loops of prosperity and dharmic fulfillment. The "
                "native's life path is characterized by organic growth in key life areas, where "
                "success in one domain naturally catalyzes success in another."
            )
        elif has_dainya and not has_maha:
            parts.append(
                "Final Synthesis: The chart carries significant Dainya Parivartana energy, "
                "indicating karmic debts that must be resolved through conscious effort. The "
                "native's path requires navigating affliction-linked exchanges, which demand "
                "disciplined remedial practices (mantras, donations, temple worship) to transform "
                "the binding karma into liberation."
            )
        elif has_maha and has_dainya:
            parts.append(
                "Final Synthesis: The chart presents a complex interplay of Maha and Dainya "
                "Parivartana yogas — a karmic landscape where periods of extraordinary blessing "
                "alternate with periods of deep affliction. The native's life is a dance between "
                "light and shadow, and mastery comes from learning to navigate both with equanimity."
            )
        elif has_khala:
            parts.append(
                "Final Synthesis: The chart features Khala Parivartana energy, introducing "
                "volatility and unpredictability into key life areas. The native's path is "
                "characterized by sudden shifts and unexpected developments — a life lived on "
                "the edge of transformation. Consistency is the challenge; courage is the reward."
            )
        elif not pairs:
            parts.append(
                "Final Synthesis: No Rasi Parivartana exchanges are present, giving the native "
                "greater freedom from karmic binding but also less organic support from exchange "
                "yogas. Life progress depends more heavily on individual planetary dasha periods "
                "and the native's own conscious effort."
            )
        else:
            parts.append(
                "Final Synthesis: The chart contains ordinary Parivartana exchanges that create "
                "subtle linking of life domains without dramatic auspiciousness or affliction."
            )

        # Nakshatra layer
        if nak_exchanges:
            parts.append(
                f"The presence of {len(nak_exchanges)} Nakshatra-level exchange{'s' if len(nak_exchanges) != 1 else ''} "
                f"adds a deep subconscious dimension. The native is working through past-life "
                f"karmic patterns at the emotional and instinctive level. Awareness of these "
                f"submerged patterns — through dream journaling, therapy, or spiritual practice — "
                f"is essential for conscious integration."
            )

        # Vedha layer
        if vedha_flags:
            parts.append(
                f"The {len(vedha_flags)} Sarvatobhadra Vedha activation{'s' if len(vedha_flags) != 1 else ''} "
                f"create structural friction that serves as a catalyst for breakthrough. The native "
                f"should embrace the areas of greatest friction as opportunities for radical "
                f"transformation. These are not obstacles to be avoided but gateways to be "
                f"consciously traversed."
            )

        # Inter-aspect modifications
        if has_jup_purification:
            parts.append(
                "Jupiter's purifying aspect provides a dharmic safety net, ensuring that even "
                "the most challenging exchanges ultimately serve the native's spiritual growth. "
                "The native should lean into Jupiterian practices — teaching, counseling, charity, "
                "pilgrimage — during difficult exchange activations."
            )

        if has_malefic_interference:
            parts.append(
                "Malefic interference (Rahu/Saturn/Ketu aspects) introduces volatility and "
                "the risk of sudden disruptions. The native should practice heightened awareness "
                "during these planets' active periods and avoid impulsive decisions when the "
                "exchange energy feels turbulent. Saturnian discipline and Rahu-conscious "
                "containment are the remedies."
            )

        # Practical guidance
        if pairs:
            house_pairs = [(p.house_a, p.house_b) for p in pairs]
            house_descriptions = {
                1: "self-identity and physical body",
                2: "wealth, family, and speech",
                3: "courage, communication, and siblings",
                4: "home, mother, and inner peace",
                5: "creativity, children, and past merit",
                6: "enemies, disease, and service",
                7: "partnership, marriage, and public dealing",
                8: "transformation, hidden matters, and longevity",
                9: "fortune, dharma, and higher learning",
                10: "career, status, and public image",
                11: "gains, aspirations, and social networks",
                12: "losses, liberation, and foreign connections",
            }
            domains = set()
            for h_a, h_b in house_pairs:
                if h_a in house_descriptions:
                    domains.add(house_descriptions[h_a])
                if h_b in house_descriptions:
                    domains.add(house_descriptions[h_b])
            if domains:
                parts.append(
                    f"To channel these exchange energies constructively, the native should focus "
                    f"on conscious integration of the following life domains: {', '.join(sorted(domains))}. "
                    f"These are the arenas where the exchange karma is most actively playing out, "
                    f"and where deliberate, aware action will yield the greatest karmic resolution."
                )

        return " ".join(parts)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _sign_index(sign: str) -> int:
        """Get the 0-based index of a sign in the zodiacal order."""
        try:
            return SIGN_ORDER.index(sign.upper())
        except ValueError:
            return 0

    @staticmethod
    def _house_from_lagna(sign: str, lagna_idx: int) -> int:
        """Compute the house number (1-12) from lagna."""
        try:
            sign_idx = SIGN_ORDER.index(sign.upper())
        except ValueError:
            return 1
        return ((sign_idx - lagna_idx) % 12) + 1

    @staticmethod
    def _longitude_to_nakshatra(longitude: float) -> tuple[str, int, int]:
        """Convert ecliptic longitude to Nakshatra, index, and pada."""
        normalized = longitude % 360.0
        nak_span = 360.0 / 27.0
        nak_index = int(normalized / nak_span)
        nakshatra = NAKSHATRA_ORDER[min(nak_index, 26)]
        pada_span = nak_span / 4
        within_nak = normalized - (nak_index * nak_span)
        pada = int(within_nak / pada_span) + 1
        pada = min(pada, 4)
        return nakshatra, nak_index, pada
