"""
TraeCAD Engine v0.1.0 — India's Parametric Architectural CAD Drafting Engine
=============================================================================

A reusable, project-agnostic Python library for generating professional
architectural DXF drawings and print-ready PDF documents.

Capabilities:
  - AutoCAD R2018 DXF generation with standard architectural layers
  - Parametric primitives: walls, doors, windows, columns, furniture
  - Arrow-free architectural dimension lines (slash-tick style)
  - Professional sheet borders and title blocks
  - Parametric furniture blocks (workstations, cabins, lockers)
  - PDF export with exact paper-size conformance (A4/A3/A1)
  - Multi-sheet PDF merging

Standards: NBC 2016 + RPwD Act 2016 + IS 4912 + IS 14666

Units: 1 drawing unit = 1 INCH (Imperial Standard, FT = 12.0)
       Metric support planned for v0.2.0

License: Proprietary — Trae AI Architecture Studio
Author:  Rajkumar C. Singh / Trae AI Architecture Studio
"""

__version__ = "0.1.0"
__author__ = "Rajkumar C. Singh"

import os
import math
from pathlib import Path
import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.config import (
    Configuration, BackgroundPolicy, ColorPolicy, LinePolicy
)
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pymupdf
from pypdf import PdfWriter


# ==============================================================================
# CONSTANTS & UNIT SYSTEM
# ==============================================================================

FT = 12.0   # 1 foot = 12 inches (drawing units)
IN = 1.0    # 1 inch  = 1 drawing unit
MM = 1.0 / 25.4  # 1 mm in drawing units (inches)

# Paper sizes in mm (width x height, landscape orientation)
PAPER_SIZES = {
    "A4": (297.0, 210.0),
    "A3": (420.0, 297.0),
    "A2": (594.0, 420.0),
    "A1": (841.0, 594.0),
    "A0": (1189.0, 841.0),
}

# Points per mm (for PDF MediaBox)
PT_PER_MM = 2.834645669

# ==============================================================================
# STANDARDIZED TEXT HEIGHTS (AIA / NBC 2016 Architectural Standards)
#
# Rational, 5-size modular hierarchy in 1/8" (3.175mm) increments.
# Printed size assumes 1/8" = 3.2mm minimum legibility per NBC 2016 Part 9.
# All values in drawing units (INCHES).
#
#   TIER        HEIGHT     USAGE
#   TX_MICRO    3/32"      Furniture tags (LIT/ADV), fine detail, locker IDs
#   TX_SMALL    1/8"       Room tags, schedule cells, notes
#   TX_MEDIUM   3/16"      Default body text, dimensions, bay labels
#   TX_LARGE    1/4"      Room names, sub-headings, aisle/row labels
#   TX_XL       5/16"     Sheet sub-titles, corridor labels, zone headings
#   TX_XXL      3/8"      Sheet titles, plan titles, major labels
#   TX_TITLE    1/2"      Cover/project titles, main drawing headings
#   TX_SUPER    3/4"      Largest plan-wide banner titles (rare)
# ==============================================================================
TX_MICRO  =  3.0 / 32.0   # 0.09375"  = 2.38 mm
TX_SMALL  =  1.0 / 8.0    # 0.125"    = 3.18 mm  (NBC min printable)
TX_MEDIUM =  3.0 / 16.0   # 0.1875"   = 4.76 mm  (DEFAULT body / dims)
TX_LARGE  =  1.0 / 4.0    # 0.25"     = 6.35 mm
TX_XL     =  5.0 / 16.0   # 0.3125"   = 7.94 mm
TX_XXL    =  3.0 / 8.0    # 0.375"    = 9.53 mm
TX_TITLE  =  1.0 / 2.0    # 0.50"     = 12.70 mm (sheet title block)
TX_SUPER  =  3.0 / 4.0    # 0.75"     = 19.05 mm (banner title)

# DIMENSION TEXT TICK OVERRIDES
TX_DIM_TEXT = TX_MEDIUM   # 3/16" dimension text
TX_DIM_TICK = TX_SMALL    # 1/8" extension/tick length

# TITLE BLOCK TEXT TIERS
TX_TB_LABEL = TX_MEDIUM   # Labels like "PROJECT:", "SHEET NO:"
TX_TB_VALUE_LG = TX_LARGE # Large values (project title, sheet title)
TX_TB_VALUE_MD = TX_MEDIUM# Medium values (client, scale, date, codes)
TX_TB_NOTE  = TX_SMALL    # Fine print / revision text


# ==============================================================================
# STANDARD ARCHITECTURAL LAYER DEFINITIONS (AIA/NBC COMPLIANT)
# ==============================================================================

ARCH_LAYERS = {
    "A-WALL":      dict(color=colors.WHITE,   linetype="CONTINUOUS", lineweight=50),
    "A-WALL-PATT": dict(color=9,              linetype="CONTINUOUS", lineweight=18),
    "A-COLUMN":    dict(color=colors.RED,      linetype="CONTINUOUS", lineweight=50),
    "A-DOOR":      dict(color=colors.YELLOW,   linetype="CONTINUOUS", lineweight=30),
    "A-WINDOW":    dict(color=colors.CYAN,     linetype="CONTINUOUS", lineweight=30),
    "A-JALI":      dict(color=colors.MAGENTA,  linetype="DASHED",    lineweight=18),
    "A-BAY":       dict(color=colors.GREEN,    linetype="CONTINUOUS", lineweight=25),
    "A-FURN":      dict(color=colors.RED,      linetype="CONTINUOUS", lineweight=18),
    "A-DIM":       dict(color=colors.CYAN,     linetype="CONTINUOUS", lineweight=15),
    "A-TEXT":      dict(color=colors.WHITE,    linetype="CONTINUOUS", lineweight=18),
    "A-TEXT-TTL":  dict(color=colors.WHITE,    linetype="CONTINUOUS", lineweight=35),
    "A-GRID":      dict(color=colors.MAGENTA,  linetype="DASHED",    lineweight=13),
    "A-HATCH":     dict(color=8,               linetype="CONTINUOUS", lineweight=13),
    "A-SITE":      dict(color=colors.YELLOW,   linetype="CONTINUOUS", lineweight=30),
    "A-ROOF":      dict(color=colors.BLUE,     linetype="CONTINUOUS", lineweight=25),
    "A-SECT-CUT":  dict(color=colors.RED,      linetype="PHANTOM",   lineweight=50),
    "A-TTLB":      dict(color=colors.WHITE,    linetype="CONTINUOUS", lineweight=35),
    "A-LOCKER":    dict(color=colors.GREEN,    linetype="CONTINUOUS", lineweight=25),
    "A-ACC":       dict(color=colors.BLUE,     linetype="CONTINUOUS", lineweight=25),
}


# ==============================================================================
# PROJECT CONFIGURATION CLASS
# ==============================================================================

class ProjectConfig:
    """
    Holds all project-specific metadata. Pass an instance to drawing functions
    so the engine remains project-agnostic.
    """
    def __init__(
        self,
        project_title="UNTITLED PROJECT",
        client="CLIENT NAME",
        date="01 JAN 2026",
        drawn_by="TraeCAD Engine",
        code_ref="NBC 2016",
        doc_ref="DOC-REF-v1.0",
        base_dir=None,
        dxf_subdir="CAD-Drawings/DXF",
        pdf_subdir="CAD-Drawings/PDF",
        paper_size="A4",
        margin_mm=20.0,
    ):
        self.project_title = project_title
        self.client = client
        self.date = date
        self.drawn_by = drawn_by
        self.code_ref = code_ref
        self.doc_ref = doc_ref
        self.paper_size = paper_size
        self.margin_mm = margin_mm

        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path.cwd()

        self.dxf_dir = self.base_dir / dxf_subdir
        self.pdf_dir = self.base_dir / pdf_subdir
        self.dxf_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)

    @property
    def paper_w_mm(self):
        return PAPER_SIZES[self.paper_size][0]

    @property
    def paper_h_mm(self):
        return PAPER_SIZES[self.paper_size][1]

    @property
    def printable_w_mm(self):
        return self.paper_w_mm - 2 * self.margin_mm

    @property
    def printable_h_mm(self):
        return self.paper_h_mm - 2 * self.margin_mm


# Default sheet dimensions in drawing units (matching A4 with 20mm margins)
def sheet_dims(config=None):
    """Returns (sheet_width, sheet_height) in drawing units for the given paper config."""
    sw = 150.0 * FT
    if config:
        sh = sw * (config.printable_h_mm / config.printable_w_mm)
    else:
        sh = sw * (170.0 / 257.0)  # A4 default
    return sw, sh


# ==============================================================================
# DOCUMENT SETUP
# ==============================================================================

def setup_doc(sheet_w=None, sheet_h=None, config=None, extra_layers=None):
    """
    Create a clean DXF document with standard architectural layers, styles,
    and sheet bounds.

    Args:
        sheet_w: Sheet width in drawing units (auto-calculated if None)
        sheet_h: Sheet height in drawing units (auto-calculated if None)
        config:  ProjectConfig instance (optional)
        extra_layers: dict of additional layers to add

    Returns:
        (doc, msp) tuple
    """
    if sheet_w is None or sheet_h is None:
        sw, sh = sheet_dims(config)
        sheet_w = sheet_w or sw
        sheet_h = sheet_h or sh

    doc = ezdxf.new(dxfversion="R2018", setup=True)
    doc.header["$INSUNITS"] = 1   # Inches
    doc.header["$MEASUREMENT"] = 0  # Imperial
    msp = doc.modelspace()

    # Register standard architectural layers
    all_layers = dict(ARCH_LAYERS)
    if extra_layers:
        all_layers.update(extra_layers)

    for name, props in all_layers.items():
        if name not in doc.layers:
            layer = doc.layers.add(name)
            layer.color = props["color"]
            layer.linetype = props["linetype"]
            layer.lineweight = props["lineweight"]

    # Register text styles
    for style_name, font_file in [("ARCH-STYLE", "ARCHITXT.TTF"), ("SIMPLEX", "simplex.shx")]:
        if style_name not in doc.styles:
            try:
                doc.styles.add(style_name, font=font_file)
            except Exception:
                pass

    doc._sheet_w = sheet_w
    doc._sheet_h = sheet_h
    return doc, msp


# ==============================================================================
# GEOMETRY & ARCHITECTURAL DRAFTING PRIMITIVES
# ==============================================================================

def rect(msp, x1, y1, x2, y2, layer="A-WALL", lw=None):
    """Draw a rectangle outline."""
    min_x, max_x = min(x1, x2), max(x1, x2)
    min_y, max_y = min(y1, y2), max(y1, y2)
    pts = [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]
    for i in range(4):
        p1, p2 = pts[i], pts[(i + 1) % 4]
        a = dict(layer=layer)
        if lw:
            a["lineweight"] = lw
        msp.add_line(p1, p2, dxfattribs=a)


def fill_rect(msp, x1, y1, x2, y2, hatch="SOLID", layer="A-HATCH"):
    """Fill a rectangular area with hatch pattern."""
    min_x, max_x = min(x1, x2), max(x1, x2)
    min_y, max_y = min(y1, y2), max(y1, y2)
    try:
        h = msp.add_hatch(color=8, dxfattribs={"layer": layer})
        h.set_pattern_fill(hatch, scale=1.0)
        h.paths.add_polyline_path(
            [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)],
            is_closed=True,
        )
    except Exception:
        pass


def circle(msp, cx, cy, radius, layer="A-FURN", lw=None):
    """Draw a circle."""
    attribs = {"layer": layer}
    if lw:
        attribs["lineweight"] = lw
    try:
        msp.add_circle((cx, cy), radius, dxfattribs=attribs)
    except Exception:
        pass


def line(msp, x1, y1, x2, y2, layer="A-WALL", lw=None):
    """Draw a single line."""
    attribs = {"layer": layer}
    if lw:
        attribs["lineweight"] = lw
    msp.add_line((x1, y1), (x2, y2), dxfattribs=attribs)


def polyline(msp, points, layer="A-WALL", lw=None, closed=False):
    """Draw a polyline through a list of (x, y) points."""
    attribs = {"layer": layer}
    if lw:
        attribs["lineweight"] = lw
    pts = list(points)
    if closed and pts and pts[0] != pts[-1]:
        pts.append(pts[0])
    for i in range(len(pts) - 1):
        msp.add_line(pts[i], pts[i + 1], dxfattribs=attribs)


# ==============================================================================
# TEXT & ANNOTATIONS
# ==============================================================================

def text_msp(msp, txt, x, y, h=TX_MEDIUM * FT, layer="A-TEXT", style="SIMPLEX",
             align=TextEntityAlignment.MIDDLE_CENTER, rot=0.0):
    """
    Add clean text with exact alignment. Handles multi-line text and
    strips non-ASCII glyphs to prevent rendering boxes.
    """
    if not txt:
        return None

    clean_txt = (
        str(txt)
        .replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2192", "->")
        .replace("\u2713", "[OK]")
        .replace("\u25ba", ">")
        .replace("\u25c4", "<")
        .replace("\u2605", "*")
    )

    lines = clean_txt.split("\n")
    if len(lines) > 1:
        line_spacing = h * 1.35
        total_ht = (len(lines) - 1) * line_spacing
        for idx, ln in enumerate(lines):
            line_y = y + (total_ht / 2.0) - (idx * line_spacing)
            try:
                t = msp.add_text(
                    ln,
                    dxfattribs={"layer": layer, "height": h, "style": style, "rotation": rot},
                )
                t.set_placement((x, line_y), align=align)
            except Exception:
                pass
        return None

    try:
        t = msp.add_text(
            clean_txt,
            dxfattribs={"layer": layer, "height": h, "style": style, "rotation": rot},
        )
        t.set_placement((x, y), align=align)
        return t
    except Exception:
        try:
            t = msp.add_text(
                clean_txt,
                dxfattribs={"layer": layer, "height": h, "rotation": rot},
            )
            t.dxf.insert = (x, y, 0)
            return t
        except Exception:
            return None


# ==============================================================================
# ARCHITECTURAL DIMENSION LINES (ARROW-FREE, SLASH-TICK STYLE)
# ==============================================================================

def arch_dim_h(msp, x1, y, x2, txt, offset=1.2 * FT, tick_sz=TX_DIM_TICK * FT,
               layer="A-DIM", text_h=TX_DIM_TEXT * FT):
    """Standard Horizontal Architectural Dimension Line with 45-degree slash ticks."""
    if x1 > x2:
        x1, x2 = x2, x1
    yd = y + offset
    msp.add_line((x1, yd), (x2, yd), dxfattribs={"layer": layer, "lineweight": 18})
    ext_gap = 0.25 * FT if offset > 0 else -0.25 * FT
    ext_over = 0.35 * FT if offset > 0 else -0.35 * FT
    msp.add_line((x1, y + ext_gap), (x1, yd + ext_over), dxfattribs={"layer": layer, "lineweight": 13})
    msp.add_line((x2, y + ext_gap), (x2, yd + ext_over), dxfattribs={"layer": layer, "lineweight": 13})
    ts = tick_sz
    msp.add_line((x1 - ts * 0.5, yd - ts * 0.5), (x1 + ts * 0.5, yd + ts * 0.5),
                 dxfattribs={"layer": layer, "lineweight": 30})
    msp.add_line((x2 - ts * 0.5, yd - ts * 0.5), (x2 + ts * 0.5, yd + ts * 0.5),
                 dxfattribs={"layer": layer, "lineweight": 30})
    ty = yd + 0.32 * FT if offset >= 0 else yd - 0.48 * FT
    text_msp(
        msp, txt, (x1 + x2) / 2.0, ty, h=text_h, layer=layer,
        align=TextEntityAlignment.BOTTOM_CENTER if offset >= 0 else TextEntityAlignment.TOP_CENTER,
    )


def arch_dim_v(msp, x, y1, y2, txt, offset=1.2 * FT, tick_sz=TX_DIM_TICK * FT,
               layer="A-DIM", text_h=TX_DIM_TEXT * FT):
    """Standard Vertical Architectural Dimension Line with 45-degree slash ticks."""
    if y1 > y2:
        y1, y2 = y2, y1
    xd = x + offset
    msp.add_line((xd, y1), (xd, y2), dxfattribs={"layer": layer, "lineweight": 18})
    ext_gap = 0.25 * FT if offset > 0 else -0.25 * FT
    ext_over = 0.35 * FT if offset > 0 else -0.35 * FT
    msp.add_line((x + ext_gap, y1), (xd + ext_over, y1), dxfattribs={"layer": layer, "lineweight": 13})
    msp.add_line((x + ext_gap, y2), (xd + ext_over, y2), dxfattribs={"layer": layer, "lineweight": 13})
    ts = tick_sz
    msp.add_line((xd - ts * 0.5, y1 - ts * 0.5), (xd + ts * 0.5, y1 + ts * 0.5),
                 dxfattribs={"layer": layer, "lineweight": 30})
    msp.add_line((xd - ts * 0.5, y2 - ts * 0.5), (xd + ts * 0.5, y2 + ts * 0.5),
                 dxfattribs={"layer": layer, "lineweight": 30})
    tx = xd + 0.35 * FT if offset >= 0 else xd - 0.35 * FT
    text_msp(
        msp, txt, tx, (y1 + y2) / 2.0, h=text_h, layer=layer, rot=90.0,
        align=TextEntityAlignment.BOTTOM_CENTER if offset >= 0 else TextEntityAlignment.TOP_CENTER,
    )


# ==============================================================================
# SHEET FRAME & TITLE BLOCK
# ==============================================================================

def draw_north_arrow(msp, x, y, size=3.0 * FT):
    """Draws a clean, standard architectural North arrow."""
    r = size * 0.5
    try:
        msp.add_circle((x, y), r, dxfattribs={"layer": "A-TTLB", "lineweight": 20})
    except Exception:
        pass
    top_pt = (x, y + r * 0.9)
    left_pt = (x - r * 0.45, y - r * 0.45)
    right_pt = (x + r * 0.45, y - r * 0.45)
    cen_pt = (x, y - r * 0.15)
    try:
        h = msp.add_hatch(color=7, dxfattribs={"layer": "A-TTLB"})
        h.set_pattern_fill("SOLID", scale=1.0)
        h.paths.add_polyline_path([top_pt, left_pt, cen_pt], is_closed=True)
    except Exception:
        pass
    msp.add_line(top_pt, right_pt, dxfattribs={"layer": "A-TTLB", "lineweight": 20})
    msp.add_line(right_pt, cen_pt, dxfattribs={"layer": "A-TTLB", "lineweight": 20})
    text_msp(msp, "N", x, y + r + 0.5 * FT, h=TX_LARGE * FT, layer="A-TEXT-TTL")


def draw_sheet_frame_and_titleblock(
    msp, sw, sh, sheet_no, sheet_title, scale_txt,
    config=None, rev="0", subtitle="", notes=None,
    # Legacy keyword args for backward compatibility
    project_title=None, client=None, draw_date=None, code_ref=None, doc_ref=None,
):
    """
    Draws professional architectural sheet border, top caption banner,
    and bottom title block fitted to whole sheet page.
    """
    _project_title = project_title or (config.project_title if config else "PROJECT TITLE")
    _client = client or (config.client if config else "CLIENT")
    _draw_date = draw_date or (config.date if config else "DATE")
    _code_ref = code_ref or (config.code_ref if config else "NBC 2016")
    _doc_ref = doc_ref or (config.doc_ref if config else "DOC-REF")

    # Outer Border
    rect(msp, 0, 0, sw, sh, layer="A-TTLB", lw=50)
    ib = 0.5 * FT
    rect(msp, ib, ib, sw - ib, sh - ib, layer="A-TTLB", lw=25)

    # TOP CAPTION BANNER
    cap_y1 = sh - ib - 5.5 * FT
    cap_y2 = sh - ib
    rect(msp, ib, cap_y1, sw - ib, cap_y2, layer="A-TTLB", lw=35)
    text_msp(msp, f"{sheet_no.upper()}  -  {sheet_title.upper()}",
             sw / 2.0, cap_y2 - 1.8 * FT, h=TX_SUPER * FT, layer="A-TEXT-TTL")
    text_msp(msp, f"{_project_title}  |  {_client}  |  SCALE: {scale_txt}",
             sw / 2.0, cap_y1 + 1.4 * FT, h=TX_XL * FT, layer="A-TEXT-TTL")

    # BOTTOM TITLE BLOCK
    tb_w = 56.0 * FT
    tb_h = 8.6 * FT
    tb_x1 = sw - ib - tb_w
    tb_y1 = ib
    tb_x2 = sw - ib
    tb_y2 = ib + tb_h

    rect(msp, tb_x1, tb_y1, tb_x2, tb_y2, layer="A-TTLB", lw=35)
    y_divs = [tb_y1 + 1.2 * FT, tb_y1 + 2.4 * FT, tb_y1 + 4.2 * FT, tb_y1 + 6.2 * FT]
    for yd in y_divs:
        msp.add_line((tb_x1, yd), (tb_x2, yd), dxfattribs={"layer": "A-TTLB", "lineweight": 20})

    col_x1 = tb_x1 + 11.0 * FT
    col_x2 = tb_x1 + 34.0 * FT
    col_x3 = tb_x1 + 44.0 * FT
    msp.add_line((col_x1, tb_y1), (col_x1, tb_y2), dxfattribs={"layer": "A-TTLB", "lineweight": 20})
    msp.add_line((col_x2, tb_y1), (col_x2, tb_y1 + 4.2 * FT), dxfattribs={"layer": "A-TTLB", "lineweight": 20})
    msp.add_line((col_x3, tb_y1), (col_x3, tb_y1 + 4.2 * FT), dxfattribs={"layer": "A-TTLB", "lineweight": 20})

    text_msp(msp, "PROJECT:", tb_x1 + 0.5 * FT, tb_y2 - 1.1 * FT, h=TX_TB_LABEL * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
    text_msp(msp, _project_title, col_x1 + 0.6 * FT, tb_y2 - 1.1 * FT, h=TX_TB_VALUE_LG * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)

    text_msp(msp, "DRAWING TITLE:", tb_x1 + 0.5 * FT, tb_y1 + 5.2 * FT, h=TX_TB_LABEL * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
    text_msp(msp, sheet_title, col_x1 + 0.6 * FT, tb_y1 + 5.2 * FT, h=TX_TB_VALUE_LG * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)

    text_msp(msp, "CLIENT:", tb_x1 + 0.5 * FT, tb_y1 + 3.3 * FT, h=TX_TB_LABEL * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
    text_msp(msp, _client, col_x1 + 0.6 * FT, tb_y1 + 3.3 * FT, h=TX_TB_VALUE_MD * FT, layer="A-TEXT", align=TextEntityAlignment.LEFT)

    text_msp(msp, "SHEET NO:", col_x2 + 0.5 * FT, tb_y1 + 3.3 * FT, h=TX_TB_LABEL * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
    text_msp(msp, sheet_no, col_x3 + 0.5 * FT, tb_y1 + 3.3 * FT, h=TX_TB_VALUE_LG * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)

    text_msp(msp, "SCALE:", tb_x1 + 0.5 * FT, tb_y1 + 1.8 * FT, h=TX_TB_LABEL * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
    text_msp(msp, scale_txt, col_x1 + 0.6 * FT, tb_y1 + 1.8 * FT, h=TX_TB_VALUE_MD * FT, layer="A-TEXT", align=TextEntityAlignment.LEFT)

    text_msp(msp, "DATE:", col_x2 + 0.5 * FT, tb_y1 + 1.8 * FT, h=TX_TB_LABEL * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
    text_msp(msp, _draw_date, col_x3 + 0.5 * FT, tb_y1 + 1.8 * FT, h=TX_TB_VALUE_MD * FT, layer="A-TEXT", align=TextEntityAlignment.LEFT)

    text_msp(msp, "CODES / REF:", tb_x1 + 0.5 * FT, tb_y1 + 0.6 * FT, h=TX_TB_LABEL * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
    text_msp(msp, f"{_code_ref}  |  DOC: {_doc_ref}  |  REV: {rev}", col_x1 + 0.6 * FT, tb_y1 + 0.6 * FT, h=TX_TB_NOTE * FT, layer="A-TEXT", align=TextEntityAlignment.LEFT)

    # North Arrow
    nx, ny = sw - ib - 4.5 * FT, sh - ib - 9.0 * FT
    draw_north_arrow(msp, nx, ny, size=2.6 * FT)

    # Notes Box
    if notes:
        nb_x1 = ib + 0.5 * FT
        nb_y1 = ib + 0.5 * FT
        nb_w = 54.0 * FT
        nb_h = 8.0 * FT
        rect(msp, nb_x1, nb_y1, nb_x1 + nb_w, nb_y1 + nb_h, layer="A-TTLB", lw=20)
        text_msp(msp, "GENERAL NOTES & COMPLIANCE:", nb_x1 + 0.6 * FT, nb_y1 + nb_h - 0.6 * FT, h=TX_LARGE * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
        for i, n in enumerate(notes):
            text_msp(msp, f"* {n}", nb_x1 + 0.6 * FT, nb_y1 + nb_h - 1.4 * FT - (i * 0.60 * FT), h=TX_MEDIUM * FT, layer="A-TEXT", align=TextEntityAlignment.LEFT)


# ==============================================================================
# PARAMETRIC FURNITURE BLOCKS
# ==============================================================================

def bay_compact(msp, bx, by, w=5.0 * FT, d=6.5 * FT, label="1", orientation="S"):
    """Type A Compact Workstation: Advocate on one side, 2 Litigants opposite."""
    msp.add_line((bx, by + d), (bx + w, by + d), dxfattribs={"layer": "A-JALI", "lineweight": 20})
    msp.add_line((bx, by), (bx, by + d), dxfattribs={"layer": "A-JALI", "lineweight": 20})
    msp.add_line((bx + w, by), (bx + w, by + d), dxfattribs={"layer": "A-BAY", "lineweight": 15})
    msp.add_line((bx, by), (bx + w, by), dxfattribs={"layer": "A-BAY", "lineweight": 15})

    dw = min(4.0 * FT, w - 0.6 * FT)
    dd = 1.3 * FT
    desk_x1 = bx + (w - dw) / 2.0
    desk_x2 = desk_x1 + dw
    desk_y1 = by + (d - dd) / 2.0
    desk_y2 = desk_y1 + dd

    rect(msp, desk_x1, desk_y1, desk_x2, desk_y2, layer="A-FURN", lw=20)
    text_msp(msp, f"BAY {label}", bx + w / 2.0, (desk_y1 + desk_y2) / 2.0, h=TX_LARGE * FT, layer="A-BAY")

    if orientation == "S":
        adv_y = desk_y2 + 0.6 * FT
        circle(msp, bx + w / 2.0, adv_y, 0.35 * FT, layer="A-FURN", lw=18)
        text_msp(msp, "ADV", bx + w / 2.0, adv_y, h=TX_SMALL * FT, layer="A-FURN")
        lit_y = desk_y1 - 0.6 * FT
        circle(msp, bx + w * 0.28, lit_y, 0.28 * FT, layer="A-FURN", lw=15)
        circle(msp, bx + w * 0.72, lit_y, 0.28 * FT, layer="A-FURN", lw=15)
        text_msp(msp, "LIT", bx + w * 0.28, lit_y, h=TX_MICRO * FT, layer="A-FURN")
        text_msp(msp, "LIT", bx + w * 0.72, lit_y, h=TX_MICRO * FT, layer="A-FURN")
    else:
        adv_y = desk_y1 - 0.6 * FT
        circle(msp, bx + w / 2.0, adv_y, 0.35 * FT, layer="A-FURN", lw=18)
        text_msp(msp, "ADV", bx + w / 2.0, adv_y, h=TX_SMALL * FT, layer="A-FURN")
        lit_y = desk_y2 + 0.6 * FT
        circle(msp, bx + w * 0.28, lit_y, 0.28 * FT, layer="A-FURN", lw=15)
        circle(msp, bx + w * 0.72, lit_y, 0.28 * FT, layer="A-FURN", lw=15)
        text_msp(msp, "LIT", bx + w * 0.28, lit_y, h=TX_MICRO * FT, layer="A-FURN")
        text_msp(msp, "LIT", bx + w * 0.72, lit_y, h=TX_MICRO * FT, layer="A-FURN")


def bay_premium(msp, bx, by, w=8.0 * FT, d=10.0 * FT, label="P1"):
    """Type B Senior Advocate Premium Cabin."""
    rect(msp, bx, by, bx + w, by + d, layer="A-WALL", lw=30)
    msp.add_line((bx, by), (bx + 3.0 * FT, by), dxfattribs={"layer": "A-DOOR", "lineweight": 30})

    desk_w, desk_d = 5.0 * FT, 2.3 * FT
    desk_x1 = bx + (w - desk_w) / 2.0
    desk_x2 = desk_x1 + desk_w
    desk_y1 = by + 4.0 * FT
    desk_y2 = desk_y1 + desk_d
    rect(msp, desk_x1, desk_y1, desk_x2, desk_y2, layer="A-FURN", lw=20)
    text_msp(msp, f"CABIN {label}\nDESK 5'x2.5'", bx + w / 2.0, (desk_y1 + desk_y2) / 2.0, h=TX_MEDIUM * FT, layer="A-FURN")

    adv_y = desk_y2 + 1.2 * FT
    circle(msp, bx + w / 2.0, adv_y, 0.48 * FT, layer="A-FURN", lw=20)
    text_msp(msp, "ADVOCATE", bx + w / 2.0, adv_y, h=TX_LARGE * FT, layer="A-FURN")

    lit_y = desk_y1 - 1.2 * FT
    for cx in [bx + 2.0 * FT, bx + 4.0 * FT, bx + 6.0 * FT]:
        circle(msp, cx, lit_y, 0.35 * FT, layer="A-FURN", lw=15)
        text_msp(msp, "CLIENT", cx, lit_y, h=TX_SMALL * FT, layer="A-FURN")

    rect(msp, bx + w - 1.2 * FT, by + 1.8 * FT, bx + w - 0.2 * FT, by + d - 1.5 * FT, layer="A-FURN")
    text_msp(msp, "BOOKS / FILES", bx + w - 0.7 * FT, by + d / 2.0, h=TX_MEDIUM * FT, layer="A-FURN", rot=90.0)


def locker_bank(msp, bx, by, num_cols, num_tiers, bank_label="",
                locker_w=1.0 * FT, locker_h=1.0 * FT, locker_d=1.25 * FT,
                col_start=1, type_code="ADV"):
    """Draws a bank of CRCA steel lockers."""
    total_w = num_cols * locker_w
    total_d = locker_d
    rect(msp, bx, by, bx + total_w, by + total_d, layer="A-LOCKER", lw=35)
    for i in range(num_cols + 1):
        lx = bx + i * locker_w
        msp.add_line((lx, by), (lx, by + total_d), dxfattribs={"layer": "A-LOCKER"})
    for i in range(num_cols):
        cx = bx + i * locker_w + locker_w * 0.5
        locker_id = f"{type_code}-{col_start + i}"
        text_msp(msp, locker_id, cx, by + total_d * 0.5, h=TX_SMALL * FT, layer="A-LOCKER")
    if bank_label:
        text_msp(msp, bank_label, bx + total_w / 2.0, by - 0.5 * FT, h=TX_XL * FT, layer="A-TEXT-TTL")
    total_cap = num_cols * num_tiers
    text_msp(msp, f"{num_cols}W x {num_tiers}H = {total_cap} LOCKERS",
             bx + total_w / 2.0, by + total_d + 0.35 * FT, h=TX_MEDIUM * FT, layer="A-TEXT")
    arch_dim_h(msp, bx, by - 1.2 * FT, bx + total_w,
               f"{total_w / FT:.1f}' ({num_cols}x12\")", offset=-0.25 * FT)
    return total_w, total_d


# ==============================================================================
# NEW PARAMETRIC BLOCKS (WEEK 2+ EXPANSION)
# ============================================================================def door_swing(msp, x, y, width=3.0 * FT, swing="left", layer="A-DOOR", door_type="accessible", auto_correct=True):
    """
    Standard door with 90-degree swing arc.
    NBC 2016 & RPwD 2016 compliance checks built-in.
    """
    # Compliance rules
    min_width = 3.0 * FT  # 900mm default accessible / commercial / main residential
    if door_type == "toilet":
        min_width = 2.5 * FT  # 750mm (minimum for standard non-accessible toilet)
    
    if width < min_width:
        msg = f"[Compliance Warn] Door type '{door_type}' at ({x:.1f}, {y:.1f}) width {width/FT:.2f} ft is less than NBC/RPwD minimum {min_width/FT:.2f} ft."
        if auto_correct:
            print(f"{msg} Auto-correcting to {min_width/FT:.2f} ft.")
            width = min_width
        else:
            print(msg)

    if swing == "left":
        msp.add_line((x, y), (x + width, y), dxfattribs={"layer": layer, "lineweight": 30})
        try:
            msp.add_arc(center=(x, y), radius=width, start_angle=0, end_angle=90,
                        dxfattribs={"layer": layer, "lineweight": 13})
        except Exception:
            pass
    else:
        msp.add_line((x, y), (x - width, y), dxfattribs={"layer": layer, "lineweight": 30})
        try:
            msp.add_arc(center=(x, y), radius=width, start_angle=90, end_angle=180,
                        dxfattribs={"layer": layer, "lineweight": 13})
        except Exception:
            pass


def window_opening(msp, x1, y, x2, sill_ht=3.0 * FT, win_ht=4.0 * FT, layer="A-WINDOW", room_area=None, climate="dry"):
    """
    Standard window opening in elevation/section view.
    NBC compliance checks for natural light & ventilation.
    """
    win_w = abs(x2 - x1)
    win_area = win_w * win_ht
    
    if room_area:
        ratio = 10.0 if climate == "dry" else 6.0
        min_win_area = room_area / ratio
        if win_area < min_win_area:
            print(f"[Compliance Warn] Window area ({win_area/144:.2f} sq ft) is below NBC minimum ventilation requirement of 1/{int(ratio)} of room area ({min_win_area/144:.2f} sq ft).")

    # Draw window
    sill_y = y + sill_ht
    head_y = sill_y + win_ht
    rect(msp, x1, sill_y, x2, head_y, layer=layer, lw=25)
    mid_x = (x1 + x2) / 2.0
    msp.add_line((mid_x, sill_y), (mid_x, head_y), dxfattribs={"layer": layer, "lineweight": 13})
    msp.add_line((x1 - 0.25 * FT, sill_y), (x2 + 0.25 * FT, sill_y),
                 dxfattribs={"layer": layer, "lineweight": 25})


def staircase_plan(msp, x, y, width=4.0 * FT, num_risers=12, tread=11.8 * IN,
                   direction="up_north", stair_type="public", auto_correct=True, layer="A-WALL"):
    """
    Standard staircase in plan view.
    NBC 2016 compliance checks built-in.
    """
    min_width = 1.5 * FT if stair_type == "public" else 1.0 * FT
    min_tread = 11.8 * IN if stair_type == "public" else 9.8 * IN
    
    if width < min_width:
        msg = f"[Compliance Warn] staircase width ({width/FT:.2f} ft) is below NBC minimum of {min_width/FT:.2f} ft for {stair_type} stairs."
        if auto_correct:
            print(f"{msg} Auto-correcting width to {min_width/FT:.2f} ft.")
            width = min_width
        else:
            print(msg)
            
    if tread < min_tread:
        msg = f"[Compliance Warn] staircase tread depth ({tread:.1f} in) is below NBC minimum of {min_tread:.1f} in for {stair_type} stairs."
        if auto_correct:
            print(f"{msg} Auto-correcting tread to {min_tread:.1f} in.")
            tread = min_tread
        else:
            print(msg)

    total_run = num_risers * tread
    if direction == "up_north":
        rect(msp, x, y, x + width, y + total_run, layer=layer, lw=30)
        for i in range(num_risers + 1):
            ty = y + i * tread
            msp.add_line((x, ty), (x + width, ty), dxfattribs={"layer": layer, "lineweight": 13})
        # UP arrow indicator
        mid_x = x + width / 2.0
        msp.add_line((mid_x, y + 1 * tread), (mid_x, y + total_run - 1 * tread),
                     dxfattribs={"layer": layer, "lineweight": 18})
        msp.add_line((mid_x, y + total_run - 1 * tread), (mid_x - 0.4 * FT, y + total_run - 2 * tread),
                     dxfattribs={"layer": layer, "lineweight": 18})
        msp.add_line((mid_x, y + total_run - 1 * tread), (mid_x + 0.4 * FT, y + total_run - 2 * tread),
                     dxfattribs={"layer": layer, "lineweight": 18})
        text_msp(msp, "UP", mid_x, y + total_run / 2.0, h=TX_LARGE * FT, layer="A-TEXT-TTL")
    elif direction == "up_east":
        rect(msp, x, y, x + total_run, y + width, layer=layer, lw=30)
        for i in range(num_risers + 1):
            tx = x + i * tread
            msp.add_line((tx, y), (tx, y + width), dxfattribs={"layer": layer, "lineweight": 13})
        mid_y = y + width / 2.0
        msp.add_line((x + 1 * tread, mid_y), (x + total_run - 1 * tread, mid_y),
                     dxfattribs={"layer": layer, "lineweight": 18})
        msp.add_line((x + total_run - 1 * tread, mid_y), (x + total_run - 2 * tread, mid_y - 0.4 * FT),
                     dxfattribs={"layer": layer, "lineweight": 18})
        msp.add_line((x + total_run - 1 * tread, mid_y), (x + total_run - 2 * tread, mid_y + 0.4 * FT),
                     dxfattribs={"layer": layer, "lineweight": 18})
        text_msp(msp, "UP", x + total_run / 2.0, mid_y, h=TX_LARGE * FT, layer="A-TEXT-TTL")

    return width, total_run


def staircase_section(msp, x, y, run=10.0 * FT, rise=10.0 * FT, num_risers=18, stair_type="public", auto_correct=True, layer="A-WALL"):
    """
    Standard staircase in sectional elevation view.
    NBC 2016 compliance checks built-in.
    """
    riser_ht = rise / num_risers
    tread_depth = run / (num_risers - 1)
    
    max_riser = 5.9 * IN if stair_type == "public" else 7.5 * IN
    if riser_ht > max_riser:
        msg = f"[Compliance Warn] staircase riser height ({riser_ht:.1f} in) exceeds NBC maximum of {max_riser:.1f} in for {stair_type} stairs."
        if auto_correct:
            needed_risers = math.ceil(rise / max_riser)
            print(f"{msg} Auto-correcting: increasing risers from {num_risers} to {needed_risers}.")
            num_risers = needed_risers
            riser_ht = rise / num_risers
            tread_depth = run / (num_risers - 1)
        else:
            print(msg)

    px, py = x, y
    for i in range(num_risers):
        msp.add_line((px, py), (px, py + riser_ht), dxfattribs={"layer": layer, "lineweight": 30})
        py += riser_ht
        if i < num_risers - 1:
            msp.add_line((px, py), (px + tread_depth, py), dxfattribs={"layer": layer, "lineweight": 30})
            px += tread_depth
            
    msp.add_line((x, y), (px, py), dxfattribs={"layer": layer, "lineweight": 20})
    return px - x, py - y


def toilet_block(msp, x, y, num_wc=3, num_urinals=2, num_basins=3,
                 accessible=True, layer="A-FURN"):
    """
    NBC 2016 & RPwD 2016 compliant toilet block in plan view.
    Renders detailed grab rails and turning radius for accessible stalls.
    """
    wc_w, wc_d = 3.5 * FT, 5.0 * FT
    urinal_w = 2.5 * FT
    basin_w = 2.0 * FT
    passage_w = 4.0 * FT

    cx = x
    for i in range(num_wc):
        rect(msp, cx, y, cx + wc_w, y + wc_d, layer="A-WALL", lw=25)
        text_msp(msp, f"WC-{i+1}", cx + wc_w / 2.0, y + wc_d / 2.0, h=TX_MEDIUM * FT, layer=layer)
        rect(msp, cx + 0.5 * FT, y + 0.5 * FT, cx + wc_w - 0.5 * FT, y + 2.0 * FT, layer=layer, lw=13)
        cx += wc_w + 0.25 * FT

    if accessible:
        acc_w, acc_d = 5.0 * FT, 6.0 * FT
        rect(msp, cx, y, cx + acc_w, y + acc_d, layer="A-ACC", lw=30)
        
        msp.add_line((cx + 1.0 * FT, y + 0.5 * FT), (cx + 4.0 * FT, y + 0.5 * FT), dxfattribs={"layer": "A-ACC", "lineweight": 25})
        msp.add_line((cx + 0.5 * FT, y + 1.5 * FT), (cx + 0.5 * FT, y + 4.5 * FT), dxfattribs={"layer": "A-ACC", "lineweight": 25})
        
        circle(msp, cx + acc_w / 2.0, y + acc_d / 2.0 + 0.5 * FT, 2.5 * FT, layer="A-JALI", lw=13)
        text_msp(msp, "RPwD 5' DIA\nTURNING CIRCLE", cx + acc_w / 2.0, y + acc_d / 2.0 + 0.5 * FT, h=TX_MICRO * FT, layer="A-ACC")
        
        door_swing(msp, cx + acc_w, y + acc_d, width=3.0 * FT, swing="left", layer="A-ACC")
        text_msp(msp, "ACC WC\n(OUTSWING DOOR)", cx + acc_w / 2.0, y + 1.5 * FT, h=TX_MEDIUM * FT, layer="A-ACC")
        
        cx += acc_w + 0.25 * FT

    for i in range(num_urinals):
        rect(msp, cx, y, cx + urinal_w, y + 2.0 * FT, layer="A-WALL", lw=20)
        text_msp(msp, f"UR-{i+1}", cx + urinal_w / 2.0, y + 1.0 * FT, h=TX_SMALL * FT, layer=layer)
        cx += urinal_w + 0.25 * FT

    basin_y = y + wc_d + passage_w
    bx = x
    for i in range(num_basins):
        rect(msp, bx, basin_y, bx + basin_w, basin_y + 1.5 * FT, layer=layer, lw=18)
        circle(msp, bx + basin_w / 2.0, basin_y + 0.75 * FT, 0.4 * FT, layer=layer, lw=13)
        text_msp(msp, f"WB-{i+1}", bx + basin_w / 2.0, basin_y - 0.4 * FT, h=TX_MICRO * FT, layer=layer)
        bx += basin_w + 0.5 * FT

    return cx - x, wc_d + passage_w + 1.5 * FT* FT


# ==============================================================================
# DXF SAVE
# ==============================================================================

def save_drawing(doc, filename, config=None):
    """Save the DXF document to the project's DXF directory."""
    if config:
        dxf_dir = config.dxf_dir
    else:
        dxf_dir = Path(__file__).resolve().parent.parent / "CAD-Drawings" / "DXF"
    dxf_dir.mkdir(parents=True, exist_ok=True)
    fpath = dxf_dir / f"{filename}.dxf"
    doc.saveas(str(fpath))
    doc._last_path = fpath
    sz = fpath.stat().st_size
    print(f"  [OK] DXF saved: {fpath.name} ({sz:,} bytes)")


# ==============================================================================
# PDF EXPORT ENGINE
# ==============================================================================

def export_dxf_to_pdf(dxf_path, config=None):
    """
    Renders DXF to print-ready PDF with exact paper-size conformance.
    Project-agnostic: uses config for paper size, margins, and output dir.
    """
    if config:
        pdf_dir = config.pdf_dir
        paper_w_mm = config.paper_w_mm
        paper_h_mm = config.paper_h_mm
        margin_mm = config.margin_mm
    else:
        pdf_dir = Path(__file__).resolve().parent.parent / "CAD-Drawings" / "PDF"
        paper_w_mm, paper_h_mm = 297.0, 210.0
        margin_mm = 20.0

    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / (dxf_path.stem + ".pdf")

    try:
        doc = ezdxf.readfile(str(dxf_path))
    except Exception as e:
        print(f"  [FAIL] Read DXF failed {dxf_path.name}: {e}")
        return pdf_path

    msp = doc.modelspace()

    try:
        ctx = RenderContext(doc)
        render_config = Configuration(
            background_policy=BackgroundPolicy.WHITE,
            color_policy=ColorPolicy.COLOR,
            custom_fg_color="#000000",
            line_policy=LinePolicy.ACCURATE,
        )

        paper_w_in = paper_w_mm / 25.4
        paper_h_in = paper_h_mm / 25.4
        fig = plt.figure(figsize=(paper_w_in, paper_h_in), dpi=300, facecolor="white")

        margin_left = margin_mm / paper_w_mm
        margin_bottom = margin_mm / paper_h_mm
        printable_w = (paper_w_mm - 2 * margin_mm) / paper_w_mm
        printable_h = (paper_h_mm - 2 * margin_mm) / paper_h_mm

        ax = fig.add_axes([margin_left, margin_bottom, printable_w, printable_h])
        ax.set_facecolor("white")
        ax.set_axis_off()

        sw = getattr(doc, "_sheet_w", 150.0 * FT)
        sh = getattr(doc, "_sheet_h", sw * (170.0 / 257.0))
        pad_x, pad_y = sw * 0.01, sh * 0.01
        ax.set_xlim(-pad_x, sw + pad_x)
        ax.set_ylim(-pad_y, sh + pad_y)

        backend = MatplotlibBackend(ax)
        frontend = Frontend(ctx, backend, config=render_config)
        frontend.draw_layout(msp, finalize=True)

        temp_pdf = pdf_dir / f"_temp_{dxf_path.stem}.pdf"
        fig.savefig(str(temp_pdf), format="pdf", facecolor="white", dpi=300, bbox_inches=None)
        plt.close(fig)

        a4_w_pt = paper_w_mm * PT_PER_MM
        a4_h_pt = paper_h_mm * PT_PER_MM
        doc_a4 = pymupdf.open()
        page_a4 = doc_a4.new_page(width=a4_w_pt, height=a4_h_pt)
        src_doc = pymupdf.open(str(temp_pdf))
        page_a4.show_pdf_page(pymupdf.Rect(0, 0, a4_w_pt, a4_h_pt), src_doc, 0)
        doc_a4.save(str(pdf_path))
        doc_a4.close()
        src_doc.close()

        if temp_pdf.exists():
            temp_pdf.unlink()
        if pdf_path.exists():
            sz = pdf_path.stat().st_size
            print(f"  [OK] PDF saved: {pdf_path.name} ({sz:,} bytes)")

    except Exception as e:
        print(f"  [FAIL] PDF export failed {dxf_path.name}: {e}")
        import traceback
        traceback.print_exc()

    return pdf_path


def merge_pdfs(pdf_dir, output_name="merged.pdf", prefix_filter=None):
    """Merge multiple PDF files from a directory into one master document."""
    pdf_dir = Path(pdf_dir)
    merger = PdfWriter()
    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    if prefix_filter:
        pdf_files = [p for p in pdf_files if p.name[:2].isdigit() and not p.name.startswith(prefix_filter)]
    pdf_files.sort(key=lambda x: x.name)

    if not pdf_files:
        print("  [WARN] No PDFs found to merge.")
        return None

    for p in pdf_files:
        try:
            merger.append(str(p))
        except Exception as e:
            print(f"  [FAIL] Could not append {p.name}: {e}")

    master_path = pdf_dir / output_name
    with open(master_path, "wb") as f_out:
        merger.write(f_out)

    sz = master_path.stat().st_size
    print(f"\n  [SUCCESS] Merged PDF: {master_path.name} ({sz:,} bytes, {len(merger.pages)} pages)")
    return master_path


# ==============================================================================
# BACKWARD COMPATIBILITY ALIASES (for existing banswara_chambers.py)
# ==============================================================================

SHEET_W, SHEET_H = sheet_dims()

# Legacy constants used by banswara_chambers.py
PROJECT_TITLE = "ADVOCATE CHAMBERS - BANSWARA DISTRICT COURT, RAJASTHAN"
CLIENT = "BAR ASSOCIATION & DLSA, BANSWARA"
DRAW_DATE = "25 AUG 2026"
DRAW_BY = "TRAE AI ARCHITECTURE STUDIO"
CODE = "NBC 2016 + RPwD ACT 2016 + IS 4912"
DOC_REF = "Banswara-DC-Advocate-Sitout-v2.4"

BASE_DIR = Path(__file__).resolve().parent.parent
DXF_DIR = BASE_DIR / "CAD-Drawings" / "DXF"
PDF_DIR = BASE_DIR / "CAD-Drawings" / "PDF"
DXF_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)

LAYERS = ARCH_LAYERS  # Alias


def export_dxf_to_a4_pdf(dxf_path):
    """Legacy wrapper for banswara_chambers.py compatibility."""
    return export_dxf_to_pdf(dxf_path)


def merge_all_16_pdfs():
    """Legacy wrapper for banswara_chambers.py compatibility."""
    return merge_pdfs(PDF_DIR, "00-Advocate-Chambers-All-16-Drawings-Complete-Set.pdf", "00-")
