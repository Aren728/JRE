"""Phase 8: High-fidelity SVG chart renderer.

Renders divisional charts (D1/D9/D10/D60 — any sign-placement set) as
standalone SVG documents in the three classical styles:

- ``north`` — North-Indian diamond (fixed-sign layout, house numbers
  derived from the lagna);
- ``south`` — South-Indian grid (fixed-sign 4x4 layout);
- ``wheel`` — circular wheel (ascendant-starting, counter-clockwise).

Pure presentation over :class:`ChartPlacement` inputs — the caller
derives placements from any source (natal D1 longitudes via
:func:`placements_from_longitudes`, or a Phase 5D ``multi_varga``
report for divisional charts). Output is deterministic: identical
inputs yield byte-identical SVG, so renderings can be golden-hashed
like every other pipeline artifact.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from xml.sax.saxutils import escape

__all__ = [
    "SVG_RENDERER_VERSION",
    "SUPPORTED_DIVISIONS",
    "SUPPORTED_STYLES",
    "ChartPlacement",
    "placements_from_longitudes",
    "render_chart_svg",
]

#: Renderer version (embedded in the SVG metadata; bump on visual change).
SVG_RENDERER_VERSION = "1.0.0"

#: Divisions this renderer is conventionally used for (informational —
#: the renderer itself is division-agnostic over placements).
SUPPORTED_DIVISIONS: tuple[str, ...] = ("D1", "D9", "D10", "D60")

#: Supported chart styles.
SUPPORTED_STYLES: tuple[str, ...] = ("north", "south", "wheel")

SIGN_NAMES: tuple[str, ...] = (
    "MESHA", "VRISHABHA", "MITHUNA", "KARKA", "SIMHA", "KANYA",
    "TULA", "VRISHCHIKA", "DHANUSHA", "MAKARA", "KUMBHA", "MEENA",
)

_SIGN_SHORT: tuple[str, ...] = (
    "Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi",
)

_PLANET_SHORT: dict[str, str] = {
    "SUN": "Su",
    "MOON": "Mo",
    "MARS": "Ma",
    "MERCURY": "Me",
    "JUPITER": "Ju",
    "VENUS": "Ve",
    "SATURN": "Sa",
    "RAHU": "Ra",
    "KETU": "Ke",
    "LAGNA": "Asc",
}

_FONT = "Helvetica, Arial, sans-serif"


@dataclass(frozen=True)
class ChartPlacement:
    """One body placed in one sign (0-indexed sign, 0 = MESHA)."""

    body: str
    sign_index: int

    @property
    def sign_name(self) -> str:
        return SIGN_NAMES[self.sign_index]

    @property
    def short(self) -> str:
        return _PLANET_SHORT.get(self.body, self.body[:2].title())


def placements_from_longitudes(longitudes: dict[str, float]) -> list[ChartPlacement]:
    """Derive placements from sidereal longitudes (0-360, 0 = MESHA 0°)."""
    placements: list[ChartPlacement] = []
    for body, lon in longitudes.items():
        value = float(lon)
        if not 0.0 <= value < 360.0:
            raise ValueError(f"{body}: longitude out of range [0, 360): {value}")
        placements.append(ChartPlacement(body=body, sign_index=int(value // 30.0) % 12))
    return placements


def _validate(placements: list[ChartPlacement], lagna_sign: int) -> None:
    if not 1 <= lagna_sign <= 12:
        raise ValueError(f"lagna_sign must be 1-12, got {lagna_sign}")
    seen: set[str] = set()
    for placement in placements:
        if not 0 <= placement.sign_index <= 11:
            raise ValueError(f"{placement.body}: sign_index must be 0-11")
        if placement.body in seen:
            raise ValueError(f"duplicate body in placements: {placement.body}")
        seen.add(placement.body)


def _svg_open(size: int, division: str, style: str, title: str) -> list[str]:
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}"'
        f' viewBox="0 0 {size} {size}" role="img">',
        f"  <title>{escape(title)}</title>",
        "  <metadata>"
        f"jrs.export.svg_renderer {SVG_RENDERER_VERSION} division={escape(division)}"
        f" style={escape(style)}</metadata>",
    ]
    return lines


def _text(x: int, y: int, content: str, size: int, anchor: str = "middle", color: str = "#111827") -> str:
    return (
        f'  <text x="{x}" y="{y}" font-family="{_FONT}" font-size="{size}"'
        f' text-anchor="{anchor}" fill="{color}">{escape(content)}</text>'
    )


# ── North-Indian diamond ────────────────────────────────────────────────────

# Fixed-sign center positions on a 400x400 North chart (rashi 1..12).
_NORTH_SIGN_POS: dict[int, tuple[int, int]] = {
    1: (200, 55),
    2: (100, 100),
    3: (40, 40),
    4: (60, 200),
    5: (100, 300),
    6: (40, 360),
    7: (200, 350),
    8: (300, 300),
    9: (360, 360),
    10: (340, 200),
    11: (300, 100),
    12: (360, 40),
}


def _north_svg(
    placements: list[ChartPlacement], lagna_sign: int, division: str, title: str
) -> str:
    lines = _svg_open(400, division, "north", title)
    # Outline: square, both diagonals, and the inner diamond.
    lines.append('  <rect x="10" y="10" width="380" height="380" fill="none" stroke="#111827" stroke-width="2"/>')
    for x1, y1, x2, y2 in (
        (10, 10, 390, 390),
        (390, 10, 10, 390),
        (200, 10, 10, 200),
        (200, 10, 390, 200),
        (200, 390, 10, 200),
        (200, 390, 390, 200),
    ):
        lines.append(
            f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#111827" stroke-width="1"/>'
        )

    by_sign: dict[int, list[ChartPlacement]] = {}
    for placement in placements:
        by_sign.setdefault(placement.sign_index + 1, []).append(placement)

    for sign in range(1, 13):
        cx, cy = _NORTH_SIGN_POS[sign]
        house = (sign - lagna_sign) % 12 + 1
        entries = by_sign.get(sign, [])
        # Layout: sign abbr (top), planets (middle, one per line), house no.
        lines.append(_text(cx, cy - 14, _SIGN_SHORT[sign - 1], 11))
        for offset, placement in enumerate(entries):
            lines.append(_text(cx, cy + 2 + offset * 14, placement.short, 13, color="#1d4ed8"))
        if len(entries) >= 3:
            # Compress: extra planets shift the sign/house labels further out.
            pass
        lines.append(_text(cx, cy + 16 + len(entries) * 14, f"({house})", 9, color="#6b7280"))

    lines.append("</svg>")
    lines.append("")
    return "\n".join(lines)


# ── South-Indian grid ───────────────────────────────────────────────────────

# Fixed-sign cell (col, row) on the 4x4 South grid (rashi 1..12).
_SOUTH_SIGN_CELL: dict[int, tuple[int, int]] = {
    1: (1, 0),
    2: (2, 0),
    3: (3, 0),
    4: (3, 1),
    5: (3, 2),
    6: (3, 3),
    7: (2, 3),
    8: (1, 3),
    9: (0, 3),
    10: (0, 2),
    11: (0, 1),
    12: (0, 0),
}


def _south_svg(
    placements: list[ChartPlacement], lagna_sign: int, division: str, title: str
) -> str:
    lines = _svg_open(400, division, "south", title)
    cell = 100
    for i in range(5):
        lines.append(f'  <line x1="{i * cell}" y1="0" x2="{i * cell}" y2="400" stroke="#111827" stroke-width="1"/>')
        lines.append(f'  <line x1="0" y1="{i * cell}" x2="400" y2="{i * cell}" stroke="#111827" stroke-width="1"/>')

    by_sign: dict[int, list[ChartPlacement]] = {}
    for placement in placements:
        by_sign.setdefault(placement.sign_index + 1, []).append(placement)

    for sign in range(1, 13):
        col, row = _SOUTH_SIGN_CELL[sign]
        x0, y0 = col * cell, row * cell
        house = (sign - lagna_sign) % 12 + 1
        entries = by_sign.get(sign, [])
        lines.append(_text(x0 + 8, y0 + 16, _SIGN_SHORT[sign - 1], 11, anchor="start"))
        lines.append(_text(x0 + cell - 6, y0 + 16, f"({house})", 9, anchor="end", color="#6b7280"))
        for offset, placement in enumerate(entries):
            lines.append(_text(x0 + cell // 2, y0 + 55 + offset * 16, placement.short, 13, color="#1d4ed8"))

    lines.append("</svg>")
    lines.append("")
    return "\n".join(lines)


# ── Circular wheel ──────────────────────────────────────────────────────────

def _wheel_point(cx: int, cy: int, radius: int, angle_deg: float) -> tuple[float, float]:
    """Point on a circle; 0° = 9 o'clock, increasing counter-clockwise."""
    theta = math.radians(angle_deg)
    return cx + radius * math.cos(theta), cy - radius * math.sin(theta)


def _wheel_svg(
    placements: list[ChartPlacement], lagna_sign: int, division: str, title: str
) -> str:
    size = 420
    cx = cy = size // 2
    r_outer = 195
    r_sign = 172
    r_planet_base = 140
    r_inner = 100
    lines = _svg_open(size, division, "wheel", title)

    lines.append(
        f'  <circle cx="{cx}" cy="{cy}" r="{r_outer}" fill="none" stroke="#111827" stroke-width="2"/>'
    )
    lines.append(
        f'  <circle cx="{cx}" cy="{cy}" r="{r_inner}" fill="none" stroke="#111827" stroke-width="1"/>'
    )

    # 10-degree rim ticks.
    for tick in range(36):
        angle = tick * 10.0
        x1, y1 = _wheel_point(cx, cy, r_outer, angle)
        x2, y2 = _wheel_point(cx, cy, r_outer - (8 if tick % 3 == 0 else 4), angle)
        lines.append(
            f'  <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"'
            ' stroke="#111827" stroke-width="1"/>'
        )

    by_sign: dict[int, list[ChartPlacement]] = {}
    for placement in placements:
        by_sign.setdefault(placement.sign_index + 1, []).append(placement)

    # 12 sectors: sector k holds the sign (lagna_sign - 1 + k) % 12.
    for k in range(12):
        sign = (lagna_sign - 1 + k) % 12
        start_angle = k * 30.0
        end_angle = start_angle + 30.0
        mid_angle = start_angle + 15.0

        x1, y1 = _wheel_point(cx, cy, r_outer, start_angle)
        x2, y2 = _wheel_point(cx, cy, r_outer, end_angle)
        xi, yi = _wheel_point(cx, cy, r_inner, start_angle)
        lines.append(
            f'  <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{xi:.2f}" y2="{yi:.2f}"'
            ' stroke="#111827" stroke-width="1"/>'
        )
        # Sign boundary on the sign ring only for non-sector starts.
        if k != 0:
            xs, ys = _wheel_point(cx, cy, r_sign + 12, start_angle)
            lines.append(
                f'  <line x1="{xs:.2f}" y1="{ys:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"'
                ' stroke="#111827" stroke-width="0.5"/>'
            )

        sx, sy = _wheel_point(cx, cy, r_sign, mid_angle)
        lines.append(_text(int(sx), int(sy) + 4, _SIGN_SHORT[sign], 12, color="#374151"))

        entries = by_sign.get(sign, [])
        for offset, placement in enumerate(entries):
            px, py = _wheel_point(cx, cy, r_planet_base - offset * 20, mid_angle)
            lines.append(
                _text(int(px), int(py) + 4, placement.short, 13, color="#1d4ed8")
            )

    # Ascendant marker on the sector boundary at 0° (9 o'clock).
    lines.append(
        f'  <line x1="{cx - r_outer}" y1="{cy}" x2="{cx - r_inner}" y2="{cy}"'
        ' stroke="#b91c1c" stroke-width="2"/>'
    )
    lines.append(_text(cx - r_outer + 22, cy - 8, "Asc", 12, anchor="start", color="#b91c1c"))

    lines.append("</svg>")
    lines.append("")
    return "\n".join(lines)


# ── Public entry point ──────────────────────────────────────────────────────

_RENDERERS = {
    "north": _north_svg,
    "south": _south_svg,
    "wheel": _wheel_svg,
}


def render_chart_svg(
    placements: list[ChartPlacement],
    lagna_sign: int,
    division: str = "D1",
    style: str = "north",
    title: str = "",
) -> str:
    """Render one chart as a standalone SVG document.

    Args:
        placements: Bodies with their 0-indexed signs (0 = MESHA).
        lagna_sign: Ascendant sign, 1-12 (1 = MESHA); fixes house
            numbering (north/south) and wheel rotation.
        division: Division label carried in the SVG metadata
            (conventionally one of :data:`SUPPORTED_DIVISIONS`).
        style: One of :data:`SUPPORTED_STYLES`.
        title: Accessible title text (escaped).

    Returns:
        Deterministic SVG text; identical inputs yield identical bytes.
    """
    if style not in _RENDERERS:
        raise ValueError(f"unsupported style: {style!r} (expected one of {SUPPORTED_STYLES})")
    if division not in SUPPORTED_DIVISIONS:
        raise ValueError(
            f"unsupported division: {division!r} (expected one of {SUPPORTED_DIVISIONS})"
        )
    _validate(placements, lagna_sign)
    resolved_title = title or f"{division} chart — {style} style"
    return _RENDERERS[style](placements, lagna_sign, division, resolved_title)
