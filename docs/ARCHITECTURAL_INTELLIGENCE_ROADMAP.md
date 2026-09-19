# Architectural Intelligence Roadmap

**Repository:** Advocate-Chambers  
**Purpose:** Turn a parametric drawing generator into a reliable architectural planning assistant for residential, commercial, institutional, and industrial buildings.  
**Status:** Planning brief and phased implementation prompt.  
**Important:** This document governs preliminary planning quality. It does not replace a licensed architect, structural engineer, MEP consultant, fire consultant, survey, or approval by the local authority.

## 1. User brief preserved for the record

> My repo https://github.com/CRAJKUMARSINGH/Advocate-Chambers is aimed at drafting planning infrastructure plans in building sector residential commerial institutional and industrial>>> though prepared by nascent software engineers yet it prepared excellent drawingd>>> as peacock weeps when he sees his foot>>>> i am ashamed of app’s lack of building orientation basic concepts>>> one example >>> in first floor of bar associatiin building it provided a door on outer wall ( no access to the room from within) the building has no balcony>>> such plans make mockery of engineer>>> nobody can have access to such rooms$$$ so no beating about the bush>>> draft a markdown prompt so as to enrich the app>>> for drawing superior to leading ai tools loke maket.ai / planner5d / archistar/ floorplanner /riomstyler / homestyler / 4lines.ai / archiagent etc etc>>> make these in weekly doses with reasonable number of weeks>>> like>$$$Aisi drawing banane ka best tareeka
> 1. Maket.ai ya Planner 5D
>    - Text likho: "40x40 feet single storey house, 3 bedrooms, kitchen+dining 14x15, living 26x15, 5ft corridor, 2 walk-in closets, stairs in corner..."
>    - Furniture automatically place ho jata hai.
> 2. ChatGPT / Claude / Grok se detailed prompt do (main de sakta hoon agar chaho).
> 3. Existing plan upload karke improve karwana:
>    - Style2AI, Massing Labs, ArkViz, Planlift jaise tools plan image se better version bana dete hain.
> Aapke Bar Association Hall ke liye
> Jo professional SVGs maine banaye the woh schematic / line drawing level ke the (architect submission style).
> Agar aapko usi JSON se is tarah ki coloured + furniture wali presentation drawing chahiye (hall mein seating rows, dais, library tables, etc.), to bolo — main us style mein bhi generate kar sakta hoon.
> Short recommendation
> - Jaldi + furniture chahiye → Planner 5D ya Maket.ai
> - Professional architect look (black & white + dimensions) → jo maine SVG banaye, unko Inkscape mein polish karo
> - Full control + custom → mujhe exact room sizes + furniture list do, main SVG/PDF bana dunga
> Batao:
> 1. Sirf residential type tools ki list chahiye, ya

## 2. Master implementation prompt

You are the lead architectural-planning software engineer for Advocate-Chambers. Improve the existing Python parametric CAD pipeline and React editor in small, testable weekly increments.

The product is not a text-to-picture toy. It must first create and validate a buildable planning model, then render that model as CAD, dimensioned PDF, SVG, and an optional coloured presentation plan. A beautiful drawing containing an impossible room is a failed output.

### Non-negotiable product rule

**No room may be presented as usable unless the model proves how a person can reach it.**

For every room, the engine must answer:

- Which door serves it?
- What space or exterior path is on the other side of that door?
- Is there a continuous walkable route from an identified entry or vertical connector?
- Does the route pass through walls, locked/private rooms, stairs, furniture, or a missing landing?
- If the door opens to the exterior, is the exterior access intentional and modeled as a stair, ramp, balcony, terrace, porch, landing, or service path?
- If it is on an upper floor, how does the user reach that floor?

If the answer is unknown, block issue-ready output and show the exact room, opening, and missing connection. Do not silently invent a balcony, corridor, staircase, or external path.

### Quality bar

Compete on trustworthy planning intelligence, not visual polish alone. Outperform casual AI floor-plan tools on topology and reachability, floor-to-floor coordination, dimensions and clearances, explicit assumptions, deterministic regeneration, professional drawing conventions, and presentation plans with furniture that respects clearances.

Use leading tools as visual benchmarks only. Do not copy their claims, assets, or interfaces.

## 3. Current-repository alignment

Keep geometry authority in Python and the React app as the editor/review surface. Extend, do not bypass, these areas:

- bar-association-hall/drawing_model.py: validation entry point;
- bar-association-hall/standard/source/preliminary_plans.json: current source plan;
- bar-association-hall/standard/source/site_plan.json: site and orientation source;
- packages/schema/project.schema.json: shared model contract;
- scripts/traecad_engine.py and drawing generators: geometry and output;
- services/api/main.py: typed validation/generation API;
- apps/web/src/components/ValidationPanel.tsx: user-facing findings;
- apps/web/src/components/Viewport2D.tsx: visual review and error overlays.

Do not treat a successful PDF render as evidence that the plan is correct. Rendering is downstream of validation.

## 4. Finding severity and output policy

Implement four severities:

- BLOCKER: impossible or unsafe topology; no issue-ready drawing allowed.
- ERROR: violates a selected planning rule; generation may be allowed only as a clearly marked non-issuable preview.
- WARNING: unresolved assumption or likely coordination problem requiring professional review.
- INFO: traceability, design rationale, or presentation note.

Every finding needs a stable ID, severity, level/space/opening/connector references, human explanation, machine rule ID, and suggested correction. Example:

~~~json
{
  "id": "VAL-GRAPH-001",
  "severity": "BLOCKER",
  "rule": "ROOM_MUST_REACH_ENTRY",
  "levelId": "FF",
  "spaceId": "FF-07",
  "openingIds": ["D-FF-04"],
  "message": "FF-07 has an exterior door but no modeled balcony, landing, stair, corridor, or other reachable access path.",
  "suggestedFixes": [
    "Connect the room to the internal corridor",
    "Model an intentional balcony/landing and its approach",
    "Remove or relocate the exterior door"
  ]
}
~~~

Never hide a blocker because the user selected coloured presentation mode. Presentation mode may style valid geometry; it may not conceal invalid geometry.

## 5. Canonical planning model to grow toward

Extend the schema without breaking existing source files. Add explicit entities or equivalent fields for:

- Project, Site, North, Level, and floor-to-floor elevations;
- Space with use, privacy, occupancy, clear dimensions, area, access intent, and required adjacencies;
- Wall with host level, segments, thickness, and boundary type;
- Opening with host wall/space, type, width, sill/head, swing, direction, access intent, and connected space/exterior zone;
- CirculationZone for corridors, lobbies, stairs, ramps, balconies, porches, terraces, and accessible routes;
- VerticalConnector with lower level, upper level, footprint, riser/tread/landing data, and arrival zone;
- ExteriorAccessZone for plot, road, porch, balcony, service yard, ramp, and site path;
- FurnitureBlock and EquipmentBlock with clearance envelopes;
- RulePack, Assumption, ValidationFinding, Sheet, and Revision.

Prefer stable IDs and explicit references over guessing from proximity. Preserve source provenance for generated objects so the user can see what came from input, a rule, or an automatic suggestion.

## 6. Core validation rules

Implement these as deterministic, unit-tested rules. They must work for any building type, with configurable rule packs rather than hard-coded Bar Association assumptions.

### A. Geometry and topology

- No invalid or self-intersecting rooms, walls, or site boundaries.
- No unintended overlap between spaces, walls, stairs, shafts, furniture, or equipment.
- Every opening fits its host wall and creates a real wall break in generated geometry.
- A door must have a valid side A and side B: a named space, a circulation zone, or an intentional exterior access zone.
- A room cannot be reachable only through a private room unless explicitly allowed.
- A room cannot be marked usable with zero doors or only a window.
- The graph must distinguish a door to a corridor from a door directly to exterior.
- Detect disconnected subgraphs on every level and across vertical connectors.

### B. Circulation and access

- Build a walkable graph from rooms, corridors, lobbies, stairs, ramps, balconies, porches, and exterior paths.
- Prove a route from every occupied space to at least one permitted entry and, where configured, to an exit/egress route.
- An upper-floor room with an exterior door must have an intentional exterior access zone and a route to it. Otherwise emit ROOM_HAS_UNJUSTIFIED_EXTERNAL_DOOR as a BLOCKER.
- Do not call a wall-side door an access solution merely because it is geometrically inside the wall.
- Check corridor continuity, dead ends, bottlenecks, door clearances, and route width.
- Track public, staff, service, private, accessible, and emergency route classes.
- Show the route overlay and first broken edge when validation fails.

### C. Doors, windows, and openings

- Check door clear width, swing, approach space, latch side where configured, and conflicts with walls, furniture, stairs, and other door leaves.
- Check that outward-swinging doors have a landing or safe exterior approach.
- Check that a balcony/terrace door has the required balcony/landing object, not just a label.
- Windows must sit on a wall, fit within its span, and carry a ventilation/daylight intent or an explicit exception.
- Detect duplicate, orphaned, hidden, or contradictory opening definitions.
- Use standard tags and a legend; never draw a door as a decorative line with no semantic opening.

### D. Vertical coordination

- Stairs, ramps, lifts, and shafts must connect named levels, not merely appear as rectangles.
- Match lower arrival, upper arrival, and landing geometry.
- Validate riser arithmetic, tread count, flight count, landing depth, width, direction, headroom placeholder, and floor-to-floor height.
- Ensure the upper-floor route reaches the connector arrival space.
- Flag rooms drawn on a level with no path from the level entrance.
- Show a section/coordination warning when floors, stairs, shafts, or wet areas do not align.

### E. Basic planning and building orientation

- Require north, road/frontage, plot boundary, setbacks, entry intent, and site orientation before site-aware generation.
- Keep public entry, staff/service entry, loading/service access, fire access, and accessible entry distinct where applicable.
- Check room dimensions and area against selected program, not arbitrary visual proportions.
- Add configurable daylight, ventilation, wet-area stacking, service shaft, and refuse/service-zone checks.
- Keep code values in versioned rule packs. Never present a local-code guess as universal compliance.

### F. Furniture and presentation

- Furniture is placed only after validated room geometry exists.
- Use reusable blocks for beds, desks, seating rows, dais, library tables, counters, toilets, kitchen units, and equipment.
- Every block has a footprint and clearance envelope; furniture must not block doors, required routes, stairs, or emergency paths.
- Colour is semantic: circulation, public, staff, service, wet, structure, and warning layers remain legible in print.
- Offer technical review drawing and coloured presentation drawing.
- The presentation drawing must retain north arrow, scale, room names, key dimensions, door swings, stair direction, and a validation status stamp.

## 7. Explainable generation workflow

Implement this sequence and expose it in the UI:

1. Capture brief: site, orientation, building type, levels, room program, access rules, occupancy, and preferences.
2. Normalize units and convert the brief into a typed planning model.
3. Generate one or more candidate layouts using explicit constraints.
4. Validate geometry, topology, circulation, vertical connections, code-pack checks, and furniture clearances.
5. Show findings and route overlays before allowing issue-ready output.
6. Let the user accept, reject, or edit a proposed correction.
7. Regenerate deterministically with a revision record.
8. Export technical sheets, coloured presentation sheets, JSON, manifest, and validation report.

The UI should explain why a room was placed, moved, rejected, or flagged. Avoid a black-box magic regenerate button.

## 8. Weekly delivery plan

### Week 1 — Baseline, fixtures, and honest status

- Freeze the current Bar Association source as a golden fixture.
- Add repeatable validation command and machine-readable JSON report.
- Add tests for orphan room, external door without access zone, overlapping rooms, invalid opening, and stair arithmetic.
- Add visible PRELIMINARY / NOT FOR CONSTRUCTION status to generated sheets.
- Record current output hashes and create a regression manifest.

Gate: the known inaccessible upper-floor-room example fails with a precise BLOCKER, and a valid fixture still renders unchanged.

### Week 2 — Schema foundation and migration

- Add levels, room use, access intent, circulation zones, exterior zones, and vertical connector references.
- Add stable IDs and source provenance.
- Write a migration for current JSON; do not manually fork the model.
- Validate schema before geometry generation.

Gate: old source files migrate into the new model and round-trip without losing rooms, openings, stairs, notes, or revisions.

### Week 3 — Reachability graph

- Build the per-level and cross-level walkable graph.
- Resolve door side A/side B and intentional exterior access.
- Add connected-component and route-to-entry checks.
- Add route overlay and first-broken-edge diagnostics in the React viewport.

Gate: every occupied room has a proven route or a named finding explaining why it does not.

### Week 4 — Openings, door swings, and clearances

- Replace decorative opening assumptions with semantic wall breaks.
- Check door widths, swings, approach zones, landing zones, and furniture conflicts.
- Add balcony, terrace, porch, and landing semantics and prohibit implied access.
- Add opening schedules and stable tags to exports.

Gate: a door cannot make a room accessible unless both sides of the opening are valid and connected.

### Week 5 — Stairs and floor-to-floor coordination

- Model stair arrivals and departures as graph nodes.
- Validate floor-to-floor height, risers, treads, landings, width, direction, and route continuity.
- Add section coordination warnings and upper-floor access tests.
- Add future-ready interfaces for ramp and lift connectors.

Gate: an upper-floor room is reachable through a validated connector, and stair changes cannot silently disconnect the plan.

### Week 6 — Program, adjacencies, and orientation

- Add building-type templates for residential, commercial, institutional, and industrial planning.
- Capture required, preferred, and forbidden adjacencies.
- Add site orientation, road/frontage, north, setbacks, entry intents, and service access.
- Implement program completeness and area/dimension checks.

Gate: the generator can explain why a room is near or away from another room and flags missing program elements before rendering.

### Week 7 — Rule packs and professional disclaimers

- Move dimensions and planning assumptions into versioned, inspectable rule packs.
- Add configurable accessibility, egress, daylight, ventilation, wet-area, and service checks.
- Separate universal geometry rules from jurisdiction-specific rules.
- Display selected rule pack, date, assumptions, and unresolved professional-review items on the report.

Gate: changing a rule pack changes findings predictably without changing geometry code or hiding unresolved assumptions.

### Week 8 — Technical drawing quality

- Improve wall hierarchy, line weights, hatches, doors, windows, stairs, dimensions, room labels, legends, title blocks, north arrows, scales, and sheet references.
- Add plan, section, and elevation consistency checks.
- Add sheet-level validation stamp: VALIDATED FOR PRELIMINARY REVIEW, or NOT ISSUABLE.
- Preserve DXF, PDF, and SVG determinism.

Gate: a reviewer can read the sheet without the web UI, and every visible opening, room, and stair is traceable to the model.

### Week 9 — Furniture and coloured presentation mode

- Add furniture and equipment libraries with scale, use, occupancy, and clearance envelopes.
- Add occupancy-aware seating layouts for halls, chambers, offices, classrooms, libraries, and waiting areas.
- Render a separate presentation sheet from the same validated model.
- Never let presentation furniture alter authoritative room or wall geometry without an explicit edit.

Gate: coloured plans look useful while preserving technical labels, route visibility, and validation status.

### Week 10 — Candidate comparison, QA, and release discipline

- Generate multiple candidates with deterministic seeds and compare them by score.
- Score area fit, adjacency satisfaction, route quality, daylight/ventilation checks, structural/service coordination, and furniture fit.
- Add golden fixtures for each building type and property-based geometry tests.
- Add a release checklist, export manifest, changelog, and failure screenshots.
- Document what the tool can and cannot certify.

Gate: no candidate marked best can contain a BLOCKER; every exported artifact has a matching model revision and validation report.

## 9. Acceptance test examples

1. Orphaned upper-floor room: first-floor room has a door on the outer wall, no internal door, and no balcony/landing/stair/path. Result: BLOCKER ROOM_HAS_UNJUSTIFIED_EXTERNAL_DOOR.
2. Valid balcony access: the same room has a modeled balcony, a valid upper-floor corridor or stair approach, a landing, and an intentional exterior route. Result: no topology blocker; code/accessibility warnings remain configurable.
3. Door into a wall: an opening exceeds its host span or does not produce a wall break. Result: ERROR.
4. Door swing conflict: a door leaf blocks a required corridor or another opening. Result: ERROR or BLOCKER according to the selected rule pack.
5. Disconnected floor: an upper floor has rooms but no connector to the entry level. Result: BLOCKER.
6. Stair mismatch: riser count multiplied by riser height does not equal floor-to-floor height. Result: ERROR.
7. Furniture blockage: a desk, seating row, or library table blocks the only route or door approach. Result: ERROR.
8. Valid service room: pantry, toilet, or service room is reachable through the intended service route and does not accidentally become the only public route. Result: pass with traceable route class.
9. Deterministic output: identical model, rule pack, and seed produce identical geometry, tags, manifest, and validation findings.
10. Presentation honesty: coloured output includes the same validation status as technical output and cannot suppress blockers.

## 10. Definition of done for every weekly dose

- Source model, schema, validator, API, UI, and renderer agree on IDs and units.
- At least one regression fixture is added for every new rule.
- A failing case includes a readable explanation and a suggested correction.
- A passing case proves the rule does not reject valid geometry.
- Technical and presentation outputs come from the same validated model.
- No code claim is made without a named rule pack and professional-review disclaimer.
- The change is deterministic, documented, and reversible.

## 11. Final instruction to the implementation agent

Do not optimize for producing more drawings. Optimize for preventing impossible drawings.

When a request is underspecified, ask for the smallest missing fact that changes topology: entry location, level connection, exterior access intent, room use, required adjacency, or applicable rule pack. If a reasonable assumption is used, write it into the model and title block. Never turn an assumption into an invisible wall, door, balcony, stair, or route.

The winning product experience is:

**brief → model → validate → explain → correct → render → export**

not:

**brief → decorate → export**
