"""JRS-073 Temporal Refinements — refinement service.

``TemporalRefinementService`` generates ``TemporalModifier`` objects
for Dasha sandhi (boundary) periods and eclipse visibility windows.

These modifiers are consumed by the convergence engine to adjust
evidence weight scalars in time-bound contexts.

Sources:
    - BPHS Dasha Vigyana Ch. 8: Sandhi periods carry transitional
      uncertainty; evidence weight should taper near boundaries.
    - BPHS Graha Pravesh Ch. 18 / Phaladeepika Ch. 14: Eclipse
      windows amplify malefic and dampen benefic influences.
"""

from __future__ import annotations

from typing import Any

from jrs.temporal.models import TemporalTrigger, parse_iso_timestamp

from .models import ModifierType, TemporalModifier


class TemporalRefinementService:
    """Generates TemporalModifier objects for temporal refinements.

    Usage::

        svc = TemporalRefinementService()
        sandhi_mods = svc.calculate_dasha_sandhi(dasha_periods)
        eclipse_mods = svc.calculate_eclipse_windows(eclipse_events)
        all_mods = svc.apply_modifiers(records, sandhi_mods + eclipse_mods)
    """

    def calculate_dasha_sandhi(
        self,
        dasha_periods: tuple[TemporalTrigger, ...],
        buffer_days: int = 15,
    ) -> tuple[TemporalModifier, ...]:
        """Generate Dasha sandhi modifiers for period boundaries.

        At exact Dasha boundaries, evidence weight is reduced (e.g., 0.5).
        The weight tapers linearly from the boundary value to 1.0 outside
        the buffer window.

        Classical source: BPHS Dasha Vigyana Ch. 8 — transitional periods
        at Dasha boundaries carry uncertainty and should not be treated
        as equivalent to the stable middle of a period.

        Args:
            dasha_periods: Tuple of TemporalTrigger objects with
                activation_start_utc and activation_end_utc.
            buffer_days: Number of days on each side of the boundary
                within which the sandhi penalty applies.

        Returns:
            A tuple of TemporalModifier objects, two per Dasha period
            (one for start boundary, one for end boundary).
        """
        modifiers: list[TemporalModifier] = []
        half_buffer = buffer_days / 2.0

        for period in dasha_periods:
            start_str = period.activation_start_utc
            end_str = period.activation_end_utc

            if not start_str or not end_str:
                continue

            start_dt = parse_iso_timestamp(start_str)
            end_dt = parse_iso_timestamp(end_str)

            if start_dt is None or end_dt is None:
                continue

            # Start boundary: taper from 0.5 at boundary to 1.0 at edge
            start_modifier = self._build_boundary_modifier(
                boundary_time=start_str,
                period_start=start_str,
                period_end=end_str,
                buffer_days=half_buffer,
                boundary_weight=0.5,
                description=(
                    f"Dasha sandhi at start of "
                    f"{period.triggering_planet} period"
                ),
            )
            if start_modifier is not None:
                modifiers.append(start_modifier)

            # End boundary: taper from 0.5 at boundary to 1.0 at edge
            end_modifier = self._build_boundary_modifier(
                boundary_time=end_str,
                period_start=start_str,
                period_end=end_str,
                buffer_days=half_buffer,
                boundary_weight=0.5,
                description=(
                    f"Dasha sandhi at end of "
                    f"{period.triggering_planet} period"
                ),
            )
            if end_modifier is not None:
                modifiers.append(end_modifier)

        return tuple(modifiers)

    def calculate_eclipse_windows(
        self,
        eclipse_events: tuple[TemporalTrigger, ...],
        malefic_amplify: float = 1.2,
        benefic_dampen: float = 0.8,
    ) -> tuple[TemporalModifier, ...]:
        """Generate eclipse window modifiers.

        During an eclipse visibility window:
        - Malefic evidence is amplified (weight > 1.0).
        - Benefic evidence is dampened (weight < 1.0).

        Classical source: BPHS Graha Pravesh Ch. 18, Phaladeepika
        Ch. 14 — eclipses strengthen malefic conditions and weaken
        benefic conditions during the visibility window.

        Args:
            eclipse_events: Tuple of TemporalTrigger objects with
                activation_start_utc and activation_end_utc.
            malefic_amplify: Weight scalar for malefic evidence (default 1.2).
            benefic_dampen: Weight scalar for benefic evidence (default 0.8).

        Returns:
            A tuple of TemporalModifier objects, one per eclipse event.
        """
        modifiers: list[TemporalModifier] = []

        for event in eclipse_events:
            start_str = event.activation_start_utc
            end_str = event.activation_end_utc

            if not start_str or not end_str:
                continue

            # Malefic amplification modifier
            malefic_mod = TemporalModifier(
                modifier_type=ModifierType.ECLIPSE_WINDOW,
                start_time=start_str,
                end_time=end_str,
                weight_scalar=malefic_amplify,
                event_window_start_utc=start_str,
                event_window_end_utc=end_str,
                description=(
                    f"Eclipse malefic amplification "
                    f"({malefic_amplify}x) during "
                    f"{event.triggering_planet} eclipse"
                ),
            )
            modifiers.append(malefic_mod)

            # Benefic dampening modifier
            benefic_mod = TemporalModifier(
                modifier_type=ModifierType.ECLIPSE_WINDOW,
                start_time=start_str,
                end_time=end_str,
                weight_scalar=benefic_dampen,
                event_window_start_utc=start_str,
                event_window_end_utc=end_str,
                description=(
                    f"Eclipse benefic dampening "
                    f"({benefic_dampen}x) during "
                    f"{event.triggering_planet} eclipse"
                ),
            )
            modifiers.append(benefic_mod)

        return tuple(modifiers)

    def apply_modifiers(
        self,
        records: tuple[Any, ...],
        modifiers: tuple[TemporalModifier, ...],
    ) -> tuple[dict[str, Any], ...]:
        """Apply temporal modifiers to evidence records.

        For each record, checks if any modifier's time window contains the
        record's activation time.  If so, applies the weight_scalar.

        Args:
            records: Evidence records with strength attributes.
            modifiers: Temporal modifiers to apply.

        Returns:
            A tuple of dicts with 'record' and 'effective_weight' keys,
            showing the effective weight for each record after modifier
            application.
        """
        results: list[dict[str, Any]] = []

        for record in records:
            # Try to get the record's time window
            record_start = getattr(record, "activation_start_utc", None)
            record_end = getattr(record, "activation_end_utc", None)

            # Check each modifier
            effective_weight = 1.0
            applied_modifiers: list[str] = []

            for modifier in modifiers:
                if self._record_overlaps_modifier(
                    record_start, record_end, modifier,
                ):
                    effective_weight *= modifier.weight_scalar
                    applied_modifiers.append(modifier.deterministic_id)

            results.append({
                "record": record,
                "effective_weight": effective_weight,
                "applied_modifiers": applied_modifiers,
            })

        return tuple(results)

    def _build_boundary_modifier(
        self,
        boundary_time: str,
        period_start: str,
        period_end: str,
        buffer_days: float,
        boundary_weight: float,
        description: str,
    ) -> TemporalModifier | None:
        """Build a single boundary modifier with tapering weight.

        The modifier window extends buffer_days on each side of the
        boundary.  At the exact boundary, weight = boundary_weight.
        At the edge of the buffer, weight = 1.0.  The weight_scalar
        in the modifier represents the *minimum* weight (at the boundary).

        Classical source: BPHS Dasha Vigyana Ch. 8.
        """
        from datetime import timedelta

        boundary_dt = parse_iso_timestamp(boundary_time)
        if boundary_dt is None:
            return None

        buffer = timedelta(days=buffer_days)
        mod_start_dt = boundary_dt - buffer
        mod_end_dt = boundary_dt + buffer

        # Clamp to the Dasha period boundaries
        period_start_dt = parse_iso_timestamp(period_start)
        period_end_dt = parse_iso_timestamp(period_end)

        if period_start_dt is not None and mod_start_dt < period_start_dt:
            mod_start_dt = period_start_dt
        if period_end_dt is not None and mod_end_dt > period_end_dt:
            mod_end_dt = period_end_dt

        if mod_start_dt >= mod_end_dt:
            return None

        return TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time=mod_start_dt.isoformat(),
            end_time=mod_end_dt.isoformat(),
            weight_scalar=boundary_weight,
            event_window_start_utc=period_start,
            event_window_end_utc=period_end,
            description=description,
        )

    @staticmethod
    def _record_overlaps_modifier(
        record_start: str | None,
        record_end: str | None,
        modifier: TemporalModifier,
    ) -> bool:
        """Check if a record's time window overlaps with a modifier."""
        if record_start is None and record_end is None:
            return False

        # Use record_start as the representative timestamp
        ts = record_start or record_end
        if ts is None:
            return False

        return modifier.applies_at(ts)
