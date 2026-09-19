#!/usr/bin/env python3
"""Week 15–16 parametric furnishing and candidate-studio enrichment.

The module deliberately keeps presentation objects separate from the
authoritative model.  It provides deterministic, reviewable planning aids:
asset metadata, clearance-aware placement/edit operations, candidate
comparison, non-destructive design layers, and render-job manifests.

Units are the canonical model's nominal inches.  This is not a code,
accessibility, fire, structural, MEP, survey, permit, or construction
certification.
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
ASSET_REPORT_PATH = REPORT_ROOT / "week15-parametric-assets-report.json"
CANDIDATE_REPORT_PATH = REPORT_ROOT / "week16-candidate-studio-report.json"
MANIFEST_PATH = REPORT_ROOT / "week1516-enrichment-manifest.json"
CHANGELOG_PATH = REPORT_ROOT / "week1516-changelog.md"

WEEK15_VERSION = "week15.parametric-assets.v1"
WEEK16_VERSION = "week16.candidate-studio.v1"
RENDER_VERSION = "week16.render-pipeline.v1"


def _asset(
    label: str,
    category: str,
    width: float,
    depth: float,
    height: float,
    *,
    room_uses: Iterable[str],
    occupancy: int = 0,
    service_side: str | None = None,
    preferred_walls: Iterable[str] = (),
    clearance: dict[str, float] | None = None,
    rotations: Iterable[int] = (0, 90),
) -> dict[str, Any]:
    clearances = {
        "front": 30.0,
        "back": 6.0,
        "left": 6.0,
        "right": 6.0,
        **(clearance or {}),
    }
    return {
        "label": label,
        "category": category,
        "dimensions": {"width": width, "depth": depth, "height": height, "unit": "inch"},
        "width": width,
        "depth": depth,
        "height": height,
        "rotationRules": {"allowedDegrees": list(rotations), "stepDegrees": 90},
        "preferredWallRelationships": list(preferred_walls),
        "serviceSide": service_side,
        "occupancy": occupancy,
        "clearanceEnvelope": clearances,
        "roomUses": list(room_uses),
        "authoritative": False,
        "presentationOnly": True,
    }


ASSET_CATALOG: dict[str, dict[str, Any]] = {
    "work-desk": _asset("Work desk", "furniture", 60, 30, 30, room_uses=("office", "chamber"), occupancy=1, preferred_walls=("back",), clearance={"front": 36}),
    "executive-desk": _asset("Executive desk", "furniture", 72, 36, 30, room_uses=("office", "chamber"), occupancy=1, preferred_walls=("back",), clearance={"front": 42}),
    "visitor-chair": _asset("Visitor chair", "seating", 20, 20, 32, room_uses=("office", "chamber", "waiting"), occupancy=1, clearance={"front": 24}),
    "audience-chair": _asset("Audience chair", "seating", 18, 18, 32, room_uses=("hall", "assembly", "classroom"), occupancy=1, clearance={"front": 18, "back": 12}),
    "bench-row": _asset("Bench seating row", "seating", 96, 20, 32, room_uses=("hall", "assembly"), occupancy=4, clearance={"front": 48, "back": 18}),
    "library-table": _asset("Library table", "library", 72, 36, 30, room_uses=("library",), occupancy=6, clearance={"front": 36, "back": 36, "left": 24, "right": 24}),
    "library-shelf": _asset("Library shelf", "library", 72, 14, 84, room_uses=("library",), preferred_walls=("back",), clearance={"front": 36}),
    "reception-counter": _asset("Reception counter", "counter", 72, 30, 42, room_uses=("reception", "lobby"), occupancy=2, service_side="front", preferred_walls=("back",), clearance={"front": 48}),
    "service-counter": _asset("Service counter", "counter", 60, 24, 36, room_uses=("service", "pantry"), occupancy=1, service_side="front", preferred_walls=("back",), clearance={"front": 36}),
    "sanitary-ware": _asset("Accessible sanitary fixture", "sanitaryware", 30, 54, 32, room_uses=("service", "healthcare"), service_side="right", clearance={"front": 60, "left": 12, "right": 12}),
    "lavatory-fixture": _asset("Lavatory fixture", "fixtures", 24, 20, 32, room_uses=("service", "healthcare"), service_side="back", clearance={"front": 42}),
    "appliance-block": _asset("Appliance block", "appliance", 36, 30, 36, room_uses=("service", "retail"), service_side="back", preferred_walls=("back",), clearance={"front": 36}),
    "dais": _asset("Dais", "dais", 144, 60, 18, room_uses=("hall", "assembly"), occupancy=4, preferred_walls=("back",), clearance={"front": 60}),
    "lectern": _asset("Lectern", "dais", 24, 20, 42, room_uses=("hall", "assembly"), occupancy=1, clearance={"front": 36}),
    "vehicle-bay": _asset("Vehicle bay", "vehicle", 108, 216, 60, room_uses=("industrial", "retail"), clearance={"front": 36, "back": 36, "left": 24, "right": 24}),
    "equipment-bench": _asset("Industrial equipment bench", "industrial-equipment", 96, 36, 36, room_uses=("industrial",), service_side="back", clearance={"front": 48, "back": 24, "left": 18, "right": 18}),
    "patient-bed": _asset("Patient bed", "healthcare", 42, 84, 24, room_uses=("healthcare",), occupancy=1, clearance={"front": 36, "left": 36, "right": 36}),
}


ROOM_TEMPLATES: dict[str, dict[str, Any]] = {
    "residential": {"recommendedAssets": ["work-desk", "visitor-chair"], "minimumClearRoute": 36},
    "office": {"recommendedAssets": ["executive-desk", "visitor-chair"], "minimumClearRoute": 36},
    "chamber": {"recommendedAssets": ["executive-desk", "visitor-chair"], "minimumClearRoute": 36},
    "hall": {"recommendedAssets": ["audience-chair", "bench-row", "dais", "lectern"], "minimumClearRoute": 48},
    "classroom": {"recommendedAssets": ["library-table", "visitor-chair"], "minimumClearRoute": 36},
    "library": {"recommendedAssets": ["library-shelf", "library-table"], "minimumClearRoute": 36},
    "healthcare": {"recommendedAssets": ["patient-bed", "sanitary-ware"], "minimumClearRoute": 48},
    "retail": {"recommendedAssets": ["reception-counter", "appliance-block"], "minimumClearRoute": 48},
    "light-industrial": {"recommendedAssets": ["vehicle-bay", "equipment-bench"], "minimumClearRoute": 48},
}


def _rect(value: Any) -> list[float] | None:
    if isinstance(value, dict):
        value = value.get("rect")
    if isinstance(value, (list, tuple)) and len(value) == 4:
        return [float(item) for item in value]
    return None


def _space_rect(space: dict[str, Any]) -> list[float] | None:
    return _rect(space.get("rect")) or _rect(space.get("geometry", {}).get("rect"))


def _expand(rect: list[float], clearances: dict[str, float] | float) -> list[float]:
    if isinstance(clearances, (int, float)):
        value = float(clearances)
        return [rect[0] - value, rect[1] - value, rect[2] + value, rect[3] + value]
    return [
        rect[0] - float(clearances.get("left", 0)),
        rect[1] - float(clearances.get("back", 0)),
        rect[2] + float(clearances.get("right", 0)),
        rect[3] + float(clearances.get("front", 0)),
    ]


def _overlap(first: list[float], second: list[float]) -> bool:
    return first[0] < second[2] and first[2] > second[0] and first[1] < second[3] and first[3] > second[1]


def _inside(inner: list[float], outer: list[float]) -> bool:
    return inner[0] >= outer[0] and inner[1] >= outer[1] and inner[2] <= outer[2] and inner[3] <= outer[3]


def _finding(rule: str, message: str, *, severity: str = "BLOCKER", object_id: str | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"severity": severity, "rule": rule, "message": message}
    if object_id:
        item["objectId"] = object_id
    return item


def _room_use(space: dict[str, Any]) -> str:
    value = str(space.get("roomUse") or space.get("use") or space.get("name", "")).lower().replace(" ", "-")
    return {"assembly": "hall", "assembly-hall": "hall", "lightindustrial": "light-industrial"}.get(value, value)


def asset_catalog() -> dict[str, Any]:
    return {"version": WEEK15_VERSION, "assets": copy.deepcopy(ASSET_CATALOG), "roomTemplates": copy.deepcopy(ROOM_TEMPLATES)}


def _placement_rect(spec: dict[str, Any], x: float, y: float, rotation: int) -> list[float]:
    quarter_turn = int(rotation) % 180 == 90
    width = float(spec["depth"] if quarter_turn else spec["width"])
    depth = float(spec["width"] if quarter_turn else spec["depth"])
    return [float(x), float(y), float(x) + width, float(y) + depth]


def _model_zones(model: dict[str, Any], host_space_id: str) -> list[tuple[str, list[float]]]:
    zones: list[tuple[str, list[float]]] = []
    for collection, rule in (("routes", "required route"), ("stairs", "stair"), ("serviceZones", "service zone")):
        for item in model.get(collection, []) or []:
            if item.get("hostSpace") not in (None, host_space_id) and item.get("spaceId") not in (None, host_space_id):
                continue
            geometry = _rect(item.get("geometry")) or _rect(item.get("rect"))
            if geometry:
                zones.append((rule, geometry))
    return zones


def validate_placement(
    model: dict[str, Any],
    placement: dict[str, Any],
    *,
    existing: Iterable[dict[str, Any]] = (),
) -> list[dict[str, Any]]:
    asset_id = str(placement.get("assetId", ""))
    spec = ASSET_CATALOG.get(asset_id)
    object_id = str(placement.get("id", asset_id or "asset"))
    if spec is None:
        return [_finding("ASSET_ID_MUST_EXIST", f"Unknown parametric asset {asset_id!r}.", object_id=object_id)]
    rect = _rect(placement.get("geometry")) or _rect(placement.get("rect"))
    if rect is None:
        return [_finding("ASSET_GEOMETRY_REQUIRED", "A placement needs a rectangular plan geometry.", object_id=object_id)]
    host_id = str(placement.get("hostSpaceId") or placement.get("spaceId") or "")
    space = next((item for item in model.get("spaces", []) if item.get("id") == host_id), None)
    findings: list[dict[str, Any]] = []
    if space is None:
        findings.append(_finding("ASSET_HOST_SPACE_REQUIRED", f"{object_id} is not hosted by a known room.", object_id=object_id))
        return findings
    space_rect = _space_rect(space)
    if space_rect and not _inside(_expand(rect, spec["clearanceEnvelope"]), space_rect):
        findings.append(_finding("ASSET_CLEARANCE_MUST_FIT_ROOM", f"{object_id} and its required clearance do not fit inside {host_id}.", object_id=object_id))
    clearance_rect = _expand(rect, spec["clearanceEnvelope"])
    for zone_name, zone_rect in _model_zones(model, host_id):
        if _overlap(clearance_rect, zone_rect):
            findings.append(_finding("ASSET_MUST_NOT_BLOCK_ZONE", f"{object_id} overlaps a {zone_name}.", object_id=object_id))
    for opening in model.get("openings", []) or []:
        if opening.get("hostSpace") != host_id:
            continue
        opening_rect = _rect(opening.get("geometry")) or _rect(opening.get("rect"))
        if opening_rect and _overlap(clearance_rect, _expand(opening_rect, 42)):
            findings.append(_finding("ASSET_MUST_NOT_BLOCK_DOOR_SWING", f"{object_id} blocks the approach or swing of {opening.get('id', 'opening')}.", object_id=object_id))
    for other in existing:
        if other.get("id") == object_id or other.get("hostSpaceId") != host_id:
            continue
        other_rect = _rect(other.get("clearanceEnvelope"))
        if other_rect and _overlap(clearance_rect, other_rect):
            findings.append(_finding("ASSET_CLEARANCES_MUST_NOT_OVERLAP", f"{object_id} overlaps the clearance envelope of {other.get('id', 'asset')}.", object_id=object_id))
    return findings


def _new_placement(asset_id: str, host_space_id: str, x: float, y: float, rotation: int = 0, *, object_id: str | None = None) -> dict[str, Any]:
    spec = ASSET_CATALOG[asset_id]
    rect = _placement_rect(spec, x, y, rotation)
    return {
        "id": object_id or f"asset-{asset_id}-{int(x)}-{int(y)}",
        "assetId": asset_id,
        "hostSpaceId": host_space_id,
        "rotation": int(rotation) % 360,
        "geometry": {"rect": rect},
        "clearanceEnvelope": _expand(rect, spec["clearanceEnvelope"]),
        "authoritative": False,
        "presentationOnly": True,
        "modelRevision": None,
    }


def find_valid_position(
    model: dict[str, Any],
    asset_id: str,
    host_space_id: str,
    *,
    existing: Iterable[dict[str, Any]] = (),
    step: float = 12.0,
) -> dict[str, Any] | None:
    if asset_id not in ASSET_CATALOG:
        raise ValueError(f"unknown asset: {asset_id}")
    space = next((item for item in model.get("spaces", []) if item.get("id") == host_space_id), None)
    space_rect = _space_rect(space or {})
    if not space_rect:
        return None
    for rotation in ASSET_CATALOG[asset_id]["rotationRules"]["allowedDegrees"]:
        spec = ASSET_CATALOG[asset_id]
        width = spec["depth"] if rotation % 180 == 90 else spec["width"]
        depth = spec["width"] if rotation % 180 == 90 else spec["depth"]
        y = space_rect[1]
        while y + depth <= space_rect[3]:
            x = space_rect[0]
            while x + width <= space_rect[2]:
                candidate = _new_placement(asset_id, host_space_id, x, y, rotation)
                if not validate_placement(model, candidate, existing=existing):
                    return candidate
                x += step
            y += step
    return None


def edit_placements(
    model: dict[str, Any],
    placements: list[dict[str, Any]],
    operation: dict[str, Any],
) -> dict[str, Any]:
    """Apply one typed presentation edit without mutating ``model``."""
    updated = copy.deepcopy(placements)
    kind = str(operation.get("type", ""))
    target_id = str(operation.get("targetId", ""))
    target = next((item for item in updated if item.get("id") == target_id), None)
    if kind == "duplicate":
        if target is None:
            raise ValueError("duplicate target not found")
        clone = copy.deepcopy(target)
        clone["id"] = str(operation.get("newId") or f"{target_id}-copy")
        dx, dy = float(operation.get("dx", 12)), float(operation.get("dy", 12))
        rect = _rect(clone["geometry"]) or [0, 0, 0, 0]
        clone["geometry"]["rect"] = [rect[0] + dx, rect[1] + dy, rect[2] + dx, rect[3] + dy]
        clone["clearanceEnvelope"] = _expand(clone["geometry"]["rect"], ASSET_CATALOG[clone["assetId"]]["clearanceEnvelope"])
        updated.append(clone)
    elif target is None:
        raise ValueError("edit target not found")
    elif kind == "drag":
        rect = _rect(target["geometry"]) or [0, 0, 0, 0]
        dx, dy = float(operation.get("dx", 0)), float(operation.get("dy", 0))
        target["geometry"]["rect"] = [rect[0] + dx, rect[1] + dy, rect[2] + dx, rect[3] + dy]
        target["clearanceEnvelope"] = _expand(target["geometry"]["rect"], ASSET_CATALOG[target["assetId"]]["clearanceEnvelope"])
    elif kind == "rotate":
        rotation = int(operation.get("rotation", target.get("rotation", 0))) % 360
        rect = _rect(target["geometry"]) or [0, 0, 0, 0]
        target["geometry"]["rect"] = _placement_rect(ASSET_CATALOG[target["assetId"]], rect[0], rect[1], rotation)
        target["rotation"] = rotation
        target["clearanceEnvelope"] = _expand(target["geometry"]["rect"], ASSET_CATALOG[target["assetId"]]["clearanceEnvelope"])
    elif kind == "replace":
        replacement = str(operation.get("assetId", ""))
        if replacement not in ASSET_CATALOG:
            raise ValueError("replacement asset not found")
        rect = _rect(target["geometry"]) or [0, 0, 0, 0]
        target.update(_new_placement(replacement, str(target["hostSpaceId"]), rect[0], rect[1], int(target.get("rotation", 0)), object_id=target_id))
    elif kind == "align":
        rect = _rect(target["geometry"]) or [0, 0, 0, 0]
        space = next(item for item in model.get("spaces", []) if item.get("id") == target.get("hostSpaceId"))
        bounds = _space_rect(space) or rect
        edge = str(operation.get("edge", "left"))
        if edge == "right":
            dx = bounds[2] - rect[2]
            dy = 0
        elif edge == "top":
            dx, dy = 0, bounds[3] - rect[3]
        elif edge == "bottom":
            dx, dy = 0, bounds[1] - rect[1]
        else:
            dx, dy = bounds[0] - rect[0], 0
        target["geometry"]["rect"] = [rect[0] + dx, rect[1] + dy, rect[2] + dx, rect[3] + dy]
        target["clearanceEnvelope"] = _expand(target["geometry"]["rect"], ASSET_CATALOG[target["assetId"]]["clearanceEnvelope"])
    elif kind == "find-valid-position":
        candidate = find_valid_position(model, target["assetId"], str(target["hostSpaceId"]), existing=[item for item in updated if item.get("id") != target_id])
        if candidate is None:
            raise ValueError("no valid position found")
        target.update(candidate)
        target["id"] = target_id
    else:
        raise ValueError(f"unsupported placement operation: {kind}")
    findings = []
    for item in updated:
        findings.extend(validate_placement(model, item, existing=[other for other in updated if other is not item]))
    return {"placements": updated, "findings": findings, "status": "blocked" if findings else "pass", "operation": copy.deepcopy(operation)}


def furnish_model(model: dict[str, Any], *, seed: int = 1516) -> dict[str, Any]:
    rng = random.Random(seed)
    placements: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for space in model.get("spaces", []) or []:
        use = _room_use(space)
        template = ROOM_TEMPLATES.get(use) or ROOM_TEMPLATES.get("office")
        if not template:
            continue
        asset_id = template["recommendedAssets"][rng.randrange(len(template["recommendedAssets"]))]
        candidate = find_valid_position(model, asset_id, str(space.get("id")), existing=placements)
        if candidate:
            candidate["modelRevision"] = model.get("project", {}).get("revision")
            candidate["id"] = f"{space.get('id')}-{asset_id}"
            placements.append(candidate)
        else:
            skipped.append({"spaceId": space.get("id"), "assetId": asset_id, "reason": "no clearance-valid position"})
    findings = []
    for item in placements:
        findings.extend(validate_placement(model, item, existing=[other for other in placements if other is not item]))
    payload = {
        "version": WEEK15_VERSION,
        "seed": seed,
        "placements": placements,
        "skipped": skipped,
        "findings": findings,
        "status": "blocked" if findings else "pass",
        "authoritativeGeometryUnchanged": True,
        "presentationOnly": True,
        "catalogVersion": WEEK15_VERSION,
    }
    payload["determinism"] = {"algorithm": "sha256", "signature": _signature(payload)}
    return payload


def _fraction(value: float, denominator: float = 1.0) -> float:
    return round(max(0.0, min(1.0, value / denominator if denominator else 0.0)), 4)


def _inherited_blocker(findings: Iterable[dict[str, Any]]) -> bool:
    return any(str(item.get("severity", "")).upper() in {"BLOCKER", "ERROR"} for item in findings)


def candidate_studio(model: dict[str, Any], *, seeds: Iterable[int] = (1516, 1523, 1547), inherited_findings: Iterable[dict[str, Any]] = ()) -> dict[str, Any]:
    inherited = list(inherited_findings)
    candidates: list[dict[str, Any]] = []
    for index, seed in enumerate(seeds, 1):
        furnishing = furnish_model(model, seed=int(seed))
        adjacency_items = model.get("adjacencies", []) or []
        adjacency_score = _fraction(sum(bool(item.get("satisfied")) for item in adjacency_items), len(adjacency_items) or 1)
        spaces = model.get("spaces", []) or []
        daylight = _fraction(sum(bool(item.get("windows")) or bool(item.get("daylight")) for item in spaces), len(spaces) or 1)
        metrics = {
            "areaFit": _fraction(sum(1 for item in (model.get("program", {}).get("spaceChecks", []) or []) if item.get("status") in {"pass", "warning"}), len(model.get("program", {}).get("spaceChecks", []) or []) or 1),
            "adjacencySatisfaction": adjacency_score,
            "routeQuality": 0.0 if any(item.get("accessIntent") == "blocked" for item in spaces) else 1.0,
            "daylightVentilation": daylight or 0.5,
            "verticalCoordination": 1.0 if model.get("verticalConnectors") else (0.5 if len(model.get("levels", [])) <= 1 else 0.0),
            "furnitureFit": 1.0 if furnishing["status"] == "pass" else 0.0,
            "visualQuality": round(0.72 + ((int(seed) % 17) / 100), 4),
        }
        score = round(sum(metrics.values()) / len(metrics), 4)
        findings = inherited + list(furnishing["findings"])
        candidates.append({
            "id": f"C-15-{index:02d}",
            "seed": int(seed),
            "metrics": metrics,
            "score": score,
            "eligibleForBest": not _inherited_blocker(findings),
            "blockerCount": sum(1 for item in findings if str(item.get("severity", "")).upper() in {"BLOCKER", "ERROR"}),
            "furnishingSignature": furnishing["determinism"]["signature"],
            "technicalPlanRevision": model.get("project", {}).get("revision"),
            "presentationRenderMustMatchModel": True,
        })
    eligible = [item for item in candidates if item["eligibleForBest"]]
    ranking = [item["id"] for item in sorted(candidates, key=lambda value: (-value["eligibleForBest"], -value["score"], value["seed"]))]
    best = max(eligible, key=lambda item: (item["score"], -item["seed"]))["id"] if eligible else None
    findings: list[dict[str, Any]] = []
    if best is None:
        findings.append(_finding("BEST_CANDIDATE_MUST_HAVE_NO_BLOCKERS", "No candidate can win while inherited or furnishing blockers remain."))
    return {
        "version": WEEK16_VERSION,
        "seeds": [int(value) for value in seeds],
        "candidates": candidates,
        "ranking": ranking,
        "bestCandidateId": best,
        "findings": findings,
        "status": "blocked" if findings else "pass",
        "comparisonMetrics": ["areaFit", "adjacencySatisfaction", "routeQuality", "daylightVentilation", "verticalCoordination", "furnitureFit", "visualQuality"],
    }


def _signature(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def design_package(model: dict[str, Any], candidate_id: str | None, *, seed: int = 1516) -> dict[str, Any]:
    model_revision = model.get("project", {}).get("revision")
    palette = ["#17324D", "#D8B26E", "#F4F0E8", "#6A7B6B"]
    layers = [
        {"id": "materials", "kind": "presentation", "authoritative": False, "sourceModelRevision": model_revision, "materialIds": ["stone-light", "wood-oak", "metal-bronze"]},
        {"id": "decor", "kind": "presentation", "authoritative": False, "sourceModelRevision": model_revision, "visible": True},
        {"id": "lighting", "kind": "presentation", "authoritative": False, "sourceModelRevision": model_revision, "preset": "daylight-soft"},
    ]
    materials = [
        {"id": "stone-light", "label": "Light stone", "finish": "matte", "colour": "#D8D2C4"},
        {"id": "wood-oak", "label": "Oak timber", "finish": "satin", "colour": "#A9794F"},
        {"id": "metal-bronze", "label": "Bronze metal", "finish": "brushed", "colour": "#8A6544"},
    ]
    jobs = [render_job(kind, model_revision, candidate_id, seed) for kind in ("render", "panorama", "presentation-sheet")]
    return {
        "version": RENDER_VERSION,
        "candidateId": candidate_id,
        "modelRevision": model_revision,
        "moodboard": {"styleTags": ["institutional", "warm-modern", "professional"], "palette": palette, "referenceImages": [], "materials": materials, "lightingPresets": ["daylight-soft", "evening-neutral"]},
        "materials": materials,
        "designLayers": layers,
        "renderJobs": jobs,
        "technicalPlanSideBySide": {"required": True, "modelRevision": model_revision, "candidateId": candidate_id},
        "authoritativeGeometryChanged": False,
    }


def render_job(kind: str, model_revision: Any, candidate_id: str | None, seed: int) -> dict[str, Any]:
    if kind not in {"render", "panorama", "presentation-sheet"}:
        raise ValueError("unsupported render job")
    job_id = "render-" + _signature({"kind": kind, "revision": model_revision, "candidate": candidate_id, "seed": seed})[:12]
    return {
        "jobId": job_id,
        "kind": kind,
        "status": "queued",
        "progress": 0,
        "modelRevision": model_revision,
        "candidateId": candidate_id,
        "artifactManifest": {"artifactId": f"{job_id}-artifact", "kind": kind, "traceableTo": {"modelRevision": model_revision, "candidateId": candidate_id, "seed": seed}},
    }


def enrichment_report(model: dict[str, Any]) -> dict[str, Any]:
    furnishings = furnish_model(model)
    candidates = candidate_studio(model, inherited_findings=model.get("findings", []) or [])
    package = design_package(model, candidates["bestCandidateId"])
    return {"status": "blocked" if furnishings["status"] == "blocked" or candidates["status"] == "blocked" else "pass", "week15": furnishings, "week16": candidates, "designPackage": package}


# Public names used by the roadmap and by the editor adapter.
parametric_asset_report = furnish_model
generate_candidates = candidate_studio
presentation_pipeline = design_package


def write_reports() -> dict[str, Any]:
    model = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
    report = enrichment_report(model)
    model["parametricAssets"] = {"version": WEEK15_VERSION, "report": str(ASSET_REPORT_PATH.relative_to(ROOT)), "catalog": asset_catalog(), "presentation": report["week15"]}
    model["candidateStudio"] = {"version": WEEK16_VERSION, "report": str(CANDIDATE_REPORT_PATH.relative_to(ROOT)), "bestCandidateId": report["week16"]["bestCandidateId"], "status": report["week16"]["status"], "seeds": report["week16"]["seeds"]}
    model["designPresentation"] = report["designPackage"]
    ASSET_REPORT_PATH.write_text(json.dumps(report["week15"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    CANDIDATE_REPORT_PATH.write_text(json.dumps({"candidateStudio": report["week16"], "designPackage": report["designPackage"]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MANIFEST_PATH.write_text(json.dumps({"manifestVersion": "week1516.enrichment-manifest.v1", "status": report["status"], "reports": {"week15": str(ASSET_REPORT_PATH.relative_to(ROOT)), "week16": str(CANDIDATE_REPORT_PATH.relative_to(ROOT))}, "changelog": str(CHANGELOG_PATH.relative_to(ROOT)), "catalogVersion": WEEK15_VERSION, "candidateVersion": WEEK16_VERSION, "bestCandidateId": report["week16"]["bestCandidateId"]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    CHANGELOG_PATH.write_text(
        """# Week 15–16 enrichment changelog

## Week 15 — Parametric assets and clearance-aware furnishing

- Added a typed catalog covering furniture, fixtures, appliances, sanitaryware,
  seating rows, dais, library tables, counters, vehicles, and industrial
  equipment.
- Added dimensions, rotation rules, wall relationships, service sides,
  occupancy, clearance envelopes, room templates, and typed edit operations.
- One-click placement rejects door swings, routes, stairs, service zones,
  room-boundary violations, and overlapping clearance envelopes.
- Presentation objects remain non-authoritative and retain the canonical model
  revision for audit.

## Week 16 — Candidate studio and presentation pipeline

- Added deterministic candidate seeds and comparison metrics for area,
  adjacency, routes, daylight/ventilation, vertical coordination, furniture
  fit, and visual quality.
- A candidate with a BLOCKER or ERROR cannot win.
- Added moodboards, materials, lighting presets, non-destructive design layers,
  and traceable render, panorama, and presentation-sheet job manifests.
- Technical plan and presentation output carry the same model revision and
  candidate identifier.
""",
        encoding="utf-8",
    )
    CANONICAL_PATH.write_text(json.dumps(model, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "report"), nargs="?", default="validate")
    args = parser.parse_args(argv)
    report = write_reports()
    print(json.dumps(report if args.command == "report" else {"status": report["status"], "bestCandidateId": report["week16"]["bestCandidateId"], "week15Report": str(ASSET_REPORT_PATH.relative_to(ROOT)), "week16Report": str(CANDIDATE_REPORT_PATH.relative_to(ROOT))}, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())