from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Set
from uuid import uuid4, UUID


class Phase(Enum):
    REQUIREMENTS = "requirements"
    DOMAIN_MODEL = "domain_model"
    DATABASE = "database"
    INTERFACE = "interface"
    SEQUENCE = "sequence"
    PROTOTYPE = "prototype"
    CODE = "code"
    TEST = "test"


class ArtifactStatus(Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class TraceEvent:
    def __init__(
        self,
        phase: Phase,
        action: str,
        artifact_id: str,
        user_id: str = "system",
        previous_version: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ):
        self.id = str(uuid4())
        self.timestamp = datetime.utcnow().isoformat()
        self.phase = phase.value
        self.action = action
        self.artifact_id = artifact_id
        self.user_id = user_id
        self.previous_version = previous_version
        self.payload = payload or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "phase": self.phase,
            "action": self.action,
            "artifact_id": self.artifact_id,
            "user_id": self.user_id,
            "previous_version": self.previous_version,
            "payload": self.payload,
        }


class UnifiedDomainModel:
    """Shared domain model that evolves across all phases."""

    def __init__(self, project_name: str):
        self.project_id = str(uuid4())
        self.project_name = project_name
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at

        # Phase 1: Requirements
        self.requirements: RequirementsArtifact = RequirementsArtifact()

        # Phase 2: Domain Model
        self.domain_model: DomainModelArtifact = DomainModelArtifact()

        # Phase 3: Database
        self.database: DatabaseArtifact = DatabaseArtifact()

        # Phase 4: Interface
        self.interface: InterfaceArtifact = InterfaceArtifact()

        # Phase 5: Sequence
        self.sequence: SequenceArtifact = SequenceArtifact()

        # Phase 6: Prototype
        self.prototype: PrototypeArtifact = PrototypeArtifact()

        # Phase 7: Code
        self.code: CodeArtifact = CodeArtifact()

        # Phase 8: Test
        self.test: TestArtifact = TestArtifact()

        # Trace log
        self.trace_log: List[TraceEvent] = []

        # Track which phases have been completed
        self.phase_status: Dict[str, str] = {
            p.value: "pending" for p in Phase
        }

    def add_trace(self, event: TraceEvent):
        self.trace_log.append(event)
        self.updated_at = datetime.utcnow().isoformat()

    def get_phase_artifact(self, phase: str) -> Any:
        mapping = {
            "requirements": self.requirements,
            "domain_model": self.domain_model,
            "database": self.database,
            "interface": self.interface,
            "sequence": self.sequence,
            "prototype": self.prototype,
            "code": self.code,
            "test": self.test,
        }
        return mapping.get(phase)

    def set_phase_artifact(self, phase: str, artifact: Any):
        mapping = {
            "requirements": "requirements",
            "domain_model": "domain_model",
            "database": "database",
            "interface": "interface",
            "sequence": "sequence",
            "prototype": "prototype",
            "code": "code",
            "test": "test",
        }
        attr = mapping.get(phase)
        if attr:
            setattr(self, attr, artifact)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "requirements": self.requirements.to_dict(),
            "domain_model": self.domain_model.to_dict(),
            "database": self.database.to_dict(),
            "interface": self.interface.to_dict(),
            "sequence": self.sequence.to_dict(),
            "prototype": self.prototype.to_dict(),
            "code": self.code.to_dict(),
            "test": self.test.to_dict(),
            "phase_status": self.phase_status,
            "trace_count": len(self.trace_log),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnifiedDomainModel":
        model = cls(data.get("project_name", ""))
        model.project_id = data.get("project_id", model.project_id)
        model.created_at = data.get("created_at", model.created_at)
        model.updated_at = data.get("updated_at", model.updated_at)
        model.phase_status = data.get("phase_status", model.phase_status)
        if "requirements" in data:
            model.requirements = RequirementsArtifact.from_dict(data["requirements"])
        if "domain_model" in data:
            model.domain_model = DomainModelArtifact.from_dict(data["domain_model"])
        if "database" in data:
            model.database = DatabaseArtifact.from_dict(data["database"])
        if "interface" in data:
            model.interface = InterfaceArtifact.from_dict(data["interface"])
        if "sequence" in data:
            model.sequence = SequenceArtifact.from_dict(data["sequence"])
        if "prototype" in data:
            model.prototype = PrototypeArtifact.from_dict(data["prototype"])
        if "code" in data:
            model.code = CodeArtifact.from_dict(data["code"])
        if "test" in data:
            model.test = TestArtifact.from_dict(data["test"])
        return model


# ──────────────────────────────────────────────
# Phase 1: Requirements Analysis
# ──────────────────────────────────────────────

class RequirementItem:
    def __init__(
        self,
        req_id: str,
        title: str,
        description: str,
        priority: str = "medium",
        category: str = "functional",
        status: str = "draft",
        gap_notes: Optional[str] = None,
    ):
        self.req_id = req_id
        self.title = title
        self.description = description
        self.priority = priority
        self.category = category
        self.status = status
        self.gap_notes = gap_notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "req_id": self.req_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "status": self.status,
            "gap_notes": self.gap_notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RequirementItem":
        return cls(**{k: v for k, v in data.items() if k in {
            "req_id", "title", "description", "priority", "category", "status", "gap_notes"
        }})


class RequirementsArtifact:
    def __init__(self):
        self.raw_input: str = ""
        self.vocab_gaps: List[str] = []
        self.items: List[RequirementItem] = []
        self.version: str = "1.0"
        self.status: ArtifactStatus = ArtifactStatus.DRAFT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_input": self.raw_input,
            "vocab_gaps": self.vocab_gaps,
            "items": [i.to_dict() for i in self.items],
            "version": self.version,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RequirementsArtifact":
        art = cls()
        art.raw_input = data.get("raw_input", "")
        art.vocab_gaps = data.get("vocab_gaps", [])
        art.items = [RequirementItem.from_dict(i) for i in data.get("items", [])]
        art.version = data.get("version", "1.0")
        art.status = ArtifactStatus(data.get("status", "draft"))
        return art


# ──────────────────────────────────────────────
# Phase 2: Domain Model (Use Cases, Actors)
# ──────────────────────────────────────────────

class Actor:
    def __init__(self, actor_id: str, name: str, description: str = ""):
        self.actor_id = actor_id
        self.name = name
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {"actor_id": self.actor_id, "name": self.name, "description": self.description}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Actor":
        return cls(data["actor_id"], data["name"], data.get("description", ""))


class UseCase:
    def __init__(
        self,
        uc_id: str,
        name: str,
        description: str,
        actors: List[str],
        preconditions: List[str],
        postconditions: List[str],
        main_flow: List[str],
        alt_flows: Optional[List[List[str]]] = None,
        req_links: Optional[List[str]] = None,
    ):
        self.uc_id = uc_id
        self.name = name
        self.description = description
        self.actors = actors
        self.preconditions = preconditions
        self.postconditions = postconditions
        self.main_flow = main_flow
        self.alt_flows = alt_flows or []
        self.req_links = req_links or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uc_id": self.uc_id,
            "name": self.name,
            "description": self.description,
            "actors": self.actors,
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "main_flow": self.main_flow,
            "alt_flows": self.alt_flows,
            "req_links": self.req_links,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UseCase":
        return cls(**{k: v for k, v in data.items() if k in {
            "uc_id", "name", "description", "actors", "preconditions",
            "postconditions", "main_flow", "alt_flows", "req_links"
        }})


class DomainModelArtifact:
    def __init__(self):
        self.actors: List[Actor] = []
        self.use_cases: List[UseCase] = []
        self.plantuml_code: str = ""
        self.version: str = "1.0"
        self.status: ArtifactStatus = ArtifactStatus.DRAFT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actors": [a.to_dict() for a in self.actors],
            "use_cases": [u.to_dict() for u in self.use_cases],
            "plantuml_code": self.plantuml_code,
            "version": self.version,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainModelArtifact":
        art = cls()
        art.actors = [Actor.from_dict(a) for a in data.get("actors", [])]
        art.use_cases = [UseCase.from_dict(u) for u in data.get("use_cases", [])]
        art.plantuml_code = data.get("plantuml_code", "")
        art.version = data.get("version", "1.0")
        art.status = ArtifactStatus(data.get("status", "draft"))
        return art


# ──────────────────────────────────────────────
# Phase 3: Database Design
# ──────────────────────────────────────────────

class ColumnDef:
    def __init__(
        self,
        name: str,
        dtype: str,
        nullable: bool = True,
        pk: bool = False,
        fk: Optional[str] = None,
        default: Optional[str] = None,
        comment: str = "",
    ):
        self.name = name
        self.dtype = dtype
        self.nullable = nullable
        self.pk = pk
        self.fk = fk
        self.default = default
        self.comment = comment

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "dtype": self.dtype, "nullable": self.nullable,
            "pk": self.pk, "fk": self.fk, "default": self.default, "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColumnDef":
        return cls(**{k: v for k, v in data.items() if k in {
            "name", "dtype", "nullable", "pk", "fk", "default", "comment"
        }})


class TableDef:
    def __init__(self, name: str, columns: Optional[List[ColumnDef]] = None, comment: str = ""):
        self.name = name
        self.columns = columns or []
        self.comment = comment

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "columns": [c.to_dict() for c in self.columns],
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TableDef":
        cols = [ColumnDef.from_dict(c) for c in data.get("columns", [])]
        return cls(data["name"], cols, data.get("comment", ""))


class DatabaseArtifact:
    def __init__(self):
        self.tables: List[TableDef] = []
        self.ddl_mysql: str = ""
        self.ddl_postgres: str = ""
        self.ddl_sqlite: str = ""
        self.plantuml_er: str = ""
        self.version: str = "1.0"
        self.status: ArtifactStatus = ArtifactStatus.DRAFT
        self.uc_links: Dict[str, List[str]] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tables": [t.to_dict() for t in self.tables],
            "ddl_mysql": self.ddl_mysql,
            "ddl_postgres": self.ddl_postgres,
            "ddl_sqlite": self.ddl_sqlite,
            "plantuml_er": self.plantuml_er,
            "version": self.version,
            "status": self.status.value,
            "uc_links": self.uc_links,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatabaseArtifact":
        art = cls()
        art.tables = [TableDef.from_dict(t) for t in data.get("tables", [])]
        art.ddl_mysql = data.get("ddl_mysql", "")
        art.ddl_postgres = data.get("ddl_postgres", "")
        art.ddl_sqlite = data.get("ddl_sqlite", "")
        art.plantuml_er = data.get("plantuml_er", "")
        art.version = data.get("version", "1.0")
        art.status = ArtifactStatus(data.get("status", "draft"))
        art.uc_links = data.get("uc_links", {})
        return art


# ──────────────────────────────────────────────
# Phase 4: Interface Design
# ──────────────────────────────────────────────

class EndpointDef:
    def __init__(
        self,
        ep_id: str,
        method: str,
        path: str,
        summary: str,
        request_schema: Optional[Dict[str, Any]] = None,
        response_schema: Optional[Dict[str, Any]] = None,
        req_links: Optional[List[str]] = None,
        uc_links: Optional[List[str]] = None,
    ):
        self.ep_id = ep_id
        self.method = method.upper()
        self.path = path
        self.summary = summary
        self.request_schema = request_schema or {}
        self.response_schema = response_schema or {}
        self.req_links = req_links or []
        self.uc_links = uc_links or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ep_id": self.ep_id, "method": self.method, "path": self.path,
            "summary": self.summary, "request_schema": self.request_schema,
            "response_schema": self.response_schema,
            "req_links": self.req_links, "uc_links": self.uc_links,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EndpointDef":
        return cls(**{k: v for k, v in data.items() if k in {
            "ep_id", "method", "path", "summary", "request_schema",
            "response_schema", "req_links", "uc_links"
        }})


class InterfaceArtifact:
    def __init__(self):
        self.endpoints: List[EndpointDef] = []
        self.openapi_spec: str = ""
        self.uc_to_ep_map: Dict[str, List[str]] = {}
        self.req_to_ep_map: Dict[str, List[str]] = {}
        self.version: str = "1.0"
        self.status: ArtifactStatus = ArtifactStatus.DRAFT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "endpoints": [e.to_dict() for e in self.endpoints],
            "openapi_spec": self.openapi_spec,
            "uc_to_ep_map": self.uc_to_ep_map,
            "req_to_ep_map": self.req_to_ep_map,
            "version": self.version,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterfaceArtifact":
        art = cls()
        art.endpoints = [EndpointDef.from_dict(e) for e in data.get("endpoints", [])]
        art.openapi_spec = data.get("openapi_spec", "")
        art.uc_to_ep_map = data.get("uc_to_ep_map", {})
        art.req_to_ep_map = data.get("req_to_ep_map", {})
        art.version = data.get("version", "1.0")
        art.status = ArtifactStatus(data.get("status", "draft"))
        return art


# ──────────────────────────────────────────────
# Phase 5: Sequence Diagram
# ──────────────────────────────────────────────

class SequenceMessage:
    def __init__(self, source: str, target: str, message: str, msg_type: str = "request"):
        self.source = source
        self.target = target
        self.message = message
        self.msg_type = msg_type

    def to_dict(self) -> Dict[str, Any]:
        return {"source": self.source, "target": self.target, "message": self.message, "msg_type": self.msg_type}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SequenceMessage":
        return cls(data["source"], data["target"], data["message"], data.get("msg_type", "request"))


class SequenceDef:
    def __init__(self, seq_id: str, name: str, participants: List[str], messages: List[SequenceMessage], uc_link: str = ""):
        self.seq_id = seq_id
        self.name = name
        self.participants = participants
        self.messages = messages
        self.uc_link = uc_link

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seq_id": self.seq_id, "name": self.name,
            "participants": self.participants,
            "messages": [m.to_dict() for m in self.messages],
            "uc_link": self.uc_link,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SequenceDef":
        msgs = [SequenceMessage.from_dict(m) for m in data.get("messages", [])]
        return cls(data["seq_id"], data["name"], data.get("participants", []), msgs, data.get("uc_link", ""))


class SequenceArtifact:
    def __init__(self):
        self.sequences: List[SequenceDef] = []
        self.plantuml_code: str = ""
        self.version: str = "1.0"
        self.status: ArtifactStatus = ArtifactStatus.DRAFT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sequences": [s.to_dict() for s in self.sequences],
            "plantuml_code": self.plantuml_code,
            "version": self.version,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SequenceArtifact":
        art = cls()
        art.sequences = [SequenceDef.from_dict(s) for s in data.get("sequences", [])]
        art.plantuml_code = data.get("plantuml_code", "")
        art.version = data.get("version", "1.0")
        art.status = ArtifactStatus(data.get("status", "draft"))
        return art


# ──────────────────────────────────────────────
# Phase 6: Page Prototype
# ──────────────────────────────────────────────

class PageComponent:
    def __init__(self, comp_id: str, comp_type: str, props: Optional[Dict[str, Any]] = None):
        self.comp_id = comp_id
        self.comp_type = comp_type
        self.props = props or {}

    def to_dict(self) -> Dict[str, Any]:
        return {"comp_id": self.comp_id, "comp_type": self.comp_type, "props": self.props}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PageComponent":
        return cls(data["comp_id"], data["comp_type"], data.get("props", {}))


class PageDef:
    def __init__(self, page_id: str, name: str, route: str, components: List[PageComponent], ep_links: Optional[List[str]] = None):
        self.page_id = page_id
        self.name = name
        self.route = route
        self.components = components
        self.ep_links = ep_links or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_id": self.page_id, "name": self.name, "route": self.route,
            "components": [c.to_dict() for c in self.components],
            "ep_links": self.ep_links,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PageDef":
        comps = [PageComponent.from_dict(c) for c in data.get("components", [])]
        return cls(data["page_id"], data["name"], data["route"], comps, data.get("ep_links", []))


class PrototypeArtifact:
    def __init__(self):
        self.pages: List[PageDef] = []
        self.html_prototypes: str = ""
        self.version: str = "1.0"
        self.status: ArtifactStatus = ArtifactStatus.DRAFT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pages": [p.to_dict() for p in self.pages],
            "html_prototypes": self.html_prototypes,
            "version": self.version,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrototypeArtifact":
        art = cls()
        art.pages = [PageDef.from_dict(p) for p in data.get("pages", [])]
        art.html_prototypes = data.get("html_prototypes", "")
        art.version = data.get("version", "1.0")
        art.status = ArtifactStatus(data.get("status", "draft"))
        return art


# ──────────────────────────────────────────────
# Phase 7: Code Generation
# ──────────────────────────────────────────────

class CodeFile:
    def __init__(self, path: str, content: str, language: str = "python"):
        self.path = path
        self.content = content
        self.language = language

    def to_dict(self) -> Dict[str, Any]:
        return {"path": self.path, "content": self.content, "language": self.language}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeFile":
        return cls(data["path"], data["content"], data.get("language", "python"))


class CodeArtifact:
    def __init__(self):
        self.backend_files: List[CodeFile] = []
        self.frontend_files: List[CodeFile] = []
        self.ep_to_code_map: Dict[str, str] = {}
        self.version: str = "1.0"
        self.status: ArtifactStatus = ArtifactStatus.DRAFT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backend_files": [f.to_dict() for f in self.backend_files],
            "frontend_files": [f.to_dict() for f in self.frontend_files],
            "ep_to_code_map": self.ep_to_code_map,
            "version": self.version,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeArtifact":
        art = cls()
        art.backend_files = [CodeFile.from_dict(f) for f in data.get("backend_files", [])]
        art.frontend_files = [CodeFile.from_dict(f) for f in data.get("frontend_files", [])]
        art.ep_to_code_map = data.get("ep_to_code_map", {})
        art.version = data.get("version", "1.0")
        art.status = ArtifactStatus(data.get("status", "draft"))
        return art


# ──────────────────────────────────────────────
# Phase 8: Testing
# ──────────────────────────────────────────────

class TestCase:
    def __init__(
        self,
        tc_id: str,
        title: str,
        description: str,
        steps: List[str],
        expected: str,
        test_type: str = "unit",
        req_links: Optional[List[str]] = None,
        uc_links: Optional[List[str]] = None,
        ep_links: Optional[List[str]] = None,
    ):
        self.tc_id = tc_id
        self.title = title
        self.description = description
        self.steps = steps
        self.expected = expected
        self.test_type = test_type
        self.req_links = req_links or []
        self.uc_links = uc_links or []
        self.ep_links = ep_links or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tc_id": self.tc_id, "title": self.title, "description": self.description,
            "steps": self.steps, "expected": self.expected, "test_type": self.test_type,
            "req_links": self.req_links, "uc_links": self.uc_links, "ep_links": self.ep_links,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestCase":
        return cls(**{k: v for k, v in data.items() if k in {
            "tc_id", "title", "description", "steps", "expected",
            "test_type", "req_links", "uc_links", "ep_links"
        }})


class TestArtifact:
    def __init__(self):
        self.test_cases: List[TestCase] = []
        self.test_code: str = ""
        self.coverage_map: Dict[str, List[str]] = {}
        self.version: str = "1.0"
        self.status: ArtifactStatus = ArtifactStatus.DRAFT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_cases": [t.to_dict() for t in self.test_cases],
            "test_code": self.test_code,
            "coverage_map": self.coverage_map,
            "version": self.version,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestArtifact":
        art = cls()
        art.test_cases = [TestCase.from_dict(t) for t in data.get("test_cases", [])]
        art.test_code = data.get("test_code", "")
        art.coverage_map = data.get("coverage_map", {})
        art.version = data.get("version", "1.0")
        art.status = ArtifactStatus(data.get("status", "draft"))
        return art
