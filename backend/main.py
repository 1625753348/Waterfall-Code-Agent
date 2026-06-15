from __future__ import annotations
import json
import os
import sys
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import io
import zipfile

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from shared.domain_model import UnifiedDomainModel, Phase

from backend.services.traceability import TraceabilityService
from backend.services.workflow import WorkflowService
from backend.services.rollback import RollbackService

from backend.agents.requirements_agent import RequirementsAgent
from backend.agents.domain_model_agent import DomainModelAgent
from backend.agents.database_agent import DatabaseAgent
from backend.agents.interface_agent import InterfaceAgent
from backend.agents.sequence_agent import SequenceAgent
from backend.agents.prototype_agent import PrototypeAgent
from backend.agents.code_agent import CodeAgent
from backend.agents.test_agent import TestAgent


# ── Services & Agents ──────────────────────────────────────────

trace_service = TraceabilityService()
workflow = WorkflowService(trace_service)
rollback_service = RollbackService()

requirements_agent = RequirementsAgent()
domain_model_agent = DomainModelAgent()
database_agent = DatabaseAgent()
interface_agent = InterfaceAgent()
sequence_agent = SequenceAgent()
prototype_agent = PrototypeAgent()
code_agent = CodeAgent()
test_agent = TestAgent()

# Register all phase handlers
workflow.register_handler("requirements", lambda m, p: requirements_agent.execute(m, p))
workflow.register_handler("domain_model", lambda m, p: domain_model_agent.execute(m, p))
workflow.register_handler("database", lambda m, p: database_agent.execute(m, p))
workflow.register_handler("interface", lambda m, p: interface_agent.execute(m, p))
workflow.register_handler("sequence", lambda m, p: sequence_agent.execute(m, p))
workflow.register_handler("prototype", lambda m, p: prototype_agent.execute(m, p))
workflow.register_handler("code", lambda m, p: code_agent.execute(m, p))
workflow.register_handler("test", lambda m, p: test_agent.execute(m, p))


# ── In-memory project store ────────────────────────────────────

projects: Dict[str, UnifiedDomainModel] = {}


def get_or_create_project(project_id: str) -> UnifiedDomainModel:
    if project_id not in projects:
        snapshot = trace_service.get_latest_snapshot(project_id)
        if snapshot:
            model = UnifiedDomainModel.from_dict(snapshot)
            projects[project_id] = model
        else:
            model = UnifiedDomainModel(f"Project-{project_id[:8]}")
            projects[project_id] = model
            trace_service.save_snapshot(project_id, model.to_dict())
    return projects[project_id]


# ── FastAPI App ────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="Waterfall Agent - SDLC 自动化系统",
    description="8阶段瀑布式软件工程自动化Agent系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/Response Models ────────────────────────────────────

class ProjectCreate(BaseModel):
    project_name: str = "My Project"


class RawInput(BaseModel):
    raw_input: str


class PhaseAction(BaseModel):
    project_id: str = "default"
    user_id: str = "system"
    comments: str = ""
    reason: str = ""
    feedback: str = ""


class ExecuteRequest(PhaseAction):
    params: Dict[str, Any] = {}


class UpdateArtifactRequest(PhaseAction):
    artifact_data: Dict[str, Any]


# ── API Routes ─────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "waterfall-agent"}


@app.post("/api/projects")
async def create_project(req: ProjectCreate):
    model = UnifiedDomainModel(req.project_name)
    projects[model.project_id] = model
    trace_service.save_snapshot(model.project_id, model.to_dict())
    return {
        "project_id": model.project_id,
        "project_name": model.project_name,
        "created_at": model.created_at,
        "phase_status": model.phase_status,
    }


@app.get("/api/projects")
async def list_projects():
    result = []
    for pid, m in projects.items():
        result.append({
            "id": pid,
            "project_id": pid,
            "project_name": m.project_name,
            "created_at": m.created_at,
            "phase_status": m.phase_status,
        })
    return {"projects": result}


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    model = get_or_create_project(project_id)
    return model.to_dict()


@app.get("/api/projects/{project_id}/phases")
async def get_phases(project_id: str):
    model = get_or_create_project(project_id)
    phase_configs = sorted(workflow.get_all_phases(), key=lambda x: x.order)
    arr = []
    obj = {}
    for pc in phase_configs:
        status = model.phase_status.get(pc.name.value, "pending")
        item = {
            "id": pc.name.value,
            "name": pc.name.value,
            "display_name": pc.display_name,
            "description": pc.description,
            "order": pc.order,
            "depends_on": [d.value for d in pc.depends_on],
            "status": status,
        }
        arr.append(item)
        obj[pc.name.value] = {"status": status}
    return {"phases": arr, "phase_map": obj}


@app.post("/api/projects/{project_id}/phases/{phase}/execute")
async def execute_phase(project_id: str, phase: str, req: ExecuteRequest):
    model = get_or_create_project(project_id)
    result = workflow.execute_phase(model, phase, req.user_id, req.params)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/projects/{project_id}/phases/{phase}/approve")
async def approve_phase(project_id: str, phase: str, req: PhaseAction):
    model = get_or_create_project(project_id)
    result = workflow.approve_phase(model, phase, req.user_id, req.comments)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/projects/{project_id}/phases/{phase}/reject")
async def reject_phase(project_id: str, phase: str, req: PhaseAction):
    model = get_or_create_project(project_id)
    result = workflow.reject_phase(model, phase, req.user_id, req.reason, req.feedback)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/projects/{project_id}/phases/{phase}/rollback")
async def rollback_phase(project_id: str, phase: str, req: PhaseAction):
    model = get_or_create_project(project_id)
    result = workflow.rollback(model, phase, req.user_id, req.reason)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/projects/{project_id}/phases/{phase}/artifact")
async def update_artifact(project_id: str, phase: str, req: UpdateArtifactRequest):
    model = get_or_create_project(project_id)
    result = workflow.update_artifact(model, phase, req.artifact_data, req.user_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/projects/{project_id}/phases/{phase}/artifact")
async def get_artifact(project_id: str, phase: str):
    model = get_or_create_project(project_id)
    artifact = model.get_phase_artifact(phase)
    if artifact is None:
        raise HTTPException(status_code=404, detail=f"Artifact for phase {phase} not found")
    return artifact.to_dict()


@app.get("/api/projects/{project_id}/code/download")
async def download_code_zip(project_id: str):
    model = get_or_create_project(project_id)
    art = model.code
    if not art.backend_files and not art.frontend_files:
        raise HTTPException(status_code=404, detail="No code files to download")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in art.backend_files:
            zf.writestr(f.path, f.content)
        for f in art.frontend_files:
            zf.writestr(f.path, f.content)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={project_id[:8]}_code.zip"})

@app.get("/api/projects/{project_id}/trace")
async def get_trace(project_id: str, phase: Optional[str] = Query(None), limit: int = Query(100)):
    events = trace_service.get_history(project_id, phase, limit)
    return {"events": events}


@app.get("/api/projects/{project_id}/snapshots")
async def list_snapshots(project_id: str):
    snapshots = rollback_service.list_snapshots(project_id)
    return {"snapshots": snapshots}


@app.post("/api/projects/{project_id}/snapshots")
async def create_snapshot(project_id: str):
    model = get_or_create_project(project_id)
    result = rollback_service.create_snapshot(project_id, model)
    return result


@app.post("/api/projects/{project_id}/restore/{snapshot_id}")
async def restore_snapshot(project_id: str, snapshot_id: str):
    restored = rollback_service.restore_snapshot(project_id, snapshot_id)
    if restored is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    projects[project_id] = restored
    trace_service.save_snapshot(project_id, restored.to_dict())
    return {"message": f"Restored snapshot {snapshot_id}", "project": restored.to_dict()}


# ── Requirements-specific route ────────────────────────────────

@app.post("/api/projects/{project_id}/requirements/analyze")
async def analyze_requirements(project_id: str, req: RawInput):
    model = get_or_create_project(project_id)
    result = requirements_agent.execute(model, {"raw_input": req.raw_input})
    trace_service.record(
        phase=Phase.REQUIREMENTS, action="analyze",
        artifact_id="requirements", user_id="system",
        payload={"input_length": len(req.raw_input), "items": len(result.get("items", []))},
        project_id=project_id,
    )
    trace_service.save_snapshot(project_id, model.to_dict())
    model.phase_status["requirements"] = "pending_review"
    return result


# ── Serve Frontend Static Files ────────────────────────────────

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
