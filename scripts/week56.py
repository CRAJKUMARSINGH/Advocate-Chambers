#!/usr/bin/env python3
"""Week 5 and Week 6 architectural-intelligence enrichment.

Week 5 validates floor-to-floor connectors as real coordination objects:
levels, arrivals, departures, risers, treads, landings, widths, direction,
and route continuity are checked together.

Week 6 adds a small, inspectable program layer.  It does not pretend to
solve a layout automatically.  It records the selected building template,
checks required room uses and dimensions, evaluates adjacency intent, and
reports site-orientation assumptions that still need professional or client
confirmation.

The canonical Week 2 model is the input and remains authoritative.  The
derived reports and model fields are additive, so older drawing generators
can continue consuming the Week 1-shaped compatibility view.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT / "bar-association-hall"
REPORT_ROOT = MODEL_ROOT / "standard"
CANONICAL_PATH = MODEL_ROOT / "standard" / "model" / "project.json"
WEEK5_REPORT_PATH = REPORT_ROOT / "week5-stair-coordination-report.json"
WEEK6_REPORT_PATH = REPORT_ROOT / "week6-program-report.json"
MANIFEST_PATH = REPORT_ROOT / "week56-enrichment-manifest.json"

MIN_STAIR_WIDTH = 44.0
MIN_LANDING_DEPTH = 48.0
MIN_TREAD = 9.0
MIN_RISER = 4.0
MAX_RISER = 7.75
STAIR_TOLERANCE = 0.05
ADJACENCY_NEAR_TOLERANCE = 48.0


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected an object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _finding(
    finding_id: str,
    severity: str,
    rule: str,
    message: str,
    *,
    level_id: str | None = None,
    space_ids: list[str] | None = None,
    connector_ids: list[str] | None = None,
    suggested_fixes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "severity": severity,
        "rule": rule,
        "levelId": level_id,
        "spaceIds": space_ids or [],
        "connectorIds": connector_ids or [],
        "message": message,
        "suggestedFixes": suggested_fixes or [],
    }


def _status(findings: Iterable[dict[str, Any]]) -> str:
    return (
        "fail"
        if any(item["severity"] in {"BLOCKER", "ERROR"} for item in findings)
        else "pass"
    )


def _finding_counts(findings: Iterable[dict[str, Any]]) -> dict[str, int]:
    values = list(findings)
    return {
        severity: sum(1 for item in values if item["severity"] == severity)
        for severity in ("BLOCKER", "ERROR", "WARNING")
        if any(item["severity"] == severity for item in values)
    }


def _rect(space: dict[str, Any]) -> tuple[float, float, float, float]:
    geometry = space.get("geometry")
    value = geometry.get("rect") if isinstance(geometry, dict) else None
    if value is None:
        value = space.get("rect")
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError(f"{space.get('id', 'UNKNOWN')}: invalid rect")
    return tuple(float(item) for item in value)  # type: ignore[return-value]


def _room_use(space: dict[str, Any]) -> str:
    return str(space.get("roomUse") or space.get("use") or "").strip().lower()


def _level_id(space: dict[str, Any]) -> str:
    return str(space.get("levelId") or space.get("level") or "")


def _space_area_sqft(space: dict[str, Any]) -> float:
    x0, y0, x1, y1 = _rect(space)
    return abs(x1 - x0) * abs(y1 - y0) / 144.0


def _level_map(model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(level.get("id")): level
        for level in model.get("levels", [])
        if isinstance(level, dict) and level.get("id")
    }


def _space_map(model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(space.get("id")): space
        for space in model.get("spaces", [])
        if isinstance(space, dict) and space.get("id")
    }


def _geometry(stair: dict[str, Any]) -> dict[str, Any]:
    value = stair.get("geometry")
    return value if isinstance(value, dict) else stair


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _route_graph(model: dict[str, Any]) -> dict[str, Any]:
    """Build the existing Week 3 graph without changing its source contract."""

    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(MODEL_ROOT))
    from drawing_model import load_model  # type: ignore
    from week2 import canonical_to_legacy  # type: ignore
    from week34 import build_reachability_graph  # type: ignore

    # Prefer the model passed by the caller.  ``load_model`` is only used to
    # discover the compatibility shape when this module is run standalone.
    site, _plans = canonical_to_legacy(model)
    plans = copy.deepcopy(_plans)
    _findings, graph = build_reachability_graph(site, plans)
    return graph


def validate_stairs(
    model: dict[str, Any],
    route_graph: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate stairs and return findings plus a stable connector schedule."""

    levels = _level_map(model)
    spaces = _space_map(model)
    stairs = {
        str(stair.get("id")): stair
        for stair in model.get("stairs", [])
        if isinstance(stair, dict) and stair.get("id")
    }
    findings: list[dict[str, Any]] = []
    schedule: list[dict[str, Any]] = []
    route_by_space = {
        str(route.get("spaceId")): route
        for route in (route_graph or {}).get("routes", [])
        if isinstance(route, dict) and route.get("spaceId")
    }

    def add(
        finding_id: str,
        severity: str,
        rule: str,
        message: str,
        **kwargs: Any,
    ) -> None:
        findings.append(_finding(finding_id, severity, rule, message, **kwargs))

    for connector in model.get("verticalConnectors", []):
        if not isinstance(connector, dict):
            continue
        connector_id = str(connector.get("id", "UNKNOWN"))
        from_level_id = str(connector.get("fromLevelId", ""))
        to_level_id = str(connector.get("toLevelId", ""))
        stair_id = str(connector.get("stairId", ""))
        departure_id = connector.get("departureSpaceId")
        arrival_id = connector.get("arrivalSpaceId")
        connector_spaces = [
            str(value) for value in (departure_id, arrival_id) if value
        ]
        stair = stairs.get(stair_id)
        from_level = levels.get(from_level_id)
        to_level = levels.get(to_level_id)

        if not from_level or not to_level:
            add(
                f"VAL5-LEVELS-{connector_id}",
                "BLOCKER",
                "CONNECTOR_LEVELS_MUST_EXIST",
                f"{connector_id} references a missing departure or arrival level.",
                connector_ids=[connector_id],
                suggested_fixes=["Reference existing level IDs on both ends of the connector."],
            )
            continue
        if not stair:
            add(
                f"VAL5-STAIR-{connector_id}",
                "BLOCKER",
                "CONNECTOR_STAIR_MUST_EXIST",
                f"{connector_id} does not reference a modeled stair or future connector interface.",
                level_id=from_level_id,
                connector_ids=[connector_id],
                suggested_fixes=["Attach a stair, ramp, or lift object with validated endpoints."],
            )
            continue
        if not departure_id or departure_id not in spaces:
            add(
                f"VAL5-DEPARTURE-{connector_id}",
                "BLOCKER",
                "CONNECTOR_DEPARTURE_MUST_EXIST",
                f"{connector_id} has no valid departure space.",
                level_id=from_level_id,
                connector_ids=[connector_id],
                suggested_fixes=["Name the lower-floor circulation or stair departure space."],
            )
        if not arrival_id or arrival_id not in spaces:
            add(
                f"VAL5-ARRIVAL-{connector_id}",
                "BLOCKER",
                "CONNECTOR_ARRIVAL_MUST_EXIST",
                f"{connector_id} has no valid arrival space.",
                level_id=to_level_id,
                connector_ids=[connector_id],
                suggested_fixes=["Name the upper-floor circulation or stair arrival space."],
            )
        if departure_id in spaces and _level_id(spaces[str(departure_id)]) != from_level_id:
            add(
                f"VAL5-DEPARTURE-LEVEL-{connector_id}",
                "ERROR",
                "CONNECTOR_DEPARTURE_LEVEL_MUST_MATCH",
                f"{connector_id} departure {departure_id} is not on {from_level_id}.",
                level_id=from_level_id,
                space_ids=[str(departure_id)],
                connector_ids=[connector_id],
                suggested_fixes=["Move the departure reference to the connector's lower level."],
            )
        if arrival_id in spaces and _level_id(spaces[str(arrival_id)]) != to_level_id:
            add(
                f"VAL5-ARRIVAL-LEVEL-{connector_id}",
                "ERROR",
                "CONNECTOR_ARRIVAL_LEVEL_MUST_MATCH",
                f"{connector_id} arrival {arrival_id} is not on {to_level_id}.",
                level_id=to_level_id,
                space_ids=[str(arrival_id)],
                connector_ids=[connector_id],
                suggested_fixes=["Move the arrival reference to the connector's upper level."],
            )

        geometry = _geometry(stair)
        stair_from = str(stair.get("levelFrom") or geometry.get("levelFrom") or "")
        stair_to = str(stair.get("levelTo") or geometry.get("levelTo") or "")
        if stair_from != from_level_id or stair_to != to_level_id:
            add(
                f"VAL5-STAIR-ENDPOINTS-{connector_id}",
                "ERROR",
                "STAIR_ENDPOINTS_MUST_MATCH_CONNECTOR",
                f"{stair_id} endpoints do not match {connector_id}.",
                level_id=from_level_id,
                connector_ids=[connector_id],
                suggested_fixes=["Use the same from/to levels on the stair and connector."],
            )

        floor_to_floor = _number(geometry.get("floorToFloor"))
        if floor_to_floor is None:
            floor_to_floor = _number(to_level.get("elevation", 0))
            floor_to_floor = (
                floor_to_floor - (_number(from_level.get("elevation", 0)) or 0)
                if floor_to_floor is not None
                else None
            )
        declared_risers = _number(geometry.get("riserCountTotal"))
        declared_riser = _number(geometry.get("riser"))
        tread = _number(geometry.get("tread"))
        width = _number(geometry.get("width"))
        landing = _number(geometry.get("landingDepth"))
        flight_count = _number(geometry.get("flightCount"))
        per_flight = _number(geometry.get("riserCountPerFlight"))

        if floor_to_floor is None or floor_to_floor <= 0:
            add(
                f"VAL5-RISE-HEIGHT-{connector_id}",
                "BLOCKER",
                "STAIR_FLOOR_TO_FLOOR_MUST_BE_POSITIVE",
                f"{stair_id} has no positive floor-to-floor height.",
                level_id=from_level_id,
                connector_ids=[connector_id],
                suggested_fixes=["Provide the coordinated level-to-level height in model units."],
            )
        if not declared_risers or declared_risers <= 0:
            add(
                f"VAL5-RISERS-{connector_id}",
                "BLOCKER",
                "STAIR_RISER_COUNT_MUST_BE_POSITIVE",
                f"{stair_id} has no positive total riser count.",
                level_id=from_level_id,
                connector_ids=[connector_id],
                suggested_fixes=["Provide the total riser count and per-flight count."],
            )
        if floor_to_floor and declared_risers and declared_risers > 0:
            calculated_riser = floor_to_floor / declared_risers
            if declared_riser is None or abs(calculated_riser - declared_riser) > STAIR_TOLERANCE:
                add(
                    f"VAL5-RISER-ARITHMETIC-{connector_id}",
                    "ERROR",
                    "STAIR_RISER_ARITHMETIC_MUST_MATCH",
                    f"{stair_id} declares {declared_riser!r} in riser height; "
                    f"{floor_to_floor:g} / {declared_risers:g} = {calculated_riser:.4f}.",
                    level_id=from_level_id,
                    connector_ids=[connector_id],
                    suggested_fixes=["Recalculate the riser height from floor-to-floor and total risers."],
                )
            if not MIN_RISER <= calculated_riser <= MAX_RISER:
                add(
                    f"VAL5-RISER-RANGE-{connector_id}",
                    "ERROR",
                    "STAIR_RISER_MUST_BE_WITHIN_PLANNING_RANGE",
                    f"{stair_id} riser {calculated_riser:.2f} is outside "
                    f"{MIN_RISER:.2f}–{MAX_RISER:.2f} nominal planning range.",
                    level_id=from_level_id,
                    connector_ids=[connector_id],
                    suggested_fixes=["Adjust floor-to-floor height or riser count and obtain code review."],
                )
        if tread is None or tread < MIN_TREAD:
            add(
                f"VAL5-TREAD-{connector_id}",
                "ERROR",
                "STAIR_TREAD_MUST_MEET_MINIMUM",
                f"{stair_id} tread {tread!r} is below the {MIN_TREAD:g} nominal minimum.",
                level_id=from_level_id,
                connector_ids=[connector_id],
                suggested_fixes=["Provide a wider going and verify the jurisdictional stair rule pack."],
            )
        if width is None or width < MIN_STAIR_WIDTH:
            add(
                f"VAL5-WIDTH-{connector_id}",
                "ERROR",
                "STAIR_WIDTH_MUST_MEET_MINIMUM",
                f"{stair_id} width {width!r} is below the {MIN_STAIR_WIDTH:g} nominal minimum.",
                level_id=from_level_id,
                connector_ids=[connector_id],
                suggested_fixes=["Increase clear stair width and verify occupancy/egress requirements."],
            )
        if landing is None or landing < MIN_LANDING_DEPTH:
            add(
                f"VAL5-LANDING-{connector_id}",
                "ERROR",
                "STAIR_LANDING_MUST_MEET_MINIMUM",
                f"{stair_id} landing depth {landing!r} is below the {MIN_LANDING_DEPTH:g} nominal minimum.",
                level_id=from_level_id,
                connector_ids=[connector_id],
                suggested_fixes=["Model a landing at least as deep as the planning minimum."],
            )
        if flight_count and per_flight and declared_risers:
            if round(flight_count * per_flight, 5) != round(declared_risers, 5):
                add(
                    f"VAL5-FLIGHT-ARITHMETIC-{connector_id}",
                    "ERROR",
                    "STAIR_FLIGHT_RISERS_MUST_SUM_TO_TOTAL",
                    f"{stair_id} flight risers do not sum to the total risers.",
                    level_id=from_level_id,
                    connector_ids=[connector_id],
                    suggested_fixes=["Make flightCount × riserCountPerFlight equal riserCountTotal."],
                )
        direction = str(geometry.get("direction", "")).lower()
        from_elevation = _number(from_level.get("elevation", 0)) or 0
        to_elevation = _number(to_level.get("elevation", 0)) or 0
        expected_direction = "up" if to_elevation > from_elevation else "down"
        if direction and direction != expected_direction:
            add(
                f"VAL5-DIRECTION-{connector_id}",
                "ERROR",
                "STAIR_DIRECTION_MUST_MATCH_LEVELS",
                f"{stair_id} direction is {direction!r}, but {from_level_id} → {to_level_id} requires {expected_direction!r}.",
                level_id=from_level_id,
                connector_ids=[connector_id],
                suggested_fixes=["Align stair direction with the level elevations."],
            )

        if route_graph is not None:
            route = route_by_space.get(str(arrival_id))
            edge_id = f"EDGE-CONNECTOR-{connector_id}"
            graph_edge = next(
                (
                    edge
                    for edge in route_graph.get("edges", [])
                    if edge.get("id") == edge_id
                ),
                None,
            )
            if graph_edge is None:
                add(
                    f"VAL5-GRAPH-EDGE-{connector_id}",
                    "BLOCKER",
                    "CONNECTOR_MUST_BE_IN_REACHABILITY_GRAPH",
                    f"{connector_id} is not represented as a floor-to-floor graph edge.",
                    level_id=from_level_id,
                    connector_ids=[connector_id],
                    suggested_fixes=["Connect the stair departure and arrival nodes in the route graph."],
                )
            if route is None or not route.get("reachable"):
                add(
                    f"VAL5-ROUTE-{connector_id}",
                    "BLOCKER",
                    "UPPER_FLOOR_ROUTE_MUST_BE_REACHABLE",
                    f"{stair_id} reaches {arrival_id}, but the upper-floor route is not proven from an intentional entry.",
                    level_id=to_level_id,
                    space_ids=connector_spaces,
                    connector_ids=[connector_id],
                    suggested_fixes=[
                        "Connect the lower-floor departure to an entry.",
                        "Connect the upper-floor arrival to the occupied upper-floor route.",
                    ],
                )

        schedule.append(
            {
                "connectorId": connector_id,
                "kind": str(stair.get("kind") or stair.get("configuration") or "vertical-connector"),
                "fromLevelId": from_level_id,
                "toLevelId": to_level_id,
                "stairId": stair_id,
                "departureSpaceId": departure_id,
                "arrivalSpaceId": arrival_id,
                "geometry": {
                    "floorToFloor": floor_to_floor,
                    "riserCountTotal": declared_risers,
                    "riser": declared_riser,
                    "tread": tread,
                    "width": width,
                    "landingDepth": landing,
                    "direction": direction or None,
                    "flightCount": flight_count,
                    "riserCountPerFlight": per_flight,
                },
                "route": route_by_space.get(str(arrival_id)),
            }
        )

    if not model.get("verticalConnectors") and len(model.get("levels", [])) > 1:
        add(
            "VAL5-CONNECTOR-MISSING",
            "BLOCKER",
            "MULTI_LEVEL_MODEL_REQUIRES_CONNECTOR",
            "The model has multiple levels but no floor-to-floor connector.",
            suggested_fixes=["Add a validated stair, ramp, or lift connector between occupied levels."],
        )

    return findings, schedule


PROGRAM_TEMPLATES: dict[str, dict[str, Any]] = {
    "institutional": {
        "label": "Institutional / civic building",
        "requiredUses": [
            {"roomUse": "reception", "label": "Reception / records", "minCount": 1, "minAreaSqFt": 100, "minWidth": 96, "minDepth": 96},
            {"roomUse": "vertical-circulation", "label": "Vertical circulation", "minCount": 1, "minAreaSqFt": 100, "minWidth": 44, "minDepth": 48},
            {"roomUse": "assembly", "label": "Assembly / public hall", "minCount": 1, "minAreaSqFt": 300, "minWidth": 120, "minDepth": 120},
            {"roomUse": "service", "label": "Service support", "minCount": 1, "minAreaSqFt": 40, "minWidth": 36, "minDepth": 36},
        ],
        "adjacencyRules": [
            {"id": "assembly-stage", "kind": "required", "left": "assembly", "right": "stage", "label": "Assembly should directly support the stage/dais."},
            {"id": "reception-circulation", "kind": "preferred", "left": "reception", "right": "vertical-circulation", "label": "Reception should be near the main circulation node."},
            {"id": "library-computer", "kind": "preferred", "left": "library", "right": "computer", "label": "Library and computer/internet support should be near."},
            {"id": "service-assembly", "kind": "forbidden", "left": "service", "right": "assembly", "label": "Service rooms should not open directly into the public assembly zone."},
        ],
    },
    "commercial": {
        "label": "Commercial",
        "requiredUses": [
            {"roomUse": "reception", "label": "Public reception", "minCount": 1, "minAreaSqFt": 80, "minWidth": 72, "minDepth": 72},
            {"roomUse": "vertical-circulation", "label": "Vertical circulation", "minCount": 1, "minAreaSqFt": 80, "minWidth": 44, "minDepth": 48},
            {"roomUse": "service", "label": "Service support", "minCount": 1, "minAreaSqFt": 40, "minWidth": 36, "minDepth": 36},
        ],
        "adjacencyRules": [
            {"id": "reception-circulation", "kind": "preferred", "left": "reception", "right": "vertical-circulation", "label": "Reception should be near vertical circulation."},
        ],
    },
    "residential": {
        "label": "Residential",
        "requiredUses": [
            {"roomUse": "vertical-circulation", "label": "Vertical circulation", "minCount": 1, "minAreaSqFt": 80, "minWidth": 44, "minDepth": 48},
            {"roomUse": "service", "label": "Service support", "minCount": 1, "minAreaSqFt": 40, "minWidth": 36, "minDepth": 36},
        ],
        "adjacencyRules": [],
    },
    "industrial": {
        "label": "Industrial",
        "requiredUses": [
            {"roomUse": "service", "label": "Service support", "minCount": 1, "minAreaSqFt": 80, "minWidth": 48, "minDepth": 48},
        ],
        "adjacencyRules": [],
    },
}


def _relationship(
    first: dict[str, Any],
    second: dict[str, Any],
    tolerance: float = ADJACENCY_NEAR_TOLERANCE,
) -> tuple[str, float]:
    ax0, ay0, ax1, ay1 = _rect(first)
    bx0, by0, bx1, by1 = _rect(second)
    x_gap = max(bx0 - ax1, ax0 - bx1, 0.0)
    y_gap = max(by0 - ay1, ay0 - by1, 0.0)
    x_overlap = min(ax1, bx1) - max(ax0, bx0)
    y_overlap = min(ay1, by1) - max(ay0, by0)
    if x_overlap > 0 and y_overlap > 0:
        return "overlap", 0.0
    if (x_gap == 0 and y_overlap > 0) or (y_gap == 0 and x_overlap > 0):
        return "adjacent", 0.0
    distance = max(x_gap, y_gap)
    if distance <= tolerance and (x_overlap > 0 or y_overlap > 0):
        return "near", distance
    return "separated", distance


def _pair_matches(
    spaces: list[dict[str, Any]],
    left_use: str,
    right_use: str,
) -> list[tuple[dict[str, Any], dict[str, Any], str, float]]:
    matches: list[tuple[dict[str, Any], dict[str, Any], str, float]] = []
    for index, first in enumerate(spaces):
        for second in spaces[index + 1 :]:
            if _level_id(first) != _level_id(second):
                continue
            first_use = _room_use(first)
            second_use = _room_use(second)
            if {first_use, second_use} != {left_use, right_use}:
                continue
            relationship, distance = _relationship(first, second)
            matches.append((first, second, relationship, distance))
    return matches


def _best_pair(
    pairs: list[tuple[dict[str, Any], dict[str, Any], str, float]],
) -> tuple[dict[str, Any], dict[str, Any], str, float] | None:
    rank = {"overlap": 0, "adjacent": 1, "near": 2, "separated": 3}
    return min(pairs, key=lambda item: (rank[item[2]], item[3])) if pairs else None


def _orientation(model: dict[str, Any]) -> dict[str, Any]:
    site = model.get("site", {})
    geometry = site.get("geometry", {}) if isinstance(site, dict) else {}
    vertices = geometry.get("plotVertices", [])
    xs = [float(point[0]) for point in vertices if isinstance(point, list) and len(point) >= 2]
    ys = [float(point[1]) for point in vertices if isinstance(point, list) and len(point) >= 2]
    supplied = model.get("orientation", {})
    supplied = supplied if isinstance(supplied, dict) else {}
    legacy = site.get("legacy", {}) if isinstance(site, dict) else {}
    return {
        "north": supplied.get("north") or geometry.get("north") or legacy.get("north"),
        "roadFrontage": supplied.get("roadFrontage") or legacy.get("road") or legacy.get("frontage"),
        "serviceAccess": supplied.get("serviceAccess") or legacy.get("serviceAccess"),
        "setbacks": copy.deepcopy(
            supplied.get("setbacks") or geometry.get("setbacks") or legacy.get("setbacks") or {}
        ),
        "plotBounds": {
            "minX": min(xs) if xs else None,
            "minY": min(ys) if ys else None,
            "maxX": max(xs) if xs else None,
            "maxY": max(ys) if ys else None,
            "width": max(xs) - min(xs) if xs else None,
            "depth": max(ys) - min(ys) if ys else None,
        },
        "source": "explicit" if supplied else "legacy-derived",
        "assumptions": [
            "North and frontage must be confirmed against a licensed site survey.",
            "Setbacks are planning inputs, not a jurisdictional compliance determination.",
        ],
    }


def program_report(
    model: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    configured = model.get("program", {})
    configured = configured if isinstance(configured, dict) else {}
    building_type = str(configured.get("buildingType") or "institutional").lower()
    template = PROGRAM_TEMPLATES.get(building_type, PROGRAM_TEMPLATES["institutional"])
    spaces = [space for space in model.get("spaces", []) if isinstance(space, dict)]
    findings: list[dict[str, Any]] = []
    space_checks: list[dict[str, Any]] = []
    for space in spaces:
        space_id = str(space.get("id", "UNKNOWN"))
        room_use = _room_use(space)
        try:
            x0, y0, x1, y1 = _rect(space)
            width = abs(x1 - x0)
            depth = abs(y1 - y0)
            area_sqft = width * depth / 144.0
        except (TypeError, ValueError):
            findings.append(
                _finding(
                    f"VAL6-DIMENSIONS-{space_id}",
                    "ERROR",
                    "SPACE_DIMENSIONS_MUST_BE_NUMERIC",
                    f"{space_id} has no valid rectangular dimensions.",
                    level_id=_level_id(space),
                    space_ids=[space_id],
                    suggested_fixes=["Provide a four-coordinate numeric rectangle."],
                )
            )
            continue
        requirements = next(
            (
                requirement
                for requirement in template["requiredUses"]
                if requirement["roomUse"] == room_use
            ),
            None,
        )
        check = {
            "spaceId": space_id,
            "levelId": _level_id(space),
            "roomUse": room_use,
            "name": space.get("name"),
            "width": width,
            "depth": depth,
            "areaSqFt": round(area_sqft, 2),
            "minimums": {
                "width": requirements.get("minWidth") if requirements else None,
                "depth": requirements.get("minDepth") if requirements else None,
                "areaSqFt": requirements.get("minAreaSqFt") if requirements else None,
            },
            "status": "pass",
        }
        if requirements:
            failed = []
            if area_sqft < requirements["minAreaSqFt"]:
                failed.append(f"area {area_sqft:.1f} < {requirements['minAreaSqFt']} sq ft")
            if width < requirements["minWidth"]:
                failed.append(f"width {width:.1f} < {requirements['minWidth']} in")
            if depth < requirements["minDepth"]:
                failed.append(f"depth {depth:.1f} < {requirements['minDepth']} in")
            if failed:
                check["status"] = "fail"
                findings.append(
                    _finding(
                        f"VAL6-DIMENSIONS-{space_id}",
                        "ERROR",
                        "SPACE_AREA_AND_DIMENSIONS_MUST_MEET_PROGRAM",
                        f"{space_id} ({space.get('name', room_use)}) fails program minimums: {'; '.join(failed)}.",
                        level_id=_level_id(space),
                        space_ids=[space_id],
                        suggested_fixes=["Resize the space or document an approved project-specific exception."],
                    )
                )
        space_checks.append(check)

    counts: dict[str, int] = {}
    for space in spaces:
        counts[_room_use(space)] = counts.get(_room_use(space), 0) + 1
    completeness: list[dict[str, Any]] = []
    for requirement in template["requiredUses"]:
        actual = counts.get(requirement["roomUse"], 0)
        satisfied = actual >= requirement["minCount"]
        completeness.append(
            {
                "roomUse": requirement["roomUse"],
                "label": requirement["label"],
                "requiredCount": requirement["minCount"],
                "actualCount": actual,
                "status": "pass" if satisfied else "missing",
            }
        )
        if not satisfied:
            findings.append(
                _finding(
                    f"VAL6-MISSING-{requirement['roomUse']}",
                    "BLOCKER",
                    "PROGRAM_REQUIRED_USE_MISSING",
                    f"Program template requires {requirement['label']} ({requirement['roomUse']}) "
                    f"at least {requirement['minCount']} time(s), but found {actual}.",
                    suggested_fixes=[f"Add or classify a {requirement['roomUse']} space before rendering."],
                )
            )

    adjacency_evaluations: list[dict[str, Any]] = []
    for rule in template["adjacencyRules"]:
        pairs = _pair_matches(spaces, rule["left"], rule["right"])
        best = _best_pair(pairs)
        relationship = best[2] if best else "missing"
        satisfied = (
            (rule["kind"] == "required" and relationship in {"adjacent", "near"})
            or (rule["kind"] == "preferred" and relationship in {"adjacent", "near"})
            or (rule["kind"] == "forbidden" and relationship not in {"adjacent", "overlap"})
        )
        evaluation = {
            "id": rule["id"],
            "kind": rule["kind"],
            "left": rule["left"],
            "right": rule["right"],
            "label": rule["label"],
            "relationship": relationship,
            "satisfied": satisfied,
            "spaceIds": [best[0]["id"], best[1]["id"]] if best else [],
            "distance": best[3] if best else None,
            "explanation": (
                f"{rule['label']} "
                + (
                    f"Observed {relationship} between {best[0].get('name', best[0]['id'])} "
                    f"and {best[1].get('name', best[1]['id'])}."
                    if best
                    else "No same-level pair with the requested room uses was found."
                )
            ),
        }
        adjacency_evaluations.append(evaluation)
        if not satisfied:
            if rule["kind"] == "required":
                severity = "BLOCKER"
                rule_code = "PROGRAM_REQUIRED_ADJACENCY_NOT_SATISFIED"
            elif rule["kind"] == "forbidden":
                severity = "BLOCKER"
                rule_code = "PROGRAM_FORBIDDEN_ADJACENCY_FOUND"
            else:
                severity = "WARNING"
                rule_code = "PROGRAM_PREFERRED_ADJACENCY_NOT_SATISFIED"
            findings.append(
                _finding(
                    f"VAL6-ADJACENCY-{rule['id']}",
                    severity,
                    rule_code,
                    evaluation["explanation"],
                    space_ids=evaluation["spaceIds"],
                    suggested_fixes=[
                        f"Review the {rule['kind']} adjacency between {rule['left']} and {rule['right']}."
                    ],
                )
            )

    orientation = _orientation(model)
    orientation_findings: list[dict[str, Any]] = []
    if not orientation.get("north"):
        orientation_findings.append(
            _finding(
                "VAL6-ORIENTATION-NORTH",
                "WARNING",
                "SITE_NORTH_MUST_BE_CONFIRMED",
                "Site north is not explicitly defined.",
                suggested_fixes=["Confirm north against the survey before orientation-dependent planning."],
            )
        )
    if not orientation.get("roadFrontage"):
        orientation_findings.append(
            _finding(
                "VAL6-ORIENTATION-FRONTAGE",
                "WARNING",
                "SITE_ROAD_FRONTAGE_MUST_BE_CONFIRMED",
                "Road/frontage is not explicitly defined in the site model.",
                suggested_fixes=["Record the public road or frontage edge before final entry and setback decisions."],
            )
        )
    if not orientation.get("serviceAccess"):
        orientation_findings.append(
            _finding(
                "VAL6-SERVICE-ACCESS",
                "WARNING",
                "SERVICE_ACCESS_INTENT_MUST_BE_CONFIRMED",
                "No dedicated service-access intent is recorded.",
                suggested_fixes=["Identify the service approach and keep it separate from public entry where required."],
            )
        )
    findings.extend(orientation_findings)
    program = {
        "buildingType": building_type,
        "templateVersion": "week6.program-template.v1",
        "templateLabel": template["label"],
        "requiredUses": copy.deepcopy(template["requiredUses"]),
        "adjacencyRules": copy.deepcopy(template["adjacencyRules"]),
        "counts": counts,
        "completeness": completeness,
        "spaceChecks": space_checks,
        "adjacencyEvaluations": adjacency_evaluations,
        "orientation": orientation,
    }
    return program, findings


def enrichment_report(model: dict[str, Any]) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(MODEL_ROOT))
    from week2 import canonical_to_legacy  # type: ignore
    from week34 import enrichment_report as week34_enrichment  # type: ignore

    site, plans = canonical_to_legacy(model)
    previous = week34_enrichment(site, plans)
    graph = previous["week3"]["graph"]
    week5_findings, stair_schedule = validate_stairs(model, graph)
    program, week6_findings = program_report(model)
    findings = previous["findings"] + week5_findings + week6_findings
    findings = sorted(findings, key=lambda item: (item["severity"], item["id"]))
    return {
        "reportVersion": "week56.enrichment.v1",
        "status": _status(findings),
        "findingCounts": _finding_counts(findings),
        "findings": findings,
        "week3": previous["week3"],
        "week4": previous["week4"],
        "week5": {
            "reportVersion": "week5.stair-coordination.v1",
            "status": _status(week5_findings),
            "findingCounts": _finding_counts(week5_findings),
            "findings": week5_findings,
            "connectors": stair_schedule,
        },
        "week6": {
            "reportVersion": "week6.program.v1",
            "status": _status(week6_findings),
            "findingCounts": _finding_counts(week6_findings),
            "findings": week6_findings,
            "program": program,
        },
    }


def write_reports() -> dict[str, Any]:
    model = read_json(CANONICAL_PATH)
    report = enrichment_report(model)
    model["program"] = copy.deepcopy(report["week6"]["program"])
    model["orientation"] = copy.deepcopy(report["week6"]["program"]["orientation"])
    model["adjacencies"] = copy.deepcopy(report["week6"]["program"]["adjacencyEvaluations"])
    enrichment = model.get("enrichment", {})
    enrichment = enrichment if isinstance(enrichment, dict) else {}
    enrichment.update(
        {
            "version": "week56.enrichment.v1",
            "week5Report": str(WEEK5_REPORT_PATH.relative_to(ROOT)),
            "week6Report": str(WEEK6_REPORT_PATH.relative_to(ROOT)),
        }
    )
    model["enrichment"] = enrichment
    write_json(
        WEEK5_REPORT_PATH,
        {
            "reportVersion": report["week5"]["reportVersion"],
            "status": report["week5"]["status"],
            "findingCounts": report["week5"]["findingCounts"],
            "findings": report["week5"]["findings"],
            "connectors": report["week5"]["connectors"],
        },
    )
    write_json(
        WEEK6_REPORT_PATH,
        {
            "reportVersion": report["week6"]["reportVersion"],
            "status": report["week6"]["status"],
            "findingCounts": report["week6"]["findingCounts"],
            "findings": report["week6"]["findings"],
            "program": report["week6"]["program"],
        },
    )
    write_json(
        MANIFEST_PATH,
        {
            "manifestVersion": "week56.enrichment-manifest.v1",
            "status": report["status"],
            "reports": {
                "week5": str(WEEK5_REPORT_PATH.relative_to(ROOT)),
                "week6": str(WEEK6_REPORT_PATH.relative_to(ROOT)),
            },
            "counts": {
                "levels": len(model.get("levels", [])),
                "stairs": len(model.get("stairs", [])),
                "connectors": len(model.get("verticalConnectors", [])),
                "spaces": len(model.get("spaces", [])),
                "adjacencyRules": len(report["week6"]["program"]["adjacencyRules"]),
            },
            "findingCounts": report["findingCounts"],
        },
    )
    write_json(CANONICAL_PATH, model)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "report"), nargs="?", default="validate")
    args = parser.parse_args(argv)
    report = write_reports()
    if args.command == "report":
        output = report
    else:
        output = {
            "status": report["status"],
            "findingCounts": report["findingCounts"],
            "reports": {
                "week5": str(WEEK5_REPORT_PATH.relative_to(ROOT)),
                "week6": str(WEEK6_REPORT_PATH.relative_to(ROOT)),
            },
        }
    print(json.dumps(output, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())