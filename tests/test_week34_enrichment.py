import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from week34 import (  # noqa: E402
    build_reachability_graph,
    semantic_openings,
    validate_openings,
    validate_reachability,
)


class Week34EnrichmentTests(unittest.TestCase):
    def setUp(self):
        self.site = {
            "units": "inch",
            "levels": [{"id": "GF", "name": "Ground Floor"}],
            "site": {"plot": [[0, 0], [300, 0], [300, 240]]},
        }
        self.plans = {
            "units": "inch",
            "wallThickness": 6,
            "spaces": [
                {"id": "GF-ENTRY", "level": "GF", "name": "Entry", "rect": [0, 0, 120, 120], "finish": "circulation"},
                {"id": "GF-ROOM", "level": "GF", "name": "Room", "rect": [126, 0, 246, 120], "finish": "public"},
            ],
            "openings": [
                {
                    "id": "D-01",
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
                    "openingId": "D-01",
                    "hostSpace": "GF-ROOM",
                    "wall": "east",
                    "porch": {"width": 48, "depth": 48},
                }
            ],
            "stairs": [],
        }

    def test_entry_opening_has_explicit_exterior_side_and_landing(self):
        semantics = semantic_openings(self.site, self.plans)
        self.assertEqual(semantics[0]["connectionType"], "exterior")
        self.assertEqual(semantics[0]["sideB"]["kind"], "exterior-zone")
        findings, schedule = validate_openings(self.site, self.plans)
        self.assertEqual(findings, [])
        self.assertEqual(schedule[0]["tag"], "D-01")

    def test_missing_side_b_is_a_blocker(self):
        plans = copy.deepcopy(self.plans)
        plans["entries"] = []
        findings, _schedule = validate_openings(self.site, plans)
        self.assertTrue(any(item["rule"] == "OPENING_SIDE_B_MUST_BE_VALID" for item in findings))

    def test_graph_proves_route_to_entry(self):
        _findings, graph = validate_reachability(self.site, self.plans)
        route = next(item for item in graph["routes"] if item["spaceId"] == "GF-ROOM")
        self.assertTrue(route["reachable"])
        self.assertIn("EDGE-OPENING-D-01", route["path"])

    def test_disconnected_room_reports_first_broken_edge(self):
        plans = copy.deepcopy(self.plans)
        plans["spaces"].append(
            {"id": "GF-ORPHAN", "level": "GF", "name": "Orphan", "rect": [0, 160, 120, 280], "finish": "public"}
        )
        plans["openings"].append(
            {
                "id": "D-ORPHAN",
                "level": "GF",
                "type": "door",
                "tag": "D-ORPHAN",
                "hostSpace": "GF-ORPHAN",
                "wall": "south",
                "offset": 20,
                "width": 36,
                "swing": "in",
            }
        )
        findings, graph = validate_reachability(self.site, plans)
        self.assertTrue(any(item["spaceId"] == "GF-ORPHAN" for item in findings))
        route = next(item for item in graph["routes"] if item["spaceId"] == "GF-ORPHAN")
        self.assertFalse(route["reachable"])


if __name__ == "__main__":
    unittest.main()