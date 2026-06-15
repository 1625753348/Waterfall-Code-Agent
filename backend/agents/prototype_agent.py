from __future__ import annotations
import json
from typing import Dict, Any, List
from shared.domain_model import (
    UnifiedDomainModel, PrototypeArtifact, PageDef, PageComponent,
)
from backend.llm_client import chat_json, get_config


class PrototypeAgent:
    """Phase 6: Generate page prototypes from use cases and endpoints."""

    def execute(self, model: UnifiedDomainModel, params: Dict[str, Any]) -> Dict[str, Any]:
        interface = model.interface
        domain_model = model.domain_model
        if not interface or not interface.endpoints:
            return {"error": "No endpoints found. Complete Phase 4 first."}

        cfg = get_config()
        if cfg.enabled:
            try:
                ep_str = json.dumps([e.to_dict() for e in interface.endpoints], ensure_ascii=False)
                system_prompt = "你是一个UI/UX设计师。根据API端点生成页面原型定义和HTML原型预览。直接输出JSON。"
                user_prompt = f"API端点：{ep_str}\n\n输出JSON格式：{{\"pages\":[{{\"page_id\":\"PAGE-001\",\"name\":\"登录页面\",\"route\":\"/login\",\"ep_links\":[\"EP-001\"],\"components\":[{{\"comp_id\":\"login-form\",\"comp_type\":\"LoginForm\",\"props\":{{\"fields\":[\"username\",\"password\"]}}}}]}}],\"html_prototypes\":\"<html>...预览HTML...</html>\"}}"
                result = chat_json(system_prompt, user_prompt)
                pages = []
                for p in result.get("pages", []):
                    comps = [PageComponent(c.get("comp_id","c"),c["comp_type"],c.get("props",{})) for c in p.get("components",[])]
                    pages.append(PageDef(p["page_id"], p["name"], p["route"], comps, ep_links=p.get("ep_links",[])))
                html_prototypes = result.get("html_prototypes", "")
            except Exception:
                pages = self._generate_pages(interface, domain_model)
                html_prototypes = self._generate_html(pages)
        else:
            pages = self._generate_pages(interface, domain_model)
            html_prototypes = self._generate_html(pages)
        artifact = PrototypeArtifact()
        artifact.pages = pages
        artifact.html_prototypes = html_prototypes

        model.prototype = artifact
        return {
            "pages": [p.to_dict() for p in pages],
            "html_prototypes": artifact.html_prototypes,
        }

    def _generate_pages(self, interface, domain_model) -> List[PageDef]:
        pages = []
        base_pages = [
            ("PAGE-001", "登录页面", "/login", ["EP-001"],
             [PageComponent("login-form", "LoginForm", {"fields": ["username", "password"]})]),
            ("PAGE-002", "注册页面", "/register", ["EP-002"],
             [PageComponent("register-form", "RegisterForm", {"fields": ["username", "password", "email"]})]),
            ("PAGE-003", "个人中心", "/profile", ["EP-003", "EP-004"],
             [PageComponent("user-info", "UserInfoCard", {}), PageComponent("edit-form", "EditForm", {})]),
            ("PAGE-004", "用户管理", "/admin/users", ["EP-005"],
             [PageComponent("user-table", "DataTable", {}), PageComponent("search-bar", "SearchBar", {})]),
            ("PAGE-005", "角色管理", "/admin/roles", ["EP-006", "EP-007"],
             [PageComponent("role-table", "DataTable", {}), PageComponent("role-form", "FormModal", {})]),
            ("PAGE-006", "操作日志", "/admin/logs", ["EP-008"],
             [PageComponent("log-table", "DataTable", {}), PageComponent("log-filter", "FilterBar", {})]),
        ]
        for pid, name, route, eps, comps in base_pages:
            pages.append(PageDef(pid, name, route, comps, ep_links=eps))

        use_case_names = ""
        if domain_model and hasattr(domain_model, "use_cases"):
            use_case_names = " ".join(uc.name for uc in domain_model.use_cases)

        if "商品" in use_case_names or "product" in use_case_names.lower():
            pages.extend([
                PageDef("PAGE-007", "商品列表", "/products", [
                    PageComponent("product-grid", "ProductGrid", {}),
                    PageComponent("search-bar", "SearchBar", {}),
                    PageComponent("category-filter", "CategoryFilter", {}),
                ], ep_links=["EP-009"]),
                PageDef("PAGE-008", "商品详情", "/products/{id}", [
                    PageComponent("product-detail", "ProductDetail", {}),
                    PageComponent("add-to-cart", "AddToCart", {}),
                ], ep_links=["EP-011"]),
                PageDef("PAGE-009", "商品管理", "/admin/products", [
                    PageComponent("product-table", "DataTable", {}),
                    PageComponent("product-form", "FormModal", {}),
                ], ep_links=["EP-009", "EP-010", "EP-012", "EP-013"]),
                PageDef("PAGE-010", "分类管理", "/admin/categories", [
                    PageComponent("category-tree", "CategoryTree", {}),
                    PageComponent("category-form", "FormModal", {}),
                ], ep_links=["EP-014"]),
                PageDef("PAGE-011", "创建订单", "/orders/new", [
                    PageComponent("order-form", "OrderForm", {}),
                    PageComponent("product-selector", "ProductSelector", {}),
                ], ep_links=["EP-015"]),
                PageDef("PAGE-012", "订单列表", "/orders", [
                    PageComponent("order-table", "DataTable", {}),
                    PageComponent("order-filter", "FilterBar", {}),
                ], ep_links=["EP-016"]),
                PageDef("PAGE-013", "订单详情", "/orders/{id}", [
                    PageComponent("order-detail", "OrderDetail", {}),
                ], ep_links=["EP-017"]),
            ])

        return pages

    def _generate_html(self, pages: List[PageDef]) -> str:
        parts = ["<html><body style='font-family: sans-serif; background: #f5f5f5; padding: 20px;'>"]
        parts.append("<h1 style='color: #333;'>页面原型预览</h1>")
        for page in pages:
            parts.append(f"<div style='background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>")
            parts.append(f"<h2 style='color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 8px;'>{page.name}</h2>")
            parts.append(f"<p style='color: #666;'><strong>路由:</strong> {page.route}</p>")
            parts.append(f"<p style='color: #666;'><strong>关联接口:</strong> {', '.join(page.ep_links) if page.ep_links else '无'}</p>")
            parts.append(f"<div style='border: 1px dashed #ccc; border-radius: 4px; padding: 16px; margin-top: 12px;'>")
            parts.append(f"<p style='color: #999; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;'>页面组件</p>")
            for comp in page.components:
                parts.append(f"<div style='background: #e8f0fe; border-radius: 4px; padding: 12px; margin: 8px 0; display: inline-block;'>")
                parts.append(f"<strong>{comp.comp_type}</strong>")
                if comp.props:
                    parts.append(f"<pre style='font-size: 11px; color: #555; margin: 4px 0 0;'>{comp.props}</pre>")
                parts.append(f"</div>")
            parts.append(f"</div></div>")
        parts.append("</body></html>")
        return "\n".join(parts)
