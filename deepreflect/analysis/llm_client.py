"""LLM-agnostic client. Supports Anthropic, OpenAI, Ollama, and any OpenAI-compatible endpoint."""
from __future__ import annotations

import json

import httpx


class LLMClient:
    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str,
        base_url: str = "",
    ) -> None:
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    async def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        if self.provider == "anthropic":
            return await self._anthropic(system, user, max_tokens)
        return await self._openai_compat(system, user, max_tokens)

    async def _anthropic(self, system: str, user: str, max_tokens: int) -> str:
        url = self.base_url or "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    async def _openai_compat(self, system: str, user: str, max_tokens: int) -> str:
        if self.provider == "ollama":
            base = self.base_url or "http://localhost:11434/v1"
            api_key = "ollama"
        elif self.provider == "openrouter":
            base = self.base_url or "https://openrouter.ai/api/v1"
            api_key = self.api_key
        else:  # openai or custom
            base = self.base_url or "https://api.openai.com/v1"
            api_key = self.api_key

        url = f"{base.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "content-type": "application/json",
        }
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            msg = data["choices"][0]["message"]
            text = (msg.get("content") or "").strip()
            if not text:
                text = (msg.get("reasoning") or "").strip()
            return text

    @classmethod
    def from_config(cls, cfg) -> "LLMClient":
        return cls(
            provider=cfg.llm_provider,
            api_key=cfg.llm_api_key,
            model=cfg.llm_model,
            base_url=cfg.llm_base_url,
        )
