from __future__ import annotations
import json
import re
from typing import Dict, Any, List, Tuple
from shared.domain_model import RequirementsArtifact, RequirementItem, UnifiedDomainModel
from backend.llm_client import chat_json, get_config


class RequirementsAgent:
    """Phase 1: Analyze raw requirements, detect vocabulary gaps, output structured requirements."""

    GAP_PATTERNS = {
        "user_role": r"(用户|角色|权限|登录|注册|admin|管理员|普通用户|游客)",
        "auth": r"(认证|授权|token|session|密码|登录|注册|验证码)",
        "error_handling": r"(错误|异常|失败|超时|重试|回滚|容错)",
        "validation": r"(验证|校验|格式|必填|可选|约束|规则)",
        "data_persistence": r"(保存|存储|持久化|数据库|缓存|文件|导出|导入)",
        "pagination": r"(分页|翻页|列表|页码|每页)",
        "search": r"(搜索|查询|筛选|过滤|排序|关键字)",
        "notification": r"(通知|消息|提醒|推送|邮件|短信)",
        "audit": r"(日志|审计|操作记录|历史|追踪|流水)",
        "permission": r"(权限|角色|菜单|按钮级|数据权限|角色分配)",
        "concurrency": r"(并发|锁|同步|异步|线程安全|事务)",
        "performance": r"(性能|响应时间|并发数|吞吐量|延迟|优化)",
        "i18n": r"(国际化|多语言|i18n|l10n|本地化)",
    }

    def execute(self, model: UnifiedDomainModel, params: Dict[str, Any]) -> Dict[str, Any]:
        raw_input = params.get("raw_input", "")
        if not raw_input:
            raw_input = model.requirements.raw_input

        cfg = get_config()
        if cfg.enabled:
            try:
                system_prompt = "你是一个资深需求分析师。将原始需求拆解为结构化需求项，并检测缺失的词汇维度。直接输出JSON，不要markdown包裹。"
                user_prompt = f"原始需求：\n{raw_input}\n\n请输出 JSON：{{ \"items\": [{{ \"req_id\": \"REQ-001\", \"title\": \"...\", \"description\": \"...\", \"priority\": \"high|medium|low\", \"category\": \"functional|non-functional|ui|api|data\", \"status\": \"draft\", \"gap_notes\": \"\" }}], \"vocab_gaps\": [\"缺失维度名\"] }}"
                result = chat_json(system_prompt, user_prompt)
                items = [RequirementItem(**i) if all(k in i for k in ("req_id","title","description","priority","category","status")) else RequirementItem(req_id=i.get("req_id","REQ-000"),title=i.get("title",""),description=i.get("description",""),priority=i.get("priority","medium"),category=i.get("category","functional"),status=i.get("status","draft"),gap_notes=i.get("gap_notes","")) for i in result.get("items",[])]
                gaps = result.get("vocab_gaps", [])
            except Exception:
                items = self._parse_requirements(raw_input)
                gaps = self._detect_gaps(raw_input, items)
        else:
            items = self._parse_requirements(raw_input)
            gaps = self._detect_gaps(raw_input, items)

        artifact = RequirementsArtifact()
        artifact.raw_input = raw_input
        artifact.items = items
        artifact.vocab_gaps = gaps

        model.requirements = artifact
        return {
            "items": [i.to_dict() for i in items],
            "vocab_gaps": gaps,
            "total_items": len(items),
            "gap_count": len(gaps),
        }

    def _parse_requirements(self, raw: str) -> List[RequirementItem]:
        lines = raw.strip().split("\n")
        items = []
        req_counter = 0
        current_title = ""
        current_desc_parts = []
        current_priority = "medium"
        current_category = "functional"
        has_numbered_match = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            priority_match = re.search(r"\[(high|medium|low)\]", line, re.IGNORECASE)
            if priority_match:
                current_priority = priority_match.group(1).lower()

            cat_match = re.search(r"\((functional|non-functional|ui|api|data)\)", line, re.IGNORECASE)
            if cat_match:
                current_category = cat_match.group(1).lower()

            is_new_item = bool(re.match(r"^[\d]+[.、)\s]", line) or re.match(r"^[-*]", line))
            if is_new_item:
                has_numbered_match = True
                if current_title:
                    req_counter += 1
                    items.append(RequirementItem(
                        req_id=f"REQ-{req_counter:03d}",
                        title=current_title,
                        description="\n".join(current_desc_parts),
                        priority=current_priority,
                        category=current_category,
                    ))
                clean = re.sub(r"^[\d]+[.、)\s]+", "", line)
                clean = re.sub(r"^[-*]\s+", "", clean)
                clean = re.sub(r"\[(high|medium|low)\]\s*", "", clean, flags=re.IGNORECASE)
                clean = re.sub(r"\((functional|non-functional|ui|api|data)\)\s*", "", clean, flags=re.IGNORECASE)
                current_title = clean.strip()
                current_desc_parts = []
                current_priority = "medium"
                current_category = "functional"
            else:
                if current_title:
                    current_desc_parts.append(line)

        if current_title:
            req_counter += 1
            items.append(RequirementItem(
                req_id=f"REQ-{req_counter:03d}",
                title=current_title,
                description="\n".join(current_desc_parts),
                priority=current_priority,
                category=current_category,
            ))

        if not items:
            req_counter += 1
            full_text = raw[:100].strip()
            items.append(RequirementItem(
                req_id=f"REQ-{req_counter:03d}",
                title=full_text if len(full_text) > 5 else raw.strip()[:100],
                description=raw,
            ))

        return items

    def _detect_gaps(self, raw: str, items: List[RequirementItem]) -> List[str]:
        combined = raw + "\n" + "\n".join(
            f"{i.title} {i.description}" for i in items
        )
        gaps = []
        for gap_name, pattern in self.GAP_PATTERNS.items():
            if not re.search(pattern, combined, re.IGNORECASE):
                gaps.append(gap_name)
        return gaps
