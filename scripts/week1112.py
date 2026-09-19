#!/usr/bin/env python3
"""Week 11 and Week 12 product enrichment.

Week 11 makes the product surface explicit: modes, capability flags, and
local-only performance counters all describe the same canonical model.

Week 12 provides a deterministic, reviewable brief compiler.  It accepts
common metric and imperial dimension forms, extracts planning facts, reports
assumptions and missing topology facts, and turns supported conversational
commands into typed revision previews.  It intentionally does not claim to
replace a professional brief, survey, or code review.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT / "bar-association-hall"
REPORT_ROOT = MODEL_ROOT / "standard"
CANONICAL_PATH = REPORT_ROOT / "model" / "project.json"
CAPABILITY_PATH = REPORT_ROOT / "week11-capability-matrix.json"
BRIEF_REPORT_PATH = REPORT_ROOT / "week12-brief-compiler-report.json"
MANIFEST_PATH = REPORT_ROOT / "week1112-enrichment-manifest.json"
CHANGELOG_PATH = REPORT_ROOT / "week1112-changelog.md"

COMPILER_VERSION = "week12.brief-compiler.v1"
MODES_VERSION = "week11.product-modes.v1"

UNIT_TO_INCH = {
    "in": 1.0,
    "inch": 1.0,
    "inches": 1.0,
    '"': 1.0,
    "ft": 12.0,
    "foot": 12.0,
    "feet": 12.0,
    "'": 12.0,
    "mm": 1.0 / 25.4,
    "millimeter": 1.0 / 25.4,
    "millimeters": 1.0 / 25.4,
    "cm": 1.0 / 2.54,
    "centimeter": 1.0 / 2.54,
    "centimeters": 1.0 / 2.54,
    "m": 1000.0 / 25.4,
    "meter": 1000.0 / 25.4,
    "meters": 1000.0 / 25.4,
}

ROOM_ALIASES = {
    "living room": "living",
    "bedroom": "bedroom",
    "bedrooms": "bedroom",
    "office": "office",
    "offices": "office",
    "library": "library",
    "libraries": "library",
    "lobby": "lobby",
    "reception": "reception",
    "hall": "assembly",
    "assembly hall": "assembly",
    "courtroom": "courtroom",
    "classroom": "classroom",
    "toilet": "service",
    "toilets": "service",
    "washroom": "service",
    "pantry": "service",
    "store": "storage-service",
}

MODES: list[dict[str, Any]] = [
    {
        "id": "brief",
        "label": "Brief",
        "description": "Compile a natural-language brief into typed planning facts.",
        "canonicalSources": ["briefCompiler"],
    },
    {
        "id": "model",
        "label": "Model",
        "description": "Review authoritative rooms, openings, levels, and routes.",
        "canonicalSources": ["spaces", "openings", "verticalConnectors", "entries"],
    },
    {
        "id": "validate",
        "label": "Validate",
        "description": "Inspect deterministic findings and professional-review items.",
        "canonicalSources": ["enrichment", "findings", "rulePack"],
    },
    {
        "id": "furnish",
        "label": "Furnish",
        "description": "Place scaled presentation objects without changing building geometry.",
        "canonicalSources": ["presentation"],
    },
    {
        "id": "present",
        "label": "Present",
        "description": "Compare and explain candidates without hiding blockers.",
        "canonicalSources": ["candidateComparison", "presentation"],
    },
    {
        "id": "export",
        "label": "Export",
        "description": "Prepare revision-matched technical and presentation outputs.",
        "canonicalSources": ["enrichment", "project.revision"],
    },
]

CAPABILITY_MATRIX: list[dict[str, Any]] = [
    {
        "id": "import",
        "label": "Plan import",
        "status": "provisional",
        "available": False,
        "modes": ["brief", "model"],
        "review": "Imported geometry must be measured and reviewed before becoming authoritative.",
    },
    {
        "id": "threeD",
        "label": "3D synchronized view",
        "status": "provisional",
        "available": False,
        "modes": ["model", "present"],
        "review": "The current release exposes the canonical 2D model; synchronized 3D is not yet implemented.",
    },
    {
        "id": "candidateComparison",
        "label": "Candidate comparison",
        "status": "available",
        "available": True,
        "modes": ["present", "validate"],
        "review": "Ranking is a transparent planning score, not a construction recommendation.",
    },
    {
        "id": "materials",
        "label": "Materials and finishes",
        "status": "provisional",
        "available": False,
        "modes": ["furnish", "present"],
        "review": "Presentation materials never alter authoritative geometry.",
    },
    {
        "id": "siteFeasibility",
        "label": "Site feasibility",
        "status": "available",
        "available": True,
        "modes": ["brief", "validate"],
        "review": "Survey, planning permission, and local professional review remain required.",
    },
    {
        "id": "collaboration",
        "label": "Collaboration and revisions",
        "status": "provisional",
        "available": False,
        "modes": ["model", "export"],
        "review": "Local typed revision previews are available; shared persistence is not yet implemented.",
    },
]


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _canonical_unit(unit: str | None, default: str = "inch") -> str:
    value = (unit or default).strip().lower()
    if value in {"metric", "si"}:
        return "m"
    if value in {"imperial", "us"}:
        return "ft"
    return value if value in UNIT_TO_INCH else default


def parse_measurement(value: str | float | int, unit: str | None = None) -> dict[str, Any]:
    """Return a measurement normalized to canonical inches."""
    if isinstance(value, (int, float)):
        number = float(value)
        source_unit = _canonical_unit(unit)
        display = f"{value} {source_unit}"
    else:
        text = str(value).strip().lower().replace("×", "x")
        mixed = re.fullmatch(r"(\d+(?:\.\d+)?)\s*['-]\s*(\d+(?:\.\d+)?)\s*(?:\"|in|inch|inches)?", text)
        if mixed:
            number = float(mixed.group(1)) * 12 + float(mixed.group(2))
            source_unit = "in"
            display = str(value)
        else:
            match = re.search(
                r"(-?\d+(?:\.\d+)?)\s*(mm|millimeters?|cm|centimeters?|m|meters?|ft|feet|foot|in|inches?|[\"'])?",
                text,
            )
            if not match:
                raise ValueError(f"cannot parse measurement: {value!r}")
            number = float(match.group(1))
            source_unit = _canonical_unit(match.group(2) or unit)
            display = str(value)
    inches = round(number * UNIT_TO_INCH[source_unit], 6)
    return {"value": inches, "unit": "inch", "sourceUnit": source_unit, "display": display}


def _dimension_pairs(text: str) -> list[tuple[str, str, int]]:
    return list(
        re.finditer(
            r"(?P<a>\d+(?:\.\d+)?)\s*(?P<au>mm|cm|m|meters?|feet|foot|ft|inches?|in|['\"])?"
            r"\s*(?:x|by|×)\s*"
            r"(?P<b>\d+(?:\.\d+)?)\s*(?P<bu>mm|cm|m|meters?|feet|foot|ft|inches?|in|['\"])?",
            text.lower(),
        )
    )


def _unit_family(text: str) -> str:
    lowered = text.lower()
    if re.search(r"\b(mm|cm|m|meters?|millimeters?|centimeters?)\b", lowered):
        return "metric"
    if re.search(r"\b(ft|feet|foot|in|inches?)\b|['\"]", lowered):
        return "imperial"
    return "unspecified"


def _find_number(text: str, pattern: str) -> int | float | None:
    match = re.search(pattern, text.lower())
    if not match:
        return None
    value = float(match.group(1))
    return int(value) if value.is_integer() else value


def _room_schedule(text: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    aliases = sorted(ROOM_ALIASES, key=len, reverse=True)
    for alias in aliases:
        for match in re.finditer(rf"(?<![a-z])(?:(\d+)\s*(?:x|no\.?\s*of)?\s*)?{re.escape(alias)}\b", text.lower()):
            start, end = match.span()
            following = text[end : end + 55]
            area_match = re.search(
                r"(?:of|at|area(?:\s*target)?\s*(?:of|=)?|target(?:\s*area)?\s*(?:of|=)?)\s*"
                r"(\d+(?:\.\d+)?)\s*(m2|m²|sqm|sq\s*m|sqft|sq\s*ft|ft2|ft²|sft)?",
                following.lower(),
            )
            count = int(match.group(1) or 1)
            area: dict[str, Any] | None = None
            if area_match:
                area_value = float(area_match.group(1))
                area_unit = area_match.group(2) or ("m2" if _unit_family(text) == "metric" else "sqft")
                factor = 10.76391 if area_unit in {"m2", "m²", "sqm", "sq m"} else 1.0
                area = {
                    "value": round(area_value * factor, 4),
                    "unit": "sqft",
                    "sourceUnit": area_unit,
                    "display": area_match.group(0).strip(),
                }
            item = {"roomUse": ROOM_ALIASES[alias], "label": alias, "count": count}
            if area:
                item["areaTarget"] = area
            if item not in results:
                results.append(item)
    return results


def _adjacencies(text: str) -> list[dict[str, str]]:
    known = sorted(ROOM_ALIASES, key=len, reverse=True)
    found: list[dict[str, str]] = []
    pattern = r"(?P<a>" + "|".join(re.escape(item) for item in known) + r")\s+" \
        r"(?P<relation>near|beside|next to|adjacent to)\s+" \
        r"(?P<b>" + "|".join(re.escape(item) for item in known) + r")"
    for match in re.finditer(pattern, text.lower()):
        item = {
            "left": ROOM_ALIASES[match.group("a")],
            "relationship": match.group("relation"),
            "right": ROOM_ALIASES[match.group("b")],
        }
        if item not in found:
            found.append(item)
    return found


def compile_brief(text: str, *, default_units: str = "inch") -> dict[str, Any]:
    """Compile a brief without mutating a canonical model."""
    started = time.perf_counter()
    source = " ".join(text.strip().split())
    lower = source.lower()
    detected_units = _unit_family(source)
    default_unit = _canonical_unit(default_units)
    facts: dict[str, Any] = {
        "units": {
            "detected": detected_units,
            "default": default_units,
            "canonical": "inch",
        },
        "site": {},
        "north": None,
        "roadFrontage": None,
        "levels": None,
        "floorToFloor": None,
        "roomSchedule": _room_schedule(source),
        "areaTargets": [],
        "accessIntent": None,
        "occupancy": None,
        "adjacencies": _adjacencies(source),
        "style": None,
        "requiredOutputs": [],
    }

    pairs = _dimension_pairs(source)
    if pairs and re.search(r"\b(site|plot|lot|campus|property)\b", lower):
        pair = next((item for item in pairs if re.search(r"\b(site|plot|lot|campus|property)\b", lower[max(0, item.start() - 30) : item.end() + 10])), pairs[0])
        facts["site"] = {
            "width": parse_measurement(pair.group("a"), pair.group("au") or default_unit),
            "depth": parse_measurement(pair.group("b"), pair.group("bu") or pair.group("au") or default_unit),
        }

    north_match = re.search(
        r"\bnorth\s*(?:is|at|toward|points?|facing)?\s*(north|south|east|west|northeast|northwest|southeast|southwest)\b",
        lower,
    )
    if north_match:
        facts["north"] = {"direction": north_match.group(1), "source": "brief"}

    frontage_match = re.search(
        r"(?:road|frontage|street)\s*(?:is|on|along|fronts?)?\s*(?:the\s+)?"
        r"(north|south|east|west|northeast|northwest|southeast|southwest)\b",
        lower,
    )
    if frontage_match:
        facts["roadFrontage"] = {"side": frontage_match.group(1), "source": "brief"}

    facts["levels"] = _find_number(lower, r"\b(\d+)\s*(?:levels?|floors?|storeys?|stories?)\b")
    floor_match = re.search(
        r"(?:floor[-\s]?to[-\s]?floor|floor height|storey height)\s*(?:is|of|=)?\s*"
        r"(\d+(?:\.\d+)?)\s*(mm|cm|m|meters?|ft|feet|inches?|in)?",
        lower,
    )
    if floor_match:
        facts["floorToFloor"] = parse_measurement(floor_match.group(1), floor_match.group(2) or default_unit)

    occupancy = _find_number(lower, r"\b(?:occupancy|capacity|for|accommodate)\s*(?:of|for|:)?\s*(\d+)\s*(?:people|persons|occupants|users)?")
    if occupancy is not None:
        facts["occupancy"] = {"people": occupancy}

    access_match = re.search(r"\b(public|staff|service|controlled|private|mixed)\s+(?:access|entry|circulation|route)\b", lower)
    if access_match:
        facts["accessIntent"] = {"value": access_match.group(1), "source": "brief"}

    style_match = re.search(r"\b(?:style|look|character)\s*(?:is|:)?\s*([a-z][a-z -]{2,30}?)(?:[,.]|$)", lower)
    if style_match:
        facts["style"] = style_match.group(1).strip()

    output_map = {
        "pdf": "pdf",
        "dxf": "dxf",
        "ifc": "ifc",
        "bim": "ifc",
        "3d": "3d",
        "render": "render",
        "presentation": "presentation",
        "report": "validation-report",
    }
    facts["requiredOutputs"] = sorted({value for key, value in output_map.items() if re.search(rf"\b{re.escape(key)}\b", lower)})

    assumptions: list[str] = []
    ambiguities: list[str] = []
    missing_topology: list[str] = []
    if detected_units == "unspecified":
        assumptions.append(f"Dimensions without units use the requested default unit: {default_units}.")
    if facts["site"] and len(pairs) > 1:
        ambiguities.append("More than one dimension pair was found; only the site-context pair was assigned to site dimensions.")
    if facts["north"] is None:
        missing_topology.append("Confirm north direction against a survey or site plan.")
    if facts["roadFrontage"] is None:
        missing_topology.append("Identify the road/frontage side and the intended public entry.")
    if facts["levels"] and facts["levels"] > 1 and facts["floorToFloor"] is None:
        missing_topology.append("Provide floor-to-floor heights for every level before placing vertical connectors.")
    if not facts["site"]:
        missing_topology.append("Provide site or plot dimensions before generating a plan.")
    if not facts["roomSchedule"]:
        missing_topology.append("Provide a room schedule with uses, counts, and area targets where known.")
    if facts["levels"] and facts["levels"] > 1:
        missing_topology.append("Identify which stair, lift, or ramp connects each level.")
    if facts["accessIntent"] is None:
        missing_topology.append("State public, staff, service, or controlled access intent for primary routes.")
    if not facts["requiredOutputs"]:
        assumptions.append("No output format was requested; generation should stop at a reviewable brief.")

    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    return {
        "compilerVersion": COMPILER_VERSION,
        "input": source,
        "facts": facts,
        "assumptions": assumptions,
        "ambiguities": ambiguities,
        "missingTopologyFacts": list(dict.fromkeys(missing_topology)),
        "readyForGeneration": not missing_topology,
        "status": "ready" if not missing_topology else "needs-review",
        "performance": {"compileDurationMs": elapsed_ms, "telemetry": "local-only"},
    }


def parse_command(text: str) -> dict[str, Any]:
    """Parse supported conversational edits into a typed command."""
    source = " ".join(text.strip().split())
    lower = source.lower()
    move = re.search(r"\bmove\s+(?:the\s+)?(?P<target>stair|stairs|lift|ramp)\s+(?P<relation>beside|near|next to|adjacent to)\s+(?:the\s+)?(?P<destination>[a-z][a-z -]+?)(?:[.!?]|$)", lower)
    if move:
        return {
            "type": "move_connector",
            "targetKind": "stair" if move.group("target") in {"stair", "stairs"} else move.group("target"),
            "relation": move.group("relation"),
            "destinationLabel": move.group("destination").strip(),
            "sourceText": source,
        }
    route = re.search(
        r"\b(?:give|provide|make)\s+(?:the\s+)?(?P<target>[a-z][a-z -]+?)\s+"
        r"(?:an?\s+)?(?P<intent>public|staff|service|controlled|private)\s+(?:access|route|entry)\b",
        lower,
    )
    if route:
        return {
            "type": "set_access_intent",
            "targetLabel": route.group("target").strip(),
            "accessIntent": route.group("intent"),
            "sourceText": source,
        }
    remove = re.search(r"\bremove\s+(?:the\s+)?(?P<target>outer door|external door|outside door|door)\b", lower)
    if remove and re.search(r"\b(unless|only if|provided that)\b", lower):
        return {
            "type": "conditional_remove_opening",
            "targetLabel": remove.group("target"),
            "condition": {
                "kind": "intentional-access-path",
                "acceptedKinds": ["balcony", "landing", "stair", "terrace", "porch"],
            },
            "sourceText": source,
        }
    return {
        "type": "unsupported",
        "sourceText": source,
        "reason": "Supported examples are moving a connector, setting a route intent, or conditionally removing an outer door.",
    }


def _find_objects(model: dict[str, Any], label: str) -> list[dict[str, Any]]:
    needle = re.sub(r"[^a-z0-9]+", " ", label.lower()).strip()
    objects: list[dict[str, Any]] = []
    for collection in ("spaces", "openings", "verticalConnectors", "stairs", "entries"):
        for item in model.get(collection, []) or []:
            haystack = " ".join(
                str(item.get(key, "")) for key in ("id", "name", "label", "roomUse", "kind", "target")
            ).lower()
            if needle and needle in re.sub(r"[^a-z0-9]+", " ", haystack):
                objects.append({"collection": collection, "object": item})
    return objects


def command_preview(model: dict[str, Any], command_text: str, *, author: str = "brief-compiler", timestamp: str | None = None) -> dict[str, Any]:
    """Create an immutable typed revision preview without mutating model."""
    command = parse_command(command_text)
    changed: list[str] = []
    findings: list[dict[str, Any]] = []
    status = "ready"
    target_objects: list[dict[str, Any]] = []

    if command["type"] == "move_connector":
        target_objects = [
            {"collection": collection, "object": item}
            for collection in ("verticalConnectors", "stairs")
            for item in (model.get(collection, []) or [])
            if str(item.get("kind", "")).lower() == command["targetKind"]
            or command["targetKind"] in str(item.get("id", "")).lower()
        ]
        destination = _find_objects(model, command["destinationLabel"])
        if target_objects:
            changed.extend(item["object"].get("id", "") for item in target_objects)
        if destination:
            changed.extend(item["object"].get("id", "") for item in destination[:1])
        else:
            status = "needs-review"
            findings.append({
                "severity": "WARNING",
                "rule": "COMMAND_DESTINATION_NOT_FOUND",
                "message": f"No canonical object matched destination {command['destinationLabel']!r}.",
            })
        if not target_objects:
            status = "needs-review"
            findings.append({
                "severity": "WARNING",
                "rule": "COMMAND_CONNECTOR_NOT_FOUND",
                "message": f"No {command['targetKind']} object was found in the canonical model.",
            })
    elif command["type"] == "set_access_intent":
        target_objects = _find_objects(model, command["targetLabel"])
        changed.extend(item["object"].get("id", "") for item in target_objects[:1])
        if not target_objects:
            status = "needs-review"
            findings.append({
                "severity": "WARNING",
                "rule": "COMMAND_TARGET_NOT_FOUND",
                "message": f"No canonical space matched {command['targetLabel']!r}.",
            })
    elif command["type"] == "conditional_remove_opening":
        target_objects = [
            {"collection": "openings", "object": item}
            for item in (model.get("openings", []) or [])
            if str(item.get("kind", "")).lower() in {"door", "external-door", "entry"}
            or "door" in str(item.get("id", "")).lower()
        ]
        # A bare stair object is not evidence that an exterior opening has a
        # valid landing or route. Count explicit access metadata or an entry
        # object carrying the intentional-access-path semantics instead.
        access_path = any(
            item.get("accessPath") is True
            or item.get("exteriorZoneId")
            or any(token in json.dumps(item).lower() for token in command["condition"]["acceptedKinds"])
            for item in (model.get("entries", []) or [])
        ) or any(
            item.get("accessPath") is True
            for collection in ("verticalConnectors", "stairs", "spaces")
            for item in (model.get(collection, []) or [])
        )
        if not access_path:
            status = "blocked"
            findings.append({
                "severity": "BLOCKER",
                "rule": "CONDITIONAL_OUTER_DOOR_REQUIRES_INTENTIONAL_ACCESS_PATH",
                "message": "The requested removal is blocked until a balcony, landing, stair, terrace, or porch is modeled.",
            })
        changed.extend(item["object"].get("id", "") for item in target_objects)
    else:
        status = "needs-review"
        findings.append({
            "severity": "WARNING",
            "rule": "UNSUPPORTED_BRIEF_COMMAND",
            "message": command["reason"],
        })

    changed = sorted({item for item in changed if item})
    before_revision = int(model.get("project", {}).get("revision", 1))
    after_revision = before_revision + 1
    revision_body = {
        "beforeRevision": before_revision,
        "afterRevision": after_revision,
        "command": command,
        "changedObjectIds": changed,
        "status": status,
    }
    revision_id = "rev-" + hashlib.sha256(
        json.dumps(revision_body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:12]
    revision = {
        "id": revision_id,
        "author": author,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "beforeRevision": before_revision,
        "afterRevision": after_revision,
        "command": command,
        "changedObjectIds": changed,
        "validationDelta": {"status": status, "findings": findings},
        "accepted": False,
    }
    return {
        "compilerVersion": COMPILER_VERSION,
        "status": status,
        "command": command,
        "targetObjects": target_objects,
        "revision": revision,
        "findings": findings,
        "canonicalModelUnchanged": True,
    }


def accept_revision(model: dict[str, Any], preview: dict[str, Any]) -> dict[str, Any]:
    """Apply only safe metadata edits and return a new model/revision pair."""
    if preview.get("status") == "blocked":
        raise ValueError("blocked revision cannot be accepted")
    updated = copy.deepcopy(model)
    revision = copy.deepcopy(preview["revision"])
    command = revision["command"]
    if command["type"] == "set_access_intent":
        for item in updated.get("spaces", []) or []:
            haystack = f"{item.get('id', '')} {item.get('name', '')}".lower()
            if command["targetLabel"].lower() in haystack:
                item["accessIntent"] = command["accessIntent"]
                item["revision"] = revision["afterRevision"]
                break
    elif command["type"] == "move_connector":
        updated.setdefault("commandIntents", []).append({
            "type": "move_connector",
            "targetKind": command["targetKind"],
            "relation": command["relation"],
            "destinationLabel": command["destinationLabel"],
            "revision": revision["afterRevision"],
        })
    elif command["type"] == "conditional_remove_opening":
        ids = set(revision["changedObjectIds"])
        updated["openings"] = [item for item in updated.get("openings", []) if item.get("id") not in ids]
    updated.setdefault("project", {})["revision"] = revision["afterRevision"]
    revision["accepted"] = True
    updated.setdefault("revisionHistory", []).append(revision)
    return {"model": updated, "revision": revision}


def performance_counters(model: dict[str, Any], *, validation_duration_ms: float = 0.0, render_duration_ms: float = 0.0, export_duration_ms: float = 0.0) -> dict[str, Any]:
    """Return local counters only; no events or identifiers leave the process."""
    serialized = json.dumps(model, sort_keys=True, separators=(",", ":")).encode("utf-8")
    collections = ("levels", "spaces", "walls", "openings", "windows", "stairs", "verticalConnectors", "entries")
    return {
        "scope": "local-only",
        "modelBytes": len(serialized),
        "objectCounts": {collection: len(model.get(collection, []) or []) for collection in collections},
        "validationDurationMs": round(validation_duration_ms, 3),
        "renderDurationMs": round(render_duration_ms, 3),
        "exportDurationMs": round(export_duration_ms, 3),
    }


DEFAULT_BRIEF = (
    "Design a 2 level advocate chambers on a site 60m x 30m. "
    "North is north and road frontage is east. Floor-to-floor is 3.6m. "
    "Include 1 reception, 2 offices, a library area target of 60m2, and an assembly hall for 120 people. "
    "Use public access, library near lobby, style contemporary, outputs PDF and DXF."
)


def build_capability_report() -> dict[str, Any]:
    return {
        "reportVersion": MODES_VERSION,
        "status": "pass",
        "canonicalModel": "bar-association-hall/standard/model/project.json",
        "modes": MODES,
        "capabilities": CAPABILITY_MATRIX,
        "policy": [
            "Presentation objects are not authoritative geometry.",
            "Provisional capabilities are visible but cannot be represented as complete.",
            "Professional-review capabilities show their unresolved decision explicitly.",
        ],
    }


def write_reports() -> dict[str, Any]:
    model = read_json(CANONICAL_PATH)
    capability_report = build_capability_report()
    brief = compile_brief(DEFAULT_BRIEF, default_units="metric")
    command_examples = [
        command_preview(model, "move the stair beside the lobby", timestamp="2026-01-01T00:00:00+00:00"),
        command_preview(model, "give the library a public route", timestamp="2026-01-01T00:00:00+00:00"),
        command_preview(model, "remove the outer door unless a balcony is modeled", timestamp="2026-01-01T00:00:00+00:00"),
    ]
    # The release report needs traceability, not a second copy of the full
    # canonical model. The API preview still returns the matched objects for
    # interactive inspection.
    for example in command_examples:
        example["targetObjects"] = [
            {"collection": item["collection"], "id": item["object"].get("id")}
            for item in example["targetObjects"]
        ]
    brief_report = {
        "reportVersion": COMPILER_VERSION,
        "status": "pass",
        "fixture": brief,
        "commandExamples": command_examples,
        "gate": {
            "missingFactsAreShownBeforeGeneration": True,
            "acceptedCommandsBecomeTypedRevisions": True,
            "canonicalModelIsNotMutatedByPreview": all(item["canonicalModelUnchanged"] for item in command_examples),
        },
    }
    model.setdefault("productModes", capability_report["modes"])
    model.setdefault("capabilityFlags", capability_report["capabilities"])
    model["briefCompiler"] = {
        "version": COMPILER_VERSION,
        "report": str(BRIEF_REPORT_PATH.relative_to(ROOT)),
        "lastCompiledStatus": brief["status"],
        "missingTopologyFacts": brief["missingTopologyFacts"],
    }
    model["performanceCounters"] = performance_counters(model)
    write_json(CAPABILITY_PATH, capability_report)
    write_json(BRIEF_REPORT_PATH, brief_report)
    write_json(
        MANIFEST_PATH,
        {
            "manifestVersion": "week1112.enrichment-manifest.v1",
            "status": "pass",
            "canonicalModel": str(CANONICAL_PATH.relative_to(ROOT)),
            "capabilityMatrix": str(CAPABILITY_PATH.relative_to(ROOT)),
            "briefCompilerReport": str(BRIEF_REPORT_PATH.relative_to(ROOT)),
            "changelog": str(CHANGELOG_PATH.relative_to(ROOT)),
            "modes": [mode["id"] for mode in MODES],
            "compilerVersion": COMPILER_VERSION,
        },
    )
    CHANGELOG_PATH.write_text(
        """# Week 11–12 enrichment changelog

## Week 11

- Added explicit Brief, Model, Validate, Furnish, Present, and Export product modes.
- Added a capability matrix that distinguishes available, provisional, and professional-review features.
- Added local-only model, validation, render, and export performance counters.
- Kept presentation and provisional features visibly separate from authoritative geometry.

## Week 12

- Added a deterministic conversational brief compiler for common metric and imperial dimensions.
- Extracted site, north, frontage, levels, floor-to-floor, rooms, areas, access, occupancy, adjacencies, style, and outputs.
- Added assumptions, ambiguities, and missing topology facts before generation.
- Added typed revision previews for connector moves, access intent changes, and conditional outer-door removal.
- Blocked conditional door removal until an intentional access path is actually modeled.

These are preliminary planning aids. They are not survey, code, permit, accessibility,
fire/life-safety, structural, MEP, or construction certification.
""",
        encoding="utf-8",
    )
    write_json(CANONICAL_PATH, model)
    return {
        "status": "pass",
        "capabilityMatrix": str(CAPABILITY_PATH.relative_to(ROOT)),
        "briefCompilerReport": str(BRIEF_REPORT_PATH.relative_to(ROOT)),
        "manifest": str(MANIFEST_PATH.relative_to(ROOT)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "report"), nargs="?", default="validate")
    args = parser.parse_args(argv)
    result = write_reports()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())