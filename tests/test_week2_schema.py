import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from week2 import (  # noqa: E402
    CANONICAL_PATH,
    SOURCE_ROOT,
    canonical_to_legacy,
    load_canonical_model,
    migrate_from_files,
    roundtrip_report,
    validate_canonical,
)


class Week2SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_canonical_model()
        cls.site = json.loads((SOURCE_ROOT / "site_plan.json").read_text())
        cls.plans = json.loads(
            (SOURCE_ROOT / "preliminary_plans.json").read_text()
        )

    def test_canonical_fixture_exists_and_validates(self):
        self.assertTrue(CANONICAL_PATH.exists())
        self.assertEqual(validate_canonical(self.model), [])
        self.assertEqual(
            self.model["schemaVersion"], "advocate-chambers.project.v2"
        )

    def test_week2_dimensions_and_provenance_are_present(self):
        self.assertEqual(len(self.model["levels"]), 2)
        self.assertEqual(len(self.model["spaces"]), len(self.plans["spaces"]))
        self.assertEqual(len(self.model["openings"]), len(self.plans["openings"]))
        self.assertEqual(len(self.model["windows"]), len(self.plans["windows"]))
        self.assertEqual(len(self.model["entries"]), len(self.plans["entries"]))
        self.assertTrue(self.model["circulationZones"])
        self.assertTrue(self.model["exteriorZones"])
        self.assertTrue(self.model["verticalConnectors"])
        for item in self.model["spaces"] + self.model["openings"]:
            self.assertIn("id", item)
            self.assertEqual(item["source"], "legacy")
            self.assertEqual(item["provenance"]["migration"], "week2.legacy-to-v2")

    def test_migration_is_deterministic(self):
        self.assertEqual(migrate_from_files(), migrate_from_files())

    def test_legacy_sources_round_trip_without_loss(self):
        report = roundtrip_report(self.model, self.site, self.plans)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["siteEqual"])
        self.assertTrue(report["plansEqual"])
        self.assertEqual(canonical_to_legacy(self.model), (self.site, self.plans))

    def test_schema_validation_rejects_missing_access_intent(self):
        invalid = copy.deepcopy(self.model)
        del invalid["spaces"][0]["accessIntent"]
        errors = validate_canonical(invalid)
        self.assertTrue(any("accessIntent" in error for error in errors))

    def test_schema_validation_rejects_broken_vertical_reference(self):
        invalid = copy.deepcopy(self.model)
        invalid["verticalConnectors"][0]["toLevelId"] = "MISSING"
        errors = validate_canonical(invalid)
        self.assertTrue(
            any("verticalConnectors[0].toLevelId" in error for error in errors)
        )


if __name__ == "__main__":
    unittest.main()