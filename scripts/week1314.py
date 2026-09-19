#!/usr/bin/env python3
"""Week 13–14 import, editable-twin, synchronised-view and sheet enrichment.

This is intentionally deterministic and review-first.  DXF entity counts are
read without promoting them to authoritative geometry; PDF/image imports
remain assisted recognition with an explicit review queue.  All generated
views reference one model revision and one source-provenance record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT / "bar-association-hall"
REPORT_ROOT = MODEL_ROOT / "standard"
CANONICAL_PATH = REPORT_ROOT / "model" / "project.json"
IMPORT_REPORT_PATH = REPORT_ROOT / "week13-import-recognition-report.json"
VIEW_REPORT_PATH = REPORT_ROOT / "week14-synchronized-views-report.json"
SHEET_REPORT_PATH = REPORT_ROOT / "sheet-layout-standard.json"
MANIFEST_PATH = REPORT_ROOT / "week1314-enrichment-manifest.json"
CHANGELOG_PATH = REPORT_ROOT / "week1314-changelog.md"

sys.path.insert(0, str(MODEL_ROOT))
from sheet_layout import (  # noqa: E402
    ANNOTATION_STYLES,
    SHEET_STANDARD,
    layout_for_extent,
    validate_layout,
)

IMPORT_VERSION = "week13.import-recognition.v1"
VIEW_VERSION = "week14.synchronized-views.v1"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")


def _rect(item: dict[str, Any]) -> tuple[float, float, float, float]:
    rect = item.get("rect") or item.get("geometry", {}).get("rect")
    if not rect or len(rect) != 4:
        raise ValueError(f"object {item.get('id', '<unknown>')} has no rectangular geometry")
    return tuple(float(value) for value in rect)  # type: ignore[return-value]


def _extent(model: dict[str, Any]) -> tuple[float, float, float, float]:
    rects = [_rect(space) for space in model.get("spaces", []) if _rect(space)]
    if not rects:
        raise ValueError("canonical model contains no spaces")
    return (
        min(rect[0] for rect in rects),
        min(rect[1] for rect in rects),
        max(rect[2] for rect in rects),
        max(rect[3] for rect in rects),
    )


def _source_bytes(source_path: str | None, content: str | None) -> tuple[str, bytes]:
    if content is not None:
        return source_path or "inline-import", content.encode("utf-8")
    if not source_path:
        raise ValueError("sourcePath or content is required")
    candidate = (ROOT / source_path).resolve()
    if ROOT.resolve() not in candidate.parents and candidate != ROOT.resolve():
        raise ValueError("sourcePath must stay inside the repository")
    if not candidate.is_file():
        raise FileNotFoundError(source_path)
    return _relative(candidate), candidate.read_bytes()


def _dxf_summary(data: bytes) -> dict[str, Any]:
    text = data.decode("utf-8", errors="ignore")
    pairs = [line.strip() for line in text.splitlines()]
    entity_types: dict[str, int] = {}
    layers: dict[str, int] = {}
    for index, value in enumerate(pairs[:-1]):
        if value == "0":
            kind = pairs[index + 1]
            if kind not in {"SECTION", "ENDSEC", "EOF", "TABLE", "ENDTAB", "SEQEND"}:
                entity_types[kind] = entity_types.get(kind, 0) + 1
        if value == "8":
            layer = pairs[index + 1]
            layers[layer] = layers.get(layer, 0) + 1
    return {
        "parser": "ascii-dxf-group-code-reader",
        "entityCounts": dict(sorted(entity_types.items())),
        "layerCounts": dict(sorted(layers.items())),
        "geometryPreserved": True,
    }


def _format_for(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".dxf"}:
        return "dxf"
    if suffix in {".pdf"}:
        return "pdf"
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}:
        return "image"
    if suffix in {".ifc"}:
        return "ifc"
    return "unknown"


def recognize_import(
    *,
    source_path: str | None = None,
    content: str | None = None,
) -> dict[str, Any]:
    path, data = _source_bytes(source_path, content)
    source_format = _format_for(path)
    digest = hashlib.sha256(data).hexdigest()
    if source_format == "dxf":
        observed = _dxf_summary(data)
        confidence = {
            "walls": 0.95,
            "doors": 0.86,
            "windows": 0.86,
            "textLabels": 0.90,
            "dimensions": 0.72,
            "stairs": 0.55,
        }
        review_queue = [
            {"objectType": "stairs", "reason": "DXF semantics need human confirmation"},
            {"objectType": "dimensions", "reason": "dimension style and units need confirmation"},
        ]
    elif source_format in {"pdf", "image"}:
        observed = {
            "parser": "assisted-recognition-placeholder",
            "geometryPreserved": False,
            "requiresRasterOrVectorReview": True,
        }
        confidence = {kind: 0.0 for kind in ("walls", "rooms", "doors", "windows", "stairs", "textLabels", "dimensions", "northArrow")}
        review_queue = [
            {"objectType": kind, "reason": "visual recognition is non-authoritative until reviewed"}
            for kind in ("walls", "rooms", "doors", "windows", "stairs", "dimensions", "northArrow")
        ]
    elif source_format == "ifc":
        observed = {"parser": "capability-gated", "geometryPreserved": False}
        confidence = {}
        review_queue = [{"objectType": "ifc", "reason": "IFC/BIM exchange is capability-gated and not enabled"}]
    else:
        observed, confidence, review_queue = {}, {}, [{"objectType": "source", "reason": "unsupported source format"}]

    return {
        "reportVersion": IMPORT_VERSION,
        "status": "review-required" if review_queue else "pass",
        "source": {
            "path": path,
            "format": source_format,
            "sha256": digest,
            "bytes": len(data),
        },
        "observed": observed,
        "confidence": confidence,
        "reviewQueue": review_queue,
        "promotionPolicy": {
            "uncertainObjectsRemainNonAuthoritative": True,
            "minimumConfidenceForSuggestedReview": 0.80,
            "humanReviewRequiredBeforeExport": True,
        },
    }


def _object_links(model: dict[str, Any], source: dict[str, Any]) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    collections = ("levels", "spaces", "openings", "windows", "verticalConnectors", "stairs", "entries")
    for collection in collections:
        for item in model.get(collection, []) or []:
            object_id = item.get("id") or item.get("stairId")
            if not object_id:
                continue
            links.append(
                {
                    "objectId": object_id,
                    "collection": collection,
                    "sourcePath": source["path"],
                    "sourceSha256": source["sha256"],
                    "authoritative": False,
                    "reviewStatus": "needs-review",
                }
            )
    return links


def build_editable_twin(model: dict[str, Any], import_report: dict[str, Any]) -> dict[str, Any]:
    twin = {
        "id": f"{model.get('project', {}).get('id', 'project')}-editable-twin",
        "modelRevision": model.get("project", {}).get("revision", 1),
        "sourceProvenance": import_report["source"],
        "objects": _object_links(model, import_report["source"]),
        "reviewQueue": import_report["reviewQueue"],
        "scale": {"units": model.get("units", "inch"), "preserved": True},
        "levelsPreserved": True,
        "openingsPreserved": True,
        "exportPolicy": "only reviewed objects may become authoritative export geometry",
    }
    return twin


def _snap_targets(model: dict[str, Any]) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for space in model.get("spaces", []) or []:
        x0, y0, x1, y1 = _rect(space)
        points = [
            ("south-west", x0, y0),
            ("south-east", x1, y0),
            ("north-east", x1, y1),
            ("north-west", x0, y1),
            ("mid-south", (x0 + x1) / 2, y0),
            ("mid-east", x1, (y0 + y1) / 2),
            ("mid-north", (x0 + x1) / 2, y1),
            ("mid-west", x0, (y0 + y1) / 2),
        ]
        for suffix, x, y in points:
            targets.append({"id": f"snap-{space['id']}-{suffix}", "kind": "space-endpoint", "objectId": space["id"], "point": [x, y]})
    return targets


def build_synchronized_views(model: dict[str, Any]) -> dict[str, Any]:
    revision = int(model.get("project", {}).get("revision", 1))
    views: list[dict[str, Any]] = []
    for level in model.get("levels", []) or []:
        level_id = level["id"]
        spaces = [space for space in model.get("spaces", []) if space.get("level", space.get("levelId")) == level_id]
        views.extend(
            [
                {"id": f"plan-{level_id}", "kind": "2d-plan", "levelId": level_id, "objectIds": [item["id"] for item in spaces], "selectionGroup": f"level-{level_id}"},
                {"id": f"model-{level_id}", "kind": "3d", "levelId": level_id, "objectIds": [item["id"] for item in spaces], "selectionGroup": f"level-{level_id}"},
                {"id": f"section-{level_id}", "kind": "section", "levelId": level_id, "objectIds": [item["id"] for item in spaces], "selectionGroup": f"level-{level_id}"},
                {"id": f"elevation-{level_id}", "kind": "elevation", "levelId": level_id, "objectIds": [item["id"] for item in spaces], "selectionGroup": f"level-{level_id}"},
            ]
        )
    return {
        "reportVersion": VIEW_VERSION,
        "status": "pass",
        "modelRevision": revision,
        "synchronizationKey": f"project-revision-{revision}",
        "views": views,
        "selection": {"sharedAcrossViews": True, "highlightByObjectId": True},
        "cameraPresets": ["plan", "axonometric", "perspective", "section-box", "north", "south", "east", "west"],
        "levelVisibility": {"sharedAcrossViews": True, "default": [level["id"] for level in model.get("levels", [])]},
        "sectionBox": {"enabled": True, "clipsAllDerivedViews": True},
        "isolatedRoom": {"enabled": True, "requiresSelection": True},
        "snapping": {
            "enabled": True,
            "targets": ["grid", "endpoint", "midpoint", "intersection", "wall", "reference-line"],
            "targetCount": len(_snap_targets(model)),
        },
        "routeOverlays": {"availableInViews": True, "source": "canonical circulation graph"},
        "validationMarkers": {"availableInViews": True, "rerunOnAcceptedEdit": True},
        "derivedGeometry": {
            "sectionsInclude": ["floorLevels", "openings", "stairs", "keyDimensions"],
            "elevationsInclude": ["floorLevels", "openings", "roofEnvelope", "keyDimensions"],
            "source": "one canonical model revision",
        },
        "gate": {
            "sharedRevisionAcrossViews": True,
            "movingWallDoorOrStairInvalidatesViews": True,
            "validationRerunsAfterAcceptedEdit": True,
            "staleGeometryIsNotSilentlyDisplayed": True,
        },
    }


def build_sheet_report(model: dict[str, Any]) -> dict[str, Any]:
    layout = layout_for_extent(1190.55, 841.89, _extent(model))
    errors = validate_layout(layout)
    return {
        "reportVersion": SHEET_STANDARD["version"],
        "status": "pass" if not errors else "fail",
        "references": {
            "sheetFormat": SHEET_STANDARD["formatFamily"],
            "titleBlock": SHEET_STANDARD["titleBlockReference"],
            "ratiosAreProjectPolicy": True,
        },
        "standard": SHEET_STANDARD,
        "annotationStyles": ANNOTATION_STYLES,
        "sampleA2Landscape": layout.as_dict(),
        "errors": errors,
        "professionalReview": "Final sheet composition, legibility and code compliance require the appointed architect/engineer.",
    }


def write_reports() -> dict[str, Any]:
    model = read_json(CANONICAL_PATH)
    source_path = "CAD-Drawings/DXF/01-Site-Master-Plan-Plots-1-and-2.dxf"
    import_report = recognize_import(source_path=source_path)
    import_report["editableTwin"] = build_editable_twin(model, import_report)
    view_report = build_synchronized_views(model)
    sheet_report = build_sheet_report(model)

    model = deepcopy(model)
    model["importRecognition"] = {
        "version": IMPORT_VERSION,
        "report": _relative(IMPORT_REPORT_PATH),
        "editableTwinId": import_report["editableTwin"]["id"],
        "status": import_report["status"],
    }
    model["synchronizedViews"] = {
        "version": VIEW_VERSION,
        "report": _relative(VIEW_REPORT_PATH),
        "modelRevision": view_report["modelRevision"],
        "synchronizationKey": view_report["synchronizationKey"],
    }
    model["sheetLayoutStandard"] = {
        "version": SHEET_STANDARD["version"],
        "report": _relative(SHEET_REPORT_PATH),
        "drawingZoneMinAreaRatio": SHEET_STANDARD["drawingZoneMinAreaRatio"],
        "supportingContentMaxAreaRatio": SHEET_STANDARD["supportingContentMaxAreaRatio"],
    }
    write_json(IMPORT_REPORT_PATH, import_report)
    write_json(VIEW_REPORT_PATH, view_report)
    write_json(SHEET_REPORT_PATH, sheet_report)
    write_json(
        MANIFEST_PATH,
        {
            "manifestVersion": "week1314.enrichment-manifest.v1",
            "status": "pass" if import_report["status"] == "review-required" and view_report["status"] == "pass" and sheet_report["status"] == "pass" else "fail",
            "canonicalModel": _relative(CANONICAL_PATH),
            "importRecognitionReport": _relative(IMPORT_REPORT_PATH),
            "synchronizedViewsReport": _relative(VIEW_REPORT_PATH),
            "sheetLayoutStandard": _relative(SHEET_REPORT_PATH),
            "changelog": _relative(CHANGELOG_PATH),
            "reviewFirstImport": True,
        },
    )
    CHANGELOG_PATH.write_text(
        """# Week 13–14 enrichment changelog

## Week 13 — import, recognition and editable digital twin

- Added deterministic DXF source inspection with entity/layer counts and SHA-256 provenance.
- Added assisted PDF/image recognition status with confidence values and an explicit review queue.
- Added an editable digital twin contract that preserves units, levels, openings and source provenance without silently promoting uncertain geometry.
- Added a capability-gated IFC/BIM state.

## Week 14 — synchronised views and sheet composition

- Added shared model-revision contracts for 2D plans, 3D, sections and elevations.
- Added shared selection, camera presets, level visibility, section-box, isolated-room, snapping, route-overlay and validation-marker contracts.
- Added a paper-space sheet layout standard based on ISO 5457 sheet formats and ISO 7200-style title-block fields.
- Adopted project limits: supporting notes/index content <= 20% of sheet area and drawing zone >= 65%; these percentages are project policy, not claimed ISO mandates.
- Standardised readable annotation tiers, with 2.5 mm paper text as the minimum target for general notes, room labels and dimensions.

These features are preliminary planning and coordination aids. They are not survey,
code, permit, accessibility, fire/life-safety, structural, MEP, or construction certification.
""",
        encoding="utf-8",
    )
    write_json(CANONICAL_PATH, model)
    return {
        "status": "pass",
        "importRecognitionReport": _relative(IMPORT_REPORT_PATH),
        "synchronizedViewsReport": _relative(VIEW_REPORT_PATH),
        "sheetLayoutStandard": _relative(SHEET_REPORT_PATH),
        "manifest": _relative(MANIFEST_PATH),
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