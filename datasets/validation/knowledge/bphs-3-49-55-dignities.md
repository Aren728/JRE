# BPHS ch. 3 v. 49-55 — Exaltation, debilitation, moolatrikona, own signs, natural relationships

- **Source**: Bṛhat Parāśara Horā Śāstra (BPHS)
- **Edition**: tr. R. Santhanam, Ranjan Publications, 2001 — Chapter 3, v. 49-55
- **Verifies**: `facts.json` → `exaltation`, `debilitation`, `moolatrikona`,
  `own_signs`, `natural_friendship`; `rashi_lords` from ch. 4 (see note)

## Excerpts (verbatim)

> 49-50. EXALTATION AND DEBILITATION: For the seven planets from the Sun on,
> the signs of exaltation are respectively Aries, Taurus, Capricorn, Virgo,
> Cancer, Pisces and Libra. ... And in the seventh sign from the said
> exaltation sign each planet has its own debilitation.

> 51-54. ADDITIONAL DIGNITIES: In Leo, the first 20 degrees are the Sun's
> Moola-Trikona while the rest is his own house. After the first 3 degrees of
> exaltation portion in Taurus, for the Moon the rest is her Moola-Trikona.
> Mars has the first 12 degrees in Aries as Moola-Trikona ... Mercury, in
> Virgo ... Venus divides Libra into two halves keeping the first as
> Moola-Trikona and the second as own house. Saturn's arrangements are same in
> Aquarius as the Sun has in Leo.

> 55. NATURAL RELATIONSHIPS: Note the signs which are the 4th, 2nd, 12th, ...
> [from the moolatrikona, plus the lord of the exaltation sign — friendship
> algorithm].

## Reading used by the facts

- Exaltation: SUN→MESHA, MOON→VRISHABHA, MARS→MAKARA, MERCURY→KANYA,
  JUPITER→KARKA, VENUS→MEENA, SATURN→TULA; debilitation = 7th sign from it.
- Moolatrikona: SUN→SIMHA, MOON→VRISHABHA, MARS→MESHA, MERCURY→KANYA,
  JUPITER→DHANUSHA, VENUS→TULA, SATURN→KUMBHA (whole-sign granularity; the
  degree zones inside a sign are not modelled).
- Own signs follow the ch. 4 sign descriptions (each sign's ruler, e.g. Leo by
  the Sun, Cancer by the Moon) — the same ch. 4 verses feed `rashi_lords`.
- `natural_friendship` is derived exactly from the v. 55 algorithm
  (lords of the 2nd/4th/5th/8th/9th/12th from the moolatrikona + the
  exaltation lord; planets on both lists are neutral, including
  exaltation-lord conflicts per the Notes' worked example "Saturn becomes
  equal to Mars"; the planet itself is never listed).
