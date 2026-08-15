# JRE-006 — Gochar / Continuous Transit Engine: Test Plan

- Version: 0.2.0 (SPECIALIST)
- Date: 2026-08-14
- Status: SPECIALIST-COMPLETE (**normative at CODING**; supersedes the
  v0.1.0 architect draft where they conflict)
- Related: [specialist spec](JRE-006-SPECIALIST-SPEC.md),
  [data contract](JRE-006-DATA-CONTRACT.md),
  [architecture core](JRE-006-GOCHAR-TRANSIT-ENGINE.md),
  [ADR-022](../decisions/ADR-022-GOCHAR-LAYER-BOUNDARY.md) …
  [ADR-029](../decisions/ADR-029-ASPECT-STATE-ECHO-EVENTS-DEFERRED.md)

## 1. Test principles

1. **Contract tests, not implementation details** — every test maps to
   a specialist-spec/data-contract requirement.
2. **Cross-layer invariants are hard gates** (DC §9).
3. **Determinism is byte-level** — in-process and cross-process.
4. **Boundary honesty** — 0°/360°, exact-on-boundary events,
   interval endpoints (including the documented exact-`end` limitation,
   SPEC §13.4), simultaneous events, leap days.
5. **Static boundary** — forbidden imports, interpretation/eclipse
   vocabulary, provenance hygiene, no `TYPE_CHECKING` bypass.

## 2. Requirement matrix (file-level)

| # | Requirement | Source | Test file |
|---|---|---|---|
| 1 | Public boundary: `jyotish` + `bhava` roots + stdlib only | SPEC §2 | `tests/unit/gochar/test_gochar_static.py` |
| 2 | No type redefinition / zero new enums | SPEC §6 | `tests/unit/gochar/test_gochar_models.py` |
| 3 | Config schema + TOML authority + no hidden defaults | SPEC §5, DC §2 | `tests/unit/gochar/test_gochar_config.py` |
| 4 | Error taxonomy (4 types) | SPEC §7, DC §3 | `tests/unit/gochar/test_gochar_errors.py` |
| 5 | Input invariants (instants, start<=end, bodies, reference, house system, series-needs-anchor) | SPEC §8 | `tests/unit/gochar/test_gochar_errors.py` |
| 6 | Instant GENERIC echo (states + optional geometry) | SPEC §10 | `tests/unit/gochar/test_gochar_instant.py` |
| 7 | Instant NATAL: house analysis == JRE-005 output (hard gate) | SPEC §16, DC §9.2 | `tests/integration/gochar/test_gochar_jre005_equality.py` |
| 8 | Transit-to-natal aspect echo (full pair set, canonical order) | SPEC §11.4 | `tests/integration/gochar/test_gochar_jre005_equality.py` |
| 9 | ASC ≡ LAGNA (hard gate) | SPEC §16, DC §9.3 | `tests/integration/gochar/test_gochar_reference_matrix.py` |
| 10 | Event stream echo byte-identity (hard gate) | SPEC §13, DC §9.1 | `tests/integration/gochar/test_gochar_jre003_echo.py` |
| 11 | Pinned event ordering `(jd, body, kind)` + ordinal identity | SPEC §13.6 | `tests/unit/gochar/test_gochar_ordering.py` |
| 12 | Endpoint semantics: start-exact included, end-exact documented limitation | SPEC §13.4 | `tests/unit/gochar/test_gochar_boundaries.py` |
| 13 | Simultaneous events (rashi+nakshatra at 0°) | SPEC §13.7 | `tests/unit/gochar/test_gochar_ordering.py` |
| 14 | 0°/360° wraparound; `boundary_deg==0.0` | SPEC §13.8 | `tests/unit/gochar/test_gochar_boundaries.py` |
| 15 | State series echo (ascending JD, config step) | SPEC §12.2 | `tests/integration/gochar/test_gochar_jre003_echo.py` |
| 16 | Natal-frame house series (config-gated, per-sample UTC, canonical order) | SPEC §12.3 | `tests/integration/gochar/test_gochar_natal_house_series.py` |
| 17 | Aspect **state** echo incl. `ApplyingSeparating` | SPEC §15 | `tests/unit/gochar/test_gochar_aspects.py` |
| 18 | Deferral assertions: no aspect events, no house-ingress kind, no generic transit chart shape | SPEC §25, ADR-029 | `tests/unit/gochar/test_gochar_static.py` + `test_gochar_aspects.py` |
| 19 | Provenance: fields, source layers, versions, input echo; no env data | SPEC §9.1, ADR-028 | `tests/unit/gochar/test_gochar_provenance.py` |
| 20 | Serialization round-trip + Schema `additionalProperties=false` | DC §6-7 | `tests/unit/gochar/test_gochar_serialize.py` |
| 21 | Golden fixture byte identity | DC §7 | `tests/integration/gochar/test_gochar_golden.py` |
| 22 | Determinism in-process + cross-process byte identity | SPEC §19 | `tests/integration/gochar/test_gochar_determinism.py` |
| 23 | Interpretation + eclipse vocabulary scans | SPEC §23-24 | `tests/unit/gochar/test_gochar_static.py` |
| 24 | Provenance hygiene scan | SPEC §26.3 | `tests/unit/gochar/test_gochar_static.py` |
| 25 | Performance p95 (delegated computation excluded) | SPEC §20 | `tests/integration/gochar/test_gochar_performance.py` |

Basename collision convention: all files prefixed `test_gochar_*`
(repo convention).

## 3. Boundary tests

- **0°/360°**: linear-provider probe (as used in the Specialist
  verification): a body crossing 359.9999° → 0.0001° yields one
  `RASHI_INGRESS` with `boundary_deg == 0.0`; no missed/duplicated
  events (echo of JRE-003 unwrap).
- **Exact-on-boundary sample**: `f0 == 0.0` path — event at the sample
  instant with `search_metadata.iterations == 0`.
- **Endpoint semantics (pinned by empirical verification)**:
  - crossing exactly at `start_utc_iso` → event included;
  - crossing exactly at `end_utc_iso` → not guaranteed (documented
    upstream limitation); the test asserts the **documented behavior**
    (0 events for the exact-end case on the synthetic provider) and
    asserts JRE-006 does not compensate;
  - crossing strictly interior → exactly one bisected event.
- **Sign/nakshatra/pada ingress and egress**: all six kinds echoed with
  correct `reached` bucket and `boundary_deg`; retrograde crossings
  produce their own events (echo identity covers it).
- **Simultaneous events**: a boundary that is both a rashi and a
  nakshatra boundary (0°, 120°, 240°) produces both kinds at one JD;
  pinned total order by `(jd, body.value, kind.value)`.
- **Duplicate suppression**: re-running the same interval yields the
  identical stream (no duplicates introduced by the re-sort); the
  stable sort preserves source order for ties.
- **Leap days**: intervals spanning 2024-02-29 (sample count and event
  stream match the JRE-003 echo).
- **Timezone**: instant requests in IANA zones produce the same UTC
  instant (delegated; verified via JRE-003); JRE-006 always passes UTC.

## 4. Cross-layer tests

- **JRE-003 echo identity (hard gate)**: `GocharIntervalResult.events`
  (after re-asserted sort) byte-equals the JRE-003 `events_between`
  tuple serialized identically; `state_samples` byte-equals
  `state_series`. Two real intervals (one spanning stations, one
  spanning ingress/egress) + the synthetic linear-provider probes.
- **JRE-005 equality (hard gate)**: `GocharNatalResult.transit_house_analysis`
  equals `bhava.derive_transit_analysis(jyotish.transit_through_houses(...),
  natal_chart=...)` — house numbers, rashis, lords, occupants,
  provenance.
- **ASC ≡ LAGNA**: whole-sign natal-frame facts agree for
  `reference_point=ASC` vs `LAGNA`.
- **Reference matrix**: LAGNA/MOON/SUN/ASC anchor semantics; unknown
  reference → `InvalidGocharRequestError` (JRE-006) /
  `UnsupportedReferencePointError` (wrapped).
- **Isolation**: `git diff` empty for JRE-002/003/004/005; no JRE-006
  file imports them except via the public roots.

## 5. Determinism tests

- In-process: serialize the same query 3× — byte-identical.
- Cross-process: subprocess re-serializes the same query —
  byte-identical.
- Ordering scan: no `set(`/`dict(` iteration in `src/gochar` ordering
  paths (static).

## 6. Static boundary tests

- Forbidden-import AST scan of `src/gochar` (§2.2), including
  `TYPE_CHECKING` blocks.
- Vocabulary scan: `dasha`, `prediction`, `yoga`, `benefic`,
  `malefic`, `auspicious`, `forecast`, `eclipse` absent from production
  identifiers.
- Provenance hygiene: no `time(`, `random`, `getpid`, `environ` in
  provenance construction.
- Public-surface pinning: `gochar.__all__` enforced.

## 7. Golden fixture

- `tests/fixtures/gochar/golden/` for one instant result and one
  interval result (fixed birth data, fixed interval, pinned ephemeris/
  catalog versions).
- `GOLDEN_VERSION` constant; hex-float pinning; byte-for-byte compare.

## 8. Serialization tests

- `result_to_dict` ↔ `result_to_json` round-trip value-identical.
- Requests round-trip via `*_request_from_dict` with full validation.
- Schema conformance + `additionalProperties=false` rejects unknown
  keys; enum strings constrained; ISO-UTC microsecond pattern.
- Malformed input → exact typed errors (DC §3).
- **Information-loss check**: event echoes keep every `TransitEvent`
  field (incl. `SearchMetadata.iterations`/`position_calls`); no
  truncation of timestamps.

## 9. Performance smoke (informational)

- Instant generic: p95 < 5 ms (delegated JRE-003 position/geometry
  excluded — precomputed once outside the timed loop, JRE-004/JRE-005
  perf-test pattern).
- Instant natal: p95 < 5 ms (delegated chart/transit + JRE-005
  derivation excluded).
- Interval (30 d, daily, 9 bodies): p95 < 10 ms (delegated event
  search/series excluded).
- Event re-sort on a 1-year interval: measured, informational.
- Report actual measurements; no manufactured pass from a single
  favorable sample.

## 10. Quality gates (CODING exit criteria)

- `pytest tests/unit tests/integration` — full suite green (existing
  regression + JRE-006).
- `ruff check src tests` — clean.
- `mypy src/astronomy src/jyotish src/knowledge src/bhava src/gochar`
  — clean (strict).
- Cross-process determinism — PASS.
- JRE-003 echo identity + JRE-005 equality hard gates — PASS.
- JRE-002/003/004/005 isolation — `git diff` empty.
- Performance smoke — within targets.
- No FORBIDDEN_WORKAROUND — static scan PASS.
