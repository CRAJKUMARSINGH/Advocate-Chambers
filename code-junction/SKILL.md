---
name: drawing-generation
description: Generates, audits, and packages architectural planning drawings from structured geometry. Use for floor plans, site plans, sections, elevations, DXF/DWG-compatible CAD, SVG review sheets, and print-ready PDFs; use AI tools for exploration and validation, never as a substitute for surveyed or licensed construction documentation.
---

# Architectural Drawing Generation

## Purpose

Produce a coordinated drawing package from an explicit source of truth:

`brief → constraints → structured geometry → review drawing → CAD → PDF → validation report`

The deliverable must be legible, traceable, reproducible, and honest about its design stage. A photorealistic AI image is a design reference, not a measured drawing.

## Tool landscape (current workflow)

Use the best tool for the stage, not one tool for everything:

- **Autodesk Forma Site Design** — early site, geolocated context, terrain, massing, environmental studies, automated site layouts, and IFC 4.3 export. Use it for feasibility and site-option comparison.
- **TestFit** — constraint-driven site planning, parking/unit/program iteration, code parameters, yield and cost/feasibility signals. Use it to compare options before fixing geometry.
- **Snaptrude** — browser-based AI/BIM exploration, program and massing studies, collaborative schematic models, and IFC/Revit/Archicad-oriented handoff. Use it for concept-to-BIM coordination where available.
- **Finch3D / Grasshopper / Revit workflows** — parametric, graph-based option generation with architect-controlled rules. Use for repeatable floor-plan and massing studies, not blind one-click approval.
- **AutoCAD 2027.1 / Autodesk AI** — precise drafting and review support: contextual Assistant, Count/Query, markup and collaboration workflows, drawing cleanup, and DWG documentation.
- **BricsCAD AI-Predict / BIM** — command assistance, drawing optimization, 2D/3D editing, and BIM element classification in DWG-centered workflows.
- **EvolveLAB Veras** — controlled visualization from a model or drawing substrate. Use for material, façade, and presentation variants; never read generated pixels back as geometry.
- **ArkDesign, Maket, Hypar, and similar generative tools** — useful for schematic alternatives when their export and rule assumptions are verified. Treat their output as an option to audit.
- **Open, reproducible fallback** — Python + `ezdxf` for DXF R2018, SVG for review sheets, Chromium print-to-PDF or `PyMuPDF`/`pypdf` for PDF packaging, and explicit geometry checks. This is the default for this repository.

Record the tool, version/date checked, input constraints, and export format in the package notes. Capabilities and export formats change; verify official documentation before promising a round trip.

## Non-negotiable design gates

1. **Source gate** — keep plot vertices, setbacks, floor programs, grids, room schedules, and assumptions in JSON/CSV/typed data. Do not use a rendered image as the source of dimensions.
2. **Constraint gate** — resolve units, north, scale, wall thickness, openings, room clearances, accessibility, stairs, sanitation, fire egress, structural grid, and services before adding decoration.
3. **Geometry gate** — validate polygon closure, self-intersections, areas, setbacks, room overlap, wall continuity, door swings, stair run/riser arithmetic, and unconnected annotations.
4. **Coordination gate** — stack wet areas and vertical circulation where intended; use stable IDs for spaces, doors, windows, columns, and sheets.
5. **Documentation gate** — every sheet gets a border, title block, sheet number, project/status, north arrow where relevant, scale, units, revision/date, source status, and notes.
6. **Export gate** — inspect the DXF entity count/layers and render each sheet to verify extents, text legibility, line hierarchy, clipping, and orientation. Confirm PDF page size and page count.
7. **Professional gate** — mark preliminary/planning studies clearly. Do not label a generated package “for construction,” “approved,” “structural,” “fire-NOC,” or “statutory” without licensed review and required surveys.

## Recommended CAD conventions

- Keep model geometry in one declared unit system; this repository uses **1 drawing unit = 1 inch** and `12 units = 1 foot`.
- Use stable layers such as `A-WALL`, `A-DOOR`, `A-WINDOW`, `A-FURN`, `A-DIM`, `A-TEXT`, `A-HATCH`, `A-COLUMN`, `A-STAIR`, `A-SITE`, `A-ROOF`, `A-SECT-CUT`, `A-TTLB`, and `A-ACC`.
- Use heavier cut walls, medium partitions/openings, light furniture/hatches, and a consistent text hierarchy. Dimension text must remain readable at the printed scale.
- Prefer DXF R2018 for broad compatibility; preserve a clean, editable layer structure. If DWG is required, state that a CAD application or converter is needed for the final DWG write.
- Generate one sheet per plan/section/elevation where possible, plus a merged review set. Use A4/A3 for routine review and A1/A0 only when the geometry and text scale justify it.

## Repository workflow

For this Advocate-Chambers repository:

```text
bar-association-hall/
  site_plan.json              # plot, setbacks, planning assumptions
  preliminary_plans.json      # coordinate source for floor review drawings
  generate_refined_cad.py     # DXF + rendered PDF plan generator
  generate_plan_pdf.py        # structured five-page planning/review PDF
  validate_plan.py            # area and envelope consistency check
  CAD/                        # editable DXF outputs
  PDF/                        # rendered drawing outputs
```

1. Read the JSON and planning notes.
2. Run `validate_plan.py`; preserve warnings about the stated 4,785 sf assumption versus the coordinate-derived envelope.
3. Generate both furnished and bare variants only when the script defines them; do not rename an older output as a new revision.
4. Render the current DXF outputs and inspect title blocks, orientation, windows/vents, stair geometry, toilet fixtures, dimensions, and margins.
5. Generate the coordinated planning PDF from the same source data.
6. Write a manifest containing UTC/local generation time, commit/source hash, generator names, output paths, page count, and validation status.
7. Package DXF, PDF, source data, manifest, and review notes together. Keep generated artifacts out of the source-of-truth files.

## AI-assisted review prompts

Use AI as a reviewer with bounded questions:

- “List rooms without a door, windows without a host wall, and dimensions that do not match the source schedule.”
- “Compare the ground and first-floor service cores and flag unstacked wet areas.”
- “Check the declared north, drawing rotation, sheet scale, and page orientation.”
- “Find any collision between furniture, door swings, accessible clearances, stair landings, or exit paths.”
- “Summarize every unresolved assumption; do not invent a value.”

The final review must cite the source JSON and the generated sheet, and must separate calculated values from brief assumptions.

## Output checklist

- Editable DXF with layers, units, title block, dimensions, and stable labels.
- PDF with known paper size, legible text, consistent margins, and a page index.
- Source data and generator scripts.
- Validation output and manifest.
- A plain-language status: `planning`, `schematic`, `design development`, or `construction documentation`.
- Explicit note that local code, survey, structure, MEP, accessibility, fire, and authority review remain required where applicable.
