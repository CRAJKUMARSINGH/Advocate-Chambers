# Project Archive and LFS Index

This document records the storage policy for completed planning projects in Advocate-Chambers.

## Current project families

| Project family | Current source locations | Archive slug | Migration status |
|---|---|---|---|
| Advocate-Chambers / Bar Association | bar-association-hall, CAD-Drawings, code-junction/Bar-Association-Standard-Drawing-Package | advocate-chambers | Inventory required; legacy paths retained |
| Jamuniya-Shaktawat | Jamuniya-Shaktawat/CAD, Jamuniya-Shaktawat/PDF, reference images | jamuniya-shaktawat | Inventory required; legacy paths retained |

## Canonical destination

~~~text
projects/YYYY/project-slug/
  project.json
  source/
  revisions/rNNN/
    model/
    inputs/
    cad/
    pdf/
    renders/
    validation/
    manifest.json
  current.json
~~~

Large binary artifacts are governed by the repository .gitattributes file and Git LFS. Text models, schemas, manifests, Markdown, Python, and TypeScript remain normal Git files.

## Migration safety

Legacy directories are read-only until every artifact has a destination path and SHA-256 checksum. No files are deleted, overwritten, or renamed solely for organization. Duplicate cleanup requires a separate review and approval.

## Required project metadata

Each project must retain its building type, location, units, north/orientation, levels, source model, assumptions, rule-pack version, revision history, validation report, artifact hashes, and professional-review status.
