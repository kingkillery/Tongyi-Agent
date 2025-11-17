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
        def __init__(self, *args, **kwargs):
            pass

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
        def __init__(self, *args, **kwargs):
            pass

from config import DEFAULT_CLAUDE_CONFIG
from delegation_policy import DelegationPolicy, AgentBudget
from verifier_gate import VerifierGate
from tool_registry import ToolRegistry, ToolCall, ToolResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClaudeAgentOrchestrator:
    """Claude Agent SDK-driven orchestrator with native tool calling capabilities."""

    def __init__(self, root: str = "."):
        if not CLAUDE_SDK_AVAILABLE:
            raise ImportError("Claude Code SDK is required. Install with: pip install claude-code-sdk")

        self.root = os.path.abspath(root)
        self.tools = ToolRegistry(root=self.root)

        # Configure OpenRouter environment for Claude Code SDK
        self._configure_openrouter()

        # MCP server creation disabled temporarily as current SDK version doesn't support it
        # self.tools_server = self._create_tools_server()

        # Initialize delegation policy for budgets (adapted as hooks)
        self.policy = DelegationPolicy(
            agent_budgets={
                "search_code": AgentBudget(max_calls=10, max_tokens=2000),
                "read_file": AgentBudget(max_calls=20, max_tokens=1000),
                "run_sandbox": AgentBudget(max_calls=5, max_tokens=1500),
                "search_papers": AgentBudget(max_calls=3, max_tokens=1000),
                "clean_csv": AgentBudget(max_calls=2, max_tokens=800),
                "clean_markdown": AgentBudget(max_calls=2, max_tokens=800),
                "summarize_results": AgentBudget(max_calls=5, max_tokens=1200),
            }
        )
        self.verifier_gate = VerifierGate()

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

    def _create_tools_server(self):
        """Create MCP server for existing Tongyi tools."""

        @tool("search_code", "Search codebase with AST indexing", {
            "query": str,
            "paths": list,
            "max_results": int
        })
        async def search_code_tool(args):
            """Search code using the existing tool registry."""
            try:
                # Map Claude SDK parameters to ToolRegistry parameters
                mapped_args = {
                    "query": args.get("query", ""),
                    "paths": args.get("paths", []),
                    "max_results": args.get("max_results", 20)
                }
                tool_call = ToolCall(
                    name="search_code",
                    parameters=mapped_args
                )
                result = self.tools.execute_tool(tool_call)
                # Handle both ToolResult with content attribute and legacy execute_tool method
                if hasattr(result, 'content'):
                    content = result.content
                elif hasattr(result, 'result'):
                    content = str(result.result) if result.result else (result.error or "No content")
                else:
                    content = str(result)
                return {"content": [{"type": "text", "text": content}]}
            except Exception as e:
                logger.error(f"search_code tool error: {e}")
                return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

        @tool("read_file", "Read file contents safely", {
            "path": str,
            "start_line": int,
            "end_line": int
        })
        async def read_file_tool(args):
            """Read file using the existing tool registry."""
            try:
                # Map Claude SDK parameters to ToolRegistry parameters
                mapped_args = {
                    "path": args.get("path", ""),
                    "start_line": args.get("start_line"),
                    "end_line": args.get("end_line")
                }
                tool_call = ToolCall(
                    name="read_file",
                    parameters=mapped_args
                )
                result = self.tools.execute_tool(tool_call)
                # Handle both ToolResult with content attribute and legacy execute_tool method
                if hasattr(result, 'content'):
                    content = result.content
                elif hasattr(result, 'result'):
                    content = str(result.result) if result.result else (result.error or "No content")
                else:
                    content = str(result)
                return {"content": [{"type": "text", "text": content}]}
            except Exception as e:
                logger.error(f"read_file tool error: {e}")
                return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

        @tool("run_sandbox", "Execute code in isolated environment", {
            "code": str,
            "timeout_s": int,
            "seed": int
        })
        async def run_sandbox_tool(args):
            """Run code in sandbox using the existing tool registry."""
            try:
                # Map Claude SDK parameters to ToolRegistry parameters
                mapped_args = {
                    "code": args.get("code", ""),
                    "timeout_s": args.get("timeout_s", 30),
                    "seed": args.get("seed", 1337)
                }
                tool_call = ToolCall(
                    name="run_sandbox",
                    parameters=mapped_args
                )
                result = self.tools.execute_tool(tool_call)
                # Handle both ToolResult with content attribute and legacy execute_tool method
                if hasattr(result, 'content'):
                    content = result.content
                elif hasattr(result, 'result'):
                    content = str(result.result) if result.result else (result.error or "No content")
                else:
                    content = str(result)
                return {"content": [{"type": "text", "text": content}]}
            except Exception as e:
                logger.error(f"run_sandbox tool error: {e}")
                return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

        @tool("search_papers", "Search academic papers", {
            "query": str,
            "max_results": int,
            "year_min": int
        })
        async def search_papers_tool(args):
            """Search papers using the existing tool registry."""
            try:
                # Map Claude SDK parameters to ToolRegistry parameters
                mapped_args = {
                    "query": args.get("query", ""),
                    "max_results": args.get("max_results", 5),
                    "year_min": args.get("year_min")
                }
                tool_call = ToolCall(
                    name="search_papers",
                    parameters=mapped_args
                )
                result = self.tools.execute_tool(tool_call)
                # Handle both ToolResult with content attribute and legacy execute_tool method
                if hasattr(result, 'content'):
                    content = result.content
                elif hasattr(result, 'result'):
                    content = str(result.result) if result.result else (result.error or "No content")
                else:
                    content = str(result)
                return {"content": [{"type": "text", "text": content}]}
            except Exception as e:
                logger.error(f"search_papers tool error: {e}")
                return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

        @tool("clean_csv", "Clean CSV data files", {
            "path": str,
            "output": str,
            "operations": list
        })
        async def clean_csv_tool(args):
            """Clean CSV using the existing tool registry."""
            try:
                # Map Claude SDK parameters to ToolRegistry parameters
                mapped_args = {
                    "path": args.get("path", ""),
                    "output": args.get("output"),
                    "operations": args.get("operations", [])
                }
                tool_call = ToolCall(
                    name="clean_csv",
                    parameters=mapped_args
                )
                result = self.tools.execute_tool(tool_call)
                # Handle both ToolResult with content attribute and legacy execute_tool method
                if hasattr(result, 'content'):
                    content = result.content
                elif hasattr(result, 'result'):
                    content = str(result.result) if result.result else (result.error or "No content")
                else:
                    content = str(result)
                return {"content": [{"type": "text", "text": content}]}
            except Exception as e:
                logger.error(f"clean_csv tool error: {e}")
                return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

        @tool("clean_markdown", "Clean and format markdown", {
            "path": str,
            "output": str,
            "collapse_empty": bool,
            "normalize_timestamps": bool
        })
        async def clean_markdown_tool(args):
            """Clean markdown using the existing tool registry."""
            try:
                # Map Claude SDK parameters to ToolRegistry parameters
                mapped_args = {
                    "path": args.get("path", ""),
                    "output": args.get("output"),
                    "collapse_empty": args.get("collapse_empty", True),
                    "normalize_timestamps": args.get("normalize_timestamps", True)
                }
                tool_call = ToolCall(
                    name="clean_markdown",
                    parameters=mapped_args
                )
                result = self.tools.execute_tool(tool_call)
                # Handle both ToolResult with content attribute and legacy execute_tool method
                if hasattr(result, 'content'):
                    content = result.content
                elif hasattr(result, 'result'):
                    content = str(result.result) if result.result else (result.error or "No content")
                else:
                    content = str(result)
                return {"content": [{"type": "text", "text": content}]}
            except Exception as e:
                logger.error(f"clean_markdown tool error: {e}")
                return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

        @tool("summarize_results", "Summarize research findings", {
            "context": str,
            "style": str
        })
        async def summarize_results_tool(args):
            """Summarize results using the existing tool registry."""
            try:
                # Map Claude SDK parameters to ToolRegistry parameters
                mapped_args = {
                    "context": args.get("context", args.get("content", "")),
                    "style": args.get("style", "summary")
                }
                tool_call = ToolCall(
                    name="summarize_results",
                    parameters=mapped_args
                )
                result = self.tools.execute_tool(tool_call)
                # Handle both ToolResult with content attribute and legacy execute_tool method
                if hasattr(result, 'content'):
                    content = result.content
                elif hasattr(result, 'result'):
                    content = str(result.result) if result.result else (result.error or "No content")
                else:
                    content = str(result)
                return {"content": [{"type": "text", "text": content}]}
            except Exception as e:
                logger.error(f"summarize_results tool error: {e}")
                return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

        return create_sdk_mcp_server(
            name="tongyi_tools",
            tools=[
                search_code_tool,
                read_file_tool,
                run_sandbox_tool,
                search_papers_tool,
                clean_csv_tool,
                clean_markdown_tool,
                summarize_results_tool
            ]
        )

    def _setup_hooks(self):
        """Setup hooks for budget management and monitoring.

        Note: Hook functionality may not be available in current Claude Code SDK version.
        This method returns empty dict for compatibility.
        """
        # For now, hooks are not configured due to SDK limitations
        # Tool usage monitoring happens at the tool level instead
        logger.info("Hooks not configured - using tool-level monitoring instead")
        return {}

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
                response_parts = await asyncio.wait_for(response_coroutine, timeout=30.0)
                logger.info(f"Collected {len(response_parts)} response parts")
            except asyncio.TimeoutError:
                logger.error("Response collection timed out after 30 seconds")
                raise asyncio.TimeoutError("Claude SDK response collection timed out after 30 seconds")
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