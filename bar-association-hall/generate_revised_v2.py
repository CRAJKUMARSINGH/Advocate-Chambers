"""
BAR ASSOCIATION BANSWARA  -  REVISED ARCHITECTURAL CAD  v2.0
=============================================================
Rev-B  18 Sep 2026  |  Author: Trae AI Architecture Studio

SHEETS (A4 PORTRAIT):
  Sheet 01  -  Ground Floor Plan
  Sheet 02  -  First Floor Plan

COORDINATE SYSTEM  (after 90-deg CW rotation for A4 portrait):
  Original N-S depth  (y=5..93, 88 ft)  ->  Drawing X axis (LEFT=south, RIGHT=north)
  Original E-W width  (x=0..55, 55 ft)  ->  Drawing Y axis (BOTTOM=east, TOP=west)

  DX(orig_y)  =  PLAN_OX + (orig_y - 5) * FT
  DY(orig_x)  =  PLAN_OY + (55 - orig_x) * FT

DOG-LEG STAIR - NBC 2016 / RPwD  (CORRECT ENGINEERING):
  Floor-to-floor  =  14'-0"  (roof slab 10" + screed+finish 2" = 12"; structural clear 14')
  Riser           =  7"   |  Risers total = (14*12)/7 = 24  |  12 per flight
  Tread           =  12"  (1 ft as specified)
  Each flight run =  12 x 12" = 12'-0"
  Clear width     =  9'-0"  (two half-flights 4'-6" each, side by side)
  Mid-landing     =  9' wide x 4'-6" deep  (NBC 4.7.1 min = stair width)
  Bottom + Top landing = 4'-6" deep each
  Compartment TOTAL:  9' wide  x  (4.5 + 12 + 4.5 + 12 + 4.5 = 37.5') long
  Stair runs E-W in original plan (orig_x 0..9, orig_y 25.5..63):
    After rotation -> DX span (orig_y 25.5..63 = 37.5 ft) x DY span (orig_x 0..9 = 9 ft)

GROUND FLOOR ROOMS:
  GF-01  President Chamber  15'x12' min (actual 25'x12') + attached toilet 7'x6'
  GF-02  Secretary Chamber  15'x12' + attached toilet 7'x6'
  GF-03  Bar Office Room    15'x12'
  GF-04  Common Lawyer Toilet  10'x8.5'  (Male + Female)
  GF-05  Dog-leg Stair core  9'x37.5'
  GF-06  Assembly Hall  ~53'x53'  -  AUDIENCE CHAIRS ONLY, NO TABLES
  GF-07  Dais / Speaker Zone  55'x14.5'
  Circulation corridor 8.5' wide (orig_y 17..25.5)

FIRST FLOOR ROOMS:
  FF-01  Library Reading Room  55'x39'  (tables, CHAIRS ON BOTH SIDES)
  FF-02  Book Stack Area  55'x18'
  FF-03  EDP / Print Centre  11'x8.5'  (3 PCs + printer)
  FF-04  FF Bar Secretary Office  15'x12'
  FF-05  Discussion Room  19'x12'
  FF-06  Dog-leg Stair (stacked)  9'x37.5'
  FF toilets stacked over GF toilets

FONT SIZES: ALL 3x the NBC minimum (300% increase as directed)
"""

import sys, math
from pathlib import Path

sys.path.insert(0, r"e:\Rajkumar\Advocate-Chambers\scripts")
from traecad_engine import (
    FT, IN, MM, PAPER_SIZES,
    ProjectConfig, setup_doc,
    line, rect, polyline, circle, fill_rect,
    text_msp, arch_dim_h, arch_dim_v,
    draw_north_arrow, draw_sheet_frame_and_titleblock,
    export_dxf_to_pdf,
)
from ezdxf.enums import TextEntityAlignment

# =============================================================================
# FONT CONSTANTS  -  3x NBC minimum (300% increase as directed)
# =============================================================================
TX_MICRO  = (3.0/32.0) * 3   # 0.281"
TX_SMALL  = (1.0/8.0)  * 3   # 0.375"
TX_MEDIUM = (3.0/16.0) * 3   # 0.563"
TX_LARGE  = (1.0/4.0)  * 3   # 0.750"
TX_XL     = (5.0/16.0) * 3   # 0.938"
TX_XXL    = (3.0/8.0)  * 3   # 1.125"
TX_TITLE  = (1.0/2.0)  * 3   # 1.500"

# =============================================================================
# PROJECT CONFIG
# =============================================================================
BASE    = Path(r"e:\Rajkumar\Advocate-Chambers\bar-association-hall")
OUT_DXF = BASE / "CAD"
OUT_PDF = BASE / "PDF"
OUT_DXF.mkdir(parents=True, exist_ok=True)
OUT_PDF.mkdir(parents=True, exist_ok=True)

config = ProjectConfig(
    project_title="BAR ASSOCIATION HALL, BANSWARA DISTRICT COURT",
    client="BAR ASSOCIATION, BANSWARA, RAJASTHAN",
    date="18 SEP 2026",
    drawn_by="TRAE AI ARCHITECTURE STUDIO  Rev-B",
    code_ref="NBC 2016 + RPwD ACT 2016 + IS 4912",
    doc_ref="BA-Banswara-RevB-v2.0",
    base_dir=str(BASE),
    dxf_subdir="CAD",
    pdf_subdir="PDF",
    paper_size="A4",
    margin_mm=10.0,
)

# =============================================================================
# CANVAS SIZE FOR A4 PORTRAIT
# A4 portrait printable  =  190mm wide  x  277mm tall  (10mm margins)
# We use 1/8"=1'-0" scale.  In drawing units (1 DU = 1 inch):
#   Plan width after rotation  =  88 ft  (original N-S depth)
#   Plan height after rotation =  55 ft  (original E-W width)
# With margins + title block + area schedule, choose:
#   SW (canvas width, horizontal = N-S axis)  =  115 ft
#   SH (canvas height, vertical  = E-W axis)  =  75 ft
# Aspect ratio SW/SH = 115/75 = 1.53  vs A4 portrait 277/190 = 1.46  ~ OK
# =============================================================================
SW = 115.0 * FT
SH =  75.0 * FT

# =============================================================================
# COORDINATE TRANSFORM  (90-deg CW rotation)
#   DX(orig_y_ft)  ->  drawing X  (south=left, north=right)
#   DY(orig_x_ft)  ->  drawing Y  (east=bottom, west=top)
# =============================================================================
PLAN_OX = 10.0 * FT   # left margin for plan
PLAN_OY =  9.0 * FT   # bottom margin for plan

def DX(orig_y_ft):
    """Original N-S coordinate (y) -> Drawing X."""
    return PLAN_OX + (orig_y_ft - 5.0) * FT

def DY(orig_x_ft):
    """Original E-W coordinate (x) -> Drawing Y."""
    return PLAN_OY + (55.0 - orig_x_ft) * FT

# Wall thicknesses
OWT = 9 * IN    # outer / load-bearing wall
IWT = 6 * IN    # inner partition

# =============================================================================
# STAIR CONSTANTS
# =============================================================================
STAIR_W_FT   = 9.0     # clear stair width (orig_x span)
STAIR_LEN_FT = 37.5    # compartment length (orig_y span)
HALF_W_FT    = 4.5     # each flight width
N_RISERS     = 12      # risers per flight (24 total @ 7" = 14'-0")
TREAD_FT     = 1.0     # 12" tread (1 ft)
RISER_IN     = 7.0     # riser height in inches
FLIGHT_RUN   = N_RISERS * TREAD_FT   # = 12.0 ft per flight
BTM_LAND     = 4.5     # bottom landing depth ft
MID_LAND     = 4.5     # mid-landing depth ft
TOP_LAND     = 4.5     # top landing depth ft
# Verification: 4.5 + 12 + 4.5 + 12 + 4.5 = 37.5 ft CORRECT

# Stair position in original coordinates
STAIR_OX = 0.0     # orig_x start (west wall)
STAIR_OY = 25.5    # orig_y start (just north of E-W corridor)
STAIR_EX = STAIR_OX + STAIR_W_FT    # = 9.0
STAIR_EY = STAIR_OY + STAIR_LEN_FT  # = 63.0

# =============================================================================
# HELPERS
# =============================================================================

def dline(msp, x1, y1, x2, y2, layer="A-WALL", lw=25):
    line(msp, x1, y1, x2, y2, layer=layer, lw=lw)

def drect(msp, x1, y1, x2, y2, layer="A-WALL", lw=25):
    rect(msp, x1, y1, x2, y2, layer=layer, lw=lw)

def lbl(msp, txt, cx, cy, h=None, layer="A-TEXT-TTL", rot=0.0):
    h = h or TX_MEDIUM * FT
    text_msp(msp, txt, cx, cy, h=h, layer=layer, rot=rot,
             align=TextEntityAlignment.MIDDLE_CENTER)

def wall_band_hatch(msp, pts):
    """Hatch a closed polygon (list of (x,y)) with ANSI31 wall pattern."""
    try:
        h = msp.add_hatch(color=8, dxfattribs={"layer": "A-HATCH"})
        h.set_pattern_fill("ANSI31", scale=0.8)
        h.paths.add_polyline_path(pts, is_closed=True)
    except Exception:
        pass

def floor_hatch(msp, x1, y1, x2, y2, pattern="ANSI32"):
    try:
        h = msp.add_hatch(color=6, dxfattribs={"layer": "A-HATCH"})
        h.set_pattern_fill(pattern, scale=0.6)
        h.paths.add_polyline_path(
            [(min(x1,x2), min(y1,y2)), (max(x1,x2), min(y1,y2)),
             (max(x1,x2), max(y1,y2)), (min(x1,x2), max(y1,y2))],
            is_closed=True)
    except Exception:
        pass

def door_plan(msp, hx, hy, width, rot_deg=0.0, swing_ccw=True, layer="A-DOOR"):
    """
    Draw a door in plan: one leaf + quarter-circle arc.
    hx,hy   = hinge point (one end of door opening in wall).
    width   = door leaf width in drawing units.
    rot_deg = rotation of the door hinge axis (0=leaf extends in +X from hinge).
    swing_ccw = True  ->  arc from 0 to +90 (CCW / anti-clockwise)
                False ->  arc from -90 to 0  (CW / clockwise)
    """
    rad = math.radians(rot_deg)
    # Leaf end point
    lx = hx + width * math.cos(rad)
    ly = hy + width * math.sin(rad)
    msp.add_line((hx, hy), (lx, ly),
                 dxfattribs={"layer": layer, "lineweight": 25})
    if swing_ccw:
        sa = rot_deg
        ea = rot_deg + 90.0
    else:
        sa = rot_deg - 90.0
        ea = rot_deg
    try:
        msp.add_arc(center=(hx, hy), radius=width,
                    start_angle=sa, end_angle=ea,
                    dxfattribs={"layer": layer, "lineweight": 15})
    except Exception:
        pass

def window_sym(msp, wall_x_or_y, start, end, direction="vertical", layer="A-WINDOW"):
    """
    Plan-view window symbol (3-line: 2 frame lines + glass mid-line) cut into wall.
    direction='vertical'  -> window opening runs vertically in DY;  wall runs in DX
    direction='horizontal'-> window opening runs horizontally in DX; wall runs in DY
    wall_x_or_y = the wall centre coordinate (DX or DY value depending on direction)
    start, end  = the two ends of the opening along the perpendicular axis
    """
    t = 3 * IN   # wall-half-thickness for symbol
    if direction == "vertical":
        # Wall parallel to DX axis; opening in DY from start to end
        wx = wall_x_or_y
        dline(msp, wx - t, start, wx - t, end, layer=layer, lw=20)  # outer frame
        dline(msp, wx + t, start, wx + t, end, layer=layer, lw=20)  # inner frame
        dline(msp, wx,     start, wx,     end, layer=layer, lw=12)  # glass centre
        dline(msp, wx - t, start, wx + t, start, layer=layer, lw=20)  # end cap
        dline(msp, wx - t, end,   wx + t, end,   layer=layer, lw=20)  # end cap
    else:
        # Wall parallel to DY axis; opening in DX from start to end
        wy = wall_x_or_y
        dline(msp, start, wy - t, end, wy - t, layer=layer, lw=20)
        dline(msp, start, wy + t, end, wy + t, layer=layer, lw=20)
        dline(msp, start, wy,     end, wy,     layer=layer, lw=12)
        dline(msp, start, wy - t, start, wy + t, layer=layer, lw=20)
        dline(msp, end,   wy - t, end,   wy + t, layer=layer, lw=20)

def wc_pan(msp, cx, cy, facing_deg=0.0):
    """WC pan + cistern symbol in plan (facing_deg=0 -> open end faces +X)."""
    r = math.radians(facing_deg)
    # pan oval (rectangle standing in)
    drect(msp,
          cx - 0.6*FT*math.cos(r+math.pi/2) - 0.7*FT*math.cos(r),
          cy - 0.6*FT*math.sin(r+math.pi/2) - 0.7*FT*math.sin(r),
          cx + 0.6*FT*math.cos(r+math.pi/2) + 0.7*FT*math.cos(r),
          cy + 0.6*FT*math.sin(r+math.pi/2) + 0.7*FT*math.sin(r),
          layer="A-FURN", lw=10)
    circle(msp, cx, cy, 0.3*FT, layer="A-FURN", lw=8)
    # cistern at back
    bx = cx - 0.7*FT*math.cos(r)
    by = cy - 0.7*FT*math.sin(r)
    drect(msp, bx - 0.6*FT*math.cos(r+math.pi/2) - 0.2*FT*math.cos(r),
               by - 0.6*FT*math.sin(r+math.pi/2) - 0.2*FT*math.sin(r),
               bx + 0.6*FT*math.cos(r+math.pi/2),
               by + 0.6*FT*math.sin(r+math.pi/2),
          layer="A-FURN", lw=10)

def washbasin(msp, cx, cy):
    circle(msp, cx, cy, 0.5*FT, layer="A-FURN", lw=10)
    circle(msp, cx, cy, 0.12*FT, layer="A-FURN", lw=8)

def chair_sym(msp, cx, cy, r=0.45*FT):
    circle(msp, cx, cy, r, layer="A-FURN", lw=8)

def chair_row(msp, row_dx, y_start, y_end, step_ft=2.0):
    """Place audience chairs in a row along DY from y_start to y_end, at DX = row_dx."""
    y = y_start
    while y <= y_end - 0.3*FT:
        chair_sym(msp, row_dx, y)
        y += step_ft * FT

# =============================================================================
# BUILDING ENVELOPE  (L-shaped, rotated 90 CW)
# =============================================================================
def draw_envelope(msp):
    """Double-line L-shaped outer wall with ANSI31 hatch."""
    # Original vertices in (x,y): (0,5),(30,5),(30,21.5),(55,21.5),(55,93),(0,93)
    # After DX/DY transform:
    outer = [
        (DX(5),    DY(0)),
        (DX(5),    DY(30)),
        (DX(21.5), DY(30)),
        (DX(21.5), DY(55)),
        (DX(93),   DY(55)),
        (DX(93),   DY(0)),
    ]
    o = OWT / FT   # wall thickness in ft for inner offset
    inner = [
        (DX(5  + o),  DY(0   + o)),
        (DX(5  + o),  DY(30  - o)),
        (DX(21.5+o),  DY(30  - o)),
        (DX(21.5+o),  DY(55  - o)),
        (DX(93 - o),  DY(55  - o)),
        (DX(93 - o),  DY(0   + o)),
    ]
    polyline(msp, outer + [outer[0]], layer="A-WALL", lw=50)
    polyline(msp, inner + [inner[0]], layer="A-WALL", lw=30)
    # Hatch wall bands
    for i in range(len(outer)):
        p1, p2 = outer[i], outer[(i+1)%len(outer)]
        ip1, ip2 = inner[i], inner[(i+1)%len(inner)]
        wall_band_hatch(msp, [p1, p2, ip2, ip1])


def draw_columns(msp):
    """12"x12" RCC columns at grid intersections."""
    col_x = [0, 15, 30, 45, 55]
    col_y = [5, 21.5, 30, 50, 63, 70, 78.5, 93]
    s = 6 * IN   # half column size
    for cx in col_x:
        for cy in col_y:
            if cx > 30 and cy < 21.5:
                continue
            bx, by = DX(cy), DY(cx)
            fill_rect(msp, bx-s, by-s, bx+s, by+s, hatch="SOLID", layer="A-COLUMN")
            drect(msp, bx-s, by-s, bx+s, by+s, layer="A-COLUMN", lw=30)


def draw_direction_labels(msp):
    """Compass labels for rotated drawing."""
    mid_y = (DY(0) + DY(55)) / 2
    mid_x = (DX(5) + DX(93)) / 2
    # South = left, North = right, West = top, East = bottom
    lbl(msp, "SOUTH  -  MAIN ENTRY",
        DX(5) - 5*FT, mid_y, h=TX_XL*FT, layer="A-TEXT-TTL", rot=90.0)
    lbl(msp, "NORTH  -  DAIS / SPEAKER",
        DX(93) + 5*FT, mid_y, h=TX_XL*FT, layer="A-TEXT-TTL", rot=90.0)
    lbl(msp, "WEST  -  ZERO SETBACK  (BLANK WALL)",
        mid_x, DY(0) + 4*FT, h=TX_LARGE*FT, layer="A-TEXT-TTL")
    lbl(msp, "EAST  -  5'-0\" SETBACK  /  EMERGENCY EXIT",
        mid_x, DY(55) - 4*FT, h=TX_LARGE*FT, layer="A-TEXT-TTL")

# =============================================================================
# DOG-LEG STAIRCASE  (NBC 2016 / RPwD)
# Stair runs E-W in original plan (orig_x=0..9, orig_y=25.5..63)
# After 90 CW rotation:
#   DX axis = N-S (orig_y) -> stair LENGTH along DX
#   DY axis = E-W (orig_x) -> stair WIDTH along DY
# Two flights side by side (dog-leg U-turn at mid-landing):
#   Flight 1: orig_x=0..4.5  (west half)  ->  DY: DY(4.5)..DY(0) in drawing = UPPER band
#   Flight 2: orig_x=4.5..9  (east half)  ->  DY: DY(9)..DY(4.5) in drawing = LOWER band
# Flight 1 goes from bottom-landing (DX=DX(25.5)) north (DX increasing) = ASCENDING
# At mid-landing U-turn, Flight 2 continues ascending from mid to top-landing
# =============================================================================
def draw_dogleg_stair(msp, floor="GF"):
    """Draw the complete dog-leg staircase."""
    # --- Geometry in DX/DY coordinates ---
    # Bottom landing zone: orig_y=25.5..30.0   (BTM_LAND=4.5 ft)
    # Flight 1:            orig_y=30.0..42.0   (FLIGHT_RUN=12 ft, orig_x=0..4.5)
    # Mid landing:         orig_y=42.0..46.5   (MID_LAND=4.5 ft, full width)
    # Flight 2:            orig_y=46.5..58.5   (FLIGHT_RUN=12 ft, orig_x=4.5..9)
    # Top landing:         orig_y=58.5..63.0   (TOP_LAND=4.5 ft)

    bl_y0, bl_y1 = 25.5,  30.0   # bottom landing in orig_y
    f1_y0, f1_y1 = 30.0,  42.0   # flight 1
    ml_y0, ml_y1 = 42.0,  46.5   # mid landing
    f2_y0, f2_y1 = 46.5,  58.5   # flight 2
    tl_y0, tl_y1 = 58.5,  63.0   # top landing

    hw = HALF_W_FT   # = 4.5 ft  (half-width in orig_x)

    # Convert to drawing coords:
    #  DX(orig_y) -> drawing X
    #  DY(orig_x) -> drawing Y  (larger orig_x = lower Y in drawing)

    BL_X0, BL_X1 = DX(bl_y0), DX(bl_y1)
    F1_X0, F1_X1 = DX(f1_y0), DX(f1_y1)
    ML_X0, ML_X1 = DX(ml_y0), DX(ml_y1)
    F2_X0, F2_X1 = DX(f2_y0), DX(f2_y1)
    TL_X0, TL_X1 = DX(tl_y0), DX(tl_y1)

    # Y spans:  Flight1 west half orig_x=0..4.5   -> DY(4.5)..DY(0)   UPPER band
    #           Flight2 east half orig_x=4.5..9   -> DY(9)..DY(4.5)   LOWER band
    TOP_Y  = DY(0.0)    # west wall side  = top of drawing (large DY)
    MID_Y  = DY(hw)     # centre dividing wall
    BOT_Y  = DY(STAIR_EX)  # DY(9.0) = east side = bottom of stair in drawing

    # ---- Compartment outer boundary ----
    drect(msp, DX(STAIR_OY), BOT_Y, DX(STAIR_EY), TOP_Y, layer="A-WALL", lw=40)

    # ---- Centre dividing wall (between two half-flights) ----
    dline(msp, F1_X0, MID_Y, TL_X1, MID_Y, layer="A-WALL", lw=25)

    # ---- BOTTOM LANDING (full width, both halves) ----
    floor_hatch(msp, BL_X0, BOT_Y, BL_X1, TOP_Y, pattern="ANSI32")
    lbl(msp, "GF APPROACH\nLANDING\n4'-6\"" if floor=="GF" else "FF APPROACH\nLANDING\n4'-6\"",
        (BL_X0+BL_X1)/2, (BOT_Y+TOP_Y)/2, h=TX_SMALL*FT, layer="A-TEXT-TTL")

    # ---- MID LANDING (full width) ----
    floor_hatch(msp, ML_X0, BOT_Y, ML_X1, TOP_Y, pattern="ANSI32")
    lbl(msp, "MID LANDING  4'-6\"",
        (ML_X0+ML_X1)/2, (BOT_Y+TOP_Y)/2, h=TX_SMALL*FT, layer="A-TEXT-TTL")

    # ---- TOP LANDING (full width) ----
    floor_hatch(msp, TL_X0, BOT_Y, TL_X1, TOP_Y, pattern="ANSI32")
    lbl(msp, "FF LANDING  4'-6\"" if floor=="GF" else "FF EXIT LANDING",
        (TL_X0+TL_X1)/2, (BOT_Y+TOP_Y)/2, h=TX_SMALL*FT, layer="A-TEXT-TTL")

    # ---- FLIGHT 1 RISER LINES (upper half: TOP_Y..MID_Y, orig_x=0..4.5) ----
    tread_dx = TREAD_FT * FT   # 12" = 1 FT in drawing units
    for i in range(N_RISERS + 1):
        rx = F1_X0 + i * tread_dx
        dline(msp, rx, MID_Y, rx, TOP_Y, layer="A-WALL", lw=15)
    # Handrails
    dline(msp, F1_X0, TOP_Y - 2*IN,  F1_X1, TOP_Y - 2*IN,  layer="A-ACC", lw=18)
    dline(msp, F1_X0, MID_Y + 2*IN,  F1_X1, MID_Y + 2*IN,  layer="A-ACC", lw=18)
    # UP arrow
    mid_f1x = (F1_X0 + F1_X1) / 2
    mid_f1y = (TOP_Y + MID_Y) / 2
    lbl(msp, "UP", mid_f1x, mid_f1y, h=TX_LARGE*FT, layer="A-SECT-CUT")
    # Arrow line
    dline(msp, F1_X0 + 1.5*FT, mid_f1y, F1_X1 - 1*FT, mid_f1y, layer="A-SECT-CUT", lw=20)
    dline(msp, F1_X1 - 1*FT, mid_f1y, F1_X1 - 2*FT, mid_f1y + 0.5*FT, layer="A-SECT-CUT", lw=20)
    dline(msp, F1_X1 - 1*FT, mid_f1y, F1_X1 - 2*FT, mid_f1y - 0.5*FT, layer="A-SECT-CUT", lw=20)

    # ---- FLIGHT 2 RISER LINES (lower half: MID_Y..BOT_Y, orig_x=4.5..9) ----
    for i in range(N_RISERS + 1):
        rx = F2_X0 + i * tread_dx
        dline(msp, rx, BOT_Y, rx, MID_Y, layer="A-WALL", lw=15)
    # Handrails
    dline(msp, F2_X0, MID_Y - 2*IN,  F2_X1, MID_Y - 2*IN,  layer="A-ACC", lw=18)
    dline(msp, F2_X0, BOT_Y + 2*IN,  F2_X1, BOT_Y + 2*IN,  layer="A-ACC", lw=18)
    # UP arrow (GF) / DOWN arrow (FF)
    mid_f2x = (F2_X0 + F2_X1) / 2
    mid_f2y = (MID_Y + BOT_Y) / 2
    arrow_txt = "UP" if floor == "GF" else "DN"
    lbl(msp, arrow_txt, mid_f2x, mid_f2y, h=TX_LARGE*FT, layer="A-SECT-CUT")
    dline(msp, F2_X0 + 1.5*FT, mid_f2y, F2_X1 - 1*FT, mid_f2y, layer="A-SECT-CUT", lw=20)
    dline(msp, F2_X1 - 1*FT, mid_f2y, F2_X1 - 2*FT, mid_f2y + 0.5*FT, layer="A-SECT-CUT", lw=20)
    dline(msp, F2_X1 - 1*FT, mid_f2y, F2_X1 - 2*FT, mid_f2y - 0.5*FT, layer="A-SECT-CUT", lw=20)

    # ---- Plan cut line (dashed, at mid-flight-1 height) ----
    cut_x = F1_X0 + FLIGHT_RUN * 0.5 * FT
    dline(msp, cut_x, BOT_Y - 1*FT, cut_x, TOP_Y + 1*FT, layer="A-SECT-CUT", lw=35)

    # ---- Entry door GF (from corridor into bottom landing) ----
    # Door on south wall of stair (DX = DX(STAIR_OY) = DX(25.5))
    # Opening in west half (DY band: MID_Y..TOP_Y), 3'-0" door, hinge at west wall
    door_plan(msp, DX(25.5), TOP_Y - 3*FT, 3*FT, rot_deg=0.0, swing_ccw=True, layer="A-DOOR")
    lbl(msp, "3'-0\"\nSTAIR\nENTRY",
        DX(25.5) - 3*FT, TOP_Y - 1.5*FT, h=TX_SMALL*FT, layer="A-DOOR")

    # ---- Exit door at FF level (from top landing north wall DX(63) -> FF lobby) ----
    door_plan(msp, DX(63.0), TOP_Y - 3*FT, 3*FT, rot_deg=0.0, swing_ccw=False, layer="A-DOOR")
    lbl(msp, "3'-0\"\nFF EXIT\n-> LOBBY",
        DX(63.0) + 3*FT, TOP_Y - 1.5*FT, h=TX_SMALL*FT, layer="A-DOOR")

    # ---- Stair label callout ----
    ht_total = int(N_RISERS * 2 * RISER_IN)
    stair_note = (
        f"DOG-LEG STAIR  {'GF-05' if floor=='GF' else 'FF-06'}"
        f"\nNBC 2016 / RPwD  |  CLEAR W = 9'-0\"  (2 x 4'-6\" FLIGHTS)"
        f"\n2 x {N_RISERS} RISERS @ {RISER_IN:.0f}\" / {int(TREAD_FT*12)}\" TREAD"
        f"  |  TOTAL HEIGHT = {ht_total}\" = {ht_total//12}'-{ht_total%12}\""
        f"\nBTM LANDING 4'-6\"  |  MID LANDING 4'-6\"  |  TOP LANDING 4'-6\""
        f"\nHANDRAILS BOTH SIDES  |  HEADROOM > 7'-0\" CLEAR"
    )
    lbl(msp, stair_note,
        (DX(STAIR_OY)+DX(STAIR_EY))/2, BOT_Y - 3.5*FT,
        h=TX_SMALL*FT, layer="A-TEXT")

    # Dimension
    arch_dim_h(msp, DX(STAIR_OY), BOT_Y - 1.5*FT, DX(STAIR_EY),
               "37'-6\" STAIR COMPARTMENT", offset=-1.2*FT)
    arch_dim_v(msp, DX(STAIR_OY) - 1.5*FT, BOT_Y, TOP_Y,
               "9'-0\" CLEAR WIDTH", offset=-1.2*FT)

# =============================================================================
# GROUND FLOOR SERVICE WING + ROOMS
# =============================================================================
def draw_gf_service_wing(msp):
    """
    GF rooms in south service wing and lower zone.
    ORIGINAL COORDINATES used, then DX/DY transform applied.
    Layout:
      GF-01 President Chamber  orig_x=30..55, orig_y=5..17
            Attached Toilet    orig_x=47..55, orig_y=5..12
      GF-02 Secretary Chamber  orig_x=15..30, orig_y=5..17
            Attached Toilet    orig_x=23..30, orig_y=5..12
      GF-03 Bar Office Room    orig_x=0..15,  orig_y=5..17
      GF-04 Common Toilet      orig_x=0..10,  orig_y=17..25.5
      E-W Corridor 8.5'        orig_x=10..55, orig_y=17..25.5
      Entry Verandah            orig_y=3..5 (outside on S setback)
    All dimensions in ORIGINAL FEET; DX/DY applied inline.
    """
    # ---- GF-01 PRESIDENT CHAMBER ----
    # orig_x=30..55  orig_y=5..17  (25' wide x 12' deep)
    PC = dict(x1=30.0, x2=55.0, y1=5.0, y2=17.0)
    # Room walls
    drect(msp, DX(PC['y1']), DY(PC['x2']), DX(PC['y2']), DY(PC['x1']),
          layer="A-WALL", lw=40)
    # Attached toilet partition (orig_x=47..55, orig_y=5..12)
    AT1 = dict(x1=47.0, x2=55.0, y1=5.0, y2=12.0)
    drect(msp, DX(AT1['y1']), DY(AT1['x2']), DX(AT1['y2']), DY(AT1['x1']),
          layer="A-WALL", lw=30)
    fill_rect(msp, DX(AT1['y1']), DY(AT1['x2']),
              DX(AT1['y2']), DY(AT1['x1']), hatch="ANSI32", layer="A-HATCH")
    # WC pan + basin in attached toilet
    wc_pan(msp, DX((AT1['y1']+AT1['y2'])/2), DY((AT1['x1']+AT1['x2'])/2) - 0.5*FT,
           facing_deg=180.0)
    washbasin(msp, DX(AT1['y2']) - 1.5*FT, DY(AT1['x2']) + 1.5*FT)
    lbl(msp, "PRES. TOILET\n7' x 6'",
        (DX(AT1['y1'])+DX(AT1['y2']))/2, DY((AT1['x1']+AT1['x2'])/2) + 2*FT,
        h=TX_SMALL*FT, layer="A-TEXT-TTL")
    # Toilet door on orig_x=47 partition (swing INTO toilet)
    # Hinge at top DY(AT1['x1']), door extends down 3 ft; swing CW
    door_plan(msp, DX(AT1['y2'])-3*FT, DY(AT1['x1']),
              3*FT, rot_deg=0.0, swing_ccw=False, layer="A-DOOR")
    lbl(msp, "3'", DX(AT1['y2'])-4.5*FT, DY(AT1['x1'])-1.5*FT,
        h=TX_SMALL*FT, layer="A-DOOR")

    # Windows on south wall (orig_y=5 -> DX(5)) - two windows
    for wx_orig in [35.0, 47.0]:
        window_sym(msp, DX(5), DY(wx_orig+2.5), DY(wx_orig-2.5), direction="vertical",
                   layer="A-WINDOW")
        lbl(msp, "W 5'0\"\nSILL 3'",
            DX(5) - 3*FT, DY(wx_orig), h=TX_SMALL*FT, layer="A-WINDOW", rot=90.0)

    # President chamber entry door from corridor (orig_y=17 wall)
    # Door 4'-0" wide, hinge at DY(45), swing INTO chamber (CCW in drawing)
    door_plan(msp, DX(17.0), DY(43.0), 4*FT, rot_deg=90.0, swing_ccw=True, layer="A-DOOR")
    lbl(msp, "4'-0\"\nPRES. ENTRY",
        DX(17.0) + 2.5*FT, DY(44.5), h=TX_SMALL*FT, layer="A-DOOR")

    # Furniture: President desk + chair + visitor chairs + sofa
    # Desk along north wall (orig_y=17 side), 8'x3'
    drect(msp, DX(17.0) - 3.5*FT, DY(38.0),
               DX(17.0) - 0.5*FT, DY(49.0),
               layer="A-FURN", lw=15)
    lbl(msp, "PRES.\nDESK\n11'x3'",
        DX(17.0)-2*FT, DY(43.5), h=TX_SMALL*FT, layer="A-FURN")
    # President chair
    chair_sym(msp, DX(17.0)-4.5*FT, DY(43.5))
    # 2 visitor chairs (facing desk)
    for vy in [36.0, 43.5, 51.0]:
        if vy <= 53.0:
            chair_sym(msp, DX(10.0), DY(vy))
    # Sofa against west wall (orig_y=5 side)
    drect(msp, DX(5)+0.5*FT, DY(54.0), DX(5)+2.5*FT, DY(32.0),
          layer="A-FURN", lw=13)
    lbl(msp, "SOFA", DX(5)+1.5*FT, DY(43.0), h=TX_SMALL*FT, layer="A-FURN", rot=90.0)

    lbl(msp,
        "GF-01  PRESIDENT CHAMBER\n25'-0\" x 12'-0\"  =  300 sq ft\n(ATTACHED TOILET 7' x 6')",
        (DX(5)+DX(17.0))/2, (DY(30.0)+DY(55.0))/2,
        h=TX_LARGE*FT, layer="A-TEXT-TTL")

    # ---- GF-02 SECRETARY CHAMBER ----
    # orig_x=15..30  orig_y=5..17
    SC = dict(x1=15.0, x2=30.0, y1=5.0, y2=17.0)
    drect(msp, DX(SC['y1']), DY(SC['x2']), DX(SC['y2']), DY(SC['x1']),
          layer="A-WALL", lw=40)
    # Attached toilet  orig_x=23..30, orig_y=5..12
    AT2 = dict(x1=23.0, x2=30.0, y1=5.0, y2=12.0)
    drect(msp, DX(AT2['y1']), DY(AT2['x2']), DX(AT2['y2']), DY(AT2['x1']),
          layer="A-WALL", lw=30)
    fill_rect(msp, DX(AT2['y1']), DY(AT2['x2']),
              DX(AT2['y2']), DY(AT2['x1']), hatch="ANSI32", layer="A-HATCH")
    wc_pan(msp, DX((AT2['y1']+AT2['y2'])/2), DY((AT2['x1']+AT2['x2'])/2) - 0.5*FT,
           facing_deg=180.0)
    washbasin(msp, DX(AT2['y2'])-1.5*FT, DY(AT2['x2'])+1.5*FT)
    lbl(msp, "SECY.\nTOILET",
        (DX(AT2['y1'])+DX(AT2['y2']))/2, DY((AT2['x1']+AT2['x2'])/2)+2*FT,
        h=TX_SMALL*FT, layer="A-TEXT-TTL")
    door_plan(msp, DX(AT2['y2'])-3*FT, DY(AT2['x1']),
              3*FT, rot_deg=0.0, swing_ccw=False, layer="A-DOOR")
    lbl(msp, "3'", DX(AT2['y2'])-4.5*FT, DY(AT2['x1'])-1.5*FT,
        h=TX_SMALL*FT, layer="A-DOOR")

    # Window on south wall
    window_sym(msp, DX(5), DY(21.0), DY(16.0), direction="vertical", layer="A-WINDOW")
    lbl(msp, "W 5'\nSILL 3'", DX(5)-3*FT, DY(18.5),
        h=TX_SMALL*FT, layer="A-WINDOW", rot=90.0)

    # Secretary entry door from corridor
    door_plan(msp, DX(17.0), DY(27.0), 3*FT, rot_deg=90.0, swing_ccw=False, layer="A-DOOR")
    lbl(msp, "3'-0\"\nSECY.", DX(17.0)+2*FT, DY(26.0),
        h=TX_SMALL*FT, layer="A-DOOR")

    # Furniture
    drect(msp, DX(17.0)-3.5*FT, DY(19.0), DX(17.0)-0.5*FT, DY(27.0),
          layer="A-FURN", lw=15)
    lbl(msp, "SECY.\nDESK", DX(17.0)-2*FT, DY(23.0),
        h=TX_SMALL*FT, layer="A-FURN")
    chair_sym(msp, DX(17.0)-4.5*FT, DY(23.0))
    for vy in [17.0, 22.5, 28.0]:
        chair_sym(msp, DX(8.0), DY(vy))

    lbl(msp,
        "GF-02  SECRETARY CHAMBER\n15'-0\" x 12'-0\"  =  180 sq ft",
        (DX(5)+DX(17.0))/2, (DY(15.0)+DY(30.0))/2,
        h=TX_LARGE*FT, layer="A-TEXT-TTL")

    # ---- GF-03 BAR OFFICE ROOM ----
    # orig_x=0..15  orig_y=5..17
    BO = dict(x1=0.0, x2=15.0, y1=5.0, y2=17.0)
    drect(msp, DX(BO['y1']), DY(BO['x2']), DX(BO['y2']), DY(BO['x1']),
          layer="A-WALL", lw=40)

    # Window on south wall (orig_y=5)
    window_sym(msp, DX(5), DY(8.0), DY(3.0), direction="vertical", layer="A-WINDOW")
    lbl(msp, "W 5'\nSILL 3'", DX(5)-3*FT, DY(5.5),
        h=TX_SMALL*FT, layer="A-WINDOW", rot=90.0)

    # Bar office door from corridor
    door_plan(msp, DX(17.0), DY(9.0), 3*FT, rot_deg=90.0, swing_ccw=False, layer="A-DOOR")
    lbl(msp, "3'-0\"\nBAR OFC", DX(17.0)+2*FT, DY(8.5),
        h=TX_SMALL*FT, layer="A-DOOR")

    # Furniture: 2 desks + almari
    drect(msp, DX(17.0)-3.5*FT, DY(4.5), DX(17.0)-0.5*FT, DY(9.5),
          layer="A-FURN", lw=13)
    lbl(msp, "DESK-1", DX(17.0)-2*FT, DY(7.0), h=TX_SMALL*FT, layer="A-FURN")
    chair_sym(msp, DX(17.0)-4.5*FT, DY(7.0))
    drect(msp, DX(17.0)-3.5*FT, DY(11.0), DX(17.0)-0.5*FT, DY(14.5),
          layer="A-FURN", lw=13)
    lbl(msp, "DESK-2", DX(17.0)-2*FT, DY(12.7), h=TX_SMALL*FT, layer="A-FURN")
    chair_sym(msp, DX(17.0)-4.5*FT, DY(12.7))
    drect(msp, DX(5)+0.5*FT, DY(14.5), DX(5)+2*FT, DY(0.5),
          layer="A-FURN", lw=13)
    lbl(msp, "ALMIRA", DX(5)+1.2*FT, DY(7.5), h=TX_SMALL*FT, layer="A-FURN", rot=90.0)

    lbl(msp,
        "GF-03  BAR OFFICE ROOM\n15'-0\" x 12'-0\"  =  180 sq ft",
        (DX(5)+DX(17.0))/2, (DY(0.0)+DY(15.0))/2,
        h=TX_LARGE*FT, layer="A-TEXT-TTL")

    # ---- GF-04 COMMON LAWYER TOILET ----
    # orig_x=0..10, orig_y=17..25.5
    CT = dict(x1=0.0, x2=10.0, y1=17.0, y2=25.5)
    drect(msp, DX(CT['y1']), DY(CT['x2']), DX(CT['y2']), DY(CT['x1']),
          layer="A-WALL", lw=35)
    # Partition Male/Female at orig_x=5
    dline(msp, DX(CT['y1']), DY(5.0), DX(CT['y2']), DY(5.0), layer="A-WALL", lw=25)
    # MALE (orig_x=0..5)
    wc_pan(msp, DX(19.5), DY(2.5), facing_deg=90.0)
    # Urinal
    drect(msp, DX(24.0), DY(2.5)+0.5*FT, DX(25.3), DY(2.5)-0.5*FT, layer="A-FURN", lw=10)
    lbl(msp, "URN", DX(24.6), DY(2.5), h=TX_MICRO*FT, layer="A-FURN")
    lbl(msp, "MALE", (DX(CT['y1'])+DX(CT['y2']))/2, DY(2.5)+1.5*FT,
        h=TX_MEDIUM*FT, layer="A-TEXT-TTL")
    # FEMALE (orig_x=5..10)
    wc_pan(msp, DX(19.5), DY(7.5), facing_deg=90.0)
    lbl(msp, "FEMALE", (DX(CT['y1'])+DX(CT['y2']))/2, DY(7.5)+1.5*FT,
        h=TX_MEDIUM*FT, layer="A-TEXT-TTL")
    # 2 wash basins near entry (orig_y=25.5 end = left in drawing)
    washbasin(msp, DX(25.0), DY(2.5))
    washbasin(msp, DX(25.0), DY(7.5))
    # Entry door from corridor (orig_y=25.5 wall)
    door_plan(msp, DX(25.5), DY(5.0), 3*FT, rot_deg=0.0, swing_ccw=False, layer="A-DOOR")
    lbl(msp, "3'-0\"\nTOILET", DX(25.5)+2*FT, DY(5.5),
        h=TX_SMALL*FT, layer="A-DOOR")
    lbl(msp,
        "GF-04  COMMON LAWYER TOILET\n10'-0\" x 8'-6\"\nMale  |  Female",
        (DX(17.0)+DX(25.5))/2, (DY(0.0)+DY(10.0))/2,
        h=TX_LARGE*FT, layer="A-TEXT-TTL")

    # ---- E-W DISTRIBUTION CORRIDOR ----
    # orig_x=10..55, orig_y=17..25.5
    floor_hatch(msp, DX(17.0), DY(55.0), DX(25.5), DY(10.0), pattern="GRATE")
    lbl(msp, "E-W DISTRIBUTION CORRIDOR  8'-6\" CLEAR",
        (DX(17.0)+DX(25.5))/2, (DY(10.0)+DY(55.0))/2,
        h=TX_LARGE*FT, layer="A-TEXT-TTL", rot=90.0)

    # Corridor partition at orig_y=17 (south face of corridor / north face of rooms)
    # Already formed by room north walls.

    # ---- ENTRY VERANDAH (orig_y=3..5, full width) ----
    drect(msp, DX(3), DY(55.0), DX(5), DY(0.0), layer="A-WALL", lw=20)
    lbl(msp, "COVERED ENTRY VERANDAH  (SOUTH SETBACK)",
        DX(4.0), (DY(0.0)+DY(55.0))/2,
        h=TX_LARGE*FT, layer="A-TEXT-TTL", rot=90.0)

    # MAIN ENTRY DOUBLE DOORS (2 x 4'-0") centred on south facade at orig_y=5
    # Hinge at DY(31) and DY(27), each swings outward (CCW in drawing = into verandah)
    door_plan(msp, DX(5), DY(31.0), 4*FT, rot_deg=90.0, swing_ccw=True, layer="A-DOOR")
    door_plan(msp, DX(5), DY(23.0), 4*FT, rot_deg=-90.0, swing_ccw=False, layer="A-DOOR")
    lbl(msp, "MAIN ENTRY\n2 x 4'-0\" DBL LEAF\n(RPwD CLEAR)",
        DX(5) - 4*FT, DY(27.0), h=TX_MEDIUM*FT, layer="A-DOOR", rot=90.0)


# =============================================================================
# GROUND FLOOR  -  MAIN ASSEMBLY HALL + DAIS
# Audience chairs ONLY - NO TABLES
# =============================================================================
def draw_gf_hall(msp):
    """
    Assembly Hall: orig_x=0..55, orig_y=25.5..78.5
    Dais:          orig_x=0..55, orig_y=78.5..93
    Stair occupies orig_x=0..9, orig_y=25.5..63 - seating wraps around it.
    """
    # Hall interior (south wall at orig_y=25.5, north wall at orig_y=78.5)
    # Seating zone A: east of stair, orig_x=10..55, orig_y=25.5..63
    # Seating zone B: north of stair, full width, orig_y=63..78.5

    # ---- Audience chairs in Zone A (east of stair) ----
    # Rows in DX (advancing north = increasing DX)
    # Seats in DY (spanning east to west = DY from DY(55) down to DY(10))
    row_pitch_ft = 2.5   # row pitch in ft (N-S direction = DX axis)
    for row_orig_y in [27.5, 30.0, 32.5, 35.0, 37.5, 40.0, 42.5, 45.0,
                       47.5, 50.0, 52.5, 55.0, 57.5, 60.0, 62.0]:
        row_dx = DX(row_orig_y)
        # Seating from orig_x=10.5..54 (east of stair + east side)
        chair_row(msp, row_dx, DY(54.0), DY(10.5), step_ft=2.2)

    # Central aisle lines (orig_x=26..29 = 3' aisle centred at x=27.5)
    dline(msp, DX(25.5), DY(29.5), DX(78.5), DY(29.5), layer="A-BAY", lw=15)
    dline(msp, DX(25.5), DY(25.5), DX(78.5), DY(25.5), layer="A-BAY", lw=15)
    lbl(msp, "4'-0\" CENTRAL AISLE  (NBC 2016 MIN 1200mm)",
        DX(50.0), DY(27.5), h=TX_LARGE*FT, layer="A-BAY", rot=90.0)

    # ---- Audience chairs in Zone B (north of stair, orig_y=63..78) ----
    for row_orig_y in [64.0, 66.5, 69.0, 71.5, 74.0, 76.5]:
        row_dx = DX(row_orig_y)
        chair_row(msp, row_dx, DY(54.0), DY(0.5), step_ft=2.2)

    # ---- Hall entry doors (from E-W corridor at orig_y=25.5) ----
    # Two double-leaf pairs:
    # Pair 1: orig_x=14..22  (hinge at DY(22), swing INTO hall = CW in drawing)
    door_plan(msp, DX(25.5), DY(22.0), 4*FT, rot_deg=0.0, swing_ccw=False, layer="A-DOOR")
    door_plan(msp, DX(25.5), DY(14.0), 4*FT, rot_deg=0.0, swing_ccw=True,  layer="A-DOOR")
    lbl(msp, "HALL ENTRY 1\n2 x 4'-0\"",
        DX(25.5)+3*FT, DY(18.0), h=TX_MEDIUM*FT, layer="A-DOOR")

    # Pair 2: orig_x=36..44
    door_plan(msp, DX(25.5), DY(44.0), 4*FT, rot_deg=0.0, swing_ccw=False, layer="A-DOOR")
    door_plan(msp, DX(25.5), DY(36.0), 4*FT, rot_deg=0.0, swing_ccw=True,  layer="A-DOOR")
    lbl(msp, "HALL ENTRY 2\n2 x 4'-0\"",
        DX(25.5)+3*FT, DY(40.0), h=TX_MEDIUM*FT, layer="A-DOOR")

    # ---- Emergency exit door on east wall (orig_y=78.5, DX(78.5)) ----
    # Swing OUT (east = downward in drawing = DY decreasing)
    door_plan(msp, DX(78.5), DY(46.0), 4*FT, rot_deg=0.0, swing_ccw=True, layer="A-DOOR")
    lbl(msp, "EMGCY EXIT\n4'-0\" SWING OUT\n(NBC 4.8)",
        DX(78.5)+3.5*FT, DY(46.0)+2*FT, h=TX_MEDIUM*FT, layer="A-DOOR")

    # ---- Windows: EAST wall (orig_y=78.5) ----
    for wx_orig in [10.0, 22.0, 36.0, 48.0]:
        window_sym(msp, DX(78.5), DY(wx_orig+3), DY(wx_orig-3),
                   direction="vertical", layer="A-WINDOW")
        lbl(msp, "W 6'\nS 2'6\"", DX(78.5)+2.5*FT, DY(wx_orig),
            h=TX_SMALL*FT, layer="A-WINDOW")

    # ---- Hall label ----
    lbl(msp,
        "MAIN ASSEMBLY HALL  GF-06\n55' x 53'  ~  2,915 sq ft\n"
        "AUDIENCE CHAIRS ONLY  -  NO TABLES\n(NBC 2016 / RPwD 2016)",
        DX(54.0), DY(44.0),
        h=TX_XXL*FT, layer="A-TEXT-TTL")

    # ---- DAIS / SPEAKER ZONE  orig_y=78.5..93, orig_x=0..55 ----
    D_Y1, D_Y2 = 78.5, 93.0
    floor_hatch(msp, DX(D_Y1), DY(55.0), DX(D_Y2), DY(0.0), pattern="ANSI32")
    drect(msp, DX(D_Y1), DY(55.0), DX(D_Y2), DY(0.0), layer="A-WALL", lw=35)

    # Dais step nosings (3 risers in plan)
    for s in range(3):
        step_dx = DX(D_Y1) + (s+1) * 0.5*FT
        dline(msp, step_dx, DY(54.5), step_dx, DY(0.5), layer="A-SECT-CUT", lw=15)
    lbl(msp, "RAISED DAIS  +1'-6\"  (3 x 6\" RISERS)",
        DX(D_Y1)+1.5*FT, DY(27.5), h=TX_MEDIUM*FT, layer="A-SECT-CUT", rot=90.0)

    # Rostrum (president desk on dais)
    drect(msp, DX(D_Y2)-5*FT, DY(32.0), DX(D_Y2)-2*FT, DY(23.0),
          layer="A-FURN", lw=25)
    lbl(msp, "PRESIDENT\nROSTRUM\n8'x3'",
        DX(D_Y2)-3.5*FT, DY(27.5), h=TX_MEDIUM*FT, layer="A-FURN")
    chair_sym(msp, DX(D_Y2)-6.5*FT, DY(27.5), r=0.55*FT)

    # Bar council members seating flanking rostrum
    for sy in [42.0, 46.0, 50.0, 7.0, 11.0, 15.0]:
        chair_sym(msp, DX(D_Y2)-3.5*FT, DY(sy))

    # RPwD ramp to dais (both sides)
    for rx in [5.0, 49.0]:
        dline(msp, DX(D_Y1), DY(rx+2), DX(D_Y1)-1.6*FT, DY(rx+2),
              layer="A-SECT-CUT", lw=13)
        dline(msp, DX(D_Y1), DY(rx-2), DX(D_Y1)-1.6*FT, DY(rx-2),
              layer="A-SECT-CUT", lw=13)
        lbl(msp, "RPwD 1:12", DX(D_Y1)-3*FT, DY(rx),
            h=TX_SMALL*FT, layer="A-SECT-CUT")

    # North wall windows on dais (orig_y=93, DX(93))
    for wx_orig in [8.0, 25.0, 42.0]:
        window_sym(msp, DX(93), DY(wx_orig+2.5), DY(wx_orig-2.5),
                   direction="vertical", layer="A-WINDOW")

    lbl(msp,
        "DAIS / SPEAKER ZONE  GF-07\n55' x 14'-6\"  =  798 sq ft",
        DX(86.0), DY(27.5), h=TX_XXL*FT, layer="A-TEXT-TTL")


# =============================================================================
# GROUND FLOOR DIMENSIONS
# =============================================================================
def draw_gf_dims(msp):
    # N-S depth (DX direction)
    arch_dim_h(msp, DX(5), DY(55.0)+2.5*FT, DX(93),
               "88'-0\"  OVERALL N-S DEPTH", offset=2*FT)
    arch_dim_h(msp, DX(5), DY(55.0)+5*FT, DX(21.5),
               "16'-6\"  SOUTH WING DEPTH", offset=2*FT)
    arch_dim_h(msp, DX(5), DY(55.0)+7.5*FT, DX(17.0),
               "12'-0\"  ROOM DEPTH", offset=2*FT)
    arch_dim_h(msp, DX(25.5), DY(55.0)+2.5*FT, DX(63.0),
               "37'-6\"  STAIR LENGTH", offset=2*FT)
    # E-W width (DY direction)
    arch_dim_v(msp, DX(93)+2.5*FT, DY(55.0), DY(0.0),
               "55'-0\"  E-W WIDTH", offset=2*FT)
    arch_dim_v(msp, DX(93)+5*FT, DY(30.0), DY(0.0),
               "30'-0\"  NORTH ZONE WIDTH", offset=2*FT)
    arch_dim_v(msp, DX(5)-2.5*FT, DY(55.0), DY(30.0),
               "25'-0\"  PRESIDENT CHAMBER", offset=-2*FT)
    arch_dim_v(msp, DX(5)-2.5*FT, DY(30.0), DY(15.0),
               "15'-0\"  SECY / BAR OFC", offset=-2*FT)


# =============================================================================
# FIRST FLOOR SERVICE WING  (stacked over GF)
# =============================================================================
def draw_ff_service(msp):
    """FF stair lobby + FF toilets + EDP centre + FF bar secretary."""
    # ---- FF toilets (stacked over GF toilets) ----
    CT = dict(x1=0.0, x2=10.0, y1=17.0, y2=25.5)
    drect(msp, DX(CT['y1']), DY(CT['x2']), DX(CT['y2']), DY(CT['x1']),
          layer="A-WALL", lw=35)
    dline(msp, DX(CT['y1']), DY(5.0), DX(CT['y2']), DY(5.0), layer="A-WALL", lw=25)
    wc_pan(msp, DX(19.5), DY(2.5), facing_deg=90.0)
    wc_pan(msp, DX(19.5), DY(7.5), facing_deg=90.0)
    washbasin(msp, DX(25.0), DY(2.5))
    washbasin(msp, DX(25.0), DY(7.5))
    door_plan(msp, DX(25.5), DY(5.5), 3*FT, rot_deg=0.0, swing_ccw=False, layer="A-DOOR")
    lbl(msp, "FF TOILET\nSTACKED", (DX(17.0)+DX(25.5))/2, (DY(0.0)+DY(10.0))/2,
        h=TX_LARGE*FT, layer="A-TEXT-TTL")

    # ---- FF E-W Corridor (stacked) ----
    floor_hatch(msp, DX(17.0), DY(55.0), DX(25.5), DY(10.0), pattern="GRATE")
    lbl(msp, "FF E-W CORRIDOR  8'-6\" CLEAR",
        (DX(17.0)+DX(25.5))/2, (DY(10.0)+DY(55.0))/2,
        h=TX_LARGE*FT, layer="A-TEXT-TTL", rot=90.0)

    # ---- FF Stair lobby (south of stair, orig_x=0..9, orig_y=5..17) ----
    drect(msp, DX(5.0), DY(9.0), DX(17.0), DY(0.0), layer="A-WALL", lw=25)
    floor_hatch(msp, DX(5.0), DY(9.0), DX(17.0), DY(0.0), pattern="GRATE")
    lbl(msp, "FF STAIR\nLOBBY",
        (DX(5.0)+DX(17.0))/2, (DY(0.0)+DY(9.0))/2,
        h=TX_MEDIUM*FT, layer="A-TEXT-TTL")
    # Exit door from stair -> FF lobby
    door_plan(msp, DX(63.0)-3*FT, DY(2.0), 3*FT, rot_deg=0.0, swing_ccw=True, layer="A-DOOR")
    lbl(msp, "3'-0\"\nSTAIR\n->FF", DX(63.0)-5*FT, DY(2.5), h=TX_SMALL*FT, layer="A-DOOR")

    # ---- EDP / PRINT CENTRE (corner) ----
    # FF-03: orig_x=44..55, orig_y=5..17  (11' x 12')
    EP = dict(x1=44.0, x2=55.0, y1=5.0, y2=17.0)
    drect(msp, DX(EP['y1']), DY(EP['x2']), DX(EP['y2']), DY(EP['x1']),
          layer="A-WALL", lw=35)
    # 3 computer workstations along east wall (orig_y=17 side = DX(17))
    for c_idx, cx_ft in enumerate([46.5, 50.0, 53.0]):
        drect(msp,
              DX(EP['y2'])-3.5*FT, DY(cx_ft+1.5),
              DX(EP['y2'])-1.5*FT, DY(cx_ft-1.5), layer="A-FURN", lw=12)
        chair_sym(msp, DX(EP['y2'])-5.0*FT, DY(cx_ft), r=0.4*FT)
        lbl(msp, f"PC-{c_idx+1}", DX(EP['y2'])-2.5*FT, DY(cx_ft),
            h=TX_SMALL*FT, layer="A-FURN")
    # Laser printer near south wall
    drect(msp, DX(EP['y1'])+1*FT, DY(EP['x2'])+0.5*FT,
          DX(EP['y1'])+3*FT,    DY(EP['x2'])+3*FT, layer="A-FURN", lw=12)
    lbl(msp, "LASER\nPRINTER",
        DX(EP['y1'])+2*FT, DY(EP['x2'])+1.75*FT, h=TX_SMALL*FT, layer="A-FURN")
    # Window on south wall
    window_sym(msp, DX(EP['y1']), DY(EP['x2']-1), DY(EP['x2']-4),
               direction="vertical", layer="A-WINDOW")
    # Entry door from corridor
    door_plan(msp, DX(EP['y2']), DY(EP['x1']+4.5), 3*FT, rot_deg=90.0,
              swing_ccw=True, layer="A-DOOR")
    lbl(msp, "3'-0\"\nEDP", DX(EP['y2'])+2.5*FT, DY(EP['x1']+4),
        h=TX_SMALL*FT, layer="A-DOOR")
    lbl(msp,
        "FF-03  EDP / PRINT CENTRE\n11' x 12'-0\"\n3 PCs + PRINTER\nELECTRONIC CITATION PRINTING",
        (DX(EP['y1'])+DX(EP['y2']))/2, DY((EP['x1']+EP['x2'])/2),
        h=TX_LARGE*FT, layer="A-TEXT-TTL")

    # ---- FF Bar Secretary ----
    # orig_x=10..25, orig_y=5..17
    FS = dict(x1=10.0, x2=25.0, y1=5.0, y2=17.0)
    drect(msp, DX(FS['y1']), DY(FS['x2']), DX(FS['y2']), DY(FS['x1']),
          layer="A-WALL", lw=30)
    window_sym(msp, DX(FS['y1']), DY(FS['x2']-2), DY(FS['x2']-7),
               direction="vertical", layer="A-WINDOW")
    door_plan(msp, DX(FS['y2']), DY(FS['x1']+4), 3*FT, rot_deg=90.0,
              swing_ccw=True, layer="A-DOOR")
    drect(msp, DX(FS['y2'])-4*FT, DY(FS['x2']-2), DX(FS['y2'])-0.5*FT, DY(FS['x2']-7),
          layer="A-FURN", lw=13)
    chair_sym(msp, DX(FS['y2'])-5.5*FT, (DY(FS['x2']-2)+DY(FS['x2']-7))/2)
    lbl(msp,
        "FF-04  FF BAR SECRETARY\n15' x 12'  =  180 sq ft",
        (DX(FS['y1'])+DX(FS['y2']))/2, DY((FS['x1']+FS['x2'])/2),
        h=TX_LARGE*FT, layer="A-TEXT-TTL")

    # ---- FF Discussion Room ----
    # orig_x=25..44, orig_y=5..17
    DS = dict(x1=25.0, x2=44.0, y1=5.0, y2=17.0)
    drect(msp, DX(DS['y1']), DY(DS['x2']), DX(DS['y2']), DY(DS['x1']),
          layer="A-WALL", lw=30)
    # Conference table
    drect(msp, DX(DS['y2'])-5.5*FT, DY(DS['x2']-3), DX(DS['y2'])-1.5*FT, DY(DS['x1']+3),
          layer="A-FURN", lw=18)
    lbl(msp, "CONF TABLE 8'x12'",
        DX(DS['y2'])-3.5*FT, DY((DS['x1']+DS['x2'])/2),
        h=TX_SMALL*FT, layer="A-FURN")
    for cdy in [DS['x1']+5, DS['x1']+10, DS['x1']+15, DS['x1']+20]:
        if cdy < DS['x2']-2:
            chair_sym(msp, DX(DS['y2'])-6.5*FT, DY(cdy))
            chair_sym(msp, DX(DS['y2'])-0.5*FT, DY(cdy))
    window_sym(msp, DX(DS['y1']), DY(DS['x2']-2), DY(DS['x1']+4),
               direction="vertical", layer="A-WINDOW")
    door_plan(msp, DX(DS['y2']), DY(DS['x2']-5), 3*FT, rot_deg=90.0,
              swing_ccw=False, layer="A-DOOR")
    lbl(msp,
        "FF-05  DISCUSSION ROOM\n19' x 12'  =  228 sq ft",
        (DX(DS['y1'])+DX(DS['y2']))/2, DY((DS['x1']+DS['x2'])/2),
        h=TX_LARGE*FT, layer="A-TEXT-TTL")


# =============================================================================
# FIRST FLOOR  -  LIBRARY + STACK
# Library tables: CHAIRS ON BOTH SIDES (north + south of each table)
# =============================================================================
def draw_ff_library(msp):
    """
    Library Reading Room FF-01: orig_x=0..55, orig_y=25.5..64.5
    Stair occupies orig_x=0..9, orig_y=25.5..63 - tables wrap around it.
    Book Stack FF-02: orig_x=0..55, orig_y=64.5..82.5
    """
    # Reading room walls
    drect(msp, DX(25.5), DY(55.0), DX(64.5), DY(0.0), layer="A-WALL", lw=35)

    # ---- Library tables with chairs on BOTH sides ----
    # Table: 5' long (orig_x direction = DY), 2' deep (orig_y direction = DX)
    tbl_len = 5.0 * FT    # DY span
    tbl_dep = 2.0 * FT    # DX span
    # Chair offset from table face: 0.8 ft
    chair_off = 0.8 * FT
    chair_sp  = 2.0 * FT  # chair spacing along table

    # Table rows in DX (orig_y): starting just east of stair bottom landing
    # Row DX positions (in orig_y terms):
    row_orig_ys = [28.0, 32.5, 37.0, 41.5, 46.0, 50.5, 55.0, 59.5]

    # Column positions (in orig_x terms, DY axis):
    # West bank (orig_x=10..27): columns at 12.5, 18.5, 24.5 (clear of stair at orig_x=0..9)
    west_cols = [12.0, 18.0, 24.0]
    # East bank (orig_x=29..54): columns at 31.5, 37.5, 43.5, 49.5
    east_cols = [31.0, 37.0, 43.0, 49.0]

    all_cols = west_cols + east_cols

    for orig_y in row_orig_ys:
        row_dx = DX(orig_y)
        for orig_x in all_cols:
            col_dy = DY(orig_x)
            # Table rectangle
            drect(msp,
                  row_dx - tbl_dep/2, col_dy - tbl_len/2,
                  row_dx + tbl_dep/2, col_dy + tbl_len/2,
                  layer="A-FURN", lw=15)
            # Chairs on NORTH side (DX + offset = orig_y side facing north)
            for sdy in [col_dy - 1.5*FT, col_dy, col_dy + 1.5*FT]:
                chair_sym(msp, row_dx + tbl_dep/2 + chair_off, sdy)
            # Chairs on SOUTH side (DX - offset = orig_y side facing south)
            for sdy in [col_dy - 1.5*FT, col_dy, col_dy + 1.5*FT]:
                chair_sym(msp, row_dx - tbl_dep/2 - chair_off, sdy)

    # Central aisle (orig_x=27..30 = 3' aisle centred at orig_x=28.5)
    dline(msp, DX(25.5), DY(30.0), DX(64.5), DY(30.0), layer="A-BAY", lw=15)
    dline(msp, DX(25.5), DY(27.0), DX(64.5), DY(27.0), layer="A-BAY", lw=15)
    lbl(msp, "4'-0\" CENTRAL AISLE  (NBC 2016)",
        DX(45.0), DY(28.5), h=TX_LARGE*FT, layer="A-BAY", rot=90.0)

    # Windows on east wall (orig_y=64.5)
    for wx_orig in [8.0, 20.0, 35.0, 50.0]:
        window_sym(msp, DX(64.5), DY(wx_orig+3), DY(wx_orig-3),
                   direction="vertical", layer="A-WINDOW")
        lbl(msp, "W 6'\nS 2'6\"", DX(64.5)+2.5*FT, DY(wx_orig),
            h=TX_SMALL*FT, layer="A-WINDOW")

    # 2 entry doors on south wall (orig_y=25.5)
    door_plan(msp, DX(25.5), DY(20.0), 4*FT, rot_deg=0.0, swing_ccw=False, layer="A-DOOR")
    door_plan(msp, DX(25.5), DY(13.0), 4*FT, rot_deg=0.0, swing_ccw=True,  layer="A-DOOR")
    lbl(msp, "LIB ENTRY 1\n2 x 4'-0\"",
        DX(25.5)+3*FT, DY(16.5), h=TX_MEDIUM*FT, layer="A-DOOR")

    door_plan(msp, DX(25.5), DY(43.0), 4*FT, rot_deg=0.0, swing_ccw=False, layer="A-DOOR")
    door_plan(msp, DX(25.5), DY(37.0), 4*FT, rot_deg=0.0, swing_ccw=True,  layer="A-DOOR")
    lbl(msp, "LIB ENTRY 2\n2 x 4'-0\"",
        DX(25.5)+3*FT, DY(40.0), h=TX_MEDIUM*FT, layer="A-DOOR")

    lbl(msp,
        "LIBRARY READING ROOM  FF-01\n55' x 39'  ~  2,145 sq ft\n"
        "TABLES WITH CHAIRS ON BOTH SIDES\n(NBC 2016 / RPwD 2016)",
        DX(45.0), DY(44.0),
        h=TX_XXL*FT, layer="A-TEXT-TTL")

    # ---- BOOK STACK AREA  orig_y=64.5..82.5 ----
    drect(msp, DX(64.5), DY(55.0), DX(82.5), DY(0.0), layer="A-WALL", lw=35)
    for sh_i in range(5):
        shy = DX(64.5 + 2.0 + sh_i * 3.0)
        dline(msp, shy,         DY(54.0), shy,       DY(1.0), layer="A-LOCKER", lw=13)
        dline(msp, shy+1.5*FT,  DY(54.0), shy+1.5*FT, DY(1.0), layer="A-LOCKER", lw=13)
        lbl(msp, f"STACK {sh_i+1:02d}", shy+0.75*FT, DY(27.5),
            h=TX_SMALL*FT, layer="A-LOCKER", rot=90.0)

    # Doors reading room -> stack (orig_y=64.5 wall)
    door_plan(msp, DX(64.5), DY(20.0), 3*FT, rot_deg=0.0, swing_ccw=False, layer="A-DOOR")
    door_plan(msp, DX(64.5), DY(40.0), 3*FT, rot_deg=0.0, swing_ccw=True,  layer="A-DOOR")
    lbl(msp, "RDNG -> STACK  2 x 3'-0\"",
        DX(64.5)+2*FT, DY(30.0), h=TX_MEDIUM*FT, layer="A-DOOR", rot=90.0)

    # Windows on east wall of stack (orig_y=82.5)
    for wx_orig in [8.0, 25.0, 45.0]:
        window_sym(msp, DX(82.5), DY(wx_orig+2.5), DY(wx_orig-2.5),
                   direction="vertical", layer="A-WINDOW")

    # North wall windows (orig_y=93)
    for wx_orig in [8.0, 25.0, 42.0]:
        window_sym(msp, DX(93.0), DY(wx_orig+2.5), DY(wx_orig-2.5),
                   direction="vertical", layer="A-WINDOW")

    lbl(msp,
        "BOOK STACK  FF-02\n55' x 18'  =  990 sq ft\n5 DOUBLE-SIDED ROWS",
        DX(73.5), DY(27.5), h=TX_XXL*FT, layer="A-TEXT-TTL")


# =============================================================================
# AREA SCHEDULE (drawn on right margin of sheet)
# =============================================================================
def draw_area_schedule(msp, floor="GF"):
    sx = DX(93) + 3*FT
    sy = DY(0.0) + SH * 0.75
    lbl(msp, f"{'GF' if floor=='GF' else 'FF'} AREA SCHEDULE",
        sx + 10*FT, sy, h=TX_XL*FT, layer="A-TEXT-TTL")
    if floor == "GF":
        rows = [
            ("GF-01  President Chamber",  "25'x12'",   "300"),
            ("       Attached Toilet",     "7'x6'",     " 42"),
            ("GF-02  Secretary Chamber",  "15'x12'",   "180"),
            ("       Attached Toilet",     "7'x6'",     " 42"),
            ("GF-03  Bar Office Room",    "15'x12'",   "180"),
            ("GF-04  Common Toilet",      "10'x8.5'",  " 85"),
            ("GF-05  Dog-leg Stair",      "9'x37.5'",  "338"),
            ("GF-06  Assembly Hall",      "55'x53'",   "2,915"),
            ("GF-07  Dais/Speaker Zone",  "55'x14.5'", "798"),
            ("       Corridors + Lobby",  "---",       "~500"),
            ("TOTAL GF",                  "",          "5,380"),
        ]
    else:
        rows = [
            ("FF-01  Library",             "55'x39'",   "2,145"),
            ("FF-02  Book Stack",          "55'x18'",   "  990"),
            ("FF-03  EDP / Print Centre",  "11'x12'",   "  132"),
            ("FF-04  FF Bar Secretary",    "15'x12'",   "  180"),
            ("FF-05  Discussion Room",     "19'x12'",   "  228"),
            ("FF-06  Dog-leg Stair",       "9'x37.5'",  "  338"),
            ("       FF Toilets",          "10'x8.5'",  "   85"),
            ("       Corridors",           "---",       " ~450"),
            ("TOTAL FF",                   "",          "4,548"),
        ]
    for i, (nm, dim, ar) in enumerate(rows):
        yt = sy - (i+1) * 1.8*FT
        bold = (i == len(rows) - 1)
        hl  = TX_LARGE*FT if bold else TX_MEDIUM*FT
        lay = "A-TEXT-TTL" if bold else "A-TEXT"
        text_msp(msp, nm,           sx,          yt, h=hl, layer=lay,
                 align=TextEntityAlignment.LEFT)
        text_msp(msp, dim,          sx + 22*FT,  yt, h=hl, layer=lay,
                 align=TextEntityAlignment.LEFT)
        text_msp(msp, ar+" sqft",   sx + 32*FT,  yt, h=hl, layer=lay,
                 align=TextEntityAlignment.LEFT)


# =============================================================================
# SHEET 01  -  GROUND FLOOR
# =============================================================================
def draw_ground_floor():
    doc, msp = setup_doc(sheet_w=SW, sheet_h=SH, config=config)

    draw_direction_labels(msp)
    draw_envelope(msp)
    draw_columns(msp)
    draw_gf_service_wing(msp)
    draw_dogleg_stair(msp, floor="GF")
    draw_gf_hall(msp)
    draw_gf_dims(msp)
    draw_area_schedule(msp, floor="GF")

    # North arrow (north = right side of drawing after 90 CW rotation)
    draw_north_arrow(msp, DX(90), DY(52) - 3*FT, size=3.5*FT)

    draw_sheet_frame_and_titleblock(
        msp, SW, SH,
        sheet_no="SHEET 01 OF 02",
        sheet_title="GROUND FLOOR PLAN",
        scale_txt='1/8"=1\'-0"  A4 PORTRAIT',
        config=config,
        rev="B",
        notes=[
            "DRAWING ROTATED 90 DEG CLOCKWISE: SOUTH=LEFT  NORTH=RIGHT  WEST=TOP  EAST=BOTTOM.",
            "DOG-LEG STAIR (GF-05): 9'-0\" CLEAR (2x4'-6\" flights) | 2x12 RISERS @7\"R/12\"T | FLOOR-TO-FLOOR 14'-0\" | LANDINGS 4'-6\" (NBC/RPwD).",
            "GF-01 PRESIDENT CHAMBER 25'x12' WITH ATTACHED TOILET 7'x6'. GF-02 SECRETARY 15'x12' + TOILET. GF-03 BAR OFFICE 15'x12'.",
            "GF-04 COMMON LAWYER TOILET: MALE + FEMALE, 10'x8'-6\". GF-06 ASSEMBLY HALL: AUDIENCE CHAIRS ONLY - NO TABLES.",
            "ALL DOORS SWING INTO ROOM. EMERGENCY EXIT EAST WALL 4'-0\" SWING OUT (NBC 4.8). WINDOWS: 5'-0\" wide, SILL 3'-0\", LINTEL 7'-0\".",
            "RCC FRAMED: 12\"x12\" COLS ON ~15' GRID. SLAB 250mm (10\"). BEAMS 230x450. VERIFY WITH LICENSED SE BEFORE SUBMISSION.",
            "NBC 2016 + RPwD ACT 2016. FONT SIZES 3x NBC MINIMUM AS DIRECTED. PRELIMINARY STUDY ONLY.",
        ]
    )

    dxf_path = OUT_DXF / "BA-RevB-Ground-Floor.dxf"
    doc.saveas(str(dxf_path))
    print(f"[OK] GF DXF: {dxf_path.name}")
    pdf = export_dxf_to_pdf(dxf_path, config)
    print(f"[OK] GF PDF: {pdf}")
    return dxf_path, pdf


# =============================================================================
# SHEET 02  -  FIRST FLOOR
# =============================================================================
def draw_first_floor():
    doc, msp = setup_doc(sheet_w=SW, sheet_h=SH, config=config)

    draw_direction_labels(msp)
    draw_envelope(msp)
    draw_columns(msp)
    draw_ff_service(msp)
    draw_dogleg_stair(msp, floor="FF")
    draw_ff_library(msp)
    draw_gf_dims(msp)
    draw_area_schedule(msp, floor="FF")

    draw_north_arrow(msp, DX(90), DY(52) - 3*FT, size=3.5*FT)

    draw_sheet_frame_and_titleblock(
        msp, SW, SH,
        sheet_no="SHEET 02 OF 02",
        sheet_title="FIRST FLOOR PLAN - LIBRARY + EDP + ADMIN",
        scale_txt='1/8"=1\'-0"  A4 PORTRAIT',
        config=config,
        rev="B",
        notes=[
            "DRAWING ROTATED 90 DEG CLOCKWISE: SOUTH=LEFT  NORTH=RIGHT  WEST=TOP  EAST=BOTTOM.",
            "DOG-LEG STAIR (FF-06): STACKED OVER GF STAIR. SAME 9'x37.5' COMPARTMENT. FF EXIT DOOR -> FF LOBBY.",
            "LIBRARY (FF-01): 55'x39'. TABLES WITH CHAIRS ON BOTH NORTH AND SOUTH SIDES. 4'-0\" CENTRAL AISLE (NBC 2016).",
            "EDP/PRINT CENTRE (FF-03): 3 PCs + LASER PRINTER. ELECTRONIC CITATION PRINTING. CORNER SEGMENT SE WING.",
            "STACK (FF-02): 5 DOUBLE-SIDED SHELF ROWS. LAW REPORTS / JOURNALS / ARCHIVES. FLOOR LOAD 300kg/m2 - VERIFY WITH SE.",
            "ALL DOORS SWING INTO ROOM. STAIR WIDTH 9'-0\" (NBC/RPwD). PLUMBING RISERS STACKED OVER GF. FF TOILETS STACKED.",
            "NBC 2016 + RPwD ACT 2016. FONT SIZES 3x NBC MINIMUM AS DIRECTED. PRELIMINARY STUDY ONLY.",
        ]
    )

    dxf_path = OUT_DXF / "BA-RevB-First-Floor.dxf"
    doc.saveas(str(dxf_path))
    print(f"[OK] FF DXF: {dxf_path.name}")
    pdf = export_dxf_to_pdf(dxf_path, config)
    print(f"[OK] FF PDF: {pdf}")
    return dxf_path, pdf


# =============================================================================
# MAIN
# =============================================================================
# BARE ARCHITECTURAL DRAWINGS  (no furniture — for statutory approval submission)
# Strategy: load the furnished DXF saved to disk, delete every entity whose
# layer starts with "A-FURN", then save as a new file and re-export PDF.
# Layers purged: A-FURN  (desks, chairs, almirahs, sofas, audience chairs,
#                          shelving symbols, computer workstations, WC pans,
#                          wash basins, sanitary ware)
# Layers KEPT:   A-WALL, A-COLUMN, A-DOOR, A-WINDOW, A-GRID, A-HATCH,
#                A-BAY, A-ACC, A-SECT-CUT, A-LOCKER (shelf outlines kept),
#                A-TEXT, A-TEXT-TTL, A-DIM, A-TTLB, A-SITE
# =============================================================================

# Furniture / sanitary layer names to strip for bare drawing
_BARE_PURGE_LAYERS = {
    "A-FURN",    # all furniture, desks, chairs, sanitary ware
}

def make_bare_drawing(furnished_dxf_path: Path, bare_stem: str,
                      sheet_no: str, sheet_title: str) -> tuple:
    """
    Load a furnished DXF, strip all A-FURN entities, update title block
    annotation to indicate 'BARE ARCHITECTURAL', save as new DXF + PDF.

    Returns (bare_dxf_path, bare_pdf_path).
    """
    import ezdxf as _ezdxf

    # Load the furnished drawing
    doc = _ezdxf.readfile(str(furnished_dxf_path))
    msp = doc.modelspace()

    # ---- Delete all entities on purge-list layers ----
    entities_to_delete = [
        e for e in msp
        if hasattr(e, 'dxf') and
           getattr(e.dxf, 'layer', '').upper() in _BARE_PURGE_LAYERS
    ]
    for e in entities_to_delete:
        msp.delete_entity(e)

    # ---- Add "BARE ARCHITECTURAL" watermark annotation ----
    # Place it in the top-left corner of the plan area
    try:
        from ezdxf.enums import TextEntityAlignment as _TAL
        t = msp.add_text(
            "BARE ARCHITECTURAL DRAWING  -  NO FURNITURE",
            dxfattribs={
                "layer": "A-TEXT-TTL",
                "height": TX_XL * FT,
                "rotation": 0.0,
            },
        )
        t.set_placement(
            (DX(5), DY(55.0) - 5*FT),
            align=_TAL.LEFT,
        )
    except Exception:
        pass

    # ---- Save bare DXF ----
    bare_dxf = OUT_DXF / f"{bare_stem}.dxf"
    doc.saveas(str(bare_dxf))
    print(f"[OK] BARE DXF: {bare_dxf.name}  "
          f"({len(entities_to_delete)} furniture entities removed)")

    # ---- Export bare PDF via traecad engine ----
    bare_pdf = export_dxf_to_pdf(bare_dxf, config)
    print(f"[OK] BARE PDF: {bare_pdf}")

    return bare_dxf, bare_pdf


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("BAR ASSOCIATION BANSWARA  Rev-B  -  CAD GENERATION")
    print("=" * 70)
    ht = int(N_RISERS * 2 * RISER_IN)
    print(f"STAIR CHECK: 2 x {N_RISERS} risers @ {RISER_IN}\" = {ht}\" "
          f"= {ht//12}'-{ht%12}\"  (target 14'-0\")")
    print(f"TREAD: {int(TREAD_FT*12)}\"  |  CLEAR WIDTH: {STAIR_W_FT}'-0\"")
    print(f"COMPARTMENT: {STAIR_W_FT}' x {STAIR_LEN_FT}'  "
          f"({BTM_LAND}+{FLIGHT_RUN}+{MID_LAND}+{FLIGHT_RUN}+{TOP_LAND} = {STAIR_LEN_FT})")
    print()

    # ---- SET A: FURNISHED (with furniture) ----
    print("--- SET A: FURNISHED DRAWINGS ---")
    gf_dxf, gf_pdf = draw_ground_floor()
    ff_dxf, ff_pdf = draw_first_floor()

    # ---- SET B: BARE ARCHITECTURAL (no furniture) ----
    print()
    print("--- SET B: BARE ARCHITECTURAL DRAWINGS (no furniture) ---")
    bare_gf_dxf, bare_gf_pdf = make_bare_drawing(
        gf_dxf,
        bare_stem="BA-RevB-Ground-Floor-BARE",
        sheet_no="SHEET 03 OF 04",
        sheet_title="GF PLAN - BARE ARCHITECTURAL (NO FURNITURE)",
    )
    bare_ff_dxf, bare_ff_pdf = make_bare_drawing(
        ff_dxf,
        bare_stem="BA-RevB-First-Floor-BARE",
        sheet_no="SHEET 04 OF 04",
        sheet_title="FF PLAN - BARE ARCHITECTURAL (NO FURNITURE)",
    )

    # ---- SUMMARY ----
    print()
    print("=" * 70)
    print("ALL 4 DRAWINGS COMPLETE:")
    print()
    print("  SET A  -  FURNISHED (walls + furniture + sanitary):")
    print(f"    GF DXF : {gf_dxf.name}")
    print(f"    GF PDF : {Path(gf_pdf).name}")
    print(f"    FF DXF : {ff_dxf.name}")
    print(f"    FF PDF : {Path(ff_pdf).name}")
    print()
    print("  SET B  -  BARE ARCHITECTURAL (walls + doors + windows + dims only):")
    print(f"    GF DXF : {bare_gf_dxf.name}")
    print(f"    GF PDF : {Path(bare_gf_pdf).name}")
    print(f"    FF DXF : {bare_ff_dxf.name}")
    print(f"    FF PDF : {Path(bare_ff_pdf).name}")
    print()
    print("  All files in:")
    print(f"    DXF -> {OUT_DXF}")
    print(f"    PDF -> {OUT_PDF}")
    print("=" * 70)
