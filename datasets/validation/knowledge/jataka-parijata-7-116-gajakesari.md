# Jātaka Pārijāta Adhyāya VII, sloka 116 — Gajakesari

- **Source**: Jātaka Pārijāta (Vaidyanātha Dīkṣita)
- **Edition**: tr. V. Subrahmanya Sastri, 1932 — Adhyāya VII, sloka 116
- **Verifies**: `jataka-parijata.gajakesari.5` (Y5) in `rules:yoga.json`

## Excerpt (verbatim)

> Sloka 116. When Jupiter occupies a kendra from the Moon, the yoga produced is
> called Gajakesari. Again if the Moon be aspected by planets, Venus, Jupiter
> and Mercury without being depressed or obscured by the Sun, the yoga produced
> is also Gajakesari.

## Reading used by the rule

Two forms, both encoded as ANY arms:

1. Jupiter in a kendra from the Moon (`relative_house(JUPITER, MOON) ∈
   {1,4,7,10}`).
2. The Moon aspected by Venus/Jupiter/Mercury (classical `aspect_strength`
   EXISTS on any of the three pairs) and not combust (`combusted = false`).

Note: the original authored citation ("ch. 8 v. 6") was INCORRECT — ch. VIII
v. 6 is the Trigraha yoga. Sloka numbering follows the Sastri translation
(Adhyāya VII, sloka 116).

## Conflict with Y1

Both Y1 (BPHS) and Y5 (JP) define "Gaja-Kesari"; their mutual
`conflicts_with` is preserved so a profile picks one winner (FIRST_WINS).
