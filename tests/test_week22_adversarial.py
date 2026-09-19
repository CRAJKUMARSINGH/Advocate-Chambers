import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from week22 import (  # noqa: E402
    DEFECTIVE_ROOT,
    FIXTURE_SCHEMA_VERSION,
    build_report,
    detect_findings,
    discover_fixtures,
    load_fixture,
    run_benchmark,
    run_fixture,
    signature,
)


class Week22AdversarialTests(unittest.TestCase):
    def test_fixture_corpus_has_at_least_fifteen_cases(self):
        fixtures = discover_fixtures()
        self.assertGreaterEqual(len(fixtures), 15)
        self.assertEqual(len({path.name for path in fixtures}), len(fixtures))

    def test_every_fixture_has_a_valid_source_and_expected_finding(self):
        for path in discover_fixtures():
            fixture, _ = load_fixture(path)
            self.assertEqual(fixture["schemaVersion"], FIXTURE_SCHEMA_VERSION)
            self.assertTrue((path.parent / fixture["sourceFixture"]).is_file())
            self.assertIn("ruleId", fixture["expectedFinding"])
            self.assertIn("affectedObjects", fixture["expectedFinding"])
            self.assertIn("evidenceFields", fixture["expectedFinding"])
            self.assertTrue(fixture["expectedFinding"]["correction"])

    def test_every_defect_is_detected_for_the_intended_rule(self):
        results = [run_fixture(path) for path in discover_fixtures()]
        failures = [result for result in results if result["status"] != "PASS"]
        self.assertEqual(failures, [])

    def test_valid_baseline_has_no_findings(self):
        fixture, model = load_fixture(DEFECTIVE_ROOT / "ADV-001-inaccessible-first-floor-room.json")
        del fixture
        # Re-load the paired source rather than the mutated model.
        baseline = json.loads((ROOT / "tests/fixtures/adversarial/valid/baseline.json").read_text())
        self.assertEqual(detect_findings(baseline), [])

    def test_benchmark_reports_zero_missed_critical_defects(self):
        benchmark = run_benchmark()
        self.assertEqual(benchmark["fixtureCount"], 15)
        self.assertEqual(benchmark["criticalDefectsMissed"], 0)
        self.assertEqual(benchmark["dangerousFalseNegatives"], 0)
        self.assertEqual(benchmark["completeFindings"], 15)
        self.assertEqual(benchmark["falsePositiveCount"], 0)

    def test_report_is_deterministic_and_passes(self):
        first = build_report()
        second = build_report()
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "PASS")
        self.assertEqual(first["reportSignature"], signature({
            key: value for key, value in first.items() if key != "reportSignature"
        }))


if __name__ == "__main__":
    unittest.main()