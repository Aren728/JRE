"""Numerology JRE — Deterministic calculation service.

``NumerologyCalculationService`` takes birth data (date, name) and
produces a ``NumerologyChart`` containing ONLY deterministic facts:
Life Path Number, Destiny Number, Personal Year Number.  No
astrological or numerological interpretation is performed.
"""

from __future__ import annotations

from .models import (
    DestinyNumber,
    LifePathNumber,
    LifePathType,
    NumerologyChart,
    NumerologySystem,
    PersonalYearNumber,
    reduce_to_single_digit,
)


def _classify_life_path(number: int) -> LifePathType:
    """Classify a Life Path number into its type."""
    mapping: dict[int, LifePathType] = {
        1: LifePathType.LEADER,
        2: LifePathType.BUILDER,
        3: LifePathType.COMMUNICATOR,
        4: LifePathType.NURTURER,
        5: LifePathType.FREEDOM_SEEKER,
        6: LifePathType.HARMONIZER,
        7: LifePathType.THINKER,
        8: LifePathType.POWERFUL,
        9: LifePathType.HUMANITARIAN,
        11: LifePathType.MASTER_11,
        22: LifePathType.MASTER_22,
        33: LifePathType.MASTER_33,
    }
    return mapping.get(number, LifePathType.LEADER)


class NumerologyCalculationService:
    """Deterministic numerology calculation service.

    Takes birth data and produces a NumerologyChart fact object.

    Usage::

        svc = NumerologyCalculationService()
        chart = svc.calculate(
            birth_date="1985-07-15",
            birth_name="John Adam Smith",
        )
    """

    def calculate(
        self,
        birth_date: str,
        birth_name: str,
        system: NumerologySystem = NumerologySystem.PYTHAGOREAN,
        target_year: int | None = None,
    ) -> NumerologyChart:
        """Calculate the complete numerology chart.

        Args:
            birth_date: ISO date string (YYYY-MM-DD).
            birth_name: Full birth name.
            system: Numerology system to use.
            target_year: Year for Personal Year calculation.
                If None, uses the current year from birth_date.

        Returns:
            A NumerologyChart containing all deterministic facts.
        """
        # Calculate Life Path Number from birth date
        life_path = self._calculate_life_path(birth_date)

        # Calculate Destiny Number from birth name
        destiny = self._calculate_destiny(birth_name)

        # Calculate Personal Year Number
        year = target_year or int(birth_date[:4])
        personal_year = self._calculate_personal_year(birth_date, year)

        return NumerologyChart(
            birth_date=birth_date,
            birth_name=birth_name,
            system=system,
            life_path=life_path,
            destiny=destiny,
            personal_year=personal_year,
        )

    def _calculate_life_path(self, birth_date: str) -> LifePathNumber:
        """Calculate Life Path Number from birth date.

        Algorithm:
            1. Parse YYYY-MM-DD into month, day, year.
            2. Reduce each component to a single digit.
            3. Sum the reduced components.
            4. Reduce the sum to a single digit (or master number).

        Source: Pythagorean tradition, Cheiro Ch. 1.
        """
        parts = birth_date.split("-")
        month = int(parts[1])
        day = int(parts[2])
        year = int(parts[0])

        # Step 1: Reduce each component
        month_reduced = reduce_to_single_digit(month)
        day_reduced = reduce_to_single_digit(day)
        year_reduced = reduce_to_single_digit(year)

        # Step 2: Sum reduced components
        raw_sum = month_reduced + day_reduced + year_reduced

        # Step 3: Final reduction
        steps: list[int] = [month_reduced, day_reduced, year_reduced, raw_sum]
        final = reduce_to_single_digit(raw_sum)

        # If final is a master number, it stays; otherwise check the raw sum
        if final not in (11, 22, 33):
            # Continue reducing if needed
            current = raw_sum
            while current > 9 and current not in (11, 22, 33):
                steps.append(current)
                current = sum(int(d) for d in str(abs(current)))
            final = current
            if final != raw_sum:
                steps.append(final)

        return LifePathNumber(
            raw_sum=raw_sum,
            reduced=final,
            life_path_type=_classify_life_path(final),
            calculation_steps=tuple(steps),
        )

    def _calculate_destiny(self, full_name: str) -> DestinyNumber:
        """Calculate Destiny/Expression Number from full birth name.

        Algorithm:
            1. Convert each letter to its Pythagorean value.
            2. Sum all values.
            3. Reduce to a single digit (or master number).

        Source: Pythagorean tradition, Cheiro Ch. 2.
        """
        letter_values: dict[str, int] = {}
        raw_sum = 0

        pyth_map = {
            "A": 1, "J": 1, "S": 1,
            "B": 2, "K": 2, "T": 2,
            "C": 3, "L": 3, "U": 3,
            "D": 4, "M": 4, "V": 4,
            "E": 5, "N": 5, "W": 5,
            "F": 6, "O": 6, "X": 6,
            "G": 7, "P": 7, "Y": 7,
            "H": 8, "Q": 8, "Z": 8,
            "I": 9, "R": 9,
        }

        for ch in full_name.upper():
            val = pyth_map.get(ch)
            if val is not None:
                letter_values[ch] = val
                raw_sum += val

        reduced = reduce_to_single_digit(raw_sum)

        return DestinyNumber(
            full_name=full_name,
            raw_sum=raw_sum,
            reduced=reduced,
            letter_values=letter_values,
        )

    def _calculate_personal_year(
        self, birth_date: str, target_year: int
    ) -> PersonalYearNumber:
        """Calculate Personal Year Number.

        Algorithm:
            1. Extract birth month and day.
            2. Sum: reduced_month + reduced_day + reduced_year.
            3. Reduce to a single digit.

        Source: Pythagorean tradition, Dan Millman Ch. 3.
        """
        parts = birth_date.split("-")
        month = int(parts[1])
        day = int(parts[2])

        month_reduced = reduce_to_single_digit(month)
        day_reduced = reduce_to_single_digit(day)
        year_reduced = reduce_to_single_digit(target_year)

        raw_sum = month_reduced + day_reduced + year_reduced
        final = reduce_to_single_digit(raw_sum)

        return PersonalYearNumber(
            birth_month=month,
            birth_day=day,
            target_year=target_year,
            raw_sum=raw_sum,
            reduced=final,
        )
