"""
OVERLAY v4 — Image-based composite
====================================
1. Render site plan PDF → high-res PNG (300 DPI)
2. Render floor plan PDF → high-res PNG (300 DPI)
3. Resize floor plan PNG to match building footprint size on site (in pixels)
4. Rotate floor plan PNG to match site drawing angle (~59°)
5. Paste onto site plan image at correct pixel position
6. Add annotation overlay (porch, trees, label, legend, callouts)
7. Save as PDF

This approach is 100% reliable — no PDF coordinate system issues.
"""

from __future__ import annotations
import math
from datetime import datetime, timezone
from pathlib import Path
from io import BytesIO

import fitz                         # PyMuPDF
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT      = Path(__file__).resolve().parent
INPUT_PDF = ROOT / "INPUTS" / "A COURT CAMPUS  IN MAHI COLONY  01 09 2025.pdf"
FLOOR_PDF = ROOT / "PDF"    / "A-101-GF-GROUND-FLOOR-PLAN-BARE.pdf"
OUT_PDF   = ROOT / "PDF"    / "SL-02-SITE-LAYOUT-OVERLAY.pdf"

DPI = 150   # render DPI — good quality, manageable file size

# ── Campus calibration ────────────────────────────────────────────────────
# Site PDF has rotation=270 stored as landscape (2384×1684 stored).
# fitz renders it as 4967×3509 landscape image (width > height).
# In the rendered image:
#   - The drawing appears with North toward bottom-left
#   - Calibration points (visually identified on the rendered image):
#     Ref A = SW campus corner  → pixel approx (600, 2800)  [bottom area]
#     Ref B = NE campus corner  → pixel approx (4200, 600)  [top area]
# NOTE: These are in PIL image coords (y from top, x from left)
REF_A_PX = (620,  2780)   # SW campus corner in rendered image pixels
REF_B_PX = (4150,  680)   # NE campus corner in rendered image pixels

CAMP_W_FT = 454.0
CAMP_H_FT = 453.0

dx = REF_B_PX[0] - REF_A_PX[0]
dy = REF_B_PX[1] - REF_A_PX[1]
dist_px = math.sqrt(dx**2 + dy**2)
dist_ft = math.sqrt(CAMP_W_FT**2 + CAMP_H_FT**2)
SC_PX_FT = dist_px / dist_ft   # pixels per foot
ANG_PIL  = math.atan2(dy, dx)  # angle in PIL space (y-down)
ANG_DEG  = math.degrees(ANG_PIL)

print(f"Scale: {SC_PX_FT:.3f} px/ft  |  Angle (PIL): {ANG_DEG:.1f} deg")

def c2px(x_ft, y_ft):
    """Campus feet (SW origin, y=north) → PIL pixels (y from top)."""
    xs = x_ft * SC_PX_FT
    ys = y_ft * SC_PX_FT
    ca = math.cos(ANG_PIL); sa = math.sin(ANG_PIL)
    xr = xs*ca - ys*sa
    yr = xs*sa + ys*ca
    return (int(REF_A_PX[0] + xr), int(REF_A_PX[1] + yr))

# ── Building (campus feet) ─────────────────────────────────────────────────
BX, BY = 50.0, 382.5
BW, BH = 90.0, 55.5        # E-W × N-S feet

SW_PX = c2px(BX,    BY)
SE_PX = c2px(BX+BW, BY)
NE_PX = c2px(BX+BW, BY+BH)
NW_PX = c2px(BX,    BY+BH)

# Building width/height in pixels
bldg_w_px = int(round(BW * SC_PX_FT))
bldg_h_px = int(round(BH * SC_PX_FT))

print(f"Building SW: {SW_PX}, SE: {SE_PX}")
print(f"Building size on image: {bldg_w_px} x {bldg_h_px} px")

# ── Floor plan drawing area within A2 page ────────────────────────────────
# Header=80+10=90pt top, title=88+10=98pt bottom, left=50pt, right strip=324pt
FP_PT_W, FP_PT_H = 1683.8, 1190.6
FP_DX_PT = 50.0
FP_DY_PT = 98.0                          # from bottom
FP_DW_PT = FP_PT_W - FP_DX_PT - 324.0  # ~1310 pt
FP_DH_PT = FP_PT_H - FP_DY_PT - 90.0   # ~1003 pt

# In pixels
FP_PX_W = int(round(FP_PT_W * DPI / 72.0))
FP_PX_H = int(round(FP_PT_H * DPI / 72.0))
FP_DX_PX = int(round(FP_DX_PT * DPI / 72.0))
FP_DY_PX = int(round(FP_DY_PT * DPI / 72.0))
FP_DW_PX = int(round(FP_DW_PT * DPI / 72.0))
FP_DH_PX = int(round(FP_DH_PT * DPI / 72.0))

# ── Colours (PIL RGBA) ─────────────────────────────────────────────────────
COL_WALL    = (30,  41,  59,  255)   # dark charcoal
COL_PORCH   = (253,230,138, 220)     # amber
COL_COL     = (139, 26, 26, 255)     # dark red RCC
COL_SETBK   = (244, 63, 94, 120)     # pink dashed
COL_TREE    = (21, 128, 61, 220)     # dark green
COL_RED     = (220, 38, 38, 255)     # entry arrow
COL_BLUE    = ( 3, 105,161, 255)     # label blue
COL_CLOUD   = (220, 38, 38, 180)     # revision cloud
COL_SHADOW  = (  0,  0,  0,  60)     # drop shadow
COL_WHITE   = (255,255,255,220)      # legend bg


def draw_tree_px(draw, cx, cy, r=8):
    draw.ellipse((cx-r,cy-r,cx+r,cy+r), fill=COL_TREE, outline=(6,95,70,255), width=1)
    hl_r=int(r*.4)
    draw.ellipse((cx-r//3-hl_r,cy-r//3-hl_r,cx-r//3+hl_r,cy-r//3+hl_r),
                 fill=(187,247,208,200))


def draw_thick_line(draw, p1, p2, width, color):
    draw.line([p1,p2], fill=color, width=width)


def draw_dashed_polygon(draw, pts, color, width=2, dash=12, gap=6):
    for i in range(len(pts)):
        p0 = pts[i]; p1 = pts[(i+1)%len(pts)]
        dx = p1[0]-p0[0]; dy = p1[1]-p0[1]
        length = math.sqrt(dx**2+dy**2)
        if length == 0: continue
        ux = dx/length; uy = dy/length
        pos = 0; drawing = True
        while pos < length:
            seg = min(dash if drawing else gap, length-pos)
            if drawing:
                sx = p0[0]+ux*pos; sy = p0[1]+uy*pos
                ex = p0[0]+ux*(pos+seg); ey = p0[1]+uy*(pos+seg)
                draw.line([(sx,sy),(ex,ey)], fill=color, width=width)
            pos += seg; drawing = not drawing


def draw_arrow_px(draw, tip, tail, color, width=3, head_size=14):
    draw.line([tail,tip], fill=color, width=width)
    dx = tip[0]-tail[0]; dy = tip[1]-tail[1]
    ang = math.atan2(dy,dx)
    for sign in [1,-1]:
        ex = tip[0] - head_size*math.cos(ang-sign*0.4)
        ey = tip[1] - head_size*math.sin(ang-sign*0.4)
        draw.line([tip,(int(ex),int(ey))], fill=color, width=width)


def main():
    # ── Step 1: Render site plan PDF to image ──────────────────────────────
    print("Rendering site plan PDF...")
    site_doc  = fitz.open(str(INPUT_PDF))
    site_mat  = fitz.Matrix(DPI/72, DPI/72)
    site_pix  = site_doc[0].get_pixmap(matrix=site_mat, alpha=False)
    site_img  = Image.frombytes("RGB", (site_pix.width, site_pix.height), site_pix.samples)
    site_doc.close()
    print(f"  Site image: {site_img.size}")

    # ── Step 2: Render floor plan PDF to image ─────────────────────────────
    print("Rendering floor plan PDF...")
    fp_doc  = fitz.open(str(FLOOR_PDF))
    fp_mat  = fitz.Matrix(DPI/72, DPI/72)
    fp_pix  = fp_doc[0].get_pixmap(matrix=fp_mat, alpha=False)
    fp_img  = Image.frombytes("RGB", (fp_pix.width, fp_pix.height), fp_pix.samples)
    fp_doc.close()
    print(f"  Floor plan image: {fp_img.size}")

    # ── Step 3: Crop floor plan to drawing area only ───────────────────────
    # PIL coords: y from top. FP_DY_PX is from bottom → flip
    fp_h_px = fp_img.size[1]
    crop_top    = fp_h_px - FP_DY_PX - FP_DH_PX
    crop_bottom = fp_h_px - FP_DY_PX
    crop_left   = FP_DX_PX
    crop_right  = FP_DX_PX + FP_DW_PX
    fp_crop = fp_img.crop((crop_left, crop_top, crop_right, crop_bottom))
    print(f"  Cropped drawing area: {fp_crop.size}")

    # ── Step 4: Resize to fit building footprint ───────────────────────────
    scale_x = bldg_w_px / fp_crop.size[0]
    scale_y = bldg_h_px / fp_crop.size[1]
    fp_scale = min(scale_x, scale_y)
    new_w = int(fp_crop.size[0] * fp_scale)
    new_h = int(fp_crop.size[1] * fp_scale)
    fp_scaled = fp_crop.resize((new_w, new_h), Image.LANCZOS)
    print(f"  Scaled to: {fp_scaled.size}  (building: {bldg_w_px}x{bldg_h_px})")

    # ── Step 5: Rotate to match site drawing angle ─────────────────────────
    # PIL rotate is anticlockwise. ANG_DEG is clockwise from east in PIL space.
    # We need to rotate the floor plan so its E-W axis aligns with the site drawing.
    rotate_angle = -ANG_DEG  # PIL anticlockwise
    fp_rot = fp_scaled.rotate(rotate_angle, expand=True,
                              resample=Image.BICUBIC,
                              fillcolor=(255,255,255))
    print(f"  Rotated {rotate_angle:.1f}° → size: {fp_rot.size}")

    # ── Step 6: Composite floor plan onto site image ───────────────────────
    # Paste position: SW corner of building on site
    # After rotation the image is larger (expand=True) — find offset to SW corner
    # The SW corner in the rotated image:
    #   Original image SW = bottom-left = (0, new_h) before rotation
    #   After rotation by rotate_angle:
    rw, rh = fp_rot.size
    # Center of original before rotation
    cx_orig = new_w / 2; cy_orig = new_h / 2
    # SW corner in original coords (bottom-left)
    sw_orig_x = 0; sw_orig_y = new_h
    # Rotated center of expanded image
    cx_rot = rw/2; cy_rot = rh/2
    # Apply rotation to SW point relative to center
    ang_rad = math.radians(rotate_angle)
    ca = math.cos(ang_rad); sa = math.sin(ang_rad)
    dx_sw = sw_orig_x - cx_orig; dy_sw = sw_orig_y - cy_orig
    sw_in_rot_x = cx_rot + dx_sw*ca - dy_sw*sa
    sw_in_rot_y = cy_rot + dx_sw*sa + dy_sw*ca

    # Paste position so SW_PX aligns with SW corner of floor plan
    paste_x = int(SW_PX[0] - sw_in_rot_x)
    paste_y = int(SW_PX[1] - sw_in_rot_y)
    print(f"  Pasting at ({paste_x}, {paste_y}), SW_PX={SW_PX}")

    # Drop shadow
    shadow_img = Image.new("RGBA", site_img.size, (0,0,0,0))
    shadow_draw = ImageDraw.Draw(shadow_img)
    shadow_pts = [
        (SW_PX[0]+8, SW_PX[1]+8), (SE_PX[0]+8, SE_PX[1]+8),
        (NE_PX[0]+8, NE_PX[1]+8), (NW_PX[0]+8, NW_PX[1]+8)
    ]
    shadow_draw.polygon(shadow_pts, fill=(0,0,0,70))
    site_rgba = site_img.convert("RGBA")
    site_rgba = Image.alpha_composite(site_rgba, shadow_img)

    # Paste floor plan (convert to RGBA for composite)
    fp_rgba = fp_rot.convert("RGBA")
    # Create white background version for cleaner paste
    site_rgba.paste(fp_rgba, (paste_x, paste_y), fp_rgba)
    result = site_rgba.convert("RGB")

    # ── Step 7: Draw annotation overlay ────────────────────────────────────
    draw = ImageDraw.Draw(result, "RGBA")

    # Building outline (thick dark)
    bldg_pts = [SW_PX, SE_PX, NE_PX, NW_PX]
    draw.polygon(bldg_pts, outline=COL_WALL, width=5)

    # RCC corner columns
    col_sz = int(1.8 * SC_PX_FT)
    for cx_c, cy_c in bldg_pts:
        draw.rectangle(
            (cx_c-col_sz//2, cy_c-col_sz//2, cx_c+col_sz//2, cy_c+col_sz//2),
            fill=COL_COL, outline=(61,0,0,255), width=1
        )
        draw.line([(cx_c-col_sz//2,cy_c-col_sz//2),(cx_c+col_sz//2,cy_c+col_sz//2)],
                  fill=(61,0,0,255), width=1)
        draw.line([(cx_c+col_sz//2,cy_c-col_sz//2),(cx_c-col_sz//2,cy_c+col_sz//2)],
                  fill=(61,0,0,255), width=1)

    # Entrance porch (East wall, centre)
    PY0 = BY + (BH-12)/2; PY1 = BY + (BH+12)/2
    PSW=c2px(BX+BW,   PY0); PSE=c2px(BX+BW+8, PY0)
    PNE=c2px(BX+BW+8, PY1); PNW=c2px(BX+BW,   PY1)
    draw.polygon([PSW,PSE,PNE,PNW], fill=COL_PORCH, outline=(180,83,9,255), width=3)
    draw_dashed_polygon(draw,
        [(PSW[0]-6,PSW[1]-6),(PSE[0]+6,PSE[1]-6),(PNE[0]+6,PNE[1]+6),(PNW[0]-6,PNW[1]+6)],
        (180,83,9,200), width=2)

    # Main entry arrow
    ecx=(PSE[0]+PNE[0])//2; ecy=(PSE[1]+PNE[1])//2
    ax=ecx+int(EAST[0]*55); ay=ecy+int(EAST[1]*55)
    draw_arrow_px(draw, (ecx,ecy), (ax,ay), COL_RED, width=4, head_size=16)

    # Setback dashed boundary
    S_=20; N_=15; E_=20; W_=20
    sb_pts=[c2px(BX-W_,BY-S_), c2px(BX+BW+E_,BY-S_),
            c2px(BX+BW+E_,BY+BH+N_), c2px(BX-W_,BY+BH+N_)]
    draw_dashed_polygon(draw, sb_pts, (244,63,94,180), width=3, dash=14, gap=7)

    # Trees
    for ti in range(7): tp=c2px(BX+5+ti*12, BY-8); draw_tree_px(draw,tp[0],tp[1],9)
    for ti in range(3): tp=c2px(BX-10, BY+8+ti*16); draw_tree_px(draw,tp[0],tp[1],9)
    for ti in range(6): tp=c2px(BX+ti*16, BY+BH+9); draw_tree_px(draw,tp[0],tp[1],11)

    # Revision cloud
    all_pts=bldg_pts+[PSW,PSE,PNE,PNW]
    mnx=min(p[0] for p in all_pts)-35; mny=min(p[1] for p in all_pts)-35
    mxx=max(p[0] for p in all_pts)+35; mxy=max(p[1] for p in all_pts)+35
    # Draw as rounded rectangle (dashed)
    draw_dashed_polygon(draw,
        [(mnx,mny),(mxx,mny),(mxx,mxy),(mnx,mxy)],
        (220,38,38,200), width=2, dash=16, gap=8)

    # ── Text annotations ────────────────────────────────────────────────
    try:
        font_bold = ImageFont.truetype("arialbd.ttf", int(18*DPI/96))
        font_reg  = ImageFont.truetype("arial.ttf",   int(14*DPI/96))
        font_sm   = ImageFont.truetype("arial.ttf",   int(12*DPI/96))
    except Exception:
        font_bold = ImageFont.load_default()
        font_reg  = font_bold
        font_sm   = font_bold

    # Building label (south of building, centred)
    lp = c2px(BX+BW/2, BY-20)
    lbl1 = "BAR ASSOCIATION HALL  G+1"
    lbl2 = "PROPOSED  ·  MAHI COLONY, BANSWARA"
    lbl3 = "90'-0\" (E-W)  ×  55'-6\" (N-S)"
    # White box
    draw.rectangle((lp[0]-180,lp[1]-10,lp[0]+180,lp[1]+52),
                   fill=(255,255,255,220), outline=COL_BLUE, width=2)
    draw.text((lp[0]-170, lp[1]-5),  lbl1, fill=COL_BLUE,   font=font_bold)
    draw.text((lp[0]-170, lp[1]+16), lbl2, fill=(3,105,161,255), font=font_reg)
    draw.text((lp[0]-170, lp[1]+32), lbl3, fill=(30,41,59,255),  font=font_sm)

    # MAIN ENTRY label
    draw.text((ax+8, ay-10), "MAIN ENTRY", fill=COL_RED, font=font_bold)

    # Legend box (top-right of image)
    LX=result.size[0]-320; LY=60
    draw.rectangle((LX,LY,LX+300,LY+180), fill=(255,255,255,230),
                   outline=(51,65,85,255), width=2)
    draw.rectangle((LX,LY,LX+300,LY+28), fill=(30,41,59,255))
    draw.text((LX+8,LY+4), "OVERLAY LEGEND — SL-02",
              fill=(255,255,255,255), font=font_bold)
    legend_items=[
        ((254,252,195,255),  "FLOOR PLAN (GF BARE)"),
        ((253,230,138,255),  "ENTRANCE PORCH 12'×8'"),
        ((244, 63, 94,180),  "SETBACK ZONE (DASHED)"),
        ((21, 128, 61,220),  "PROPOSED TREES"),
        ((139, 26, 26,255),  "RCC CORNER COLUMNS"),
    ]
    ly=LY+36
    for clr,lbl in legend_items:
        draw.rectangle((LX+10,ly,LX+26,ly+14), fill=clr, outline=(51,65,85,255), width=1)
        draw.text((LX+34,ly-1), lbl, fill=(30,41,59,255), font=font_sm)
        ly+=22
    draw.text((LX+10,LY+155),
              f"REV P02  {datetime.now(timezone.utc).strftime('%d-%b-%Y').upper()}",
              fill=(30,41,59,255), font=font_sm)

    # ── Step 8: Save as PDF ────────────────────────────────────────────────
    print("Saving output PDF...")
    img_buf = BytesIO()
    result.save(img_buf, format="PDF", resolution=DPI)
    OUT_PDF.write_bytes(img_buf.getvalue())
    print(f"[OK] {OUT_PDF.name}")
    print(f"     {OUT_PDF}")


# Compute EAST vector in PIL space for arrow direction
ANG_PIL_VAL = ANG_PIL
EAST = (math.cos(ANG_PIL_VAL), math.sin(ANG_PIL_VAL))

if __name__ == "__main__":
    main()
