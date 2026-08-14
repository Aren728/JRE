# ADR-015 — Multi-House-System Views: Per-System JRE-003 Charts, Never Mixed

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-005 Bhava / House Engine](../architecture/JRE-005-BHAVA-CORE.md)
- Supersedes: nothing (inherits JRE-003's "explicit systems, never
  mixed" rule, ADR-002)
- Decision maker: Architect

## Context

Classical practice uses whole-sign bhavas as the norm (Parashari), but
cusp-based systems (Placidus, Koch, etc.) are widely used regionally.
JRE-003 already supports six house systems — one per chart config —
and forbids mixing systems within one chart (ADR-002). JRE-005 must
answer "which house is planet X in?" for any system, and must support
comparative analysis (e.g. whole-sign vs Placidus) without corrupting
the "never mixed" invariant.

## Decision

1. **`BhavaConfig.house_systems` is a tuple of `HouseSystem`** (default
   `(WHOLE_SIGN,)`). For each entry, JRE-005 requests **one JRE-003
   `NatalChart`** for the same birth data (a separate `JyotishService.chart`
   call per system). JRE-005 never computes cusps itself (ADR-013).
2. **Every derived fact is tagged with its `house_system`**, and
   `HouseAnalysis` contains exactly one system. The top-level
   `HouseAnalysisResult` may carry several analyses (one per configured
   system) for comparison, but **no fact set ever combines systems** —
   there is no "merged" view.
3. **Identity is `(house_system, house_number)`** — house 4 under
   WHOLE_SIGN and house 4 under PLACIDUS are different facts with
   different spans/occupants; consumers must not conflate them.
4. **System-specific semantics are explicit**: whole-sign bhavas have
   `BoundaryKind.SIGN_BOUNDARY`; cusp systems have
   `BoundaryKind.COMPUTED_CUSP`; occupancy differences between systems
   are expected, tagged, and testable (TEST-PLAN §5).
5. **The whole-sign default is pinned and echoed** — it matches the
   JRE-003 default and the Parashari norm; any other system is explicit
   opt-in. No silent fallback between systems.

Rationale:

- Reusing JRE-003's per-chart computation keeps a single source of
  geometric truth and zero new cusp math (ADR-013).
- Tagging every fact preserves the JRE-003 invariant (never mixed) while
  enabling the comparative views classical analysis and rules need.
- Explicit identity prevents the classic bug of comparing house numbers
  across systems as if they were the same house.

Rejected alternatives:

- **A single "primary" system with silent fallback** — hides tradition
  variation, contradicts the explicit-variation policy (architecture
  §29), and would silently change rule inputs.
- **Recompute all systems inside `bhava`** — duplicates cusp math,
  forbidden by ADR-013.
- **Merge systems into one fact set** — violates the never-mixed
  invariant and makes provenance ambiguous.

## Consequences

- `BhavaService.analyze` performs `len(house_systems)` JRE-003 chart
  calls; performance scales linearly (documented, TEST-PLAN §13).
- `DerivationBlock.house_system` is present on every fact.
- The JRE-004 `relative_house` contract holds per system: each system's
  analysis is a separate fact space (ADR-014 applies within a system).

## References

- [ADR-002 (adapter placement, never-mixed)](ADR-002-HOUSE-ECLIPSE-ADAPTER-PLACEMENT.md)
- [JRE-003 architecture §9](../architecture/JRE-003-JYOTISH-CORE.md)
- [JRE-005 architecture §9, §30](../architecture/JRE-005-BHAVA-CORE.md)
