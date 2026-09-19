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

The current legacy fixture intentionally reports unresolved route/opening
findings. That is an auditable failure state, not a green-light claim for
construction.

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