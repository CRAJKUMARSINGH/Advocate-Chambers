"""Generate coordinated A2 PDF sheets and editable DXF plans.

The JSON files under source/ are authoritative. PDF and DXF are derived
artifacts and may be regenerated at any time.
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
PDF_DIR = ROOT / "PDF"
CAD_DIR = ROOT / "CAD"
MANIFEST = ROOT / "manifest.json"
PAGE_W, PAGE_H = landscape(A2)
SCALE = 0.80  # points per model inch; plotted scale is approximately 1/8" = 1'-0"
BLACK = colors.HexColor("#192530")
GRAY = colors.HexColor("#65717a")
LIGHT = colors.HexColor("#e9eef0")
PALE = colors.HexColor("#f6f8f8")
ACCENT = colors.HexColor("#2e5c62")
RED = colors.HexColor("#8b3c32")


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
    ox, oy = ax + offset[0], ay + offset[1]
    c.saveState()
    c.setStrokeColor(GRAY)
    c.setLineWidth(0.65)
    if abs(bx - ax) >= abs(by - ay):
        oy = min(ay, by) + offset[1]
        c.line(ax, ay, ax, oy)
        c.line(bx, by, bx, oy)
        c.line(ax, oy, bx, oy)
        draw_arrow(c, ax, oy, 0)
        draw_arrow(c, bx, oy, math.pi)
        tx, ty = (ax + bx) / 2, oy + 8
    else:
        ox = min(ax, bx) + offset[0]
        c.line(ax, ay, ox, ay)
        c.line(bx, by, ox, by)
        c.line(ox, ay, ox, by)
        draw_arrow(c, ox, ay, math.pi / 2)
        draw_arrow(c, ox, by, -math.pi / 2)
        tx, ty = ox - 12, (ay + by) / 2
    c.setFillColor(GRAY)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(tx, ty, label)
    c.restoreState()


def draw_north(c: canvas.Canvas, x: float, y: float) -> None:
    c.saveState()
    c.setStrokeColor(BLACK)
    c.setFillColor(BLACK)
    c.setLineWidth(1)
    c.line(x, y, x, y + 30)
    draw_arrow(c, x, y + 30, math.pi / 2, 10)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(x, y + 42, "N")
    c.setFont("Helvetica", 7)
    c.drawCentredString(x, y - 12, "NORTH")
    c.restoreState()


def draw_title_block(c: canvas.Canvas, sheet: dict[str, Any], level_name: str) -> None:
    x, y, w, h = 790, 34, PAGE_W - 824, 112
    c.saveState()
    c.setStrokeColor(BLACK)
    c.setLineWidth(1)
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.line(x, y + 34, x + w, y + 34)
    c.line(x + 120, y, x + 120, y + h)
    c.line(x + w - 156, y, x + w - 156, y + h)
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(x + 12, y + h - 24, "BAR ASSOCIATION HALL")
    c.setFont("Helvetica", 8)
    c.drawString(x + 12, y + h - 39, "BANSWARA, RAJASTHAN")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 12, y + 14, "PRELIMINARY / SCHEMATIC")
    c.setFont("Helvetica", 8)
    c.drawString(x + 132, y + 19, level_name.upper())
    c.drawString(x + 132, y + 8, "NOT FOR CONSTRUCTION")
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(x + w - 78, y + 73, sheet["number"])
    c.setFont("Helvetica", 8)
    c.drawCentredString(x + w - 78, y + 57, "SHEET")
    c.drawCentredString(x + w - 78, y + 16, "REV P01")
    c.restoreState()


def draw_legend(c: canvas.Canvas, x: float, y: float, plans: dict[str, Any]) -> None:
    c.saveState()
    c.setFillColor(PALE)
    c.setStrokeColor(colors.HexColor("#c7d0d4"))
    c.roundRect(x, y, 430, 188, 4, stroke=1, fill=1)
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 14, y + 166, "DRAWING NOTES")
    c.setFont("Helvetica", 8)
    lines = [
        "1. Dimensions are in feet and inches unless noted otherwise.",
        "2. Cut walls are heavy; partitions and fixtures are lighter for legibility.",
        "3. D-tags identify door openings; W-tags identify window openings.",
        "4. Door symbols include a wall break, hinge, leaf, and 90° swing arc.",
        "5. Stair is a two-flight 180° dog-leg with a connecting landing.",
        "6. Confirm all dimensions against survey and issued consultant drawings.",
        "7. Local code, fire, accessibility, structure, MEP, and authority review remain required.",
    ]
    y_line = y + 148
    for line in lines:
        c.drawString(x + 14, y_line, line)
        y_line -= 16
    c.setStrokeColor(BLACK)
    c.setLineWidth(2.2)
    c.line(x + 14, y + 25, x + 44, y + 25)
    c.setLineWidth(0.75)
    c.line(x + 80, y + 25, x + 110, y + 25)
    c.setFont("Helvetica", 7)
    c.drawString(x + 50, y + 22, "CUT WALL")
    c.drawString(x + 116, y + 22, "PARTITION / OPENING")
    c.restoreState()


def draw_schedule(c: canvas.Canvas, x: float, y: float, spaces: list[dict[str, Any]]) -> None:
    width = 430
    row_h = 20
    height = row_h * (len(spaces) + 2)
    c.saveState()
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#aebac0"))
    c.rect(x, y, width, height, stroke=1, fill=1)
    c.setFillColor(ACCENT)
    c.rect(x, y + height - row_h, width, row_h, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 8, y + height - 12, "SPACE SCHEDULE")
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x + 8, y + height - 31, "ID")
    c.drawString(x + 48, y + height - 31, "SPACE")
    c.drawRightString(x + width - 8, y + height - 31, "AREA SF")
    c.setStrokeColor(colors.HexColor("#d6dde0"))
    for index, space in enumerate(spaces):
        yy = y + height - row_h * (index + 3)
        c.line(x, yy, x + width, yy)
        c.setFillColor(BLACK)
        c.setFont("Helvetica", 7)
        c.drawString(x + 8, yy + 5, space["id"])
        c.drawString(x + 48, yy + 5, space["name"][:42])
        c.drawRightString(x + width - 8, yy + 5, f"{area(space):,.1f}")
    c.restoreState()


def space_geometry(space: dict[str, Any], opening: dict[str, Any]) -> tuple[float, float, float, float]:
    return rect(space)


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
    c.setStrokeColor(colors.white)
    c.setLineWidth(6)
    c.line(*a, *b)
    c.setStrokeColor(RED)
    c.setLineWidth(0.8)
    wall = door["wall"]
    horizontal = wall in {"north", "south"}
    if horizontal:
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
        hinge = a
        sign = 1 if wall == "west" else -1
        if door.get("swing") == "out":
            sign *= -1
        leaf_end = (b[0] + sign * (b[1] - a[1]), b[1])
        c.line(*hinge, *leaf_end)
        radius = abs(b[1] - a[1])
        c.arc(hinge[0] - radius if sign < 0 else hinge[0], hinge[1] - radius if sign < 0 else hinge[1], hinge[0] + radius if sign > 0 else hinge[0], hinge[1] + radius if sign > 0 else hinge[1], 0 if sign > 0 else 90, 90 if sign > 0 else 180)
        tag_x, tag_y = a[0] + sign * 11, (a[1] + b[1]) / 2
    c.setFillColor(RED)
    c.setFont("Helvetica-Bold", 6)
    c.drawCentredString(tag_x, tag_y, door["tag"])
    c.restoreState()


def draw_window(c: canvas.Canvas, origin: tuple[float, float], space: dict[str, Any], window: dict[str, Any]) -> None:
    (x0, y0), (x1, y1) = wall_segment(space, window["wall"], window["offset"], window["width"])
    a = pdf_point(origin, x0, y0)
    b = pdf_point(origin, x1, y1)
    c.saveState()
    c.setStrokeColor(colors.white)
    c.setLineWidth(7)
    c.line(*a, *b)
    c.setStrokeColor(colors.HexColor("#386e8b"))
    c.setLineWidth(1.5)
    c.line(*a, *b)
    if window["wall"] in {"north", "south"}:
        c.line(a[0], a[1] - 3, b[0], b[1] - 3)
        tx, ty = (a[0] + b[0]) / 2, a[1] + 8
    else:
        c.line(a[0] + 3, a[1], b[0] + 3, b[1])
        tx, ty = a[0] + 8, (a[1] + b[1]) / 2
    c.setFillColor(colors.HexColor("#386e8b"))
    c.setFont("Helvetica-Bold", 6)
    c.drawCentredString(tx, ty, window["tag"])
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
    # Two equal parallel flights with a real intermediate landing.
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
    c.setLineWidth(1.4)
    c.rect(landing_x, landing_y, stair["landingDepth"] * SCALE, lane_gap, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(ACCENT)
    c.drawString(ox + 8, oy + 18, f'UP 18R @ {stair["riser"]:.2f}" / {stair["tread"]:.0f}" T')
    c.drawString(ox + 8, oy + 8, f'F.F. = {inches_feet(stair["floorToFloor"])}')
    c.setFillColor(BLACK)
    c.setFont("Helvetica", 6)
    c.drawString(landing_x + 6, landing_y + lane_gap / 2, "LANDING")
    c.restoreState()


def draw_entry_features(
    c: canvas.Canvas,
    origin: tuple[float, float],
    plans: dict[str, Any],
    spaces: list[dict[str, Any]],
    level: str,
) -> None:
    """Show entry importance and the porch without hiding design assumptions."""
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
        c.setFillColor(RED)
        c.setStrokeColor(RED)
        c.setFont("Helvetica-Bold", 7 if entry["kind"] == "main" else 6)
        if entry["wall"] == "south":
            label_y = a[1] - 22
            c.drawCentredString(mid_x, label_y, entry["label"])
        elif entry["wall"] == "east":
            c.translate(mid_x + 24, mid_y)
            c.rotate(90)
            c.drawCentredString(0, 0, entry["label"])
        else:
            c.drawCentredString(mid_x, mid_y + 18, entry["label"])
        if entry["kind"] == "main" and entry.get("porch"):
            porch = entry["porch"]
            width = porch["width"]
            depth = porch["depth"]
            cx = (a_model[0] + b_model[0]) / 2
            x0 = cx - width / 2
            y0 = min(a_model[1], b_model[1]) - depth
            px, py = pdf_point(origin, x0, y0)
            c.setDash(4, 3)
            c.setLineWidth(1)
            c.rect(px, py, width * SCALE, depth * SCALE, stroke=1, fill=0)
            c.setDash()
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(px + width * SCALE / 2, py + depth * SCALE / 2, porch["label"])
            c.setFont("Helvetica", 5)
            c.drawCentredString(px + width * SCALE / 2, py + depth * SCALE / 2 - 9, "PROVISIONAL")
        c.restoreState()


def draw_furniture(c: canvas.Canvas, origin: tuple[float, float], space: dict[str, Any]) -> None:
    x0, y0, x1, y1 = rect(space)
    if "Assembly Hall" in space["name"]:
        c.saveState()
        c.setStrokeColor(colors.HexColor("#b9c1c4"))
        c.setLineWidth(0.45)
        for row in range(5):
            yy = y0 + 110 + row * 58
            for column in range(10):
                xx = x0 + 65 + column * 56
                c.circle(*pdf_point(origin, xx, yy), 3, stroke=1, fill=0)
        c.restoreState()
    if "Library Reading" in space["name"]:
        c.saveState()
        c.setStrokeColor(colors.HexColor("#82979d"))
        c.setLineWidth(0.6)
        for row in range(6):
            yy = y0 + 80 + row * 56
            c.line(*pdf_point(origin, x0 + 90, yy), *pdf_point(origin, x1 - 90, yy))
        c.restoreState()
    if "Stack Area" in space["name"]:
        c.saveState()
        c.setStrokeColor(colors.HexColor("#82979d"))
        c.setLineWidth(0.8)
        for row in range(7):
            yy = y0 + 35 + row * 23
            c.line(*pdf_point(origin, x0 + 60, yy), *pdf_point(origin, x1 - 60, yy))
        c.restoreState()


def draw_plan_sheet(c: canvas.Canvas, site: dict[str, Any], plans: dict[str, Any], level: str, sheet: dict[str, Any]) -> None:
    spaces = [space for space in plans["spaces"] if space["level"] == level]
    c.setTitle(f'{site["project"]["name"]} - {sheet["title"]}')
    c.setAuthor("Parametric planning drawing generator")
    c.setStrokeColor(BLACK)
    c.setLineWidth(1.2)
    c.rect(28, 28, PAGE_W - 56, PAGE_H - 56, stroke=1, fill=0)
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(64, PAGE_H - 58, f'{sheet["number"]}  |  {sheet["title"].upper()}')
    c.setFont("Helvetica", 8)
    c.drawString(64, PAGE_H - 73, "BAR ASSOCIATION HALL · BANSWARA · COORDINATED MODEL P01 · SCHEMATIC")

    origin = (78, 178)
    c.saveState()
    c.setFillColor(colors.white)
    c.setStrokeColor(BLACK)
    c.setLineWidth(1.2)
    for space in spaces:
        x0, y0, x1, y1 = rect(space)
        sx, sy = pdf_point(origin, x0, y0)
        sw, sh = (x1 - x0) * SCALE, (y1 - y0) * SCALE
        fill = colors.HexColor("#ffffff")
        if space["finish"] == "public":
            fill = colors.HexColor("#f4f5f3")
        elif space["finish"] == "service":
            fill = colors.HexColor("#eef4f4")
        elif space["finish"] == "circulation":
            fill = colors.HexColor("#f5eee5")
        c.setFillColor(fill)
        c.setStrokeColor(colors.HexColor("#718087"))
        c.setLineWidth(0.75)
        c.rect(sx, sy, sw, sh, stroke=1, fill=1)
        draw_furniture(c, origin, space)
        c.setFillColor(BLACK)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(sx + sw / 2, sy + sh / 2 + 5, space["name"].upper())
        c.setFont("Helvetica", 7)
        c.drawCentredString(sx + sw / 2, sy + sh / 2 - 8, f'{inches_feet(x1 - x0)} × {inches_feet(y1 - y0)}')
        c.setFont("Helvetica", 6.5)
        c.setFillColor(GRAY)
        c.drawCentredString(sx + sw / 2, sy + sh / 2 - 19, f'{space["id"]}  ·  {area(space):,.1f} SF')
    # Apply a clear cut-wall perimeter and the building extent dimensions.
    min_x = min(rect(s)[0] for s in spaces)
    min_y = min(rect(s)[1] for s in spaces)
    max_x = max(rect(s)[2] for s in spaces)
    max_y = max(rect(s)[3] for s in spaces)
    px, py = pdf_point(origin, min_x, min_y)
    c.setStrokeColor(BLACK)
    c.setLineWidth(2.4)
    c.rect(px, py, (max_x - min_x) * SCALE, (max_y - min_y) * SCALE, stroke=1, fill=0)
    c.restoreState()

    space_by_id = {space["id"]: space for space in spaces}
    for opening in plans["openings"]:
        if opening["level"] == level:
            draw_door(c, origin, space_by_id[opening["hostSpace"]], opening)
    for window in plans["windows"]:
        if window["level"] == level:
            draw_window(c, origin, space_by_id[window["hostSpace"]], window)
    stair_space = next((space for space in spaces if space.get("stairId") == "STAIR-01"), None)
    if stair_space:
        draw_stair(c, origin, stair_space, plans["stairs"][0])
    draw_entry_features(c, origin, plans, spaces, level)

    draw_dimension(c, origin, (min_x, min_y), (max_x, min_y), (0, -52), inches_feet(max_x - min_x))
    draw_dimension(c, origin, (min_x, min_y), (min_x, max_y), (-62, 0), inches_feet(max_y - min_y))
    draw_north(c, 690, PAGE_H - 136)
    draw_legend(c, 820, PAGE_H - 370, plans)
    draw_schedule(c, 820, 230, spaces)
    draw_title_block(c, sheet, site["levels"][0 if level == "GF" else 1]["name"])
    c.showPage()


def create_dxf(site: dict[str, Any], plans: dict[str, Any], level: str, filename: Path) -> None:
    doc = ezdxf.new("R2018")
    doc.units = 1  # inches
    for layer, color in [
        ("A-WALL", 7),
        ("A-DOOR", 1),
        ("A-WINDOW", 4),
        ("A-FURN", 8),
        ("A-DIM", 2),
        ("A-TEXT", 7),
        ("A-STAI R", 3),
        ("A-TTLB", 7),
    ]:
        safe_layer = layer.replace(" ", "-")
        if safe_layer not in doc.layers:
            doc.layers.add(safe_layer, color=color)
    msp = doc.modelspace()
    spaces = [space for space in plans["spaces"] if space["level"] == level]
    for space in spaces:
        x0, y0, x1, y1 = rect(space)
        msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], dxfattribs={"layer": "A-WALL", "closed": True})
        msp.add_text(space["name"].upper(), dxfattribs={"layer": "A-TEXT", "height": 8}).set_placement(((x0 + x1) / 2, (y0 + y1) / 2), align=TextEntityAlignment.MIDDLE_CENTER)
        msp.add_text(space["id"], dxfattribs={"layer": "A-TEXT", "height": 5}).set_placement(((x0 + x1) / 2, (y0 + y1) / 2 - 12), align=TextEntityAlignment.MIDDLE_CENTER)
        draw = next((item for item in plans["openings"] if item["hostSpace"] == space["id"] and item["level"] == level), None)
        if draw:
            (a, b) = wall_segment(space, draw["wall"], draw["offset"], draw["width"])
            msp.add_line(a, b, dxfattribs={"layer": "A-DOOR"})
    for opening in plans["openings"]:
        if opening["level"] != level:
            continue
        space = next(space for space in spaces if space["id"] == opening["hostSpace"])
        a, b = wall_segment(space, opening["wall"], opening["offset"], opening["width"])
        msp.add_text(opening["tag"], dxfattribs={"layer": "A-DOOR", "height": 5}).set_placement(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), align=TextEntityAlignment.MIDDLE_CENTER)
    for entry in plans.get("entries", []):
        if entry["level"] != level:
            continue
        host = next(space for space in spaces if space["id"] == entry["hostSpace"])
        opening = next(opening for opening in plans["openings"] if opening["id"] == entry["openingId"])
        a, b = wall_segment(host, opening["wall"], opening["offset"], opening["width"])
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        msp.add_text(entry["label"], dxfattribs={"layer": "A-DOOR", "height": 6}).set_placement(mid, align=TextEntityAlignment.MIDDLE_CENTER)
        if entry["kind"] == "main" and entry.get("porch"):
            porch = entry["porch"]
            cx = mid[0]
            y0 = min(a[1], b[1]) - porch["depth"]
            x0 = cx - porch["width"] / 2
            msp.add_lwpolyline(
                [(x0, y0), (x0 + porch["width"], y0), (x0 + porch["width"], y0 + porch["depth"]), (x0, y0 + porch["depth"]), (x0, y0)],
                dxfattribs={"layer": "A-DOOR", "closed": True},
            )
            msp.add_text("MAIN ENTRY PORCH / PROVISIONAL", dxfattribs={"layer": "A-DOOR", "height": 5}).set_placement(
                (cx, y0 + porch["depth"] / 2), align=TextEntityAlignment.MIDDLE_CENTER
            )
    stair_space = next((space for space in spaces if space.get("stairId") == "STAIR-01"), None)
    if stair_space:
        x0, y0, _, _ = rect(stair_space)
        stair = plans["stairs"][0]
        run = (stair["riserCountPerFlight"] - 1) * stair["tread"]
        for base_y, reverse in [(y0 + 58, False), (y0 + 150, True)]:
            for step in range(stair["riserCountPerFlight"]):
                xx = x0 + 10 + (stair["riserCountPerFlight"] - 1 - step if reverse else step) * stair["tread"]
                msp.add_line((xx, base_y), (xx, base_y + stair["width"]), dxfattribs={"layer": "A-STAI-R"})
            msp.add_line((x0 + 10, base_y), (x0 + 10 + run, base_y), dxfattribs={"layer": "A-STAI-R"})
            msp.add_line((x0 + 10, base_y + stair["width"]), (x0 + 10 + run, base_y + stair["width"]), dxfattribs={"layer": "A-STAI-R"})
        msp.add_text("UP", dxfattribs={"layer": "A-STAI-R", "height": 6}).set_placement((x0 + 48, y0 + 86), align=TextEntityAlignment.MIDDLE_CENTER)
    msp.add_text(f'{site["project"]["name"]} · {level} · SCHEMATIC', dxfattribs={"layer": "A-TTLB", "height": 10}).set_placement((0, -36))
    doc.saveas(filename)


def write_manifest(site: dict[str, Any], plans: dict[str, Any], outputs: list[str], validation: list[str]) -> None:
    source_hash = hashlib.sha256()
    for path in sorted((ROOT / "source").glob("*.json")):
        source_hash.update(path.read_bytes())
    data = {
        "project": site["project"]["name"],
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "sourceSha256": source_hash.hexdigest(),
        "generator": "generate_standard_drawings.py",
        "status": "pass" if not validation else "fail",
        "outputs": outputs,
        "validationErrors": validation,
        "sheetSize": "A2 landscape",
        "declaredPlotScale": '1/8" = 1\'-0" approximate',
        "professionalStatus": "schematic",
        "notes": [
            "DXF is R2018-compatible and uses model units of inches.",
            "The uploaded PDFs are retained under references/original and are not used as geometry source.",
            "This package is not for construction and requires survey, code, fire, accessibility, structural, MEP, and licensed review.",
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
    sheets = [
        ("GF", {"number": "A-101", "title": "Ground Floor Plan", "file": "A-101-Ground-Floor-Plan.pdf"}),
        ("FF", {"number": "A-102", "title": "First Floor Plan", "file": "A-102-First-Floor-Plan.pdf"}),
    ]
    pdfs: list[Path] = []
    for level, sheet in sheets:
        pdf_path = PDF_DIR / sheet["file"]
        c = canvas.Canvas(str(pdf_path), pagesize=landscape(A2))
        draw_plan_sheet(c, site, plans, level, sheet)
        c.save()
        pdfs.append(pdf_path)
        outputs.append(str(pdf_path.relative_to(ROOT)))
        dxf_path = CAD_DIR / f'{sheet["number"]}-{level}-Plan-R2018.dxf'
        create_dxf(site, plans, level, dxf_path)
        outputs.append(str(dxf_path.relative_to(ROOT)))

    review_path = PDF_DIR / "Bar-Association-Standard-Review-Set.pdf"
    writer = PdfWriter()
    for pdf in pdfs:
        for page in PdfReader(str(pdf)).pages:
            writer.add_page(page)
    with review_path.open("wb") as handle:
        writer.write(handle)
    outputs.append(str(review_path.relative_to(ROOT)))
    write_manifest(site, plans, outputs, errors)
    print(json.dumps({"status": "pass", "outputs": outputs, "manifest": str(MANIFEST.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())