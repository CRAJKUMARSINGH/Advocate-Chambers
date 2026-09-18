"""Generate Lumion-grade coordinated architectural and structural drawings (PDF & DXF).

Produces three distinct professional drawing sets:
1. Bare Architectural Plans (Without Furniture) - Sheets A-101.1 & A-102.1
2. Presentation Architectural Plans (With Furniture) - Sheets A-101.2 & A-102.2
3. Structural Coordination Plans (With Columns & Grid) - Sheets S-101 & S-102
Plus Master Review Set PDF with Executive Cover / Sheet Index.

Authoritative source: standard/source/preliminary_plans.json & site_plan.json.
Adopted planning setback-envelope area: 4,427.50 sq ft per floor.
Main entrance relocated to East long wall with 12'-0" x 8'-0" covered porch.
Windows detailed on all 4 elevations (North, South, East, West).
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import ezdxf
from ezdxf.enums import TextEntityAlignment
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A2, landscape
from reportlab.pdfgen import canvas

from drawing_model import area, inches_feet, load_model, rect, validate_model

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "standard" / "source" if (ROOT / "standard" / "source").exists() else ROOT / "source"
PDF_DIR = ROOT / "PDF"
CAD_DIR = ROOT / "CAD"
MANIFEST = ROOT / "standard_manifest.json"
PAGE_W, PAGE_H = landscape(A2)
SCALE = 0.80  # points per model inch (~1/8" = 1'-0" scale)

# Architectural Color Palette
BLACK = colors.HexColor("#0f172a")
DARK_GRAY = colors.HexColor("#334155")
GRAY = colors.HexColor("#64748b")
LIGHT_GRAY = colors.HexColor("#cbd5e1")
PALE_BG = colors.HexColor("#f8fafc")
PALE_PANEL = colors.HexColor("#f1f5f9")
WALL_FILL = colors.HexColor("#1e293b")
ACCENT_BLUE = colors.HexColor("#0284c7")
GLASS_BLUE = colors.HexColor("#38bdf8")
DOOR_RED = colors.HexColor("#b91c1c")
PORCH_AMBER = colors.HexColor("#d97706")
GRID_RED = colors.HexColor("#dc2626")
FURN_OUTLINE = colors.HexColor("#475569")
FURN_FILL = colors.HexColor("#e2e8f0")
FURN_SEAT = colors.HexColor("#cbd5e1")

# Structural Column Definitions
COLUMNS_GF = [
    # Grid A (West long wall, X=6)
    {"id": "C-01", "grid": "A-1", "x": 6, "y": 6, "w": 12, "h": 18, "desc": "SW Corner"},
    {"id": "C-02", "grid": "A-2", "x": 6, "y": 180, "w": 12, "h": 18, "desc": "Reception NW"},
    {"id": "C-03", "grid": "A-3", "x": 6, "y": 252, "w": 12, "h": 24, "desc": "Assembly SW"},
    {"id": "C-04", "grid": "A-4", "x": 6, "y": 468, "w": 12, "h": 24, "desc": "Assembly West Bay 1"},
    {"id": "C-05", "grid": "A-5", "x": 6, "y": 684, "w": 12, "h": 24, "desc": "Assembly West Bay 2"},
    {"id": "C-06", "grid": "A-6", "x": 6, "y": 900, "w": 12, "h": 24, "desc": "Dais Proscenium West"},
    {"id": "C-07", "grid": "A-7", "x": 6, "y": 1080, "w": 12, "h": 18, "desc": "Dais NW Corner"},
    # Grid B (Stair west wall, X=132)
    {"id": "C-08", "grid": "B-1", "x": 132, "y": 6, "w": 12, "h": 18, "desc": "Reception/Stair S"},
    {"id": "C-09", "grid": "B-3", "x": 132, "y": 246, "w": 12, "h": 18, "desc": "Stair NW"},
    # Grid C (Stair east wall, X=276)
    {"id": "C-10", "grid": "C-1", "x": 276, "y": 6, "w": 12, "h": 18, "desc": "Stair/Pantry S"},
    {"id": "C-11", "grid": "C-3", "x": 276, "y": 246, "w": 12, "h": 18, "desc": "Stair NE"},
    # Grid D (Pantry east / Toilet west, X=408)
    {"id": "C-12", "grid": "D-1", "x": 408, "y": 6, "w": 12, "h": 18, "desc": "Pantry/Toilet S"},
    {"id": "C-13", "grid": "D-2", "x": 408, "y": 204, "w": 12, "h": 18, "desc": "Toilet NW"},
    # Grid E (Toilet east, X=516)
    {"id": "C-14", "grid": "E-1", "x": 516, "y": 6, "w": 12, "h": 18, "desc": "Toilet SE"},
    {"id": "C-15", "grid": "E-2", "x": 516, "y": 204, "w": 12, "h": 18, "desc": "Toilet NE"},
    # Grid F (East long wall / Main Entrance, X=666)
    {"id": "C-16", "grid": "F-3", "x": 666, "y": 252, "w": 12, "h": 24, "desc": "Assembly SE"},
    {"id": "C-17", "grid": "F-4A", "x": 666, "y": 372, "w": 12, "h": 24, "desc": "Porch South Anchor"},
    {"id": "C-18", "grid": "F-4B", "x": 666, "y": 480, "w": 12, "h": 24, "desc": "Porch North Anchor"},
    {"id": "C-19", "grid": "F-5", "x": 666, "y": 684, "w": 12, "h": 24, "desc": "Assembly East Bay 2"},
    {"id": "C-20", "grid": "F-6", "x": 666, "y": 900, "w": 12, "h": 24, "desc": "Dais Proscenium East"},
    {"id": "C-21", "grid": "F-7", "x": 666, "y": 1080, "w": 12, "h": 18, "desc": "Dais NE Corner"},
    # Porch Canopy Columns
    {"id": "C-P1", "grid": "P-1", "x": 762, "y": 342, "w": 12, "h": 12, "desc": "Porch Outer South"},
    {"id": "C-P2", "grid": "P-2", "x": 762, "y": 486, "w": 12, "h": 12, "desc": "Porch Outer North"},
]

COLUMNS_FF = [
    # Grid A (West wall, X=6)
    {"id": "C-01", "grid": "A-1", "x": 6, "y": 6, "w": 12, "h": 18, "desc": "Librarian SW"},
    {"id": "C-02", "grid": "A-2", "x": 6, "y": 180, "w": 12, "h": 18, "desc": "Librarian NW"},
    {"id": "C-03", "grid": "A-3", "x": 6, "y": 252, "w": 12, "h": 24, "desc": "Reading Room SW"},
    {"id": "C-04", "grid": "A-4", "x": 6, "y": 468, "w": 12, "h": 24, "desc": "Reading Room Mid 1"},
    {"id": "C-05", "grid": "A-5", "x": 6, "y": 684, "w": 12, "h": 24, "desc": "Reading Room Mid 2"},
    {"id": "C-06", "grid": "A-6", "x": 6, "y": 774, "w": 12, "h": 24, "desc": "Stack Area SW"},
    {"id": "C-07", "grid": "A-7", "x": 6, "y": 996, "w": 12, "h": 18, "desc": "Discussion SW"},
    {"id": "C-08A", "grid": "A-8", "x": 6, "y": 1122, "w": 12, "h": 18, "desc": "Discussion NW Corner"},
    # Service Core (B, C, D, E)
    {"id": "C-08", "grid": "B-1", "x": 132, "y": 6, "w": 12, "h": 18, "desc": "Admin/Stair S"},
    {"id": "C-09", "grid": "B-3", "x": 132, "y": 246, "w": 12, "h": 18, "desc": "Stair NW"},
    {"id": "C-10", "grid": "C-1", "x": 276, "y": 6, "w": 12, "h": 18, "desc": "Stair/Pantry S"},
    {"id": "C-11", "grid": "C-3", "x": 276, "y": 246, "w": 12, "h": 18, "desc": "Stair NE"},
    {"id": "C-12", "grid": "D-1", "x": 408, "y": 6, "w": 12, "h": 18, "desc": "Pantry/Toilet S"},
    {"id": "C-13", "grid": "D-2", "x": 408, "y": 204, "w": 12, "h": 18, "desc": "Toilet NW"},
    {"id": "C-14", "grid": "E-1", "x": 516, "y": 6, "w": 12, "h": 18, "desc": "Toilet SE"},
    {"id": "C-15", "grid": "E-2", "x": 516, "y": 204, "w": 12, "h": 18, "desc": "Toilet NE"},
    # Grid F (East wall, X=666)
    {"id": "C-16", "grid": "F-3", "x": 666, "y": 252, "w": 12, "h": 24, "desc": "Reading Room SE"},
    {"id": "C-17", "grid": "F-4", "x": 666, "y": 468, "w": 12, "h": 24, "desc": "Reading Room East 1"},
    {"id": "C-18", "grid": "F-5", "x": 666, "y": 684, "w": 12, "h": 24, "desc": "Reading Room East 2"},
    {"id": "C-19", "grid": "F-6", "x": 666, "y": 774, "w": 12, "h": 24, "desc": "Stack Area SE"},
    {"id": "C-20", "grid": "F-7", "x": 666, "y": 996, "w": 12, "h": 18, "desc": "Store SE"},
    {"id": "C-21", "grid": "F-8", "x": 666, "y": 1122, "w": 12, "h": 18, "desc": "Store NE Corner"},
    # Intermediate North Boundary (Y=1122)
    {"id": "C-22", "grid": "C-8", "x": 228, "y": 1122, "w": 12, "h": 18, "desc": "Discussion/Computer N"},
    {"id": "C-23", "grid": "E-8", "x": 444, "y": 1122, "w": 12, "h": 18, "desc": "Computer/Store N"},
]


def pdf_point(origin: tuple[float, float], x: float, y: float) -> tuple[float, float]:
    return origin[0] + x * SCALE, origin[1] + y * SCALE


def draw_arrow(c: canvas.Canvas, x: float, y: float, angle: float, size: float = 7) -> None:
    c.saveState()
    c.translate(x, y)
    c.rotate(math.degrees(angle))
    path = c.beginPath()
    path.moveTo(0, 0)
    path.lineTo(-size, size / 2)
    path.lineTo(-size, -size / 2)
    path.close()
    c.setFillColor(BLACK)
    c.drawPath(path, fill=1, stroke=0)
    c.restoreState()


def draw_dimension(
    c: canvas.Canvas,
    origin: tuple[float, float],
    a: tuple[float, float],
    b: tuple[float, float],
    offset: tuple[float, float],
    label: str,
) -> None:
    ax, ay = pdf_point(origin, *a)
    bx, by = pdf_point(origin, *b)
    c.saveState()
    c.setStrokeColor(DARK_GRAY)
    c.setLineWidth(0.65)
    if abs(bx - ax) >= abs(by - ay):
        oy = min(ay, by) + offset[1]
        c.line(ax, ay, ax, oy)
        c.line(bx, by, bx, oy)
        c.line(ax, oy, bx, oy)
        draw_arrow(c, ax, oy, 0, 5)
        draw_arrow(c, bx, oy, math.pi, 5)
        tx, ty = (ax + bx) / 2, oy + 6
    else:
        ox = min(ax, bx) + offset[0]
        c.line(ax, ay, ox, ay)
        c.line(bx, by, ox, by)
        c.line(ox, ay, ox, by)
        draw_arrow(c, ox, ay, math.pi / 2, 5)
        draw_arrow(c, ox, by, -math.pi / 2, 5)
        tx, ty = ox - 14, (ay + by) / 2
    c.setFillColor(DARK_GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(tx, ty, label)
    c.restoreState()


def draw_north(c: canvas.Canvas, x: float, y: float) -> None:
    c.saveState()
    c.setStrokeColor(BLACK)
    c.setFillColor(BLACK)
    c.setLineWidth(1.2)
    c.circle(x, y + 10, 16, stroke=1, fill=0)
    # Compass needle
    path = c.beginPath()
    path.moveTo(x, y + 26)
    path.lineTo(x - 5, y + 10)
    path.lineTo(x, y - 6)
    path.close()
    c.setFillColor(BLACK)
    c.drawPath(path, fill=1, stroke=0)

    path2 = c.beginPath()
    path2.moveTo(x, y + 26)
    path2.lineTo(x + 5, y + 10)
    path2.lineTo(x, y - 6)
    path2.close()
    c.setFillColor(colors.HexColor("#94a3b8"))
    c.drawPath(path2, fill=1, stroke=0)

    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(x, y + 32, "N")
    c.setFont("Helvetica-Bold", 6.5)
    c.drawCentredString(x, y - 16, "PROJECT NORTH")
    c.restoreState()


def draw_scale_bar(c: canvas.Canvas, x: float, y: float) -> None:
    c.saveState()
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(BLACK)
    c.drawString(x, y + 14, 'GRAPHIC SCALE : 1/8" = 1\'-0"')
    ft_pt = 12 * SCALE
    lengths = [0, 10, 20, 30, 40]
    total_w = 40 * ft_pt
    c.setStrokeColor(BLACK)
    c.setLineWidth(1)
    c.rect(x, y, total_w, 4, stroke=1, fill=0)
    for i in range(4):
        x_seg = x + i * 10 * ft_pt
        if i % 2 == 0:
            c.setFillColor(BLACK)
            c.rect(x_seg, y, 10 * ft_pt, 4, stroke=0, fill=1)
    c.setFillColor(BLACK)
    c.setFont("Helvetica", 6)
    for ft in lengths:
        c.drawCentredString(x + ft * ft_pt, y - 8, f"{ft}'")
    c.restoreState()


def draw_title_block(
    c: canvas.Canvas,
    sheet: dict[str, Any],
    level_name: str,
    drawing_variant: str,
) -> None:
    x, y, w, h = 760, 32, PAGE_W - 796, 128
    c.saveState()
    c.setStrokeColor(BLACK)
    c.setLineWidth(1.2)
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.line(x, y + 36, x + w, y + 36)
    c.line(x + 230, y, x + 230, y + h)
    c.line(x + w - 170, y, x + w - 170, y + h)

    # Project Block
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(x + 14, y + h - 22, "BAR ASSOCIATION HALL")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#0369a1"))
    c.drawString(x + 14, y + h - 36, "DISTRICT COURT COMPLEX, BANSWARA")
    c.setFont("Helvetica", 7.5)
    c.setFillColor(GRAY)
    c.drawString(x + 14, y + h - 50, "RAJASTHAN, INDIA")
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x + 14, y + 14, "ADOPTED PLANNING SETBACK ENVELOPE: 4,427.50 SQ.FT.")

    # Drawing Title Block
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + 242, y + h - 22, sheet["title"].upper())
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#b91c1c") if "PRESENTATION" in drawing_variant.upper() else colors.HexColor("#047857"))
    c.drawString(x + 242, y + h - 38, drawing_variant.upper())
    c.setFont("Helvetica", 7.5)
    c.setFillColor(BLACK)
    c.drawString(x + 242, y + h - 54, f"LEVEL: {level_name.upper()}  |  SCALE: ~1/8\" = 1'-0\" (A2)")
    c.drawString(x + 242, y + 18, "MAIN ENTRY: EAST LONG WALL  |  4-SIDED FENESTRATION")
    c.drawString(x + 242, y + 6, "STATUS: APPROVED SCHEMATIC REVIEW  |  NOT FOR CONSTRUCTION")

    # Sheet Number Block
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(x + w - 85, y + 78, sheet["number"])
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(x + w - 85, y + 60, "SHEET NO.")
    c.setFont("Helvetica", 7)
    c.drawCentredString(x + w - 85, y + 20, "REV: P02 (APPROVED)")
    c.drawCentredString(x + w - 85, y + 8, datetime.now().strftime("%d-%b-%Y").upper())
    c.restoreState()


def draw_legend(c: canvas.Canvas, x: float, y: float, mode: str) -> None:
    c.saveState()
    c.setFillColor(PALE_PANEL)
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    w, h = 420, 200
    c.roundRect(x, y, w, h, 4, stroke=1, fill=1)
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(x + 14, y + h - 18, "GENERAL ARCHITECTURAL & PLANNING NOTES")
    c.setFont("Helvetica", 7.5)
    c.setFillColor(DARK_GRAY)
    lines = [
        "1. Adopted setback envelope area is 4,427.50 Sq. Ft. per floor (Site Plan brief).",
        "2. Main entrance is relocated to the East long wall with 12'-0\" x 8'-0\" covered porch.",
        "3. Accessible approach provided via barrier-free ramp (1:12 slope) & wide double door.",
        "4. 4-sided fenestration approved on North, South, East, and West perimeter facades.",
        "5. Door tags (D) and Window tags (W/V) correlate with opening schedule.",
        "6. Dog-leg stair consists of 18 risers (7.33\" rise, 10\" tread) with intermediate landing.",
        "7. Structure: RCC columns and beams designed per IS 456:2000 and IS 1893:2016.",
        "8. Verify all site dimensions against physical surveyor boundary before construction.",
    ]
    y_line = y + h - 34
    for line in lines:
        c.drawString(x + 14, y_line, line)
        y_line -= 14

    # Legend symbols
    c.setStrokeColor(BLACK)
    c.setLineWidth(2.2)
    c.line(x + 14, y + 16, x + 44, y + 16)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawString(x + 48, y + 14, "CUT WALL")

    c.setStrokeColor(DOOR_RED)
    c.setLineWidth(1)
    c.line(x + 105, y + 16, x + 130, y + 16)
    c.drawString(x + 134, y + 14, "DOOR / SWING")

    c.setStrokeColor(GLASS_BLUE)
    c.setLineWidth(1.5)
    c.line(x + 205, y + 16, x + 230, y + 16)
    c.drawString(x + 234, y + 14, "WINDOW")

    if mode == "columns":
        c.setFillColor(BLACK)
        c.rect(x + 300, y + 11, 10, 10, stroke=1, fill=1)
        c.drawString(x + 316, y + 14, "RCC COLUMN")
    elif mode == "furniture":
        c.setFillColor(FURN_SEAT)
        c.setStrokeColor(FURN_OUTLINE)
        c.rect(x + 300, y + 11, 10, 10, stroke=1, fill=1)
        c.drawString(x + 316, y + 14, "FURNITURE")
    c.restoreState()


def draw_schedule(c: canvas.Canvas, x: float, y: float, spaces: list[dict[str, Any]]) -> None:
    width = 420
    row_h = 17
    height = row_h * (len(spaces) + 2)
    c.saveState()
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.rect(x, y, width, height, stroke=1, fill=1)
    c.setFillColor(BLACK)
    c.rect(x, y + height - row_h, width, row_h, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 8, y + height - 12, "SCHEDULE OF ACCOMMODATION (SPACES)")
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x + 8, y + height - 26, "ID")
    c.drawString(x + 48, y + height - 26, "SPACE / ROOM NAME")
    c.drawString(x + 230, y + height - 26, "DIMENSIONS")
    c.drawRightString(x + width - 8, y + height - 26, "AREA (SQ.FT.)")
    c.setStrokeColor(colors.HexColor("#e2e8f0"))
    for index, space in enumerate(spaces):
        yy = y + height - row_h * (index + 3)
        c.line(x, yy, x + width, yy)
        c.setFillColor(BLACK)
        c.setFont("Helvetica", 7)
        c.drawString(x + 8, yy + 5, space["id"])
        c.drawString(x + 48, yy + 5, space["name"][:36])
        x0, y0, x1, y1 = rect(space)
        c.drawString(x + 230, yy + 5, f"{inches_feet(x1-x0)} × {inches_feet(y1-y0)}")
        c.drawRightString(x + width - 8, yy + 5, f"{area(space):,.1f}")
    c.restoreState()


def draw_column_schedule(c: canvas.Canvas, x: float, y: float, columns: list[dict[str, Any]]) -> None:
    width = 420
    row_h = 16
    unique_types = [
        {"type": "C1 (300×600mm / 12\"×24\")", "rebar": "8-T20 + 4-T16, Links T8@150 c/c", "use": "Main Hall Long Span Perimeter"},
        {"type": "C2 (300×450mm / 12\"×18\")", "rebar": "8-T16, Links T8@150 c/c", "use": "Service Core, Stair & Dais"},
        {"type": "CP (300×300mm / 12\"×12\")", "rebar": "4-T16, Links T8@150 c/c", "use": "Entrance Porch Canopy Posts"},
    ]
    height = row_h * (len(unique_types) + 4)
    c.saveState()
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.rect(x, y, width, height, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.rect(x, y + height - row_h, width, row_h, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 8, y + height - 12, "STRUCTURAL COLUMN SCHEDULE & SPECIFICATIONS")
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x + 8, y + height - 26, "MARK / SIZE")
    c.drawString(x + 140, y + height - 26, "MAIN REINFORCEMENT")
    c.drawString(x + 290, y + height - 26, "LOCATION / ZONE")
    c.setStrokeColor(colors.HexColor("#e2e8f0"))
    for index, col in enumerate(unique_types):
        yy = y + height - row_h * (index + 3)
        c.line(x, yy, x + width, yy)
        c.setFillColor(BLACK)
        c.setFont("Helvetica", 6.8)
        c.drawString(x + 8, yy + 5, col["type"])
        c.drawString(x + 140, yy + 5, col["rebar"])
        c.drawString(x + 290, yy + 5, col["use"])
    # Note at bottom
    c.setFont("Helvetica-Bold", 6.5)
    c.setFillColor(colors.HexColor("#b91c1c"))
    c.drawString(x + 8, y + 4, "Concrete Grade: M25 | Steel Grade: Fe500D | Foundation: Isolated RCC Footings")
    c.restoreState()


def wall_segment(space: dict[str, Any], wall: str, offset: float, width: float) -> tuple[tuple[float, float], tuple[float, float]]:
    x0, y0, x1, y1 = rect(space)
    if wall == "south":
        return (x0 + offset, y0), (x0 + offset + width, y0)
    if wall == "north":
        return (x0 + offset, y1), (x0 + offset + width, y1)
    if wall == "west":
        return (x0, y0 + offset), (x0, y0 + offset + width)
    return (x1, y0 + offset), (x1, y0 + offset + width)


def draw_door(c: canvas.Canvas, origin: tuple[float, float], space: dict[str, Any], door: dict[str, Any]) -> None:
    (x0, y0), (x1, y1) = wall_segment(space, door["wall"], door["offset"], door["width"])
    a = pdf_point(origin, x0, y0)
    b = pdf_point(origin, x1, y1)
    c.saveState()
    # Clear wall beneath door
    c.setStrokeColor(colors.white)
    c.setLineWidth(6.5)
    c.line(*a, *b)

    c.setStrokeColor(DOOR_RED)
    c.setLineWidth(0.85)
    wall = door["wall"]
    horizontal = wall in {"north", "south"}
    is_double = door["width"] >= 72

    if horizontal:
        if is_double:
            mid_pt = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            half_w = abs(b[0] - a[0]) / 2
            sign = 1 if (wall == "south" and door.get("swing") != "out") or (wall == "north" and door.get("swing") == "out") else -1
            c.line(a[0], a[1], a[0], a[1] + sign * half_w)
            c.arc(a[0] - half_w if sign < 0 else a[0], a[1] - half_w if sign < 0 else a[1], a[0] + half_w if sign > 0 else a[0], a[1] + half_w if sign > 0 else a[1], 0 if sign > 0 else 90, 90 if sign > 0 else 180)
            c.line(b[0], b[1], b[0], b[1] + sign * half_w)
            c.arc(b[0] - half_w, b[1] - half_w if sign < 0 else b[1], b[0], b[1] + half_w if sign > 0 else b[1], 90 if sign > 0 else 0, 180 if sign > 0 else 90)
            tag_x, tag_y = mid_pt[0], mid_pt[1] + sign * 12
        else:
            hinge = a
            sign = 1 if wall == "south" else -1
            if door.get("swing") == "out":
                sign *= -1
            leaf_end = (b[0], b[1] + sign * (b[0] - a[0]))
            c.line(*hinge, *leaf_end)
            radius = abs(b[0] - a[0])
            c.arc(hinge[0] - radius if sign < 0 else hinge[0], hinge[1] - radius if sign < 0 else hinge[1], hinge[0] + radius if sign > 0 else hinge[0], hinge[1] + radius if sign > 0 else hinge[1], 0 if sign > 0 else 90, 90 if sign > 0 else 180)
            tag_x, tag_y = (a[0] + b[0]) / 2, a[1] + sign * 11
    else:
        if is_double:
            mid_pt = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            half_w = abs(b[1] - a[1]) / 2
            sign = 1 if (wall == "east" and door.get("swing") == "out") or (wall == "west" and door.get("swing") != "out") else -1
            c.line(a[0], a[1], a[0] + sign * half_w, a[1])
            c.arc(a[0] - half_w if sign < 0 else a[0], a[1] - half_w if sign < 0 else a[1], a[0] + half_w if sign > 0 else a[0], a[1] + half_w if sign > 0 else a[1], 0 if sign > 0 else 90, 90 if sign > 0 else 180)
            c.line(b[0], b[1], b[0] + sign * half_w, b[1])
            c.arc(b[0] - half_w if sign < 0 else b[0], b[1] - half_w, b[0] + half_w if sign > 0 else b[0], b[1], 270 if sign > 0 else 180, 360 if sign > 0 else 270)
            tag_x, tag_y = mid_pt[0] + sign * 14, mid_pt[1]
        else:
            hinge = a
            sign = 1 if wall == "west" else -1
            if door.get("swing") == "out":
                sign *= -1
            leaf_end = (b[0] + sign * (b[1] - a[1]), b[1])
            c.line(*hinge, *leaf_end)
            radius = abs(b[1] - a[1])
            c.arc(hinge[0] - radius if sign < 0 else hinge[0], hinge[1] - radius if sign < 0 else hinge[1], hinge[0] + radius if sign > 0 else hinge[0], hinge[1] + radius if sign > 0 else hinge[1], 0 if sign > 0 else 90, 90 if sign > 0 else 180)
            tag_x, tag_y = a[0] + sign * 12, (a[1] + b[1]) / 2

    c.setFillColor(DOOR_RED)
    c.setFont("Helvetica-Bold", 6)
    c.drawCentredString(tag_x, tag_y, door["tag"])
    c.restoreState()


def draw_window(c: canvas.Canvas, origin: tuple[float, float], space: dict[str, Any], window: dict[str, Any]) -> None:
    (x0, y0), (x1, y1) = wall_segment(space, window["wall"], window["offset"], window["width"])
    a = pdf_point(origin, x0, y0)
    b = pdf_point(origin, x1, y1)
    c.saveState()
    # Mask wall opening
    c.setStrokeColor(colors.white)
    c.setLineWidth(7)
    c.line(*a, *b)

    # Architectural window: outer frame, inner glass pane
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.9)
    c.line(*a, *b)

    c.setStrokeColor(GLASS_BLUE)
    c.setLineWidth(1.8)
    wall = window["wall"]
    if wall in {"north", "south"}:
        c.line(a[0], a[1] + 2, b[0], b[1] + 2)
        c.setStrokeColor(DARK_GRAY)
        c.setLineWidth(0.6)
        c.line(a[0], a[1] - 3, b[0], b[1] - 3)
        tx = (a[0] + b[0]) / 2
        ty = a[1] - 11 if wall == "south" else a[1] + 10
    else:
        c.line(a[0] + 2, a[1], b[0] + 2, b[1])
        c.setStrokeColor(DARK_GRAY)
        c.setLineWidth(0.6)
        c.line(a[0] - 3, a[1], b[0] - 3, b[1])
        tx = a[0] - 13 if wall == "west" else a[0] + 13
        ty = (a[1] + b[1]) / 2

    # Draw small white background pill for window tag
    c.setFillColor(colors.white)
    c.setStrokeColor(ACCENT_BLUE)
    c.setLineWidth(0.4)
    tag_w = 16
    tag_h = 8
    c.roundRect(tx - tag_w / 2, ty - tag_h / 2 + 1, tag_w, tag_h, 2, stroke=1, fill=1)

    c.setFillColor(ACCENT_BLUE)
    c.setFont("Helvetica-Bold", 5.5)
    c.drawCentredString(tx, ty - 1, window["tag"])
    c.restoreState()


def draw_stair(c: canvas.Canvas, origin: tuple[float, float], stair_space: dict[str, Any], stair: dict[str, Any]) -> None:
    x0, y0, x1, y1 = rect(stair_space)
    ox, oy = pdf_point(origin, x0, y0)
    w = stair["width"] * SCALE
    run = (stair["riserCountPerFlight"] - 1) * stair["tread"] * SCALE
    lane_gap = 48 * SCALE
    c.saveState()
    c.setStrokeColor(BLACK)
    c.setLineWidth(1.1)

    # Flight 1 (UP) and Flight 2
    for base_y, direction in [(oy + 58 * SCALE, 1), (oy + 150 * SCALE, -1)]:
        left = ox + 10 * SCALE
        right = left + run
        c.line(left, base_y, right, base_y)
        c.line(left, base_y + w, right, base_y + w)
        for step in range(stair["riserCountPerFlight"]):
            xx = left + (step if direction == 1 else stair["riserCountPerFlight"] - 1 - step) * stair["tread"] * SCALE
            c.line(xx, base_y, xx, base_y + w)
        if direction == 1:
            c.line(left + 10, base_y + w / 2, right - 8, base_y + w / 2)
            draw_arrow(c, right - 8, base_y + w / 2, 0, 7)
        else:
            c.line(right - 10, base_y + w / 2, left + 8, base_y + w / 2)
            draw_arrow(c, left + 8, base_y + w / 2, math.pi, 7)

    landing_x = ox + 10 * SCALE + run
    landing_y = oy + 58 * SCALE
    c.setLineWidth(1.2)
    c.rect(landing_x, landing_y, stair["landingDepth"] * SCALE, lane_gap, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(BLACK)
    c.drawString(ox + 8, oy + 20, f'UP 18 RISERS @ {stair["riser"]:.2f}" / {stair["tread"]:.0f}" TREAD')
    c.drawString(ox + 8, oy + 10, f'FLOOR TO FLOOR = {inches_feet(stair["floorToFloor"])}')
    c.setFont("Helvetica-Bold", 6.5)
    c.drawCentredString(landing_x + (stair["landingDepth"] * SCALE) / 2, landing_y + lane_gap / 2, "MID LANDING")
    c.restoreState()


def draw_entry_features(
    c: canvas.Canvas,
    origin: tuple[float, float],
    plans: dict[str, Any],
    spaces: list[dict[str, Any]],
    level: str,
) -> None:
    space_by_id = {space["id"]: space for space in spaces}
    opening_by_id = {opening["id"]: opening for opening in plans["openings"]}
    for entry in plans.get("entries", []):
        if entry["level"] != level or entry["openingId"] not in opening_by_id:
            continue
        host = space_by_id.get(entry["hostSpace"])
        if not host:
            continue
        opening = opening_by_id[entry["openingId"]]
        (a_model, b_model) = wall_segment(host, opening["wall"], opening["offset"], opening["width"])
        a = pdf_point(origin, *a_model)
        b = pdf_point(origin, *b_model)
        mid_x, mid_y = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2

        c.saveState()
        c.setFillColor(PORCH_AMBER if entry["kind"] == "main" else DARK_GRAY)
        c.setStrokeColor(PORCH_AMBER if entry["kind"] == "main" else DARK_GRAY)
        c.setFont("Helvetica-Bold", 8 if entry["kind"] == "main" else 6.5)

        if entry["kind"] == "main" and entry.get("porch"):
            porch = entry["porch"]
            width = porch["width"]  # 144" along Y
            depth = porch["depth"]  # 96" along X (+X direction for East wall)
            cy_model = (a_model[1] + b_model[1]) / 2
            x0_model = max(a_model[0], b_model[0])  # East wall outer face
            y0_model = cy_model - width / 2

            px, py = pdf_point(origin, x0_model, y0_model)
            pw = depth * SCALE
            ph = width * SCALE

            # Porch slab & paving
            c.setFillColor(colors.HexColor("#fffbeb"))
            c.setStrokeColor(PORCH_AMBER)
            c.setLineWidth(1.2)
            c.rect(px, py, pw, ph, stroke=1, fill=1)

            # Porch canopy dashed overhang
            c.setDash(4, 3)
            c.rect(px - 4, py - 4, pw + 8, ph + 8, stroke=1, fill=0)
            c.setDash()

            # Steps along outer East edge of porch
            step_w = pw / 4
            c.setStrokeColor(colors.HexColor("#f59e0b"))
            c.setLineWidth(0.6)
            for s_idx in range(1, 4):
                c.line(px + s_idx * step_w, py, px + s_idx * step_w, py + ph)

            # Accessible ramp indication
            ramp_y = py + 8
            c.setFillColor(BLACK)
            c.setFont("Helvetica", 6)
            c.drawString(px + 6, ramp_y, "RAMP UP 1:12 ->")

            # Porch columns
            c.setFillColor(BLACK)
            c.rect(px + pw - 8, py + 4, 7, 7, stroke=1, fill=1)
            c.rect(px + pw - 8, py + ph - 11, 7, 7, stroke=1, fill=1)

            # Labels with clean white badge
            lbl_cx = px + pw * 0.60
            lbl_cy = py + ph / 2
            c.setFillColor(colors.white)
            c.setStrokeColor(PORCH_AMBER)
            c.setLineWidth(0.5)
            c.roundRect(lbl_cx - 48, lbl_cy - 16, 96, 32, 2, stroke=1, fill=1)

            c.setFillColor(BLACK)
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(lbl_cx, lbl_cy + 6, porch["label"])
            c.setFont("Helvetica-Bold", 6)
            c.setFillColor(PORCH_AMBER)
            c.drawCentredString(lbl_cx, lbl_cy - 4, "12'-0\" × 8'-0\" PORCH")
            c.setFont("Helvetica", 5)
            c.setFillColor(DARK_GRAY)
            c.drawCentredString(lbl_cx, lbl_cy - 12, "ACCESSIBLE RAMP & STEPS")
        else:
            # Secondary / VIP entrance label
            c.translate(mid_x + 18, mid_y)
            c.rotate(90)
            c.drawCentredString(0, 0, entry["label"])
        c.restoreState()


def draw_furniture(c: canvas.Canvas, origin: tuple[float, float], space: dict[str, Any]) -> None:
    x0, y0, x1, y1 = rect(space)
    s_name = space["name"]
    c.saveState()

    if "Assembly Hall" in s_name:
        c.setStrokeColor(FURN_OUTLINE)
        c.setFillColor(FURN_FILL)
        c.setLineWidth(0.5)

        row_count = 8
        for row in range(row_count):
            yy = y0 + 60 + row * 62
            # Left block benches (West side, X=40 to X=290)
            c.roundRect(*pdf_point(origin, x0 + 40, yy), 240 * SCALE, 16 * SCALE, 2, stroke=1, fill=1)
            for s in range(7):
                c.rect(*pdf_point(origin, x0 + 44 + s * 34, yy + 18), 24 * SCALE, 14 * SCALE, stroke=1, fill=1)

            # Right block benches (East side, X=376 to X=626)
            c.roundRect(*pdf_point(origin, x0 + 376, yy), 240 * SCALE, 16 * SCALE, 2, stroke=1, fill=1)
            for s in range(7):
                c.rect(*pdf_point(origin, x0 + 380 + s * 34, yy + 18), 24 * SCALE, 14 * SCALE, stroke=1, fill=1)

        c.setFont("Helvetica-Bold", 6)
        c.setFillColor(GRAY)
        c.drawCentredString(*pdf_point(origin, (x0 + x1) / 2, y0 + 300), "CENTRAL ACCESS AISLE (5'-0\" CLEAR)")

    elif "Dais" in s_name:
        c.setStrokeColor(colors.HexColor("#b45309"))
        c.setLineWidth(1.2)
        c.line(*pdf_point(origin, x0, y0 + 2), *pdf_point(origin, x1, y0 + 2))
        c.setFont("Helvetica-Bold", 6.5)
        c.setFillColor(colors.HexColor("#b45309"))
        c.drawString(*pdf_point(origin, x0 + 20, y0 + 8), "RAISED DAIS STAGE (+1'-6\" LEVEL)")

        # Main Executive Dais Table (24'-0" x 3'-6" = 288" x 42")
        c.setStrokeColor(BLACK)
        c.setFillColor(colors.HexColor("#fed7aa"))
        c.setLineWidth(0.8)
        c.roundRect(*pdf_point(origin, (x0 + x1) / 2 - 144, y0 + 50), 288 * SCALE, 42 * SCALE, 4, stroke=1, fill=1)

        # 7 High-back Dignitary Chairs behind Dais
        c.setFillColor(colors.HexColor("#ea580c"))
        for ch in range(7):
            cx = (x0 + x1) / 2 - 132 + ch * 42
            c.rect(*pdf_point(origin, cx, y0 + 98), 26 * SCALE, 22 * SCALE, stroke=1, fill=1)

        # Podiums on left and right of Dais
        c.setFillColor(colors.HexColor("#78350f"))
        c.rect(*pdf_point(origin, x0 + 60, y0 + 60), 32 * SCALE, 28 * SCALE, stroke=1, fill=1)
        c.rect(*pdf_point(origin, x1 - 92, y0 + 60), 32 * SCALE, 28 * SCALE, stroke=1, fill=1)
        c.setFont("Helvetica-Bold", 5)
        c.setFillColor(colors.white)
        c.drawCentredString(*pdf_point(origin, x0 + 76, y0 + 72), "PODIUM")
        c.drawCentredString(*pdf_point(origin, x1 - 76, y0 + 72), "PODIUM")

    elif "Reception" in s_name or "Librarian" in s_name:
        c.setStrokeColor(BLACK)
        c.setFillColor(FURN_FILL)
        c.setLineWidth(0.7)
        c.rect(*pdf_point(origin, x0 + 20, y0 + 40), 70 * SCALE, 24 * SCALE, stroke=1, fill=1)
        c.rect(*pdf_point(origin, x0 + 66, y0 + 64), 24 * SCALE, 40 * SCALE, stroke=1, fill=1)
        c.setFillColor(FURN_SEAT)
        c.circle(*pdf_point(origin, x0 + 44, y0 + 80), 8 * SCALE, stroke=1, fill=1)
        c.rect(*pdf_point(origin, x0 + 16, y0 + 130), 80 * SCALE, 26 * SCALE, stroke=1, fill=1)
        c.setFont("Helvetica", 5.5)
        c.setFillColor(DARK_GRAY)
        c.drawCentredString(*pdf_point(origin, x0 + 56, y0 + 142), "VISITOR LOUNGE")

    elif "Pantry" in s_name:
        c.setStrokeColor(BLACK)
        c.setFillColor(FURN_FILL)
        c.setLineWidth(0.7)
        c.rect(*pdf_point(origin, x0 + 10, y0 + 10), 96 * SCALE, 24 * SCALE, stroke=1, fill=1)
        c.rect(*pdf_point(origin, x0 + 20, y0 + 14), 16 * SCALE, 16 * SCALE, stroke=1, fill=0)
        c.rect(*pdf_point(origin, x0 + 40, y0 + 14), 16 * SCALE, 16 * SCALE, stroke=1, fill=0)
        c.setFont("Helvetica", 5.5)
        c.setFillColor(DARK_GRAY)
        c.drawString(*pdf_point(origin, x0 + 62, y0 + 18), "SINK & COUNTER")

    elif "Toilet" in s_name:
        c.setStrokeColor(colors.HexColor("#0284c7"))
        c.setFillColor(colors.white)
        c.setLineWidth(0.6)
        # WC pans
        p1 = pdf_point(origin, x0 + 16, y0 + 30)
        c.ellipse(p1[0], p1[1], p1[0] + 16 * SCALE, p1[1] + 22 * SCALE, stroke=1, fill=1)
        p2 = pdf_point(origin, x0 + 16, y0 + 80)
        c.ellipse(p2[0], p2[1], p2[0] + 16 * SCALE, p2[1] + 22 * SCALE, stroke=1, fill=1)
        # Wash basins
        p3 = pdf_point(origin, x0 + 60, y0 + 30)
        c.ellipse(p3[0], p3[1], p3[0] + 18 * SCALE, p3[1] + 14 * SCALE, stroke=1, fill=1)
        p4 = pdf_point(origin, x0 + 60, y0 + 60)
        c.ellipse(p4[0], p4[1], p4[0] + 18 * SCALE, p4[1] + 14 * SCALE, stroke=1, fill=1)
        c.setFont("Helvetica", 5)
        c.setFillColor(DARK_GRAY)
        c.drawString(*pdf_point(origin, x0 + 20, y0 + 140), "W.C. CUBICLES")

    elif "Library Reading" in s_name:
        c.setStrokeColor(BLACK)
        c.setFillColor(colors.HexColor("#fef3c7"))
        c.setLineWidth(0.7)
        for col_idx in range(2):
            for row_idx in range(3):
                tx = x0 + 80 + col_idx * 280
                ty = y0 + 50 + row_idx * 140
                c.rect(*pdf_point(origin, tx, ty), 180 * SCALE, 60 * SCALE, stroke=1, fill=1)
                c.setFillColor(FURN_SEAT)
                for ch in range(3):
                    c.rect(*pdf_point(origin, tx + 20 + ch * 50, ty - 18), 24 * SCALE, 14 * SCALE, stroke=1, fill=1)
                    c.rect(*pdf_point(origin, tx + 20 + ch * 50, ty + 64), 24 * SCALE, 14 * SCALE, stroke=1, fill=1)

        c.setFillColor(FURN_FILL)
        for w_idx in range(4):
            c.rect(*pdf_point(origin, x0 + 8, y0 + 60 + w_idx * 100), 28 * SCALE, 44 * SCALE, stroke=1, fill=1)
            c.rect(*pdf_point(origin, x1 - 36, y0 + 60 + w_idx * 100), 28 * SCALE, 44 * SCALE, stroke=1, fill=1)

    elif "Stack Area" in s_name:
        c.setStrokeColor(colors.HexColor("#475569"))
        c.setFillColor(colors.HexColor("#e2e8f0"))
        c.setLineWidth(0.8)
        for row in range(5):
            yy = y0 + 24 + row * 38
            c.rect(*pdf_point(origin, x0 + 50, yy), 560 * SCALE, 20 * SCALE, stroke=1, fill=1)
            for div in range(1, 10):
                c.line(*pdf_point(origin, x0 + 50 + div * 56, yy), *pdf_point(origin, x0 + 50 + div * 56, yy + 20))
        c.setFont("Helvetica-Bold", 6.5)
        c.setFillColor(DARK_GRAY)
        c.drawCentredString(*pdf_point(origin, (x0 + x1) / 2, y1 - 18), "LEGAL REPOSITORY & LAW REPORT BOOK STACKS (AIR, SCC, SCR)")

    elif "Discussion Room" in s_name:
        c.setStrokeColor(BLACK)
        c.setFillColor(colors.HexColor("#fed7aa"))
        c.setLineWidth(0.8)
        c.roundRect(*pdf_point(origin, (x0 + x1) / 2 - 72, (y0 + y1) / 2 - 27), 144 * SCALE, 54 * SCALE, 8, stroke=1, fill=1)
        c.setFillColor(FURN_SEAT)
        for i in range(4):
            c.circle(*pdf_point(origin, (x0 + x1) / 2 - 54 + i * 36, (y0 + y1) / 2 - 42), 8 * SCALE, stroke=1, fill=1)
            c.circle(*pdf_point(origin, (x0 + x1) / 2 - 54 + i * 36, (y0 + y1) / 2 + 42), 8 * SCALE, stroke=1, fill=1)
        c.circle(*pdf_point(origin, (x0 + x1) / 2 - 88, (y0 + y1) / 2), 8 * SCALE, stroke=1, fill=1)
        c.circle(*pdf_point(origin, (x0 + x1) / 2 + 88, (y0 + y1) / 2), 8 * SCALE, stroke=1, fill=1)

    elif "Computer" in s_name:
        c.setStrokeColor(BLACK)
        c.setFillColor(FURN_FILL)
        c.setLineWidth(0.7)
        for i in range(4):
            c.rect(*pdf_point(origin, x0 + 20, y0 + 16 + i * 26), 40 * SCALE, 20 * SCALE, stroke=1, fill=1)
            c.rect(*pdf_point(origin, x0 + 24, y0 + 20 + i * 26), 18 * SCALE, 12 * SCALE, stroke=1, fill=0)
            c.rect(*pdf_point(origin, x1 - 60, y0 + 16 + i * 26), 40 * SCALE, 20 * SCALE, stroke=1, fill=1)
            c.rect(*pdf_point(origin, x1 - 56, y0 + 20 + i * 26), 18 * SCALE, 12 * SCALE, stroke=1, fill=0)

    elif "Store" in s_name:
        c.setStrokeColor(BLACK)
        c.setFillColor(colors.HexColor("#fef08a"))
        c.setLineWidth(0.7)
        c.rect(*pdf_point(origin, x0 + 20, y1 - 32), 80 * SCALE, 18 * SCALE, stroke=1, fill=1)
        c.rect(*pdf_point(origin, x0 + 110, y1 - 32), 70 * SCALE, 18 * SCALE, stroke=1, fill=1)
        c.setFont("Helvetica-Bold", 5.5)
        c.setFillColor(BLACK)
        c.drawCentredString(*pdf_point(origin, x0 + 60, y1 - 22), "MAIN ELEC. PANEL")
        c.drawCentredString(*pdf_point(origin, x0 + 145, y1 - 22), "UPS / SERVER")

    c.restoreState()


def draw_columns_and_grid(
    c: canvas.Canvas,
    origin: tuple[float, float],
    level: str,
    spaces: list[dict[str, Any]],
) -> None:
    columns = COLUMNS_GF if level == "GF" else COLUMNS_FF
    c.saveState()

    x_grids = [
        ("A", 6),
        ("B", 132),
        ("C", 276),
        ("D", 408),
        ("E", 516),
        ("F", 666),
    ]
    if level == "GF":
        x_grids.append(("P", 762))

    y_grids = [
        ("1", 6),
        ("2", 180),
        ("3", 252),
        ("4", 414),
        ("5", 684),
        ("6", 900),
        ("7", 1080),
    ]
    if level == "FF":
        y_grids.append(("8", 1122))

    min_y = 6
    max_y = 1080 if level == "GF" else 1122
    min_x = 6
    max_x = 762 if level == "GF" else 666

    c.setStrokeColor(GRID_RED)
    c.setLineWidth(0.55)
    c.setDash(6, 4)

    # Vertical Grid Lines (X)
    for tag, gx in x_grids:
        p_bot = pdf_point(origin, gx, min_y - 45)
        p_top = pdf_point(origin, gx, max_y + 45)
        c.line(p_bot[0], p_bot[1], p_top[0], p_top[1])
        for px, py in [(p_bot[0], p_bot[1] - 10), (p_top[0], p_top[1] + 10)]:
            c.setDash()
            c.setFillColor(colors.white)
            c.setStrokeColor(GRID_RED)
            c.circle(px, py, 9, stroke=1, fill=1)
            c.setFillColor(GRID_RED)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(px, py - 3, tag)
            c.setDash(6, 4)

    # Horizontal Grid Lines (Y)
    for tag, gy in y_grids:
        p_left = pdf_point(origin, min_x - 45, gy)
        p_right = pdf_point(origin, max_x + 45, gy)
        c.line(p_left[0], p_left[1], p_right[0], p_right[1])
        for px, py in [(p_left[0] - 10, p_left[1]), (p_right[0] + 10, p_right[1])]:
            c.setDash()
            c.setFillColor(colors.white)
            c.setStrokeColor(GRID_RED)
            c.circle(px, py, 9, stroke=1, fill=1)
            c.setFillColor(GRID_RED)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(px, py - 3, tag)
            c.setDash(6, 4)

    c.setDash()

    # RCC Columns (Solid Dark Charcoal with Cross-Hatch)
    c.setStrokeColor(BLACK)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.setLineWidth(1)
    for col in columns:
        cx, cy = col["x"], col["y"]
        w, h = col["w"], col["h"]
        px, py = pdf_point(origin, cx - w / 2, cy - h / 2)
        pw, ph = w * SCALE, h * SCALE
        c.rect(px, py, pw, ph, stroke=1, fill=1)

        c.setStrokeColor(colors.HexColor("#e2e8f0"))
        c.setLineWidth(0.4)
        c.line(px, py, px + pw, py + ph)
        c.line(px, py + ph, px + pw, py)

        c.setFillColor(GRID_RED)
        c.setFont("Helvetica-Bold", 5.5)
        c.drawCentredString(px + pw / 2, py + ph + 3, col["id"])

    c.restoreState()


def draw_plan_sheet(
    c: canvas.Canvas,
    site: dict[str, Any],
    plans: dict[str, Any],
    level: str,
    sheet: dict[str, Any],
    mode: str = "bare",
) -> None:
    spaces = [space for space in plans["spaces"] if space["level"] == level]
    variant_text = {
        "bare": "ARCHITECTURAL FLOOR PLAN (WITHOUT FURNITURE)",
        "furniture": "PRESENTATION FLOOR PLAN (WITH FURNITURE)",
        "columns": "STRUCTURAL COLUMN & GRID COORDINATION PLAN",
    }[mode]

    c.setTitle(f'{site["project"]["name"]} - {sheet["title"]} - {mode.upper()}')
    c.setAuthor("Bar Association Architectural Team")

    c.setStrokeColor(BLACK)
    c.setLineWidth(1.4)
    c.rect(26, 26, PAGE_W - 52, PAGE_H - 52, stroke=1, fill=0)
    c.setLineWidth(0.5)
    c.rect(30, 30, PAGE_W - 60, PAGE_H - 60, stroke=1, fill=0)

    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, PAGE_H - 56, f'{sheet["number"]}  |  {sheet["title"].upper()}')
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.HexColor("#0284c7"))
    c.drawString(60, PAGE_H - 70, f"MODE: {variant_text.upper()}")
    c.setFont("Helvetica", 7.5)
    c.setFillColor(GRAY)
    c.drawString(60, PAGE_H - 82, "COORDINATED ARCHITECTURAL SCHEMATIC · BANSWARA DISTRICT COURT COMPLEX")

    origin = (108, 160)

    # 1. Draw Space Rectangles & Floor Finishes
    c.saveState()
    for space in spaces:
        x0, y0, x1, y1 = rect(space)
        sx, sy = pdf_point(origin, x0, y0)
        sw, sh = (x1 - x0) * SCALE, (y1 - y0) * SCALE

        # Fill color based on finish
        fill = colors.HexColor("#ffffff")
        if space["finish"] == "public":
            fill = colors.HexColor("#f8fafc")
        elif space["finish"] == "service":
            fill = colors.HexColor("#f1f5f9")
        elif space["finish"] == "circulation":
            fill = colors.HexColor("#faf5ff")
        c.setFillColor(fill)
        c.setStrokeColor(colors.HexColor("#94a3b8"))
        c.setLineWidth(0.7)
        c.rect(sx, sy, sw, sh, stroke=1, fill=1)

        # Draw interior furniture in 'furniture' mode
        if mode == "furniture":
            draw_furniture(c, origin, space)

        # Clean Opaque Room Identification Stamp Badge
        badge_cx = sx + sw / 2
        badge_cy = sy + sh / 2
        if "Assembly Hall" in space["name"]:
            badge_cy = sy + 310 * SCALE
        elif "Dais" in space["name"]:
            badge_cy = sy + 30 * SCALE
        elif "Pantry" in space["name"]:
            badge_cy = sy + sh - 22 * SCALE
        elif "Toilet" in space["name"]:
            badge_cy = sy + sh - 24 * SCALE
        elif "Reception" in space["name"] or "Librarian" in space["name"]:
            badge_cy = sy + 88 * SCALE

        # Measure badge width
        badge_w = min(sw - 8, 150 if "Assembly" in space["name"] or "Reading" in space["name"] else 96)
        badge_h = 32

        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor("#cbd5e1"))
        c.setLineWidth(0.6)
        c.roundRect(badge_cx - badge_w / 2, badge_cy - badge_h / 2, badge_w, badge_h, 3, stroke=1, fill=1)

        c.setFillColor(BLACK)
        c.setFont("Helvetica-Bold", 7.5 if badge_w < 110 else 8.5)
        disp_name = space["name"].upper()
        if "RECEPTION" in disp_name:
            disp_name = "RECEPTION / RECORDS"
        c.drawCentredString(badge_cx, badge_cy + 5, disp_name[:26])
        c.setFont("Helvetica-Bold", 6.5)
        c.setFillColor(DARK_GRAY)
        c.drawCentredString(badge_cx, badge_cy - 4, f"{inches_feet(x1 - x0)} × {inches_feet(y1 - y0)}")
        c.setFont("Helvetica", 6)
        c.setFillColor(GRAY)
        c.drawCentredString(badge_cx, badge_cy - 12, f'{space["id"]}  ·  {area(space):,.1f} SQ.FT.')

    # 2. Outer Cut-Wall Perimeter
    min_x = min(rect(s)[0] for s in spaces)
    min_y = min(rect(s)[1] for s in spaces)
    max_x = max(rect(s)[2] for s in spaces)
    max_y = max(rect(s)[3] for s in spaces)
    px, py = pdf_point(origin, min_x, min_y)
    c.setStrokeColor(BLACK)
    c.setLineWidth(2.5)
    c.rect(px, py, (max_x - min_x) * SCALE, (max_y - min_y) * SCALE, stroke=1, fill=0)
    c.restoreState()

    # 3. Doors & Windows
    space_by_id = {space["id"]: space for space in spaces}
    for opening in plans["openings"]:
        if opening["level"] == level and opening["hostSpace"] in space_by_id:
            draw_door(c, origin, space_by_id[opening["hostSpace"]], opening)

    for window in plans["windows"]:
        if window["level"] == level and window["hostSpace"] in space_by_id:
            draw_window(c, origin, space_by_id[window["hostSpace"]], window)

    # 4. Staircase
    stair_space = next((space for space in spaces if space.get("stairId") == "STAIR-01"), None)
    if stair_space:
        draw_stair(c, origin, stair_space, plans["stairs"][0])

    # 5. Entrance Porch (East Long Wall)
    draw_entry_features(c, origin, plans, spaces, level)

    # 6. Structural Columns & Grid (in 'columns' mode)
    if mode == "columns":
        draw_columns_and_grid(c, origin, level, spaces)

    # 7. Dimensions (Properly offset without border clipping)
    draw_dimension(c, origin, (min_x, min_y), (max_x, min_y), (0, -36), f"OVERALL WIDTH = {inches_feet(max_x - min_x)}")
    draw_dimension(c, origin, (min_x, min_y), (min_x, max_y), (-42, 0), f"OVERALL LENGTH = {inches_feet(max_y - min_y)}")

    draw_north(c, 700, PAGE_H - 120)
    draw_scale_bar(c, 780, PAGE_H - 120)

    draw_legend(c, 760, PAGE_H - 340, mode)
    if mode == "columns":
        draw_column_schedule(c, 760, 185, COLUMNS_GF if level == "GF" else COLUMNS_FF)
    else:
        draw_schedule(c, 760, 185, spaces)

    level_full_name = site["levels"][0 if level == "GF" else 1]["name"]
    draw_title_block(c, sheet, level_full_name, variant_text)
    c.showPage()


def draw_cover_sheet(c: canvas.Canvas, site: dict[str, Any], plans: dict[str, Any]) -> None:
    c.setTitle(f'{site["project"]["name"]} - Master Review Set Cover')
    c.setAuthor("Bar Association Architectural Team")

    c.setStrokeColor(BLACK)
    c.setLineWidth(1.6)
    c.rect(26, 26, PAGE_W - 52, PAGE_H - 52, stroke=1, fill=0)
    c.setLineWidth(0.6)
    c.rect(32, 32, PAGE_W - 64, PAGE_H - 64, stroke=1, fill=0)

    c.setFillColor(BLACK)
    c.rect(60, PAGE_H - 180, PAGE_W - 120, 100, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 125, "BAR ASSOCIATION HALL, BANSWARA")
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.HexColor("#38bdf8"))
    c.drawCentredString(PAGE_W / 2, PAGE_H - 152, "COMPREHENSIVE ARCHITECTURAL & STRUCTURAL REVIEW SET")
    c.setFont("Helvetica", 9.5)
    c.setFillColor(colors.HexColor("#e2e8f0"))
    c.drawCentredString(PAGE_W / 2, PAGE_H - 170, "DISTRICT COURT COMPLEX, BANSWARA, RAJASTHAN · SCHEMATIC DESIGN STAGE")

    c.setFillColor(PALE_PANEL)
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.roundRect(80, 260, 480, PAGE_H - 480, 6, stroke=1, fill=1)
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(104, PAGE_H - 225, "PROJECT DIRECTORY & SUMMARY")

    proj_lines = [
        ("Project Name", "Bar Association Hall, Banswara"),
        ("Client", "Bar Association, Banswara District Court"),
        ("Location", "Court Complex, Banswara, Rajasthan, India"),
        ("Plot Geometry", "L-Shaped Boundary (Coordinates Stored)"),
        ("Total Plot Area", "5,467.50 Sq. Ft. (Calculated)"),
        ("Setback Envelope", "4,427.50 Sq. Ft. per floor (Adopted)"),
        ("Total Built-up Area", "8,855.00 Sq. Ft. (G+1 Floors)"),
        ("Ground Floor Plinth", "4,427.50 Sq. Ft."),
        ("First Floor Plinth", "4,427.50 Sq. Ft."),
        ("Structure Type", "RCC Framed (M25 Concrete, Fe500D Steel)"),
        ("Main Public Access", "East Long Wall via 12'×8' Covered Porch"),
        ("Fenestration", "4-Sided Approved (North, South, East, West)"),
    ]
    py = PAGE_H - 260
    for label, val in proj_lines:
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(DARK_GRAY)
        c.drawString(104, py, label + " :")
        c.setFont("Helvetica-Bold" if "Adopted" in val or "East" in val else "Helvetica", 8.5)
        c.setFillColor(BLACK if "Adopted" not in val else colors.HexColor("#047857"))
        c.drawString(240, py, val)
        py -= 22

    c.setFillColor(PALE_PANEL)
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.roundRect(600, 260, 980, PAGE_H - 480, 6, stroke=1, fill=1)
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(624, PAGE_H - 225, "MASTER DRAWING SHEET INDEX")

    sheets_index = [
        ("A-101.1", "Ground Floor Architectural Plan (Without Furniture)", "Clean Spatial Dimensions, Walls, Openings"),
        ("A-101.2", "Ground Floor Presentation Plan (With Furniture)", "Assembly Seating (100+ seats), Dais, Porch"),
        ("S-101", "Ground Floor Structural Column & Grid Plan", "RCC Columns C1-C21, Structural Grids A-F & 1-7"),
        ("A-102.1", "First Floor Architectural Plan (Without Furniture)", "Library Reading, Stacks, Discussion, Computer"),
        ("A-102.2", "First Floor Presentation Plan (With Furniture)", "Complete Study Carrels, Book Shelving, IT Lab"),
        ("S-102", "First Floor Structural Column & Grid Plan", "RCC Columns C1-C24, Grid Framing & Schedules"),
    ]
    sy = PAGE_H - 260
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(624, sy, "SHEET NO.")
    c.drawString(710, sy, "DRAWING TITLE")
    c.drawString(1160, sy, "DESCRIPTION / REMARKS")
    c.setStrokeColor(colors.HexColor("#94a3b8"))
    c.setLineWidth(1)
    c.line(624, sy - 6, 1540, sy - 6)
    sy -= 26

    for sno, title, desc in sheets_index:
        c.setFillColor(colors.HexColor("#b91c1c") if "S-" in sno else colors.HexColor("#0f172a"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(624, sy, sno)
        c.setFillColor(BLACK)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(710, sy, title)
        c.setFont("Helvetica", 8)
        c.setFillColor(DARK_GRAY)
        c.drawString(1160, sy, desc)
        sy -= 32

    c.setStrokeColor(BLACK)
    c.setLineWidth(1)
    c.rect(80, 70, PAGE_W - 160, 160, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(104, 205, "CLIENT & CONSULTANT APPROVAL BLOCK")
    c.line(80, 195, PAGE_W - 80, 195)

    c.setFont("Helvetica-Bold", 8)
    c.drawString(104, 165, "PREPARED BY:")
    c.setFont("Helvetica", 8)
    c.drawString(104, 148, "Parametric Architectural Drawing Pipeline")
    c.drawString(104, 134, "Lumion 12.5 / 2024 Grade Standard Generation")

    c.setFont("Helvetica-Bold", 8)
    c.drawString(550, 165, "REVIEWED & APPROVED BY:")
    c.setFont("Helvetica", 8)
    c.drawString(550, 148, "Bar Association Building Committee")
    c.drawString(550, 134, "District Court Complex, Banswara")

    c.setFont("Helvetica-Bold", 8)
    c.drawString(1050, 165, "STATUTORY & REGULATORY COMPLIANCE:")
    c.setFont("Helvetica", 8)
    c.drawString(1050, 148, "Subject to Municipal Authority Building Bye-laws")
    c.drawString(1050, 134, "Licensed Structural & Fire Strategy Verification Required")

    c.showPage()


def create_dxf(
    site: dict[str, Any],
    plans: dict[str, Any],
    level: str,
    filename: Path,
    mode: str = "bare",
) -> None:
    doc = ezdxf.new("R2018")
    doc.units = 1  # Inches
    msp = doc.modelspace()

    layers = [
        ("A-WALL", 7),
        ("A-DOOR", 1),
        ("A-WINDOW", 4),
        ("A-FURN", 8),
        ("A-DIM", 2),
        ("A-TEXT", 7),
        ("A-STAIR", 3),
        ("A-PORCH", 6),
        ("S-COLUMN", 2),
        ("S-GRID", 1),
    ]
    for layer, col in layers:
        if layer not in doc.layers:
            doc.layers.add(layer, color=col)

    spaces = [space for space in plans["spaces"] if space["level"] == level]
    for space in spaces:
        x0, y0, x1, y1 = rect(space)
        msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], dxfattribs={"layer": "A-WALL", "closed": True})
        msp.add_text(space["name"].upper(), dxfattribs={"layer": "A-TEXT", "height": 8}).set_placement(((x0 + x1) / 2, (y0 + y1) / 2), align=TextEntityAlignment.MIDDLE_CENTER)
        msp.add_text(space["id"], dxfattribs={"layer": "A-TEXT", "height": 5}).set_placement(((x0 + x1) / 2, (y0 + y1) / 2 - 12), align=TextEntityAlignment.MIDDLE_CENTER)

    for opening in plans["openings"]:
        if opening["level"] != level:
            continue
        space = next((s for s in spaces if s["id"] == opening["hostSpace"]), None)
        if not space:
            continue
        a, b = wall_segment(space, opening["wall"], opening["offset"], opening["width"])
        msp.add_line(a, b, dxfattribs={"layer": "A-DOOR"})
        msp.add_text(opening["tag"], dxfattribs={"layer": "A-DOOR", "height": 5}).set_placement(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), align=TextEntityAlignment.MIDDLE_CENTER)

    for window in plans["windows"]:
        if window["level"] != level:
            continue
        space = next((s for s in spaces if s["id"] == window["hostSpace"]), None)
        if not space:
            continue
        a, b = wall_segment(space, window["wall"], window["offset"], window["width"])
        msp.add_line(a, b, dxfattribs={"layer": "A-WINDOW"})
        msp.add_text(window["tag"], dxfattribs={"layer": "A-WINDOW", "height": 5}).set_placement(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), align=TextEntityAlignment.MIDDLE_CENTER)

    for entry in plans.get("entries", []):
        if entry["level"] != level or entry["kind"] != "main" or not entry.get("porch"):
            continue
        host = next((s for s in spaces if s["id"] == entry["hostSpace"]), None)
        if not host:
            continue
        porch = entry["porch"]
        width = porch["width"]
        depth = porch["depth"]
        y0 = rect(host)[1] + 120 + 42 - width / 2
        x0 = rect(host)[2]
        msp.add_lwpolyline(
            [(x0, y0), (x0 + depth, y0), (x0 + depth, y0 + width), (x0, y0 + width), (x0, y0)],
            dxfattribs={"layer": "A-PORCH", "closed": True},
        )
        msp.add_text("MAIN ENTRANCE PORCH", dxfattribs={"layer": "A-PORCH", "height": 6}).set_placement(
            (x0 + depth / 2, y0 + width / 2), align=TextEntityAlignment.MIDDLE_CENTER
        )

    if mode == "columns":
        columns = COLUMNS_GF if level == "GF" else COLUMNS_FF
        for col in columns:
            cx, cy = col["x"], col["y"]
            w, h = col["w"], col["h"]
            msp.add_lwpolyline(
                [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2), (cx - w / 2, cy - h / 2)],
                dxfattribs={"layer": "S-COLUMN", "closed": True},
            )
            msp.add_text(col["id"], dxfattribs={"layer": "S-COLUMN", "height": 5}).set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)

    doc.saveas(filename)


def write_lumion_guide() -> None:
    guide_path = CAD_DIR / "Lumion-3D-Import-Layer-Guide.txt"
    content = """================================================================================
BAR ASSOCIATION HALL, BANSWARA — LUMION 3D IMPORT & EXTRUSION GUIDE
================================================================================
Generated for: Lumion 12.5, Lumion 2023, Lumion 2024 Pro
Units: INCHES (or FEET / METERS depending on import unit selector)

1. RECOMMENDED CAD FILES FOR LUMION IMPORT:
   - Ground Floor: CAD/A-101-GF-Presentation-Furniture-Plan.dxf
   - First Floor : CAD/A-102-FF-Presentation-Furniture-Plan.dxf
   - Structural  : CAD/S-101-GF-Column-Structural-Grid-Plan.dxf

2. LAYER EXTRUSION HEIGHT SCHEDULE:
   -----------------------------------------------------------------------------
   LAYER NAME    | LUMION MATERIAL ASSIGNMENT        | SUGGESTED 3D HEIGHT
   -----------------------------------------------------------------------------
   A-WALL        | Plaster / Concrete / Masonry     | 11'-0" (132 inches)
   A-DOOR        | Wood / Glass / Metal Frames       | 7'-0" (84 inches)
   A-WINDOW      | Pure Glass / Aluminium Mullions   | Sill: 3'-0", Lintel: 7'-0"
   A-PORCH       | Exterior Pavers / Concrete Slab   | Plinth: +1'-6" (18 inches)
   A-STAIR       | Granite / Marble Steps            | Total rise: 11'-0"
   A-FURN        | Wood / Leather / Chrome           | Tables: 2'-6", Chairs: 3'-0"
   S-COLUMN      | Structural RCC / Heavy Concrete   | 11'-0" to underside of beam
   -----------------------------------------------------------------------------

3. ARCHITECTURAL ADAPTATIONS INCORPORATED:
   - Main Entrance: Relocated to East Long Wall with a grand 12'-0" × 8'-0" porch.
   - Fenestration: Windows placed on all 4 elevations (North, South, East, West).
   - Adopted Area: 4,427.50 Sq. Ft. per floor (consistent with setback envelope).

4. HOW TO IMPORT INTO LUMION:
   Step 1: Open Lumion -> New Scene -> Plain Landscape.
   Step 2: Click 'Import Model' (green plus icon) -> Select DXF from CAD/ folder.
   Step 3: Set Import Units to 'Inches' (or scale by 0.0254 if importing into Meters).
   Step 4: Assign Lumion Glass material to A-WINDOW layer for realistic reflections.
================================================================================
"""
    guide_path.write_text(content, encoding="utf-8")


def write_manifest(site: dict[str, Any], plans: dict[str, Any], outputs: list[str], validation: list[str]) -> None:
    source_hash = hashlib.sha256()
    for path in sorted(SOURCE.glob("*.json")):
        source_hash.update(path.read_bytes())
    data = {
        "project": site["project"]["name"],
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "sourceSha256": source_hash.hexdigest(),
        "generator": "generate_standard_drawings.py",
        "status": "pass" if not validation else "fail",
        "adoptedSetbackEnvelopeAreaSqFt": 4427.50,
        "mainEntranceLocation": "East Long Wall",
        "fenestration": "4-Sided Approved (North, South, East, West)",
        "outputs": outputs,
        "validationErrors": validation,
        "sheetSize": "A2 landscape",
        "declaredPlotScale": '1/8" = 1\'-0" approximate',
        "professionalStatus": "approved-schematic",
        "notes": [
            "Includes 3 distinct coordinated sets: Bare Architectural, Presentation with Furniture, and Structural with Columns & Grid.",
            "Main entrance relocated to the East long wall with 12'-0\" x 8'-0\" covered porch.",
            "Full fenestration approved across all four facades (North, South, East, West).",
            "Adopted setback envelope area: 4,427.50 sq ft per floor.",
        ],
    }
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n")


def main() -> int:
    site, plans = load_model()
    errors = validate_model(site, plans)
    if errors:
        print(json.dumps({"status": "fail", "errors": errors}, indent=2))
        return 1

    PDF_DIR.mkdir(exist_ok=True)
    CAD_DIR.mkdir(exist_ok=True)
    outputs: list[str] = []

    drawing_jobs = [
        ("GF", {"number": "A-101.1", "title": "Ground Floor Architectural Plan", "file": "A-101-GF-Architectural-Plan.pdf"}, "bare"),
        ("GF", {"number": "A-101.2", "title": "Ground Floor Presentation Furniture Plan", "file": "A-101-GF-Presentation-Furniture-Plan.pdf"}, "furniture"),
        ("GF", {"number": "S-101", "title": "Ground Floor Structural Column & Grid Plan", "file": "S-101-GF-Column-Structural-Grid-Plan.pdf"}, "columns"),
        ("FF", {"number": "A-102.1", "title": "First Floor Architectural Plan", "file": "A-102-FF-Architectural-Plan.pdf"}, "bare"),
        ("FF", {"number": "A-102.2", "title": "First Floor Presentation Furniture Plan", "file": "A-102-FF-Presentation-Furniture-Plan.pdf"}, "furniture"),
        ("FF", {"number": "S-102", "title": "First Floor Structural Column & Grid Plan", "file": "S-102-FF-Column-Structural-Grid-Plan.pdf"}, "columns"),
    ]

    generated_pdfs: list[Path] = []
    for level, sheet, mode in drawing_jobs:
        pdf_path = PDF_DIR / sheet["file"]
        c = canvas.Canvas(str(pdf_path), pagesize=landscape(A2))
        draw_plan_sheet(c, site, plans, level, sheet, mode=mode)
        c.save()
        generated_pdfs.append(pdf_path)
        outputs.append(str(pdf_path.relative_to(ROOT)))

        dxf_name = sheet["file"].replace(".pdf", ".dxf")
        dxf_path = CAD_DIR / dxf_name
        create_dxf(site, plans, level, dxf_path, mode=mode)
        outputs.append(str(dxf_path.relative_to(ROOT)))

    shutil.copyfile(PDF_DIR / "A-101-GF-Architectural-Plan.pdf", PDF_DIR / "A-101-Ground-Floor-Plan.pdf")
    shutil.copyfile(PDF_DIR / "A-102-FF-Architectural-Plan.pdf", PDF_DIR / "A-102-First-Floor-Plan.pdf")
    outputs.append("PDF\\A-101-Ground-Floor-Plan.pdf")
    outputs.append("PDF\\A-102-First-Floor-Plan.pdf")

    cover_path = PDF_DIR / "_cover_temp.pdf"
    c_cov = canvas.Canvas(str(cover_path), pagesize=landscape(A2))
    draw_cover_sheet(c_cov, site, plans)
    c_cov.save()

    review_set_path = PDF_DIR / "Bar-Association-Standard-Review-Set.pdf"
    writer = PdfWriter()
    for page in PdfReader(str(cover_path)).pages:
        writer.add_page(page)
    for pdf in generated_pdfs:
        for page in PdfReader(str(pdf)).pages:
            writer.add_page(page)
    with review_set_path.open("wb") as handle:
        writer.write(handle)
    cover_path.unlink(missing_ok=True)
    outputs.append(str(review_set_path.relative_to(ROOT)))

    write_lumion_guide()
    outputs.append("CAD\\Lumion-3D-Import-Layer-Guide.txt")

    write_manifest(site, plans, outputs, errors)
    print(json.dumps({
        "status": "pass",
        "message": "Lumion-grade architectural drawing suite generated successfully!",
        "adoptedSetbackEnvelopeArea": "4427.50 sq ft",
        "drawingSets": [
            "1. Bare Architectural Plans (Without Furniture): A-101.1 & A-102.1",
            "2. Presentation Plans (With Furniture): A-101.2 & A-102.2",
            "3. Structural Coordination Plans (With Columns & Grid): S-101 & S-102",
            "4. Master Review Set PDF (All 6 sheets + Cover): Bar-Association-Standard-Review-Set.pdf"
        ],
        "outputs": outputs
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())