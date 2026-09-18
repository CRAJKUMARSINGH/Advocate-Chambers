"""Shared source loading and geometry checks for the bar association drawing set."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "standard" / "source" if (ROOT / "standard" / "source").exists() else ROOT / "source"


def load_model() -> tuple[dict[str, Any], dict[str, Any]]:
    site = json.loads((SOURCE / "site_plan.json").read_text())
    plans = json.loads((SOURCE / "preliminary_plans.json").read_text())
    return site, plans


def rect(space: dict[str, Any]) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = (float(value) for value in space["rect"])
    return x0, y0, x1, y1


def area(space: dict[str, Any]) -> float:
    x0, y0, x1, y1 = rect(space)
    return abs(x1 - x0) * abs(y1 - y0) / 144


def inches_feet(value: float) -> str:
    feet = int(value // 12)
    inches = round(value - feet * 12)
    if inches == 12:
        feet += 1
        inches = 0
    return f'''{feet}'-{inches}"'''


def validate_model(site: dict[str, Any], plans: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plans.get("units") != "inch":
        errors.append("The drawing model must use inches as its sole internal unit.")
    if float(plans.get("wallThickness", 0)) <= 0:
        errors.append("Wall thickness must be greater than zero.")

    spaces = plans["spaces"]
    ids = [space["id"] for space in spaces]
    if len(ids) != len(set(ids)):
        errors.append("Space IDs must be unique.")

    for space in spaces:
        x0, y0, x1, y1 = rect(space)
        if x1 <= x0 or y1 <= y0:
            errors.append(f'{space["id"]}: rectangle must have positive width and height.')

    for index, first in enumerate(spaces):
        ax0, ay0, ax1, ay1 = rect(first)
        for second in spaces[index + 1 :]:
            if first["level"] != second["level"]:
                continue
            bx0, by0, bx1, by1 = rect(second)
            overlap_w = min(ax1, bx1) - max(ax0, bx0)
            overlap_h = min(ay1, by1) - max(ay0, by0)
            if overlap_w > 0 and overlap_h > 0:
                errors.append(f'{first["id"]} overlaps {second["id"]}.')

    space_by_id = {space["id"]: space for space in spaces}
    for opening in plans["openings"] + plans["windows"]:
        host = space_by_id.get(opening["hostSpace"])
        if not host:
            errors.append(f'{opening["id"]}: host space {opening["hostSpace"]} does not exist.')
            continue
        x0, y0, x1, y1 = rect(host)
        span = x1 - x0 if opening["wall"] in {"north", "south"} else y1 - y0
        if opening["offset"] < 0 or opening["offset"] + opening["width"] > span:
            errors.append(f'{opening["id"]}: opening does not fit on its host wall.')

    for stair in plans["stairs"]:
        expected = stair["riserCountPerFlight"] * stair["flightCount"]
        if expected != stair["riserCountTotal"]:
            errors.append(f'{stair["id"]}: flight riser counts do not equal total risers.')
        rise = stair["riserCountTotal"] * stair["riser"]
        if abs(rise - stair["floorToFloor"]) > 0.1:
            errors.append(
                f'{stair["id"]}: riser arithmetic gives {rise:.2f} in, '
                f'not {stair["floorToFloor"]:.2f} in floor-to-floor.'
            )
        if stair["landingDepth"] < stair["width"]:
            errors.append(f'{stair["id"]}: landing depth is less than stair width.')
        if stair["kind"] != "dog-leg" or stair["turn"] != "180-deg":
            errors.append(f'{stair["id"]}: stair is not a 180-degree dog-leg stair.')

    if len(site.get("site", {}).get("plot", [])) < 3:
        errors.append("The site plot must contain at least three vertices.")
    if not any("Door symbols show a wall break" in note for note in plans.get("notes", [])):
        errors.append("Door notation note is missing from the source model.")
    entry_ids = {entry["id"] for entry in plans.get("entries", [])}
    if "ENTRY-MAIN" not in entry_ids:
        errors.append("The source model must explicitly identify the primary main entry.")
    for entry in plans.get("entries", []):
        if entry["openingId"] not in {opening["id"] for opening in plans["openings"]}:
            errors.append(f'{entry["id"]}: referenced opening does not exist.')
        if entry.get("kind") == "main" and "porch" not in entry:
            errors.append(f'{entry["id"]}: main entry is missing a porch coordination zone.')
    return errors