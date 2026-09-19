# Bar Association Banswara - G+1 Building Plan

**Project:** Advocate Chambers & Bar Association Hall  
**Location:** Banswara, Rajasthan  
**Plot shape:** L-shaped irregular polygon  
**Status:** Dimensioned architectural preliminary review package

> Planning package only: dimensions, room layouts, structural notes, services, and cost figures must be verified by a licensed architect/engineer, site survey, and the competent local authority before construction or statutory submission.

## Week 1 — Baseline, fixtures, and honest status: DONE

Week 1 implementation is complete and included in the repository:

- Structured validation findings with stable rule IDs and `BLOCKER` / `ERROR` severity.
- Regression tests for orphan rooms, unjustified upper-floor exterior doors, overlapping rooms, invalid openings, and stair arithmetic.
- Golden source and CAD/PDF artifact hashes in `standard/regression_manifest.json`.
- Machine-readable validation output in `standard/week1-validation-report.json`.
- Generated sheets marked `PRELIMINARY REVIEW ONLY — NOT FOR CONSTRUCTION`.
- Existing legacy CAD/PDF paths preserved; no binary migration or history rewrite performed.

Run the Week 1 checks from the repository root:

    python3 -m unittest discover -s tests -p 'test_week1*.py'
    python3 scripts/week1.py verify-manifest
    python3 scripts/week1.py validate --write-report

The current source correctly reports a non-issuable baseline because the known
upper-floor external-door condition remains unresolved, including `FF-07 /
D-FF-07`. This is recorded as a precise `ROOM_HAS_UNJUSTIFIED_EXTERNAL_DOOR`
`BLOCKER`, not treated as a pass.

## Refined preliminary plans

- `ground_floor_preliminary.svg` - Coordinated ground-floor review plan.
- `first_floor_preliminary.svg` - Coordinated first-floor review plan.
- `derived_g_plus_1_plan.pdf` - Printable five-page derived plan set with site diagram, floor plans, area reconciliation, cost basis, and review actions.
- `preliminary_plan_review.md` - Design basis, room schedules, and review checklist.
- `preliminary_plans.json` - Coordinate source for both plan drawings.
- `generate_plan_pdf.py` - Rebuilds the derived PDF from the JSON inputs using the local Chromium print path.

The refined drawings use the simple coordinate setback envelope of **4,427.5 sq ft per floor**. The brief's earlier **4,785 sq ft** figure is retained in the estimate as an unresolved assumption and is intentionally not used to inflate these preliminary layouts.

The derived PDF follows the coordinate-based 4,427.5 sq ft envelope. It is a planning study, not a construction, approval, fire-NOC, or structural drawing.

Revision B makes the circulation explicit: the hall entry is centered on the south long wall, and the stair has an independent 4'-0" clear exterior entry for first-floor visitors. The stair note separates the 4'-0" clear flight width from the 11" tread depth.

## Plot and setbacks

| Item | Planning value |
| --- | --- |
| North width | 60'-0" |
| South width | 35'-0" |
| West depth | 98'-0" |
| East step | 12'-0" top + 16'-6" bottom (as stated in the brief) |
| West setback | 0'-0" |
| North setback | 5'-0" |
| South setback | 5'-0" |
| East setback | 5'-0" |

## Package contents

- `site_plan.json` - Plot geometry, setbacks, stated planning area, and floor program.
- `ground_floor_layout.md` and `first_floor_layout.md` - Refined room schedules and planning notes.
- `amenities.md` - Shared sanitary, utility, accessibility, and safety provisions.
- `structural_grid.md` and `structural_grid.json` - Conceptual RCC grid and framing assumptions.
- `electrical_plumbing_layout.md` - Concept-level MEP requirements.
- `estimate_plinth_area.md` - Revised ₹1,850/sq ft planning estimate.
- `SOURCE_IMAGE.md` - Metadata and provenance for the attached hand-drawn site plan.
- `traecad_engine.py` - Generates a PNG envelope diagram and DXF boundary from `site_plan.json`.
- `validate_plan.py` - Standard-library geometry and area consistency check.

## Run the local checks

    python3 bar-association-hall/validate_plan.py
    python3 bar-association-hall/traecad_engine.py
    python3 scripts/week2.py validate
    python3 scripts/week2.py roundtrip

The generator writes optional outputs to `bar-association-hall/generated/` and requires the packages listed in `requirements.txt`.

## Week 2 enrichment — complete

Week 2 schema foundation and migration have been applied and merged to the
repository's `main` branch. The legacy Week 1 JSON remains the auditable source
input, while `standard/model/project.json` is the generated canonical v2 model.
It now carries explicit levels, room use, access intent, circulation zones,
exterior entry zones, vertical connector references, stable IDs, and source
provenance. The drawing loaders validate this canonical model before exposing
geometry to the generators.

The migration is deterministic and round-trips the existing rooms, openings,
windows, entries, stairs, notes, levels, and revisions without loss:

    python3 scripts/week2.py migrate
    python3 scripts/week2.py validate
    python3 scripts/week2.py roundtrip

The source is still preliminary planning information and remains subject to
licensed architectural, structural, fire, accessibility, survey, and authority
review. Week 2 does not make the drawings construction-ready.
