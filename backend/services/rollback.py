from __future__ import annotations
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os

from shared.domain_model import UnifiedDomainModel


class RollbackService:
    """Manages snapshot-based rollback to any previous state."""

    def __init__(self, snapshot_dir: str = None):
        self.snapshot_dir = snapshot_dir or os.path.join(
            os.path.dirname(__file__), "..", "data", "trace"
        )
        os.makedirs(self.snapshot_dir, exist_ok=True)

    def list_snapshots(self, project_id: str = "default") -> List[Dict[str, Any]]:
        prefix = f"{project_id}_snapshot_"
        snapshots = []
        if os.path.exists(self.snapshot_dir):
            for fname in os.listdir(self.snapshot_dir):
                if fname.startswith(prefix) and fname.endswith(".json"):
                    ts = fname.replace(prefix, "").replace(".json", "")
                    snapshots.append({
                        "id": ts,
                        "timestamp": ts,
                        "filename": fname,
                        "path": os.path.join(self.snapshot_dir, fname),
                    })
        return sorted(snapshots, key=lambda x: x["timestamp"], reverse=True)

    def create_snapshot(self, project_id: str, model: UnifiedDomainModel):
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        fname = f"{project_id}_snapshot_{ts}.json"
        fpath = os.path.join(self.snapshot_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(model.to_dict(), f, ensure_ascii=False, indent=2)
        return {"snapshot_id": ts, "filename": fname, "timestamp": ts}

    def restore_snapshot(self, project_id: str, snapshot_id: str) -> Optional[UnifiedDomainModel]:
        fname = f"{project_id}_snapshot_{snapshot_id}.json"
        fpath = os.path.join(self.snapshot_dir, fname)
        if not os.path.exists(fpath):
            fpath = os.path.join(self.snapshot_dir, f"{project_id}_snapshot.json")
            if not os.path.exists(fpath):
                return None
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return UnifiedDomainModel.from_dict(data)
