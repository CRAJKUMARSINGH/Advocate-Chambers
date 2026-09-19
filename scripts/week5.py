#!/usr/bin/env python3
"""Focused Week 5 stair and floor-to-floor coordination command."""

from __future__ import annotations

import json
from week56 import ROOT, WEEK5_REPORT_PATH, write_reports


def main() -> int:
    report = write_reports()
    week5 = report["week5"]
    print(
        json.dumps(
            {
                "status": week5["status"],
                "findingCounts": week5["findingCounts"],
                "report": str(WEEK5_REPORT_PATH.relative_to(ROOT)),
            },
            indent=2,
        )
    )
    return 0 if week5["status"] == "pass" else 1

if __name__ == "__main__":
    raise SystemExit(main())