from __future__ import annotations
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

from shared.domain_model import TraceEvent, Phase


class TraceabilityService:
    """Tracks every action across all phases for full audit trail and rollback."""

    def __init__(self, trace_dir: str = None):
        self.trace_dir = trace_dir or os.path.join(os.path.dirname(__file__), "..", "data", "trace")
        os.makedirs(self.trace_dir, exist_ok=True)

    def record(
        self,
        phase: Phase,
        action: str,
        artifact_id: str,
        user_id: str = "system",
        previous_version: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        project_id: str = "default",
    ) -> TraceEvent:
        event = TraceEvent(phase, action, artifact_id, user_id, previous_version, payload)
        log_entry = event.to_dict()
        log_entry["project_id"] = project_id
        trace_file = os.path.join(self.trace_dir, f"{project_id}_trace.jsonl")
        with open(trace_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        return event

    def get_history(
        self, project_id: str = "default", phase: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        trace_file = os.path.join(self.trace_dir, f"{project_id}_trace.jsonl")
        if not os.path.exists(trace_file):
            return []
        events = []
        with open(trace_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    ev = json.loads(line)
                    if phase is None or ev.get("phase") == phase:
                        events.append(ev)
        return events[-limit:]

    def get_latest_snapshot(
        self, project_id: str = "default"
    ) -> Optional[Dict[str, Any]]:
        snapshot_file = os.path.join(self.trace_dir, f"{project_id}_snapshot.json")
        if os.path.exists(snapshot_file):
            with open(snapshot_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def save_snapshot(self, project_id: str, model_dict: Dict[str, Any]):
        snapshot_file = os.path.join(self.trace_dir, f"{project_id}_snapshot.json")
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(model_dict, f, ensure_ascii=False, indent=2)

    def get_versions(self, project_id: str = "default") -> List[Dict[str, Any]]:
        trace_file = os.path.join(self.trace_dir, f"{project_id}_trace.jsonl")
        if not os.path.exists(trace_file):
            return []
        versions = []
        with open(trace_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    ev = json.loads(line)
                    if ev.get("action") in ("approve", "reject", "update_artifact", "rollback"):
                        versions.append({
                            "id": ev["id"],
                            "timestamp": ev["timestamp"],
                            "phase": ev["phase"],
                            "action": ev["action"],
                            "artifact_id": ev["artifact_id"],
                        })
        return versions
