# ADR-005 — Continuous Transit Engine: Deterministic Event Search with Memoization

- Status: ACCEPTED
- Date: 2026-08-12
- Related task: [JRE-003 Jyotish Coordinate and State Layer](../architecture/JRE-003-JYOTISH-CORE.md)
- Decision maker: Architect

## Context

Requirement E forbids representing a transit as a bare bucket ("Jupiter =
Sagittarius") and demands queries: Rashi/Nakshatra/Pada ingress and egress
times, station (retrograde/direct) times, exact degree at an instant, and
complete interval state. These are **root-finding problems** over the
continuous longitude function `λ(t)` and its speed `v(t) = dλ/dt`. Two risks
dominate:

1. **Determinism**: iterative search can be made nondeterministic by
   iteration-order dependence, wall-clock-based stopping, or floating-point
   drift.
2. **Cost**: JRE-002 deliberately shipped without caching (Specialist Spec
   §30) and documented the revisit condition: "if a consumer batches many
   instants, add a process-scoped memo". JRE-003 is exactly that consumer.

## Decision

### 1. Event search algorithm (fixed, versioned)

- **Sample**: `f(t) = λ_used(t) − boundary` (for ingress/egress) or
  `v(t)` (for stations), sampled at a fixed step
  (`transit_sample_step_hours = 6.0`, configurable, versioned).
- **Sign-change isolation**: every interval where `f` changes sign is an
  event candidate. **Retrograde re-crossings are honored**: a body may enter
  a sign, go retrograde, exit, and re-enter within one query interval — each
  sign change produces its own `TransitEvent` (no merging, no dropping).
  Wrap-around at 0°/360° is handled by unwrapping `λ` (adding/subtracting
  360° to preserve continuity) before differencing.
- **Root refinement**: bisection on each isolated monotonic segment to
  `transit_tolerance_jd = 1e-4` (≈ 8.6 s), bounded by a fixed iteration cap
  (e.g. 60). Non-convergence raises `TransitSearchError` (never a silent
  approximation).
- **Determinism**: fixed step, fixed tolerance, fixed iteration cap, no wall
  clock, no randomness, no dependence on iteration order. Every event echoes
  `SearchMetadata` (algorithm, step, tolerance, iterations, position-call
  count) so the exact parameters that produced it are auditable.

### 2. Position memoization (bounded, process-scoped, pure)

- A process-scoped cache keyed by the exact tuple
  `(julian_day_ut, bodies, CalculationConfig)` (plus zodiac mode for
  classification caches) maps to the computed `PlanetState`s.
- It is a **pure memo of a pure function**: same key ⇒ same value, so
  determinism is unaffected (requirement K).
- Bounded (e.g. LRU of 10 000 entries) to keep the 2-core/4 GB target
  (architecture §22).

### 3. API shape

- `position_at(jd, bodies, config) -> tuple[PlanetState, ...]`
- `events_between(start_jd, end_jd, bodies, kinds, config) -> tuple[TransitEvent, ...]`
- `state_series(start_jd, end_jd, step, bodies, config) -> tuple[PlanetState, ...]`
- All UTC-in / UTC-out; timezone is presentation-only.

Rationale: bisection on monotonic segments is the simplest algorithm with a
provable convergence bound and zero tunable surprises; the memoization
revisit condition documented in JRE-002 §30 is precisely met by the transit
engine's sampling workload. Together they make the continuous model exact,
fast, and reproducible.

Rejected alternatives:

- **Closed-form event times** — λ(t) and v(t) have no closed form; every
  ephemeris (including Swiss Ephemeris itself) finds events by iteration.
- **Using a coarse table as the answer** (e.g. "Jupiter in Sagittarius on
  these dates") — violates requirement E's continuity mandate.
- **Unbounded caching** — memory risk on the low-resource target.
- **Sampling adaptively with wall-clock feedback** — nondeterministic.

## Consequences

- Every transit query is reproducible to the second (tolerance) across runs,
  hosts, and processes (cross-process test, TEST-PLAN §4).
- Event counts are exact: a retrograde planet produces multiple genuine
  events; tests assert these against independent ephemeris/panchanga data.
- `position_calls` in `SearchMetadata` lets QA/VALIDATOR measure the
  memoization effect.
- Cache parameters (size, eviction) are CODING-time constants recorded in
  the specialist spec, not runtime config — determinism must not depend on
  cache state.

## References

- [JRE-002 Specialist Spec §30 (caching revisit)](../architecture/JRE-002-SPECIALIST-SPEC.md)
- [JRE-003 Architecture §11, §17, §22](../architecture/JRE-003-JYOTISH-CORE.md)
