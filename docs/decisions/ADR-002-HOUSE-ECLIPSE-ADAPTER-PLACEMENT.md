# ADR-002 — House Cusp and Eclipse Adapters Live in `jyotish`, Not `astronomy`

- Status: ACCEPTED
- Date: 2026-08-12
- Related task: [JRE-003 Jyotish Coordinate and State Layer](../architecture/JRE-003-JYOTISH-CORE.md)
- Supersedes: nothing (extends ADR-001's provider discipline)
- Decision maker: Architect

## Context

JRE-003 must compute lagna, bhavas (houses), and eclipse facts. These need
astronomical capabilities that the merged JRE-002 core does **not** provide:

- House cusps / ascendant — `swe.houses` / `swe.houses_ex` (JRE-002
  deliberately excluded houses; its Specialist Spec §36.5 recorded Kundali
  ascendant as a separate future task).
- Eclipse timing — `swe.sol_eclipse_when_glob`, `swe.lun_eclipse_when`,
  `swe.sol_eclipse_where`, etc.

JRE-002 is MERGED and must remain unchanged (a new capability is not a
"compatibility defect" that would justify modifying it). The question is
where the adapters for these two new astronomical capabilities live.

## Decision

1. **New top-level package `src/jyotish/`** owns all JRE-003 capability.
2. **Planetary positions continue to come exclusively from JRE-002's public
   API** (`AstronomicalService`). JRE-003 never recomputes positions.
3. **The two new provider abstractions are defined in `jyotish`**:
   - `HouseCuspProvider` (protocol + registry) — `jyotish/houses.py`.
   - `EclipseProvider` (protocol + registry) — `jyotish/eclipse.py`.
4. **The initial Swiss Ephemeris adapters for these live in
   `jyotish/swisseph/`** (`houses.py`, `eclipse.py`, `constants.py`), not in
   `src/astronomy/swisseph/`. JRE-002 is byte-for-byte untouched.
5. Future providers (pure-Python house systems, alternative eclipse engines)
   implement the same protocols and register without touching JRE-002 or
   `jyotish` core.

Rationale:

- The hard rule "JRE-002 must remain unchanged" takes precedence over a
  hypothetical cleaner home in `astronomy`. Adding modules to
  `src/astronomy/` would modify the merged core and its static-gate surface.
- JRE-002's static tests scan only `src/astronomy`; a `jyotish` package
  importing the `swisseph` binding inside its own isolated `swisseph/`
  subpackage violates no JRE-002 gate (verified against
  `test_static.py`'s scope).
- Provider discipline is preserved: `jyotish` core depends on protocols, the
  binding is confined to one adapter subpackage (same pattern as JRE-002),
  and the astronomy providers' results are consumed through the `astronomy`
  public API only.
- Consumers of `jyotish` never see `swisseph` (static test, TEST-PLAN §8).

Rejected alternatives:

- **Extend `astronomy` with houses/eclipse adapters** — modifies the merged
  JRE-002 core; requires re-validating the astronomy package; unnecessary.
- **Compute houses/eclipses in pure Python initially** — no validated,
  offline, deterministic implementation available at this stage; the pinned
  binding provides validated results (ADR-001). Pure derivations (e.g.
  whole-sign bhavas from the ascendant) ARE used where they are exact.
- **A third package (`houses/`, `eclipses/`)** — unnecessary fragmentation;
  both are needed only by Jyotish consumers at this stage.

## Consequences

- JRE-002 remains MERGED and unmodified; its test suite and gates are
  unaffected by JRE-003.
- `jyotish` has two provider registries (houses, eclipses) in addition to
  consuming the astronomy registry through `AstronomicalService`.
- The swisseph binding is imported from exactly two production locations in
  JRE-003 (`jyotish/swisseph/houses.py`, `jyotish/swisseph/eclipse.py`),
  enforced by a static test.
- `pyproject.toml` must add `jyotish` and `jyotish.swisseph` packages and the
  `tests/*/jyotish` testpaths at CODING time (build metadata only; no JRE-002
  code changes).
- If a future provider needs the same eclipse/house data through a unified
  astronomy interface, the protocols can be re-homed behind a `jre.` namespace
  refactor — a separately versioned decision.

## References

- [JRE-002 Specialist Spec §36.5](../architecture/JRE-002-SPECIALIST-SPEC.md)
  (ascendant as a future task)
- [JRE-003 Architecture §5, §9, §14](../architecture/JRE-003-JYOTISH-CORE.md)
