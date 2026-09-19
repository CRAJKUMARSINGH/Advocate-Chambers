import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from week1920 import (  # noqa: E402
    archive_project_state,
    build_archive_manifest,
    create_revision_record,
    restore_project_state,
    validate_archive_manifest,
    verify_project_package,
)


def model_fixture():
    return {
        "project": {"id": "proj-advocate-chambers", "name": "Advocate Chambers", "revision": 4},
        "units": "inch",
        "spaces": [{"id": "GF-01", "levelId": "GF", "geometry": {"rect": [0, 0, 100, 100]}}],
    }


class Week1920EnrichmentTests(unittest.TestCase):
    def test_manifest_hashes_real_files_and_marks_missing_without_guessing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "bar-association-hall/standard/model/project.json"
            source.parent.mkdir(parents=True)
            source.write_text(json.dumps(model_fixture()), encoding="utf-8")
            manifest = build_archive_manifest(
                model_fixture(),
                root=root,
                artifact_paths=("bar-association-hall/standard/model/project.json", "missing/report.pdf"),
            )
            source_record = next(item for item in manifest["artifacts"] if item["path"].endswith("project.json"))
            missing_record = next(item for item in manifest["artifacts"] if item["path"] == "missing/report.pdf")
            self.assertEqual(source_record["status"], "verified")
            self.assertEqual(len(source_record["sha256"]), 64)
            self.assertEqual(missing_record["status"], "missing")
            self.assertIsNone(missing_record["sha256"])
            self.assertEqual(validate_archive_manifest(manifest), [])

    def test_manifest_tampering_is_blocked(self):
        manifest = build_archive_manifest(model_fixture(), artifact_paths=("README.md",))
        manifest["project"]["revision"] = 99
        errors = validate_archive_manifest(manifest)
        self.assertIn("manifestSignature does not match manifest contents", errors)

    def test_revision_record_is_deterministic_and_immutable(self):
        first = create_revision_record(
            model_fixture(),
            author="architect",
            reason="Coordinate archive contract",
            parent_revision=3,
        )
        second = create_revision_record(
            model_fixture(),
            author="architect",
            reason="Coordinate archive contract",
            parent_revision=3,
        )
        self.assertEqual(first, second)
        self.assertEqual(first["revisionId"], "r004")
        self.assertTrue(first["immutable"])
        with self.assertRaises(ValueError):
            create_revision_record(model_fixture(), author="architect", reason="bad", parent_revision=4)

    def test_archive_restore_is_soft_and_preserves_current_revision(self):
        state = {"project": {"id": "proj-archive", "revision": 7}, "revisions": [{"revision": 7}]}
        archived = archive_project_state(state, author="owner", reason="Move to archive")
        self.assertTrue(archived["project"]["archived"])
        self.assertEqual(archived["project"]["revision"], 7)
        restored = restore_project_state(archived, author="owner", reason="Resume coordination")
        self.assertFalse(restored["project"]["archived"])
        self.assertEqual(restored["project"]["revision"], 7)
        self.assertEqual(state["project"].get("archived"), None)

    def test_complete_package_requires_all_artifacts(self):
        manifest = build_archive_manifest(model_fixture(), artifact_paths=("missing/report.pdf",))
        verification = verify_project_package(manifest)
        self.assertEqual(verification["status"], "blocked")
        self.assertIn("missing/report.pdf", verification["missingArtifacts"])
        self.assertFalse(verification["destructiveCleanupAllowed"])
        relaxed = verify_project_package(manifest, require_complete=False)
        self.assertEqual(relaxed["status"], "pass")


if __name__ == "__main__":
    unittest.main()