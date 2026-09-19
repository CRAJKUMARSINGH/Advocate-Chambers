#!/usr/bin/env python3
"""Week 3 reachability graph command."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bar-association-hall"))
sys.path.insert(0, str(ROOT / "scripts"))

from drawing_model import load_model  # noqa: E402
from week34 import (  # noqa: E402
    WEEK3_REPORT_PATH,
    build_reachability_graph,
    validate_reachability,
    write_json,
)


def main() -> int:
    site, plans = load_model()
    findings, graph = validate_reachability(site, plans)
    report = {
        "reportVersion": "week3.reachability.v1",
        "status": "pass" if not findings else "fail",
        "findingCounts": {
            severity: sum(1 for item in findings if item["severity"] == severity)
            for severity in ("BLOCKER", "ERROR", "WARNING")
            if any(item["severity"] == severity for item in findings)
        },
        "graph": graph,
        "findings": findings,
    }
    write_json(WEEK3_REPORT_PATH, report)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())