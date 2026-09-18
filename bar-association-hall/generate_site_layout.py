"""
COURT CAMPUS MAHI COLONY BANSWARA (RAJ.)
=========================================
Sheet SL-01 — Proposed Site Layout Plan
Showing: Existing site context + Proposed Bar Association Hall footprint

Site:     Area (A) = 205,400 sq ft  (approx 454' × 453')
Building: Bar Association Hall — G+1
          Footprint: 90'-0" (E-W longer wall) × 55'-6" (N-S shorter wall)
          Orientation: Longer wall East-West (parallel to BT Road south boundary)
          Position: NW zone, near Shiv Temple, inside boundary with setbacks

Setbacks (proposed):
  North  : 15'-0"  (from north boundary)
  West   : 20'-0"  (from west BT Road boundary — magenta)
  South  : open (garden / approach)
  East   : open (internal campus road)

Main Entrance : East long wall (as per approved design)
North arrow   : Up = North

Paper: A2 Landscape
Scale: 1" = 20'-0"  (1/240)
"""

from __future__ import annotations
import math
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A2, landscape
from reportlab.pdfgen import canvas

# ─────────────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parent
PDF_OUT = ROOT / "PDF"
PDF_OUT.mkdir(exist_ok=True)

PAGE_W, PAGE_H = landscape(A2)

# ─────────────────────────────────────────────────────────────────────────────
# Scale: 1" paper = 20' site  →  1 site-foot = PAGE_PT / 20
# We work in FEET for site plan
# ─────────────────────────────────────────────────────────────────────────────
SCALE = 1.8   # PDF points per site-foot  (≈ 1"=20' on A2)

def p(x_ft, y_ft, ox=0, oy=0):
    """Convert site feet to PDF points with origin offset."""
    return ox + x_ft * SCALE, oy + y_ft * SCALE

# ─────────────────────────────────────────────────────────────────────────────
# Colours
# ─────────────────────────────────────────────────────────────────────────────
BLACK       = colors.HexColor("#0d1117")
DARK_GRAY   = colors.HexColor("#334155")
GRAY        = colors.HexColor("#64748b")
LIGHT_GRAY  = colors.HexColor("#cbd5e1")
PALE_BG     = colors.HexColor("#f8fafc")

# Site elements (matching CAD drawing conventions)
BOUNDARY    = colors.HexColor("#1e40af")   # blue — site boundary
BT_ROAD_CLR = colors.HexColor("#c026d3")   # magenta — BT Road
INT_ROAD    = colors.HexColor("#d97706")   # amber — internal roads
GARDEN_CLR  = colors.HexColor("#16a34a")   # green — garden / landscape
BUILDING_EX = colors.HexColor("#94a3b8")   # grey — existing buildings
BUILDING_PR = colors.HexColor("#1e293b")   # dark — proposed building
BUILDING_FL = colors.HexColor("#fef3c7")   # cream — proposed floor fill
SETBACK_CLR = colors.HexColor("#fecdd3")   # pink — setback zone
PORCH_CLR   = colors.HexColor("#fde68a")   # amber — entrance porch
TEMPLE_CLR  = colors.HexColor("#f97316")   # orange — Shiv Temple
PARKING_CLR = colors.HexColor("#e2e8f0")   # light — parking
TREE_CLR    = colors.HexColor("#15803d")   # dark green — trees
DIM_CLR     = colors.HexColor("#1e293b")   # dim lines

# ─────────────────────────────────────────────────────────────────────────────
# Site geometry (feet) — from PDF site plan dimensions
# Origin = SW corner of Area (A) main campus boundary
# Site approx 454' E-W × 453' N-S (205,400 sq ft)
# ─────────────────────────────────────────────────────────────────────────────
SITE_W = 454.0   # E-W
SITE_H = 453.0   # N-S

# Drawing origin on PDF page (SW corner of site)
OX = 48.0   # PDF points from left
OY = 108.0  # PDF points from bottom

def pt(x_ft, y_ft):
    return OX + x_ft * SCALE, OY + y_ft * SCALE

# ─────────────────────────────────────────────────────────────────────────────
# Key coordinates (feet from SW origin)
# ─────────────────────────────────────────────────────────────────────────────
# West BT Road (magenta) — runs N-S along west boundary
BT_ROAD_W  = 0      # west edge of campus (road boundary)
BT_ROAD_E  = 30     # road width ~30'

# South BT Road — runs E-W along south boundary
BT_ROAD_S  = 0
BT_ROAD_N_S= 24     # road width ~24'

# Shiv Temple — NW corner, approx 30' from west, 380' from south
TEMPLE_X   = 36
TEMPLE_Y   = 390
TEMPLE_W   = 42
TEMPLE_H   = 38

# Existing Court Building — centre of site
COURT_X    = 140
COURT_Y    = 160
COURT_W    = 220
COURT_H    = 200

# Parking — SW zone
PARK_X     = 32
PARK_Y     = 24
PARK_W     = 100
PARK_H     = 80

# Gardens — south strip
GARD1_X    = 32
GARD1_Y    = 108
GARD1_W    = 90
GARD1_H    = 45

# ─────────────────────────────────────────────────────────────────────────────
# PROPOSED BAR ASSOCIATION HALL
# Longer wall = E-W = 90'-0"
# Shorter wall = N-S = 55'-6" = 55.5'
# Position: NW zone, near Shiv Temple
# Setbacks: West=20', North=15' from boundary
# ─────────────────────────────────────────────────────────────────────────────
HALL_W  = 90.0    # E-W (longer)
HALL_H  = 55.5    # N-S (shorter)

# Place building: west side = 50' from west boundary (20' setback + 30' road)
# north side = SITE_H - 15' setback - HALL_H
HALL_X  = BT_ROAD_E + 20   # = 50' from west boundary
HALL_Y  = SITE_H - 15 - HALL_H  # = 382.5' from south

# Entrance porch — East long wall, centred at mid-height of hall
PORCH_W  = 8.0    # 8' deep (east)
PORCH_H  = 12.0   # 12' wide (N-S)
PORCH_X  = HALL_X + HALL_W
PORCH_Y  = HALL_Y + (HALL_H - PORCH_H) / 2

# Approach road from internal campus road to porch
APPROACH_W = PORCH_W + 40  # extend 40' east of porch
APPROACH_Y0= PORCH_Y - 6
APPROACH_Y1= PORCH_Y + PORCH_H + 6

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def draw_tree(c, x_ft, y_ft, r_ft=3):
    px, py = pt(x_ft, y_ft)
    rp = r_ft * SCALE
    c.setFillColor(TREE_CLR); c.setStrokeColor(colors.HexColor("#065f46")); c.setLineWidth(0.6)
    c.circle(px, py, rp, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#bbf7d0")); c.setLineWidth(0)
    c.circle(px - rp*0.3, py + rp*0.3, rp*0.4, stroke=0, fill=1)

def draw_dim_h(c, x0_ft, x1_ft, y_ft, offset_ft, label):
    """Horizontal dimension line."""
    x0p, y0p = pt(x0_ft, y_ft + offset_ft)
    x1p, _   = pt(x1_ft, y_ft + offset_ft)
    ex0, ey0 = pt(x0_ft, y_ft)
    ex1, ey1 = pt(x1_ft, y_ft)
    c.setStrokeColor(DIM_CLR); c.setLineWidth(0.5)
    c.line(ex0, ey0, x0p, y0p)
    c.line(ex1, ey1, x1p, y0p)
    c.line(x0p, y0p, x1p, y0p)
    # Tick marks
    c.line(x0p-3, y0p-3, x0p+3, y0p+3)
    c.line(x1p-3, y0p-3, x1p+3, y0p+3)
    c.setFillColor(DIM_CLR); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString((x0p+x1p)/2, y0p+5, label)

def draw_dim_v(c, y0_ft, y1_ft, x_ft, offset_ft, label):
    """Vertical dimension line."""
    x0p, y0p = pt(x_ft + offset_ft, y0_ft)
    _,   y1p = pt(x_ft + offset_ft, y1_ft)
    ex0, ey0 = pt(x_ft, y0_ft)
    ex1, ey1 = pt(x_ft, y1_ft)
    c.setStrokeColor(DIM_CLR); c.setLineWidth(0.5)
    c.line(ex0, ey0, x0p, y0p)
    c.line(ex1, ey1, x0p, y1p)
    c.line(x0p, y0p, x0p, y1p)
    c.line(x0p-3, y0p-3, x0p+3, y0p+3)
    c.line(x0p-3, y1p-3, x0p+3, y1p+3)
    c.setFillColor(DIM_CLR); c.setFont("Helvetica-Bold", 7)
    c.saveState()
    c.translate(x0p - 14, (y0p+y1p)/2)
    c.rotate(90)
    c.drawCentredString(0, 0, label)
    c.restoreState()

def draw_north(c, cx, cy, r=18):
    c.saveState()
    c.setStrokeColor(BLACK); c.setLineWidth(1.2)
    c.circle(cx, cy, r, stroke=1, fill=0)
    p1 = c.beginPath()
    p1.moveTo(cx, cy+r); p1.lineTo(cx-6, cy); p1.lineTo(cx, cy-r); p1.close()
    c.setFillColor(BLACK); c.drawPath(p1, fill=1, stroke=0)
    p2 = c.beginPath()
    p2.moveTo(cx, cy+r); p2.lineTo(cx+6, cy); p2.lineTo(cx, cy-r); p2.close()
    c.setFillColor(LIGHT_GRAY); c.drawPath(p2, fill=1, stroke=0)
    c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(cx, cy+r+6, "N")
    c.setFont("Helvetica", 6); c.setFillColor(GRAY)
    c.drawCentredString(cx, cy-r-10, "NORTH")
    c.restoreState()

def draw_scale_bar(c, x, y):
    c.saveState()
    c.setFont("Helvetica-Bold", 7); c.setFillColor(DARK_GRAY)
    c.drawString(x, y+14, "GRAPHIC SCALE  1\" = 20'-0\"")
    segs = [0, 20, 40, 60, 80, 100]
    for i in range(len(segs)-1):
        sx0 = x + segs[i]*SCALE
        sw  = (segs[i+1]-segs[i])*SCALE
        c.setFillColor(BLACK if i%2==0 else colors.white)
        c.setStrokeColor(BLACK); c.setLineWidth(0.6)
        c.rect(sx0, y, sw, 5, stroke=1, fill=1)
    c.setFillColor(DARK_GRAY); c.setFont("Helvetica", 6)
    for ft in segs:
        c.drawCentredString(x + ft*SCALE, y-8, f"{ft}'")
    c.drawString(x + 100*SCALE + 4, y-8, "FEET")
    c.restoreState()

# ─────────────────────────────────────────────────────────────────────────────
# MAIN DRAWING FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def draw_site_layout(c):
    # ── Page background
    c.setFillColor(colors.HexColor("#f0f4f8"))
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    # ── Border
    c.setStrokeColor(BLACK); c.setLineWidth(1.6)
    c.rect(18, 18, PAGE_W-36, PAGE_H-36, stroke=1, fill=0)
    c.setLineWidth(0.45); c.setStrokeColor(LIGHT_GRAY)
    c.rect(24, 24, PAGE_W-48, PAGE_H-48, stroke=1, fill=0)

    # ── Header
    c.setFillColor(colors.HexColor("#1e293b"))
    c.rect(26, PAGE_H-100, PAGE_W-52, 74, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 16)
    c.drawString(44, PAGE_H-52, "SL-01  |  PROPOSED SITE LAYOUT PLAN")
    c.setFont("Helvetica-Bold", 9); c.setFillColor(colors.HexColor("#38bdf8"))
    c.drawString(44, PAGE_H-68, "BAR ASSOCIATION HALL — COURT CAMPUS, MAHI COLONY, BANSWARA (RAJ.)")
    c.setFont("Helvetica", 7.5); c.setFillColor(LIGHT_GRAY)
    c.drawString(44, PAGE_H-83, "PROPOSED BUILDING NEAR SHIV TEMPLE (NW ZONE)  ·  LONGER WALL EAST-WEST  ·  SCALE 1\" = 20'-0\"")

    # ═══════════════════════════════════════════════════════════════════════
    # 1. SITE BOUNDARY
    # ═══════════════════════════════════════════════════════════════════════
    bx0, by0 = pt(0, 0)
    bx1, by1 = pt(SITE_W, SITE_H)
    c.setFillColor(colors.HexColor("#fffbf0"))
    c.setStrokeColor(BOUNDARY); c.setLineWidth(2.0)
    c.rect(bx0, by0, SITE_W*SCALE, SITE_H*SCALE, stroke=1, fill=1)

    # Site boundary label
    c.setFillColor(BOUNDARY); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString((bx0+bx1)/2, by0-12, "SITE BOUNDARY — AREA (A) = 2,05,400 SQ.FT.")

    # ═══════════════════════════════════════════════════════════════════════
    # 2. BT ROADS
    # ═══════════════════════════════════════════════════════════════════════
    # West BT Road (magenta) — vertical, left of site
    wx0, wy0 = pt(BT_ROAD_W - BT_ROAD_E, 0)
    c.setFillColor(colors.HexColor("#fdf4ff"))
    c.setStrokeColor(BT_ROAD_CLR); c.setLineWidth(1.8)
    c.rect(wx0, wy0, BT_ROAD_E*SCALE, SITE_H*SCALE, stroke=1, fill=1)
    c.setFillColor(BT_ROAD_CLR); c.setFont("Helvetica-Bold", 7)
    c.saveState()
    c.translate(wx0 + BT_ROAD_E*SCALE/2 - 5, wy0 + SITE_H*SCALE/2)
    c.rotate(90)
    c.drawCentredString(0, 0, "B.T. ROAD (SH-32)  TO UDAIPUR / TO RATLAM")
    c.restoreState()

    # South BT Road (magenta) — horizontal, below site
    sx0, sy0 = pt(0, BT_ROAD_S - BT_ROAD_N_S)
    c.setFillColor(colors.HexColor("#fdf4ff"))
    c.setStrokeColor(BT_ROAD_CLR); c.setLineWidth(1.8)
    c.rect(sx0, sy0, SITE_W*SCALE, BT_ROAD_N_S*SCALE, stroke=1, fill=1)
    c.setFillColor(BT_ROAD_CLR); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(sx0 + SITE_W*SCALE/2, sy0+6, "B.T. ROAD (SH-32)")

    # ═══════════════════════════════════════════════════════════════════════
    # 3. INTERNAL CAMPUS ROAD
    # ═══════════════════════════════════════════════════════════════════════
    # Perimeter internal road (24' wide) inside boundary
    IROAD = 24
    irx0, iry0 = pt(BT_ROAD_E, IROAD)
    irw = (SITE_W - BT_ROAD_E) * SCALE
    irh = (SITE_H - 2*IROAD) * SCALE
    c.setFillColor(colors.HexColor("#fef9c3"))
    c.setStrokeColor(INT_ROAD); c.setLineWidth(1.2)
    c.rect(irx0, iry0, irw, irh, stroke=1, fill=0)
    c.setFillColor(INT_ROAD); c.setFont("Helvetica-Bold", 6)
    c.drawString(irx0+4, iry0+4, "INTERNAL CAMPUS ROAD (24' WIDE)")

    # ═══════════════════════════════════════════════════════════════════════
    # 4. PARKING
    # ═══════════════════════════════════════════════════════════════════════
    pkx, pky = pt(PARK_X, PARK_Y)
    c.setFillColor(PARKING_CLR); c.setStrokeColor(DARK_GRAY); c.setLineWidth(0.8)
    c.rect(pkx, pky, PARK_W*SCALE, PARK_H*SCALE, stroke=1, fill=1)
    # Parking bays (lines)
    bay_w = 9 * SCALE
    c.setStrokeColor(GRAY); c.setLineWidth(0.4)
    for bi in range(1, int(PARK_W/9)):
        bpx = pkx + bi*bay_w
        c.line(bpx, pky, bpx, pky + PARK_H*SCALE)
    c.setFillColor(DARK_GRAY); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(pkx + PARK_W*SCALE/2, pky + PARK_H*SCALE/2 + 4, "PARKING")
    c.setFont("Helvetica", 6)
    c.drawCentredString(pkx + PARK_W*SCALE/2, pky + PARK_H*SCALE/2 - 6, "4,300 SQ.FT.")

    # ═══════════════════════════════════════════════════════════════════════
    # 5. GARDENS
    # ═══════════════════════════════════════════════════════════════════════
    for gx, gy, gw, gh, glbl in [
        (32,  108, 90, 45, "GARDEN"),
        (130, 108, 90, 45, "GARDEN"),
    ]:
        gxp, gyp = pt(gx, gy)
        c.setFillColor(colors.HexColor("#dcfce7"))
        c.setStrokeColor(GARDEN_CLR); c.setLineWidth(0.8)
        c.rect(gxp, gyp, gw*SCALE, gh*SCALE, stroke=1, fill=1)
        # Grass hatch
        c.setStrokeColor(colors.HexColor("#86efac")); c.setLineWidth(0.3)
        for gi in range(0, gw, 8):
            c.line(gxp+gi*SCALE, gyp, gxp+gi*SCALE, gyp+gh*SCALE)
        c.setFillColor(GARDEN_CLR); c.setFont("Helvetica-Bold", 6.5)
        c.drawCentredString(gxp+gw*SCALE/2, gyp+gh*SCALE/2, glbl)

    # ═══════════════════════════════════════════════════════════════════════
    # 6. EXISTING COURT BUILDING
    # ═══════════════════════════════════════════════════════════════════════
    ecx, ecy = pt(COURT_X, COURT_Y)
    c.setFillColor(colors.HexColor("#e2e8f0"))
    c.setStrokeColor(colors.HexColor("#475569")); c.setLineWidth(1.4)
    c.rect(ecx, ecy, COURT_W*SCALE, COURT_H*SCALE, stroke=1, fill=1)
    # Hatch pattern
    c.setStrokeColor(colors.HexColor("#94a3b8")); c.setLineWidth(0.35)
    for hi in range(0, COURT_W, 12):
        c.line(ecx+hi*SCALE, ecy, ecx+hi*SCALE, ecy+COURT_H*SCALE)
    c.setFillColor(colors.HexColor("#1e293b")); c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(ecx+COURT_W*SCALE/2, ecy+COURT_H*SCALE/2+8, "EXISTING")
    c.drawCentredString(ecx+COURT_W*SCALE/2, ecy+COURT_H*SCALE/2-6, "COURT BUILDING")
    c.setFont("Helvetica", 7)
    c.drawCentredString(ecx+COURT_W*SCALE/2, ecy+COURT_H*SCALE/2-18, f"{COURT_W:.0f}' × {COURT_H:.0f}'")

    # ═══════════════════════════════════════════════════════════════════════
    # 7. SHIV TEMPLE (NW corner)
    # ═══════════════════════════════════════════════════════════════════════
    tx, ty = pt(TEMPLE_X, TEMPLE_Y)
    c.setFillColor(colors.HexColor("#fff7ed"))
    c.setStrokeColor(TEMPLE_CLR); c.setLineWidth(1.4)
    c.rect(tx, ty, TEMPLE_W*SCALE, TEMPLE_H*SCALE, stroke=1, fill=1)
    # Temple symbol — cross
    tcx = tx + TEMPLE_W*SCALE/2
    tcy = ty + TEMPLE_H*SCALE/2
    c.setStrokeColor(TEMPLE_CLR); c.setLineWidth(1.2)
    c.line(tcx, ty+4, tcx, ty+TEMPLE_H*SCALE-4)
    c.line(tx+4, tcy, tx+TEMPLE_W*SCALE-4, tcy)
    c.setFillColor(TEMPLE_CLR); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(tcx, ty-10, "SHIV TEMPLE")

    # ═══════════════════════════════════════════════════════════════════════
    # 8. SETBACK ZONE (dashed boundary around proposed building)
    # ═══════════════════════════════════════════════════════════════════════
    SET_N = 15; SET_W = 20; SET_S = 20; SET_E = 20
    szx, szy = pt(HALL_X - SET_W, HALL_Y - SET_S)
    szw = (HALL_W + SET_W + SET_E) * SCALE
    szh = (HALL_H + SET_S + SET_N) * SCALE
    c.setStrokeColor(SETBACK_CLR); c.setLineWidth(0.8); c.setDash(6, 3)
    c.rect(szx, szy, szw, szh, stroke=1, fill=0)
    c.setDash()
    c.setFillColor(SETBACK_CLR); c.setFont("Helvetica", 6)
    c.drawString(szx+3, szy+3, "SETBACK ZONE")

    # ═══════════════════════════════════════════════════════════════════════
    # 9. PROPOSED BAR ASSOCIATION HALL — MAIN ELEMENT
    # ═══════════════════════════════════════════════════════════════════════
    hx, hy = pt(HALL_X, HALL_Y)
    hw = HALL_W * SCALE
    hh = HALL_H * SCALE

    # Floor fill
    c.setFillColor(BUILDING_FL)
    c.rect(hx, hy, hw, hh, stroke=0, fill=1)

    # Wall thickness (3' at scale)
    WALL_T = 3 * SCALE
    c.setFillColor(BUILDING_PR)
    # South wall
    c.rect(hx, hy, hw, WALL_T, stroke=0, fill=1)
    # North wall
    c.rect(hx, hy+hh-WALL_T, hw, WALL_T, stroke=0, fill=1)
    # West wall
    c.rect(hx, hy, WALL_T, hh, stroke=0, fill=1)
    # East wall
    c.rect(hx+hw-WALL_T, hy, WALL_T, hh, stroke=0, fill=1)

    # RCC corner columns (red-brown)
    COL_SZ = WALL_T * 1.5
    for ccx, ccy in [(hx, hy), (hx+hw-COL_SZ, hy),
                     (hx, hy+hh-COL_SZ), (hx+hw-COL_SZ, hy+hh-COL_SZ)]:
        c.setFillColor(colors.HexColor("#8b1a1a"))
        c.rect(ccx, ccy, COL_SZ, COL_SZ, stroke=0, fill=1)

    # Building outline
    c.setStrokeColor(BUILDING_PR); c.setLineWidth(2.2)
    c.rect(hx, hy, hw, hh, stroke=1, fill=0)

    # Service core (NW inside building)
    sc_w = 55 * SCALE; sc_h = 15 * SCALE
    c.setFillColor(colors.HexColor("#bfdbfe"))
    c.setStrokeColor(BUILDING_PR); c.setLineWidth(0.8)
    c.rect(hx + WALL_T, hy + hh - WALL_T - sc_h, sc_w, sc_h, stroke=1, fill=1)
    c.setFillColor(DARK_GRAY); c.setFont("Helvetica", 5.5)
    c.drawCentredString(hx + WALL_T + sc_w/2,
                        hy + hh - WALL_T - sc_h/2,
                        "SERVICE CORE")

    # Assembly hall zone label
    c.setFillColor(BUILDING_PR); c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(hx + hw/2, hy + hh/2 + 10, "BAR ASSOCIATION HALL")
    c.setFont("Helvetica-Bold", 7.5); c.setFillColor(colors.HexColor("#0369a1"))
    c.drawCentredString(hx + hw/2, hy + hh/2 - 4, "G + 1  BUILDING")
    c.setFont("Helvetica", 6.5); c.setFillColor(DARK_GRAY)
    c.drawCentredString(hx + hw/2, hy + hh/2 - 16,
                        f"{HALL_W:.0f}'-0\" (E-W)  ×  {HALL_H:.0f}'-6\" (N-S)")
    c.drawCentredString(hx + hw/2, hy + hh/2 - 26,
                        "PLINTH AREA = 4,995 SQ.FT. PER FLOOR")
    c.setFont("Helvetica", 6); c.setFillColor(colors.HexColor("#b91c1c"))
    c.drawCentredString(hx + hw/2, hy + hh/2 - 36,
                        "PROPOSED — FOR APPROVAL")

    # ═══════════════════════════════════════════════════════════════════════
    # 10. ENTRANCE PORCH (East side — main entry)
    # ═══════════════════════════════════════════════════════════════════════
    px0, py0 = pt(PORCH_X, PORCH_Y)
    pw = PORCH_W * SCALE
    ph = PORCH_H * SCALE
    c.setFillColor(PORCH_CLR); c.setStrokeColor(colors.HexColor("#b45309")); c.setLineWidth(1.0)
    c.rect(px0, py0, pw, ph, stroke=1, fill=1)
    c.setDash(3, 2)
    c.rect(px0-2, py0-2, pw+4, ph+4, stroke=1, fill=0)
    c.setDash()
    c.setFillColor(colors.HexColor("#92400e")); c.setFont("Helvetica-Bold", 5.5)
    c.drawCentredString(px0+pw/2, py0+ph/2+2, "PORCH")
    c.drawCentredString(px0+pw/2, py0+ph/2-6, "12'×8'")

    # Main entrance arrow
    arr_x = px0 + pw + 20
    arr_y = py0 + ph/2
    c.setStrokeColor(colors.HexColor("#dc2626")); c.setLineWidth(1.2)
    c.line(arr_x, arr_y, px0+pw+4, arr_y)
    c.line(px0+pw+4, arr_y, px0+pw+10, arr_y+5)
    c.line(px0+pw+4, arr_y, px0+pw+10, arr_y-5)
    c.setFillColor(colors.HexColor("#dc2626")); c.setFont("Helvetica-Bold", 6.5)
    c.drawString(arr_x+3, arr_y+2, "MAIN ENTRY")

    # ═══════════════════════════════════════════════════════════════════════
    # 11. APPROACH ROAD to entrance
    # ═══════════════════════════════════════════════════════════════════════
    apx, apy = pt(HALL_X + HALL_W + PORCH_W, PORCH_Y - 6)
    apw = 40 * SCALE
    aph = (PORCH_H + 12) * SCALE
    c.setFillColor(colors.HexColor("#fef9c3"))
    c.setStrokeColor(INT_ROAD); c.setLineWidth(0.7); c.setDash(4, 2)
    c.rect(apx, apy, apw, aph, stroke=1, fill=1)
    c.setDash()
    c.setFillColor(INT_ROAD); c.setFont("Helvetica", 5.5)
    c.drawCentredString(apx+apw/2, apy+aph/2, "APPROACH")

    # ═══════════════════════════════════════════════════════════════════════
    # 12. TREES along building perimeter
    # ═══════════════════════════════════════════════════════════════════════
    # South side of building
    for ti in range(6):
        draw_tree(c, HALL_X + 8 + ti*14, HALL_Y - 8, 3)
    # West side
    for ti in range(3):
        draw_tree(c, HALL_X - 8, HALL_Y + 8 + ti*16, 3)
    # NW corner (near Shiv Temple — larger trees)
    for ti in range(4):
        draw_tree(c, HALL_X - 15 + ti*8, HALL_Y + HALL_H + 10, 4)

    # ═══════════════════════════════════════════════════════════════════════
    # 13. DIMENSIONS
    # ═══════════════════════════════════════════════════════════════════════
    # Building width (E-W)
    draw_dim_h(c, HALL_X, HALL_X+HALL_W, HALL_Y, -12, f"{HALL_W:.0f}'-0\"  (E-W LONGER WALL)")
    # Building depth (N-S)
    draw_dim_v(c, HALL_Y, HALL_Y+HALL_H, HALL_X, -16, f"{HALL_H:.0f}'-6\"  (N-S)")
    # West setback
    draw_dim_h(c, BT_ROAD_E, HALL_X, HALL_Y+HALL_H/2, 8, "WEST SETBACK 20'-0\"")
    # North setback
    draw_dim_v(c, HALL_Y+HALL_H, SITE_H, HALL_X+HALL_W/2, 10, "NORTH SETBACK 15'-0\"")

    # ═══════════════════════════════════════════════════════════════════════
    # 14. LEGEND BOX
    # ═══════════════════════════════════════════════════════════════════════
    lg_x = PAGE_W - 220
    lg_y = 108
    lg_w = 194
    lg_h = 200
    c.setFillColor(PALE_BG); c.setStrokeColor(LIGHT_GRAY); c.setLineWidth(0.7)
    c.roundRect(lg_x, lg_y, lg_w, lg_h, 4, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.rect(lg_x, lg_y+lg_h-20, lg_w, 20, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 8)
    c.drawString(lg_x+8, lg_y+lg_h-14, "LEGEND")

    legend_items = [
        (BOUNDARY,     "SITE BOUNDARY"),
        (BT_ROAD_CLR,  "B.T. ROAD (MAGENTA)"),
        (INT_ROAD,     "INTERNAL CAMPUS ROAD"),
        (BUILDING_PR,  "PROPOSED BUILDING"),
        (BUILDING_EX,  "EXISTING BUILDINGS"),
        (GARDEN_CLR,   "GARDEN / LANDSCAPE"),
        (PARKING_CLR,  "PARKING AREA"),
        (PORCH_CLR,    "ENTRANCE PORCH"),
        (TEMPLE_CLR,   "SHIV TEMPLE"),
        (SETBACK_CLR,  "SETBACK ZONE"),
        (TREE_CLR,     "TREES"),
    ]
    ly = lg_y + lg_h - 36
    for clr, lbl in legend_items:
        c.setFillColor(clr); c.setStrokeColor(DARK_GRAY); c.setLineWidth(0.4)
        c.rect(lg_x+10, ly, 14, 10, stroke=1, fill=1)
        c.setFillColor(DARK_GRAY); c.setFont("Helvetica", 7)
        c.drawString(lg_x+30, ly+2, lbl)
        ly -= 16

    # ═══════════════════════════════════════════════════════════════════════
    # 15. NORTH ROSE & SCALE BAR
    # ═══════════════════════════════════════════════════════════════════════
    draw_north(c, PAGE_W - 80, PAGE_H - 160)
    draw_scale_bar(c, PAGE_W - 320, PAGE_H - 175)

    # ═══════════════════════════════════════════════════════════════════════
    # 16. TITLE BLOCK
    # ═══════════════════════════════════════════════════════════════════════
    TB_X = 18; TB_Y = 18; TB_W = PAGE_W-36; TB_H = 78
    c.setFillColor(colors.HexColor("#f1f5f9"))
    c.setStrokeColor(BLACK); c.setLineWidth(0.8)
    c.rect(TB_X, TB_Y, TB_W, TB_H, stroke=1, fill=1)

    col1 = TB_X + TB_W*0.35
    col2 = TB_X + TB_W*0.72
    c.setLineWidth(0.6)
    c.line(col1, TB_Y, col1, TB_Y+TB_H)
    c.line(col2, TB_Y, col2, TB_Y+TB_H)

    # Block 1
    c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 12)
    c.drawString(TB_X+10, TB_Y+TB_H-20, "COURT CAMPUS, MAHI COLONY, BANSWARA (RAJ.)")
    c.setFont("Helvetica-Bold", 8); c.setFillColor(colors.HexColor("#0369a1"))
    c.drawString(TB_X+10, TB_Y+TB_H-34, "PROPOSED ADVOCATE CHAMBERS / BAR ASSOCIATION HALL")
    c.setFont("Helvetica", 7); c.setFillColor(GRAY)
    c.drawString(TB_X+10, TB_Y+TB_H-48, "SITE: AREA (A) = 2,05,400 SQ.FT.  |  BUILDING FOOTPRINT: 4,995 SQ.FT.")
    c.setFont("Helvetica-Bold", 7); c.setFillColor(DARK_GRAY)
    c.drawString(TB_X+10, TB_Y+16, "SETBACKS: NORTH 15' | WEST 20' | EAST & SOUTH OPEN")
    c.drawString(TB_X+10, TB_Y+5,  "STATUS: PROPOSED — FOR REVIEW  |  NOT FOR CONSTRUCTION")

    # Block 2
    dx = col1+10
    c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 11)
    c.drawString(dx, TB_Y+TB_H-20, "SITE LAYOUT PLAN")
    c.setFont("Helvetica-Bold", 8); c.setFillColor(colors.HexColor("#047857"))
    c.drawString(dx, TB_Y+TB_H-34, "SHOWING PROPOSED BUILDING FOOTPRINT")
    c.setFont("Helvetica", 7.5); c.setFillColor(DARK_GRAY)
    c.drawString(dx, TB_Y+TB_H-48, "SCALE: 1\" = 20'-0\"  |  PAPER: A2 LANDSCAPE")
    c.setFont("Helvetica-Bold", 7); c.setFillColor(BLACK)
    c.drawString(dx, TB_Y+16, "ORIENTATION: LONGER WALL EAST-WEST")
    c.drawString(dx, TB_Y+5,  "MAIN ENTRY: EAST LONG WALL WITH COVERED PORCH")

    # Block 3 — Sheet ID
    sx = col2 + (PAGE_W-36-(col2-TB_X))/2
    c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(sx, TB_Y+48, "SL-01")
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(sx, TB_Y+32, "SHEET NO.")
    c.setFont("Helvetica", 6.5); c.setFillColor(GRAY)
    c.drawCentredString(sx, TB_Y+18, "REV: P01")
    c.drawCentredString(sx, TB_Y+7,
                        datetime.now(timezone.utc).strftime("%d-%b-%Y").upper())


# ─────────────────────────────────────────────────────────────────────────────
def main():
    out = PDF_OUT / "SL-01-PROPOSED-SITE-LAYOUT-PLAN.pdf"
    c = canvas.Canvas(str(out), pagesize=landscape(A2))
    c.setCreator("generate_site_layout.py — Bar Association Hall, Banswara")
    c.setTitle("SL-01 — Proposed Site Layout Plan")
    draw_site_layout(c)
    c.save()
    print(f"[OK] Site layout generated: {out.name}")
    print(f"     Location : {out}")
    print(f"     Building : {HALL_W:.0f}'-0\" (E-W) x {HALL_H:.0f}'-6\" (N-S)")
    print(f"     Position : {HALL_X:.0f}' from west boundary, {SITE_H-HALL_Y-HALL_H:.0f}' from north boundary")
    print(f"     Scale    : 1\" = 20'-0\"")

if __name__ == "__main__":
    main()
