# ADR-006 — Eclipse Engine: Interface, Initial Provider, and Data-Only Boundary

- Status: ACCEPTED
- Date: 2026-08-12
- Related task: [JRE-003 Jyotish Coordinate and State Layer](../architecture/JRE-003-JYOTISH-CORE.md)
- Decision maker: Architect

## Context

Requirement H mandates a **defined interface** for astronomical eclipse
information: solar/lunar eclipses, contact/maximum/end times where available,
geometry, classification, geographic visibility where available, associated
planetary/node positions, and pre/post event intervals **as data** — with the
explicit rule that the layer must never claim an eclipse causes wealth, loss,
war, illness, marriage, career, spiritual events, or anything else.

The pinned binding (pysweph 2.10.03, ADR-001) exposes eclipse functions
(`sol_eclipse_when_glob`, `sol_eclipse_where`, `lun_eclipse_when`,
`sol_eclipse_how`, `lun_eclipse_how`) but **not** the `SEFLG_ECL_*` named
constants (empirically verified). Stable raw C-header values are required
(e.g. `SEFLG_ECL_LIGHT = 0x8000`, `SEFLG_ECL_CENTRAL = 0x10000`,
`SEFLG_ECL_PENUMBRA = 0x20000`), and they work (verified against the total
solar eclipse of 1991-07-11 and total lunar eclipse of 1990-02-09).

## Decision

### 1. Interface (the contract)

```python
class EclipseProvider(Protocol):
    provider_id: str
    def find_eclipses(self, jd_start: float, jd_end: float,
                      kind: EclipseKind | None,
                      config: JyotishConfig) -> tuple[EclipseEvent, ...]: ...
```

- `kind=None` searches both solar and lunar.
- Deterministic: identical interval + config ⇒ identical events and times.
- Any future eclipse engine implements this protocol and registers in the
  `jyotish` eclipse registry (ADR-002).

### 2. Initial provider: the pinned binding, with documented constants

- `jyotish/swisseph/constants.py` defines the `SEFLG_ECL_*` raw values once,
  with a citation to the Swiss Ephemeris C header — no magic numbers in
  other modules, and no reliance on unexposed binding names.
- `jyotish/swisseph/eclipse.py` maps `find_eclipses` onto the binding's
  global eclipse routines; per-call state discipline and the module lock
  follow the JRE-002 adapter pattern (ADR-001).
- Geographic visibility is included **where available** (`sol_eclipse_where`).

### 3. Data-only boundary (requirement H)

- `EclipseEvent` carries astronomical facts only: kind, classification,
  contact/maximum/end times, magnitude, geometry, node and Sun/Moon positions
  at maximum, visibility, and `pre_/post_event_interval_days` describing the
  temporal extent of phases.
- **No causation, no significance.** No field, enum, or message implies an
  effect on wealth, health, events, or fate. Static gate
  (`test_no_interpretation_vocabulary`) covers `src/jyotish`, including the
  eclipse module (TEST-PLAN §8).
- Interpretation of eclipse facts belongs to future layers (requirement I).

### 4. Validation

- Independent comparison against the NASA Five Millennium Canon of Eclipses
  (times, classification, magnitude) and published eclipse tables — never
  against JRE's own output (TEST-PLAN §12, VALIDATOR).

Rationale: the binding provides validated, offline, deterministic eclipse
arithmetic consistent with the pinned ephemeris (ADR-001). Defining the
protocol first keeps the engine swappable; documenting the raw constants with
citation keeps the adapter honest when the binding's Python surface omits
names. The data-only rule is enforced structurally, not just by convention.

Rejected alternatives:

- **A pure-Python eclipse engine initially** — no validated offline
  implementation available at this stage; large, error-prone surface for no
  benefit when the binding already provides it.
- **Hardcoding `SEFLG_ECL_*` values inline at call sites** — violates the
  constants discipline used throughout JRE-002; all values centralized and
  cited instead.
- **No geographic visibility at all** — requirement H says "where available";
  the binding provides it, so it is included with a `None` fallback.
- **Including eclipse "significance" data** — prohibited by requirement H.

## Consequences

- JRE-003 can answer "eclipses in interval X" deterministically and offline.
- The raw-constant decision is versioned and auditable; if a future binding
  release exposes named constants, the adapter can switch behind the same
  protocol (versioned decision).
- VALIDATOR must confirm eclipse times/classification against the NASA
  catalog before MERGE.
- Interpretation layers later consume `EclipseEvent` facts without touching
  the eclipse engine.

## References

- [JRE-003 Architecture §14, §23](../architecture/JRE-003-JYOTISH-CORE.md)
- [JRE-003 Data Contract §9](../architecture/JRE-003-DATA-CONTRACT.md)
- [ADR-001 Ephemeris Provider](ADR-001-EPHEMERIS-PROVIDER.md)
