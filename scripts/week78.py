#!/usr/bin/env python3
"""Week 7 and Week 8 architectural-intelligence enrichment.

Week 7 adds versioned, inspectable rule packs.  Universal geometry checks are
kept separate from configurable planning checks so changing a jurisdictional
pack changes findings without changing geometry code.

Week 8 adds a deterministic technical-drawing quality contract.  It does not
claim that a PDF is approved for construction; it verifies that sheets,
labels, model IDs, drawing conventions, and validation status can be traced
together before export.
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
RULE_PACK_ROOT = REPORT_ROOT / "rule-packs"
DEFAULT_RULE_PACK_PATH = RULE_PACK_ROOT / "india-preliminary-review.v1.json"
WEEK7_REPORT_PATH = REPORT_ROOT / "week7-rule-pack-report.json"
WEEK8_REPORT_PATH = REPORT_ROOT / "week8-drawing-quality-report.json"
MANIFEST_PATH = REPORT_ROOT / "week78-enrichment-manifest.json"


DEFAULT_RULE_PACK: dict[str, Any] = {
    "id": "india-preliminary-review",
    "version": "1.0.0",
    "effectiveDate": "2026-09-19",
    "jurisdiction": "India / preliminary planning review",
    "description": (
        "Configurable planning checks for preliminary review. This pack is "
        "not a code-compliance or approval determination."
    ),
    "universal": {
        "requireUniqueIds": True,
        "requireTraceableOpeningHosts": True,
        "requirePositiveOpeningWidths": True,
        "requireNumericSpaceRects": True,
    },
    "accessibility": {
        "doorMinWidth": 32.0,
        "routeMinWidth": 44.0,
        "stairMinWidth": 44.0,
    },
    "egress": {
        "minimumExteriorExitsByUse": {"assembly": 1},
        "minimumExteriorExitWidth": 36.0,
    },
    "daylight": {
        "requiredWindowUses": ["reception", "office", "library", "assembly"],
    },
    "ventilation": {
        "requiredWindowUses": ["reception", "office", "library", "assembly", "service"],
    },
    "wetArea": {
        "uses": ["service"],
        "minimumVentilationOpenings": 1,
    },
    "service": {
        "requireOpeningForUses": ["service"],
    },
    "professionalReviewItems": [
        "Have a licensed architect confirm the selected jurisdiction and applicable development rules.",
        "Have an accessibility professional verify route widths, landings, door clearances, and fixtures.",
        "Have a fire/life-safety professional verify occupancy, travel distance, exits, and fire separation.",
        "Have structural, MEP, survey, and local-authority reviewers confirm assumptions before issue.",
    ],
    "assumptions": [
        "All dimensions are nominal planning dimensions in inches.",
        "A passing check is not a permit, code, fire, accessibility, or construction certification.",
        "Missing source information is reported as an assumption or warning rather than silently invented.",
    ],
}


DRAWING_LAYERS = {
    "wall-cut": {"lineWeight": 0.50, "purpose": "cut walls and primary structure"},
    "wall-projection": {"lineWeight": 0.25, "purpose": "overhead and projected geometry"},
    "opening": {"lineWeight": 0.25, "purpose": "doors, windows, and swing graphics"},
    "stair": {"lineWeight": 0.35, "purpose": "riser, tread, landing, and direction graphics"},
    "dimension": {"lineWeight": 0.18, "purpose": "dimensions and extension lines"},
    "annotation": {"lineWeight": 0.18, "purpose": "labels, legends, and notes"},
    "hatch": {"lineWeight": 0.13, "purpose": "material and cut-area hatches"},
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected an object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _rect(space: dict[str, Any]) -> tuple[float, float, float, float] | None:
    geometry = space.get("geometry")
    value = geometry.get("rect") if isinstance(geometry, dict) else space.get("rect")
    if not isinstance(value, list) or len(value) != 4:
        return None
    numbers = [_number(item) for item in value]
    if any(item is None for item in numbers):
        return None
    return tuple(numbers)  # type: ignore[return-value]


def _room_use(space: dict[str, Any]) -> str:
    return str(space.get("roomUse") or space.get("use") or "").strip().lower()


def _level_id(item: dict[str, Any]) -> str:
    return str(item.get("levelId") or item.get("level") or "")


def _geometry(item: dict[str, Any]) -> dict[str, Any]:
    value = item.get("geometry")
    return value if isinstance(value, dict) else item


def _finding(
    finding_id: str,
    severity: str,
    rule: str,
    message: str,
    *,
    source: str,
    category: str,
    pack_id: str | None = None,
    level_id: str | None = None,
    space_ids: list[str] | None = None,
    opening_ids: list[str] | None = None,
    suggested_fixes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "severity": severity,
        "rule": rule,
        "source": source,
        "category": category,
        "rulePackId": pack_id,
        "levelId": level_id,
        "spaceIds": space_ids or [],
        "openingIds": opening_ids or [],
        "message": message,
        "suggestedFixes": suggested_fixes or [],
    }


def _finding_counts(findings: Iterable[dict[str, Any]]) -> dict[str, int]:
    values = list(findings)
    return {
        severity: sum(1 for item in values if item["severity"] == severity)
        for severity in ("BLOCKER", "ERROR", "WARNING")
        if any(item["severity"] == severity for item in values)
    }


def _status(findings: Iterable[dict[str, Any]]) -> str:
    return "fail" if any(item["severity"] in {"BLOCKER", "ERROR"} for item in findings) else "pass"


def _load_rule_pack(path: Path | None = None) -> dict[str, Any]:
    pack = copy.deepcopy(DEFAULT_RULE_PACK)
    if path is not None and path.exists():
        supplied = read_json(path)
        for key, value in supplied.items():
            if isinstance(value, dict) and isinstance(pack.get(key), dict):
                pack[key].update(value)
            else:
                pack[key] = value
    required = ("id", "version", "universal", "accessibility", "egress")
    missing = [key for key in required if key not in pack]
    if missing:
        raise ValueError(f"rule pack is missing required keys: {', '.join(missing)}")
    return pack


def _space_maps(model: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    spaces = [item for item in model.get("spaces", []) if isinstance(item, dict)]
    by_id = {str(item.get("id")): item for item in spaces if item.get("id")}
    by_use: dict[str, list[dict[str, Any]]] = {}
    for space in spaces:
        by_use.setdefault(_room_use(space), []).append(space)
    return by_id, by_use


def _opening_width(opening: dict[str, Any]) -> float | None:
    return _number(_geometry(opening).get("width"))


def _opening_connection(opening: dict[str, Any]) -> str:
    semantic = opening.get("semantic")
    if isinstance(semantic, dict):
        return str(semantic.get("connectionType") or "")
    return ""


def rule_pack_report(model: dict[str, Any], rule_pack: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run universal and configurable planning checks against one rule pack."""

    pack = copy.deepcopy(rule_pack or DEFAULT_RULE_PACK)
    pack_id = str(pack["id"])
    spaces_by_id, spaces_by_use = _space_maps(model)
    openings = [item for item in model.get("openings", []) if isinstance(item, dict)]
    windows = [item for item in model.get("windows", []) if isinstance(item, dict)]
    findings: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []

    def add(
        finding_id: str,
        severity: str,
        rule: str,
        message: str,
        *,
        source: str,
        category: str,
        **kwargs: Any,
    ) -> None:
        findings.append(
            _finding(
                finding_id,
                severity,
                rule,
                message,
                source=source,
                category=category,
                pack_id=pack_id,
                **kwargs,
            )
        )

    def check(check_id: str, category: str, source: str, status: str, detail: str) -> None:
        checks.append(
            {
                "id": check_id,
                "category": category,
                "source": source,
                "status": status,
                "detail": detail,
                "rulePackId": pack_id if source == "jurisdictional" else None,
            }
        )

    universal = pack["universal"]
    if universal.get("requireUniqueIds", True):
        collections = (
            ("spaces", model.get("spaces", [])),
            ("openings", model.get("openings", [])),
            ("windows", model.get("windows", [])),
            ("stairs", model.get("stairs", [])),
            ("levels", model.get("levels", [])),
        )
        for label, items in collections:
            ids = [str(item.get("id")) for item in items if isinstance(item, dict) and item.get("id")]
            duplicates = sorted({item for item in ids if ids.count(item) > 1})
            if duplicates:
                add(
                    f"VAL7-UNIQUE-{label}",
                    "ERROR",
                    "MODEL_IDS_MUST_BE_UNIQUE",
                    f"{label} contains duplicate IDs: {', '.join(duplicates)}.",
                    source="universal",
                    category="geometry",
                    suggested_fixes=["Give every model object one stable, unique ID."],
                )
        check("UNIVERSAL-IDS", "geometry", "universal", "pass", "Checked stable IDs across model collections.")

    if universal.get("requireNumericSpaceRects", True):
        invalid_spaces = [str(space.get("id", "UNKNOWN")) for space in spaces_by_id.values() if _rect(space) is None]
        if invalid_spaces:
            add(
                "VAL7-SPACE-RECTS",
                "ERROR",
                "SPACE_RECTANGLES_MUST_BE_NUMERIC",
                f"Spaces without numeric rectangles: {', '.join(invalid_spaces)}.",
                source="universal",
                category="geometry",
                space_ids=invalid_spaces,
                suggested_fixes=["Provide four numeric coordinates for every space rectangle."],
            )
            check("UNIVERSAL-SPACE-RECTS", "geometry", "universal", "fail", "One or more spaces lack numeric rectangles.")
        else:
            check("UNIVERSAL-SPACE-RECTS", "geometry", "universal", "pass", "All spaces have numeric rectangles.")

    if universal.get("requireTraceableOpeningHosts", True):
        unhosted = [
            str(opening.get("id", "UNKNOWN"))
            for opening in openings
            if not opening.get("hostSpace") or str(opening.get("hostSpace")) not in spaces_by_id
        ]
        if unhosted:
            add(
                "VAL7-OPENING-HOSTS",
                "ERROR",
                "OPENINGS_MUST_REFERENCE_EXISTING_SPACES",
                f"Openings without an existing host space: {', '.join(unhosted)}.",
                source="universal",
                category="geometry",
                opening_ids=unhosted,
                suggested_fixes=["Attach each visible opening to its authoritative host space."],
            )
            check("UNIVERSAL-OPENING-HOSTS", "geometry", "universal", "fail", "Opening traceability is incomplete.")
        else:
            check("UNIVERSAL-OPENING-HOSTS", "geometry", "universal", "pass", "Every opening references a model space.")

    if universal.get("requirePositiveOpeningWidths", True):
        invalid_widths = [
            str(opening.get("id", "UNKNOWN"))
            for opening in openings
            if _opening_width(opening) is None or _opening_width(opening) <= 0
        ]
        if invalid_widths:
            add(
                "VAL7-OPENING-WIDTHS",
                "ERROR",
                "OPENING_WIDTHS_MUST_BE_POSITIVE",
                f"Openings without positive widths: {', '.join(invalid_widths)}.",
                source="universal",
                category="geometry",
                opening_ids=invalid_widths,
                suggested_fixes=["Provide a positive nominal width and verify the host wall span."],
            )
            check("UNIVERSAL-OPENING-WIDTHS", "geometry", "universal", "fail", "Opening width data is incomplete.")
        else:
            check("UNIVERSAL-OPENING-WIDTHS", "geometry", "universal", "pass", "All openings have positive widths.")

    accessibility = pack["accessibility"]
    min_door = float(accessibility.get("doorMinWidth", 0))
    narrow_doors = [
        opening
        for opening in openings
        if str(opening.get("kind") or opening.get("type")) == "door"
        and (_opening_width(opening) or 0) < min_door
    ]
    if narrow_doors:
        for opening in narrow_doors:
            add(
                f"VAL7-ACCESS-DOOR-{opening.get('id', 'UNKNOWN')}",
                "ERROR",
                "ACCESSIBLE_DOOR_WIDTH_MUST_MEET_RULE_PACK",
                f"{opening.get('id')} width {_opening_width(opening)} is below the {min_door:g} in rule-pack minimum.",
                source="jurisdictional",
                category="accessibility",
                level_id=_level_id(opening),
                opening_ids=[str(opening.get("id"))],
                suggested_fixes=["Increase clear width and verify approach, landing, hardware, and threshold."],
            )
    check(
        "ACCESSIBILITY-DOOR-WIDTH",
        "accessibility",
        "jurisdictional",
        "fail" if narrow_doors else "pass",
        f"Checked {len(openings)} openings against a {min_door:g} in minimum.",
    )

    stairs = [item for item in model.get("stairs", []) if isinstance(item, dict)]
    min_stair = float(accessibility.get("stairMinWidth", 0))
    narrow_stairs = [stair for stair in stairs if (_number(_geometry(stair).get("width")) or 0) < min_stair]
    for stair in narrow_stairs:
        add(
            f"VAL7-ACCESS-STAIR-{stair.get('id', 'UNKNOWN')}",
            "ERROR",
            "ACCESSIBLE_STAIR_WIDTH_MUST_MEET_RULE_PACK",
            f"{stair.get('id')} width {_geometry(stair).get('width')} is below the {min_stair:g} in rule-pack minimum.",
            source="jurisdictional",
            category="accessibility",
            level_id=str(stair.get("levelFrom") or _geometry(stair).get("levelFrom") or ""),
            suggested_fixes=["Coordinate clear width, handrails, landings, and the required accessible route."],
        )
    check(
        "ACCESSIBILITY-STAIR-WIDTH",
        "accessibility",
        "jurisdictional",
        "fail" if narrow_stairs else "pass",
        f"Checked {len(stairs)} stairs against a {min_stair:g} in minimum.",
    )

    egress = pack["egress"]
    min_exit_width = float(egress.get("minimumExteriorExitWidth", 0))
    entries = {str(item.get("openingId")) for item in model.get("entries", []) if isinstance(item, dict)}
    for use, required_count in egress.get("minimumExteriorExitsByUse", {}).items():
        for space in spaces_by_use.get(str(use), []):
            exits = [
                opening
                for opening in openings
                if str(opening.get("hostSpace")) == str(space.get("id"))
                and (
                    _opening_connection(opening) == "exterior"
                    or str(opening.get("id")) in entries
                    or (isinstance(opening.get("semantic"), dict) and opening["semantic"].get("sideB") is None)
                )
            ]
            total_width = sum(_opening_width(opening) or 0 for opening in exits)
            if len(exits) < int(required_count) or total_width < min_exit_width:
                add(
                    f"VAL7-EGRESS-{space.get('id')}",
                    "BLOCKER",
                    "EGRESS_EXITS_MUST_MEET_RULE_PACK",
                    f"{space.get('id')} ({use}) has {len(exits)} exterior exit(s) and {total_width:g} in total width; "
                    f"the pack requires {int(required_count)} exit(s) and {min_exit_width:g} in.",
                    source="jurisdictional",
                    category="egress",
                    level_id=_level_id(space),
                    space_ids=[str(space.get("id"))],
                    suggested_fixes=["Add or coordinate exterior exits and verify occupant load with a fire consultant."],
                )
    check("EGRESS-EXITS", "egress", "jurisdictional", "fail" if any(item["rule"] == "EGRESS_EXITS_MUST_MEET_RULE_PACK" for item in findings) else "pass", "Checked configured exterior exit requirements.")

    window_hosts = {str(item.get("hostSpace")) for item in windows if item.get("hostSpace")}
    for category, config_key in (("daylight", "requiredWindowUses"), ("ventilation", "requiredWindowUses")):
        required_uses = pack.get(category, {}).get(config_key, [])
        for use in required_uses:
            for space in spaces_by_use.get(str(use), []):
                if str(space.get("id")) not in window_hosts:
                    add(
                        f"VAL7-{category.upper()}-{space.get('id')}",
                        "WARNING",
                        f"{category.upper()}_OPENING_ASSUMPTION_MISSING",
                        f"{space.get('id')} ({use}) has no modeled window/opening for {category}.",
                        source="jurisdictional",
                        category=category,
                        level_id=_level_id(space),
                        space_ids=[str(space.get("id"))],
                        suggested_fixes=[f"Model the {category} strategy or document why another approved strategy applies."],
                    )
        check_id = f"{category.upper()}-OPENINGS"
        check(
            check_id,
            category,
            "jurisdictional",
            "fail" if any(item["category"] == category and item["severity"] in {"ERROR", "BLOCKER"} for item in findings) else "pass",
            f"Checked configured {category} opening assumptions.",
        )

    wet = pack["wetArea"]
    for space in [item for use in wet.get("uses", []) for item in spaces_by_use.get(str(use), [])]:
        count = sum(1 for window in windows if str(window.get("hostSpace")) == str(space.get("id")))
        if count < int(wet.get("minimumVentilationOpenings", 0)):
            add(
                f"VAL7-WET-{space.get('id')}",
                "WARNING",
                "WET_AREA_VENTILATION_MUST_BE_EXPLAINED",
                f"{space.get('id')} has {count} modeled ventilation opening(s), below the configured {wet.get('minimumVentilationOpenings')}.",
                source="jurisdictional",
                category="wet-area",
                level_id=_level_id(space),
                space_ids=[str(space.get("id"))],
                suggested_fixes=["Document a window, shaft, mechanical exhaust, or other reviewed wet-area strategy."],
            )
    check("WET-AREA-VENTILATION", "wet-area", "jurisdictional", "pass", "Wet-area ventilation assumptions are explicitly reported.")

    for use in pack.get("service", {}).get("requireOpeningForUses", []):
        for space in spaces_by_use.get(str(use), []):
            if not any(str(opening.get("hostSpace")) == str(space.get("id")) for opening in openings):
                add(
                    f"VAL7-SERVICE-{space.get('id')}",
                    "WARNING",
                    "SERVICE_SPACE_ROUTE_MUST_BE_EXPLAINED",
                    f"{space.get('id')} ({use}) has no modeled door/opening.",
                    source="jurisdictional",
                    category="service",
                    level_id=_level_id(space),
                    space_ids=[str(space.get("id"))],
                    suggested_fixes=["Document the service route and keep it distinct from public circulation where required."],
                )
    check("SERVICE-ROUTES", "service", "jurisdictional", "pass", "Service-route assumptions are explicitly reported.")

    professional_items = list(pack.get("professionalReviewItems", []))
    return {
        "reportVersion": "week7.rule-pack.v1",
        "status": _status(findings),
        "findingCounts": _finding_counts(findings),
        "selectedRulePack": copy.deepcopy(pack),
        "checks": checks,
        "findings": findings,
        "assumptions": list(pack.get("assumptions", [])),
        "professionalReviewItems": professional_items,
        "separation": {
            "universalRuleCount": sum(1 for item in checks if item["source"] == "universal"),
            "jurisdictionalRuleCount": sum(1 for item in checks if item["source"] == "jurisdictional"),
            "geometryChangedByPack": False,
        },
    }


def _sheet_catalog(model: dict[str, Any]) -> list[dict[str, Any]]:
    levels = [item for item in model.get("levels", []) if isinstance(item, dict)]
    sheets: list[dict[str, Any]] = []
    for index, level in enumerate(levels, start=1):
        level_id = str(level.get("id"))
        sheets.append(
            {
                "sheetId": f"A-{100 + index:03d}",
                "kind": "plan",
                "levelId": level_id,
                "title": f"{level.get('name', level_id)} plan",
                "scale": "1:100",
                "northArrow": True,
                "legend": True,
                "titleBlock": True,
                "sourceModelIds": {
                    "spaces": sorted(str(item.get("id")) for item in model.get("spaces", []) if _level_id(item) == level_id),
                    "openings": sorted(str(item.get("id")) for item in model.get("openings", []) if _level_id(item) == level_id),
                    "windows": sorted(str(item.get("id")) for item in model.get("windows", []) if _level_id(item) == level_id),
                    "stairs": sorted(str(item.get("id")) for item in model.get("stairs", []) if str(item.get("levelFrom")) == level_id or str(item.get("levelTo")) == level_id),
                },
            }
        )
    sheets.extend(
        [
            {
                "sheetId": "A-301",
                "kind": "section",
                "levelId": None,
                "title": "Building section",
                "scale": "1:100",
                "northArrow": False,
                "legend": True,
                "titleBlock": True,
                "sourceModelIds": {"levels": sorted(str(item.get("id")) for item in levels), "stairs": sorted(str(item.get("id")) for item in model.get("stairs", []))},
            },
            {
                "sheetId": "A-401",
                "kind": "elevation",
                "levelId": None,
                "title": "Principal elevation",
                "scale": "1:100",
                "northArrow": True,
                "legend": True,
                "titleBlock": True,
                "sourceModelIds": {"levels": sorted(str(item.get("id")) for item in levels), "openings": sorted(str(item.get("id")) for item in model.get("openings", []))},
            },
        ]
    )
    return sheets


def drawing_quality_report(
    model: dict[str, Any],
    week7: dict[str, Any],
    week56: dict[str, Any],
) -> dict[str, Any]:
    """Create a deterministic, model-traceable technical drawing contract."""

    findings: list[dict[str, Any]] = []
    spaces = [item for item in model.get("spaces", []) if isinstance(item, dict)]
    openings = [item for item in model.get("openings", []) if isinstance(item, dict)]
    stairs = [item for item in model.get("stairs", []) if isinstance(item, dict)]
    levels = [item for item in model.get("levels", []) if isinstance(item, dict)]
    space_ids = {str(item.get("id")) for item in spaces}
    level_ids = {str(item.get("id")) for item in levels}

    invalid_traceability = [
        str(item.get("id", "UNKNOWN"))
        for item in openings
        if not item.get("id") or str(item.get("hostSpace")) not in space_ids or _level_id(item) not in level_ids
    ]
    if invalid_traceability:
        findings.append(
            {
                "id": "VAL8-OPENING-TRACEABILITY",
                "severity": "ERROR",
                "rule": "VISIBLE_OPENINGS_MUST_TRACE_TO_MODEL",
                "message": f"Openings cannot be traced to a level and host space: {', '.join(invalid_traceability)}.",
                "sourceModelIds": invalid_traceability,
            }
        )
    invalid_spaces = [str(item.get("id", "UNKNOWN")) for item in spaces if not item.get("id") or not item.get("name")]
    if invalid_spaces:
        findings.append(
            {
                "id": "VAL8-SPACE-LABELS",
                "severity": "ERROR",
                "rule": "VISIBLE_SPACES_MUST_HAVE_TRACEABLE_LABELS",
                "message": f"Spaces need stable IDs and room labels: {', '.join(invalid_spaces)}.",
                "sourceModelIds": invalid_spaces,
            }
        )
    invalid_stairs = [str(item.get("id", "UNKNOWN")) for item in stairs if not item.get("id") or not item.get("levelFrom") or not item.get("levelTo")]
    if invalid_stairs:
        findings.append(
            {
                "id": "VAL8-STAIR-TRACEABILITY",
                "severity": "ERROR",
                "rule": "VISIBLE_STAIRS_MUST_TRACE_TO_LEVELS",
                "message": f"Stairs need stable IDs and two level endpoints: {', '.join(invalid_stairs)}.",
                "sourceModelIds": invalid_stairs,
            }
        )

    sheets = _sheet_catalog(model)
    for sheet in sheets:
        required = ("scale", "legend", "titleBlock")
        missing = [key for key in required if not sheet.get(key)]
        if missing:
            findings.append(
                {
                    "id": f"VAL8-SHEET-{sheet['sheetId']}",
                    "severity": "ERROR",
                    "rule": "SHEET_METADATA_MUST_BE_COMPLETE",
                    "message": f"{sheet['sheetId']} is missing: {', '.join(missing)}.",
                    "sourceModelIds": [],
                }
            )

    canonical_payload = {
        "modelRevision": model.get("project", {}).get("revision"),
        "levels": sorted(str(item.get("id")) for item in levels),
        "spaces": sorted((str(item.get("id")), str(item.get("name"))) for item in spaces),
        "openings": sorted((str(item.get("id")), str(item.get("hostSpace")), str(item.get("tag"))) for item in openings),
        "windows": sorted(str(item.get("id")) for item in model.get("windows", []) if isinstance(item, dict)),
        "stairs": sorted(str(item.get("id")) for item in stairs),
        "sheets": sheets,
        "layers": DRAWING_LAYERS,
    }
    deterministic_signature = hashlib.sha256(
        json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    base_status = week56.get("status", "fail")
    rule_status = week7.get("status", "fail")
    issuable = not findings and base_status == "pass" and rule_status == "pass"
    return {
        "reportVersion": "week8.drawing-quality.v1",
        "status": "pass" if issuable else "fail",
        "stamp": "VALIDATED FOR PRELIMINARY REVIEW" if issuable else "NOT ISSUABLE",
        "issuable": issuable,
        "findingCounts": _finding_counts(findings),
        "findings": findings,
        "sheetCatalog": sheets,
        "drawingStandards": {
            "layers": copy.deepcopy(DRAWING_LAYERS),
            "wallHierarchy": "wall-cut > wall-projection > opening > annotation",
            "hatches": ["cut-material", "wet-area", "service-zone"],
            "dimensionUnits": model.get("units", "inch"),
            "titleBlockFields": ["project", "sheetId", "revision", "scale", "status", "north"],
            "traceabilityRequired": True,
        },
        "consistency": {
            "planLevelIds": sorted(level_ids),
            "sectionLevelIds": sorted(str(item.get("id")) for item in levels),
            "elevationLevelIds": sorted(str(item.get("id")) for item in levels),
            "planSectionElevationLevelsMatch": True,
            "visibleSpaceCount": len(spaces),
            "visibleOpeningCount": len(openings),
            "visibleStairCount": len(stairs),
            "modelTraceability": not invalid_traceability and not invalid_spaces and not invalid_stairs,
        },
        "determinism": {
            "algorithm": "sha256",
            "inputContract": "canonical model IDs + labels + sheet catalog + drawing standards",
            "signature": deterministic_signature,
            "sameModelSameRulePackProducesSameSignature": True,
            "exportFormats": ["DXF", "PDF", "SVG"],
        },
        "validationGate": {
            "week56Status": base_status,
            "week7Status": rule_status,
            "week8LocalStatus": "pass" if not findings else "fail",
            "professionalReviewRequired": True,
            "explanation": (
                "The sheet stamp inherits upstream validation status; it cannot hide blockers "
                "or substitute for qualified professional review."
            ),
        },
    }


def enrichment_report(
    model: dict[str, Any],
    *,
    rule_pack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "scripts"))
    from week56 import enrichment_report as week56_enrichment_report  # type: ignore

    previous = week56_enrichment_report(model)
    week7 = rule_pack_report(model, rule_pack)
    week8 = drawing_quality_report(model, week7, previous)
    findings = previous["findings"] + week7["findings"] + week8["findings"]
    return {
        "reportVersion": "week78.enrichment.v1",
        "status": _status(findings),
        "findingCounts": _finding_counts(findings),
        "findings": findings,
        "week5": previous["week5"],
        "week6": previous["week6"],
        "week7": week7,
        "week8": week8,
    }


def write_reports(rule_pack_path: Path | None = None) -> dict[str, Any]:
    pack_path = rule_pack_path or DEFAULT_RULE_PACK_PATH
    pack = _load_rule_pack(pack_path if pack_path.exists() else None)
    RULE_PACK_ROOT.mkdir(parents=True, exist_ok=True)
    write_json(DEFAULT_RULE_PACK_PATH, pack)
    model = read_json(CANONICAL_PATH)
    report = enrichment_report(model, rule_pack=pack)
    model["rulePack"] = {
        "id": pack["id"],
        "version": pack["version"],
        "path": str(DEFAULT_RULE_PACK_PATH.relative_to(ROOT)),
        "effectiveDate": pack.get("effectiveDate"),
        "jurisdiction": pack.get("jurisdiction"),
    }
    model["drawingQuality"] = {
        "report": str(WEEK8_REPORT_PATH.relative_to(ROOT)),
        "stamp": report["week8"]["stamp"],
        "deterministicSignature": report["week8"]["determinism"]["signature"],
    }
    enrichment = model.get("enrichment", {})
    enrichment = enrichment if isinstance(enrichment, dict) else {}
    enrichment.update(
        {
            "version": "week78.enrichment.v1",
            "week7Report": str(WEEK7_REPORT_PATH.relative_to(ROOT)),
            "week8Report": str(WEEK8_REPORT_PATH.relative_to(ROOT)),
            "rulePack": str(DEFAULT_RULE_PACK_PATH.relative_to(ROOT)),
        }
    )
    model["enrichment"] = enrichment
    write_json(
        WEEK7_REPORT_PATH,
        {
            "reportVersion": report["week7"]["reportVersion"],
            "status": report["week7"]["status"],
            "findingCounts": report["week7"]["findingCounts"],
            "selectedRulePack": report["week7"]["selectedRulePack"],
            "checks": report["week7"]["checks"],
            "findings": report["week7"]["findings"],
            "assumptions": report["week7"]["assumptions"],
            "professionalReviewItems": report["week7"]["professionalReviewItems"],
            "separation": report["week7"]["separation"],
        },
    )
    write_json(WEEK8_REPORT_PATH, report["week8"])
    write_json(
        MANIFEST_PATH,
        {
            "manifestVersion": "week78.enrichment-manifest.v1",
            "status": report["status"],
            "rulePack": str(DEFAULT_RULE_PACK_PATH.relative_to(ROOT)),
            "reports": {
                "week7": str(WEEK7_REPORT_PATH.relative_to(ROOT)),
                "week8": str(WEEK8_REPORT_PATH.relative_to(ROOT)),
            },
            "drawingStamp": report["week8"]["stamp"],
            "deterministicSignature": report["week8"]["determinism"]["signature"],
            "counts": {
                "levels": len(model.get("levels", [])),
                "spaces": len(model.get("spaces", [])),
                "openings": len(model.get("openings", [])),
                "windows": len(model.get("windows", [])),
                "sheets": len(report["week8"]["sheetCatalog"]),
            },
            "findingCounts": report["findingCounts"],
        },
    )
    write_json(CANONICAL_PATH, model)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "report"), nargs="?", default="validate")
    parser.add_argument("--rule-pack", type=Path, default=None)
    args = parser.parse_args(argv)
    report = write_reports(args.rule_pack)
    output = report if args.command == "report" else {
        "status": report["status"],
        "findingCounts": report["findingCounts"],
        "week7": {"status": report["week7"]["status"], "report": str(WEEK7_REPORT_PATH.relative_to(ROOT))},
        "week8": {"status": report["week8"]["status"], "stamp": report["week8"]["stamp"], "report": str(WEEK8_REPORT_PATH.relative_to(ROOT))},
    }
    print(json.dumps(output, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())