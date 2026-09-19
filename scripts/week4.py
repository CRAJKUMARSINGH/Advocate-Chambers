#!/usr/bin/env python3
"""Week 4 semantic openings, clearances, and schedule command."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bar-association-hall"))
sys.path.insert(0, str(ROOT / "scripts"))

from drawing_model import load_model  # noqa: E402
from week34 import (  # noqa: E402
    SCHEDULE_PATH,
    WEEK4_REPORT_PATH,
    validate_openings,
    write_json,
)


def main() -> int:
    site, plans = load_model()
    findings, schedule = validate_openings(site, plans)
    report = {
        "reportVersion": "week4.openings.v1",
        "status": "pass"
        if not any(item["severity"] in {"BLOCKER", "ERROR"} for item in findings)
        else "fail",
        "findingCounts": {
            severity: sum(1 for item in findings if item["severity"] == severity)
            for severity in ("BLOCKER", "ERROR", "WARNING")
            if any(item["severity"] == severity for item in findings)
        },
        "findings": findings,
    }
    write_json(WEEK4_REPORT_PATH, report)
    write_json(
        SCHEDULE_PATH,
        {
            "scheduleVersion": "week4.opening-schedule.v1",
            "status": report["status"],
            "openings": schedule,
        },
    )
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())