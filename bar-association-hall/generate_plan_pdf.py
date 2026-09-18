#!/usr/bin/env python3
"""Generate a printable, self-contained preliminary G+1 plan PDF.

The source of truth is site_plan.json plus preliminary_plans.json. The PDF is
created through Chromium's headless print-to-PDF path so the generator does
not require a Python PDF package.
"""

from __future__ import annotations

import html
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"


def load_json(name: str) -> dict:
    with (ROOT / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def polygon_area(points: list[tuple[float, float]]) -> float:
    return abs(
        sum(
            points[i][0] * points[(i + 1) % len(points)][1]
            - points[(i + 1) % len(points)][0] * points[i][1]
            for i in range(len(points))
        )
        / 2.0
    )


def envelope(plan: dict) -> list[tuple[float, float]]:
    points = [(float(item["x"]), float(item["y"])) for item in plan["vertices"]]
    s = plan["setbacks_ft"]
    min_x = min(x for x, _ in points)
    max_x = max(x for x, _ in points)
    min_y = min(y for _, y in points)
    max_y = max(y for _, y in points)
    step_x, step_y = points[2]
    return [
        (min_x + s["west"], min_y + s["south"]),
        (step_x - s["east"], min_y + s["south"]),
        (step_x - s["east"], step_y + s["south"]),
        (max_x - s["east"], step_y + s["south"]),
        (max_x - s["east"], max_y - s["north"]),
        (min_x + s["west"], max_y - s["north"]),
    ]


def ft(value: float) -> str:
    whole = int(value)
    inches = round((value - whole) * 12)
    if inches == 12:
        whole += 1
        inches = 0
    return f"{whole}'-{inches}\"" if inches else f"{whole}'-0\""


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def project_svg(plan: dict) -> str:
    plot = [(float(item["x"]), float(item["y"])) for item in plan["vertices"]]
    env = envelope(plan)
    width, height = 700, 760
    margin = 70
    scale = min((width - 2 * margin) / 65, (height - 2 * margin) / 105)

    def xy(point: tuple[float, float]) -> tuple[float, float]:
        x, y = point
        return margin + x * scale, height - margin - y * scale

    def points(items: list[tuple[float, float]]) -> str:
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in map(xy, items))

    labels = [
        (32.5, 99.5, "NORTH 60'-0\""),
        (-5.5, 49, "WEST 98'-0\""),
        (17.5, -2.5, "SOUTH 35'-0\""),
        (61.5, 57, "EAST 5'-0\" setback"),
    ]
    label_svg = "".join(
        f'<text x="{xy((x, y))[0]:.1f}" y="{xy((x, y))[1]:.1f}" '
        f'class="dim">{esc(label)}</text>'
        for x, y, label in labels
    )
    return f"""
    <svg class="plan-svg" viewBox="0 0 {width} {height}" role="img"
         aria-label="Site plan and setback envelope">
      <style>
        .plot {{ fill:#fff1e8; stroke:#a33b1f; stroke-width:2.5; }}
        .env {{ fill:#d8f3e4; stroke:#13795b; stroke-width:2.5; stroke-dasharray:8 5; }}
        .dim {{ fill:#24364b; font: 13px Arial, sans-serif; }}
        .note {{ fill:#637083; font: 11px Arial, sans-serif; }}
      </style>
      <rect width="100%" height="100%" fill="#fbfaf7"/>
      <polygon class="plot" points="{points(plot + [plot[0]])}"/>
      <polygon class="env" points="{points(env + [env[0]])}"/>
      <text x="80" y="40" class="dim">PLOT BOUNDARY</text>
      <text x="80" y="58" class="note">L-shaped rationalized input</text>
      <text x="390" y="40" class="dim">SIMPLE SETBACK ENVELOPE</text>
      <text x="390" y="58" class="note">0' west / 5' north, south, east</text>
      {label_svg}
      <line x1="635" y1="110" x2="635" y2="55" stroke="#24364b" stroke-width="2"/>
      <polygon points="635,45 628,62 642,62" fill="#24364b"/>
      <text x="645" y="58" class="dim">N</text>
      <text x="80" y="725" class="note">Not to scale for construction. Verify by survey and true polygon offset.</text>
    </svg>
    """.strip()


def floor_svg(floor: dict, title: str) -> str:
    width, height = 820, 730
    left, top = 70, 35
    # The full 93 ft north-south envelope must remain inside the viewBox.
    scale = 6.5

    def xy(x: float, y: float) -> tuple[float, float]:
        return left + x * scale, height - top - y * scale

    colors = ["#dceeff", "#eee4ff", "#dff5e8", "#ffe8d6", "#fff5c7", "#e8edf2", "#f9dce9", "#d9f1f0", "#e9e1d0"]
    rooms = floor["rooms"]
    shapes = []
    for index, room in enumerate(rooms):
        x, y, w, h = map(float, (room["x"], room["y"], room["w"], room["h"]))
        px, py = xy(x, y + h)
        rw, rh = w * scale, h * scale
        label = esc(room["name"])
        size = 13 if len(label) < 24 else 10
        graphic = ""
        if "Stair" in room["name"]:
            # A dog-leg public stair: 4 ft clear flights, 11 in treads,
            # 4 ft landings, and a 6 in central wall/rail zone.
            flight_w = 4 * scale
            gap = 0.75 * scale
            landing_h = 4 * scale
            flight_h = 8 * (11 / 12) * scale
            sx = px + max(4, (rw - (2 * flight_w + gap)) / 2)
            sy = py + max(4, (rh - (2 * landing_h + flight_h)) / 2)
            total_w = 2 * flight_w + gap
            graphic = (
                f'<g class="stair">'
                f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{total_w:.1f}" height="{landing_h:.1f}" fill="#f7f7f2" stroke="#24364b" stroke-width="1"/>'
                f'<rect x="{sx:.1f}" y="{sy + landing_h + flight_h:.1f}" width="{total_w:.1f}" height="{landing_h:.1f}" fill="#f7f7f2" stroke="#24364b" stroke-width="1"/>'
                f'<rect x="{sx:.1f}" y="{sy + landing_h:.1f}" width="{flight_w:.1f}" height="{flight_h:.1f}" fill="#ffffff" stroke="#24364b" stroke-width="1"/>'
                f'<rect x="{sx + flight_w + gap:.1f}" y="{sy + landing_h:.1f}" width="{flight_w:.1f}" height="{flight_h:.1f}" fill="#ffffff" stroke="#24364b" stroke-width="1"/>'
                f'<line x1="{sx + flight_w:.1f}" y1="{sy + landing_h:.1f}" x2="{sx + flight_w:.1f}" y2="{sy + landing_h + flight_h:.1f}" stroke="#24364b" stroke-width="2"/>'
                "".join(
                    f'<line x1="{sx:.1f}" y1="{sy + landing_h + i * flight_h / 8:.1f}" x2="{sx + flight_w:.1f}" y2="{sy + landing_h + i * flight_h / 8:.1f}" stroke="#8793a0" stroke-width="0.8"/>'
                    f'<line x1="{sx + flight_w + gap:.1f}" y1="{sy + landing_h + (8 - i) * flight_h / 8:.1f}" x2="{sx + 2 * flight_w + gap:.1f}" y2="{sy + landing_h + (8 - i) * flight_h / 8:.1f}" stroke="#8793a0" stroke-width="0.8"/>'
                    for i in range(1, 8)
                )
                + f'<text x="{sx + total_w / 2:.1f}" y="{sy + landing_h / 2 + 3:.1f}" class="stair-note" text-anchor="middle">4\'-0" LANDING</text>'
                f'<text x="{sx + flight_w / 2:.1f}" y="{sy + landing_h + flight_h / 2:.1f}" class="stair-note" text-anchor="middle">UP</text>'
                f'<text x="{sx + flight_w + gap + flight_w / 2:.1f}" y="{sy + landing_h + flight_h / 2:.1f}" class="stair-note" text-anchor="middle">DOWN</text>'
                f'<text x="{sx + total_w / 2:.1f}" y="{sy + landing_h + flight_h + landing_h / 2 + 3:.1f}" class="stair-note" text-anchor="middle">4\'-0" LANDING</text>'
                f'</g>'
                f'<text x="{px + rw / 2:.1f}" y="{py + rh - 4:.1f}" class="size" text-anchor="middle">4\'-0" CLEAR · 11" TREAD · 6-2/3" RISER</text>'
            )
        else:
            graphic = (
                f'<text x="{px + rw / 2:.1f}" y="{py + rh / 2:.1f}" class="room" '
                f'font-size="{size}" text-anchor="middle">{label}</text>'
                f'<text x="{px + rw / 2:.1f}" y="{py + rh / 2 + 17:.1f}" class="size" '
                f'text-anchor="middle">{ft(w)} × {ft(h)}</text>'
            )
        shapes.append(
            f'<rect x="{px:.1f}" y="{py:.1f}" width="{rw:.1f}" height="{rh:.1f}" '
            f'fill="{colors[index % len(colors)]}" stroke="#24364b" stroke-width="2"/>'
            + graphic
        )
    # The envelope outline is used to make the L-shaped cutout visible.
    env = envelope(load_json("site_plan.json"))
    env_points = " ".join(f"{xy(x, y)[0]:.1f},{xy(x, y)[1]:.1f}" for x, y in env)
    access_graphics = []
    for access in floor.get("access_points", []):
        ax, ay = float(access["coordinate"]["x"]), float(access["coordinate"]["y"])
        mx, my = xy(ax, ay)
        half = float(access["clear_width_ft"]) * scale / 2
        name = access["name"].lower()
        if "hall" in name:
            color = "#a33b1f"
            text_y = my - 9
            label = f'MAIN HALL ENTRY · {ft(float(access["clear_width_ft"]))} CLEAR'
        else:
            color = "#13795b"
            text_y = my + 18
            label = f'INDEPENDENT STAIR ENTRY · {ft(float(access["clear_width_ft"]))} CLEAR'
        access_graphics.append(
            f'<line x1="{mx - half:.1f}" y1="{my:.1f}" x2="{mx + half:.1f}" y2="{my:.1f}" '
            f'stroke="#fbfaf7" stroke-width="5"/>'
            f'<line x1="{mx - half:.1f}" y1="{my:.1f}" x2="{mx + half:.1f}" y2="{my:.1f}" '
            f'stroke="{color}" stroke-width="3"/>'
            f'<polygon points="{mx:.1f},{my - 6:.1f} {mx - 6:.1f},{my + 5:.1f} {mx + 6:.1f},{my + 5:.1f}" fill="{color}"/>'
            f'<text x="{mx:.1f}" y="{text_y:.1f}" class="access" text-anchor="middle">{esc(label)}</text>'
        )
    return f"""
    <svg class="plan-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">
      <style>
        .room {{ fill:#24364b; font: 12px Arial, sans-serif; font-weight:700; }}
        .size {{ fill:#637083; font: 10px Arial, sans-serif; }}
        .note {{ fill:#637083; font: 11px Arial, sans-serif; }}
        .stair-note {{ fill:#24364b; font: 8px Arial, sans-serif; font-weight:700; }}
        .access {{ fill:#a33b1f; font: 9px Arial, sans-serif; font-weight:700; }}
      </style>
      <rect width="100%" height="100%" fill="#fbfaf7"/>
      <polygon points="{env_points}" fill="none" stroke="#13795b" stroke-width="3" stroke-dasharray="8 5"/>
      {''.join(shapes)}
      {''.join(access_graphics)}
      <line x1="70" y1="105" x2="427" y2="105" stroke="#637083" stroke-width="1"/>
      <text x="248" y="98" class="note" text-anchor="middle">UPPER ENVELOPE 55'-0"</text>
      <line x1="45" y1="105" x2="45" y2="710" stroke="#637083" stroke-width="1"/>
      <text x="34" y="410" class="note" text-anchor="middle" transform="rotate(-90 34 410)">MAXIMUM DEPTH 88'-0"</text>
      <text x="70" y="716" class="note">Green dashed line = simple coordinate-derived envelope. 9" external walls / 4-1/2" internal walls shown diagrammatically.</text>
    </svg>
    """.strip()


def schedule_rows(floor: dict) -> str:
    rows = []
    for room in floor["rooms"]:
        area = float(room["w"]) * float(room["h"])
        rows.append(
            f"<tr><td>{esc(room['id'])}</td><td>{esc(room['name'])}</td>"
            f"<td>{ft(float(room['w']))} × {ft(float(room['h']))}</td><td>{area:,.1f}</td></tr>"
        )
    return "".join(rows)


def html_doc(plan: dict, plans: dict) -> str:
    plot = [(float(item["x"]), float(item["y"])) for item in plan["vertices"]]
    plot_area = polygon_area(plot)
    env_area = polygon_area(envelope(plan))
    claimed = float(plan["planning_area_claimed_sqft_per_floor"])
    gf, ff = plans["floors"]["ground"], plans["floors"]["first"]
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Derived G+1 Plan Set</title>
<style>
@page {{ size:A4; margin:0; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; color:#24364b; font-family:Arial, sans-serif; background:#eee; }}
.page {{ width:210mm; min-height:297mm; padding:17mm 16mm 14mm; page-break-after:always; background:#fbfaf7; position:relative; }}
.page:last-child {{ page-break-after:auto; }}
h1 {{ font-size:30px; line-height:1.08; margin:0 0 7px; color:#102238; letter-spacing:-.5px; }}
h2 {{ font-size:20px; margin:0 0 8px; color:#102238; }}
h3 {{ font-size:13px; margin:16px 0 6px; color:#13795b; text-transform:uppercase; letter-spacing:1px; }}
p, li {{ font-size:11px; line-height:1.45; }}
.kicker {{ color:#13795b; font-size:11px; font-weight:bold; text-transform:uppercase; letter-spacing:2px; margin-bottom:13px; }}
.sub {{ color:#637083; font-size:14px; line-height:1.4; max-width:145mm; }}
.rule {{ border:0; border-top:2px solid #d9e1e8; margin:14px 0; }}
.grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:9px; margin:18px 0; }}
.card {{ border:1px solid #d9e1e8; border-radius:8px; padding:10px; background:white; }}
.card .label {{ font-size:9px; text-transform:uppercase; color:#637083; letter-spacing:.7px; }}
.card .value {{ margin-top:5px; font-size:19px; font-weight:bold; color:#13795b; }}
.callout {{ border-left:5px solid #e0a12a; background:#fff5d7; padding:10px 12px; margin:12px 0; }}
.callout strong {{ color:#845d00; }}
.ok {{ border-left-color:#13795b; background:#e8f6ee; }}
.ok strong {{ color:#13795b; }}
.plan-svg {{ width:100%; height:166mm; display:block; border:1px solid #d9e1e8; background:#fbfaf7; }}
.floor-svg {{ width:100%; height:145mm; display:block; border:1px solid #d9e1e8; background:#fbfaf7; }}
table {{ width:100%; border-collapse:collapse; font-size:10px; margin-top:8px; }}
th {{ text-align:left; background:#24364b; color:white; padding:6px; }}
td {{ border-bottom:1px solid #d9e1e8; padding:5px 6px; vertical-align:top; }}
td:last-child, th:last-child {{ text-align:right; }}
.two {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
.footer {{ position:absolute; left:16mm; right:16mm; bottom:7mm; display:flex; justify-content:space-between; color:#8793a0; font-size:9px; border-top:1px solid #d9e1e8; padding-top:5px; }}
.mono {{ font-family:monospace; font-size:10px; }}
ul {{ padding-left:18px; }}
</style></head><body>

<section class="page">
  <div class="kicker">Advocate Chambers · Bar Association Banswara</div>
  <h1>Derived G+1<br>Preliminary Plan Set</h1>
  <p class="sub">A dimensioned architectural preliminary package for a ground-floor Bar Association hall and first-floor Bar Library, derived from the stored L-shaped plot geometry and the room schedule in the repository.</p>
  <hr class="rule">
  <div class="grid">
    <div class="card"><div class="label">Plot geometry</div><div class="value">L-shaped</div><p>98′ west depth · 60′ north · 35′ south</p></div>
    <div class="card"><div class="label">Setbacks used</div><div class="value">0′ / 5′</div><p>West 0′ · North/South/East 5′</p></div>
    <div class="card"><div class="label">Derived envelope</div><div class="value">{env_area:,.1f} sf</div><p>Coordinate-based, per floor</p></div>
  </div>
  <div class="callout"><strong>Important area reconciliation:</strong> the brief carries {claimed:,.0f} sq ft per floor, but the stored coordinates and simple setback envelope calculate {env_area:,.1f} sq ft. This PDF uses {env_area:,.1f} sq ft for the drawn plan. A licensed architect must verify the survey and true polygon offset before approval, procurement, or construction.</div>
  <h3>What is included</h3>
  <ul>
    <li>Site boundary and setback diagram</li>
    <li>Ground-floor hall with a centered long-wall entry, independent stair entry, reception, pantry, toilets, and dais</li>
    <li>First-floor library with the same independent exterior stair access</li>
    <li>Area reconciliation, cost basis, and next-step review checklist</li>
  </ul>
  <h3>Source and status</h3>
  <p>Source context: user-provided hand sketch and planning notes. The photograph shows an earlier smaller dimension set; later notes provide the rationalized 98′/60′/35′ inputs. This is a preliminary planning study, not a construction, approval, fire-NOC, or structural drawing.</p>
  <div class="footer"><span>Revision B · 17 September 2026</span><span>Planning study only</span></div>
</section>

<section class="page">
  <div class="kicker">01 · Site geometry</div>
  <h2>Plot and setback envelope</h2>
  <p>The plotted polygon follows the repository's rationalized coordinates. The green dashed outline is the simple coordinate-derived envelope used for the floor plans.</p>
  {project_svg(plan)}
  <div class="two">
    <div><h3>Stored dimensions</h3><table>
      <tr><th>Edge / input</th><th>Value</th></tr>
      <tr><td>North width</td><td>60′-0″</td></tr>
      <tr><td>South width</td><td>35′-0″</td></tr>
      <tr><td>West depth</td><td>98′-0″</td></tr>
      <tr><td>East step</td><td>12′-0″ + 16′-6″</td></tr>
    </table></div>
    <div><h3>Area check</h3><table>
      <tr><th>Measure</th><th>Area</th></tr>
      <tr><td>Polygon from coordinates</td><td>{plot_area:,.1f} sf</td></tr>
      <tr><td>Simple setback envelope</td><td>{env_area:,.1f} sf</td></tr>
      <tr><td>Brief assumption</td><td>{claimed:,.1f} sf</td></tr>
    </table></div>
  </div>
  <div class="footer"><span>Advocate Chambers · Banswara</span><span>Site diagram</span></div>
</section>

<section class="page">
  <div class="kicker">02 · Ground floor</div>
  <h2>Bar Association Hall</h2>
  <p>The main hall entry is centered on the 55′ south long wall and reached through the public lobby. The stair has a separate south exterior entry, so first-floor visitors do not pass through the ground-floor hall. The west zero-setback edge is shown as a blank wall; the east-side exit remains a review placeholder.</p>
  {floor_svg(gf, "Ground floor plan")}
  <table><tr><th>ID</th><th>Space</th><th>Nominal size</th><th>Area sf</th></tr>{schedule_rows(gf)}</table>
  <div class="footer"><span>Advocate Chambers · Banswara</span><span>Ground floor · Preliminary</span></div>
</section>

<section class="page">
  <div class="kicker">03 · First floor</div>
  <h2>Bar Library + Pantry</h2>
  <p>The stair, pantry, and wet areas are stacked over the ground-floor service core. First-floor visitors use the independent exterior stair entry. Reading and stack zones occupy the upper wing; shelving loads and escape capacity require engineering review.</p>
  {floor_svg(ff, "First floor plan")}
  <table><tr><th>ID</th><th>Space</th><th>Nominal size</th><th>Area sf</th></tr>{schedule_rows(ff)}</table>
  <div class="footer"><span>Advocate Chambers · Banswara</span><span>First floor · Preliminary</span></div>
</section>

<section class="page">
  <div class="kicker">04 · Decisions before design development</div>
  <h2>Cost basis and review plan</h2>
  <div class="callout ok"><strong>Recommended next move:</strong> commission a site survey and ask the architect/engineer to resolve the area discrepancy before treating the room sizes or estimate as final.</div>
  <h3>Planning estimate carried in the repository</h3>
  <table>
    <tr><th>Item</th><th>Basis</th><th>Amount (₹)</th></tr>
    <tr><td>Ground floor construction</td><td>4,785 sf × ₹1,850</td><td>88,52,250</td></tr>
    <tr><td>First floor construction</td><td>4,785 sf × ₹1,850</td><td>88,52,250</td></tr>
    <tr><td>Construction subtotal</td><td>9,570 sf × ₹1,850</td><td>1,77,04,500</td></tr>
    <tr><td>Electrical centage + development</td><td>12% + 10% of subtotal</td><td>38,94,990</td></tr>
    <tr><td>Special fixtures</td><td>Lump sum</td><td>10,00,000</td></tr>
    <tr><td>QA + contingencies</td><td>1% + 1.5% of A+B</td><td>5,64,987</td></tr>
    <tr><td>Prorata charges</td><td>13% of A+B+C</td><td>30,11,382</td></tr>
    <tr><td><strong>Rounded planning total</strong></td><td>Not a tender value</td><td><strong>₹2,61,75,859</strong></td></tr>
  </table>
  <div class="two">
    <div><h3>Technical checks</h3><ul>
      <li>Confirm zero-west setback legality, fire separation, waterproofing, scaffolding, and maintenance access.</li>
      <li>Confirm occupant load, stair width, exits, travel distance, accessible route, and toilet clearances.</li>
      <li>Coordinate structural grid, foundation, soil, shelving loads, and roof water tank.</li>
    </ul></div>
    <div><h3>Repository outputs</h3><ul>
      <li><span class="mono">site_plan.json</span> and <span class="mono">preliminary_plans.json</span></li>
      <li>Ground and first-floor SVG review drawings</li>
      <li>Cost, structural, MEP, amenities, and source notes</li>
      <li>This PDF plus the reproducible generator script</li>
    </ul></div>
  </div>
  <p class="sub">The ₹1,850/sq ft estimate intentionally retains the brief's 4,785 sq ft assumption. Reprice after the survey and coordinated design fix the final plinth area.</p>
  <div class="footer"><span>Advocate Chambers · Banswara</span><span>Review actions</span></div>
</section>
</body></html>"""


def main() -> int:
    plan = load_json("site_plan.json")
    plans = load_json("preliminary_plans.json")
    OUT.mkdir(exist_ok=True)
    html_path = OUT / "derived_g_plus_1_plan.html"
    pdf_path = ROOT / "derived_g_plus_1_plan.pdf"
    (ROOT / "ground_floor_preliminary.svg").write_text(
        floor_svg(plans["floors"]["ground"], "Ground floor architectural preliminary plan"),
        encoding="utf-8",
    )
    (ROOT / "first_floor_preliminary.svg").write_text(
        floor_svg(plans["floors"]["first"], "First floor architectural preliminary plan"),
        encoding="utf-8",
    )
    html_path.write_text(html_doc(plan, plans), encoding="utf-8")

    browser = shutil.which("chromium") or shutil.which("google-chrome")
    if not browser:
        print(f"HTML written to {html_path}; Chromium was not found, so PDF was not generated.", file=sys.stderr)
        return 2
    command = [
        browser,
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--allow-file-access-from-files",
        f"--print-to-pdf={pdf_path}",
        f"file://{html_path}",
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"Generated {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())