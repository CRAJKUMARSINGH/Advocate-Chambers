import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT / "bar-association-hall"
sys.path.insert(0, str(MODEL_ROOT))

from drawing_model import load_model, validate_model_findings  # noqa: E402


class Week1ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site, cls.plans = load_model()

    def findings_for(self, plans):
        return validate_model_findings(self.site, plans)

    @staticmethod
    def rules(findings):
        return {finding["rule"] for finding in findings}

    def test_known_upper_floor_external_door_is_a_precise_blocker(self):
        findings = self.findings_for(copy.deepcopy(self.plans))
        matches = [
            finding
            for finding in findings
            if finding["rule"] == "ROOM_HAS_UNJUSTIFIED_EXTERNAL_DOOR"
            and finding["spaceId"] == "FF-07"
            and "D-FF-07" in finding["openingIds"]
        ]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["severity"], "BLOCKER")
        self.assertIn("balcony", matches[0]["message"])

    def test_orphan_room_is_blocked(self):
        plans = copy.deepcopy(self.plans)
        plans["spaces"].append(
            {
                "id": "TEST-ORPHAN",
                "level": "GF",
                "name": "Unconnected Test Room",
                "rect": [700, 6, 820, 126],
                "finish": "public",
            }
        )
        findings = self.findings_for(plans)
        orphan = [finding for finding in findings if finding["spaceId"] == "TEST-ORPHAN"]
        self.assertTrue(any(finding["rule"] == "ROOM_MUST_HAVE_DOOR" for finding in orphan))
        self.assertTrue(any(finding["severity"] == "BLOCKER" for finding in orphan))

    def test_external_door_without_access_zone_is_blocked(self):
        plans = copy.deepcopy(self.plans)
        opening = next(item for item in plans["openings"] if item["id"] == "D-FF-07")
        opening.pop("accessZoneId", None)
        opening.pop("exteriorAccessZoneId", None)
        findings = self.findings_for(plans)
        self.assertIn("ROOM_HAS_UNJUSTIFIED_EXTERNAL_DOOR", self.rules(findings))

    def test_overlapping_rooms_are_rejected(self):
        plans = copy.deepcopy(self.plans)
        plans["spaces"].append(
            {
                "id": "TEST-OVERLAP",
                "level": "GF",
                "name": "Overlapping Test Room",
                "rect": [20, 20, 100, 100],
                "finish": "public",
            }
        )
        findings = self.findings_for(plans)
        self.assertTrue(
            any(
                finding["rule"] == "SPACES_MUST_NOT_OVERLAP"
                and "TEST-OVERLAP" in finding["message"]
                for finding in findings
            )
        )

    def test_invalid_opening_is_rejected(self):
        plans = copy.deepcopy(self.plans)
        opening = next(item for item in plans["openings"] if item["id"] == "D-GF-01")
        opening["offset"] = 10000
        findings = self.findings_for(plans)
        match = next(finding for finding in findings if finding["id"] == "VAL-OPENING-FIT-D-GF-01")
        self.assertEqual(match["rule"], "OPENING_MUST_FIT_HOST_WALL")
        self.assertEqual(match["severity"], "ERROR")

    def test_stair_arithmetic_is_rejected(self):
        plans = copy.deepcopy(self.plans)
        plans["stairs"][0]["riser"] = 7
        findings = self.findings_for(plans)
        match = next(finding for finding in findings if finding["rule"] == "STAIR_RISER_ARITHMETIC")
        self.assertEqual(match["severity"], "ERROR")
        self.assertIn("STAIR-01", match["connectorIds"])

    def test_valid_connected_fixture_has_no_blocking_findings(self):
        site = {
            "project": {"name": "Week 1 valid fixture"},
            "levels": [{"id": "GF", "name": "Ground Floor"}],
            "site": {"plot": [[0, 0], [240, 0], [240, 240]]},
        }
        plans = {
            "projectId": "week1-valid-fixture",
            "units": "inch",
            "wallThickness": 6,
            "spaces": [
                {"id": "GF-ENTRY", "level": "GF", "name": "Entry", "rect": [0, 0, 120, 120], "finish": "circulation"},
                {"id": "GF-ROOM", "level": "GF", "name": "Review Room", "rect": [126, 0, 246, 120], "finish": "public"},
            ],
            "openings": [
                {
                    "id": "D-MAIN",
                    "level": "GF",
                    "type": "door",
                    "tag": "D-01",
                    "hostSpace": "GF-ROOM",
                    "wall": "east",
                    "offset": 42,
                    "width": 36,
                    "swing": "out",
                }
            ],
            "windows": [],
            "entries": [
                {
                    "id": "ENTRY-MAIN",
                    "level": "GF",
                    "kind": "main",
                    "label": "Main entry",
                    "openingId": "D-MAIN",
                    "hostSpace": "GF-ROOM",
                    "wall": "east",
                    "status": "confirmed",
                    "porch": {"width": 48, "depth": 48},
                }
            ],
            "stairs": [],
            "notes": ["Door symbols show a wall break."],
        }
        blocking = [
            finding
            for finding in validate_model_findings(site, plans)
            if finding["severity"] in {"BLOCKER", "ERROR"}
        ]
        self.assertEqual(blocking, [])

    def test_source_files_are_valid_json(self):
        source = MODEL_ROOT / "standard" / "source"
        for name in ("site_plan.json", "preliminary_plans.json"):
            with (source / name).open(encoding="utf-8") as handle:
                self.assertIsInstance(json.load(handle), dict)


if __name__ == "__main__":
    unittest.main()