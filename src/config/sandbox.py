"""
Sandbox Configuration
----------------------
Centralized configuration for sandbox execution environment.
"""
from dataclasses import dataclass
import os


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution."""

    # Docker settings
    docker_image: str = "python:3.13-slim"
    memory_limit: str = "256m"
    cpu_limit: str = "0.5"  # Half a core

    # Execution limits
    default_timeout_s: int = 60
    stdio_limit: int = 64 * 1024  # 64 KB each for stdout/stderr

    # Environment
    seed: int = 1337  # Default RNG seed for deterministic execution

    @classmethod
    def from_env(cls):
        """Load configuration from environment variables."""
        return cls(
            docker_image=os.getenv("SANDBOX_DOCKER_IMAGE", cls.docker_image),
            memory_limit=os.getenv("SANDBOX_MEMORY_LIMIT", cls.memory_limit),
            cpu_limit=os.getenv("SANDBOX_CPU_LIMIT", cls.cpu_limit),
            default_timeout_s=int(os.getenv("SANDBOX_TIMEOUT", str(cls.default_timeout_s))),
        )


# Default sandbox configuration
DEFAULT_SANDBOX_CONFIG = SandboxConfig()
