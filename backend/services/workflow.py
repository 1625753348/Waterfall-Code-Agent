from __future__ import annotations
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from uuid import uuid4

from shared.domain_model import (
    UnifiedDomainModel, Phase, ArtifactStatus, TraceEvent,
    RequirementsArtifact, DomainModelArtifact, DatabaseArtifact,
    InterfaceArtifact, SequenceArtifact, PrototypeArtifact,
    CodeArtifact, TestArtifact,
)
from .traceability import TraceabilityService


class PhaseConfig:
    def __init__(
        self,
        name: Phase,
        display_name: str,
        description: str,
        depends_on: List[Phase],
        order: int,
    ):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.depends_on = depends_on
        self.order = order


PHASE_CONFIGS = {
    Phase.REQUIREMENTS: PhaseConfig(
        Phase.REQUIREMENTS, "需求分析", "分析原始需求，识别词汇缺口并建模需求项",
        depends_on=[], order=1,
    ),
    Phase.DOMAIN_MODEL: PhaseConfig(
        Phase.DOMAIN_MODEL, "领域模型", "创建用例图、参与者与用例定义",
        depends_on=[Phase.REQUIREMENTS], order=2,
    ),
    Phase.DATABASE: PhaseConfig(
        Phase.DATABASE, "数据库设计", "设计表结构并生成多方言DDL与ER图",
        depends_on=[Phase.DOMAIN_MODEL], order=3,
    ),
    Phase.INTERFACE: PhaseConfig(
        Phase.INTERFACE, "接口设计", "定义API端点并关联需求与用例",
        depends_on=[Phase.DATABASE], order=4,
    ),
    Phase.SEQUENCE: PhaseConfig(
        Phase.SEQUENCE, "时序图", "生成时序图描述交互流程",
        depends_on=[Phase.INTERFACE], order=5,
    ),
    Phase.PROTOTYPE: PhaseConfig(
        Phase.PROTOTYPE, "页面原型", "设计页面原型并关联接口",
        depends_on=[Phase.SEQUENCE], order=6,
    ),
    Phase.CODE: PhaseConfig(
        Phase.CODE, "代码生成", "生成后端与前端代码",
        depends_on=[Phase.PROTOTYPE], order=7,
    ),
    Phase.TEST: PhaseConfig(
        Phase.TEST, "测试用例", "生成测试用例并验证核心原则",
        depends_on=[Phase.CODE], order=8,
    ),
}


class WorkflowService:
    """Orchestrates phases: sequencing, status tracking, validation, approval flow."""

    def __init__(self, trace_service: TraceabilityService):
        self.trace = trace_service
        self._phase_handlers: Dict[str, Callable] = {}

    def register_handler(self, phase: str, handler: Callable):
        self._phase_handlers[phase] = handler

    def get_phase_config(self, phase: Phase) -> PhaseConfig:
        return PHASE_CONFIGS[phase]

    def get_all_phases(self) -> List[PhaseConfig]:
        return [PHASE_CONFIGS[p] for p in Phase]

    def get_phase_status(self, model: UnifiedDomainModel, phase: str) -> str:
        return model.phase_status.get(phase, "pending")

    def can_execute(self, model: UnifiedDomainModel, phase: str) -> tuple[bool, str]:
        config = PHASE_CONFIGS.get(Phase(phase))
        if not config:
            return False, f"Unknown phase: {phase}"
        for dep in config.depends_on:
            dep_status = model.phase_status.get(dep.value, "pending")
            if dep_status != "approved":
                return False, f"Dependency {dep.value} is not approved (status: {dep_status})"
        current_status = model.phase_status.get(phase, "pending")
        if current_status == "approved":
            return False, f"Phase {phase} is already approved"
        return True, "ok"

    def execute_phase(self, model: UnifiedDomainModel, phase: str, user_id: str = "system", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        can, msg = self.can_execute(model, phase)
        if not can:
            return {"success": False, "error": msg}

        handler = self._phase_handlers.get(phase)
        if not handler:
            return {"success": False, "error": f"No handler registered for phase {phase}"}

        try:
            result = handler(model, params or {})
            model.phase_status[phase] = "pending_review"

            self.trace.record(
                phase=Phase(phase),
                action="execute",
                artifact_id=phase,
                user_id=user_id,
                payload={"result_summary": str(result)[:500]},
                project_id=model.project_id,
            )
            self.trace.save_snapshot(model.project_id, model.to_dict())

            return {"success": True, "phase": phase, "data": result}
        except Exception as e:
            self.trace.record(
                phase=Phase(phase),
                action="execute_failed",
                artifact_id=phase,
                user_id=user_id,
                payload={"error": str(e)},
                project_id=model.project_id,
            )
            return {"success": False, "error": str(e)}

    def approve_phase(self, model: UnifiedDomainModel, phase: str, user_id: str = "system", comments: str = "") -> Dict[str, Any]:
        if model.phase_status.get(phase) not in ("pending_review", "rejected"):
            return {"success": False, "error": f"Phase {phase} is not in reviewable state"}
        model.phase_status[phase] = "approved"
        artifact = model.get_phase_artifact(phase)
        if artifact:
            artifact.status = ArtifactStatus.APPROVED
        self.trace.record(
            phase=Phase(phase), action="approve", artifact_id=phase,
            user_id=user_id, payload={"comments": comments},
            project_id=model.project_id,
        )
        self.trace.save_snapshot(model.project_id, model.to_dict())
        return {"success": True, "phase": phase, "status": "approved"}

    def reject_phase(self, model: UnifiedDomainModel, phase: str, user_id: str = "system", reason: str = "", feedback: str = "") -> Dict[str, Any]:
        if model.phase_status.get(phase) != "pending_review":
            return {"success": False, "error": f"Phase {phase} is not pending review"}
        model.phase_status[phase] = "rejected"
        artifact = model.get_phase_artifact(phase)
        if artifact:
            artifact.status = ArtifactStatus.REJECTED
        self.trace.record(
            phase=Phase(phase), action="reject", artifact_id=phase,
            user_id=user_id, payload={"reason": reason, "feedback": feedback},
            project_id=model.project_id,
        )
        return {"success": True, "phase": phase, "status": "rejected"}

    def rollback(self, model: UnifiedDomainModel, phase: str, user_id: str = "system", reason: str = "") -> Dict[str, Any]:
        target_phase = Phase(phase)
        config = PHASE_CONFIGS.get(target_phase)
        if not config:
            return {"success": False, "error": f"Unknown phase: {phase}"}

        phases_to_clear = [p for p in Phase if p.value == phase or (
            hasattr(PHASE_CONFIGS.get(p), "order") and
            hasattr(config, "order") and
            PHASE_CONFIGS[p].order > config.order
        )]
        for p in phases_to_clear:
            if p.value in model.phase_status:
                model.phase_status[p.value] = "pending"
            artifact = model.get_phase_artifact(p.value)
            if artifact:
                artifact.status = ArtifactStatus.DRAFT

        self.trace.record(
            phase=target_phase, action="rollback", artifact_id=phase,
            user_id=user_id, payload={"reason": reason, "cleared_phases": [p.value for p in phases_to_clear]},
            project_id=model.project_id,
        )
        self.trace.save_snapshot(model.project_id, model.to_dict())
        return {
            "success": True,
            "rolled_back_to": phase,
            "cleared": [p.value for p in phases_to_clear],
        }

    def update_artifact(
        self, model: UnifiedDomainModel, phase: str, artifact_data: Dict[str, Any], user_id: str = "system"
    ) -> Dict[str, Any]:
        builder = {
            "requirements": lambda d: RequirementsArtifact.from_dict(d),
            "domain_model": lambda d: DomainModelArtifact.from_dict(d),
            "database": lambda d: DatabaseArtifact.from_dict(d),
            "interface": lambda d: InterfaceArtifact.from_dict(d),
            "sequence": lambda d: SequenceArtifact.from_dict(d),
            "prototype": lambda d: PrototypeArtifact.from_dict(d),
            "code": lambda d: CodeArtifact.from_dict(d),
            "test": lambda d: TestArtifact.from_dict(d),
        }
        if phase not in builder:
            return {"success": False, "error": f"Unknown phase: {phase}"}

        old_artifact = model.get_phase_artifact(phase)
        old_version = getattr(old_artifact, "version", "0.0") if old_artifact else "0.0"
        new_artifact = builder[phase](artifact_data)
        model.set_phase_artifact(phase, new_artifact)
        model.phase_status[phase] = "pending_review"

        self.trace.record(
            phase=Phase(phase), action="update_artifact", artifact_id=phase,
            user_id=user_id,
            previous_version=old_version,
            payload={"new_version": new_artifact.version if hasattr(new_artifact, "version") else "unknown"},
            project_id=model.project_id,
        )
        self.trace.save_snapshot(model.project_id, model.to_dict())
        return {"success": True, "phase": phase}
