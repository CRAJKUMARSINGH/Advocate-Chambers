"""Deterministic sheet-layout and annotation standards for all exports.

The ISO 5457 and ISO 7200 families standardise sheet formats, margins and
title-block information, but they do not prescribe a universal percentage for
notes or an index.  This module therefore keeps those standards separate from
the project policy: the drawing zone is protected first, and supporting
content is capped so a renderer cannot silently consume the plan area.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ISO_SHEET_FORMATS_MM: dict[str, tuple[float, float]] = {
    "A0": (1189.0, 841.0),
    "A1": (841.0, 594.0),
    "A2": (594.0, 420.0),
    "A3": (420.0, 297.0),
    "A4": (297.0, 210.0),
}

# Points, with 72 points per inch.  The values are deliberately conservative:
# the renderer may choose a larger margin but never a smaller one.
SHEET_STANDARD: dict[str, Any] = {
    "version": "week13.sheet-layout.v1",
    "formatFamily": "ISO 5457 A-series",
    "titleBlockReference": "ISO 7200 information fields",
    "status": "project-adopted preliminary drawing standard",
    "pageMarginPt": 26.0,
    "innerMarginPt": 8.0,
    "titleBlockHeightPt": 96.0,
    "supportingBandHeightPt": 78.0,
    "supportingContentMaxAreaRatio": 0.20,
    "drawingZoneMinAreaRatio": 0.65,
    "policy": [
        "Plan/elevation/section geometry gets the primary drawing zone.",
        "Notes, legends, schedules, and sheet indices live in a shared supporting band, not an unbounded side rail.",
        "A title block is structured and compact; it must not displace the primary drawing.",
        "Annotation sizes are model-independent paper sizes and are scaled only by the selected sheet scale.",
    ],
}

ANNOTATION_STYLES: dict[str, dict[str, Any]] = {
    "title": {"paperHeightMm": 5.0, "minHeightPt": 12.0, "weight": "bold"},
    "subtitle": {"paperHeightMm": 3.5, "minHeightPt": 8.0, "weight": "bold"},
    "roomLabel": {"paperHeightMm": 2.5, "minHeightPt": 6.5, "weight": "regular"},
    "dimension": {"paperHeightMm": 2.5, "minHeightPt": 6.5, "weight": "regular"},
    "generalNote": {"paperHeightMm": 2.5, "minHeightPt": 6.5, "weight": "regular"},
    "keynote": {"paperHeightMm": 2.5, "minHeightPt": 6.5, "weight": "bold"},
    "minimumReadable": {"paperHeightMm": 2.5, "minHeightPt": 6.5},
}


def dxf_text_height(style: str, model_units_per_paper_inch: float = 96.0) -> float:
    """Convert a paper annotation target to model-space DXF height.

    The default corresponds to the existing 1/8 inch = 1 foot plotting scale
    used by the standard drawing package (1 paper inch = 96 model inches).
    """

    target = ANNOTATION_STYLES.get(style, ANNOTATION_STYLES["generalNote"])
    return round(float(target["paperHeightMm"]) / 25.4 * model_units_per_paper_inch, 3)


@dataclass(frozen=True)
class SheetLayout:
    pageWidth: float
    pageHeight: float
    margin: float
    titleBlock: dict[str, float]
    supportingBand: dict[str, float]
    drawingZone: dict[str, float]
    scale: float
    origin: tuple[float, float]
    areaRatios: dict[str, float]

    def as_dict(self) -> dict[str, Any]:
        return {
            "page": {"width": self.pageWidth, "height": self.pageHeight},
            "margin": self.margin,
            "titleBlock": self.titleBlock,
            "supportingBand": self.supportingBand,
            "drawingZone": self.drawingZone,
            "scale": round(self.scale, 6),
            "origin": [round(value, 3) for value in self.origin],
            "areaRatios": self.areaRatios,
        }


def layout_for_extent(
    page_width: float,
    page_height: float,
    extent: tuple[float, float, float, float],
) -> SheetLayout:
    """Return a centred plan layout whose supporting content stays bounded."""

    min_x, min_y, max_x, max_y = extent
    if max_x <= min_x or max_y <= min_y:
        raise ValueError("drawing extent must have positive width and height")

    margin = max(float(SHEET_STANDARD["pageMarginPt"]), min(page_width, page_height) * 0.025)
    title_height = min(float(SHEET_STANDARD["titleBlockHeightPt"]), page_height * 0.14)
    support_height = min(float(SHEET_STANDARD["supportingBandHeightPt"]), page_height * 0.12)
    header_height = min(48.0, page_height * 0.07)

    title = {
        "x": margin,
        "y": margin,
        "width": page_width - 2 * margin,
        "height": title_height,
    }
    support = {
        "x": margin,
        "y": margin + title_height,
        "width": page_width - 2 * margin,
        "height": support_height,
    }
    drawing = {
        "x": margin,
        "y": margin + title_height + support_height,
        "width": page_width - 2 * margin,
        "height": page_height - 2 * margin - title_height - support_height - header_height,
    }
    if drawing["width"] <= 0 or drawing["height"] <= 0:
        raise ValueError("page is too small for the adopted sheet layout")

    extent_width = max_x - min_x
    extent_height = max_y - min_y
    scale = min(
        drawing["width"] / extent_width,
        drawing["height"] / extent_height,
    ) * 0.94
    origin = (
        drawing["x"] + (drawing["width"] - extent_width * scale) / 2 - min_x * scale,
        drawing["y"] + (drawing["height"] - extent_height * scale) / 2 - min_y * scale,
    )
    total_area = page_width * page_height
    occupied = (title_height + support_height) * page_width
    area_ratios = {
        "titleBlock": round(title_height * page_width / total_area, 4),
        "supportingContent": round(support_height * page_width / total_area, 4),
        "reservedNonDrawing": round(occupied / total_area, 4),
        "drawingZone": round(1 - occupied / total_area, 4),
    }
    return SheetLayout(
        pageWidth=page_width,
        pageHeight=page_height,
        margin=margin,
        titleBlock=title,
        supportingBand=support,
        drawingZone=drawing,
        scale=scale,
        origin=origin,
        areaRatios=area_ratios,
    )


def validate_layout(layout: SheetLayout) -> list[str]:
    """Return deterministic errors for use by report generators and tests."""

    errors: list[str] = []
    if layout.areaRatios["supportingContent"] > SHEET_STANDARD["supportingContentMaxAreaRatio"]:
        errors.append("supporting content exceeds the adopted 20% sheet-area cap")
    if layout.areaRatios["drawingZone"] < SHEET_STANDARD["drawingZoneMinAreaRatio"]:
        errors.append("drawing zone is below the adopted 65% minimum")
    if layout.scale <= 0:
        errors.append("drawing scale must be positive")
    return errors
