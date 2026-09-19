import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from week1516 import (  # noqa: E402
    ASSET_CATALOG,
    ROOM_TEMPLATES,
    candidate_studio,
    design_package,
    edit_placements,
    find_valid_position,
    furnish_model,
    validate_placement,
)


def model_fixture():
    return {
        "project": {"id": "fixture", "revision": 8},
        "levels": [{"id": "GF", "elevation": 0}],
        "spaces": [{"id": "GF-OFFICE", "name": "Office", "roomUse": "office", "geometry": {"rect": [0, 0, 240, 240]}}],
        "openings": [],
        "routes": [{"id": "ROUTE", "spaceId": "GF-OFFICE", "geometry": {"rect": [0, 0, 240, 36]}}],
        "stairs": [],
        "serviceZones": [],
        "adjacencies": [{"satisfied": True}],
        "program": {"spaceChecks": [{"status": "pass"}]},
    }


class Week1516EnrichmentTests(unittest.TestCase):
    def test_catalog_and_templates_cover_week15_categories(self):
        categories = {item["category"] for item in ASSET_CATALOG.values()}
        self.assertTrue({"furniture", "fixtures", "appliance", "sanitaryware", "seating", "dais", "library", "counter", "vehicle", "industrial-equipment"} & categories)
        self.assertEqual({"residential", "office", "chamber", "hall", "classroom", "library", "healthcare", "retail", "light-industrial"}, set(ROOM_TEMPLATES))
        for spec in ASSET_CATALOG.values():
            self.assertFalse(spec["authoritative"])
            self.assertIn("clearanceEnvelope", spec)
            self.assertIn("rotationRules", spec)

    def test_one_click_furnishing_preserves_authority_and_is_deterministic(self):
        model = model_fixture()
        before = copy.deepcopy(model)
        first = furnish_model(model, seed=1516)
        second = furnish_model(model, seed=1516)
        self.assertEqual(first["determinism"], second["determinism"])
        self.assertTrue(first["authoritativeGeometryUnchanged"])
        self.assertEqual(model, before)
        self.assertTrue(all(item["presentationOnly"] for item in first["placements"]))

    def test_route_and_door_swing_are_blockers(self):
        model = model_fixture()
        placement = {
            "id": "desk-1",
            "assetId": "work-desk",
            "hostSpaceId": "GF-OFFICE",
            "geometry": {"rect": [0, 0, 60, 30]},
        }
        findings = validate_placement(model, placement)
        self.assertTrue(any(item["rule"] == "ASSET_MUST_NOT_BLOCK_ZONE" for item in findings))
        model["openings"] = [{"id": "D-1", "hostSpace": "GF-OFFICE", "geometry": {"rect": [0, 200, 36, 218]}}]
        placement["geometry"]["rect"] = [0, 180, 60, 210]
        self.assertTrue(any(item["rule"] == "ASSET_MUST_NOT_BLOCK_DOOR_SWING" for item in validate_placement(model, placement)))

    def test_edit_operations_and_valid_position(self):
        model = model_fixture()
        placement = find_valid_position(model, "work-desk", "GF-OFFICE")
        self.assertIsNotNone(placement)
        placement["id"] = "desk-1"
        moved = edit_placements(model, [placement], {"type": "duplicate", "targetId": "desk-1", "newId": "desk-2", "dx": 100, "dy": 100})
        self.assertEqual(len(moved["placements"]), 2)
        replaced = edit_placements(model, [placement], {"type": "replace", "targetId": "desk-1", "assetId": "executive-desk"})
        self.assertEqual(replaced["placements"][0]["assetId"], "executive-desk")

    def test_candidate_studio_deterministic_and_blocker_safe(self):
        model = model_fixture()
        first = candidate_studio(model, seeds=(1, 2, 3))
        second = candidate_studio(model, seeds=(1, 2, 3))
        self.assertEqual(first["ranking"], second["ranking"])
        self.assertIsNotNone(first["bestCandidateId"])
        blocked = candidate_studio(model, seeds=(1,), inherited_findings=[{"severity": "BLOCKER", "rule": "TEST"}])
        self.assertIsNone(blocked["bestCandidateId"])

    def test_design_package_is_revision_traceable_and_non_destructive(self):
        package = design_package(model_fixture(), "C-15-01")
        self.assertFalse(package["authoritativeGeometryChanged"])
        self.assertEqual(package["technicalPlanSideBySide"]["modelRevision"], 8)
        self.assertTrue(all(job["artifactManifest"]["traceableTo"]["candidateId"] == "C-15-01" for job in package["renderJobs"]))


if __name__ == "__main__":
    unittest.main()