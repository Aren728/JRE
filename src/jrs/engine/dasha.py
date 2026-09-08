"""
Calculates precise Vimshottari Dasha, Antardasha, and Pratyantardasha periods
based on the Moon's sidereal longitude and birth timestamp.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

DASHA_LORDS: List[Tuple[str, float]] = [
    ("Ketu", 7.0),
    ("Venus", 20.0),
    ("Sun", 6.0),
    ("Moon", 10.0),
    ("Mars", 7.0),
    ("Rahu", 18.0),
    ("Jupiter", 16.0),
    ("Saturn", 19.0),
    ("Mercury", 17.0),
]

TOTAL_VIMSHOTTARI_YEARS = 120.0
NAKSHATRA_SPAN_DEG = 13.0 + (1.0 / 3.0)  # 13°20' = 13.3333°


def _add_years(start_dt: datetime, years: float) -> datetime:
    """Helper to convert float years to exact timedelta."""
    return start_dt + timedelta(days=years * 365.2425)


def calculate_vimshottari_dasha(
    moon_longitude: float,
    birth_date_str: str,
    target_date: datetime | None = None,
) -> Dict[str, Any]:
    """
    Computes exact active Mahadasha, Antardasha, and Pratyantardasha.
    Defaults target_date to current execution time.
    """
    if target_date is None:
        target_date = datetime.now()

    birth_dt = datetime.strptime(birth_date_str, "%Y-%m-%d")

    # 1. Starting Nakshatra and Mahadasha Lord
    nak_idx = int(moon_longitude // NAKSHATRA_SPAN_DEG) % 27
    lord_idx = nak_idx % 9
    mahadasha_lord, total_m_years = DASHA_LORDS[lord_idx]

    # 2. Balance of Mahadasha remaining at birth
    deg_into_nak = moon_longitude % NAKSHATRA_SPAN_DEG
    fraction_consumed = deg_into_nak / NAKSHATRA_SPAN_DEG
    fraction_remaining = 1.0 - fraction_consumed

    # Start date of initial Mahadasha (backcalculated)
    m_start = _add_years(birth_dt, -(total_m_years * fraction_consumed))
    m_end = _add_years(m_start, total_m_years)

    # 3. Iterate Mahadashas to encapsulate target_date
    current_m_idx = lord_idx
    while target_date >= m_end:
        current_m_idx = (current_m_idx + 1) % 9
        m_start = m_end
        mahadasha_lord, total_m_years = DASHA_LORDS[current_m_idx]
        m_end = _add_years(m_start, total_m_years)

    # 4. Iterate Antardashas (AD)
    a_start = m_start
    antardasha_lord = mahadasha_lord
    current_a_idx = current_m_idx
    a_end = a_start

    for a_offset in range(9):
        current_a_idx = (current_m_idx + a_offset) % 9
        a_lord_name, a_duration = DASHA_LORDS[current_a_idx]
        a_years = (total_m_years * a_duration) / TOTAL_VIMSHOTTARI_YEARS
        a_end = _add_years(a_start, a_years)

        if a_start <= target_date < a_end:
            antardasha_lord = a_lord_name
            break
        a_start = a_end

    # 5. Iterate Pratyantardashas (PAD)
    p_start = a_start
    pratyantardasha_lord = antardasha_lord
    p_end = p_start
    a_years_actual = (total_m_years * DASHA_LORDS[current_a_idx][1]) / TOTAL_VIMSHOTTARI_YEARS

    for p_offset in range(9):
        current_p_idx = (current_a_idx + p_offset) % 9
        p_lord_name, p_duration = DASHA_LORDS[current_p_idx]
        p_years = (a_years_actual * p_duration) / TOTAL_VIMSHOTTARI_YEARS
        p_end = _add_years(p_start, p_years)

        if p_start <= target_date < p_end:
            pratyantardasha_lord = p_lord_name
            break
        p_start = p_end

    return {
        "mahadasha": mahadasha_lord,
        "antardasha": antardasha_lord,
        "pratyantardasha": pratyantardasha_lord,
        "start_date": p_start.strftime("%Y-%m-%d"),
        "end_date": p_end.strftime("%Y-%m-%d"),
    }
