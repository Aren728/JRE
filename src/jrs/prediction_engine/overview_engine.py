"""
Master Report Overview Engine - Generates deep, conversational psychological & karmic narratives.
"""

from typing import Dict

# Astrological personality databases
LAGNA_PROFILES = {
    "Aries": {
        "element": "Fire",
        "quality": "Pioneer",
        "instinct": "act first, think later",
        "filter": "courage and direct action",
    },
    "Taurus": {
        "element": "Earth",
        "quality": "Builder",
        "instinct": "seek stability and sensory pleasure",
        "filter": "practicality and patience",
    },
    "Gemini": {
        "element": "Air",
        "quality": "Communicator",
        "instinct": "gather information and connect ideas",
        "filter": "curiosity and intellectual variety",
    },
    "Cancer": {
        "element": "Water",
        "quality": "Nurturer",
        "instinct": "protect and create emotional security",
        "filter": "intuition and emotional memory",
    },
    "Leo": {
        "element": "Fire",
        "quality": "Leader",
        "instinct": "express creativity and command attention",
        "filter": "pride and self-expression",
    },
    "Virgo": {
        "element": "Earth",
        "quality": "Analyst",
        "instinct": "refine, organize, and improve",
        "filter": "practicality and attention to detail",
    },
    "Libra": {
        "element": "Air",
        "quality": "Diplomat",
        "instinct": "create harmony and balance",
        "filter": "relationships and aesthetic beauty",
    },
    "Scorpio": {
        "element": "Water",
        "quality": "Transformer",
        "instinct": "probe depths and regenerate",
        "filter": "intensity and psychological truth",
    },
    "Sagittarius": {
        "element": "Fire",
        "quality": "Explorer",
        "instinct": "seek meaning and expand horizons",
        "filter": "philosophy and adventure",
    },
    "Capricorn": {
        "element": "Earth",
        "quality": "Architect",
        "instinct": "build structures and achieve mastery",
        "filter": "discipline and long-term strategy",
    },
    "Aquarius": {
        "element": "Air",
        "quality": "Innovator",
        "instinct": "break conventions and envision the future",
        "filter": "intellectual detachment and humanitarian ideals",
    },
    "Pisces": {
        "element": "Water",
        "quality": "Mystic",
        "instinct": "dissolve boundaries and merge with the infinite",
        "filter": "imagination and spiritual surrender",
    },
}

NAKSHATRA_PROFILES = {
    "Ashwini": {
        "ruler": "Ketu",
        "symbol": "Horse's Head",
        "depth": "healing and swift action",
        "shadow": "impatience and scattered energy",
    },
    "Bharani": {
        "ruler": "Venus",
        "symbol": "Yoni",
        "depth": "creation and restraint",
        "shadow": "indulgence and possessiveness",
    },
    "Krittika": {
        "ruler": "Sun",
        "symbol": "Razor",
        "depth": "purification through fire",
        "shadow": "cutting criticism and anger",
    },
    "Rohini": {
        "ruler": "Moon",
        "symbol": "Chariot",
        "depth": "manifestation and beauty",
        "shadow": "material attachment and stubbornness",
    },
    "Mrigashira": {
        "ruler": "Mars",
        "symbol": "Deer",
        "depth": "restless searching for truth",
        "shadow": "scattered focus and anxiety",
    },
    "Ardra": {
        "ruler": "Rahu",
        "symbol": "Teardrop",
        "depth": "transformation through storms",
        "shadow": "destruction and emotional turbulence",
    },
    "Punarvasu": {
        "ruler": "Jupiter",
        "symbol": "Quiver",
        "depth": "renewal and optimism",
        "shadow": "over-expansion and lack of boundaries",
    },
    "Pushya": {
        "ruler": "Saturn",
        "symbol": "Cow's Udder",
        "depth": "nurturing and discipline",
        "shadow": "over-protectiveness and rigidity",
    },
    "Ashlesha": {
        "ruler": "Mercury",
        "symbol": "Serpent",
        "depth": "psychological penetration",
        "shadow": "manipulation and entanglement",
    },
    "Magha": {
        "ruler": "Ketu",
        "symbol": "Throne",
        "depth": "ancestral power and tradition",
        "shadow": "entitlement and rigidity",
    },
    "Purva Phalguni": {
        "ruler": "Venus",
        "symbol": "Hammock",
        "depth": "creative enjoyment",
        "shadow": "laziness and superficiality",
    },
    "Uttara Phalguni": {
        "ruler": "Sun",
        "symbol": "Bed",
        "depth": "generosity and leadership",
        "shadow": "pride and dominance",
    },
    "Hasta": {
        "ruler": "Moon",
        "symbol": "Hand",
        "depth": "skillful manifestation",
        "shadow": "perfectionism and criticism",
    },
    "Chitra": {
        "ruler": "Mars",
        "symbol": "Jewel",
        "depth": "artistic brilliance",
        "shadow": "vanity and illusion",
    },
    "Swati": {
        "ruler": "Rahu",
        "symbol": "Shoot",
        "depth": "independence and adaptability",
        "shadow": "rootlessness and restlessness",
    },
    "Vishakha": {
        "ruler": "Jupiter",
        "symbol": "Triumphal Arch",
        "depth": "focused determination",
        "shadow": "obsessive goal-chasing",
    },
    "Anuradha": {
        "ruler": "Saturn",
        "symbol": "Lotus",
        "depth": "devotion and transformation",
        "shadow": "jealousy and control",
    },
    "Jyeshtha": {
        "ruler": "Mercury",
        "symbol": "Earring",
        "depth": "protective power",
        "shadow": "suspicion and superiority",
    },
    "Mula": {
        "ruler": "Ketu",
        "symbol": "Root",
        "depth": "radical truth-seeking",
        "shadow": "destruction and nihilism",
    },
    "Purva Ashadha": {
        "ruler": "Venus",
        "symbol": "Fan",
        "depth": "invincible flow",
        "shadow": "arrogance and overwhelm",
    },
    "Uttara Ashadha": {
        "ruler": "Sun",
        "symbol": "Elephant Tusk",
        "depth": "universal victory",
        "shadow": "inflexibility and pride",
    },
    "Shravana": {
        "ruler": "Moon",
        "symbol": "Ear",
        "depth": "deep listening and learning",
        "shadow": "gossip and information overload",
    },
    "Dhanishta": {
        "ruler": "Mars",
        "symbol": "Drum",
        "depth": "rhythmic manifestation",
        "shadow": "rhythm disruption and chaos",
    },
    "Shatabhisha": {
        "ruler": "Rahu",
        "symbol": "Circle",
        "depth": "healing through isolation",
        "shadow": "detachment and secrecy",
    },
    "Purva Bhadrapada": {
        "ruler": "Jupiter",
        "symbol": "Sword",
        "depth": "spiritual fire",
        "shadow": "extremism and fanaticism",
    },
    "Uttara Bhadrapada": {
        "ruler": "Saturn",
        "symbol": "Twins",
        "depth": "oceanic wisdom and restraint",
        "shadow": "hidden depths and secrecy",
    },
    "Revati": {
        "ruler": "Mercury",
        "symbol": "Fish",
        "depth": "nurturing completion",
        "shadow": "escapism and confusion",
    },
}

ELEMENT_COMBINATIONS = {
    ("Fire", "Fire"): "double fire creates intense passion but can burn out quickly",
    ("Fire", "Earth"): "fire warms earth into fertile soil for manifestation",
    ("Fire", "Air"): "fire and air feed each other in explosive inspiration",
    ("Fire", "Water"): "fire and water create steam—powerful but volatile",
    ("Earth", "Earth"): "double earth creates unshakeable stability but resistance to change",
    ("Earth", "Air"): "earth grounds air's ideas into practical reality",
    ("Earth", "Water"): "earth and water create fertile mud for growth",
    ("Air", "Air"): "double air creates mental brilliance but lack of grounding",
    ("Air", "Water"): "air stirs water's emotions into waves of feeling",
    ("Water", "Water"): "double water creates deep intuition but emotional overwhelm",
}


def generate_overview_narrative(chart_data: Dict) -> str:
    """Generates the deep, conversational overview narrative."""

    lagna = chart_data.get("lagna", "Virgo")
    moon_sign = chart_data.get("moon_sign", "Pisces")
    moon_nakshatra = chart_data.get("moon_nakshatra", "Uttara Bhadrapada")

    lagna_profile = LAGNA_PROFILES.get(lagna, LAGNA_PROFILES["Virgo"])
    nakshatra_profile = NAKSHATRA_PROFILES.get(
        moon_nakshatra, NAKSHATRA_PROFILES["Uttara Bhadrapada"]
    )

    element_combo = ELEMENT_COMBINATIONS.get(
        (
            lagna_profile["element"],
            "Water" if nakshatra_profile["ruler"] in ["Saturn", "Ketu"] else "Fire",
        ),
        "creates a unique alchemical blend of opposing forces",
    )

    narrative = f"""
# Your Psychological & Karmic Blueprint

## 🌌 The Core Alignment: The Anchor and the Deep Ocean

Your personality is not a collection of isolated traits; it is a living, breathing ecosystem. Your outward approach to the world is governed by a **{lagna} Ascendant (Lagna)**, meaning your conscious mind operates with sharp precision, analytical depth, and a natural instinct to {lagna_profile["instinct"]}. You look at life through a lens of **{lagna_profile["filter"]}**, always searching for the underlying structure of things.

However, beneath this {lagna_profile["quality"].lower()}, {lagna_profile["element"].lower()} exterior lies an incredibly vast, mystical, and complex inner world driven by your **Moon in {moon_nakshatra} Nakshatra**.

This creates a fascinating, powerful internal polarity:

**The Outer Self ({lagna}):** Craves {lagna_profile["filter"]}, clarity, and tangible results. You present yourself to the world as dependable, observant, and highly capable of managing chaos.

**The Inner Self ({moon_nakshatra}):** Operates in the deep, unseen waters of the subconscious. This Nakshatra—symbolized by the "{nakshatra_profile["symbol"]}" and ruled by {nakshatra_profile["ruler"]}—endows you with an old-soul wisdom, a powerful intuition, and a quiet, subterranean intensity.

While your face shows the world a calm, methodical problem-solver, your soul is constantly navigating profound existential questions, hidden desires, and spiritual transformations.

## 🏛️ The Structural Matrix: How Your Archetypes Intersect

To understand how these cosmic forces dictate your daily life, emotional responses, and destiny, let us look at how these layers seamlessly lock together.

**Layer** | **The Cosmic Placement** | **The Living Reality (How It Manifests in You)**
---|---|---
 **The Lens** | {lagna} Lagna | You are the natural {lagna_profile["quality"].lower()} of the zodiac. Your first instinct is to {lagna_profile["instinct"]}. You have a low tolerance for superficiality or sloppiness, filtering your entire reality through a need for {lagna_profile["filter"]}.
⭐ **The Subconscious** | {moon_nakshatra} | This is the source of your quiet strength. You possess an innate capacity to endure dark, heavy, or complex emotional phases that would break others. You don't just feel emotions; you process them on a karmic, spiritual level, giving you a naturally secretive and highly protective inner world.
🔥 **The Balance** | {lagna_profile["element"]} & {nakshatra_profile["depth"].split()[0]} | Your elemental mix creates {element_combo}. The {lagna_profile["element"]} of {lagna} keeps you anchored, professional, and realistic, while the heavy water element of your Nakshatra gives you immense psychic depth, intense private fantasies, and a powerful emotional current.

## 🔮 The Definitive Synthesis: Understanding Your Shadow & Light

Because your chart connects the {lagna_profile["filter"]} of {lagna} with the {nakshatra_profile["depth"]} of {moon_nakshatra}, your life is a constant dance between control and surrender.

### 1. The Mind and the Hidden Landscape

You possess a mind that can easily compartmentalize. Your {lagna} Ascendant allows you to maintain absolute composure and logic in your professional or public life. Yet, because your Moon resides in a {nakshatra_profile["ruler"]}-ruled Nakshatra, your private thoughts harbor a rich, intense, and sometimes taboo world of fantasy. You are deeply drawn to mysteries, secrets, and the hidden psychological motives of others. You see through people instantly, picking up on their unspoken shadows.

### 2. The Relationship Dynamic

In relationships, this polarity creates a specific vulnerability. Your outer self seeks a partner who is reliable, clean, and logical. But your inner self craves absolute, soul-merging depth—the kind that often defies conventional boundaries. This can lead to intense internal conflicts where your logic tells you to walk away, but your deep karmic intuition binds you to complex, private, or unconventional emotional attachments.

### 3. Your Final Evolutionary Path

You are designed to move from mere intellectual observation to profound spiritual wisdom. Your greatest power is realized when you stop trying to micro-manage your emotions with your intellect, and instead trust the deep, quiet resilience of your intuition. You are meant to be an anchor for others in times of crisis, using your sharp {lagna} brain to execute the profound, compassionate wisdom generated by your soul.

## 🎯 The Verdict

You do not need to look further to understand your core nature: **You are a pragmatic mystic.** Your life assignment is to use your sharp, analytical mind to give structure, meaning, and voice to the vast, oceanic depths of your internal world.

The shadow you must integrate is the belief that logic and intuition are enemies. They are not. They are twin flames of the same fire. When you honor both—when you allow your {lagna} precision to serve your {moon_nakshatra} wisdom rather than suppress it—you become unstoppable.

Your light is your ability to make the mystical practical, to bring heaven down to earth. Your shadow is the tendency to either over-analyze your feelings (Virgo trap) or drown in them without structure (Nakshatra trap).

**The middle path is your mastery.**
"""
    return narrative


def get_mock_chart_data() -> Dict:
    """Mock data for testing."""
    return {
        "lagna": "Virgo",
        "moon_sign": "Pisces",
        "moon_nakshatra": "Uttara Bhadrapada",
        "sun_sign": "Leo",
        "weekday": "Tuesday",
    }
