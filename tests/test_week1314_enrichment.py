import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "bar-association-hall"))

from sheet_layout import SHEET_STANDARD, layout_for_extent, validate_layout  # noqa: E402
from week1314 import (  # noqa: E402
    build_synchronized_views,
    recognize_import,
    read_json,
)


MODEL_PATH = ROOT / "bar-association-hall/standard/model/project.json"
DXF_PATH = "CAD-Drawings/DXF/01-Site-Master-Plan-Plots-1-and-2.dxf"


class Week1314EnrichmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = read_json(MODEL_PATH)

    def test_dxf_recognition_is_provenanced_and_review_first(self):
        report = recognize_import(source_path=DXF_PATH)
        self.assertEqual(report["source"]["format"], "dxf")
        self.assertEqual(len(report["source"]["sha256"]), 64)
        self.assertTrue(report["observed"]["geometryPreserved"])
        self.assertTrue(report["promotionPolicy"]["uncertainObjectsRemainNonAuthoritative"])
        self.assertTrue(report["reviewQueue"])

    def test_pdf_recognition_does_not_claim_authoritative_geometry(self):
        report = recognize_import(source_path="CAD-Drawings/PDF/01-Site-Master-Plan-Plots-1-and-2.pdf")
        self.assertEqual(report["source"]["format"], "pdf")
        self.assertFalse(report["observed"]["geometryPreserved"])
        self.assertTrue(all(value == 0.0 for value in report["confidence"].values()))

    def test_views_share_revision_and_invalidation_gate(self):
        report = build_synchronized_views(self.model)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["modelRevision"], self.model["project"]["revision"])
        self.assertTrue(report["selection"]["sharedAcrossViews"])
        self.assertTrue(report["gate"]["validationRerunsAfterAcceptedEdit"])
        self.assertGreater(report["snapping"]["targetCount"], 0)
        self.assertIn("floorLevels", report["derivedGeometry"]["sectionsInclude"])

    def test_sheet_policy_protects_plan_area(self):
        layout = layout_for_extent(1190.55, 841.89, (0, 0, 660, 1116))
        self.assertEqual(validate_layout(layout), [])
        self.assertLessEqual(
            layout.areaRatios["supportingContent"],
            SHEET_STANDARD["supportingContentMaxAreaRatio"],
        )
        self.assertGreaterEqual(
            layout.areaRatios["drawingZone"],
            SHEET_STANDARD["drawingZoneMinAreaRatio"],
        )

    def test_canonical_model_has_prior_week_data(self):
        self.assertIn("briefCompiler", self.model)
        self.assertIn("drawingQuality", self.model)


if __name__ == "__main__":
    unittest.main()