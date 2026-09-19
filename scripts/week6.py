#!/usr/bin/env python3
"""Focused Week 6 program, adjacency, and orientation command."""

from __future__ import annotations

import json

from week56 import ROOT, WEEK6_REPORT_PATH, write_reports


def main() -> int:
    report = write_reports()
    week6 = report["week6"]
    print(
        json.dumps(
            {
                "status": week6["status"],
                "findingCounts": week6["findingCounts"],
                "report": str(WEEK6_REPORT_PATH.relative_to(ROOT)),
            },
            indent=2,
        )
    )
    return 0 if week6["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())