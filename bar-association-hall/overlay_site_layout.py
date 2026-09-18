"""
OVERLAY: Proposed Bar Association Hall footprint onto existing site plan PDF
=============================================================================
Input  : INPUTS/A COURT CAMPUS IN MAHI COLONY 01 09 2025.pdf  (A0 Portrait)
Output : PDF/SL-02-SITE-LAYOUT-OVERLAY.pdf

Strategy:
  - Existing PDF page = 1684 × 2384 pt (A0 Portrait)
  - The site plan is rotated ~15° anticlockwise on the sheet
  - We use pypdf to stamp a transparent overlay (reportlab) onto the base PDF
  - Overlay draws: proposed building footprint, porch, approach road,
    setback dashes, trees, dimension callouts, legend patch, revision cloud

Coordinate mapping (calibrated from PDF site plan):
  The existing drawing shows the campus roughly as:
    Top    = South (Garh side)
    Bottom = North (Main road / BT Road SH-32)
    Left   = East
    Right  = West
  BUT the drawing is rotated ~15° on the A0 sheet.

  We pick two known reference points from the existing PDF:
    Ref A = SW corner of main campus boundary (near BT road junction)
            → approximately PDF point (310, 260)
    Ref B = NE corner of campus boundary
            → approximately PDF point (1340, 1980)

  Campus size = Area(A) ≈ 205,400 sq ft  ≈ 454' × 453'
  Scale factor = dist(A,B) / sqrt(454²+453²) in pt/ft

  Building placement (NW zone of campus, near Shiv Temple):
    - In campus coords: X=50' from west, Y=382' from south (north zone)
    - Longer wall E-W = 90', shorter N-S = 55.5'
    - Main entry on East long wall
"""

from __future__ import annotations
import math
import io
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, FloatObject
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas

# ─────────────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).resolve().parent
INPUT_PDF = ROOT / "INPUTS" / "A COURT CAMPUS  IN MAHI COLONY  01 09 2025.pdf"
OUT_PDF   = ROOT / "PDF" / "SL-02-SITE-LAYOUT-OVERLAY.pdf"

# ─────────────────────────────────────────────────────────────────────────────
# Page dimensions (from pypdf read)
PAGE_W = 1684.0   # pt (A0 portrait width)
PAGE_H = 2384.0   # pt (A0 portrait height)

# ─────────────────────────────────────────────────────────────────────────────
# CALIBRATION — Two reference points in PDF coordinates
# These are calibrated by visual inspection of the campus boundary corners
# on the existing 1684×2384 pt page.
#
# The site plan drawing on the page is oriented with:
#   North = bottom-left direction
#   South = top-right direction
#   Drawing is rotated ~15° anticlockwise from portrait orientation
#
# Ref A = South-West campus corner (near BT Road / SH-32 junction, bottom)
REF_A_PDF = (335.0, 290.0)    # (x, y) in PDF points  [bottom-left area]
# Ref B = North-East campus corner (top of drawing, near Mahi CE Office)
REF_B_PDF = (1340.0, 1970.0)  # (x, y) in PDF points  [top-right area]

# Campus size in feet
CAMPUS_W_FT = 454.0   # E-W
CAMPUS_H_FT = 453.0   # N-S

# Compute scale (pt per foot) and rotation angle
dx_pdf = REF_B_PDF[0] - REF_A_PDF[0]
dy_pdf = REF_B_PDF[1] - REF_A_PDF[1]
dist_pdf = math.sqrt(dx_pdf**2 + dy_pdf**2)
dist_ft  = math.sqrt(CAMPUS_W_FT**2 + CAMPUS_H_FT**2)
SCALE_PT_FT = dist_pdf / dist_ft   # PDF points per foot

# Drawing rotation angle (angle of campus diagonal in PDF space)
DRAW_ANGLE = math.atan2(dy_pdf, dx_pdf)  # radians

def campus_to_pdf(x_ft: float, y_ft: float) -> tuple[float, float]:
    """
    Convert campus coordinates (feet, origin = SW corner) to PDF points.
    Campus X = East, Campus Y = North (up).
    The drawing is rotated DRAW_ANGLE on the PDF page.
    """
    # Scale
    xs = x_ft * SCALE_PT_FT
    ys = y_ft * SCALE_PT_FT
    # Rotate
    cos_a = math.cos(DRAW_ANGLE)
    sin_a = math.sin(DRAW_ANGLE)
    xr = xs * cos_a - ys * sin_a
    yr = xs * sin_a + ys * cos_a
    # Translate to Ref A
    px = REF_A_PDF[0] + xr
    py = REF_A_PDF[1] + yr
    return px, py

# ─────────────────────────────────────────────────────────────────────────────
# BUILDING PARAMETERS (feet, campus coords)
# ─────────────────────────────────────────────────────────────────────────────
HALL_X   = 50.0    # east from west boundary
HALL_Y   = 382.5   # north from south boundary (puts building in NW zone)
HALL_W   = 90.0    # E-W longer wall
HALL_H   = 55.5    # N-S shorter wall

# Entrance porch (east long wall, centred)
PORCH_D  = 8.0     # depth east
PORCH_W  = 12.0    # width N-S
PORCH_X  = HALL_X + HALL_W
PORCH_Y  = HALL_Y + (HALL_H - PORCH_W) / 2

# ─────────────────────────────────────────────────────────────────────────────
# COLOURS
# ─────────────────────────────────────────────────────────────────────────────
WALL_CLR    = colors.HexColor("#1e293b")
FLOOR_CLR   = colors.HexColor("#fef9c3")    # pale yellow — proposed fill
PORCH_CLR   = colors.HexColor("#fde68a")
COL_CLR     = colors.HexColor("#8b1a1a")
SETBACK_CLR = colors.HexColor("#f43f5e")
DIM_CLR     = colors.HexColor("#0f172a")
LABEL_CLR   = colors.HexColor("#0369a1")
TREE_CLR    = colors.HexColor("#15803d")
CLOUD_CLR   = colors.HexColor("#dc2626")
SHADOW_CLR  = colors.Color(0, 0, 0, alpha=0.18)

# ─────────────────────────────────────────────────────────────────────────────
def draw_tree_overlay(c, cx, cy, r=4.5):
    c.setFillColor(TREE_CLR); c.setStrokeColor(colors.HexColor("#065f46"))
    c.setLineWidth(0.6)
    c.circle(cx, cy, r, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#bbf7d0")); c.setLineWidth(0)
    c.circle(cx - r*0.3, cy + r*0.3, r*0.4, stroke=0, fill=1)

def draw_revision_cloud(c, x0, y0, x1, y1):
    """Draw revision cloud around proposed building."""
    c.saveState()
    c.setStrokeColor(CLOUD_CLR); c.setLineWidth(1.0); c.setDash(4, 3)
    pad = 18
    c.roundRect(x0-pad, y0-pad, (x1-x0)+2*pad, (y1-y0)+2*pad,
                12, stroke=1, fill=0)
    c.setDash()
    c.setFillColor(CLOUD_CLR); c.setFont("Helvetica-Bold", 7)
    c.drawString(x0-pad, y0-pad-10, "REVISION CLOUD — PROPOSED BUILDING")
    c.restoreState()

def draw_callout(c, tip_x, tip_y, label_x, label_y, text_lines):
    """Leader line with text box."""
    c.setStrokeColor(DIM_CLR); c.setLineWidth(0.8)
    c.line(tip_x, tip_y, label_x, label_y)
    c.setFillColor(colors.white); c.setStrokeColor(DIM_CLR); c.setLineWidth(0.6)
    box_w = max(len(t) for t in text_lines) * 5.5 + 10
    box_h = len(text_lines) * 11 + 6
    c.roundRect(label_x, label_y - 4, box_w, box_h, 3, stroke=1, fill=1)
    c.setFillColor(DIM_CLR); c.setFont("Helvetica-Bold", 7.5)
    for i, t in enumerate(text_lines):
        c.drawString(label_x + 5, label_y + (len(text_lines)-1-i)*11 + 2, t)

# ─────────────────────────────────────────────────────────────────────────────
# BUILD OVERLAY — transparent reportlab canvas same size as original PDF
# ─────────────────────────────────────────────────────────────────────────────
def build_overlay() -> bytes:
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))

    # ── 4 corners of proposed building in PDF coords ──────────────────────
    SW = campus_to_pdf(HALL_X,          HALL_Y)
    SE = campus_to_pdf(HALL_X + HALL_W, HALL_Y)
    NE = campus_to_pdf(HALL_X + HALL_W, HALL_Y + HALL_H)
    NW = campus_to_pdf(HALL_X,          HALL_Y + HALL_H)

    # Building centre
    CX = (SW[0]+SE[0]+NE[0]+NW[0])/4
    CY = (SW[1]+SE[1]+NE[1]+NW[1])/4

    # ── Draw angle in degrees (for rotated text/elements)
    ang_deg = math.degrees(DRAW_ANGLE)

    c.saveState()

    # ── 1. DROP SHADOW ────────────────────────────────────────────────────
    shadow_off = 6
    c.setFillColor(SHADOW_CLR)
    path = c.beginPath()
    path.moveTo(SW[0]+shadow_off, SW[1]-shadow_off)
    path.lineTo(SE[0]+shadow_off, SE[1]-shadow_off)
    path.lineTo(NE[0]+shadow_off, NE[1]-shadow_off)
    path.lineTo(NW[0]+shadow_off, NW[1]-shadow_off)
    path.close()
    c.drawPath(path, fill=1, stroke=0)

    # ── 2. SETBACK ZONE (dashed) ──────────────────────────────────────────
    SET_N=15; SET_S=20; SET_E=20; SET_W=20
    szSW = campus_to_pdf(HALL_X-SET_W,          HALL_Y-SET_S)
    szSE = campus_to_pdf(HALL_X+HALL_W+SET_E,   HALL_Y-SET_S)
    szNE = campus_to_pdf(HALL_X+HALL_W+SET_E,   HALL_Y+HALL_H+SET_N)
    szNW = campus_to_pdf(HALL_X-SET_W,          HALL_Y+HALL_H+SET_N)
    c.setStrokeColor(SETBACK_CLR); c.setLineWidth(1.0); c.setDash(6, 4)
    c.setFillColor(colors.Color(0.98, 0.9, 0.9, alpha=0.25))
    path2 = c.beginPath()
    path2.moveTo(*szSW); path2.lineTo(*szSE)
    path2.lineTo(*szNE); path2.lineTo(*szNW); path2.close()
    c.drawPath(path2, fill=1, stroke=1)
    c.setDash()

    # ── 3. FLOOR FILL ─────────────────────────────────────────────────────
    c.setFillColor(FLOOR_CLR)
    path3 = c.beginPath()
    path3.moveTo(*SW); path3.lineTo(*SE)
    path3.lineTo(*NE); path3.lineTo(*NW); path3.close()
    c.drawPath(path3, fill=1, stroke=0)

    # ── 4. WALLS (filled bands along each edge) ───────────────────────────
    WALL_T_FT = 1.0   # 1 foot wall thickness at this scale
    def wall_band(p0, p1, thickness_ft, inward_dir):
        """Draw a filled wall band along edge p0→p1."""
        tx = inward_dir[0] * thickness_ft * SCALE_PT_FT
        ty = inward_dir[1] * thickness_ft * SCALE_PT_FT
        pts = [p0, p1,
               (p1[0]+tx, p1[1]+ty),
               (p0[0]+tx, p0[1]+ty)]
        c.setFillColor(WALL_CLR)
        path = c.beginPath()
        path.moveTo(*pts[0])
        for pt in pts[1:]:
            path.lineTo(*pt)
        path.close()
        c.drawPath(path, fill=1, stroke=0)

    # Inward unit vectors for each wall
    # South wall (SW→SE): inward = North direction rotated
    north = (math.cos(DRAW_ANGLE + math.pi/2), math.sin(DRAW_ANGLE + math.pi/2))
    south = (-north[0], -north[1])
    east  = (math.cos(DRAW_ANGLE), math.sin(DRAW_ANGLE))
    west  = (-east[0], -east[1])

    wall_band(SW, SE, WALL_T_FT, north)   # south wall
    wall_band(NW, NE, WALL_T_FT, south)   # north wall
    wall_band(SW, NW, WALL_T_FT, east)    # west wall
    wall_band(SE, NE, WALL_T_FT, west)    # east wall

    # ── 5. OUTLINE ────────────────────────────────────────────────────────
    c.setStrokeColor(WALL_CLR); c.setLineWidth(2.8); c.setFillColor(colors.Color(0,0,0,0))
    path4 = c.beginPath()
    path4.moveTo(*SW); path4.lineTo(*SE)
    path4.lineTo(*NE); path4.lineTo(*NW); path4.close()
    c.drawPath(path4, fill=0, stroke=1)

    # ── 6. RCC CORNER COLUMNS ────────────────────────────────────────────
    col_sz = WALL_T_FT * 1.6 * SCALE_PT_FT
    for corner in [SW, SE, NE, NW]:
        cx_c, cy_c = corner[0] - col_sz/2, corner[1] - col_sz/2
        c.setFillColor(COL_CLR); c.setStrokeColor(WALL_CLR); c.setLineWidth(0.5)
        c.rect(cx_c, cy_c, col_sz, col_sz, stroke=1, fill=1)
        c.setStrokeColor(colors.HexColor("#3d0000")); c.setLineWidth(0.4)
        c.line(cx_c, cy_c, cx_c+col_sz, cy_c+col_sz)
        c.line(cx_c+col_sz, cy_c, cx_c, cy_c+col_sz)

    # ── 7. ENTRANCE PORCH ────────────────────────────────────────────────
    P_SW = campus_to_pdf(PORCH_X,          PORCH_Y)
    P_SE = campus_to_pdf(PORCH_X+PORCH_D,  PORCH_Y)
    P_NE = campus_to_pdf(PORCH_X+PORCH_D,  PORCH_Y+PORCH_W)
    P_NW = campus_to_pdf(PORCH_X,          PORCH_Y+PORCH_W)
    c.setFillColor(PORCH_CLR); c.setStrokeColor(colors.HexColor("#b45309")); c.setLineWidth(1.2)
    pp = c.beginPath()
    pp.moveTo(*P_SW); pp.lineTo(*P_SE); pp.lineTo(*P_NE); pp.lineTo(*P_NW); pp.close()
    c.drawPath(pp, fill=1, stroke=1)
    # Canopy dashes
    c.setDash(4, 3); c.setLineWidth(0.7)
    off = 5
    pp2 = c.beginPath()
    pp2.moveTo(P_SW[0]-off, P_SW[1]-off)
    pp2.lineTo(P_SE[0]+off, P_SE[1]-off)
    pp2.lineTo(P_NE[0]+off, P_NE[1]+off)
    pp2.lineTo(P_NW[0]-off, P_NW[1]+off)
    pp2.close()
    c.drawPath(pp2, fill=0, stroke=1)
    c.setDash()

    # ── 8. MAIN ENTRY ARROW ───────────────────────────────────────────────
    entry_cx = (P_SE[0]+P_NE[0])/2
    entry_cy = (P_SE[1]+P_NE[1])/2
    arrow_end_x = entry_cx + east[0]*30
    arrow_end_y = entry_cy + east[1]*30
    c.setStrokeColor(colors.HexColor("#dc2626")); c.setLineWidth(1.4)
    c.line(arrow_end_x, arrow_end_y, entry_cx, entry_cy)
    c.setFillColor(colors.HexColor("#dc2626"))
    c.circle(entry_cx, entry_cy, 3, stroke=0, fill=1)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(arrow_end_x + 4, arrow_end_y, "MAIN ENTRY")

    # ── 9. TREES ─────────────────────────────────────────────────────────
    # Along south face of building
    for ti in range(6):
        tp = campus_to_pdf(HALL_X + 8 + ti*13, HALL_Y - 7)
        draw_tree_overlay(c, tp[0], tp[1], 5)
    # Along west face
    for ti in range(3):
        tp = campus_to_pdf(HALL_X - 8, HALL_Y + 10 + ti*15)
        draw_tree_overlay(c, tp[0], tp[1], 5)
    # North of building (near Shiv Temple)
    for ti in range(4):
        tp = campus_to_pdf(HALL_X + ti*20, HALL_Y + HALL_H + 8)
        draw_tree_overlay(c, tp[0], tp[1], 6)

    # ── 10. REVISION CLOUD ────────────────────────────────────────────────
    all_pts = [SW, SE, NE, NW]
    min_x = min(p[0] for p in all_pts) - 25
    min_y = min(p[1] for p in all_pts) - 25
    max_x = max(p[0] for p in all_pts) + 25
    max_y = max(p[1] for p in all_pts) + 25
    c.setStrokeColor(CLOUD_CLR); c.setLineWidth(1.2); c.setDash(5, 3)
    c.roundRect(min_x, min_y, max_x-min_x, max_y-min_y, 16, stroke=1, fill=0)
    c.setDash()

    # ── 11. DIMENSION CALLOUTS ────────────────────────────────────────────
    # Building width label (E-W)
    mid_s = ((SW[0]+SE[0])/2, (SW[1]+SE[1])/2)
    dim_off_s = (north[0]*(-22), north[1]*(-22))
    draw_callout(c,
                 mid_s[0], mid_s[1],
                 mid_s[0]+dim_off_s[0]-10, mid_s[1]+dim_off_s[1]-28,
                 ["90'-0\" (E-W)", "LONGER WALL"])

    # Building depth label (N-S)
    mid_e = ((SE[0]+NE[0])/2, (SE[1]+NE[1])/2)
    draw_callout(c,
                 mid_e[0], mid_e[1],
                 mid_e[0]+east[0]*25, mid_e[1]+east[1]*25-10,
                 ["55'-6\" (N-S)", "SHORTER WALL"])

    # ── 12. BUILDING LABEL ────────────────────────────────────────────────
    # Rotate text to match drawing orientation
    c.saveState()
    c.translate(CX, CY)
    c.rotate(ang_deg)
    c.setFillColor(LABEL_CLR); c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(0, 12, "PROPOSED BAR ASSOCIATION HALL")
    c.setFont("Helvetica-Bold", 8); c.setFillColor(WALL_CLR)
    c.drawCentredString(0, 0, "G + 1  |  90'-0\" × 55'-6\"")
    c.setFont("Helvetica", 7); c.setFillColor(colors.HexColor("#0369a1"))
    c.drawCentredString(0, -12, "PLINTH AREA ≈ 4,995 SQ.FT./FLOOR")
    c.setFont("Helvetica-Bold", 7); c.setFillColor(colors.HexColor("#dc2626"))
    c.drawCentredString(0, -24, "PROPOSED — FOR APPROVAL")
    c.restoreState()

    # ── 13. LEGEND PATCH (top-right corner of page) ───────────────────────
    LG_X = PAGE_W - 230; LG_Y = PAGE_H - 280
    LG_W = 210; LG_H = 170
    c.setFillColor(colors.Color(1,1,1,0.92))
    c.setStrokeColor(colors.HexColor("#334155")); c.setLineWidth(0.8)
    c.roundRect(LG_X, LG_Y, LG_W, LG_H, 4, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.rect(LG_X, LG_Y+LG_H-22, LG_W, 22, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 9)
    c.drawString(LG_X+8, LG_Y+LG_H-15, "PROPOSED OVERLAY LEGEND")
    items = [
        (FLOOR_CLR,   WALL_CLR,    "PROPOSED BUILDING (G+1)"),
        (PORCH_CLR,   colors.HexColor("#b45309"), "ENTRANCE PORCH (12'×8')"),
        (SETBACK_CLR, SETBACK_CLR, "SETBACK ZONE (DASHED)"),
        (TREE_CLR,    colors.HexColor("#065f46"),  "PROPOSED TREES"),
        (COL_CLR,     WALL_CLR,    "RCC COLUMNS"),
    ]
    ly = LG_Y + LG_H - 40
    for fc, sc, lbl in items:
        c.setFillColor(fc); c.setStrokeColor(sc); c.setLineWidth(0.5)
        c.rect(LG_X+10, ly, 16, 11, stroke=1, fill=1)
        c.setFillColor(colors.HexColor("#1e293b")); c.setFont("Helvetica", 7.5)
        c.drawString(LG_X+32, ly+2, lbl)
        ly -= 18

    # Revision note
    c.setFillColor(colors.HexColor("#1e293b")); c.setFont("Helvetica-Bold", 7)
    c.drawString(LG_X+8, LG_Y+8,
                 f"REV P01 — {datetime.now(timezone.utc).strftime('%d-%b-%Y').upper()}")
    c.drawString(LG_X+8, LG_Y+19,
                 "LONGER WALL : EAST - WEST DIRECTION")

    c.restoreState()
    c.save()
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# MERGE: stamp overlay onto original PDF
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print(f"Reading base PDF: {INPUT_PDF.name}")
    base_reader  = PdfReader(str(INPUT_PDF))
    base_page    = base_reader.pages[0]

    print(f"  Page size: {float(base_page.mediabox.width):.0f} × "
          f"{float(base_page.mediabox.height):.0f} pt")
    print(f"  Scale: {SCALE_PT_FT:.3f} pt/ft")
    print(f"  Draw angle: {math.degrees(DRAW_ANGLE):.1f} deg")

    print("Building overlay...")
    overlay_bytes  = build_overlay()
    overlay_reader = PdfReader(io.BytesIO(overlay_bytes))
    overlay_page   = overlay_reader.pages[0]

    print("Merging...")
    writer = PdfWriter()
    writer.add_page(base_page)
    writer.pages[0].merge_page(overlay_page)

    OUT_PDF.parent.mkdir(exist_ok=True)
    with open(OUT_PDF, "wb") as f:
        writer.write(f)

    print(f"[OK] Output: {OUT_PDF.name}")
    print(f"     Location: {OUT_PDF}")
    print(f"     Building SW campus coords: ({HALL_X}', {HALL_Y}')")
    print(f"     Building size: {HALL_W}' (E-W) x {HALL_H}' (N-S)")
    print(f"     Main entry: East long wall with porch")


if __name__ == "__main__":
    main()
