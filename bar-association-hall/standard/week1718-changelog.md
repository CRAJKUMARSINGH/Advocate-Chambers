# Week 17–18 enrichment changelog

## Week 17 — Site feasibility and transparent plan review

- Added a site workspace with plot bounds, north, setbacks, access points,
  level/footprint records, context layers, and explicit assumptions.
- Added preliminary rule-pack evaluation for coverage, setbacks, height,
  floor-area target, parking, accessibility, daylight, ventilation, egress,
  fire access, service access, and wet-area coordination.
- Every result records its rule ID, input geometry, source, calculation,
  assumption, confidence, and suggested correction.
- PDF/CAD review is a separate non-authoritative workflow; recognition never
  claims approval or promotes uncertain geometry automatically.

## Week 18 — Collaboration, revision history, and professional delivery

- Added deterministic read-only technical and presentation review-link
  contracts and comments anchored to model objects or render viewpoints.
- Added revision comparison for geometry, validation, area, openings, and
  furniture changes.
- Added Draft, Review, Client Presentation, Preliminary Coordination, and
  Not Issuable approval states.
- Added a coordinated export manifest and release gate for source JSON,
  validation report, technical/coloured PDFs, DXF, optional IFC, images,
  assumptions, rule-pack version, and manifest.
- Unresolved BLOCKER findings are rejected unless the caller explicitly marks
  the package as a non-issuable review package.
