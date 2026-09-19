"""FastAPI thin adapter — Patch 2 of TRANSFORMATION_PATCH_GUIDE.

Geometry authority remains in Python (traecad_engine + the two drawing
generators under /bar-association-hall). FastAPI only exposes typed endpoints
for the React 19.3 editor to call. No DXF/PDF rendering happens inline for
/generate — it is queued as a Job and produces Artifact links.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict

ROOT = Path(__file__).resolve().parents[2]
BA_HALL = ROOT / "bar-association-hall"
SCHEMA_PATH = ROOT / "packages" / "schema" / "project-v2.schema.json"

sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(BA_HALL))

try:
    import traecad_engine  # noqa: F401  — authoritative geometry engine
except Exception:  # pragma: no cover - engine import is informational
    traecad_engine = None

try:
    from drawing_model import validate_model, load_model  # type: ignore
except Exception:  # pragma: no cover
    validate_model = None  # type: ignore
    load_model = None  # type: ignore

try:
    from week34 import enrichment_report  # type: ignore
    from week56 import enrichment_report as week56_enrichment_report  # type: ignore
    from week78 import enrichment_report as week78_enrichment_report  # type: ignore
except Exception:  # pragma: no cover
    enrichment_report = None  # type: ignore
    week56_enrichment_report = None  # type: ignore
    week78_enrichment_report = None  # type: ignore

try:
    from week1112 import (  # type: ignore
        accept_revision,
        build_capability_report,
        command_preview,
        compile_brief,
        performance_counters,
    )
except Exception:  # pragma: no cover
    accept_revision = None  # type: ignore
    build_capability_report = None  # type: ignore
    command_preview = None  # type: ignore
    compile_brief = None  # type: ignore
    performance_counters = None  # type: ignore

try:
    from week1314 import (  # type: ignore
        build_editable_twin,
        build_sheet_report,
        build_synchronized_views,
        recognize_import,
    )
except Exception:  # pragma: no cover
    build_editable_twin = None  # type: ignore
    build_sheet_report = None  # type: ignore
    build_synchronized_views = None  # type: ignore
    recognize_import = None  # type: ignore

try:
    from week1516 import (  # type: ignore
        ASSET_CATALOG,
        ROOM_TEMPLATES,
        candidate_studio,
        design_package,
        edit_placements,
        furnish_model,
        render_job,
        validate_placement,
    )
except Exception:  # pragma: no cover
    ASSET_CATALOG = None  # type: ignore
    ROOM_TEMPLATES = None  # type: ignore
    candidate_studio = None  # type: ignore
    design_package = None  # type: ignore
    edit_placements = None  # type: ignore
    furnish_model = None  # type: ignore
    render_job = None  # type: ignore
    validate_placement = None  # type: ignore

try:
    from week1718 import (  # type: ignore
        APPROVAL_STATES,
        ANCHOR_TYPES,
        compare_revisions,
        coordinated_package,
        create_comment,
        create_review_link,
        enrichment_report as week1718_enrichment_report,
        evaluate_rule_pack,
        imported_review_workflow,
    )
except Exception:  # pragma: no cover
    APPROVAL_STATES = None  # type: ignore
    ANCHOR_TYPES = None  # type: ignore
    compare_revisions = None  # type: ignore
    coordinated_package = None  # type: ignore
    create_comment = None  # type: ignore
    create_review_link = None  # type: ignore
    week1718_enrichment_report = None  # type: ignore
    evaluate_rule_pack = None  # type: ignore
    imported_review_workflow = None  # type: ignore

try:
    from week1920 import (  # type: ignore
        archive_project_state,
        build_archive_manifest,
        create_revision_record,
        restore_project_state,
        verify_project_package,
    )
except Exception:  # pragma: no cover
    archive_project_state = None  # type: ignore
    build_archive_manifest = None  # type: ignore
    create_revision_record = None  # type: ignore
    restore_project_state = None  # type: ignore
    verify_project_package = None  # type: ignore


app = FastAPI(
    title="Advocate-Chambers CAD API",
    description=(
        "Typed adapter for the React 19.3 editor. Geometry + DXF/PDF export "
        "remain in Python; this service validates, queues jobs, and serves "
        "artifact links."
    ),
    version="1.0.0-week20",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# In-memory stores — Patch 2 only. Persistence is deferred to Patch 4+.
# ---------------------------------------------------------------------------
JOBS: dict[str, dict[str, Any]] = {}
ARTIFACTS: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Pydantic models — aligned with packages/schema/project-v2.schema.json
# ---------------------------------------------------------------------------
class ProjectRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., pattern=r"^proj-[a-z0-9-]+$")
    name: str
    units: str = "inch"
    revision: int = 1


class ValidateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    project: dict[str, Any]
    plans: dict[str, Any]


class ValidateResponse(BaseModel):
    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checkedAt: str


class BriefCompileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(..., min_length=1, max_length=12000)
    defaultUnits: str = Field(default="inch", pattern="^(inch|imperial|metric|in|ft|m|cm|mm)$")


class CommandPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    command: str = Field(..., min_length=1, max_length=2000)
    author: str = Field(default="brief-compiler", min_length=1, max_length=120)
    accept: bool = False


class ImportRecognizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sourcePath: str | None = Field(default=None, max_length=500)
    content: str | None = Field(default=None, max_length=2_000_000)


class FurnishRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: dict[str, Any]
    seed: int = Field(default=1516, ge=0, le=2_147_483_647)


class PlacementValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: dict[str, Any]
    placement: dict[str, Any]
    existing: list[dict[str, Any]] = Field(default_factory=list)


class PlacementEditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: dict[str, Any]
    placements: list[dict[str, Any]]
    operation: dict[str, Any]


class CandidateStudioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: dict[str, Any]
    seeds: list[int] = Field(default_factory=lambda: [1516, 1523, 1547], min_length=1, max_length=12)
    inheritedFindings: list[dict[str, Any]] = Field(default_factory=list)


class DesignPackageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidateId: str | None = None
    seed: int = Field(default=1516, ge=0, le=2_147_483_647)
    model: dict[str, Any]


class SiteFeasibilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: dict[str, Any]


class ReviewLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: dict[str, Any]
    view: str = Field(default="technical", pattern="^(technical|presentation)$")
    baseUrl: str = Field(default="/review", min_length=1, max_length=200)


class CommentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: dict[str, Any]
    author: str = Field(..., min_length=1, max_length=120)
    body: str = Field(..., min_length=1, max_length=5000)
    anchorType: str
    anchorId: str = Field(..., min_length=1, max_length=200)
    viewpoint: dict[str, Any] | None = None


class RevisionCompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    before: dict[str, Any]
    after: dict[str, Any]


class DeliveryPackageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: dict[str, Any]
    feasibilityReport: dict[str, Any] | None = None
    allowNonIssuable: bool = False
    includeIfc: bool = False


class ImportedReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sourcePath: str = Field(..., min_length=1, max_length=500)
    sourceFormat: str | None = Field(default=None, max_length=20)


class ArchiveManifestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: dict[str, Any]
    artifactPaths: list[str] | None = None
    validationReport: dict[str, Any] | None = None
    rulePackVersion: str | None = None


class RevisionRecordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: dict[str, Any]
    author: str = Field(..., min_length=1, max_length=120)
    reason: str = Field(..., min_length=1, max_length=2000)
    validationReport: dict[str, Any] | None = None
    parentRevision: int | None = Field(default=None, ge=0)
    artifactManifest: dict[str, Any] | None = None


class PackageVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    manifest: dict[str, Any]
    requireComplete: bool = True


class ArchiveStateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: dict[str, Any]
    action: str = Field(..., pattern="^(archive|restore)$")
    author: str = Field(..., min_length=1, max_length=120)
    reason: str = Field(..., min_length=1, max_length=2000)


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    projectId: str
    pipeline: str = Field(default="refined", pattern="^(refined|standard)$")
    level: str | None = Field(default=None, pattern="^(GF|FF|ALL)$")
    sheetSize: str = Field(default="A4", pattern="^(A4|A3|A2|A1|A0)$")


class JobResponse(BaseModel):
    jobId: str
    status: str
    enqueuedAt: str


class JobStatus(BaseModel):
    jobId: str
    status: str
    progress: int
    startedAt: str | None
    finishedAt: str | None
    artifactIds: list[str]
    error: str | None = None


class Artifact(BaseModel):
    artifactId: str
    jobId: str
    name: str
    kind: str
    url: str
    sizeBytes: int | None = None
    sha256: str | None = None
    generatedAt: str


# ---------------------------------------------------------------------------
# Endpoints — the 6 documented in Patch 2 §3
# ---------------------------------------------------------------------------
@app.get("/health", tags=["meta"])
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "advocate-chambers-cad-api",
        "version": app.version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritativeGeometry": "python" if traecad_engine is not None else "unavailable",
        "schema": str(SCHEMA_PATH.relative_to(ROOT)) if SCHEMA_PATH.exists() else None,
    }


@app.get("/projects/{project_id}", tags=["projects"], response_model=ProjectRef)
def get_project(project_id: str) -> ProjectRef:
    """Return the project header — Patch 2 stub; file-backed JSON in Patch 4."""
    known = {
        "proj-banswara-bar-association": {
            "id": "proj-banswara-bar-association",
            "name": "Bar Association Hall - Banswara",
            "units": "inch",
            "revision": 1,
        }
    }
    if project_id not in known:
        raise HTTPException(status_code=404, detail=f"unknown project {project_id!r}")
    return ProjectRef(**known[project_id])


@app.post("/validate", tags=["validation"], response_model=ValidateResponse)
def validate(req: ValidateRequest) -> ValidateResponse:
    """Validate a project + plans payload using drawing_model.validate_model.

    Falls back to a light structural check if drawing_model cannot be loaded,
    but only the drawing_model path enforces NBC stair arithmetic, opening
    fit, and non-overlap constraints.
    """
    errors: list[str] = []
    warnings: list[str] = []
    if validate_model is not None:
        try:
            errs = validate_model(req.project, req.plans)
            errors.extend(errs)
        except Exception as exc:  # pragma: no cover
            errors.append(f"validate_model raised: {exc!r}")
    else:  # pragma: no cover
        warnings.append("drawing_model import failed — light structural only")
        if "spaces" not in req.plans:
            errors.append("plans.spaces missing")
        if "openings" not in req.plans:
            errors.append("plans.openings missing")
    return ValidateResponse(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        checkedAt=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/analysis", tags=["validation"])
def analysis(level: str | None = None) -> dict[str, Any]:
    """Return the Week 3 graph and Week 4 opening semantics for the viewport."""

    if (
        load_model is None
        or enrichment_report is None
        or week56_enrichment_report is None
        or week78_enrichment_report is None
    ):
        raise HTTPException(status_code=503, detail="analysis engine unavailable")
    try:
        site, plans = load_model()
        report = enrichment_report(site, plans)
        # Week 5–6 consumes the canonical model so program and coordination
        # metadata remain additive instead of being flattened into the legacy
        # drawing view.
        from week2 import load_canonical_model  # type: ignore

        canonical = load_canonical_model()
        coordination = week56_enrichment_report(canonical)
        enriched = week78_enrichment_report(canonical)
    except Exception as exc:  # pragma: no cover - surfaced as an API diagnostic
        raise HTTPException(status_code=500, detail=f"analysis failed: {exc}") from exc

    selected_level = level if level in {"GF", "FF"} else None
    spaces = [
        {
            "id": space.get("id"),
            "levelId": space.get("level"),
            "name": space.get("name"),
            "rect": space.get("rect"),
            "roomUse": space.get("roomUse"),
        }
        for space in plans.get("spaces", [])
        if selected_level is None or space.get("level") == selected_level
    ]
    graph = report["week3"]["graph"]
    graph["nodes"] = [
        node
        for node in graph["nodes"]
        if selected_level is None
        or node.get("levelId") == selected_level
        or node.get("kind") == "exterior-zone"
    ]
    node_ids = {node["id"] for node in graph["nodes"]}
    graph["edges"] = [
        edge
        for edge in graph["edges"]
        if edge.get("from") in node_ids and edge.get("to") in node_ids
    ]
    graph["routes"] = [
        route
        for route in graph["routes"]
        if selected_level is None or route.get("levelId") == selected_level
    ]
    schedule = [
        item
        for item in report["week4"]["schedule"]
        if selected_level is None or item.get("levelId") == selected_level
    ]
    findings = [
        finding
        for finding in report["findings"]
        if selected_level is None or finding.get("levelId") == selected_level
    ]
    findings.extend(
        finding
        for finding in coordination["week5"]["findings"] + coordination["week6"]["findings"]
        if selected_level is None or finding.get("levelId") in {None, selected_level}
    )
    findings.extend(
        finding
        for finding in enriched["week7"]["findings"] + enriched["week8"]["findings"]
        if selected_level is None or finding.get("levelId") in {None, selected_level}
    )
    return {
        "reportVersion": enriched["reportVersion"],
        "status": enriched["status"],
        "findingCounts": {
            severity: sum(1 for finding in findings if finding["severity"] == severity)
            for severity in ("BLOCKER", "ERROR", "WARNING")
            if any(finding["severity"] == severity for finding in findings)
        },
        "spaces": spaces,
        "graph": graph,
        "openings": schedule,
        "findings": findings,
        "week5": coordination["week5"],
        "week6": coordination["week6"],
        "connectors": coordination["week5"]["connectors"],
        "program": coordination["week6"]["program"],
        "orientation": coordination["week6"]["program"]["orientation"],
        "adjacencies": coordination["week6"]["program"]["adjacencyEvaluations"],
        "week7": enriched["week7"],
        "week8": enriched["week8"],
        "rulePack": enriched["week7"]["selectedRulePack"],
        "drawingQuality": enriched["week8"],
    }


@app.get("/capabilities", tags=["product"])
def capabilities() -> dict[str, Any]:
    """Describe product modes without implying that provisional features exist."""
    if build_capability_report is None:
        raise HTTPException(status_code=503, detail="product capability layer unavailable")
    return build_capability_report()


@app.post("/brief/compile", tags=["brief"])
def compile_brief_endpoint(req: BriefCompileRequest) -> dict[str, Any]:
    """Compile a brief into facts and topology questions without generating geometry."""
    if compile_brief is None:
        raise HTTPException(status_code=503, detail="brief compiler unavailable")
    return compile_brief(req.text, default_units=req.defaultUnits)


@app.post("/brief/command", tags=["brief"])
def command_endpoint(req: CommandPreviewRequest) -> dict[str, Any]:
    """Preview a typed command against the canonical model.

    Acceptance is intentionally in-memory at this stage. A future persistence
    worker can save the returned revision after the same validation contract
    has passed; the API never treats a prompt string as an implicit mutation.
    """
    if command_preview is None or accept_revision is None:
        raise HTTPException(status_code=503, detail="brief command layer unavailable")
    try:
        from week2 import load_canonical_model  # type: ignore

        canonical = load_canonical_model()
        preview = command_preview(canonical, req.command, author=req.author)
        if req.accept and preview["status"] != "blocked":
            accepted = accept_revision(canonical, preview)
            preview["acceptedRevision"] = accepted["revision"]
            preview["acceptedModelRevision"] = accepted["model"]["project"]["revision"]
            preview["canonicalModelUnchanged"] = False
        return preview
    except Exception as exc:  # pragma: no cover - surfaced as an API diagnostic
        raise HTTPException(status_code=500, detail=f"brief command failed: {exc}") from exc


@app.get("/performance", tags=["product"])
def performance() -> dict[str, Any]:
    """Return local-only counters for the current canonical model."""
    if performance_counters is None:
        raise HTTPException(status_code=503, detail="performance counters unavailable")
    try:
        from week2 import load_canonical_model  # type: ignore

        return performance_counters(load_canonical_model())
    except Exception as exc:  # pragma: no cover - surfaced as an API diagnostic
        raise HTTPException(status_code=500, detail=f"performance counters failed: {exc}") from exc


@app.post("/import/recognize", tags=["import"])
def import_recognize(req: ImportRecognizeRequest) -> dict[str, Any]:
    """Inspect a plan source without promoting uncertain recognition to geometry."""
    if recognize_import is None or build_editable_twin is None:
        raise HTTPException(status_code=503, detail="import recognition layer unavailable")
    try:
        from week2 import load_canonical_model  # type: ignore

        report = recognize_import(source_path=req.sourcePath, content=req.content)
        model = load_canonical_model()
        report["editableTwin"] = build_editable_twin(model, report)
        return report
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"source not found: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"import recognition failed: {exc}") from exc


@app.get("/views/synchronized", tags=["views"])
def synchronized_views() -> dict[str, Any]:
    """Return the shared-revision 2D/3D/section/elevation view contract."""
    if build_synchronized_views is None:
        raise HTTPException(status_code=503, detail="synchronized view layer unavailable")
    try:
        from week2 import load_canonical_model  # type: ignore

        return build_synchronized_views(load_canonical_model())
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"synchronized views failed: {exc}") from exc


@app.get("/sheet-standard", tags=["export"])
def sheet_standard() -> dict[str, Any]:
    """Return the paper-space policy used by future PDF and DXF exports."""
    if build_sheet_report is None:
        raise HTTPException(status_code=503, detail="sheet layout standard unavailable")
    try:
        from week2 import load_canonical_model  # type: ignore

        return build_sheet_report(load_canonical_model())
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"sheet standard failed: {exc}") from exc


@app.get("/furnishing/catalog", tags=["furnishing"])
def furnishing_catalog() -> dict[str, Any]:
    """Return the Week 15 parametric asset and room-template catalog."""
    if ASSET_CATALOG is None or ROOM_TEMPLATES is None:
        raise HTTPException(status_code=503, detail="parametric asset layer unavailable")
    return {"version": "week15.parametric-assets.v1", "assets": ASSET_CATALOG, "roomTemplates": ROOM_TEMPLATES}


@app.post("/furnishing/preview", tags=["furnishing"])
def furnishing_preview(req: FurnishRequest) -> dict[str, Any]:
    """Place presentation assets without mutating authoritative geometry."""
    if furnish_model is None:
        raise HTTPException(status_code=503, detail="parametric furnishing layer unavailable")
    return furnish_model(req.model, seed=req.seed)


@app.post("/furnishing/validate", tags=["furnishing"])
def furnishing_validate(req: PlacementValidationRequest) -> dict[str, Any]:
    """Check a placement against room, opening, route, stair and service geometry."""
    if validate_placement is None:
        raise HTTPException(status_code=503, detail="parametric furnishing layer unavailable")
    findings = validate_placement(req.model, req.placement, existing=req.existing)
    return {"status": "blocked" if findings else "pass", "findings": findings}


@app.post("/furnishing/edit", tags=["furnishing"])
def furnishing_edit(req: PlacementEditRequest) -> dict[str, Any]:
    """Apply one typed drag, rotate, duplicate, align, replace or auto-place edit."""
    if edit_placements is None:
        raise HTTPException(status_code=503, detail="parametric furnishing layer unavailable")
    try:
        return edit_placements(req.model, req.placements, req.operation)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/candidates/studio", tags=["candidates"])
def candidates_studio(req: CandidateStudioRequest) -> dict[str, Any]:
    """Compare deterministic candidates; blockers always disqualify a winner."""
    if candidate_studio is None:
        raise HTTPException(status_code=503, detail="candidate studio unavailable")
    return candidate_studio(req.model, seeds=req.seeds, inherited_findings=req.inheritedFindings)


@app.post("/presentation/package", tags=["presentation"])
def presentation_package(req: DesignPackageRequest) -> dict[str, Any]:
    """Return moodboard, materials, non-destructive layers and render manifests."""
    if design_package is None or candidate_studio is None:
        raise HTTPException(status_code=503, detail="presentation pipeline unavailable")
    candidate_id = req.candidateId
    if candidate_id is None:
        candidate_id = candidate_studio(req.model, seeds=[req.seed])["bestCandidateId"]
    return design_package(req.model, candidate_id, seed=req.seed)


@app.post("/presentation/render-job", tags=["presentation"])
def presentation_render_job(req: DesignPackageRequest) -> dict[str, Any]:
    """Create a deterministic queued render, panorama or presentation-sheet job."""
    if render_job is None:
        raise HTTPException(status_code=503, detail="render pipeline unavailable")
    kind = str(req.model.get("renderKind", "render"))
    try:
        return render_job(kind, req.model.get("project", {}).get("revision"), req.candidateId, req.seed)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/site/feasibility", tags=["site-review"])
def site_feasibility(req: SiteFeasibilityRequest) -> dict[str, Any]:
    """Evaluate the transparent Week 17 rule-pack checks."""
    if evaluate_rule_pack is None:
        raise HTTPException(status_code=503, detail="site feasibility layer unavailable")
    try:
        return evaluate_rule_pack(req.model)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/site/imported-review", tags=["site-review"])
def site_imported_review(req: ImportedReviewRequest) -> dict[str, Any]:
    """Create a non-authoritative PDF/CAD review workflow contract."""
    if imported_review_workflow is None:
        raise HTTPException(status_code=503, detail="imported review layer unavailable")
    return imported_review_workflow(req.sourcePath, req.sourceFormat)


@app.post("/collaboration/review-link", tags=["collaboration"])
def collaboration_review_link(req: ReviewLinkRequest) -> dict[str, Any]:
    """Create a deterministic read-only technical or presentation link."""
    if create_review_link is None:
        raise HTTPException(status_code=503, detail="collaboration layer unavailable")
    try:
        return create_review_link(req.model, view=req.view, base_url=req.baseUrl)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/collaboration/comments", tags=["collaboration"])
def collaboration_comment(req: CommentRequest) -> dict[str, Any]:
    """Create a comment anchored to a model object or render viewpoint."""
    if create_comment is None:
        raise HTTPException(status_code=503, detail="collaboration layer unavailable")
    try:
        return create_comment(
            req.model,
            author=req.author,
            body=req.body,
            anchor_type=req.anchorType,
            anchor_id=req.anchorId,
            viewpoint=req.viewpoint,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/collaboration/revision-compare", tags=["collaboration"])
def collaboration_revision_compare(req: RevisionCompareRequest) -> dict[str, Any]:
    """Compare geometry, validation, areas, openings, and furniture."""
    if compare_revisions is None:
        raise HTTPException(status_code=503, detail="revision comparison layer unavailable")
    return compare_revisions(req.before, req.after)


@app.post("/delivery/package", tags=["delivery"])
def delivery_package(req: DeliveryPackageRequest) -> dict[str, Any]:
    """Build the Week 18 coordinated package manifest and release decision."""
    if coordinated_package is None or evaluate_rule_pack is None:
        raise HTTPException(status_code=503, detail="professional delivery layer unavailable")
    feasibility = req.feasibilityReport or evaluate_rule_pack(req.model)
    return coordinated_package(
        req.model,
        feasibility,
        allow_non_issuable=req.allowNonIssuable,
        include_ifc=req.includeIfc,
    )


@app.get("/delivery/contract", tags=["delivery"])
def delivery_contract() -> dict[str, Any]:
    """Return approval states and the Week 18 package contract."""
    if APPROVAL_STATES is None or ANCHOR_TYPES is None:
        raise HTTPException(status_code=503, detail="professional delivery layer unavailable")
    return {
        "version": "week18.professional-delivery.v1",
        "approvalStates": list(APPROVAL_STATES),
        "commentAnchors": sorted(ANCHOR_TYPES),
        "releaseGate": "unresolved BLOCKER findings require an explicit Not Issuable review export",
    }


@app.post("/archive/manifest", tags=["archive"])
def archive_manifest(req: ArchiveManifestRequest) -> dict[str, Any]:
    """Build a manifest-first archive plan with real or missing artifact records."""
    if build_archive_manifest is None:
        raise HTTPException(status_code=503, detail="archive layer unavailable")
    return build_archive_manifest(
        req.model,
        artifact_paths=req.artifactPaths or (
            "bar-association-hall/standard/model/project.json",
            "bar-association-hall/standard/week17-site-feasibility-report.json",
            "bar-association-hall/standard/week18-delivery-package-report.json",
        ),
        validation_report=req.validationReport,
        rule_pack_version=req.rulePackVersion,
    )


@app.post("/revisions/record", tags=["archive"])
def revision_record(req: RevisionRecordRequest) -> dict[str, Any]:
    """Create an immutable, deterministic revision descriptor."""
    if create_revision_record is None:
        raise HTTPException(status_code=503, detail="revision layer unavailable")
    try:
        return create_revision_record(
            req.model,
            author=req.author,
            reason=req.reason,
            validation_report=req.validationReport,
            parent_revision=req.parentRevision,
            artifact_manifest=req.artifactManifest,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/archive/verify", tags=["archive"])
def archive_verify(req: PackageVerifyRequest) -> dict[str, Any]:
    """Verify manifest structure and optionally require a complete package."""
    if verify_project_package is None:
        raise HTTPException(status_code=503, detail="archive layer unavailable")
    return verify_project_package(req.manifest, require_complete=req.requireComplete)


@app.post("/archive/state", tags=["archive"])
def archive_state(req: ArchiveStateRequest) -> dict[str, Any]:
    """Soft-archive or restore state without changing the current revision."""
    operation = archive_project_state if req.action == "archive" else restore_project_state
    if operation is None:
        raise HTTPException(status_code=503, detail="archive layer unavailable")
    try:
        return operation(req.state, author=req.author, reason=req.reason)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/generate", tags=["jobs"], response_model=JobResponse)
def generate(req: GenerateRequest) -> JobResponse:
    """Queue a DXF+PDF generation job. Does NOT render inline.

    The worker (Patch 4) will exec the selected generator and publish artifacts
    against this jobId. For Patch 2 we expose the contract shape plus a
    best-effort sync execution so endpoints are demonstrable.
    """
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    enqueued = datetime.now(timezone.utc).isoformat()
    JOBS[job_id] = {
        "status": "pending",
        "progress": 0,
        "startedAt": None,
        "finishedAt": None,
        "artifactIds": [],
        "error": None,
        "request": req.model_dump(),
    }
    # Patch-2-only eager transition: mark running, do not block response.
    JOBS[job_id]["status"] = "queued"
    return JobResponse(jobId=job_id, status="queued", enqueuedAt=enqueued)


@app.get("/jobs/{job_id}", tags=["jobs"], response_model=JobStatus)
def get_job(job_id: str) -> JobStatus:
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="unknown job")
    j = JOBS[job_id]
    if j["status"] == "queued":
        j["status"] = "running"
        j["progress"] = 50
        j["startedAt"] = j.get("startedAt") or datetime.now(timezone.utc).isoformat()
        # Patch 2: produce synthetic "done" state on second poll so UI contract
        # is observable. Real Patch 4 worker runs subprocess generators.
        j["status"] = "done"
        j["progress"] = 100
        j["finishedAt"] = datetime.now(timezone.utc).isoformat()
        for kind in ("dxf-gf", "dxf-ff", "pdf-gf", "pdf-ff", "review-pdf"):
            aid = f"art-{uuid.uuid4().hex[:8]}-{kind}"
            ARTIFACTS[aid] = {
                "jobId": job_id,
                "name": f"{req_name(job_id, kind)}.{ext_of(kind)}",
                "kind": kind,
                "url": f"/artifacts/{aid}",
                "generatedAt": datetime.now(timezone.utc).isoformat(),
            }
            j["artifactIds"].append(aid)
    return JobStatus(
        jobId=job_id,
        status=j["status"],
        progress=j["progress"],
        startedAt=j["startedAt"],
        finishedAt=j["finishedAt"],
        artifactIds=j["artifactIds"],
        error=j.get("error"),
    )


@app.get("/artifacts/{artifact_id}", tags=["artifacts"], response_model=Artifact)
def get_artifact(artifact_id: str) -> Artifact:
    if artifact_id not in ARTIFACTS:
        raise HTTPException(status_code=404, detail="unknown artifact")
    a = ARTIFACTS[artifact_id]
    return Artifact(
        artifactId=artifact_id,
        jobId=a["jobId"],
        name=a["name"],
        kind=a["kind"],
        url=a["url"],
        generatedAt=a["generatedAt"],
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def req_name(job_id: str, kind: str) -> str:
    return f"{job_id}-{kind.replace('-', '_')}"


def ext_of(kind: str) -> str:
    return "dxf" if kind.startswith("dxf") else "pdf"
