import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from week78 import (  # noqa: E402
    DEFAULT_RULE_PACK,
    drawing_quality_report,
    rule_pack_report,
)


def model_fixture():
    return {
        "units": "inch",
        "project": {"revision": 1},
        "levels": [
            {"id": "GF", "name": "Ground", "elevation": 0},
            {"id": "FF", "name": "First", "elevation": 144},
        ],
        "spaces": [
            {"id": "GF-HALL", "levelId": "GF", "name": "Hall", "roomUse": "assembly", "geometry": {"rect": [0, 0, 240, 240]}},
            {"id": "GF-SERVICE", "levelId": "GF", "name": "Service", "roomUse": "service", "geometry": {"rect": [240, 0, 360, 120]}},
        ],
        "openings": [
            {"id": "D-HALL", "kind": "door", "levelId": "GF", "hostSpace": "GF-HALL", "geometry": {"width": 48}, "semantic": {"connectionType": "exterior"}},
            {"id": "D-SERVICE", "kind": "door", "levelId": "GF", "hostSpace": "GF-SERVICE", "geometry": {"width": 36}},
        ],
        "windows": [
            {"id": "W-HALL", "kind": "window", "levelId": "GF", "hostSpace": "GF-HALL", "geometry": {"width": 72}},
            {"id": "W-SERVICE", "kind": "window", "levelId": "GF", "hostSpace": "GF-SERVICE", "geometry": {"width": 36}},
        ],
        "stairs": [],
        "entries": [],
    }


class Week78EnrichmentTests(unittest.TestCase):
    def test_rule_pack_keeps_universal_and_jurisdictional_checks_separate(self):
        report = rule_pack_report(model_fixture())
        self.assertEqual(report["status"], "pass")
        self.assertGreater(report["separation"]["universalRuleCount"], 0)
        self.assertGreater(report["separation"]["jurisdictionalRuleCount"], 0)
        self.assertFalse(report["separation"]["geometryChangedByPack"])

    def test_changing_pack_changes_findings_without_changing_geometry(self):
        model = model_fixture()
        strict_pack = copy.deepcopy(DEFAULT_RULE_PACK)
        strict_pack["accessibility"]["doorMinWidth"] = 60
        report = rule_pack_report(model, strict_pack)
        self.assertTrue(any(item["rule"] == "ACCESSIBLE_DOOR_WIDTH_MUST_MEET_RULE_PACK" for item in report["findings"]))
        self.assertEqual(model["spaces"][0]["geometry"]["rect"], [0, 0, 240, 240])

    def test_drawing_quality_stamp_inherits_upstream_failure(self):
        week7 = {"status": "pass"}
        week56 = {"status": "fail"}
        report = drawing_quality_report(model_fixture(), week7, week56)
        self.assertEqual(report["stamp"], "NOT ISSUABLE")
        self.assertFalse(report["issuable"])
        self.assertEqual(len(report["sheetCatalog"]), 4)
        self.assertTrue(report["determinism"]["sameModelSameRulePackProducesSameSignature"])

    def test_drawing_quality_catches_untraceable_opening(self):
        model = model_fixture()
        model["openings"][0]["hostSpace"] = "MISSING"
        report = drawing_quality_report(model, {"status": "pass"}, {"status": "pass"})
        self.assertTrue(any(item["rule"] == "VISIBLE_OPENINGS_MUST_TRACE_TO_MODEL" for item in report["findings"]))
        self.assertEqual(report["status"], "fail")


if __name__ == "__main__":
    unittest.main()