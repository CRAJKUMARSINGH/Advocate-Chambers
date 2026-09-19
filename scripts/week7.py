#!/usr/bin/env python3
"""Focused Week 7 rule-pack validation command."""

from __future__ import annotations

import json

from week78 import ROOT, WEEK7_REPORT_PATH, write_reports


def main() -> int:
    report = write_reports()
    week7 = report["week7"]
    print(json.dumps({
        "status": week7["status"],
        "findingCounts": week7["findingCounts"],
        "rulePack": week7["selectedRulePack"]["id"],
        "report": str(WEEK7_REPORT_PATH.relative_to(ROOT)),
    }, indent=2))
    return 0 if week7["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())