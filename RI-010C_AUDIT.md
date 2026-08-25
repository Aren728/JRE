# RI-010C Architecture Impact Audit

**Date:** 2026-08-25
**Status:** Read-Only Audit

---

## 1. Can existing JRE engines calculate all facts needed for RI-010B and RI-010C?

**Answer: No.**

*   **RI-010B (Multi-planet relationships):** The existing engines (`src/yoga/`, `src/drik/`) cover basic structural facts (conjunctions, standard aspects, basic exchanges, and named yogas like Raja/Dhana). However, they **cannot** calculate:
    *   **Aspect Strength Gradation:** The Drik engine computes presence/orbs but not the classical 1/4, 1/2, 3/4, full strength values required for RI-010B.
    *   **Parivartana Classification:** The Yoga engine detects exchanges but does not classify them as Maha, Kahala, or Dainya.
    *   **Dispositor Chains:** There is no logic to trace sign-lord chains or identify final dispositors.
*   **RI-010C (Transit activation):** The existing engines are **static** (natal chart only). They lack the temporal logic (Dasha, Antardasha, Transit-to-Natal aspecting) required for activation timing.

## 2. Do we need a new "Relationship Graph" JRE engine?

**Recommendation: Yes.**

*   **Reasoning:** Dispositor chains and aspect chains are inherently graph-based. While this logic *could* live in the JRS (Knowledge) layer, it would blur the line between deterministic facts (the graph structure) and interpretation (what the graph means).
*   **Proposed Architecture:** A new `JRE-014 (RelationshipGraph)` engine should compute the deterministic graph (nodes=planets, edges=dispositorship/aspect chains) and provide facts like "A is the final dispositor of B" or "Chain A-B-C is broken at B."

## 3. Are there any missing deterministic facts for the 4-fold distinction?

**Yes, several critical gaps remain:**

*   **Formation:** Mostly covered, but missing **Pancha Mahapurusha** detection (though simple) and **Multi-planet conjunction dominance** logic.
*   **Strength:** Missing **Aspect Strength Gradation**, **Parivartana Classification**, and **Combustion Detection** (as a strength modifier).
*   **Manifestation:** Completely missing. We need a **Temporal Engine (JRE-015)** to calculate Dasha/Bhukti periods and Transit overlays.
*   **Outcome:** Mostly JRS territory, but deterministic "potential" factors (e.g., "Yoga is in a Dusthana") are missing from the Strength layer.

---

**Summary:** To fully support RI-010B and RI-010C, the project requires:
1.  **JRE-014 (RelationshipGraph)** for dispositor/aspect chains.
2.  **JRE-015 (Temporal)** for Dasha and Transit activation.
3.  **Enhancements to JRE-012 (Drik)** for aspect strength gradation.
4.  **Enhancements to JRE-013 (Yoga)** for Parivartana classification and combustion detection.
