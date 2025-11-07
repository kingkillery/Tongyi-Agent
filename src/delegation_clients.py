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
    timeout: int = 120  # Increased timeout for complex reasoning

    def chat(self, prompt: str, *, model: str, **params: Any) -> Any:
        """
        Send a chat request to OpenRouter.
        
        Args:
            prompt: Either a string prompt or a list of message dicts for multi-turn conversations
            model: Model identifier
            **params: Additional parameters (temperature, tools, etc.)
        
        Returns:
            Response object with .choices[0].message or string content
        """
        # Handle both string prompts and full message arrays
        if isinstance(prompt, str):
            messages = [
                {"role": "system", "content": params.pop("system_prompt", "You are a helpful research assistant.")},
                {"role": "user", "content": prompt},
            ]
        elif isinstance(prompt, list):
            # Use provided messages directly (for multi-turn conversations)
            messages = prompt
        else:
            raise ValueError(f"Invalid prompt type: {type(prompt)}")
        
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
        
        # Return full response object if tools were used, otherwise return content string
        if "tools" in params or "tool_choice" in params:
            # Return a simple object with the response structure
            class Response:
                def __init__(self, data):
                    self.data = data
                    self.choices = data.get("choices", [])
                    self.tool_calls = self.choices[0].get("message", {}).get("tool_calls") if self.choices else None
                
                def __str__(self):
                    if self.choices:
                        return self.choices[0].get("message", {}).get("content", "").strip()
                    return ""
            
            return Response(data)
        else:
            # Simple string response for backward compatibility
            return choices[0].get("message", {}).get("content", "").strip()


def load_openrouter_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> Optional[OpenRouterClient]:
    token = api_key or os.getenv("OPENROUTER_API_KEY")
    if not token:
        return None
    return OpenRouterClient(api_key=token, base_url=base_url or "https://openrouter.ai/api/v1")

