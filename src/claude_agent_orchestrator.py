"""
Claude Agent SDK-Powered Orchestrator
Uses Claude Agent SDK as the core reasoning engine with native tool calling.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
    CLAUDE_SDK_AVAILABLE = True

    # Create stub tool decorator since it's not available in current SDK version
    def tool(name, description, params):
        """Stub tool decorator for compatibility."""
        def decorator(func):
            func._tool_name = name
            func._tool_description = description
            func._tool_params = params
            return func
        return decorator

    # Create stub MCP server function since it's not available in current SDK version
    def create_sdk_mcp_server(name, tools):
        """Stub MCP server creator for compatibility."""
        return {
            "name": name,
            "tools": tools,
            "type": "stub",
            "message": "MCP server functionality not available in current SDK version"
        }

    # HookMatcher is not available in the current SDK version
    class HookMatcher:
        """Lightweight compatibility shim for Claude SDK hook matching."""

        def __init__(self, event: Optional[str] = None, *, tool: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None):
            self.event = event
            self.tool = tool
            self.metadata = metadata or {}

        def matches(self, event_name: Optional[str], tool_name: Optional[str] = None) -> bool:
            """Return True when both the event and tool constraints match."""
            if self.event and event_name != self.event:
                return False
            if self.tool and tool_name != self.tool:
                return False
            return True

except ImportError:
    CLAUDE_SDK_AVAILABLE = False
    # Create dummy classes for graceful fallback
    class ClaudeSDKClient:
        def __init__(self, *args, **kwargs):
            raise ImportError("Claude Code SDK not installed. Install with: pip install claude-code-sdk")

    class ClaudeCodeOptions:
        def __init__(self, *args, **kwargs):
            pass

    def tool(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def create_sdk_mcp_server(*args, **kwargs):
        raise ImportError("Claude Code SDK not installed")

    # HookMatcher is not available in the current SDK version
    class HookMatcher:
        """Fallback shim providing minimal matching semantics."""

        def __init__(self, event: Optional[str] = None, *, tool: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None):
            self.event = event
            self.tool = tool
            self.metadata = metadata or {}

        def matches(self, event_name: Optional[str], tool_name: Optional[str] = None) -> bool:
            if self.event and event_name != self.event:
                return False
            if self.tool and tool_name != self.tool:
                return False
            return True

from model_config import DEFAULT_CLAUDE_CONFIG
from delegation_policy import AgentBudget
from orchestrator_base import BaseOrchestrator
from tool_registry import ToolCall, ToolResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClaudeAgentOrchestrator(BaseOrchestrator):
    """Claude Agent SDK-driven orchestrator with native tool calling capabilities."""

    def _initialize_client(self):
        """Initialize Claude SDK client and components."""
        if not CLAUDE_SDK_AVAILABLE:
            raise ImportError("Claude Code SDK is required. Install with: pip install claude-code-sdk")

        # Configure OpenRouter environment for Claude Code SDK
        self._configure_openrouter()

        # MCP server creation disabled temporarily as current SDK version doesn't support it
        # self.tools_server = self._create_tools_server()

    def _configure_openrouter(self):
        """Configure OpenRouter environment variables for Claude Code SDK."""
        # Configure OpenRouter as the backend for Claude Code SDK
        if DEFAULT_CLAUDE_CONFIG.openrouter_api_key:
            # Set OpenRouter API key as ANTHROPIC_API_KEY for Claude SDK
            os.environ["ANTHROPIC_API_KEY"] = DEFAULT_CLAUDE_CONFIG.openrouter_api_key
            logger.info("Configured Claude Code SDK to use OpenRouter API key")

            # Set OpenRouter base URL as ANTHROPIC_BASE_URL for Claude SDK
            if hasattr(DEFAULT_CLAUDE_CONFIG, 'openrouter_base_url') and DEFAULT_CLAUDE_CONFIG.openrouter_base_url:
                os.environ["ANTHROPIC_BASE_URL"] = DEFAULT_CLAUDE_CONFIG.openrouter_base_url
                logger.info(f"Configured Claude Code SDK to use OpenRouter base URL: {DEFAULT_CLAUDE_CONFIG.openrouter_base_url}")

            # Clear any conflicting environment variables that might interfere
            conflicting_vars = ["OPENAI_API_KEY", "OPENAI_BASE_URL"]
            for var in conflicting_vars:
                if var in os.environ:
                    del os.environ[var]
                    logger.info(f"Removed conflicting environment variable: {var}")
        else:
            logger.warning("OpenRouter API key not configured - Claude Code SDK may not work properly")

        # System prompt adapted for Claude Agent SDK
        self.system_prompt = """You are Tongyi Agent, a research-grade AI assistant powered by Claude Agent SDK with tool-augmented reasoning capabilities.

Your environment includes an isolated sandbox, local search capabilities, data cleaning utilities, and access to external academic sources when necessary.

ROLE: Operate as the primary reasoning core for Tongyi Agent. Plan, call tools, interpret their outputs, and synthesize verified, coherent results using Claude's native tool calling.

OBJECTIVE: Maximize utility and precision in all reasoning tasks by:
1. Preferring local information first (project files, markdowns, CSVs)
2. Using external tools (Scholar) only if local context is insufficient
3. Maintaining source-cited, auditable outputs
4. Following strict safety and budget limits per tool

REASONING POLICY:
1. Local-first retrieval: Always begin by searching or reading local files. Avoid external data unless explicitly necessary.
2. Structured reasoning: Break down user requests into subgoals. Select the best combination of tools to satisfy each subgoal.
3. Tool invocation discipline: Each tool call must include only relevant parameters. Always capture tool output before reasoning forward.
4. Verification: Include citations or reference origins for any factual claim. Verify all generated content before presenting the final answer.
5. Failure recovery: If a tool call fails, retry with adjusted parameters or use an alternative. Never hallucinate tool outputs.
6. Completion: End the loop only when confident that all relevant tools have been used, the output is logically consistent, and sources are cited or verified.

Tool usage rules:
- Use search_code and read_file FIRST to explore local information
- Only use search_papers when local information is insufficient
- Use run_sandbox for calculations, data processing, or analysis
- Use clean_csv/clean_markdown when explicitly asked to process data files
- Execute one tool at a time, analyze results, then decide next action
- Always cite sources using file paths for local content and DOIs/URLs for papers
- Native Claude tool calling is available - use it directly

Response format:
- Use Claude's native tool calling for all tool operations
- Provide clear, structured responses with proper citations
- Never fabricate tool outputs. Never guess when verifiable data can be retrieved.
- Terminate the reasoning loop only after all necessary information is gathered and verified."""

        # Initialize Claude Code SDK client with OpenRouter configuration
        # Try minimal configuration first to debug the issue
        try:
            self.options = ClaudeCodeOptions(
                allowed_tools=["Read", "Write", "Bash"],
                permission_mode="acceptEdits",  # Use simple permission mode
                model="claude-3-5-sonnet-20241022",  # Try standard Claude model name
                max_turns=10  # Reduce turns for testing
            )
            logger.info("Claude SDK options configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Claude SDK options: {e}")
            # Try even simpler configuration
            self.options = ClaudeCodeOptions()
            logger.info("Using minimal Claude SDK configuration")

        try:
            self.client = ClaudeSDKClient(self.options)
            logger.info("Claude SDK client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Claude SDK client: {e}")
            raise

        # Track session state
        self.conversation_history = []
        self.tool_usage_stats = defaultdict(int)
        self.session_start_time = time.time()

    async def process_query(self, query: str) -> str:
        """Process a user query using Claude Agent SDK."""
        try:
            logger.info("Attempting to connect to Claude SDK client...")
            # Add connection timeout
            await asyncio.wait_for(self.client.connect(), timeout=30.0)
            logger.info("Successfully connected to Claude SDK")

            # Send query to Claude with timeout
            logger.info(f"Sending query: {query[:50]}...")
            await asyncio.wait_for(self.client.query(query), timeout=30.0)
            logger.info("Query sent successfully")

            # Collect response with timeout and cancellation handling
            response_parts = []
            try:
                logger.info("Starting to collect response from Claude SDK...")
                # Use asyncio.wait_for to add timeout to the entire response collection
                response_coroutine = self._collect_response()
                response_parts = await asyncio.wait_for(response_coroutine, timeout=120.0)
                logger.info(f"Collected {len(response_parts)} response parts")
            except asyncio.TimeoutError:
                logger.error("Response collection timed out after 120 seconds")
                raise asyncio.TimeoutError("Claude SDK response collection timed out after 120 seconds")
            except asyncio.CancelledError:
                logger.error("Response collection was cancelled")
                # Clean up client connection if needed
                try:
                    if hasattr(self.client, 'is_connected') and self.client.is_connected:
                        await self.client.disconnect()
                except Exception:
                    pass  # Ignore cleanup errors
                return "Error: Query processing was cancelled. Please try again."

            final_response = ''.join(response_parts)

            # Store in conversation history
            self.conversation_history.append({
                'type': 'user_query',
                'content': query,
                'timestamp': time.time()
            })
            self.conversation_history.append({
                'type': 'assistant_response',
                'content': final_response,
                'timestamp': time.time()
            })

            # Disconnect with timeout
            try:
                await asyncio.wait_for(self.client.disconnect(), timeout=10.0)
                logger.info("Successfully disconnected from Claude SDK")
            except asyncio.TimeoutError:
                logger.warning("Disconnect timed out, but this is not critical")

            return final_response

        except asyncio.CancelledError:
            logger.error("Query processing was cancelled")
            # Clean up client connection if needed
            try:
                if hasattr(self.client, 'is_connected') and self.client.is_connected:
                    await self.client.disconnect()
            except Exception:
                pass  # Ignore cleanup errors
            raise  # Re-raise to trigger fallback
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            if hasattr(self.client, 'is_connected') and self.client.is_connected:
                await self.client.disconnect()
            raise  # Re-raise to trigger fallback instead of returning error string

    async def _collect_response(self):
        """Helper method to collect response from Claude SDK."""
        response_parts = []
        message_count = 0
        logger.info("Starting to iterate through receive_response()...")

        try:
            async for message in self.client.receive_response():
                message_count += 1
                logger.info(f"Received message #{message_count}: {type(message)} - {message}")

                if hasattr(message, 'content'):
                    logger.info(f"Message has content with {len(message.content)} blocks")
                    for i, block in enumerate(message.content):
                        logger.info(f"Block #{i}: {type(block)} - {block}")
                        if hasattr(block, 'text'):
                            response_parts.append(block.text)
                            logger.info(f"Received text block: {block.text[:50]}...")
                        elif hasattr(block, 'tool_use'):
                            # Tool calls are handled automatically by Claude SDK
                            logger.info(f"Tool called: {block.tool_use.get('name', 'unknown')}")
                else:
                    logger.info(f"Message has no content attribute")

                # Safety break to prevent infinite loops
                if message_count > 10:
                    logger.warning("Received too many messages, breaking to prevent infinite loop")
                    break

        except Exception as e:
            logger.error(f"Error in _collect_response: {e}")
            raise

        logger.info(f"Finished collecting {len(response_parts)} response parts from {message_count} messages")
        return response_parts

    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        session_duration = time.time() - self.session_start_time

        return {
            'session_duration': session_duration,
            'total_tool_calls': sum(self.tool_usage_stats.values()),
            'tool_usage': dict(self.tool_usage_stats),
            'conversation_turns': len([h for h in self.conversation_history if h['type'] == 'user_query']),
            'messages_exchanged': len(self.conversation_history)
        }

    def reset_session(self):
        """Reset the session state."""
        self.conversation_history.clear()
        self.tool_usage_stats.clear()
        self.session_start_time = time.time()
        logger.info("Session reset")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if hasattr(self.client, 'is_connected') and self.client.is_connected:
            await self.client.disconnect()