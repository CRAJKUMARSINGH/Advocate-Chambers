# Advocate-Chambers: Future React + CAD Platform Transformation Patch Guide

**Status:** Future migration plan — do not apply as a blind rewrite  
**Target baseline:** React 19.3 + TypeScript  
**Current source of truth:** Python geometry/export engine plus JSON planning data  
**Primary objective:** Add a reliable interactive drafting product without weakening DXF/PDF precision

React 24 is not the current verified release line. The React team’s September 2026 release is React 19.3:

<https://react.dev/blog/2026/09/09/react-19-3>

## 1. Migration decision

Do **not** convert the geometry engine from Python to JavaScript in the first phase.

Use this split:

| Concern | Recommended platform | Rule |
|---|---|---|
| Interactive editor | React 19.3 + TypeScript | User interaction, review, annotation, option comparison |
| 2D drawing surface | SVG first; Canvas only for high-volume overlays | Every visible object has a stable geometry ID |
| Optional 3D view | Three.js after 2D validation is stable | Visualization is downstream of measured geometry |
| API | FastAPI + Pydantic | Typed commands, validation, job status, artifact links |
| Geometry and drafting | Existing Python `traecad_engine` | Remains the authoritative DXF/PDF generator |
| Source data | Versioned JSON Schema | Plot, rooms, walls, openings, stairs, grids, services |
| Persistence | PostgreSQL later; file-backed JSON first | Do not add a database before the model stabilizes |
| Background generation | Worker queue or process job | DXF/PDF export must not block the browser request |
| Artifacts | Object storage or a project artifact folder | Store input revision, generator version, and checksums |

The browser may propose edits. The Python service decides whether those edits are geometrically valid.

## 2. Repository target shape

Add the web platform beside the current drawing code:

```text
Advocate-Chambers/
├── apps/
│   └── web/                         # React 19.3 + TypeScript editor
├── services/
│   └── api/                         # FastAPI adapter and job endpoints
├── packages/
│   └── schema/                      # JSON Schema and shared examples
├── scripts/
│   ├── traecad_engine.py            # authoritative CAD/PDF engine
│   └── ...                          # existing generators
├── bar-association-hall/
│   ├── site_plan.json               # existing project source
│   ├── preliminary_plans.json       # existing floor-plan source
│   ├── generate_refined_cad.py
│   ├── validate_plan.py
│   └── ...
├── docs/
│   ├── TRANSFORMATION_PATCH_GUIDE.md
│   └── geometry/
└── .github/
    └── workflows/
        ├── validate-drawings.yml
        └── web-ci.yml
```

Do not move or rename the current CAD directories until the new pipeline can regenerate byte-different but geometrically equivalent outputs and the review package has passed.

## 3. Patch sequence

Apply these patches as separate pull requests. Each PR must be runnable and reversible.

### Patch 0 — Freeze and inventory

Create a branch:

```bash
git switch -c feat/react-cad-platform-foundation
```

Record:

- current commit and generator versions;
- Python version and package lock;
- source JSON files;
- DXF layer names and declared units;
- PDF paper sizes and sheet count;
- known planning warnings, including the 4,427.5 sf coordinate envelope versus the 4,785 sf brief assumption.

Add a machine-readable artifact manifest. Never use a rendered PDF or AI image as the migration source.

### Patch 1 — Add the typed schema package

Create `packages/schema/project.schema.json` with these top-level objects:

```json
{
  "project": {},
  "units": "inch",
  "site": {},
  "levels": [],
  "spaces": [],
  "walls": [],
  "openings": [],
  "stairs": [],
  "structuralGrid": {},
  "sheets": [],
  "assumptions": [],
  "revisions": []
}
```

Every drawable object needs:

```json
{
  "id": "stair-gf-main",
  "kind": "stair",
  "levelId": "GF",
  "geometry": {},
  "source": "user|generator|import",
  "status": "draft|validated|warning|rejected",
  "revision": 1
}
```

Use stable IDs, not array indexes. Preserve the original planning JSON through an explicit adapter; do not silently reinterpret old coordinates.

### Patch 2 — Wrap the existing Python engine

Create a thin FastAPI service. The first version should expose:

```text
GET  /api/health
GET  /api/projects/{project_id}
POST /api/projects/{project_id}/validate
POST /api/projects/{project_id}/generate
GET  /api/jobs/{job_id}
GET  /api/artifacts/{artifact_id}
```

Example request:

```json
{
  "projectId": "bar-association-hall",
  "sourceRevision": "git:25d9b67",
  "formats": ["dxf", "pdf"],
  "variants": ["furnished", "bare"],
  "sheets": ["GF", "FF"],
  "validationProfile": "planning-review"
}
```

The API must return a job ID for generation:

```json
{
  "jobId": "job_01...",
  "status": "queued",
  "sourceRevision": "git:25d9b67"
}
```

The generator must write to a job-specific temporary folder, then publish only after validation succeeds. Never let a browser request overwrite the source JSON.

### Patch 3 — Add the React editor shell

Create `apps/web` with:

- React 19.3;
- TypeScript with strict mode;
- a router;
- query/mutation state management;
- an error boundary;
- a project/level selector;
- a 2D viewport;
- a property inspector;
- a validation panel;
- an artifact/download panel.

Initial screens:

1. **Project overview** — source revision, warnings, latest artifacts.
2. **2D plan editor** — pan, zoom, select, measure, toggle layers.
3. **Validation drawer** — geometry errors and unresolved assumptions.
4. **Export dialog** — DXF/PDF, furnished/bare, sheet selection.

Do not begin with a free-form “AI draw anything” prompt. Start with constrained commands:

```text
add wall
move wall endpoint
add door
change room label
place window on host wall
change stair parameters
validate plan
generate review set
```

### Patch 4 — Build the geometry command layer

All edits flow through typed commands:

```ts
type GeometryCommand =
  | { type: "move-wall-endpoint"; wallId: string; endpoint: "a" | "b"; point: Point }
  | { type: "add-opening"; wallId: string; opening: OpeningInput }
  | { type: "set-room-label"; spaceId: string; label: string }
  | { type: "set-stair-parameters"; stairId: string; params: StairParameters };
```

The browser sends a command. The API:

1. loads the current revision;
2. applies the command;
3. validates the full model;
4. returns accepted geometry plus warnings/errors;
5. persists only an accepted revision.

Rejected commands must return a reason and the affected object IDs. No silent snapping or silent dimension changes.

## 4. Dog-legged staircase acceptance contract

The staircase must be a parametric object, not a collection of decorative lines.

### Minimum model

```json
{
  "id": "stair-gf-main",
  "kind": "dog-leg",
  "levelFrom": "GF",
  "levelTo": "FF",
  "widthIn": 108,
  "flightCount": 2,
  "riserCountTotal": 26,
  "riserCountPerFlight": 13,
  "treadIn": 12,
  "riserIn": 6.846,
  "landingDepthIn": 108,
  "turn": "180-deg",
  "direction": "up",
  "handrails": ["left", "right"],
  "status": "draft"
}
```

Values above are project parameters from the current planning package, not universal code values. Local code and licensed design review remain authoritative.

### Geometric rules

A valid dog-legged stair must have:

- two parallel flights;
- a 180-degree change of direction;
- a real intermediate landing connecting the flights;
- equal or explicitly justified flight widths;
- riser/tread counts whose arithmetic reaches the floor-to-floor height;
- landing depth not less than the declared stair width unless a rule-set explicitly permits another value;
- `UP` and `DOWN` direction semantics;
- no overlap with walls, doors, furniture, or required circulation;
- a clear start and clear end;
- guard/handrail metadata;
- a section/elevation representation derived from the same parameters.

### Automated tests

Add tests before exposing a stair editor:

```text
test_dogleg_has_two_parallel_flights
test_dogleg_has_180_degree_turn
test_dogleg_landing_connects_flights
test_riser_count_matches_floor_height
test_tread_run_matches_declared_length
test_landing_depth_meets_profile
test_stair_does_not_overlap_openings
test_stair_has_up_and_down_semantics
test_stair_plan_and_section_share_source_parameters
test_invalid_stair_is_rejected_not_repaired_silently
```

The UI may render a stair symbol, but the server must validate the actual flight polygons, landing polygon, riser count, and clearances.

## 5. Drafting and artifact rules

### DXF

- Preserve the existing declared unit system: one drawing unit equals one inch.
- Preserve stable architectural layers.
- Generate editable lines, arcs, text, hatches, and dimensions.
- Keep furniture and bare variants as separate outputs.
- Reopen every generated file with `ezdxf` before publishing.
- Record DXF version, entity count, layer count, and checksum.

### PDF

- Generate from the same accepted geometry revision as the DXF.
- Record page size, orientation, page count, sheet number, scale, and revision.
- Render or inspect every page before publication.
- Keep preliminary/planning status visible in the title block and manifest.

### AI

Use AI for:

- option generation;
- code/profile lookup with citations;
- conflict detection;
- schedule checking;
- annotation suggestions;
- visual exploration from an existing model.

Do not use AI image output as:

- a dimension source;
- a structural design;
- a fire or accessibility compliance decision;
- a substitute for survey data;
- a substitute for licensed approval.

## 6. Recommended AI-tool integration boundaries

| Tool category | Use in this product | Do not use it for |
|---|---|---|
| Site/generative tools such as Forma or TestFit | Early feasibility and option comparison | Authoritative final geometry without audit |
| BIM exploration such as Snaptrude or Finch workflows | Schematic program and massing | Unverified code compliance |
| CAD assistants such as AutoCAD AI or BricsCAD AI | Cleanup, query, repetitive drafting support | Inventing missing dimensions |
| Visualization such as Veras | Material and façade studies | Reading precise geometry back from pixels |
| Local Python engine | Deterministic validation and DXF/PDF | Conversational free-form design without schema |

Store imported options as explicit alternatives with provenance:

```json
{
  "alternativeId": "option-03",
  "sourceTool": "external-tool-name",
  "sourceVersion": "checked-version",
  "importedAt": "2026-09-18T00:00:00Z",
  "assumptions": [],
  "validated": false
}
```

## 7. CI and release gates

### Pull request checks

```text
format/lint
typecheck
unit geometry tests
staircase acceptance tests
JSON schema validation
DXF smoke generation
DXF reopen check
PDF page-size/page-count check
artifact manifest check
```

### Release check

Publish only when:

- the source revision is recorded;
- all geometry errors are zero;
- warnings are listed and acknowledged;
- furnished and bare outputs are both intentional;
- title blocks show the correct revision;
- DXF and PDF are generated from the same source revision;
- artifacts have checksums;
- planning status is not mislabeled as construction documentation.

## 8. What not to change

Do not:

- replace Python with a JavaScript geometry rewrite just to use React;
- make the browser the authority for geometry;
- convert PDFs or AI images into dimensions by visual estimation;
- hide the area discrepancy between the coordinate envelope and brief assumption;
- hardcode one staircase as the only staircase type;
- publish a generated drawing as approved or for construction;
- add a database before the JSON schema and revision model are stable;
- merge a large migration with unrelated drawing edits.

## 9. Definition of done for the future migration

The migration is ready for production iteration when a user can:

1. open `bar-association-hall`;
2. view the ground and first floors in a layered 2D editor;
3. select a stair and see its actual parameters;
4. change a stair parameter and receive validation feedback;
5. inspect unresolved planning assumptions;
6. generate furnished and bare DXFs;
7. generate the coordinated PDF review set;
8. reopen the DXF outputs successfully;
9. see the source revision and checksums;
10. reproduce the same package from the command line.

The key quality test is not whether the interface looks modern. It is whether the web editor and the exported drawings remain geometrically faithful to the same validated source model.