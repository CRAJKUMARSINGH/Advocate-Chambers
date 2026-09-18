"""Validate the structured architectural drawing source.

This intentionally checks the model before export. It does not certify code,
life safety, accessibility, structure, or construction suitability.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from drawing_model import load_model, validate_model


def main() -> int:
    site, plans = load_model()
    errors = validate_model(site, plans)
    report = {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "space_count": len(plans["spaces"]),
        "opening_count": len(plans["openings"]),
        "window_count": len(plans["windows"]),
        "stair_count": len(plans["stairs"]),
    }
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())