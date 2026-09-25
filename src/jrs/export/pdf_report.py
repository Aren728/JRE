"""Phase 8: Executive forensic PDF report generator (ReportLab).

Composes one printable document from the pipeline artifacts:

1. header block (subject, fixture, engine version, renderer version);
2. birth-chart summary (lagna, Moon nakshatra, planetary positions);
3. yoga findings (status, category, involved planets, chain impact,
   cancellation reasons);
4. provenance summary (evidence-graph id, layer summary, relationship
   histogram — the same diagnostic payload the provenance exporter
   emits);
5. legal disclaimer footer.

Determinism: the document is built with ``invariant=1`` (ReportLab
pins its internal timestamps), so identical inputs yield byte-identical
PDFs — the export participates in the repo's golden-byte discipline.

ReportLab is an **optional** dependency: install with
``pip install .[export]``. The import is lazy; calling
:func:`render_forensic_pdf` without it raises a descriptive
:class:`ImportError`.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "PDF_REPORT_VERSION",
    "ForensicReportInput",
    "render_forensic_pdf",
    "rows_from_evaluation",
]

#: Report generator version (embedded in PDF metadata).
PDF_REPORT_VERSION = "1.0.0"


@dataclass(frozen=True)
class ForensicReportInput:
    """Shaped payload for one forensic PDF report."""

    subject: str
    fixture_id: str
    lagna: str = ""
    moon_nakshatra: str = ""
    engine_version: str = ""
    #: Rows: {body, sign, house?, dignity?}
    positions: list[dict[str, Any]] = field(default_factory=list)
    #: Rows: {yoga_name, status, category?, involved?, chain_impact?,
    #:        cancellation_reason?, citation?}
    yogas: list[dict[str, Any]] = field(default_factory=list)
    #: Diagnostic-JSON payload from provenance_to_diagnostic_json().
    provenance_summary: dict[str, Any] | None = None


def rows_from_evaluation(evaluation: Any) -> dict[str, Any]:
    """Map an ``EvaluationResponse`` into ForensicReportInput fields.

    Keeps the PDF core decoupled from the pydantic API schemas: the
    caller (or API layer) passes any object carrying ``subject``,
    ``lagna``, ``moon_nakshatra``, ``yogas`` (YogaResult-like entries
    with ``model_dump`` or attribute access), and ``engine_version``.
    """
    def _dump(item: Any) -> dict[str, Any]:
        if hasattr(item, "model_dump"):
            return dict(item.model_dump())
        return dict(item)

    yogas: list[dict[str, Any]] = []
    for item in getattr(evaluation, "yogas", []):
        row = _dump(item)
        yogas.append(
            {
                "yoga_name": row.get("yoga_name", ""),
                "status": row.get("status", ""),
                "category": row.get("category", ""),
                "involved": ", ".join(row.get("involved_planets") or []),
                "chain_impact": row.get("chain_impact"),
                "cancellation_reason": row.get("cancellation_reason"),
            }
        )

    return {
        "subject": getattr(evaluation, "subject", "Custom"),
        "lagna": getattr(evaluation, "lagna", ""),
        "moon_nakshatra": getattr(evaluation, "moon_nakshatra", ""),
        "engine_version": getattr(evaluation, "engine_version", ""),
        "yogas": yogas,
    }


def render_forensic_pdf(report_input: ForensicReportInput) -> bytes:
    """Render the executive forensic report as deterministic PDF bytes.

    Raises:
        ImportError: When ReportLab is not installed (install the
            ``export`` extra: ``pip install .[export]``).
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise ImportError(
            "ReportLab is required for PDF export. Install the export extra: "
            "pip install .[export]"
        ) from exc

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=f"JRE Forensic Report — {report_input.subject}",
        author="JRE — Jyotish Reasoning Engine",
        subject=f"Executive forensic report for {report_input.fixture_id or report_input.subject}",
        creator=f"jrs.export.pdf_report {PDF_REPORT_VERSION}",
        invariant=1,  # pin internal timestamps -> deterministic bytes
    )

    styles = getSampleStyleSheet()
    heading = ParagraphStyle(
        "ForensicHeading",
        parent=styles["Heading2"],
        spaceBefore=10,
        spaceAfter=4,
    )
    body = ParagraphStyle("ForensicBody", parent=styles["BodyText"], fontSize=9)
    small = ParagraphStyle("ForensicSmall", parent=styles["BodyText"], fontSize=8)

    accent = colors.HexColor("#1d4ed8")
    ink = colors.HexColor("#111827")
    faint = colors.HexColor("#6b7280")
    band = colors.HexColor("#eef2ff")

    def _table(data: list[list[str]], widths: list[float] | None = None) -> Table:
        table = Table(data, colWidths=widths, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("TEXTCOLOR", (0, 0), (-1, 0), ink),
                    ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#374151")),
                    ("BACKGROUND", (0, 0), (-1, 0), band),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        return table

    story: list[Any] = []

    # ── 1. Header ──
    story.append(Paragraph("Executive Forensic Report", styles["Title"]))
    story.append(
        Paragraph(
            f"Subject: <b>{report_input.subject}</b>"
            f" &nbsp;·&nbsp; Fixture: {report_input.fixture_id or '—'}"
            f" &nbsp;·&nbsp; Engine: {report_input.engine_version or '—'}"
            f" &nbsp;·&nbsp; Generator: jrs.export.pdf_report {PDF_REPORT_VERSION}",
            body,
        )
    )
    story.append(Spacer(1, 4 * mm))

    # ── 2. Birth-chart summary ──
    story.append(Paragraph("1. Birth Chart Summary", heading))
    story.append(
        Paragraph(
            f"Lagna: <b>{report_input.lagna or '—'}</b>"
            f" &nbsp;·&nbsp; Moon Nakshatra: <b>{report_input.moon_nakshatra or '—'}</b>",
            body,
        )
    )
    if report_input.positions:
        header = ["Body", "Sign", "House", "Dignity"]
        rows = [header]
        for pos in report_input.positions:
            rows.append(
                [
                    str(pos.get("body", "")),
                    str(pos.get("sign", "")),
                    str(pos.get("house", "—")),
                    str(pos.get("dignity", "—")),
                ]
            )
        story.append(_table(rows, widths=[30 * mm, 35 * mm, 25 * mm, 60 * mm]))
    else:
        story.append(Paragraph("No positions supplied.", small))

    # ── 3. Yoga findings ──
    story.append(Paragraph("2. Yoga Findings", heading))
    if report_input.yogas:
        rows = [["Yoga", "Status", "Category", "Involved", "Chain", "Notes"]]
        for yoga in report_input.yogas:
            chain = yoga.get("chain_impact")
            notes = yoga.get("cancellation_reason") or ""
            rows.append(
                [
                    str(yoga.get("yoga_name", "")),
                    str(yoga.get("status", "")),
                    str(yoga.get("category", "") or "—"),
                    str(yoga.get("involved", "") or "—"),
                    f"{chain:.3f}" if isinstance(chain, (int, float)) else "—",
                    notes[:80],
                ]
            )
        story.append(
            _table(
                rows,
                widths=[32 * mm, 20 * mm, 26 * mm, 34 * mm, 14 * mm, 34 * mm],
            )
        )
    else:
        story.append(Paragraph("No yogas supplied.", small))

    # ── 4. Provenance summary ──
    provenance = report_input.provenance_summary
    if isinstance(provenance, dict):
        story.append(Paragraph("3. Provenance Summary", heading))
        story.append(
            Paragraph(
                f"Graph: <font name='Courier'>{provenance.get('graph_id', '—')}</font>"
                f" &nbsp;·&nbsp; {provenance.get('node_count', 0)} nodes"
                f" · {provenance.get('edge_count', 0)} edges",
                body,
            )
        )
        layer_rows = [["Layer", "Nodes"]]
        for layer, count in (provenance.get("layer_summary") or {}).items():
            layer_rows.append([str(layer), str(count)])
        if len(layer_rows) > 1:
            story.append(_table(layer_rows, widths=[60 * mm, 30 * mm]))
        story.append(
            Paragraph(
                "Full chain exported via jrs.export.provenance_export "
                "(diagnostic JSON / GraphML).",
                small,
            )
        )

    # ── 5. Disclaimer ──
    story.append(Spacer(1, 6 * mm))
    story.append(
        Paragraph(
            "DISCLAIMER: This output is a computational interpretation based on "
            "classical Vedic astrology rulesets (BPHS, Phaladeepika). It is provided "
            "for informational and research purposes only. It does not constitute "
            "medical, financial, legal, or guaranteed predictive advice.",
            small,
        )
    )

    doc.build(story)
    return buffer.getvalue()
