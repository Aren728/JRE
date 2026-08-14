# BPHS ch. 36 v. 3-4 — Gaja Kesari Yoga

- **Source**: Bṛhat Parāśara Horā Śāstra (BPHS)
- **Edition**: tr. R. Santhanam, Ranjan Publications, 2001 — Chapter 36 ("Many
  Other Yogas"), verses 3-4, p. 296
- **Verifies**: `bphs.gajakesari.1` (Y1) in `rules:yoga.json`

## Excerpt (verbatim)

> 3-4. GAJA KESARI YOGA: Should Jupiter be in an angle from the ascendant or
> from the Moon, and be conjunct or aspected by (another) benefice, avoiding at
> the same time debilitation, combustion and inimical sign, Gaja Kesari yoga is
> caused.

## Reading used by the rule

- Jupiter in a kendra (angle) from **the lagna or the Moon** — both arms encoded.
- Conjunct **or** aspected by a benefic — encoded as conjunction-with-benefic
  (Moon or Venus) or directional classical aspect (`aspect_strength` EXISTS).
- Free of debilitation, combustion and inimical sign — encoded as
  `dignity ∈ {EXALTED, MULATRIKONA, OWN, FRIEND, NEUTRAL}` and
  `combusted = false`.

Note: this is the *fourth* yoga chapter's verse; the original authored
citation ("ch. 25 v. 12") was INCORRECT — ch. 25 is "Effects of Non-Luminous
Planets". The corrected citation is ch. 36 v. 3-4.
