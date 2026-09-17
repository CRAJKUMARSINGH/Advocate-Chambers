# Bar Association Banswara - G+1 Building Plan

**Project:** Advocate Chambers & Bar Association Hall  
**Location:** Banswara, Rajasthan  
**Plot shape:** L-shaped irregular polygon  
**Status:** Planning package with refined preliminary review plans  

> Planning package only: dimensions, room layouts, structural notes, services, and cost figures must be verified by a licensed architect/engineer, site survey, and the competent local authority before construction or statutory submission.

## Refined preliminary plans

- `ground_floor_preliminary.svg` - Coordinated ground-floor review plan.
- `first_floor_preliminary.svg` - Coordinated first-floor review plan.
- `preliminary_plan_review.md` - Design basis, room schedules, and review checklist.
- `preliminary_plans.json` - Coordinate source for both plan drawings.

The refined drawings use the simple coordinate setback envelope of **4,427.5 sq ft per floor**. The brief's earlier **4,785 sq ft** figure is retained in the estimate as an unresolved assumption and is intentionally not used to inflate these preliminary layouts.

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

The generator writes optional outputs to `bar-association-hall/generated/` and requires the packages listed in `requirements.txt`.
