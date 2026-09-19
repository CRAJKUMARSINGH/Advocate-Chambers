import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from week910 import (  # noqa: E402
    GOLDEN_FIXTURES,
    FURNITURE_LIBRARY,
    _canonical_model_adapter,
    candidate_comparison_report,
    furniture_presentation_report,
    geometry_property_report,
    golden_fixture_report,
)
from week1516 import ASSET_CATALOG, furnish_model  # noqa: E402


def model_fixture():
    return {
        "schemaVersion": "advocate-chambers.project.v2",
        "project": {"id": "fixture", "revision": 3},
        "levels": [{"id": "GF", "elevation": 0}],
        "spaces": [
            {
                "id": "GF-HALL",
                "levelId": "GF",
                "name": "Hall",
                "roomUse": "assembly",
                "geometry": {"rect": [0, 0, 360, 360]},
            },
            {
                "id": "GF-OFFICE",
                "levelId": "GF",
                "name": "Office",
                "roomUse": "office",
                "geometry": {"rect": [360, 0, 180, 180]},
            },
        ],
        "openings": [],
        "windows": [{"id": "W-HALL", "hostSpace": "GF-HALL"}],
        "entries": [{"id": "ENTRY", "levelId": "GF", "hostSpace": "GF-HALL"}],
        "verticalConnectors": [],
        "stairs": [],
        "program": {
            "spaceChecks": [{"status": "pass"}],
            "adjacencyEvaluations": [{"satisfied": True}],
            "requiredUses": [{"roomUse": "assembly"}],
        },
        "adjacencies": [{"satisfied": True}],
    }


class Week910EnrichmentTests(unittest.TestCase):
    def test_week9_library_is_only_a_view_of_week15_catalog(self):
        self.assertTrue(FURNITURE_LIBRARY)
        for asset_id, legacy in FURNITURE_LIBRARY.items():
            canonical = ASSET_CATALOG[legacy["canonicalAssetId"]]
            self.assertEqual(legacy["schemaVersion"], "week15.parametric-assets.v1")
            self.assertEqual(legacy["width"], canonical["width"])
            self.assertEqual(legacy["depth"], canonical["depth"])
            self.assertEqual(legacy["occupancy"], canonical["occupancy"])

    def test_week9_wrapper_and_week15_engine_have_same_validation_result(self):
        model = model_fixture()
        legacy = furniture_presentation_report(model, seed=23)
        canonical = furnish_model(_canonical_model_adapter(model), seed=23)
        self.assertEqual(legacy["canonicalReport"]["findings"], canonical["findings"])
        self.assertEqual(legacy["canonicalReport"]["status"], canonical["status"])
        self.assertTrue(all(item["presentationOnly"] for item in canonical["placements"]))

    def test_furniture_is_scaled_traceable_and_non_authoritative(self):
        model = model_fixture()
        before = copy.deepcopy(model["spaces"])
        report = furniture_presentation_report(model, seed=11)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["placements"])
        self.assertTrue(all(item["authoritative"] is False for item in report["placements"]))
        self.assertEqual(model["spaces"], before)
        self.assertTrue(report["authoritativeGeometryUnchanged"])

    def test_furniture_layout_is_deterministic(self):
        first = furniture_presentation_report(model_fixture(), seed=23)
        second = furniture_presentation_report(model_fixture(), seed=23)
        self.assertEqual(first["determinism"]["signature"], second["determinism"]["signature"])
        self.assertEqual(first["placements"], second["placements"])

    def test_week15_validator_avoids_door_approach_block(self):
        model = model_fixture()
        model["openings"] = [
            {
                "id": "D-OFFICE",
                "hostSpace": "GF-OFFICE",
                "geometry": {"rect": [420, 0, 48, 18]},
            }
        ]
        report = furniture_presentation_report(model)
        self.assertEqual(report["canonicalReport"]["status"], "pass")
        self.assertFalse(any(item["rule"] == "FURNITURE_MUST_NOT_BLOCK_DOOR_APPROACH" for item in report["findings"]))

    def test_candidate_comparison_never_marks_inherited_blocker_best(self):
        report = candidate_comparison_report(
            model_fixture(),
            [{"severity": "BLOCKER", "rule": "ROOM_HAS_UNJUSTIFIED_EXTERNAL_DOOR"}],
        )
        self.assertIsNone(report["bestCandidateId"])
        self.assertTrue(all(not item["eligibleForBest"] for item in report["candidates"]))
        self.assertTrue(any(item["rule"] == "BEST_CANDIDATE_MUST_HAVE_NO_BLOCKERS" for item in report["findings"]))

    def test_candidate_comparison_is_deterministic(self):
        first = candidate_comparison_report(model_fixture(), seeds=(11, 23, 47))
        second = candidate_comparison_report(model_fixture(), seeds=(11, 23, 47))
        self.assertEqual(first["ranking"], second["ranking"])
        self.assertEqual(first["bestCandidateId"], second["bestCandidateId"])

    def test_golden_fixtures_cover_all_building_types(self):
        report = golden_fixture_report()
        self.assertEqual(report["status"], "pass")
        self.assertEqual(set(report["buildingTypes"]), set(GOLDEN_FIXTURES))

    def test_geometry_properties_pass(self):
        report = geometry_property_report(seed=7, cases=32)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["failures"], [])


if __name__ == "__main__":
    unittest.main()