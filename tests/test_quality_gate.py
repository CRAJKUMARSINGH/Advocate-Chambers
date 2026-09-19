import copy
import json
import sys
import unittest

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from quality_gate import (  # noqa: E402
    build_quality_gate,
    evaluate_adversarial,
    evaluate_performance,
    evaluate_professional_review,
    validate_quality_gate,
)


def passing_adversarial():
    return {
        "totalCriticalDefects": 30,
        "detectedCriticalDefects": 30,
        "missedCriticalDefects": 0,
        "dangerousFalseNegatives": 0,
        "completeFindings": 30,
        "falsePositiveCount": 0,
    }


def passing_review():
    return {
        "reviewers": 2,
        "plansReviewed": 25,
        "usableAgreement": 0.92,
        "criticalDefectsAcceptedAsUsable": 0,
        "criticalFindingsReproducible": True,
    }


def passing_performance():
    return {
        "profiles": ["small", "medium", "large"],
        "silentTimeouts": 0,
        "outOfMemoryFailures": 0,
        "dataLossEvents": 0,
        "nondeterministicRuns": 0,
    }


class QualityGateTests(unittest.TestCase):
    def test_missing_tracks_are_incomplete_not_pass(self):
        report = build_quality_gate()
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertFalse(report["releaseReady"])
        self.assertEqual(report["tracks"]["adversarial"]["status"], "INCOMPLETE")
        self.assertEqual(report["tracks"]["professionalReview"]["status"], "INCOMPLETE")
        self.assertEqual(report["tracks"]["performance"]["status"], "INCOMPLETE")
        self.assertEqual(validate_quality_gate(report), [])

    def test_critical_false_negative_blocks_release(self):
        result = passing_adversarial()
        result["missedCriticalDefects"] = 1
        result["dangerousFalseNegatives"] = 1
        result["detectedCriticalDefects"] = 29
        self.assertEqual(evaluate_adversarial(result)["status"], "BLOCKED")

        report = build_quality_gate(
            adversarial=result,
            professional_review=passing_review(),
            performance=passing_performance(),
        )
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["releaseReady"])

    def test_professional_uncertainty_requires_review(self):
        result = passing_review()
        result["usableAgreement"] = 0.84
        self.assertEqual(evaluate_professional_review(result)["status"], "REVIEW_REQUIRED")

    def test_performance_failure_blocks_release(self):
        result = passing_performance()
        result["nondeterministicRuns"] = 1
        self.assertEqual(evaluate_performance(result)["status"], "BLOCKED")

    def test_all_tracks_pass_only_when_every_hard_gate_passes(self):
        report = build_quality_gate(
            adversarial=passing_adversarial(),
            professional_review=passing_review(),
            performance=passing_performance(),
        )
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["releaseReady"])
        self.assertEqual(report["score"], 100)
        self.assertEqual(validate_quality_gate(report), [])

    def test_tampered_report_signature_is_rejected(self):
        report = build_quality_gate()
        tampered = copy.deepcopy(report)
        tampered["tracks"]["regression"]["passed"] = 68
        errors = validate_quality_gate(tampered)
        self.assertIn("reportSignature does not match report contents", errors)

    def test_report_round_trips_as_json(self):
        report = build_quality_gate()
        decoded = json.loads(json.dumps(report))
        self.assertEqual(validate_quality_gate(decoded), [])


if __name__ == "__main__":
    unittest.main()