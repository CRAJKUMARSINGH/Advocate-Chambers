import copy
import sys
import unittest

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from week56 import (  # noqa: E402
    enrichment_report,
    program_report,
    validate_stairs,
)


def canonical_fixture():
    return {
        "schemaVersion": "advocate-chambers.project.v2",
        "project": {
            "id": "proj-test",
            "name": "Test civic building",
            "location": "Test",
            "status": "schematic",
            "revision": 1,
            "source": "user",
            "legacy": {},
        },
        "units": "inch",
        "wallThickness": 6,
        "site": {
            "id": "SITE-TEST",
            "kind": "site",
            "levelId": "SITE",
            "geometry": {
                "plotVertices": [[0, 0], [600, 0], [600, 600], [0, 600]],
                "north": "up",
                "setbacks": {"north": 60, "south": 60, "east": 60, "west": 60},
            },
            "legacy": {},
        },
        "levels": [
            {"id": "GF", "name": "Ground", "elevation": 0, "floorToFloor": 144},
            {"id": "FF", "name": "First", "elevation": 144, "floorToFloor": 144},
        ],
        "spaces": [
            {"id": "GF-RECEPTION", "levelId": "GF", "name": "Reception", "roomUse": "reception", "geometry": {"rect": [0, 0, 120, 120]}},
            {"id": "GF-STAIR", "levelId": "GF", "name": "Main Stair", "roomUse": "vertical-circulation", "geometry": {"rect": [120, 0, 180, 120]}},
            {"id": "GF-HALL", "levelId": "GF", "name": "Assembly Hall", "roomUse": "assembly", "geometry": {"rect": [0, 180, 360, 540]}},
            {"id": "GF-STAGE", "levelId": "GF", "name": "Stage", "roomUse": "stage", "geometry": {"rect": [0, 540, 360, 660]}},
            {"id": "GF-SERVICE", "levelId": "GF", "name": "Service", "roomUse": "service", "geometry": {"rect": [240, 0, 360, 120]}},
            {"id": "FF-STAIR", "levelId": "FF", "name": "Main Stair", "roomUse": "vertical-circulation", "geometry": {"rect": [120, 0, 180, 120]}},
            {"id": "FF-LIBRARY", "levelId": "FF", "name": "Library", "roomUse": "library", "geometry": {"rect": [0, 180, 360, 540]}},
            {"id": "FF-COMPUTER", "levelId": "FF", "name": "Computer", "roomUse": "computer", "geometry": {"rect": [360, 180, 480, 300]}},
        ],
        "verticalConnectors": [
            {
                "id": "VC-01",
                "kind": "vertical-connector",
                "fromLevelId": "GF",
                "toLevelId": "FF",
                "stairId": "STAIR-01",
                "departureSpaceId": "GF-STAIR",
                "arrivalSpaceId": "FF-STAIR",
                "accessIntent": "vertical",
            }
        ],
        "stairs": [
            {
                "id": "STAIR-01",
                "kind": "stair",
                "levelFrom": "GF",
                "levelTo": "FF",
                "verticalConnectorId": "VC-01",
                "configuration": "straight",
                "geometry": {
                    "floorToFloor": 144,
                    "riserCountTotal": 20,
                    "riserCountPerFlight": 20,
                    "flightCount": 1,
                    "riser": 7.2,
                    "tread": 10,
                    "width": 48,
                    "landingDepth": 48,
                    "direction": "up",
                },
            }
        ],
        "openings": [],
        "windows": [],
        "entries": [],
        "circulationZones": [],
        "exteriorZones": [],
        "assumptions": [],
        "notes": [],
        "revisions": [{"id": "r1", "date": "2026-01-01", "author": "test", "summary": "fixture", "source": "user", "legacy": {}}],
        "legacyMetadata": {"plans": {"projectId": "test", "units": "inch", "wallThickness": 6}},
    }


class Week56EnrichmentTests(unittest.TestCase):
    def test_valid_stair_schedule_passes_geometry_checks(self):
        findings, schedule = validate_stairs(canonical_fixture())
        self.assertEqual(findings, [])
        self.assertEqual(schedule[0]["connectorId"], "VC-01")
        self.assertEqual(schedule[0]["geometry"]["riser"], 7.2)

    def test_stair_riser_arithmetic_is_explainable(self):
        model = canonical_fixture()
        model["stairs"][0]["geometry"]["riser"] = 8
        findings, _schedule = validate_stairs(model)
        self.assertTrue(any(item["rule"] == "STAIR_RISER_ARITHMETIC_MUST_MATCH" for item in findings))

    def test_missing_arrival_is_a_blocker(self):
        model = canonical_fixture()
        model["verticalConnectors"][0]["arrivalSpaceId"] = "FF-MISSING"
        findings, _schedule = validate_stairs(model)
        self.assertTrue(any(item["rule"] == "CONNECTOR_ARRIVAL_MUST_EXIST" for item in findings))

    def test_program_template_completeness_and_adjacency_are_reported(self):
        program, findings = program_report(canonical_fixture())
        self.assertEqual(program["buildingType"], "institutional")
        self.assertTrue(all(item["status"] == "pass" for item in program["completeness"]))
        assembly_stage = next(item for item in program["adjacencyEvaluations"] if item["id"] == "assembly-stage")
        self.assertTrue(assembly_stage["satisfied"])
        self.assertTrue(any(item["rule"] == "SITE_ROAD_FRONTAGE_MUST_BE_CONFIRMED" for item in findings))

    def test_missing_required_program_use_is_a_blocker(self):
        model = canonical_fixture()
        model["spaces"] = [
            space for space in model["spaces"] if space["roomUse"] != "assembly"
        ]
        program, findings = program_report(model)
        assembly = next(item for item in program["completeness"] if item["roomUse"] == "assembly")
        self.assertEqual(assembly["status"], "missing")
        self.assertTrue(any(item["rule"] == "PROGRAM_REQUIRED_USE_MISSING" for item in findings))

    def test_enrichment_report_contains_week5_and_week6_sections(self):
        report = enrichment_report(canonical_fixture())
        self.assertIn("week5", report)
        self.assertIn("week6", report)
        self.assertEqual(report["week5"]["connectors"][0]["stairId"], "STAIR-01")
        self.assertIn("orientation", report["week6"]["program"])

    def test_invalid_dimensions_fail_program_gate(self):
        model = canonical_fixture()
        model["spaces"][0]["geometry"]["rect"] = [0, 0, 24, 24]
        _program, findings = program_report(model)
        self.assertTrue(any(item["rule"] == "SPACE_AREA_AND_DIMENSIONS_MUST_MEET_PROGRAM" for item in findings))


if __name__ == "__main__":
    unittest.main()