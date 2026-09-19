# Week 9–10 architectural enrichment — applied

The Week 9 and Week 10 enrichment from
[`docs/ARCHITECTURAL_INTELLIGENCE_ROADMAP.md`](docs/ARCHITECTURAL_INTELLIGENCE_ROADMAP.md)
has been implemented and merged into the canonical planning pipeline.

## Delivered

- **Week 9 — furniture and presentation:** a versioned furniture/equipment library
  with scale, occupancy, and clearance envelopes; deterministic occupancy-aware
  layouts; and a presentation layer that cannot mutate authoritative room, wall,
  opening, stair, or route geometry.
- **Week 10 — comparison and release discipline:** deterministic candidate seeds,
  transparent scorecards for area, adjacency, route quality, daylight/ventilation,
  structural/service coordination, and furniture fit; golden fixtures for
  residential, commercial, institutional, and industrial programs; geometry
  property checks; a release checklist; an export manifest; a changelog; and a
  readable blocked-case SVG fixture.

Run the enrichment and focused regression suite with:

```bash
npm run enrich:week910
npm run test:week910
```

The generated artifacts are under
`bar-association-hall/standard/`, including the Week 9 presentation report,
Week 10 candidate/QA report, release checklist, manifest, changelog, and
failure fixture.

**Release note:** the canonical Bar Association model is now blocker-free
through Week 10. Week 10 selects a deterministic best candidate and the Week 8
sheet stamp is **VALIDATED FOR PRELIMINARY REVIEW**. Two Week 6 warnings remain
for survey-confirmed road frontage and service-access intent; they are explicit
assumptions, not hidden pass conditions. These outputs are still preliminary
planning aids and require review by the licensed architect, structural engineer,
MEP consultant, fire/life-safety professional, surveyor, and local authority.

**Task verification:** Week 3–10 enrichment and the Week 3–8 blocker-removal
pass are complete on `main`. The full weekly regression suite passes (`37`
tests), Week 1–8 validation commands pass, Week 2 migration round-trips without
loss, Week 9 presentation validation passes, and Week 10 release gating selects
candidate `C-01` with `releaseReady: true`. The remaining Week 6 warnings stay
visible for professional review.

# Advocate-Chambers

Architectural planning intelligence for the Bar Association Hall project in
Banswara. The Week 2 canonical model remains the source of truth for geometry;
the Week 3–4 enrichment adds explainable routes, semantic openings, clearance
checks, and stable opening schedules before drawing export.

## Post-Week-20 validation program

The next enrichment phase is an evidence-based validation program rather than
another feature-only phase. It adds a weekly plan for adversarial architectural
fixtures, independent professional review, performance benchmarks, and
reproducibility gates.

See
[`docs/VALIDATION_AND_BENCHMARK_WEEKLY_PROGRAM.md`](docs/VALIDATION_AND_BENCHMARK_WEEKLY_PROGRAM.md)
for the Week 21–27 execution plan, acceptance thresholds, benchmark workload
profiles, reviewer scorecard, release classifications, and proposed evidence
layout.

The target release statement is: **100% detection of known critical defects,
zero dangerous false negatives, reproducible professional findings, measured
performance, and no loss of a valid project revision.** Until those gates are
met, generated plans remain preliminary planning and coordination aids and are
not automatically issuable.

## Week 21 task status — applied

Week 21 establishes the machine-readable quality-gate contract and records the
current regression baseline before adversarial, professional-review, and
performance evidence is supplied.

- Added `scripts/quality_gate.py` with `PASS`, `REVIEW_REQUIRED`, `BLOCKED`,
  and `INCOMPLETE` states.
- Added schemas for adversarial benchmark, professional review, and performance
  benchmark results under `packages/schema/`.
- Added tamper detection through a deterministic report signature.
- Added `tests/test_quality_gate.py` covering missing evidence, critical false
  negatives, professional uncertainty, performance failures, passing gates, and
  report tampering.
- Added the baseline artifact:
  `bar-association-hall/standard/quality-gate-report.json`.

The current Week 21 report is intentionally `INCOMPLETE` because the Week 23–25
evidence tracks have not yet been executed. The Week 22 adversarial track is
now connected to the quality gate and reports its own result. Missing
benchmark evidence is not treated as a pass.

Run the Week 21 contract checks with:

```bash
npm run enrich:week21
npm run validate:week21
npm run test:week21
```

## Week 22 task status — applied

Week 22 adds the adversarial fixture foundation required to test dangerous
architectural defects instead of only validating successful examples.

- Added 15 deterministic defective fixtures paired with one valid source model.
- Added expected rule ID, severity, affected objects, evidence fields, and
  suggested correction contracts for every fixture.
- Added automated fixture discovery, explicit model mutations, finding
  execution, and benchmark reporting.
- Added the fixture metadata schema at
  `packages/schema/week22-adversarial-fixture.schema.json`.
- Added the foundation report at
  `bar-association-hall/standard/week22-adversarial-foundation-report.json`.

The Week 22 benchmark must report zero missed critical defects, zero dangerous
false negatives, no valid-baseline false positives, and complete evidence and
correction data for every finding. Independent professional review remains
required; this benchmark does not grant planning or construction approval.

The Week 22 adversarial track currently passes with 15 of 15 critical fixtures
detected. The combined quality gate remains `INCOMPLETE` until the Week 24
professional-review and Week 25 performance evidence are supplied.

Run the Week 22 fixture checks with:

```bash
npm run enrich:week22
npm run validate:week22
npm run test:week22
```

## Week 3–4 task status

**Applied on `main`:**

- Week 3 per-level and cross-level walkability graph with connected components,
  entry-root route checks, vertical connector edges, and first-broken-edge
  diagnostics.
- Week 4 semantic wall breaks with side A/side B, explicit exterior-entry
  semantics, door width and swing checks, approach/landing checks, furniture
  conflict hooks, and stable opening tags.
- Deterministic reports:
  - `bar-association-hall/standard/week3-reachability-report.json`
  - `bar-association-hall/standard/week4-openings-report.json`
  - `bar-association-hall/standard/opening-schedule.json`
  - `bar-association-hall/standard/week34-enrichment-manifest.json`
- FastAPI `/analysis` endpoint and React viewport route overlay.
- Regression tests in `tests/test_week34_enrichment.py`.

The current legacy fixture now passes the route/opening gates after the topology
correction pass. Synthetic regression fixtures still prove that orphaned rooms,
invalid side B openings, and disconnected routes remain blockers when
introduced.

## Commands

```bash
npm run enrich:week34
npm run validate:week3
npm run validate:week4
python -m unittest discover -s tests -p 'test_week*.py'
npm run typecheck:web
npm run build:web
```

All dimensions are nominal planning dimensions in inches. Outputs remain
preliminary review material and require qualified architectural, structural,
fire/life-safety, accessibility, and local-code review before construction.

## Week 5–6 task status

**Applied on `main`:**

- Week 5 stair and floor-to-floor coordination validates connector endpoints,
  level elevations, riser arithmetic, tread, landing, width, direction, and
  route continuity. It keeps future-ready connector semantics for ramps and
  lifts without pretending they are validated stairs.
- Week 6 adds an inspectable institutional program template, required room-use
  completeness, area/dimension checks, required/preferred/forbidden
  adjacencies, and site orientation/frontage/service-access assumptions.
- Deterministic reports:
  - `bar-association-hall/standard/week5-stair-coordination-report.json`
  - `bar-association-hall/standard/week6-program-report.json`
  - `bar-association-hall/standard/week56-enrichment-manifest.json`
- The FastAPI `/analysis` response now includes Week 5 connectors and Week 6
  program, orientation, adjacency, and finding data.
- Regression tests live in `tests/test_week56_enrichment.py`.

Commands:

```bash
npm run enrich:week56
npm run validate:week5
npm run validate:week6
python -m unittest discover -s tests -p 'test_week*.py'
```

## Week 7–8 task status

**Applied on `main`:**

- Week 7 adds the versioned `india-preliminary-review` rule pack under
  `bar-association-hall/standard/rule-packs/`.
- Universal geometry checks are separated from configurable accessibility,
  egress, daylight, ventilation, wet-area, and service checks.
- Reports now carry the selected pack, effective date, assumptions,
  professional-review items, and deterministic finding metadata. A rule-pack
  change changes findings without changing authoritative geometry.
- Week 8 adds a deterministic technical-drawing quality contract covering
  wall/layer hierarchy, hatches, labels, legends, title blocks, north arrows,
  scales, sheet references, plan/section/elevation consistency, and traceability
  from visible openings, spaces, and stairs back to model IDs.
- Sheet status is explicit: `VALIDATED FOR PRELIMINARY REVIEW` only when all
  upstream gates pass; otherwise `NOT ISSUABLE`.
- Deterministic reports:
  - `bar-association-hall/standard/week7-rule-pack-report.json`
  - `bar-association-hall/standard/week8-drawing-quality-report.json`
  - `bar-association-hall/standard/week78-enrichment-manifest.json`
- The FastAPI `/analysis` response now includes Week 7 rule-pack data and Week
  8 drawing-quality/stamp data.
- Regression tests live in `tests/test_week78_enrichment.py`.

Commands:

```bash
npm run enrich:week78
npm run validate:week7
npm run validate:week8
npm run test:week78
```

The Week 8 stamp is a preliminary-review gate, not a construction,
accessibility, fire/life-safety, structural, MEP, survey, permit, or local-code
certification.

## Week 11–12 task status

**Applied and marked done:**

- Week 11 adds explicit **Brief, Model, Validate, Furnish, Present, and Export**
  product modes in the web editor.
- The capability matrix distinguishes available, provisional, and
  professional-review features for import, 3D, candidate comparison, materials,
  site feasibility, and collaboration.
- Local-only performance counters report model size, object counts, validation
  duration, render duration, and export duration without telemetry.
- Week 12 adds a deterministic conversational brief compiler for metric and
  imperial units. It extracts site dimensions, north, frontage, levels,
  floor-to-floor heights, room schedules, area targets, access intent,
  occupancy, adjacencies, style, and requested outputs.
- Briefs show assumptions, ambiguities, and missing topology facts before plan
  generation. Supported commands become typed revision previews with changed
  object IDs and validation deltas; conditional outer-door removal is blocked
  until an intentional access path is modeled.
- FastAPI routes: `GET /capabilities`, `GET /performance`,
  `POST /brief/compile`, and `POST /brief/command`.
- Deterministic artifacts:
  - `bar-association-hall/standard/week11-capability-matrix.json`
  - `bar-association-hall/standard/week12-brief-compiler-report.json`
  - `bar-association-hall/standard/week1112-enrichment-manifest.json`
  - `bar-association-hall/standard/week1112-changelog.md`
- Regression tests live in `tests/test_week1112_enrichment.py`.

Commands:

```bash
npm run enrich:week1112
npm run validate:week11
npm run validate:week12
npm run test:week1112
```

The brief compiler and product modes are preliminary planning aids. They do
not provide survey, code, permit, accessibility, fire/life-safety, structural,
MEP, or construction certification.

## Week 13–14 task status — applied and marked done

The Week 13 and Week 14 enrichment from
[`docs/ARCHITECTURAL_INTELLIGENCE_ROADMAP.md`](docs/ARCHITECTURAL_INTELLIGENCE_ROADMAP.md)
is implemented in the canonical pipeline.

- **Week 13 — import, recognition and editable digital twin:** DXF source
  inspection preserves source hash, entity/layer counts and geometry-preserved
  status; PDF/image recognition is explicitly assisted and review-required;
  uncertain objects remain non-authoritative; editable-twin links preserve
  units, levels, openings and source provenance; IFC/BIM remains capability-gated.
- **Week 14 — synchronised views:** 2D plans, 3D, sections and elevations share
  one model revision and selection key, with camera presets, level visibility,
  section-box and isolated-room contracts, snapping targets, route overlays and
  validation markers.
- **Sheet coverage rationalisation:** PDF and DXF export code now uses one
  paper-space layout contract. It is based on ISO 5457 A-series sheet formats
  and ISO 7200-style title-block information fields. The drawing zone is
  protected first; notes, legends and indices share a bounded band, with a
  project policy of **supporting content ≤ 20%** and **drawing zone ≥ 65%**.
  These ratios are project policy, not a claim that ISO prescribes a universal
  percentage.
- **Annotation standard:** future labels, dimensions, keynotes and general
  notes use a shared paper-space type scale with a 2.5 mm minimum readable
  target for ordinary annotations; DXF model-space heights derive from that
  same policy instead of scattered constants.
- **FastAPI routes:** `POST /import/recognize`, `GET /views/synchronized`, and
  `GET /sheet-standard`.
- **Deterministic artifacts:**
  - `bar-association-hall/standard/week13-import-recognition-report.json`
  - `bar-association-hall/standard/week14-synchronized-views-report.json`
  - `bar-association-hall/standard/sheet-layout-standard.json`
  - `bar-association-hall/standard/week1314-enrichment-manifest.json`
  - `bar-association-hall/standard/week1314-changelog.md`
- Regression tests: `tests/test_week1314_enrichment.py`.

Commands:

```bash
npm run enrich:week1314
npm run validate:week13
npm run validate:week14
npm run test:week1314
```

**Task completion:** Week 13–14 enrichment and the sheet-coverage/
annotation-standard correction are complete and are included in this `main`
release. All outputs remain
preliminary planning/coordination aids and require the appointed architect,
engineers, surveyor and local authority review.

## Week 15–16 task status — applied and marked done

The Week 15 and Week 16 enrichment from
[`docs/ARCHITECTURAL_INTELLIGENCE_ROADMAP.md`](docs/ARCHITECTURAL_INTELLIGENCE_ROADMAP.md)
is implemented in the canonical pipeline.

- **Week 15 — parametric assets and clearance-aware furnishing:** the typed
  catalog covers furniture, fixtures, appliances, sanitaryware, seating rows,
  dais, library tables, counters, vehicles, and industrial equipment. Every
  asset carries dimensions, allowed rotations, wall relationships, service
  side, occupancy, and clearance-envelope data. Room templates cover
  residential, offices/chambers, halls, classrooms, libraries, healthcare,
  retail, and light industrial use.
- Drag, rotate, duplicate, align, replace, and find-valid-position operations
  are typed and non-mutating. Placement rejects door swings, required routes,
  stairs, service zones, room-boundary violations, and overlapping clearances.
  Presentation objects are never authoritative construction geometry.
- **Week 16 — candidate studio and presentation pipeline:** candidates use
  deterministic seeds and transparent area, adjacency, route,
  daylight/ventilation, vertical-coordination, furniture-fit, and visual
  metrics. A candidate with a `BLOCKER` or `ERROR` cannot win.
- Moodboards, palettes, materials, lighting presets, non-destructive design
  layers, render/panorama/presentation-sheet job manifests, and
  technical-plan-to-render revision traceability are included.
- **Sheet rationalisation remains enforced:** ISO 5457 A-series sheet formats
  and ISO 7200-style information fields guide the contract; this project
  policy caps supporting notes/legends/indices at **20%** of the sheet area
  and protects at least **65%** for the drawing zone. These are adopted
  project limits, not a claim that ISO prescribes a universal ratio.
- FastAPI routes: `GET /furnishing/catalog`, `POST /furnishing/preview`,
  `POST /furnishing/validate`, `POST /furnishing/edit`,
  `POST /candidates/studio`, `POST /presentation/package`, and
  `POST /presentation/render-job`.
- Deterministic artifacts:
  - `bar-association-hall/standard/week15-parametric-assets-report.json`
  - `bar-association-hall/standard/week16-candidate-studio-report.json`
  - `bar-association-hall/standard/week1516-enrichment-manifest.json`
  - `bar-association-hall/standard/week1516-changelog.md`
- Regression tests live in `tests/test_week1516_enrichment.py`.

Commands:

```bash
npm run enrich:week1516
npm run validate:week15
npm run validate:week16
npm run test:week1516
```

**Task completion:** Week 15–16 enrichment is complete and marked done in
this README. Outputs remain preliminary planning/presentation aids and require
appointed architect, engineers, surveyor, and local-authority review.

## Week 17–18 task status — applied and marked done

The Week 17 and Week 18 enrichment from
[`docs/ARCHITECTURAL_INTELLIGENCE_ROADMAP.md`](docs/ARCHITECTURAL_INTELLIGENCE_ROADMAP.md)
is implemented in the canonical pipeline and marked complete here.

- **Week 17 — site feasibility and transparent plan review:** the site
  workspace exposes plot bounds, north, setbacks, access points, level and
  footprint records, context layers, and assumptions without mutating
  authoritative geometry.
- The configurable rule-pack evaluator checks coverage, setbacks, height,
  floor-area targets, parking, accessibility, daylight, ventilation, egress,
  fire access, service access, and wet-area coordination. Each result includes
  a rule ID, input geometry, source, calculation, assumption, confidence, and
  suggested correction, with explicit `pass`, `fail`, `unknown`, and
  professional-review semantics.
- PDF/CAD inspection is a separate imported-review workflow. It records the
  source and review steps but never claims approval or promotes uncertain
  observations to authoritative geometry.
- **Week 18 — collaboration and professional delivery:** deterministic
  read-only technical/presentation review-link contracts, comments anchored to
  rooms, walls, openings, dimensions, validation findings, or viewpoints, and
  revision comparison for geometry, validation, area, openings, and furniture
  changes are included.
- Approval states are `Draft`, `Review`, `Client Presentation`, `Preliminary
  Coordination`, and `Not Issuable`. The coordinated package manifest covers
  source JSON, validation report, technical PDF, coloured PDF, DXF, optional
  IFC, images, assumptions, rule-pack version, and manifest. The release gate
  rejects unresolved blockers unless the export is explicitly marked
  `Not Issuable`.
- FastAPI routes: `POST /site/feasibility`, `POST /site/imported-review`,
  `POST /collaboration/review-link`, `POST /collaboration/comments`,
  `POST /collaboration/revision-compare`, `POST /delivery/package`, and
  `GET /delivery/contract`.
- Deterministic artifacts:
  - `bar-association-hall/standard/week17-site-feasibility-report.json`
  - `bar-association-hall/standard/week18-delivery-package-report.json`
  - `bar-association-hall/standard/week1718-enrichment-manifest.json`
  - `bar-association-hall/standard/week1718-changelog.md`
- Regression tests live in `tests/test_week1718_enrichment.py`.

Commands:

```bash
npm run enrich:week1718
npm run validate:week17
npm run validate:week18
npm run test:week1718
```

**Task completion:** Week 17–18 enrichment is complete and marked done in
this README. All checks remain preliminary planning/coordination aids and
require review by the appointed architect, accessibility professional,
fire/life-safety professional, structural and MEP engineers, surveyor, and
local authority. The separate binary cleanup remains intentionally untouched.

## Week 19–20 task status — applied and marked done

The Week 19 and Week 20 enrichment is implemented in the canonical pipeline
and marked complete here.

- **Week 19 — project archive and artifact integrity:** the manifest-first
  archive contract records project/revision identity, destination layout,
  artifact kind, byte size, SHA-256, validation status, and explicit missing
  records. Manifest signatures, duplicate paths, and duplicate artifact IDs
  are validated before a package can be treated as recoverable.
- **Week 20 — durable revision operations:** immutable revision records carry
  parent revision, author, reason, model signature, validation summary, and
  artifact-manifest signature. Soft archive and restore retain the current
  revision and source history; complete-package verification blocks incomplete
  migration instead of inventing hashes or silently deleting files.
- API contracts are available at `POST /archive/manifest`,
  `POST /revisions/record`, `POST /archive/verify`, and
  `POST /archive/state`.
- Deterministic artifacts:
  - `bar-association-hall/standard/week19-archive-integrity-report.json`
  - `bar-association-hall/standard/week20-revision-operations-report.json`
  - `bar-association-hall/standard/week1920-archive-manifest.json`
  - `bar-association-hall/standard/week1920-changelog.md`
- Regression tests live in `tests/test_week1920_enrichment.py`.

Commands:

```bash
npm run enrich:week1920
npm run validate:week19
npm run validate:week20
npm run test:week1920
```

**Task completion:** Week 17–20 enrichment is complete and marked done in
this README. These archive, revision, and verification contracts remain
preliminary coordination infrastructure; the separate 84-file binary cleanup
and any destructive history rewrite remain intentionally untouched.

## Furnishing architecture consolidation — applied

The Week 15 parametric asset schema is now the single furnishing authority.
The former Week 9 `FURNITURE_LIBRARY` is a compatibility view generated from
that catalog; it no longer owns independent dimensions, occupancy, or
clearance values. Week 9 presentation and candidate functions delegate to the
Week 15 furnishing engine and translate only the legacy response shape.

- One placement/clearance validator handles room fit, door swings, routes,
  stairs, service zones, and furniture clearances.
- Week 9-to-Week 15 rectangle adaptation preserves older callers while
  canonical model rectangles remain authoritative.
- Materials, decoration, lighting, and render jobs remain in the separate
  non-authoritative Week 16 presentation layer.
- Migration tests verify that the Week 9 compatibility wrapper and Week 15
  engine return the same placement-validation result and that legacy library
  values are sourced from the Week 15 catalog.
