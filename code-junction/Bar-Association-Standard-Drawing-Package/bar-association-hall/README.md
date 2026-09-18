# Bar Association Hall — Standard Drawing Package

This package replaces the uploaded abstract review diagrams with a coordinated
schematic plan set generated from structured geometry.

## Source of truth

- `source/site_plan.json` — project, plot, north, levels, and assumptions.
- `source/preliminary_plans.json` — spaces, openings, windows, stair parameters,
  and drawing notes.
- `source/project.schema.json` — machine-readable shape of the planning model.

The PDFs from the upload are retained under `references/original/` for traceability
only. They are not read back as geometry and are not treated as construction
documents.

## Generate

```bash
cd bar-association-hall
uv run python validate_plan.py
uv run python generate_standard_drawings.py
```

Outputs:

- `PDF/A-101-Ground-Floor-Plan.pdf`
- `PDF/A-102-First-Floor-Plan.pdf`
- `PDF/Bar-Association-Standard-Review-Set.pdf`
- `CAD/A-101-GF-Plan-R2018.dxf`
- `CAD/A-102-FF-Plan-R2018.dxf`
- `manifest.json`

The PDF sheets are A2 landscape with a consistent title block, north arrow,
dimension strings, door/window tags, conventional door swings, and a parametric
two-flight dog-leg stair. DXF model units are inches and the file uses
R2018-compatible architectural layers.

The ground-floor model explicitly carries the entry intent from the uploaded
reference drawing: `SOUTH / MAIN ENTRY` is the primary public access and
`EAST / VIP ENTRY` is secondary. The main-entry porch is drawn as a dashed
`PROVISIONAL` 10'-0" × 6'-0" coordination zone; its cover, steps or ramp,
drainage, accessibility, and final dimensions still require client, survey,
and code confirmation.

## Status and limitations

The package is **schematic / preliminary**, not for construction. The stair
parameters are explicit planning assumptions: 18 total risers, 9 per flight,
7.3333-inch riser, 10-inch tread, 48-inch landing depth, and 48-inch stair
width. Confirm the stair against the applicable local code and final floor-to-
floor elevations.

Survey, local building code, fire egress, accessibility, structure, MEP,
services, waterproofing, and licensed architectural review remain required
before design development, approval, procurement, or construction.