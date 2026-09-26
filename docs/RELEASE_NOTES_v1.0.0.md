# JRE 1.0.0 — Release Notes

*Production release of the Jyotish Reasoning Engine: a deterministic,
hash-audited classical Jyotish pipeline with a frozen empirical
benchmark, provenance-complete predictions, and a sealed ablation
study.*

## Highlights

- **Deterministic core.** Swiss Ephemeris 2.10.03 → fact extraction →
  yoga evaluation → provenance DAG, all pure and byte-reproducible.
  Nine golden-state stages (chart, jre_facts, dasha, yogas,
  ashtakavarga, gochara, multi_varga, dasha_transit, evidence_graph)
  are hash-verified across 50 fixtures on every run.
- **Frozen benchmark (JRE-BENCH-001).** 40 charts / 120 dated events,
  event-level scoring protocol. Gating baseline **Micro-F1 = 0.7435**
  (TP=71 / FP=31 / FN=18); companion with all Phase 5 mechanisms
  **Micro-F1 = 0.7565**. Non-degradation gate enforced in CI.
- **Empirical ablation study (JRE-ABLATION-001).** Paired per-event
  leave-one-out ablation with exact binomial McNemar tests: the D9/D10
  cross-varga rescue is the only verdict-moving mechanism (+0.0130 F1,
  2/0 discordant, p = 0.5); SAV, Gochara/Vedha, and the Dasha gate act
  through confidence ordering only.
- **Pre-registered expansion (JRE-BENCH-002).** Power analysis locked:
  ≥ 720 scored events (240 charts) for ≥ 0.80 power at π = 0.9 on the
  observed effect; single confirmatory pass, no-peeking protocol.
- **Full provenance & lineage.** Every prediction resolves backward
  through Rule → Dasha Gate → Transit → Varga → Yoga → SAV → raw
  ephemeris floats (`/api/v1/evidence/lineage/{fixture_id}`).
- **Platform.** OpenAPI 3.1 contract (27 paths) enforced in CI; async
  offload with timeout bounds; strict DTOs; security fuzz suite
  (traversal, payload caps, extreme-date bounds).
- **Export pipeline.** Provenance JSON/GraphML, SVG charts
  (north/south/wheel × D1/D9/D10/D60), executive forensic PDF
  (ReportLab, byte-deterministic), and the auto-generated benchmark
  paper (`docs/paper/`).
- **Observatory UI.** Evidence Graph Inspector, Dasha Tree, Yoga
  Inspector, and SAV Viewer integrated in one forensic dashboard.

## Validation Summary

| Gate | Result |
|---|---|
| Clean-room audit (JRE-REPRODUCE-001) | REPRODUCIBLE — Stage 1–9 hashes + bit-for-bit baseline |
| Benchmark gate (Phase F3) | PASS — 0.7435 retained |
| Ablation anchors | BASELINE + FULL reproduce sealed values bit-for-bit |
| Invariants (identity + sensitivity) | PASS |
| Security fuzz suite | PASS (39 tests) |
| Frontend suite | 139/139 |
| OpenAPI contract | 3.1.0, 27 paths / 23 components |
| Release seal | `releases/v1.0.0.json` (content-hash verified) |

## Upgrade Notes (from v1.0.0-rc1 / v1.0.0-beta)

- `ENGINE_VERSION` is now `v1.0.0`; golden manifests are re-stamped
  (all pinned Stage 1–9 payload hashes unchanged — the bump touches
  manifest metadata only).
- Project version reconciled to `1.0.0` (was `1.1.0rc1` in
  `pyproject.toml`, `v1.0.0-beta` in the engine).
- The rc1 seal (`releases/v1.0.0-rc1.json`) is immutable and remains
  auditable at its Phase 9F tree (`git checkout 585f2c9`):
  `--check --release-id v1.0.0-rc1` passes at that tree. At HEAD it
  reports expected content drift (api/frontend/golden sections) from
  this version reconciliation.

## Known Limitations

- Ablation effects are underpowered at n = 120; the confirmatory
  analysis awaits the JRE-BENCH-002 expansion (pre-registered).
- Confidence-pathway mechanisms (SAV, Gochara, Dasha gate) are
  invisible to verdict-level F1 on this corpus; secondary endpoints in
  BENCH-002 address this.
- ReportLab is an optional extra (`pip install .[export]`).
- WeasyPrint-based 9-step report generator is legacy/unused by the
  release tooling.

## Artifact Map

| Artifact | Path |
|---|---|
| Benchmark seal | `benchmarks/JRE-BENCH-001.json` |
| Pre-registration | `docs/validation/phase_11a_bench002_preregistration.md` |
| Ablation study | `reports/ablation_matrix.{json,md}` |
| Benchmark paper | `docs/paper/jre_bench_paper.{md,pdf}` |
| Release seal | `releases/v1.0.0.json` |
| Reproducibility audit | `scripts/audit_clean_reproduce.py` |
| Lineage API | `GET /api/v1/evidence/lineage/{fixture_id}` |
