from __future__ import annotations
import os
import json
from typing import Optional, Dict, Any

import httpx


class LLMConfig:
    def __init__(self):
        self.enabled = os.environ.get("LLM_ENABLED", "").lower() in ("true", "1", "yes")
        self.api_key = os.environ.get("LLM_API_KEY", "")
        self.api_base = os.environ.get("LLM_API_BASE", "https://api.openai.com/v1")
        self.model = os.environ.get("LLM_MODEL", "gpt-4o")
        self.max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "4096"))
        self.temperature = float(os.environ.get("LLM_TEMPERATURE", "0.7"))

    @classmethod
    def from_env(cls) -> LLMConfig:
        return cls()

    def check(self) -> str | None:
        if not self.enabled:
            return "LLM is disabled (set LLM_ENABLED=true)"
        if not self.api_key:
            return "LLM_API_KEY is not set"
        return None


_default_config: LLMConfig | None = None


def get_config() -> LLMConfig:
    global _default_config
    if _default_config is None:
        _default_config = LLMConfig.from_env()
    return _default_config


def chat(system_prompt: str, user_prompt: str, config: Optional[LLMConfig] = None) -> str:
    cfg = config or get_config()
    err = cfg.check()
    if err:
        raise RuntimeError(err)
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }
    body: Dict[str, Any] = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": cfg.max_tokens,
        "temperature": cfg.temperature,
    }
    url = f"{cfg.api_base.rstrip('/')}/chat/completions"
    with httpx.Client(timeout=180) as client:
        resp = client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def chat_json(system_prompt: str, user_prompt: str, config: Optional[LLMConfig] = None) -> dict:
    text = chat(system_prompt, user_prompt, config)
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        cleaned = cleaned.rsplit("```", 1)[0]
    return json.loads(cleaned.strip())
