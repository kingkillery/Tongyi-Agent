"""
Training Manager for Agent Lightning Integration
Handles configuration, training orchestration, and performance monitoring
"""
from __future__ import annotations

import configparser
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Union

from optimized_tongyi_agent import OptimizedTongyiAgent, create_optimized_agent
from optimized_claude_agent import OptimizedClaudeAgent, create_optimized_claude_agent

logger = logging.getLogger(__name__)


class TrainingManager:
    """
    Manages Agent Lightning training configuration and execution
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize training manager

        Args:
            config_path: Path to training configuration file
        """
        self.config_path = config_path or "training_config.ini"
        self.config = self._load_config()

        self.active_agents: Dict[str, Union[OptimizedTongyiAgent, OptimizedClaudeAgent]] = {}
        self.training_stats: Dict[str, Dict[str, Any]] = {}

        logger.info("Training Manager initialized")

    def _load_config(self) -> configparser.ConfigParser:
        """Load training configuration from file"""
        config = configparser.ConfigParser()

        if os.path.exists(self.config_path):
            config.read(self.config_path)
            logger.info(f"Loaded training configuration from {self.config_path}")
        else:
            logger.warning(f"Training config file not found: {self.config_path}, using defaults")
            self._create_default_config(config)

        return config

    def _create_default_config(self, config: configparser.ConfigParser):
        """Create default configuration if file doesn't exist"""
        config['training'] = {
            'enabled': 'false',
            'mode': 'prompt',
            'training_data_path': '.tongyi_training',
            'auto_save_interval': '10'
        }

        config['prompt_optimization'] = {
            'iterations': '100',
            'optimization_target': 'research_efficiency',
            'learning_rate': '0.001',
            'use_history': 'true',
            'history_size': '50'
        }

        # Add other default sections...
        logger.info("Created default training configuration")

    def is_training_enabled(self) -> bool:
        """Check if training is enabled in configuration"""
        return self.config.getboolean('training', 'enabled', fallback=False)

    def get_training_mode(self) -> str:
        """Get current training mode"""
        return self.config.get('training', 'mode', fallback='prompt')

    def create_optimized_agent(self,
                             agent_type: str,
                             root: str = ".",
                             optimization_mode: Optional[str] = None,
                             enable_training: Optional[bool] = None) -> Union[OptimizedTongyiAgent, OptimizedClaudeAgent]:
        """
        Create an optimized agent with training capabilities

        Args:
            agent_type: "tongyi" or "claude"
            root: Root directory
            optimization_mode: Override config optimization mode
            enable_training: Override config training setting

        Returns:
            Optimized agent instance
        """
        if optimization_mode is None:
            optimization_mode = self.get_training_mode()

        if enable_training is None:
            enable_training = self.is_training_enabled()

        training_data_path = self.config.get('training', 'training_data_path', fallback='.tongyi_training')

        try:
            if agent_type.lower() == "tongyi":
                agent = create_optimized_agent(
                    root=root,
                    optimization_mode=optimization_mode,
                    enable_training=enable_training
                )
            elif agent_type.lower() == "claude":
                agent = create_optimized_claude_agent(
                    root=root,
                    optimization_mode=optimization_mode,
                    enable_training=enable_training
                )
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")

            # Store for management
            agent_id = f"{agent_type}_{int(time.time())}"
            self.active_agents[agent_id] = agent

            logger.info(f"Created optimized {agent_type} agent (ID: {agent_id})")
            return agent

        except Exception as e:
            logger.error(f"Failed to create optimized {agent_type} agent: {e}")
            raise

    def run_optimization(self,
                        agent: Union[OptimizedTongyiAgent, OptimizedClaudeAgent],
                        optimization_type: Optional[str] = None,
                        iterations: Optional[int] = None) -> bool:
        """
        Run optimization on an agent

        Args:
            agent: Agent to optimize
            optimization_type: Type of optimization
            iterations: Number of iterations

        Returns:
            True if optimization succeeded
        """
        try:
            if optimization_type is None:
                optimization_type = self.get_training_mode()

            if iterations is None:
                iterations = self.config.getint('prompt_optimization', 'iterations', fallback=100)

            logger.info(f"Starting {optimization_type} optimization for {iterations} iterations")
            agent.optimize(optimization_type=optimization_type, iterations=iterations)

            return True

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return False

    def get_agent_stats(self, agent: Union[OptimizedTongyiAgent, OptimizedClaudeAgent]) -> Dict[str, Any]:
        """Get performance statistics for an agent"""
        try:
            return agent.get_performance_stats()
        except Exception as e:
            logger.error(f"Failed to get agent stats: {e}")
            return {}

    def export_training_data(self,
                             agent: Union[OptimizedTongyiAgent, OptimizedClaudeAgent],
                             filepath: Optional[str] = None) -> bool:
        """
        Export training data from an agent

        Args:
            agent: Agent to export data from
            filepath: Export filepath

        Returns:
            True if export succeeded
        """
        try:
            if filepath is None:
                export_path = self.config.get('export', 'export_path', fallback='./training_exports')
                timestamp = int(time.time())
                agent_type = "tongyi" if hasattr(agent, 'base_orchestrator') and hasattr(agent.base_orchestrator, 'tools') else "claude"
                filepath = os.path.join(export_path, f"{agent_type}_training_data_{timestamp}.json")

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            agent.export_training_data(filepath)
            logger.info(f"Training data exported to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to export training data: {e}")
            return False

    def run_training_session(self,
                             agent_type: str,
                             root: str = ".",
                             queries: List[str] = None,
                             optimization_iterations: int = 50) -> Dict[str, Any]:
        """
        Run a complete training session

        Args:
            agent_type: "tongyi" or "claude"
            root: Root directory
            queries: Training queries (optional)
            optimization_iterations: Number of optimization iterations

        Returns:
            Training session results
        """
        session_results = {
            'agent_type': agent_type,
            'start_time': time.time(),
            'queries_processed': 0,
            'optimization_run': False,
            'success': False,
            'error': None
        }

        try:
            # Create optimized agent
            agent = self.create_optimized_agent(agent_type=agent_type, root=root)

            # Process training queries if provided
            if queries:
                logger.info(f"Processing {len(queries)} training queries")
                for i, query in enumerate(queries):
                    try:
                        if agent_type == "claude":
                            import asyncio
                            asyncio.run(agent.process_query(query))
                        else:
                            agent.run(query)

                        session_results['queries_processed'] += 1

                        # Log progress
                        if (i + 1) % 10 == 0:
                            logger.info(f"Processed {i + 1}/{len(queries)} queries")

                    except Exception as e:
                        logger.warning(f"Failed to process query {i+1}: {e}")

            # Run optimization
            logger.info("Running optimization...")
            optimization_success = self.run_optimization(
                agent=agent,
                iterations=optimization_iterations
            )
            session_results['optimization_run'] = True

            # Get final stats
            final_stats = self.get_agent_stats(agent)
            session_results['final_stats'] = final_stats

            # Export training data
            self.export_training_data(agent)

            session_results['success'] = True
            session_results['end_time'] = time.time()
            session_results['duration'] = session_results['end_time'] - session_results['start_time']

            logger.info(f"Training session completed successfully in {session_results['duration']:.2f}s")
            return session_results

        except Exception as e:
            session_results['error'] = str(e)
            session_results['end_time'] = time.time()
            session_results['duration'] = session_results['end_time'] - session_results['start_time']

            logger.error(f"Training session failed: {e}")
            return session_results

    def get_training_config_summary(self) -> Dict[str, Any]:
        """Get summary of current training configuration"""
        return {
            'training_enabled': self.is_training_enabled(),
            'training_mode': self.get_training_mode(),
            'training_data_path': self.config.get('training', 'training_data_path'),
            'auto_save_interval': self.config.getint('training', 'auto_save_interval'),
            'optimization_iterations': self.config.getint('prompt_optimization', 'iterations'),
            'optimization_target': self.config.get('prompt_optimization', 'optimization_target'),
            'config_file': self.config_path
        }

    def update_config(self, section: str, key: str, value: str) -> bool:
        """
        Update configuration value

        Args:
            section: Configuration section
            key: Configuration key
            value: New value

        Returns:
            True if update succeeded
        """
        try:
            if not self.config.has_section(section):
                self.config.add_section(section)

            self.config.set(section, key, value)

            # Save to file
            with open(self.config_path, 'w') as f:
                self.config.write(f)

            logger.info(f"Updated config: [{section}] {key} = {value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            return False

    def cleanup(self):
        """Cleanup resources and save any pending data"""
        for agent_id, agent in self.active_agents.items():
            try:
                # Save any pending training data
                if hasattr(agent, 'interaction_history') and agent.interaction_history:
                    logger.info(f"Saving training data for agent {agent_id}")
                    # The agent should auto-save, but we can force it
                    if hasattr(agent, '_save_training_data'):
                        agent._save_training_data()
            except Exception as e:
                logger.error(f"Failed to cleanup agent {agent_id}: {e}")

        self.active_agents.clear()
        logger.info("Training Manager cleanup completed")


# Global training manager instance
_training_manager = None

def get_training_manager(config_path: Optional[str] = None) -> TrainingManager:
    """Get or create global training manager instance"""
    global _training_manager
    if _training_manager is None:
        _training_manager = TrainingManager(config_path)
    return _training_manager

def cleanup_training_manager():
    """Cleanup global training manager"""
    global _training_manager
    if _training_manager is not None:
        _training_manager.cleanup()
        _training_manager = None