#!/usr/bin/env python3
"""Week 3 and Week 4 architectural-intelligence enrichment.

The legacy-shaped ``plans`` dictionary is deliberately accepted here so this
module can be used by the existing drawing validator and by the React API
without changing the Week 2 round-trip contract.  The module derives a
semantic opening layer, builds a deterministic walkable graph, and emits
explainable findings and opening schedules.

No geometric assumption is promoted to access intent: an opening is internal
only when it faces a named space, and it is exterior only when an entry or an
explicit exterior zone says so.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT / "bar-association-hall"
REPORT_ROOT = MODEL_ROOT / "standard"
CANONICAL_PATH = MODEL_ROOT / "standard" / "model" / "project.json"
WEEK3_REPORT_PATH = REPORT_ROOT / "week3-reachability-report.json"
WEEK4_REPORT_PATH = REPORT_ROOT / "week4-openings-report.json"
SCHEDULE_PATH = REPORT_ROOT / "opening-schedule.json"
MANIFEST_PATH = REPORT_ROOT / "week34-enrichment-manifest.json"


WALLS = ("north", "south", "east", "west")
OPPOSITE_WALL = {"north": "south", "south": "north", "east": "west", "west": "east"}
DEFAULT_WALL_TOLERANCE = 6.0
DEFAULT_MIN_DOOR_WIDTH = 36.0
DEFAULT_APPROACH_DEPTH = 42.0
DEFAULT_LANDING_DEPTH = 48.0


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected an object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def _space_level(space: dict[str, Any]) -> str | None:
    return str(space.get("level") or space.get("levelId") or "") or None


def _space_rect(space: dict[str, Any]) -> tuple[float, float, float, float]:
    geometry = space.get("geometry", {})
    rect = geometry.get("rect") if isinstance(geometry, dict) else None
    rect = rect if rect is not None else space.get("rect")
    if not isinstance(rect, list) or len(rect) != 4:
        raise ValueError(f"{space.get('id', 'UNKNOWN')}: invalid rectangle")
    return tuple(float(value) for value in rect)  # type: ignore[return-value]


def _opening_geometry(opening: dict[str, Any]) -> dict[str, Any]:
    geometry = opening.get("geometry")
    if isinstance(geometry, dict):
        return geometry
    return opening


def _opening_offset(opening: dict[str, Any]) -> float:
    return float(_opening_geometry(opening).get("offset", 0))


def _opening_width(opening: dict[str, Any]) -> float:
    return float(_opening_geometry(opening).get("width", 0))


def _wall_span(space: dict[str, Any], wall: str) -> float:
    x0, y0, x1, y1 = _space_rect(space)
    return x1 - x0 if wall in {"north", "south"} else y1 - y0


def _wall_coordinate(space: dict[str, Any], wall: str) -> float:
    x0, y0, x1, y1 = _space_rect(space)
    return {"south": y0, "north": y1, "west": x0, "east": x1}[wall]


def _wall_interval(
    space: dict[str, Any], wall: str, opening: dict[str, Any]
) -> tuple[float, float]:
    x0, y0, x1, y1 = _space_rect(space)
    start = _opening_offset(opening)
    end = start + _opening_width(opening)
    if wall in {"north", "south"}:
        return x0 + start, x0 + end
    return y0 + start, y0 + end


def _touching_spaces(
    host: dict[str, Any],
    opening: dict[str, Any],
    spaces: Iterable[dict[str, Any]],
    tolerance: float = DEFAULT_WALL_TOLERANCE,
) -> list[dict[str, Any]]:
    wall = opening.get("wall")
    if wall not in WALLS:
        return []
    first, second = _wall_interval(host, wall, opening)
    host_coordinate = _wall_coordinate(host, wall)
    candidates: list[dict[str, Any]] = []
    for candidate in spaces:
        if candidate is host or _space_level(candidate) != _space_level(host):
            continue
        candidate_wall = OPPOSITE_WALL[wall]
        if abs(host_coordinate - _wall_coordinate(candidate, candidate_wall)) > tolerance:
            continue
        cx0, cy0, cx1, cy1 = _space_rect(candidate)
        cfirst, csecond = (
            (cx0, cx1) if wall in {"north", "south"} else (cy0, cy1)
        )
        if min(second, csecond) - max(first, cfirst) > 0:
            candidates.append(candidate)
    return sorted(candidates, key=lambda item: str(item.get("id")))


def _entries_by_opening(plans: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for entry in plans.get("entries", []):
        if isinstance(entry, dict) and entry.get("openingId"):
            result.setdefault(str(entry["openingId"]), []).append(entry)
    return result


def _external_zone_id(entry: dict[str, Any]) -> str:
    if entry.get("exteriorZoneId"):
        return str(entry["exteriorZoneId"])
    return f"EXT-{entry.get('id', 'UNKNOWN')}"


def _explicit_external_zone_ids(plans: dict[str, Any]) -> set[str]:
    ids = {
        str(zone.get("id"))
        for zone in plans.get("exteriorAccessZones", []) + plans.get("exteriorZones", [])
        if isinstance(zone, dict) and zone.get("id")
    }
    for entry in plans.get("entries", []):
        if isinstance(entry, dict) and entry.get("porch"):
            ids.add(_external_zone_id(entry))
    return ids


def _opening_is_valid_wall_break(
    host: dict[str, Any], opening: dict[str, Any]
) -> bool:
    wall = opening.get("wall")
    if wall not in WALLS:
        return False
    try:
        offset = _opening_offset(opening)
        width = _opening_width(opening)
        return offset >= 0 and width > 0 and offset + width <= _wall_span(host, wall)
    except (TypeError, ValueError, KeyError):
        return False


def _approach_rect(
    host: dict[str, Any], opening: dict[str, Any]
) -> tuple[float, float, float, float] | None:
    """Return a conservative inside-the-host approach envelope."""

    wall = opening.get("wall")
    if wall not in WALLS:
        return None
    try:
        x0, y0, x1, y1 = _space_rect(host)
        start, end = _wall_interval(host, wall, opening)
    except (TypeError, ValueError, KeyError):
        return None
    depth = DEFAULT_APPROACH_DEPTH
    if wall == "south":
        return (start, y0, end, min(y1, y0 + depth))
    if wall == "north":
        return (start, max(y0, y1 - depth), end, y1)
    if wall == "west":
        return (x0, start, min(x1, x0 + depth), end)
    return (max(x0, x1 - depth), start, x1, end)


def _rectangles_overlap(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> bool:
    return (
        min(first[2], second[2]) > max(first[0], second[0])
        and min(first[3], second[3]) > max(first[1], second[1])
    )


def semantic_openings(
    site: dict[str, Any], plans: dict[str, Any]
) -> list[dict[str, Any]]:
    """Return deterministic side-A/side-B semantics for every opening."""

    del site  # Reserved for rule-pack-specific exterior boundary checks.
    spaces = [space for space in plans.get("spaces", []) if isinstance(space, dict)]
    space_by_id = {str(space.get("id")): space for space in spaces if space.get("id")}
    entries_by_opening = _entries_by_opening(plans)
    external_zone_ids = _explicit_external_zone_ids(plans)
    result: list[dict[str, Any]] = []

    for opening in plans.get("openings", []):
        if not isinstance(opening, dict):
            continue
        opening_id = str(opening.get("id", "UNKNOWN"))
        host_id = str(opening.get("hostSpace", ""))
        host = space_by_id.get(host_id)
        wall = opening.get("wall")
        kind = str(opening.get("type", "door"))
        entries = entries_by_opening.get(opening_id, [])
        touching = _touching_spaces(host, opening, spaces) if host else []

        explicit_space_id = (
            opening.get("connectedSpaceId")
            or opening.get("sideB")
            or opening.get("sideBSpaceId")
        )
        side_b: dict[str, Any] | None = None
        connection_type = "unconnected"
        if explicit_space_id and str(explicit_space_id) in space_by_id:
            side_b = {
                "kind": "space",
                "spaceId": str(explicit_space_id),
                "levelId": _space_level(space_by_id[str(explicit_space_id)]),
                "source": "explicit",
            }
            connection_type = "internal"
        elif touching:
            candidate = touching[0]
            side_b = {
                "kind": "space",
                "spaceId": str(candidate["id"]),
                "levelId": _space_level(candidate),
                "source": "geometric-adjacency",
            }
            connection_type = "internal"
        else:
            explicit_zone = (
                opening.get("exteriorAccessZoneId")
                or opening.get("accessZoneId")
                or opening.get("exteriorZoneId")
            )
            entry = entries[0] if entries else None
            if explicit_zone or entry:
                zone_id = str(explicit_zone or _external_zone_id(entry))
                side_b = {
                    "kind": "exterior-zone",
                    "zoneId": zone_id,
                    "levelId": _space_level(host) if host else opening.get("level"),
                    "source": "explicit-entry" if entry else "explicit-zone",
                    "isNamedZone": zone_id in external_zone_ids,
                }
                connection_type = "exterior"
            elif opening.get("exteriorAccess") is True:
                level_id = str(opening.get("level") or _space_level(host) or "UNKNOWN")
                side_b = {
                    "kind": "exterior",
                    "zoneId": f"EXTERIOR-{level_id}",
                    "levelId": level_id,
                    "source": "explicit-flag",
                    "isNamedZone": False,
                }
                connection_type = "exterior"

        wall_break = _opening_is_valid_wall_break(host, opening) if host else False
        width = _opening_width(opening) if opening else 0.0
        swing = _opening_geometry(opening).get("swing")
        is_door = kind == "door"
        entry = entries[0] if entries else None
        requires_landing = connection_type == "exterior" and bool(entry)
        porch = entry.get("porch") if entry else None
        landing_valid = not requires_landing or (
            isinstance(porch, dict)
            and float(porch.get("width", 0)) >= width
            and float(porch.get("depth", 0)) >= DEFAULT_LANDING_DEPTH
        )
        approach = {
            "requiredWidth": DEFAULT_MIN_DOOR_WIDTH if is_door else width,
            "requiredDepth": DEFAULT_APPROACH_DEPTH if is_door else 0,
            "landingRequired": requires_landing,
            "landingValid": landing_valid,
            "zoneId": _external_zone_id(entry) if requires_landing else None,
        }
        result.append(
            {
                "openingId": opening_id,
                "stableTag": str(opening.get("tag") or opening_id),
                "kind": kind,
                "levelId": opening.get("level") or (_space_level(host) if host else None),
                "hostSpace": host_id,
                "sideA": {
                    "kind": "space",
                    "spaceId": host_id,
                    "levelId": _space_level(host) if host else opening.get("level"),
                    "valid": host is not None,
                },
                "sideB": side_b,
                "connectionType": connection_type,
                "wall": wall,
                "wallBreak": wall_break,
                "width": width,
                "swing": swing,
                "approach": approach,
                "entryIds": [str(item.get("id")) for item in entries],
            }
        )
    return result


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


def validate_openings(
    site: dict[str, Any], plans: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate semantic openings and return findings plus an opening schedule."""

    semantics = semantic_openings(site, plans)
    spaces_by_id = {
        str(space.get("id")): space
        for space in plans.get("spaces", [])
        if isinstance(space, dict) and space.get("id")
    }
    openings_by_id = {
        str(opening.get("id")): opening
        for opening in plans.get("openings", [])
        if isinstance(opening, dict) and opening.get("id")
    }
    findings: list[dict[str, Any]] = []
    for item in semantics:
        opening_id = item["openingId"]
        level_id = item.get("levelId")
        if not item["sideA"]["valid"]:
            findings.append(
                _finding(
                    f"VAL4-SIDE-A-{opening_id}",
                    "ERROR",
                    "OPENING_SIDE_A_MUST_BE_VALID",
                    f"{opening_id} has no valid host space for side A.",
                    level_id=level_id,
                    opening_ids=[opening_id],
                    suggested_fixes=["Reference an existing host space on the opening level."],
                )
            )
        if not item["wallBreak"]:
            findings.append(
                _finding(
                    f"VAL4-WALL-BREAK-{opening_id}",
                    "ERROR",
                    "OPENING_MUST_CREATE_WALL_BREAK",
                    f"{opening_id} does not produce a valid semantic wall break.",
                    level_id=level_id,
                    space_id=item.get("hostSpace"),
                    opening_ids=[opening_id],
                    suggested_fixes=["Place the opening within the host wall span and keep its width positive."],
                )
            )
        if item["kind"] == "door":
            if item["width"] < DEFAULT_MIN_DOOR_WIDTH:
                findings.append(
                    _finding(
                        f"VAL4-WIDTH-{opening_id}",
                        "ERROR",
                        "DOOR_CLEAR_WIDTH_MINIMUM",
                        f"{opening_id} is {item['width']:.1f} in wide; the Week 4 baseline requires at least {DEFAULT_MIN_DOOR_WIDTH:.0f} in.",
                        level_id=level_id,
                        space_id=item.get("hostSpace"),
                        opening_ids=[opening_id],
                        suggested_fixes=["Increase clear door width or select a rule pack with an explicit exception."],
                    )
                )
            if item["swing"] not in {"in", "out"}:
                findings.append(
                    _finding(
                        f"VAL4-SWING-{opening_id}",
                        "ERROR",
                        "DOOR_SWING_MUST_BE_EXPLICIT",
                        f"{opening_id} has no explicit in/out swing.",
                        level_id=level_id,
                        space_id=item.get("hostSpace"),
                        opening_ids=[opening_id],
                        suggested_fixes=["Set geometry.swing to 'in' or 'out' and review the leaf against approach space."],
                    )
                )
            if item["sideB"] is None:
                findings.append(
                    _finding(
                        f"VAL4-SIDE-B-{opening_id}",
                        "BLOCKER",
                        "OPENING_SIDE_B_MUST_BE_VALID",
                        f"{opening_id} has no named adjacent space, connector approach, or intentional exterior zone on side B.",
                        level_id=level_id,
                        space_id=item.get("hostSpace"),
                        opening_ids=[opening_id],
                        suggested_fixes=[
                            "Connect the door to a named space.",
                            "Add a porch, landing, balcony, terrace, or explicit exterior access zone.",
                        ],
                    )
                )
            elif item["connectionType"] == "exterior" and item["approach"]["landingRequired"] and not item["approach"]["landingValid"]:
                findings.append(
                    _finding(
                        f"VAL4-LANDING-{opening_id}",
                        "ERROR",
                        "EXTERIOR_DOOR_REQUIRES_VALID_LANDING",
                        f"{opening_id} opens to an entry route without a landing/porch at least as wide as the door and {DEFAULT_LANDING_DEPTH:.0f} in deep.",
                        level_id=level_id,
                        space_id=item.get("hostSpace"),
                        opening_ids=[opening_id],
                        suggested_fixes=["Model a landing or porch with a valid width and clear depth."],
                    )
                )
        if item["connectionType"] == "internal" and item["sideB"] is not None:
            if item["sideB"].get("levelId") != level_id:
                findings.append(
                    _finding(
                        f"VAL4-CROSS-LEVEL-{opening_id}",
                        "ERROR",
                        "OPENING_SIDES_MUST_SHARE_LEVEL",
                        f"{opening_id} connects spaces on different levels without a vertical connector.",
                        level_id=level_id,
                        opening_ids=[opening_id],
                        suggested_fixes=["Use a modeled stair, ramp, or lift connector for cross-level movement."],
                    )
                )
        host = spaces_by_id.get(str(item["hostSpace"]))
        opening = openings_by_id.get(str(opening_id))
        approach_rect = _approach_rect(host, opening) if host and opening else None
        if approach_rect:
            for furniture in plans.get("furniture", []):
                if not isinstance(furniture, dict):
                    continue
                if furniture.get("level") != item.get("levelId"):
                    continue
                furniture_rect = furniture.get("rect")
                if not isinstance(furniture_rect, list) or len(furniture_rect) != 4:
                    continue
                try:
                    blocked = _rectangles_overlap(
                        approach_rect,
                        tuple(float(value) for value in furniture_rect),  # type: ignore[arg-type]
                    )
                except (TypeError, ValueError):
                    blocked = False
                if blocked:
                    furniture_id = str(furniture.get("id", "UNKNOWN"))
                    findings.append(
                        _finding(
                            f"VAL4-FURNITURE-{opening_id}-{furniture_id}",
                            "ERROR",
                            "DOOR_APPROACH_MUST_REMAIN_CLEAR",
                            f"{opening_id} approach zone is blocked by furniture/equipment {furniture_id}.",
                            level_id=level_id,
                            space_id=item.get("hostSpace"),
                            opening_ids=[opening_id],
                            suggested_fixes=[
                                f"Move {furniture_id} outside the {DEFAULT_APPROACH_DEPTH:.0f} in door approach envelope.",
                            ],
                        )
                    )

    schedule = [
        {
            "tag": item["stableTag"],
            "openingId": item["openingId"],
            "levelId": item["levelId"],
            "kind": item["kind"],
            "hostSpace": item["hostSpace"],
            "sideA": item["sideA"],
            "sideB": item["sideB"],
            "connectionType": item["connectionType"],
            "wall": item["wall"],
            "width": item["width"],
            "swing": item["swing"],
            "wallBreak": item["wallBreak"],
            "approach": item["approach"],
            "entryIds": item["entryIds"],
        }
        for item in semantics
    ]
    return findings, schedule


def build_reachability_graph(
    site: dict[str, Any], plans: dict[str, Any]
) -> dict[str, Any]:
    """Build the per-level and cross-level walkable graph."""

    semantics = semantic_openings(site, plans)
    spaces = [space for space in plans.get("spaces", []) if isinstance(space, dict)]
    space_by_id = {str(space.get("id")): space for space in spaces if space.get("id")}
    nodes: dict[str, dict[str, Any]] = {
        str(space["id"]): {
            "id": str(space["id"]),
            "kind": "space",
            "levelId": _space_level(space),
            "name": space.get("name"),
            "rect": list(_space_rect(space)),
        }
        for space in spaces
    }
    edges: list[dict[str, Any]] = []
    entry_roots: set[str] = set()

    def add_node(node_id: str, kind: str, level_id: str | None, **extra: Any) -> None:
        nodes.setdefault(node_id, {"id": node_id, "kind": kind, "levelId": level_id, **extra})

    for item in semantics:
        side_b = item["sideB"]
        if not side_b:
            continue
        from_id = item["hostSpace"]
        if from_id not in nodes:
            continue
        if side_b["kind"] == "space":
            to_id = str(side_b["spaceId"])
            if to_id not in nodes:
                continue
        else:
            to_id = str(side_b["zoneId"])
            add_node(to_id, "exterior-zone", side_b.get("levelId"), explicit=side_b.get("source"))
            if item["entryIds"] and (
                not item["approach"]["landingRequired"]
                or item["approach"]["landingValid"]
            ):
                entry_roots.add(to_id)
        edges.append(
            {
                "id": f"EDGE-OPENING-{item['openingId']}",
                "kind": "opening",
                "from": from_id,
                "to": to_id,
                "openingId": item["openingId"],
                "levelId": item["levelId"],
                "routeClass": "exterior-entry" if side_b["kind"] != "space" else "internal",
            }
        )

    for connector in plans.get("stairs", []):
        if not isinstance(connector, dict):
            continue
        stair_id = str(connector.get("id", "UNKNOWN"))
        from_level = connector.get("levelFrom")
        to_level = connector.get("levelTo")
        from_space = next(
            (
                str(space["id"])
                for space in spaces
                if _space_level(space) == from_level
                and space.get("stairId") == connector.get("id")
            ),
            None,
        )
        to_space = next(
            (
                str(space["id"])
                for space in spaces
                if _space_level(space) == to_level
                and space.get("stairId") == connector.get("id")
            ),
            None,
        )
        connector_id = f"VC-{stair_id}"
        if from_space and to_space:
            edges.append(
                {
                    "id": f"EDGE-CONNECTOR-{connector_id}",
                    "kind": "vertical-connector",
                    "from": from_space,
                    "to": to_space,
                    "connectorId": connector_id,
                    "levelId": from_level,
                    "toLevelId": to_level,
                    "routeClass": "vertical",
                }
            )

    adjacency: dict[str, list[tuple[str, dict[str, Any]]]] = {
        node_id: [] for node_id in nodes
    }
    for edge in edges:
        adjacency.setdefault(edge["from"], []).append((edge["to"], edge))
        adjacency.setdefault(edge["to"], []).append((edge["from"], edge))

    routes: dict[str, dict[str, Any]] = {}
    queue: deque[str] = deque(sorted(entry_roots))
    previous: dict[str, tuple[str | None, dict[str, Any] | None]] = {
        root: (None, None) for root in sorted(entry_roots)
    }
    while queue:
        current = queue.popleft()
        for neighbor, edge in sorted(adjacency.get(current, []), key=lambda pair: pair[0]):
            if neighbor not in previous:
                previous[neighbor] = (current, edge)
                queue.append(neighbor)

    for space_id, space in sorted(space_by_id.items()):
        if space_id not in previous:
            route_edges: list[str] = []
            cursor = space_id
            while cursor in previous and previous[cursor][0] is not None:
                prev, edge = previous[cursor]
                if edge:
                    route_edges.append(edge["id"])
                cursor = str(prev)
            route_edges.reverse()
            routes[space_id] = {
                "spaceId": space_id,
                "levelId": _space_level(space),
                "reachable": False,
                "entryRoots": [],
                "path": route_edges,
                "firstBrokenEdge": route_edges[0] if route_edges else None,
            }
        else:
            path: list[str] = []
            cursor = space_id
            root = cursor
            while previous.get(cursor, (None, None))[0] is not None:
                prev, edge = previous[cursor]
                if edge:
                    path.append(edge["id"])
                cursor = str(prev)
                root = cursor
            path.reverse()
            routes[space_id] = {
                "spaceId": space_id,
                "levelId": _space_level(space),
                "reachable": True,
                "entryRoots": [root] if root in entry_roots else [],
                "path": path,
                "firstBrokenEdge": None,
            }

    components: list[list[str]] = []
    remaining = set(nodes)
    while remaining:
        start = min(remaining)
        component: list[str] = []
        pending = [start]
        remaining.remove(start)
        while pending:
            current = pending.pop()
            component.append(current)
            for neighbor, _edge in adjacency.get(current, []):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    pending.append(neighbor)
        components.append(sorted(component))

    return {
        "nodes": [nodes[node_id] for node_id in sorted(nodes)],
        "edges": sorted(edges, key=lambda edge: edge["id"]),
        "entryRoots": sorted(entry_roots),
        "routes": [routes[key] for key in sorted(routes)],
        "components": sorted(components, key=lambda component: component[0] if component else ""),
    }


def validate_reachability(
    site: dict[str, Any], plans: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    graph = build_reachability_graph(site, plans)
    semantics = semantic_openings(site, plans)
    findings: list[dict[str, Any]] = []
    for route in graph["routes"]:
        space_id = route["spaceId"]
        space = next(
            (item for item in plans.get("spaces", []) if item.get("id") == space_id),
            {},
        )
        if str(space.get("finish", "")).lower() == "circulation":
            continue
        if not route["reachable"]:
            candidate_doors = [
                item["openingId"]
                for item in semantics
                if item["hostSpace"] == space_id and item["kind"] == "door"
            ]
            first_broken = candidate_doors[0] if candidate_doors else None
            findings.append(
                _finding(
                    f"VAL3-UNREACHABLE-{space_id}",
                    "BLOCKER",
                    "ROOM_ROUTE_UNREACHABLE",
                    f"{space_id} ({space.get('name', 'Unnamed space')}) has no proven route to an intentional entry.",
                    level_id=route["levelId"],
                    space_id=space_id,
                    opening_ids=candidate_doors,
                    suggested_fixes=[
                        "Connect the room to a reachable corridor or stair arrival.",
                        "Add an intentional exterior entry with a valid approach/landing.",
                        *( [f"Review first broken door edge {first_broken}."] if first_broken else [] ),
                    ],
                )
            )
    for item in semantics:
        if item["kind"] == "door" and item["sideB"] is None:
            findings.append(
                _finding(
                    f"VAL3-BROKEN-EDGE-{item['openingId']}",
                    "BLOCKER",
                    "ROUTE_EDGE_MUST_HAVE_TWO_VALID_SIDES",
                    f"{item['openingId']} cannot be used as a route edge because side B is not modeled.",
                    level_id=item["levelId"],
                    space_id=item["hostSpace"],
                    opening_ids=[item["openingId"]],
                    suggested_fixes=[
                        "Name the adjacent space or attach an explicit exterior access zone.",
                    ],
                )
            )
    return findings, graph


def enrichment_report(
    site: dict[str, Any], plans: dict[str, Any]
) -> dict[str, Any]:
    week3_findings, graph = validate_reachability(site, plans)
    week4_findings, schedule = validate_openings(site, plans)
    findings = sorted(
        week3_findings + week4_findings,
        key=lambda item: (item["severity"], item["id"]),
    )
    week3_report = {
        "reportVersion": "week3.reachability.v1",
        "status": "pass"
        if not any(item["severity"] in {"BLOCKER", "ERROR"} for item in week3_findings)
        else "fail",
        "findingCounts": {
            severity: sum(1 for item in week3_findings if item["severity"] == severity)
            for severity in ("BLOCKER", "ERROR", "WARNING")
            if any(item["severity"] == severity for item in week3_findings)
        },
        "graph": graph,
        "findings": week3_findings,
    }
    return {
        "reportVersion": "week34.enrichment.v1",
        "status": "pass"
        if not any(item["severity"] in {"BLOCKER", "ERROR"} for item in findings)
        else "fail",
        "findingCounts": {
            severity: sum(1 for item in findings if item["severity"] == severity)
            for severity in ("BLOCKER", "ERROR", "WARNING")
            if any(item["severity"] == severity for item in findings)
        },
        "findings": findings,
        "week3": week3_report,
        "week4": {
            "reportVersion": "week4.openings.v1",
            "schedule": schedule,
            "findings": week4_findings,
        },
    }


def validate_week34(site: dict[str, Any], plans: dict[str, Any]) -> list[dict[str, Any]]:
    """Compatibility entry point used by the Week 1 validator and API."""

    return enrichment_report(site, plans)["findings"]


def _load_sources() -> tuple[dict[str, Any], dict[str, Any]]:
    sys.path.insert(0, str(ROOT / "bar-association-hall"))
    from drawing_model import load_model  # type: ignore

    return load_model()


def write_reports() -> dict[str, Any]:
    site, plans = _load_sources()
    report = enrichment_report(site, plans)
    # Keep the Week 2 model as the authoritative source while adding an
    # additive semantic layer to each opening.  The legacy adapter ignores
    # this layer, so Week 2 round-trip tests remain lossless for the original
    # source files.
    sys.path.insert(0, str(ROOT / "scripts"))
    from week2 import canonical_to_legacy, load_canonical_model  # type: ignore

    canonical = load_canonical_model(CANONICAL_PATH)
    canonical_openings = {
        str(opening.get("id")): opening
        for opening in canonical.get("openings", [])
        if isinstance(opening, dict) and opening.get("id")
    }
    for semantic in report["week4"]["schedule"]:
        opening = canonical_openings.get(str(semantic["openingId"]))
        if opening is not None:
            opening["semantic"] = copy.deepcopy(semantic)
    canonical["enrichment"] = {
        "version": "week34.enrichment.v1",
        "week3Report": str(WEEK3_REPORT_PATH.relative_to(ROOT)),
        "week4Report": str(WEEK4_REPORT_PATH.relative_to(ROOT)),
        "openingSchedule": str(SCHEDULE_PATH.relative_to(ROOT)),
    }
    # Validate that the additive layer did not alter the Week 2 compatibility
    # view before persisting it.
    migrated_site, migrated_plans = canonical_to_legacy(canonical)
    if migrated_site != site or migrated_plans != plans:
        raise ValueError("Week 3/4 enrichment changed the Week 2 compatibility view")
    write_json(CANONICAL_PATH, canonical)
    write_json(WEEK3_REPORT_PATH, report["week3"])
    write_json(
        WEEK4_REPORT_PATH,
        {
            "reportVersion": report["week4"]["reportVersion"],
            "status": "pass"
            if not any(
                item["severity"] in {"BLOCKER", "ERROR"}
                for item in report["week4"]["findings"]
            )
            else "fail",
            "findingCounts": {
                severity: sum(
                    1 for item in report["week4"]["findings"] if item["severity"] == severity
                )
                for severity in ("BLOCKER", "ERROR", "WARNING")
                if any(item["severity"] == severity for item in report["week4"]["findings"])
            },
            "findings": report["week4"]["findings"],
        },
    )
    write_json(
        SCHEDULE_PATH,
        {
            "scheduleVersion": "week4.opening-schedule.v1",
            "status": report["status"],
            "openings": report["week4"]["schedule"],
        },
    )
    write_json(
        MANIFEST_PATH,
        {
            "manifestVersion": "week34.enrichment-manifest.v1",
            "status": report["status"],
            "reports": {
                "week3": str(WEEK3_REPORT_PATH.relative_to(ROOT)),
                "week4": str(WEEK4_REPORT_PATH.relative_to(ROOT)),
                "openingSchedule": str(SCHEDULE_PATH.relative_to(ROOT)),
            },
            "counts": {
                "spaces": len(plans.get("spaces", [])),
                "openings": len(plans.get("openings", [])),
                "graphNodes": len(report["week3"]["graph"]["nodes"]),
                "graphEdges": len(report["week3"]["graph"]["edges"]),
            },
            "findingCounts": report["findingCounts"],
        },
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("validate", "report", "schedule"),
        nargs="?",
        default="validate",
    )
    args = parser.parse_args(argv)
    report = write_reports()
    if args.command == "schedule":
        output = report["week4"]["schedule"]
    elif args.command == "report":
        output = report
    else:
        output = {
            "status": report["status"],
            "findingCounts": report["findingCounts"],
            "reports": {
                "week3": str(WEEK3_REPORT_PATH.relative_to(ROOT)),
                "week4": str(WEEK4_REPORT_PATH.relative_to(ROOT)),
                "openingSchedule": str(SCHEDULE_PATH.relative_to(ROOT)),
            },
        }
    print(json.dumps(output, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())