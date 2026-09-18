"""
OVERLAY v3: Embed actual GF floor plan inside building footprint on site plan
=============================================================================
Method: pypdf Transformation matrix to position/scale/rotate floor plan page
        onto the site plan page, then draw context overlay on top.

Base PDF  : INPUTS/A COURT CAMPUS IN MAHI COLONY 01 09 2025.pdf  (A0 Portrait 1684x2384)
Floor Plan: PDF/A-101-GF-GROUND-FLOOR-PLAN-BARE.pdf              (A2 Landscape 1684x1191)
Output    : PDF/SL-02-SITE-LAYOUT-OVERLAY.pdf
"""

from __future__ import annotations
import math, io
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas

ROOT      = Path(__file__).resolve().parent
INPUT_PDF = ROOT / "INPUTS" / "A COURT CAMPUS  IN MAHI COLONY  01 09 2025.pdf"
FLOOR_PDF = ROOT / "PDF"    / "A-101-GF-GROUND-FLOOR-PLAN-BARE.pdf"
OUT_PDF   = ROOT / "PDF"    / "SL-02-SITE-LAYOUT-OVERLAY.pdf"

PAGE_W, PAGE_H = 1684.0, 2384.0   # A0 portrait (site plan page)
FP_W,   FP_H   = 1683.8, 1190.6   # A2 landscape (floor plan page)

# ── Campus calibration ────────────────────────────────────────────────────
REF_A = (335.0, 290.0)     # SW campus corner in site PDF points
REF_B = (1340.0, 1970.0)   # NE campus corner in site PDF points
CAMP_W, CAMP_H = 454.0, 453.0   # feet

dx = REF_B[0]-REF_A[0]; dy = REF_B[1]-REF_A[1]
SC  = math.sqrt(dx**2+dy**2) / math.sqrt(CAMP_W**2+CAMP_H**2)  # pt/ft
ANG = math.atan2(dy, dx)   # ~59 deg

def c2p(x_ft, y_ft):
    """Campus feet → site PDF points."""
    xs, ys = x_ft*SC, y_ft*SC
    ca, sa  = math.cos(ANG), math.sin(ANG)
    return REF_A[0]+xs*ca-ys*sa, REF_A[1]+xs*sa+ys*ca

# ── Building (campus feet) ────────────────────────────────────────────────
BX, BY   = 50.0, 382.5      # SW corner (campus coords)
BW, BH   = 90.0, 55.5       # E-W × N-S (feet)
PD, PW_  = 8.0, 12.0        # porch depth & width

EAST  = (math.cos(ANG), math.sin(ANG))
NORTH = (math.cos(ANG+math.pi/2), math.sin(ANG+math.pi/2))

SW = c2p(BX,    BY)
SE = c2p(BX+BW, BY)
NE = c2p(BX+BW, BY+BH)
NW = c2p(BX,    BY+BH)
CX = (SW[0]+SE[0]+NE[0]+NW[0])/4
CY = (SW[1]+SE[1]+NE[1]+NW[1])/4

# ── Compute Transformation for floor plan page ────────────────────────────
# Floor plan drawing area within A2 page (from layout engine constants):
#   left margin=50, right strip=324, header=80+10, title=88+10
FP_DX = 50.0
FP_DY = 98.0
FP_DW = FP_W - FP_DX - 324.0   # ~1310 pt
FP_DH = FP_H - FP_DY - 90.0    # ~1003 pt

# We want this drawing area to fit exactly inside BW×BH feet on site
site_bw_pt = BW * SC   # building width in site PDF points
site_bh_pt = BH * SC   # building height in site PDF points

# Scale: fit floor plan drawing area into site building footprint
scale_fp = min(site_bw_pt/FP_DW, site_bh_pt/FP_DH)

# The Transformation we need:
# 1. Translate so floor plan drawing origin (FP_DX, FP_DY) goes to (0,0)
# 2. Scale by scale_fp
# 3. Rotate by ANG (to match site orientation)
# 4. Translate to SW corner of building on site

ang_deg = math.degrees(ANG)
ca, sa  = math.cos(ANG), math.sin(ANG)

# Combined 3x3 affine (a b c d e f) where:
# [x'] = [a b] [x] + [e]
# [y']   [c d] [y]   [f]
# Step 1+2: translate-then-scale: x'' = (x - FP_DX)*scale_fp
# Step 3: rotate: x''' = x''*cos - y''*sin
# Combined:
a  = scale_fp * ca
b  = -scale_fp * sa
c_ = scale_fp * sa
d  = scale_fp * ca
e_ = SW[0] + (-FP_DX*scale_fp)*ca - (-FP_DY*scale_fp)*sa
f_ = SW[1] + (-FP_DX*scale_fp)*sa + (-FP_DY*scale_fp)*ca

# Colours
W_CLR   = colors.HexColor("#1e293b")
P_CLR   = colors.HexColor("#fde68a")
C_CLR   = colors.HexColor("#8b1a1a")
S_CLR   = colors.HexColor("#f43f5e")
D_CLR   = colors.HexColor("#0f172a")
L_CLR   = colors.HexColor("#0369a1")
T_CLR   = colors.HexColor("#15803d")
R_CLR   = colors.HexColor("#dc2626")

def tree(c, cx, cy, r=5):
    c.setFillColor(T_CLR); c.setStrokeColor(colors.HexColor("#065f46")); c.setLineWidth(0.6)
    c.circle(cx,cy,r,stroke=1,fill=1)
    c.setFillColor(colors.HexColor("#bbf7d0")); c.setLineWidth(0)
    c.circle(cx-r*.3,cy+r*.3,r*.4,stroke=0,fill=1)

def callout(c, tx,ty, lx,ly, lines):
    c.setStrokeColor(D_CLR); c.setLineWidth(0.8); c.line(tx,ty,lx,ly)
    bw=max(len(t) for t in lines)*5.8+12; bh=len(lines)*12+8
    c.setFillColor(colors.Color(1,1,1,.92)); c.setStrokeColor(D_CLR); c.setLineWidth(0.5)
    c.roundRect(lx,ly-4,bw,bh,3,stroke=1,fill=1)
    c.setFillColor(D_CLR); c.setFont("Helvetica-Bold",8)
    for i,t in enumerate(lines):
        c.drawString(lx+6, ly+(len(lines)-1-i)*12+2, t)

def build_context_overlay():
    """Draw porch, trees, setback, callouts, label, legend on top of floor plan."""
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(PAGE_W,PAGE_H))

    # Setback dashed zone
    S_=20; N_=15; E_=20; W_=20
    spts=[c2p(BX-W_,BX-0+BY-S_)[0],]  # recalc properly
    z=[(c2p(BX-W_,BY-S_)), (c2p(BX+BW+E_,BY-S_)),
       (c2p(BX+BW+E_,BY+BH+N_)), (c2p(BX-W_,BY+BH+N_))]
    c.setStrokeColor(S_CLR); c.setLineWidth(1.0); c.setDash(7,4)
    c.setFillColor(colors.Color(.98,.88,.88,.12))
    p=c.beginPath()
    p.moveTo(*z[0]); [p.lineTo(*z[i]) for i in range(1,4)]; p.close()
    c.drawPath(p,fill=1,stroke=1); c.setDash()

    # Building heavy outline
    c.setStrokeColor(W_CLR); c.setLineWidth(3.2); c.setFillColor(colors.Color(0,0,0,0))
    bnd=c.beginPath()
    bnd.moveTo(*SW); bnd.lineTo(*SE); bnd.lineTo(*NE); bnd.lineTo(*NW); bnd.close()
    c.drawPath(bnd,fill=0,stroke=1)

    # RCC corner columns
    csz=1.6*SC
    for cx_,cy_ in [SW,SE,NE,NW]:
        c.setFillColor(C_CLR); c.setStrokeColor(W_CLR); c.setLineWidth(0.5)
        c.rect(cx_-csz/2,cy_-csz/2,csz,csz,stroke=1,fill=1)
        c.setStrokeColor(colors.HexColor("#3d0000")); c.setLineWidth(0.4)
        c.line(cx_-csz/2,cy_-csz/2,cx_+csz/2,cy_+csz/2)
        c.line(cx_+csz/2,cy_-csz/2,cx_-csz/2,cy_+csz/2)

    # Entrance porch (East wall, centre)
    PSW=c2p(BX+BW,      BY+(BH-PW_)/2)
    PSE=c2p(BX+BW+PD,   BY+(BH-PW_)/2)
    PNE=c2p(BX+BW+PD,   BY+(BH+PW_)/2)
    PNW=c2p(BX+BW,      BY+(BH+PW_)/2)
    c.setFillColor(P_CLR); c.setStrokeColor(colors.HexColor("#b45309")); c.setLineWidth(1.4)
    pp=c.beginPath()
    pp.moveTo(*PSW); pp.lineTo(*PSE); pp.lineTo(*PNE); pp.lineTo(*PNW); pp.close()
    c.drawPath(pp,fill=1,stroke=1)
    c.setDash(4,3); c.setLineWidth(0.8)
    pp2=c.beginPath()
    pp2.moveTo(PSW[0]-5,PSW[1]-5); pp2.lineTo(PSE[0]+5,PSE[1]-5)
    pp2.lineTo(PNE[0]+5,PNE[1]+5); pp2.lineTo(PNW[0]-5,PNW[1]+5); pp2.close()
    c.drawPath(pp2,fill=0,stroke=1); c.setDash()

    # Main entry arrow
    ecx=(PSE[0]+PNE[0])/2; ecy=(PSE[1]+PNE[1])/2
    ax=ecx+EAST[0]*40; ay=ecy+EAST[1]*40
    c.setStrokeColor(R_CLR); c.setLineWidth(1.6)
    c.line(ax,ay,ecx,ecy)
    c.setFillColor(R_CLR); c.circle(ecx,ecy,4,stroke=0,fill=1)
    c.setFont("Helvetica-Bold",10); c.drawString(ax+5,ay+2,"MAIN ENTRY")

    # Porch label
    pc=(PSW[0]+PSE[0]+PNE[0]+PNW[0])/4
    py=(PSW[1]+PSE[1]+PNE[1]+PNW[1])/4
    c.saveState(); c.translate(pc,py); c.rotate(ang_deg)
    c.setFillColor(W_CLR); c.setFont("Helvetica-Bold",7)
    c.drawCentredString(0,3,"PORCH"); c.drawCentredString(0,-7,"12'×8'")
    c.restoreState()

    # Trees
    for ti in range(7): tp=c2p(BX+5+ti*12, BY-7); tree(c,tp[0],tp[1],5)
    for ti in range(3): tp=c2p(BX-8, BY+8+ti*16); tree(c,tp[0],tp[1],5)
    for ti in range(6): tp=c2p(BX+ti*16, BY+BH+8); tree(c,tp[0],tp[1],6)

    # Revision cloud
    all_=[SW,SE,NE,NW,PSW,PSE,PNE,PNW]
    mnx=min(p[0] for p in all_)-30; mny=min(p[1] for p in all_)-30
    mxx=max(p[0] for p in all_)+30; mxy=max(p[1] for p in all_)+30
    c.setStrokeColor(R_CLR); c.setLineWidth(1.3); c.setDash(5,3)
    c.roundRect(mnx,mny,mxx-mnx,mxy-mny,20,stroke=1,fill=0); c.setDash()

    # Dimension callouts
    ms=((SW[0]+SE[0])/2,(SW[1]+SE[1])/2)
    callout(c, ms[0],ms[1], ms[0]+NORTH[0]*(-35),ms[1]+NORTH[1]*(-35)-18,
            ["90'-0\" (E-W)","LONGER WALL"])
    me=((SE[0]+NE[0])/2,(SE[1]+NE[1])/2)
    callout(c, me[0],me[1], me[0]+EAST[0]*32+5,me[1]+EAST[1]*32-10,
            ["55'-6\" (N-S)","SHORTER WALL"])

    # Building name label (south of building, rotated)
    lp=c2p(BX+BW/2, BY-16)
    c.saveState(); c.translate(lp[0],lp[1]); c.rotate(ang_deg)
    c.setFillColor(colors.Color(1,1,1,.9)); c.setStrokeColor(L_CLR); c.setLineWidth(0.7)
    c.roundRect(-110,-22,220,44,4,stroke=1,fill=1)
    c.setFillColor(L_CLR); c.setFont("Helvetica-Bold",10)
    c.drawCentredString(0,12,"BAR ASSOCIATION HALL  G+1")
    c.setFont("Helvetica",8); c.setFillColor(colors.HexColor("#0369a1"))
    c.drawCentredString(0,-2,"PROPOSED  ·  MAHI COLONY, BANSWARA")
    c.setFont("Helvetica-Bold",7); c.setFillColor(R_CLR)
    c.drawCentredString(0,-14,"FOR REVIEW  —  NOT FOR CONSTRUCTION")
    c.restoreState()

    # Legend
    LX=PAGE_W-245; LY=PAGE_H-275; LW=222; LH=165
    c.setFillColor(colors.Color(1,1,1,.93))
    c.setStrokeColor(colors.HexColor("#334155")); c.setLineWidth(0.8)
    c.roundRect(LX,LY,LW,LH,4,stroke=1,fill=1)
    c.setFillColor(colors.HexColor("#1e293b")); c.rect(LX,LY+LH-22,LW,22,stroke=0,fill=1)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold",9)
    c.drawString(LX+8,LY+LH-14,"OVERLAY LEGEND — SL-02")
    items=[(colors.HexColor("#fef9c3"),W_CLR,"FLOOR PLAN (GF BARE)"),
           (P_CLR,colors.HexColor("#b45309"),"ENTRANCE PORCH 12'×8'"),
           (S_CLR,S_CLR,"SETBACK ZONE (DASHED)"),
           (T_CLR,colors.HexColor("#065f46"),"PROPOSED TREES"),
           (C_CLR,W_CLR,"RCC CORNER COLUMNS")]
    ly=LY+LH-42
    for fc,sc,lb in items:
        c.setFillColor(fc); c.setStrokeColor(sc); c.setLineWidth(0.5)
        c.rect(LX+10,ly,16,11,stroke=1,fill=1)
        c.setFillColor(colors.HexColor("#1e293b")); c.setFont("Helvetica",7.5)
        c.drawString(LX+32,ly+2,lb); ly-=18
    c.setFont("Helvetica-Bold",7); c.setFillColor(colors.HexColor("#1e293b"))
    c.drawString(LX+8,LY+18,"LONGER WALL : EAST-WEST")
    c.drawString(LX+8,LY+7,
        f"REV P02  {datetime.now(timezone.utc).strftime('%d-%b-%Y').upper()}")

    c.save()
    return buf.getvalue()


def main():
    print(f"Base : {INPUT_PDF.name}")
    print(f"Plan : {FLOOR_PDF.name}")
    print(f"Scale: {SC:.3f} pt/ft  |  Angle: {math.degrees(ANG):.1f} deg")

    # ── Read both source PDFs ──────────────────────────────────────────────
    base_reader  = PdfReader(str(INPUT_PDF))
    floor_reader = PdfReader(str(FLOOR_PDF))

    base_page  = base_reader.pages[0]
    floor_page = floor_reader.pages[0]

    # ── Apply transformation to floor plan page ───────────────────────────
    # Transformation matrix: scales, rotates, translates floor plan
    # so its drawing area aligns with the building footprint on site
    print(f"Transform: a={a:.4f} b={b:.4f} c={c_:.4f} d={d:.4f} e={e_:.1f} f={f_:.1f}")
    tf = Transformation((a, b, c_, d, e_, f_))
    floor_page.add_transformation(tf)
    # Expand mediabox so page covers the full A0 site page
    floor_page.mediabox.lower_left  = (0, 0)
    floor_page.mediabox.upper_right = (PAGE_W, PAGE_H)

    # ── Build output: base + floor plan + context overlay ─────────────────
    writer = PdfWriter()
    writer.add_page(base_page)

    # Layer 1: transformed floor plan
    writer.pages[0].merge_page(floor_page)

    # Layer 2: context overlay (porch, trees, labels etc.)
    ctx_bytes  = build_context_overlay()
    ctx_reader = PdfReader(io.BytesIO(ctx_bytes))
    writer.pages[0].merge_page(ctx_reader.pages[0])

    with open(OUT_PDF,"wb") as f:
        writer.write(f)

    print(f"[OK] {OUT_PDF.name}")
    print(f"     {OUT_PDF}")


if __name__ == "__main__":
    main()
