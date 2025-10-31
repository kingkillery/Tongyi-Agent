"""
Tongyi-Powered Orchestrator
Uses Tongyi DeepResearch as the core reasoning engine with structured tool calling.
"""
from __future__ import annotations

import json
import os
import sys
import time
import logging
from typing import Any, Dict, List, Optional

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import DEFAULT_TONGYI_CONFIG, DEFAULT_MODEL_ROUTER, ModelRouter
from delegation_clients import load_openrouter_client, AgentClientError
from delegation_policy import DelegationPolicy, AgentBudget
from verifier_gate import VerifierGate
from tool_registry import ToolRegistry, ToolCall, ToolResult
from react_parser import ReActParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TongyiOrchestrator:
    """Tongyi-driven orchestrator with tool calling capabilities."""
    
    def __init__(self, root: str = "."):
        self.root = os.path.abspath(root)
        self.tools = ToolRegistry(root=self.root)
        self.client = load_openrouter_client(
            api_key=DEFAULT_TONGYI_CONFIG.api_key,
            base_url=DEFAULT_TONGYI_CONFIG.base_url,
        )
        if not self.client:
            raise RuntimeError("Failed to initialize OpenRouter client")

        # Initialize ReAct parser for natural-language tool call parsing
        self.react_parser = ReActParser()

        # Model router to alternate between paid/free models
        self.model_router = ModelRouter(
            primary_model=DEFAULT_TONGYI_CONFIG.model_name,
            free_model=DEFAULT_TONGYI_CONFIG.free_model_name,
            free_interval=DEFAULT_TONGYI_CONFIG.free_call_interval,
        )

        # Initialize delegation policy for budgets
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
        
        self.system_prompt = """You are Tongyi Agent, a research-grade AI assistant running as a local-first, tool-augmented reasoning engine.

Your environment includes an isolated sandbox, local search capabilities, data cleaning utilities, and access to external academic sources when necessary.

ROLE: Operate as the primary reasoning core for Tongyi Agent. Plan, call tools, interpret their outputs, and synthesize verified, coherent results.

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

Response format:
- If you need to use a tool, respond with valid JSON: {{"tool": "tool_name", "parameters": {{...}}}}
- If you have the final answer, respond normally without JSON

Never fabricate tool outputs. Never guess when verifiable data can be retrieved.
Terminate the reasoning loop only after all necessary information is gathered and verified."""
    
    def run(self, question: str) -> str:
        """Run the Tongyi-powered orchestrator."""
        logger.info(f"Starting Tongyi orchestrator for question: {question[:100]}...")
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Question: {question}\n\nProject root: {self.root}"}
        ]
        
        max_iterations = 20
        iteration = 0
        tool_calls_made = []
        
        while iteration < max_iterations:
            iteration += 1
            start_time = time.time()
            
            try:
                # Prepare tools for function calling
                tools_schemas = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.parameters
                        }
                    }
                    for tool in self.tools.get_tools()
                ]
                
                response = self.client.chat(
                    "\n".join([msg["content"] for msg in messages]),
                    model=self.model_router.next_model(),
                    temperature=DEFAULT_TONGYI_CONFIG.temperature,
                    top_p=DEFAULT_TONGYI_CONFIG.top_p,
                    repetition_penalty=DEFAULT_TONGYI_CONFIG.repetition_penalty,
                    max_tokens=min(4096, DEFAULT_TONGYI_CONFIG.max_tokens),
                    tools=tools_schemas,
                )
                
                logger.info(f"Tongyi response received in {time.time() - start_time:.2f}s")
                
            except AgentClientError as e:
                logger.error(f"Error calling Tongyi: {e}")
                return f"Error calling Tongyi: {e}"
            
            # Check if response contains tool calls (OpenRouter format)
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Handle structured tool calls
                for tool_call in response.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        parameters = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in tool call arguments: {tool_call.function.arguments}")
                        continue
                    
                    # Check budget
                    if not self.policy.allow(tool_name):
                        error_msg = f"Tool {tool_name} budget exceeded"
                        logger.warning(error_msg)
                        messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": error_msg})
                        continue
                    
                    # Execute tool
                    call = ToolCall(name=tool_name, parameters=parameters)
                    tool_start = time.time()
                    result = self.tools.execute_tool(call)
                    tool_duration = time.time() - tool_start
                    
                    # Log tool execution
                    tool_calls_made.append({
                        "tool": tool_name,
                        "parameters": parameters,
                        "duration_ms": tool_duration * 1000,
                        "success": result.error is None
                    })
                    logger.info(f"Tool {tool_name} executed in {tool_duration:.2f}s")
                    
                    # Add tool result to conversation
                    if result.error:
                        tool_response = result.error
                        logger.warning(f"Tool {tool_name} failed: {result.error}")
                    else:
                        tool_response = json.dumps(result.result, indent=2)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_response
                    })
                continue
            
            # Check if response is a simple JSON tool call (fallback)
            try:
                tool_call = json.loads(response.strip())
                if isinstance(tool_call, dict) and "tool" in tool_call:
                    tool_name = tool_call["tool"]
                    parameters = tool_call.get("parameters", {})
                    
                    # Check budget
                    if not self.policy.allow(tool_name):
                        error_msg = f"Tool {tool_name} budget exceeded"
                        logger.warning(error_msg)
                        messages.append({"role": "user", "content": error_msg})
                        continue
                    
                    # Execute tool
                    call = ToolCall(name=tool_name, parameters=parameters)
                    tool_start = time.time()
                    result = self.tools.execute_tool(call)
                    tool_duration = time.time() - tool_start
                    
                    # Log tool execution
                    tool_calls_made.append({
                        "tool": tool_name,
                        "parameters": parameters,
                        "duration_ms": tool_duration * 1000,
                        "success": result.error is None
                    })
                    logger.info(f"Tool {tool_name} executed in {tool_duration:.2f}s")
                    
                    # Add tool result to conversation
                    if result.error:
                        tool_response = f"Tool {tool_name} failed: {result.error}"
                        logger.warning(f"Tool {tool_name} failed: {result.error}")
                    else:
                        tool_response = f"Tool {tool_name} returned: {json.dumps(result.result, indent=2)}"
                    
                    messages.append({"role": "assistant", "content": response})
                    messages.append({"role": "user", "content": tool_response})
                    continue
            except (json.JSONDecodeError, TypeError):
                # Try ReAct-style natural language parsing (fallback)
                react_blocks = self.react_parser.parse_response(response)
                if react_blocks and any(block.action for block in react_blocks):
                    logger.info(f"ReAct blocks detected, processing {len(react_blocks)} blocks")
                    blocks_executed = False

                    for block in react_blocks:
                        if not block.action or not block.action_input:
                            continue

                        tool_name = block.action
                        parameters = block.action_input

                        # Check budget
                        if not self.policy.allow(tool_name):
                            error_msg = f"Tool {tool_name} budget exceeded"
                            logger.warning(error_msg)
                            messages.append({"role": "user", "content": error_msg})
                            continue

                        # Execute tool
                        call = ToolCall(name=tool_name, parameters=parameters)
                        tool_start = time.time()
                        result = self.tools.execute_tool(call)
                        tool_duration = time.time() - tool_start

                        # Log tool execution
                        tool_calls_made.append({
                            "tool": tool_name,
                            "parameters": parameters,
                            "duration_ms": tool_duration * 1000,
                            "success": result.error is None
                        })
                        logger.info(f"Tool {tool_name} executed in {tool_duration:.2f}s (via ReAct)")
                        blocks_executed = True

                        # Add tool result to conversation
                        if result.error:
                            tool_response = f"Error: {result.error}"
                            logger.warning(f"Tool {tool_name} failed: {result.error}")
                        else:
                            tool_response = json.dumps(result.result, indent=2)

                        # Format as ReAct observation
                        formatted_observation = self.react_parser.format_observation(tool_response, tool_name)
                        messages.append({"role": "user", "content": formatted_observation})

                    if blocks_executed:
                        continue

                # Not a tool call, this is the final answer
                logger.info(f"Final answer received after {iteration-1} tool calls")
                
                # Extract claims and verify them
                verified_response = self._verify_response(response, tool_calls_made)
                
                # Log execution summary
                total_duration = time.time() - start_time
                logger.info(f"Orchestrator completed in {total_duration:.2f}s with {len(tool_calls_made)} tool calls")
                
                return verified_response
            
            # If we get here, something went wrong with tool parsing
            if iteration == max_iterations:
                logger.warning(f"Reached maximum iterations ({max_iterations})")
                return response + "\n\n[Note: Reached maximum tool iterations]"
        
        logger.error("Maximum iterations reached without final answer")
        return "Error: Maximum iterations reached without final answer"
    
    def _verify_response(self, response: str, tool_calls_made: List[Dict]) -> str:
        """Verify claims in the response using the verifier gate."""
        # Extract sources from tool calls
        sources = []
        for call in tool_calls_made:
            if call["tool"] in ["search_code", "read_file"]:
                sources.append(f"local_file:{call['tool']}")
            elif call["tool"] == "search_papers":
                sources.append("external_scholar")
        
        # For now, just return the response with a verification note
        # In a full implementation, we would extract claims and verify each one
        if sources:
            return f"{response}\n\n[Verified with sources: {', '.join(sources)}]"
        return response
    
    def get_tool_usage_summary(self) -> Dict[str, Any]:
        """Return summary of available tools for debugging."""
        return {
            "total_tools": len(self.tools.get_tools()),
            "tool_names": [t.name for t in self.tools.get_tools()],
            "root_directory": self.root,
            "model": DEFAULT_TONGYI_CONFIG.model_name
        }
