"""
BAR ASSOCIATION HALL, BANSWARA — SEATING PLAN
===============================================
Sheet  SP-101  —  Ground Floor Seating Arrangement

Audience seating  : PVC chairs, 18"×18" seat, 30" row pitch
                    2 side aisles (3'-0") + 1 centre aisle (3'-0")
                    560 audience chairs in 20 rows × 28 cols

Dais seating      : 12 high-back executive chairs at curved dais table
                    (President centre, 5 either side, 1 podium each wing)

Paper             : A2 Landscape @ 1/8" = 1'-0"
Source            : standard/source/preliminary_plans.json + site_plan.json
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A2, landscape
from reportlab.pdfgen import canvas

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parent
SRC     = ROOT / "standard" / "source"
PDF_OUT = ROOT / "PDF"
PDF_OUT.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Page & Scale
# ─────────────────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = landscape(A2)
SCALE = 0.75   # pt per model-inch  (1/8" = 1'-0")

# ─────────────────────────────────────────────────────────────────────────────
# Colour Palette  (matches generate_lumion_drawings.py)
# ─────────────────────────────────────────────────────────────────────────────
BLACK         = colors.HexColor("#0d1117")
CHARCOAL      = colors.HexColor("#1e293b")
DARK_GRAY     = colors.HexColor("#334155")
GRAY          = colors.HexColor("#64748b")
LIGHT_GRAY    = colors.HexColor("#cbd5e1")
PALE_BG       = colors.HexColor("#f8fafc")
PALE_PANEL    = colors.HexColor("#f1f5f9")

WALL_STROKE   = colors.HexColor("#0d1117")
PART_THICK    = 1.6
WALL_THICK    = 2.8

FILL_HALL     = colors.HexColor("#fefce8")    # warm cream — assembly zone
FILL_DAIS     = colors.HexColor("#fff7ed")    # amber tint — dais
FILL_SERVICE  = colors.HexColor("#eff6ff")    # cool blue  — service core
FILL_CIRC     = colors.HexColor("#faf5ff")    # lavender   — stair / lobby

ACCENT_BLUE   = colors.HexColor("#0284c7")
GLASS_BLUE    = colors.HexColor("#38bdf8")
DOOR_RED      = colors.HexColor("#b91c1c")
PORCH_AMBER   = colors.HexColor("#d97706")

# Seating colours
PVC_FILL      = colors.HexColor("#bfdbfe")    # light sky-blue  — audience PVC chair
PVC_STROKE    = colors.HexColor("#1d4ed8")    # royal blue      — chair outline
PVC_OCCUPIED  = colors.HexColor("#dbeafe")    # seat pad
AISLE_DASH    = colors.HexColor("#94a3b8")

EXEC_FILL     = colors.HexColor("#7c3aed")    # purple          — executive chair
EXEC_STROKE   = colors.HexColor("#4c1d95")
EXEC_SEAT     = colors.HexColor("#ede9fe")
DAIS_TABLE    = colors.HexColor("#fde68a")    # amber           — dais table top
DAIS_EDGE     = colors.HexColor("#b45309")
PODIUM_FILL   = colors.HexColor("#78350f")

NUMBERING     = colors.HexColor("#1e3a8a")    # dark navy       — row/col numbers


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def pp(origin: tuple, x: float, y: float) -> tuple:
    """Model-inch → PDF-point."""
    return origin[0] + x * SCALE, origin[1] + y * SCALE


def fmtft(inches: float) -> str:
    ft  = int(inches // 12)
    inc = round(inches - ft * 12)
    if inc == 12:
        ft += 1; inc = 0
    return f"{ft}'-{inc}\""


def arrow(c, x, y, angle, size=5):
    c.saveState()
    c.translate(x, y); c.rotate(math.degrees(angle))
    p = c.beginPath()
    p.moveTo(0, 0); p.lineTo(-size, size/2); p.lineTo(-size, -size/2); p.close()
    c.setFillColor(DARK_GRAY); c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# North Rose
# ─────────────────────────────────────────────────────────────────────────────
def draw_north(c, cx, cy):
    c.saveState()
    c.setStrokeColor(BLACK); c.setLineWidth(1.2)
    c.circle(cx, cy, 20, stroke=1, fill=0)
    p1 = c.beginPath()
    p1.moveTo(cx, cy+20); p1.lineTo(cx-7, cy); p1.lineTo(cx, cy-20); p1.close()
    c.setFillColor(BLACK); c.drawPath(p1, fill=1, stroke=0)
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
    segs  = [0, 5, 10, 20, 30, 40]
    total = 40 * ft_pt
    c.setStrokeColor(BLACK); c.setLineWidth(0.8)
    c.rect(x, y, total, 5, stroke=1, fill=0)
    for i, seg in enumerate(segs[:-1]):
        c.setFillColor(BLACK if i % 2 == 0 else colors.white)
        c.rect(x + seg*ft_pt, y, (segs[i+1]-segs[i])*ft_pt, 5, stroke=0, fill=1)
    c.setFillColor(DARK_GRAY); c.setFont("Helvetica", 6)
    for ft in segs:
        c.drawCentredString(x + ft*ft_pt, y-8, f"{ft}'")
    c.drawString(x + total+4, y-8, "FEET")
    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Title Block
# ─────────────────────────────────────────────────────────────────────────────
def draw_title_block(c):
    TB_X = 18; TB_Y = 18
    TB_W = PAGE_W - 36; TB_H = 88

    c.saveState()
    # Sheet border — double line
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
    c.setLineWidth(0.7)
    c.line(col1, TB_Y, col1, TB_Y+TB_H)
    c.line(col2, TB_Y, col2, TB_Y+TB_H)

    # Block 1 — Project
    c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 13)
    c.drawString(TB_X+12, TB_Y+TB_H-22, "BAR ASSOCIATION HALL")
    c.setFont("Helvetica-Bold", 9); c.setFillColor(colors.HexColor("#0369a1"))
    c.drawString(TB_X+12, TB_Y+TB_H-36, "DISTRICT COURT COMPLEX, BANSWARA")
    c.setFont("Helvetica", 8); c.setFillColor(GRAY)
    c.drawString(TB_X+12, TB_Y+TB_H-50, "RAJASTHAN, INDIA")
    c.setFont("Helvetica-Bold", 7); c.setFillColor(DARK_GRAY)
    c.drawString(TB_X+12, TB_Y+18, "AUDIENCE: 560 PVC CHAIRS  |  DAIS: 12 EXEC. CHAIRS")
    c.drawString(TB_X+12, TB_Y+7,  "MAIN ENTRY: EAST LONG WALL  ·  4-SIDED FENESTRATION")

    # Block 2 — Drawing title
    dx = col1 + 12
    c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 12)
    c.drawString(dx, TB_Y+TB_H-22, "GROUND FLOOR — SEATING ARRANGEMENT PLAN")
    c.setFont("Helvetica-Bold", 8.5); c.setFillColor(colors.HexColor("#7c3aed"))
    c.drawString(dx, TB_Y+TB_H-37, "SEATING LAYOUT PLAN")
    c.setFont("Helvetica", 7.5); c.setFillColor(DARK_GRAY)
    c.drawString(dx, TB_Y+TB_H-52, "LEVEL: GROUND FLOOR   SCALE: 1/8\" = 1'-0\"  (A2 LANDSCAPE)")
    c.setFont("Helvetica-Bold", 7); c.setFillColor(BLACK)
    c.drawString(dx, TB_Y+14, "PVC CHAIR: 18\"×18\" SEAT  |  ROW PITCH: 30\"  |  3 AISLES")
    c.drawString(dx, TB_Y+4,  "STATUS: FOR REVIEW — NOT FOR CONSTRUCTION")

    # Block 3 — Sheet ID
    sx = col2 + (PAGE_W-36 - (col2-TB_X)) / 2
    c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(sx, TB_Y+56, "SP-101")
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(sx, TB_Y+40, "SHEET NO.")
    c.setFont("Helvetica", 6.5); c.setFillColor(GRAY)
    c.drawCentredString(sx, TB_Y+24, "REV: P01")
    c.drawCentredString(sx, TB_Y+13,
                        datetime.now(timezone.utc).strftime("%d-%b-%Y").upper())
    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Seating Legend Panel
# ─────────────────────────────────────────────────────────────────────────────
def draw_legend(c, x, y):
    W, H = 400, 190
    c.saveState()
    c.setFillColor(PALE_PANEL); c.setStrokeColor(LIGHT_GRAY); c.setLineWidth(0.8)
    c.roundRect(x, y, W, H, 4, stroke=1, fill=1)

    # Header bar
    c.setFillColor(CHARCOAL)
    c.rect(x, y+H-20, W, 20, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 8.5)
    c.drawString(x+10, y+H-14, "SEATING LEGEND & NOTES")

    # Symbol swatches
    row_y = y + H - 46
    items = [
        (PVC_FILL,  PVC_STROKE,  "PVC AUDIENCE CHAIR (18\"×18\")"),
        (EXEC_SEAT, EXEC_STROKE, "EXECUTIVE CHAIR — DAIS (HIGH-BACK)"),
        (DAIS_TABLE,DAIS_EDGE,   "DAIS TABLE (CURVED, HIGH-GLOSS FINISH)"),
    ]
    for fill, stroke, label in items:
        c.setFillColor(fill); c.setStrokeColor(stroke); c.setLineWidth(0.8)
        c.roundRect(x+12, row_y, 14, 14, 2, stroke=1, fill=1)
        c.setFillColor(DARK_GRAY); c.setFont("Helvetica-Bold", 7)
        c.drawString(x+32, row_y+4, label)
        row_y -= 22

    # Aisle swatch
    c.setStrokeColor(AISLE_DASH); c.setLineWidth(1.5); c.setDash(4, 3)
    c.line(x+12, row_y+7, x+26, row_y+7); c.setDash()
    c.setFillColor(DARK_GRAY); c.setFont("Helvetica-Bold", 7)
    c.drawString(x+32, row_y+4, "ACCESS AISLE (3'-0\" CLEAR MIN.)")
    row_y -= 26

    # Notes
    c.setFont("Helvetica", 6.5); c.setFillColor(DARK_GRAY)
    notes = [
        "1.  Audience PVC chairs: 2 side aisles 3'-0\" + 1 centre aisle 3'-0\".",
        "2.  Row pitch: 30\" (back of seat to back of next seat).",
        "3.  Rows numbered R01–R20 front (dais) to rear. Cols A–N each block.",
        "4.  Each seat marked: R01-A … R20-N  (left & right blocks identical).",
        "5.  Dais seats: D-01 (leftmost) to D-12 (rightmost).  D-06 = President.",
        "6.  Wheelchair spaces: 4 positions at front sides (not shown).",
        "7.  Total audience seating: 560 chairs.  Dais seating: 12 chairs.",
    ]
    for note in notes:
        c.drawString(x+10, row_y, note); row_y -= 12
    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Seating Summary Table
# ─────────────────────────────────────────────────────────────────────────────
def draw_summary_table(c, x, y):
    W = 400; ROW = 16
    rows = [
        ("Assembly Hall",          "55'-0\" × 57'-0\"", "3,135 sq ft", "Audience PVC Chairs"),
        ("Dais / Speaker Zone",    "55'-0\" × 14'-6\"", "797.5 sq ft", "12 Executive Chairs"),
        ("Total Seating Area",     "G.F. Only",          "3,932.5 sq ft", "572 Seats Total"),
    ]
    H = ROW * (len(rows) + 2)
    c.saveState()
    c.setFillColor(colors.white); c.setStrokeColor(LIGHT_GRAY); c.setLineWidth(0.7)
    c.rect(x, y, W, H, stroke=1, fill=1)

    # Header
    c.setFillColor(CHARCOAL); c.rect(x, y+H-ROW, W, ROW, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x+8, y+H-ROW+4, "SEATING CAPACITY SUMMARY")

    # Column headers
    c.setFillColor(DARK_GRAY); c.setFont("Helvetica-Bold", 6.5)
    c.drawString(x+6,   y+H-2*ROW+4, "ZONE")
    c.drawString(x+120, y+H-2*ROW+4, "SIZE")
    c.drawString(x+215, y+H-2*ROW+4, "AREA")
    c.drawString(x+295, y+H-2*ROW+4, "SEATING")

    c.setStrokeColor(LIGHT_GRAY)
    for i, (zone, size, area, seating) in enumerate(rows):
        ry = y + H - ROW*(i+3)
        c.setLineWidth(0.4); c.line(x, ry, x+W, ry)
        bg = colors.HexColor("#ede9fe") if i == 2 else (PALE_BG if i % 2 == 0 else colors.white)
        c.setFillColor(bg)
        c.rect(x, ry, W, ROW, stroke=0, fill=1)
        bold = i == 2
        c.setFillColor(BLACK); c.setFont("Helvetica-Bold" if bold else "Helvetica", 6.5)
        c.drawString(x+6,   ry+4, zone)
        c.drawString(x+120, ry+4, size)
        c.drawString(x+215, ry+4, area)
        c.drawString(x+295, ry+4, seating)
    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# Draw a single PVC audience chair
# ─────────────────────────────────────────────────────────────────────────────
def draw_pvc_chair(c, px, py, w, d, seat_label=""):
    """
    px, py      — bottom-left corner in PDF points
    w           — chair width in PDF points
    d           — chair depth in PDF points
    seat_label  — e.g. "R01-A" printed on seat cushion
    """
    c.setFillColor(PVC_FILL); c.setStrokeColor(PVC_STROKE); c.setLineWidth(0.45)
    # Seat cushion (lower 60% of depth)
    seat_h = d * 0.60
    c.roundRect(px, py, w, seat_h, 1.5, stroke=1, fill=1)
    # Back rest (upper 35%)
    back_h = d * 0.35
    c.setFillColor(PVC_OCCUPIED)
    c.roundRect(px + w*0.08, py + seat_h + 1, w*0.84, back_h, 1.2, stroke=1, fill=1)
    # Leg dots (4 corners — tiny)
    leg_r = 1.2
    for lx, ly in [(px+2, py+2), (px+w-2, py+2)]:
        c.setFillColor(DARK_GRAY)
        c.circle(lx, ly, leg_r, stroke=0, fill=1)
    # ── Seat number label on cushion ──
    if seat_label:
        c.setFillColor(NUMBERING)
        c.setFont("Helvetica-Bold", 3.2)
        c.drawCentredString(px + w/2, py + seat_h*0.38, seat_label)


# ─────────────────────────────────────────────────────────────────────────────
# Draw a single executive dais chair
# ─────────────────────────────────────────────────────────────────────────────
def draw_exec_chair(c, cx, cy, w, d, is_president=False):
    """
    cx, cy  — centre-bottom of chair in PDF points
    w, d    — width and depth in PDF points
    """
    fill = colors.HexColor("#581c87") if is_president else EXEC_FILL
    seat_fill = colors.HexColor("#f3e8ff") if is_president else EXEC_SEAT
    stroke = colors.HexColor("#3b0764") if is_president else EXEC_STROKE

    c.setFillColor(fill); c.setStrokeColor(stroke); c.setLineWidth(0.55)
    # High back — taller than seat
    back_h = d * 1.1
    c.roundRect(cx - w/2, cy + d*0.55, w, back_h, 2, stroke=1, fill=1)
    # Seat cushion
    c.setFillColor(seat_fill)
    c.roundRect(cx - w/2, cy, w, d*0.60, 2, stroke=1, fill=1)
    # Armrests
    c.setFillColor(fill)
    c.roundRect(cx - w/2 - 3, cy + 4, 4, d*0.4, 1, stroke=1, fill=1)
    c.roundRect(cx + w/2 - 1, cy + 4, 4, d*0.4, 1, stroke=1, fill=1)
    # President marker — gold crown dot
    if is_president:
        c.setFillColor(colors.HexColor("#fbbf24"))
        c.circle(cx, cy + d*0.55 + back_h - 5, 3, stroke=0, fill=1)


# ─────────────────────────────────────────────────────────────────────────────
# Draw Audience Seating Block in Assembly Hall
# ─────────────────────────────────────────────────────────────────────────────
def draw_audience_seating(c, origin, hall_x0, hall_y0, hall_x1, hall_y1):
    """
    Draw 20 rows × 28 chairs (14 left + 14 right) in the Assembly Hall.
    All coordinates in model-inches.
    """
    # ── Seating geometry (model-inches) ──
    SIDE_CLEAR    = 24    # 2'-0" wall clearance each side
    FRONT_CLEAR   = 48    # 4'-0" clearance from north wall (toward dais)
    REAR_CLEAR    = 36    # 3'-0" rear clearance at south wall
    SIDE_AISLE_W  = 36    # 3'-0" each side aisle
    CENTRE_AISLE  = 36    # 3'-0" centre aisle

    CHAIR_W       = 18    # 18" wide
    ROW_PITCH     = 30    # 30" row-to-row

    # Usable seating zone
    zone_x0 = hall_x0 + SIDE_CLEAR + SIDE_AISLE_W
    zone_x1 = hall_x1 - SIDE_CLEAR - SIDE_AISLE_W
    zone_y0 = hall_y0 + REAR_CLEAR       # south end (row 1 is nearest dais = top)
    zone_y1 = hall_y1 - FRONT_CLEAR      # north end adjacent to dais

    usable_w = zone_x1 - zone_x0 - CENTRE_AISLE   # width after centre aisle
    usable_h = zone_y1 - zone_y0

    chairs_per_block = int(usable_w / 2 // CHAIR_W)   # 14
    n_rows            = int(usable_h // ROW_PITCH)      # 20

    half_w = chairs_per_block * CHAIR_W               # width of one block
    cx_zone = (zone_x0 + zone_x1) / 2

    left_block_x0  = cx_zone - CENTRE_AISLE/2 - half_w
    right_block_x0 = cx_zone + CENTRE_AISLE/2

    chair_w_pt = CHAIR_W * SCALE
    chair_d_pt = 18 * SCALE    # 18" depth visual
    row_pt     = ROW_PITCH * SCALE

    total_chairs = 0

    for row in range(n_rows):
        # Rows go from south (row 0 = rear) northward (closer to dais)
        row_y_model = zone_y0 + row * ROW_PITCH
        row_y_pt, _ = pp(origin, 0, row_y_model)
        _, row_y_pt = pp(origin, 0, row_y_model)

        row_label = f"R{row+1:02d}"

        for block_idx, block_x0_model in enumerate((left_block_x0, right_block_x0)):
            for col in range(chairs_per_block):
                cx_model = block_x0_model + col * CHAIR_W
                px, py = pp(origin, cx_model, row_y_model)
                # Seat label: R01-A … R01-N  (left block), R01-A … R01-N (right block)
                col_letter = chr(ord('A') + col)
                seat_label = f"R{row+1:02d}-{col_letter}"
                draw_pvc_chair(c, px, py, chair_w_pt, chair_d_pt,
                               seat_label=seat_label)
                total_chairs += 1

        # Row number label (on left margin)
        lx, ly = pp(origin, left_block_x0 - 20, row_y_model + 4)
        c.setFillColor(NUMBERING); c.setFont("Helvetica-Bold", 5)
        c.drawRightString(lx, ly, row_label)

        # Same label right side
        rx, ry = pp(origin, right_block_x0 + half_w + 6, row_y_model + 4)
        c.setFillColor(NUMBERING); c.setFont("Helvetica-Bold", 5)
        c.drawString(rx, ry, row_label)

    # Column letters along front row
    for block_x0_model in (left_block_x0, right_block_x0):
        for col in range(chairs_per_block):
            cx_model = block_x0_model + col * CHAIR_W + CHAIR_W/2
            cx_pt, _ = pp(origin, cx_model, 0)
            _, cy_pt = pp(origin, 0, zone_y0 - 12)
            c.setFillColor(NUMBERING); c.setFont("Helvetica-Bold", 5)
            c.drawCentredString(cx_pt, cy_pt,
                                chr(ord('A') + col))

    # ── Aisle dashed lines ──
    c.saveState()
    c.setStrokeColor(AISLE_DASH); c.setLineWidth(0.9); c.setDash(5, 4)

    def vline(x_model):
        px_, py0_ = pp(origin, x_model, zone_y0 - 10)
        _,   py1_ = pp(origin, x_model, zone_y1 + 10)
        c.line(px_, py0_, px_, py1_)

    # Left side aisle axis
    vline(left_block_x0 - SIDE_AISLE_W/2)
    # Right side aisle axis
    vline(right_block_x0 + half_w + SIDE_AISLE_W/2)
    # Centre aisle axis
    vline(cx_zone)

    c.setDash()
    c.restoreState()

    # ── Aisle labels ──
    def aisle_label(x_model, label):
        lx_, _ = pp(origin, x_model, 0)
        _, ly_ = pp(origin, 0, zone_y1 + 22)
        c.saveState()
        c.translate(lx_, ly_)
        c.rotate(90)
        c.setFillColor(GRAY); c.setFont("Helvetica-Bold", 5.5)
        c.drawCentredString(0, 0, label)
        c.restoreState()

    aisle_label(left_block_x0 - SIDE_AISLE_W/2, "SIDE AISLE — 3'-0\"")
    aisle_label(cx_zone,                          "CENTRE AISLE — 3'-0\"")
    aisle_label(right_block_x0 + half_w + SIDE_AISLE_W/2, "SIDE AISLE — 3'-0\"")

    # ── Total chair count annotation ──
    ann_x, ann_y = pp(origin, (hall_x0+hall_x1)/2, zone_y0 - 32)
    c.setFillColor(colors.HexColor("#1e3a8a"))
    c.setStrokeColor(colors.HexColor("#93c5fd"))
    c.roundRect(ann_x - 90, ann_y - 8, 180, 18, 3, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(ann_x, ann_y, f"TOTAL AUDIENCE SEATING : {total_chairs} PVC CHAIRS")

    return total_chairs


# ─────────────────────────────────────────────────────────────────────────────
# Draw Dais Seating (12 Executive Chairs)
# ─────────────────────────────────────────────────────────────────────────────
def draw_dais_seating(c, origin, dais_x0, dais_y0, dais_x1, dais_y1):
    """
    12 high-back executive chairs at curved dais table.
    President at centre, 5 to each side, podiums at both ends.
    """
    dais_cx   = (dais_x0 + dais_x1) / 2

    # ── Raised dais step edge ──
    c.saveState()
    c.setStrokeColor(DAIS_EDGE); c.setLineWidth(1.8)
    px0, py0 = pp(origin, dais_x0, dais_y0 + 6)
    px1, _   = pp(origin, dais_x1, dais_y0 + 6)
    c.line(px0, py0, px1, py0)
    c.setFillColor(DAIS_EDGE); c.setFont("Helvetica-Bold", 6)
    c.drawString(px0+4, py0+3, "RAISED DAIS  +1'-6\" F.F.L.")
    c.restoreState()

    # ── Curved dais table: 22'-0" long × 3'-6" deep = 264" × 42" ──
    TABLE_W  = 264   # inches
    TABLE_D  = 42    # inches
    table_x0 = dais_cx - TABLE_W/2
    table_y0 = dais_y0 + 52   # set back from dais edge

    tx0, ty0 = pp(origin, table_x0, table_y0)
    tw = TABLE_W * SCALE
    td = TABLE_D * SCALE

    c.saveState()
    # Table fill with subtle curve shadow
    c.setFillColor(DAIS_TABLE); c.setStrokeColor(DAIS_EDGE); c.setLineWidth(1.4)
    c.roundRect(tx0, ty0, tw, td, 8, stroke=1, fill=1)
    # Table gloss line
    c.setStrokeColor(colors.HexColor("#fef3c7")); c.setLineWidth(0.6)
    c.roundRect(tx0+4, ty0+4, tw-8, td-8, 6, stroke=1, fill=0)
    # Name plate strip
    c.setFillColor(colors.HexColor("#92400e"))
    c.rect(tx0+8, ty0+td-10, tw-16, 8, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 5.5)
    c.drawCentredString(tx0+tw/2, ty0+td-5, "DAIS TABLE — BAR ASSOCIATION HALL, BANSWARA")
    c.restoreState()

    # ── 12 executive chairs behind the table (south face) ──
    N_CHAIRS  = 12
    CHAIR_W_M = 22   # model-inches per chair (tighter exec spacing)
    CHAIR_D_M = 28   # model-inches depth

    chair_w_pt = CHAIR_W_M * SCALE
    chair_d_pt = CHAIR_D_M * SCALE

    total_chairs_w = N_CHAIRS * CHAIR_W_M
    chair_start_x  = dais_cx - total_chairs_w / 2
    chair_y        = table_y0 + TABLE_D + 8   # just behind table

    for i in range(N_CHAIRS):
        cx_model = chair_start_x + i * CHAIR_W_M + CHAIR_W_M/2
        cx_pt, cy_pt = pp(origin, cx_model, chair_y)
        is_president = (i == N_CHAIRS // 2 - 1) or (i == N_CHAIRS // 2)
        # Centre two chairs = President positions; use single president marker on seat 6 (0-indexed 5)
        draw_exec_chair(c, cx_pt, cy_pt, chair_w_pt, chair_d_pt,
                        is_president=(i == N_CHAIRS // 2 - 1))
        # ── Dais seat number label ──
        seat_no = f"D-{i+1:02d}"
        c.setFillColor(colors.white if (i == N_CHAIRS // 2 - 1) else EXEC_STROKE)
        c.setFont("Helvetica-Bold", 4.0)
        c.drawCentredString(cx_pt, cy_pt + chair_d_pt * 0.28, seat_no)

    # President label
    pres_cx_model = chair_start_x + (N_CHAIRS//2 - 1) * CHAIR_W_M + CHAIR_W_M/2
    px_, py_ = pp(origin, pres_cx_model, chair_y + CHAIR_D_M + 12)
    c.setFillColor(colors.HexColor("#581c87"))
    c.setFont("Helvetica-Bold", 6)
    c.drawCentredString(px_, py_, "PRESIDENT")

    # ── Podiums at left and right of table ──
    for pod_x_model, pod_label in [
        (table_x0 - 56, "PODIUM"),
        (table_x0 + TABLE_W + 16, "PODIUM"),
    ]:
        px_, py_ = pp(origin, pod_x_model, table_y0 + 6)
        pw = 36 * SCALE; pd = 28 * SCALE
        c.setFillColor(PODIUM_FILL); c.setStrokeColor(BLACK); c.setLineWidth(0.8)
        c.roundRect(px_, py_, pw, pd, 3, stroke=1, fill=1)
        # Microphone stand dot
        c.setFillColor(colors.HexColor("#fbbf24"))
        c.circle(px_+pw/2, py_+pd+4, 3, stroke=0, fill=1)
        c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 5)
        c.drawCentredString(px_+pw/2, py_+pd/2, pod_label)

    # ── Flag stands ──
    for fx, fy in [(dais_x0+20, dais_y0+60), (dais_x1-30, dais_y0+60)]:
        px_, py_ = pp(origin, fx, fy)
        c.setStrokeColor(DARK_GRAY); c.setLineWidth(0.8)
        c.line(px_, py_, px_, py_ + 20*SCALE)
        c.setFillColor(colors.HexColor("#ef4444"))
        c.rect(px_, py_+20*SCALE, 12*SCALE, 8*SCALE, stroke=0, fill=1)

    # ── Dais capacity annotation ──
    ann_x, ann_y = pp(origin, dais_cx, dais_y1 - 12)
    c.setFillColor(colors.HexColor("#4c1d95"))
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(ann_x, ann_y, "DAIS SEATING : 12 EXECUTIVE CHAIRS  |  PRESIDENT (CENTRE)")


# ─────────────────────────────────────────────────────────────────────────────
# Draw wall outlines of all spaces (simple, no furniture)
# ─────────────────────────────────────────────────────────────────────────────
def draw_walls(c, origin, spaces):
    # Zone fills
    ZONE = {
        "Assembly Hall":    FILL_HALL,
        "Dais":             FILL_DAIS,
        "Stair":            FILL_CIRC,
        "Reception":        FILL_CIRC,
        "Pantry":           FILL_SERVICE,
        "Toilet":           FILL_SERVICE,
    }
    def get_fill(name):
        for key, col in ZONE.items():
            if key in name:
                return col
        return PALE_BG

    for sp in spaces:
        x0, y0, x1, y1 = float(sp["rect"][0]), float(sp["rect"][1]), \
                          float(sp["rect"][2]), float(sp["rect"][3])
        sx, sy = pp(origin, x0, y0)
        sw = (x1-x0) * SCALE; sh = (y1-y0) * SCALE
        c.setFillColor(get_fill(sp["name"]))
        c.setStrokeColor(colors.HexColor("#94a3b8")); c.setLineWidth(0.5)
        c.rect(sx, sy, sw, sh, stroke=1, fill=1)

    # Perimeter heavy wall
    ext_x0 = min(float(s["rect"][0]) for s in spaces)
    ext_y0 = min(float(s["rect"][1]) for s in spaces)
    ext_x1 = max(float(s["rect"][2]) for s in spaces)
    ext_y1 = max(float(s["rect"][3]) for s in spaces)
    px0, py0 = pp(origin, ext_x0, ext_y0)
    ew = (ext_x1-ext_x0)*SCALE; eh = (ext_y1-ext_y0)*SCALE
    c.setStrokeColor(WALL_STROKE); c.setLineWidth(WALL_THICK)
    c.rect(px0, py0, ew, eh, stroke=1, fill=0)

    # Internal partition walls
    c.setStrokeColor(DARK_GRAY); c.setLineWidth(PART_THICK)
    for sp in spaces:
        x0, y0, x1, y1 = float(sp["rect"][0]), float(sp["rect"][1]), \
                          float(sp["rect"][2]), float(sp["rect"][3])
        sx, sy = pp(origin, x0, y0)
        sw = (x1-x0)*SCALE; sh = (y1-y0)*SCALE
        c.rect(sx, sy, sw, sh, stroke=1, fill=0)

    # Room name badges (light)
    for sp in spaces:
        x0, y0, x1, y1 = float(sp["rect"][0]), float(sp["rect"][1]), \
                          float(sp["rect"][2]), float(sp["rect"][3])
        sw = (x1-x0)*SCALE; sh = (y1-y0)*SCALE
        # Only label non-seating rooms (seating rooms labelled separately)
        if "Assembly Hall" in sp["name"] or "Dais" in sp["name"]:
            continue
        cx_, cy_ = pp(origin, (x0+x1)/2, (y0+y1)/2)
        c.setFillColor(CHARCOAL); c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(cx_, cy_+5, sp["name"].upper())
        c.setFillColor(GRAY); c.setFont("Helvetica", 5.5)
        c.drawCentredString(cx_, cy_-5,
                            f"{fmtft(x1-x0)} x {fmtft(y1-y0)}")


# ─────────────────────────────────────────────────────────────────────────────
# Main Sheet Composer
# ─────────────────────────────────────────────────────────────────────────────
def draw_seating_sheet(c, site, plans):
    global SCALE

    level  = "GF"
    spaces = [s for s in plans["spaces"] if s["level"] == level]

    # ── Page background ──
    c.setFillColor(colors.HexColor("#f0f4f8"))
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    # ── Border ──
    c.setStrokeColor(BLACK); c.setLineWidth(1.6)
    c.rect(18, 18, PAGE_W-36, PAGE_H-36, stroke=1, fill=0)
    c.setLineWidth(0.45); c.setStrokeColor(LIGHT_GRAY)
    c.rect(24, 24, PAGE_W-48, PAGE_H-48, stroke=1, fill=0)

    # ── Header strip ──
    HEADER_H = 72
    c.setFillColor(CHARCOAL)
    c.rect(26, PAGE_H - 26 - HEADER_H, PAGE_W-52, HEADER_H, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 15)
    c.drawString(40, PAGE_H - 26 - HEADER_H + 48,
                 "SP-101  |  GROUND FLOOR — SEATING ARRANGEMENT PLAN")
    c.setFont("Helvetica-Bold", 8); c.setFillColor(colors.HexColor("#a78bfa"))
    c.drawString(40, PAGE_H - 26 - HEADER_H + 30,
                 "AUDIENCE : 560 PVC CHAIRS  |  DAIS : 12 EXECUTIVE CHAIRS  |  TOTAL : 572 SEATS")
    c.setFont("Helvetica", 7); c.setFillColor(LIGHT_GRAY)
    c.drawString(40, PAGE_H - 26 - HEADER_H + 14,
                 "BANSWARA DISTRICT COURT COMPLEX, RAJASTHAN  ·  SEATING LAYOUT — FOR REVIEW")

    # ── Title block (bottom strip) ──
    draw_title_block(c)
    TB_H = 88   # height of title block at bottom

    # ── Right-side info strip ──
    STRIP_W   = 310          # width reserved on right for legend + north + scale
    MARGIN_L  = 30           # left margin from border
    MARGIN_R  = 30           # right margin from border
    TOP_Y     = PAGE_H - 26 - HEADER_H - 8   # just below header
    BOT_Y     = 18 + TB_H + 8                # just above title block

    # Drawing area (plan goes here)
    draw_area_x0 = 18 + MARGIN_L
    draw_area_x1 = PAGE_W - 18 - MARGIN_R - STRIP_W - 8
    draw_area_y0 = BOT_Y
    draw_area_y1 = TOP_Y
    draw_area_w  = draw_area_x1 - draw_area_x0
    draw_area_h  = draw_area_y1 - draw_area_y0

    # Plan extents in model-inches
    plan_x0 = min(float(s["rect"][0]) for s in spaces)
    plan_y0 = min(float(s["rect"][1]) for s in spaces)
    plan_x1 = max(float(s["rect"][2]) for s in spaces)
    plan_y1 = max(float(s["rect"][3]) for s in spaces)
    plan_w  = plan_x1 - plan_x0
    plan_h  = plan_y1 - plan_y0

    # Fit-to-area scale (no cap — maximise plan size)
    scale_x = draw_area_w / plan_w
    scale_y = draw_area_h / plan_h
    SCALE   = min(scale_x, scale_y) * 0.96   # 96% of available = small margin

    # Centre plan in drawing area
    draw_w  = plan_w * SCALE
    draw_h  = plan_h * SCALE
    orig_x  = draw_area_x0 + (draw_area_w - draw_w) / 2
    orig_y  = draw_area_y0 + (draw_area_h - draw_h) / 2
    origin  = (orig_x - plan_x0*SCALE, orig_y - plan_y0*SCALE)

    # ── 1. Wall outlines + zone fills ──
    draw_walls(c, origin, spaces)

    # ── 2. Find Assembly Hall + Dais spaces ──
    hall = next(s for s in spaces if "Assembly Hall" in s["name"])
    dais = next(s for s in spaces if "Dais" in s["name"])

    hx0, hy0 = float(hall["rect"][0]), float(hall["rect"][1])
    hx1, hy1 = float(hall["rect"][2]), float(hall["rect"][3])
    dx0, dy0 = float(dais["rect"][0]), float(dais["rect"][1])
    dx1, dy1 = float(dais["rect"][2]), float(dais["rect"][3])

    # ── 3. Audience seating ──
    total_audience = draw_audience_seating(c, origin, hx0, hy0, hx1, hy1)

    # ── 4. Dais seating ──
    draw_dais_seating(c, origin, dx0, dy0, dx1, dy1)

    # ── 5. Hall label ──
    hall_cx, hall_cy = pp(origin, (hx0+hx1)/2, hy1 - 18)
    c.setFillColor(CHARCOAL); c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(hall_cx, hall_cy, "MAIN ASSEMBLY HALL")

    # ── Right strip: panels stacked top-to-bottom ──
    strip_x = PAGE_W - 18 - MARGIN_R - STRIP_W
    strip_y  = TOP_Y    # current Y cursor (fills downward)

    # North rose + scale bar — top of strip
    north_cx = strip_x + STRIP_W - 36
    north_cy = strip_y - 44
    draw_north(c, north_cx, north_cy)
    draw_scale_bar(c, strip_x + 8, strip_y - 76)
    strip_y  = strip_y - 90

    # Legend panel
    legend_h = 190
    strip_y -= legend_h + 8
    draw_legend(c, strip_x, strip_y)

    # Summary table
    summ_h = 5 * 16   # 3 data rows + 2 header rows
    strip_y -= summ_h + 8
    draw_summary_table(c, strip_x, strip_y)

    # Thin separator line between drawing and strip
    c.setStrokeColor(LIGHT_GRAY); c.setLineWidth(0.7)
    c.line(strip_x - 6, BOT_Y, strip_x - 6, TOP_Y)


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────
def main():
    site  = json.loads((SRC / "site_plan.json").read_text(encoding="utf-8"))
    plans = json.loads((SRC / "preliminary_plans.json").read_text(encoding="utf-8"))

    out_path = PDF_OUT / "SP-101-GF-SEATING-ARRANGEMENT-PLAN.pdf"
    c = canvas.Canvas(str(out_path), pagesize=landscape(A2))
    c.setCreator("generate_seating_plan.py — Bar Association Hall, Banswara")
    c.setTitle("SP-101 — Ground Floor Seating Arrangement Plan")

    draw_seating_sheet(c, site, plans)
    c.save()

    print(f"[OK] Seating plan generated: {out_path.name}")
    print(f"     Location : {out_path}")
    print(f"     Audience : 560 PVC chairs (20 rows x 28 cols, 3 aisles)")
    print(f"     Dais     : 12 executive chairs (President centre)")
    print(f"     Total    : 572 seats")


if __name__ == "__main__":
    main()
