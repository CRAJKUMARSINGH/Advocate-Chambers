#!/usr/bin/env python3
"""Week 1 validation, regression-report, and artifact-integrity commands.

This script intentionally uses only the Python standard library. It can run in
a clean checkout before CAD/PDF rendering dependencies are installed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT / "bar-association-hall"
SOURCE_ROOT = MODEL_ROOT / "standard" / "source"
REPORT_PATH = MODEL_ROOT / "standard" / "week1-validation-report.json"
MANIFEST_PATH = MODEL_ROOT / "standard" / "regression_manifest.json"

sys.path.insert(0, str(MODEL_ROOT))
from drawing_model import load_model, validate_model_findings  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validation_report() -> dict[str, Any]:
    site, plans = load_model()
    findings = validate_model_findings(site, plans)
    counts: dict[str, int] = {}
    for finding in findings:
        severity = finding["severity"]
        counts[severity] = counts.get(severity, 0) + 1
    blocking = [finding for finding in findings if finding["severity"] in {"BLOCKER", "ERROR"}]
    return {
        "reportVersion": "week1.validation.v1",
        "projectId": plans.get("projectId"),
        "source": {
            "site": str((SOURCE_ROOT / "site_plan.json").relative_to(ROOT)),
            "plans": str((SOURCE_ROOT / "preliminary_plans.json").relative_to(ROOT)),
        },
        "status": "pass" if not blocking else "fail",
        "findingCounts": counts,
        "findings": findings,
        "checkedObjects": {
            "spaces": len(plans.get("spaces", [])),
            "openings": len(plans.get("openings", [])),
            "windows": len(plans.get("windows", [])),
            "stairs": len(plans.get("stairs", [])),
        },
        "policy": {
            "issueReadyOutputAllowed": not blocking,
            "professionalStatus": "PRELIMINARY / NOT FOR CONSTRUCTION",
        },
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def run_validate(write_report: bool) -> int:
    report = validation_report()
    if write_report:
        write_json(REPORT_PATH, report)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


def artifact_files() -> list[Path]:
    files: list[Path] = []
    for directory in (MODEL_ROOT / "PDF", MODEL_ROOT / "CAD"):
        if directory.exists():
            files.extend(path for path in directory.rglob("*") if path.is_file())
    return sorted(files)


def build_manifest() -> dict[str, Any]:
    source_files = [
        SOURCE_ROOT / "site_plan.json",
        SOURCE_ROOT / "preliminary_plans.json",
    ]
    artifacts = []
    for path in artifact_files():
        artifacts.append(
            {
                "path": str(path.relative_to(ROOT)),
                "kind": path.suffix.lower().lstrip(".") or "file",
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    return {
        "manifestVersion": "week1.regression.v1",
        "projectId": "bar-association-hall",
        "fixture": {
            "id": "bar-association-hall-week1-baseline",
            "policy": "Source hashes are the golden fixture. Any intentional model change requires a new revision.",
            "source": [
                {
                    "path": str(path.relative_to(ROOT)),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
                for path in source_files
            ],
            "expectedValidationStatus": "fail",
            "requiredBaselineRule": "ROOM_HAS_UNJUSTIFIED_EXTERNAL_DOOR",
        },
        "validationReport": str(REPORT_PATH.relative_to(ROOT)),
        "artifactRoots": ["bar-association-hall/PDF", "bar-association-hall/CAD"],
        "artifacts": artifacts,
        "notes": [
            "Legacy paths remain untouched during Week 1.",
            "Hashes verify identity; they do not replace backups or Git LFS.",
            "PRELIMINARY / NOT FOR CONSTRUCTION is the only issue status for this baseline.",
        ],
    }


def run_manifest(write_manifest: bool) -> int:
    manifest = build_manifest()
    if write_manifest:
        write_json(MANIFEST_PATH, manifest)
    print(json.dumps(manifest, indent=2))
    return 0


def run_verify_manifest() -> int:
    if not MANIFEST_PATH.exists():
        print(json.dumps({"status": "fail", "error": f"missing {MANIFEST_PATH.relative_to(ROOT)}"}))
        return 1
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    mismatches: list[dict[str, Any]] = []
    for record in manifest.get("fixture", {}).get("source", []):
        path = ROOT / record["path"]
        if not path.exists():
            mismatches.append({"path": record["path"], "reason": "missing"})
            continue
        actual = {"bytes": path.stat().st_size, "sha256": sha256(path)}
        expected = {"bytes": record["bytes"], "sha256": record["sha256"]}
        if actual != expected:
            mismatches.append({"path": record["path"], "expected": expected, "actual": actual})
    for record in manifest.get("artifacts", []):
        path = ROOT / record["path"]
        if not path.exists():
            mismatches.append({"path": record["path"], "reason": "missing"})
            continue
        actual = {"bytes": path.stat().st_size, "sha256": sha256(path)}
        expected = {"bytes": record["bytes"], "sha256": record["sha256"]}
        if actual != expected:
            mismatches.append({"path": record["path"], "expected": expected, "actual": actual})
    result = {
        "status": "pass" if not mismatches else "fail",
        "manifest": str(MANIFEST_PATH.relative_to(ROOT)),
        "checkedSources": len(manifest.get("fixture", {}).get("source", [])),
        "checkedArtifacts": len(manifest.get("artifacts", [])),
        "mismatches": mismatches,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="emit the Week 1 JSON validation report")
    validate_parser.add_argument("--write-report", action="store_true", help=f"write {REPORT_PATH.relative_to(ROOT)}")

    manifest_parser = subparsers.add_parser("manifest", help="compute the baseline source and artifact manifest")
    manifest_parser.add_argument("--write", action="store_true", help=f"write {MANIFEST_PATH.relative_to(ROOT)}")

    subparsers.add_parser("verify-manifest", help="verify all recorded source and artifact hashes")
    args = parser.parse_args()

    if args.command == "validate":
        return run_validate(args.write_report)
    if args.command == "manifest":
        return run_manifest(args.write)
    return run_verify_manifest()


if __name__ == "__main__":
    raise SystemExit(main())