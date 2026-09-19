"""Shared source loading and geometry checks for the bar association drawing set.

Week 1 adds structured findings without changing the source-model contract.
``validate_model`` remains a string-list compatibility wrapper for the existing
generators and API; new callers should use ``validate_model_findings``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "standard" / "source" if (ROOT / "standard" / "source").exists() else ROOT / "source"
sys.path.insert(0, str(ROOT.parent / "scripts"))

from week2 import canonical_to_legacy, load_canonical_model  # noqa: E402
from week34 import validate_week34  # noqa: E402


def load_model() -> tuple[dict[str, Any], dict[str, Any]]:
    """Load the validated canonical model through the legacy generator view.

    Existing drawing functions still consume the Week 1-shaped dictionaries.
    They receive those dictionaries only after the Week 2 canonical model has
    been loaded and validated, so the source model cannot bypass schema checks.
    """

    canonical = load_canonical_model()
    return canonical_to_legacy(canonical)


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


def _finding(
    finding_id: str,
    severity: str,
    rule: str,
    message: str,
    *,
    level_id: str | None = None,
    space_id: str | None = None,
    opening_ids: list[str] | None = None,
    connector_ids: list[str] | None = None,
    suggested_fixes: list[str] | None = None,
) -> dict[str, Any]:
    """Create the stable Week 1 finding shape described by the roadmap."""

    return {
        "id": finding_id,
        "severity": severity,
        "rule": rule,
        "levelId": level_id,
        "spaceId": space_id,
        "openingIds": opening_ids or [],
        "connectorIds": connector_ids or [],
        "message": message,
        "suggestedFixes": suggested_fixes or [],
    }


def _level_order(site: dict[str, Any], plans: dict[str, Any]) -> dict[str, int]:
    configured = [
        str(level["id"])
        for level in site.get("levels", [])
        if isinstance(level, dict) and level.get("id")
    ]
    if not configured:
        configured = list(dict.fromkeys(str(space.get("level")) for space in plans.get("spaces", [])))
    return {level_id: index for index, level_id in enumerate(configured)}


def _opening_span(space: dict[str, Any], opening: dict[str, Any]) -> float:
    x0, y0, x1, y1 = rect(space)
    return x1 - x0 if opening.get("wall") in {"north", "south"} else y1 - y0


def _opening_fits(space: dict[str, Any], opening: dict[str, Any]) -> bool:
    try:
        offset = float(opening["offset"])
        width = float(opening["width"])
    except (KeyError, TypeError, ValueError):
        return False
    return offset >= 0 and width > 0 and offset + width <= _opening_span(space, opening)


def _wall_coordinate(space: dict[str, Any], wall: str) -> float:
    x0, y0, x1, y1 = rect(space)
    return {"south": y0, "north": y1, "west": x0, "east": x1}[wall]


def _wall_interval(space: dict[str, Any], wall: str, opening: dict[str, Any]) -> tuple[float, float]:
    x0, y0, x1, y1 = rect(space)
    start = float(opening.get("offset", 0))
    end = start + float(opening.get("width", 0))
    if wall in {"north", "south"}:
        return x0 + start, x0 + end
    return y0 + start, y0 + end


def _has_adjacent_space(
    host: dict[str, Any],
    opening: dict[str, Any],
    spaces: list[dict[str, Any]],
    wall_tolerance: float,
) -> bool:
    """Return whether an opening faces another named space on its level.

    The source model uses small partition gaps in a few places, so the
    wall-thickness tolerance intentionally accepts a near-touching adjacent
    room. It does not turn a completely exterior wall into an interior route.
    """

    wall = opening.get("wall")
    if wall not in {"north", "south", "east", "west"}:
        return False
    host_coordinate = _wall_coordinate(host, wall)
    first, second = _wall_interval(host, wall, opening)
    for candidate in spaces:
        if candidate is host or candidate.get("level") != host.get("level"):
            continue
        cx0, cy0, cx1, cy1 = rect(candidate)
        candidate_wall = {"south": "north", "north": "south", "west": "east", "east": "west"}[wall]
        candidate_coordinate = _wall_coordinate(candidate, candidate_wall)
        if abs(host_coordinate - candidate_coordinate) > wall_tolerance:
            continue
        cfirst, csecond = _wall_interval(
            candidate,
            "north" if wall in {"north", "south"} else "east",
            {"offset": 0, "width": 0},
        )
        if wall in {"north", "south"}:
            cfirst, csecond = cx0, cx1
        else:
            cfirst, csecond = cy0, cy1
        if min(second, csecond) - max(first, cfirst) > 0:
            return True
    return False


def _has_intentional_exterior_access(
    opening: dict[str, Any],
    host: dict[str, Any],
    plans: dict[str, Any],
) -> bool:
    """Recognize only explicit exterior-access intent, never proximity."""

    if opening.get("accessZoneId") or opening.get("exteriorAccessZoneId"):
        return True
    if opening.get("exteriorAccess") is True:
        return True
    if host.get("accessZoneId") or host.get("exteriorAccessZoneId"):
        return True
    access_zones = {
        zone.get("id")
        for zone in plans.get("exteriorAccessZones", []) + plans.get("circulationZones", [])
        if isinstance(zone, dict) and zone.get("id")
    }
    referenced_zone = opening.get("accessZoneId") or opening.get("exteriorAccessZoneId")
    if referenced_zone and referenced_zone in access_zones:
        return True
    return any(
        entry.get("openingId") == opening.get("id") and entry.get("porch")
        for entry in plans.get("entries", [])
        if isinstance(entry, dict)
    )


def validate_model_findings(site: dict[str, Any], plans: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate the model and return deterministic, machine-readable findings."""

    findings: list[dict[str, Any]] = []
    spaces = plans.get("spaces", [])
    openings = plans.get("openings", [])
    windows = plans.get("windows", [])
    space_by_id = {space.get("id"): space for space in spaces if space.get("id")}
    level_order = _level_order(site, plans)

    def add(
        finding_id: str,
        severity: str,
        rule: str,
        message: str,
        **kwargs: Any,
    ) -> None:
        findings.append(_finding(finding_id, severity, rule, message, **kwargs))

    if plans.get("units") != "inch":
        add(
            "VAL-MODEL-UNITS",
            "ERROR",
            "MODEL_UNITS_MUST_BE_INCH",
            "The drawing model must use inches as its sole internal unit.",
            suggested_fixes=["Set plans.units to 'inch' and preserve the source dimensions."],
        )
    if float(plans.get("wallThickness", 0)) <= 0:
        add(
            "VAL-MODEL-WALL-THICKNESS",
            "ERROR",
            "WALL_THICKNESS_MUST_BE_POSITIVE",
            "Wall thickness must be greater than zero.",
            suggested_fixes=["Provide a positive wallThickness in model units."],
        )

    ids = [space.get("id") for space in spaces]
    if len(ids) != len(set(ids)):
        add(
            "VAL-MODEL-DUPLICATE-SPACE-ID",
            "ERROR",
            "SPACE_IDS_MUST_BE_UNIQUE",
            "Space IDs must be unique.",
            suggested_fixes=["Assign every space a stable, unique ID."],
        )

    for space in spaces:
        try:
            x0, y0, x1, y1 = rect(space)
        except (KeyError, TypeError, ValueError):
            add(
                f'VAL-GEOM-INVALID-SPACE-{space.get("id", "UNKNOWN")}',
                "ERROR",
                "SPACE_RECTANGLE_MUST_BE_VALID",
                f'{space.get("id", "UNKNOWN")}: rectangle must contain four numeric coordinates.',
                level_id=space.get("level"),
                space_id=space.get("id"),
                suggested_fixes=["Provide rect as [x0, y0, x1, y1] using model units."],
            )
            continue
        if x1 <= x0 or y1 <= y0:
            add(
                f'VAL-GEOM-INVALID-SPACE-{space.get("id", "UNKNOWN")}',
                "ERROR",
                "SPACE_RECTANGLE_MUST_HAVE_AREA",
                f'{space["id"]}: rectangle must have positive width and height.',
                level_id=space.get("level"),
                space_id=space.get("id"),
                suggested_fixes=["Correct the rectangle coordinates or remove the empty space."],
            )

    for index, first in enumerate(spaces):
        try:
            ax0, ay0, ax1, ay1 = rect(first)
        except (KeyError, TypeError, ValueError):
            continue
        for second in spaces[index + 1 :]:
            if first["level"] != second["level"]:
                continue
            try:
                bx0, by0, bx1, by1 = rect(second)
            except (KeyError, TypeError, ValueError):
                continue
            overlap_w = min(ax1, bx1) - max(ax0, bx0)
            overlap_h = min(ay1, by1) - max(ay0, by0)
            if overlap_w > 0 and overlap_h > 0:
                add(
                    f'VAL-GEOM-OVERLAP-{first["id"]}-{second["id"]}',
                    "ERROR",
                    "SPACES_MUST_NOT_OVERLAP",
                    f'{first["id"]} overlaps {second["id"]}.',
                    level_id=first.get("level"),
                    space_id=first.get("id"),
                    suggested_fixes=[
                        f"Move or resize {first['id']} or {second['id']} so their clear rectangles do not overlap."
                    ],
                )

    doors_by_space: dict[str, list[dict[str, Any]]] = {}
    for opening in openings:
        host = space_by_id.get(opening.get("hostSpace"))
        if not host:
            add(
                f'VAL-OPENING-ORPHAN-{opening.get("id", "UNKNOWN")}',
                "ERROR",
                "OPENING_HOST_MUST_EXIST",
                f'{opening.get("id", "UNKNOWN")}: host space {opening.get("hostSpace")} does not exist.',
                level_id=opening.get("level"),
                opening_ids=[opening.get("id", "UNKNOWN")],
                suggested_fixes=["Reference an existing space on the same level."],
            )
            continue
        if opening.get("type", "door") == "door":
            doors_by_space.setdefault(host["id"], []).append(opening)
        if not _opening_fits(host, opening):
            add(
                f'VAL-OPENING-FIT-{opening.get("id", "UNKNOWN")}',
                "ERROR",
                "OPENING_MUST_FIT_HOST_WALL",
                f'{opening.get("id", "UNKNOWN")}: opening does not fit on its host wall.',
                level_id=opening.get("level"),
                space_id=host.get("id"),
                opening_ids=[opening.get("id", "UNKNOWN")],
                suggested_fixes=["Move the opening within the host wall or reduce its width."],
            )

    for window in windows:
        host = space_by_id.get(window.get("hostSpace"))
        if not host:
            add(
                f'VAL-OPENING-ORPHAN-{window.get("id", "UNKNOWN")}',
                "ERROR",
                "OPENING_HOST_MUST_EXIST",
                f'{window.get("id", "UNKNOWN")}: host space {window.get("hostSpace")} does not exist.',
                level_id=window.get("level"),
                opening_ids=[window.get("id", "UNKNOWN")],
                suggested_fixes=["Reference an existing space on the same level."],
            )
        elif not _opening_fits(host, window):
            add(
                f'VAL-OPENING-FIT-{window.get("id", "UNKNOWN")}',
                "ERROR",
                "OPENING_MUST_FIT_HOST_WALL",
                f'{window.get("id", "UNKNOWN")}: opening does not fit on its host wall.',
                level_id=window.get("level"),
                space_id=host.get("id"),
                opening_ids=[window.get("id", "UNKNOWN")],
                suggested_fixes=["Move the opening within the host wall or reduce its width."],
            )

    for space in spaces:
        if not doors_by_space.get(space.get("id")) and space.get("finish") != "circulation":
            add(
                f'VAL-GRAPH-ORPHAN-{space.get("id", "UNKNOWN")}',
                "BLOCKER",
                "ROOM_MUST_HAVE_DOOR",
                f'{space.get("id", "UNKNOWN")} ({space.get("name", "Unnamed space")}) has no modeled door.',
                level_id=space.get("level"),
                space_id=space.get("id"),
                suggested_fixes=[
                    "Add a semantic door connected to a named space or intentional exterior access zone.",
                    "Remove the space if it is not part of the occupied plan.",
                ],
            )

    # Week 1 deliberately checks the known upper-floor exterior-door failure
    # before attempting the full Week 3 route graph. A named adjacent space,
    # explicit access zone, porch, or vertical stair connector is evidence;
    # a door merely drawn on a wall is not.
    for opening in openings:
        if opening.get("type", "door") != "door":
            continue
        host = space_by_id.get(opening.get("hostSpace"))
        if not host or level_order.get(opening.get("level"), 0) == 0:
            continue
        if host.get("stairId"):
            continue
        connected_space = opening.get("connectedSpaceId") or opening.get("sideB")
        if connected_space in space_by_id:
            continue
        if _has_intentional_exterior_access(opening, host, plans):
            continue
        add(
            f'VAL-GRAPH-EXTERIOR-DOOR-{opening.get("id", "UNKNOWN")}',
            "BLOCKER",
            "ROOM_HAS_UNJUSTIFIED_EXTERNAL_DOOR",
            (
                f'{host.get("id")} ({host.get("name", "Unnamed space")}) is on upper level '
                f'{opening.get("level")} and {opening.get("id")} opens to the exterior '
                "without a modeled balcony, landing, stair, corridor, porch, terrace, "
                "or other intentional access zone."
            ),
            level_id=opening.get("level"),
            space_id=host.get("id"),
            opening_ids=[opening.get("id", "UNKNOWN")],
            suggested_fixes=[
                "Connect the room to an internal corridor or reachable stair arrival.",
                "Model an intentional balcony/landing/exterior access zone and its approach.",
                "Remove or relocate the exterior door.",
            ],
        )

    for stair in plans.get("stairs", []):
        expected = stair.get("riserCountPerFlight", 0) * stair.get("flightCount", 0)
        if expected != stair.get("riserCountTotal"):
            add(
                f'VAL-STAIR-COUNT-{stair.get("id", "UNKNOWN")}',
                "ERROR",
                "STAIR_RISER_COUNT_MUST_MATCH_FLIGHTS",
                f'{stair.get("id", "UNKNOWN")}: flight riser counts do not equal total risers.',
                connector_ids=[stair.get("id", "UNKNOWN")],
                suggested_fixes=["Set riserCountTotal to riserCountPerFlight × flightCount."],
            )
        rise = stair.get("riserCountTotal", 0) * stair.get("riser", 0)
        if abs(rise - stair["floorToFloor"]) > 0.1:
            add(
                f'VAL-STAIR-RISE-{stair.get("id", "UNKNOWN")}',
                "ERROR",
                "STAIR_RISER_ARITHMETIC",
                (
                    f'{stair.get("id", "UNKNOWN")}: riser arithmetic gives {rise:.2f} in, '
                    f'not {stair.get("floorToFloor", 0):.2f} in floor-to-floor.'
                ),
                connector_ids=[stair.get("id", "UNKNOWN")],
                suggested_fixes=[
                    "Adjust riser height or count so total rise equals floor-to-floor height."
                ],
            )
        if stair.get("landingDepth", 0) < stair.get("width", 0):
            add(
                f'VAL-STAIR-LANDING-{stair.get("id", "UNKNOWN")}',
                "ERROR",
                "STAIR_LANDING_MUST_MATCH_WIDTH",
                f'{stair.get("id", "UNKNOWN")}: landing depth is less than stair width.',
                connector_ids=[stair.get("id", "UNKNOWN")],
                suggested_fixes=["Increase landing depth to at least the clear stair width."],
            )
        if stair.get("kind") != "dog-leg" or stair.get("turn") != "180-deg":
            add(
                f'VAL-STAIR-TYPE-{stair.get("id", "UNKNOWN")}',
                "ERROR",
                "STAIR_TYPE_MUST_BE_COORDINATED",
                f'{stair.get("id", "UNKNOWN")}: stair is not a 180-degree dog-leg stair.',
                connector_ids=[stair.get("id", "UNKNOWN")],
                suggested_fixes=["Model the intended stair type and turn explicitly."],
            )

    if len(site.get("site", {}).get("plot", [])) < 3:
        add(
            "VAL-SITE-PLOT",
            "ERROR",
            "SITE_PLOT_MUST_HAVE_THREE_VERTICES",
            "The site plot must contain at least three vertices.",
            suggested_fixes=["Provide the surveyed site boundary before site-aware generation."],
        )
    entry_ids = {entry["id"] for entry in plans.get("entries", [])}
    if "ENTRY-MAIN" not in entry_ids:
        add(
            "VAL-ENTRY-MAIN",
            "ERROR",
            "MAIN_ENTRY_MUST_BE_EXPLICIT",
            "The source model must explicitly identify the primary main entry.",
            suggested_fixes=["Add an ENTRY-MAIN record linked to a semantic opening."],
        )
    for entry in plans.get("entries", []):
        if entry["openingId"] not in {opening["id"] for opening in openings}:
            add(
                f'VAL-ENTRY-OPENING-{entry.get("id", "UNKNOWN")}',
                "ERROR",
                "ENTRY_OPENING_MUST_EXIST",
                f'{entry.get("id", "UNKNOWN")}: referenced opening does not exist.',
                level_id=entry.get("level"),
                suggested_fixes=["Link the entry to an opening in plans.openings."],
            )
        if entry.get("kind") == "main" and "porch" not in entry:
            add(
                f'VAL-ENTRY-PORCH-{entry.get("id", "UNKNOWN")}',
                "ERROR",
                "MAIN_ENTRY_REQUIRES_ACCESS_ZONE",
                f'{entry.get("id", "UNKNOWN")}: main entry is missing a porch coordination zone.',
                level_id=entry.get("level"),
                suggested_fixes=["Model the intended porch, ramp, landing, or approach zone."],
            )

    # Week 3/4 enrichment runs against the same compatibility-shaped model
    # used by the legacy generators.  Keep the original Week 1 rules above
    # intact, then add deterministic graph/opening findings without changing
    # the Week 2 migration round-trip.
    existing_ids = {finding["id"] for finding in findings}
    for finding in validate_week34(site, plans):
        if finding["id"] not in existing_ids:
            findings.append(finding)
            existing_ids.add(finding["id"])
    return findings


def validate_model(site: dict[str, Any], plans: dict[str, Any]) -> list[str]:
    """Backward-compatible string errors for existing generators and API."""

    return [
        f'{finding["rule"]}: {finding["message"]}'
        for finding in validate_model_findings(site, plans)
        if finding["severity"] in {"BLOCKER", "ERROR"}
    ]