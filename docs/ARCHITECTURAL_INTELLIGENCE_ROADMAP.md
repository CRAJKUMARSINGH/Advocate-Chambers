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

### Week 1 implementation note

The first implementation slice is now wired into the repository:

- `python scripts/week1.py validate --write-report` emits
  `bar-association-hall/standard/week1-validation-report.json`.
- `python -m unittest discover -s tests -p 'test_week1*.py'` covers orphan rooms,
  unjustified upper-floor exterior doors, overlapping rooms, invalid openings,
  and stair arithmetic.
- `python scripts/week1.py manifest --write` records source and existing
  CAD/PDF artifact SHA-256 hashes in
  `bar-association-hall/standard/regression_manifest.json`.
- `python scripts/week1.py verify-manifest` blocks a checksum mismatch or
  missing artifact.
- Generated title blocks use `PRELIMINARY REVIEW ONLY | NOT FOR CONSTRUCTION`.

The golden source now reports `pass` after the Week 3–8 topology correction
pass. `FF-07` / `D-FF-07` is recognized as an internal opening to the library
stack route rather than being misclassified as an exterior door. Synthetic
orphan fixtures continue to prove that the original blocker is still detected
when the adjacent route is absent. Legacy binaries remain in place; no history
rewrite or bulk move is part of Week 1.

### Week 2 — Schema foundation and migration

- Add levels, room use, access intent, circulation zones, exterior zones, and vertical connector references.
- Add stable IDs and source provenance.
- Write a migration for current JSON; do not manually fork the model.
- Validate schema before geometry generation.

Gate: old source files migrate into the new model and round-trip without losing rooms, openings, stairs, notes, or revisions.

### Week 2 implementation note

The Week 2 foundation is now implemented:

- `scripts/week2.py migrate` deterministically creates
  `bar-association-hall/standard/model/project.json` using the canonical
  `advocate-chambers.project.v2` model.
- `packages/schema/project-v2.schema.json` documents the canonical contract.
- Every migrated level and drawable carries a stable ID, source path, source ID,
  migration version, legacy keys, status, and revision.
- Spaces now carry `roomUse` and `accessIntent`; circulation zones, exterior
  entry zones, and vertical connector references are explicit model objects.
- `scripts/week2.py roundtrip` proves that the existing rooms, openings,
  windows, entries, stairs, notes, levels, and revisions survive migration
  without loss.
- The drawing model loader validates the canonical model before handing the
  compatibility-shaped view to geometry generators.

The existing Week 1 source remains the auditable legacy input. Week 2 does not
silently repair topology; the explicit Week 3–5 correction pass resolves
reachable internal openings and the stair arrival route while preserving the
legacy round-trip.

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

### Week 3–4 implementation note

Week 3 and Week 4 enrichment is now applied:

- `scripts/week34.py` derives semantic side A/side B opening data, builds a
  deterministic per-level/cross-level route graph, reports connected
  components and first-broken-edge diagnostics, and writes the opening
  schedule.
- `scripts/week3.py` and `scripts/week4.py` provide focused validation
  commands.
- The canonical model stores additive opening semantics without changing the
  Week 2 legacy round-trip. Reports are written to
  `bar-association-hall/standard/`.
- FastAPI `/analysis` exposes the graph, routes, findings, and opening schedule
  to the React viewport. Unreachable rooms are visibly marked and route edges
  are overlaid.
- The current legacy fixture passes the route and opening gates after the
  correction pass. Synthetic fixtures still fail when access intent, landing
  data, or connected openings are absent, preserving the expected auditable
  blocker behavior.

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

### Week 5–6 implementation note

Week 5 and Week 6 enrichment is now applied:

- `scripts/week5.py` and `scripts/week56.py` validate stair endpoints,
  floor-to-floor arithmetic, risers, treads, landings, widths, direction,
  connector graph edges, and upper-floor route continuity.
- `scripts/week6.py` and `scripts/week56.py` add versioned building-type
  templates, required room-use completeness, area/dimension checks,
  required/preferred/forbidden adjacency evaluation, and site
  north/frontage/service-access assumptions.
- Reports are written to
  `bar-association-hall/standard/week5-stair-coordination-report.json`,
  `bar-association-hall/standard/week6-program-report.json`, and
  `bar-association-hall/standard/week56-enrichment-manifest.json`.
- The canonical model stores the additive `program`, `orientation`, and
  `adjacencies` layer, while `/analysis` exposes the same data to the React
  viewport.

The current legacy fixture passes the Week 3–5 access and stair gates. Week 6
passes the institutional program completeness and dimension gate while warning
about unconfirmed site frontage and service access.

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


---

# Phase Two — Competitive product enrichment

**Purpose:** Add the strongest useful capabilities observed in current AI floor-plan, interior-design, architectural-modelling, and plan-review products, without weakening the geometry and circulation discipline established in Phase One.

**Schedule:** 8 weekly doses after Phase One.  
**Positioning:** Make Advocate-Chambers easier and more visually capable than casual design tools, while making it more trustworthy than image-first AI generators.

## 12. Feature intelligence taken from the named tools

The following capabilities were checked against public product pages. They are used as feature patterns, not copied branding or code.

| Product pattern | Capability to learn from it | Advocate-Chambers implementation | Superior version for this product |
|---|---|---|---|
| Maket | Generate a plan from a natural-language brief; draw from scratch; upload an existing plan; refine by text; view in 3D; export PDF/DXF | Brief compiler, editable model, import pipeline, conversational edit commands, technical exports | Every text edit becomes a reviewable model revision and is revalidated before export |
| Planner 5D | Generate and compare layouts; furnish spaces; create moodboards, collages, colour palettes; modify images and improve visualizations | Candidate studio, presentation boards, materials, finishes, image/reference workflow | Compare alternatives using circulation, area, adjacency, clearance, and presentation scores—not appearance alone |
| Floorplanner | Accurate 2D planning, real-time 3D, digital-twin workflow, extensive model library, high-resolution renders | Synchronized 2D/3D viewport, reusable object library, render queue | 2D, 3D, CAD geometry, validation findings, and route overlays all come from one canonical model |
| Homestyler | Convert an uploaded plan or sketch into an editable 3D model; drag-and-drop furnishing; templates; cloud rendering | Plan recognition/import, furniture catalog, room templates, render service | Imported geometry is measured, tagged, and flagged for uncertainty before it can become authoritative |
| Roomstyler | Build/furnish/decorate workflow; 2D/3D views; real furniture items; 3D photos; panoramas and VR-style presentation | Design modes, real-scale assets, camera presets, panorama export | Furniture placement checks door swings, route widths, occupancy, and room function before presentation |
| Archistar | Site context, aerial/site information, building types, feasibility, environmental metrics, planning-rule checks, transparent plan-review reports, PDF/CAD/BIM review | Site feasibility workspace, rule packs, scorecards, visual review reports, future BIM bridge | Show the rule, source, calculation, confidence, and unresolved professional decision for every finding |
| Archiagent | Millimetre-scale plans, live dimensions, multi-storey 3D, parametric walls/doors/windows/stairs/roofs, scaled furnishing, self-audit | Parametric object tools, live dimensions, 3D building view, furniture clearance audit | Self-audit runs after every material edit and blocks impossible geometry before it reaches the render stage |
| 4Lines.ai | Browser CAD/BIM workflow, floors, stairs, slabs, roofs, snapping, sections/elevations/3D, IFC/DXF import, construction phases, model-to-render comparison | Multi-level model workspace, snapping, import/export, phase layers, section/elevation views, render comparison | Preserve explicit architectural semantics and validation provenance through every import, edit, and export |

**Important limitation:** marketing pages describe product capabilities, not proof of code compliance or construction readiness. Advocate-Chambers must never convert a competitor feature into a compliance promise.

## 13. Phase Two product objectives

By the end of Phase Two, a user should be able to:

1. Describe a building in plain language and receive a structured, editable brief.
2. Upload a PDF, image, DXF, or supported BIM exchange file and see what was confidently recognized and what requires confirmation.
3. Edit the model in 2D while seeing synchronized 3D, sections, elevations, dimensions, and route overlays.
4. Generate several valid layout candidates and compare them on a transparent scorecard.
5. Furnish a validated plan with scaled objects, clearances, materials, and presentation styles.
6. Test site and rule-pack feasibility with visual, traceable reports.
7. Share a client-friendly presentation without hiding technical warnings.
8. Export a consistent technical package whose model, validation report, and render all refer to the same revision.

## 14. Phase Two weekly doses

### Week 11 — Competitive capability layer and product modes

- Add explicit product modes: Brief, Model, Validate, Furnish, Present, and Export.
- Add feature flags for import, 3D, candidate comparison, materials, site feasibility, and collaboration.
- Create a capability matrix in the UI showing what is available, what is provisional, and what requires professional review.
- Add telemetry-free local performance counters: model size, validation duration, render duration, and export duration.
- Keep all new features behind the same canonical project model.

**Gate:** a user can see where each feature operates and cannot accidentally treat a presentation-only object as authoritative building geometry.

### Week 12 — Conversational brief compiler

- Accept natural-language briefs in metric or imperial units.
- Extract site dimensions, north, road/frontage, levels, floor-to-floor heights, room schedule, area targets, access intent, occupancy, adjacencies, style, and required outputs.
- Display extracted facts, assumptions, ambiguities, and missing topology facts before generation.
- Support commands such as “move the stair beside the lobby,” “give the library a public route,” and “remove the outer door unless a balcony is modeled.”
- Convert every accepted command into a typed revision, not an untracked prompt mutation.

**Gate:** the system asks for or marks missing facts that change circulation before generating a plan.

### Week 13 — Import, recognition, and editable digital twin

- Import PDF/image plans for assisted recognition and DXF for geometry-preserving import.
- Add optional IFC/BIM exchange support behind a clear capability flag.
- Recognize walls, rooms, doors, windows, stairs, text labels, dimensions, and north arrows with confidence values.
- Put uncertain objects into a review queue; never silently promote uncertain recognition to authoritative geometry.
- Show before/after comparison between source drawing and editable model.

**Gate:** a plan can be imported, reviewed, corrected, and exported without losing scale, levels, openings, or source provenance.

### Week 14 — Synchronized 2D, 3D, sections, and elevations

- Add a real-time 2D/3D split view with shared selection and highlighting.
- Add orbit, walk-through, camera presets, level visibility, section box, and isolated-room views.
- Generate simple sections and elevations from the same model, including floor levels, openings, stairs, roofs, and key dimensions.
- Add snapping to grid, endpoints, midpoints, intersections, walls, and reference lines.
- Show route overlays and validation markers in every view.

**Gate:** moving a wall, door, or stair updates all dependent views and reruns validation without stale geometry.

### Week 15 — Parametric assets, furniture, and clearance-aware furnishing

- Create a catalog system for furniture, fixtures, appliances, sanitaryware, seating rows, dais, library tables, counters, vehicles, and industrial equipment.
- Store dimensions, rotation rules, preferred wall relationships, service-side requirements, occupancy, and clearance envelopes.
- Support drag, rotate, duplicate, align, replace, and “find a valid position” operations.
- Add room-type templates for residential, offices, chambers, halls, classrooms, libraries, healthcare, retail, and light industrial use.
- Separate presentation furniture from construction geometry while preserving scale and access checks.

**Gate:** one-click furnishing never places an object over a door swing, required route, stair, service zone, or minimum clear area.

### Week 16 — Candidate studio, moodboards, materials, and render pipeline

- Generate several layout candidates from the same brief with deterministic seeds.
- Compare candidates using area fit, adjacency satisfaction, route quality, daylight/ventilation checks, vertical coordination, furniture fit, and visual quality.
- Add moodboards, reference images, colour palettes, materials, finishes, lighting presets, and style tags.
- Add non-destructive design layers so materials and decor cannot alter validated walls or openings.
- Add 3D render, panorama, and presentation-sheet jobs with progress and artifact manifests.
- Show technical plan beside presentation render so users can audit whether the image matches the model.

**Gate:** the visually attractive candidate cannot win by hiding a BLOCKER; render output is traceable to a valid model revision.

### Week 17 — Site feasibility, rule packs, and transparent plan review

- Add a site workspace with plot, north, road/frontage, setbacks, access points, building footprint, levels, and context layers.
- Add rule-pack checks for coverage, setbacks, height, floor-area targets, parking, accessibility, daylight, ventilation, egress, fire access, service access, and wet-area coordination where data is available.
- Add a feasibility dashboard with pass, fail, unknown, and professional-review states.
- Make every result inspectable: rule ID, input geometry, source, calculation, assumption, confidence, and suggested correction.
- Support PDF/CAD review as a separate imported-review workflow; do not claim that automated review grants approval.

**Gate:** a reviewer can reproduce why a site or plan received each result and can distinguish a failed rule from missing data.

### Week 18 — Collaboration, revision history, and professional delivery

- Add shareable review links with read-only technical and presentation views.
- Add comments anchored to rooms, walls, openings, dimensions, validation findings, and render viewpoints.
- Add revision compare: geometry changes, validation changes, area changes, opening changes, and furniture changes.
- Add approval states: Draft, Review, Client Presentation, Preliminary Coordination, and Not Issuable.
- Export a coordinated package: source JSON, validation report, technical PDF, coloured PDF, DXF, optional IFC, images, assumptions, rule-pack version, and manifest.
- Add a release gate that rejects packages with unresolved BLOCKER findings unless the user explicitly exports a marked non-issuable review package.

**Gate:** another professional can open the package, identify the exact model revision, understand all unresolved issues, and reproduce the drawing set.

### Week 19 — Project archive, artifact integrity, and migration safety

- Add a manifest-first archive contract under `projects/YYYY/project-slug/`
  without moving, overwriting, or deleting legacy source paths.
- Record project ID, revision, source provenance, artifact kind, destination
  path, byte size, SHA-256, validation status, and missing-artifact state.
- Verify manifest signatures, duplicate paths, duplicate artifact IDs, and
  source/report completeness before a package is considered recoverable.
- Keep binary cleanup separate from organization and require a reviewed,
  explicit change for any destructive duplicate removal.

**Gate:** a reviewer can identify every verified and missing artifact, reproduce
each recorded hash, and see exactly what remains before migration or cleanup.

### Week 20 — Durable revision operations and reproducibility

- Create immutable revision records with parent revision, author, reason,
  model signature, validation summary, and artifact-manifest signature.
- Add soft archive and restore operations that retain source files, revision
  history, and the current revision; no operation silently deletes geometry.
- Add complete-package verification with explicit blocked/incomplete results
  rather than guessed hashes or placeholder artifacts.
- Expose archive, revision, restore, and verification contracts through the
  typed API and deterministic command-line reports.

**Gate:** another workspace can verify the package contract, recover the
current revision, and distinguish an incomplete migration from a valid archive.

## 15. Phase Two acceptance tests

1. Natural-language input with missing upper-floor access produces a clarification or BLOCKER before rendering.
2. A PDF plan with an outer door and no balcony is recognized as an uncertain or invalid access condition, not beautified as a valid room.
3. Moving a wall in 2D updates 3D, section, elevation, dimensions, furniture clearance, and validation findings.
4. Importing a DXF preserves scale and opens a review queue for objects that cannot be semantically classified.
5. Furniture search returns only objects that fit the room or explains why no valid position exists.
6. Candidate comparison ranks a less attractive but fully reachable plan above an attractive plan with a blocked route.
7. A render camera cannot show a door, stair, balcony, or roof that is absent from the authoritative model.
8. A rule-pack report identifies whether a result is PASS, FAIL, UNKNOWN, or PROFESSIONAL REVIEW REQUIRED.
9. Comments and findings remain anchored after a revision or are explicitly marked as displaced.
10. Final export contains matching revision IDs and hashes for model, validation report, technical sheets, presentation sheets, and renders.
11. An archive manifest rejects tampered content and never treats a missing artifact as verified.
12. Soft archive and restore preserve the current revision and all prior revision records.

## 16. Feature priority if engineering capacity is limited

Build in this order:

1. Self-audit after every edit.
2. Conversational brief compiler with explicit assumptions.
3. Import and recognition review queue.
4. Synchronized 2D/3D and section views.
5. Clearance-aware furniture catalog.
6. Candidate comparison and transparent scoring.
7. Site feasibility and rule-pack reports.
8. Moodboards, high-resolution rendering, panorama, collaboration, and optional BIM exchange.

Do not sacrifice reachability, dimensions, opening semantics, stair coordination, or validation provenance to ship a faster render.

## 17. Public references checked for this Phase Two

- [Maket features](https://www.maket.ai/features) and [Maket AI floor-plan generator](https://www.maket.ai/ai-floor-plan-generator)
- [Planner 5D AI Interior Design Studio](https://ai.planner5d.com/)
- [Floorplanner](https://floorplanner.com/)
- [Homestyler](https://homestyler.com/partner)
- [Roomstyler 3D Planner](https://roomstyler.com/3dplanner)
- [Archistar AI plan review](https://www.archistar.ai/)
- [Archiagent](https://www.archiagent.ai/)
- [4Lines.ai](https://4lines.ai/)

These references should be rechecked before implementing any integration or claiming feature parity, because product availability, pricing, and feature names change.


---

# Phase Two Addendum — Post-Planning Edit Library

## Why this is required

A professional planning engine must also feel as immediate as modern 3D home-design software. After a plan is generated, the user should be able to select a wall, move a door, add a window, drag furniture, or change a room layout and see the result immediately in both 2D and 3D.

The difference is that Advocate-Chambers must make these edits semantically and safely. A visual edit is not complete until the geometry, access graph, dimensions, schedules, and validation findings have been updated.

## Two-layer editing architecture

### Authoritative planning layer

This layer controls valid building geometry and contains:

- walls, rooms, doors, windows, stairs, balconies, corridors, and service zones;
- structural and vertical coordination objects;
- dimensions, levels, areas, and schedules;
- public, private, staff, service, accessible, and emergency routes;
- validation findings and professional-review status.

### Presentation layer

This layer controls non-authoritative visual design and contains:

- furniture, fixtures, equipment, materials, colours, lighting, decor, cameras, and renders;
- moodboards, style presets, and presentation layouts;
- client-facing images and walkthroughs.

Presentation objects may improve appearance, but they must never hide a blocker or silently change the authoritative walls, openings, routes, or levels.

## Required feature-library categories

### 1. Wall editing

- Select, move, split, extend, offset, trim, join, and delete walls.
- Drag wall ends with live dimensions.
- Snap to grid, corners, midpoints, columns, reference lines, and existing walls.
- Preserve wall thickness and room boundaries.
- Warn before a wall edit disconnects a room, corridor, stair, or service route.
- Support lock, group, hide, isolate, and undo/redo.

### 2. Door library

Include main entrance, single, double, sliding, folding, fire, service, accessible, balcony, and internal doors.

Every door object must store:

- width, height, frame, sill or threshold where applicable;
- hinge side, swing direction, opening arc, and clear approach zone;
- host wall and side A/side B connections;
- access intent: public, private, staff, service, emergency, or exterior;
- clearance envelope and validation state.

Dragging a door onto a wall must create a real wall opening. It must not be a decorative line laid over an unbroken wall.

### 3. Window library

Include sliding, casement, fixed, clerestory, ventilator, bay, skylight, and louvered windows.

Every window object must store:

- width, height, sill, head, and opening direction;
- host wall and wall span position;
- daylight and ventilation intent;
- opening type, tag, and schedule data.

The editor must warn when a window conflicts with a corner, column, door, another opening, or a required service zone.

### 4. Furniture and equipment library

Include beds, sofas, tables, desks, wardrobes, kitchen units, toilets, showers, counters, reception desks, library shelves, courtroom seating, dais, waiting-area furniture, vehicles, and industrial equipment.

Every item must include:

- real-world dimensions and scale;
- rotation and mirroring rules;
- occupancy or user count where relevant;
- preferred wall or service-side relationships;
- clearance envelope;
- door, route, stair, and emergency-path conflict rules;
- searchable room type, category, style, and manufacturer-neutral metadata.

Support drag, rotate, duplicate, align, distribute, mirror, group, replace, and find-valid-position operations.

### 5. Room-type furnishing tools

Provide one-click starting layouts for:

- bedrooms, living rooms, kitchens, toilets, offices, chambers, reception areas;
- bar association halls, courtrooms, libraries, classrooms, waiting rooms, retail areas;
- healthcare rooms, service spaces, workshops, warehouses, and light industrial areas.

One-click furnishing is a starting suggestion only. The engine must run clearance and route checks before marking it valid.

## Instant 2D and 3D synchronization

Every accepted edit must update the following from the same canonical model:

- 2D floor plan;
- real-time 3D building view;
- section and elevation views;
- dimensions and area schedule;
- door and window schedules;
- furniture and equipment clearances;
- circulation and egress graph;
- validation panel and route overlays;
- export manifest and revision record.

A 3D view must never show an object that is absent from the authoritative model, and a 2D plan must never show stale geometry after a 3D edit.

## Edit transaction workflow

Implement every user edit as a transaction:

1. Select an object or editing tool.
2. Show dimensions, properties, constraints, and connected objects.
3. Preview the proposed movement or replacement.
4. Apply the edit to a temporary model.
5. Run lightweight geometry, opening, clearance, and reachability checks.
6. Show a green valid state, yellow professional-review state, or red blocked state.
7. Let the user accept, cancel, or undo.
8. Save an immutable revision with author, timestamp, changed object IDs, and validation delta.
9. Queue heavier rendering and export jobs only after acceptance.

## Example command behaviour

For the command: “Move this door to the corridor,” the system must:

1. locate a valid host wall;
2. create a real opening;
3. check width, swing, approach, and landing clearance;
4. identify both connected spaces;
5. update the route graph;
6. verify that the room remains reachable;
7. update the 2D plan, 3D scene, schedules, and dimensions;
8. show any new warning or blocker before export.

For the command: “Furnish this library,” the system must:

1. identify the room and its use;
2. load a library-specific furniture template;
3. place shelves, tables, chairs, and circulation aisles to scale;
4. preserve door swings, accessible routes, and emergency paths;
5. show capacity and remaining clear area;
6. allow the user to edit the arrangement;
7. save furniture as a presentation or planning revision according to user choice.

## Phase Two implementation sequence

### Edit Library Dose A — Core manipulation

- Selection, snapping, dimensions, properties, multi-select, lock, hide, undo, and redo.
- Wall move, split, join, offset, and trim.
- Temporary preview model and lightweight validation.

### Edit Library Dose B — Openings

- Door and window catalog.
- True wall breaks, swings, dimensions, tags, schedules, and clearance envelopes.
- Exterior-access and balcony/landing validation.

### Edit Library Dose C — Furniture

- Parametric furniture blocks.
- Drag, rotate, align, duplicate, replace, and find-valid-position.
- Room templates, clearance envelopes, route conflict checks, and occupancy.

### Edit Library Dose D — Synchronized 3D

- Shared object selection between 2D and 3D.
- Orbit, walk-through, camera presets, level visibility, section box, and isolated-room mode.
- Live updates to sections, elevations, dimensions, and validation overlays.

### Edit Library Dose E — Revision and export

- Transaction history, revision comparison, comments, accepted/rejected edits, and source provenance.
- Coordinated export of JSON, validation report, technical PDF, presentation PDF, DXF, optional IFC, and renders.
- Reject issue-ready export when unresolved BLOCKER findings remain.

## Acceptance tests

1. Moving a wall updates room area, dimensions, 2D, 3D, section, furniture clearances, and validation findings.
2. Dragging a door onto a wall creates a real wall break and a valid side A/side B connection.
3. A door cannot be accepted if its swing blocks the only route or another required opening.
4. A first-floor external door cannot be accepted without a modeled balcony, landing, stair, terrace, porch, or other intentional access path.
5. A window cannot be placed outside a host wall or over an incompatible opening.
6. Furniture cannot be accepted when it blocks the only room entrance, accessible route, stair, or required clearance.
7. The user can undo a combined edit and restore the exact prior model revision.
8. Presentation mode cannot hide a blocker produced by an authoritative planning edit.
9. Identical edits on the same model and seed produce identical geometry, IDs, validation findings, and exports.
10. Every accepted edit appears in the revision history with changed object IDs and a validation delta.

## Product principle

Give users the simplicity of a 3D home-design editor, but keep the intelligence of an architectural planning system underneath:

**select → edit → preview → validate → accept → synchronize → export**

Never allow:

**select → decorate → hide the problem → export**


---

# Project Archive and Large-File Storage

## Storage decision

Use two complementary layers:

1. **Git LFS** for versioned large binary artifacts inside the repository: PDF, DXF, IFC, images, 3D models, spreadsheets, archives, and presentation exports.
2. **An organized project archive** for application-readable project state, revisions, manifests, validation reports, and artifact relationships.

Git LFS is repository storage; it is not a complete runtime database or user-upload storage system. If the application later stores projects outside Git, use the same project and revision keys in a local artifact store during development and an object store in production.

## Canonical archive structure

Use stable project slugs and immutable revision folders. Do not use filenames such as final, final2, latest, new, or corrected as version control.

~~~text
projects/
  2026/
    advocate-chambers/
      project.json
      README.md
      source/
      revisions/
        r001/
          model/
          inputs/
          cad/
          pdf/
          renders/
          validation/
          manifest.json
        r002/
          ...
      current.json
    jamuniya-shaktawat/
      project.json
      revisions/
        r001/
          ...
      current.json

archive/
  project-index.json
  migration-manifest.json
~~~

The same structure may be implemented under an application storage root if the repository is not the runtime store. Every artifact must be addressable by project slug, revision ID, artifact kind, filename, and content hash.

## Current repository inventory

Treat the following as existing project families until migration is verified:

- Advocate-Chambers / Bar Association: bar-association-hall, CAD-Drawings, and the related standard drawing package.
- Jamuniya-Shaktawat: CAD, PDF, and source/reference images.
- code-junction: implementation guides and package documentation, not a client drawing project.
- apps, packages, services, and scripts: product source code, not project deliverables.

The current CAD-Drawings archive contains both ARCHIEVES and active CAD/PDF trees. Preserve the original paths during migration, record checksums, then mark them legacy read-only. Do not delete or overwrite them until every artifact has a destination and a verified hash.

## Project manifest contract

Each project must have a manifest containing:

- project ID and stable slug;
- project name, building type, location, client label, and status;
- source model path and schema version;
- levels, units, orientation, and rule-pack version;
- revision list and current revision ID;
- artifact list with kind, relative path, size, content hash, source revision, and generated timestamp;
- validation summary and unresolved professional-review items;
- migration status and legacy source paths.

Example artifact record:

~~~json
{
  "artifactId": "art-advocate-chambers-r002-a101-pdf",
  "projectId": "advocate-chambers",
  "revisionId": "r002",
  "kind": "technical-pdf",
  "path": "projects/2026/advocate-chambers/revisions/r002/pdf/A-101-GF-Plan.pdf",
  "sha256": "recorded-at-migration",
  "bytes": 0,
  "generatedAt": "2026-09-19T00:00:00Z",
  "validationStatus": "preliminary-review"
}
~~~

Do not use a placeholder hash in a real manifest; the migration tool must calculate it.

## LFS policy

Track large or binary artifacts with Git LFS using .gitattributes. Keep JSON, Markdown, Python, TypeScript, schemas, manifests, and validation reports in normal Git so they remain reviewable and diffable.

Recommended LFS patterns:

- PDF, DXF, IFC, GLB, FBX, ZIP, XLSX, DOCX, PPTX;
- PNG, JPG, JPEG, WEBP, and other generated raster images;
- large exported CAD, BIM, render, panorama, and presentation files.

Do not put source JSON, schemas, manifests, or small text-based SVG drawings into LFS unless there is a measured reason. LFS tracking must not be mistaken for a backup policy; maintain repository and artifact backup procedures separately.

## Migration sequence

1. Inventory every existing project folder and binary artifact.
2. Classify each item as source, input, generated artifact, reference, duplicate, or unknown.
3. Compute SHA-256 checksums and record size, path, project, and revision guess.
4. Create project manifests and destination paths without deleting legacy files.
5. Add LFS patterns and migrate new or verified large artifacts through Git LFS.
6. Compare source and destination hashes; reject the migration on any mismatch.
7. Update application indexes and artifact links to use project ID plus revision ID.
8. Mark legacy paths read-only and retain a redirect map.
9. Only after review, remove exact duplicates in a separate, explicitly approved cleanup change.

Never rewrite the repository's public history as part of routine organization. Perform history migration only as a separately approved maintenance operation with a full backup and a documented rollback plan.

## Runtime project storage requirements

The application must provide:

- create, open, duplicate, archive, and restore project operations;
- project search by name, type, location, status, and updated date;
- revision timeline with model and artifact comparisons;
- artifact preview for PDF, image, CAD metadata, and validation report;
- immutable generated artifacts linked to the exact model revision;
- soft archive rather than destructive deletion;
- export of one complete project package with its manifest.

A project is not complete when only the latest drawing is saved. It is complete when the brief, model, assumptions, validation report, source inputs, generated artifacts, and revision history can be recovered together.

## Storage acceptance tests

1. Every current project candidate has a stable project ID and manifest.
2. Every generated PDF/DXF/image is linked to a revision and content hash.
3. Reopening a project restores the same model, validation findings, and artifact links.
4. Duplicate filenames in different projects do not overwrite each other.
5. A failed or partial generation cannot replace the current valid revision.
6. Legacy paths remain recoverable during migration.
7. A checksum mismatch blocks migration and reports the exact artifact.
8. Archive and restore preserve source provenance and validation status.
9. Large binaries use LFS policy while text contracts remain ordinary Git files.
10. A complete project package can be exported and restored on another workspace.
