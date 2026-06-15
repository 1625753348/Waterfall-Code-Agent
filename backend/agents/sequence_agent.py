from __future__ import annotations
from typing import Dict, Any, List
from shared.domain_model import (
    UnifiedDomainModel, SequenceArtifact, SequenceDef, SequenceMessage,
)


class SequenceAgent:
    """Phase 5: Generate sequence diagrams from use cases and endpoints."""

    def execute(self, model: UnifiedDomainModel, params: Dict[str, Any]) -> Dict[str, Any]:
        domain_model = model.domain_model
        if not domain_model or not domain_model.use_cases:
            return {"error": "No use cases found. Complete Phase 2 first."}

        sequences = self._generate_sequences(domain_model)
        artifact = SequenceArtifact()
        artifact.sequences = sequences
        artifact.plantuml_code = self._generate_plantuml(sequences)

        model.sequence = artifact
        return {
            "sequences": [s.to_dict() for s in sequences],
            "plantuml_code": artifact.plantuml_code,
        }

    def _generate_sequences(self, domain_model) -> List[SequenceDef]:
        sequences = []
        for i, uc in enumerate(domain_model.use_cases):
            seq_id = f"SEQ-{i+1:03d}"
            participants = ["用户"]
            for actor_id in uc.actors:
                actor = next((a for a in domain_model.actors if a.actor_id == actor_id), None)
                if actor:
                    participants.append(actor.name)
            participants.append("系统")
            participants.append("数据库")

            messages = [
                SequenceMessage("用户", "系统", f"发起{uc.name}请求"),
                SequenceMessage("系统", "系统", "校验输入参数"),
                SequenceMessage("系统", "数据库", "查询/写入数据"),
                SequenceMessage("数据库", "系统", "返回数据结果"),
                SequenceMessage("系统", "系统", "处理业务逻辑"),
                SequenceMessage("系统", "用户", f"返回{uc.name}结果"),
            ]

            sequences.append(SequenceDef(
                seq_id=seq_id,
                name=uc.name,
                participants=list(set(participants)),
                messages=messages,
                uc_link=uc.uc_id,
            ))
        return sequences

    def _generate_plantuml(self, sequences: List[SequenceDef]) -> str:
        lines = ["@startuml", "skinparam sequenceMessageAlign center", ""]
        for seq in sequences:
            name = seq.name.replace('"', "'")
            lines.append(f"title 时序图: {name}")
            for p in seq.participants:
                lines.append(f'participant "{p}" as {p.replace(" ", "_")}')
            lines.append("")
            for msg in seq.messages:
                src = msg.source.replace(" ", "_")
                tgt = msg.target.replace(" ", "_")
                arrow = "->" if msg.msg_type == "request" else "-->"
                text = msg.message.replace('"', "'")
                lines.append(f"{src}{arrow}{tgt}: {text}")
            lines.append("")
            lines.append("newpage")
            lines.append("")
        lines.append("@enduml")
        return "\n".join(lines)
