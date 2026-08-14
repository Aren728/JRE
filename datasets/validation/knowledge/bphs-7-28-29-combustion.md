# BPHS ch. 7 (notes to v. 28-29) — combustion table

- **Source**: Bṛhat Parāśara Horā Śāstra (BPHS)
- **Edition**: tr. R. Santhanam, Ranjan Publications, 2001 — Chapter 7
  ("Divisional Consideration"), notes to v. 28-29
- **Verifies**: `facts.json` → `combustion_degrees`

## Excerpt (verbatim)

> Please see the following table for degrees of combustion.

> | Planet   | Combustion in direct motion | Combustion in (R) motion |
> |----------|-----------------------------|--------------------------|
> | Moon     | 12°                         | —                        |
> | Mars     | 17°                         | 8°                       |
> | Mercury  | 14°                         | 12°                      |
> | Jupiter  | 11°                         | —                        |
> | Venus    | 10°                         | 8°                       |
> | Saturn   | 16°                         | —                        |

## Reading used by the facts

- Thresholds recorded exactly as above; bodies with no retrograde column
  (Moon, Jupiter, Saturn) use the direct value for retrograde motion too.
- Rahu and Ketu do not appear in the table and are never combust; the Sun is
  the combustion source and is itself never combust.
- `combusted = separation_from_sun <= threshold`, using the shortest angular
  separation from the snapshot `pair(SUN, <BODY>)` entries.
