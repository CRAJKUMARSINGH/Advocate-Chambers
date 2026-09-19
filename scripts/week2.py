#!/usr/bin/env python3
"""Week 2 canonical-model migration and schema validation.

The Week 1 source files remain the human-readable legacy input.  This module
is the only place that maps that input into the canonical Week 2 model.  The
canonical model is validated before any drawing code receives a plan, and the
inverse adapter makes the migration round-trip testable.

This module deliberately uses only the Python standard library so it can run
in a clean checkout before optional CAD/PDF dependencies are installed.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT / "bar-association-hall"
SOURCE_ROOT = MODEL_ROOT / "standard" / "source"
CANONICAL_PATH = MODEL_ROOT / "standard" / "model" / "project.json"
SCHEMA_PATH = ROOT / "packages" / "schema" / "project-v2.schema.json"

SCHEMA_VERSION = "advocate-chambers.project.v2"
MIGRATION_VERSION = "week2.legacy-to-v2"
SOURCE_PLAN_PATH = "bar-association-hall/standard/source/preliminary_plans.json"
SOURCE_SITE_PATH = "bar-association-hall/standard/source/site_plan.json"

STATUS_VALUES = {"draft", "schematic", "validated", "warning", "rejected"}
OBJECT_STATUS_VALUES = {"draft", "validated", "warning", "rejected"}
SOURCE_VALUES = {"user", "generator", "import", "survey", "legacy"}
ACCESS_INTENTS = {
    "public",
    "staff",
    "service",
    "controlled",
    "vertical",
    "entry",
    "daylight-ventilation",
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _path(source_path: str, collection: str, index: int) -> str:
    return f"{source_path}#/{collection}/{index}"


def _provenance(
    source_path: str,
    collection: str,
    index: int,
    source_id: str,
    legacy: dict[str, Any],
) -> dict[str, Any]:
    return {
        "sourcePath": _path(source_path, collection, index),
        "sourceId": source_id,
        "migration": MIGRATION_VERSION,
        "legacyKeys": sorted(legacy.keys()),
    }


def _base(
    *,
    item_id: str,
    kind: str,
    level_id: str,
    source_path: str,
    collection: str,
    index: int,
    legacy: dict[str, Any],
    status: str = "warning",
) -> dict[str, Any]:
    return {
        "id": item_id,
        "kind": kind,
        "levelId": level_id,
        "source": "legacy",
        "status": status,
        "revision": 1,
        "provenance": _provenance(
            source_path, collection, index, item_id, legacy
        ),
        "legacy": copy.deepcopy(legacy),
    }


def _room_use(space: dict[str, Any]) -> str:
    name = str(space.get("name", "")).lower()
    finish = str(space.get("finish", "")).lower()
    if space.get("stairId") or finish == "circulation":
        return "vertical-circulation"
    if "toilet" in name or "pantry" in name or finish == "service":
        return "service"
    if "dais" in name or "speaker" in name:
        return "stage"
    if "hall" in name or "assembly" in name:
        return "assembly"
    if "library" in name or "book" in name:
        return "library"
    if "discussion" in name:
        return "discussion"
    if "computer" in name or "internet" in name:
        return "computer"
    if "store" in name or "electrical" in name:
        return "storage-service"
    if "reception" in name:
        return "reception"
    if "president" in name or "secretary" in name or "librarian" in name:
        return "office"
    return finish or "unclassified"


def _access_intent_for_space(space: dict[str, Any]) -> str:
    room_use = _room_use(space)
    if room_use == "vertical-circulation":
        return "vertical"
    if room_use in {"service", "storage-service"}:
        return "service"
    if room_use in {"office"}:
        return "staff"
    if room_use == "stage":
        return "controlled"
    return "public"


def _status_for_legacy(value: Any, default: str = "warning") -> str:
    value = str(value or "").lower()
    if value in {"validated", "confirmed", "coordinated"}:
        return "validated"
    if value in {"rejected"}:
        return "rejected"
    return default


def _level(
    level: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    level_id = str(level["id"])
    return {
        "id": level_id,
        "name": level["name"],
        "elevation": level["elevation"],
        "floorToFloor": level["floorToFloor"],
        "source": "legacy",
        "status": "warning",
        "revision": 1,
        "provenance": _provenance(
            SOURCE_SITE_PATH, "levels", index, level_id, level
        ),
        "legacy": copy.deepcopy(level),
    }


def migrate_legacy(
    site: dict[str, Any],
    plans: dict[str, Any],
) -> dict[str, Any]:
    """Build the canonical v2 model from the existing Week 1 source files."""

    project_legacy = site.get("project", {})
    project_id = str(plans.get("projectId", "advocate-chambers"))
    project = {
        "id": f"proj-{project_id}",
        "name": project_legacy.get("name", project_id),
        "location": project_legacy.get("location", ""),
        "status": project_legacy.get("status", "schematic"),
        "revision": len(site.get("revisions", [])) or 1,
        "source": "legacy",
        "legacy": copy.deepcopy(project_legacy),
    }
    if project["status"] not in STATUS_VALUES:
        project["status"] = "schematic"

    canonical_site_legacy = site.get("site", {})
    canonical_site = {
        "id": "SITE-" + re.sub(r"[^A-Z0-9]+", "-", project_id.upper()).strip("-"),
        "kind": "site",
        "levelId": "SITE",
        "geometry": {
            "plotVertices": copy.deepcopy(canonical_site_legacy.get("plot", [])),
            "setbacks": copy.deepcopy(canonical_site_legacy.get("setbacks", {})),
            "north": canonical_site_legacy.get("north", "up"),
        },
        "source": "legacy",
        "status": "warning",
        "revision": 1,
        "provenance": _provenance(
            SOURCE_SITE_PATH, "site", 0, "SITE", canonical_site_legacy
        ),
        "legacy": copy.deepcopy(canonical_site_legacy),
    }

    levels = [
        _level(level, index)
        for index, level in enumerate(site.get("levels", []))
    ]
    level_ids = {level["id"] for level in levels}
    spaces: list[dict[str, Any]] = []
    circulation_zones: list[dict[str, Any]] = []
    for index, legacy in enumerate(plans.get("spaces", [])):
        item_id = str(legacy["id"])
        level_id = str(legacy["level"])
        space = _base(
            item_id=item_id,
            kind="space",
            level_id=level_id,
            source_path=SOURCE_PLAN_PATH,
            collection="spaces",
            index=index,
            legacy=legacy,
        )
        space.update(
            {
                "name": legacy["name"],
                "roomUse": _room_use(legacy),
                "accessIntent": _access_intent_for_space(legacy),
                "geometry": {"rect": copy.deepcopy(legacy["rect"])},
            }
        )
        spaces.append(space)

        if legacy.get("finish") == "circulation" or legacy.get("stairId"):
            zone_id = f"CIRC-{item_id}"
            zone = _base(
                item_id=zone_id,
                kind="circulation-zone",
                level_id=level_id,
                source_path=SOURCE_PLAN_PATH,
                collection="spaces",
                index=index,
                legacy=legacy,
            )
            zone.update(
                {
                    "zoneType": "vertical-approach",
                    "spaceId": item_id,
                    "accessIntent": "vertical",
                    "geometry": {"rect": copy.deepcopy(legacy["rect"])},
                }
            )
            circulation_zones.append(zone)

    entry_by_opening = {
        entry["openingId"]: entry for entry in plans.get("entries", [])
    }
    openings: list[dict[str, Any]] = []
    for index, legacy in enumerate(plans.get("openings", [])):
        item_id = str(legacy["id"])
        entry = entry_by_opening.get(item_id)
        opening = _base(
            item_id=item_id,
            kind="door",
            level_id=str(legacy["level"]),
            source_path=SOURCE_PLAN_PATH,
            collection="openings",
            index=index,
            legacy=legacy,
        )
        opening.update(
            {
                "tag": legacy["tag"],
                "hostSpace": legacy["hostSpace"],
                "wall": legacy["wall"],
                "accessIntent": "entry" if entry else "room",
                "geometry": {
                    "offset": legacy["offset"],
                    "width": legacy["width"],
                    "swing": legacy.get("swing", "in"),
                },
            }
        )
        openings.append(opening)

    windows: list[dict[str, Any]] = []
    for index, legacy in enumerate(plans.get("windows", [])):
        item_id = str(legacy["id"])
        window = _base(
            item_id=item_id,
            kind="window",
            level_id=str(legacy["level"]),
            source_path=SOURCE_PLAN_PATH,
            collection="windows",
            index=index,
            legacy=legacy,
        )
        window.update(
            {
                "tag": legacy["tag"],
                "hostSpace": legacy["hostSpace"],
                "wall": legacy["wall"],
                "accessIntent": "daylight-ventilation",
                "geometry": {
                    "offset": legacy["offset"],
                    "width": legacy["width"],
                },
            }
        )
        windows.append(window)

    exterior_zones: list[dict[str, Any]] = []
    canonical_entries: list[dict[str, Any]] = []
    for index, legacy in enumerate(plans.get("entries", [])):
        item_id = str(legacy["id"])
        porch = legacy.get("porch")
        exterior_zone_id = None
        if porch:
            exterior_zone_id = f"EXT-{item_id}"
            zone = _base(
                item_id=exterior_zone_id,
                kind="exterior-zone",
                level_id=str(legacy["level"]),
                source_path=SOURCE_PLAN_PATH,
                collection="entries",
                index=index,
                legacy=legacy,
                status=_status_for_legacy(legacy.get("status")),
            )
            zone.update(
                {
                    "zoneType": "porch",
                    "accessIntent": "entry",
                    "geometry": {
                        "width": porch.get("width"),
                        "depth": porch.get("depth"),
                        "label": porch.get("label"),
                    },
                }
            )
            exterior_zones.append(zone)

        entry = _base(
            item_id=item_id,
            kind="entry",
            level_id=str(legacy["level"]),
            source_path=SOURCE_PLAN_PATH,
            collection="entries",
            index=index,
            legacy=legacy,
            status=_status_for_legacy(legacy.get("status")),
        )
        entry.update(
            {
                "entryKind": legacy["kind"],
                "label": legacy["label"],
                "openingId": legacy["openingId"],
                "hostSpace": legacy["hostSpace"],
                "wall": legacy["wall"],
                "accessIntent": "entry",
                "exteriorZoneId": exterior_zone_id,
            }
        )
        canonical_entries.append(entry)

    stairs: list[dict[str, Any]] = []
    vertical_connectors: list[dict[str, Any]] = []
    for index, legacy in enumerate(plans.get("stairs", [])):
        item_id = str(legacy["id"])
        connector_id = f"VC-{item_id}"
        stair = _base(
            item_id=item_id,
            kind="stair",
            level_id=str(legacy["levelFrom"]),
            source_path=SOURCE_PLAN_PATH,
            collection="stairs",
            index=index,
            legacy=legacy,
            status=_status_for_legacy(legacy.get("status")),
        )
        stair.update(
            {
                "levelFrom": legacy["levelFrom"],
                "levelTo": legacy["levelTo"],
                "verticalConnectorId": connector_id,
                "configuration": legacy.get("kind", "dog-leg"),
                "turnDegrees": 180 if legacy.get("turn") == "180-deg" else 0,
                "geometry": {
                    key: copy.deepcopy(legacy[key])
                    for key in (
                        "width",
                        "flightCount",
                        "riserCountTotal",
                        "riserCountPerFlight",
                        "floorToFloor",
                        "riser",
                        "tread",
                        "landingDepth",
                        "landingPosition",
                        "northVoid",
                        "direction",
                        "handrails",
                    )
                    if key in legacy
                },
            }
        )
        stairs.append(stair)

        from_space = next(
            (
                space["id"]
                for space in spaces
                if space["levelId"] == legacy["levelFrom"]
                and space["legacy"].get("stairId") == item_id
            ),
            None,
        )
        to_space = next(
            (
                space["id"]
                for space in spaces
                if space["levelId"] == legacy["levelTo"]
                and space["legacy"].get("stairId") == item_id
            ),
            None,
        )
        connector = _base(
            item_id=connector_id,
            kind="vertical-connector",
            level_id=str(legacy["levelFrom"]),
            source_path=SOURCE_PLAN_PATH,
            collection="stairs",
            index=index,
            legacy=legacy,
            status=_status_for_legacy(legacy.get("status")),
        )
        connector.update(
            {
                "fromLevelId": legacy["levelFrom"],
                "toLevelId": legacy["levelTo"],
                "stairId": item_id,
                "departureSpaceId": from_space,
                "arrivalSpaceId": to_space,
                "accessIntent": "vertical",
            }
        )
        vertical_connectors.append(connector)

    revisions = []
    for revision in site.get("revisions", []):
        revisions.append(
            {
                "id": revision["id"],
                "date": revision["date"],
                "author": revision.get("author", "legacy-source"),
                "summary": revision["description"],
                "source": "legacy",
                "legacy": copy.deepcopy(revision),
            }
        )

    legacy_metadata = {
        "plans": {
            key: copy.deepcopy(plans[key])
            for key in ("projectId", "units", "wallThickness")
            if key in plans
        },
        "sourcePaths": {
            "site": SOURCE_SITE_PATH,
            "plans": SOURCE_PLAN_PATH,
        },
    }
    return {
        "schemaVersion": SCHEMA_VERSION,
        "project": project,
        "units": plans.get("units", "inch"),
        "wallThickness": plans.get("wallThickness"),
        "site": canonical_site,
        "levels": levels,
        "spaces": spaces,
        "openings": openings,
        "windows": windows,
        "entries": canonical_entries,
        "circulationZones": circulation_zones,
        "exteriorZones": exterior_zones,
        "verticalConnectors": vertical_connectors,
        "stairs": stairs,
        "assumptions": copy.deepcopy(canonical_site_legacy.get("assumptions", [])),
        "notes": copy.deepcopy(plans.get("notes", [])),
        "revisions": revisions,
        "legacyMetadata": legacy_metadata,
    }


def _legacy_item(item: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(item.get("legacy", {}))


def canonical_to_legacy(
    model: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Convert an unchanged canonical model back to the two Week 1 sources."""

    metadata = model.get("legacyMetadata", {}).get("plans", {})
    plans: dict[str, Any] = copy.deepcopy(metadata)
    plans.setdefault("projectId", model["project"]["id"].removeprefix("proj-"))
    plans.setdefault("units", model["units"])
    plans.setdefault("wallThickness", model["wallThickness"])

    def map_space(item: dict[str, Any]) -> dict[str, Any]:
        value = _legacy_item(item)
        value.update(
            {
                "id": item["id"],
                "level": item["levelId"],
                "name": item["name"],
                "rect": copy.deepcopy(item["geometry"]["rect"]),
            }
        )
        return value

    def map_opening(item: dict[str, Any]) -> dict[str, Any]:
        value = _legacy_item(item)
        value.update(
            {
                "id": item["id"],
                "level": item["levelId"],
                "tag": item["tag"],
                "hostSpace": item["hostSpace"],
                "wall": item["wall"],
                "offset": item["geometry"]["offset"],
                "width": item["geometry"]["width"],
            }
        )
        if item["geometry"].get("swing") is not None:
            value["swing"] = item["geometry"]["swing"]
        return value

    def map_window(item: dict[str, Any]) -> dict[str, Any]:
        value = _legacy_item(item)
        value.update(
            {
                "id": item["id"],
                "level": item["levelId"],
                "tag": item["tag"],
                "hostSpace": item["hostSpace"],
                "wall": item["wall"],
                "offset": item["geometry"]["offset"],
                "width": item["geometry"]["width"],
            }
        )
        return value

    def map_entry(item: dict[str, Any]) -> dict[str, Any]:
        value = _legacy_item(item)
        value.update(
            {
                "id": item["id"],
                "level": item["levelId"],
                "kind": item["entryKind"],
                "label": item["label"],
                "openingId": item["openingId"],
                "hostSpace": item["hostSpace"],
                "wall": item["wall"],
            }
        )
        return value

    def map_stair(item: dict[str, Any]) -> dict[str, Any]:
        value = _legacy_item(item)
        value.update(
            {
                "id": item["id"],
                "kind": item["configuration"],
                "levelFrom": item["levelFrom"],
                "levelTo": item["levelTo"],
            }
        )
        value.update(copy.deepcopy(item["geometry"]))
        return value

    plans["spaces"] = [map_space(item) for item in model.get("spaces", [])]
    plans["openings"] = [
        map_opening(item) for item in model.get("openings", [])
    ]
    plans["windows"] = [
        map_window(item) for item in model.get("windows", [])
    ]
    plans["entries"] = [
        map_entry(item) for item in model.get("entries", [])
    ]
    plans["stairs"] = [
        map_stair(item) for item in model.get("stairs", [])
    ]
    plans["notes"] = copy.deepcopy(model.get("notes", []))

    site_legacy = copy.deepcopy(model["site"].get("legacy", {}))
    project_legacy = copy.deepcopy(model["project"].get("legacy", {}))
    site = {
        "project": project_legacy,
        "units": model["units"],
        "site": site_legacy,
        "levels": [
            copy.deepcopy(level.get("legacy", {
                "id": level["id"],
                "name": level["name"],
                "elevation": level["elevation"],
                "floorToFloor": level["floorToFloor"],
            }))
            for level in model.get("levels", [])
        ],
        "revisions": [
            copy.deepcopy(revision.get("legacy", {
                "id": revision["id"],
                "date": revision["date"],
                "description": revision["summary"],
            }))
            for revision in model.get("revisions", [])
        ],
    }
    return site, plans


def migrate_from_files(
    site_path: Path = SOURCE_ROOT / "site_plan.json",
    plans_path: Path = SOURCE_ROOT / "preliminary_plans.json",
) -> dict[str, Any]:
    return migrate_legacy(read_json(site_path), read_json(plans_path))


def load_canonical_model(
    path: Path = CANONICAL_PATH,
) -> dict[str, Any]:
    """Load and validate the model used by all geometry entry points."""

    model = read_json(path) if path.exists() else migrate_from_files()
    errors = validate_canonical(model)
    if errors:
        raise ValueError(
            "Week 2 canonical model validation failed:\n"
            + "\n".join(f"- {error}" for error in errors)
        )
    return model


def _require(
    errors: list[str],
    value: Any,
    path: str,
    expected: str,
) -> None:
    if value is None:
        errors.append(f"{path}: missing required {expected}")


def _validate_base(
    errors: list[str],
    item: dict[str, Any],
    path: str,
    expected_kind: str,
) -> None:
    if not isinstance(item, dict):
        errors.append(f"{path}: expected object")
        return
    for key in (
        "id",
        "kind",
        "levelId",
        "source",
        "status",
        "revision",
        "provenance",
    ):
        _require(errors, item.get(key), f"{path}.{key}", "value")
    if item.get("kind") != expected_kind:
        errors.append(f"{path}.kind: expected {expected_kind!r}")
    if item.get("source") not in SOURCE_VALUES:
        errors.append(f"{path}.source: unsupported source")
    if item.get("status") not in OBJECT_STATUS_VALUES:
        errors.append(f"{path}.status: unsupported status")
    if not isinstance(item.get("revision"), int) or item.get("revision", 0) < 1:
        errors.append(f"{path}.revision: expected positive integer")
    provenance = item.get("provenance")
    if not isinstance(provenance, dict):
        errors.append(f"{path}.provenance: expected object")
    else:
        for key in ("sourcePath", "sourceId", "migration", "legacyKeys"):
            _require(errors, provenance.get(key), f"{path}.provenance.{key}", "value")


def _validate_rect(errors: list[str], value: Any, path: str) -> None:
    if (
        not isinstance(value, list)
        or len(value) != 4
        or not all(isinstance(number, (int, float)) for number in value)
    ):
        errors.append(f"{path}: expected [x0, y0, x1, y1] numbers")
        return
    if value[2] <= value[0] or value[3] <= value[1]:
        errors.append(f"{path}: rectangle must have positive width and height")


def validate_canonical(model: dict[str, Any]) -> list[str]:
    """Return deterministic validation errors for the v2 canonical model."""

    errors: list[str] = []
    if not isinstance(model, dict):
        return ["$: expected object"]
    required = (
        "schemaVersion",
        "project",
        "units",
        "wallThickness",
        "site",
        "levels",
        "spaces",
        "openings",
        "windows",
        "entries",
        "circulationZones",
        "exteriorZones",
        "verticalConnectors",
        "stairs",
        "assumptions",
        "notes",
        "revisions",
    )
    for key in required:
        _require(errors, model.get(key), f"$.{key}", "value")
    if model.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"$.schemaVersion: expected {SCHEMA_VERSION!r}")
    if model.get("units") != "inch":
        errors.append("$.units: expected 'inch'")
    if not isinstance(model.get("wallThickness"), (int, float)) or model.get("wallThickness", 0) <= 0:
        errors.append("$.wallThickness: expected positive number")

    project = model.get("project")
    if not isinstance(project, dict):
        errors.append("$.project: expected object")
    else:
        for key in ("id", "name", "location", "status", "revision", "source", "legacy"):
            _require(errors, project.get(key), f"$.project.{key}", "value")
        if not re.fullmatch(r"proj-[a-z0-9-]+", str(project.get("id", ""))):
            errors.append("$.project.id: expected stable proj-... identifier")
        if project.get("status") not in STATUS_VALUES:
            errors.append("$.project.status: unsupported status")

    levels = model.get("levels")
    level_ids: set[str] = set()
    if not isinstance(levels, list) or not levels:
        errors.append("$.levels: expected a non-empty array")
        levels = []
    for index, level in enumerate(levels):
        path = f"$.levels[{index}]"
        if not isinstance(level, dict):
            errors.append(f"{path}: expected object")
            continue
        level_id = level.get("id")
        if level_id in level_ids:
            errors.append(f"{path}.id: duplicate level id {level_id!r}")
        level_ids.add(str(level_id))
        for key in ("id", "name", "elevation", "floorToFloor", "source", "status", "revision", "provenance", "legacy"):
            _require(errors, level.get(key), f"{path}.{key}", "value")
        if not isinstance(level.get("floorToFloor"), (int, float)) or level.get("floorToFloor", 0) <= 0:
            errors.append(f"{path}.floorToFloor: expected positive number")

    site = model.get("site")
    if not isinstance(site, dict):
        errors.append("$.site: expected object")
    else:
        _validate_base(errors, site, "$.site", "site")
        geometry = site.get("geometry", {})
        if not isinstance(geometry, dict):
            errors.append("$.site.geometry: expected object")
        elif len(geometry.get("plotVertices", [])) < 3:
            errors.append("$.site.geometry.plotVertices: expected at least 3 vertices")

    collections: tuple[tuple[str, str], ...] = (
        ("spaces", "space"),
        ("openings", "door"),
        ("windows", "window"),
        ("entries", "entry"),
        ("circulationZones", "circulation-zone"),
        ("exteriorZones", "exterior-zone"),
        ("verticalConnectors", "vertical-connector"),
        ("stairs", "stair"),
    )
    all_ids: dict[str, str] = {}
    collection_values: dict[str, list[dict[str, Any]]] = {}
    for collection, kind in collections:
        values = model.get(collection)
        collection_values[collection] = values if isinstance(values, list) else []
        if not isinstance(values, list):
            errors.append(f"$.{collection}: expected array")
            continue
        for index, item in enumerate(values):
            path = f"$.{collection}[{index}]"
            _validate_base(errors, item, path, kind)
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id"))
            if item_id in all_ids:
                errors.append(
                    f"{path}.id: duplicate stable id {item_id!r}; "
                    f"already used at {all_ids[item_id]}"
                )
            all_ids[item_id] = path
            if item.get("levelId") not in level_ids and item.get("levelId") != "SITE":
                errors.append(f"{path}.levelId: unknown level {item.get('levelId')!r}")

    for index, space in enumerate(collection_values["spaces"]):
        path = f"$.spaces[{index}]"
        if not isinstance(space, dict):
            continue
        for key in ("name", "roomUse", "accessIntent", "geometry"):
            _require(errors, space.get(key), f"{path}.{key}", "value")
        if space.get("accessIntent") not in ACCESS_INTENTS:
            errors.append(f"{path}.accessIntent: unsupported intent")
        _validate_rect(errors, space.get("geometry", {}).get("rect") if isinstance(space.get("geometry"), dict) else None, f"{path}.geometry.rect")

    for collection in ("openings", "windows"):
        for index, item in enumerate(collection_values[collection]):
            path = f"$.{collection}[{index}]"
            if not isinstance(item, dict):
                continue
            for key in ("tag", "hostSpace", "wall", "accessIntent", "geometry"):
                _require(errors, item.get(key), f"{path}.{key}", "value")
            if item.get("hostSpace") not in all_ids:
                errors.append(f"{path}.hostSpace: unknown space {item.get('hostSpace')!r}")
            if item.get("accessIntent") not in ACCESS_INTENTS and item.get("accessIntent") != "room":
                errors.append(f"{path}.accessIntent: unsupported intent")
            geometry = item.get("geometry")
            if not isinstance(geometry, dict) or geometry.get("width", 0) <= 0:
                errors.append(f"{path}.geometry.width: expected positive number")

    for index, entry in enumerate(collection_values["entries"]):
        path = f"$.entries[{index}]"
        if not isinstance(entry, dict):
            continue
        for key in ("entryKind", "label", "openingId", "hostSpace", "accessIntent"):
            _require(errors, entry.get(key), f"{path}.{key}", "value")
        if entry.get("openingId") not in all_ids:
            errors.append(f"{path}.openingId: unknown opening")
        if entry.get("hostSpace") not in all_ids:
            errors.append(f"{path}.hostSpace: unknown space")
        if entry.get("accessIntent") not in ACCESS_INTENTS:
            errors.append(f"{path}.accessIntent: unsupported intent")

    for index, connector in enumerate(collection_values["verticalConnectors"]):
        path = f"$.verticalConnectors[{index}]"
        if not isinstance(connector, dict):
            continue
        for key in ("fromLevelId", "toLevelId", "stairId", "accessIntent"):
            _require(errors, connector.get(key), f"{path}.{key}", "value")
        for key in ("fromLevelId", "toLevelId"):
            if connector.get(key) not in level_ids:
                errors.append(f"{path}.{key}: unknown level")
        if connector.get("stairId") not in all_ids:
            errors.append(f"{path}.stairId: unknown stair")
        if connector.get("accessIntent") != "vertical":
            errors.append(f"{path}.accessIntent: expected 'vertical'")

    for index, stair in enumerate(collection_values["stairs"]):
        path = f"$.stairs[{index}]"
        if not isinstance(stair, dict):
            continue
        for key in ("levelFrom", "levelTo", "verticalConnectorId", "configuration", "geometry"):
            _require(errors, stair.get(key), f"{path}.{key}", "value")
        if stair.get("verticalConnectorId") not in all_ids:
            errors.append(f"{path}.verticalConnectorId: unknown connector")
        if stair.get("levelFrom") not in level_ids or stair.get("levelTo") not in level_ids:
            errors.append(f"{path}: stair references an unknown level")

    revisions = model.get("revisions")
    if not isinstance(revisions, list) or not revisions:
        errors.append("$.revisions: expected a non-empty array")
    else:
        for index, revision in enumerate(revisions):
            path = f"$.revisions[{index}]"
            if not isinstance(revision, dict):
                errors.append(f"{path}: expected object")
                continue
            for key in ("id", "date", "author", "summary", "source", "legacy"):
                _require(errors, revision.get(key), f"{path}.{key}", "value")

    return errors


def roundtrip_report(
    canonical: dict[str, Any],
    source_site: dict[str, Any],
    source_plans: dict[str, Any],
) -> dict[str, Any]:
    migrated_site, migrated_plans = canonical_to_legacy(canonical)
    site_equal = migrated_site == source_site
    plans_equal = migrated_plans == source_plans
    return {
        "status": "pass" if site_equal and plans_equal else "fail",
        "siteEqual": site_equal,
        "plansEqual": plans_equal,
        "sourceCounts": {
            "levels": len(source_site.get("levels", [])),
            "spaces": len(source_plans.get("spaces", [])),
            "openings": len(source_plans.get("openings", [])),
            "windows": len(source_plans.get("windows", [])),
            "entries": len(source_plans.get("entries", [])),
            "stairs": len(source_plans.get("stairs", [])),
            "notes": len(source_plans.get("notes", [])),
            "revisions": len(source_site.get("revisions", [])),
        },
    }


def _cmd_migrate(args: argparse.Namespace) -> int:
    model = migrate_from_files()
    errors = validate_canonical(model)
    if errors:
        print(json.dumps({"status": "fail", "errors": errors}, indent=2))
        return 1
    output = Path(args.output) if args.output else CANONICAL_PATH
    write_json(output, model)
    print(json.dumps({
        "status": "pass",
        "output": str(output.relative_to(ROOT) if output.is_relative_to(ROOT) else output),
        "schemaVersion": model["schemaVersion"],
        "counts": {
            key: len(model[key])
            for key in (
                "levels",
                "spaces",
                "openings",
                "windows",
                "entries",
                "circulationZones",
                "exteriorZones",
                "verticalConnectors",
                "stairs",
            )
        },
    }, indent=2))
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.path) if args.path else CANONICAL_PATH
    model = load_canonical_model(path)
    errors = validate_canonical(model)
    print(json.dumps({
        "status": "pass" if not errors else "fail",
        "path": str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path),
        "schemaVersion": model.get("schemaVersion"),
        "errors": errors,
    }, indent=2))
    return 0 if not errors else 1


def _cmd_roundtrip(args: argparse.Namespace) -> int:
    canonical = migrate_from_files()
    report = roundtrip_report(
        canonical,
        read_json(SOURCE_ROOT / "site_plan.json"),
        read_json(SOURCE_ROOT / "preliminary_plans.json"),
    )
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    migrate = commands.add_parser("migrate", help="write the canonical v2 model")
    migrate.add_argument("--output", help="override canonical output path")
    migrate.set_defaults(func=_cmd_migrate)

    validate = commands.add_parser("validate", help="validate canonical v2 JSON")
    validate.add_argument("path", nargs="?", help="canonical JSON path")
    validate.set_defaults(func=_cmd_validate)

    roundtrip = commands.add_parser(
        "roundtrip",
        help="prove the legacy source survives v2 migration and inverse mapping",
    )
    roundtrip.set_defaults(func=_cmd_roundtrip)
    return parser


if __name__ == "__main__":
    arguments = build_parser().parse_args()
    sys.exit(arguments.func(arguments))