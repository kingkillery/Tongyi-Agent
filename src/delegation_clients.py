"""Agent client adapters for delegation handlers."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


class AgentClientError(RuntimeError):
    pass


@dataclass
class OpenRouterClient:
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    timeout: int = 60

    def chat(self, prompt: str, *, model: str, **params: Any) -> str:
        messages = [
            {"role": "system", "content": params.pop("system_prompt", "You are a helpful research assistant.")},
            {"role": "user", "content": prompt},
        ]
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        payload.update(params)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:  # pragma: no cover
            raise AgentClientError(f"Network error calling OpenRouter: {exc}") from exc
        if resp.status_code >= 400:
            raise AgentClientError(f"OpenRouter error {resp.status_code}: {resp.text}")
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            raise AgentClientError("OpenRouter returned no choices")
        return choices[0].get("message", {}).get("content", "").strip()


def load_openrouter_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> Optional[OpenRouterClient]:
    token = api_key or os.getenv("OPENROUTER_API_KEY")
    if not token:
        return None
    return OpenRouterClient(api_key=token, base_url=base_url or "https://openrouter.ai/api/v1")

