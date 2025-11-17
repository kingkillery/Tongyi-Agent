"""
Optimized Tongyi Agent with Agent Lightning Integration
Transforms Tongyi Orchestrator into a learning, adaptive research assistant
"""
from __future__ import annotations

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

from tongyi_orchestrator import TongyiOrchestrator
from config import DEFAULT_TONGYI_CONFIG

logger = logging.getLogger(__name__)


class OptimizedTongyiAgent:
    """
    Agent Lightning-optimized Tongyi Agent
    Combines Tongyi's research capabilities with learning optimization
    """

    def __init__(self,
                 root: str = ".",
                 optimization_mode: str = "prompt",
                 enable_training: bool = False,
                 training_data_path: Optional[str] = None):
        """
        Initialize optimized Tongyi Agent

        Args:
            root: Root directory for research
            optimization_mode: "prompt", "rl", or "sft"
            enable_training: Whether to enable learning from interactions
            training_data_path: Path to store/retrieve training data
        """
        if not AGENT_LIGHTNING_AVAILABLE:
            logger.warning("Agent Lightning not available, using standard Tongyi Orchestrator")
            enable_training = False

        self.root = os.path.abspath(root)
        self.optimization_mode = optimization_mode
        self.enable_training = enable_training
        self.training_data_path = training_data_path or os.path.join(root, ".tongyi_training")

        # Initialize base Tongyi Orchestrator
        self.base_orchestrator = TongyiOrchestrator(root=root)

        # Training setup
        self.interaction_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, float] = {
            "total_interactions": 0,
            "successful_researches": 0,
            "average_response_time": 0.0,
            "tool_usage_efficiency": 0.0
        }

        # Initialize Agent Lightning if available
        if self.enable_training and AGENT_LIGHTNING_AVAILABLE:
            self._setup_lightning_optimizer()
        else:
            self.lightning_trainer = None

        logger.info(f"Optimized Tongyi Agent initialized with optimization_mode={optimization_mode}")

    def _setup_lightning_optimizer(self):
        """Setup Agent Lightning optimizer based on mode"""
        try:
            if self.optimization_mode == "prompt":
                self.lightning_trainer = PromptOptimizer(
                    base_agent=self.base_orchestrator,
                    optimization_target="research_efficiency"
                )
            elif self.optimization_mode == "rl":
                self.lightning_trainer = RLTrainer(
                    base_agent=self.base_orchestrator,
                    reward_function=self._research_reward_function
                )
            else:
                logger.warning(f"Optimization mode '{self.optimization_mode}' not yet implemented")
                self.lightning_trainer = None

            logger.info(f"Agent Lightning optimizer setup completed for mode: {self.optimization_mode}")
        except Exception as e:
            logger.error(f"Failed to setup Agent Lightning optimizer: {e}")
            self.lightning_trainer = None

    def run(self, query: str) -> str:
        """
        Run research query with optional learning optimization

        Args:
            query: Research question or task

        Returns:
            Research response
        """
        start_time = time.time()

        try:
            # If we have an optimizer, use it
            if self.lightning_trainer:
                response = self._run_with_optimization(query)
            else:
                response = self.base_orchestrator.run(query)

            # Record interaction for learning
            if self.enable_training:
                self._record_interaction(query, response, time.time() - start_time)

            return response

        except Exception as e:
            logger.error(f"Error in optimized Tongyi Agent: {e}")
            # Fallback to base orchestrator
            return self.base_orchestrator.run(query)

    def _run_with_optimization(self, query: str) -> str:
        """Run query with Agent Lightning optimization"""
        try:
            # For prompt optimization
            if self.optimization_mode == "prompt":
                # Use optimized prompts if available
                optimized_query = self.lightning_trainer.optimize_input(query)
                response = self.base_orchestrator.run(optimized_query)
                self.lightning_trainer.record_feedback(query, optimized_query, response)
                return response

            # For RL optimization
            elif self.optimization_mode == "rl":
                # Use RL-trained decision making
                return self.lightning_trainer.act(query)

            # Default to base orchestrator
            return self.base_orchestrator.run(query)

        except Exception as e:
            logger.warning(f"Optimization failed, falling back to base orchestrator: {e}")
            return self.base_orchestrator.run(query)

    def _record_interaction(self, query: str, response: str, response_time: float):
        """Record interaction for learning analytics"""
        interaction = {
            "timestamp": time.time(),
            "query": query,
            "response": response,
            "response_time": response_time,
            "query_length": len(query),
            "response_length": len(response),
            "tools_used": self._extract_tools_used(response)
        }

        self.interaction_history.append(interaction)
        self.performance_metrics["total_interactions"] += 1

        # Update running averages
        self._update_performance_metrics(response_time)

        # Periodically save training data
        if len(self.interaction_history) % 10 == 0:
            self._save_training_data()

    def _extract_tools_used(self, response: str) -> List[str]:
        """Extract which tools were used from response"""
        # This is a simple implementation - could be enhanced
        tools = []
        if "search_code" in response.lower():
            tools.append("search_code")
        if "search_papers" in response.lower():
            tools.append("search_papers")
        if "run_sandbox" in response.lower():
            tools.append("run_sandbox")
        return tools

    def _update_performance_metrics(self, response_time: float):
        """Update performance metrics"""
        total = self.performance_metrics["total_interactions"]
        current_avg = self.performance_metrics["average_response_time"]

        # Update average response time
        self.performance_metrics["average_response_time"] = (
            (current_avg * (total - 1) + response_time) / total
        )

    def _research_reward_function(self, query: str, response: str, tools_used: List[str]) -> float:
        """
        Reward function for RL training
        Higher rewards for better research outcomes
        """
        reward = 0.0

        # Reward for comprehensive responses
        if len(response) > 500:
            reward += 0.2

        # Reward for using appropriate tools
        research_keywords = ["research", "analyze", "search", "find", "investigate"]
        is_research_query = any(keyword in query.lower() for keyword in research_keywords)

        if is_research_query and tools_used:
            reward += 0.3 * len(set(tools_used))  # Reward tool diversity

        # Reward for citations and sources
        if "http" in response or "doi" in response.lower():
            reward += 0.2

        # Reward for structured analysis
        if "##" in response or "```" in response:  # Markdown structure
            reward += 0.1

        return reward

    def _save_training_data(self):
        """Save training data for future optimization"""
        try:
            os.makedirs(self.training_data_path, exist_ok=True)

            data_file = os.path.join(self.training_data_path, "interactions.jsonl")
            with open(data_file, "a", encoding="utf-8") as f:
                interaction = self.interaction_history[-1]
                f.write(json.dumps(interaction) + "\n")

            # Save metrics
            metrics_file = os.path.join(self.training_data_path, "metrics.json")
            with open(metrics_file, "w", encoding="utf-8") as f:
                json.dump(self.performance_metrics, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save training data: {e}")

    def optimize(self, optimization_type: str = "prompt", iterations: int = 100):
        """
        Run optimization training

        Args:
            optimization_type: Type of optimization to run
            iterations: Number of optimization iterations
        """
        if not self.lightning_trainer:
            logger.error("Agent Lightning trainer not initialized")
            return

        try:
            logger.info(f"Starting {optimization_type} optimization for {iterations} iterations")

            if optimization_type == "prompt" and len(self.interaction_history) > 10:
                # Use interaction history for prompt optimization
                self.lightning_trainer.optimize_from_history(
                    self.interaction_history[-50:],  # Use last 50 interactions
                    iterations=iterations
                )
            else:
                # Run generic optimization
                self.lightning_trainer.optimize(iterations=iterations)

            logger.info("Optimization completed successfully")

        except Exception as e:
            logger.error(f"Optimization failed: {e}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        stats = self.performance_metrics.copy()
        stats["optimization_mode"] = self.optimization_mode
        stats["training_enabled"] = self.enable_training
        stats["interactions_recorded"] = len(self.interaction_history)

        if self.lightning_trainer:
            stats["lightning_status"] = "active"
        else:
            stats["lightning_status"] = "inactive"

        return stats

    def export_training_data(self, filepath: str):
        """Export training data for external analysis"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "interactions": self.interaction_history,
                    "metrics": self.performance_metrics,
                    "config": {
                        "optimization_mode": self.optimization_mode,
                        "training_enabled": self.enable_training
                    }
                }, f, indent=2)
            logger.info(f"Training data exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export training data: {e}")


# Factory function for easy instantiation
def create_optimized_agent(root: str = ".",
                           optimization_mode: str = "prompt",
                           enable_training: bool = False) -> OptimizedTongyiAgent:
    """
    Factory function to create optimized Tongyi Agent

    Args:
        root: Root directory
        optimization_mode: "prompt", "rl", or "sft"
        enable_training: Enable learning from interactions

    Returns:
        OptimizedTongyiAgent instance
    """
    return OptimizedTongyiAgent(
        root=root,
        optimization_mode=optimization_mode,
        enable_training=enable_training
    )