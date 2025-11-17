"""
Tool Registry for Tongyi Agent
Provides structured tools with schemas for function calling.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from code_search import CodeSearch
from file_read import read_snippet
from sandbox_exec import run_snippet, ExecResult
from scholar_adapter import ScholarAdapter, PaperMeta
from csv_utils import sniff_csv, suggest_cleaning_steps, clean_csv
from md_utils import parse_markdown, suggest_md_cleaning, clean_markdown


@dataclass
class ToolCall:
    name: str
    parameters: Dict[str, Any]


@dataclass
class ToolResult:
    name: str
    result: Any = None
    error: Optional[str] = None


class ToolSchema(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


class ToolRegistry:
    """Registry of tools available to Tongyi agent."""
    
    def __init__(self, root: str):
        self.root = os.path.abspath(root)
        self.code_search = CodeSearch(root=self.root)
        self.scholar = ScholarAdapter()
    
    def get_tools(self) -> List[ToolSchema]:
        """Return list of available tools with schemas."""
        return [
            ToolSchema(
                name="search_code",
                description="Search source code and documentation for answers or references to a query.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "search terms or natural question"},
                        "paths": {"type": "array", "items": {"type": "string"}, "description": "optional array of strings — specific directories to search"},
                        "max_results": {"type": "integer", "description": "integer — maximum number of results to return (default 20)"}
                    },
                    "required": ["query"]
                }
            ),
            ToolSchema(
                name="read_file",
                description="Read the contents of a file safely in the sandbox (read-only).",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "string — path to the file (relative to workspace)"},
                        "start_line": {"type": "integer", "description": "optional integer — line number to start reading"},
                        "end_line": {"type": "integer", "description": "optional integer — line number to stop reading"}
                    },
                    "required": ["path"]
                }
            ),
            ToolSchema(
                name="run_sandbox",
                description="Execute code safely in an isolated sandbox with read-only mounts and no network access.",
                parameters={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "string — Python code snippet to execute"},
                        "timeout_s": {"type": "integer", "description": "integer — timeout in seconds (default 30)"},
                        "seed": {"type": "integer", "description": "optional integer — deterministic seed for reproducibility"}
                    },
                    "required": ["code"]
                }
            ),
            ToolSchema(
                name="search_papers",
                description="Search academic papers from Semantic Scholar, Crossref, arXiv, and OpenAlex.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "string — keywords or natural question"},
                        "max_results": {"type": "integer", "description": "integer — number of results (default 5)"},
                        "year_min": {"type": "integer", "description": "optional integer — minimum publication year"}
                    },
                    "required": ["query"]
                }
            ),
            ToolSchema(
                name="clean_csv",
                description="Clean and normalize a CSV dataset safely in the sandbox.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "string — input CSV path"},
                        "output": {"type": "string", "description": "optional string — output path (default adds _cleaned suffix)"},
                        "operations": {"type": "array", "items": {"type": "string"}, "description": "optional array — list of cleaning operations (fill_nulls, normalize, validate)"}
                    },
                    "required": ["path"]
                }
            ),
            ToolSchema(
                name="clean_markdown",
                description="Clean and structure a markdown document by normalizing sections and deduplicating entries.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "string — input markdown path"},
                        "output": {"type": "string", "description": "optional string — output path (default adds _cleaned suffix)"},
                        "collapse_empty": {"type": "boolean", "description": "optional boolean — remove empty sections"},
                        "normalize_timestamps": {"type": "boolean", "description": "optional boolean — unify timestamps in notes"}
                    },
                    "required": ["path"]
                }
            ),
            ToolSchema(
                name="summarize_results",
                description="Summarize tool outputs and synthesize final answer with proper citations.",
                parameters={
                    "type": "object",
                    "properties": {
                        "context": {"type": "string", "description": "string — concatenated tool results"},
                        "style": {"type": "string", "description": "optional string — tone or output format (summary, report, json, markdown)"}
                    },
                    "required": ["context"]
                }
            )
        ]
    
    def execute_tool(self, call: ToolCall) -> ToolResult:
        """Execute a tool call and return the result."""
        try:
            if call.name == "search_code":
                raw_query = call.parameters["query"]
                if isinstance(raw_query, str):
                    query = raw_query
                elif isinstance(raw_query, (list, tuple)):
                    query = " ".join(str(item) for item in raw_query)
                else:
                    query = str(raw_query)
                paths = call.parameters.get("paths", [])
                max_results = call.parameters.get("max_results", 20)
                results = self.code_search.search(query, paths=paths, max_results=max_results)
                serializable_results = [asdict(hit) for hit in results]
                return ToolResult(name=call.name, result=serializable_results)
            
            elif call.name == "read_file":
                path = call.parameters["path"]
                full_path = os.path.join(self.root, path)
                if not os.path.exists(full_path):
                    return ToolResult(name=call.name, error=f"File not found: {path}")
                start_line = call.parameters.get("start_line")
                end_line = call.parameters.get("end_line")
                content = read_snippet(full_path, start=start_line, end=end_line)
                return ToolResult(name=call.name, result=asdict(content))
            
            elif call.name == "run_sandbox":
                code = call.parameters["code"]
                timeout_s = call.parameters.get("timeout_s", 30)
                seed = call.parameters.get("seed", 1337)
                result = run_snippet(code, timeout_s=timeout_s, seed=seed, base_dir=self.root)
                return ToolResult(name=call.name, result={
                    "ok": result.ok,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "duration_ms": result.duration_ms
                })
            
            elif call.name == "search_papers":
                query = call.parameters["query"]
                max_results = call.parameters.get("max_results", 5)
                year_min = call.parameters.get("year_min")
                papers = self.scholar.search(query, k=max_results)
                # Filter by year if specified
                if year_min:
                    papers = [p for p in papers if p.year and p.year >= year_min]
                # Format papers for response
                formatted = []
                for p in papers:
                    formatted.append({
                        "title": p.title,
                        "authors": p.authors[:3],
                        "venue": p.venue,
                        "year": p.year,
                        "abstract": p.abstract,
                        "doi": p.doi,
                        "url": p.url,
                        "source": p.source
                    })
                return ToolResult(name=call.name, result=formatted)
            
            elif call.name == "clean_csv":
                path = call.parameters["path"]
                output = call.parameters.get("output")
                if not output:
                    output = path.replace(".csv", "_cleaned.csv")
                full_input = os.path.join(self.root, path)
                full_output = os.path.join(self.root, output)
                if not os.path.exists(full_input):
                    return ToolResult(name=call.name, error=f"Input file not found: {path}")
                info = sniff_csv(full_input)
                steps = suggest_cleaning_steps(info)
                result = clean_csv(info, steps, full_output)
                return ToolResult(name=call.name, result=result)
            
            elif call.name == "clean_markdown":
                path = call.parameters["path"]
                output = call.parameters.get("output")
                if not output:
                    output = path.replace(".md", "_cleaned.md")
                collapse_empty = call.parameters.get("collapse_empty", True)
                normalize_timestamps = call.parameters.get("normalize_timestamps", True)
                full_input = os.path.join(self.root, path)
                full_output = os.path.join(self.root, output)
                if not os.path.exists(full_input):
                    return ToolResult(name=call.name, error=f"Input file not found: {path}")
                info = parse_markdown(full_input)
                steps = suggest_md_cleaning(info)
                # Apply additional options
                if collapse_empty:
                    steps.append({"type": "collapse_empty_sections"})
                if normalize_timestamps:
                    steps.append({"type": "normalize_timestamps"})
                result = clean_markdown(info, steps, full_output)
                return ToolResult(name=call.name, result=result)
            
            elif call.name == "summarize_results":
                context = call.parameters["context"]
                style = call.parameters.get("style", "summary")
                # This is a meta-tool that just returns the context with formatting
                if style == "json":
                    return ToolResult(name=call.name, result={"summary": context})
                elif style == "markdown":
                    return ToolResult(name=call.name, result=f"# Summary\n\n{context}")
                else:
                    return ToolResult(name=call.name, result=context)
            
            else:
                return ToolResult(name=call.name, error=f"Unknown tool: {call.name}")
        
        except Exception as e:
            return ToolResult(name=call.name, error=str(e))
    
    def get_tools_prompt(self) -> str:
        """Return formatted tools description for prompts."""
        tools = self.get_tools()
        tool_desc = []
        for tool in tools:
            params = json.dumps(tool.parameters, indent=2)
            tool_desc.append(f"- {tool.name}: {tool.description}\n  Parameters: {params}")
        return "\n\n".join(tool_desc)
