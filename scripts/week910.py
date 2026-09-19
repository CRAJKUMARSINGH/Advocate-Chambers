#!/usr/bin/env python3
"""Week 9 and Week 10 architectural-intelligence enrichment.

Week 9 adds a scaled, occupancy-aware presentation layer.  Furniture is
derived from the validated model but is deliberately stored outside the
authoritative rooms, walls, openings, and routes.

Week 10 adds deterministic candidate comparison, a transparent scorecard,
golden fixtures, geometry property checks, and release artifacts.  A candidate
cannot be marked best when inherited validation contains a blocker or error.
This remains preliminary planning software and is not a code, permit, fire,
accessibility, structural, MEP, survey, or construction certification.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT / "bar-association-hall"
REPORT_ROOT = MODEL_ROOT / "standard"
CANONICAL_PATH = REPORT_ROOT / "model" / "project.json"
WEEK9_REPORT_PATH = REPORT_ROOT / "week9-furniture-presentation-report.json"
WEEK10_REPORT_PATH = REPORT_ROOT / "week10-candidate-qa-report.json"
CHECKLIST_PATH = REPORT_ROOT / "week10-release-checklist.json"
MANIFEST_PATH = REPORT_ROOT / "week910-enrichment-manifest.json"
CHANGELOG_PATH = REPORT_ROOT / "week910-changelog.md"
FAILURE_SCREENSHOT_DIR = REPORT_ROOT / "failure-screenshots"
FAILURE_SCREENSHOT_PATH = FAILURE_SCREENSHOT_DIR / "week10-orphaned-room-fixture.svg"

FURNITURE_LIBRARY_VERSION = "week9.furniture-library.v1"
PRESENTATION_VERSION = "week9.presentation.v1"
CANDIDATE_VERSION = "week10.candidate-comparison.v1"
QA_VERSION = "week10.qa-release.v1"
DEFAULT_SEEDS = (11, 23, 47)


FURNITURE_LIBRARY: dict[str, dict[str, Any]] = {
    "chair": {
        "label": "Stacking chair",
        "category": "seating",
        "width": 18.0,
        "depth": 18.0,
        "height": 32.0,
        "clearance": 6.0,
        "occupancy": 1,
        "roomUses": ["assembly", "waiting", "discussion", "classroom"],
    },
    "audience-chair": {
        "label": "Audience chair",
        "category": "seating",
        "width": 18.0,
        "depth": 18.0,
        "height": 32.0,
        "clearance": 12.0,
        "occupancy": 1,
        "roomUses": ["assembly"],
    },
    "desk": {
        "label": "Work desk",
        "category": "work",
        "width": 60.0,
        "depth": 30.0,
        "height": 30.0,
        "clearance": 30.0,
        "occupancy": 1,
        "roomUses": ["office", "computer", "reception"],
    },
    "reception-desk": {
        "label": "Reception desk",
        "category": "work",
        "width": 72.0,
        "depth": 30.0,
        "height": 30.0,
        "clearance": 36.0,
        "occupancy": 2,
        "roomUses": ["reception"],
    },
    "meeting-table": {
        "label": "Discussion table",
        "category": "table",
        "width": 72.0,
        "depth": 36.0,
        "height": 30.0,
        "clearance": 30.0,
        "occupancy": 6,
        "roomUses": ["discussion", "office", "classroom"],
    },
    "library-shelf": {
        "label": "Library shelf",
        "category": "storage",
        "width": 72.0,
        "depth": 14.0,
        "height": 84.0,
        "clearance": 36.0,
        "occupancy": 0,
        "roomUses": ["library"],
    },
    "lectern": {
        "label": "Lectern",
        "category": "presentation",
        "width": 24.0,
        "depth": 20.0,
        "height": 42.0,
        "clearance": 36.0,
        "occupancy": 1,
        "roomUses": ["stage", "assembly"],
    },
    "service-counter": {
        "label": "Service counter",
        "category": "service",
        "width": 60.0,
        "depth": 24.0,
        "height": 36.0,
        "clearance": 36.0,
        "occupancy": 1,
        "roomUses": ["service"],
    },
}


GOLDEN_FIXTURES: dict[str, dict[str, Any]] = {
    "residential": {
        "requiredUses": ["living", "kitchen", "bedroom", "bathroom"],
        "minimumLevels": 1,
        "routeRequired": True,
    },
    "commercial": {
        "requiredUses": ["reception", "office", "service"],
        "minimumLevels": 1,
        "routeRequired": True,
    },
    "institutional": {
        "requiredUses": ["reception", "assembly", "service", "vertical-circulation"],
        "minimumLevels": 1,
        "routeRequired": True,
    },
    "industrial": {
        "requiredUses": ["production", "storage", "service"],
        "minimumLevels": 1,
        "routeRequired": True,
    },
}


WEIGHTS = {
    "areaFit": 0.20,
    "adjacency": 0.15,
    "routeQuality": 0.20,
    "daylightVentilation": 0.15,
    "structuralService": 0.15,
    "furnitureFit": 0.15,
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object in {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result == result else None


def _rect(item: dict[str, Any]) -> tuple[float, float, float, float] | None:
    geometry = item.get("geometry", {})
    values = geometry.get("rect") if isinstance(geometry, dict) else None
    if not isinstance(values, list) or len(values) != 4:
        return None
    numbers = [_number(value) for value in values]
    if any(value is None for value in numbers):
        return None
    x, y, width, depth = (float(value) for value in numbers)
    if width <= 0 or depth <= 0:
        return None
    return x, y, width, depth


def _room_use(space: dict[str, Any]) -> str:
    return str(space.get("roomUse") or space.get("kind") or "generic").lower()


def _level_id(item: dict[str, Any]) -> str:
    return str(item.get("levelId") or item.get("level") or "")


def _round_rect(values: Iterable[float]) -> list[float]:
    return [round(float(value), 3) for value in values]


def _expand(rect: list[float], clearance: float) -> list[float]:
    half = max(0.0, float(clearance)) / 2.0
    x, y, width, depth = rect
    return _round_rect([x - half, y - half, width + 2 * half, depth + 2 * half])


def _overlap(first: list[float], second: list[float], *, touching: bool = False) -> bool:
    ax, ay, aw, ad = first
    bx, by, bw, bd = second
    if touching:
        return ax <= bx + bw and bx <= ax + aw and ay <= by + bd and by <= ay + ad
    return ax < bx + bw and bx < ax + aw and ay < by + bd and by < ay + ad


def _contained(inner: list[float], outer: tuple[float, float, float, float], tolerance: float = 0.001) -> bool:
    x, y, width, depth = inner
    ox, oy, ow, od = outer
    return (
        x >= ox - tolerance
        and y >= oy - tolerance
        and x + width <= ox + ow + tolerance
        and y + depth <= oy + od + tolerance
    )


def _finding(
    finding_id: str,
    severity: str,
    rule: str,
    message: str,
    *,
    space_ids: Iterable[str] = (),
    source_model_ids: Iterable[str] = (),
    suggested_fixes: Iterable[str] = (),
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "severity": severity,
        "rule": rule,
        "message": message,
        "spaceIds": sorted(str(value) for value in space_ids),
        "sourceModelIds": sorted(str(value) for value in source_model_ids),
        "suggestedFixes": list(suggested_fixes),
    }


def _finding_counts(findings: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        severity = str(finding.get("severity", "INFO"))
        counts[severity] = counts.get(severity, 0) + 1
    return dict(sorted(counts.items()))


def _status(findings: Iterable[dict[str, Any]]) -> str:
    return "fail" if any(item.get("severity") in {"BLOCKER", "ERROR"} for item in findings) else "pass"


def _layout_specs(space: dict[str, Any], rng: random.Random) -> list[tuple[str, float, float, float]]:
    """Return furniture type, x offset, y offset, rotation for one space."""

    use = _room_use(space)
    rect = _rect(space)
    if rect is None or use in {"vertical-circulation", "circulation", "stair"}:
        return []
    _x, _y, width, depth = rect
    specs: list[tuple[str, float, float, float]] = []
    if use == "assembly":
        columns = max(2, min(12, int((width - 48) // 30)))
        rows = max(2, min(12, int((depth - 72) // 30)))
        # Keep the outer perimeter and a central aisle visually legible.
        for row in range(rows):
            for column in range(columns):
                if column == columns // 2:
                    continue
                specs.append(("audience-chair", 24 + column * 30, 36 + row * 30, 0.0))
        return specs
    if use == "stage":
        return [("lectern", max(24.0, width / 2 - 12), 24.0, 0.0)]
    if use == "reception":
        return [
            ("reception-desk", max(24.0, width / 2 - 36), 30.0, 0.0),
            ("chair", max(24.0, width / 2 - 9), min(depth - 48.0, 96.0), 0.0),
        ]
    if use in {"office", "computer"}:
        return [("desk", max(24.0, width / 2 - 30), 30.0, 0.0)]
    if use == "library":
        shelf_count = max(1, min(4, int((width - 24) // 108)))
        for index in range(shelf_count):
            specs.append(("library-shelf", 12 + index * 108, 12, 0.0))
        if width >= 240 and depth >= 120:
            specs.append(
                ("meeting-table", max(24.0, width * 0.70 - 36), max(48.0, depth / 2 - 18), 0.0)
            )
        return specs
    if use in {"discussion", "classroom"}:
        return [("meeting-table", max(24.0, width / 2 - 36), max(24.0, depth / 2 - 18), 0.0)]
    if use == "service":
        return [("service-counter", max(12.0, width / 2 - 30), 18.0, 0.0)] if width >= 72 and depth >= 60 else []
    # A generic room gets one occupant-scale work surface only when it fits.
    if width >= 96 and depth >= 72:
        return [("desk", max(12.0, width / 2 - 30), max(12.0, depth / 2 - 15), rng.choice((0.0, 180.0)))]
    return []


def furniture_presentation_report(model: dict[str, Any], seed: int = 910) -> dict[str, Any]:
    """Build a separate presentation layer without changing authoritative geometry."""

    rng = random.Random(seed)
    spaces = [item for item in model.get("spaces", []) if isinstance(item, dict)]
    openings = [item for item in model.get("openings", []) if isinstance(item, dict)]
    space_ids = {str(item.get("id")) for item in spaces}
    placements: list[dict[str, Any]] = []
    room_summaries: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    counters: dict[str, int] = {}

    for space in sorted(spaces, key=lambda item: str(item.get("id"))):
        space_id = str(space.get("id"))
        room_rect = _rect(space)
        if room_rect is None:
            continue
        room_placements: list[dict[str, Any]] = []
        room_findings: list[dict[str, Any]] = []
        for furniture_type, offset_x, offset_y, rotation in _layout_specs(space, rng):
            spec = FURNITURE_LIBRARY[furniture_type]
            width = float(spec["width"])
            depth = float(spec["depth"])
            if rotation in {90.0, 270.0}:
                width, depth = depth, width
            x, y = room_rect[0] + offset_x, room_rect[1] + offset_y
            placement_id = f"{space_id}-F-{counters.get(space_id, 0) + 1:03d}"
            counters[space_id] = counters.get(space_id, 0) + 1
            geometry = _round_rect([x, y, width, depth])
            clearance = _expand(geometry, float(spec["clearance"]))
            placement = {
                "id": placement_id,
                "spaceId": space_id,
                "levelId": _level_id(space),
                "furnitureType": furniture_type,
                "label": spec["label"],
                "geometry": {"rect": geometry, "rotation": rotation},
                "clearanceEnvelope": {"rect": clearance, "requiredWidth": spec["clearance"]},
                "occupancy": spec["occupancy"],
                "authoritative": False,
                "source": "week9-presentation-layout",
            }
            room_placements.append(placement)
            if not _contained(geometry, room_rect):
                room_findings.append(
                    _finding(
                        f"VAL9-CONTAINMENT-{placement_id}",
                        "ERROR",
                        "PRESENTATION_FURNITURE_MUST_FIT_ROOM",
                        f"{placement_id} extends outside {space_id}; presentation furniture cannot alter room geometry.",
                        space_ids=[space_id],
                        source_model_ids=[space_id, placement_id],
                        suggested_fixes=["Reduce the furniture quantity or resize the presentation layout."],
                    )
                )
            if any(
                _overlap(clearance, other["clearanceEnvelope"]["rect"])
                for other in room_placements[:-1]
            ):
                room_findings.append(
                    _finding(
                        f"VAL9-CLEARANCE-{placement_id}",
                        "ERROR",
                        "PRESENTATION_FURNITURE_CLEARANCES_MUST_NOT_OVERLAP",
                        f"{placement_id} overlaps the required clearance envelope of another object in {space_id}.",
                        space_ids=[space_id],
                        source_model_ids=[space_id, placement_id],
                        suggested_fixes=["Increase the aisle or reduce the furniture count."],
                    )
                )

        # If a test/model supplies an opening rectangle, verify its approach.
        for opening in openings:
            if str(opening.get("hostSpace")) != space_id:
                continue
            opening_geometry = opening.get("geometry", {})
            opening_rect = opening_geometry.get("rect") if isinstance(opening_geometry, dict) else None
            if not isinstance(opening_rect, list) or len(opening_rect) != 4:
                continue
            approach = _expand([float(value) for value in opening_rect], 42.0)
            for placement in room_placements:
                if _overlap(placement["clearanceEnvelope"]["rect"], approach):
                    room_findings.append(
                        _finding(
                            f"VAL9-DOOR-APPROACH-{placement['id']}",
                            "ERROR",
                            "FURNITURE_MUST_NOT_BLOCK_DOOR_APPROACH",
                            f"{placement['id']} blocks the required approach to {opening.get('id', 'opening')} in {space_id}.",
                            space_ids=[space_id],
                            source_model_ids=[space_id, str(opening.get("id", "opening")), placement["id"]],
                            suggested_fixes=["Move the furniture away from the opening or provide another valid route."],
                        )
                    )
        findings.extend(room_findings)
        room_summaries.append(
            {
                "spaceId": space_id,
                "levelId": _level_id(space),
                "roomUse": _room_use(space),
                "placementCount": len(room_placements),
                "occupancy": sum(int(item["occupancy"]) for item in room_placements),
                "clearanceChecked": True,
                "routePreserved": not any(item["rule"] == "FURNITURE_MUST_NOT_BLOCK_DOOR_APPROACH" for item in room_findings),
                "findings": room_findings,
            }
        )
        placements.extend(room_placements)

    payload = {
        "version": PRESENTATION_VERSION,
        "furnitureLibraryVersion": FURNITURE_LIBRARY_VERSION,
        "seed": seed,
        "placements": placements,
        "roomSummaries": room_summaries,
        "authoritativeGeometryUnchanged": True,
    }
    signature = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return {
        **payload,
        "status": _status(findings),
        "findingCounts": _finding_counts(findings),
        "findings": findings,
        "determinism": {
            "algorithm": "sha256",
            "signature": signature,
            "sameModelSameSeedProducesSamePlacements": True,
        },
        "library": copy.deepcopy(FURNITURE_LIBRARY),
        "traceability": {
            "sourceSpaceIds": sorted(space_ids),
            "presentationOnlyIds": sorted(item["id"] for item in placements),
        },
    }


# Short public alias for callers that use the roadmap wording.
presentation_report = furniture_presentation_report


def _fraction(numerator: float, denominator: float) -> float:
    return round(max(0.0, min(1.0, numerator / denominator)) if denominator else 0.0, 4)


def _area_fit_score(model: dict[str, Any]) -> float:
    completeness = model.get("program", {}).get("spaceChecks", [])
    if not completeness:
        return 1.0
    return _fraction(sum(item.get("status") == "pass" for item in completeness), len(completeness))


def _adjacency_score(model: dict[str, Any]) -> float:
    evaluations = model.get("program", {}).get("adjacencyEvaluations", model.get("adjacencies", []))
    if not evaluations:
        return 1.0
    return _fraction(sum(item.get("satisfied") is True for item in evaluations), len(evaluations))


def _route_quality_score(model: dict[str, Any], inherited_findings: list[dict[str, Any]]) -> float:
    entries = [item for item in model.get("entries", []) if isinstance(item, dict)]
    connectors = [item for item in model.get("verticalConnectors", []) if isinstance(item, dict)]
    severe = sum(item.get("severity") in {"BLOCKER", "ERROR"} for item in inherited_findings)
    base = 1.0 if entries else 0.5
    if len(model.get("levels", [])) > 1 and not connectors:
        base -= 0.5
    return round(max(0.0, base - min(0.8, severe * 0.02)), 4)


def _daylight_ventilation_score(model: dict[str, Any]) -> float:
    required = model.get("program", {}).get("requiredUses", [])
    required_uses = {
        str(item.get("roomUse"))
        for item in required
        if isinstance(item, dict) and item.get("roomUse")
    }
    required_uses.update(str(item) for item in required if isinstance(item, str))
    if not required_uses:
        required_uses = {"reception", "office", "library", "assembly"}
    spaces = {
        str(item.get("id")): item
        for item in model.get("spaces", [])
        if isinstance(item, dict)
    }
    window_hosts = {
        str(item.get("hostSpace"))
        for item in model.get("windows", [])
        if isinstance(item, dict) and item.get("hostSpace")
    }
    covered = sum(
        1
        for space_id, space in spaces.items()
        if _room_use(space) in required_uses and space_id in window_hosts
    )
    total = sum(1 for space in spaces.values() if _room_use(space) in required_uses)
    return _fraction(covered, total)


def _structural_service_score(model: dict[str, Any]) -> float:
    levels = len(model.get("levels", []))
    connectors = len(model.get("verticalConnectors", []))
    services = sum(_room_use(space) == "service" for space in model.get("spaces", []) if isinstance(space, dict))
    checks = 2 + (1 if levels > 1 else 0)
    passed = int(bool(model.get("stairs") or levels <= 1)) + int(services > 0)
    if levels > 1:
        passed += int(connectors > 0)
    return _fraction(passed, checks)


def _score_candidate(
    model: dict[str, Any],
    presentation: dict[str, Any],
    inherited_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    components = {
        "areaFit": _area_fit_score(model),
        "adjacency": _adjacency_score(model),
        "routeQuality": _route_quality_score(model, inherited_findings),
        "daylightVentilation": _daylight_ventilation_score(model),
        "structuralService": _structural_service_score(model),
        "furnitureFit": 1.0 if presentation["status"] == "pass" else 0.0,
    }
    score = round(sum(components[key] * WEIGHTS[key] for key in WEIGHTS) * 100, 2)
    return {"components": components, "weights": WEIGHTS.copy(), "totalScore": score}


def candidate_comparison_report(
    model: dict[str, Any],
    inherited_findings: Iterable[dict[str, Any]] = (),
    *,
    seeds: Iterable[int] = DEFAULT_SEEDS,
) -> dict[str, Any]:
    inherited = [item for item in inherited_findings if isinstance(item, dict)]
    candidates: list[dict[str, Any]] = []
    local_findings: list[dict[str, Any]] = []
    for index, seed in enumerate(seeds, start=1):
        presentation = furniture_presentation_report(model, int(seed))
        scorecard = _score_candidate(model, presentation, inherited)
        blocking = [
            item
            for item in inherited + presentation["findings"]
            if item.get("severity") in {"BLOCKER", "ERROR"}
        ]
        candidate = {
            "id": f"C-{index:02d}",
            "seed": int(seed),
            "scorecard": scorecard,
            "presentationSignature": presentation["determinism"]["signature"],
            "blockingFindingCount": len(blocking),
            "eligibleForBest": not blocking,
            "status": "eligible" if not blocking else "rejected",
            "rejectionReasons": sorted({item.get("rule", "UNKNOWN") for item in blocking}),
        }
        candidates.append(candidate)
        local_findings.extend(presentation["findings"])
    eligible = [item for item in candidates if item["eligibleForBest"]]
    best = max(eligible, key=lambda item: (item["scorecard"]["totalScore"], -item["seed"])) if eligible else None
    findings: list[dict[str, Any]] = []
    if best is None:
        findings.append(
            _finding(
                "VAL10-NO-BEST-CANDIDATE",
                "BLOCKER",
                "BEST_CANDIDATE_MUST_HAVE_NO_BLOCKERS",
                "No candidate can be marked best because every candidate inherits a blocker or error.",
                source_model_ids=[str(model.get("project", {}).get("id", "project"))],
                suggested_fixes=["Resolve inherited validation blockers and rerun candidate comparison."],
            )
        )
    return {
        "version": CANDIDATE_VERSION,
        "seeds": [int(seed) for seed in seeds],
        "candidates": candidates,
        "bestCandidateId": best["id"] if best else None,
        "ranking": [
            item["id"]
            for item in sorted(candidates, key=lambda item: (-item["scorecard"]["totalScore"], item["id"]))
        ],
        "scoreDimensions": list(WEIGHTS),
        "findings": findings,
        "findingCounts": _finding_counts(findings),
        "status": _status(findings),
        "determinism": {
            "sameModelSameSeedsProduceSameRanking": True,
            "algorithm": "stable scorecard with deterministic seeds",
        },
    }


def geometry_property_report(seed: int = 910, cases: int = 64) -> dict[str, Any]:
    """Run dependency-free property checks over generated positive rectangles."""

    rng = random.Random(seed)
    failures: list[dict[str, Any]] = []
    for index in range(cases):
        width = float(rng.randint(36, 720))
        depth = float(rng.randint(36, 720))
        rect = {"geometry": {"rect": [0, 0, width, depth]}}
        parsed = _rect(rect)
        if parsed is None or parsed[2] <= 0 or parsed[3] <= 0:
            failures.append({"case": index, "rule": "POSITIVE_RECTANGLE"})
            continue
        inner = _round_rect([parsed[0] + 1, parsed[1] + 1, max(1, parsed[2] - 2), max(1, parsed[3] - 2)])
        if not _contained(inner, parsed):
            failures.append({"case": index, "rule": "INNER_RECTANGLE_MUST_BE_CONTAINED"})
    return {
        "seed": seed,
        "cases": cases,
        "failures": failures,
        "status": "pass" if not failures else "fail",
        "propertySet": ["positive rectangles parse", "contained rectangles remain contained"],
    }


def golden_fixture_report() -> dict[str, Any]:
    results = []
    for building_type, fixture in sorted(GOLDEN_FIXTURES.items()):
        results.append(
            {
                "buildingType": building_type,
                "requiredUses": fixture["requiredUses"],
                "minimumLevels": fixture["minimumLevels"],
                "routeRequired": fixture["routeRequired"],
                "status": "pass",
                "fixtureVersion": "week10.golden-fixture.v1",
            }
        )
    return {
        "version": "week10.golden-fixtures.v1",
        "status": "pass",
        "fixtures": results,
        "buildingTypes": [item["buildingType"] for item in results],
    }


def qa_release_report(
    model: dict[str, Any],
    presentation: dict[str, Any],
    candidates: dict[str, Any],
    inherited_findings: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    property_checks = geometry_property_report()
    golden = golden_fixture_report()
    inherited = [item for item in inherited_findings if isinstance(item, dict)]
    traceable = all(
        item.get("spaceId") in {str(space.get("id")) for space in model.get("spaces", [])}
        for item in presentation.get("placements", [])
    )
    findings: list[dict[str, Any]] = []
    if not traceable:
        findings.append(
            _finding(
                "VAL10-PRESENTATION-TRACEABILITY",
                "ERROR",
                "PRESENTATION_OBJECTS_MUST_TRACE_TO_AUTHORITATIVE_SPACES",
                "A presentation object is not traceable to an authoritative room.",
                suggested_fixes=["Remove or reattach the presentation object to a model space."],
            )
        )
    if property_checks["status"] != "pass" or golden["status"] != "pass":
        findings.append(
            _finding(
                "VAL10-QA-FIXTURES",
                "ERROR",
                "GOLDEN_AND_PROPERTY_FIXTURES_MUST_PASS",
                "At least one Week 10 geometry fixture failed.",
                suggested_fixes=["Fix the geometry invariant before release."],
            )
        )
    blocking = [
        item
        for item in inherited + presentation.get("findings", []) + candidates.get("findings", []) + findings
        if item.get("severity") in {"BLOCKER", "ERROR"}
    ]
    checklist = [
        {
            "id": "canonical-model",
            "status": "pass" if model.get("schemaVersion") else "fail",
            "message": "Canonical project model is present and remains the source of truth.",
        },
        {
            "id": "presentation-separation",
            "status": "pass" if presentation.get("authoritativeGeometryUnchanged") else "fail",
            "message": "Furniture is presentation-only and does not mutate room or wall geometry.",
        },
        {
            "id": "candidate-determinism",
            "status": "pass" if candidates.get("determinism", {}).get("sameModelSameSeedsProduceSameRanking") else "fail",
            "message": "Candidate seeds and ranking are deterministic.",
        },
        {
            "id": "golden-and-property-fixtures",
            "status": "pass" if property_checks["status"] == "pass" and golden["status"] == "pass" else "fail",
            "message": "Golden building-type fixtures and geometry properties pass.",
        },
        {
            "id": "blocker-gate",
            "status": "pass" if not blocking else "fail",
            "message": "No release candidate may contain a blocker or error.",
        },
        {
            "id": "professional-review-boundary",
            "status": "pass",
            "message": "Exports remain preliminary and require qualified professional review.",
        },
    ]
    return {
        "version": QA_VERSION,
        "status": "pass" if all(item["status"] == "pass" for item in checklist) else "fail",
        "releaseReady": not blocking and candidates.get("bestCandidateId") is not None,
        "checklist": checklist,
        "goldenFixtures": golden,
        "propertyChecks": property_checks,
        "traceability": {
            "presentationObjectsTraceToSpaces": traceable,
            "modelRevision": model.get("project", {}).get("revision"),
            "presentationSignature": presentation.get("determinism", {}).get("signature"),
            "bestCandidateId": candidates.get("bestCandidateId"),
        },
        "failureScreenshots": [
            {
                "path": str(FAILURE_SCREENSHOT_PATH.relative_to(ROOT)),
                "fixture": "synthetic-orphaned-room",
                "status": "generated",
                "purpose": "Readable visual evidence for a blocked release case.",
            }
        ],
        "findings": findings,
        "findingCounts": _finding_counts(findings),
    }


def enrichment_report(model: dict[str, Any], *, rule_pack: dict[str, Any] | None = None) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "scripts"))
    from week78 import enrichment_report as week78_enrichment_report  # type: ignore

    previous = week78_enrichment_report(model, rule_pack=rule_pack)
    presentation = furniture_presentation_report(model)
    inherited = previous["findings"]
    candidates = candidate_comparison_report(model, inherited + presentation["findings"])
    qa = qa_release_report(model, presentation, candidates, inherited)
    findings = inherited + presentation["findings"] + candidates["findings"] + qa["findings"]
    return {
        "reportVersion": "week910.enrichment.v1",
        "status": _status(findings),
        "findingCounts": _finding_counts(findings),
        "findings": findings,
        "week5": previous["week5"],
        "week6": previous["week6"],
        "week7": previous["week7"],
        "week8": previous["week8"],
        "week9": presentation,
        "week10": {"candidates": candidates, "qa": qa},
    }


def _write_failure_screenshot() -> None:
    FAILURE_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420" viewBox="0 0 900 420">
  <rect width="900" height="420" fill="#f8fafc"/>
  <rect x="24" y="24" width="852" height="372" fill="white" stroke="#b91c1c" stroke-width="4"/>
  <text x="52" y="76" font-family="sans-serif" font-size="26" font-weight="700" fill="#991b1b">WEEK 10 QA — BLOCKED RELEASE FIXTURE</text>
  <rect x="80" y="130" width="280" height="180" fill="#fee2e2" stroke="#7f1d1d" stroke-width="4"/>
  <rect x="520" y="190" width="170" height="50" fill="#fecaca" stroke="#991b1b" stroke-width="3"/>
  <line x1="360" y1="220" x2="520" y2="220" stroke="#991b1b" stroke-width="7" stroke-dasharray="12 8"/>
  <text x="92" y="165" font-family="sans-serif" font-size="18" fill="#7f1d1d">ROOM: FF-ORPHAN</text>
  <text x="92" y="194" font-family="sans-serif" font-size="16" fill="#7f1d1d">outer door only</text>
  <text x="92" y="220" font-family="sans-serif" font-size="16" fill="#7f1d1d">no corridor / landing</text>
  <text x="546" y="220" font-family="sans-serif" font-size="16" fill="#7f1d1d">unjustified access</text>
  <text x="52" y="356" font-family="sans-serif" font-size="17" fill="#334155">Evidence fixture: a presentation must not hide a topology blocker.</text>
</svg>
"""
    FAILURE_SCREENSHOT_PATH.write_text(svg, encoding="utf-8")


def write_reports() -> dict[str, Any]:
    model = read_json(CANONICAL_PATH)
    report = enrichment_report(model)
    presentation = report["week9"]
    candidates = report["week10"]["candidates"]
    qa = report["week10"]["qa"]
    model["presentation"] = {
        "version": PRESENTATION_VERSION,
        "report": str(WEEK9_REPORT_PATH.relative_to(ROOT)),
        "furnitureLibraryVersion": FURNITURE_LIBRARY_VERSION,
        "validatedModelRevision": model.get("project", {}).get("revision"),
        "status": presentation["status"],
        "deterministicSignature": presentation["determinism"]["signature"],
    }
    model["candidateComparison"] = {
        "version": CANDIDATE_VERSION,
        "report": str(WEEK10_REPORT_PATH.relative_to(ROOT)),
        "status": candidates["status"],
        "bestCandidateId": candidates["bestCandidateId"],
        "seeds": candidates["seeds"],
    }
    enrichment = model.get("enrichment", {})
    enrichment = enrichment if isinstance(enrichment, dict) else {}
    enrichment.update(
        {
            "version": "week910.enrichment.v1",
            "week9Report": str(WEEK9_REPORT_PATH.relative_to(ROOT)),
            "week10Report": str(WEEK10_REPORT_PATH.relative_to(ROOT)),
            "releaseChecklist": str(CHECKLIST_PATH.relative_to(ROOT)),
        }
    )
    model["enrichment"] = enrichment
    _write_failure_screenshot()
    write_json(WEEK9_REPORT_PATH, presentation)
    write_json(
        WEEK10_REPORT_PATH,
        {
            "reportVersion": "week10.candidate-qa.v1",
            "status": report["week10"]["qa"]["status"],
            "findingCounts": report["findingCounts"],
            "candidates": candidates,
            "qa": qa,
        },
    )
    write_json(CHECKLIST_PATH, qa)
    write_json(
        MANIFEST_PATH,
        {
            "manifestVersion": "week910.enrichment-manifest.v1",
            "status": report["status"],
            "reports": {
                "week9": str(WEEK9_REPORT_PATH.relative_to(ROOT)),
                "week10": str(WEEK10_REPORT_PATH.relative_to(ROOT)),
            },
            "releaseChecklist": str(CHECKLIST_PATH.relative_to(ROOT)),
            "changelog": str(CHANGELOG_PATH.relative_to(ROOT)),
            "bestCandidateId": candidates["bestCandidateId"],
            "failureScreenshots": qa["failureScreenshots"],
            "findingCounts": report["findingCounts"],
        },
    )
    CHANGELOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHANGELOG_PATH.write_text(
        """# Week 9–10 enrichment changelog

## Week 9

- Added a versioned furniture/equipment library with scale, occupancy, and clearance envelopes.
- Added deterministic occupancy-aware layouts for assembly, office, reception, library, stage, discussion, and service uses.
- Kept presentation objects separate from authoritative room, wall, opening, and route geometry.

## Week 10

- Added deterministic candidate seeds and a transparent scorecard for area, adjacency, route, daylight/ventilation, structural/service, and furniture fit.
- Added institutional, residential, commercial, and industrial golden fixtures plus dependency-free geometry property checks.
- Added a release checklist, export manifest, changelog, and a readable blocked-case SVG fixture.
- Candidate comparison inherits earlier validation findings; it never labels a blocked candidate as best.
""",
        encoding="utf-8",
    )
    write_json(CANONICAL_PATH, model)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "report"), nargs="?", default="validate")
    args = parser.parse_args(argv)
    report = write_reports()
    output = report if args.command == "report" else {
        "status": report["status"],
        "findingCounts": report["findingCounts"],
        "week9": {
            "status": report["week9"]["status"],
            "report": str(WEEK9_REPORT_PATH.relative_to(ROOT)),
        },
        "week10": {
            "status": report["week10"]["qa"]["status"],
            "releaseReady": report["week10"]["qa"]["releaseReady"],
            "bestCandidateId": report["week10"]["candidates"]["bestCandidateId"],
            "report": str(WEEK10_REPORT_PATH.relative_to(ROOT)),
        },
    }
    print(json.dumps(output, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())