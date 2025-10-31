"""
Configuration for Tongyi DeepResearch Agent
Optimized parameters based on Tongyi DeepResearch specifications
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, field_validator
import os
import sys
from dotenv import load_dotenv

load_dotenv()

class TongyiConfig(BaseModel):
    """Tongyi DeepResearch model configuration"""
    
    # Model parameters
    model_name: str = "alibaba/tongyi-deepresearch-30b-a3b"
    free_model_name: str = "alibaba/tongyi-deepresearch-30b-a3b:free"
    free_call_interval: int = 3  # Use free tier every Nth call
    api_key: str
    base_url: Optional[str] = None
    
    # Inference parameters for optimal stability
    temperature: float = 0.85
    repetition_penalty: float = 1.1
    top_p: float = 0.95
    max_tokens: int = 128000  # 128K context length
    
    # Tool and interaction limits
    max_tool_invocations: int = 128
    max_parallel_branches: int = 8
    
    # Mode configuration
    default_mode: str = "react"  # "react" or "heavy"
    
    # Context management
    enable_markov_state: bool = True
    memory_compression_ratio: float = 0.3
    
    # Web access configuration
    search_timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 1.0
    
    # Data filtering
    enable_content_filtering: bool = True
    relevance_threshold: float = 0.7
    max_concurrent_requests: int = 10
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        if not v or not v.strip():
            print("ERROR: OPENROUTER_API_KEY is required for Tongyi Agent to function.", file=sys.stderr)
            print("", file=sys.stderr)
            print("Setup instructions:", file=sys.stderr)
            print("1. Get an API key from https://openrouter.ai/keys", file=sys.stderr)
            print("2. Add to your .env file:", file=sys.stderr)
            print("   OPENROUTER_API_KEY=your-key-here", file=sys.stderr)
            print("   # Or set environment variable:", file=sys.stderr)
            print("   export OPENROUTER_API_KEY='your-key-here'", file=sys.stderr)
            print("", file=sys.stderr)
            sys.exit(1)
        return v.strip()
    
    class Config:
        env_file = ".env"
        env_prefix = "TONGYI_"


class ModelRouter:
    """Routes requests between primary and free Tongyi models."""

    def __init__(self, primary_model: str, free_model: Optional[str], free_interval: int) -> None:
        self.primary_model = primary_model.strip()
        self.free_model = free_model.strip() if free_model else None
        self.free_interval = free_interval if free_interval and free_interval > 0 else 0
        self._counter = 0

    def next_model(self) -> str:
        """Return the model to use for the next call, alternating per interval."""
        self._counter += 1
        if self.free_model and self.free_interval and self._counter % self.free_interval == 0:
            return self.free_model
        return self.primary_model

    def reset(self) -> None:
        """Reset the router counter (useful for testing)."""
        self._counter = 0

class ToolConfig(BaseModel):
    """Tool-specific configurations"""
    
    # Search tool
    search_engine: str = "google"
    max_results_per_query: int = 10
    search_safe_level: str = "medium"
    
    # Visit tool
    visit_timeout: int = 15
    max_page_size: int = 1000000  # 1MB
    user_agent: str = "Tongyi-DeepResearch-Agent/1.0"
    
    # Python tool
    python_timeout: int = 30
    python_memory_limit: str = "512M"
    
    # Scholar tool
    max_papers_per_query: int = 20
    scholar_timeout: int = 20
    
    # File Parser tool
    max_file_size: int = 5000000  # 5MB
    supported_formats: list = [
        ".pdf", ".txt", ".md", ".json", ".csv", 
        ".xlsx", ".pptx", ".docx", ".html"
    ]

# Default configurations
DEFAULT_TONGYI_CONFIG = TongyiConfig(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

DEFAULT_TOOL_CONFIG = ToolConfig()

# Default model router for alternating between paid and free models
DEFAULT_MODEL_ROUTER = ModelRouter(
    primary_model=DEFAULT_TONGYI_CONFIG.model_name,
    free_model=DEFAULT_TONGYI_CONFIG.free_model_name,
    free_interval=DEFAULT_TONGYI_CONFIG.free_call_interval,
)

def get_config() -> Dict[str, Any]:
    """Get combined configuration dictionary"""
    return {
        "tongyi": DEFAULT_TONGYI_CONFIG.model_dump(),
        "tools": DEFAULT_TOOL_CONFIG.model_dump()
    }
