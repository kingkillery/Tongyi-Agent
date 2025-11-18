"""
Base Orchestrator Class
-----------------------
Provides common initialization and interface for all orchestrator implementations.
Reduces code duplication and enforces consistent patterns across orchestrators.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Dict, Optional

import sys
from pathlib import Path

# Add src to path for config imports
_src_path = Path(__file__).parent
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from config.budgets import DEFAULT_AGENT_BUDGETS  # noqa: E402
from delegation_policy import AgentBudget, DelegationPolicy  # noqa: E402
from tool_registry import ToolRegistry  # noqa: E402
from verifier_gate import VerifierGate  # noqa: E402


class BaseOrchestrator(ABC):
    """Base class for all orchestrators with common initialization and interface."""

    def __init__(
        self,
        root: str = ".",
        tools: Optional[ToolRegistry] = None,
        agent_budgets: Optional[Dict[str, AgentBudget]] = None,
    ):
        """Initialize common orchestrator components.

        Args:
            root: Root directory for code search and file operations
            tools: Optional ToolRegistry instance (for dependency injection in tests)
            agent_budgets: Optional custom agent budgets (uses defaults if not provided)
        """
        self.root = os.path.abspath(root)

        # Tool registry (can be injected for testing)
        self.tools = tools or self._create_tools()

        # Delegation policy with budgets
        budgets = agent_budgets or self._get_default_budgets()
        self.policy = DelegationPolicy(agent_budgets=budgets)

        # Verifier gate for claim verification
        self.verifier_gate = VerifierGate()

        # Subclass-specific initialization
        self._initialize_client()

    def _create_tools(self) -> Optional[ToolRegistry]:
        """Create tool registry. Override if orchestrator doesn't use tools.

        Returns:
            ToolRegistry instance or None if orchestrator doesn't use standard tools
        """
        return ToolRegistry(root=self.root)

    def _get_default_budgets(self) -> Dict[str, AgentBudget]:
        """Get default agent budgets. Override to customize per orchestrator.

        Returns:
            Dictionary of tool/agent names to budget limits
        """
        return DEFAULT_AGENT_BUDGETS.copy()

    @abstractmethod
    def _initialize_client(self):
        """Initialize model-specific client (Tongyi, Claude, local delegator, etc.).

        This is called after common initialization and should set up any
        model-specific clients, parsers, or configurations.
        """
        pass

    @abstractmethod
    def run(self, question: str) -> str:
        """Execute orchestration to answer the question.

        Args:
            question: User's question/query to answer

        Returns:
            Final answer as a string
        """
        pass

    def get_tool_usage_summary(self) -> Dict[str, any]:
        """Get summary of tool usage and configuration.

        Returns:
            Dictionary with orchestrator metadata
        """
        summary = {
            "root_directory": self.root,
            "orchestrator_type": self.__class__.__name__,
        }

        if self.tools:
            summary["available_tools"] = [t.name for t in self.tools.get_tools()]
            summary["total_tools"] = len(self.tools.get_tools())

        return summary
