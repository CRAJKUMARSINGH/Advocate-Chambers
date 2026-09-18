# Preliminary Plan Review - Refined G+1 Scheme

**Revision:** B  |  **Status:** Dimensioned architectural preliminary review  |  **Units:** Feet

> This is an architectural preliminary review drawing set, not a construction drawing, approval drawing, fire NOC drawing, or structural design. Have the final scheme checked against a site survey, local bylaws, NBC/RPwD requirements, fire strategy, structure, and services.

## Review drawings

- `ground_floor_preliminary.svg` - Public entry, assembly hall, dais, service core, and review exit.
- `first_floor_preliminary.svg` - Library, stack area, admin, discussion, computer, and stacked service core.
- `derived_g_plus_1_plan.pdf` - Printable five-page summary derived from the stored JSON geometry and room schedules.
- `preliminary_plans.json` - Coordinate source for the room rectangles and review notes.
- `generate_plan_pdf.py` - Regenerates the PDF and architectural SVG plans.

## Design basis

- Rationalized plot polygon: `(0,0) -> (35,0) -> (35,16.5) -> (60,16.5) -> (60,98) -> (0,98)`.
- Setbacks: west 0'-0", north 5'-0", south 5'-0", east 5'-0".
- Simple coordinate envelope used for this revision: `(0,5) -> (30,5) -> (30,21.5) -> (55,21.5) -> (55,93) -> (0,93)`.
- Calculated envelope area: **4,427.5 sq ft per floor**. The brief's 4,785 sq ft figure remains an unresolved planning assumption and is not used to stretch the rooms in these drawings.
- Architectural convention: 9" external walls, 4-1/2" internal walls, and dimensioned doors/egress annotations.
- Stair: dog-leg RCC stair with **4'-0" clear flight width**, 11" tread, 6-2/3" riser, two 4'-0" landings, and 18 risers for the assumed 10'-0" floor-to-floor height. The 4'-0" dimension is not a tread depth.

## Area reconciliation

| Measure | Area |
| --- | ---: |
| Polygon area from stored coordinates | 5,467.5 sq ft |
| Simple coordinate setback envelope | 4,427.5 sq ft per floor |
| Earlier area carried in the planning brief | 4,785 sq ft per floor |

The 4,785 sq ft figure should not be used for procurement, sanction, or cost commitment until the site is surveyed and a true inward polygon offset is checked by the architect.

## Ground-floor schedule

| ID | Space | Coordinates (x, y) | Size | Area |
| --- | --- | --- | --- | ---: |
| GF-01 | Reception / Records | (0, 5) | 9' x 16'-6" | 148.5 sq ft |
| GF-02 | Dog-leg Stair Core | (9, 5) | 12' x 16'-6" | 198 sq ft |
| GF-03 | Toilet Block | (21, 5) | 9' x 16'-6" | 148.5 sq ft |
| GF-04 | Entry Lobby / Public Circulation | (0, 21.5) | 30' x 8' | 240 sq ft |
| GF-05 | Pantry | (30, 21.5) | 10' x 8' | 80 sq ft |
| GF-06 | Main Assembly Hall | (0, 29.5) | 55' x 49' | 2,695 sq ft |
| GF-07 | Dais / Speaker Zone | (0, 78.5) | 55' x 14'-6" | 797.5 sq ft |
| | **Programmed room area** | | | **4,307.5 sq ft** |

## First-floor schedule

| ID | Space | Coordinates (x, y) | Size | Area |
| --- | --- | --- | --- | ---: |
| FF-01 | Librarian / Admin | (0, 5) | 9' x 16'-6" | 148.5 sq ft |
| FF-02 | Dog-leg Stair Core | (9, 5) | 12' x 16'-6" | 198 sq ft |
| FF-03 | Toilet Block | (21, 5) | 9' x 16'-6" | 148.5 sq ft |
| FF-04 | Library Lobby / Circulation | (0, 21.5) | 30' x 8' | 240 sq ft |
| FF-05 | Pantry | (30, 21.5) | 10' x 8' | 80 sq ft |
| FF-06 | Library Reading Room | (0, 29.5) | 55' x 35' | 1,925 sq ft |
| FF-07 | Stack Area / Book Storage | (0, 64.5) | 55' x 18' | 990 sq ft |
| FF-08 | Discussion Room | (0, 82.5) | 18' x 10'-6" | 189 sq ft |
| FF-09 | Computer / Internet | (18, 82.5) | 18' x 10'-6" | 189 sq ft |
| FF-10 | Store / Electrical | (36, 82.5) | 19' x 10'-6" | 199.5 sq ft |
| | **Programmed room area** | | | **4,307.5 sq ft** |

## Decisions carried into this revision

1. The main public entry is at the south, through a reception/records vestibule.
2. The main hall entry is centered on the hall's 55'-0" south long wall and reached through the public lobby.
3. The stair has an independent 4'-0" clear external entry from the south, so first-floor visitors do not enter through the ground-floor hall.
4. The stair, pantry, and toilet block are aligned between floors to reduce service complexity.
5. The west zero-setback wall is shown without openings.
6. The ground-floor hall has a central aisle and northern dais; the first floor keeps the same upper-wing footprint for a flexible reading room and stack zone.
7. An east-side exit is marked as a review placeholder, not as an approved fire exit.
8. The stair is dimensioned architecturally as a 4'-0" clear public stair flight; the tread depth is separately set at 11".

## Items for the preliminary review meeting

- Confirm the surveyed plot dimensions: the attached sketch and later rationalized brief contain different dimension sets.
- Confirm whether 0' west setback is legally and practically permissible, including fire separation, waterproofing, scaffolding, and maintenance access.
- Confirm occupant capacity, number and width of exits, travel distances, stair width, stair headroom, accessible route, and toilet clearances.
- Confirm structural grid, column locations, floor-to-floor height, foundation system, and any soil/retaining requirement.
- Confirm daylight/ventilation strategy on the north, south, and east faces.
- Reprice the estimate only after the area, room schedule, structure, MEP, finishes, and statutory scope are fixed.
