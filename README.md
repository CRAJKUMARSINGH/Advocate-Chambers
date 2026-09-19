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
