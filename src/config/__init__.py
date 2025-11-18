"""
Centralized Configuration Module
---------------------------------
Provides centralized access to all configuration settings and re-exports
legacy symbols so existing imports like `from config import ...` continue
working after the model configuration refactor.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so we can import model_config at repo root
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Local configuration modules (package)
from config.budgets import DEFAULT_AGENT_BUDGETS  # noqa: F401
from config.timeouts import DEFAULT_TIMEOUTS, TimeoutConfig  # noqa: F401
from config.sandbox import DEFAULT_SANDBOX_CONFIG, SandboxConfig  # noqa: F401

# Re-export model configuration from top-level model_config.py for backward compatibility
try:
    from model_config import (  # type: ignore
        DEFAULT_TONGYI_CONFIG,
        DEFAULT_CLAUDE_CONFIG,
        DEFAULT_MODEL_ROUTER,
        DEFAULT_TOOL_CONFIG,
        ModelRouter,
        ModelConfig,
        OpenRouterModels,
        get_config,
    )
except Exception:  # pragma: no cover - allow partial availability in minimal envs
    # Provide soft fallbacks so importing `config` doesn't explode in constrained envs
    DEFAULT_TONGYI_CONFIG = None  # type: ignore
    DEFAULT_CLAUDE_CONFIG = None  # type: ignore
    DEFAULT_MODEL_ROUTER = None  # type: ignore
    DEFAULT_TOOL_CONFIG = None  # type: ignore
    ModelRouter = None  # type: ignore
    ModelConfig = None  # type: ignore
    OpenRouterModels = None  # type: ignore
    def get_config():  # type: ignore
        return {}

__all__ = [
    # Local package configs
    "DEFAULT_AGENT_BUDGETS",
    "DEFAULT_TIMEOUTS",
    "TimeoutConfig",
    "DEFAULT_SANDBOX_CONFIG",
    "SandboxConfig",
    # Re-exported model configuration (legacy interface)
    "DEFAULT_TONGYI_CONFIG",
    "DEFAULT_CLAUDE_CONFIG",
    "DEFAULT_MODEL_ROUTER",
    "DEFAULT_TOOL_CONFIG",
    "ModelRouter",
    "ModelConfig",
    "OpenRouterModels",
    "get_config",
]
