from __future__ import annotations
import json
from typing import Dict, Any, List
from shared.domain_model import (
    UnifiedDomainModel, InterfaceArtifact, EndpointDef,
)
from backend.llm_client import chat_json, get_config


class InterfaceAgent:
    """Phase 4: Generate API endpoints from use cases with requirement traceability."""

    def execute(self, model: UnifiedDomainModel, params: Dict[str, Any]) -> Dict[str, Any]:
        domain_model = model.domain_model
        if not domain_model or not domain_model.use_cases:
            return {"error": "No use cases found. Complete Phase 2 first."}

        cfg = get_config()
        if cfg.enabled:
            try:
                uc_str = json.dumps([u.to_dict() for u in domain_model.use_cases], ensure_ascii=False)
                system_prompt = "你是一个API设计师。根据用例生成RESTful API端点、OpenAPI规范和关联映射。直接输出JSON。"
                user_prompt = f"用例：{uc_str}\n\n输出JSON格式：{{\"endpoints\":[{{\"ep_id\":\"EP-001\",\"method\":\"POST\",\"path\":\"/api/v1/...\",\"summary\":\"...\",\"request_schema\":{{\"type\":\"object\",\"properties\":{{}},\"required\":[]}},\"response_schema\":{{\"type\":\"object\",\"properties\":{{}}}},\"req_links\":[\"REQ-001\"],\"uc_links\":[\"UC-001\"]}}],\"openapi_spec\":\"...\",\"uc_to_ep_map\":{{\"UC-001\":[\"EP-001\"]}},\"req_to_ep_map\":{{\"REQ-001\":[\"EP-001\"]}}}}"
                result = chat_json(system_prompt, user_prompt)
                endpoints = [EndpointDef(**e) for e in result.get("endpoints", [])]
            except Exception:
                endpoints = self._generate_endpoints(domain_model)
        else:
            endpoints = self._generate_endpoints(domain_model)
        artifact = InterfaceArtifact()
        artifact.endpoints = endpoints
        artifact.uc_to_ep_map = self._build_uc_map(endpoints)
        artifact.req_to_ep_map = self._build_req_map(endpoints)
        artifact.openapi_spec = self._generate_openapi(endpoints)

        model.interface = artifact
        return {
            "endpoints": [e.to_dict() for e in endpoints],
            "uc_to_ep_map": artifact.uc_to_ep_map,
            "req_to_ep_map": artifact.req_to_ep_map,
            "openapi_spec": artifact.openapi_spec,
        }

    def _generate_endpoints(self, domain_model) -> List[EndpointDef]:
        endpoints = [
            EndpointDef("EP-001", "POST", "/api/v1/auth/login", "用户登录", {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "用户名"},
                    "password": {"type": "string", "description": "密码"},
                },
                "required": ["username", "password"],
            }, {
                "type": "object",
                "properties": {
                    "token": {"type": "string"},
                    "user": {"type": "object"},
                },
            }, req_links=["REQ-001"], uc_links=["UC-001"]),
            EndpointDef("EP-002", "POST", "/api/v1/auth/register", "用户注册", {
                "type": "object",
                "properties": {
                    "username": {"type": "string"}, "password": {"type": "string"}, "email": {"type": "string"},
                },
                "required": ["username", "password", "email"],
            }, {
                "type": "object",
                "properties": {"id": {"type": "integer"}, "username": {"type": "string"}},
            }, req_links=["REQ-001"], uc_links=["UC-001"]),
            EndpointDef("EP-003", "GET", "/api/v1/users/me", "获取当前用户信息", {}, {
                "type": "object",
                "properties": {"id": {"type": "integer"}, "username": {"type": "string"}, "email": {"type": "string"}, "roles": {"type": "array"}},
            }, req_links=["REQ-001"], uc_links=["UC-001"]),
            EndpointDef("EP-004", "PUT", "/api/v1/users/me", "更新当前用户信息", {
                "type": "object",
                "properties": {"email": {"type": "string"}, "phone": {"type": "string"}},
            }, {}, req_links=["REQ-002"], uc_links=["UC-002"]),
            EndpointDef("EP-005", "GET", "/api/v1/users", "用户列表（管理员）", {}, {
                "type": "array", "items": {"type": "object"},
            }, req_links=["REQ-003"], uc_links=["UC-003"]),
            EndpointDef("EP-006", "GET", "/api/v1/roles", "角色列表", {}, {"type": "array"},
                req_links=["REQ-004"], uc_links=["UC-004"]),
            EndpointDef("EP-007", "POST", "/api/v1/roles", "创建角色", {}, {},
                req_links=["REQ-004"], uc_links=["UC-004"]),
            EndpointDef("EP-008", "GET", "/api/v1/operation-logs", "操作日志列表", {}, {"type": "array"},
                req_links=["REQ-005"], uc_links=["UC-005"]),
        ]

        use_case_names = " ".join(uc.name for uc in domain_model.use_cases)
        if "商品" in use_case_names or "product" in use_case_names.lower():
            endpoints.extend([
                EndpointDef("EP-009", "GET", "/api/v1/products", "商品列表", {}, {"type": "array"},
                    req_links=["REQ-006"], uc_links=["UC-006"]),
                EndpointDef("EP-010", "POST", "/api/v1/products", "创建商品", {}, {},
                    req_links=["REQ-006"], uc_links=["UC-006"]),
                EndpointDef("EP-011", "GET", "/api/v1/products/{id}", "获取商品详情", {}, {},
                    req_links=["REQ-006"], uc_links=["UC-006"]),
                EndpointDef("EP-012", "PUT", "/api/v1/products/{id}", "更新商品", {}, {},
                    req_links=["REQ-006"], uc_links=["UC-006"]),
                EndpointDef("EP-013", "DELETE", "/api/v1/products/{id}", "删除商品", {}, {},
                    req_links=["REQ-006"], uc_links=["UC-006"]),
                EndpointDef("EP-014", "GET", "/api/v1/categories", "分类列表", {}, {"type": "array"},
                    req_links=["REQ-007"], uc_links=["UC-007"]),
                EndpointDef("EP-015", "POST", "/api/v1/orders", "创建订单", {}, {},
                    req_links=["REQ-008"], uc_links=["UC-008"]),
                EndpointDef("EP-016", "GET", "/api/v1/orders", "订单列表", {}, {"type": "array"},
                    req_links=["REQ-008"], uc_links=["UC-008"]),
                EndpointDef("EP-017", "GET", "/api/v1/orders/{id}", "订单详情", {}, {},
                    req_links=["REQ-008"], uc_links=["UC-008"]),
            ])

        for i, uc in enumerate(domain_model.use_cases):
            if i < len(endpoints):
                endpoints[i].uc_links = endpoints[i].uc_links or [uc.uc_id]
                endpoints[i].req_links = endpoints[i].req_links or (uc.req_links or [])

        return endpoints

    def _build_uc_map(self, endpoints: List[EndpointDef]) -> Dict[str, List[str]]:
        mapping = {}
        for ep in endpoints:
            for uc_id in ep.uc_links:
                if uc_id not in mapping:
                    mapping[uc_id] = []
                mapping[uc_id].append(ep.ep_id)
        return mapping

    def _build_req_map(self, endpoints: List[EndpointDef]) -> Dict[str, List[str]]:
        mapping = {}
        for ep in endpoints:
            for req_id in ep.req_links:
                if req_id not in mapping:
                    mapping[req_id] = []
                mapping[req_id].append(ep.ep_id)
        return mapping

    def _generate_openapi(self, endpoints: List[EndpointDef]) -> str:
        lines = ["openapi: 3.0.0", "info:", "  title: Waterfall Agent API", "  version: 1.0.0", "paths:"]
        for ep in endpoints:
            lines.append(f"  {ep.path}:")
            lines.append(f"    {ep.method.lower()}:")
            lines.append(f"      summary: {ep.summary}")
            lines.append(f"      operationId: {ep.ep_id.lower().replace('-', '_')}")
            lines.append("      responses:")
            lines.append("        '200':")
            lines.append("          description: Successful response")
        return "\n".join(lines)
