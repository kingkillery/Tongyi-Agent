"""
Configuration for Tongyi Agent
Supports both Tongyi DeepResearch and Claude Agent SDK backends
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, field_validator, ConfigDict
import os
import sys
import configparser
from dotenv import load_dotenv

load_dotenv()

def load_models_config():
    """Load model configuration from models.ini file if it exists"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'models.ini')

    if os.path.exists(config_path):
        config.read(config_path)
        return config
    return None

MODELS_CONFIG = load_models_config()

class TongyiConfig(BaseModel):
    """Tongyi DeepResearch model configuration"""
    
    model_config = ConfigDict(env_file=".env", env_prefix="TONGYI_", extra="ignore")
    
    # Model parameters - easily overrideable with environment variables
    model_name: str = "alibaba/tongyi-deepresearch-30b-a3b"  # Use paid version
    free_model_name: str = "openrouter/sherlock-think-alpha"  # Use Sherlock Think Alpha model
    free_call_interval: int = 3  # Use free tier every Nth call
    api_key: str
    base_url: Optional[str] = None

    @field_validator('model_name')
    @classmethod
    def validate_model_name(cls, v, info):
        """Allow model override via environment variable or models.ini"""
        # Priority: CLI env var > models.ini > default
        env_model = os.getenv("TONGYI_MODEL_OVERRIDE") or os.getenv("MODEL_OVERRIDE")
        if env_model:
            return env_model

        if MODELS_CONFIG and MODELS_CONFIG.has_option('models', 'primary'):
            return MODELS_CONFIG.get('models', 'primary')

        return v

    @field_validator('free_model_name')
    @classmethod
    def validate_free_model_name(cls, v, info):
        """Allow free model override via environment variable or models.ini"""
        # Priority: CLI env var > models.ini > default
        env_free_model = os.getenv("TONGYI_FREE_MODEL_OVERRIDE") or os.getenv("FREE_MODEL_OVERRIDE")
        if env_free_model:
            return env_free_model

        if MODELS_CONFIG and MODELS_CONFIG.has_option('models', 'fallback'):
            return MODELS_CONFIG.get('models', 'fallback')

        return v

    @field_validator('free_call_interval')
    @classmethod
    def validate_free_call_interval(cls, v, info):
        """Allow fallback interval override via models.ini"""
        if MODELS_CONFIG and MODELS_CONFIG.has_option('models', 'fallback_interval'):
            try:
                return int(MODELS_CONFIG.get('models', 'fallback_interval'))
            except ValueError:
                pass
        return v
    
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
    
    model_config = ConfigDict(extra="ignore")
    
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
    base_url="https://openrouter.ai/api/v1",
    free_call_interval=3  # Use free tier every 3rd call
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
        "claude": DEFAULT_CLAUDE_CONFIG.model_dump(),
        "tools": DEFAULT_TOOL_CONFIG.model_dump()
    }


class ModelConfig(BaseModel):
    """Model configuration for easy switching"""

    name: str
    display_name: str
    provider: str
    context_length: int
    pricing_per_mtok: Optional[float] = None
    capabilities: list[str] = []

class OpenRouterModels:
    """Registry of available OpenRouter models"""

    # Popular Claude models
    CLAUDE_35_SONNET = ModelConfig(
        name="anthropic/claude-3.5-sonnet",
        display_name="Claude 3.5 Sonnet",
        provider="Anthropic",
        context_length=200000,
        pricing_per_mtok=3.0,
        capabilities=["tool-calling", "coding", "reasoning", "long-context"]
    )

    CLAUDE_35_HAIKU = ModelConfig(
        name="anthropic/claude-3.5-haiku",
        display_name="Claude 3.5 Haiku",
        provider="Anthropic",
        context_length=200000,
        pricing_per_mtok=0.8,
        capabilities=["tool-calling", "fast", "coding"]
    )

    CLAUDE_3_OPUS = ModelConfig(
        name="anthropic/claude-3-opus",
        display_name="Claude 3 Opus",
        provider="Anthropic",
        context_length=200000,
        pricing_per_mtok=15.0,
        capabilities=["reasoning", "analysis", "complex-tasks"]
    )

    CLAUDE_3_SONNET = ModelConfig(
        name="anthropic/claude-3-sonnet",
        display_name="Claude 3 Sonnet",
        provider="Anthropic",
        context_length=200000,
        pricing_per_mtok=3.0,
        capabilities=["balanced", "tool-calling"]
    )

    CLAUDE_3_HAIKU = ModelConfig(
        name="anthropic/claude-3-haiku",
        display_name="Claude 3 Haiku",
        provider="Anthropic",
        context_length=200000,
        pricing_per_mtok=0.25,
        capabilities=["fast", "simple-tasks"]
    )

    # Open source models
    MISTRAL_LARGE = ModelConfig(
        name="mistralai/mistral-large",
        display_name="Mistral Large",
        provider="Mistral",
        context_length=32000,
        pricing_per_mtok=2.0,
        capabilities=["coding", "reasoning", "multilingual"]
    )

    MISTRRAL_CODESTRAL = ModelConfig(
        name="mistralai/codestral",
        display_name="Mistral Codestral",
        provider="Mistral",
        context_length=32000,
        pricing_per_mtok=1.0,
        capabilities=["coding", "code-generation"]
    )

    QWEN_72B = ModelConfig(
        name="qwen/qwen-72b-chat",
        display_name="Qwen-72B Chat",
        provider="Alibaba",
        context_length=32000,
        pricing_per_mtok=0.9,
        capabilities=["coding", "reasoning", "multilingual"]
    )

    @classmethod
    def get_all_models(cls) -> Dict[str, ModelConfig]:
        """Get all available models as a dictionary"""
        return {
            cls.CLAUDE_35_SONNET.name: cls.CLAUDE_35_SONNET,
            cls.CLAUDE_35_HAIKU.name: cls.CLAUDE_35_HAIKU,
            cls.CLAUDE_3_OPUS.name: cls.CLAUDE_3_OPUS,
            cls.CLAUDE_3_SONNET.name: cls.CLAUDE_3_SONNET,
            cls.CLAUDE_3_HAIKU.name: cls.CLAUDE_3_HAIKU,
            cls.MISTRAL_LARGE.name: cls.MISTRAL_LARGE,
            cls.MISTRRAL_CODESTRAL.name: cls.MISTRRAL_CODESTRAL,
            cls.QWEN_72B.name: cls.QWEN_72B,
        }

    @classmethod
    def get_recommended_models(cls) -> List[ModelConfig]:
        """Get recommended models for different use cases"""
        return [
            cls.CLAUDE_35_SONNET,  # Best overall
            cls.CLAUDE_35_HAIKU,   # Fast and cheap
            cls.MISTRRAL_CODESTRAL, # Coding focused
        ]

class ClaudeConfig(BaseModel):
    """Claude Code SDK configuration with OpenRouter backend"""

    model_config = ConfigDict(env_file=".env", env_prefix="CLAUDE_", extra="ignore")

    # Model parameters - configured for OpenRouter
    model_name: str = OpenRouterModels.CLAUDE_35_SONNET.name  # Default to best overall
    api_key: Optional[str] = None

    # OpenRouter configuration
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Model switching configuration
    model_preferences_file: str = "~/.tongyi_agent_models.json"
    save_model_choices: bool = True

    # Inference parameters
    temperature: float = 0.7
    top_p: float = 0.95
    max_tokens: int = 8192

    # Tool and interaction limits
    max_tool_invocations: int = 50
    timeout: int = 120  # seconds

    # Permission and safety
    permission_mode: str = "acceptEdits"  # "acceptEdits", "readOnly", or "prompt"

    # MCP Server configuration
    mcp_server_timeout: int = 30
    enable_tool_logging: bool = True

    # Session management
    max_conversation_history: int = 50
    enable_session_persistence: bool = True

    @field_validator('openrouter_api_key')
    @classmethod
    def validate_openrouter_api_key(cls, v, info):
        # Get the API key from environment if not provided
        if not v:
            v = os.getenv("OPENROUTER_API_KEY")
        if not v:
            print("WARNING: OPENROUTER_API_KEY not configured. Claude Code SDK may not work properly.", file=sys.stderr)
            print("Set OPENROUTER_API_KEY in your .env file or environment variables.", file=sys.stderr)
        return v.strip() if v else None

    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        # For backward compatibility, but we prioritize OpenRouter key
        return v.strip() if v else None


# Default Claude configuration with OpenRouter backend
DEFAULT_CLAUDE_CONFIG = ClaudeConfig(
    api_key=os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY"),
    openrouter_api_key=os.getenv("OPENROUTER_API_KEY")
)
