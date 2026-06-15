from __future__ import annotations
from typing import Dict, Any, List
import json

from shared.domain_model import (
    UnifiedDomainModel, CodeArtifact, CodeFile,
)
from backend.llm_client import chat_json, get_config


class CodeAgent:
    """Phase 7: Generate backend and frontend code from previous artifacts."""

    def execute(self, model: UnifiedDomainModel, params: Dict[str, Any]) -> Dict[str, Any]:
        interface = model.interface
        database = model.database
        if not interface or not interface.endpoints:
            return {"error": "No endpoints found. Complete Phase 4 first."}

        cfg = get_config()
        if cfg.enabled:
            try:
                context = {
                    "endpoints": [e.to_dict() for e in interface.endpoints],
                    "tables": [t.to_dict() for t in database.tables] if database else [],
                }
                system_prompt = "你是一个全栈工程师。根据API端点和数据库表生成完整的后端(Python/FastAPI/SQLAlchemy)和前端(TypeScript/React)代码。直接输出JSON，每条代码文件包含path和content字段。"
                user_prompt = f"上下文：{json.dumps(context, ensure_ascii=False)}\n\n输出JSON格式：{{\"backend_files\":[{{\"path\":\"backend/main.py\",\"content\":\"...\",\"language\":\"python\"}}],\"frontend_files\":[{{\"path\":\"frontend/src/api/index.ts\",\"content\":\"...\",\"language\":\"typescript\"}}],\"ep_to_code_map\":{{\"EP-001\":\"handlers/ep_001.py\"}}}}"
                result = chat_json(system_prompt, user_prompt)
                backend_files = [CodeFile(f["path"], f["content"], f.get("language","python")) for f in result.get("backend_files",[])]
                frontend_files = [CodeFile(f["path"], f["content"], f.get("language","typescript")) for f in result.get("frontend_files",[])]
                ep_to_code_map = result.get("ep_to_code_map", {})
            except Exception:
                backend_files = self._generate_backend(interface, database, model)
                frontend_files = self._generate_frontend(interface, model)
                ep_to_code_map = {ep.ep_id: f"handlers/{ep.ep_id.lower().replace('-', '_')}.py" for ep in interface.endpoints}
        else:
            backend_files = self._generate_backend(interface, database, model)
            frontend_files = self._generate_frontend(interface, model)
            ep_to_code_map = {ep.ep_id: f"handlers/{ep.ep_id.lower().replace('-', '_')}.py" for ep in interface.endpoints}

        artifact = CodeArtifact()
        artifact.backend_files = backend_files
        artifact.frontend_files = frontend_files
        artifact.ep_to_code_map = ep_to_code_map

        model.code = artifact
        return {
            "backend_files": [f.to_dict() for f in backend_files],
            "frontend_files": [f.to_dict() for f in frontend_files],
            "ep_to_code_map": ep_to_code_map,
        }

    def _generate_backend(self, interface, database, model) -> List[CodeFile]:
        files = []

        # main.py
        files.append(CodeFile("backend/main.py", """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Waterfall API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
""", "python"))

        # models.py
        table_models = []
        if database and database.tables:
            for table in database.tables:
                cols = []
                for c in table.columns:
                    py_type = {"BIGINT": "int", "INT": "int", "TINYINT": "int",
                               "VARCHAR": "str", "TEXT": "str", "DECIMAL": "float",
                               "DATETIME": "datetime"}.get(c.dtype.split("(")[0], "str")
                    cols.append(f"    {c.name}: Optional[{py_type}] = None")
                table_models.append(f"""
class {table.name.title().replace('_', '')}(Base):
    __tablename__ = "{table.name}"
{chr(10).join(cols)}""")

        files.append(CodeFile("backend/models.py", f"""from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional

Base = declarative_base()

{''.join(table_models) if table_models else '# No tables defined'}
""", "python"))

        # handlers
        for ep in interface.endpoints:
            handler_code = f"""
async def handle_{ep.ep_id.lower().replace('-', '_')}(request, response):
    \"\"\"{ep.summary}\"\"\"
    # TODO: implement {ep.method} {ep.path}
    return {{"message": "{ep.summary} - not implemented"}}
"""
            files.append(CodeFile(
                f"backend/handlers/{ep.ep_id.lower().replace('-', '_')}.py",
                handler_code,
                "python"
            ))

        # requirements.txt
        files.append(CodeFile("backend/requirements.txt", """fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.2
pytest==7.4.3
httpx==0.25.2
""", "text"))

        return files

    def _generate_frontend(self, interface, model) -> List[CodeFile]:
        files = []

        prototype = model.prototype

        endpoints_json = []
        for ep in interface.endpoints:
            endpoints_json.append({
                "id": ep.ep_id,
                "method": ep.method,
                "path": ep.path,
                "summary": ep.summary,
            })

        files.append(CodeFile("frontend/src/api/index.ts", f"""import axios from 'axios';

const api = axios.create({{
  baseURL: '/api/v1',
  timeout: 10000,
}});

api.interceptors.request.use((config) => {{
  const token = localStorage.getItem('token');
  if (token) {{
    config.headers.Authorization = `Bearer ${{token}}`;
  }}
  return config;
}});

{self._ts_api_functions(interface)}

export default api;
""", "typescript"))

        files.append(CodeFile("frontend/src/types/index.ts", f"""export interface User {{
  id: number;
  username: string;
  email: string;
  phone?: string;
  status: number;
}}

export interface ApiResponse<T> {{
  code: number;
  message: string;
  data: T;
}}

export const API_ENDPOINTS = {json.dumps(endpoints_json, indent=2, ensure_ascii=False)};
""", "typescript"))

        pages_code = []
        if prototype and prototype.pages:
            for page in prototype.pages:
                pages_code.append(f"""import React from 'react';
import {{ API_ENDPOINTS }} from '../types';

const {page.name.replace(' ', '')}: React.FC = () => {{
  return (
    <div className="page-container">
      <h1>{page.name}</h1>
      <p>Route: {page.route}</p>
      <div className="page-components">
        {page.components[0].comp_type if page.components else 'div'}
      </div>
    </div>
  );
}};

export default {page.name.replace(' ', '')};
""")

        if pages_code:
            files.append(CodeFile("frontend/src/pages/index.tsx", "\n".join(pages_code), "typescript"))

        files.append(CodeFile("frontend/package.json", """{
  "name": "waterfall-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.2",
    "antd": "^5.12.0",
    "@ant-design/icons": "^5.2.6"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test"
  },
  "devDependencies": {
    "typescript": "^5.3.2",
    "@types/react": "^18.2.39",
    "@types/react-dom": "^18.2.17"
  }
}
""", "json"))

        return files

    def _ts_api_functions(self, interface) -> str:
        funcs = []
        for ep in interface.endpoints:
            ep_id_safe = ep.ep_id.lower().replace('-', '_')
            func_body = f"export const {ep_id_safe} = async (params?: any) => {{\n  return api.{{" + "{}".format(ep.method.lower()) + f"}}(`{ep.path.replace('{', '${')}`, params);\n}};"
            funcs.append(func_body + "\n")
        return "\n".join(funcs)
