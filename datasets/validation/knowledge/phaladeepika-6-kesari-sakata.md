# Phaladīpikā ch. 6 — Kesari, Sakata and the Sakata cancellation

- **Source**: Phaladīpikā (Mantreśvara)
- **Edition**: tr. Dr. G. S. Kapoor (Ranjan Publications; undated scan) — Chapter 6
  (yogas), following v. 14, p. 62
- **Verifies**: `phaladeepika.kesari.7`, `phaladeepika.sakata.3` and
  `phaladeepika.sakata-cancellation.8` in `rules:yoga.json`

## Excerpt (verbatim)

> Kesari Yoga is caused when in a birth chart the Moon is in a Kendra position
> to Jupiter.
>
> The Moon in the 12th, 8th or 6th house from Jupiter causes Sakata Yoga.
> The Sakata Yoga is cancelled if the Moon be in a Kendra position from the
> Ascendant (lagna).

## Reading used by the rules

- **Kesari** (`.kesari.7`): `relative_house(MOON, JUPITER) ∈ {1,4,7,10}`.
- **Sakata** (`.sakata.3`): `relative_house(MOON, JUPITER) ∈ {12,8,6}`.
- **Cancellation** (`.sakata-cancellation.8`): `relative_house(MOON, LAGNA)
  ∈ {1,4,7,10}`, declared as an `exception_for` the Sakata rule.

These are the *Jupiter-referenced* forms — the reason `RELATIVE_HOUSE_REFS`
was extended to all nine grahas in FACT_VOCABULARY v1.1.0 (ADR-012).

Note: the original authored citation ("ch. 6 v. 12") was INCORRECT — v. 12 is
the Amala yoga; the Kesari/Sakata definitions sit in the notes following
v. 14. The edition record was also corrected from "Chiranjiva Sharma" to the
Kapoor translation actually verified.
