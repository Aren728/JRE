# JRE-007 — Canonical Context & Fact Snapshot

Status: IMPLEMENTED
Priority: HIGH

## Objective

Create the deterministic **canonical context and fact snapshot layer** that
assembles one canonical, provenance-bearing snapshot of *already-computed*
lower-layer facts (JRE-002/003/005/006) and hands it to future engines
(Varga, Dasha, Drishti, Karaka, Avastha, Yoga, Bala, Ashtakavarga, Tajika,
Jaimini, Prashna, Muhurta, Rectification). JRE-007 computes **nothing new**:
no positions, cusps, lagna, geometry, aspects, event searches, eclipses, or
house facts; no doctrine; no rule matching; no interpretation; no prediction.

## Repository baseline

- JRE-002 — `78aff38` (MERGED)
- JRE-003 — `e568a64` + additive public API commits `06d551f`, `339f393`
  (MERGED; current JRE-003 public surface)
- JRE-004 — `04bbaf9` (MERGED)
- JRE-005 — `92085ff` (MERGED)
- JRE-006 — `e9fd670` (MERGED)
- Working tree was clean at `e9fd670` before JRE-007 implementation.

## Required Inputs (all consumed from public APIs)

JRE-003 (`jyotish` public root only):
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
- `JyotishService.eclipses` — eclipse facts (JRE-003 echo, ADR-006/027).
- `JyotishConfig` — ayanamsa, zodiac mode, house system, node model.
- `RASHI_CATALOG_VERSION`, `NAKSHATRA_CATALOG_VERSION` — provenance pins.

JRE-005 (`bhava` public root only):
- `BhavaService.analyze_chart` — natal-frame house analysis.
- `BhavaConfig` — house systems, tradition profile.

JRE-006 (`gochar` public root only):
- `GocharInstantResult` / `GocharNatalResult` / `GocharIntervalResult` —
  transit state echoes (opaque to JRE-007).

## Required Outputs (derived facts)

- **CanonicalContext** — the top-level deterministic context container
  (context id, purpose, birth echo, configuration, capability manifest,
  chart identity, source layers).
- **CanonicalFactSnapshot** — the envelope: natal chart echo, planet
  states, pair geometry, house analyses, transit event/state echoes,
  gochar echoes, eclipse echoes (JRE-003, ADR-006/027), and the
  six-stage provenance chain (SPEC §3/§16).
- **FactEnvelope** / **FactKind** / **CapabilityManifest** /
  **CapabilityState** (`AVAILABLE` / `NOT_REQUESTED` / `UNAVAILABLE`) —
  the capability-accounting and fact-addressing model.
- **ContextService** — facade: `snapshot_instant` (GENERIC),
  `snapshot_natal` (INDIVIDUAL), `snapshot_interval`,
  `snapshot_eclipses` (JRE-003 echo, ADR-006/027).
- **Four frozen V1 capabilities**: `instant`, `natal`, `interval`, `eclipse`.
- Natal/transit separation is structural: natal sections (`natal_chart` /
  `house_analyses`) and transit sections (`transit_events` /
  `state_samples`) are independent optional fields and are never merged
  (SPEC §17, ADR-021/025).
- Deterministic serialization (JSON round-trip, Schema with
  `additionalProperties=false`).

## Separation Requirement

- **JRE-002** = astronomy / exact planetary positions.
- **JRE-003** = Jyotish coordinate + planetary state + continuous event
  search (positions, classification, cusps, geometry, ingress/egress,
  stations).
- **JRE-004** = classical knowledge/rules/provenance/conflict/resolution.
- **JRE-005** = derived bhava/house facts (natal and transit instants).
- **JRE-006** = gochar / continuous transit state facts.
- **JRE-007** = canonical context & fact snapshot — the composition layer
  that assembles lower-layer facts into a provenance-bearing envelope
  for future engines.
- **JRE-008** (varga) = divisional chart engine — consumes JRE-003
  `PlanetState` facts, not JRE-007 directly (opaque join via
  `chart_identity`).
- **Future synthesis** = interpretation/prediction.

JRE-007 MUST NOT interpret: no dasha, no prediction, no yoga
declarations, no benefic/malefic, no auspiciousness, no gochar
judgements, no drishti doctrine, no classical rule resolution, no
varga computation, no avastha, no bala, no ashtakavarga, no karaka
doctrine, no confidence, no eclipse significance, no interval
arithmetic.

## Determinism

- Every externally observable result is a pure function of: the input
  query (instant/interval bounds, bodies, birth data, config) and the
  pinned catalog/ephemeris versions. Repeated in-process and
  cross-process runs produce byte-identical serialized output.
- `chart_identity` is a deterministic SHA-256 fingerprint of chart facts
  (birth echo, lower-layer configs, catalog versions) — no wall-clock
  data (ADR-028).
- Provenance chain is assembled from echoed lower-layer versions; no
  environment data (PIDs, wall-clock, randomness).

## Implementation

### Files

- `src/context/__init__.py` — public API surface (157 lines)
- `src/context/config.py` — TOML config authority (65 lines)
- `src/context/derive.py` — pure helpers: chart identity, civil UTC split,
  canonical body order, provenance chain, snapshot assembly (327 lines)
- `src/context/errors.py` — error taxonomy (4 classes)
- `src/context/models.py` — frozen data models (201+ lines)
- `src/context/serialize.py` — deterministic JSON serialization (80+ lines)
- `src/context/service.py` — ContextService facade (43+ lines)
- `config/context.toml` — default configuration

### Tests

- `tests/unit/context/` — 7 test files covering models, errors, derive,
  serialize, service, static gates
- `tests/integration/context/` — 4 test files covering determinism,
  echo fidelity, serialization round-trip

### Key Design Decisions

1. **Zero new enums** — every astronomical enum is reused from
   `jyotish` / `bhava` / `gochar` public roots.
2. **Capability contract** — frozen V1 capability ids (`instant`, `natal`,
   `interval`, `eclipse`) with deterministic version compatibility
   checking.
3. **Provenance chain** — six-stage fact chain (INPUT → ASTRONOMICAL →
   NORMALIZATION → DERIVED → DOCTRINE_RULE → FUTURE_INFERENCE) with
   reserved forward slots.
4. **Natal/transit separation** — structural: natal sections and transit
   sections are independent optional fields, never merged.
5. **Chart identity** — deterministic SHA-256 fingerprint enabling
   cross-layer identity joins (Varga, caching).
6. **Config authority** — `config/context.toml` declares every default
   (no hidden defaults); `ContextConfig` immutable and echoed.

## Change history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-08-16 | JRE-007 implemented: context module, config, errors, models, derive, service, serialize, unit + integration tests |
