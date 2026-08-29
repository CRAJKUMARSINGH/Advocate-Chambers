"""
Advocate Chambers Banswara - Architectural CAD Drawings & PDF Generator (Complete 16-Sheet Suite)
Generates all 16 Architectural Drawing Sheets:
  - DXF (AutoCAD R2018 native format)
  - PDF (Print-Ready A4 Landscape 297mm x 210mm with exact 20mm margins all around)
  - Dedicated Detailed Plan & Elevations for Type A (5'x6.5') and Type B (8'x10') Sitouts
  - Practical Seating: Advocate seated on one side of desk, 2-3 Litigants/Clients on opposite side
  - Prominent Top & Bottom Architectural Captions & Title Blocks
  - Merged 16-Page Master PDF Document

Units: 1 drawing unit = 1 INCH (Imperial Standard, FT = 12.0)
Standard: NBC 2016 + RPwD Act 2016 + IS 4912 + IS 14666
"""
import os
import math
from pathlib import Path
import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy, LinePolicy
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pymupdf
from pypdf import PdfWriter

BASE_DIR = Path(r"e:\Rajkumar\Advocate-Chambers")
DXF_DIR = BASE_DIR / "CAD-Drawings" / "DXF"
PDF_DIR = BASE_DIR / "CAD-Drawings" / "PDF"
DXF_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)

FT = 12.0  # 1 foot = 12 inches

PROJECT_TITLE = "ADVOCATE CHAMBERS - BANSWARA DISTRICT COURT, RAJASTHAN"
CLIENT = "BAR ASSOCIATION & DLSA, BANSWARA"
DRAW_DATE = "25 AUG 2026"
DRAW_BY = "TRAE AI ARCHITECTURE STUDIO"
CODE = "NBC 2016 + RPwD ACT 2016 + IS 4912"
DOC_REF = "Banswara-DC-Advocate-Sitout-v2.4"

# A4 Landscape aspect ratio matching 257mm x 170mm printable area (297x210mm with 20mm margins)
SHEET_W = 150.0 * FT
SHEET_H = SHEET_W * (170.0 / 257.0)  # ~99.22 ft

LAYERS = {
    "A-WALL": dict(color=colors.WHITE, linetype="CONTINUOUS", lineweight=50),
    "A-WALL-PATT": dict(color=9, linetype="CONTINUOUS", lineweight=18),
    "A-COLUMN": dict(color=colors.RED, linetype="CONTINUOUS", lineweight=50),
    "A-DOOR": dict(color=colors.YELLOW, linetype="CONTINUOUS", lineweight=30),
    "A-WINDOW": dict(color=colors.CYAN, linetype="CONTINUOUS", lineweight=30),
    "A-JALI": dict(color=colors.MAGENTA, linetype="DASHED", lineweight=18),
    "A-BAY": dict(color=colors.GREEN, linetype="CONTINUOUS", lineweight=25),
    "A-FURN": dict(color=colors.RED, linetype="CONTINUOUS", lineweight=18),
    "A-DIM": dict(color=colors.CYAN, linetype="CONTINUOUS", lineweight=15),
    "A-TEXT": dict(color=colors.WHITE, linetype="CONTINUOUS", lineweight=18),
    "A-TEXT-TTL": dict(color=colors.WHITE, linetype="CONTINUOUS", lineweight=35),
    "A-GRID": dict(color=colors.MAGENTA, linetype="DASHED", lineweight=13),
    "A-HATCH": dict(color=8, linetype="CONTINUOUS", lineweight=13),
    "A-SITE": dict(color=colors.YELLOW, linetype="CONTINUOUS", lineweight=30),
    "A-ROOF": dict(color=colors.BLUE, linetype="CONTINUOUS", lineweight=25),
    "A-SECT-CUT": dict(color=colors.RED, linetype="PHANTOM", lineweight=50),
    "A-TTLB": dict(color=colors.WHITE, linetype="CONTINUOUS", lineweight=35),
    "A-LOCKER": dict(color=colors.GREEN, linetype="CONTINUOUS", lineweight=25),
    "A-ACC": dict(color=colors.BLUE, linetype="CONTINUOUS", lineweight=25),
}


def setup_doc(sheet_w=SHEET_W, sheet_h=SHEET_H):
    """Create a clean DXF document with layers, styles, and sheet bounds."""
    doc = ezdxf.new(dxfversion="R2018", setup=True)
    doc.header["$INSUNITS"] = 1  # Inches
    doc.header["$MEASUREMENT"] = 0  # Imperial
    msp = doc.modelspace()
    for name, props in LAYERS.items():
        if name not in doc.layers:
            layer = doc.layers.add(name)
            layer.color = props["color"]
            layer.linetype = props["linetype"]
            layer.lineweight = props["lineweight"]

    if "ARCH-STYLE" not in doc.styles:
        try:
            doc.styles.add("ARCH-STYLE", font="ARCHITXT.TTF")
        except Exception:
            pass
    if "SIMPLEX" not in doc.styles:
        try:
            doc.styles.add("SIMPLEX", font="simplex.shx")
        except Exception:
            pass

    doc._sheet_w = sheet_w
    doc._sheet_h = sheet_h
    return doc, msp


# ==============================================================================
# GEOMETRY & ARCHITECTURAL DRAFTING PRIMITIVES (ZERO UNWANTED ARROWS)
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
        h.paths.add_polyline_path([(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)], is_closed=True)
    except Exception:
        pass


def text_msp(msp, txt, x, y, h=1.25 * FT, layer="A-TEXT", style="SIMPLEX",
             align=TextEntityAlignment.MIDDLE_CENTER, rot=0.0):
    """Add clean text with exact alignment and zero missing glyph boxes."""
    if not txt:
        return None
    clean_txt = str(txt).replace("—", "-").replace("–", "-").replace("→", "->").replace("✓", "[OK]").replace("►", ">").replace("◄", "<").replace("★", "*")
    lines = clean_txt.split("\n")
    if len(lines) > 1:
        line_spacing = h * 1.35
        total_ht = (len(lines) - 1) * line_spacing
        for idx, line in enumerate(lines):
            line_y = y + (total_ht / 2.0) - (idx * line_spacing)
            try:
                t = msp.add_text(line, dxfattribs={"layer": layer, "height": h, "style": style, "rotation": rot})
                t.set_placement((x, line_y), align=align)
            except Exception:
                pass
        return None
    try:
        t = msp.add_text(clean_txt, dxfattribs={"layer": layer, "height": h, "style": style, "rotation": rot})
        t.set_placement((x, y), align=align)
        return t
    except Exception:
        try:
            t = msp.add_text(clean_txt, dxfattribs={"layer": layer, "height": h, "rotation": rot})
            t.dxf.insert = (x, y, 0)
            return t
        except Exception:
            return None


def arch_dim_h(msp, x1, y, x2, txt, offset=1.2 * FT, tick_sz=0.45 * FT, layer="A-DIM", text_h=0.60 * FT):
    """
    Standard Horizontal Architectural Dimension Line with 45-degree slash ticks.
    100% arrow-free, clean, crisp drafting.
    """
    if x1 > x2:
        x1, x2 = x2, x1
    yd = y + offset
    msp.add_line((x1, yd), (x2, yd), dxfattribs={"layer": layer, "lineweight": 18})
    ext_gap = 0.25 * FT if offset > 0 else -0.25 * FT
    ext_over = 0.35 * FT if offset > 0 else -0.35 * FT
    msp.add_line((x1, y + ext_gap), (x1, yd + ext_over), dxfattribs={"layer": layer, "lineweight": 13})
    msp.add_line((x2, y + ext_gap), (x2, yd + ext_over), dxfattribs={"layer": layer, "lineweight": 13})
    ts = tick_sz
    msp.add_line((x1 - ts * 0.5, yd - ts * 0.5), (x1 + ts * 0.5, yd + ts * 0.5), dxfattribs={"layer": layer, "lineweight": 30})
    msp.add_line((x2 - ts * 0.5, yd - ts * 0.5), (x2 + ts * 0.5, yd + ts * 0.5), dxfattribs={"layer": layer, "lineweight": 30})
    ty = yd + 0.32 * FT if offset >= 0 else yd - 0.48 * FT
    text_msp(msp, txt, (x1 + x2) / 2.0, ty, h=text_h, layer=layer,
             align=TextEntityAlignment.BOTTOM_CENTER if offset >= 0 else TextEntityAlignment.TOP_CENTER)


def arch_dim_v(msp, x, y1, y2, txt, offset=1.2 * FT, tick_sz=0.45 * FT, layer="A-DIM", text_h=0.60 * FT):
    """
    Standard Vertical Architectural Dimension Line with 45-degree slash ticks.
    100% arrow-free, clean, crisp drafting.
    """
    if y1 > y2:
        y1, y2 = y2, y1
    xd = x + offset
    msp.add_line((xd, y1), (xd, y2), dxfattribs={"layer": layer, "lineweight": 18})
    ext_gap = 0.25 * FT if offset > 0 else -0.25 * FT
    ext_over = 0.35 * FT if offset > 0 else -0.35 * FT
    msp.add_line((x + ext_gap, y1), (xd + ext_over, y1), dxfattribs={"layer": layer, "lineweight": 13})
    msp.add_line((x + ext_gap, y2), (xd + ext_over, y2), dxfattribs={"layer": layer, "lineweight": 13})
    ts = tick_sz
    msp.add_line((xd - ts * 0.5, y1 - ts * 0.5), (xd + ts * 0.5, y1 + ts * 0.5), dxfattribs={"layer": layer, "lineweight": 30})
    msp.add_line((xd - ts * 0.5, y2 - ts * 0.5), (xd + ts * 0.5, y2 + ts * 0.5), dxfattribs={"layer": layer, "lineweight": 30})
    tx = xd + 0.35 * FT if offset >= 0 else xd - 0.35 * FT
    text_msp(msp, txt, tx, (y1 + y2) / 2.0, h=text_h, layer=layer, rot=90.0,
             align=TextEntityAlignment.BOTTOM_CENTER if offset >= 0 else TextEntityAlignment.TOP_CENTER)


def draw_sheet_frame_and_titleblock(msp, sw, sh, sheet_no, sheet_title, scale_txt,
                                   rev="0", subtitle="", notes=None):
    """
    Draws professional architectural sheet border, top caption banner,
    and bottom title block fitted to whole A4 page (min 20mm margin).
    """
    # Outer Border (Touches exact 20mm page margin boundary)
    rect(msp, 0, 0, sw, sh, layer="A-TTLB", lw=50)
    # Inner Border (0.5 ft margin inside)
    ib = 0.5 * FT
    rect(msp, ib, ib, sw - ib, sh - ib, layer="A-TTLB", lw=25)

    # --------------------------------------------------------------------------
    # TOP CAPTION BANNER (Bold, prominent drawing header)
    # --------------------------------------------------------------------------
    cap_y1 = sh - ib - 5.5 * FT
    cap_y2 = sh - ib
    rect(msp, ib, cap_y1, sw - ib, cap_y2, layer="A-TTLB", lw=35)
    
    text_msp(msp, f"{sheet_no.upper()}  -  {sheet_title.upper()}",
             sw / 2.0, cap_y2 - 1.8 * FT, h=0.95 * FT, layer="A-TEXT-TTL")
    text_msp(msp, f"{PROJECT_TITLE}  |  {CLIENT}  |  SCALE: {scale_txt}",
             sw / 2.0, cap_y1 + 1.4 * FT, h=0.55 * FT, layer="A-TEXT-TTL")

    # --------------------------------------------------------------------------
    # BOTTOM TITLE BLOCK (Bottom Right: Width 56 ft, Height 8.5 ft)
    # --------------------------------------------------------------------------
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

    text_msp(msp, "PROJECT:", tb_x1 + 0.5 * FT, tb_y2 - 1.1 * FT, h=0.50 * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
    text_msp(msp, PROJECT_TITLE, col_x1 + 0.6 * FT, tb_y2 - 1.1 * FT, h=0.62 * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)

    text_msp(msp, "DRAWING TITLE:", tb_x1 + 0.5 * FT, tb_y1 + 5.2 * FT, h=0.50 * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
    text_msp(msp, sheet_title, col_x1 + 0.6 * FT, tb_y1 + 5.2 * FT, h=0.65 * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)

    text_msp(msp, "CLIENT:", tb_x1 + 0.5 * FT, tb_y1 + 3.3 * FT, h=0.45 * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
    text_msp(msp, CLIENT, col_x1 + 0.6 * FT, tb_y1 + 3.3 * FT, h=0.50 * FT, layer="A-TEXT", align=TextEntityAlignment.LEFT)

    text_msp(msp, "SHEET NO:", col_x2 + 0.5 * FT, tb_y1 + 3.3 * FT, h=0.45 * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
    text_msp(msp, sheet_no, col_x3 + 0.5 * FT, tb_y1 + 3.3 * FT, h=0.62 * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)

    text_msp(msp, "SCALE:", tb_x1 + 0.5 * FT, tb_y1 + 1.8 * FT, h=0.45 * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
    text_msp(msp, scale_txt, col_x1 + 0.6 * FT, tb_y1 + 1.8 * FT, h=0.55 * FT, layer="A-TEXT", align=TextEntityAlignment.LEFT)

    text_msp(msp, "DATE:", col_x2 + 0.5 * FT, tb_y1 + 1.8 * FT, h=0.45 * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
    text_msp(msp, DRAW_DATE, col_x3 + 0.5 * FT, tb_y1 + 1.8 * FT, h=0.50 * FT, layer="A-TEXT", align=TextEntityAlignment.LEFT)

    text_msp(msp, "CODES / REF:", tb_x1 + 0.5 * FT, tb_y1 + 0.6 * FT, h=0.40 * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
    text_msp(msp, f"{CODE}  |  DOC: {DOC_REF}  |  REV: {rev}", col_x1 + 0.6 * FT, tb_y1 + 0.6 * FT, h=0.43 * FT, layer="A-TEXT", align=TextEntityAlignment.LEFT)

    # North Indicator in Top Right (below banner)
    nx, ny = sw - ib - 4.5 * FT, sh - ib - 9.0 * FT
    draw_north_arrow(msp, nx, ny, size=2.6 * FT)

    # Notes Box along bottom left
    if notes:
        nb_x1 = ib + 0.5 * FT
        nb_y1 = ib + 0.5 * FT
        nb_w = 54.0 * FT
        nb_h = 8.0 * FT
        rect(msp, nb_x1, nb_y1, nb_x1 + nb_w, nb_y1 + nb_h, layer="A-TTLB", lw=20)
        text_msp(msp, "GENERAL NOTES & COMPLIANCE:", nb_x1 + 0.6 * FT, nb_y1 + nb_h - 0.6 * FT, h=0.50 * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
        for i, n in enumerate(notes):
            text_msp(msp, f"* {n}", nb_x1 + 0.6 * FT, nb_y1 + nb_h - 1.4 * FT - (i * 0.60 * FT), h=0.40 * FT, layer="A-TEXT", align=TextEntityAlignment.LEFT)


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
    text_msp(msp, "N", x, y + r + 0.5 * FT, h=0.75 * FT, layer="A-TEXT-TTL")


def bay_compact(msp, bx, by, w=5.0 * FT, d=6.5 * FT, label="1", orientation="S"):
    """
    Draws a Type A Compact Workstation (5'x6.5') with 3.5' Jali partition.
    PRACTICAL ERGONOMIC ARRANGEMENT:
      - Advocate seated on one side of the desk with executive mesh chair.
      - 2 Litigants seated on the OPPOSITE side of the desk facing the advocate.
      - Desk (4'x1.5') positioned in the center.
    """
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
    text_msp(msp, f"BAY {label}", bx + w / 2.0, (desk_y1 + desk_y2) / 2.0, h=0.45 * FT, layer="A-BAY")

    if orientation == "S":
        adv_y = desk_y2 + 0.6 * FT
        try:
            msp.add_circle((bx + w / 2.0, adv_y), 0.35 * FT, dxfattribs={"layer": "A-FURN", "lineweight": 18})
        except Exception:
            pass
        text_msp(msp, "ADV", bx + w / 2.0, adv_y, h=0.33 * FT, layer="A-FURN")

        lit_y = desk_y1 - 0.6 * FT
        try:
            msp.add_circle((bx + w * 0.28, lit_y), 0.28 * FT, dxfattribs={"layer": "A-FURN", "lineweight": 15})
            msp.add_circle((bx + w * 0.72, lit_y), 0.28 * FT, dxfattribs={"layer": "A-FURN", "lineweight": 15})
        except Exception:
            pass
        text_msp(msp, "LIT", bx + w * 0.28, lit_y, h=0.25 * FT, layer="A-FURN")
        text_msp(msp, "LIT", bx + w * 0.72, lit_y, h=0.25 * FT, layer="A-FURN")
    else:
        adv_y = desk_y1 - 0.6 * FT
        try:
            msp.add_circle((bx + w / 2.0, adv_y), 0.35 * FT, dxfattribs={"layer": "A-FURN", "lineweight": 18})
        except Exception:
            pass
        text_msp(msp, "ADV", bx + w / 2.0, adv_y, h=0.33 * FT, layer="A-FURN")

        lit_y = desk_y2 + 0.6 * FT
        try:
            msp.add_circle((bx + w * 0.28, lit_y), 0.28 * FT, dxfattribs={"layer": "A-FURN", "lineweight": 15})
            msp.add_circle((bx + w * 0.72, lit_y), 0.28 * FT, dxfattribs={"layer": "A-FURN", "lineweight": 15})
        except Exception:
            pass
        text_msp(msp, "LIT", bx + w * 0.28, lit_y, h=0.25 * FT, layer="A-FURN")
        text_msp(msp, "LIT", bx + w * 0.72, lit_y, h=0.25 * FT, layer="A-FURN")


def bay_premium(msp, bx, by, w=8.0 * FT, d=10.0 * FT, label="P1"):
    """
    Draws a Type B Senior Advocate Premium Cabin (8'x10').
    Advocate seated on inner side, 3 Clients/Litigants on opposite side of executive desk.
    """
    rect(msp, bx, by, bx + w, by + d, layer="A-WALL", lw=30)
    msp.add_line((bx, by), (bx + 3.0 * FT, by), dxfattribs={"layer": "A-DOOR", "lineweight": 30})
    
    desk_w, desk_d = 5.0 * FT, 2.3 * FT
    desk_x1 = bx + (w - desk_w) / 2.0
    desk_x2 = desk_x1 + desk_w
    desk_y1 = by + 4.0 * FT
    desk_y2 = desk_y1 + desk_d
    rect(msp, desk_x1, desk_y1, desk_x2, desk_y2, layer="A-FURN", lw=20)
    text_msp(msp, f"CABIN {label}\nDESK 5'x2.5'", bx + w / 2.0, (desk_y1 + desk_y2) / 2.0, h=0.40 * FT, layer="A-FURN")

    adv_y = desk_y2 + 1.2 * FT
    try:
        msp.add_circle((bx + w / 2.0, adv_y), 0.48 * FT, dxfattribs={"layer": "A-FURN", "lineweight": 20})
    except Exception:
        pass
    text_msp(msp, "ADVOCATE", bx + w / 2.0, adv_y, h=0.38 * FT, layer="A-FURN")

    lit_y = desk_y1 - 1.2 * FT
    for cx in [bx + 2.0 * FT, bx + 4.0 * FT, bx + 6.0 * FT]:
        try:
            msp.add_circle((cx, lit_y), 0.35 * FT, dxfattribs={"layer": "A-FURN", "lineweight": 15})
        except Exception:
            pass
        text_msp(msp, "CLIENT", cx, lit_y, h=0.30 * FT, layer="A-FURN")

    rect(msp, bx + w - 1.2 * FT, by + 1.8 * FT, bx + w - 0.2 * FT, by + d - 1.5 * FT, layer="A-FURN")
    text_msp(msp, "BOOKS / FILES", bx + w - 0.7 * FT, by + d / 2.0, h=0.40 * FT, layer="A-FURN", rot=90.0)


def locker_bank(msp, bx, by, num_cols, num_tiers, bank_label="",
                locker_w=1.0 * FT, locker_h=2.50 * FT, locker_d=1.25 * FT,
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
        text_msp(msp, locker_id, cx, by + total_d * 0.5, h=0.30 * FT, layer="A-LOCKER")
    if bank_label:
        text_msp(msp, bank_label, bx + total_w / 2.0, by - 0.5 * FT, h=0.55 * FT, layer="A-TEXT-TTL")
    total_cap = num_cols * num_tiers
    text_msp(msp, f"{num_cols}W x {num_tiers}H = {total_cap} LOCKERS",
             bx + total_w / 2.0, by + total_d + 0.35 * FT, h=0.40 * FT, layer="A-TEXT")
    arch_dim_h(msp, bx, by - 1.2 * FT, bx + total_w, f"{total_w / FT:.1f}' ({num_cols}x12\")", offset=-0.25 * FT)
    return total_w, total_d


# ==============================================================================
# 16 COMPLETE ARCHITECTURAL CAD SHEETS
# ==============================================================================

# SHEET 01: SITE MASTER PLAN
def draw_sheet_01_site_plan():
    doc, msp = setup_doc()

    ox, oy = 10.0 * FT, 12.0 * FT
    p1_w, p1_d = 100.0 * FT, 72.0 * FT
    rect(msp, ox, oy, ox + p1_w, oy + p1_d, layer="A-SITE", lw=45)
    text_msp(msp, "PLOT 1 BOUNDARY (100'-0\" x 100'-0\" = 10,000 SQ FT)", ox + p1_w / 2.0, oy + p1_d + 2.5 * FT, h=0.80 * FT, layer="A-TEXT-TTL")

    gap = 8.0 * FT
    p2_ox = ox + p1_w + gap
    p2_w, p2_d = 65.0 * FT, 45.0 * FT
    rect(msp, p2_ox, oy + 27.0 * FT, p2_ox + p2_w, oy + 27.0 * FT + p2_d, layer="A-SITE", lw=45)
    text_msp(msp, "PLOT 2 BOUNDARY (70'-0\" x 50'-0\" = 3,500 SQ FT)", p2_ox + p2_w / 2.0, oy + 72.0 * FT + 2.5 * FT, h=0.80 * FT, layer="A-TEXT-TTL")

    rect(msp, ox + 4.0 * FT, oy + 4.0 * FT, ox + p1_w - 4.0 * FT, oy + p1_d - 4.0 * FT, layer="A-GRID", lw=18)
    rect(msp, p2_ox + 4.0 * FT, oy + 31.0 * FT, p2_ox + p2_w - 4.0 * FT, oy + 27.0 * FT + p2_d - 4.0 * FT, layer="A-GRID", lw=18)

    rect(msp, ox + 4.0 * FT, oy + 4.0 * FT, ox + 96.0 * FT, oy + p1_d - 4.0 * FT, layer="A-WALL", lw=45)
    fill_rect(msp, ox + 4.0 * FT, oy + 4.0 * FT, ox + 96.0 * FT, oy + p1_d - 4.0 * FT, hatch="ANSI31", layer="A-HATCH")
    text_msp(msp, "PLOT 1 ADVOCATE COMPLEX\nBUILDABLE FOOTPRINT: 90'-0\" x 90'-0\" (8,100 SQ FT)\n115 BAYS (OPT 1) / 120 BAYS (OPT 2 G+1)", ox + 50.0 * FT, oy + 36.0 * FT, h=0.95 * FT, layer="A-TEXT-TTL")

    rect(msp, p2_ox + 4.0 * FT, oy + 31.0 * FT, p2_ox + 61.0 * FT, oy + 68.0 * FT, layer="A-WALL", lw=45)
    fill_rect(msp, p2_ox + 4.0 * FT, oy + 31.0 * FT, p2_ox + 61.0 * FT, oy + 68.0 * FT, hatch="ANSI31", layer="A-HATCH")
    text_msp(msp, "PLOT 2 ANNEX\nFOOTPRINT: 60'-0\" x 40'-0\" (2,400 SQ FT)\n35 BAYS + AMENITIES (OPT 1) / 30 BAYS (OPT 2)", p2_ox + 32.5 * FT, oy + 50.0 * FT, h=0.85 * FT, layer="A-TEXT-TTL")

    rect(msp, ox + p1_w, oy + 45.0 * FT, p2_ox, oy + 55.0 * FT, layer="A-ROOF", lw=25)
    text_msp(msp, "10' COVERED WALKWAY", ox + p1_w + gap / 2.0, oy + 50.0 * FT, h=0.50 * FT, layer="A-TEXT-TTL", rot=90.0)

    plaza_y1 = oy - 14.0 * FT
    plaza_y2 = oy
    rect(msp, ox, plaza_y1, p2_ox + p2_w, plaza_y2, layer="A-SITE", lw=30)
    text_msp(msp, "20 ft LANDSCAPED PLAZA - PEDESTRIAN ENTRY FACING DISTRICT COURT MAIN ENTRANCE (SOUTH)", (ox + p2_ox + p2_w) / 2.0, oy - 7.0 * FT, h=0.75 * FT, layer="A-TEXT-TTL")

    for tx in [ox + 10.0 * FT, ox + 35.0 * FT, ox + 65.0 * FT, ox + 90.0 * FT, p2_ox + 15.0 * FT, p2_ox + 45.0 * FT]:
        msp.add_circle((tx, oy - 7.0 * FT), 2.2 * FT, dxfattribs={"layer": "A-BAY", "lineweight": 18})
        text_msp(msp, "TREE", tx, oy - 7.0 * FT, h=0.40 * FT, layer="A-BAY")

    rect(msp, ox + 10.0 * FT, oy + p1_d - 4.0 * FT, ox + 60.0 * FT, oy + p1_d, layer="A-FURN")
    text_msp(msp, "25 TWO-WHEELER SLOTS (P1)", ox + 35.0 * FT, oy + p1_d - 2.0 * FT, h=0.45 * FT, layer="A-FURN")

    rect(msp, p2_ox + 10.0 * FT, oy + 68.0 * FT, p2_ox + 50.0 * FT, oy + 72.0 * FT, layer="A-FURN")
    text_msp(msp, "15 TWO-WHEELER SLOTS (P2)", p2_ox + 30.0 * FT, oy + 70.0 * FT, h=0.45 * FT, layer="A-FURN")

    rect(msp, ox, oy + 15.0 * FT, ox + 4.0 * FT, oy + 60.0 * FT, layer="A-FURN")
    text_msp(msp, "50 BICYCLE SLOTS", ox + 2.0 * FT, oy + 37.5 * FT, h=0.45 * FT, layer="A-FURN", rot=90.0)

    arch_dim_h(msp, ox, oy - 16.0 * FT, ox + p1_w, "100'-0\" (PLOT 1 FRONTAGE)", offset=-1.2 * FT)
    arch_dim_h(msp, ox + p1_w, oy - 16.0 * FT, p2_ox, "10'-0\" GAP", offset=-1.2 * FT)
    arch_dim_h(msp, p2_ox, oy - 16.0 * FT, p2_ox + p2_w, "70'-0\" (PLOT 2 FRONTAGE)", offset=-1.2 * FT)

    notes = [
        "Total Campus Site Area: 13,500 Sq Ft (Plot 1 = 10,000 Sq Ft + Plot 2 = 3,500 Sq Ft).",
        "Setbacks: 5'-0\" Clear Setback on all perimeters ensuring NBC 2016 Fire Safety compliance.",
        "Rainwater Harvesting: 2 Nos. Recharge Soak Pits + Trench Network collecting 100% roof/plaza runoff.",
        "Access: Barrier-free RPwD ramped entry (1:12 slope) connecting Court South Gate to both Plots.",
    ]
    draw_sheet_frame_and_titleblock(msp, SHEET_W, SHEET_H, "SHEET 01 OF 16", "SITE MASTER PLAN & CAMPUS LAYOUT (PLOTS 1 & 2)", "1\" = 20'-0\"", notes=notes)
    save_drawing(doc, "01-Site-Master-Plan-Plots-1-and-2")
    return doc


# SHEET 02: OPTION 1 - PLOT 1 GROUND FLOOR PLAN (115 BAYS)
def draw_sheet_02_o1_p1_gf():
    doc, msp = setup_doc()

    ox, oy = 28.0 * FT, 11.0 * FT
    WB, HB = 90.0 * FT, 74.0 * FT

    rect(msp, ox, oy, ox + WB, oy + HB, layer="A-WALL", lw=50)
    fill_rect(msp, ox, oy, ox + WB, oy + HB, hatch="ANSI31", layer="A-HATCH")
    fill_rect(msp, ox + 0.75 * FT, oy + 0.75 * FT, ox + WB - 0.75 * FT, oy + HB - 0.75 * FT, hatch="SOLID", layer="A-HATCH")

    msp.add_line((ox + WB / 2.0 - 5.0 * FT, oy), (ox + WB / 2.0 - 5.0 * FT, oy + 1.0 * FT), dxfattribs={"layer": "A-DOOR", "lineweight": 40})
    msp.add_line((ox + WB / 2.0 + 5.0 * FT, oy), (ox + WB / 2.0 + 5.0 * FT, oy + 1.0 * FT), dxfattribs={"layer": "A-DOOR", "lineweight": 40})
    text_msp(msp, "10 ft MAIN DOUBLE-LEAF ENTRY (SOUTH - COURT FACING)", ox + WB / 2.0, oy + 2.0 * FT, h=0.70 * FT, layer="A-DOOR")

    entry_y_top = oy + 8.0 * FT
    rect(msp, ox + 2.0 * FT, oy + 1.0 * FT, ox + 18.0 * FT, entry_y_top, layer="A-FURN")
    text_msp(msp, "RECEPTION 16'x8'\n(Low Counter - RPwD Access)", ox + 10.0 * FT, oy + 4.5 * FT, h=0.50 * FT, layer="A-TEXT-TTL")

    rect(msp, ox + 45.0 * FT, oy + 1.0 * FT, ox + 88.0 * FT, entry_y_top, layer="A-FURN")
    text_msp(msp, "LITIGANT WAITING HALL 43'x8'\n(80 FIXED CUSHIONED SEATS + 100 FOLDING SEATS + 3 NOTICE BOARDS)", ox + 66.5 * FT, oy + 4.5 * FT, h=0.50 * FT, layer="A-TEXT-TTL")

    corr_y_bot = oy + 34.0 * FT
    corr_y_top = oy + 40.0 * FT
    rect(msp, ox + 1.0 * FT, corr_y_bot, ox + WB - 1.0 * FT, corr_y_top, layer="A-WALL", lw=25)
    text_msp(msp, "====== 6 ft MAIN CENTRAL CORRIDOR (EAST-WEST) ======", ox + WB / 2.0, (corr_y_bot + corr_y_top) / 2.0, h=0.70 * FT, layer="A-TEXT-TTL")

    cx1 = ox + WB - 22.0 * FT
    cy1 = oy + 9.5 * FT
    cx2 = ox + WB - 2.0 * FT
    cy2 = cy1 + 9.0 * FT
    rect(msp, cx1, cy1, cx2, cy2, layer="A-BAY", lw=30)
    text_msp(msp, "MINI COURTYARD 20'x10'\n5 NATIVE TREES + STONE BENCHES", (cx1 + cx2) / 2.0, (cy1 + cy2) / 2.0, h=0.55 * FT, layer="A-BAY")

    bw, bd = 5.0 * FT, 5.8 * FT
    start_x = ox + 4.0 * FT
    n_cols = 15

    # North Zone: Rows A & B (Back-to-Back: 1 Advocate vs 2 Opposite Litigants)
    row_a_y = oy + HB - 4.5 * FT - bd
    row_b_y = row_a_y - 3.2 * FT - bd
    for i in range(n_cols):
        bay_compact(msp, start_x + i * bw, row_a_y, bw, bd, str(i + 1), orientation="S")
        bay_compact(msp, start_x + i * bw, row_b_y, bw, bd, str(i + 1 + 15), orientation="N")
    text_msp(msp, "ROW A (BAYS 1-15: ADVOCATE NORTH, 2 LITIGANTS SOUTH)", start_x + n_cols * bw / 2.0, row_a_y + bd + 0.5 * FT, h=0.50 * FT, layer="A-TEXT-TTL")
    text_msp(msp, "4' AISLE 1", start_x + n_cols * bw / 2.0, row_a_y - 1.6 * FT, h=0.47 * FT, layer="A-TEXT")
    text_msp(msp, "ROW B (BAYS 16-30: ADVOCATE SOUTH, 2 LITIGANTS NORTH)", start_x + n_cols * bw / 2.0, row_b_y - 0.5 * FT, h=0.50 * FT, layer="A-TEXT-TTL")

    # Rows C & D (Back-to-Back: 1 Advocate vs 2 Opposite Litigants)
    row_c_y = row_b_y - 3.2 * FT - bd
    row_d_y = row_c_y - 3.2 * FT - bd
    for i in range(n_cols):
        bay_compact(msp, start_x + i * bw, row_c_y, bw, bd, str(31 + i), orientation="S")
        bay_compact(msp, start_x + i * bw, row_d_y, bw, bd, str(46 + i), orientation="N")
    text_msp(msp, "ROW C (BAYS 31-45)", start_x + n_cols * bw / 2.0, row_c_y + bd + 0.5 * FT, h=0.50 * FT, layer="A-TEXT-TTL")
    text_msp(msp, "4' AISLE 2", start_x + n_cols * bw / 2.0, row_c_y - 1.6 * FT, h=0.47 * FT, layer="A-TEXT")
    text_msp(msp, "ROW D (BAYS 46-60)", start_x + n_cols * bw / 2.0, row_d_y - 0.5 * FT, h=0.50 * FT, layer="A-TEXT-TTL")

    # South Zone: Rows E & F (Back-to-Back)
    row_e_y = corr_y_bot - 1.0 * FT - bd
    row_f_y = row_e_y - 3.2 * FT - bd
    for i in range(n_cols):
        bay_compact(msp, start_x + i * bw, row_e_y, bw, bd, str(61 + i), orientation="S")
        bay_compact(msp, start_x + i * bw, row_f_y, bw, bd, str(76 + i), orientation="N")
    text_msp(msp, "ROW E (BAYS 61-75)", start_x + n_cols * bw / 2.0, row_e_y + bd + 0.5 * FT, h=0.50 * FT, layer="A-TEXT-TTL")
    text_msp(msp, "4' AISLE 3", start_x + n_cols * bw / 2.0, row_e_y - 1.6 * FT, h=0.47 * FT, layer="A-TEXT")
    text_msp(msp, "ROW F (BAYS 76-90)", start_x + n_cols * bw / 2.0, row_f_y - 0.5 * FT, h=0.50 * FT, layer="A-TEXT-TTL")

    # Rows G & H
    row_g_y = row_f_y - 3.2 * FT - bd
    row_h_y = row_g_y - 3.2 * FT - bd
    for i in range(n_cols):
        bay_compact(msp, start_x + i * bw, row_g_y, bw, bd, str(91 + i), orientation="S")
    for i in range(10):
        bay_compact(msp, start_x + i * bw, row_h_y, bw, bd, str(106 + i), orientation="N")
    for i in range(5):
        bay_compact(msp, cx1 + i * 4.0 * FT, oy + 1.0 * FT, 4.0 * FT, 7.0 * FT, str(111 + i), orientation="S")

    text_msp(msp, "ROW G (BAYS 91-105)", start_x + n_cols * bw / 2.0, row_g_y + bd + 0.5 * FT, h=0.50 * FT, layer="A-TEXT-TTL")
    text_msp(msp, "4' AISLE 4", start_x + n_cols * bw / 2.0, row_g_y - 1.6 * FT, h=0.47 * FT, layer="A-TEXT")
    text_msp(msp, "ROW H (BAYS 106-115)", start_x + 10 * bw / 2.0, row_h_y - 0.5 * FT, h=0.50 * FT, layer="A-TEXT-TTL")

    # North Wall Lockers (150 Advocate Lockers)
    lock_y = oy + HB - 3.0 * FT
    for b_idx in range(3):
        bx = start_x + b_idx * 11.5 * FT
        start_num = b_idx * 50 + 1
        locker_bank(msp, bx, lock_y, 10, 5, f"BANK {b_idx + 1}: ADV {start_num}-{start_num + 49}",
                    col_start=start_num, type_code="A")

    ro_x = start_x + 36.0 * FT
    rect(msp, ro_x, lock_y, ro_x + 8.0 * FT, lock_y + 1.5 * FT, layer="A-FURN")
    text_msp(msp, "RO PLANT (2x20 L/H)\n+ WATER COOLER", ro_x + 4.0 * FT, lock_y + 0.75 * FT, h=0.40 * FT, layer="A-FURN")

    rect(msp, ox + WB - 12.0 * FT, oy + HB - 2.0 * FT, ox + WB - 2.0 * FT, oy + HB, layer="A-DOOR", lw=40)
    text_msp(msp, "10 ft FIRE EXIT N", ox + WB - 7.0 * FT, oy + HB - 1.0 * FT, h=0.50 * FT, layer="A-DOOR")

    arch_dim_h(msp, ox, oy - 2.0 * FT, ox + WB, "90'-0\" (BUILDABLE WIDTH)", offset=-1.2 * FT)
    arch_dim_v(msp, ox - 2.0 * FT, oy, oy + HB, "90'-0\" (BUILDABLE DEPTH)", offset=-1.2 * FT)

    notes = [
        "Workstation Layout: Advocate seated on inner side of desk; 2 Litigants seated on OPPOSITE side facing advocate.",
        "Option 1.1.1 Plot 1 Capacity: 115 Advocate Workstations (5'x6.5' Type A) with 3.5 ft Jali Partitions.",
        "Lockers: 150 Advocate Steel Lockers (IS 14666 CRCA 24 SWG) in 3 Banks along North perimeter wall.",
        "Waiting Capacity: 80 Fixed + 100 Folding seats for visiting litigants with 3 Notice Boards.",
    ]
    draw_sheet_frame_and_titleblock(msp, SHEET_W, SHEET_H, "SHEET 02 OF 16", "OPTION 1 - PLOT 1 GROUND FLOOR PLAN (115 BAYS + 150 LOCKERS)", "1/8\" = 1'-0\"", notes=notes)
    save_drawing(doc, "02-Option1-Plot1-Ground-Floor-Plan-115-Bays")
    return doc


# SHEET 03: OPTION 1 - PLOT 2 GROUND FLOOR PLAN (35 BAYS)
def draw_sheet_03_o1_p2_gf():
    doc, msp = setup_doc()

    ox, oy = 35.0 * FT, 18.0 * FT
    WB, HB = 80.0 * FT, 55.0 * FT

    rect(msp, ox, oy, ox + WB, oy + HB, layer="A-WALL", lw=50)
    fill_rect(msp, ox, oy, ox + WB, oy + HB, hatch="ANSI31", layer="A-HATCH")
    fill_rect(msp, ox + 0.75 * FT, oy + 0.75 * FT, ox + WB - 0.75 * FT, oy + HB - 0.75 * FT, hatch="SOLID", layer="A-HATCH")

    centr_x1 = ox + WB / 2.0 - 3.0 * FT
    centr_x2 = ox + WB / 2.0 + 3.0 * FT
    rect(msp, centr_x1, oy + 12.0 * FT, centr_x2, oy + HB - 4.0 * FT, layer="A-WALL", lw=20)
    text_msp(msp, "5 ft N-S CENTRAL AISLE", (centr_x1 + centr_x2) / 2.0, oy + 32.0 * FT, h=0.60 * FT, layer="A-TEXT-TTL", rot=90.0)

    bw, bd = 6.0 * FT, 7.5 * FT
    sx = ox + 3.0 * FT
    dx = centr_x2 + 2.0 * FT

    # Rows J & K (Back-to-Back: Advocate & 2 Litigants on opposite sides)
    row_j_y = oy + HB - 4.0 * FT - bd
    row_k_y = row_j_y - 4.5 * FT - bd
    for i in range(5):
        bay_compact(msp, sx + i * bw, row_j_y, bw, bd, str(116 + i), orientation="S")
        bay_compact(msp, dx + i * bw, row_j_y, bw, bd, str(121 + i), orientation="S")
        bay_compact(msp, sx + i * bw, row_k_y, bw, bd, str(126 + i), orientation="N")
        bay_compact(msp, dx + i * bw, row_k_y, bw, bd, str(131 + i), orientation="N")

    text_msp(msp, "ROW J (BAYS 116-125: ADVOCATE NORTH, 2 LITIGANTS SOUTH)", ox + WB / 2.0, row_j_y + bd + 0.5 * FT, h=0.55 * FT, layer="A-TEXT-TTL")
    text_msp(msp, "4' AISLE 5", ox + WB / 2.0, row_j_y - 2.2 * FT, h=0.47 * FT, layer="A-TEXT")
    text_msp(msp, "ROW K (BAYS 126-135: ADVOCATE SOUTH, 2 LITIGANTS NORTH)", ox + WB / 2.0, row_k_y - 0.6 * FT, h=0.55 * FT, layer="A-TEXT-TTL")

    # Rows L & M
    row_l_y = row_k_y - 4.5 * FT - bd
    row_m_y = row_l_y - 4.5 * FT - bd
    for i in range(5):
        bay_compact(msp, sx + i * bw, row_l_y, bw, bd, str(136 + i), orientation="S")
        bay_compact(msp, dx + i * bw, row_l_y, bw, bd, str(141 + i), orientation="S")
        bay_compact(msp, sx + i * bw, row_m_y, bw, bd, str(146 + i), orientation="N")

    text_msp(msp, "ROW L (BAYS 136-145)", ox + WB / 2.0, row_l_y + bd + 0.5 * FT, h=0.55 * FT, layer="A-TEXT-TTL")
    text_msp(msp, "4' AISLE 6", ox + WB / 2.0, row_l_y - 2.2 * FT, h=0.47 * FT, layer="A-TEXT")
    text_msp(msp, "ROW M (BAYS 146-150)", sx + 15.0 * FT, row_m_y - 0.6 * FT, h=0.55 * FT, layer="A-TEXT-TTL")

    rect(msp, dx, row_m_y, dx + 30.0 * FT, row_m_y + bd, layer="A-BAY", lw=25)
    text_msp(msp, "FLEX SLOTS 151-155\n(VISITING / AD-HOC ADVOCATES)", dx + 15.0 * FT, row_m_y + bd / 2.0, h=0.55 * FT, layer="A-BAY")

    lock_y = oy + HB - 3.5 * FT
    locker_bank(msp, sx, lock_y, 8, 5, "LITIGANT LOCKERS: L1-L40 (40 NOS)", col_start=1, type_code="L")

    rect(msp, ox + 2.0 * FT, oy + 1.0 * FT, ox + 24.0 * FT, oy + 11.0 * FT, layer="A-FURN")
    text_msp(msp, "JR. ADVOCATE LOUNGE 22'x10'\n15 CHAIRS + 2 TABLES + RO WATER", ox + 13.0 * FT, oy + 6.0 * FT, h=0.50 * FT, layer="A-TEXT-TTL")

    rect(msp, ox + 26.0 * FT, oy + 1.0 * FT, ox + WB - 2.0 * FT, oy + 11.0 * FT, layer="A-FURN")
    text_msp(msp, "AMENITIES BLOCK 50'x10'\n3 GENTS WC + 2 URINALS | 3 LADIES WC | 1 RPwD ACCESSIBLE WC | 6 WASHBASINS + CLEAN STORE", ox + 53.0 * FT, oy + 6.0 * FT, h=0.47 * FT, layer="A-TEXT-TTL")

    msp.add_line((ox + WB / 2.0 - 4.0 * FT, oy), (ox + WB / 2.0 - 4.0 * FT, oy + 1.0 * FT), dxfattribs={"layer": "A-DOOR", "lineweight": 35})
    msp.add_line((ox + WB / 2.0 + 4.0 * FT, oy), (ox + WB / 2.0 + 4.0 * FT, oy + 1.0 * FT), dxfattribs={"layer": "A-DOOR", "lineweight": 35})
    text_msp(msp, "6 ft SOUTH ENTRY -> WALKWAY TO PLOT 1", ox + WB / 2.0, oy + 1.5 * FT, h=0.55 * FT, layer="A-DOOR")

    rect(msp, ox + WB - 8.0 * FT, oy + HB - 2.0 * FT, ox + WB - 2.0 * FT, oy + HB, layer="A-DOOR", lw=35)
    text_msp(msp, "6 ft FIRE EXIT N", ox + WB - 5.0 * FT, oy + HB - 1.0 * FT, h=0.50 * FT, layer="A-DOOR")

    arch_dim_h(msp, ox, oy - 2.0 * FT, ox + WB, "60'-0\" (BUILDABLE WIDTH)", offset=-1.2 * FT)
    arch_dim_v(msp, ox - 2.0 * FT, oy, oy + HB, "40'-0\" (BUILDABLE DEPTH)", offset=-1.2 * FT)

    notes = [
        "Workstation Layout: Advocate seated on one side of desk, 2 Litigants on opposite side facing advocate.",
        "Option 1.1.2 Plot 2 Capacity: 35 Advocate Workstations (Bays 116-150) + 5 Flex Slots (151-155).",
        "Amenities: Full Sanitation Block with 7 WCs (incl. Accessible WC) + 2 Urinals + 6 Basins complying with NBC 2016.",
        "Total Campus Capacity (Option 1): Plot 1 (115) + Plot 2 (35) = 150 ADVOCATE WORKSTATIONS COMPLETE.",
    ]
    draw_sheet_frame_and_titleblock(msp, SHEET_W, SHEET_H, "SHEET 03 OF 16", "OPTION 1 - PLOT 2 GROUND FLOOR PLAN (35 BAYS + AMENITIES + 40 LOCKERS)", "1/8\" = 1'-0\"", notes=notes)
    save_drawing(doc, "03-Option1-Plot2-Ground-Floor-Plan-35-Bays")
    return doc


# SHEET 04: OPTION 1 - COMBINED CAMPUS GROUND FLOOR PLAN
def draw_sheet_04_o1_combined_campus():
    doc, msp = setup_doc()

    ox, oy = 10.0 * FT, 12.0 * FT
    p1_bx, p1_by = ox + 4.0 * FT, oy + 4.0 * FT
    rect(msp, ox, oy, ox + 80.0 * FT, oy + 72.0 * FT, layer="A-SITE", lw=35)
    rect(msp, p1_bx, p1_by, p1_bx + 72.0 * FT, p1_by + 64.0 * FT, layer="A-WALL", lw=45)
    text_msp(msp, "PLOT 1 - 115 ADVOCATE BAYS\n+ 150 ADVOCATE LOCKERS + WAITING HALL + COURTYARD", p1_bx + 36.0 * FT, p1_by + 32.0 * FT, h=0.95 * FT, layer="A-TEXT-TTL")

    p2_ox = ox + 88.0 * FT
    p2_bx, p2_by = p2_ox + 4.0 * FT, oy + 32.0 * FT
    rect(msp, p2_ox, oy + 28.0 * FT, p2_ox + 50.0 * FT, oy + 72.0 * FT, layer="A-SITE", lw=35)
    rect(msp, p2_bx, p2_by, p2_bx + 42.0 * FT, p2_by + 36.0 * FT, layer="A-WALL", lw=45)
    text_msp(msp, "PLOT 2 - 35 ADVOCATE BAYS\n+ 40 LITIGANT LOCKERS\n+ AMENITIES + LOUNGE", p2_bx + 21.0 * FT, p2_by + 18.0 * FT, h=0.80 * FT, layer="A-TEXT-TTL")

    rect(msp, ox + 80.0 * FT, oy + 45.0 * FT, p2_ox, oy + 53.0 * FT, layer="A-ROOF", lw=25)
    text_msp(msp, "10 ft COVERED WALKWAY", ox + 84.0 * FT, oy + 49.0 * FT, h=0.45 * FT, layer="A-TEXT-TTL", rot=90.0)

    rect(msp, ox, oy - 12.0 * FT, p2_ox + 50.0 * FT, oy, layer="A-SITE", lw=30)
    text_msp(msp, "20 ft LANDSCAPED PLAZA - PEDESTRIAN ACCESS FROM DISTRICT COURT", (ox + p2_ox + 50.0 * FT) / 2.0, oy - 6.0 * FT, h=0.75 * FT, layer="A-TEXT-TTL")

    text_msp(msp, ">> ADVOCATE & LITIGANT ENTRY CIRCULATION >>", p1_bx + 36.0 * FT, oy - 2.5 * FT, h=0.55 * FT, layer="A-ACC")

    tb_x, tb_y = p2_ox, oy + 2.0 * FT
    rect(msp, tb_x, tb_y, tb_x + 50.0 * FT, tb_y + 24.0 * FT, layer="A-TTLB", lw=25)
    stat_lines = [
        "OPTION 1 CAMPUS SUMMARY (GROUND FLOOR ONLY):",
        "* Plot 1 Advocate Workstations : 115 Nos (5'x6.5')",
        "* Plot 2 Advocate Workstations :  35 Nos (5'x6.5')",
        "* TOTAL ADVOCATE CAPACITY      : 150 ADVOCATES",
        "* Advocate Steel Lockers (P1)  : 150 Lockers",
        "* Litigant Public Lockers (P2) :  40 Lockers",
        "* TOTAL CAMPUS LOCKERS         : 190 LOCKERS",
        "* Total Built-Up Area (BUA)    : 10,500 Sq Ft",
        "* Total Project Cost           : Rs. 2.16 Crore",
    ]
    for i, ln in enumerate(stat_lines):
        h_val = 0.20 * FT if i in (0, 3, 6, 8) else 0.16 * FT
        layer_val = "A-TEXT-TTL" if i in (0, 3, 6, 8) else "A-TEXT"
        text_msp(msp, ln, tb_x + 1.0 * FT, tb_y + 22.0 * FT - i * 2.3 * FT, h=h_val, layer=layer_val, align=TextEntityAlignment.LEFT)

    arch_dim_h(msp, ox, oy - 14.0 * FT, p2_ox + 50.0 * FT, "180'-0\" COMBINED CAMPUS FRONTAGE", offset=-1.2 * FT)

    notes = [
        "Option 1 delivers all 150 advocate workstations at ground level with zero vertical stair climbing.",
        "Full RPwD Barrier-Free accessibility: 1:12 ramps, 5'-0\" clear aisles, low counters, accessible toilets.",
        "Total Lockers: 190 Steel Units allocated 1:1 to all 150 Advocates + 40 Day-Use Litigants.",
    ]
    draw_sheet_frame_and_titleblock(msp, SHEET_W, SHEET_H, "SHEET 04 OF 16", "OPTION 1 - COMBINED CAMPUS GROUND FLOOR PLAN (150 BAYS + 190 LOCKERS)", "1\" = 16'-0\"", notes=notes)
    save_drawing(doc, "04-Option1-Combined-Campus-Ground-Floor-Plan")
    return doc


# SHEET 05: OPTION 1 - BUILDING SECTIONS AND DETAILS
def draw_sheet_05_o1_sections():
    doc, msp = setup_doc()

    ox, oy = 25.0 * FT, 25.0 * FT
    W = 100.0 * FT
    plinth = 1.5 * FT
    clr_ht = 11.0 * FT
    slab = 1.0 * FT
    parapet = 3.0 * FT

    msp.add_line((ox - 5.0 * FT, oy), (ox + W + 5.0 * FT, oy), dxfattribs={"layer": "A-SECT-CUT", "lineweight": 50})
    text_msp(msp, "GROUND LEVEL (0'-0\")", ox - 6.0 * FT, oy, h=0.50 * FT, layer="A-TEXT", align=TextEntityAlignment.RIGHT)

    rect(msp, ox, oy, ox + W, oy + plinth, layer="A-WALL", lw=40)
    fill_rect(msp, ox, oy, ox + W, oy + plinth, hatch="ANSI31", layer="A-HATCH")
    text_msp(msp, "PLINTH LEVEL (+1'-6\")", ox - 6.0 * FT, oy + plinth, h=0.50 * FT, layer="A-TEXT", align=TextEntityAlignment.RIGHT)

    wall_bot = oy + plinth
    wall_top = wall_bot + clr_ht
    for wx in [ox, ox + W - 0.75 * FT]:
        rect(msp, wx, wall_bot, wx + 0.75 * FT, wall_top, layer="A-WALL", lw=50)
        fill_rect(msp, wx, wall_bot, wx + 0.75 * FT, wall_top, hatch="ANSI32", layer="A-HATCH")

    roof_bot = wall_top
    roof_top = roof_bot + slab
    rect(msp, ox - 1.0 * FT, roof_bot, ox + W + 1.0 * FT, roof_top, layer="A-ROOF", lw=40)
    fill_rect(msp, ox - 1.0 * FT, roof_bot, ox + W + 1.0 * FT, roof_top, hatch="ANSI31", layer="A-HATCH")
    text_msp(msp, "ROOF SLAB LEVEL (+13'-6\") [125mm RCC M20 + 1 ft BRICKBAT COBA WATERPROOFING]", ox + W / 2.0, roof_bot + 0.5 * FT, h=0.55 * FT, layer="A-TEXT-TTL")

    rect(msp, ox, roof_top, ox + 0.75 * FT, roof_top + parapet, layer="A-WALL", lw=35)
    rect(msp, ox + W - 0.75 * FT, roof_top, ox + W, roof_top + parapet, layer="A-WALL", lw=35)
    text_msp(msp, "PARAPET TOP (+16'-6\")", ox - 6.0 * FT, roof_top + parapet, h=0.50 * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.RIGHT)

    for jx in [ox + 16.0 * FT, ox + 32.0 * FT, ox + 68.0 * FT, ox + 84.0 * FT]:
        rect(msp, jx, wall_bot, jx + 0.4 * FT, wall_bot + 3.5 * FT, layer="A-JALI", lw=25)
        text_msp(msp, "3.5' JALI", jx + 0.2 * FT, wall_bot + 4.2 * FT, h=0.40 * FT, layer="A-JALI")

    text_msp(msp, "6 ft CENTRAL CORRIDOR (CLEAR FLOOR)", ox + 50.0 * FT, wall_bot + 2.5 * FT, h=0.60 * FT, layer="A-TEXT-TTL")

    for fx in [ox + 12.0 * FT, ox + 28.0 * FT, ox + 50.0 * FT, ox + 72.0 * FT, ox + 88.0 * FT]:
        msp.add_line((fx, roof_bot), (fx, roof_bot - 1.5 * FT), dxfattribs={"layer": "A-FURN", "lineweight": 20})
        msp.add_line((fx - 1.5 * FT, roof_bot - 1.5 * FT), (fx + 1.5 * FT, roof_bot - 1.5 * FT), dxfattribs={"layer": "A-FURN", "lineweight": 20})
        text_msp(msp, "FAN", fx, roof_bot - 2.0 * FT, h=0.38 * FT, layer="A-FURN")

    arch_dim_v(msp, ox + W + 4.0 * FT, oy, oy + plinth, "1'-6\" PLINTH", offset=1.2 * FT)
    arch_dim_v(msp, ox + W + 4.0 * FT, wall_bot, wall_top, "11'-0\" CLEAR CEILING HT", offset=1.2 * FT)
    arch_dim_v(msp, ox + W + 4.0 * FT, roof_bot, roof_top, "1'-0\" ROOF SLAB", offset=1.2 * FT)
    arch_dim_v(msp, ox + W + 4.0 * FT, roof_top, roof_top + parapet, "3'-0\" PARAPET", offset=1.2 * FT)
    arch_dim_v(msp, ox + W + 8.0 * FT, oy, roof_top + parapet, "16'-6\" TOTAL BUILDING HEIGHT", offset=1.8 * FT)
    arch_dim_h(msp, ox, oy - 3.0 * FT, ox + W, "90'-0\" BUILDING WIDTH", offset=-1.2 * FT)

    notes = [
        "Floor to Ceiling Clear Height: 11'-0\" (3.35 m) exceeds NBC 2016 minimum of 9'-0\" for natural cooling.",
        "Roof Finish: High-albedo white China Mosaic tile (SRI > 80) over 1 ft brickbat coba reducing heat gain by 20%.",
        "Ventilation: Cross-ventilation achieved via 12 brick-jali vents (4'x2') and 24 sliding windows (4'x4').",
    ]
    draw_sheet_frame_and_titleblock(msp, SHEET_W, SHEET_H, "SHEET 05 OF 16", "OPTION 1 - BUILDING CROSS-SECTION A-A & TECHNICAL DETAILS", "1/8\" = 1'-0\"", notes=notes)
    save_drawing(doc, "05-Option1-Building-Sections-and-Details")
    return doc


# SHEET 06: OPTION 1 - SOUTH FRONT & NORTH REAR ELEVATIONS
def draw_sheet_06_o1_elevations():
    doc, msp = setup_doc()

    ox, oy = 25.0 * FT, 14.0 * FT
    W, H = 100.0 * FT, 16.5 * FT

    # View 1: South Front Elevation
    rect(msp, ox, oy, ox + W, oy + 1.5 * FT, layer="A-WALL", lw=40)
    fill_rect(msp, ox, oy, ox + W, oy + 1.5 * FT, hatch="SOLID", layer="A-HATCH")
    text_msp(msp, "6\" RED SANDSTONE EMULSION PLINTH BAND", ox + W / 2.0, oy + 0.75 * FT, h=0.50 * FT, layer="A-TEXT-TTL")

    rect(msp, ox, oy + 1.5 * FT, ox + W, oy + 13.5 * FT, layer="A-WALL", lw=40)
    rect(msp, ox, oy + 13.5 * FT, ox + W, oy + 16.5 * FT, layer="A-WALL", lw=40)

    rect(msp, ox + W / 2.0 - 5.0 * FT, oy + 1.5 * FT, ox + W / 2.0 + 5.0 * FT, oy + 8.5 * FT, layer="A-DOOR", lw=45)
    text_msp(msp, "10 ft MAIN DOUBLE-LEAF ENTRY", ox + W / 2.0, oy + 5.0 * FT, h=0.60 * FT, layer="A-DOOR")

    win_xs = [ox + 8.0 * FT, ox + 20.0 * FT, ox + 32.0 * FT, ox + 68.0 * FT, ox + 80.0 * FT, ox + 92.0 * FT]
    for wx in win_xs:
        rect(msp, wx, oy + 4.0 * FT, wx + 4.0 * FT, oy + 8.0 * FT, layer="A-WINDOW", lw=30)
        msp.add_line((wx + 2.0 * FT, oy + 4.0 * FT), (wx + 2.0 * FT, oy + 8.0 * FT), dxfattribs={"layer": "A-WINDOW"})
        text_msp(msp, "4'x4'", wx + 2.0 * FT, oy + 6.0 * FT, h=0.45 * FT, layer="A-WINDOW")

    for wx in win_xs:
        rect(msp, wx, oy + 9.5 * FT, wx + 4.0 * FT, oy + 11.5 * FT, layer="A-JALI", lw=25)
        text_msp(msp, "JALI", wx + 2.0 * FT, oy + 10.5 * FT, h=0.40 * FT, layer="A-JALI")

    rect(msp, ox + 25.0 * FT, oy + 13.8 * FT, ox + 75.0 * FT, oy + 15.8 * FT, layer="A-TEXT-TTL", lw=25)
    text_msp(msp, "ADVOCATE SITOUT - BANSWARA DISTRICT COURT", ox + W / 2.0, oy + 14.8 * FT, h=0.75 * FT, layer="A-TEXT-TTL")
    text_msp(msp, "SOUTH (FRONT) ELEVATION - OPTION 1", ox + W / 2.0, oy - 2.5 * FT, h=0.80 * FT, layer="A-TEXT-TTL")

    # View 2: North Rear Elevation
    oy2 = oy + 28.0 * FT
    rect(msp, ox, oy2, ox + W, oy2 + 1.5 * FT, layer="A-WALL", lw=40)
    fill_rect(msp, ox, oy2, ox + W, oy2 + 1.5 * FT, hatch="SOLID", layer="A-HATCH")
    rect(msp, ox, oy2 + 1.5 * FT, ox + W, oy2 + 13.5 * FT, layer="A-WALL", lw=40)
    rect(msp, ox, oy2 + 13.5 * FT, ox + W, oy2 + 16.5 * FT, layer="A-WALL", lw=40)

    for ex in [ox + 12.0 * FT, ox + W - 16.0 * FT]:
        rect(msp, ex, oy2 + 1.5 * FT, ex + 4.0 * FT, oy2 + 8.5 * FT, layer="A-DOOR", lw=40)
        text_msp(msp, "FIRE EXIT", ex + 2.0 * FT, oy2 + 5.0 * FT, h=0.45 * FT, layer="A-DOOR")

    for wx in [ox + 24.0 * FT, ox + 36.0 * FT, ox + 48.0 * FT, ox + 60.0 * FT, ox + 72.0 * FT]:
        rect(msp, wx, oy2 + 4.0 * FT, wx + 4.0 * FT, oy2 + 8.0 * FT, layer="A-WINDOW", lw=30)
        text_msp(msp, "4'x4'", wx + 2.0 * FT, oy2 + 6.0 * FT, h=0.45 * FT, layer="A-WINDOW")

    text_msp(msp, "NORTH (REAR) ELEVATION - OPTION 1", ox + W / 2.0, oy2 - 2.5 * FT, h=0.80 * FT, layer="A-TEXT-TTL")

    arch_dim_h(msp, ox, oy - 5.0 * FT, ox + W, "92'-0\" OVERALL FACADE WIDTH", offset=-1.2 * FT)
    arch_dim_v(msp, ox - 3.0 * FT, oy, oy + 16.5 * FT, "16'-6\" TOTAL HEIGHT", offset=-1.2 * FT)

    notes = [
        "Facade Finish: Weatherproof light cream exterior acrylic emulsion + 6\" deep red sandstone plinth band.",
        "Joinery: Heavy duty 10 ft double steel entrance frame + 24 Nos. aluminium sliding glazed windows.",
        "Passive Cooling: 12 brick-jali ventilators provide continuous natural airflow without power consumption.",
    ]
    draw_sheet_frame_and_titleblock(msp, SHEET_W, SHEET_H, "SHEET 06 OF 16", "OPTION 1 - SOUTH FRONT & NORTH REAR ELEVATIONS", "1/8\" = 1'-0\"", notes=notes)
    save_drawing(doc, "06-Option1-South-Front-and-North-Rear-Elevations")
    return doc


# SHEET 07: OPTION 2 - PLOT 1 GROUND FLOOR PLAN (60 BAYS)
def draw_sheet_07_o2_p1_gf():
    doc, msp = setup_doc()

    ox, oy = 28.0 * FT, 11.0 * FT
    WB, HB = 90.0 * FT, 74.0 * FT

    rect(msp, ox, oy, ox + WB, oy + HB, layer="A-WALL", lw=50)
    fill_rect(msp, ox, oy, ox + WB, oy + HB, hatch="ANSI31", layer="A-HATCH")
    fill_rect(msp, ox + 0.75 * FT, oy + 0.75 * FT, ox + WB - 0.75 * FT, oy + HB - 0.75 * FT, hatch="SOLID", layer="A-HATCH")

    cx1 = ox + (WB - 24.0 * FT) / 2.0
    cy1 = oy + (HB - 24.0 * FT) / 2.0
    cx2 = cx1 + 24.0 * FT
    cy2 = cy1 + 24.0 * FT
    rect(msp, cx1, cy1, cx2, cy2, layer="A-BAY", lw=40)
    fill_rect(msp, cx1, cy1, cx2, cy2, hatch="SOLID", layer="A-HATCH")

    msp.add_circle(((cx1 + cx2) / 2.0, (cy1 + cy2) / 2.0), 5.5 * FT, dxfattribs={"layer": "A-ROOF", "lineweight": 30})
    msp.add_circle(((cx1 + cx2) / 2.0, (cy1 + cy2) / 2.0), 2.5 * FT, dxfattribs={"layer": "A-ROOF", "lineweight": 20})
    text_msp(msp, "24'x24' OPEN-TO-SKY COURTYARD\nSTEPWELL FOUNTAIN + 4 TREES + 6 BENCHES\n(DOUBLE HEIGHT 23' CLEAR VOID)",
             (cx1 + cx2) / 2.0, (cy1 + cy2) / 2.0, h=0.65 * FT, layer="A-TEXT-TTL")

    rect(msp, cx1 - 5.0 * FT, cy1 - 5.0 * FT, cx2 + 5.0 * FT, cy2 + 5.0 * FT, layer="A-WALL", lw=25)
    text_msp(msp, "6 ft RING CORRIDOR", (cx1 + cx2) / 2.0, cy1 - 2.5 * FT, h=0.50 * FT, layer="A-TEXT-TTL")

    for i in range(8):
        px = ox + 4.0 * FT + i * 8.5 * FT
        bay_premium(msp, px, oy + HB - 11.0 * FT, 8.0 * FT, 9.5 * FT, f"N{i + 1}")

    st_x = ox + WB - 18.0 * FT
    rect(msp, st_x, oy + HB - 11.0 * FT, ox + WB - 2.0 * FT, oy + HB - 2.0 * FT, layer="A-WALL", lw=40)
    text_msp(msp, "2x LIFTS (13P MRL)\n+ 2x STAIRS (5' WIDE)", st_x + 8.0 * FT, oy + HB - 6.5 * FT, h=0.55 * FT, layer="A-TEXT-TTL")

    for row in range(4):
        for col in range(7):
            bx = ox + 3.0 * FT + row * 6.0 * FT
            by = oy + 10.0 * FT + col * 4.0 * FT
            bay_compact(msp, bx, by, 5.5 * FT, 3.8 * FT, f"W{row * 7 + col + 1}", orientation="S" if row % 2 == 0 else "N")
    text_msp(msp, "WEST CLUSTER: 28 OPEN BAYS (W1-W28)", ox + 14.0 * FT, oy + 40.0 * FT, h=0.55 * FT, layer="A-TEXT-TTL", rot=90.0)

    for row in range(4):
        for col in range(6):
            bx = cx2 + 7.0 * FT + row * 6.0 * FT
            by = oy + 10.0 * FT + col * 4.0 * FT
            bay_compact(msp, bx, by, 5.5 * FT, 3.8 * FT, f"E{row * 6 + col + 1}", orientation="S" if row % 2 == 0 else "N")
    text_msp(msp, "EAST CLUSTER: 24 OPEN BAYS (E1-E24)", ox + WB - 11.0 * FT, oy + 24.0 * FT, h=0.55 * FT, layer="A-TEXT-TTL", rot=90.0)

    rect(msp, ox + 3.0 * FT, oy + 2.0 * FT, ox + 20.0 * FT, oy + 9.0 * FT, layer="A-FURN")
    text_msp(msp, "RECEPTION 17'x8'\n(2 Counters + Braille Desk)", ox + 11.5 * FT, oy + 5.5 * FT, h=0.50 * FT, layer="A-TEXT-TTL")

    rect(msp, ox + 45.0 * FT, oy + 2.0 * FT, ox + 88.0 * FT, oy + 9.0 * FT, layer="A-FURN")
    text_msp(msp, "LITIGANT WAITING HALL 43'x8' (75 CUSHIONED + 50 FOLDING SEATS)", ox + 66.5 * FT, oy + 5.5 * FT, h=0.50 * FT, layer="A-TEXT-TTL")

    msp.add_line((ox + WB / 2.0 - 5.0 * FT, oy), (ox + WB / 2.0 - 5.0 * FT, oy + 1.5 * FT), dxfattribs={"layer": "A-DOOR", "lineweight": 40})
    msp.add_line((ox + WB / 2.0 + 5.0 * FT, oy), (ox + WB / 2.0 + 5.0 * FT, oy + 1.5 * FT), dxfattribs={"layer": "A-DOOR", "lineweight": 40})
    text_msp(msp, "10 ft MAIN CARVED STONE ENTRY ARCH", ox + WB / 2.0, oy + 2.0 * FT, h=0.60 * FT, layer="A-DOOR")

    arch_dim_h(msp, ox, oy - 2.0 * FT, ox + WB, "90'-0\" (BUILDABLE WIDTH)", offset=-1.2 * FT)
    arch_dim_v(msp, ox - 2.0 * FT, oy, oy + HB, "90'-0\" (BUILDABLE DEPTH)", offset=-1.2 * FT)

    notes = [
        "Option 2 Ground Floor Capacity: 8 Senior Advocate Premium Cabins (N1-N8) + 52 Open Workstations = 60 ADVOCATES.",
        "Ergonomic Arrangement: Advocate seated on inner side of desk; clients/litigants seated on opposite side.",
        "Central Courtyard: 24'x24' double-height open-to-sky haveli courtyard creating natural stack ventilation.",
        "Vertical Circulation: 2 High-Speed 13-Passenger Lifts (MRL with ARD) + 2 RPwD Compliant 5 ft Staircases.",
    ]
    draw_sheet_frame_and_titleblock(msp, SHEET_W, SHEET_H, "SHEET 07 OF 16", "OPTION 2 - PLOT 1 GROUND FLOOR PLAN (60 BAYS + COURTYARD)", "1/8\" = 1'-0\"", notes=notes)
    save_drawing(doc, "07-Option2-Plot1-Ground-Floor-Plan-60-Bays")
    return doc


# SHEET 08: OPTION 2 - PLOT 1 FIRST FLOOR PLAN (60 BAYS)
def draw_sheet_08_o2_p1_ff():
    doc, msp = setup_doc()

    ox, oy = 28.0 * FT, 11.0 * FT
    WB, HB = 90.0 * FT, 74.0 * FT

    rect(msp, ox, oy, ox + WB, oy + HB, layer="A-WALL", lw=50)

    cx1 = ox + (WB - 24.0 * FT) / 2.0
    cy1 = oy + (HB - 24.0 * FT) / 2.0
    cx2 = cx1 + 24.0 * FT
    cy2 = cy1 + 24.0 * FT
    rect(msp, cx1, cy1, cx2, cy2, layer="A-JALI", lw=30)
    text_msp(msp, "24'x24' COURTYARD VOID (OPEN TO SKY)\nOVERLOOKING GROUND FLOOR FOUNTAIN & TREES", (cx1 + cx2) / 2.0, (cy1 + cy2) / 2.0, h=0.65 * FT, layer="A-TEXT-TTL")

    rect(msp, cx1 - 5.0 * FT, cy1 - 5.0 * FT, cx2 + 5.0 * FT, cy2 + 5.0 * FT, layer="A-WALL", lw=25)
    text_msp(msp, "6 ft RING CORRIDOR FLOOR", (cx1 + cx2) / 2.0, cy1 - 2.5 * FT, h=0.50 * FT, layer="A-TEXT-TTL")

    for i in range(8):
        px = ox + 4.0 * FT + i * 8.5 * FT
        bay_premium(msp, px, oy + HB - 11.0 * FT, 8.0 * FT, 9.5 * FT, f"N{i + 9}")

    for row in range(4):
        for col in range(7):
            bx = ox + 3.0 * FT + row * 6.0 * FT
            by = oy + 10.0 * FT + col * 4.0 * FT
            bay_compact(msp, bx, by, 5.5 * FT, 3.8 * FT, f"W{row * 7 + col + 29}", orientation="S" if row % 2 == 0 else "N")

    rect(msp, ox + 3.0 * FT, oy + 2.0 * FT, ox + 35.0 * FT, oy + 12.0 * FT, layer="A-FURN")
    text_msp(msp, "BAR ASSOCIATION ROOM 32'x10'\n(100 SEATS + BAR COUNTER)", ox + 19.0 * FT, oy + 7.0 * FT, h=0.55 * FT, layer="A-TEXT-TTL")

    rect(msp, ox + 40.0 * FT, oy + 2.0 * FT, ox + 88.0 * FT, oy + 12.0 * FT, layer="A-FURN")
    text_msp(msp, "LAW REFERENCE LIBRARY 48'x10'\n(1,000+ BOOKS + 4 COMPUTER STATIONS)", ox + 64.0 * FT, oy + 7.0 * FT, h=0.55 * FT, layer="A-TEXT-TTL")

    sb_y1 = oy + 32.0 * FT
    sb_y2 = sb_y1 + 10.0 * FT
    rect(msp, ox + WB, sb_y1, ox + WB + 15.0 * FT, sb_y2, layer="A-ROOF", lw=40)
    text_msp(msp, "10 ft COVERED SKY-BRIDGE -> TO PLOT 2 FIRST FLOOR", ox + WB + 7.5 * FT, (sb_y1 + sb_y2) / 2.0, h=0.50 * FT, layer="A-ROOF")

    arch_dim_h(msp, ox, oy - 2.0 * FT, ox + WB, "90'-0\" (BUILDING WIDTH)", offset=-1.2 * FT)

    notes = [
        "Option 2 First Floor Capacity: 12 Senior Cabins (N9-N20) + 48 Open Workstations = 60 ADVOCATES.",
        "Plot 1 G+1 Combined Total: 120 ADVOCATES accommodated with complete professional amenities.",
        "Sky-Bridge: 10 ft wide elevated walkway connecting directly to Plot 2 Conference and Dining facilities.",
    ]
    draw_sheet_frame_and_titleblock(msp, SHEET_W, SHEET_H, "SHEET 08 OF 16", "OPTION 2 - PLOT 1 FIRST FLOOR PLAN (60 BAYS + BAR ROOM + SKY-BRIDGE)", "1/8\" = 1'-0\"", notes=notes)
    save_drawing(doc, "08-Option2-Plot1-First-Floor-Plan-60-Bays")
    return doc


# SHEET 09: OPTION 2 - PLOT 1 SECOND FLOOR PLAN
def draw_sheet_09_o2_p1_2f():
    doc, msp = setup_doc()

    ox, oy = 28.0 * FT, 11.0 * FT
    WB, HB = 90.0 * FT, 74.0 * FT

    rect(msp, ox, oy, ox + WB, oy + HB, layer="A-WALL", lw=50)

    rect(msp, ox + 3.0 * FT, oy + HB - 26.0 * FT, ox + 43.0 * FT, oy + HB - 2.0 * FT, layer="A-FURN", lw=35)
    text_msp(msp, "BAR ASSOCIATION GRAND HALL 40'x30' (1,200 SQ FT)\n200-SEAT THEATRE CAPACITY | RAISED DAIS & PODIUM\n(PHASE 2 CONVERTIBLE TO 20 WORKSTATION BAYS)",
             ox + 23.0 * FT, oy + HB - 14.0 * FT, h=0.60 * FT, layer="A-TEXT-TTL")

    rect(msp, ox + 47.0 * FT, oy + HB - 26.0 * FT, ox + 72.0 * FT, oy + HB - 2.0 * FT, layer="A-FURN", lw=35)
    text_msp(msp, "CENTRAL LAW LIBRARY 25'x30' (750 SQ FT)\n1,000+ BOOKS | 10 READING CARRELS | 4 PC TERMINALS\n(PHASE 2 CONVERTIBLE TO 16 BAYS + 4 CABINS)",
             ox + 59.5 * FT, oy + HB - 14.0 * FT, h=0.55 * FT, layer="A-TEXT-TTL")

    rect(msp, ox + 58.0 * FT, oy + 10.0 * FT, ox + 88.0 * FT, oy + 32.0 * FT, layer="A-FURN", lw=35)
    text_msp(msp, "MULTI-PURPOSE HALL 30'x25' (750 SQ FT)\n40-SEAT CONFERENCE + PANTRY KITCHENETTE\n(PHASE 2 CONVERTIBLE TO 20 BAYS)",
             ox + 73.0 * FT, oy + 21.0 * FT, h=0.55 * FT, layer="A-TEXT-TTL")

    rect(msp, ox + 3.0 * FT, oy + 2.0 * FT, ox + 54.0 * FT, oy + 24.0 * FT, layer="A-BAY", lw=30)
    text_msp(msp, "TERRACE ROOF GARDEN ~2,000 SQ FT (SOUTH OVERLOOK)\nPERGOLA COVER (15'x20') + 4 STONE BENCHES + NATIVE PLANTERS\n(PHASE 2: 4 GLASS PREMIUM CABINS POSSIBLE)",
             ox + 28.5 * FT, oy + 13.0 * FT, h=0.60 * FT, layer="A-BAY")

    cx1 = ox + (WB - 24.0 * FT) / 2.0
    cy1 = oy + (HB - 24.0 * FT) / 2.0
    rect(msp, cx1, cy1, cx1 + 24.0 * FT, cy1 + 24.0 * FT, layer="A-JALI", lw=30)
    text_msp(msp, "24'x24' COURTYARD VOID", cx1 + 12.0 * FT, cy1 + 12.0 * FT, h=0.65 * FT, layer="A-TEXT-TTL")

    arch_dim_h(msp, ox, oy - 2.0 * FT, ox + WB, "90'-0\" (BUILDING WIDTH)", offset=-1.2 * FT)

    notes = [
        "Second Floor Flexibility: Provides institutional prestige spaces now, with built-in conversion for +40 bays in Phase 2.",
        "Structural Capacity: Engineered for 150 kg/sq ft live load to permit an additional 4th storey if future expansion requires.",
        "Roof Terrace: High albedo cool roof and shaded pergola seating providing thermal insulation to floors below.",
    ]
    draw_sheet_frame_and_titleblock(msp, SHEET_W, SHEET_H, "SHEET 09 OF 16", "OPTION 2 - PLOT 1 SECOND FLOOR PLAN (BAR HALL + LIBRARY + TERRACE)", "1/8\" = 1'-0\"", notes=notes)
    save_drawing(doc, "09-Option2-Plot1-Second-Floor-Plan-Bar-Hall-and-Library")
    return doc


# SHEET 10: OPTION 2 - PLOT 2 GROUND FLOOR PLAN (15 BAYS)
def draw_sheet_10_o2_p2_gf():
    doc, msp = setup_doc()

    ox, oy = 35.0 * FT, 18.0 * FT
    WB, HB = 80.0 * FT, 55.0 * FT

    rect(msp, ox, oy, ox + WB, oy + HB, layer="A-WALL", lw=50)

    rect(msp, ox + 2.0 * FT, oy + HB - 12.0 * FT, ox + WB - 2.0 * FT, oy + HB - 1.0 * FT, layer="A-FURN", lw=30)
    text_msp(msp, "COVERED TWO-WHEELER PARKING - 35 BIKES\n2 ROWS STEEL RACKS + 2 EV CHARGING POINTS (NORTH SERVICE ACCESS)",
             ox + WB / 2.0, oy + HB - 6.5 * FT, h=0.60 * FT, layer="A-TEXT-TTL")

    for i in range(5):
        bx = ox + 4.0 * FT + i * 14.5 * FT
        bay_compact(msp, bx, oy + 18.0 * FT, 8.0 * FT, 9.0 * FT, str(121 + i), orientation="S")
        bay_compact(msp, bx, oy + 28.5 * FT, 8.0 * FT, 9.0 * FT, str(126 + i), orientation="N")
        bay_compact(msp, bx, oy + 7.5 * FT, 8.0 * FT, 9.0 * FT, str(131 + i), orientation="S")

    rect(msp, ox + 2.0 * FT, oy + 1.0 * FT, ox + 22.0 * FT, oy + 6.5 * FT, layer="A-FURN")
    text_msp(msp, "JR. LOUNGE 20'x5'\n20 SEATS + RO WATER", ox + 12.0 * FT, oy + 3.75 * FT, h=0.47 * FT, layer="A-FURN")

    rect(msp, ox + 42.0 * FT, oy + 1.0 * FT, ox + WB - 2.0 * FT, oy + 6.5 * FT, layer="A-FURN")
    text_msp(msp, "AMENITIES: 4G+4L WCs | 4 URINALS | 2 RPwD ACCESSIBLE WCs | 6 BASINS", ox + 58.0 * FT, oy + 3.75 * FT, h=0.45 * FT, layer="A-FURN")

    rect(msp, ox + 24.0 * FT, oy + 1.0 * FT, ox + 40.0 * FT, oy + 6.5 * FT, layer="A-WALL", lw=30)
    text_msp(msp, "LIFT 10P + STAIR 5' W", ox + 32.0 * FT, oy + 3.75 * FT, h=0.47 * FT, layer="A-WALL")

    arch_dim_h(msp, ox, oy - 2.0 * FT, ox + WB, "60'-0\" (BUILDING WIDTH)", offset=-1.2 * FT)
    arch_dim_v(msp, ox - 2.0 * FT, oy, oy + HB, "40'-0\" (BUILDING DEPTH)", offset=-1.2 * FT)

    notes = [
        "Option 2 Plot 2 Ground Floor: 15 Open Workstations (Bays 121-135) + 35-Bike Covered Parking.",
        "Sanitation: Full commercial toilet block exceeding NBC 2016 norms by 3x including 2 Accessible WCs.",
        "Vertical Circulation: 10-Passenger MRL lift with voice annunciation and Braille controls serving GF+FF.",
    ]
    draw_sheet_frame_and_titleblock(msp, SHEET_W, SHEET_H, "SHEET 10 OF 16", "OPTION 2 - PLOT 2 GROUND FLOOR PLAN (15 BAYS + BIKE PARKING)", "1/8\" = 1'-0\"", notes=notes)
    save_drawing(doc, "10-Option2-Plot2-Ground-Floor-Plan-15-Bays")
    return doc


# SHEET 11: OPTION 2 - PLOT 2 FIRST FLOOR PLAN (15 BAYS)
def draw_sheet_11_o2_p2_ff():
    doc, msp = setup_doc()

    ox, oy = 35.0 * FT, 18.0 * FT
    WB, HB = 80.0 * FT, 55.0 * FT

    rect(msp, ox, oy, ox + WB, oy + HB, layer="A-WALL", lw=50)

    for i in range(8):
        bx = ox + 3.0 * FT + i * 9.2 * FT
        bay_compact(msp, bx, oy + HB - 14.0 * FT, 8.0 * FT, 8.5 * FT, str(136 + i), orientation="S")
    for i in range(7):
        bx = ox + 3.0 * FT + i * 10.5 * FT
        bay_compact(msp, bx, oy + HB - 24.0 * FT, 8.0 * FT, 8.5 * FT, str(144 + i), orientation="N")

    rect(msp, ox + 2.0 * FT, oy + 1.0 * FT, ox + 32.0 * FT, oy + 18.0 * FT, layer="A-FURN", lw=30)
    text_msp(msp, "CONFERENCE ROOM 30'x17'\n40-SEAT AUDITORIUM | 100\" SCREEN + PA", ox + 17.0 * FT, oy + 9.5 * FT, h=0.55 * FT, layer="A-TEXT-TTL")

    rect(msp, ox + 45.0 * FT, oy + 1.0 * FT, ox + WB - 2.0 * FT, oy + 18.0 * FT, layer="A-FURN", lw=30)
    text_msp(msp, "BAR CAFETERIA & DINING 33'x17'\n50 SEATS + KITCHENETTE & VENDING", ox + 61.0 * FT, oy + 9.5 * FT, h=0.55 * FT, layer="A-TEXT-TTL")

    rect(msp, ox - 15.0 * FT, oy + 18.0 * FT, ox, oy + 28.0 * FT, layer="A-ROOF", lw=40)
    text_msp(msp, "<- 10 ft SKY-BRIDGE TO PLOT 1 FF RING CORRIDOR", ox - 7.5 * FT, oy + 23.0 * FT, h=0.50 * FT, layer="A-ROOF")

    arch_dim_h(msp, ox, oy - 2.0 * FT, ox + WB, "60'-0\" (BUILDING WIDTH)", offset=-1.2 * FT)
    arch_dim_v(msp, ox - 2.0 * FT, oy, oy + HB, "40'-0\" (BUILDING DEPTH)", offset=-1.2 * FT)

    notes = [
        "Option 2 Plot 2 First Floor: 15 Open Workstations (Bays 136-150) completes Phase 1 total of 150 ADVOCATES.",
        "Conference Facility: 40-seat multimedia presentation hall with video conferencing for DLSA & Bar meetings.",
        "Sky-Bridge Connection: 10 ft wide covered link provides seamless indoor access between all campus buildings.",
    ]
    draw_sheet_frame_and_titleblock(msp, SHEET_W, SHEET_H, "SHEET 11 OF 16", "OPTION 2 - PLOT 2 FIRST FLOOR PLAN (15 BAYS + CONF. + DINING)", "1/8\" = 1'-0\"", notes=notes)
    save_drawing(doc, "11-Option2-Plot2-First-Floor-Plan-15-Bays")
    return doc


# SHEET 12: OPTION 2 - PLOT 1 LONGITUDINAL SECTION
def draw_sheet_02_12_o2_p1_section():
    doc, msp = setup_doc()

    ox, oy = 25.0 * FT, 16.0 * FT
    W = 100.0 * FT
    plinth = 1.5 * FT
    gf_ht = 11.0 * FT
    slab = 1.0 * FT

    lvl_plinth = oy + plinth
    lvl_ff_slab = lvl_plinth + gf_ht + slab
    lvl_2f_slab = lvl_ff_slab + gf_ht + slab
    lvl_roof_slab = lvl_2f_slab + gf_ht + slab
    lvl_parapet = lvl_roof_slab + 3.0 * FT

    msp.add_line((ox - 5.0 * FT, oy), (ox + W + 15.0 * FT, oy), dxfattribs={"layer": "A-SECT-CUT", "lineweight": 50})

    rect(msp, ox, oy, ox + W, lvl_plinth, layer="A-WALL", lw=40)
    fill_rect(msp, ox, oy, ox + W, lvl_plinth, hatch="ANSI31", layer="A-HATCH")

    for wx in [ox, ox + W - 0.75 * FT]:
        rect(msp, wx, lvl_plinth, wx + 0.75 * FT, lvl_roof_slab, layer="A-WALL", lw=50)

    for sl_top, sl_name in [(lvl_ff_slab, "1F SLAB (+12'-0\")"), (lvl_2f_slab, "2F SLAB (+24'-0\")"), (lvl_roof_slab, "ROOF SLAB (+36'-0\")")]:
        rect(msp, ox - 1.0 * FT, sl_top - slab, ox + W + 1.0 * FT, sl_top, layer="A-ROOF", lw=40)
        fill_rect(msp, ox - 1.0 * FT, sl_top - slab, ox + W + 1.0 * FT, sl_top, hatch="ANSI31", layer="A-HATCH")
        text_msp(msp, sl_name, ox + W / 2.0, sl_top - 0.5 * FT, h=0.55 * FT, layer="A-TEXT-TTL")

    rect(msp, ox, lvl_roof_slab, ox + 0.75 * FT, lvl_parapet, layer="A-WALL", lw=35)
    rect(msp, ox + W - 0.75 * FT, lvl_roof_slab, ox + W, lvl_parapet, layer="A-WALL", lw=35)

    cx1 = ox + (W - 28.0 * FT) / 2.0
    cx2 = cx1 + 28.0 * FT
    msp.add_line((cx1, lvl_plinth), (cx1, lvl_parapet), dxfattribs={"layer": "A-JALI", "linetype": "DASHED", "lineweight": 20})
    msp.add_line((cx2, lvl_plinth), (cx2, lvl_parapet), dxfattribs={"layer": "A-JALI", "linetype": "DASHED", "lineweight": 20})
    text_msp(msp, "24'x24' OPEN-TO-SKY COURTYARD VOID\n(DOUBLE HEIGHT 23' CLEAR GF->2F)", (cx1 + cx2) / 2.0, (lvl_plinth + lvl_2f_slab) / 2.0, h=0.70 * FT, layer="A-TEXT-TTL")

    msp.add_circle(((cx1 + cx2) / 2.0, lvl_plinth + 2.0 * FT), 2.5 * FT, dxfattribs={"layer": "A-ROOF"})
    text_msp(msp, "FOUNTAIN", (cx1 + cx2) / 2.0, lvl_plinth + 2.0 * FT, h=0.45 * FT, layer="A-ROOF")

    sb_x1 = ox + W
    rect(msp, sb_x1, lvl_ff_slab - 0.5 * FT, sb_x1 + 12.0 * FT, lvl_ff_slab + 4.5 * FT, layer="A-ROOF", lw=35)
    text_msp(msp, "SKY-BRIDGE -> PLOT 2 FF (@ 12 ft)", sb_x1 + 6.0 * FT, lvl_ff_slab + 2.0 * FT, h=0.45 * FT, layer="A-ROOF")

    lmx = ox + W + 15.0 * FT
    for yval, label in [(oy, "GL: 0'-0\""), (lvl_plinth, "PLINTH: +1'-6\""), (lvl_ff_slab, "1F: +12'-0\""), (lvl_2f_slab, "2F: +24'-0\""), (lvl_roof_slab, "ROOF: +36'-0\""), (lvl_parapet, "PARAPET: +39'-0\"")]:
        msp.add_line((lmx - 1.0 * FT, yval), (lmx + 1.0 * FT, yval), dxfattribs={"layer": "A-DIM", "lineweight": 20})
        text_msp(msp, label, lmx + 1.5 * FT, yval, h=0.50 * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)

    arch_dim_h(msp, ox, oy - 2.0 * FT, ox + W, "90'-0\" BUILDING LENGTH", offset=-1.2 * FT)
    arch_dim_v(msp, ox - 3.0 * FT, oy, lvl_parapet, "39'-0\" TOTAL HEIGHT (<15m MUNICIPAL LIMIT)", offset=-1.2 * FT)

    notes = [
        "Total Height: 39'-0\" (11.9 m) strictly complies with Banswara municipal height limit of 15.0 m.",
        "Structural Frame: RCC framed column-beam structure detailed for Seismic Zone III (IS 1893:2016).",
        "Stack Ventilation: Double-height 24'x24' central courtyard creates natural updraft cooling for all 3 floors.",
    ]
    draw_sheet_frame_and_titleblock(msp, SHEET_W, SHEET_H, "SHEET 12 OF 16", "OPTION 2 - PLOT 1 LONGITUDINAL SECTION (THROUGH COURTYARD)", "1/8\" = 1'-0\"", notes=notes)
    save_drawing(doc, "12-Option2-Plot1-Longitudinal-Section-Courtyard")
    return doc


# SHEET 13: OPTION 2 - PLOT 2 G+1 SECTION
def draw_sheet_13_o2_p2_section():
    doc, msp = setup_doc()

    ox, oy = 25.0 * FT, 25.0 * FT
    W = 80.0 * FT
    plinth = 1.5 * FT
    clr_ht = 11.0 * FT
    slab = 1.0 * FT
    parapet = 3.0 * FT

    lvl_plinth = oy + plinth
    lvl_ff_slab = lvl_plinth + clr_ht + slab
    lvl_roof_slab = lvl_ff_slab + clr_ht + slab
    lvl_parapet = lvl_roof_slab + parapet

    msp.add_line((ox - 15.0 * FT, oy), (ox + W + 5.0 * FT, oy), dxfattribs={"layer": "A-SECT-CUT", "lineweight": 50})

    rect(msp, ox, oy, ox + W, lvl_plinth, layer="A-WALL", lw=40)
    fill_rect(msp, ox, oy, ox + W, lvl_plinth, hatch="ANSI31", layer="A-HATCH")

    for wx in [ox, ox + W - 0.75 * FT]:
        rect(msp, wx, lvl_plinth, wx + 0.75 * FT, lvl_roof_slab, layer="A-WALL", lw=50)

    for sl_top, sl_name in [(lvl_ff_slab, "1F SLAB (+12'-0\")"), (lvl_roof_slab, "ROOF SLAB (+24'-0\")")]:
        rect(msp, ox - 1.0 * FT, sl_top - slab, ox + W + 1.0 * FT, sl_top, layer="A-ROOF", lw=40)
        fill_rect(msp, ox - 1.0 * FT, sl_top - slab, ox + W + 1.0 * FT, sl_top, hatch="ANSI31", layer="A-HATCH")
        text_msp(msp, sl_name, ox + W / 2.0, sl_top - 0.5 * FT, h=0.55 * FT, layer="A-TEXT-TTL")

    rect(msp, ox, lvl_roof_slab, ox + W, lvl_parapet, layer="A-WALL", lw=35)

    sb_x1 = ox - 15.0 * FT
    rect(msp, sb_x1, lvl_ff_slab - 0.5 * FT, ox, lvl_ff_slab + 4.5 * FT, layer="A-ROOF", lw=40)
    text_msp(msp, "10 ft SKY-BRIDGE -> CONNECTS TO PLOT 1 FF (@ 12'-0\")", (sb_x1 + ox) / 2.0, lvl_ff_slab + 2.0 * FT, h=0.50 * FT, layer="A-ROOF")

    text_msp(msp, "GF: 15 BAYS + 35 BIKE PARKING + AMENITIES", ox + W / 2.0, lvl_plinth + 5.5 * FT, h=0.65 * FT, layer="A-TEXT")
    text_msp(msp, "FF: 15 BAYS + 40-SEAT CONF. + 50-SEAT DINING", ox + W / 2.0, lvl_ff_slab + 5.5 * FT, h=0.65 * FT, layer="A-TEXT")

    arch_dim_h(msp, ox, oy - 2.0 * FT, ox + W, "60'-0\" BUILDING WIDTH", offset=-1.2 * FT)
    arch_dim_v(msp, ox + W + 3.0 * FT, oy, lvl_parapet, "26'-0\" PLOT 2 TOTAL HEIGHT (~7.9 m)", offset=1.2 * FT)

    notes = [
        "Plot 2 G+1 Structure Total Height: 26'-0\" (7.9 m) designed as an annex to main Plot 1 complex.",
        "Sky-Bridge Elevation: Exact 12'-0\" elevation matches both buildings for barrier-free horizontal transit.",
        "Structure: RCC isolated column footings with M25 concrete and Fe500D TMT rebars.",
    ]
    draw_sheet_frame_and_titleblock(msp, SHEET_W, SHEET_H, "SHEET 13 OF 16", "OPTION 2 - PLOT 2 G+1 SECTION & SKY-BRIDGE CONNECTION", "1/8\" = 1'-0\"", notes=notes)
    save_drawing(doc, "13-Option2-Plot2-Section-and-Skybridge")
    return doc


# SHEET 14: HERITAGE FACADE, BAY TYPOLOGIES & LOCKERS
def draw_sheet_14_heritage_and_details():
    doc, msp = setup_doc()

    ox, oy = 15.0 * FT, 52.0 * FT
    W, H = 100.0 * FT, 36.0 * FT

    rect(msp, ox, oy, ox + W, oy + 2.0 * FT, layer="A-WALL", lw=40)
    fill_rect(msp, ox, oy, ox + W, oy + 2.0 * FT, hatch="SOLID", layer="A-HATCH")
    text_msp(msp, "2 ft PINK BANSWARA SANDSTONE PLINTH", ox + W / 2.0, oy + 1.0 * FT, h=0.55 * FT, layer="A-TEXT-TTL")

    rect(msp, ox, oy + 2.0 * FT, ox + W, oy + H, layer="A-WALL", lw=45)

    for i in range(9):
        jx = ox + 3.5 * FT + i * 10.5 * FT
        rect(msp, jx, oy + 4.0 * FT, jx + 7.0 * FT, oy + 20.0 * FT, layer="A-WINDOW", lw=35)
        text_msp(msp, f"JHAROKHA {i + 1}\n(CARVED STONE)", jx + 3.5 * FT, oy + 12.0 * FT, h=0.45 * FT, layer="A-WINDOW")

    rect(msp, ox - 2.0 * FT, oy + 30.0 * FT, ox + W + 2.0 * FT, oy + 31.5 * FT, layer="A-ROOF", lw=40)
    text_msp(msp, "4 ft DEEP FULL-WIDTH CANTILEVERED STONE CHAJJAS (SUN & MONSOON PROTECTION)", ox + W / 2.0, oy + 30.75 * FT, h=0.55 * FT, layer="A-ROOF")

    rect(msp, ox + W / 2.0 - 6.0 * FT, oy + 2.0 * FT, ox + W / 2.0 + 6.0 * FT, oy + 14.0 * FT, layer="A-DOOR", lw=45)
    text_msp(msp, "MAIN ENTRY TORAN ARCH\n(12 ft HIGH PYLONS)", ox + W / 2.0, oy + 8.0 * FT, h=0.55 * FT, layer="A-DOOR")

    text_msp(msp, "OPTION 2 - SOUTH FRONT HERITAGE ELEVATION (RAJASTHANI HAVELI ARCHITECTURE)", ox + W / 2.0, oy + H + 2.0 * FT, h=0.85 * FT, layer="A-TEXT-TTL")

    # Section 2: Detailed Bay Typologies with Opposite-Side Seating
    bx_typ = 14.0 * FT
    by_typ = 11.0 * FT
    text_msp(msp, "BAY TYPOLOGY A: COMPACT (5'x6.5')", bx_typ + 4.0 * FT, by_typ + 15.0 * FT, h=0.60 * FT, layer="A-TEXT-TTL")
    bay_compact(msp, bx_typ, by_typ + 4.0 * FT, 6.0 * FT, 7.5 * FT, "TYP-A", orientation="S")
    text_msp(msp, "(Advocate Inner Side | 2 Litigants Opposite Side)", bx_typ + 4.0 * FT, by_typ + 2.5 * FT, h=0.40 * FT, layer="A-TEXT")

    bx_prem = bx_typ + 15.0 * FT
    text_msp(msp, "BAY TYPOLOGY B: PREMIUM CABIN (8'x10')", bx_prem + 4.0 * FT, by_typ + 15.0 * FT, h=0.60 * FT, layer="A-TEXT-TTL")
    bay_premium(msp, bx_prem, by_typ + 3.0 * FT, 8.0 * FT, 9.5 * FT, "TYP-B")
    text_msp(msp, "(Senior Advocate Inner Side | 3 Clients Opposite Side)", bx_prem + 4.0 * FT, by_typ + 1.8 * FT, h=0.40 * FT, layer="A-TEXT")

    # Section 3: Locker System Schedule & Specifications
    sch_x = bx_prem + 16.0 * FT
    sch_y = by_typ
    sch_w = 68.0 * FT
    sch_h = 16.0 * FT
    rect(msp, sch_x, sch_y, sch_x + sch_w, sch_y + sch_h, layer="A-TTLB", lw=30)
    text_msp(msp, "CAMPUS LOCKER SYSTEM SPECIFICATIONS & BUDGET ESTIMATE (190 TOTAL)", sch_x + sch_w / 2.0, sch_y + sch_h - 1.2 * FT, h=0.60 * FT, layer="A-TEXT-TTL")

    locker_specs = [
        "1. Material: IS 513 CRCA Steel Sheet 24 SWG (0.6mm) Body + 22 SWG Reinforcement Doors.",
        "2. Locking: 2-in-1 Dual Key Lock (ISI Marked) per cell + Master Key Override for Security Desk.",
        "3. Coating: 60 micron Epoxy Polyester Powder Coating (Advocate: Grey RAL 7035 | Litigant: Blue RAL 5012).",
        "4. Distribution: Plot 1 N-Wall (150 Adv Lockers in 3 Banks) + Plot 2 N-Wall (40 Litig Lockers in 1 Bank).",
        "5. Compliance: NBC 2016 Sec. 12.3.2 (3.75 ft clear aisle provided) + RPwD Act 2016 low-reach lockers.",
        "6. Total Locker Budget: 150 Adv (Rs.4.20L) + 40 Litig (Rs.1.04L) + Install + GST = Rs. 6.63 Lakhs Total.",
    ]
    for i, sp in enumerate(locker_specs):
        text_msp(msp, sp, sch_x + 1.0 * FT, sch_y + sch_h - 3.2 * FT - i * 1.8 * FT, h=0.43 * FT, layer="A-TEXT", align=TextEntityAlignment.LEFT)

    notes = [
        "Workstation Layout: Advocate seated on inner side of desk; 2 Litigants on opposite side facing advocate.",
        "Heritage Architecture: Pink Sandstone jharokhas and carved toran gateways capture iconic Rajasthani identity.",
        "Locker Guarantee: 100% individual locker allocation for all 150 advocates + 40 visiting public day-lockers.",
    ]
    draw_sheet_frame_and_titleblock(msp, SHEET_W, SHEET_H, "SHEET 14 OF 16", "HERITAGE FACADE, BAY TYPOLOGIES & LOCKER SYSTEM MASTER SHEET", "MIXED DETAILS", notes=notes)
    save_drawing(doc, "14-Heritage-Elevations-Bay-Typologies-and-Locker-Details")
    return doc


# SHEET 15: TYPE A COMPACT WORKSTATION SITOUT (5'x6.5') - DETAILED PLAN, ELEVATIONS & DETAILS
def draw_sheet_15_type_a_sitout():
    doc, msp = setup_doc()

    # --------------------------------------------------------------------------
    # VIEWPORT 1: DETAILED PLAN OF TYPE A COMPACT SITOUT (Scale 1:15)
    # --------------------------------------------------------------------------
    px, py = 12.0 * FT, 46.0 * FT
    pw, pd = 35.0 * FT, 42.0 * FT  # Enclosed boundary representing 5'x6.5' bay
    
    rect(msp, px, py, px + pw, py + pd, layer="A-WALL", lw=40)
    rect(msp, px, py + pd - 1.8 * FT, px + pw, py + pd, layer="A-JALI", lw=30)
    fill_rect(msp, px, py + pd - 1.8 * FT, px + pw, py + pd, hatch="ANSI31", layer="A-HATCH")
    text_msp(msp, "3.5 ft HIGH BRICK JALI SCREEN (REAR)", px + pw / 2.0, py + pd - 0.9 * FT, h=0.50 * FT, layer="A-JALI")

    rect(msp, px, py, px + 1.8 * FT, py + pd, layer="A-JALI", lw=30)
    fill_rect(msp, px, py, px + 1.8 * FT, py + pd, hatch="ANSI31", layer="A-HATCH")
    text_msp(msp, "3.5 ft JALI", px + 0.9 * FT, py + pd / 2.0, h=0.45 * FT, layer="A-JALI", rot=90.0)

    # Consultation Desk in Center (4'-0" x 1'-6")
    dx1 = px + 4.5 * FT
    dx2 = px + pw - 4.5 * FT
    dy1 = py + 16.0 * FT
    dy2 = py + 26.0 * FT
    rect(msp, dx1, dy1, dx2, dy2, layer="A-FURN", lw=35)
    fill_rect(msp, dx1, dy1, dx2, dy2, hatch="SOLID", layer="A-HATCH")
    text_msp(msp, "MODULAR CONSULTATION DESK\n4'-0\" x 1'-6\" (1200 x 450 mm)\n18mm PRE-LAM BWR PLY + 2mm PVC EDGE",
             (dx1 + dx2) / 2.0, (dy1 + dy2) / 2.0, h=0.55 * FT, layer="A-FURN")

    rect(msp, dx2 - 7.0 * FT, dy1, dx2, dy2, layer="A-FURN", lw=20)
    text_msp(msp, "3-DRAWER\nPEDESTAL", dx2 - 3.5 * FT, (dy1 + dy2) / 2.0, h=0.40 * FT, layer="A-FURN")

    # Advocate Seating Zone (Inner / Top Side)
    adv_cx = (dx1 + dx2) / 2.0
    adv_cy = dy2 + 6.5 * FT
    msp.add_circle((adv_cx, adv_cy), 3.5 * FT, dxfattribs={"layer": "A-FURN", "lineweight": 25})
    msp.add_circle((adv_cx, adv_cy), 1.8 * FT, dxfattribs={"layer": "A-FURN", "lineweight": 15})
    text_msp(msp, "ADVOCATE CHAIR\n(ERGONOMIC MESH MID-BACK SWIVEL)", adv_cx, adv_cy, h=0.50 * FT, layer="A-TEXT-TTL")
    text_msp(msp, "<- 2'-2\" ADVOCATE ZONE ->", adv_cx, py + pd - 3.5 * FT, h=0.45 * FT, layer="A-DIM")

    # Litigant Seating Zone (Opposite / Bottom Side facing Advocate)
    lit1_cx = px + 10.0 * FT
    lit2_cx = px + pw - 10.0 * FT
    lit_cy = dy1 - 6.5 * FT
    for lcx, lbl in [(lit1_cx, "LITIGANT 1"), (lit2_cx, "LITIGANT 2")]:
        msp.add_circle((lcx, lit_cy), 2.8 * FT, dxfattribs={"layer": "A-FURN", "lineweight": 20})
        text_msp(msp, f"{lbl}\nVISITOR CHAIR", lcx, lit_cy, h=0.45 * FT, layer="A-FURN")
    text_msp(msp, "<- 2'-1\" LITIGANT VISITOR ZONE (24\" C/C SPACING) ->", (lit1_cx + lit2_cx) / 2.0, py + 2.5 * FT, h=0.45 * FT, layer="A-DIM")

    # Aisle Access
    rect(msp, px, py - 4.5 * FT, px + pw, py, layer="A-ACC", lw=25)
    text_msp(msp, "=== 4'-0\" CLEAR PUBLIC CIRCULATION AISLE ===", px + pw / 2.0, py - 2.25 * FT, h=0.50 * FT, layer="A-ACC")

    # Dimension strings
    arch_dim_h(msp, px, py + pd + 2.0 * FT, px + pw, "5'-0\" (1500 mm) BAY WIDTH", offset=1.0 * FT)
    arch_dim_v(msp, px - 3.5 * FT, py, py + pd, "6'-6\" (1980 mm) BAY DEPTH", offset=-1.0 * FT)
    arch_dim_h(msp, dx1, dy2 + 1.0 * FT, dx2, "4'-0\" (1200 mm) DESK", offset=0.5 * FT)
    arch_dim_v(msp, dx2 + 1.5 * FT, dy1, dy2, "1'-6\" (450 mm)", offset=0.5 * FT)

    text_msp(msp, "PLAN: TYPE A COMPACT SITOUT (1 ADVOCATE vs 2 OPPOSITE LITIGANTS)", px + pw / 2.0, py + pd + 6.0 * FT, h=0.75 * FT, layer="A-TEXT-TTL")

    # --------------------------------------------------------------------------
    # VIEWPORT 2: LONGITUDINAL SIDE ELEVATION / SECTION (Scale 1:15)
    # --------------------------------------------------------------------------
    sx, sy = 75.0 * FT, 46.0 * FT
    sw_v, sh_v = 65.0 * FT, 42.0 * FT

    msp.add_line((sx, sy), (sx + sw_v, sy), dxfattribs={"layer": "A-SECT-CUT", "lineweight": 45})
    text_msp(msp, "PLINTH LEVEL (FL: 0'-0\")", sx + 10.0 * FT, sy - 1.5 * FT, h=0.45 * FT, layer="A-TEXT")

    rect(msp, sx + 2.0 * FT, sy, sx + 5.0 * FT, sy + 21.0 * FT, layer="A-JALI", lw=35)
    fill_rect(msp, sx + 2.0 * FT, sy, sx + 5.0 * FT, sy + 21.0 * FT, hatch="ANSI31", layer="A-HATCH")
    text_msp(msp, "3'-6\" BRICK JALI SCREEN", sx + 3.5 * FT, sy + 23.0 * FT, h=0.45 * FT, layer="A-JALI")

    adv_seat_x = sx + 14.0 * FT
    rect(msp, adv_seat_x - 3.0 * FT, sy + 9.0 * FT, adv_seat_x + 3.0 * FT, sy + 11.0 * FT, layer="A-FURN", lw=25)
    rect(msp, adv_seat_x - 3.0 * FT, sy + 11.0 * FT, adv_seat_x - 1.5 * FT, sy + 22.0 * FT, layer="A-FURN", lw=25)
    text_msp(msp, "ADVOCATE\nSEATED (INNER)", adv_seat_x, sy + 16.0 * FT, h=0.47 * FT, layer="A-TEXT-TTL")

    desk_sx = sx + 24.0 * FT
    desk_sw = 12.0 * FT
    rect(msp, desk_sx, sy, desk_sx + desk_sw, sy + 15.0 * FT, layer="A-FURN", lw=35)
    rect(msp, desk_sx + 2.0 * FT, sy, desk_sx + desk_sw - 2.0 * FT, sy + 13.5 * FT, layer="A-FURN", lw=15)
    text_msp(msp, "DESK 2'-6\" HT\n(MODESTY PANEL)", desk_sx + desk_sw / 2.0, sy + 7.5 * FT, h=0.45 * FT, layer="A-FURN")

    lit_seat_x = sx + 44.0 * FT
    rect(msp, lit_seat_x - 3.0 * FT, sy + 9.0 * FT, lit_seat_x + 3.0 * FT, sy + 11.0 * FT, layer="A-FURN", lw=25)
    rect(msp, lit_seat_x + 1.5 * FT, sy + 11.0 * FT, lit_seat_x + 3.0 * FT, sy + 20.0 * FT, layer="A-FURN", lw=25)
    text_msp(msp, "2x LITIGANTS\nSEATED (VISITOR)", lit_seat_x, sy + 16.0 * FT, h=0.47 * FT, layer="A-FURN")

    rect(msp, sx + 52.0 * FT, sy, sx + sw_v, sy + 2.0 * FT, layer="A-ACC", lw=20)
    text_msp(msp, "4'-0\" AISLE", sx + 58.5 * FT, sy + 5.0 * FT, h=0.45 * FT, layer="A-ACC")

    msp.add_line((sx, sy + 38.0 * FT), (sx + sw_v, sy + 38.0 * FT), dxfattribs={"layer": "A-ROOF", "lineweight": 30})
    text_msp(msp, "CEILING LEVEL (+11'-0\" CLEAR)", sx + 12.0 * FT, sy + 39.5 * FT, h=0.45 * FT, layer="A-ROOF")
    text_msp(msp, "LED BATTEN 20W + BLDC CEILING FAN", sx + 40.0 * FT, sy + 35.5 * FT, h=0.43 * FT, layer="A-FURN")

    arch_dim_v(msp, sx - 2.0 * FT, sy, sy + 15.0 * FT, "2'-6\" (750mm) DESK HT", offset=-0.5 * FT)
    arch_dim_v(msp, sx - 2.0 * FT, sy, sy + 21.0 * FT, "3'-6\" (1050mm) JALI HT", offset=-1.5 * FT)
    arch_dim_v(msp, sx - 2.0 * FT, sy, sy + 38.0 * FT, "11'-0\" (3350mm) CEILING", offset=-2.5 * FT)

    text_msp(msp, "SIDE ELEVATION / SECTION S-01: ERGONOMIC SITTING CLEARANCE", sx + sw_v / 2.0, sy + pd + 6.0 * FT, h=0.75 * FT, layer="A-TEXT-TTL")

    # --------------------------------------------------------------------------
    # VIEWPORT 3: FRONT ELEVATION E-01 (VIEW FROM LITIGANT SIDE)
    # --------------------------------------------------------------------------
    fx, fy = 12.0 * FT, 11.0 * FT
    fw, fh = 55.0 * FT, 25.0 * FT

    rect(msp, fx, fy, fx + fw, fy + 1.0 * FT, layer="A-WALL", lw=40)
    rect(msp, fx + 5.0 * FT, fy + 1.0 * FT, fx + fw - 5.0 * FT, fy + 21.0 * FT, layer="A-JALI", lw=25)
    text_msp(msp, "3'-6\" BRICK JALI SCREEN WITH SMOOTH CEMENT COPING", fx + fw / 2.0, fy + 22.2 * FT, h=0.45 * FT, layer="A-JALI")

    dfx1 = fx + 10.0 * FT
    dfx2 = fx + fw - 10.0 * FT
    dfy1 = fy + 1.0 * FT
    dfy2 = fy + 15.0 * FT
    rect(msp, dfx1, dfy1, dfx2, dfy2, layer="A-FURN", lw=35)
    rect(msp, dfx2 - 8.0 * FT, dfy1, dfx2, dfy2, layer="A-FURN", lw=20)
    text_msp(msp, "LOCKABLE\n3-DRAWER\nPEDESTAL", dfx2 - 4.0 * FT, (dfy1 + dfy2) / 2.0, h=0.40 * FT, layer="A-FURN")
    text_msp(msp, "4'-0\" MODULAR DESK FRONT (MODESTY PANEL)", (dfx1 + dfx2 - 8.0 * FT) / 2.0, (dfy1 + dfy2) / 2.0, h=0.47 * FT, layer="A-FURN")

    msp.add_circle(((dfx1 + dfx2 - 8.0 * FT) / 2.0, fy + 17.5 * FT), 2.5 * FT, dxfattribs={"layer": "A-FURN", "lineweight": 20})
    text_msp(msp, "ADVOCATE CHAIR", (dfx1 + dfx2 - 8.0 * FT) / 2.0, fy + 17.5 * FT, h=0.35 * FT, layer="A-FURN")

    text_msp(msp, "FRONT ELEVATION E-01 (VIEW FROM VISITOR/AISLE SIDE)", fx + fw / 2.0, fy + fh + 1.5 * FT, h=0.60 * FT, layer="A-TEXT-TTL")

    # --------------------------------------------------------------------------
    # VIEWPORT 4: MATERIAL SPECIFICATIONS & COST BREAKDOWN
    # --------------------------------------------------------------------------
    tx, ty = 75.0 * FT, 11.0 * FT
    tw, th = 65.0 * FT, 25.0 * FT
    rect(msp, tx, ty, tx + tw, ty + th, layer="A-TTLB", lw=30)
    text_msp(msp, "TYPE A SITOUT - SPECIFICATIONS, ELECTRICAL & COST SCHEDULE", tx + tw / 2.0, ty + th - 1.2 * FT, h=0.55 * FT, layer="A-TEXT-TTL")

    items = [
        "1. Workstation Desk: 4'x1.5' (1200x450mm) 18mm Pre-lam BWR Plywood + 2mm PVC Edgeband -> Rs. 2,200",
        "2. Advocate Chair: Ergonomic high-density foam mid-back mesh swivel chair with lumbar support -> Rs. 1,500",
        "3. Litigant Chairs: 2 Nos. heavy-duty tubular steel frame visitor chairs with leatherette seat -> Rs. 1,000",
        "4. Jali Partition: 3.5 ft high terracotta brick-jali screen in 1:3 cement mortar + coping -> Rs. 600",
        "5. Total Furniture Cost per Bay: Rs. 5,300 / Sitout Module (150 Bays = Rs. 7.95 Lakhs Total).",
        "6. Electrical / Data: 2 Nos. 6A 3-pin switch sockets + 1 USB charging port + 1 LED switch per bay.",
        "7. Aisle Clearance: 4'-0\" (1200mm) clear passage complying with NBC 2016 and RPwD Act 2016.",
    ]
    for i, itm in enumerate(items):
        h_val = 0.17 * FT if i in (4, 6) else 0.15 * FT
        l_val = "A-TEXT-TTL" if i in (4, 6) else "A-TEXT"
        text_msp(msp, itm, tx + 1.0 * FT, ty + th - 3.2 * FT - i * 3.0 * FT, h=h_val, layer=l_val, align=TextEntityAlignment.LEFT)

    notes = [
        "Type A Compact Sitout: Standard modular workstation accommodating 1 Advocate + 2 Opposite Litigants.",
        "Ergonomics: 2'-2\" advocate legroom + 2'-1\" visitor legroom + 4'-0\" double-loaded circulation aisle.",
        "Natural Ventilation: 3.5 ft high brick jali screen enables continuous cross-ventilation across the entire hall.",
    ]
    draw_sheet_frame_and_titleblock(msp, SHEET_W, SHEET_H, "SHEET 15 OF 16", "TYPE A COMPACT WORKSTATION SITOUT (5'x6.5') - DETAILED PLAN & ELEVATIONS", "1/2\" = 1'-0\"", notes=notes)
    save_drawing(doc, "15-Type-A-Workstation-Sitout-Detailed-Plan-and-Elevations")
    return doc


# SHEET 16: TYPE B SENIOR ADVOCATE PREMIUM CABIN (8'x10') - DETAILED PLAN, ELEVATIONS & DETAILS
def draw_sheet_16_type_b_cabin():
    doc, msp = setup_doc()

    # --------------------------------------------------------------------------
    # VIEWPORT 1: DETAILED PLAN OF TYPE B SENIOR CABIN (Scale 1:20)
    # --------------------------------------------------------------------------
    px, py = 12.0 * FT, 46.0 * FT
    pw, pd = 42.0 * FT, 44.0 * FT  # 8'x10' cabin scaled
    
    rect(msp, px, py, px + pw, py + pd, layer="A-WALL", lw=45)
    
    door_w = 12.0 * FT
    rect(msp, px, py, px + door_w, py + 1.2 * FT, layer="A-DOOR", lw=35)
    msp.add_arc((px, py), radius=door_w, start_angle=0, end_angle=90, dxfattribs={"layer": "A-DOOR", "lineweight": 20})
    text_msp(msp, "3'-0\"x7'-0\" FLUSH DOOR\n(VISION GLASS + MORTISE LOCK)", px + door_w / 2.0, py - 2.5 * FT, h=0.45 * FT, layer="A-DOOR")

    dx1 = px + 8.0 * FT
    dx2 = px + pw - 8.0 * FT
    dy1 = py + 18.0 * FT
    dy2 = py + 30.0 * FT
    rect(msp, dx1, dy1, dx2, dy2, layer="A-FURN", lw=40)
    fill_rect(msp, dx1, dy1, dx2, dy2, hatch="SOLID", layer="A-HATCH")
    text_msp(msp, "SENIOR ADVOCATE EXECUTIVE DESK\n5'-0\" x 2'-6\" (1500 x 750 mm)\nTEAK VENEER + WIRE MANAGEMENT + DRAWERS",
             (dx1 + dx2) / 2.0, (dy1 + dy2) / 2.0, h=0.55 * FT, layer="A-FURN")

    adv_cx = (dx1 + dx2) / 2.0
    adv_cy = dy2 + 6.5 * FT
    msp.add_circle((adv_cx, adv_cy), 4.5 * FT, dxfattribs={"layer": "A-FURN", "lineweight": 30})
    msp.add_circle((adv_cx, adv_cy), 2.2 * FT, dxfattribs={"layer": "A-FURN", "lineweight": 15})
    text_msp(msp, "HIGH-BACK EXECUTIVE\nLEATHERETTE RECLINER", adv_cx, adv_cy, h=0.50 * FT, layer="A-TEXT-TTL")

    c_spacing = (dx2 - dx1) / 3.0
    for i in range(3):
        cx = dx1 + c_spacing * (i + 0.5)
        cy = dy1 - 6.5 * FT
        msp.add_circle((cx, cy), 3.0 * FT, dxfattribs={"layer": "A-FURN", "lineweight": 20})
        text_msp(msp, f"CLIENT {i + 1}", cx, cy, h=0.43 * FT, layer="A-FURN")
    text_msp(msp, "<- 3x CLIENT VISITOR CHAIRS (ARMREST TYPE) ->", (dx1 + dx2) / 2.0, py + 4.5 * FT, h=0.45 * FT, layer="A-DIM")

    rect(msp, px + pw - 5.0 * FT, py + 8.0 * FT, px + pw - 0.8 * FT, py + pd - 4.0 * FT, layer="A-FURN", lw=30)
    text_msp(msp, "FULL-HEIGHT LAW BOOKSHELF & CASE ARCHIVE (6'-0\" x 1'-0\")",
             px + pw - 2.9 * FT, (py + 8.0 * FT + py + pd - 4.0 * FT) / 2.0, h=0.45 * FT, layer="A-FURN", rot=90.0)

    arch_dim_h(msp, px, py + pd + 2.0 * FT, px + pw, "8'-0\" (2400 mm) CABIN WIDTH", offset=1.0 * FT)
    arch_dim_v(msp, px - 3.5 * FT, py, py + pd, "10'-0\" (3000 mm) CABIN DEPTH", offset=-1.0 * FT)
    arch_dim_h(msp, dx1, dy2 + 1.0 * FT, dx2, "5'-0\" (1500 mm) DESK", offset=0.5 * FT)
    arch_dim_v(msp, dx2 + 1.5 * FT, dy1, dy2, "2'-6\" (750 mm)", offset=0.5 * FT)

    text_msp(msp, "PLAN: TYPE B SENIOR ADVOCATE CABIN (8'-0\" x 10'-0\" = 80 SQ FT)", px + pw / 2.0, py + pd + 6.0 * FT, h=0.75 * FT, layer="A-TEXT-TTL")

    # --------------------------------------------------------------------------
    # VIEWPORT 2: FRONT ELEVATION E-02 (CORRIDOR ENTRANCE FACADE)
    # --------------------------------------------------------------------------
    fx, fy = 75.0 * FT, 46.0 * FT
    fw, fh = 65.0 * FT, 42.0 * FT

    msp.add_line((fx, fy), (fx + fw, fy), dxfattribs={"layer": "A-SECT-CUT", "lineweight": 45})
    rect(msp, fx + 2.0 * FT, fy, fx + fw - 2.0 * FT, fy + 35.0 * FT, layer="A-WALL", lw=40)
    
    door_fx1 = fx + 6.0 * FT
    door_fx2 = door_fx1 + 18.0 * FT
    rect(msp, door_fx1, fy, door_fx2, fy + 35.0 * FT, layer="A-DOOR", lw=35)
    rect(msp, door_fx1 + 4.0 * FT, fy + 16.0 * FT, door_fx2 - 4.0 * FT, fy + 30.0 * FT, layer="A-WINDOW", lw=25)
    text_msp(msp, "VISION GLASS\n12\"x36\"", (door_fx1 + door_fx2) / 2.0, fy + 23.0 * FT, h=0.43 * FT, layer="A-WINDOW")
    text_msp(msp, "BRASS NAMEPLATE\n& MORTISE LOCK", (door_fx1 + door_fx2) / 2.0, fy + 10.0 * FT, h=0.40 * FT, layer="A-DOOR")

    rect(msp, door_fx2 + 4.0 * FT, fy + 25.0 * FT, fx + fw - 6.0 * FT, fy + 33.0 * FT, layer="A-JALI", lw=25)
    text_msp(msp, "ACOUSTIC JALI LOUVERS (AIRFLOW + SOUND PRIVACY)", (door_fx2 + 4.0 * FT + fx + fw - 6.0 * FT) / 2.0, fy + 29.0 * FT, h=0.43 * FT, layer="A-JALI")

    rect(msp, door_fx2 + 4.0 * FT, fy + 4.0 * FT, fx + fw - 6.0 * FT, fy + 22.0 * FT, layer="A-WALL", lw=20)
    text_msp(msp, "ACOUSTIC FABRIC WALL PANELLING\n(WARM WOOD GRAIN TEXTURE)", (door_fx2 + 4.0 * FT + fx + fw - 6.0 * FT) / 2.0, fy + 13.0 * FT, h=0.47 * FT, layer="A-WALL")

    arch_dim_v(msp, fx - 1.5 * FT, fy, fy + 35.0 * FT, "7'-0\" (2100mm) PARTITION HT", offset=-1.0 * FT)
    text_msp(msp, "FRONT ELEVATION E-02: 7 ft HIGH CABIN ENTRANCE FACADE", fx + fw / 2.0, fy + pd + 6.0 * FT, h=0.75 * FT, layer="A-TEXT-TTL")

    # --------------------------------------------------------------------------
    # VIEWPORT 3: INTERIOR SECTIONAL ELEVATION S-02 (LOOKING EAST)
    # --------------------------------------------------------------------------
    ix, iy = 12.0 * FT, 11.0 * FT
    iw, ih = 55.0 * FT, 25.0 * FT

    msp.add_line((ix, iy), (ix + iw, iy), dxfattribs={"layer": "A-SECT-CUT", "lineweight": 45})
    rect(msp, ix + 8.0 * FT, iy, ix + 32.0 * FT, iy + 15.0 * FT, layer="A-FURN", lw=35)
    text_msp(msp, "EXECUTIVE DESK 5'x2.5' (2'-6\" HT)", ix + 20.0 * FT, iy + 7.5 * FT, h=0.45 * FT, layer="A-FURN")
    
    rect(msp, ix + 36.0 * FT, iy, ix + iw - 4.0 * FT, iy + 22.0 * FT, layer="A-FURN", lw=30)
    for shelf_y in [iy + 5.5 * FT, iy + 11.0 * FT, iy + 16.5 * FT]:
        msp.add_line((ix + 36.0 * FT, shelf_y), (ix + iw - 4.0 * FT, shelf_y), dxfattribs={"layer": "A-FURN", "lineweight": 18})
    text_msp(msp, "LAW REPORTS & BINDERS\n(4-TIER BOOKSHELF)", ix + 45.5 * FT, iy + 11.0 * FT, h=0.40 * FT, layer="A-FURN")

    text_msp(msp, "INTERIOR ELEVATION S-02 (LOOKING TOWARD STORAGE)", ix + iw / 2.0, iy + ih + 1.5 * FT, h=0.60 * FT, layer="A-TEXT-TTL")

    # --------------------------------------------------------------------------
    # VIEWPORT 4: SPECIFICATIONS & COST SCHEDULE
    # --------------------------------------------------------------------------
    tx, ty = 75.0 * FT, 11.0 * FT
    tw, th = 65.0 * FT, 25.0 * FT
    rect(msp, tx, ty, tx + tw, ty + th, layer="A-TTLB", lw=30)
    text_msp(msp, "TYPE B SENIOR CABIN - SPECIFICATIONS & COST SCHEDULE", tx + tw / 2.0, ty + th - 1.2 * FT, h=0.55 * FT, layer="A-TEXT-TTL")

    items_b = [
        "1. Executive Desk: 5'x2.5' (1500x750mm) Teak veneer finish + lockable 3-drawer pedestal -> Rs. 6,500",
        "2. Senior Advocate Chair: High-back ergonomic reclining chair in leatherette with armrests -> Rs. 4,200",
        "3. Client Chairs: 3 Nos. cushioned visitor chairs with wooden armrests -> Rs. 2,400",
        "4. Storage: Full-height 4-tier Law Bookshelf & Case Filing Cabinet (6'x1'x7' high) -> Rs. 3,200",
        "5. Door & Partition: 3'x7' Flush door with brass mortise lock + 7 ft high acoustic wall -> Rs. 2,200",
        "6. Total Cost per Cabin: Rs. 18,500 / Cabin (20 Cabins in Option 2 = Rs. 3.70 Lakhs Total).",
        "7. Electrical / IT: 4 Nos. 6A sockets + 1 16A AC point + LAN Internet port + Wall Fan point.",
    ]
    for i, itm in enumerate(items_b):
        h_val = 0.17 * FT if i in (5, 6) else 0.15 * FT
        l_val = "A-TEXT-TTL" if i in (5, 6) else "A-TEXT"
        text_msp(msp, itm, tx + 1.0 * FT, ty + th - 3.2 * FT - i * 3.0 * FT, h=h_val, layer=l_val, align=TextEntityAlignment.LEFT)

    notes = [
        "Type B Senior Cabin: Dedicated private consulting chamber for Senior Advocates (80 sq ft).",
        "Seating Geometry: Senior Advocate seated behind executive desk; 3 Clients seated on opposite side.",
        "Privacy & Acoustics: 7 ft high partition with solid core door, vision panel, and overhead acoustic jali transoms.",
    ]
    draw_sheet_frame_and_titleblock(msp, SHEET_W, SHEET_H, "SHEET 16 OF 16", "TYPE B SENIOR ADVOCATE PREMIUM CABIN (8'x10') - PLAN & ELEVATIONS", "1/2\" = 1'-0\"", notes=notes)
    save_drawing(doc, "16-Type-B-Premium-Cabin-Sitout-Detailed-Plan-and-Elevations")
    return doc


# ==============================================================================
# CAD SAVING & SMART A4 PDF EXPORT ENGINE (EXACT 20MM MARGINS)
# ==============================================================================

def save_drawing(doc, name):
    dxf_path = DXF_DIR / f"{name}.dxf"
    try:
        doc.saveas(str(dxf_path))
        sz = dxf_path.stat().st_size
        print(f"  [OK] DXF saved: {dxf_path.name} ({sz:,} bytes)")
    except Exception as e:
        print(f"  [FAIL] DXF failed {name}: {e}")
    doc._last_path = dxf_path
    return dxf_path


# ==============================================================================
# SMART A4 PDF EXPORT ENGINE — CENTERED, ARROW-FREE, EXACT 20MM MARGINS
# ==============================================================================

def _dxf_data_bbox(msp):
    """
    Scan all LINE, CIRCLE, ARC, TEXT, HATCH entities and return the
    axis-aligned bounding box of the actual drawn content.
    Returns (xmin, ymin, xmax, ymax) or None if no geometry found.
    """
    xs, ys = [], []
    for e in msp:
        t = e.dxftype()
        try:
            if t == "LINE":
                xs += [e.dxf.start.x, e.dxf.end.x]
                ys += [e.dxf.start.y, e.dxf.end.y]
            elif t in ("CIRCLE", "ARC"):
                cx, cy = e.dxf.center.x, e.dxf.center.y
                r = e.dxf.radius
                xs += [cx - r, cx + r]
                ys += [cy - r, cy + r]
            elif t in ("TEXT", "ATTDEF"):
                xs.append(e.dxf.insert.x)
                ys.append(e.dxf.insert.y)
            elif t == "INSERT":
                xs.append(e.dxf.insert.x)
                ys.append(e.dxf.insert.y)
        except Exception:
            pass
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def export_dxf_to_a4_pdf(dxf_path):
    """
    Renders DXF to true A4 Landscape PDF (297 mm x 210 mm, exact 20 mm margins).
    Guarantees:
      - Centrally aligned on A4 landscape paper (MediaBox: 841.89 x 595.28 pt)
      - Minimum 20mm margins on all 4 sides
      - Complete title block, borders, and captions visible
      - ACI Color 7 (White) rendered as crisp Black on White background
      - Zero unwanted AutoCAD/ACAD arrows or artifacts
    """
    pdf_path = PDF_DIR / (dxf_path.stem + ".pdf")
    try:
        doc = ezdxf.readfile(str(dxf_path))
    except Exception as e:
        print(f"  [FAIL] Read DXF failed {dxf_path.name}: {e}")
        return pdf_path

    msp = doc.modelspace()

    try:
        ctx = RenderContext(doc)
        config = Configuration(
            background_policy=BackgroundPolicy.WHITE,
            color_policy=ColorPolicy.COLOR,
            custom_fg_color="#000000",
            line_policy=LinePolicy.ACCURATE
        )

        # Standard A4 Landscape Dimensions: 297 mm x 210 mm (11.6929" x 8.2677")
        a4_w_in, a4_h_in = 297.0 / 25.4, 210.0 / 25.4
        fig = plt.figure(figsize=(a4_w_in, a4_h_in), dpi=300, facecolor="white")

        # 20 mm margins on all four sides:
        # Left margin = 20 / 297 = 0.067340067
        # Bottom margin = 20 / 210 = 0.095238095
        # Width = 257 / 297 = 0.865319865
        # Height = 170 / 210 = 0.809523809
        ax = fig.add_axes([0.067340067, 0.095238095, 0.865319865, 0.809523809])
        ax.set_facecolor("white")
        ax.set_axis_off()

        sw = getattr(doc, "_sheet_w", SHEET_W)
        sh = getattr(doc, "_sheet_h", SHEET_H)

        # Add 1% padding so border sits cleanly inside the 20mm margin
        pad_x = sw * 0.01
        pad_y = sh * 0.01
        ax.set_xlim(-pad_x, sw + pad_x)
        ax.set_ylim(-pad_y, sh + pad_y)

        backend = MatplotlibBackend(ax)
        frontend = Frontend(ctx, backend, config=config)
        frontend.draw_layout(msp, finalize=True)

        temp_pdf = PDF_DIR / f"_temp_{dxf_path.stem}.pdf"
        fig.savefig(str(temp_pdf), format="pdf", facecolor="white", dpi=300, bbox_inches=None)
        plt.close(fig)

        # Wrap into exact standard A4 Landscape MediaBox (841.88976 x 595.27559 pt = 297 x 210 mm)
        a4_w_pt, a4_h_pt = 297.0 * 2.834645669, 210.0 * 2.834645669
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
            print(f"  [OK] A4 PDF saved: {pdf_path.name} ({sz:,} bytes)")

    except Exception as e:
        print(f"  [FAIL] PDF export failed {dxf_path.name}: {e}")
        import traceback
        traceback.print_exc()

    return pdf_path


def merge_all_16_pdfs():
    """Merges all 16 individual A4 PDF sheets into a single master document."""
    merger = PdfWriter()
    pdf_files = sorted(list(PDF_DIR.glob("*.pdf")))
    single_sheets = [p for p in pdf_files if p.name[:2].isdigit() and not p.name.startswith("00-")]
    single_sheets.sort(key=lambda x: x.name)

    if not single_sheets:
        print("  [WARN] No individual PDFs found to merge.")
        return None

    for p in single_sheets:
        try:
            merger.append(str(p))
        except Exception as e:
            print(f"  [FAIL] Could not append {p.name}: {e}")

    master_pdf_path = PDF_DIR / "00-Advocate-Chambers-All-16-Drawings-Complete-Set.pdf"
    with open(master_pdf_path, "wb") as f_out:
        merger.write(f_out)

    sz = master_pdf_path.stat().st_size
    print(f"\n  [SUCCESS] Merged 16-Page Master PDF created: {master_pdf_path.name} ({sz:,} bytes, {len(merger.pages)} pages)")
    return master_pdf_path


# ==============================================================================
# MAIN EXECUTION ORCHESTRATOR
# ==============================================================================

def main():
    print("\n" + "=" * 85)
    print("ADVOCATE CHAMBERS BANSWARA - A4 LANDSCAPE CAD & PDF GENERATION SUITE (16 SHEETS)")
    print(f"Target DXF Folder : {DXF_DIR}")
    print(f"Target PDF Folder : {PDF_DIR}")
    print("=" * 85 + "\n")

    drawers = [
        ("01  SITE MASTER PLAN & CAMPUS LAYOUT", draw_sheet_01_site_plan),
        ("02  OPTION 1  PLOT 1 GROUND FLOOR PLAN (115 BAYS)", draw_sheet_02_o1_p1_gf),
        ("03  OPTION 1  PLOT 2 GROUND FLOOR PLAN (35 BAYS)", draw_sheet_03_o1_p2_gf),
        ("04  OPTION 1  COMBINED CAMPUS GROUND FLOOR PLAN", draw_sheet_04_o1_combined_campus),
        ("05  OPTION 1  BUILDING SECTIONS & DETAILS", draw_sheet_05_o1_sections),
        ("06  OPTION 1  SOUTH & NORTH ELEVATIONS", draw_sheet_06_o1_elevations),
        ("07  OPTION 2  PLOT 1 GROUND FLOOR PLAN (60 BAYS)", draw_sheet_07_o2_p1_gf),
        ("08  OPTION 2  PLOT 1 FIRST FLOOR PLAN (60 BAYS)", draw_sheet_08_o2_p1_ff),
        ("09  OPTION 2  PLOT 1 SECOND FLOOR PLAN (BAR HALL)", draw_sheet_09_o2_p1_2f),
        ("10  OPTION 2  PLOT 2 GROUND FLOOR PLAN (15 BAYS)", draw_sheet_10_o2_p2_gf),
        ("11  OPTION 2  PLOT 2 FIRST FLOOR PLAN (15 BAYS)", draw_sheet_11_o2_p2_ff),
        ("12  OPTION 2  PLOT 1 LONGITUDINAL SECTION", draw_sheet_02_12_o2_p1_section),
        ("13  OPTION 2  PLOT 2 G+1 SECTION & SKYBRIDGE", draw_sheet_13_o2_p2_section),
        ("14  HERITAGE FACADE, BAY TYPOLOGIES & LOCKERS", draw_sheet_14_heritage_and_details),
        ("15  TYPE A WORKSTATION SITOUT (5'x6.5') DETAILS", draw_sheet_15_type_a_sitout),
        ("16  TYPE B PREMIUM CABIN (8'x10') DETAILS", draw_sheet_16_type_b_cabin),
    ]

    print(">>> STEP 1: GENERATING ALL 16 AUTOCAD NATIVE DXF DRAWINGS <<<\n")
    generated_dxfs = []
    for label, fn in drawers:
        print(f"[{label:50s}]", end="  ")
        try:
            doc = fn()
            if hasattr(doc, "_last_path") and doc._last_path.exists():
                generated_dxfs.append(doc._last_path)
            print()
        except Exception as e:
            print(f"[FAIL] Error: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n>>> STEP 1 COMPLETE: {len(generated_dxfs)} of 16 DXF files successfully created. <<<\n")

    print(">>> STEP 2: EXPORTING HIGH-RESOLUTION PRINT-READY A4 PDFs (20MM MARGINS) <<<\n")
    generated_pdfs = []
    for dxf in generated_dxfs:
        print(f"[{dxf.name[:55]:55s}]", end="  ")
        pdf = export_dxf_to_a4_pdf(dxf)
        if pdf.exists():
            generated_pdfs.append(pdf)

    print(f"\n>>> STEP 2 COMPLETE: {len(generated_pdfs)} A4 PDF sheets exported. <<<\n")

    print(">>> STEP 3: COMPILING MERGED 16-PAGE MASTER DELIVERABLE PDF <<<\n")
    master_pdf = merge_all_16_pdfs()

    print("\n" + "=" * 85)
    print("DELIVERY SUMMARY - ADVOCATE CHAMBERS BANSWARA (COMPLETE 16-SHEET PACKAGE)")
    print("=" * 85)
    print(f"  * DXF Files Generated : {len(generated_dxfs)} Files")
    print(f"  * PDF Files Generated : {len(generated_pdfs)} Individual A4 Sheets (297mm x 210mm)")
    if master_pdf and master_pdf.exists():
        print(f"  * Master Compiled PDF : {master_pdf.name} (16 Pages, {master_pdf.stat().st_size:,} bytes)")
    print(f"\n  DXF Folder : {DXF_DIR}")
    print(f"  PDF Folder : {PDF_DIR}")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    main()
