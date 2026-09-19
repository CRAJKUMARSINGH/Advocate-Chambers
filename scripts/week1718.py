#!/usr/bin/env python3
"""Week 17–18 site review, collaboration, and professional delivery.

This module adds two deliberately reviewable layers around the canonical
planning model:

* Week 17 derives a site workspace and evaluates a configurable rule pack.
  Every result carries its inputs, calculation, source, assumption,
  confidence, and suggested correction. Missing evidence is ``unknown`` or
  ``professional-review``; it is never silently treated as a pass.
* Week 18 provides deterministic contracts for read-only review links,
  anchored comments, revision comparison, approval states, and a coordinated
  export package. The package gate blocks unresolved BLOCKER findings unless
  the caller explicitly requests a marked non-issuable review package.

The outputs are preliminary planning and coordination aids. They are not
permit, code, fire, accessibility, survey, structural, MEP, or construction
certification.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT / "bar-association-hall"
REPORT_ROOT = MODEL_ROOT / "standard"
CANONICAL_PATH = REPORT_ROOT / "model" / "project.json"
RULE_PACK_PATH = REPORT_ROOT / "rule-packs" / "india-preliminary-review.v1.json"
WEEK17_REPORT_PATH = REPORT_ROOT / "week17-site-feasibility-report.json"
WEEK18_REPORT_PATH = REPORT_ROOT / "week18-delivery-package-report.json"
MANIFEST_PATH = REPORT_ROOT / "week1718-enrichment-manifest.json"
CHANGELOG_PATH = REPORT_ROOT / "week1718-changelog.md"

WEEK17_VERSION = "week17.site-feasibility.v1"
WEEK18_VERSION = "week18.professional-delivery.v1"
RULE_PACK_VERSION = "india-preliminary-review@1.0.0"
APPROVAL_STATES = (
    "Draft",
    "Review",
    "Client Presentation",
    "Preliminary Coordination",
    "Not Issuable",
)
ANCHOR_TYPES = {
    "room",
    "wall",
    "opening",
    "dimension",
    "validation-finding",
    "render-viewpoint",
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected an object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _signature(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _rect(item: dict[str, Any]) -> list[float] | None:
    geometry = item.get("geometry")
    value = geometry.get("rect") if isinstance(geometry, dict) else item.get("rect")
    if not isinstance(value, list) or len(value) != 4:
        return None
    try:
        numbers = [float(part) for part in value]
    except (TypeError, ValueError):
        return None
    x0, y0, x1, y1 = numbers
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def _area(rect: list[float] | None) -> float:
    if not rect:
        return 0.0
    return max(0.0, rect[2] - rect[0]) * max(0.0, rect[3] - rect[1])


def _room_use(space: dict[str, Any]) -> str:
    return str(space.get("roomUse") or space.get("use") or "").strip().lower()


def _level_id(item: dict[str, Any]) -> str:
    return str(item.get("levelId") or item.get("level") or "")


def _plot_bounds(model: dict[str, Any]) -> list[float] | None:
    site = model.get("site") or {}
    geometry = site.get("geometry") if isinstance(site, dict) else {}
    vertices = geometry.get("plotVertices") if isinstance(geometry, dict) else None
    if not vertices:
        vertices = (model.get("orientation") or {}).get("plotVertices")
    if not isinstance(vertices, list) or not vertices:
        return None
    points = [point for point in vertices if isinstance(point, list) and len(point) == 2]
    if not points:
        return None
    try:
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
    except (TypeError, ValueError):
        return None
    return [min(xs), min(ys), max(xs), max(ys)]


def _site_workspace(model: dict[str, Any]) -> dict[str, Any]:
    """Build the Week 17 editable site/context contract without changing model geometry."""

    site = copy.deepcopy(model.get("site") or {})
    site_geometry = site.get("geometry") if isinstance(site, dict) else {}
    orientation = model.get("orientation") or {}
    plot_bounds = _plot_bounds(model)
    levels = [
        {
            "id": level.get("id"),
            "name": level.get("name"),
            "elevation": level.get("elevation"),
            "floorToFloor": level.get("floorToFloor"),
        }
        for level in model.get("levels", [])
    ]
    footprints: list[dict[str, Any]] = []
    for level in model.get("levels", []):
        spaces = [
            space
            for space in model.get("spaces", [])
            if _level_id(space) == level.get("id") and _rect(space)
        ]
        rects = [_rect(space) for space in spaces]
        valid_rects = [rect for rect in rects if rect]
        if valid_rects:
            footprints.append(
                {
                    "levelId": level.get("id"),
                    "rects": valid_rects,
                    "envelope": [
                        min(rect[0] for rect in valid_rects),
                        min(rect[1] for rect in valid_rects),
                        max(rect[2] for rect in valid_rects),
                        max(rect[3] for rect in valid_rects),
                    ],
                    "area": round(sum(_area(rect) for rect in valid_rects), 4),
                    "source": "canonical spaces",
                }
            )
    assumptions = list(model.get("assumptions") or [])
    assumptions.extend(
        [
            "Plot, north, road frontage, and setbacks remain survey/jurisdiction inputs.",
            "Site checks are preliminary rule-pack checks and do not grant approval.",
        ]
    )
    return {
        "version": WEEK17_VERSION,
        "projectId": (model.get("project") or {}).get("id"),
        "modelRevision": (model.get("project") or {}).get("revision"),
        "units": model.get("units", "inch"),
        "plot": {
            "vertices": (site_geometry or {}).get("plotVertices"),
            "bounds": plot_bounds,
            "north": (site_geometry or {}).get("north") or orientation.get("north"),
            "roadFrontage": orientation.get("roadFrontage"),
            "setbacks": (site_geometry or {}).get("setbacks") or orientation.get("setbacks") or {},
        },
        "accessPoints": copy.deepcopy(model.get("entries") or []),
        "buildingFootprints": footprints,
        "levels": levels,
        "contextLayers": [
            {"id": "plot", "kind": "site-boundary", "visible": True, "authoritative": False},
            {"id": "footprints", "kind": "building-footprint", "visible": True, "authoritative": True},
            {"id": "north", "kind": "orientation", "visible": True, "authoritative": False},
            {"id": "access", "kind": "access-points", "visible": True, "authoritative": False},
            {"id": "review", "kind": "imported-review-overlay", "visible": False, "authoritative": False},
        ],
        "assumptions": sorted(set(str(item) for item in assumptions)),
        "editableGeometry": False,
        "source": "canonical project model",
    }


def _result(
    rule_id: str,
    category: str,
    status: str,
    *,
    severity: str,
    input_geometry: dict[str, Any],
    source: str,
    calculation: str,
    assumption: str,
    confidence: float,
    suggested_correction: str,
    message: str,
) -> dict[str, Any]:
    return {
        "ruleId": rule_id,
        "category": category,
        "status": status,
        "severity": severity,
        "inputGeometry": input_geometry,
        "source": source,
        "calculation": calculation,
        "assumption": assumption,
        "confidence": round(max(0.0, min(1.0, confidence)), 3),
        "message": message,
        "suggestedCorrection": suggested_correction,
    }


def _status_from_bool(value: bool | None) -> tuple[str, str]:
    if value is None:
        return "unknown", "REVIEW"
    return ("pass", "INFO") if value else ("fail", "BLOCKER")


def _professional_review(value: bool | None) -> tuple[str, str]:
    """A nominal result that still requires a qualified professional review."""

    if value is None:
        return "unknown", "REVIEW"
    return "professional-review", "REVIEW"


def _window_hosts(model: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for window in model.get("windows", []):
        host = window.get("hostSpace")
        if host:
            counts[str(host)] = counts.get(str(host), 0) + 1
    return counts


def evaluate_rule_pack(
    model: dict[str, Any],
    *,
    rule_pack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate all Week 17 rules with transparent, reproducible evidence."""

    pack = rule_pack or read_json(RULE_PACK_PATH)
    workspace = _site_workspace(model)
    plot = workspace["plot"]
    bounds = plot.get("bounds")
    spaces = list(model.get("spaces") or [])
    gf_spaces = [space for space in spaces if _level_id(space) == "GF" and _rect(space)]
    footprint_area = sum(_area(_rect(space)) for space in gf_spaces)
    plot_area = _area(bounds)
    results: list[dict[str, Any]] = []

    coverage_limit = pack.get("site", {}).get("maximumCoverage") if isinstance(pack.get("site"), dict) else None
    coverage_ok: bool | None = None
    if coverage_limit is not None and plot_area:
        coverage_ok = footprint_area / plot_area <= float(coverage_limit)
    results.append(
        _result(
            "SITE-COVERAGE",
            "coverage",
            _status_from_bool(coverage_ok)[0],
            severity=_status_from_bool(coverage_ok)[1],
            input_geometry={"plotBounds": bounds, "groundFloorSpaceIds": [space.get("id") for space in gf_spaces]},
            source="rule pack site.maximumCoverage + canonical spaces",
            calculation=f"ground-floor area {footprint_area:.2f} / plot envelope area {plot_area:.2f}",
            assumption="A maximum coverage value must be supplied by the selected jurisdiction.",
            confidence=0.98 if coverage_ok is not None else 0.0,
            suggested_correction="Set rule-pack site.maximumCoverage after jurisdiction and survey confirmation.",
            message="Coverage can be evaluated." if coverage_ok is not None else "Coverage is unknown because the rule pack has no jurisdictional maximum.",
        )
    )

    setbacks = plot.get("setbacks") or {}
    building = next((item.get("envelope") for item in workspace["buildingFootprints"] if item.get("levelId") == "GF"), None)
    setback_values = {key: setbacks.get(key) for key in ("north", "south", "east", "west")}
    setback_check: bool | None = None
    unit_mismatch = bool(
        bounds
        and building
        and (
            building[2] - building[0] > (bounds[2] - bounds[0]) * 2
            or building[3] - building[1] > (bounds[3] - bounds[1]) * 2
        )
    )
    if bounds and building and not unit_mismatch and all(value is not None for value in setback_values.values()):
        setback_check = (
            building[0] - bounds[0] >= float(setback_values["west"])
            and bounds[2] - building[2] >= float(setback_values["east"])
            and building[1] - bounds[1] >= float(setback_values["south"])
            and bounds[3] - building[3] >= float(setback_values["north"])
        )
    results.append(
        _result(
            "SITE-SETBACKS",
            "setbacks",
            _status_from_bool(setback_check)[0],
            severity=_status_from_bool(setback_check)[1],
            input_geometry={"plotBounds": bounds, "groundFloorEnvelope": building, "setbacks": setback_values},
            source="canonical site geometry and orientation.setbacks",
            calculation="compare each envelope edge to the corresponding plot edge plus required setback"
            + ("; suspected unit/scale mismatch prevents a reliable comparison" if unit_mismatch else ""),
            assumption=(
                "Site and building dimensions appear to use incompatible scales; confirm units before evaluating setbacks."
                if unit_mismatch
                else "Setback values are planning inputs and must be confirmed by the appointed surveyor/authority."
            ),
            confidence=0.92 if setback_check is not None else 0.0,
            suggested_correction=(
                "Normalize site and building units, then confirm the survey and jurisdictional setbacks."
                if unit_mismatch
                else "Confirm plot survey and jurisdictional setbacks, then adjust footprint or record an approved exception."
            ),
            message=(
                "Setback compliance is unknown because site and building scales require reconciliation."
                if unit_mismatch
                else "Footprint satisfies the recorded preliminary setbacks." if setback_check else "Setback compliance is unknown or not satisfied."
            ),
        )
    )

    height_limit = pack.get("site", {}).get("maximumHeight") if isinstance(pack.get("site"), dict) else None
    max_elevation = max((float(level.get("elevation", 0)) for level in model.get("levels", [])), default=0.0)
    height_ok = None if height_limit is None else max_elevation <= float(height_limit)
    results.append(
        _result(
            "SITE-HEIGHT",
            "height",
            _status_from_bool(height_ok)[0],
            severity=_status_from_bool(height_ok)[1],
            input_geometry={"levels": workspace["levels"]},
            source="rule pack site.maximumHeight + canonical levels",
            calculation=f"highest recorded level elevation = {max_elevation:.2f} {workspace['units']}",
            assumption="A height datum and jurisdictional maximum are not present in this preliminary model.",
            confidence=0.95 if height_ok is not None else 0.0,
            suggested_correction="Add a verified height limit and datum to the selected rule pack.",
            message="Height is unknown until a verified limit and datum are supplied.",
        )
    )

    target = (model.get("program") or {}).get("targetFloorAreaSqFt")
    total_floor_area = sum(_area(_rect(space)) for space in spaces) / 144.0
    target_ok = None if target is None else abs(total_floor_area - float(target)) <= max(1.0, float(target) * 0.05)
    results.append(
        _result(
            "PROGRAM-FLOOR-AREA",
            "floor-area-target",
            _status_from_bool(target_ok)[0],
            severity=_status_from_bool(target_ok)[1],
            input_geometry={"spaceIds": [space.get("id") for space in spaces]},
            source="canonical program.targetFloorAreaSqFt + space rectangles",
            calculation=f"recorded floor area = {total_floor_area:.2f} sq ft; target = {target!r}",
            assumption="No target floor area is currently recorded in the program brief.",
            confidence=0.9 if target_ok is not None else 0.0,
            suggested_correction="Record an approved target range in the program brief before treating area as pass/fail.",
            message="Floor-area target is unknown until the brief supplies a target.",
        )
    )

    parking = (model.get("program") or {}).get("parking")
    parking_ok = None if parking is None else bool(parking.get("spaces") is not None)
    results.append(
        _result(
            "SITE-PARKING",
            "parking",
            _status_from_bool(parking_ok)[0],
            severity=_status_from_bool(parking_ok)[1],
            input_geometry={"siteBounds": bounds},
            source="canonical program.parking",
            calculation=f"parking input = {parking!r}",
            assumption="Parking demand and vehicle access are not defined in the current model.",
            confidence=0.8 if parking_ok is not None else 0.0,
            suggested_correction="Add parking count, accessible bays, loading, and maneuvering geometry after a site survey.",
            message="Parking is unknown because no parking program or geometry is recorded.",
        )
    )

    openings = list(model.get("openings") or [])
    accessible_width = float((pack.get("accessibility") or {}).get("doorMinWidth", 32))
    route_width = float((pack.get("accessibility") or {}).get("routeMinWidth", 44))
    route_values = [
        float((item.get("geometry") or {}).get("width", 0))
        for item in (model.get("circulationZones") or [])
        if (item.get("geometry") or {}).get("width") is not None
    ]
    access_ok = bool(openings) and all(float((item.get("geometry") or {}).get("width", 0)) >= accessible_width for item in openings)
    if not route_values:
        access_value: bool | None = None
    else:
        access_value = all(value >= route_width for value in route_values)
    access_status = access_ok if route_values else None
    access_state, access_severity = _professional_review(access_status)
    results.append(
        _result(
            "ACCESSIBILITY-ROUTES",
            "accessibility",
            access_state,
            severity=access_severity,
            input_geometry={"openingIds": [item.get("id") for item in openings], "routeIds": [item.get("id") for item in model.get("circulationZones", [])]},
            source="rule pack accessibility + canonical openings/circulation zones",
            calculation=f"door minimum {accessible_width}; route minimum {route_width}; route widths = {route_values}",
            assumption="A full accessible route audit needs measured thresholds, landings, fixtures, and vertical access.",
            confidence=0.72 if access_status is not None else 0.0,
            suggested_correction="Have an accessibility professional verify the entire route, not just nominal rectangle widths.",
            message="Accessibility requires professional review; route widths are incomplete." if access_status is None else "Nominal route and opening widths meet the configured preliminary thresholds.",
        )
    )

    window_hosts = _window_hosts(model)
    required_daylight = set((pack.get("daylight") or {}).get("requiredWindowUses", []))
    required_vent = set((pack.get("ventilation") or {}).get("requiredWindowUses", []))
    daylight_unknown = [space.get("id") for space in spaces if _room_use(space) in required_daylight and not window_hosts.get(space.get("id"))]
    ventilation_unknown = [space.get("id") for space in spaces if _room_use(space) in required_vent and not window_hosts.get(space.get("id"))]
    daylight_value: bool | None = None if not required_daylight else not daylight_unknown
    ventilation_value: bool | None = None if not required_vent else not ventilation_unknown
    for rule_id, category, value, missing, required, text in (
        ("DAYLIGHT-OPENINGS", "daylight", daylight_value, daylight_unknown, required_daylight, "daylight"),
        ("VENTILATION-OPENINGS", "ventilation", ventilation_value, ventilation_unknown, required_vent, "ventilation"),
    ):
        results.append(
            _result(
                rule_id,
                category,
                _status_from_bool(value)[0],
                severity=_status_from_bool(value)[1],
                input_geometry={"spaceIds": [space.get("id") for space in spaces if _room_use(space) in required], "windowHostCounts": window_hosts},
                source=f"rule pack {category}.requiredWindowUses + canonical windows",
                calculation=f"required uses = {sorted(required)}; missing host spaces = {missing}",
                assumption="Window presence is only a planning proxy; area, orientation, obstruction, and mechanical systems need review.",
                confidence=0.75 if value is not None else 0.0,
                suggested_correction=f"Review {text} area, orientation, obstructions, and mechanical strategy with the appointed professional.",
                message=f"All configured {text} uses have window hosts." if value else f"{text.title()} evidence is missing for {missing}." if missing else f"{text.title()} rule has no configured uses.",
            )
        )

    exit_rule = (pack.get("egress") or {}).get("minimumExteriorExitsByUse", {})
    assembly_spaces = [space for space in spaces if _room_use(space) == "assembly"]
    exterior_entries = [entry for entry in model.get("entries", []) if entry.get("exteriorZoneId")]
    egress_value: bool | None = None
    if assembly_spaces and exit_rule.get("assembly") is not None:
        egress_value = len(exterior_entries) >= int(exit_rule["assembly"])
    egress_state, egress_severity = _professional_review(egress_value)
    results.append(
        _result(
            "EGRESS-EXTERIOR-EXITS",
            "egress",
            egress_state,
            severity=egress_severity,
            input_geometry={"assemblySpaceIds": [space.get("id") for space in assembly_spaces], "entryIds": [entry.get("id") for entry in exterior_entries]},
            source="rule pack egress + canonical entries and room uses",
            calculation=f"exterior entries = {len(exterior_entries)}; configured assembly minimum = {exit_rule.get('assembly')!r}",
            assumption="Travel distance, occupant load, exit separation, fire doors, and discharge are not fully modeled.",
            confidence=0.6 if egress_value is not None else 0.0,
            suggested_correction="Run a fire/life-safety review using occupant load, travel paths, exit widths, separation, and discharge.",
            message="Nominal exterior-entry count is available, but egress remains professional review.",
        )
    )

    for rule_id, category, value, source_key, correction in (
        ("FIRE-ACCESS", "fire-access", None, "site.fireAccess", "Add verified fire appliance access geometry and turning data."),
        ("SERVICE-ACCESS", "service-access", None, "site.serviceAccess", "Add a service entry, route, and loading/service-zone geometry."),
    ):
        results.append(
            _result(
                rule_id,
                category,
                "unknown",
                severity="REVIEW",
                input_geometry={"plotBounds": bounds, "entries": [entry.get("id") for entry in model.get("entries", [])]},
                source=source_key,
                calculation="no authoritative fire/service access geometry is present",
                assumption="Site access intent must be confirmed against survey, vehicle requirements, and local authority guidance.",
                confidence=0.0,
                suggested_correction=correction,
                message=f"{category.replace('-', ' ').title()} is unknown.",
            )
        )

    wet_uses = set((pack.get("wetArea") or {}).get("uses", []))
    wet_spaces = [space for space in spaces if _room_use(space) in wet_uses]
    wet_value: bool | None = None
    if wet_spaces:
        wet_value = all(window_hosts.get(space.get("id"), 0) >= 1 for space in wet_spaces)
    wet_state, wet_severity = _professional_review(wet_value)
    results.append(
        _result(
            "WET-AREA-COORDINATION",
            "wet-area",
            wet_state,
            severity=wet_severity,
            input_geometry={"wetSpaceIds": [space.get("id") for space in wet_spaces], "windowHostCounts": window_hosts},
            source="rule pack wetArea + canonical service spaces/windows",
            calculation=f"wet-area spaces with at least one ventilation opening = {sum(window_hosts.get(space.get('id'), 0) >= 1 for space in wet_spaces)} / {len(wet_spaces)}",
            assumption="Plumbing stacks, shafts, falls, waterproofing, and mechanical ventilation are not represented.",
            confidence=0.5 if wet_value is not None else 0.0,
            suggested_correction="Coordinate wet areas with the MEP layout, shafts, drainage, waterproofing, and ventilation strategy.",
            message="Wet-area coordination is unknown because no wet-area spaces are explicitly typed." if not wet_spaces else "Wet-area openings are nominally present; MEP coordination remains required.",
        )
    )

    counts = {status: sum(1 for result in results if result["status"] == status) for status in ("pass", "fail", "unknown", "professional-review")}
    counts["review"] = sum(1 for result in results if result["severity"] == "REVIEW")
    return {
        "version": WEEK17_VERSION,
        "rulePack": {
            "id": pack.get("id"),
            "version": pack.get("version"),
            "path": str(RULE_PACK_PATH.relative_to(ROOT)),
            "jurisdiction": pack.get("jurisdiction"),
        },
        "workspace": workspace,
        "results": results,
        "dashboard": {
            "counts": counts,
            "status": "fail" if counts["fail"] else "review" if counts["unknown"] or counts["review"] else "pass",
            "professionalReviewRequired": True,
            "approvalClaim": False,
        },
        "assumptions": workspace["assumptions"],
    }


def imported_review_workflow(source_path: str, source_format: str | None = None) -> dict[str, Any]:
    """Describe a PDF/CAD review without promoting it to authoritative geometry."""

    suffix = Path(source_path).suffix.lower().lstrip(".")
    detected = source_format or ("dxf" if suffix == "dxf" else "pdf" if suffix == "pdf" else suffix or "unknown")
    supported = detected in {"dxf", "pdf", "image"}
    return {
        "version": "week17.imported-review.v1",
        "source": {"path": source_path, "format": detected},
        "workflow": "separate-imported-review",
        "supported": supported,
        "status": "review-required" if supported else "unsupported",
        "promotion": {
            "authoritativeGeometry": False,
            "approvalGranted": False,
            "requiresHumanReview": True,
            "uncertainObjectsRemainNonAuthoritative": True,
        },
        "steps": [
            "ingest source and record SHA-256",
            "inspect CAD entities or render PDF/image for review",
            "map observations to candidate model objects",
            "record reviewer decisions and unresolved uncertainty",
            "promote only reviewed geometry through the normal revision workflow",
        ],
    }


def _model_snapshot(model: dict[str, Any]) -> dict[str, Any]:
    spaces = []
    for space in model.get("spaces", []):
        spaces.append(
            {
                "id": space.get("id"),
                "levelId": _level_id(space),
                "rect": _rect(space),
                "roomUse": _room_use(space),
                "area": _area(_rect(space)),
            }
        )
    openings = [
        {
            "id": item.get("id"),
            "hostSpace": item.get("hostSpace"),
            "geometry": item.get("geometry"),
            "kind": item.get("kind"),
        }
        for item in model.get("openings", [])
    ]
    validation = model.get("validationFindings") or model.get("findings") or []
    furniture = model.get("placements") or model.get("furniture") or []
    return {
        "revision": (model.get("project") or {}).get("revision"),
        "geometry": {"spaces": spaces, "levels": model.get("levels", [])},
        "validation": validation,
        "areas": {item["id"]: item["area"] for item in spaces if item.get("id")},
        "openings": openings,
        "furniture": furniture,
    }


def _index_by_id(items: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("id")): item for item in items if item.get("id") is not None}


def _diff_category(
    before: Iterable[dict[str, Any]],
    after: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    old = _index_by_id(before)
    new = _index_by_id(after)
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(key for key in set(old) & set(new) if old[key] != new[key])
    return {"added": added, "removed": removed, "changed": changed, "count": len(added) + len(removed) + len(changed)}


def compare_revisions(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Compare the required professional review categories deterministically."""

    old = _model_snapshot(before)
    new = _model_snapshot(after)
    geometry = _diff_category(old["geometry"]["spaces"], new["geometry"]["spaces"])
    geometry["levelsChanged"] = old["geometry"]["levels"] != new["geometry"]["levels"]
    validation = _diff_category(old["validation"], new["validation"])
    openings = _diff_category(old["openings"], new["openings"])
    furniture = _diff_category(old["furniture"], new["furniture"])
    area_changes = [
        {
            "spaceId": space_id,
            "before": old["areas"].get(space_id),
            "after": new["areas"].get(space_id),
            "delta": round((new["areas"].get(space_id, 0) - old["areas"].get(space_id, 0)), 4),
        }
        for space_id in sorted(set(old["areas"]) | set(new["areas"]))
        if old["areas"].get(space_id) != new["areas"].get(space_id)
    ]
    result = {
        "version": "week18.revision-compare.v1",
        "fromRevision": old["revision"],
        "toRevision": new["revision"],
        "geometryChanges": geometry,
        "validationChanges": validation,
        "areaChanges": area_changes,
        "openingChanges": openings,
        "furnitureChanges": furniture,
    }
    result["signature"] = _signature(result)
    return result


def create_review_link(
    model: dict[str, Any],
    *,
    view: str = "technical",
    base_url: str = "/review",
) -> dict[str, Any]:
    if view not in {"technical", "presentation"}:
        raise ValueError("view must be technical or presentation")
    revision = (model.get("project") or {}).get("revision")
    token = _signature({"project": (model.get("project") or {}).get("id"), "revision": revision, "view": view})[:24]
    return {
        "version": "week18.review-link.v1",
        "linkId": f"review-{token}",
        "url": f"{base_url.rstrip('/')}/{token}",
        "view": view,
        "modelRevision": revision,
        "readOnly": True,
        "technicalView": view == "technical",
        "presentationView": view == "presentation",
        "permissions": {"read": True, "comment": True, "editGeometry": False, "export": False},
        "expires": None,
    }


def create_comment(
    model: dict[str, Any],
    *,
    author: str,
    body: str,
    anchor_type: str,
    anchor_id: str,
    viewpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if anchor_type not in ANCHOR_TYPES:
        raise ValueError(f"anchor_type must be one of {sorted(ANCHOR_TYPES)}")
    if not body.strip():
        raise ValueError("body must not be empty")
    valid_ids: set[str] = set()
    for collection in ("spaces", "openings", "windows", "stairs"):
        valid_ids.update(str(item.get("id")) for item in model.get(collection, []) if item.get("id"))
    valid_ids.update(str(item.get("id")) for item in model.get("findings", []) if item.get("id"))
    if anchor_type != "render-viewpoint" and anchor_id not in valid_ids:
        raise ValueError(f"anchor_id {anchor_id!r} is not present in the model")
    revision = (model.get("project") or {}).get("revision")
    comment = {
        "version": "week18.comment.v1",
        "id": f"comment-{_signature({'author': author, 'body': body, 'anchorId': anchor_id, 'revision': revision})[:16]}",
        "author": author,
        "body": body,
        "anchor": {"type": anchor_type, "id": anchor_id, "viewpoint": viewpoint},
        "modelRevision": revision,
        "status": "open",
    }
    return comment


def coordinated_package(
    model: dict[str, Any],
    feasibility_report: dict[str, Any],
    *,
    allow_non_issuable: bool = False,
    include_ifc: bool = False,
) -> dict[str, Any]:
    """Build an export manifest and enforce the Week 18 release gate."""

    findings = feasibility_report.get("results", [])
    blockers = [
        result["ruleId"]
        for result in findings
        if result.get("severity") in {"BLOCKER", "ERROR"} or result.get("status") == "fail"
    ]
    approval = "Not Issuable" if blockers and allow_non_issuable else "Preliminary Coordination"
    status = "review-package" if blockers and allow_non_issuable else "blocked" if blockers else "ready"
    artifact_specs = [
        ("source-json", "source", "bar-association-hall/standard/model/project.json", True),
        ("validation-report", "json", "bar-association-hall/standard/week17-site-feasibility-report.json", True),
        ("technical-pdf", "pdf", "exports/technical-coordinated.pdf", True),
        ("coloured-pdf", "pdf", "exports/coloured-coordinated.pdf", True),
        ("dxf", "dxf", "exports/coordinated.dxf", True),
        ("images", "image-set", "exports/presentation-images/", True),
        ("assumptions", "json", "bar-association-hall/standard/week17-site-feasibility-report.json#/assumptions", True),
        ("rule-pack", "json", str(RULE_PACK_PATH.relative_to(ROOT)), True),
        ("manifest", "json", "exports/coordinated-package-manifest.json", True),
    ]
    if include_ifc:
        artifact_specs.insert(5, ("ifc", "ifc", "exports/coordinated.ifc", False))
    package = {
        "version": WEEK18_VERSION,
        "projectId": (model.get("project") or {}).get("id"),
        "modelRevision": (model.get("project") or {}).get("revision"),
        "approvalState": approval,
        "releaseGate": {
            "status": status,
            "unresolvedBlockers": blockers,
            "explicitNonIssuableExport": bool(allow_non_issuable),
            "rule": "reject unresolved BLOCKER findings unless explicitly marked Not Issuable",
        },
        "artifacts": [
            {"id": artifact_id, "kind": kind, "path": path, "required": required, "generated": False}
            for artifact_id, kind, path, required in artifact_specs
        ],
        "assumptions": feasibility_report.get("assumptions", []),
        "rulePackVersion": RULE_PACK_VERSION,
        "sourceModel": {"path": "bar-association-hall/standard/model/project.json", "revision": (model.get("project") or {}).get("revision")},
        "manifestSignature": None,
    }
    package["manifestSignature"] = _signature({key: value for key, value in package.items() if key != "manifestSignature"})
    return package


def enrichment_report(model: dict[str, Any]) -> dict[str, Any]:
    feasibility = evaluate_rule_pack(model)
    package = coordinated_package(model, feasibility)
    return {
        "version": "week1718.enrichment.v1",
        "week17": feasibility,
        "week18": {
            "version": WEEK18_VERSION,
            "approvalStates": list(APPROVAL_STATES),
            "reviewLinks": [
                create_review_link(model, view="technical"),
                create_review_link(model, view="presentation"),
            ],
            "commentAnchors": sorted(ANCHOR_TYPES),
            "revisionCompare": {
                "version": "week18.revision-compare.v1",
                "categories": ["geometry", "validation", "area", "openings", "furniture"],
                "deterministic": True,
            },
            "coordinatedPackage": package,
            "importedReview": imported_review_workflow("review-source.pdf", "pdf"),
            "professionalReviewRequired": True,
        },
        "status": "blocked" if package["releaseGate"]["status"] == "blocked" else "review",
    }


def write_reports() -> dict[str, Any]:
    model = read_json(CANONICAL_PATH)
    report = enrichment_report(model)
    write_json(WEEK17_REPORT_PATH, report["week17"])
    write_json(WEEK18_REPORT_PATH, report["week18"])
    manifest = {
        "manifestVersion": "week1718.enrichment-manifest.v1",
        "week17Version": WEEK17_VERSION,
        "week18Version": WEEK18_VERSION,
        "rulePackVersion": RULE_PACK_VERSION,
        "reports": {
            "week17": str(WEEK17_REPORT_PATH.relative_to(ROOT)),
            "week18": str(WEEK18_REPORT_PATH.relative_to(ROOT)),
        },
        "status": report["status"],
        "professionalReviewRequired": True,
        "releaseGate": report["week18"]["coordinatedPackage"]["releaseGate"],
    }
    write_json(MANIFEST_PATH, manifest)
    CHANGELOG_PATH.write_text(
        """# Week 17–18 enrichment changelog

## Week 17 — Site feasibility and transparent plan review

- Added a site workspace with plot bounds, north, setbacks, access points,
  level/footprint records, context layers, and explicit assumptions.
- Added preliminary rule-pack evaluation for coverage, setbacks, height,
  floor-area target, parking, accessibility, daylight, ventilation, egress,
  fire access, service access, and wet-area coordination.
- Every result records its rule ID, input geometry, source, calculation,
  assumption, confidence, and suggested correction.
- PDF/CAD review is a separate non-authoritative workflow; recognition never
  claims approval or promotes uncertain geometry automatically.

## Week 18 — Collaboration, revision history, and professional delivery

- Added deterministic read-only technical and presentation review-link
  contracts and comments anchored to model objects or render viewpoints.
- Added revision comparison for geometry, validation, area, openings, and
  furniture changes.
- Added Draft, Review, Client Presentation, Preliminary Coordination, and
  Not Issuable approval states.
- Added a coordinated export manifest and release gate for source JSON,
  validation report, technical/coloured PDFs, DXF, optional IFC, images,
  assumptions, rule-pack version, and manifest.
- Unresolved BLOCKER findings are rejected unless the caller explicitly marks
  the package as a non-issuable review package.
""",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("report", "validate", "compare"))
    parser.add_argument("--before", type=Path)
    parser.add_argument("--after", type=Path)
    args = parser.parse_args(argv)
    if args.command == "compare":
        if not args.before or not args.after:
            parser.error("compare requires --before and --after")
        print(json.dumps(compare_revisions(read_json(args.before), read_json(args.after)), indent=2))
        return 0
    report = write_reports() if args.command == "report" else enrichment_report(read_json(CANONICAL_PATH))
    print(json.dumps({"status": report["status"], "manifest": str(MANIFEST_PATH.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())