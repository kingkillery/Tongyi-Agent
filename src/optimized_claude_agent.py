"""
Optimized Claude Agent with Agent Lightning Integration
Transforms Claude Agent SDK into a learning, adaptive research assistant
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Union

try:
    from agentlightning import AgentLightning, OptimizationType
    from agentlightning.optimizers import PromptOptimizer, RLTrainer
    AGENT_LIGHTNING_AVAILABLE = True
except ImportError:
    AGENT_LIGHTNING_AVAILABLE = False
    # Create dummy classes for graceful fallback
    class AgentLightning:
        def __init__(self, *args, **kwargs):
            raise ImportError("Agent Lightning not installed. Install with: pip install agentlightning")

    class OptimizationType:
        PROMPT = "prompt"
        RL = "rl"
        SFT = "sft"

from claude_agent_orchestrator import ClaudeAgentOrchestrator
from config import DEFAULT_CLAUDE_CONFIG

logger = logging.getLogger(__name__)


class OptimizedClaudeAgent:
    """
    Agent Lightning-optimized Claude Agent
    Combines Claude SDK's capabilities with learning optimization
    """

    def __init__(self,
                 root: str = ".",
                 optimization_mode: str = "prompt",
                 enable_training: bool = False,
                 training_data_path: Optional[str] = None):
        """
        Initialize optimized Claude Agent

        Args:
            root: Root directory for research
            optimization_mode: "prompt", "rl", or "sft"
            enable_training: Whether to enable learning from interactions
            training_data_path: Path to store/retrieve training data
        """
        if not AGENT_LIGHTNING_AVAILABLE:
            logger.warning("Agent Lightning not available, using standard Claude Agent SDK")
            enable_training = False

        self.root = os.path.abspath(root)
        self.optimization_mode = optimization_mode
        self.enable_training = enable_training
        self.training_data_path = training_data_path or os.path.join(root, ".claude_training")

        # Initialize base Claude Agent SDK
        self.base_orchestrator = ClaudeAgentOrchestrator(root=root)

        # Training setup
        self.interaction_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, float] = {
            "total_interactions": 0,
            "successful_researches": 0,
            "average_response_time": 0.0,
            "tool_usage_efficiency": 0.0,
            "claude_sdk_success_rate": 0.0
        }

        # Initialize Agent Lightning if available
        if self.enable_training and AGENT_LIGHTNING_AVAILABLE:
            self._setup_lightning_optimizer()
        else:
            self.lightning_trainer = None

        logger.info(f"Optimized Claude Agent initialized with optimization_mode={optimization_mode}")

    def _setup_lightning_optimizer(self):
        """Setup Agent Lightning optimizer for Claude SDK"""
        try:
            if self.optimization_mode == "prompt":
                self.lightning_trainer = PromptOptimizer(
                    base_agent=self.base_orchestrator,
                    optimization_target="claude_research_efficiency"
                )
            elif self.optimization_mode == "rl":
                self.lightning_trainer = RLTrainer(
                    base_agent=self.base_orchestrator,
                    reward_function=self._claude_reward_function
                )
            else:
                logger.warning(f"Optimization mode '{self.optimization_mode}' not yet implemented")
                self.lightning_trainer = None

            logger.info(f"Agent Lightning optimizer setup completed for Claude SDK mode: {self.optimization_mode}")
        except Exception as e:
            logger.error(f"Failed to setup Agent Lightning optimizer: {e}")
            self.lightning_trainer = None

    async def process_query(self, query: str) -> str:
        """
        Process query with Claude SDK and optional learning optimization

        Args:
            query: Research question or task

        Returns:
            Research response
        """
        start_time = time.time()
        claude_success = False

        try:
            # If we have an optimizer, use it
            if self.lightning_trainer:
                response = await self._run_with_optimization(query)
            else:
                response = await self.base_orchestrator.process_query(query)

            claude_success = True
            response_time = time.time() - start_time

            # Record interaction for learning
            if self.enable_training:
                self._record_interaction(query, response, response_time, claude_success)

            return response

        except Exception as e:
            logger.error(f"Error in optimized Claude Agent: {e}")
            response_time = time.time() - start_time

            # Record failed interaction
            if self.enable_training:
                self._record_interaction(query, str(e), response_time, claude_success)

            # Re-raise for fallback handling
            raise

    async def _run_with_optimization(self, query: str) -> str:
        """Run query with Agent Lightning optimization"""
        try:
            # For prompt optimization
            if self.optimization_mode == "prompt":
                # Use optimized prompts if available
                optimized_query = self.lightning_trainer.optimize_input(query)
                response = await self.base_orchestrator.process_query(optimized_query)
                self.lightning_trainer.record_feedback(query, optimized_query, response)
                return response

            # For RL optimization
            elif self.optimization_mode == "rl":
                # Use RL-trained decision making
                return await self.lightning_trainer.act_async(query)

            # Default to base orchestrator
            return await self.base_orchestrator.process_query(query)

        except Exception as e:
            logger.warning(f"Optimization failed, falling back to base Claude SDK: {e}")
            return await self.base_orchestrator.process_query(query)

    def _record_interaction(self, query: str, response: str, response_time: float, claude_success: bool):
        """Record interaction for learning analytics"""
        interaction = {
            "timestamp": time.time(),
            "query": query,
            "response": response,
            "response_time": response_time,
            "claude_success": claude_success,
            "query_length": len(query),
            "response_length": len(response),
            "tools_used": self._extract_tools_used(response)
        }

        self.interaction_history.append(interaction)
        self.performance_metrics["total_interactions"] += 1

        if claude_success:
            self.performance_metrics["successful_researches"] += 1

        # Update running averages
        self._update_performance_metrics(response_time, claude_success)

        # Periodically save training data
        if len(self.interaction_history) % 10 == 0:
            self._save_training_data()

    def _extract_tools_used(self, response: str) -> List[str]:
        """Extract which tools were used from Claude SDK response"""
        tools = []
        # Claude SDK specific tools
        claude_tools = ["Read", "Write", "Bash", "Glob", "Grep", "WebFetch", "TodoWrite", "WebSearch"]

        for tool in claude_tools:
            if f"Tool called: {tool}" in response or f"{tool}(" in response:
                tools.append(tool)

        return tools

    def _update_performance_metrics(self, response_time: float, claude_success: bool):
        """Update performance metrics"""
        total = self.performance_metrics["total_interactions"]
        current_avg = self.performance_metrics["average_response_time"]
        current_success_rate = self.performance_metrics["claude_sdk_success_rate"]

        # Update average response time
        self.performance_metrics["average_response_time"] = (
            (current_avg * (total - 1) + response_time) / total
        )

        # Update Claude SDK success rate
        if claude_success:
            self.performance_metrics["claude_sdk_success_rate"] = (
                (current_success_rate * (total - 1) + 1.0) / total
            )
        else:
            self.performance_metrics["claude_sdk_success_rate"] = (
                (current_success_rate * (total - 1)) / total
            )

    def _claude_reward_function(self, query: str, response: str, tools_used: List[str]) -> float:
        """
        Reward function for RL training specific to Claude SDK
        Higher rewards for better Claude SDK utilization
        """
        reward = 0.0

        # Reward for comprehensive Claude SDK responses
        if len(response) > 1000:
            reward += 0.2

        # Reward for using Claude SDK tools effectively
        claude_tools = ["Read", "Write", "Bash", "Grep", "WebFetch"]
        claude_tools_used = [tool for tool in tools_used if tool in claude_tools]

        if claude_tools_used:
            reward += 0.3 * len(set(claude_tools_used))  # Reward tool diversity

        # Reward for proper file operations (Claude SDK strength)
        file_operations = ["Read", "Write", "Edit"]
        file_ops_used = [tool for tool in claude_tools_used if tool in file_operations]
        if file_ops_used:
            reward += 0.2

        # Reward for web operations
        web_operations = ["WebFetch", "WebSearch"]
        web_ops_used = [tool for tool in claude_tools_used if tool in web_operations]
        if web_ops_used:
            reward += 0.15

        # Reward for structured analysis
        if "```" in response or "## " in response:  # Code blocks or headers
            reward += 0.1

        return reward

    def _save_training_data(self):
        """Save training data for future optimization"""
        try:
            os.makedirs(self.training_data_path, exist_ok=True)

            data_file = os.path.join(self.training_data_path, "claude_interactions.jsonl")
            with open(data_file, "a", encoding="utf-8") as f:
                interaction = self.interaction_history[-1]
                f.write(json.dumps(interaction) + "\n")

            # Save metrics
            metrics_file = os.path.join(self.training_data_path, "claude_metrics.json")
            with open(metrics_file, "w", encoding="utf-8") as f:
                json.dump(self.performance_metrics, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save Claude training data: {e}")

    def optimize(self, optimization_type: str = "prompt", iterations: int = 100):
        """
        Run optimization training for Claude SDK

        Args:
            optimization_type: Type of optimization to run
            iterations: Number of optimization iterations
        """
        if not self.lightning_trainer:
            logger.error("Agent Lightning trainer not initialized for Claude SDK")
            return

        try:
            logger.info(f"Starting Claude SDK {optimization_type} optimization for {iterations} iterations")

            if optimization_type == "prompt" and len(self.interaction_history) > 10:
                # Use interaction history for prompt optimization
                self.lightning_trainer.optimize_from_history(
                    self.interaction_history[-50:],  # Use last 50 interactions
                    iterations=iterations
                )
            else:
                # Run generic optimization
                self.lightning_trainer.optimize(iterations=iterations)

            logger.info("Claude SDK optimization completed successfully")

        except Exception as e:
            logger.error(f"Claude SDK optimization failed: {e}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current Claude SDK performance statistics"""
        stats = self.performance_metrics.copy()
        stats["optimization_mode"] = self.optimization_mode
        stats["training_enabled"] = self.enable_training
        stats["interactions_recorded"] = len(self.interaction_history)
        stats["agent_type"] = "claude_sdk"

        if self.lightning_trainer:
            stats["lightning_status"] = "active"
        else:
            stats["lightning_status"] = "inactive"

        return stats

    def export_training_data(self, filepath: str):
        """Export Claude SDK training data for external analysis"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "agent_type": "claude_sdk",
                    "interactions": self.interaction_history,
                    "metrics": self.performance_metrics,
                    "config": {
                        "optimization_mode": self.optimization_mode,
                        "training_enabled": self.enable_training
                    }
                }, f, indent=2)
            logger.info(f"Claude SDK training data exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export Claude training data: {e}")

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics compatible with base Claude SDK"""
        stats = self.get_performance_stats()

        # Add base orchestrator stats if available
        if hasattr(self.base_orchestrator, 'get_session_stats'):
            base_stats = self.base_orchestrator.get_session_stats()
            stats.update(base_stats)

        return stats

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Save any pending training data
        if self.enable_training and self.interaction_history:
            self._save_training_data()


# Factory function for easy instantiation
def create_optimized_claude_agent(root: str = ".",
                                 optimization_mode: str = "prompt",
                                 enable_training: bool = False) -> OptimizedClaudeAgent:
    """
    Factory function to create optimized Claude Agent

    Args:
        root: Root directory
        optimization_mode: "prompt", "rl", or "sft"
        enable_training: Enable learning from interactions

    Returns:
        OptimizedClaudeAgent instance
    """
    return OptimizedClaudeAgent(
        root=root,
        optimization_mode=optimization_mode,
        enable_training=enable_training
    )


# Synchronous wrapper for compatibility
class SyncOptimizedClaudeAgent:
    """Synchronous wrapper for OptimizedClaudeAgent"""

    def __init__(self, *args, **kwargs):
        self.async_agent = OptimizedClaudeAgent(*args, **kwargs)

    def process_query(self, query: str) -> str:
        """Synchronous wrapper for async process_query"""
        try:
            import asyncio
            return asyncio.run(self.async_agent.process_query(query))
        except Exception as e:
            logger.error(f"Error in sync Claude agent wrapper: {e}")
            raise

    def __getattr__(self, name):
        """Delegate other methods to async agent"""
        return getattr(self.async_agent, name)