#!/usr/bin/env python3
"""Week 22 adversarial architectural fixture foundation.

The fixture runner starts with one valid canonical planning model and applies
explicit, reviewable mutations to create defective cases. Each case carries
an expected rule, severity, affected objects, evidence fields, and correction.
The runner is intentionally deterministic and reports missing evidence as a
failed benchmark result rather than silently passing it.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "adversarial"
VALID_ROOT = FIXTURE_ROOT / "valid"
DEFECTIVE_ROOT = FIXTURE_ROOT / "defective"
REPORT_ROOT = ROOT / "bar-association-hall" / "standard"
REPORT_PATH = REPORT_ROOT / "week22-adversarial-foundation-report.json"

FIXTURE_SCHEMA_VERSION = "week22.adversarial-fixture.v1"
REPORT_VERSION = "week22.adversarial-foundation.v1"
SEVERITIES = {"BLOCKER", "ERROR", "WARNING"}


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


def signature(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _segments(path: str) -> list[str]:
    return [segment for segment in path.split(".") if segment]


def _get_path(value: Any, path: str) -> Any:
    current = value
    for segment in _segments(path):
        current = current[int(segment)] if isinstance(current, list) else current[segment]
    return current


def apply_mutation(model: dict[str, Any], mutation: dict[str, Any]) -> None:
    """Apply a small explicit set/remove/append mutation to a fixture model."""

    path = mutation["path"]
    operation = mutation.get("operation", "set")
    segments = _segments(path)
    if not segments:
        raise ValueError("mutation path cannot be empty")
    parent: Any = model
    for segment in segments[:-1]:
        parent = parent[int(segment)] if isinstance(parent, list) else parent[segment]
    leaf = segments[-1]
    if operation == "set":
        if isinstance(parent, list):
            parent[int(leaf)] = copy.deepcopy(mutation["value"])
        else:
            parent[leaf] = copy.deepcopy(mutation["value"])
    elif operation == "remove":
        if isinstance(parent, list):
            parent.pop(int(leaf))
        else:
            parent.pop(leaf, None)
    elif operation == "append":
        target = parent[int(leaf)] if isinstance(parent, list) else parent[leaf]
        target.append(copy.deepcopy(mutation["value"]))
    else:
        raise ValueError(f"unsupported mutation operation: {operation}")


def load_fixture(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    fixture = read_json(path)
    if fixture.get("schemaVersion") != FIXTURE_SCHEMA_VERSION:
        raise ValueError(f"{path}: unsupported schemaVersion")
    source_path = (path.parent / str(fixture["sourceFixture"])).resolve()
    if not source_path.is_file():
        raise ValueError(f"{path}: source fixture does not exist: {source_path}")
    model = read_json(source_path)
    for mutation in fixture.get("mutations", []):
        apply_mutation(model, mutation)
    return fixture, model


def _finding(
    rule_id: str,
    affected_objects: list[str],
    evidence: dict[str, Any],
    correction: str,
) -> dict[str, Any]:
    return {
        "ruleId": rule_id,
        "severity": "BLOCKER",
        "affectedObjects": affected_objects,
        "evidence": evidence,
        "suggestedCorrection": correction,
    }


def detect_findings(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect the Week 22 defect families from the mutated planning model."""

    findings: list[dict[str, Any]] = []
    spaces = list(model.get("spaces") or [])
    openings = list(model.get("openings") or [])
    window_hosts = {str(item.get("hostSpace")) for item in model.get("windows", []) if item.get("hostSpace")}
    opening_hosts = {str(item.get("hostSpace")) for item in openings if item.get("hostSpace")}

    for route in model.get("routes", []):
        if route.get("connected") is False:
            findings.append(
                _finding(
                    "ACCESS.ROUTE.CONTINUITY",
                    [str(route.get("spaceId")), str(route.get("id"))],
                    {"spaceId": route.get("spaceId"), "routeId": route.get("id"), "connected": False},
                    "Connect the room to a valid internal route from an entry or vertical connector.",
                )
            )

    for opening in openings:
        opening_id = str(opening.get("id"))
        if opening.get("opensInto") == "wall":
            findings.append(
                _finding(
                    "OPENING.WALL.INTERSECTION",
                    [opening_id, str(opening.get("hostSpace"))],
                    {"openingId": opening_id, "opensInto": "wall"},
                    "Move the opening to a real wall break and verify both sides of the opening.",
                )
            )
        if opening.get("sideBKind") in {"private-room", "locked-room"}:
            findings.append(
                _finding(
                    "OPENING.PRIVATE.ACCESS",
                    [opening_id, str(opening.get("hostSpace"))],
                    {"openingId": opening_id, "sideBKind": opening.get("sideBKind")},
                    "Connect the room to a public or circulation space, not through a private or locked room.",
                )
            )
        if opening.get("swingConflict") is True:
            findings.append(
                _finding(
                    "OPENING.SWING.CLEARANCE",
                    [opening_id, str(opening.get("hostSpace"))],
                    {"openingId": opening_id, "swingConflict": True},
                    "Reverse or relocate the door swing so the route and required clearance remain usable.",
                )
            )
        if opening.get("external") is True and opening.get("landing") is not True:
            findings.append(
                _finding(
                    "OPENING.EXTERNAL.LANDING",
                    [opening_id, str(opening.get("hostSpace"))],
                    {"openingId": opening_id, "external": True, "landing": opening.get("landing")},
                    "Add an intentional porch, balcony, stair, ramp, or landing for the external door.",
                )
            )

    for space in spaces:
        if space.get("requiresDoor") and str(space.get("id")) not in opening_hosts:
            findings.append(
                _finding(
                    "ACCESS.SERVING.DOOR",
                    [str(space.get("id"))],
                    {"spaceId": space.get("id"), "servingDoor": False},
                    "Add a serving door that connects the room to a valid circulation or exterior access path.",
                )
            )
        if space.get("requiresDaylight") and str(space.get("id")) not in window_hosts:
            findings.append(
                _finding(
                    "DAYLIGHT.OPENINGS",
                    [str(space.get("id"))],
                    {"spaceId": space.get("id"), "windowCount": 0},
                    "Provide a compliant daylight opening or record an approved alternative strategy.",
                )
            )
        if space.get("requiresVentilation") and str(space.get("id")) not in window_hosts:
            findings.append(
                _finding(
                    "VENTILATION.OPENINGS",
                    [str(space.get("id"))],
                    {"spaceId": space.get("id"), "windowCount": 0},
                    "Provide a compliant ventilation opening or record a designed mechanical strategy.",
                )
            )

    for furniture in model.get("furniture", []):
        if furniture.get("blocksRoute") is True:
            findings.append(
                _finding(
                    "FURNITURE.ROUTE.CLEARANCE",
                    [str(furniture.get("id")), str(furniture.get("spaceId"))],
                    {"furnitureId": furniture.get("id"), "blocksRoute": True},
                    "Relocate or resize the furniture so the required route and clearances remain open.",
                )
            )

    for stair in model.get("stairs", []):
        if stair.get("landing") is not True:
            findings.append(
                _finding(
                    "STAIR.LANDING.REQUIRED",
                    [str(stair.get("id"))],
                    {"stairId": stair.get("id"), "landing": stair.get("landing")},
                    "Add and dimension a valid landing at the stair approach and discharge.",
                )
            )

    for connector in model.get("verticalConnectors", []):
        if connector.get("connected") is False:
            findings.append(
                _finding(
                    "ACCESS.VERTICAL.CONTINUITY",
                    [str(connector.get("id"))],
                    {
                        "connectorId": connector.get("id"),
                        "fromLevel": connector.get("fromLevel"),
                        "toLevel": connector.get("toLevel"),
                        "connected": False,
                    },
                    "Connect the vertical connector to valid routes on both levels.",
                )
            )

    site = model.get("site") or {}
    if (site.get("fireAccess") or {}).get("status") != "verified":
        findings.append(
            _finding(
                "SITE.FIRE.ACCESS",
                ["site.fireAccess"],
                {"fireAccess": site.get("fireAccess")},
                "Provide verified fire-appliance access, turning, approach, and discharge geometry.",
            )
        )
    if (site.get("serviceAccess") or {}).get("status") != "verified":
        findings.append(
            _finding(
                "SITE.SERVICE.ACCESS",
                ["site.serviceAccess"],
                {"serviceAccess": site.get("serviceAccess")},
                "Provide a deliberate service entry, route, loading point, and service-zone geometry.",
            )
        )

    plot = site.get("plotBounds") or [0, 0, 0, 0]
    envelope = site.get("buildingEnvelope") or [0, 0, 0, 0]
    setbacks = site.get("setbacks") or {}
    margins = {
        "west": envelope[0] - plot[0],
        "east": plot[2] - envelope[2],
        "south": envelope[1] - plot[1],
        "north": plot[3] - envelope[3],
    }
    if any(margins.get(side, 0) < float(setbacks.get(side, 0)) for side in ("north", "south", "east", "west")):
        findings.append(
            _finding(
                "SITE.SETBACKS",
                ["site.buildingEnvelope"],
                {"plotBounds": plot, "buildingEnvelope": envelope, "setbacks": setbacks, "margins": margins},
                "Move the building envelope inside the required setbacks and confirm the rule pack.",
            )
        )

    for wet_area in model.get("wetAreas", []):
        if (wet_area.get("coordination") or {}).get("status") != "verified":
            findings.append(
                _finding(
                    "WET-AREA.COORDINATION",
                    [str(wet_area.get("id")), str(wet_area.get("spaceId"))],
                    {"wetAreaId": wet_area.get("id"), "coordination": wet_area.get("coordination")},
                    "Coordinate shafts, drainage, falls, waterproofing, ventilation, and the MEP layout.",
                )
            )

    return findings


def _validate_expected(fixture: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any]:
    expected = fixture.get("expectedFinding") or {}
    required = ("ruleId", "severity", "affectedObjects", "evidenceFields", "correction")
    missing = [field for field in required if field not in expected]
    matching = [item for item in findings if item.get("ruleId") == expected.get("ruleId")]
    actual = matching[0] if matching else None
    errors: list[str] = []
    if missing:
        errors.extend(f"expectedFinding missing {field}" for field in missing)
    if actual is None:
        errors.append(f"expected rule was not detected: {expected.get('ruleId')}")
    else:
        if actual.get("severity") != expected.get("severity"):
            errors.append("detected severity does not match expected severity")
        if not set(expected.get("affectedObjects", [])).issubset(set(actual.get("affectedObjects", []))):
            errors.append("detected affected objects do not include expected objects")
        if not set(expected.get("evidenceFields", [])).issubset(set(actual.get("evidence", {}))):
            errors.append("detected evidence is missing expected fields")
        if not actual.get("suggestedCorrection") or not expected.get("correction"):
            errors.append("finding and contract must both include a suggested correction")
    unexpected = [item for item in findings if item.get("ruleId") != expected.get("ruleId")]
    if unexpected:
        errors.append("fixture produced unexpected additional findings")
    return {
        "status": "PASS" if not errors else "FAIL",
        "fixtureId": fixture.get("fixtureId"),
        "expectedRuleId": expected.get("ruleId"),
        "actualRuleId": actual.get("ruleId") if actual else None,
        "severity": actual.get("severity") if actual else expected.get("severity"),
        "affectedObjects": actual.get("affectedObjects", []) if actual else [],
        "evidence": actual.get("evidence", {}) if actual else {},
        "suggestedCorrection": actual.get("suggestedCorrection") if actual else None,
        "errors": errors,
    }


def run_fixture(path: Path) -> dict[str, Any]:
    fixture, model = load_fixture(path)
    findings = detect_findings(model)
    result = _validate_expected(fixture, findings)
    result["sourceFixture"] = fixture.get("sourceFixture")
    result["fixturePath"] = str(path.relative_to(ROOT))
    result["findingCount"] = len(findings)
    return result


def discover_fixtures() -> list[Path]:
    return sorted(DEFECTIVE_ROOT.glob("ADV-*.json"))


def run_benchmark() -> dict[str, Any]:
    fixture_paths = discover_fixtures()
    if not fixture_paths:
        raise ValueError("no adversarial fixtures found")
    results = [run_fixture(path) for path in fixture_paths]
    valid_model = read_json(VALID_ROOT / "baseline.json")
    valid_findings = detect_findings(valid_model)
    passed = sum(result["status"] == "PASS" for result in results)
    total = len(results)
    return {
        "fixtureCount": total,
        "validSourceFixtures": 1,
        "criticalFixtures": total,
        "criticalDefectsDetected": passed,
        "criticalDefectsMissed": total - passed,
        "dangerousFalseNegatives": total - passed,
        "completeFindings": sum(
            result["status"] == "PASS"
            and bool(result["evidence"])
            and bool(result["suggestedCorrection"])
            for result in results
        ),
        "falsePositiveCount": len(valid_findings),
        "validBaselineFindingCount": len(valid_findings),
        "results": results,
    }


def build_report() -> dict[str, Any]:
    benchmark = run_benchmark()
    status = "PASS" if (
        benchmark["criticalDefectsMissed"] == 0
        and benchmark["dangerousFalseNegatives"] == 0
        and benchmark["completeFindings"] == benchmark["criticalFixtures"]
        and benchmark["falsePositiveCount"] == 0
    ) else "FAIL"
    report: dict[str, Any] = {
        "version": REPORT_VERSION,
        "fixtureSchemaVersion": FIXTURE_SCHEMA_VERSION,
        "status": status,
        "sourceFixture": "tests/fixtures/adversarial/valid/baseline.json",
        "benchmark": {
            key: benchmark[key]
            for key in (
                "fixtureCount",
                "validSourceFixtures",
                "criticalFixtures",
                "criticalDefectsDetected",
                "criticalDefectsMissed",
                "dangerousFalseNegatives",
                "completeFindings",
                "falsePositiveCount",
            )
        },
        "results": benchmark["results"],
        "validBaseline": {"findingCount": benchmark["validBaselineFindingCount"]},
        "acceptance": {
            "allFixturesHaveExpectedContracts": status == "PASS",
            "criticalDefectRecall": (
                benchmark["criticalDefectsDetected"] / benchmark["criticalFixtures"]
                if benchmark["criticalFixtures"]
                else None
            ),
            "zeroDangerousFalseNegatives": benchmark["dangerousFalseNegatives"] == 0,
            "everyFindingHasEvidenceAndCorrection": (
                benchmark["completeFindings"] == benchmark["criticalFixtures"]
            ),
        },
        "professionalReviewRequired": True,
        "reportSignature": None,
    }
    report["reportSignature"] = signature(
        {key: value for key, value in report.items() if key != "reportSignature"}
    )
    return report


def write_report() -> dict[str, Any]:
    report = build_report()
    write_json(REPORT_PATH, report)
    return report


def validate_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("version", "fixtureSchemaVersion", "status", "benchmark", "results", "reportSignature"):
        if field not in report:
            errors.append(f"missing report field: {field}")
    if report.get("status") not in {"PASS", "FAIL"}:
        errors.append("report status must be PASS or FAIL")
    if report.get("reportSignature"):
        expected = signature({key: value for key, value in report.items() if key != "reportSignature"})
        if report["reportSignature"] != expected:
            errors.append("reportSignature does not match report contents")
    expected_count = report.get("benchmark", {}).get("fixtureCount")
    if expected_count != len(report.get("results", [])):
        errors.append("benchmark fixtureCount does not match result count")
    if any(result.get("status") != "PASS" for result in report.get("results", [])):
        errors.append("one or more adversarial fixtures failed its expected contract")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("report", "validate"))
    args = parser.parse_args(argv)
    if args.command == "report":
        report = write_report()
        print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
        print(f"fixtures: {report['benchmark']['fixtureCount']}")
        print(f"status: {report['status']}")
        return 0 if report["status"] == "PASS" else 1
    report = read_json(REPORT_PATH)
    errors = validate_report(report)
    print(report.get("status", "INVALID"))
    for error in errors:
        print(error)
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())