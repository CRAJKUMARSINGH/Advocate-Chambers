import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from traecad_engine import *
import math

FT = 12.0
IN = 1.0
OWT = 12 * IN
IWT = 8 * IN

TX_MICRO  =  3.0 / 32.0 * 4.0
TX_SMALL  =  1.0 / 8.0  * 4.0
TX_MEDIUM =  3.0 / 16.0 * 4.0
TX_LARGE  =  1.0 / 4.0  * 4.0
TX_XL     =  5.0 / 16.0 * 4.0
TX_XXL    =  3.0 / 8.0  * 4.0
TX_TITLE  =  1.0 / 2.0  * 4.0
TX_SUPER  =  3.0 / 4.0  * 4.0
TX_DIM_TEXT = TX_MEDIUM
TX_DIM_TICK = TX_SMALL
TX_TB_LABEL = TX_MEDIUM
TX_TB_VALUE_LG = TX_LARGE
TX_TB_VALUE_MD = TX_MEDIUM
TX_TB_NOTE  = TX_SMALL


def door_swing_local(msp, hinge_x, hinge_y, width, swing_dir=1,
                     angle=90.0, layer="A-DOOR", lw=24):
    rad = math.radians(angle)
    leaf_ex = hinge_x + width * math.cos(0)
    leaf_ey = hinge_y + width * swing_dir * math.sin(0)
    msp.add_line((hinge_x, hinge_y), (leaf_ex, leaf_ey),
                 dxfattribs={"layer": layer, "lineweight": lw})
    start_a = 0.0 if swing_dir > 0 else 360.0 - angle
    end_a = angle if swing_dir > 0 else 360.0
    try:
        msp.add_arc(center=(hinge_x, hinge_y), radius=width,
                    start_angle=start_a, end_angle=end_a,
                    dxfattribs={"layer": layer, "lineweight": int(lw*0.6)})
    except Exception:
        pass


def window_plan(msp, cx, cy, w, direction="s", layer="A-WINDOW", lw=22):
    if direction in ("s", "n"):
        wx1 = cx - w / 2.0
        wx2 = cx + w / 2.0
        wy1 = cy - 3 * IN
        wy2 = cy + 3 * IN
        line(msp, wx1, wy1, wx2, wy1, layer=layer, lw=lw)
        line(msp, wx1, wy2, wx2, wy2, layer=layer, lw=lw)
        line(msp, wx1, wy1 + 1 * IN, wx2, wy1 + 1 * IN, layer=layer, lw=max(lw - 4, 10))
        line(msp, wx1, wy2 - 1 * IN, wx2, wy2 - 1 * IN, layer=layer, lw=max(lw - 4, 10))
        line(msp, wx1, wy1, wx1, wy2, layer=layer, lw=lw)
        line(msp, wx2, wy1, wx2, wy2, layer=layer, lw=lw)
    else:
        wx1 = cx - 3 * IN
        wx2 = cx + 3 * IN
        wy1 = cy - w / 2.0
        wy2 = cy + w / 2.0
        line(msp, wx1, wy1, wx1, wy2, layer=layer, lw=lw)
        line(msp, wx2, wy1, wx2, wy2, layer=layer, lw=lw)
        line(msp, wx1 + 1 * IN, wy1, wx1 + 1 * IN, wy2, layer=layer, lw=max(lw - 4, 10))
        line(msp, wx2 - 1 * IN, wy1, wx2 - 1 * IN, wy2, layer=layer, lw=max(lw - 4, 10))
        line(msp, wx1, wy1, wx2, wy1, layer=layer, lw=lw)
        line(msp, wx1, wy2, wx2, wy2, layer=layer, lw=lw)
    return True


def public_stair_dogleg(msp, ox, oy):
    w_ft = 9.0
    length_ft = 33.0
    flight_risers = 13
    tread_in = 12.0
    riser_in = 6.846
    w = w_ft * FT
    L = length_ft * FT
    tread = tread_in * IN
    riser_count = flight_risers
    flight_run = riser_count * tread

    rect(msp, ox, oy, ox + w, oy + L, layer="A-WALL", lw=40)

    bottom_land_depth = (L - 2 * flight_run - w) / 2.0
    mid_land_d = w
    top_land_depth = bottom_land_depth

    fl1_y0 = oy + bottom_land_depth
    fl1_y1 = fl1_y0 + flight_run
    mid_y0 = fl1_y1
    mid_y1 = mid_y0 + mid_land_d
    fl2_y0 = mid_y1
    fl2_y1 = fl2_y0 + flight_run

    fill_rect(msp, ox, oy, ox + w, oy + bottom_land_depth, hatch="ANSI32", layer="A-HATCH")
    text_msp(msp, "GF LANDING", ox + w / 2.0, oy + bottom_land_depth / 2.0,
             h=TX_SMALL * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)

    fill_rect(msp, ox, mid_y0, ox + w, mid_y1, hatch="ANSI32", layer="A-HATCH")
    text_msp(msp, "MID LANDING", ox + w / 2.0, (mid_y0 + mid_y1) / 2.0,
             h=TX_SMALL * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)

    fill_rect(msp, ox, fl2_y1, ox + w, oy + L, hatch="ANSI32", layer="A-HATCH")
    text_msp(msp, "FF LANDING", ox + w / 2.0, fl2_y1 + top_land_depth / 2.0,
             h=TX_SMALL * FT, layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)

    partition_x = ox + 4.5 * FT

    f1x0 = ox
    f1x1 = ox + 4 * FT
    for i in range(riser_count + 1):
        y_ = fl1_y0 + i * tread
        line(msp, f1x0, y_, f1x1, y_, layer="A-WALL", lw=22)

    line(msp, f1x0, fl1_y0, f1x0, fl1_y1, layer="A-ACC", lw=22)
    line(msp, partition_x, fl1_y0, partition_x, fl1_y1, layer="A-ACC", lw=22)

    f2x0 = ox + 5 * FT
    f2x1 = ox + w
    for i in range(riser_count + 1):
        y_ = fl2_y0 + i * tread
        line(msp, f2x0, y_, f2x1, y_, layer="A-WALL", lw=22)

    line(msp, f2x1, fl2_y0, f2x1, fl2_y1, layer="A-ACC", lw=22)
    line(msp, partition_x, fl2_y0, partition_x, fl2_y1, layer="A-ACC", lw=22)

    arr_mid_y = (fl1_y0 + fl1_y1) / 2.0
    line(msp, ox + 2 * FT, fl1_y0 + 12 * IN, ox + 2 * FT, fl1_y1 - 12 * IN,
         layer="A-SECT-CUT", lw=26)
    line(msp, ox + 2 * FT, fl1_y1 - 12 * IN, ox + 2 * FT - 8 * IN, fl1_y1 - 20 * IN,
         layer="A-SECT-CUT", lw=26)
    line(msp, ox + 2 * FT, fl1_y1 - 12 * IN, ox + 2 * FT + 8 * IN, fl1_y1 - 20 * IN,
         layer="A-SECT-CUT", lw=26)
    text_msp(msp, "UP", ox + 2 * FT, arr_mid_y,
             h=TX_LARGE * FT, layer="A-SECT-CUT", align=TextEntityAlignment.MIDDLE_CENTER)

    arr2_mid_y = (fl2_y0 + fl2_y1) / 2.0
    line(msp, ox + 7 * FT, fl2_y1 - 12 * IN, ox + 7 * FT, fl2_y0 + 12 * IN,
         layer="A-SECT-CUT", lw=26)
    line(msp, ox + 7 * FT, fl2_y0 + 12 * IN, ox + 7 * FT - 8 * IN, fl2_y0 + 20 * IN,
         layer="A-SECT-CUT", lw=26)
    line(msp, ox + 7 * FT, fl2_y0 + 12 * IN, ox + 7 * FT + 8 * IN, fl2_y0 + 20 * IN,
         layer="A-SECT-CUT", lw=26)
    text_msp(msp, "DOWN", ox + 7 * FT, arr2_mid_y,
             h=TX_LARGE * FT, layer="A-SECT-CUT", align=TextEntityAlignment.MIDDLE_CENTER)

    hdr = f"STAIRE 9'W  2x{riser_count}RISERS  {tread_in:.0f}\"T  {riser_in:.1f}\"R"
    text_msp(msp, hdr, ox + w / 2.0, oy - 2.0 * FT,
             h=TX_SMALL * FT, layer="A-TEXT", align=TextEntityAlignment.MIDDLE_CENTER)

    return {
        "compartment_ox": ox, "compartment_oy": oy,
        "compartment_ex": ox + w, "compartment_ey": oy + L,
        "bottom_land": (ox, oy, ox + w, oy + bottom_land_depth),
        "mid_land": (ox, mid_y0, ox + w, mid_y1),
        "top_land": (ox, fl2_y1, ox + w, oy + L),
        "fl1": (f1x0, fl1_y0, f1x1, fl1_y1),
        "fl2": (f2x0, fl2_y0, f2x1, fl2_y1),
    }


BASE = Path(__file__).resolve().parent
OUT_DXF = BASE / "CAD"
OUT_PDF = BASE / "PDF"
OUT_DXF.mkdir(parents=True, exist_ok=True)
OUT_PDF.mkdir(parents=True, exist_ok=True)

import os as _os
BARE = _os.environ.get("BARE", "0") == "1"
SUFFIX = "-BARE" if BARE else ""

def _skip_layer(layer: str) -> bool:
    if not BARE:
        return False
    if layer is None:
        return False
    skip_prefixes = (
        "A-FURN", "A-LOCKER", "A-JALI",
        "FURN", "LOCKER", "JALI",
    )
    return any(layer.startswith(p) for p in skip_prefixes)

config = ProjectConfig(
    project_title="BAR ASSOCIATION HALL - BANSWARA",
    client="BAR ASSOCIATION, BANSWARA",
    date="18 SEPT 2026",
    drawn_by="TRAE AI ARCHITECTURE",
    code_ref="NBC 2016",
    doc_ref="BA-Banswara-Revised",
    base_dir=str(BASE),
    dxf_subdir="CAD",
    pdf_subdir="PDF",
    paper_size="A4",
    margin_mm=10.0,
)

SW = 120.0 * FT
SH = SW * (config.printable_h_mm / config.printable_w_mm) * (297.0 / 210.0)

PLAN_OX = 15.0 * FT
PLAN_OY = 18.0 * FT


def X(x_ft): return PLAN_OX + x_ft * FT
def Y(y_ft): return PLAN_OY + y_ft * FT

ENV_PTS = [
    (X(0),   Y(5)),
    (X(30),  Y(5)),
    (X(30),  Y(21.5)),
    (X(55),  Y(21.5)),
    (X(55),  Y(93)),
    (X(0),   Y(93)),
]


def rotate_pt(px, py, cx, cy, deg=-90.0):
    r = math.radians(deg)
    dx, dy = px - cx, py - cy
    rx = dx * math.cos(r) - dy * math.sin(r) + cx
    ry = dx * math.sin(r) + dy * math.cos(r) + cy
    return rx, ry


def rotated_rect(msp, x1, y1, x2, y2, cx, cy, deg=-90.0, **kw):
    pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    rpts = [rotate_pt(p[0], p[1], cx, cy, deg) for p in pts]
    polyline(msp, rpts, closed=True, **kw)


def rotated_line(msp, x1, y1, x2, y2, cx, cy, deg=-90.0, **kw):
    rx1, ry1 = rotate_pt(x1, y1, cx, cy, deg)
    rx2, ry2 = rotate_pt(x2, y2, cx, cy, deg)
    line(msp, rx1, ry1, rx2, ry2, **kw)


def rotated_text(msp, txt, x, y, cx, cy, deg=-90.0, **kw):
    rx, ry = rotate_pt(x, y, cx, cy, deg)
    kw.setdefault("rot", 0.0)
    kw["rot"] = (kw.get("rot", 0.0) + deg) % 360.0
    text_msp(msp, txt, rx, ry, **kw)


def rotated_circle(msp, cx0, cy0, r, cx, cy, deg=-90.0, **kw):
    rx, ry = rotate_pt(cx0, cy0, cx, cy, deg)
    circle(msp, rx, ry, r, **kw)


ROT_CX = X(27.5)
ROT_CY = Y(49.0)
ROT_DEG = -90.0


def r_rect(msp, x1, y1, x2, y2, **kw):
    if _skip_layer(kw.get("layer", "")): return
    rotated_rect(msp, x1, y1, x2, y2, ROT_CX, ROT_CY, ROT_DEG, **kw)


def r_line(msp, x1, y1, x2, y2, **kw):
    if _skip_layer(kw.get("layer", "")): return
    rotated_line(msp, x1, y1, x2, y2, ROT_CX, ROT_CY, ROT_DEG, **kw)


def r_text(msp, txt, x, y, **kw):
    if _skip_layer(kw.get("layer", "")): return
    rotated_text(msp, txt, x, y, ROT_CX, ROT_CY, ROT_DEG, **kw)


def r_circle(msp, cx0, cy0, r, **kw):
    if _skip_layer(kw.get("layer", "")): return
    rotated_circle(msp, cx0, cy0, r, ROT_CX, ROT_CY, ROT_DEG, **kw)


def r_fill_rect(msp, x1, y1, x2, y2, **kw):
    if _skip_layer(kw.get("layer", "")): return
    min_x, max_x = min(x1, x2), max(x1, x2)
    min_y, max_y = min(y1, y2), max(y1, y2)
    pts = [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]
    rpts = [rotate_pt(p[0], p[1], ROT_CX, ROT_CY, ROT_DEG) for p in pts]
    try:
        layer = kw.get("layer", "A-HATCH")
        hatch_pat = kw.get("hatch", "SOLID")
        h = msp.add_hatch(color=8, dxfattribs={"layer": layer})
        h.set_pattern_fill(hatch_pat, scale=kw.get("scale", 1.0))
        h.paths.add_polyline_path(rpts, is_closed=True)
    except Exception:
        pass


def r_door_swing(msp, hx, hy, w, swing_dir=1, **kw):
    hx_r, hy_r = rotate_pt(hx, hy, ROT_CX, ROT_CY, ROT_DEG)
    leaf_ex = hx + w * math.cos(0)
    leaf_ey = hy + w * swing_dir * math.sin(0)
    lex_r, ley_r = rotate_pt(leaf_ex, leaf_ey, ROT_CX, ROT_CY, ROT_DEG)
    layer = kw.get("layer", "A-DOOR")
    lw = kw.get("lw", 24)
    msp.add_line((hx_r, hy_r), (lex_r, ley_r), dxfattribs={"layer": layer, "lineweight": lw})
    start_a = 0.0 if swing_dir > 0 else 360.0 - 90.0
    end_a = 90.0 if swing_dir > 0 else 360.0
    try:
        msp.add_arc(center=(hx_r, hy_r), radius=w,
                    start_angle=(start_a + ROT_DEG) % 360,
                    end_angle=(end_a + ROT_DEG) % 360,
                    dxfattribs={"layer": layer, "lineweight": int(lw*0.6)})
    except Exception:
        pass


def r_window(msp, cx0, cy0, w, direction="s"):
    t_full = OWT
    t_half = t_full / 2.0
    lw_o = 36
    lw_m = 24
    if direction in ("s", "n"):
        wx1, wx2 = cx0 - w/2, cx0 + w/2
        wy1, wy2 = cy0 - t_half, cy0 + t_half
        r_line(msp, wx1, wy1, wx2, wy1, layer="A-WINDOW", lw=lw_o)
        r_line(msp, wx1, wy2, wx2, wy2, layer="A-WINDOW", lw=lw_o)
        r_line(msp, wx1, wy1, wx1, wy2, layer="A-WINDOW", lw=lw_o)
        r_line(msp, wx2, wy1, wx2, wy2, layer="A-WINDOW", lw=lw_o)
        ml_cx = (wx1 + wx2) / 2.0
        ml1_y = wy1 + t_full*0.33
        ml2_y = wy1 + t_full*0.67
        r_line(msp, wx1, ml1_y, wx2, ml1_y, layer="A-WINDOW", lw=lw_m)
        r_line(msp, wx1, ml2_y, wx2, ml2_y, layer="A-WINDOW", lw=lw_m)
        r_line(msp, ml_cx, wy1, ml_cx, wy2, layer="A-WINDOW", lw=lw_m)
        for gx in range(5):
            gxi = wx1 + w*(gx+1)/6.0
            r_line(msp, gxi, wy1+1*IN, gxi, wy2-1*IN, layer="A-WINDOW", lw=14)
        r_text(msp, f"W {int(w/FT)}'-0\"", cx0, cy0 + 1.2*FT + t_half,
               h=TX_SMALL*FT, layer="A-WINDOW",
               align=TextEntityAlignment.MIDDLE_CENTER)
    else:
        wx1, wx2 = cx0 - t_half, cx0 + t_half
        wy1, wy2 = cy0 - w/2, cy0 + w/2
        r_line(msp, wx1, wy1, wx1, wy2, layer="A-WINDOW", lw=lw_o)
        r_line(msp, wx2, wy1, wx2, wy2, layer="A-WINDOW", lw=lw_o)
        r_line(msp, wx1, wy1, wx2, wy1, layer="A-WINDOW", lw=lw_o)
        r_line(msp, wx1, wy2, wx2, wy2, layer="A-WINDOW", lw=lw_o)
        ml_cy = (wy1 + wy2) / 2.0
        ml1_x = wx1 + t_full*0.33
        ml2_x = wx1 + t_full*0.67
        r_line(msp, ml1_x, wy1, ml1_x, wy2, layer="A-WINDOW", lw=lw_m)
        r_line(msp, ml2_x, wy1, ml2_x, wy2, layer="A-WINDOW", lw=lw_m)
        r_line(msp, wx1, ml_cy, wx2, ml_cy, layer="A-WINDOW", lw=lw_m)
        for gy in range(5):
            gyi = wy1 + w*(gy+1)/6.0
            r_line(msp, wx1+1*IN, gyi, wx2-1*IN, gyi, layer="A-WINDOW", lw=14)
        r_text(msp, f"W {int(w/FT)}'-0\"", cx0 + 1.2*FT + t_half, cy0,
               h=TX_SMALL*FT, layer="A-WINDOW", rot=90.0,
               align=TextEntityAlignment.MIDDLE_CENTER)


def r_ventilator(msp, cx0, cy0, size=2.5*FT, direction="s", label="V"):
    t_full = 10 * IN
    t_half = t_full / 2.0
    lw_o = 34
    lw_s = 20
    if direction in ("s", "n"):
        wx1, wx2 = cx0 - size/2, cx0 + size/2
        wy1, wy2 = cy0 - t_half, cy0 + t_half
        r_rect(msp, wx1, wy1, wx2, wy2, layer="A-WINDOW", lw=lw_o)
        slat_n = 9
        for s in range(slat_n):
            frac = (s + 0.5) / slat_n
            sy = wy1 + frac * (wy2 - wy1)
            r_line(msp, wx1 + 0.1*size, sy, wx2 - 0.1*size, sy,
                   layer="A-WINDOW", lw=lw_s)
        r_text(msp, label, cx0, cy0 - 1.6*FT,
               h=TX_MEDIUM*FT, layer="A-WINDOW",
               align=TextEntityAlignment.MIDDLE_CENTER)
        r_text(msp, "VENT", cx0, cy0 + 1.4*FT,
               h=TX_MICRO*FT, layer="A-WINDOW",
               align=TextEntityAlignment.MIDDLE_CENTER)
    else:
        wx1, wx2 = cx0 - t_half, cx0 + t_half
        wy1, wy2 = cy0 - size/2, cy0 + size/2
        r_rect(msp, wx1, wy1, wx2, wy2, layer="A-WINDOW", lw=lw_o)
        slat_n = 9
        for s in range(slat_n):
            frac = (s + 0.5) / slat_n
            sx = wx1 + frac * (wx2 - wx1)
            r_line(msp, sx, wy1 + 0.1*size, sx, wy2 - 0.1*size,
                   layer="A-WINDOW", lw=lw_s)
        r_text(msp, label, cx0 - 1.6*FT, cy0,
               h=TX_MEDIUM*FT, layer="A-WINDOW", rot=90.0,
               align=TextEntityAlignment.MIDDLE_CENTER)
        r_text(msp, "VENT", cx0 + 1.4*FT, cy0,
               h=TX_MICRO*FT, layer="A-WINDOW", rot=90.0,
               align=TextEntityAlignment.MIDDLE_CENTER)


def r_arch_dim_h(msp, x1, y, x2, txt, offset=1.2*FT):
    if x1 > x2: x1, x2 = x2, x1
    yd = y + offset
    r_line(msp, x1, yd, x2, yd, layer="A-DIM", lw=18)
    ext_gap = 0.25*FT if offset > 0 else -0.25*FT
    ext_over = 0.35*FT if offset > 0 else -0.35*FT
    r_line(msp, x1, y + ext_gap, x1, yd + ext_over, layer="A-DIM", lw=13)
    r_line(msp, x2, y + ext_gap, x2, yd + ext_over, layer="A-DIM", lw=13)
    ts = TX_DIM_TICK * FT
    r_line(msp, x1 - ts*0.5, yd - ts*0.5, x1 + ts*0.5, yd + ts*0.5, layer="A-DIM", lw=30)
    r_line(msp, x2 - ts*0.5, yd - ts*0.5, x2 + ts*0.5, yd + ts*0.5, layer="A-DIM", lw=30)
    ty = yd + 0.4*FT if offset >= 0 else yd - 0.6*FT
    r_text(msp, txt, (x1+x2)/2, ty, h=TX_DIM_TEXT*FT, layer="A-DIM",
           align=TextEntityAlignment.BOTTOM_CENTER if offset >= 0 else TextEntityAlignment.TOP_CENTER)


def r_arch_dim_v(msp, x, y1, y2, txt, offset=1.2*FT):
    if y1 > y2: y1, y2 = y2, y1
    xd = x + offset
    r_line(msp, xd, y1, xd, y2, layer="A-DIM", lw=18)
    ext_gap = 0.25*FT if offset > 0 else -0.25*FT
    ext_over = 0.35*FT if offset > 0 else -0.35*FT
    r_line(msp, x + ext_gap, y1, xd + ext_over, y1, layer="A-DIM", lw=13)
    r_line(msp, x + ext_gap, y2, xd + ext_over, y2, layer="A-DIM", lw=13)
    ts = TX_DIM_TICK * FT
    r_line(msp, xd - ts*0.5, y1 - ts*0.5, xd + ts*0.5, y1 + ts*0.5, layer="A-DIM", lw=30)
    r_line(msp, xd - ts*0.5, y2 - ts*0.5, xd + ts*0.5, y2 + ts*0.5, layer="A-DIM", lw=30)
    tx = xd + 0.45*FT if offset >= 0 else xd - 0.45*FT
    r_text(msp, txt, tx, (y1+y2)/2, h=TX_DIM_TEXT*FT, layer="A-DIM", rot=90.0,
           align=TextEntityAlignment.BOTTOM_CENTER if offset >= 0 else TextEntityAlignment.TOP_CENTER)


def draw_building_envelope(msp):
    pts = list(ENV_PTS)
    rpts = [rotate_pt(p[0], p[1], ROT_CX, ROT_CY, ROT_DEG) for p in pts]
    polyline(msp, rpts, layer="A-WALL", lw=55, closed=True)
    inner = [
        (X(0)    + OWT, Y(5)    + OWT),
        (X(30)   - OWT, Y(5)    + OWT),
        (X(30)   - OWT, Y(21.5) - OWT),
        (X(55)   - OWT, Y(21.5) - OWT),
        (X(55)   - OWT, Y(93)   - OWT),
        (X(0)    + OWT, Y(93)   - OWT),
    ]
    rpts_i = [rotate_pt(p[0], p[1], ROT_CX, ROT_CY, ROT_DEG) for p in inner]
    polyline(msp, rpts_i, layer="A-WALL", lw=35, closed=True)
    try:
        for i in range(len(pts)):
            p1 = pts[i]; p2 = pts[(i+1) % len(pts)]
            ip1 = inner[i]; ip2 = inner[(i+1) % len(inner)]
            r1 = rotate_pt(p1[0], p1[1], ROT_CX, ROT_CY, ROT_DEG)
            r2 = rotate_pt(p2[0], p2[1], ROT_CX, ROT_CY, ROT_DEG)
            ri1 = rotate_pt(ip1[0], ip1[1], ROT_CX, ROT_CY, ROT_DEG)
            ri2 = rotate_pt(ip2[0], ip2[1], ROT_CX, ROT_CY, ROT_DEG)
            h = msp.add_hatch(color=8, dxfattribs={"layer": "A-HATCH"})
            h.set_pattern_fill("ANSI31", scale=0.8)
            h.paths.add_polyline_path([r1, r2, ri2, ri1], is_closed=True)
    except Exception:
        pass


def draw_column_grid(msp):
    col_x = [0, 15, 30, 45, 55]
    col_y = [5, 11.5, 30, 50, 70, 93]
    for cx in col_x:
        if cx <= 30:
            y1, y2 = 5, 93
        else:
            y1, y2 = 21.5, 93
        r_line(msp, X(cx), Y(y1), X(cx), Y(y2), layer="A-GRID", lw=13)
        r_text(msp, f"C-{cx}'", X(cx), Y(93) + 1.5*FT, h=TX_MEDIUM*FT, layer="A-GRID",
               align=TextEntityAlignment.MIDDLE_CENTER)
    for cy in col_y:
        if cy <= 5 or cy > 21.5:
            x2 = 55
        else:
            x2 = 30
        r_line(msp, X(0), Y(cy), X(x2), Y(cy), layer="A-GRID", lw=13)
        r_text(msp, f"R-{cy}'", X(0) - 1.5*FT, Y(cy), h=TX_MEDIUM*FT, layer="A-GRID", rot=90.0,
               align=TextEntityAlignment.MIDDLE_CENTER)
    col_sz = 12 * IN
    for cx in col_x:
        for cy in col_y:
            if cx > 30 and cy < 21.5:
                continue
            bx = X(cx) - col_sz/2
            by = Y(cy) - col_sz/2
            r_fill_rect(msp, bx, by, bx + col_sz, by + col_sz, hatch="SOLID", layer="A-COLUMN")
            r_rect(msp, bx, by, bx + col_sz, by + col_sz, layer="A-COLUMN", lw=30)


def draw_directions(msp):
    r_text(msp, "SOUTH - PUBLIC ENTRY", X(27.5), Y(5) - 4*FT, h=TX_XL*FT, layer="A-TEXT-TTL",
           align=TextEntityAlignment.MIDDLE_CENTER)
    r_text(msp, "NORTH", X(27.5), Y(93) + 1.5*FT, h=TX_LARGE*FT, layer="A-TEXT-TTL",
           align=TextEntityAlignment.MIDDLE_CENTER)
    r_text(msp, "WEST", X(0) - 4*FT, Y(49), h=TX_LARGE*FT, layer="A-TEXT-TTL", rot=90.0,
           align=TextEntityAlignment.MIDDLE_CENTER)
    r_text(msp, "EAST - VIP PORTICO", X(55) + 4*FT, Y(49), h=TX_XL*FT, layer="A-TEXT-TTL", rot=90.0,
           align=TextEntityAlignment.MIDDLE_CENTER)


def draw_south_portico(msp):
    px1 = X(0) - 1 * FT
    px2 = X(30) + 1 * FT
    py1 = Y(5) - 5 * FT
    py2 = Y(5)
    r_rect(msp, px1, py1, px2, py2, layer="A-SITE", lw=30)
    r_fill_rect(msp, px1, py1, px2, py2, hatch="GRATE", layer="A-BAY")
    for p in range(5):
        cx = px1 + (px2 - px1) * (p + 1) / 6.0
        col_bx = cx - 6 * IN
        col_by = py1 + 6 * IN
        r_fill_rect(msp, col_bx, col_by, col_bx + 12*IN, col_by + 12*IN, hatch="SOLID", layer="A-COLUMN")
        r_rect(msp, col_bx, col_by, col_bx + 12*IN, col_by + 12*IN, layer="A-COLUMN", lw=28)
    r_text(msp, "PUBLIC ENTRY PORTICO", (px1+px2)/2, (py1+py2)/2, h=TX_LARGE*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)


def draw_east_portico(msp):
    px1 = X(55)
    px2 = X(55) + 5 * FT
    py1 = Y(28)
    py2 = Y(62)
    r_rect(msp, px1, py1, px2, py2, layer="A-SITE", lw=30)
    r_fill_rect(msp, px1, py1, px2, py2, hatch="GRATE", layer="A-BAY")
    num_cols = 5
    for p in range(num_cols):
        cy = py1 + (py2 - py1) * (p + 0.5) / num_cols
        col_bx = px1 + 2.0 * FT - 6 * IN
        col_by = cy - 6 * IN
        r_fill_rect(msp, col_bx, col_by, col_bx + 12*IN, col_by + 12*IN, hatch="SOLID", layer="A-COLUMN")
        r_rect(msp, col_bx, col_by, col_bx + 12*IN, col_by + 12*IN, layer="A-COLUMN", lw=28)
    r_text(msp, "VIP PORTICO", (px1+px2)/2, (py1+py2)/2, h=TX_XL*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER, rot=90.0)


def r_stair_dogleg(msp, ox, oy):
    s = public_stair_dogleg.__wrapped__ if hasattr(public_stair_dogleg, "__wrapped__") else None
    w_ft = 9.0
    length_ft = 33.0
    flight_risers = 13
    tread_in = 12.0
    w = w_ft * FT
    L = length_ft * FT
    tread = tread_in * IN
    riser_count = flight_risers
    flight_run = riser_count * tread
    bottom_land_depth = (L - 2 * flight_run - w) / 2.0
    mid_land_d = w
    top_land_depth = bottom_land_depth
    fl1_y0 = oy + bottom_land_depth
    fl1_y1 = fl1_y0 + flight_run
    mid_y0 = fl1_y1
    mid_y1 = mid_y0 + mid_land_d
    fl2_y0 = mid_y1
    fl2_y1 = fl2_y0 + flight_run
    r_rect(msp, ox, oy, ox + w, oy + L, layer="A-WALL", lw=40)
    r_fill_rect(msp, ox, oy, ox + w, oy + bottom_land_depth, hatch="ANSI32", layer="A-HATCH")
    r_text(msp, "GF LANDING", ox + w/2, oy + bottom_land_depth/2, h=TX_SMALL*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)
    r_fill_rect(msp, ox, mid_y0, ox + w, mid_y1, hatch="ANSI32", layer="A-HATCH")
    r_text(msp, "MID LANDING", ox + w/2, (mid_y0+mid_y1)/2, h=TX_SMALL*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)
    r_fill_rect(msp, ox, fl2_y1, ox + w, oy + L, hatch="ANSI32", layer="A-HATCH")
    r_text(msp, "FF LANDING", ox + w/2, fl2_y1 + top_land_depth/2, h=TX_SMALL*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)
    partition_x = ox + 4.5 * FT
    f1x0, f1x1 = ox, ox + 4 * FT
    for i in range(riser_count + 1):
        y_ = fl1_y0 + i * tread
        r_line(msp, f1x0, y_, f1x1, y_, layer="A-WALL", lw=22)
    r_line(msp, f1x0, fl1_y0, f1x0, fl1_y1, layer="A-ACC", lw=22)
    r_line(msp, partition_x, fl1_y0, partition_x, fl1_y1, layer="A-ACC", lw=22)
    f2x0, f2x1 = ox + 5 * FT, ox + w
    for i in range(riser_count + 1):
        y_ = fl2_y0 + i * tread
        r_line(msp, f2x0, y_, f2x1, y_, layer="A-WALL", lw=22)
    r_line(msp, f2x1, fl2_y0, f2x1, fl2_y1, layer="A-ACC", lw=22)
    r_line(msp, partition_x, fl2_y0, partition_x, fl2_y1, layer="A-ACC", lw=22)
    arr_mid_y = (fl1_y0 + fl1_y1) / 2
    r_line(msp, ox + 2*FT, fl1_y0 + 12*IN, ox + 2*FT, fl1_y1 - 12*IN, layer="A-SECT-CUT", lw=26)
    r_line(msp, ox + 2*FT, fl1_y1 - 12*IN, ox + 2*FT - 8*IN, fl1_y1 - 20*IN, layer="A-SECT-CUT", lw=26)
    r_line(msp, ox + 2*FT, fl1_y1 - 12*IN, ox + 2*FT + 8*IN, fl1_y1 - 20*IN, layer="A-SECT-CUT", lw=26)
    r_text(msp, "UP", ox + 2*FT, arr_mid_y, h=TX_LARGE*FT, layer="A-SECT-CUT",
           align=TextEntityAlignment.MIDDLE_CENTER)
    arr2_mid_y = (fl2_y0 + fl2_y1) / 2
    r_line(msp, ox + 7*FT, fl2_y1 - 12*IN, ox + 7*FT, fl2_y0 + 12*IN, layer="A-SECT-CUT", lw=26)
    r_line(msp, ox + 7*FT, fl2_y0 + 12*IN, ox + 7*FT - 8*IN, fl2_y0 + 20*IN, layer="A-SECT-CUT", lw=26)
    r_line(msp, ox + 7*FT, fl2_y0 + 12*IN, ox + 7*FT + 8*IN, fl2_y0 + 20*IN, layer="A-SECT-CUT", lw=26)
    r_text(msp, "DOWN", ox + 7*FT, arr2_mid_y, h=TX_LARGE*FT, layer="A-SECT-CUT",
           align=TextEntityAlignment.MIDDLE_CENTER)
    r_text(msp, f"STAIR 9'W  2x13R  12\"T  6.8\"R", ox + w/2, oy - 2.0*FT, h=TX_SMALL*FT,
           layer="A-TEXT", align=TextEntityAlignment.MIDDLE_CENTER)


def draw_ground_floor():
    doc, msp = setup_doc(sheet_w=SH, sheet_h=SW, config=config)

    draw_directions(msp)
    draw_south_portico(msp)
    draw_east_portico(msp)
    draw_building_envelope(msp)
    draw_column_grid(msp)

    # ===== SOUTH WING Y=5..21.5 =====
    # Entry Lobby: Y=5..13
    lx1, lx2 = X(0) + OWT, X(30) - OWT
    ly1, ly2 = Y(5) + OWT, Y(13) - IWT/2
    r_fill_rect(msp, lx1, ly1, lx2, ly2, hatch="GRATE", layer="A-BAY")
    r_text(msp, "ENTRY LOBBY", (lx1+lx2)/2, (ly1+ly2)/2, h=TX_XL*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)

    # Lobby double door (south) from portico
    dd_cx = (lx1+lx2)/2
    r_door_swing(msp, dd_cx - 4*FT, ly1, 4*FT, swing_dir=1)
    r_door_swing(msp, dd_cx, ly1, 4*FT, swing_dir=-1)
    r_text(msp, "MAIN ENTRY 2x4'-0\"", dd_cx, ly1 - 2*FT, h=TX_SMALL*FT,
           layer="A-DOOR", align=TextEntityAlignment.MIDDLE_CENTER)

    # Lobby -> north corridor double door
    r_door_swing(msp, dd_cx - 3*FT, ly2 - 3*FT, 3*FT, swing_dir=1)
    r_door_swing(msp, dd_cx, ly2 - 3*FT, 3*FT, swing_dir=-1)

    # SOUTH WING: Y=13..21.5 (8.5' deep zone below L-step)
    # Bar Office: X=0..15, Y=13..21.5
    bo_x1, bo_x2 = X(0) + OWT, X(15) - IWT/2
    bo_y1, bo_y2 = Y(13) + IWT/2, Y(21.5) - OWT
    r_rect(msp, bo_x1, bo_y1, bo_x2, bo_y2, layer="A-WALL", lw=32)
    r_text(msp, "BAR OFFICE\n15' x 8.5'", (bo_x1+bo_x2)/2, (bo_y1+bo_y2)/2, h=TX_LARGE*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)
    r_rect(msp, bo_x1 + 1*FT, bo_y1 + 1*FT, bo_x2 - 1*FT, bo_y1 + 3*FT, layer="A-FURN", lw=18)
    r_text(msp, "WORK DESK", (bo_x1+bo_x2)/2, bo_y1 + 2*FT, h=TX_SMALL*FT,
           layer="A-FURN", align=TextEntityAlignment.MIDDLE_CENTER)
    r_door_swing(msp, bo_x2 - 3*FT, bo_y1, 3*FT, swing_dir=1)
    r_window(msp, (bo_x1+bo_x2)/2, Y(21.5) - OWT/2, 5*FT, direction="n")

    # Common Toilet (Lawyers) : X=15..30, Y=13..21.5
    ct_x1, ct_x2 = X(15) + IWT/2, X(30) - OWT
    ct_y1, ct_y2 = Y(13) + IWT/2, Y(21.5) - OWT
    r_rect(msp, ct_x1, ct_y1, ct_x2, ct_y2, layer="A-WALL", lw=32)
    # Male: X=15..22.5 (7.5' wide), Female: X=22.5..30 (7.5' wide)
    mx1, mx2 = ct_x1, ct_x1 + (ct_x2-ct_x1)*0.5 - IWT/2
    fx1, fx2 = ct_x1 + (ct_x2-ct_x1)*0.5 + IWT/2, ct_x2
    r_line(msp, (mx1+mx2+fx1+fx2)/4 - 1, ct_y1, (mx1+mx2+fx1+fx2)/4 - 1, ct_y2, layer="A-WALL", lw=28)

    # Male Toilet: 5 urinals + 2 WCs
    r_text(msp, "MALE", (mx1+mx2)/2, ct_y2 - 1*FT, h=TX_LARGE*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)
    # 5 Urinals along north wall
    for u in range(5):
        ux = mx1 + 0.6*FT + u * ((mx2-mx1) - 1.2*FT) / 5.0
        r_rect(msp, ux, ct_y2 - 2.2*FT, ux + 1.2*FT, ct_y2 - 0.4*FT, layer="A-FURN", lw=14)
    # 2 WC cubicles along west side (south half)
    wc_w = (mx2 - mx1 - IWT) / 2.0
    for i in range(2):
        wcx1 = mx1 + i * (wc_w + IWT/2)
        wcx2 = wcx1 + wc_w
        r_rect(msp, wcx1, ct_y1, wcx2, ct_y1 + 5*FT, layer="A-WALL", lw=22)
        r_rect(msp, wcx2 - 1.8*FT, ct_y1 + 0.6*FT, wcx2 - 0.5*FT, ct_y1 + 1.8*FT, layer="A-FURN", lw=12)
    # 2 Wash basins
    for i in range(2):
        bx = mx1 + 1.2*FT + i * ((mx2-mx1)-2.4*FT)/1.0
        bx = (mx1+mx2)/2
        by_ = ct_y1 + 7*FT + i*0.01
        r_circle(msp, bx, ct_y1 + 6.5*FT, 0.55*FT, layer="A-FURN", lw=14)
    # Entry door male: south wall east side
    r_door_swing(msp, mx2 - 3*FT - 0.5*FT, ct_y1, 2.75*FT, swing_dir=1)

    # Female Toilet: 3 WCs + 2 basins
    r_text(msp, "FEMALE", (fx1+fx2)/2, ct_y2 - 1*FT, h=TX_LARGE*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)
    fw = (fx2 - fx1 - IWT) / 3.0
    for i in range(3):
        fcx1 = fx1 + i * (fw + IWT/3)
        fcx2 = fcx1 + fw
        r_rect(msp, fcx1, ct_y1 + 2*FT, fcx2, ct_y2 - 2.5*FT, layer="A-WALL", lw=22)
        r_rect(msp, fcx2 - 1.8*FT, ct_y2 - 4.2*FT, fcx2 - 0.5*FT, ct_y2 - 3*FT, layer="A-FURN", lw=12)
        r_door_swing(msp, fcx2 - 2*FT, ct_y1 + 2*FT, 2*FT, swing_dir=-1)
    # 2 Basins south side
    for i in range(2):
        r_circle(msp, fx1 + 1.8*FT + i*(fx2-fx1-3.6*FT), ct_y1 + 1*FT, 0.5*FT, layer="A-FURN", lw=14)
    # Entry door female: south wall west side
    r_door_swing(msp, fx1 + 0.5*FT, ct_y1, 2.75*FT, swing_dir=-1)

    # =========================================================
    # GF EXTERIOR WINDOWS - SOUTH WALL (Y=5, X=0..30) 5 WINDOWS
    # =========================================================
    for sw in [(5, 5), (12, 5), (18, 5), (24, 5), (28, 5)]:
        r_window(msp, X(sw[0]), Y(5) + OWT/2, 5*FT, direction="s")
    # =========================================================
    # GF EXTERIOR WINDOWS - SOUTH WING EAST WALL (X=30, Y=5..21.5) 2 WINDOWS
    # =========================================================
    for ew in [(9, "e"), (18, "e")]:
        r_window(msp, X(30) - OWT/2, Y(ew[0]), 5*FT, direction="e")

    # ===== E-W CORRIDOR Y=21.5..25.5 (4' wide) =====
    cx1, cx2 = X(0) + OWT, X(55) - OWT
    cy1, cy2 = Y(21.5) + IWT/2, Y(25.5) - IWT/2
    r_fill_rect(msp, cx1, cy1, cx2, cy2, hatch="GRATE", layer="A-BAY")
    r_text(msp, "CORRIDOR 4'-0\"", X(27.5), (cy1+cy2)/2, h=TX_XL*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)

    # ===== EAST SIDE: VIP DOOR from VIP Portico (X=55..60, Y=28..62) into circulation zone =====
    # Enter building through east envelope at X=55, landing in the X=46..55 stair/circulation
    # band (south of stair flight, below Y=28 area). Door opens inward (swing -1) into zone.
    vx, vy = X(55) - OWT, Y(32)
    r_door_swing(msp, vx, vy - 2*FT, 4*FT, swing_dir=-1)
    r_text(msp, "VIP ENTRY 4'-0\"", vx - 5.5*FT, vy, h=TX_SMALL*FT,
           layer="A-DOOR", align=TextEntityAlignment.MIDDLE_CENTER, rot=90.0)

    # ===== STAIR: X=46..55, Y=21.5..54.5 (9'x33') =====
    stair_ox = X(46) + IWT/2
    stair_oy = Y(21.5) + IWT/2
    r_stair_dogleg(msp, stair_ox, stair_oy)
    # Stair entry door from corridor
    s_ex = stair_ox + 9*FT
    s_ey = stair_oy + 33*FT
    # South door (bottom landing entry from corridor)
    r_door_swing(msp, stair_ox + (s_ex - stair_ox)/2 - 1.5*FT, stair_oy, 3*FT, swing_dir=1)
    # North exit door from stair to north circulation
    r_door_swing(msp, stair_ox + (s_ex - stair_ox)/2 - 1.5*FT, s_ey - 3*FT, 3*FT, swing_dir=-1)

    # ===== WEST SIDE ROOMS off corridor: RPwD Accessible WC + Storage =====
    # RPwD AWC: X=0..8, Y=25.5..32
    awc_x1, awc_x2 = X(0) + OWT, X(8) - IWT/2
    awc_y1, awc_y2 = Y(25.5) + IWT/2, Y(32) - IWT/2
    r_rect(msp, awc_x1, awc_y1, awc_x2, awc_y2, layer="A-ACC", lw=32)
    r_circle(msp, (awc_x1+awc_x2)/2, (awc_y1+awc_y2)/2, 2.5*FT, layer="A-JALI", lw=18)
    r_text(msp, "5' TURN\nRPwD WC", (awc_x1+awc_x2)/2, (awc_y1+awc_y2)/2, h=TX_SMALL*FT,
           layer="A-ACC", align=TextEntityAlignment.MIDDLE_CENTER)
    r_rect(msp, awc_x2 - 2.4*FT, awc_y1 + 0.8*FT, awc_x2 - 0.8*FT, awc_y1 + 2.2*FT, layer="A-FURN", lw=16)
    r_circle(msp, awc_x1 + 1.8*FT, awc_y2 - 1.6*FT, 0.6*FT, layer="A-FURN", lw=16)
    r_door_swing(msp, awc_x2 - 3*FT, awc_y1, 3*FT, swing_dir=1)
    r_text(msp, "RPwD ACCESSIBLE WC", (awc_x1+awc_x2)/2, awc_y2 + 0.8*FT, h=TX_SMALL*FT,
           layer="A-ACC", align=TextEntityAlignment.MIDDLE_CENTER)

    # ===== MAIN HALL (Audience chairs only, NO tables) X=0..46, Y=25.5..75 =====
    mhx1, mhy1 = X(0) + OWT, Y(25.5) + IWT/2
    mhx2, mhy2 = X(46) - IWT/2, Y(75) - IWT/2
    r_rect(msp, mhx1, mhy1, mhx2, mhy2, layer="A-WALL", lw=32)
    r_text(msp, "MAIN HALL\nAUDIENCE", (mhx1+mhx2)/2, mhy2 - 4*FT, h=TX_XXL*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)

    # Central 4' Aisle N-S
    aisle_cx = (mhx1 + mhx2) / 2
    aisle_w = 4 * FT
    r_line(msp, aisle_cx - aisle_w/2, mhy1, aisle_cx - aisle_w/2, mhy2, layer="A-BAY", lw=16)
    r_line(msp, aisle_cx + aisle_w/2, mhy1, aisle_cx + aisle_w/2, mhy2, layer="A-BAY", lw=16)
    r_text(msp, "CENTRAL AISLE 4'", aisle_cx, (mhy1+mhy2)/2, h=TX_LARGE*FT,
           layer="A-TEXT-TTL", rot=90.0, align=TextEntityAlignment.MIDDLE_CENTER)

    # Audience Chairs ONLY (no tables) - 12 rows x ~24 chairs per side
    num_rows = 12
    row_start = mhy1 + 3 * FT
    row_end = mhy2 - 8 * FT
    row_gap = (row_end - row_start) / (num_rows - 1)
    seat_dia = 0.5 * FT
    for r in range(num_rows):
        ry = row_start + r * row_gap
        # Left side chairs
        left_x_start = mhx1 + 1.8 * FT
        left_x_end = aisle_cx - aisle_w/2 - 1.2 * FT
        num_left = int((left_x_end - left_x_start) / (2.2 * FT))
        for c in range(num_left):
            cx_ = left_x_start + c * 2.2 * FT
            r_circle(msp, cx_, ry, seat_dia, layer="A-FURN", lw=14)
        # Right side chairs
        right_x_end = mhx2 - 1.8 * FT
        right_x_start = aisle_cx + aisle_w/2 + 1.2 * FT
        num_right = int((right_x_end - right_x_start) / (2.2 * FT))
        for c in range(num_right):
            cx_ = right_x_start + c * 2.2 * FT
            r_circle(msp, cx_, ry, seat_dia, layer="A-FURN", lw=14)
        r_text(msp, f"R{r+1:02d}", mhx1 + 0.6*FT, ry, h=TX_SMALL*FT, layer="A-BAY")

    # Hall entry doors from corridor (south wall): 2 pairs
    hsw1_h = X(10) + 0.5*FT
    r_door_swing(msp, hsw1_h, mhy1, 4*FT, swing_dir=1)
    r_door_swing(msp, hsw1_h + 4*FT, mhy1, 4*FT, swing_dir=-1)
    r_text(msp, "ENTRY 1  2x4'-0\"", hsw1_h + 4*FT, mhy1 + 2.5*FT, h=TX_SMALL*FT,
           layer="A-DOOR", align=TextEntityAlignment.MIDDLE_CENTER)
    hsw2_h = X(32) + 0.5*FT
    r_door_swing(msp, hsw2_h, mhy1, 4*FT, swing_dir=1)
    r_door_swing(msp, hsw2_h + 4*FT, mhy1, 4*FT, swing_dir=-1)
    r_text(msp, "ENTRY 2  2x4'-0\"", hsw2_h + 4*FT, mhy1 + 2.5*FT, h=TX_SMALL*FT,
           layer="A-DOOR", align=TextEntityAlignment.MIDDLE_CENTER)

    # Hall exit door on WEST wall? No, west is 0' setback (blank). Exit on EAST wall:
    egress_w = 4 * FT
    r_door_swing(msp, mhx2, Y(40) - egress_w/2, egress_w, swing_dir=1)
    r_text(msp, "EXIT 4'-0\"", mhx2 - 5.5*FT, Y(40), h=TX_SMALL*FT,
           layer="A-DOOR", align=TextEntityAlignment.MIDDLE_CENTER)
    r_door_swing(msp, mhx2, Y(60) - egress_w/2, egress_w, swing_dir=1)

    # =========================================================
    # GF EXTERIOR WINDOWS - MAIN EAST WALL (X=55, Y=21.5..93) 9 WINDOWS
    # =========================================================
    for yf in [25, 32, 40, 48, 56, 64, 72, 82, 90]:
        r_window(msp, X(55) - OWT/2, Y(yf), 6*FT, direction="e")
    # West: no windows (0' setback per plot)

    # =========================================================
    # GF NORTH ZONE (Y=75..93 above Main Hall back wall)
    #   X=0..16  President Chamber (16'x12')  +  Attached Toilet (Y=75..81)
    #   X=16..31 Secretary Chamber (15'x12') +  Attached Toilet (Y=75..81)
    #   X=31..46 Revised Dais + Rostrum (15'x18') raised +1'-6"
    #   X=46..55 Stacked above Stair (GF stair Y=21.5..54.5); above reserved
    # Access corridor band: Y=75..81 (connects toilet/annex vestibules + dais rear)
    # =========================================================

    # PRESIDENT CHAMBER + ATTACHED TOILET (X=0..16, Y=81..93 = 16'x12')
    pc_x1, pc_x2 = X(0) + OWT, X(16) - IWT/2
    pc_y1, pc_y2 = Y(81) + IWT/2, Y(93) - OWT
    r_rect(msp, pc_x1, pc_y1, pc_x2, pc_y2, layer="A-WALL", lw=35)
    r_text(msp, "PRESIDENT CHAMBER\n16' x 12'", (pc_x1+pc_x2)/2, (pc_y1+pc_y2)/2 + 1*FT, h=TX_XL*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)
    # President desk
    r_rect(msp, pc_x1 + 1.5*FT, pc_y2 - 4.5*FT, pc_x2 - 1.5*FT, pc_y2 - 1.5*FT, layer="A-FURN", lw=22)
    r_text(msp, "DESK 13'x3'", (pc_x1+pc_x2)/2, pc_y2 - 3*FT, h=TX_SMALL*FT,
           layer="A-FURN", align=TextEntityAlignment.MIDDLE_CENTER)
    r_circle(msp, (pc_x1+pc_x2)/2, pc_y2 - 5.2*FT, 0.5*FT, layer="A-FURN", lw=18)
    # Visitor seating (sofa)
    r_rect(msp, pc_x1 + 1.5*FT, pc_y1 + 1.5*FT, pc_x1 + 8*FT, pc_y1 + 3.5*FT, layer="A-FURN", lw=18)
    r_text(msp, "SOFA", (pc_x1 + 4.75*FT), pc_y1 + 2.5*FT, h=TX_SMALL*FT, layer="A-FURN",
           align=TextEntityAlignment.MIDDLE_CENTER)
    # Chamber entry door (SOUTH wall):
    r_door_swing(msp, pc_x2 - 3*FT - 1*FT, pc_y1, 3*FT, swing_dir=1)
    r_window(msp, (pc_x1+pc_x2)/2, Y(93) - OWT/2, 6*FT, direction="n")

    # PRESIDENT ATTACHED TOILET: X=0..9, Y=75..81 (9'x6')
    pt_x1, pt_x2 = X(0) + OWT, X(9) - IWT/2
    pt_y1, pt_y2 = Y(75) + IWT/2, Y(81) - IWT/2
    r_rect(msp, pt_x1, pt_y1, pt_x2, pt_y2, layer="A-WALL", lw=30)
    r_rect(msp, pt_x2 - 2.4*FT, pt_y1 + 1*FT, pt_x2 - 0.8*FT, pt_y1 + 2.4*FT, layer="A-FURN", lw=16)
    r_circle(msp, pt_x1 + 1.8*FT, pt_y2 - 1.2*FT, 0.5*FT, layer="A-FURN", lw=16)
    r_circle(msp, (pt_x1+pt_x2)/2, (pt_y1+pt_y2)/2, 2.2*FT, layer="A-JALI", lw=14)
    r_text(msp, "ATT. TOILET", (pt_x1+pt_x2)/2, pt_y2 + 0.6*FT, h=TX_SMALL*FT, layer="A-ACC",
           align=TextEntityAlignment.MIDDLE_CENTER)
    # Interconnecting door from president chamber -> toilet on north wall
    r_door_swing(msp, pt_x2 - 3*FT - 0.2*FT, pt_y2, 2.75*FT, swing_dir=1)
    # Also external access door on EAST wall of toilet (optional, for corridor access)
    r_door_swing(msp, pt_x2, pt_y1 + 1.5*FT, 2.75*FT, swing_dir=-1)

    # SECRETARY CHAMBER + ATTACHED TOILET (X=16..31, Y=81..93 = 15'x12')
    sc_x1, sc_x2 = X(16) + IWT/2, X(31) - IWT/2
    sc_y1, sc_y2 = Y(81) + IWT/2, Y(93) - OWT
    r_rect(msp, sc_x1, sc_y1, sc_x2, sc_y2, layer="A-WALL", lw=35)
    r_text(msp, "SECRETARY CHAMBER\n15' x 12'", (sc_x1+sc_x2)/2, (sc_y1+sc_y2)/2 + 1*FT, h=TX_XL*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)
    r_rect(msp, sc_x1 + 1.5*FT, sc_y2 - 4.5*FT, sc_x2 - 1.5*FT, sc_y2 - 1.5*FT, layer="A-FURN", lw=22)
    r_circle(msp, (sc_x1+sc_x2)/2, sc_y2 - 5.2*FT, 0.5*FT, layer="A-FURN", lw=18)
    r_door_swing(msp, sc_x1 + 1*FT, sc_y1, 3*FT, swing_dir=1)
    r_window(msp, (sc_x1+sc_x2)/2, Y(93) - OWT/2, 6*FT, direction="n")

    # SECRETARY ATTACHED TOILET: X=22..31, Y=75..81 (9'x6')
    st_x1, st_x2 = X(22) + IWT/2, X(31) - IWT/2
    st_y1, st_y2 = Y(75) + IWT/2, Y(81) - IWT/2
    r_rect(msp, st_x1, st_y1, st_x2, st_y2, layer="A-WALL", lw=30)
    r_rect(msp, st_x2 - 2.4*FT, st_y1 + 1*FT, st_x2 - 0.8*FT, st_y1 + 2.4*FT, layer="A-FURN", lw=16)
    r_circle(msp, st_x1 + 1.8*FT, st_y2 - 1.2*FT, 0.5*FT, layer="A-FURN", lw=16)
    r_text(msp, "ATT. TOILET", (st_x1+st_x2)/2, st_y2 + 0.6*FT, h=TX_SMALL*FT, layer="A-ACC",
           align=TextEntityAlignment.MIDDLE_CENTER)
    # Interconnecting door from secretary chamber -> toilet
    r_door_swing(msp, st_x2 - 3*FT - 0.2*FT, st_y2, 2.75*FT, swing_dir=1)
    # Also door from corridor into toilet on south
    r_door_swing(msp, st_x1 + 0.3*FT, st_y1, 2.75*FT, swing_dir=-1)

    # Circulation corridor E-W connecting chambers + hall back corridor
    # Access corridor Y=75..81 between toilets and rest of building
    ac_x1, ac_x2 = X(31) + IWT/2, X(46) - IWT/2
    ac_y1, ac_y2 = Y(75) + IWT/2, Y(81) - IWT/2
    r_fill_rect(msp, ac_x1, ac_y1, ac_x2, ac_y2, hatch="GRATE", layer="A-BAY")
    r_text(msp, "ACCESS CORRIDOR", (ac_x1+ac_x2)/2, (ac_y1+ac_y2)/2, h=TX_LARGE*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER, rot=90.0)

    # REVISED DAIS: X=31..46, Y=75..93 (15'x18')
    rdx1, rdy1 = X(31) + IWT/2, Y(75) + IWT/2
    rdx2, rdy2 = X(46) - IWT/2, Y(93) - OWT
    r_fill_rect(msp, rdx1, rdy1, rdx2, rdy2, hatch="ANSI32", layer="A-HATCH")
    r_rect(msp, rdx1, rdy1, rdx2, rdy2, layer="A-WALL", lw=35)
    for s in range(3):
        sy_ = rdy1 + (s+1)*0.5*FT
        r_line(msp, rdx1 + 0.5*FT, sy_, rdx2 - 0.5*FT, sy_, layer="A-SECT-CUT", lw=18)
    rdw2, rdd2 = 12*FT, 3*FT
    rx1, ry1 = (rdx1+rdx2)/2 - rdw2/2, rdy2 - 6.5*FT
    rx2, ry2 = rx1 + rdw2, ry1 + rdd2
    r_rect(msp, rx1, ry1, rx2, ry2, layer="A-FURN", lw=26)
    r_text(msp, "ROSTRUM", (rx1+rx2)/2, (ry1+ry2)/2, h=TX_LARGE*FT, layer="A-FURN",
           align=TextEntityAlignment.MIDDLE_CENTER)
    r_circle(msp, (rx1+rx2)/2, ry2 + 1.2*FT, 0.55*FT, layer="A-FURN", lw=18)
    r_door_swing(msp, rdx1 + 1*FT, rdy1, 3*FT, swing_dir=1)
    r_window(msp, (rdx1+rdx2)/2, Y(93) - OWT/2, 5*FT, direction="n")

    # =========================================================
    # GF EXTERIOR WINDOWS - NORTH WALL (Y=93, X=0..55) 8 WINDOWS
    # =========================================================
    for xf in [5, 13, 21, 29, 36, 43, 49, 53]:
        r_window(msp, X(xf), Y(93) - OWT/2, 6*FT, direction="n")

    # =========================================================
    # GF VENTILATORS (every toilet / pantry / service room)
    # =========================================================
    # V1 = Male Common Toilet (X~15..22.5) - SOUTH wall
    r_ventilator(msp, X(18.75), Y(5) + OWT/2, size=2.5*FT, direction="s", label="V1")
    # V2 = Female Common Toilet (X~22.5..30) - SOUTH wall
    r_ventilator(msp, X(26.25), Y(5) + OWT/2, size=2.5*FT, direction="s", label="V2")
    # V3 = RPwD Accessible WC (X=0..8) - SOUTH wall near lobby
    r_ventilator(msp, X(4), Y(5) + OWT/2, size=2.5*FT, direction="s", label="V3")
    # V4 = President Attached Toilet (X=0..9, Y=75..81) - NORTH wall
    r_ventilator(msp, X(4.5), Y(93) - OWT/2, size=2.5*FT, direction="n", label="V4")
    # V5 = Secretary Attached Toilet (X=22..31, Y=75..81) - NORTH wall
    r_ventilator(msp, X(26.5), Y(93) - OWT/2, size=2.5*FT, direction="n", label="V5")
    # V6 = Bar Office (X=0..15, Y=13..21.5) - SOUTH wall
    r_ventilator(msp, X(7.5), Y(5) + OWT/2, size=2.5*FT, direction="s", label="V6")
    # V7 = Common Toilet Air - EAST wall south wing
    r_ventilator(msp, X(30) - OWT/2, Y(13), size=2.5*FT, direction="e", label="V7")

    # Dimensions
    r_arch_dim_h(msp, X(0), Y(1) - 1*FT, X(30), "30'-0\"", offset=-1.2*FT)
    r_arch_dim_h(msp, X(0), Y(1) - 3*FT, X(55), "55'-0\" OVERALL", offset=-1.2*FT)
    r_arch_dim_h(msp, X(30), Y(1) - 1*FT, X(55), "25'-0\"", offset=-1.2*FT)
    r_arch_dim_v(msp, X(0) - 1*FT, Y(5), Y(21.5), "16'-6\"", offset=-1.2*FT)
    r_arch_dim_v(msp, X(0) - 3*FT, Y(5), Y(93), "88'-0\" OVERALL", offset=-1.2*FT)
    r_arch_dim_v(msp, X(55) + 0.5*FT, Y(21.5), Y(93), "71'-6\"", offset=1.0*FT)

    # Area Schedule GF only (SIMPLE)
    sx, sy = X(55) + 8*FT, Y(75)
    r_text(msp, "AREA SCHEDULE GF", sx, sy + 7*FT, h=TX_XL*FT, layer="A-TEXT-TTL", align=TextEntityAlignment.LEFT)
    areas = [
        ("President Chamber + Att. WC", "246"),
        ("Secretary Chamber + Att. WC", "234"),
        ("Bar Office",                "128"),
        ("Common Toilet (M+F)",        "128"),
        ("RPwD Accessible WC",         "52"),
        ("Main Hall Audience",       "2,277"),
        ("Revised Dais + Rostrum",     "270"),
        ("Lobby + Corridor + Stair",   "832"),
        ("TOTAL GF",                 "4,167"),
    ]
    for i, (name, area) in enumerate(areas):
        y_ = sy - (i * 1.6*FT)
        is_bold = i == len(areas) - 1
        h_ = TX_LARGE*FT if is_bold else TX_MEDIUM*FT
        layer_ = "A-TEXT-TTL" if is_bold else "A-TEXT"
        r_text(msp, name, sx, y_, h=h_, layer=layer_, align=TextEntityAlignment.LEFT)
        r_text(msp, f"{area} sft", sx + 28*FT, y_, h=h_, layer=layer_, align=TextEntityAlignment.LEFT)

    # Title block
    draw_sheet_frame_and_titleblock(
        msp, SH, SW,
        sheet_no="SHEET 01 OF 02",
        sheet_title="GROUND FLOOR PLAN",
        scale_txt='1/8" = 1\'-0"',
        config=config,
    )

    # Save
    dxf_path = OUT_DXF / f"BA-Refined-Ground-Floor-Plan{SUFFIX}.dxf"
    doc.saveas(str(dxf_path))
    print(f"[OK] GF DXF saved: {dxf_path.name}")
    pdf = export_dxf_to_pdf(dxf_path, config)
    print(f"[OK] GF PDF saved: {pdf}")
    return dxf_path, pdf


def draw_first_floor():
    doc, msp = setup_doc(sheet_w=SH, sheet_h=SW, config=config)

    draw_directions(msp)
    draw_building_envelope(msp)
    draw_column_grid(msp)

    # SOUTH WING LOBBY
    lx1, lx2 = X(0) + OWT, X(30) - OWT
    ly1, ly2 = Y(5) + OWT, Y(13) - IWT/2
    r_fill_rect(msp, lx1, ly1, lx2, ly2, hatch="GRATE", layer="A-BAY")
    r_text(msp, "FF LOBBY", (lx1+lx2)/2, (ly1+ly2)/2, h=TX_XL*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)

    # SOUTH WING: Y=13..21.5 - PANTRY + STORE
    pn_x1, pn_x2 = X(0) + OWT, X(15) - IWT/2
    pn_y1, pn_y2 = Y(13) + IWT/2, Y(21.5) - OWT
    r_rect(msp, pn_x1, pn_y1, pn_x2, pn_y2, layer="A-WALL", lw=32)
    r_text(msp, "PANTRY", (pn_x1+pn_x2)/2, (pn_y1+pn_y2)/2, h=TX_LARGE*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)
    r_rect(msp, pn_x1 + 0.5*FT, pn_y1 + 0.5*FT, pn_x2 - 0.5*FT, pn_y1 + 2.8*FT, layer="A-FURN", lw=18)
    r_circle(msp, pn_x1 + 4*FT, pn_y1 + 1.6*FT, 0.5*FT, layer="A-FURN", lw=14)
    r_door_swing(msp, pn_x2 - 3*FT, pn_y1, 3*FT, swing_dir=1)
    r_window(msp, (pn_x1+pn_x2)/2, Y(21.5) - OWT/2, 5*FT, direction="n")

    # STORE
    st_x1, st_x2 = X(15) + IWT/2, X(30) - OWT
    st_y1, st_y2 = Y(13) + IWT/2, Y(21.5) - OWT
    r_rect(msp, st_x1, st_y1, st_x2, st_y2, layer="A-WALL", lw=32)
    r_text(msp, "STORE ROOM", (st_x1+st_x2)/2, (st_y1+st_y2)/2, h=TX_LARGE*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)
    r_rect(msp, st_x1 + 0.5*FT, st_y1 + 0.5*FT, st_x1 + 3*FT, st_y2 - 0.5*FT, layer="A-LOCKER", lw=18)
    r_door_swing(msp, st_x1 + 1*FT, st_y1, 3*FT, swing_dir=1)

    # =========================================================
    # FF EXTERIOR WINDOWS - SOUTH WALL (Y=5, X=0..30) 5 WINDOWS
    # =========================================================
    for sw in [(5, 5), (12, 5), (18, 5), (24, 5), (28, 5)]:
        r_window(msp, X(sw[0]), Y(5) + OWT/2, 5*FT, direction="s")
    # =========================================================
    # FF EXTERIOR WINDOWS - SOUTH WING EAST WALL (X=30, Y=5..21.5) 2 WINDOWS
    # =========================================================
    for ew in [(9, "e"), (18, "e")]:
        r_window(msp, X(30) - OWT/2, Y(ew[0]), 5*FT, direction="e")

    # E-W CORRIDOR
    cx1, cx2 = X(0) + OWT, X(55) - OWT
    cy1, cy2 = Y(21.5) + IWT/2, Y(25.5) - IWT/2
    r_fill_rect(msp, cx1, cy1, cx2, cy2, hatch="GRATE", layer="A-BAY")
    r_text(msp, "CORRIDOR 4'-0\"", X(27.5), (cy1+cy2)/2, h=TX_XL*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)

    # STAIR (STACKED over GF)
    stair_ox = X(46) + IWT/2
    stair_oy = Y(21.5) + IWT/2
    r_stair_dogleg(msp, stair_ox, stair_oy)
    s_ex = stair_ox + 9*FT
    s_ey = stair_oy + 33*FT
    r_door_swing(msp, (stair_ox + s_ex)/2 - 1.5*FT, stair_oy, 3*FT, swing_dir=1)
    r_door_swing(msp, (stair_ox + s_ex)/2 - 1.5*FT, s_ey - 3*FT, 3*FT, swing_dir=-1)

    # ===== EDP PROCESS CENTRE (corner segment, 2-3 computers) =====
    # Corner: SW corner of North Wing -> X=0..15, Y=25.5..40
    edp_x1, edp_x2 = X(0) + OWT, X(15) - IWT/2
    edp_y1, edp_y2 = Y(25.5) + IWT/2, Y(40) - IWT/2
    r_rect(msp, edp_x1, edp_y1, edp_x2, edp_y2, layer="A-WALL", lw=35)
    r_text(msp, "EDP PROCESS CENTRE\nCITATION PRINTING\n15' x 14.5'", (edp_x1+edp_x2)/2, (edp_y1+edp_y2)/2 + 2*FT, h=TX_XL*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)
    # 3 computer desks
    desk_w, desk_d = 4*FT, 2*FT
    for c in range(3):
        cx_ = edp_x1 + 1.5*FT + c * (desk_w + 0.8*FT)
        r_rect(msp, cx_, edp_y1 + 2*FT, cx_ + desk_w, edp_y1 + 2*FT + desk_d, layer="A-FURN", lw=20)
        # Chair behind desk (toward interior)
        r_circle(msp, cx_ + desk_w/2, edp_y1 + 2*FT + desk_d + 0.8*FT, 0.45*FT, layer="A-FURN", lw=16)
        # Monitor
        r_rect(msp, cx_ + desk_w/2 - 0.7*FT, edp_y1 + 2*FT + 0.3*FT, cx_ + desk_w/2 + 0.7*FT, edp_y1 + 2*FT + 1*FT, layer="A-FURN", lw=14)
        r_text(msp, f"PC-{c+1}", cx_ + desk_w/2, edp_y1 + 2*FT + desk_d/2, h=TX_SMALL*FT,
               layer="A-FURN", align=TextEntityAlignment.MIDDLE_CENTER)
    # Printer table
    r_rect(msp, edp_x1 + 1.5*FT, edp_y2 - 3*FT, edp_x2 - 1.5*FT, edp_y2 - 1*FT, layer="A-FURN", lw=18)
    r_text(msp, "PRINTER / PLOTTER", (edp_x1+edp_x2)/2, edp_y2 - 2*FT, h=TX_SMALL*FT,
           layer="A-FURN", align=TextEntityAlignment.MIDDLE_CENTER)
    # Entry door
    r_door_swing(msp, edp_x2 - 3*FT - 0.5*FT, edp_y1, 3*FT, swing_dir=1)
    r_text(msp, "3'-0\"", edp_x2 - 2*FT, edp_y1 + 1.8*FT, h=TX_SMALL*FT, layer="A-DOOR", rot=45.0)

    # ===== LIBRARY READING ROOM: Tables with chairs on BOTH SIDES =====
    # X=15..46, Y=25.5..75  (31' wide x 49.5' deep)
    lx1, ly1 = X(15) + IWT/2, Y(25.5) + IWT/2
    lx2, ly2 = X(46) - IWT/2, Y(75) - IWT/2
    r_rect(msp, lx1, ly1, lx2, ly2, layer="A-WALL", lw=35)
    r_text(msp, "LIBRARY READING ROOM\nTABLES WITH CHAIRS BOTH SIDES", (lx1+lx2)/2, ly2 - 3*FT, h=TX_XXL*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)

    # Central 4' Aisle
    laisle_cx = (lx1 + lx2) / 2
    laisle_w = 4 * FT
    r_line(msp, laisle_cx - laisle_w/2, ly1, laisle_cx - laisle_w/2, ly2, layer="A-BAY", lw=16)
    r_line(msp, laisle_cx + laisle_w/2, ly1, laisle_cx + laisle_w/2, ly2, layer="A-BAY", lw=16)
    r_text(msp, "AISLE 4'", laisle_cx, (ly1+ly2)/2, h=TX_LARGE*FT,
           layer="A-TEXT-TTL", rot=90.0, align=TextEntityAlignment.MIDDLE_CENTER)

    # Library tables with chairs on BOTH SIDES
    # 6 rows of tables, each row has tables on left and right of aisle
    tbl_w, tbl_d = 5 * FT, 2.2 * FT
    num_trows = 6
    trow_start = ly1 + 4 * FT
    trow_end = ly2 - 10 * FT
    tgap = (trow_end - trow_start) / (num_trows - 1) if num_trows > 1 else 0

    for tr in range(num_trows):
        ty_ = trow_start + tr * tgap
        # 2 tables left of aisle
        for tl in range(2):
            tx_ = lx1 + 1.5*FT + tl * (tbl_w + 1.2*FT)
            r_rect(msp, tx_, ty_, tx_ + tbl_w, ty_ + tbl_d, layer="A-FURN", lw=22)
            # Chairs: BOTH SIDES of table (top AND bottom)
            # Bottom side (south): 3 chairs
            for bc in range(3):
                r_circle(msp, tx_ + 1*FT + bc * 1.5*FT, ty_ - 0.8*FT, 0.42*FT, layer="A-FURN", lw=14)
            # Top side (north): 3 chairs
            for tc in range(3):
                r_circle(msp, tx_ + 1*FT + tc * 1.5*FT, ty_ + tbl_d + 0.8*FT, 0.42*FT, layer="A-FURN", lw=14)
            r_text(msp, f"T{tr+1}.{tl+1}", tx_ + tbl_w/2, ty_ + tbl_d/2, h=TX_SMALL*FT,
                   layer="A-FURN", align=TextEntityAlignment.MIDDLE_CENTER)
        # 2 tables right of aisle
        for tr_ in range(2):
            tx_ = laisle_cx + laisle_w/2 + 1.2*FT + tr_ * (tbl_w + 1.2*FT)
            r_rect(msp, tx_, ty_, tx_ + tbl_w, ty_ + tbl_d, layer="A-FURN", lw=22)
            # Chairs BOTH SIDES
            for bc in range(3):
                r_circle(msp, tx_ + 1*FT + bc * 1.5*FT, ty_ - 0.8*FT, 0.42*FT, layer="A-FURN", lw=14)
            for tc in range(3):
                r_circle(msp, tx_ + 1*FT + tc * 1.5*FT, ty_ + tbl_d + 0.8*FT, 0.42*FT, layer="A-FURN", lw=14)
            r_text(msp, f"T{tr+1}.{tr_+3}", tx_ + tbl_w/2, ty_ + tbl_d/2, h=TX_SMALL*FT,
                   layer="A-FURN", align=TextEntityAlignment.MIDDLE_CENTER)

    # Library entry doors from corridor (south wall): 2 pairs
    le1_h = X(20) + 0.5*FT
    r_door_swing(msp, le1_h, ly1, 4*FT, swing_dir=1)
    r_door_swing(msp, le1_h + 4*FT, ly1, 4*FT, swing_dir=-1)
    le2_h = X(38) - 4*FT + 0.5*FT
    r_door_swing(msp, le2_h, ly1, 4*FT, swing_dir=1)
    r_door_swing(msp, le2_h + 4*FT, ly1, 4*FT, swing_dir=-1)

    # Library exit on EAST wall (above stair)
    egress_w = 4 * FT
    r_door_swing(msp, lx2, Y(60) - egress_w/2, egress_w, swing_dir=1)
    r_text(msp, "EXIT 4'-0\"", lx2 - 5.5*FT, Y(60), h=TX_SMALL*FT,
           layer="A-DOOR", align=TextEntityAlignment.MIDDLE_CENTER)

    # =========================================================
    # FF EXTERIOR WINDOWS - MAIN EAST WALL (X=55, Y=21.5..93) 9 WINDOWS
    # =========================================================
    for yf in [25, 32, 40, 48, 56, 64, 72, 82, 90]:
        r_window(msp, X(55) - OWT/2, Y(yf), 6*FT, direction="e")
    # =========================================================
    # FF EXTERIOR WINDOWS - NORTH WALL (Y=93, X=0..55) 8 WINDOWS
    # =========================================================
    for xf in [5, 13, 21, 29, 36, 43, 49, 53]:
        r_window(msp, X(xf), Y(93) - OWT/2, 6*FT, direction="n")

    # ===== STACK AREA: X=15..46, Y=75..85 =====
    sk_x1, sk_y1 = X(15) + IWT/2, Y(75) + IWT/2
    sk_x2, sk_y2 = X(46) - IWT/2, Y(85) - IWT/2
    r_rect(msp, sk_x1, sk_y1, sk_x2, sk_y2, layer="A-WALL", lw=32)
    r_text(msp, "STACK AREA / BOOK STORAGE", (sk_x1+sk_x2)/2, (sk_y1+sk_y2)/2 + 5*FT, h=TX_XL*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)
    # 5 double-sided shelf rows
    for sr in range(5):
        sy_ = sk_y1 + 1*FT + sr * ((sk_y2 - sk_y1 - 2*FT) / 5.0)
        r_line(msp, sk_x1 + 2*FT, sy_, sk_x2 - 2*FT, sy_, layer="A-LOCKER", lw=20)
        r_line(msp, sk_x1 + 2*FT, sy_ + 2*FT, sk_x2 - 2*FT, sy_ + 2*FT, layer="A-LOCKER", lw=20)
        r_text(msp, f"STACK {sr+1:02d}", (sk_x1+sk_x2)/2, sy_ + 1*FT, h=TX_SMALL*FT,
               layer="A-LOCKER", align=TextEntityAlignment.MIDDLE_CENTER)
    # Cross aisle
    cross_cx = (sk_x1+sk_x2)/2
    r_line(msp, cross_cx - 1.5*FT, sk_y1, cross_cx - 1.5*FT, sk_y2, layer="A-BAY", lw=16)
    r_line(msp, cross_cx + 1.5*FT, sk_y1, cross_cx + 1.5*FT, sk_y2, layer="A-BAY", lw=16)
    # 2 doors from library into stack (on SOUTH wall)
    r_door_swing(msp, cross_cx - 4.5*FT, sk_y1, 3*FT, swing_dir=1)
    r_door_swing(msp, cross_cx + 1.5*FT, sk_y1, 3*FT, swing_dir=-1)

    # ===== FF CHAMBERS ROW: LIBRARIAN + ADMIN + SECY (NORTH) =====
    # LIBRARIAN / ADMIN: X=0..16, Y=85..93 -> 8' only. Use X=0..16, Y=81..93 (12' deep)
    # PRESIDENT chamber on GF used X=0..16,Y=81..93. For FF:
    # LIBRARIAN: X=0..16, Y=81..93 (16'x12')
    # ADMIN / BAR SECRETARY: X=46..55, Y=62..80 (9'x18')? Too narrow.
    # Use: NORTH of CHAMBERS ROW:
    #   X=0..16, Y=85..93 no -> Use X=0..16, Y=81..93 is 12' deep. Stack above Pres. chamber.
    # We already have Stack at X=15..46,Y=75..85, so north of that is Y=85..93 (8' too shallow).

    # Place LIBRARIAN and ADMIN rooms in the X=0..15, Y=40..75 corridor area (west strip)
    # Widen EDP to fill Y=25.5..40 and then add:
    # LIBRARIAN CABIN: X=0..15, Y=40..55 (15'x15')
    # ADMIN OFFICE:  X=0..15, Y=55..75 (15'x20')

    # LIBRARIAN CABIN
    lb_x1, lb_x2 = X(0) + OWT, X(15) - IWT/2
    lb_y1, lb_y2 = Y(40) + IWT/2, Y(55) - IWT/2
    r_rect(msp, lb_x1, lb_y1, lb_x2, lb_y2, layer="A-WALL", lw=32)
    r_text(msp, "LIBRARIAN\n15' x 15'", (lb_x1+lb_x2)/2, (lb_y1+lb_y2)/2, h=TX_XL*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)
    r_rect(msp, lb_x1 + 1.5*FT, lb_y2 - 4.5*FT, lb_x2 - 1.5*FT, lb_y2 - 1.5*FT, layer="A-FURN", lw=20)
    r_circle(msp, (lb_x1+lb_x2)/2, lb_y2 - 5.2*FT, 0.45*FT, layer="A-FURN", lw=16)
    # Issue-return counter on east
    r_rect(msp, lb_x2 - 2.5*FT, lb_y1 + 2*FT, lb_x2 - 0.5*FT, lb_y2 - 2*FT, layer="A-FURN", lw=20)
    r_text(msp, "ISSUE COUNTER", lb_x2 - 1.5*FT, (lb_y1+lb_y2)/2, h=TX_SMALL*FT,
           layer="A-FURN", align=TextEntityAlignment.MIDDLE_CENTER, rot=90.0)
    r_door_swing(msp, lb_x2 - 3*FT - 0.3*FT, lb_y1, 3*FT, swing_dir=1)

    # ADMIN OFFICE
    ao_x1, ao_x2 = X(0) + OWT, X(15) - IWT/2
    ao_y1, ao_y2 = Y(55) + IWT/2, Y(75) - IWT/2
    r_rect(msp, ao_x1, ao_y1, ao_x2, ao_y2, layer="A-WALL", lw=32)
    r_text(msp, "ADMIN OFFICE\n15' x 20'", (ao_x1+ao_x2)/2, (ao_y1+ao_y2)/2, h=TX_XL*FT,
           layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)
    r_rect(msp, ao_x1 + 1*FT, ao_y1 + 1*FT, ao_x2 - 1*FT, ao_y1 + 2.5*FT, layer="A-FURN", lw=20)
    r_text(msp, "WORK DESK 13'x1.5'", (ao_x1+ao_x2)/2, ao_y1 + 1.75*FT, h=TX_SMALL*FT,
           layer="A-FURN", align=TextEntityAlignment.MIDDLE_CENTER)
    # 2 workstations
    for w in range(2):
        wx_ = ao_x1 + 2*FT + w * ((ao_x2-ao_x1) - 4*FT)/1.0
        r_rect(msp, wx_, ao_y2 - 7*FT, wx_ + 4*FT, ao_y2 - 3*FT, layer="A-FURN", lw=18)
        r_circle(msp, wx_ + 2*FT, ao_y2 - 8*FT, 0.4*FT, layer="A-FURN", lw=14)
    # Filing cabinets
    r_rect(msp, ao_x1 + 0.5*FT, ao_y1 + 4*FT, ao_x1 + 2.5*FT, ao_y1 + 14*FT, layer="A-LOCKER", lw=16)
    r_door_swing(msp, ao_x2 - 3*FT - 0.3*FT, ao_y1, 3*FT, swing_dir=1)

    # FF TOILET (in the X=46..55 zone above stair, Y=54.5..70)
    ffto_x1, ffto_x2 = X(46) + IWT/2, X(55) - OWT
    ffto_y1, ffto_y2 = Y(54.5) + IWT/2, Y(70) - IWT/2
    r_rect(msp, ffto_x1, ffto_y1, ffto_x2, ffto_y2, layer="A-WALL", lw=32)
    # Male 55% / Female 45% of width
    ffmx1, ffmx2 = ffto_x1, ffto_x1 + (ffto_x2-ffto_x1)*0.55 - IWT/2
    fffx1, fffx2 = ffto_x1 + (ffto_x2-ffto_x1)*0.55 + IWT/2, ffto_x2
    r_line(msp, (ffmx2+fffx1)/2, ffto_y1, (ffmx2+fffx1)/2, ffto_y2, layer="A-WALL", lw=28)
    # Male: 3 urinals + 2 WCs + 2 basins
    r_text(msp, "MALE", (ffmx1+ffmx2)/2, ffto_y2 - 0.8*FT, h=TX_LARGE*FT, layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)
    for u in range(3):
        ux = ffmx1 + 0.5*FT + u * ((ffmx2-ffmx1) - 1*FT) / 3.0
        r_rect(msp, ux, ffto_y2 - 2.2*FT, ux + 1.1*FT, ffto_y2 - 0.4*FT, layer="A-FURN", lw=14)
    mw_w = (ffmx2 - ffmx1 - IWT) / 2.0
    for i in range(2):
        mwcx1 = ffmx1 + i * (mw_w + IWT/2)
        mwcx2 = mwcx1 + mw_w
        r_rect(msp, mwcx1, ffto_y1, mwcx2, ffto_y1 + 4.5*FT, layer="A-WALL", lw=20)
        r_rect(msp, mwcx2 - 1.8*FT, ffto_y1 + 0.6*FT, mwcx2 - 0.5*FT, ffto_y1 + 1.8*FT, layer="A-FURN", lw=12)
    r_door_swing(msp, ffmx2 - 2.75*FT, ffto_y1, 2.75*FT, swing_dir=1)
    # Female: 3 WCs + 2 basins
    r_text(msp, "FEMALE", (fffx1+fffx2)/2, ffto_y2 - 0.8*FT, h=TX_LARGE*FT, layer="A-TEXT-TTL", align=TextEntityAlignment.MIDDLE_CENTER)
    ffw = (fffx2 - fffx1 - IWT) / 3.0
    for i in range(3):
        ffcx1 = fffx1 + i * (ffw + IWT/3)
        ffcx2 = ffcx1 + ffw
        r_rect(msp, ffcx1, ffto_y1 + 2*FT, ffcx2, ffto_y2 - 2.5*FT, layer="A-WALL", lw=20)
        r_rect(msp, ffcx2 - 1.8*FT, ffto_y2 - 4.2*FT, ffcx2 - 0.5*FT, ffto_y2 - 3*FT, layer="A-FURN", lw=12)
        r_door_swing(msp, ffcx2 - 2*FT, ffto_y1 + 2*FT, 2*FT, swing_dir=-1)
    r_door_swing(msp, fffx1 + 0.2*FT, ffto_y1, 2.75*FT, swing_dir=-1)
    # 2 basins (one each)
    r_circle(msp, (ffmx1+ffmx2)/2, ffto_y1 + 6.5*FT, 0.5*FT, layer="A-FURN", lw=14)
    r_circle(msp, (fffx1+fffx2)/2, ffto_y1 + 1*FT, 0.5*FT, layer="A-FURN", lw=14)
    # =========================================================
    # FF EXTRA WINDOW - FF TOILET EAST WALL (additional dedicated)
    # =========================================================
    r_window(msp, X(55) - OWT/2, Y(62), 6*FT, direction="e")

    # =========================================================
    # FF VENTILATORS (pantry, store, toilets, stack, admin)
    # =========================================================
    # FV1 = PANTRY (X=0..15, Y=13..21.5) - SOUTH wall
    r_ventilator(msp, X(7.5), Y(5) + OWT/2, size=2.5*FT, direction="s", label="FV1")
    # FV2 = STORE (X=15..30, Y=13..21.5) - SOUTH wall
    r_ventilator(msp, X(22.5), Y(5) + OWT/2, size=2.5*FT, direction="s", label="FV2")
    # FV3 = FF MALE TOILET (X=46..50.5, Y=54.5..70) - EAST wall
    r_ventilator(msp, X(55) - OWT/2, Y(57), size=2.5*FT, direction="e", label="FV3")
    # FV4 = FF FEMALE TOILET (X=50.5..55, Y=54.5..70) - EAST wall
    r_ventilator(msp, X(55) - OWT/2, Y(68), size=2.5*FT, direction="e", label="FV4")
    # FV5 = STACK AREA (X=15..46, Y=75..85) - NORTH wall
    r_ventilator(msp, X(30.5), Y(93) - OWT/2, size=2.5*FT, direction="n", label="FV5")
    # FV6 = EDP CENTRE / ADMIN CORNER - SOUTH wing east wall
    r_ventilator(msp, X(30) - OWT/2, Y(20), size=2.5*FT, direction="e", label="FV6")

    # Access corridor from stair exit (north of stair landing) to toilet + EDP etc
    # Already have E-W corridor at Y=21.5..25.5, and doors open from there.
    # Additional corridor connector from stair north exit (Y=54.5) running west
    # into library area is handled via doors.

    # Dimensions
    r_arch_dim_h(msp, X(0), Y(1) - 1*FT, X(30), "30'-0\"", offset=-1.2*FT)
    r_arch_dim_h(msp, X(0), Y(1) - 3*FT, X(55), "55'-0\" OVERALL", offset=-1.2*FT)
    r_arch_dim_h(msp, X(30), Y(1) - 1*FT, X(55), "25'-0\"", offset=-1.2*FT)
    r_arch_dim_v(msp, X(0) - 1*FT, Y(5), Y(21.5), "16'-6\"", offset=-1.2*FT)
    r_arch_dim_v(msp, X(0) - 3*FT, Y(5), Y(93), "88'-0\" OVERALL", offset=-1.2*FT)
    r_arch_dim_v(msp, X(55) + 0.5*FT, Y(21.5), Y(93), "71'-6\"", offset=1.0*FT)

    # Title block (no notes, no area schedule per user instruction - only GF has area)
    draw_sheet_frame_and_titleblock(
        msp, SH, SW,
        sheet_no="SHEET 02 OF 02",
        sheet_title="FIRST FLOOR PLAN",
        scale_txt='1/8" = 1\'-0"',
        config=config,
    )

    # Save
    dxf_path = OUT_DXF / f"BA-Refined-First-Floor-Plan{SUFFIX}.dxf"
    doc.saveas(str(dxf_path))
    print(f"[OK] FF DXF saved: {dxf_path.name}")
    pdf = export_dxf_to_pdf(dxf_path, config)
    print(f"[OK] FF PDF saved: {pdf}")
    return dxf_path, pdf


if __name__ == "__main__":
    print("=" * 72)
    print("BAR ASSOCIATION BANSWARA — COMPLETE REDESIGN STARTED")
    print("  Stair: 9'W (2x4'+1'), 12\"Tread, 26 Risers, 33' Run")
    print("  Rotation: 90° Clockwise (A4 Portrait)")
    print("  Fonts: 4x size (300% increase)")
    print("  GF: Pres+Secy Chambers, Bar Off, 5-Urinal Toilet, Hall Chairs Only")
    print("  FF: EDP Centre Corner, Library Tables Chairs Both Sides")
    print("=" * 72)
    gf_dxf, gf_pdf = draw_ground_floor()
    ff_dxf, ff_pdf = draw_first_floor()
    print("=" * 72)
    print("ALL REDESIGNED DRAWINGS GENERATED SUCCESSFULLY")
    print(f"  GF DXF : {gf_dxf}")
    print(f"  GF PDF : {gf_pdf}")
    print(f"  FF DXF : {ff_dxf}")
    print(f"  FF PDF : {ff_pdf}")
    print("=" * 72)
