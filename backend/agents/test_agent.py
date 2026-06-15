from __future__ import annotations
from typing import Dict, Any, List
from shared.domain_model import (
    UnifiedDomainModel, TestArtifact, TestCase,
)


class TestAgent:
    """Phase 8: Generate test cases from requirements, use cases, and endpoints."""

    def execute(self, model: UnifiedDomainModel, params: Dict[str, Any]) -> Dict[str, Any]:
        reqs = model.requirements
        domain = model.domain_model
        interface = model.interface

        test_cases = self._generate_test_cases(reqs, domain, interface)

        artifact = TestArtifact()
        artifact.test_cases = test_cases

        coverage_map = {}
        for tc in test_cases:
            for req_id in tc.req_links:
                if req_id not in coverage_map:
                    coverage_map[req_id] = []
                coverage_map[req_id].append(tc.tc_id)
        artifact.coverage_map = coverage_map

        test_code = self._generate_test_code(test_cases, interface)
        artifact.test_code = test_code

        model.test = artifact
        return {
            "test_cases": [t.to_dict() for t in test_cases],
            "test_code": test_code,
            "coverage_map": coverage_map,
            "coverage_stats": {
                "total_test_cases": len(test_cases),
                "requirements_covered": len(coverage_map),
                "total_requirements": len(reqs.items) if reqs else 0,
            },
        }

    def _generate_test_cases(self, reqs, domain, interface) -> List[TestCase]:
        test_cases = []

        if reqs and reqs.items:
            for req in reqs.items:
                tc_id = f"TC-REQ-{req.req_id.replace('REQ-', '')}"
                test_cases.append(TestCase(
                    tc_id=tc_id,
                    title=f"[需求] {req.title} - 正向测试",
                    description=f"验证需求: {req.title}",
                    steps=[
                        f"准备测试环境",
                        f"执行{req.title}操作",
                        f"验证操作结果符合预期",
                    ],
                    expected=f"{req.title}成功执行，系统返回正确结果",
                    test_type="functional",
                    req_links=[req.req_id],
                ))

        if domain and domain.use_cases:
            for uc in domain.use_cases:
                tc_id = f"TC-UC-{uc.uc_id.replace('UC-', '')}"
                steps = uc.main_flow[:]
                expected = f"用例'{uc.name}'主流程执行成功" if uc.postconditions else "操作完成"
                test_cases.append(TestCase(
                    tc_id=tc_id,
                    title=f"[用例] {uc.name} - 主流程",
                    description=f"验证用例: {uc.name}",
                    steps=steps,
                    expected=expected,
                    test_type="integration",
                    uc_links=[uc.uc_id],
                    req_links=uc.req_links,
                ))
                if uc.alt_flows:
                    for i, alt in enumerate(uc.alt_flows):
                        test_cases.append(TestCase(
                            tc_id=f"{tc_id}-ALT-{i+1}",
                            title=f"[用例] {uc.name} - 异常流{i+1}",
                            description=f"验证用例异常处理: {uc.name}",
                            steps=alt,
                            expected="系统正确处理异常并返回错误信息",
                            test_type="negative",
                            uc_links=[uc.uc_id],
                        ))

        if interface and interface.endpoints:
            for ep in interface.endpoints:
                test_cases.append(TestCase(
                    tc_id=f"TC-API-{ep.ep_id.replace('EP-', '')}",
                    title=f"[API] {ep.method} {ep.path} - 接口测试",
                    description=f"验证接口: {ep.summary}",
                    steps=[
                        f"构造{ep.method} {ep.path}请求",
                        "设置请求头（包含认证信息）",
                        "发送请求并获取响应",
                        "验证HTTP状态码",
                        "验证响应体格式",
                    ],
                    expected="接口返回正确的状态码和数据结构",
                    test_type="api",
                    ep_links=[ep.ep_id],
                    uc_links=ep.uc_links,
                    req_links=ep.req_links,
                ))

        # Core principle validation tests
        test_cases.extend(self._generate_principle_tests())

        return test_cases

    def _generate_principle_tests(self) -> List[TestCase]:
        return [
            TestCase(
                tc_id="TC-PRINCIPLE-001",
                title="核心原则验证: 数据完整性",
                description="验证系统数据操作的原子性、一致性、隔离性和持久性",
                steps=[
                    "并发执行数据写入操作",
                    "模拟事务中断场景",
                    "验证数据库数据一致性",
                ],
                expected="系统在任何异常场景下都能保证数据完整性",
                test_type="security",
            ),
            TestCase(
                tc_id="TC-PRINCIPLE-002",
                title="核心原则验证: 权限控制",
                description="验证系统的权限控制机制是否正确",
                steps=[
                    "使用未授权用户访问管理接口",
                    "验证权限校验是否生效",
                    "测试角色权限矩阵",
                ],
                expected="未授权访问被正确拦截，权限控制有效",
                test_type="security",
            ),
            TestCase(
                tc_id="TC-PRINCIPLE-003",
                title="核心原则验证: 输入校验",
                description="验证系统对所有输入的校验机制",
                steps=[
                    "提交空值",
                    "提交超长字符串",
                    "提交特殊字符/XSS",
                    "提交SQL注入字符串",
                ],
                expected="系统正确校验并拒绝所有非法输入",
                test_type="security",
            ),
            TestCase(
                tc_id="TC-PRINCIPLE-004",
                title="核心原则验证: 错误处理",
                description="验证系统的全局异常处理机制",
                steps=[
                    "请求不存在的资源",
                    "触发业务逻辑异常",
                    "触发系统级异常",
                ],
                expected="系统返回友好的错误信息，不会泄露敏感信息",
                test_type="negative",
            ),
            TestCase(
                tc_id="TC-PRINCIPLE-005",
                title="核心原则验证: 性能基准",
                description="验证接口响应时间在合理范围内",
                steps=[
                    "准备性能测试环境",
                    "使用JMeter/k6发送并发请求",
                    "监控接口响应时间",
                ],
                expected="95%的请求响应时间在500ms以内",
                test_type="performance",
            ),
        ]

    def _generate_test_code(self, test_cases: List[TestCase], interface) -> str:
        lines = [
            "'''",
            "Auto-generated test cases by Waterfall Agent",
            f"Total: {len(test_cases)} test cases",
            "'''",
            "import pytest",
            "from httpx import AsyncClient",
            "",
        ]

        if interface and interface.endpoints:
            lines.append("")
            lines.append("@pytest.mark.asyncio")
            lines.append("async def test_api_health():")
            lines.append("    async with AsyncClient(base_url='http://test') as client:")
            lines.append("        resp = await client.get('/health')")
            lines.append("        assert resp.status_code == 200")
            lines.append("")

            for ep in interface.endpoints[:5]:
                tc_id = f"TC-API-{ep.ep_id.replace('EP-', '')}"
                safe_name = f"test_{ep.ep_id.lower().replace('-', '_')}"
                lines.append("")
                lines.append("@pytest.mark.asyncio")
                lines.append(f"async def test_{safe_name}():")
                lines.append(f'    """{ep.summary}"""')
                path = ep.path.replace("{", "{").replace("}", "}")
                if ep.method == "GET":
                    lines.append("    async with AsyncClient(base_url='http://test') as client:")
                    lines.append(f"        resp = await client.get('{path}')")
                    if path in ("/api/v1/auth/login", "/api/v1/auth/register"):
                        lines.append("        assert resp.status_code in (200, 422)")
                    else:
                        lines.append("        assert resp.status_code in (200, 401, 403, 404)")
                elif ep.method == "POST":
                    lines.append("    async with AsyncClient(base_url='http://test') as client:")
                    lines.append(f"        resp = await client.post('{path}', json={{}})")
                    lines.append("        assert resp.status_code in (200, 201, 422)")
                elif ep.method == "PUT":
                    lines.append("    async with AsyncClient(base_url='http://test') as client:")
                    lines.append(f"        resp = await client.put('{path}', json={{}})")
                    lines.append("        assert resp.status_code in (200, 422)")
                elif ep.method == "DELETE":
                    lines.append("    async with AsyncClient(base_url='http://test') as client:")
                    lines.append(f"        resp = await client.delete('{path}')")
                    lines.append("        assert resp.status_code in (200, 204, 404)")
                lines.append("")

        lines.append("")
        lines.append("# Principle validation tests")
        for tc in [t for t in test_cases if t.tc_id.startswith("TC-PRINCIPLE")]:
            lines.append("")
            lines.append("@pytest.mark.asyncio")
            lines.append(f"async def test_{tc.tc_id.lower().replace('-', '_')}():")
            lines.append(f'    """{tc.title}"""')
            lines.append(f"    assert True  # TODO: implement {tc.tc_id}")
            lines.append("")

        return "\n".join(lines)
