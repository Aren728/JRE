# JRE-004 Validation Evidence (reference excerpts)

Committed per TEST-PLAN §12 ("Independent cross-source validation") so the
VALIDATOR can verify rule citations and facts tables **offline, without
network access**.

## Licensing limitation

The full source texts (Santhanam BPHS, Sastri Bṛhat Jātaka / Jātaka Pārijāta,
Kapoor Phaladīpikā, Raman Praśna Mārgam) are **copyrighted translations** and
cannot be committed in full. This directory therefore records only **short
evidence excerpts** — one or two sentences per citation, the minimum needed to
verify a rule's meaning — together with full locators (chapter/verse/sloka,
edition, page where available) and a pointer to the source of the text used
during validation.

The complete texts were consulted during VALIDATOR (downloaded to a scratch
directory, not committed); every excerpt below is quoted verbatim from the
edition recorded in its header. Full-text copies belong to their respective
translators/publishers; quote only for scholarly verification.

## Manifest

| File | Verifies | Used by |
|---|---|---|
| `bphs-3-11-benefics-malefics.md` | natural benefic/malefic table | `facts.json` → `nature` |
| `bphs-3-49-55-dignities.md` | exaltation/debilitation/moolatrikona/own/friendship | `facts.json` → `exaltation`, `debilitation`, `moolatrikona`, `own_signs`, `natural_friendship` |
| `bphs-7-28-29-combustion.md` | combustion degrees table | `facts.json` → `combustion_degrees` |
| `bphs-26-2-5-aspects.md` | ¼/½/¾/full aspect doctrine + special aspects | `facts.json` → `aspect_strength_positions`, `special_aspects` |
| `bphs-36-3-4-gajakesari.md` | corrected `bphs.gajakesari.1` (Y1) | `rules:yoga.json` |
| `bphs-20-1-2-ninth-house.md` | corrected `bphs.bhava-9.3` | `rules:karaka.json` (bhava) |
| `bphs-32-31-34-house-significance.md` | corrected karaka/significator rules | `rules:karaka.json` |
| `phaladeepika-2-23-aspect-strength.md` | Phaladīpikā aspect doctrine (agrees with BPHS ch. 26) | `facts.json` → aspect tables |
| `phaladeepika-6-kesari-sakata.md` | corrected `phaladeepika.kesari.7`, `phaladeepika.sakata.3`, `phaladeepika.sakata-cancellation.8` | `rules:yoga.json` |
| `jataka-parijata-7-116-gajakesari.md` | corrected `jataka-parijata.gajakesari.5` (Y5) | `rules:yoga.json` |
| `prasna-marga-not-verified.md` | **negative** evidence for the two NEEDS-RESEARCH rules | `rules:yoga.json` (INACTIVE) |

Coverage per TEST-PLAN §12: at least one rule from each of BPHS, Bṛhat Jātaka,
Jātaka Pārijāta, Phaladīpikā, and a regional source (Praśna Mārgam — negative
evidence, rule held INACTIVE).

## How to add evidence

1. Quote **only** the shortest passage that establishes the rule's meaning.
2. Record edition, chapter/verse/sloka, and (if known) page number.
3. State exactly which rule/fact the excerpt supports or refutes.
