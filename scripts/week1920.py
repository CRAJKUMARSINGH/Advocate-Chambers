#!/usr/bin/env python3
"""Week 19–20 archive integrity and revision operations.

Week 19 makes project storage inspectable without moving or deleting legacy
files.  It produces a manifest-first archive plan with real SHA-256 hashes
for files that exist and explicit ``missing`` records for files that still
need migration.  Week 20 adds deterministic revision records, soft archive
and restore operations, and verification of a complete project package.

These are storage and coordination contracts, not a replacement for a
database, object store, access-control system, or construction approval.
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
WEEK17_REPORT_PATH = REPORT_ROOT / "week17-site-feasibility-report.json"
WEEK18_REPORT_PATH = REPORT_ROOT / "week18-delivery-package-report.json"
WEEK19_REPORT_PATH = REPORT_ROOT / "week19-archive-integrity-report.json"
WEEK20_REPORT_PATH = REPORT_ROOT / "week20-revision-operations-report.json"
MANIFEST_PATH = REPORT_ROOT / "week1920-archive-manifest.json"
CHANGELOG_PATH = REPORT_ROOT / "week1920-changelog.md"

WEEK19_VERSION = "week19.project-archive.v1"
WEEK20_VERSION = "week20.revision-operations.v1"
ARCHIVE_LAYOUT_VERSION = "projects/2026/{project-slug}"
ARCHIVE_ARTIFACT_PATHS = (
    "bar-association-hall/standard/model/project.json",
    "bar-association-hall/standard/rule-packs/india-preliminary-review.v1.json",
    "bar-association-hall/standard/week17-site-feasibility-report.json",
    "bar-association-hall/standard/week18-delivery-package-report.json",
    "bar-association-hall/standard/week1718-enrichment-manifest.json",
    "bar-association-hall/standard/week1718-changelog.md",
)
ARCHIVEABLE_SUFFIXES = {
    ".dxf",
    ".ifc",
    ".glb",
    ".gltf",
    ".jpg",
    ".jpeg",
    ".pdf",
    ".png",
    ".pptx",
    ".webp",
    ".xlsx",
    ".zip",
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


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def signature(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project(model: dict[str, Any]) -> dict[str, Any]:
    project = model.get("project")
    if not isinstance(project, dict) or not project.get("id"):
        raise ValueError("model.project.id is required")
    return project


def _revision(model: dict[str, Any]) -> int:
    value = _project(model).get("revision")
    if not isinstance(value, int) or value < 0:
        raise ValueError("model.project.revision must be a non-negative integer")
    return value


def _slug(project_id: str) -> str:
    slug = "".join(character if character.isalnum() or character in "-_" else "-" for character in project_id.lower())
    return slug.strip("-") or "project"


def _validation_summary(report: dict[str, Any] | None) -> dict[str, Any]:
    results = report.get("results", []) if isinstance(report, dict) else []
    if not isinstance(results, list):
        results = []
    counts = {"pass": 0, "fail": 0, "unknown": 0, "professional-review": 0}
    blockers: list[str] = []
    for result in results:
        if not isinstance(result, dict):
            continue
        status = str(result.get("status", "unknown"))
        if status in counts:
            counts[status] += 1
        if result.get("severity") in {"BLOCKER", "ERROR"} or status == "fail":
            if result.get("ruleId"):
                blockers.append(str(result["ruleId"]))
    return {
        "counts": counts,
        "blockers": sorted(set(blockers)),
        "professionalReviewRequired": bool(
            counts["unknown"] or counts["professional-review"] or (report or {}).get("dashboard", {}).get("professionalReviewRequired")
        ),
    }


def _artifact_kind(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if path.endswith("project.json"):
        return "source-json"
    if "rule-packs/" in path:
        return "rule-pack"
    if "validation" in path or "feasibility" in path:
        return "validation-report"
    if suffix in ARCHIVEABLE_SUFFIXES:
        return suffix[1:]
    return "text-contract"


def artifact_record(
    path: str,
    *,
    root: Path = ROOT,
    project_id: str,
    revision: int,
    validation_status: str = "preliminary-review",
) -> dict[str, Any]:
    """Create a real or explicitly missing artifact record."""

    relative = Path(path)
    absolute = relative if relative.is_absolute() else root / relative
    exists = absolute.is_file()
    record: dict[str, Any] = {
        "artifactId": f"art-{_slug(project_id)}-r{revision:03d}-{signature(path)[:10]}",
        "projectId": project_id,
        "revisionId": f"r{revision:03d}",
        "kind": _artifact_kind(path),
        "path": path,
        "bytes": absolute.stat().st_size if exists else None,
        "sha256": sha256_file(absolute) if exists else None,
        "generatedAt": None,
        "validationStatus": validation_status,
        "status": "verified" if exists else "missing",
    }
    if not exists:
        record["reviewNote"] = "Destination artifact is not present; migration must supply it before issue."
    return record


def build_archive_manifest(
    model: dict[str, Any],
    *,
    artifact_paths: Iterable[str] = ARCHIVE_ARTIFACT_PATHS,
    root: Path = ROOT,
    validation_report: dict[str, Any] | None = None,
    rule_pack_version: str | None = None,
) -> dict[str, Any]:
    """Build a manifest without mutating the source model or filesystem."""

    project = _project(model)
    revision = _revision(model)
    project_id = str(project["id"])
    slug = _slug(project_id)
    paths = sorted(set(str(path) for path in artifact_paths))
    artifacts = [
        artifact_record(
            path,
            root=root,
            project_id=project_id,
            revision=revision,
        )
        for path in paths
    ]
    source_record = next((item for item in artifacts if item["path"].endswith("/model/project.json")), None)
    validation = _validation_summary(validation_report)
    manifest: dict[str, Any] = {
        "version": WEEK19_VERSION,
        "layoutVersion": ARCHIVE_LAYOUT_VERSION,
        "project": {
            "id": project_id,
            "slug": slug,
            "name": project.get("name", project_id),
            "units": model.get("units", project.get("units", "inch")),
            "revision": revision,
        },
        "archive": {
            "root": f"projects/2026/{slug}/",
            "current": f"projects/2026/{slug}/current.json",
            "revision": f"projects/2026/{slug}/revisions/r{revision:03d}/",
            "mode": "manifest-first",
            "legacyPathsRetained": True,
            "destructiveCleanup": False,
        },
        "sourceModel": {
            "path": "bar-association-hall/standard/model/project.json",
            "revision": revision,
            "sha256": source_record["sha256"] if source_record else None,
        },
        "rulePackVersion": rule_pack_version,
        "validation": validation,
        "artifacts": artifacts,
        "integrity": {
            "status": "pass" if all(item["status"] == "verified" for item in artifacts) else "incomplete",
            "verifiedCount": sum(item["status"] == "verified" for item in artifacts),
            "missingCount": sum(item["status"] == "missing" for item in artifacts),
            "hashAlgorithm": "sha256",
        },
        "migration": {
            "status": "review-required",
            "legacySourcePaths": ["bar-association-hall", "CAD-Drawings", "Jamuniya-Shaktawat"],
            "nextAction": "review destination paths and hashes before any separate cleanup change",
        },
        "manifestSignature": None,
    }
    manifest["manifestSignature"] = signature(
        {key: value for key, value in manifest.items() if key != "manifestSignature"}
    )
    return manifest


def validate_archive_manifest(manifest: dict[str, Any]) -> list[str]:
    """Return precise integrity errors; an empty list means the contract is valid."""

    errors: list[str] = []
    for required in ("version", "project", "archive", "sourceModel", "artifacts", "integrity", "manifestSignature"):
        if required not in manifest:
            errors.append(f"missing top-level field: {required}")
    project = manifest.get("project", {})
    if not project.get("id"):
        errors.append("project.id is required")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("artifacts must be a non-empty list")
        artifacts = []
    paths: set[str] = set()
    ids: set[str] = set()
    for index, item in enumerate(artifacts):
        if not isinstance(item, dict):
            errors.append(f"artifacts[{index}] must be an object")
            continue
        path = item.get("path")
        artifact_id = item.get("artifactId")
        if not path:
            errors.append(f"artifacts[{index}].path is required")
        elif path in paths:
            errors.append(f"duplicate artifact path: {path}")
        else:
            paths.add(path)
        if not artifact_id:
            errors.append(f"artifacts[{index}].artifactId is required")
        elif artifact_id in ids:
            errors.append(f"duplicate artifact ID: {artifact_id}")
        else:
            ids.add(artifact_id)
        status = item.get("status")
        if status not in {"verified", "missing"}:
            errors.append(f"artifacts[{index}].status must be verified or missing")
        if status == "verified" and (not item.get("sha256") or not isinstance(item.get("bytes"), int)):
            errors.append(f"artifacts[{index}] verified records require bytes and sha256")
        if status == "missing" and item.get("sha256") is not None:
            errors.append(f"artifacts[{index}] missing record cannot carry a hash")
    expected = signature({key: value for key, value in manifest.items() if key != "manifestSignature"})
    if manifest.get("manifestSignature") != expected:
        errors.append("manifestSignature does not match manifest contents")
    return errors


def create_revision_record(
    model: dict[str, Any],
    *,
    author: str,
    reason: str,
    validation_report: dict[str, Any] | None = None,
    parent_revision: int | None = None,
    artifact_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create an immutable revision descriptor from the authoritative model."""

    if not author.strip():
        raise ValueError("author must not be empty")
    if not reason.strip():
        raise ValueError("reason must not be empty")
    revision = _revision(model)
    if parent_revision is not None and parent_revision >= revision:
        raise ValueError("parent_revision must be lower than the new revision")
    report_summary = _validation_summary(validation_report)
    record: dict[str, Any] = {
        "version": WEEK20_VERSION,
        "revisionId": f"r{revision:03d}",
        "projectId": str(_project(model)["id"]),
        "revision": revision,
        "parentRevision": parent_revision,
        "author": author.strip(),
        "reason": reason.strip(),
        "modelSignature": signature(model),
        "validation": report_summary,
        "artifactManifestSignature": (artifact_manifest or {}).get("manifestSignature"),
        "status": "review-required" if report_summary["professionalReviewRequired"] else "ready-for-review",
        "immutable": True,
    }
    record["recordSignature"] = signature({key: value for key, value in record.items() if key != "recordSignature"})
    return record


def archive_project_state(
    state: dict[str, Any],
    *,
    author: str,
    reason: str,
) -> dict[str, Any]:
    """Soft archive a project while keeping all revisions recoverable."""

    if not author.strip() or not reason.strip():
        raise ValueError("author and reason are required")
    result = copy.deepcopy(state)
    project = result.setdefault("project", {})
    if not project.get("id"):
        raise ValueError("state.project.id is required")
    if project.get("archived"):
        return result
    project["archived"] = True
    project["archiveAction"] = {
        "kind": "soft-archive",
        "author": author.strip(),
        "reason": reason.strip(),
    }
    project["archivePolicy"] = "retain-source-and-revisions"
    return result


def restore_project_state(state: dict[str, Any], *, author: str, reason: str) -> dict[str, Any]:
    """Restore a soft-archived project without changing its current revision."""

    if not author.strip() or not reason.strip():
        raise ValueError("author and reason are required")
    result = copy.deepcopy(state)
    project = result.setdefault("project", {})
    if not project.get("id"):
        raise ValueError("state.project.id is required")
    project["archived"] = False
    project["archiveAction"] = {
        "kind": "restore",
        "author": author.strip(),
        "reason": reason.strip(),
    }
    return result


def verify_project_package(
    manifest: dict[str, Any],
    *,
    require_complete: bool = True,
) -> dict[str, Any]:
    """Verify contract shape and report missing artifacts without guessing."""

    errors = validate_archive_manifest(manifest)
    missing = [item["path"] for item in manifest.get("artifacts", []) if item.get("status") == "missing"]
    if require_complete and missing:
        errors.append(f"{len(missing)} artifact(s) are missing from the package")
    return {
        "version": "week20.package-verification.v1",
        "status": "pass" if not errors else "blocked",
        "errors": errors,
        "missingArtifacts": missing,
        "verifiedArtifacts": [
            item["path"] for item in manifest.get("artifacts", []) if item.get("status") == "verified"
        ],
        "requiresCompletePackage": require_complete,
        "destructiveCleanupAllowed": False,
    }


def enrichment_report(model: dict[str, Any]) -> dict[str, Any]:
    manifest = build_archive_manifest(model)
    revision = create_revision_record(
        model,
        author="architectural-pipeline",
        reason="Week 19–20 archive and revision enrichment",
        artifact_manifest=manifest,
    )
    return {
        "version": "week1920.enrichment.v1",
        "week19": {
            "version": WEEK19_VERSION,
            "manifest": manifest,
            "policy": {
                "legacyPathsRetained": True,
                "duplicateCleanupRequiresSeparateApproval": True,
                "hashAlgorithm": "sha256",
            },
        },
        "week20": {
            "version": WEEK20_VERSION,
            "revisionRecord": revision,
            "operations": ["create-revision", "soft-archive", "restore", "verify-package"],
            "releaseStatus": "review-required",
        },
        "professionalReviewRequired": True,
        "destructiveCleanup": "intentionally untouched",
    }


def write_reports() -> dict[str, Any]:
    model = read_json(CANONICAL_PATH)
    week17_report = read_json(WEEK17_REPORT_PATH) if WEEK17_REPORT_PATH.exists() else None
    manifest = build_archive_manifest(
        model,
        validation_report=week17_report,
        rule_pack_version="india-preliminary-review@1.0.0",
    )
    week19 = {
        "version": WEEK19_VERSION,
        "manifestPath": str(MANIFEST_PATH.relative_to(ROOT)),
        "manifestSignature": manifest["manifestSignature"],
        "integrity": manifest["integrity"],
        "migration": manifest["migration"],
        "professionalReviewRequired": True,
    }
    week20_revision = create_revision_record(
        model,
        author="architectural-pipeline",
        reason="Week 19–20 archive and revision enrichment",
        validation_report=week17_report,
        artifact_manifest=manifest,
    )
    week20 = {
        "version": WEEK20_VERSION,
        "revisionRecord": week20_revision,
        "packageVerification": verify_project_package(manifest, require_complete=False),
        "operations": {
            "softArchive": "available",
            "restore": "available",
            "currentRevisionPreservedOnRestore": True,
        },
        "professionalReviewRequired": True,
        "destructiveCleanup": "intentionally untouched",
    }
    write_json(WEEK19_REPORT_PATH, week19)
    write_json(WEEK20_REPORT_PATH, week20)
    # Rebuild after the reports exist so their hashes are included.
    manifest = build_archive_manifest(
        model,
        validation_report=week17_report,
        rule_pack_version="india-preliminary-review@1.0.0",
    )
    write_json(MANIFEST_PATH, manifest)
    CHANGELOG_PATH.write_text(
        "# Week 19–20 architectural enrichment\n\n"
        "- Added a manifest-first archive contract with SHA-256 artifact records.\n"
        "- Added deterministic revision records and package verification.\n"
        "- Added non-destructive soft archive and restore state transitions.\n"
        "- Kept legacy paths and the separate binary cleanup untouched.\n",
        encoding="utf-8",
    )
    return {"week19": week19, "week20": week20, "manifest": manifest}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("report", "validate"))
    args = parser.parse_args(argv)
    if args.command == "report":
        write_reports()
        print(f"wrote {WEEK19_REPORT_PATH.relative_to(ROOT)}")
        print(f"wrote {WEEK20_REPORT_PATH.relative_to(ROOT)}")
        print(f"wrote {MANIFEST_PATH.relative_to(ROOT)}")
        return 0
    model = read_json(CANONICAL_PATH)
    report = enrichment_report(model)
    errors = validate_archive_manifest(report["week19"]["manifest"])
    print("pass" if not errors else "fail")
    for error in errors:
        print(error)
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())