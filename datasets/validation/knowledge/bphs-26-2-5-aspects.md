# BPHS ch. 26 v. 2-5 — Evaluation of planetary aspects

- **Source**: Bṛhat Parāśara Horā Śāstra (BPHS)
- **Edition**: tr. R. Santhanam, Ranjan Publications, 2001 — Chapter 26
  ("Evaluation of Planetary Aspects"), v. 2-5
- **Verifies**: `facts.json` → `aspect_strength_positions`, `special_aspects`;
  the schema doctrine constants `ASPECT_POSITION_STRENGTHS` and
  `SPECIAL_ASPECT_POSITIONS` (ADR-012)

## Excerpt (verbatim)

> 2-5. PLANETARY ASPECTS: ... 3rd and 10th, 5th and 9th, 4th and 8th and lastly
> 7th on these places the aspects increase gradually in slabs of quarters i.e.
> 1/4, 1/2, 3/4th and full. ... All planets aspect the 7th fully. Saturn,
> Jupiter and Mars have special aspects respectively on 3rd and 10th, 5th and
> 9th, and 4th and 8th.

## Reading used by the facts

- QUARTER = {3, 10}; HALF = {5, 9}; THREE_QUARTER = {4, 8}; FULL = {7}.
- Special full aspects: Saturn {3, 10}, Jupiter {5, 9}, Mars {4, 8}.
- Directional: `pair(A,B).aspect_strength` is A's glance on B, resolved from
  `relative_houses` (house of B from A).
