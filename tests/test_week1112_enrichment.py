import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from week1112 import (  # noqa: E402
    CAPABILITY_MATRIX,
    MODES,
    accept_revision,
    command_preview,
    compile_brief,
    parse_measurement,
    performance_counters,
)


def model_fixture():
    return {
        "schemaVersion": "advocate-chambers.project.v2",
        "project": {"id": "fixture", "revision": 4},
        "levels": [{"id": "GF", "elevation": 0}, {"id": "FF", "elevation": 144}],
        "spaces": [
            {"id": "GF-LOBBY", "name": "Lobby", "roomUse": "lobby", "levelId": "GF"},
            {"id": "FF-LIBRARY", "name": "Library", "roomUse": "library", "levelId": "FF"},
        ],
        "openings": [{"id": "D-OUTER", "kind": "door", "hostSpace": "GF-LOBBY"}],
        "stairs": [{"id": "STAIR-01", "kind": "stair", "levelId": "GF"}],
        "verticalConnectors": [],
        "entries": [],
    }


class Week1112EnrichmentTests(unittest.TestCase):
    def test_product_modes_and_capabilities_are_explicit(self):
        self.assertEqual([mode["id"] for mode in MODES], ["brief", "model", "validate", "furnish", "present", "export"])
        self.assertTrue(any(item["status"] == "provisional" for item in CAPABILITY_MATRIX))
        self.assertTrue(any(item["status"] == "available" for item in CAPABILITY_MATRIX))

    def test_metric_measurements_normalize_to_inches(self):
        parsed = parse_measurement("3.6m")
        self.assertEqual(parsed["unit"], "inch")
        self.assertAlmostEqual(parsed["value"], 141.732283, places=5)

    def test_brief_compiler_extracts_facts_and_marks_topology_gaps(self):
        result = compile_brief(
            "Design 2 levels on a site 30m x 20m. North is north. "
            "Road frontage is east. Floor-to-floor 3.5m. "
            "2 offices, library area target of 50m2, occupancy 80 people. "
            "Public access, library near lobby, style contemporary, outputs PDF DXF.",
            default_units="metric",
        )
        self.assertEqual(result["status"], "needs-review")
        self.assertEqual(result["facts"]["site"]["width"]["unit"], "inch")
        self.assertEqual(result["facts"]["levels"], 2)
        self.assertEqual(result["facts"]["occupancy"]["people"], 80)
        self.assertTrue(result["facts"]["roomSchedule"])
        self.assertIn("Identify which stair, lift, or ramp connects each level.", result["missingTopologyFacts"])

    def test_complete_brief_can_be_ready(self):
        result = compile_brief(
            "site 30m x 20m, north is north, road frontage is east, 1 level, "
            "library area target 50m2, public access, output PDF",
            default_units="metric",
        )
        self.assertEqual(result["status"], "ready")
        self.assertTrue(result["readyForGeneration"])

    def test_previews_are_non_mutating_and_conditional_door_is_blocked(self):
        model = model_fixture()
        before = copy.deepcopy(model)
        preview = command_preview(model, "remove the outer door unless a balcony is modeled", timestamp="2026-01-01T00:00:00+00:00")
        self.assertEqual(preview["status"], "blocked")
        self.assertTrue(any(item["severity"] == "BLOCKER" for item in preview["findings"]))
        self.assertTrue(preview["canonicalModelUnchanged"])
        self.assertEqual(model, before)

    def test_typed_revision_can_be_accepted_without_freeform_mutation(self):
        model = model_fixture()
        preview = command_preview(model, "give the library a public route", timestamp="2026-01-01T00:00:00+00:00")
        accepted = accept_revision(model, preview)
        self.assertTrue(accepted["revision"]["accepted"])
        self.assertEqual(accepted["model"]["project"]["revision"], 5)
        self.assertEqual(accepted["model"]["spaces"][1]["accessIntent"], "public")
        self.assertEqual(accepted["model"]["revisionHistory"][0]["changedObjectIds"], ["FF-LIBRARY"])

    def test_performance_counters_are_local_and_structured(self):
        counters = performance_counters(model_fixture(), validation_duration_ms=2.5)
        self.assertEqual(counters["scope"], "local-only")
        self.assertGreater(counters["modelBytes"], 0)
        self.assertEqual(counters["validationDurationMs"], 2.5)


if __name__ == "__main__":
    unittest.main()