"""
Base tool interface for Tongyi DeepResearch Agent
Provides common functionality for all tools
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

class ToolResult(BaseModel):
    """Standardized tool result format"""
    
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    
class ToolCategory(Enum):
    """Tool categories for agent coordination"""
    SEARCH = "search"
    WEB = "web" 
    COMPUTATION = "computation"
    ACADEMIC = "academic"
    FILE_PROCESSING = "file_processing"

@dataclass
class ToolContext:
    """Context information passed to tools"""
    
    user_query: str
    current_plan: Optional[str] = None
    previous_steps: List[str] = None
    timeout: Optional[int] = None
    max_retries: int = 3
    
    def __post_init__(self):
        if self.previous_steps is None:
            self.previous_steps = []

class BaseTool(ABC):
    """Base class for all tools in the Tongyi DeepResearch agent"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"tool.{self.__class__.__name__.lower()}")
        self.category = self._get_category()
        self.name = self.__class__.__name__.lower()
        
    @abstractmethod
    def _get_category(self) -> ToolCategory:
        """Return the tool category"""
        pass
    
    @abstractmethod
    async def execute(self, query: str, context: ToolContext) -> ToolResult:
        """Execute the tool with given query and context"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return tool description for agent planning"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Return tool parameter schema"""
        pass
    
    async def execute_with_retry(self, query: str, context: ToolContext) -> ToolResult:
        """Execute tool with retry logic"""
        
        last_error = None
        for attempt in range(context.max_retries + 1):
            try:
                result = await self.execute(query, context)
                if result.success:
                    return result
                    
                last_error = result.error
                if attempt < context.max_retries:
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                    
            except Exception as e:
                last_error = str(e)
                if attempt < context.max_retries:
                    await asyncio.sleep(1 * (attempt + 1))
                    
        return ToolResult(
            success=False,
            error=f"Tool execution failed after {context.max_retries + 1} attempts: {last_error}",
            metadata={"attempts": context.max_retries + 1}
        )
    
    def validate_query(self, query: str) -> bool:
        """Validate if query is appropriate for this tool"""
        return len(query.strip()) > 0
    
    def extract_key_info(self, result: Any) -> Dict[str, Any]:
        """Extract and structure key information from tool result"""
        return {"raw_result": result, "tool_name": self.name}
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Get comprehensive tool information"""
        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.get_description(),
            "parameters": self.get_parameters(),
            "config": self.config
        }
