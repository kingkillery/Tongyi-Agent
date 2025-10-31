"""
ReAct Parser for Tongyi Agent
Parses natural language ReAct blocks and converts them to structured tool calls.
"""
from __future__ import annotations

import json
import re
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class ReActBlock:
    """Represents a single ReAct reasoning block."""
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None


class ReActParser:
    """Parses ReAct-style reasoning blocks from LLM responses."""
    
    def __init__(self):
        # Patterns for different ReAct components
        self.thought_pattern = re.compile(r'Thought:\s*(.*?)(?=\n(?:Action|Action Input|Observation)|$)', re.IGNORECASE | re.DOTALL)
        self.action_pattern = re.compile(r'Action:\s*(.*?)(?=\n(?:Action Input|Observation)|$)', re.IGNORECASE | re.DOTALL)
        self.action_input_pattern = re.compile(r'Action Input:\s*(.*?)(?=\n(?:Observation)|$)', re.IGNORECASE | re.DOTALL)
        self.observation_pattern = re.compile(r'Observation:\s*(.*?)(?=\n(?:Thought|Action)|$)', re.IGNORECASE | re.DOTALL)
        
        # Alternative patterns for more flexible parsing
        self.tool_call_pattern = re.compile(r'```json\s*\{(.*?)\}\s*```', re.DOTALL)
        self.simple_tool_pattern = re.compile(r'\{[^}]*"tool"[^}]*\}', re.DOTALL)
    
    def parse_response(self, response: str) -> List[ReActBlock]:
        """
        Parse a complete response into ReAct blocks.

        Args:
            response: Raw LLM response text

        Returns:
            List of ReActBlock objects
        """
        blocks = []

        # Ensure response is a string (handle Mock objects and other types)
        if not isinstance(response, str):
            return blocks

        # Try to extract structured tool calls first
        tool_calls = self._extract_tool_calls(response)
        if tool_calls:
            # Convert tool calls to ReAct blocks
            for tool_call in tool_calls:
                block = ReActBlock(
                    thought=f"Using tool {tool_call.get('tool', 'unknown')}",
                    action=tool_call.get('tool'),
                    action_input=tool_call.get('parameters', {})
                )
                blocks.append(block)
            return blocks

        # Parse natural language ReAct format
        sections = self._split_sections(response)
        
        for section in sections:
            block = self._parse_section(section)
            if block:
                blocks.append(block)
        
        return blocks
    
    def _extract_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Extract structured tool calls from response."""
        tool_calls = []
        
        # Try JSON code blocks
        json_matches = self.tool_call_pattern.findall(response)
        for match in json_matches:
            try:
                tool_call = json.loads('{' + match + '}')
                if 'tool' in tool_call:
                    tool_calls.append(tool_call)
            except json.JSONDecodeError:
                continue
        
        # Try simple JSON objects
        simple_matches = self.simple_tool_pattern.findall(response)
        for match in simple_matches:
            try:
                tool_call = json.loads(match)
                if 'tool' in tool_call:
                    tool_calls.append(tool_call)
            except json.JSONDecodeError:
                continue
        
        return tool_calls
    
    def _split_sections(self, response: str) -> List[str]:
        """Split response into ReAct sections."""
        # Look for "Thought:" patterns to split sections
        thought_starts = list(self.thought_pattern.finditer(response))
        
        if not thought_starts:
            # No explicit thought sections, treat whole response as one
            return [response]
        
        sections = []
        for i, match in enumerate(thought_starts):
            start = match.start()
            end = thought_starts[i + 1].start() if i + 1 < len(thought_starts) else len(response)
            sections.append(response[start:end])
        
        return sections
    
    def _parse_section(self, section: str) -> Optional[ReActBlock]:
        """Parse a single section into a ReAct block."""
        thought_match = self.thought_pattern.search(section)
        action_match = self.action_pattern.search(section)
        action_input_match = self.action_input_pattern.search(section)
        observation_match = self.observation_pattern.search(section)
        
        thought = thought_match.group(1).strip() if thought_match else ""
        action = action_match.group(1).strip() if action_match else None
        
        # Parse action input
        action_input = None
        if action_input_match:
            action_input_text = action_input_match.group(1).strip()
            action_input = self._parse_action_input(action_input_text)
        
        observation = observation_match.group(1).strip() if observation_match else None
        
        if not thought and not action:
            return None
        
        return ReActBlock(
            thought=thought,
            action=action,
            action_input=action_input,
            observation=observation
        )
    
    def _parse_action_input(self, input_text: str) -> Dict[str, Any]:
        """Parse action input from text."""
        # Try JSON parsing first
        try:
            return json.loads(input_text)
        except json.JSONDecodeError:
            pass
        
        # Try key=value format
        if '=' in input_text:
            result = {}
            for line in input_text.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    result[key.strip()] = value.strip()
            return result
        
        # Treat as single string parameter
        return {"input": input_text}
    
    def has_tool_calls(self, response: str) -> bool:
        """Check if response contains any tool calls."""
        return bool(self._extract_tool_calls(response) or self.action_pattern.search(response))
    
    def extract_final_answer(self, response: str) -> Optional[str]:
        """Extract the final answer from a response (non-tool call content)."""
        if self.has_tool_calls(response):
            # Look for content after the last tool call/observation
            parts = re.split(r'(?:Observation:|```json.*?```)', response, flags=re.IGNORECASE | re.DOTALL)
            if len(parts) > 1:
                final_answer = parts[-1].strip()
                return final_answer if final_answer else None
        
        # Check if this looks like a complete answer
        if not self.has_tool_calls(response) and len(response.strip()) > 20:
            return response.strip()
        
        return None
    
    def format_observation(self, tool_result: str, tool_name: str) -> str:
        """Format tool result as an observation for the next turn."""
        return f"Observation: {tool_name} returned: {tool_result}"


class ReActExecutor:
    """Executes ReAct blocks using available tools."""
    
    def __init__(self, tool_registry):
        self.tool_registry = tool_registry
        self.parser = ReActParser()
        self.conversation_history: List[Dict[str, str]] = []
    
    def execute_react_response(self, response: str) -> Tuple[str, bool]:
        """
        Execute a ReAct response and return the observation.
        
        Args:
            response: LLM response containing ReAct blocks
            
        Returns:
            Tuple of (observation_text, is_final_answer)
        """
        # Check for final answer
        final_answer = self.parser.extract_final_answer(response)
        if final_answer:
            return final_answer, True
        
        # Parse and execute tool calls
        blocks = self.parser.parse_response(response)
        observations = []
        
        for block in blocks:
            if block.action and block.action_input:
                try:
                    # Execute tool call
                    from tool_registry import ToolCall
                    tool_call = ToolCall(name=block.action, parameters=block.action_input)
                    result = self.tool_registry.execute_tool(tool_call)
                    
                    if result.error:
                        observation = f"Error: {result.error}"
                    else:
                        observation = json.dumps(result.result, indent=2)
                    
                    formatted_obs = self.parser.format_observation(observation, block.action)
                    observations.append(formatted_obs)
                    
                except Exception as e:
                    error_obs = f"Error executing {block.action}: {str(e)}"
                    observations.append(error_obs)
        
        return "\n".join(observations) if observations else "No tool calls executed", False


if __name__ == "__main__":
    # Example usage
    parser = ReActParser()
    
    # Test response with different formats
    test_responses = [
        '''Thought: I need to search for information about Python files.
Action: search_code
Action Input: {"query": "python imports", "max_results": 5}''',
        
        '''```json
{"tool": "read_file", "parameters": {"path": "src/main.py"}}
```''',
        
        '''This is the final answer to the user's question about the system architecture.'''
    ]
    
    for i, response in enumerate(test_responses, 1):
        print(f"\n--- Test Response {i} ---")
        print(response)
        
        blocks = parser.parse_response(response)
        print(f"\nParsed {len(blocks)} blocks:")
        for j, block in enumerate(blocks):
            print(f"  Block {j+1}: {block}")
        
        final_answer = parser.extract_final_answer(response)
        print(f"Final answer: {final_answer}")
        
        has_tools = parser.has_tool_calls(response)
        print(f"Has tool calls: {has_tools}")
