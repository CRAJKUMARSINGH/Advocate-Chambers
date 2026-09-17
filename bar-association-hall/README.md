# Bar Association Banswara - G+1 Building Plan

**Project:** Advocate Chambers & Bar Association Hall  
**Location:** Banswara, Rajasthan  
**Plot shape:** L-shaped irregular polygon  
**Source:** User-provided hand-drawn site plan and planning brief  

> Planning package only: dimensions, room layouts, structural notes, services, and cost figures must be verified by a licensed architect/engineer, site survey, and the competent local authority before construction or statutory submission.

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

The rationalized plot polygon is stored in `site_plan.json` in feet. The brief states approximately 4,785 sq ft of net buildable area per floor; `validate_plan.py` reports the area implied by the stored coordinates and flags any difference for review.

## Floors

- **Ground floor:** Bar Association Banswara Hall with reception, assembly hall, dais, pantry, toilets, first-aid, store, and electrical/server facilities.
- **First floor:** Bar Library + Pantry with reading room, stack area, librarian/admin room, discussion and computer rooms, toilets, and support spaces.

## Package contents

- `site_plan.json` - Plot geometry, setbacks, stated planning area, and floor program.
- `ground_floor_layout.md` - Ground-floor room schedule and planning notes.
- `first_floor_layout.md` - First-floor room schedule and planning notes.
- `amenities.md` - Shared sanitary, utility, accessibility, and safety provisions.
- `structural_grid.md` and `structural_grid.json` - Conceptual RCC grid and framing assumptions.
- `electrical_plumbing_layout.md` - Concept-level MEP requirements.
- `estimate_plinth_area.md` - Revised ₹1,850/sq ft planning estimate.
- `SOURCE_IMAGE.md` - Metadata and provenance for the attached hand-drawn site plan.
- `traecad_engine.py` - Generates a PNG envelope diagram and DXF boundary from `site_plan.json`.
- `validate_plan.py` - Standard-library geometry and area consistency check.
- `generate_zip.sh` and `generate_zip.ps1` - Optional local package archive helpers.

## Safety and compliance notes

- The west wall is planned at zero setback: treat it as a blank, independently supported, waterproofed wall subject to local fire and boundary-wall rules.
- Natural light and ventilation are planned from the north, south, and east sides only.
- Toilet and pantry stacks are aligned conceptually between floors to simplify services.
- References to NBC India 2016, RPwD requirements, or fire provisions are design references, not a compliance certificate.

## Run the local checks

From the repository root:

    python bar-association-hall/validate_plan.py
    python bar-association-hall/traecad_engine.py

The generator writes optional outputs to `bar-association-hall/generated/` and requires the packages listed in `requirements.txt`.
