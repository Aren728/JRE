# JRE-006 — Gochar / Continuous Transit Engine

Status: SPECIALIST-COMPLETE
Priority: HIGH

## Objective

Create the deterministic **gochar / continuous transit state layer** that
consumes JRE-003 transit primitives (positions, classification, event
search) and JRE-005 derived house facts, and produces structured,
machine-readable **transit state and interval facts** (instant gochar
state, transit-to-natal relationships, deterministic event streams over
date ranges) for downstream interpretation layers (dasha, drishti, yoga,
synthesis). JRE-006 is a composition/derivation layer: it echoes and
derives, never recomputes positions, cusps, lagna, geometry, or
event-search results, and it never interprets.

## Repository baseline

- JRE-002 — `78aff38` (MERGED)
- JRE-003 — `e568a64` + additive public API commits `06d551f`, `339f393`
  (MERGED; current JRE-003 public surface)
- JRE-004 — `04bbaf9` (MERGED)
- JRE-005 — `92085ff` (MERGED)
- Working tree is clean at `92085ff`.

## Required Inputs (all consumed from public APIs)

JRE-003 (`jyotish` public root only — ADR-013 boundary style):

- `JyotishService.planetary_state` / `position_at` — instant transit
  planet states (longitude, rashi, nakshatra, pada, retrograde, speed).
- `JyotishService.state_series` — sampled continuous states over an
  ISO-UTC interval.
- `JyotishService.events_between` — deterministic ingress/egress/station
  events (ADR-005 bisection engine), closed interval.
- `JyotishService.pair_geometry` — instant transit-transit and
  transit-to-natal aspect geometry (ADR-004).
- `JyotishService.chart` — natal chart (birth snapshot echo, lagna,
  bhavas, planet states, provider metadata, catalog versions).
- `JyotishService.transit_through_houses` — transit instant against a
  natal chart per explicit reference (LAGNA/MOON/SUN/ASC).
- `TransitEvent` / `TransitEventKind` / `SearchMetadata` /
  `TransitReferencePoint` / `TransitThroughHouses` / `HouseTransitEntry`
  — echoed types, never redefined.
- `iso_utc_to_jd` / `jd_to_iso_utc` — canonical time conversion.
- `RASHI_CATALOG_VERSION`, `NAKSHATRA_CATALOG_VERSION` — provenance pins.

JRE-005 (`bhava` public root only):

- `derive_transit_analysis(TransitThroughHouses)` — natal-frame transit
  house facts (`TransitHouseFact`, `FactFrame.TRANSIT`).
- `relative_house` — natal-frame relative-house arithmetic (ADR-014).

## Required Outputs (derived facts)

- **Instant gochar state** (GENERIC): transit planet states + rashi /
  nakshatra / pada / retrograde echoes; optional transit-transit pair
  geometry echo.
- **Instant transit-to-natal facts** (INDIVIDUAL): per transit body —
  natal-frame house number/rashi (via JRE-005), aspects to natal planets
  (echo), retrograde/node state echo, reference-point echo.
- **Interval facts**: deterministic event stream (echo of
  `events_between`, re-asserted pinned ordering), sampled state series
  (echo), optional natal-frame house series (config-gated sampling).
- **Provenance** on every fact: source layers, catalog/ephemeris
  versions, derivation identity/version, input echo — no
  environment-dependent data.
- Deterministic serialization (JSON round-trip, Schema with
  `additionalProperties=false`).

## Separation Requirement

- **JRE-002** = astronomy / exact planetary positions.
- **JRE-003** = Jyotish coordinate + planetary state + continuous event
  search (positions, classification, cusps, geometry, ingress/egress,
  stations).
- **JRE-005** = derived bhava/house facts (natal and transit instants).
- **JRE-006** = gochar / continuous transit **state facts** — the
  composition layer over JRE-003 primitives and JRE-005 house facts,
  including transit-to-natal relationships and deterministic interval
  event facts.
- **JRE-004** = classical knowledge/rules/provenance/conflict/resolution.
- **JRE-007** (future) = eclipse engine — eclipse detection is out of
  JRE-006 scope.
- **Future synthesis** = interpretation/prediction.

JRE-006 MUST NOT interpret: no dasha, no prediction, no yoga
declarations, no benefic/malefic, no auspiciousness, no gochar
judgements, no drishti doctrine, no classical rule resolution. The word
"transit" here means structural transit-state handling only.

## Determinism

- Every externally observable result is a pure function of: the input
  query (interval bounds, bodies, reference point, house system, config)
  and the pinned catalog/ephemeris versions. Repeated in-process and
  cross-process runs produce byte-identical serialized output.
- Event ordering uses the pinned sort key
  `(event_julian_day_ut, body.value, kind.value)` — re-asserted, never
  derived from set/dict iteration.
- Echoed JRE-003/JRE-005 results are copied verbatim; no re-derivation
  that could diverge.

## Public API readiness

Preliminary audit (ARCHITECT): every v0.1 required capability is
**AVAILABLE** on the current public JRE-003/JRE-005 surfaces. Three
capabilities are **DEFERRED to v0.2** because the public API lacks them
(generic natal-free transit chart; cusp-based house-ingress events over
time; continuous aspect events with applying/exact/separating
timestamps) — each recorded with a minimal additive JRE-003 API
proposal in the architecture core doc. No FORBIDDEN_WORKAROUND is
required for v0.1.

## Stage history

### Architect stage

- Delivered: [JRE-006 architecture core](../../docs/architecture/JRE-006-GOCHAR-TRANSIT-ENGINE.md)
  (boundary definition, continuous transit model, event model,
  retrograde/station model, aspect model, reference-frame model,
  precision/time model, provenance model, serialization model,
  performance model, eclipse/JRE-007 boundary, public-API readiness
  audit, risk register), [data contract](../../docs/architecture/JRE-006-DATA-CONTRACT.md),
  [test plan](../../docs/architecture/JRE-006-TEST-PLAN.md),
  [ADR-022](../../docs/decisions/ADR-022-GOCHAR-LAYER-BOUNDARY.md) …
  [ADR-028](../../docs/decisions/ADR-028-GOCHAR-PROVENANCE-ECHO.md).
- **Verdict: ARCHITECTURE-COMPLETE — SPECIALIST REQUIRED.**
- Advanced to ARCHITECT-COMPLETE (SPECIALIST status reserved for
  SPECIALIST).

### Specialist stage

- Delivered: [specialist spec](../../docs/architecture/JRE-006-SPECIALIST-SPEC.md)
  v0.2.0 (normative at CODING): zero new enums, 4-error taxonomy,
  field-level result/request models, instant/interval derivation paths,
  inherited event/station semantics, endpoint-semantics correction,
  aspect-state echo (ADR-029), reference-frame invariants, precision &
  time rules, deterministic ordering, provenance, serialization,
  performance budgets, static gates, CODING handoff checklist.
- Finalized [data contract](../../docs/architecture/JRE-006-DATA-CONTRACT.md) v0.2.0
  and [test plan](../../docs/architecture/JRE-006-TEST-PLAN.md) v0.2.0;
  added [ADR-029](../../docs/decisions/ADR-029-ASPECT-STATE-ECHO-EVENTS-DEFERRED.md).
- Specialist verification: public-API audit (14/14 v0.1 dependencies
  AVAILABLE; no JRE-002 additive API required); empirical boundary
  probe confirmed start-exact events included and exact-`end` events
  not guaranteed (inherited JRE-003 limitation — documented, not
  compensated); `ApplyingSeparating` confirmed as echo-able state.
- **Verdict: SPECIALIST-COMPLETE — API READY FOR CODING.** No
  implementation; JRE-002/003/004/005 untouched.
- Advanced to SPECIALIST-COMPLETE (CODING status reserved for CODING).

## Change history

- 2026-08-14 — ARCHITECT-COMPLETE: architecture, data contract, test
  plan, ADR-022..028, queue item created.
- 2026-08-14 — SPECIALIST-COMPLETE: specialist spec v0.2.0 + finalized
  data contract/test plan v0.2.0 + ADR-029; endpoint semantics
  corrected; aspect state/event boundary pinned.
