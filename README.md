# Waterfall Agent — SDLC 自动化系统

AI Agent 驱动的 8 阶段瀑布式软件工程全流程自动化系统。每个阶段由独立 Agent 执行，生成结构化可审查的产物，支持人工审批、回滚、全链路追溯。

## 核心理念

- **阶段化交付** — 需求 → 领域模型 → 数据库 → 接口 → 时序 → 原型 → 代码 → 测试，前序审批后方可执行后续
- **人机协同** — Agent 自动产出，人工审批放行，可驳回/回滚/编辑
- **全链路追溯** — 每一步操作记录为 TraceEvent，可回溯任意时刻的快照
- **结构化产物** — 每个阶段的输出是强类型结构化数据模型，而非文本，供下游 Agent 精确消费

## 架构

```
user ←→ FastAPI (backend/main.py) ←→ 8 Agents (backend/agents/)
                ↕                           ↕
         WorkflowService           UnifiedDomainModel
         TraceabilityService        (shared/domain_model.py)
         RollbackService
                ↕
         Static Frontend (index.html)
```

## 8 阶段

| # | 阶段 | Agent | 输出产物 |
|---|------|-------|---------|
| 1 | 需求分析 | `RequirementsAgent` | 需求项列表、词汇缺口检测 |
| 2 | 领域模型 | `DomainModelAgent` | 参与者、用例、PlantUML 用例图 |
| 3 | 数据库设计 | `DatabaseAgent` | 表结构、多方言 DDL、ER 图 |
| 4 | 接口设计 | `InterfaceAgent` | REST API 端点、OpenAPI 规范 |
| 5 | 时序图 | `SequenceAgent` | 交互流程、PlantUML 时序图 |
| 6 | 页面原型 | `PrototypeAgent` | 页面列表、组件定义 |
| 7 | 代码生成 | `CodeAgent` | 后端 + 前端代码文件 |
| 8 | 测试用例 | `TestAgent` | 测试用例、覆盖映射、测试代码 |

## 快速开始

```bash
# 安装依赖
pip install fastapi uvicorn pydantic

# 启动服务（开发模式，支持热重载）
python start.py

# 或直接 uvicorn
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

打开 `http://127.0.0.1:8000` 使用 Web UI。

### API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/projects` | 创建项目 |
| GET | `/api/projects` | 项目列表 |
| GET | `/api/projects/{id}` | 项目详情 |
| POST | `/api/projects/{id}/phases/{phase}/execute` | 执行阶段 |
| POST | `/api/projects/{id}/phases/{phase}/approve` | 审批通过 |
| POST | `/api/projects/{id}/phases/{phase}/reject` | 驳回 |
| POST | `/api/projects/{id}/phases/{phase}/rollback` | 回滚（清除后续） |
| GET | `/api/projects/{id}/phases/{phase}/artifact` | 获取产物 |
| POST | `/api/projects/{id}/phases/{phase}/artifact` | 编辑产物 |
| GET | `/api/projects/{id}/trace` | 追溯日志 |
| GET | `/api/projects/{id}/code/download` | 下载代码 ZIP |

## 使用流程

1. **创建项目** → 填写项目名称
2. **阶段 1 需求分析** → 输入原始需求文本 → 执行 → Agent 自动拆解需求项、检测词汇缺口 → 审批
3. **逐阶段推进** → 每个阶段执行后审查产物，满意则审批通过自动进入下一阶段
4. **回滚** → 任一阶段发现问题可回滚，后续阶段自动清除
5. **产物编辑** → 支持人工直接编辑产物 JSON
6. **代码下载** → 代码阶段完成后可一键下载整个项目 ZIP

## 项目结构

```
waterfall-agent/
├── start.py                     # 启动入口
├── backend/
│   ├── main.py                  # FastAPI 应用 + 路由
│   ├── static/index.html        # 前端 SPA
│   ├── agents/                  # 8 个阶段 Agent
│   │   ├── requirements_agent.py
│   │   ├── domain_model_agent.py
│   │   ├── database_agent.py
│   │   ├── interface_agent.py
│   │   ├── sequence_agent.py
│   │   ├── prototype_agent.py
│   │   ├── code_agent.py
│   │   └── test_agent.py
│   └── services/                # 支撑服务
│       ├── workflow.py          # 阶段状态机 + 依赖校验
│       ├── traceability.py      # 追溯 + JSONL 审计日志
│       └── rollback.py          # 快照回滚
├── shared/
│   └── domain_model.py          # 统一领域模型（8 个 Artifact + TraceEvent）
```

## 技术栈

- **后端**: Python 3.10+, FastAPI, Uvicorn, Pydantic
- **前端**: 纯 HTML/CSS/JS（无框架依赖）
- **图表**: PlantUML 在线渲染（用例图、ER 图、时序图）
- **存储**: 内存（进程内）+ JSONL 审计日志 + JSON 快照文件
