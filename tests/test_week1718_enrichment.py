import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from week1718 import (  # noqa: E402
    APPROVAL_STATES,
    ANCHOR_TYPES,
    compare_revisions,
    coordinated_package,
    create_comment,
    create_review_link,
    evaluate_rule_pack,
    imported_review_workflow,
)


def model_fixture():
    return {
        "project": {"id": "proj-fixture", "revision": 4},
        "units": "inch",
        "site": {
            "geometry": {
                "north": "up",
                "plotVertices": [[0, 0], [300, 0], [300, 300], [0, 300]],
                "setbacks": {"north": 10, "south": 10, "east": 10, "west": 10},
            }
        },
        "orientation": {"north": "up", "setbacks": {"north": 10, "south": 10, "east": 10, "west": 10}},
        "levels": [{"id": "GF", "elevation": 0, "floorToFloor": 144}],
        "spaces": [
            {
                "id": "GF-OFFICE",
                "levelId": "GF",
                "roomUse": "office",
                "geometry": {"rect": [20, 20, 180, 180]},
            }
        ],
        "openings": [{"id": "D-1", "hostSpace": "GF-OFFICE", "geometry": {"width": 36}}],
        "windows": [{"id": "W-1", "hostSpace": "GF-OFFICE", "geometry": {"width": 60}}],
        "entries": [{"id": "ENTRY-1", "hostSpace": "GF-OFFICE", "exteriorZoneId": "EXT-1"}],
        "circulationZones": [{"id": "ROUTE-1", "geometry": {"width": 48}}],
        "stairs": [],
        "assumptions": ["Fixture dimensions are nominal."],
    }


class Week1718EnrichmentTests(unittest.TestCase):
    def test_feasibility_is_transparent_and_does_not_claim_approval(self):
        report = evaluate_rule_pack(model_fixture())
        self.assertEqual(report["version"], "week17.site-feasibility.v1")
        self.assertFalse(report["dashboard"]["approvalClaim"])
        self.assertTrue(report["dashboard"]["professionalReviewRequired"])
        self.assertGreaterEqual(len(report["results"]), 10)
        self.assertGreaterEqual(report["dashboard"]["counts"]["professional-review"], 1)
        for result in report["results"]:
            self.assertIn("ruleId", result)
            self.assertIn("inputGeometry", result)
            self.assertIn("calculation", result)
            self.assertIn("confidence", result)
            self.assertIn(result["status"], {"pass", "fail", "unknown", "professional-review"})

    def test_imported_review_stays_non_authoritative(self):
        review = imported_review_workflow("incoming/review.pdf")
        self.assertEqual(review["workflow"], "separate-imported-review")
        self.assertTrue(review["promotion"]["requiresHumanReview"])
        self.assertFalse(review["promotion"]["authoritativeGeometry"])
        self.assertFalse(review["promotion"]["approvalGranted"])

    def test_scale_mismatch_is_unknown_not_a_silent_setback_failure(self):
        model = model_fixture()
        model["site"]["geometry"]["plotVertices"] = [[0, 0], [60, 0], [60, 98], [0, 98]]
        result = next(item for item in evaluate_rule_pack(model)["results"] if item["ruleId"] == "SITE-SETBACKS")
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["severity"], "REVIEW")
        self.assertIn("incompatible scales", result["assumption"])

    def test_links_and_comments_are_revision_anchored(self):
        model = model_fixture()
        link_a = create_review_link(model, view="technical")
        link_b = create_review_link(model, view="technical")
        self.assertEqual(link_a, link_b)
        self.assertTrue(link_a["readOnly"])
        comment = create_comment(
            model,
            author="reviewer",
            body="Confirm the office window schedule.",
            anchor_type="room",
            anchor_id="GF-OFFICE",
        )
        self.assertEqual(comment["anchor"]["type"], "room")
        self.assertEqual(comment["modelRevision"], 4)
        with self.assertRaises(ValueError):
            create_comment(model, author="reviewer", body="bad", anchor_type="room", anchor_id="missing")

    def test_revision_compare_covers_required_categories(self):
        before = model_fixture()
        after = copy.deepcopy(before)
        after["project"]["revision"] = 5
        after["spaces"][0]["geometry"]["rect"][2] = 200
        after["openings"].append({"id": "D-2", "hostSpace": "GF-OFFICE", "geometry": {"width": 36}})
        after["furniture"] = [{"id": "desk-1", "assetId": "work-desk"}]
        diff = compare_revisions(before, after)
        self.assertEqual(diff["fromRevision"], 4)
        self.assertEqual(diff["toRevision"], 5)
        self.assertEqual(diff["geometryChanges"]["changed"], ["GF-OFFICE"])
        self.assertEqual(diff["openingChanges"]["added"], ["D-2"])
        self.assertEqual(diff["furnitureChanges"]["added"], ["desk-1"])
        self.assertEqual(len(diff["areaChanges"]), 1)

    def test_release_gate_requires_explicit_non_issuable_flag(self):
        model = model_fixture()
        feasibility = evaluate_rule_pack(model)
        feasibility["results"].append(
            {
                "ruleId": "TEST-BLOCKER",
                "status": "fail",
                "severity": "BLOCKER",
            }
        )
        blocked = coordinated_package(model, feasibility)
        self.assertEqual(blocked["releaseGate"]["status"], "blocked")
        self.assertEqual(blocked["approvalState"], "Preliminary Coordination")
        review_package = coordinated_package(model, feasibility, allow_non_issuable=True, include_ifc=True)
        self.assertEqual(review_package["releaseGate"]["status"], "review-package")
        self.assertEqual(review_package["approvalState"], "Not Issuable")
        self.assertTrue(any(item["kind"] == "ifc" for item in review_package["artifacts"]))

    def test_contract_enumerations_are_stable(self):
        self.assertEqual(
            APPROVAL_STATES,
            ("Draft", "Review", "Client Presentation", "Preliminary Coordination", "Not Issuable"),
        )
        self.assertIn("validation-finding", ANCHOR_TYPES)


if __name__ == "__main__":
    unittest.main()