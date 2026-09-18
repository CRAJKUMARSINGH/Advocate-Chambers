"""
BAR ASSOCIATION HALL, BANSWARA — LUMION-GRADE PROFESSIONAL ARCHITECTURAL DRAWINGS
====================================================================================
Produces 3 drawing sets, 2 floors each = 6 sheets + 1 cover = 7-page master PDF.

SET 1  — ARCHITECTURAL FLOOR PLAN (WITHOUT FURNITURE)
        A-101  Ground Floor  |  A-102  First Floor

SET 2  — PRESENTATION FLOOR PLAN (WITH FURNITURE & FURNISHINGS)
        A-201  Ground Floor  |  A-202  First Floor

SET 3  — STRUCTURAL COLUMN & GRID COORDINATION PLAN (WITH COLUMNS)
        S-101  Ground Floor  |  S-102  First Floor

Source:  standard/source/site_plan.json
         standard/source/preliminary_plans.json

Approved concept drawings: bar-association-hall/approved concept/
  A-101-Ground-Floor-Plan.pdf
  A-102-First-Floor-Plan.pdf
  Bar-Association-Standard-Review-Set.pdf

Design directives:
  • Main entrance on EAST LONG WALL with 12'-0" × 8'-0" covered porch
  • Windows on ALL FOUR SIDES (North, South, East, West)
  • RCC framed structure, column grid coordinated with approved concept
  • 4,427.50 sq ft per floor (setback envelope)
  • Paper: A2 landscape @ 1/8" = 1'-0"
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import os as _os

# ── Patch ezdxf font_manager to skip corrupt font files ──────────────────────
# (Needed because some Windows system fonts are malformed and cause TTLibError)
def _patch_ezdxf_font_manager():
    try:
        from fontTools.ttLib import TTFont
        import ezdxf.fonts.font_manager as _fm
        _orig_get = _fm.get_ttf_font_face

        def _safe_get(file):
            try:
                return _orig_get(file)
            except Exception:
                return None

        _fm.get_ttf_font_face = _safe_get

        _orig_scan = _fm.FontManager.scan_folder

        def _safe_scan(self, folder):
            try:
                _orig_scan(self, folder)
            except Exception:
                pass

        _fm.FontManager.scan_folder = _safe_scan
    except Exception:
        pass

_patch_ezdxf_font_manager()

import ezdxf
from ezdxf import units as dxf_units
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A2, landscape
from reportlab.pdfgen import canvas

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "standard" / "source"
PDF_OUT = ROOT / "PDF"
CAD_OUT = ROOT / "CAD"
PDF_OUT.mkdir(exist_ok=True)
CAD_OUT.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Page & Scale
# ─────────────────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = landscape(A2)
# 1/8" = 1'-0"  →  SCALE = (1/8) / (1/72)  = 72/8 = 9 pt per foot
# In the model, coordinates are in inches.  At 1/8" scale: 1 inch model = 1/8 pt… no.
# At 1/8"=1'-0", 1 foot = 1/8 inch on paper = 9 pt (72 pt/in × 1/8 in/ft)
# 1 model-inch = (1/12) foot → (1/12) × 9 = 0.75 pt
SCALE = 0.75   # pt per model-inch

# ─────────────────────────────────────────────────────────────────────────────
# Lumion-grade Architectural Colour Palette
# ─────────────────────────────────────────────────────────────────────────────
BLACK        = colors.HexColor("#0d1117")
CHARCOAL     = colors.HexColor("#1e293b")
DARK_GRAY    = colors.HexColor("#334155")
GRAY         = colors.HexColor("#64748b")
LIGHT_GRAY   = colors.HexColor("#cbd5e1")
PALE_BG      = colors.HexColor("#f8fafc")
PALE_PANEL   = colors.HexColor("#f1f5f9")

# Wall cut = dense graphite
WALL_HATCH   = colors.HexColor("#1e293b")
WALL_STROKE  = colors.HexColor("#0d1117")
WALL_THICK   = 2.8   # pt outer perimeter
PART_THICK   = 1.6   # pt partition

# Zone fills
FILL_PUBLIC       = colors.HexColor("#fefce8")   # warm cream – assembly / library
FILL_SERVICE      = colors.HexColor("#eff6ff")   # cool blue  – pantry / toilet / store
FILL_CIRCULATION  = colors.HexColor("#faf5ff")   # soft lavender – stair / lobby
FILL_DAIS         = colors.HexColor("#fff7ed")   # warm amber – dais / stage
FILL_READING      = colors.HexColor("#f0fdf4")   # green tint – reading / study

ACCENT_BLUE  = colors.HexColor("#0284c7")
GLASS_BLUE   = colors.HexColor("#38bdf8")
GLASS_FILL   = colors.HexColor("#e0f2fe")
DOOR_RED     = colors.HexColor("#b91c1c")
DOOR_FILL    = colors.HexColor("#fee2e2")
PORCH_AMBER  = colors.HexColor("#d97706")
PORCH_FILL   = colors.HexColor("#fffbeb")
GRID_RED     = colors.HexColor("#dc2626")
GRID_ALPHA   = colors.HexColor("#fef2f2")

FURN_STROKE  = colors.HexColor("#475569")
FURN_FILL    = colors.HexColor("#e2e8f0")
FURN_SEAT    = colors.HexColor("#bfdbfe")
FURN_WOOD    = colors.HexColor("#d97706")
FURN_FABRIC  = colors.HexColor("#818cf8")

COL_FILL     = colors.HexColor("#1e293b")
COL_STROKE   = colors.HexColor("#0f172a")
COL_HATCH    = colors.HexColor("#94a3b8")

# ─────────────────────────────────────────────────────────────────────────────
# Column definitions (model coordinates, inches)
# ─────────────────────────────────────────────────────────────────────────────
COLUMNS_GF = [
    # Grid A – West perimeter (x=6)
    {"id":"C-01","x":6,  "y":6,    "w":12,"h":18,"desc":"SW Corner"},
    {"id":"C-02","x":6,  "y":180,  "w":12,"h":18,"desc":"Reception NW"},
    {"id":"C-03","x":6,  "y":252,  "w":12,"h":24,"desc":"Hall SW"},
    {"id":"C-04","x":6,  "y":468,  "w":12,"h":24,"desc":"Hall W-mid 1"},
    {"id":"C-05","x":6,  "y":684,  "w":12,"h":24,"desc":"Hall W-mid 2"},
    {"id":"C-06","x":6,  "y":900,  "w":12,"h":24,"desc":"Dais Proscenium W"},
    {"id":"C-07","x":6,  "y":1080, "w":12,"h":18,"desc":"Dais NW"},
    # Grid B – Service core W (x=132)
    {"id":"C-08","x":132,"y":6,    "w":12,"h":18,"desc":"Reception E / Stair S"},
    {"id":"C-09","x":132,"y":246,  "w":12,"h":18,"desc":"Stair NW"},
    # Grid C – Service core mid (x=276)
    {"id":"C-10","x":276,"y":6,    "w":12,"h":18,"desc":"Stair/Pantry S"},
    {"id":"C-11","x":276,"y":246,  "w":12,"h":18,"desc":"Stair NE"},
    # Grid D – Pantry-Toilet partition (x=408)
    {"id":"C-12","x":408,"y":6,    "w":12,"h":18,"desc":"Pantry E / Toilet W S"},
    {"id":"C-13","x":408,"y":204,  "w":12,"h":18,"desc":"Toilet NW"},
    # Grid E – Toilet east (x=516)
    {"id":"C-14","x":516,"y":6,    "w":12,"h":18,"desc":"Toilet SE"},
    {"id":"C-15","x":516,"y":204,  "w":12,"h":18,"desc":"Toilet NE"},
    # Grid F – East perimeter (x=666)
    {"id":"C-16","x":666,"y":252,  "w":12,"h":24,"desc":"Hall SE"},
    {"id":"C-17","x":666,"y":372,  "w":12,"h":24,"desc":"Porch S-anchor"},
    {"id":"C-18","x":666,"y":480,  "w":12,"h":24,"desc":"Porch N-anchor"},
    {"id":"C-19","x":666,"y":684,  "w":12,"h":24,"desc":"Hall E-mid 2"},
    {"id":"C-20","x":666,"y":900,  "w":12,"h":24,"desc":"Dais Proscenium E"},
    {"id":"C-21","x":666,"y":1080, "w":12,"h":18,"desc":"Dais NE"},
    # Porch canopy posts (x=762)
    {"id":"C-P1","x":762,"y":342,  "w":12,"h":12,"desc":"Porch post S"},
    {"id":"C-P2","x":762,"y":486,  "w":12,"h":12,"desc":"Porch post N"},
]

COLUMNS_FF = [
    {"id":"C-01","x":6,  "y":6,    "w":12,"h":18,"desc":"Admin SW"},
    {"id":"C-02","x":6,  "y":180,  "w":12,"h":18,"desc":"Admin NW"},
    {"id":"C-03","x":6,  "y":252,  "w":12,"h":24,"desc":"Reading SW"},
    {"id":"C-04","x":6,  "y":468,  "w":12,"h":24,"desc":"Reading W-mid 1"},
    {"id":"C-05","x":6,  "y":684,  "w":12,"h":24,"desc":"Reading W-mid 2"},
    {"id":"C-06","x":6,  "y":774,  "w":12,"h":24,"desc":"Stack SW"},
    {"id":"C-07","x":6,  "y":996,  "w":12,"h":18,"desc":"Rooms SW"},
    {"id":"C-08","x":6,  "y":1122, "w":12,"h":18,"desc":"NW corner"},
    {"id":"C-09","x":132,"y":6,    "w":12,"h":18,"desc":"Admin E / Stair S"},
    {"id":"C-10","x":132,"y":246,  "w":12,"h":18,"desc":"Stair NW"},
    {"id":"C-11","x":276,"y":6,    "w":12,"h":18,"desc":"Stair-Pantry S"},
    {"id":"C-12","x":276,"y":246,  "w":12,"h":18,"desc":"Stair NE"},
    {"id":"C-13","x":408,"y":6,    "w":12,"h":18,"desc":"Pantry-Toilet S"},
    {"id":"C-14","x":408,"y":204,  "w":12,"h":18,"desc":"Toilet NW"},
    {"id":"C-15","x":516,"y":6,    "w":12,"h":18,"desc":"Toilet SE"},
    {"id":"C-16","x":516,"y":204,  "w":12,"h":18,"desc":"Toilet NE"},
    {"id":"C-17","x":666,"y":252,  "w":12,"h":24,"desc":"Reading SE"},
    {"id":"C-18","x":666,"y":468,  "w":12,"h":24,"desc":"Reading E-mid 1"},
    {"id":"C-19","x":666,"y":684,  "w":12,"h":24,"desc":"Reading E-mid 2"},
    {"id":"C-20","x":666,"y":774,  "w":12,"h":24,"desc":"Stack SE"},
    {"id":"C-21","x":666,"y":996,  "w":12,"h":18,"desc":"Rooms SE"},
    {"id":"C-22","x":666,"y":1122, "w":12,"h":18,"desc":"NE corner"},
    {"id":"C-23","x":228,"y":1122, "w":12,"h":18,"desc":"Disc-Comp N"},
    {"id":"C-24","x":444,"y":1122, "w":12,"h":18,"desc":"Comp-Store N"},
]

# ─────────────────────────────────────────────────────────────────────────────
# Geometry helpers
# ─────────────────────────────────────────────────────────────────────────────
def pp(origin: tuple[float, float], x: float, y: float) -> tuple[float, float]:
    """Convert model (inches) → PDF points."""
    return origin[0] + x * SCALE, origin[1] + y * SCALE


def rect(space: dict) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = (float(v) for v in space["rect"])
    return x0, y0, x1, y1


def sqft(space: dict) -> float:
    x0, y0, x1, y1 = rect(space)
    return abs(x1 - x0) * abs(y1 - y0) / 144.0


def fmtft(inches: float) -> str:
    ft = int(inches // 12)
    inc = round(inches - ft * 12)
    if inc == 12:
        ft += 1; inc = 0
    return f"{ft}'-{inc}\""


def wall_pts(space: dict, wall: str, offset: float, width: float):
    x0, y0, x1, y1 = rect(space)
    if wall == "south":  return (x0+offset, y0), (x0+offset+width, y0)
    if wall == "north":  return (x0+offset, y1), (x0+offset+width, y1)
    if wall == "west":   return (x0, y0+offset), (x0, y0+offset+width)
    return (x1, y0+offset), (x1, y0+offset+width)


# ─────────────────────────────────────────────────────────────────────────────
# Arrow helper
# ─────────────────────────────────────────────────────────────────────────────
def arrow(c: canvas.Canvas, x: float, y: float, angle: float, size: float = 6) -> None:
    c.saveState()
    c.translate(x, y)
    c.rotate(math.degrees(angle))
    p = c.beginPath()
    p.moveTo(0, 0); p.lineTo(-size, size/2); p.lineTo(-size, -size/2); p.close()
    c.setFillColor(CHARCOAL); c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Dimension Line
# ─────────────────────────────────────────────────────────────────────────────
def draw_dim(c, origin, a_model, b_model, off, label):
    ax, ay = pp(origin, *a_model)
    bx, by = pp(origin, *b_model)
    c.saveState()
    c.setStrokeColor(DARK_GRAY); c.setLineWidth(0.55)
    if abs(bx-ax) >= abs(by-ay):  # horizontal
        oy = min(ay, by) + off[1]
        c.line(ax, ay, ax, oy); c.line(bx, by, bx, oy); c.line(ax, oy, bx, oy)
        arrow(c, ax, oy, 0, 5); arrow(c, bx, oy, math.pi, 5)
        tx, ty = (ax+bx)/2, oy+7
    else:  # vertical
        ox = min(ax, bx) + off[0]
        c.line(ax, ay, ox, ay); c.line(bx, by, ox, by); c.line(ox, ay, ox, by)
        arrow(c, ox, ay, math.pi/2, 5); arrow(c, ox, by, -math.pi/2, 5)
        tx, ty = ox-15, (ay+by)/2
    c.setFillColor(DARK_GRAY); c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(tx, ty, label)
    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# North Rose
# ─────────────────────────────────────────────────────────────────────────────
def draw_north(c, cx, cy):
    c.saveState()
    c.setStrokeColor(BLACK); c.setFillColor(BLACK)
    c.setLineWidth(1.2)
    c.circle(cx, cy, 20, stroke=1, fill=0)
    # North half — filled black
    p1 = c.beginPath()
    p1.moveTo(cx, cy+20); p1.lineTo(cx-7, cy); p1.lineTo(cx, cy-20); p1.close()
    c.setFillColor(BLACK); c.drawPath(p1, fill=1, stroke=0)
    # South half — white outline
    p2 = c.beginPath()
    p2.moveTo(cx, cy+20); p2.lineTo(cx+7, cy); p2.lineTo(cx, cy-20); p2.close()
    c.setFillColor(LIGHT_GRAY); c.drawPath(p2, fill=1, stroke=0)
    c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(cx, cy+26, "N")
    c.setFont("Helvetica", 6); c.setFillColor(GRAY)
    c.drawCentredString(cx, cy-32, "PROJECT NORTH")
    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Graphic Scale Bar
# ─────────────────────────────────────────────────────────────────────────────
def draw_scale_bar(c, x, y):
    c.saveState()
    c.setFont("Helvetica-Bold", 7); c.setFillColor(DARK_GRAY)
    c.drawString(x, y+16, 'GRAPHIC SCALE  1/8" = 1\'-0"')
    ft_pt = 12 * SCALE
    segs = [0, 5, 10, 20, 30, 40]
    total = 40 * ft_pt
    c.setStrokeColor(BLACK); c.setLineWidth(0.8)
    c.rect(x, y, total, 5, stroke=1, fill=0)
    for i, seg in enumerate(segs[:-1]):
        seg_x = x + seg * ft_pt
        seg_w = (segs[i+1]-segs[i]) * ft_pt
        c.setFillColor(BLACK if i % 2 == 0 else colors.white)
        c.rect(seg_x, y, seg_w, 5, stroke=0, fill=1)
    c.setFillColor(DARK_GRAY); c.setFont("Helvetica", 6)
    for ft in segs:
        c.drawCentredString(x + ft*ft_pt, y-8, f"{ft}'")
    c.drawString(x + total+4, y-8, "FEET")
    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Professional Title Block
# ─────────────────────────────────────────────────────────────────────────────
def draw_title_block(c, sheet_no, sheet_title, level_name, variant_tag, rev="P01"):
    TB_X = 18
    TB_Y = 18
    TB_W = PAGE_W - 36
    TB_H = 88

    c.saveState()
    # Outer border (double line)
    c.setStrokeColor(BLACK); c.setLineWidth(1.6)
    c.rect(18, 18, PAGE_W-36, PAGE_H-36, stroke=1, fill=0)
    c.setLineWidth(0.5)
    c.rect(24, 24, PAGE_W-48, PAGE_H-48, stroke=1, fill=0)

    # Title block background
    c.setFillColor(PALE_PANEL); c.setStrokeColor(BLACK); c.setLineWidth(0.8)
    c.rect(TB_X, TB_Y, TB_W, TB_H, stroke=1, fill=1)

    # Vertical dividers
    col1 = TB_X + TB_W * 0.32
    col2 = TB_X + TB_W * 0.72
    c.line(col1, TB_Y, col1, TB_Y+TB_H)
    c.line(col2, TB_Y, col2, TB_Y+TB_H)

    # ── Block 1: Project info
    c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 13)
    c.drawString(TB_X+12, TB_Y+TB_H-22, "BAR ASSOCIATION HALL")
    c.setFont("Helvetica-Bold", 9); c.setFillColor(colors.HexColor("#0369a1"))
    c.drawString(TB_X+12, TB_Y+TB_H-36, "DISTRICT COURT COMPLEX, BANSWARA")
    c.setFont("Helvetica", 8); c.setFillColor(GRAY)
    c.drawString(TB_X+12, TB_Y+TB_H-50, "RAJASTHAN, INDIA")
    c.setFont("Helvetica-Bold", 7); c.setFillColor(DARK_GRAY)
    c.drawString(TB_X+12, TB_Y+18, "PLANNING SETBACK ENVELOPE: 4,427.50 SQ.FT. PER FLOOR")
    c.drawString(TB_X+12, TB_Y+7,  "MAIN ENTRY: EAST LONG WALL  ·  WINDOWS: ALL FOUR SIDES")

    # ── Block 2: Drawing title
    dx = col1+12
    c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 12)
    c.drawString(dx, TB_Y+TB_H-22, sheet_title.upper())
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(colors.HexColor("#047857") if "FURNITURE" not in variant_tag else colors.HexColor("#b91c1c"))
    c.drawString(dx, TB_Y+TB_H-37, variant_tag.upper())
    c.setFont("Helvetica", 7.5); c.setFillColor(DARK_GRAY)
    c.drawString(dx, TB_Y+TB_H-52, f"LEVEL: {level_name.upper()}   SCALE: 1/8\" = 1'-0\"  (A2 LANDSCAPE)")
    c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 7)
    c.drawString(dx, TB_Y+14, "STRUCTURE: RCC FRAME  IS 456:2000 / IS 1893:2016")
    c.drawString(dx, TB_Y+4,  "STATUS: APPROVED SCHEMATIC — NOT FOR CONSTRUCTION")

    # ── Block 3: Sheet ID
    sx = col2 + (PAGE_W-36 - (col2-TB_X)) / 2
    c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(sx, TB_Y+56, sheet_no)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(sx, TB_Y+40, "SHEET NO.")
    c.setFont("Helvetica", 6.5); c.setFillColor(GRAY)
    c.drawCentredString(sx, TB_Y+24, f"REV: {rev}")
    c.drawCentredString(sx, TB_Y+13, datetime.now(timezone.utc).strftime("%d-%b-%Y").upper())
    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Legend & Notes Panel
# ─────────────────────────────────────────────────────────────────────────────
def draw_legend(c, x, y, mode):
    W, H = 400, 218
    c.saveState()
    c.setFillColor(PALE_PANEL); c.setStrokeColor(LIGHT_GRAY); c.setLineWidth(0.8)
    c.roundRect(x, y, W, H, 4, stroke=1, fill=1)

    c.setFillColor(CHARCOAL); c.rect(x, y+H-20, W, 20, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 8.5)
    c.drawString(x+10, y+H-14, "GENERAL NOTES & LEGEND")

    c.setFont("Helvetica", 7); c.setFillColor(DARK_GRAY)
    notes = [
        "1.  Setback envelope: 4,427.50 sq ft per floor (site_plan.json).",
        "2.  Main entrance EAST long wall, 12'-0\"×8'-0\" covered porch with ramp.",
        "3.  Accessible ramp 1:12 slope and 5'-0\" wide double-leaf entry door.",
        "4.  Windows on all four facades (N,S,E,W) for cross-ventilation & daylight.",
        "5.  Dog-leg stair: 18 risers @ 7.33\" rise, 10\" tread, mid-floor landing.",
        "6.  RCC columns & beams per IS 456:2000. Seismic zone per IS 1893:2016.",
        "7.  Survey boundary, fire NOC, local authority approval required before build.",
        "8.  All dimensions shown are nominal planning dimensions ±25 mm.",
    ]
    yy = y + H - 36
    for n in notes:
        c.drawString(x+10, yy, n); yy -= 13.5

    # Symbol key
    row_y = y + 12
    # Wall
    c.setStrokeColor(BLACK); c.setLineWidth(2.5)
    c.line(x+10, row_y+4, x+36, row_y+4)
    c.setFont("Helvetica-Bold", 6); c.setFillColor(DARK_GRAY)
    c.drawString(x+40, row_y+2, "CUT WALL")
    # Door
    c.setStrokeColor(DOOR_RED); c.setLineWidth(1)
    c.line(x+96, row_y+4, x+118, row_y+4)
    c.drawString(x+122, row_y+2, "DOOR/SWING")
    # Window
    c.setStrokeColor(GLASS_BLUE); c.setLineWidth(1.8)
    c.line(x+188, row_y+4, x+210, row_y+4)
    c.drawString(x+214, row_y+2, "WINDOW")
    if mode == "columns":
        c.setFillColor(CHARCOAL); c.setStrokeColor(BLACK); c.setLineWidth(0.6)
        c.rect(x+268, row_y, 10, 10, stroke=1, fill=1)
        c.drawString(x+282, row_y+2, "RCC COLUMN")
    elif mode == "furniture":
        c.setFillColor(FURN_FILL); c.setStrokeColor(FURN_STROKE); c.setLineWidth(0.6)
        c.rect(x+268, row_y, 10, 10, stroke=1, fill=1)
        c.drawString(x+282, row_y+2, "FURNITURE")
    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Room Schedule Panel
# ─────────────────────────────────────────────────────────────────────────────
def draw_schedule(c, x, y, spaces):
    W = 400; ROW = 15
    rows = len(spaces)
    H = ROW * (rows + 2)
    c.saveState()
    c.setFillColor(colors.white); c.setStrokeColor(LIGHT_GRAY); c.setLineWidth(0.7)
    c.rect(x, y, W, H, stroke=1, fill=1)

    # Header
    c.setFillColor(CHARCOAL); c.rect(x, y+H-ROW, W, ROW, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x+8, y+H-ROW+4, "ROOM / SPACE SCHEDULE")

    # Column headers
    c.setFillColor(DARK_GRAY); c.setFont("Helvetica-Bold", 6.5)
    c.drawString(x+6,   y+H-2*ROW+4, "ID")
    c.drawString(x+40,  y+H-2*ROW+4, "SPACE NAME")
    c.drawString(x+210, y+H-2*ROW+4, "SIZE")
    c.drawRightString(x+W-6, y+H-2*ROW+4, "AREA (SQ.FT.)")
    c.setStrokeColor(LIGHT_GRAY)

    total = 0.0
    for i, sp in enumerate(spaces):
        ry = y + H - ROW*(i+3)
        c.setLineWidth(0.4); c.line(x, ry, x+W, ry)
        x0,y0_,x1,y1_ = rect(sp)
        a = sqft(sp); total += a
        c.setFillColor(BLACK if i%2==0 else PALE_BG)
        c.rect(x, ry, W, ROW, stroke=0, fill=1)
        c.setFillColor(DARK_GRAY); c.setFont("Helvetica", 6.5)
        c.drawString(x+6,   ry+4, sp["id"])
        c.drawString(x+40,  ry+4, sp["name"][:34])
        c.drawString(x+210, ry+4, f"{fmtft(x1-x0)} × {fmtft(y1_-y0_)}")
        c.drawRightString(x+W-6, ry+4, f"{a:,.1f}")

    # Total row
    c.setFillColor(PALE_PANEL); c.setStrokeColor(LIGHT_GRAY)
    c.rect(x, y, W, ROW, stroke=1, fill=1)
    c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 7)
    c.drawString(x+40, y+4, "TOTAL ADOPTABLE AREA")
    c.drawRightString(x+W-6, y+4, f"{total:,.1f} SQ.FT.")
    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Column Schedule Panel
# ─────────────────────────────────────────────────────────────────────────────
def draw_col_schedule(c, x, y):
    types = [
        ("C1 – 300×600mm","8-T20+4-T16, Links T8@150","Main hall long-span perimeter"),
        ("C2 – 300×450mm","8-T16, Links T8@150",       "Service core, stair, dais"),
        ("CP – 300×300mm","4-T16, Links T8@150",        "Entrance porch canopy posts"),
    ]
    W = 400; ROW = 15; H = ROW*(len(types)+3)
    c.saveState()
    c.setFillColor(colors.white); c.setStrokeColor(LIGHT_GRAY); c.setLineWidth(0.7)
    c.rect(x, y, W, H, stroke=1, fill=1)
    c.setFillColor(CHARCOAL); c.rect(x, y+H-ROW, W, ROW, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x+8, y+H-ROW+4, "STRUCTURAL COLUMN SCHEDULE")
    c.setFillColor(DARK_GRAY); c.setFont("Helvetica-Bold", 6.5)
    c.drawString(x+6,   y+H-2*ROW+4, "MARK / SIZE")
    c.drawString(x+120, y+H-2*ROW+4, "MAIN REBAR")
    c.drawString(x+250, y+H-2*ROW+4, "ZONE")
    c.setStrokeColor(LIGHT_GRAY)
    for i, (mk, rb, zn) in enumerate(types):
        ry = y + H - ROW*(i+3)
        c.setLineWidth(0.4); c.line(x, ry, x+W, ry)
        c.setFillColor(BLACK if i%2==0 else PALE_BG)
        c.rect(x, ry, W, ROW, stroke=0, fill=1)
        c.setFillColor(DARK_GRAY); c.setFont("Helvetica", 6.5)
        c.drawString(x+6, ry+4, mk)
        c.drawString(x+120, ry+4, rb)
        c.drawString(x+250, ry+4, zn)
    # Spec line
    c.setFillColor(PALE_BG); c.setStrokeColor(LIGHT_GRAY)
    c.rect(x, y, W, ROW, stroke=1, fill=1)
    c.setFillColor(DOOR_RED); c.setFont("Helvetica-Bold", 6.5)
    c.drawString(x+8, y+4, "M25 CONCRETE  |  Fe500D STEEL  |  ISOLATED RCC FOOTINGS")
    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Door Drawing (Lumion-style with arc sweep)
# ─────────────────────────────────────────────────────────────────────────────
def draw_door(c, origin, space, opening):
    (mx0, my0),(mx1, my1) = wall_pts(space, opening["wall"], opening["offset"], opening["width"])
    a = pp(origin, mx0, my0)
    b = pp(origin, mx1, my1)

    wall   = opening["wall"]
    swing  = opening.get("swing", "in")
    w      = opening["width"]
    is_double = w >= 72
    horiz  = wall in {"north", "south"}
    WT_pt  = 6 * SCALE   # wall thickness in PDF points

    c.saveState()

    # ── 1. Clear wall opening (white gap matching wall thickness)
    c.setStrokeColor(colors.white)
    c.setLineWidth(WT_pt * 2.2)
    c.line(*a, *b)

    # ── 2. Door frame lines — two thin dark lines at jambs (both edges of opening)
    c.setStrokeColor(colors.HexColor("#1a1a1a")); c.setLineWidth(1.0)
    if horiz:
        # Frame lines perpendicular to wall (vertical stubs at each jamb)
        for pt in [a, b]:
            c.line(pt[0], pt[1] - WT_pt, pt[0], pt[1] + WT_pt)
    else:
        for pt in [a, b]:
            c.line(pt[0] - WT_pt, pt[1], pt[0] + WT_pt, pt[1])

    # ── 3. Door leaf + swing arc — dark brown, clean
    LEAF_CLR = colors.HexColor("#5d3a1a")   # warm dark brown
    ARC_CLR  = colors.HexColor("#8b5e3c")   # lighter brown for arc

    def leaf_and_arc(hinge, radius, start_a, end_a, leaf_angle_deg):
        """Draw door leaf line + swing arc from hinge point."""
        import math as _m
        ang = _m.radians(leaf_angle_deg)
        leaf_ex = hinge[0] + radius * _m.cos(ang)
        leaf_ey = hinge[1] + radius * _m.sin(ang)
        # Leaf
        c.setStrokeColor(LEAF_CLR); c.setLineWidth(1.2)
        c.line(hinge[0], hinge[1], leaf_ex, leaf_ey)
        # Arc
        c.setStrokeColor(ARC_CLR); c.setLineWidth(0.7)
        c.arc(hinge[0]-radius, hinge[1]-radius,
              hinge[0]+radius, hinge[1]+radius,
              start_a, end_a)

    if horiz:
        sign = 1 if ((wall=="south" and swing!="out") or
                     (wall=="north" and swing=="out")) else -1
        if is_double:
            hw = abs(b[0]-a[0])/2
            if sign > 0:
                leaf_and_arc(a, hw, 0,  90,  90)
                leaf_and_arc(b, hw, 90, 180, 90)
            else:
                leaf_and_arc(a, hw, 270, 360, 270)
                leaf_and_arc(b, hw, 270, 360, 270)
        else:
            hw = abs(b[0]-a[0])
            if sign > 0:
                leaf_and_arc(a, hw, 0, 90, 90)
            else:
                leaf_and_arc(a, hw, 270, 360, 270)
    else:
        sign = 1 if ((wall=="west" and swing!="out") or
                     (wall=="east" and swing=="out")) else -1
        if is_double:
            hv = abs(b[1]-a[1])/2
            if sign > 0:
                leaf_and_arc(a, hv, 0,   90,  90)
                leaf_and_arc(b, hv, 270, 360, 270)
            else:
                leaf_and_arc(a, hv, 90,  180, 90)
                leaf_and_arc(b, hv, 180, 270, 180)
        else:
            hv = abs(b[1]-a[1])
            if sign > 0:
                leaf_and_arc(a, hv, 0, 90, 90)
            else:
                leaf_and_arc(a, hv, 90, 180, 90)

    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Window Drawing — Architectural standard (3-line symbol: frame+glass+sill)
# Matches reference: clear wall gap, outer frame, glass pane fill, sill line
# NO tag bubble — clean professional style
# ─────────────────────────────────────────────────────────────────────────────
def draw_window(c, origin, space, window):
    (mx0, my0),(mx1, my1) = wall_pts(space, window["wall"], window["offset"], window["width"])
    a = pp(origin, mx0, my0)
    b = pp(origin, mx1, my1)

    wall     = window["wall"]
    is_horiz = wall in {"north", "south"}
    WT_pt    = 6 * SCALE   # wall thickness
    ow       = abs(b[0]-a[0]) if is_horiz else abs(b[1]-a[1])

    # ── Colours
    FRAME_CLR = colors.HexColor("#1a1a1a")
    GLASS_CLR = colors.HexColor("#aed6f1")   # light blue glass
    SILL_CLR  = colors.HexColor("#2e4057")   # dark sill line

    c.saveState()

    # ── 1. Clear wall opening
    c.setStrokeColor(colors.white); c.setLineWidth(WT_pt * 2.2)
    c.line(*a, *b)

    # ── 2. Glass fill (thin coloured band in centre of opening)
    GLASS_T = WT_pt * 0.35   # glass pane thickness
    if is_horiz:
        gx = min(a[0], b[0]); gy = a[1]
        c.setFillColor(GLASS_CLR); c.setLineWidth(0)
        c.rect(gx, gy - GLASS_T, ow, GLASS_T*2, stroke=0, fill=1)
    else:
        gy = min(a[1], b[1]); gx = a[0]
        c.setFillColor(GLASS_CLR); c.setLineWidth(0)
        c.rect(gx - GLASS_T, gy, GLASS_T*2, ow, stroke=0, fill=1)

    # ── 3. Three lines: outer frame | glass centre | inner sill
    #   Line 1 — outer frame (on wall face, thick)
    c.setStrokeColor(FRAME_CLR); c.setLineWidth(1.4)
    c.line(*a, *b)

    #   Line 2 — glass centre line (offset inward, blue)
    OFF2 = WT_pt * 0.25
    c.setStrokeColor(GLASS_CLR); c.setLineWidth(1.8)
    if is_horiz:
        c.line(a[0], a[1]+OFF2, b[0], b[1]+OFF2)
    else:
        c.line(a[0]+OFF2, a[1], b[0]+OFF2, b[1])

    #   Line 3 — inner sill line (offset further, dark)
    OFF3 = WT_pt * 0.55
    c.setStrokeColor(SILL_CLR); c.setLineWidth(0.7)
    if is_horiz:
        c.line(a[0], a[1]+OFF3, b[0], b[1]+OFF3)
    else:
        c.line(a[0]+OFF3, a[1], b[0]+OFF3, b[1])

    # ── 4. End caps (short perpendicular lines at jambs — like the reference)
    c.setStrokeColor(FRAME_CLR); c.setLineWidth(1.0)
    if is_horiz:
        for pt in [a, b]:
            c.line(pt[0], pt[1]-WT_pt*0.6, pt[0], pt[1]+WT_pt*0.6)
    else:
        for pt in [a, b]:
            c.line(pt[0]-WT_pt*0.6, pt[1], pt[0]+WT_pt*0.6, pt[1])

    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Staircase Drawing (dog-leg 2-flight 180° turn)
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Staircase Drawing — Architectural presentation grade
# Matches reference: numbered treads, nosing dots, handrail, mid-landing,
# UP arrow, break line, section marks, wall hatch, RCC columns at corners
# ─────────────────────────────────────────────────────────────────────────────
def draw_stair(c, origin, stair_space, stair):
    x0, y0, x1, y1 = rect(stair_space)
    nrisers   = stair["riserCountPerFlight"]   # 12 per flight
    tread_in  = stair["tread"]                 # 9"
    width_in  = stair["width"]                 # 48" = 4'-0" stair width
    land_in   = stair["landingDepth"]          # 42"
    WALL_T    = 6                              # wall thickness inches

    # ── Derived PDF values ─────────────────────────────────────────────────
    tread_pt  = tread_in  * SCALE             # 9 * 0.75 = 6.75 pt  (tread depth along Y)
    width_pt  = width_in  * SCALE             # 48 * 0.75 = 36 pt   (stair width along X)
    land_pt   = land_in   * SCALE             # 42 * 0.75 = 31.5 pt (landing depth along Y)
    wall_pt   = WALL_T    * SCALE
    flight_run= nrisers * tread_pt            # 12 × 9 × SCALE = 81 pt  (run along Y)

    # Space bounds in PDF
    sx, sy    = pp(origin, x0, y0)
    sw        = (x1 - x0) * SCALE            # 144 * 0.75 = 108 pt
    sh        = (y1 - y0) * SCALE            # 270 * 0.75 = 202.5 pt

    # ── Colours matching reference ─────────────────────────────────────────
    WALL_DARK   = colors.HexColor("#2d2d2d")    # near-black wall fill
    WALL_HATCH  = colors.HexColor("#8b4513")    # orange-brown wall hatch
    TREAD_FILL  = colors.HexColor("#fef9e7")    # pale cream tread
    TREAD_ALT   = colors.HexColor("#fdf5dc")    # alternate tread shade
    LANDING_CLR = colors.HexColor("#e8f4f8")    # blue-grey landing
    NOSING_CLR  = colors.HexColor("#b8860b")    # dark gold nosing dots
    HANDRAIL    = colors.HexColor("#5d4e37")    # dark brown handrail
    COL_RED     = colors.HexColor("#8b1a1a")    # RCC column red-brown
    BREAK_LINE  = colors.HexColor("#e74c3c")    # red break/cut line
    SECTION_CLR = colors.HexColor("#c0392b")    # section mark red
    ARROW_CLR   = colors.HexColor("#1a1a2e")    # dark navy arrow

    c.saveState()

    # ═══════════════════════════════════════════════════════════════════════
    # 1. OUTER WALL BOUNDARY — filled dark with hatch lines
    # ═══════════════════════════════════════════════════════════════════════
    # Outer box
    c.setFillColor(WALL_DARK); c.setStrokeColor(WALL_DARK); c.setLineWidth(0)
    c.rect(sx, sy, sw, sh, stroke=0, fill=1)

    # Inner open area (cream background)
    inner_x = sx + wall_pt
    inner_y = sy + wall_pt
    inner_w = sw - 2*wall_pt
    inner_h = sh - 2*wall_pt
    c.setFillColor(colors.HexColor("#fafafa"))
    c.rect(inner_x, inner_y, inner_w, inner_h, stroke=0, fill=1)

    # Wall hatch (diagonal lines on all 4 wall bands — orange/brown)
    c.setStrokeColor(WALL_HATCH); c.setLineWidth(0.7)
    hatch_gap = 4
    # Bottom wall band
    for hx in range(int(sw / hatch_gap) + 2):
        hxp = sx + hx * hatch_gap
        c.line(hxp, sy, min(hxp + wall_pt, sx+sw), min(sy + wall_pt, sy+sh))
    # Top wall band
    for hx in range(int(sw / hatch_gap) + 2):
        hxp = sx + hx * hatch_gap
        c.line(hxp, sy+sh-wall_pt, min(hxp + wall_pt, sx+sw), sy+sh)
    # Left wall band
    for hy in range(int(sh / hatch_gap) + 2):
        hyp = sy + hy * hatch_gap
        c.line(sx, hyp, min(sx + wall_pt, sx+sw), min(hyp + wall_pt, sy+sh))
    # Right wall band
    for hy in range(int(sh / hatch_gap) + 2):
        hyp = sy + hy * hatch_gap
        c.line(sx+sw-wall_pt, hyp, sx+sw, min(hyp + wall_pt, sy+sh))

    # ═══════════════════════════════════════════════════════════════════════
    # 2. RCC COLUMNS — dark red-brown squares at all 4 corners (visible)
    # ═══════════════════════════════════════════════════════════════════════
    col_sz = wall_pt * 1.5
    for cx_col, cy_col in [
        (sx,           sy),
        (sx+sw-col_sz, sy),
        (sx,           sy+sh-col_sz),
        (sx+sw-col_sz, sy+sh-col_sz),
    ]:
        c.setFillColor(COL_RED); c.setStrokeColor(WALL_DARK); c.setLineWidth(0.5)
        c.rect(cx_col, cy_col, col_sz, col_sz, stroke=1, fill=1)
        # Cross hatch on column
        c.setStrokeColor(colors.HexColor("#3d0000")); c.setLineWidth(0.4)
        c.line(cx_col, cy_col, cx_col+col_sz, cy_col+col_sz)
        c.line(cx_col+col_sz, cy_col, cx_col, cy_col+col_sz)

    # ═══════════════════════════════════════════════════════════════════════
    # 3. STAIR GEOMETRY — landing at SOUTH wall, flights run NORTH
    #    Layout (Y increases northward on page):
    #    Y=sy+wall  : south wall inner face
    #    +land_pt   : 4'-0" landing slab (bilkul south wall se sata hua)
    #    +flight_run: flight 1 (12 treads × 9")
    #    +mid_wall  : 6" partition between flights
    #    +flight_run: flight 2 (12 treads × 9") — reversed direction
    #    +void      : 4'-0" open void at north (user circulation space)
    # ═══════════════════════════════════════════════════════════════════════
    mid_wall_pt = wall_pt
    flight_w    = (inner_w - mid_wall_pt) / 2

    # Landing at bottom (south)
    land_y0 = inner_y
    land_y1 = land_y0 + land_pt

    # Flight 1 — LEFT half, going UP (south→north)
    f1_x0 = inner_x
    f1_x1 = inner_x + flight_w
    f1_y0 = land_y1
    f1_y1 = f1_y0 + flight_run

    # Flight 2 — RIGHT half, continuing UP from landing (user turns at landing)
    f2_x0 = inner_x + flight_w + mid_wall_pt
    f2_x1 = inner_x + inner_w
    f2_y0 = land_y1
    f2_y1 = f2_y0 + flight_run

    # Mid-partition between the two flights
    c.setFillColor(WALL_DARK); c.setLineWidth(0)
    c.rect(inner_x + flight_w, land_y1,
           mid_wall_pt, flight_run, stroke=0, fill=1)

    # North void (4' free space above flights)
    void_y0 = f1_y1
    void_y1 = inner_y + inner_h
    c.setFillColor(colors.HexColor("#e8f4e8"))  # light green = open void
    c.setStrokeColor(WALL_DARK); c.setLineWidth(0.6)
    c.rect(inner_x, void_y0, inner_w, void_y1 - void_y0, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#2d6a2d")); c.setFont("Helvetica-Bold", 4.5)
    c.drawCentredString(inner_x + inner_w/2, (void_y0+void_y1)/2, "OPEN / VOID")

    # ═══════════════════════════════════════════════════════════════════════
    # 4. LANDING SLAB — at SOUTH (bilkul south wall se sata hua)
    # ═══════════════════════════════════════════════════════════════════════
    c.setFillColor(LANDING_CLR); c.setStrokeColor(WALL_DARK); c.setLineWidth(0.8)
    c.rect(inner_x, land_y0, inner_w, land_pt, stroke=1, fill=1)
    # Landing hatch (horizontal lines)
    c.setStrokeColor(colors.HexColor("#a9cce3")); c.setLineWidth(0.4)
    hl_gap = 5
    for hl in range(int(land_pt / hl_gap) + 2):
        hy = land_y0 + hl * hl_gap
        if hy <= land_y1:
            c.line(inner_x, hy, inner_x + inner_w, hy)
    mid_land_cx = inner_x + inner_w / 2
    mid_land_cy = land_y0 + land_pt / 2
    c.setFillColor(WALL_DARK); c.setFont("Helvetica-Bold", 5)
    c.drawCentredString(mid_land_cx, mid_land_cy + 3, "LANDING")
    c.drawCentredString(mid_land_cx, mid_land_cy - 5, "4'-0\" WIDE")

    # ═══════════════════════════════════════════════════════════════════════
    # 5. TREADS — Flight 1 LEFT (numbered 1→12, south to north / bottom to top)
    # ═══════════════════════════════════════════════════════════════════════
    for r in range(nrisers):
        ty0 = f1_y0 + r * tread_pt
        ty1 = ty0 + tread_pt
        # Alternate fill
        c.setFillColor(TREAD_FILL if r % 2 == 0 else TREAD_ALT)
        c.setStrokeColor(WALL_DARK); c.setLineWidth(0.5)
        c.rect(f1_x0, ty0, flight_w, tread_pt, stroke=1, fill=1)
        # Tread number
        c.setFillColor(WALL_DARK); c.setFont("Helvetica-Bold", 4.5)
        c.drawCentredString(f1_x0 + flight_w / 2, ty0 + 2, str(r + 1))
        # Nosing dots (top/north edge of tread — the nosing line)
        c.setFillColor(NOSING_CLR)
        for nd in range(3):
            nx = f1_x0 + flight_w * (0.2 + nd * 0.3)
            c.circle(nx, ty0 + tread_pt - 1.5, 0.8, stroke=0, fill=1)

    # ═══════════════════════════════════════════════════════════════════════
    # 6. TREADS — Flight 2 RIGHT (numbered 13→24, south to north on plan
    #             but travel direction is reversed — down from landing)
    # ═══════════════════════════════════════════════════════════════════════
    for r in range(nrisers):
        # Flight 2 treads: tread 13 is at TOP (near landing), 24 at BOTTOM
        # On plan we draw them south-to-north too, but arrow points DOWN (south)
        ty0 = f2_y1 - (r + 1) * tread_pt   # reversed: tread 0 near landing (top)
        ty1 = ty0 + tread_pt
        c.setFillColor(TREAD_FILL if r % 2 == 0 else TREAD_ALT)
        c.setStrokeColor(WALL_DARK); c.setLineWidth(0.5)
        c.rect(f2_x0, ty0, flight_w, tread_pt, stroke=1, fill=1)
        # Tread number (continues from 13)
        c.setFillColor(WALL_DARK); c.setFont("Helvetica-Bold", 4.5)
        c.drawCentredString(f2_x0 + flight_w / 2, ty0 + 2, str(nrisers + r + 1))
        # Nosing dots on south (lower) edge of each tread for flight 2
        c.setFillColor(NOSING_CLR)
        for nd in range(3):
            nx = f2_x0 + flight_w * (0.2 + nd * 0.3)
            c.circle(nx, ty0 + 1.5, 0.8, stroke=0, fill=1)

    # ═══════════════════════════════════════════════════════════════════════
    # 7. HANDRAILS — thin dark lines along open/outer sides of each flight
    # ═══════════════════════════════════════════════════════════════════════
    c.setStrokeColor(HANDRAIL); c.setLineWidth(1.4)
    # Flight 1 handrail (left/west edge)
    c.line(f1_x0 + 3, f1_y0, f1_x0 + 3, f1_y1)
    # Flight 2 handrail (right/east edge)
    c.line(f2_x1 - 3, f2_y0, f2_x1 - 3, f2_y1)
    # Handrail label
    c.setFillColor(HANDRAIL); c.setFont("Helvetica-Bold", 4.5)
    c.drawString(f1_x0 + 5, (f1_y0 + f1_y1) / 2 - 2, "H/R")
    c.drawString(f2_x1 - 14, (f2_y0 + f2_y1) / 2 - 2, "H/R")

    # ═══════════════════════════════════════════════════════════════════════
    # 8. UP / DN ARROWS along centre of each flight
    # ═══════════════════════════════════════════════════════════════════════
    arrow_x1 = (f1_x0 + f1_x1) / 2   # centre of flight 1
    arrow_x2 = (f2_x0 + f2_x1) / 2   # centre of flight 2

    def draw_vert_arrow(ax, ay0, ay1, direction, label):
        """direction=1 → up (arrow at top), -1 → down (arrow at bottom)"""
        c.setStrokeColor(ARROW_CLR); c.setLineWidth(0.9)
        c.line(ax, ay0, ax, ay1)
        tip_y = ay1 if direction > 0 else ay0
        c.line(tip_y and ax - 3, tip_y - direction * 6, ax, tip_y)
        c.line(ax + 3, tip_y - direction * 6, ax, tip_y)
        c.setFillColor(ARROW_CLR); c.setFont("Helvetica-Bold", 5.5)
        c.drawCentredString(ax, (ay0 + ay1) / 2 + 3, label)

    # Flight 1 arrow — UP (going north/up)
    draw_vert_arrow(arrow_x1, f1_y0 + 6, f1_y1 - 6, 1, "UP")
    # Flight 2 arrow — DN (going down toward entry from landing)
    draw_vert_arrow(arrow_x2, f2_y0 + 6, f2_y1 - 6, -1, "DN")

    # ═══════════════════════════════════════════════════════════════════════
    # 9. BREAK LINE — dashed red horizontal line mid-height of flight 1
    # ═══════════════════════════════════════════════════════════════════════
    break_y = f1_y0 + flight_run * 0.5
    c.setStrokeColor(BREAK_LINE); c.setLineWidth(0.8); c.setDash(3, 2)
    c.line(f1_x0, break_y, f1_x1, break_y)
    c.setDash()
    # Zigzag break symbol at centre
    mid_bx = (f1_x0 + f1_x1) / 2
    c.setStrokeColor(BREAK_LINE); c.setLineWidth(0.8)
    pts = [(mid_bx - 8, break_y), (mid_bx - 4, break_y + 4),
           (mid_bx + 4, break_y - 4), (mid_bx + 8, break_y)]
    for i in range(len(pts) - 1):
        c.line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1])

    # ═══════════════════════════════════════════════════════════════════════
    # 10. SECTION MARKS A-A on bottom wall (matching reference)
    # ═══════════════════════════════════════════════════════════════════════
    sec_x = inner_x + inner_w / 2
    for sec_y_pos, side in [(sy - 8, "B"), (sy + sh + 2, "T")]:
        c.setFillColor(colors.white); c.setStrokeColor(SECTION_CLR); c.setLineWidth(0.8)
        c.circle(sec_x, sec_y_pos + (0 if side == "B" else 6), 5, stroke=1, fill=1)
        c.setFillColor(SECTION_CLR); c.setFont("Helvetica-Bold", 5.5)
        c.drawCentredString(sec_x, sec_y_pos + (0 if side == "B" else 6) - 2, "A")
    # Section line through
    c.setStrokeColor(SECTION_CLR); c.setLineWidth(0.5); c.setDash(6, 2)
    c.line(sec_x, sy - 3, sec_x, sy + sh + 3)
    c.setDash()

    # ═══════════════════════════════════════════════════════════════════════
    # 11. DIMENSION ANNOTATIONS outside stair box
    # ═══════════════════════════════════════════════════════════════════════
    # Flight run dimension — left side of box (along Y)
    dim_x = sx - 14
    c.setStrokeColor(DARK_GRAY); c.setLineWidth(0.5)
    c.line(dim_x, f1_y0, dim_x, f1_y1)
    c.line(dim_x - 3, f1_y0, dim_x + 3, f1_y0)
    c.line(dim_x - 3, f1_y1, dim_x + 3, f1_y1)
    c.setFillColor(DARK_GRAY); c.setFont("Helvetica-Bold", 5)
    c.drawCentredString(dim_x - 18, (f1_y0 + f1_y1) / 2,
                        f"{nrisers}×{tread_in:.0f}\"={fmtft(nrisers*tread_in)}")

    # Flight width dim on bottom (along X)
    dim_y = sy - 14
    c.setStrokeColor(DARK_GRAY); c.setLineWidth(0.5)
    c.line(f1_x0, dim_y, f1_x1, dim_y)
    c.line(f1_x0, dim_y - 3, f1_x0, dim_y + 3)
    c.line(f1_x1, dim_y - 3, f1_x1, dim_y + 3)
    c.setFillColor(DARK_GRAY); c.setFont("Helvetica-Bold", 5)
    c.drawCentredString((f1_x0 + f1_x1) / 2, dim_y - 9,
                        fmtft(width_in))

    # ═══════════════════════════════════════════════════════════════════════
    # 12. DATA BLOCK — riser/tread/floor-floor info
    # ═══════════════════════════════════════════════════════════════════════
    c.setFillColor(colors.HexColor("#1e293b"))
    c.setFont("Helvetica-Bold", 5)
    info_y = sy - 24
    c.drawCentredString(sx + sw/2, info_y,
                        f"{stair['riserCountTotal']}R @ {stair['riser']:.2f}\" / {tread_in:.0f}\" TREAD  |  F-F = {fmtft(stair['floorToFloor'])}")

    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Main Entrance Porch (East long wall)
# ─────────────────────────────────────────────────────────────────────────────
def draw_porch(c, origin, plans, spaces, level):
    sp_by_id  = {s["id"]: s for s in spaces}
    op_by_id  = {o["id"]: o for o in plans["openings"]}
    for entry in plans.get("entries", []):
        if entry["level"] != level or entry["kind"] != "main":
            continue
        if entry["openingId"] not in op_by_id:
            continue
        host   = sp_by_id.get(entry["hostSpace"])
        if not host: continue
        op     = op_by_id[entry["openingId"]]
        (am, bm) = wall_pts(host, op["wall"], op["offset"], op["width"])
        a, b   = pp(origin, *am), pp(origin, *bm)

        porch  = entry["porch"]
        W_inch = porch["width"]   # 144 = 12 ft
        D_inch = porch["depth"]   # 96  =  8 ft
        cy     = (am[1]+bm[1])/2
        x0m    = max(am[0], bm[0])   # east outer face
        y0m    = cy - W_inch/2

        px, py = pp(origin, x0m, y0m)
        pw = D_inch * SCALE
        ph = W_inch * SCALE

        c.saveState()
        # Porch slab
        c.setFillColor(PORCH_FILL); c.setStrokeColor(PORCH_AMBER); c.setLineWidth(1.4)
        c.rect(px, py, pw, ph, stroke=1, fill=1)
        # Canopy overhang dashed
        c.setDash(5,3); c.setLineWidth(0.8)
        c.rect(px-3, py-3, pw+6, ph+6, stroke=1, fill=0)
        c.setDash()

        # 3 steps (striped)
        step_w = pw/4
        c.setStrokeColor(colors.HexColor("#f59e0b")); c.setLineWidth(0.6)
        for si in range(1,4):
            c.line(px+si*step_w, py, px+si*step_w, py+ph)

        # Ramp label
        c.setFillColor(BLACK); c.setFont("Helvetica", 5.8)
        c.drawString(px+4, py+10, "RAMP 1:12 →")

        # Porch canopy columns
        for col_y in [py+6, py+ph-14]:
            c.setFillColor(CHARCOAL); c.setStrokeColor(BLACK); c.setLineWidth(0.8)
            c.rect(px+pw-10, col_y, 9, 9, stroke=1, fill=1)

        # Label badge
        lx = px + pw*0.55; ly = py + ph/2
        c.setFillColor(PORCH_FILL); c.setStrokeColor(PORCH_AMBER); c.setLineWidth(0.7)
        c.roundRect(lx-50, ly-18, 100, 36, 3, stroke=1, fill=1)
        c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(lx, ly+9, "MAIN ENTRANCE PORCH")
        c.setFillColor(PORCH_AMBER); c.setFont("Helvetica-Bold", 6.5)
        c.drawCentredString(lx, ly, "12'-0\" × 8'-0\"")
        c.setFillColor(DARK_GRAY); c.setFont("Helvetica", 5.5)
        c.drawCentredString(lx, ly-9, "RAMP + STEPS · ACCESSIBLE")

        # Arrow pointing into building
        arrow(c, a[0]-4, (a[1]+b[1])/2, math.pi, 8)
        c.setFillColor(PORCH_AMBER); c.setFont("Helvetica-Bold", 6.5)
        c.drawCentredString(a[0]-18, (a[1]+b[1])/2+10, "EAST")
        c.drawCentredString(a[0]-18, (a[1]+b[1])/2+1, "ENTRY")
        c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Furniture Drawing (Lumion-grade detail per room type)
# ─────────────────────────────────────────────────────────────────────────────
def draw_furniture(c, origin, space):
    x0, y0, x1, y1 = rect(space)
    name = space["name"]
    c.saveState()

    if "Assembly Hall" in name:
        # ── Audience PVC chairs: no tables, rows only
        # Layout: 2 side aisles (36") + 1 centre aisle (36"), 2'-0" wall clearance
        SIDE_CLEAR   = 24   # 2'-0" wall clearance
        SIDE_AISLE   = 36   # 3'-0" side aisle
        CENTRE_AISLE = 36   # 3'-0" centre aisle
        FRONT_CLEAR  = 48   # 4'-0" from north wall (toward dais)
        REAR_CLEAR   = 36   # 3'-0" rear clearance

        CHAIR_W  = 18       # 18" wide
        CHAIR_D  = 18       # 18" deep (visual)
        ROW_PITCH= 30       # 30" row pitch

        zone_x0 = x0 + SIDE_CLEAR + SIDE_AISLE
        zone_x1 = x1 - SIDE_CLEAR - SIDE_AISLE
        zone_y0 = y0 + REAR_CLEAR
        zone_y1 = y1 - FRONT_CLEAR

        usable_w = (zone_x1 - zone_x0 - CENTRE_AISLE)
        chairs_per_block = int(usable_w / 2 // CHAIR_W)
        n_rows = int((zone_y1 - zone_y0) // ROW_PITCH)
        half_w = chairs_per_block * CHAIR_W
        cx_zone = (zone_x0 + zone_x1) / 2
        left_x0  = cx_zone - CENTRE_AISLE/2 - half_w
        right_x0 = cx_zone + CENTRE_AISLE/2

        chair_w_pt = CHAIR_W * SCALE
        chair_d_pt = CHAIR_D * SCALE

        c.setLineWidth(0.45)
        for row in range(n_rows):
            row_y = zone_y0 + row * ROW_PITCH
            for block_x0m in (left_x0, right_x0):
                for col in range(chairs_per_block):
                    cx_m = block_x0m + col * CHAIR_W
                    px, py = pp(origin, cx_m, row_y)
                    # Seat cushion
                    c.setFillColor(FURN_SEAT); c.setStrokeColor(FURN_STROKE)
                    c.roundRect(px, py, chair_w_pt, chair_d_pt*0.60, 1.5, stroke=1, fill=1)
                    # Back rest
                    c.setFillColor(colors.HexColor("#bfdbfe"))
                    c.roundRect(px+chair_w_pt*0.08,
                                py+chair_d_pt*0.60+0.8,
                                chair_w_pt*0.84,
                                chair_d_pt*0.35, 1.2, stroke=1, fill=1)

        # Aisle dashed lines
        c.setStrokeColor(colors.HexColor("#94a3b8")); c.setLineWidth(0.7); c.setDash(4,3)
        for ax in [left_x0 - SIDE_AISLE/2, cx_zone, right_x0 + half_w + SIDE_AISLE/2]:
            lx, ly0 = pp(origin, ax, zone_y0 - 8)
            _,  ly1 = pp(origin, ax, zone_y1 + 8)
            c.line(lx, ly0, lx, ly1)
        c.setDash()

        # Aisle label
        c.setFillColor(GRAY); c.setFont("Helvetica-Bold", 5.5)
        c.drawCentredString(*pp(origin, cx_zone, y0 + (zone_y1-y0)*0.5),
                            "CENTRE AISLE — 3'-0\"")

    elif "Dais" in name:
        # Raised dais with executive table + chairs + podiums + flag stands
        # Dais step edge line
        c.setStrokeColor(colors.HexColor("#b45309")); c.setLineWidth(1.6)
        c.line(*pp(origin,x0,y0+4), *pp(origin,x1,y0+4))
        c.setFillColor(colors.HexColor("#b45309")); c.setFont("Helvetica-Bold", 6)
        c.drawString(*pp(origin,x0+16,y0+8), "RAISED DAIS  +1'-6\" F.F.L.")

        # Executive table 24'×3'-6" = 288"×42"
        tx0 = (x0+x1)/2 - 144; tx1 = tx0 + 288
        c.setFillColor(colors.HexColor("#fde68a")); c.setStrokeColor(BLACK); c.setLineWidth(0.9)
        c.roundRect(*pp(origin,tx0,y0+48), 288*SCALE, 42*SCALE, 5, stroke=1, fill=1)
        c.setFillColor(DARK_GRAY); c.setFont("Helvetica-Bold", 5.5)
        c.drawCentredString(*pp(origin,(tx0+tx1)/2,y0+67), "EXECUTIVE DAIS TABLE")

        # 7 high-back chairs behind table
        for i in range(7):
            cx = tx0 + 18 + i*40
            c.setFillColor(colors.HexColor("#92400e"))
            c.roundRect(*pp(origin,cx,y0+96), 28*SCALE, 24*SCALE, 3, stroke=1, fill=1)

        # Podiums
        for pod_x, lbl in [(x0+50,"PODIUM"),(x1-82,"PODIUM")]:
            c.setFillColor(colors.HexColor("#78350f")); c.setStrokeColor(BLACK)
            c.roundRect(*pp(origin,pod_x,y0+56), 32*SCALE, 30*SCALE, 3, stroke=1, fill=1)
            c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 5)
            c.drawCentredString(*pp(origin,pod_x+16,y0+69), lbl)

        # National flag stands
        for fx, fy in [(x0+20,y0+50),(x1-20,y0+50)]:
            px_, py_ = pp(origin,fx,fy)
            c.setStrokeColor(DARK_GRAY); c.setFillColor(DARK_GRAY); c.setLineWidth(0.8)
            c.line(px_, py_, px_, py_+20*SCALE)
            c.rect(px_-1, py_+18*SCALE, 12*SCALE, 8*SCALE, stroke=1, fill=1)

    elif "Reception" in name or "Librarian" in name:
        # L-shaped reception counter + visitor chairs
        c.setFillColor(FURN_FILL); c.setStrokeColor(FURN_STROKE); c.setLineWidth(0.8)
        # Long counter
        c.roundRect(*pp(origin,x0+14,y0+36), 86*SCALE, 22*SCALE, 3, stroke=1, fill=1)
        # Return wing
        c.roundRect(*pp(origin,x0+72,y0+58), 22*SCALE, 44*SCALE, 3, stroke=1, fill=1)
        # Staff chair
        c.setFillColor(FURN_SEAT)
        c.circle(*pp(origin,x0+46,y0+78), 10*SCALE, stroke=1, fill=1)
        c.setFont("Helvetica-Bold", 5.5); c.setFillColor(DARK_GRAY)
        c.drawCentredString(*pp(origin,x0+56,y0+26), "COUNTER")
        # Visitor chairs × 3
        for i in range(3):
            c.setFillColor(FURN_SEAT)
            c.roundRect(*pp(origin,x0+10+i*34,y0+130), 24*SCALE, 20*SCALE, 3, stroke=1, fill=1)
        c.setFont("Helvetica", 5.5)
        c.drawCentredString(*pp(origin,x0+56,y0+158), "WAITING AREA")

    elif "Pantry" in name:
        # Counter + sink + fridge + shelves
        c.setFillColor(FURN_FILL); c.setStrokeColor(FURN_STROKE); c.setLineWidth(0.7)
        c.roundRect(*pp(origin,x0+8,y0+8), 104*SCALE, 24*SCALE, 3, stroke=1, fill=1)
        # Sink
        c.setFillColor(GLASS_FILL); c.setStrokeColor(ACCENT_BLUE); c.setLineWidth(0.6)
        c.ellipse(*pp(origin,x0+14,y0+12), *pp(origin,x0+36,y0+24), stroke=1, fill=1)
        c.ellipse(*pp(origin,x0+42,y0+12), *pp(origin,x0+62,y0+24), stroke=1, fill=1)
        # Fridge
        c.setFillColor(PALE_BG); c.setStrokeColor(DARK_GRAY)
        c.roundRect(*pp(origin,x0+74,y0+10), 20*SCALE, 20*SCALE, 2, stroke=1, fill=1)
        c.setFont("Helvetica", 5); c.setFillColor(DARK_GRAY)
        c.drawCentredString(*pp(origin,x0+84,y0+18), "F")
        # Label
        c.setFont("Helvetica-Bold", 5.5)
        c.drawCentredString(*pp(origin,(x0+x1)/2,y0+52), "PANTRY COUNTER & SINK")

    elif "Toilet" in name:
        c.setStrokeColor(ACCENT_BLUE); c.setFillColor(GLASS_FILL); c.setLineWidth(0.6)
        # WC pans (oval)
        for oy_off in [28, 90, 150]:
            c.ellipse(*pp(origin,x0+12,y0+oy_off), *pp(origin,x0+30,y0+oy_off+22), stroke=1, fill=1)
        # Wash basins
        for oy_off in [50, 112]:
            c.ellipse(*pp(origin,x0+50,y0+oy_off), *pp(origin,x0+68,y0+oy_off+16), stroke=1, fill=1)
        # Partition lines
        c.setStrokeColor(DARK_GRAY); c.setLineWidth(0.5)
        for split_y in [0.33, 0.66]:
            sy_ = y0 + (y1-y0)*split_y
            c.line(*pp(origin,x0,sy_), *pp(origin,x0+108,sy_))
        c.setFont("Helvetica-Bold", 5.5); c.setFillColor(ACCENT_BLUE)
        c.drawString(*pp(origin,x0+6,y1-18), "M/F/ACCESSIBLE")

    elif "Library Reading" in name:
        # Study tables (6) + wall shelves + individual seats
        c.setStrokeColor(FURN_STROKE); c.setFillColor(colors.HexColor("#fef9c3")); c.setLineWidth(0.6)
        for col in range(2):
            for row in range(3):
                tx_ = x0 + 70 + col*290
                ty_ = y0 + 40 + row*155
                c.roundRect(*pp(origin,tx_,ty_), 200*SCALE, 60*SCALE, 4, stroke=1, fill=1)
                # Chairs each side of table
                c.setFillColor(FURN_SEAT)
                for seat in range(4):
                    c.roundRect(*pp(origin,tx_+20+seat*46,ty_-20), 26*SCALE, 16*SCALE, 2, stroke=1, fill=1)
                    c.roundRect(*pp(origin,tx_+20+seat*46,ty_+64), 26*SCALE, 16*SCALE, 2, stroke=1, fill=1)
        # Wall shelves (west & east)
        c.setFillColor(FURN_FILL); c.setStrokeColor(FURN_STROKE)
        for wx_ in [x0+4, x1-36]:
            for wy_ in range(3):
                c.rect(*pp(origin,wx_,y0+50+wy_*150), 32*SCALE, 44*SCALE, stroke=1, fill=1)
        c.setFont("Helvetica-Bold", 5.5); c.setFillColor(DARK_GRAY)
        c.drawCentredString(*pp(origin,(x0+x1)/2,y1-14), "READING ROOM — 6 STUDY TABLES")

    elif "Stack Area" in name:
        # Double-sided book stacks
        c.setStrokeColor(DARK_GRAY); c.setFillColor(colors.HexColor("#e2e8f0")); c.setLineWidth(0.8)
        stack_rows = 5
        for r in range(stack_rows):
            yy_ = y0 + 20 + r*38
            c.rect(*pp(origin,x0+36,yy_), 590*SCALE, 22*SCALE, stroke=1, fill=1)
            # Dividers
            for d in range(1,11):
                dx_ = x0+36+d*59
                c.setLineWidth(0.4)
                c.line(*pp(origin,dx_,yy_), *pp(origin,dx_,yy_+22))
                c.setLineWidth(0.8)
        c.setFont("Helvetica-Bold", 6); c.setFillColor(DARK_GRAY)
        c.drawCentredString(*pp(origin,(x0+x1)/2,y1-14), "LAW REPORT BOOK STACKS (AIR, SCC, SCR, SLR)")

    elif "Discussion" in name:
        # Round conference table + chairs
        cx_ = (x0+x1)/2; cy_ = (y0+y1)/2
        c.setFillColor(colors.HexColor("#fde68a")); c.setStrokeColor(BLACK); c.setLineWidth(0.8)
        c.circle(*pp(origin,cx_,cy_), 40*SCALE, stroke=1, fill=1)
        c.setFillColor(FURN_SEAT)
        for ang_deg in range(0,360,45):
            ang = math.radians(ang_deg)
            rx_ = cx_ + 56*math.cos(ang); ry_ = cy_ + 56*math.sin(ang)
            c.circle(*pp(origin,rx_,ry_), 10*SCALE, stroke=1, fill=1)
        c.setFont("Helvetica-Bold", 5.5); c.setFillColor(DARK_GRAY)
        c.drawCentredString(*pp(origin,cx_,cy_+50), "CONFERENCE TABLE")

    elif "Computer" in name:
        # Computer workstations along two walls
        c.setFillColor(FURN_FILL); c.setStrokeColor(FURN_STROKE); c.setLineWidth(0.7)
        for i in range(5):
            # Left row
            c.roundRect(*pp(origin,x0+12,y0+14+i*22), 42*SCALE, 18*SCALE, 2, stroke=1, fill=1)
            # Screen
            c.setFillColor(GLASS_FILL)
            c.rect(*pp(origin,x0+16,y0+17+i*22), 20*SCALE, 12*SCALE, stroke=1, fill=1)
            c.setFillColor(FURN_FILL)
            # Right row
            c.roundRect(*pp(origin,x1-54,y0+14+i*22), 42*SCALE, 18*SCALE, 2, stroke=1, fill=1)
            c.setFillColor(GLASS_FILL)
            c.rect(*pp(origin,x1-50,y0+17+i*22), 20*SCALE, 12*SCALE, stroke=1, fill=1)
            c.setFillColor(FURN_FILL)
        c.setFont("Helvetica-Bold", 5.5); c.setFillColor(DARK_GRAY)
        c.drawCentredString(*pp(origin,(x0+x1)/2,y1-14), "COMPUTER WORKSTATIONS")

    elif "Store" in name:
        # Electrical panel + server rack + shelving
        c.setFillColor(colors.HexColor("#fef08a")); c.setStrokeColor(BLACK); c.setLineWidth(0.7)
        c.roundRect(*pp(origin,x0+14,y1-32), 70*SCALE, 20*SCALE, 2, stroke=1, fill=1)
        c.roundRect(*pp(origin,x0+90,y1-32), 60*SCALE, 20*SCALE, 2, stroke=1, fill=1)
        c.setFont("Helvetica-Bold", 5); c.setFillColor(BLACK)
        c.drawCentredString(*pp(origin,x0+49,y1-20), "ELEC. PANEL")
        c.drawCentredString(*pp(origin,x0+120,y1-20), "UPS/SERVER")
        # Shelves below
        for sr in range(3):
            c.setFillColor(PALE_BG); c.setStrokeColor(DARK_GRAY)
            c.rect(*pp(origin,x0+14,y0+16+sr*36), 180*SCALE, 18*SCALE, stroke=1, fill=1)

    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Structural Columns + Grid
# ─────────────────────────────────────────────────────────────────────────────
def draw_columns_grid(c, origin, level):
    cols = COLUMNS_GF if level == "GF" else COLUMNS_FF

    x_grids = [("A",6),("B",132),("C",276),("D",408),("E",516),("F",666)]
    if level == "GF": x_grids.append(("P",762))

    y_grids = [("1",6),("2",180),("3",252),("4",414),("5",684),("6",900),("7",1080)]
    if level == "FF": y_grids.append(("8",1122))

    min_y = 6; max_y = 1080 if level=="GF" else 1122
    min_x = 6; max_x = 762 if level=="GF" else 666

    c.saveState()

    # Grid lines (thin red dashed)
    c.setStrokeColor(GRID_RED); c.setLineWidth(0.45); c.setDash(7,4)
    for _, gx in x_grids:
        p1 = pp(origin, gx, min_y-50)
        p2 = pp(origin, gx, max_y+50)
        c.line(p1[0], p1[1], p2[0], p2[1])
    for _, gy in y_grids:
        p1 = pp(origin, min_x-50, gy)
        p2 = pp(origin, max_x+50, gy)
        c.line(p1[0], p1[1], p2[0], p2[1])
    c.setDash()

    # Grid bubbles
    for tag, gx in x_grids:
        for sign in [-1,+1]:
            bx, by = pp(origin, gx, min_y-50 if sign<0 else max_y+50)
            c.setFillColor(colors.white); c.setStrokeColor(GRID_RED); c.setLineWidth(1)
            c.circle(bx, by+sign*2, 9, stroke=1, fill=1)
            c.setFillColor(GRID_RED); c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString(bx, by+sign*2-3, tag)
    for tag, gy in y_grids:
        for sign in [-1,+1]:
            bx, by_ = pp(origin, min_x-50 if sign<0 else max_x+50, gy)
            c.setFillColor(colors.white); c.setStrokeColor(GRID_RED); c.setLineWidth(1)
            c.circle(bx+sign*2, by_, 9, stroke=1, fill=1)
            c.setFillColor(GRID_RED); c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString(bx+sign*2, by_-3, tag)

    # RCC Columns — solid charcoal with cross-hatch
    for col in cols:
        cx_, cy_ = col["x"], col["y"]
        cw, ch   = col["w"], col["h"]
        px, py   = pp(origin, cx_-cw/2, cy_-ch/2)
        pw, ph   = cw*SCALE, ch*SCALE

        c.setFillColor(COL_FILL); c.setStrokeColor(COL_STROKE); c.setLineWidth(0.9)
        c.rect(px, py, pw, ph, stroke=1, fill=1)
        # Cross-hatch lines
        c.setStrokeColor(COL_HATCH); c.setLineWidth(0.35)
        c.line(px, py, px+pw, py+ph)
        c.line(px, py+ph, px+pw, py)
        # Column ID
        c.setFillColor(GRID_RED); c.setFont("Helvetica-Bold", 5)
        c.drawCentredString(px+pw/2, py+ph+3, col["id"])

    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Space Zone Fill (rich Lumion palette)
# ─────────────────────────────────────────────────────────────────────────────
def zone_fill(space) -> object:
    n = space["name"]
    f = space.get("finish","public")
    if "Dais" in n or "Speaker" in n: return FILL_DAIS
    if "Assembly Hall" in n: return FILL_PUBLIC
    if "Reading Room" in n or "Stack" in n or "Discussion" in n or "Computer" in n: return FILL_READING
    if f == "circulation" or "Stair" in n: return FILL_CIRCULATION
    if f == "service" or "Toilet" in n or "Pantry" in n or "Store" in n: return FILL_SERVICE
    return FILL_PUBLIC


# ─────────────────────────────────────────────────────────────────────────────
# Draw one complete floor plan sheet
# ─────────────────────────────────────────────────────────────────────────────
def draw_floor_sheet(c, site, plans, level, sheet_no, sheet_title, mode):
    spaces  = [s for s in plans["spaces"] if s["level"]==level]
    sp_by_id = {s["id"]:s for s in spaces}

    variant_label = {
        "bare":      "ARCHITECTURAL FLOOR PLAN  (WITHOUT FURNITURE)",
        "furniture": "PRESENTATION FLOOR PLAN  (WITH FURNITURE)",
        "columns":   "STRUCTURAL COLUMN & GRID COORDINATION PLAN  (WITH COLUMNS)",
    }[mode]
    level_name = next(l["name"] for l in site["levels"] if l["id"]==level)

    # ── Page setup
    c.setTitle(f"{site['project']['name']} — {sheet_title} — {mode.upper()}")
    c.setAuthor("Bar Association Architectural Team, Banswara")

    # ── Full-page Lumion background gradient feel
    c.setFillColor(colors.HexColor("#f0f4f8"))
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    # Border (already drawn via title block; skip double-draw, draw subtle here)
    c.setStrokeColor(BLACK); c.setLineWidth(1.6)
    c.rect(18, 18, PAGE_W-36, PAGE_H-36, stroke=1, fill=0)
    c.setLineWidth(0.45); c.setStrokeColor(LIGHT_GRAY)
    c.rect(24, 24, PAGE_W-48, PAGE_H-48, stroke=1, fill=0)

    # ── Sheet header (inside top border)
    c.setFillColor(CHARCOAL)
    c.rect(26, PAGE_H-106, PAGE_W-52, 80, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 16)
    c.drawString(44, PAGE_H-62, f"{sheet_no}  |  {sheet_title.upper()}")
    c.setFont("Helvetica-Bold", 8.5); c.setFillColor(GLASS_BLUE)
    c.drawString(44, PAGE_H-80, variant_label)
    c.setFont("Helvetica", 7.5); c.setFillColor(LIGHT_GRAY)
    c.drawString(44, PAGE_H-95, "BANSWARA DISTRICT COURT COMPLEX  ·  COORDINATED ARCHITECTURAL SCHEMATIC")

    # ── Layout constants ──────────────────────────────────────────────────────
    HEADER_H  = 80    # top header bar height
    TB_H      = 88    # title block height at bottom
    STRIP_W   = 310   # right info strip width
    MARGIN_L  = 32    # left margin inside border
    MARGIN_R  = 14    # right margin inside border (between strip and border)
    MARGIN_T  = 10    # gap below header
    MARGIN_B  = 10    # gap above title block

    # Pixel boundaries for drawing area (plan zone)
    draw_area_x0 = 18 + MARGIN_L
    draw_area_x1 = PAGE_W - 18 - MARGIN_R - STRIP_W - 8
    draw_area_y0 = 18 + TB_H + MARGIN_B
    draw_area_y1 = PAGE_H - 26 - HEADER_H - MARGIN_T
    draw_area_w  = draw_area_x0 - draw_area_x0 + (draw_area_x1 - draw_area_x0)
    draw_area_h  = draw_area_y1 - draw_area_y0

    # Plan model extents
    plan_x0 = min(s["rect"][0] for s in spaces)
    plan_y0 = min(s["rect"][1] for s in spaces)
    plan_x1 = max(s["rect"][2] for s in spaces)
    plan_y1 = max(s["rect"][3] for s in spaces)
    plan_w  = plan_x1 - plan_x0
    plan_h  = plan_y1 - plan_y0

    # Fit-to-area scale — maximise plan, no arbitrary cap
    global SCALE
    SCALE = min((draw_area_x1 - draw_area_x0) / plan_w,
                draw_area_h / plan_h) * 0.96

    # Centre plan in drawing area
    draw_w = plan_w * SCALE
    draw_h = plan_h * SCALE
    orig_x = draw_area_x0 + ((draw_area_x1 - draw_area_x0) - draw_w) / 2
    orig_y = draw_area_y0 + (draw_area_h - draw_h) / 2
    origin = (orig_x - plan_x0*SCALE, orig_y - plan_y0*SCALE)

    # ── 1. Columns & Grid (below everything if in columns mode, drawn first)
    if mode == "columns":
        draw_columns_grid(c, origin, level)

    # ── 2. Space zone fills (floor colours ONLY — no wall strokes here)
    for space in spaces:
        x0_, y0_, x1_, y1_ = rect(space)
        sx, sy = pp(origin, x0_, y0_)
        sw, sh = (x1_-x0_)*SCALE, (y1_-y0_)*SCALE
        c.setFillColor(zone_fill(space))
        c.setStrokeColor(colors.HexColor("#94a3b8")); c.setLineWidth(0.3)
        c.rect(sx, sy, sw, sh, stroke=0, fill=1)

    # ── 3. Furniture (before walls so walls sit on top)
    if mode == "furniture":
        for space in spaces:
            draw_furniture(c, origin, space)

    # ── 4. ARCHITECTURAL WALLS — filled solid dark charcoal with hatch
    # Wall thickness from model data (inches)
    WT      = float(plans.get("wallThickness", 6))   # 6" = inner partitions
    OWT     = WT * 2                                  # 12" = outer perimeter wall
    WT_pt   = WT   * SCALE
    OWT_pt  = OWT  * SCALE

    WALL_FILL_CLR   = colors.HexColor("#2c2c2c")   # near-black fill
    WALL_HATCH_CLR  = colors.HexColor("#555555")   # subtle hatch lines
    COL_FILL_CLR    = colors.HexColor("#8b1a1a")   # dark red RCC column

    def filled_wall(ax0, ay0, ax1, ay1, hatch=True):
        """Draw a filled wall rectangle with optional diagonal hatch."""
        wx, wy = pp(origin, ax0, ay0)
        ww = (ax1-ax0)*SCALE
        wh = (ay1-ay0)*SCALE
        if ww == 0 or wh == 0:
            return
        c.setFillColor(WALL_FILL_CLR); c.setStrokeColor(WALL_FILL_CLR); c.setLineWidth(0)
        c.rect(wx, wy, ww, wh, stroke=0, fill=1)
        if hatch and abs(ww) > 2 and abs(wh) > 2:
            c.setStrokeColor(WALL_HATCH_CLR); c.setLineWidth(0.35)
            gap = max(3, min(ww, wh) / 3)
            # Diagonal hatch lines at 45°
            n_lines = int((abs(ww) + abs(wh)) / gap) + 2
            for i in range(n_lines):
                hx0 = wx + i*gap;       hy0 = wy
                hx1 = wx;               hy1 = wy + i*gap
                # Clip to rect
                c.line(max(wx, hx0), max(wy, hy0),
                       min(wx+ww, hx1+ww), min(wy+wh, hy1+wh))

    def rcc_column(cx, cy, cw, ch):
        """Draw a solid RCC column square at model coords."""
        px_, py_ = pp(origin, cx, cy)
        pw_ = cw*SCALE; ph_ = ch*SCALE
        c.setFillColor(COL_FILL_CLR); c.setStrokeColor(WALL_FILL_CLR); c.setLineWidth(0.5)
        c.rect(px_, py_, pw_, ph_, stroke=1, fill=1)
        # Cross hatch
        c.setStrokeColor(colors.HexColor("#3d0000")); c.setLineWidth(0.5)
        c.line(px_, py_, px_+pw_, py_+ph_)
        c.line(px_+pw_, py_, px_, py_+ph_)

    # Build wall segments from space boundaries
    # Strategy: for every space edge, draw a wall band of appropriate thickness
    # Outer perimeter = OWT, internal boundaries = WT
    ext_x0 = min(s["rect"][0] for s in spaces)
    ext_y0 = min(s["rect"][1] for s in spaces)
    ext_x1 = max(s["rect"][2] for s in spaces)
    ext_y1 = max(s["rect"][3] for s in spaces)

    # ── Outer perimeter walls (12" thick) — draw as 4 filled bands
    # South wall
    filled_wall(ext_x0-OWT, ext_y0-OWT, ext_x1+OWT, ext_y0)
    # North wall
    filled_wall(ext_x0-OWT, ext_y1,     ext_x1+OWT, ext_y1+OWT)
    # West wall
    filled_wall(ext_x0-OWT, ext_y0,     ext_x0,     ext_y1)
    # East wall
    filled_wall(ext_x1,     ext_y0,     ext_x1+OWT, ext_y1)

    # ── Internal partition walls (6" thick)
    # Collect all unique internal wall lines from space edges
    # Each space rect edge that is NOT on the outer perimeter is an internal wall
    internal_walls = set()  # store as (x0,y0,x1,y1) tuples normalised
    for space in spaces:
        sx_, sy_, sx1, sy1 = (float(v) for v in space["rect"])
        edges = [
            (sx_, sy_, sx1, sy_),   # south edge
            (sx_, sy1, sx1, sy1),   # north edge
            (sx_, sy_, sx_, sy1),   # west edge
            (sx1, sy_, sx1, sy1),   # east edge
        ]
        for ex0, ey0, ex1, ey1 in edges:
            # Skip outer perimeter edges
            on_perim = (
                (ey0 == ey1 == ext_y0) or (ey0 == ey1 == ext_y1) or
                (ex0 == ex1 == ext_x0) or (ex0 == ex1 == ext_x1)
            )
            if not on_perim:
                key = (min(ex0,ex1), min(ey0,ey1), max(ex0,ex1), max(ey0,ey1))
                internal_walls.add(key)

    for wx0, wy0, wx1, wy1 in internal_walls:
        if wx0 == wx1:  # vertical wall
            filled_wall(wx0, wy0, wx0+WT, wy1)
        else:           # horizontal wall
            filled_wall(wx0, wy0, wx1, wy0+WT)

    # ── Outer perimeter stroke on top (crisp outer boundary)
    px0_, py0_ = pp(origin, ext_x0-OWT, ext_y0-OWT)
    pw_  = (ext_x1-ext_x0+2*OWT)*SCALE
    ph_  = (ext_y1-ext_y0+2*OWT)*SCALE
    c.setStrokeColor(WALL_FILL_CLR); c.setLineWidth(WALL_THICK+1); c.setFillColor(colors.Color(0,0,0,0))
    c.rect(px0_, py0_, pw_, ph_, stroke=1, fill=0)

    # ── RCC columns at all outer corners + major junctions
    col_sz = OWT   # column size = wall thickness
    # 4 outer corners
    for ccx, ccy in [
        (ext_x0-OWT, ext_y0-OWT), (ext_x1, ext_y0-OWT),
        (ext_x0-OWT, ext_y1),     (ext_x1, ext_y1),
    ]:
        rcc_column(ccx, ccy, col_sz, col_sz)

    # Mid-wall junction columns (where internal walls meet outer wall)
    for space in spaces:
        sx_, sy_, sx1, sy1 = (float(v) for v in space["rect"])
        for jx, jy in [(sx_,sy_),(sx1,sy_),(sx_,sy1),(sx1,sy1)]:
            # Only at internal junctions (not outer corners)
            is_outer = (
                (jx == ext_x0 and jy == ext_y0) or (jx == ext_x1 and jy == ext_y0) or
                (jx == ext_x0 and jy == ext_y1) or (jx == ext_x1 and jy == ext_y1)
            )
            if not is_outer:
                rcc_column(jx - WT/2, jy - WT/2, WT, WT)

    # ── 5. Doors
    for op in plans["openings"]:
        if op["level"]==level and op["hostSpace"] in sp_by_id:
            draw_door(c, origin, sp_by_id[op["hostSpace"]], op)

    # ── 6. Windows
    for win in plans["windows"]:
        if win["level"]==level and win["hostSpace"] in sp_by_id:
            draw_window(c, origin, sp_by_id[win["hostSpace"]], win)

    # ── 7. Staircase
    stair_sp = next((s for s in spaces if s.get("stairId")=="STAIR-01"), None)
    if stair_sp:
        draw_stair(c, origin, stair_sp, plans["stairs"][0])

    # ── 8. Entrance porch (East long wall)
    draw_porch(c, origin, plans, spaces, level)

    # ── 9. Room badge labels (drawn last so they sit on top)
    for space in spaces:
        x0_, y0_, x1_, y1_ = rect(space)
        sw = (x1_-x0_)*SCALE
        sh = (y1_-y0_)*SCALE
        badge_cx = pp(origin, (x0_+x1_)/2, 0)[0]
        badge_cy = pp(origin, 0, (y0_+y1_)/2)[1]

        # Adjust badge Y for tall rooms
        if "Assembly" in space["name"]:
            badge_cy = pp(origin, 0, y0_+310)[1]
        elif "Reading Room" in space["name"]:
            badge_cy = pp(origin, 0, y0_+200)[1]
        elif "Stack" in space["name"]:
            badge_cy = pp(origin, 0, y0_+80)[1]
        elif "Dais" in space["name"]:
            badge_cy = pp(origin, 0, y0_+32)[1]
        elif "Pantry" in space["name"]:
            badge_cy = pp(origin, 0, y1_-22)[1]
        elif "Toilet" in space["name"]:
            badge_cy = pp(origin, 0, y1_-26)[1]

        bw = min(sw-6, 160)
        bh = 34

        c.setFillColor(colors.white); c.setStrokeColor(LIGHT_GRAY); c.setLineWidth(0.7)
        c.roundRect(badge_cx-bw/2, badge_cy-bh/2, bw, bh, 3, stroke=1, fill=1)

        c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 7.5 if bw>120 else 6.5)
        c.drawCentredString(badge_cx, badge_cy+8, space["name"].upper()[:26])
        c.setFont("Helvetica-Bold", 6); c.setFillColor(DARK_GRAY)
        x0_, y0_, x1_, y1_ = rect(space)
        c.drawCentredString(badge_cx, badge_cy-0, f"{fmtft(x1_-x0_)} × {fmtft(y1_-y0_)}")
        c.setFont("Helvetica", 5.8); c.setFillColor(GRAY)
        c.drawCentredString(badge_cx, badge_cy-10, f"{space['id']}  ·  {sqft(space):,.1f} sq.ft.")

    # ── 10. Overall Dimensions
    draw_dim(c, origin,
             (ext_x0, ext_y0), (ext_x1, ext_y0), (0,-46),
             f"OVERALL WIDTH = {fmtft(ext_x1-ext_x0)}")
    draw_dim(c, origin,
             (ext_x0, ext_y0), (ext_x0, ext_y1), (-56,0),
             f"OVERALL LENGTH = {fmtft(ext_y1-ext_y0)}")

    # ── 11. Ancillaries — right strip (north rose, scale bar, legend, schedule)
    strip_x   = PAGE_W - 18 - MARGIN_R - STRIP_W
    strip_top = PAGE_H - 26 - HEADER_H - MARGIN_T   # top of strip
    strip_bot = 18 + TB_H + MARGIN_B                 # bottom of strip

    # Separator line between plan and strip
    c.setStrokeColor(LIGHT_GRAY); c.setLineWidth(0.7)
    c.line(strip_x - 6, strip_bot, strip_x - 6, strip_top)

    # North rose (top-right of strip)
    north_cx = strip_x + STRIP_W - 36
    north_cy = strip_top - 44
    draw_north(c, north_cx, north_cy)

    # Scale bar (below north rose)
    draw_scale_bar(c, strip_x + 8, strip_top - 76)

    # Legend panel (below scale bar)
    legend_h = 218
    legend_y  = strip_top - 76 - 16 - legend_h
    draw_legend(c, strip_x, legend_y, mode)

    # Schedule / column schedule (above title block)
    if mode == "columns":
        sched_h = 15 * (3 + 3)   # 3 col types + headers
        sched_y = strip_bot + 4
        draw_col_schedule(c, strip_x, sched_y)
    else:
        sched_h = 15 * (len(spaces) + 2)
        sched_y = strip_bot + 4
        draw_schedule(c, strip_x, sched_y, spaces)

    # ── 12. Title block (bottom band)
    draw_title_block(c, sheet_no, sheet_title, level_name, variant_label)

    c.showPage()


# ─────────────────────────────────────────────────────────────────────────────
# Cover / Index Sheet
# ─────────────────────────────────────────────────────────────────────────────
SHEETS = [
    ("A-101","GROUND FLOOR PLAN","GF","bare"),
    ("A-201","GROUND FLOOR PLAN","GF","furniture"),
    ("S-101","GROUND FLOOR PLAN","GF","columns"),
    ("A-102","FIRST FLOOR PLAN","FF","bare"),
    ("A-202","FIRST FLOOR PLAN","FF","furniture"),
    ("S-102","FIRST FLOOR PLAN","FF","columns"),
]

def draw_cover(c, site, plans):
    c.setTitle(f"{site['project']['name']} — Master Review Set")
    c.setAuthor("Bar Association Architectural Team, Banswara")

    # Background
    c.setFillColor(CHARCOAL)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    # Top accent band
    c.setFillColor(ACCENT_BLUE)
    c.rect(0, PAGE_H-12, PAGE_W, 12, stroke=0, fill=1)
    c.setFillColor(PORCH_AMBER)
    c.rect(0, PAGE_H-20, PAGE_W, 8, stroke=0, fill=1)

    # Main title
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(PAGE_W/2, PAGE_H-100, "BAR ASSOCIATION HALL")
    c.setFont("Helvetica-Bold", 17); c.setFillColor(GLASS_BLUE)
    c.drawCentredString(PAGE_W/2, PAGE_H-130, "DISTRICT COURT COMPLEX, BANSWARA, RAJASTHAN")
    c.setFont("Helvetica", 11); c.setFillColor(LIGHT_GRAY)
    c.drawCentredString(PAGE_W/2, PAGE_H-152, "COMPREHENSIVE ARCHITECTURAL & STRUCTURAL REVIEW SET  ·  G+1 BUILDING")

    # Separator rule
    c.setStrokeColor(PORCH_AMBER); c.setLineWidth(1.2)
    c.line(80, PAGE_H-168, PAGE_W-80, PAGE_H-168)

    # Project info grid
    proj_items = [
        ("PROJECT",          "Bar Association Hall, Banswara"),
        ("LOCATION",         "District Court Complex, Banswara, Rajasthan, India"),
        ("BUILDING TYPE",    "Bar Association Hall — G+1 (Ground + First Floor)"),
        ("PLANNING AREA",    "4,427.50 sq.ft. per floor (Setback Envelope)"),
        ("MAIN ENTRANCE",    "East Long Wall — 12'-0\" × 8'-0\" Covered Porch"),
        ("FENESTRATION",     "All Four Facades (North, South, East, West)"),
        ("STRUCTURE",        "RCC Framed — IS 456:2000 / IS 1893:2016"),
        ("SCALE",            '1/8" = 1\'-0"  |  Sheet: A2 Landscape'),
        ("DATE",             datetime.now(timezone.utc).strftime("%d-%b-%Y").upper()),
        ("REVISION",         "P01 — Approved Schematic"),
        ("STATUS",           "APPROVED SCHEMATIC DESIGN — NOT FOR CONSTRUCTION"),
    ]
    box_x, box_y = 80, PAGE_H-480
    box_w = PAGE_W-160
    row_h = 26
    c.setFillColor(colors.HexColor("#1e3a5f")); c.setStrokeColor(ACCENT_BLUE); c.setLineWidth(0.6)
    c.roundRect(box_x, box_y, box_w, len(proj_items)*row_h+16, 6, stroke=1, fill=1)
    for i, (k, v) in enumerate(proj_items):
        ry = box_y + len(proj_items)*row_h - i*row_h + 4
        if i % 2 == 0:
            c.setFillColor(colors.HexColor("#162d4a"))
            c.rect(box_x+1, ry-row_h+3, box_w-2, row_h-1, stroke=0, fill=1)
        c.setFillColor(PORCH_AMBER); c.setFont("Helvetica-Bold", 8)
        c.drawString(box_x+12, ry-12, k)
        c.setFillColor(colors.white); c.setFont("Helvetica", 8)
        c.drawString(box_x+160, ry-12, v)

    # Sheet index
    idx_y = box_y - 40
    c.setFillColor(GLASS_BLUE); c.setFont("Helvetica-Bold", 11)
    c.drawString(box_x, idx_y, "SHEET INDEX")
    c.setStrokeColor(GLASS_BLUE); c.setLineWidth(0.8)
    c.line(box_x, idx_y-4, box_x+150, idx_y-4)

    col_w = (box_w)/len(SHEETS)
    for i,(sno,stitle,lv,md) in enumerate(SHEETS):
        sx = box_x + i*col_w
        sy = idx_y - 70
        c.setFillColor(colors.HexColor("#1e3a5f")); c.setStrokeColor(ACCENT_BLUE); c.setLineWidth(0.6)
        c.roundRect(sx+4, sy, col_w-8, 62, 4, stroke=1, fill=1)
        c.setFillColor(ACCENT_BLUE if "A-" in sno else PORCH_AMBER)
        c.roundRect(sx+4, sy+44, col_w-8, 18, 4, stroke=0, fill=1)
        c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(sx+col_w/2, sy+50, sno)
        c.setFont("Helvetica", 7); c.setFillColor(LIGHT_GRAY)
        c.drawCentredString(sx+col_w/2, sy+32, stitle)
        c.drawCentredString(sx+col_w/2, sy+20, "GF" if lv=="GF" else "FF")
        mode_lbl = {"bare":"BARE / NO FURN.","furniture":"WITH FURNITURE","columns":"WITH COLUMNS"}[md]
        c.setFillColor(GLASS_BLUE); c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(sx+col_w/2, sy+8, mode_lbl)

    # Bottom strip
    c.setFillColor(PORCH_AMBER)
    c.rect(0, 0, PAGE_W, 10, stroke=0, fill=1)
    c.setFillColor(ACCENT_BLUE)
    c.rect(0, 10, PAGE_W, 8, stroke=0, fill=1)

    c.showPage()


# ─────────────────────────────────────────────────────────────────────────────
# DXF export helper
# ─────────────────────────────────────────────────────────────────────────────
def export_dxf(plans, level, sheet_no, mode):
    doc = ezdxf.new(dxfversion="R2010")
    doc.units = dxf_units.MM
    msp = doc.modelspace()

    layers = {
        "WALLS":     {"color": 7,  "ltype": "CONTINUOUS", "lw": 50},
        "ROOMS":     {"color": 8,  "ltype": "CONTINUOUS", "lw": 18},
        "DOORS":     {"color": 1,  "ltype": "CONTINUOUS", "lw": 25},
        "WINDOWS":   {"color": 5,  "ltype": "CONTINUOUS", "lw": 18},
        "COLUMNS":   {"color": 7,  "ltype": "CONTINUOUS", "lw": 50},
        "GRID":      {"color": 1,  "ltype": "DASHED",     "lw": 13},
        "DIM":       {"color": 4,  "ltype": "CONTINUOUS", "lw": 13},
        "TEXT":      {"color": 7,  "ltype": "CONTINUOUS", "lw": 13},
        "FURNITURE": {"color": 8,  "ltype": "CONTINUOUS", "lw": 13},
        "PORCH":     {"color": 40, "ltype": "CONTINUOUS", "lw": 25},
    }
    for lname, lattr in layers.items():
        if lname not in doc.layers:
            lay = doc.layers.new(lname)
            lay.color = lattr["color"]
            lay.lineweight = lattr["lw"]

    # inch → mm (1 inch = 25.4 mm)
    def m(v): return float(v) * 25.4

    spaces = [s for s in plans["spaces"] if s["level"]==level]
    for space in spaces:
        x0,y0,x1,y1 = rect(space)
        pts = [(m(x0),m(y0)),(m(x1),m(y0)),(m(x1),m(y1)),(m(x0),m(y1)),(m(x0),m(y0))]
        msp.add_lwpolyline(pts, close=False, dxfattribs={"layer":"WALLS"})
        # Room text
        cx = (m(x0)+m(x1))/2; cy = (m(y0)+m(y1))/2
        msp.add_text(space["name"], dxfattribs={"layer":"TEXT","height":100,"insert":(cx,cy)})
        msp.add_text(f'{fmtft(x1-x0)} x {fmtft(y1-y0)}',
                     dxfattribs={"layer":"TEXT","height":70,"insert":(cx,cy-150)})

    # Doors
    sp_map = {s["id"]:s for s in spaces}
    for op in plans["openings"]:
        if op["level"]!=level or op["hostSpace"] not in sp_map: continue
        (p0m,p1m) = wall_pts(sp_map[op["hostSpace"]], op["wall"], op["offset"], op["width"])
        msp.add_line((m(p0m[0]),m(p0m[1])), (m(p1m[0]),m(p1m[1])),
                     dxfattribs={"layer":"DOORS"})

    # Windows
    for win in plans["windows"]:
        if win["level"]!=level or win["hostSpace"] not in sp_map: continue
        (p0m,p1m) = wall_pts(sp_map[win["hostSpace"]], win["wall"], win["offset"], win["width"])
        msp.add_line((m(p0m[0]),m(p0m[1])), (m(p1m[0]),m(p1m[1])),
                     dxfattribs={"layer":"WINDOWS"})

    # Columns (columns mode only)
    if mode == "columns":
        cols = COLUMNS_GF if level=="GF" else COLUMNS_FF
        for col in cols:
            cx_,cy_ = col["x"],col["y"]
            cw,ch   = col["w"]/2, col["h"]/2
            pts = [
                (m(cx_-cw),m(cy_-ch)),(m(cx_+cw),m(cy_-ch)),
                (m(cx_+cw),m(cy_+ch)),(m(cx_-cw),m(cy_+ch)),(m(cx_-cw),m(cy_-ch))
            ]
            msp.add_lwpolyline(pts, close=False, dxfattribs={"layer":"COLUMNS"})
            msp.add_text(col["id"], dxfattribs={"layer":"TEXT","height":60,
                          "insert":(m(cx_),m(cy_+ch+8))})

    path = CAD_OUT / f"{sheet_no}-{level}-{mode}.dxf"
    doc.saveas(str(path))
    return path.name


# ─────────────────────────────────────────────────────────────────────────────
# Delete old output files
# ─────────────────────────────────────────────────────────────────────────────
def clean_old_outputs():
    """Remove previous drawing PDFs and DXF files that are being superseded.
    Skips files that are currently open/locked (e.g. open in a PDF viewer)."""
    patterns = [
        PDF_OUT / "*.pdf",
        CAD_OUT / "*.dxf",
        CAD_OUT / "*.txt",
        ROOT / "standard" / "PDF" / "*.pdf",
        ROOT / "standard" / "CAD" / "*.dxf",
    ]
    deleted = []
    skipped = []
    for pat in patterns:
        for f in pat.parent.glob(pat.name):
            if "approved concept" in str(f).lower():
                continue
            try:
                f.unlink(missing_ok=True)
                deleted.append(f.name)
            except PermissionError:
                skipped.append(f.name)   # file open in viewer — skip silently
    if skipped:
        print(f"  [SKIP] {len(skipped)} file(s) in use (close PDF viewer to overwrite): {', '.join(skipped)}")
    return deleted


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # Load authoritative source model
    site  = json.loads((SRC / "site_plan.json").read_text(encoding="utf-8"))
    plans = json.loads((SRC / "preliminary_plans.json").read_text(encoding="utf-8"))

    # Clean up old outputs
    removed = clean_old_outputs()
    if removed:
        print(f"  Removed {len(removed)} old output file(s).")

    outputs = []
    individual_pdfs = []

    # ── Generate 6 individual sheet PDFs + 6 DXF files ──────────────────────
    for sheet_no, sheet_title, level, mode in SHEETS:
        pdf_name = f"{sheet_no}-{level}-{sheet_title.replace(' ','-')}-{mode.upper()}.pdf"
        pdf_path = PDF_OUT / pdf_name

        c = canvas.Canvas(str(pdf_path), pagesize=landscape(A2))
        c.setCreator("generate_lumion_drawings.py — Bar Association Hall")

        draw_floor_sheet(c, site, plans, level, sheet_no, sheet_title, mode)
        c.save()

        # DXF export
        dxf_name = export_dxf(plans, level, sheet_no, mode)

        outputs.append(pdf_name)
        outputs.append(dxf_name)
        individual_pdfs.append(pdf_path)
        print(f"  ✓  {pdf_name}")
        print(f"  ✓  {dxf_name}")

    # ── Master Review Set (cover + all 6 sheets) ─────────────────────────────
    master_tmp = PDF_OUT / "_cover_tmp.pdf"
    c = canvas.Canvas(str(master_tmp), pagesize=landscape(A2))
    c.setCreator("generate_lumion_drawings.py — Bar Association Hall")
    draw_cover(c, site, plans)
    c.save()

    master_path = PDF_OUT / "Bar-Association-Lumion-Master-Review-Set.pdf"
    writer = PdfWriter()
    for p in [master_tmp] + individual_pdfs:
        reader = PdfReader(str(p))
        for page in reader.pages:
            writer.add_page(page)
    with open(master_path, "wb") as f:
        writer.write(f)
    master_tmp.unlink(missing_ok=True)

    outputs.append(master_path.name)
    print(f"  ✓  {master_path.name}  (MASTER — 7 pages)")

    # ── Update manifest ───────────────────────────────────────────────────────
    src_bytes = (SRC / "preliminary_plans.json").read_bytes()
    manifest = {
        "project": "Bar Association Hall, Banswara",
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "generator": "generate_lumion_drawings.py",
        "sourceSha256": hashlib.sha256(src_bytes).hexdigest(),
        "status": "pass",
        "adoptedSetbackEnvelopeAreaSqFt": 4427.5,
        "mainEntranceLocation": "East Long Wall — 12'-0\" × 8'-0\" Covered Porch",
        "fenestration": "4-Sided (North, South, East, West)",
        "drawingSets": {
            "Set 1 — Architectural (No Furniture)":  ["A-101","A-102"],
            "Set 2 — Presentation (With Furniture)": ["A-201","A-202"],
            "Set 3 — Structural (With Columns)":     ["S-101","S-102"],
        },
        "outputs": outputs,
        "sheetSize": "A2 Landscape",
        "scale": "1/8\" = 1'-0\" (approx)",
        "notes": [
            "3 professional drawing sets produced from approved schematic source model.",
            "Main entrance on East long wall with 12'-0\" × 8'-0\" covered accessible porch.",
            "Windows on all four facades approved per design directive.",
            "Old confusing drawing files removed before generation.",
            "Source: standard/source/preliminary_plans.json + site_plan.json",
        ],
    }
    (ROOT / "standard_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    print()
    print("=" * 62)
    print("  BAR ASSOCIATION HALL — LUMION DRAWINGS COMPLETE")
    print("=" * 62)
    print(f"  PDF output folder : {PDF_OUT}")
    print(f"  CAD output folder : {CAD_OUT}")
    print(f"  Master review PDF : {master_path.name}")
    print()
    print("  DRAWING SETS:")
    print("  SET 1 — WITHOUT FURNITURE  : A-101 (GF), A-102 (FF)")
    print("  SET 2 — WITH FURNITURE     : A-201 (GF), A-202 (FF)")
    print("  SET 3 — WITH COLUMNS/GRID  : S-101 (GF), S-102 (FF)")
    print()


if __name__ == "__main__":
    main()
