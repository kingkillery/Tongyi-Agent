"""Agent client adapters for delegation handlers."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

# Import centralized error handling
from error_handler import (
    APIKeyError,
    ModelNotFoundError,
    NetworkError,
    RateLimitError,
    TimeoutError,
    get_api_unavailable_message,
    get_invalid_api_key_message,
    get_model_unavailable_message,
    get_rate_limit_message,
    get_timeout_message,
    is_retryable_error,
)

# Import caching for API calls
from cache import get_api_cache


class AgentClientError(RuntimeError):
    """Base error class for agent client failures."""
    pass


@dataclass
class OpenRouterClient:
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    timeout: int = 120  # Increased timeout for complex reasoning
    max_retries: int = 3
    backoff_factor: float = 1.5
    enable_cache: bool = True  # Enable caching for API responses

    def chat(self, prompt: str, *, model: str, use_cache: Optional[bool] = None, **params: Any) -> Any:
        """
        Send a chat request to OpenRouter.

        Args:
            prompt: Either a string prompt or a list of message dicts for multi-turn conversations
            model: Model identifier
            use_cache: Override default cache behavior (optional)
            **params: Additional parameters (temperature, tools, etc.)

        Returns:
            Response object with .choices[0].message or string content
        """
        # Determine if caching should be used
        should_cache = use_cache if use_cache is not None else self.enable_cache

        # Skip caching for tool calls (stateful operations)
        has_tools = "tools" in params or "tool_choice" in params
        if has_tools:
            should_cache = False

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

        # Try cache first if enabled
        if should_cache and not has_tools:
            cache = get_api_cache()
            # Create cache key from model, messages, and key params
            cache_params = {k: v for k, v in params.items() if k in ['temperature', 'top_p', 'max_tokens']}
            cache_key = cache._make_key(model, messages, **cache_params)
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                # Return cached response in same format
                if isinstance(cached_response, str):
                    return cached_response
                else:
                    # Recreate Response object from cached data
                    class Response:
                        def __init__(self, data):
                            self.data = data
                            self.choices = data.get("choices", [])
                            self.tool_calls = self.choices[0].get("message", {}).get("tool_calls") if self.choices else None

                        def __str__(self):
                            if self.choices:
                                return self.choices[0].get("message", {}).get("content", "").strip()
                            return ""
                    return Response(cached_response)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        resp = self._post_with_retry(payload, headers)
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            raise AgentClientError("OpenRouter returned no choices")

        # Cache the response if enabled
        if should_cache and not has_tools:
            cache = get_api_cache()
            cache_params = {k: v for k, v in params.items() if k in ['temperature', 'top_p', 'max_tokens']}
            cache_key = cache._make_key(model, messages, **cache_params)
            cache.set(cache_key, data)

        # Return full response object if tools were used, otherwise return content string
        if has_tools:
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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _post_with_retry(self, payload: Dict[str, Any], headers: Dict[str, str]) -> requests.Response:
        endpoint = f"{self.base_url.rstrip('/')}/chat/completions"
        attempt = 0
        last_error: Optional[str] = None

        while attempt <= self.max_retries:
            try:
                resp = requests.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:  # pragma: no cover
                last_error = str(exc)
                if attempt == self.max_retries:
                    raise AgentClientError(
                        "Network error reaching OpenRouter. Check your internet connection and proxy settings."
                    ) from exc
                self._sleep_with_backoff(attempt)
                attempt += 1
                continue

            if resp.status_code < 400:
                return resp

            if self._is_transient_status(resp.status_code) and attempt < self.max_retries:
                last_error = self._format_http_error(resp)
                self._sleep_with_backoff(attempt)
                attempt += 1
                continue

            raise AgentClientError(self._format_http_error(resp))

        raise AgentClientError(last_error or "Unknown error contacting OpenRouter")

    def _sleep_with_backoff(self, attempt: int) -> None:
        delay = min(self.backoff_factor ** attempt, 15)
        time.sleep(delay)

    @staticmethod
    def _is_transient_status(status_code: int) -> bool:
        return status_code in {408, 425, 429, 500, 502, 503, 504}

    def _format_http_error(self, resp: requests.Response) -> str:
        """Format HTTP error with user-friendly messages using centralized error handling."""
        status = resp.status_code
        body_preview = resp.text.strip().replace("\n", " ")[:300] or "<empty response>"

        # Use centralized error messages for common error types
        if status in {401, 403}:
            return get_invalid_api_key_message()
        elif status == 404:
            return get_model_unavailable_message("requested endpoint or model")
        elif status == 429:
            return get_rate_limit_message()
        elif status >= 500:
            return get_api_unavailable_message()
        else:
            # Generic error with minimal guidance
            hints = [
                "Review your request parameters and try again.",
                "Run 'python -m config_validator --check-openrouter' for diagnostics.",
            ]
            hint_text = " ".join(hints)
            request_id = resp.headers.get("x-request-id")
            if request_id:
                hint_text += f" (request id: {request_id})"
            return f"OpenRouter error {status}: {body_preview}. {hint_text}"


def load_openrouter_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> Optional[OpenRouterClient]:
    token = api_key or os.getenv("OPENROUTER_API_KEY")
    if not token:
        return None
    return OpenRouterClient(api_key=token, base_url=base_url or "https://openrouter.ai/api/v1")

