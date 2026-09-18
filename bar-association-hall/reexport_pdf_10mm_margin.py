"""
RE-EXPORT EXISTING DXF -> A4 LANDSCAPE PDF with 10mm MARGINS
Inputs:  CAD/BA-Refined-Ground-Floor-Plan.dxf
         CAD/BA-Refined-First-Floor-Plan.dxf
Outputs: PDF/BA-Refined-Ground-Floor-Plan-10mmMargin-A4Landscape.pdf
         PDF/BA-Refined-First-Floor-Plan-10mmMargin-A4Landscape.pdf

Paper:  A4 Landscape 297mm x 210mm
Margins: 10mm ALL AROUND (Top/Bottom/Left/Right)
         Printable: (297 - 2*10) = 277mm  x  (210 - 2*10) = 190mm
"""

import sys
import os
from pathlib import Path
import math

sys.path.insert(0, r"e:\Rajkumar\Advocate-Chambers\scripts")
from traecad_engine import (
    ezdxf, FT, colors, TextEntityAlignment,
    RenderContext, Frontend, Configuration,
    BackgroundPolicy, ColorPolicy, LinePolicy,
    MatplotlibBackend, plt, pymupdf, PAPER_SIZES, PT_PER_MM,
)

BASE = Path(r"e:\Rajkumar\Advocate-Chambers\bar-association-hall")
DXF_DIR = BASE / "CAD"
PDF_DIR = BASE / "PDF"
PDF_DIR.mkdir(parents=True, exist_ok=True)

# ---- 10mm MARGIN A4 LANDSCAPE CONFIG ----
PAPER_W_MM = 297.0
PAPER_H_MM = 210.0
MARGIN_MM = 10.0


def export_dxf_10mm_a4landscape(dxf_path: Path, output_pdf_path: Path):
    """
    Render a DXF to EXACT A4 Landscape PDF with 10mm margins on all sides.
    Auto-fits the drawing model extents to the printable area (277mm x 190mm).
    """
    print(f"\n[1/4] Reading DXF: {dxf_path.name}")
    try:
        doc = ezdxf.readfile(str(dxf_path))
    except Exception as e:
        print(f"    [FAIL] Read DXF failed: {e}")
        return False

    msp = doc.modelspace()

    # ---- Compute MODEL EXTENTS from all entities ----
    print(f"[2/4] Computing drawing extents ...")
    ext_min_x = ext_min_y = float("inf")
    ext_max_x = ext_max_y = float("-inf")
    count = 0
    try:
        for e in msp:
            try:
                if hasattr(e, "dxf"):
                    attrs = []
                    for attr in ["start", "end", "center", "insert", "p1", "p2", "p3", "p4", "text_midpoint", "midpoint"]:
                        if hasattr(e.dxf, attr):
                            val = getattr(e.dxf, attr)
                            if val is not None:
                                attrs.append(val)
                    for pt in attrs:
                        try:
                            if hasattr(pt, "x") and hasattr(pt, "y"):
                                x, y = float(pt.x), float(pt.y)
                            elif isinstance(pt, (list, tuple)) and len(pt) >= 2:
                                x, y = float(pt[0]), float(pt[1])
                            else:
                                continue
                            if x < ext_min_x: ext_min_x = x
                            if y < ext_min_y: ext_min_y = y
                            if x > ext_max_x: ext_max_x = x
                            if y > ext_max_y: ext_max_y = y
                            count += 1
                        except Exception:
                            pass
            except Exception:
                continue
        if count > 0 and ext_min_x != float("inf"):
            dwg_w = ext_max_x - ext_min_x
            dwg_h = ext_max_y - ext_min_y
            print(f"    Entities scanned: {count} pts")
            print(f"    Model bbox: [{ext_min_x/FT:.2f}', {ext_min_y/FT:.2f}']  ->  [{ext_max_x/FT:.2f}', {ext_max_y/FT:.2f}']")
            print(f"    Drawing size: {dwg_w/FT:.2f}' x {dwg_h/FT:.2f}'")
        else:
            raise RuntimeError("no points collected")
    except Exception as e:
        print(f"    Auto-extents fallback ({e}); using stored sheet dims.")
        sw = getattr(doc, "_sheet_w", 160.0 * FT)
        sh = getattr(doc, "_sheet_h", sw * (190.0 / 277.0))
        ext_min_x, ext_min_y = 0.0, 0.0
        ext_max_x, ext_max_y = sw, sh
        dwg_w, dwg_h = sw, sh

    # Add 1% padding around drawing
    pad_x = dwg_w * 0.01
    pad_y = dwg_h * 0.01
    lim_xmin = ext_min_x - pad_x
    lim_xmax = ext_max_x + pad_x
    lim_ymin = ext_min_y - pad_y
    lim_ymax = ext_max_y + pad_y

    # ---- PAPER / PRINTABLE CALC ----
    paper_w_in = PAPER_W_MM / 25.4
    paper_h_in = PAPER_H_MM / 25.4
    printable_w_mm = PAPER_W_MM - 2 * MARGIN_MM
    printable_h_mm = PAPER_H_MM - 2 * MARGIN_MM
    print(f"[3/4] A4 Landscape: {PAPER_W_MM}x{PAPER_H_MM} mm  |  Printable: {printable_w_mm}x{printable_h_mm} mm  (10mm margins all)")

    fig = plt.figure(figsize=(paper_w_in, paper_h_in), dpi=300, facecolor="white")
    margin_left = MARGIN_MM / PAPER_W_MM
    margin_bottom = MARGIN_MM / PAPER_H_MM
    printable_w_ratio = printable_w_mm / PAPER_W_MM
    printable_h_ratio = printable_h_mm / PAPER_H_MM
    ax = fig.add_axes([margin_left, margin_bottom, printable_w_ratio, printable_h_ratio])
    ax.set_facecolor("white")
    ax.set_axis_off()

    ax.set_xlim(lim_xmin, lim_xmax)
    ax.set_ylim(lim_ymin, lim_ymax)

    ctx = RenderContext(doc)
    render_cfg = Configuration(
        background_policy=BackgroundPolicy.WHITE,
        color_policy=ColorPolicy.COLOR,
        custom_fg_color="#000000",
        line_policy=LinePolicy.ACCURATE,
    )
    backend = MatplotlibBackend(ax)
    frontend = Frontend(ctx, backend, config=render_cfg)
    frontend.draw_layout(msp, finalize=True)

    # ---- SAVE to TEMP PDF, then impose on EXACT A4 MediaBox ----
    temp_pdf = PDF_DIR / f"_temp_10mm_{dxf_path.stem}.pdf"
    fig.savefig(str(temp_pdf), format="pdf", facecolor="white", dpi=300, bbox_inches=None)
    plt.close(fig)

    a4_w_pt = PAPER_W_MM * PT_PER_MM
    a4_h_pt = PAPER_H_MM * PT_PER_MM
    doc_a4 = pymupdf.open()
    page_a4 = doc_a4.new_page(width=a4_w_pt, height=a4_h_pt)
    src_doc = pymupdf.open(str(temp_pdf))
    page_a4.show_pdf_page(pymupdf.Rect(0, 0, a4_w_pt, a4_h_pt), src_doc, 0)
    doc_a4.save(str(output_pdf_path))
    doc_a4.close()
    src_doc.close()

    if temp_pdf.exists():
        temp_pdf.unlink()

    sz = output_pdf_path.stat().st_size
    print(f"[4/4] PDF saved: {output_pdf_path.name}  ({sz:,} bytes)")
    print(f"    MediaBox: {PAPER_W_MM}x{PAPER_H_MM} mm A4 Landscape  |  Margins: {MARGIN_MM}mm all sides")
    return True


# ======================================================================
# RUN BOTH FLOORS
# ======================================================================
if __name__ == "__main__":
    print("=" * 72)
    print("RE-EXPORT DXF -> A4 LANDSCAPE PDF  (10mm MARGINS ALL AROUND)")
    print("=" * 72)

    jobs = [
        (
            DXF_DIR / "BA-Refined-Ground-Floor-Plan.dxf",
            PDF_DIR / "BA-Refined-Ground-Floor-Plan-10mmMargin-A4Landscape-rev2.pdf",
            "GROUND FLOOR",
        ),
        (
            DXF_DIR / "BA-Refined-First-Floor-Plan.dxf",
            PDF_DIR / "BA-Refined-First-Floor-Plan-10mmMargin-A4Landscape-rev2.pdf",
            "FIRST FLOOR",
        ),
    ]

    all_ok = True
    for dxf, pdf, label in jobs:
        print(f"\n>>>>>  {label}  <<<<<")
        if not dxf.exists():
            print(f"    [SKIP] DXF not found: {dxf}")
            all_ok = False
            continue
        ok = export_dxf_10mm_a4landscape(dxf, pdf)
        if not ok:
            all_ok = False

    print("\n" + "=" * 72)
    if all_ok:
        print("SUCCESS: Both PDFs exported with 10mm margins on A4 Landscape.")
    else:
        print("DONE with warnings — see messages above.")
    print("=" * 72)
