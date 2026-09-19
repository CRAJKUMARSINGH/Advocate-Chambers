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


app = FastAPI(
    title="Advocate-Chambers CAD API",
    description=(
        "Typed adapter for the React 19.3 editor. Geometry + DXF/PDF export "
        "remain in Python; this service validates, queues jobs, and serves "
        "artifact links."
    ),
    version="1.0.0-week8",
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
