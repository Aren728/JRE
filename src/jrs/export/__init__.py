"""Phase 8: High-Fidelity Export & Report Generation.

Pure, deterministic export of pipeline artifacts for audit and
productization:

- :mod:`jrs.export.provenance_export` — diagnostic JSON + GraphML export
  of the Phase 3 evidence DAG (full provenance).
- :mod:`jrs.export.svg_renderer` — high-fidelity SVG chart rendering
  (D1/D9/D10/D60 in North-Indian, South-Indian, and circular-wheel
  styles) for print and web embedding.
- :mod:`jrs.export.pdf_report` — executive forensic PDF report
  (ReportLab) combining the chart, yoga findings, and the provenance
  chain in one document.

Design constraints (inherited from the golden-state discipline):

- every exporter is a pure function of its inputs — no wall-clock, no
  I/O inside the library (the CLI layer owns files);
- serialization reuses the golden-state float canonicalization
  (round-6) so exported artifacts are byte-stable across runs;
- ReportLab is an optional extra (``pip install .[export]``); the
  provenance and SVG exporters have no third-party dependencies.
"""

from __future__ import annotations

from jrs.export.provenance_export import (
    EXPORT_SCHEMA_VERSION,
    provenance_to_diagnostic_json,
    provenance_to_graphml,
)
from jrs.export.svg_renderer import (
    SVG_RENDERER_VERSION,
    render_chart_svg,
)

__all__ = [
    "EXPORT_SCHEMA_VERSION",
    "SVG_RENDERER_VERSION",
    "provenance_to_diagnostic_json",
    "provenance_to_graphml",
    "render_chart_svg",
]
