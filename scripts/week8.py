#!/usr/bin/env python3
"""Focused Week 8 technical drawing quality command."""

from __future__ import annotations

import json

from week78 import ROOT, WEEK8_REPORT_PATH, write_reports


def main() -> int:
    report = write_reports()
    week8 = report["week8"]
    print(json.dumps({
        "status": week8["status"],
        "stamp": week8["stamp"],
        "findingCounts": week8["findingCounts"],
        "report": str(WEEK8_REPORT_PATH.relative_to(ROOT)),
    }, indent=2))
    return 0 if week8["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())