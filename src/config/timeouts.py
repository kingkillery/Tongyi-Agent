"""
Timeout Configuration
---------------------
Centralized timeout settings for all external operations.
"""
from dataclasses import dataclass


@dataclass
class TimeoutConfig:
    """Timeout configuration for various operations."""

    # API-related timeouts
    api_request: int = 120  # OpenRouter/external API requests
    api_connection: int = 30  # Initial connection establishment
    api_disconnect: int = 10  # Graceful disconnect timeout

    # Sandbox execution timeouts
    sandbox_execution: int = 60  # Code execution in sandbox
    docker_operations: int = 30  # Docker pull/run operations

    # External service timeouts
    scholar_search: int = 60  # Academic paper search
    file_download: int = 30  # File/PDF downloads

    # Docker checks
    docker_check: int = 5  # Docker availability check


# Default timeout instance
DEFAULT_TIMEOUTS = TimeoutConfig()
