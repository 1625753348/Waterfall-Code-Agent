from __future__ import annotations
from typing import Dict, Any, List
from shared.domain_model import (
    UnifiedDomainModel, DomainModelArtifact, Actor, UseCase, RequirementItem,
)


class DomainModelAgent:
    """Phase 2: Generate use case diagram elements from requirements."""

    def execute(self, model: UnifiedDomainModel, params: Dict[str, Any]) -> Dict[str, Any]:
        reqs = model.requirements
        if not reqs or not reqs.items:
            return {"error": "No requirements found. Complete Phase 1 first."}

        actors = self._generate_actors(reqs.items)
        use_cases = self._generate_use_cases(reqs.items, actors)

        artifact = DomainModelArtifact()
        artifact.actors = actors
        artifact.use_cases = use_cases
        artifact.plantuml_code = self._generate_plantuml(actors, use_cases)

        model.domain_model = artifact
        return {
            "actors": [a.to_dict() for a in actors],
            "use_cases": [u.to_dict() for u in use_cases],
            "plantuml_code": artifact.plantuml_code,
        }

    def _generate_actors(self, reqs: list) -> List[Actor]:
        actors = []
        keyword_map = {
            "admin": Actor("ACT-001", "管理员", "系统管理员，负责系统配置与用户管理"),
            "user": Actor("ACT-002", "普通用户", "系统的日常使用者"),
            "guest": Actor("ACT-003", "游客", "未登录的浏览用户"),
        }
        combined = "\n".join(f"{r.title} {r.description}" for r in reqs)
        found = set()
        for keyword, actor in keyword_map.items():
            if keyword.lower() in combined.lower():
                if keyword not in found:
                    actors.append(actor)
                    found.add(keyword)
        if not actors:
            actors.append(Actor("ACT-001", "用户", "系统用户"))
        return actors

    def _generate_use_cases(self, reqs: list, actors: list) -> List[UseCase]:
        use_cases = []
        for i, req in enumerate(reqs):
            uc_id = f"UC-{i+1:03d}"
            actor_ids = [a.actor_id for a in actors[:1]]
            flow = self._build_flow(req)
            use_cases.append(UseCase(
                uc_id=uc_id,
                name=req.title,
                description=req.description,
                actors=actor_ids,
                preconditions=["用户已登录系统" if "登录" in req.title else "用户已进入系统"],
                postconditions=["操作完成，数据已保存"],
                main_flow=flow,
                alt_flows=[["异常处理：系统返回错误信息"]],
                req_links=[req.req_id],
            ))
        return use_cases

    def _build_flow(self, req: RequirementItem) -> List[str]:
        return [
            f"1. 用户进入{req.title}模块",
            f"2. 系统展示{req.title}界面",
            f"3. 用户执行{req.title}操作",
            "4. 系统校验输入数据",
            "5. 系统处理请求并返回结果",
            "6. 系统记录操作日志",
        ]

    def _generate_plantuml(self, actors: list, use_cases: list) -> str:
        lines = ["@startuml", "left to right direction", "skinparam packageStyle rectangle", ""]
        lines.append("actor 用户 as User")
        for actor in actors:
            name = actor.name.replace(" ", "_")
            lines.append(f"actor {name} as {actor.actor_id.replace('-', '')}")
        lines.append("")
        lines.append("rectangle 系统 {")
        for uc in use_cases:
            uc_name = uc.name.replace('"', "'")
            lines.append(f"  usecase \"{uc_name}\" as {uc.uc_id.replace('-', '')}")
        lines.append("}")
        lines.append("")
        for uc in use_cases:
            for actor_id in uc.actors:
                src = actor_id.replace('-', '')
                dst = uc.uc_id.replace('-', '')
                lines.append(f"{src} --> {dst}")
        lines.append("@enduml")
        return "\n".join(lines)
