#!/usr/bin/env python3
"""
Agent Lightning Quick Start Example
Demonstrates how to use optimized Tongyi Agent with training capabilities
"""

import asyncio
import os
import sys
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def example_1_basic_training():
    """Example 1: Basic training with Tongyi Agent"""
    print("[Example 1] Basic Training with Tongyi Agent")
    print("=" * 50)

    try:
        from training_manager import get_training_manager

        # Create training manager
        manager = get_training_manager()

        # Create optimized Tongyi agent with training enabled
        agent = manager.create_optimized_agent(
            agent_type="tongyi",
            optimization_mode="prompt",
            enable_training=True
        )

        print("✅ Optimized Tongyi Agent created with training enabled")

        # Simulate some training interactions
        training_queries = [
            "What is machine learning?",
            "How does neural network work?",
            "Explain deep learning concepts",
            "What are the latest AI developments?",
            "Compare supervised vs unsupervised learning"
        ]

        print(f"\n📚 Processing {len(training_queries)} training queries...")

        for i, query in enumerate(training_queries, 1):
            print(f"\n[{i}/{len(training_queries)}] Query: {query}")
            start_time = time.time()

            try:
                response = agent.run(query)
                response_time = time.time() - start_time
                print(f"✅ Response ({response_time:.2f}s): {response[:100]}...")
            except Exception as e:
                print(f"❌ Error: {e}")

        # Get performance stats
        stats = agent.get_performance_stats()
        print(f"\n📊 Training Stats:")
        print(f"  Total Interactions: {stats['total_interactions']}")
        print(f"  Average Response Time: {stats['average_response_time']:.2f}s")
        print(f"  Training Enabled: {stats['training_enabled']}")
        print(f"  Lightning Status: {stats['lightning_status']}")

        # Run optimization
        print(f"\n🔧 Running optimization...")
        success = manager.run_optimization(agent, iterations=50)

        if success:
            print("✅ Optimization completed successfully!")
        else:
            print("❌ Optimization failed")

    except ImportError as e:
        print(f"❌ Agent Lightning not available: {e}")
        print("Install with: pip install agentlightning torch transformers")
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_2_claude_sdk_training():
    """Example 2: Training with Claude Agent SDK"""
    print("\n🤖 Example 2: Claude Agent SDK with Training")
    print("=" * 50)

    try:
        from optimized_claude_agent import create_optimized_claude_agent

        # Create optimized Claude agent
        agent = create_optimized_claude_agent(
            root=".",
            optimization_mode="prompt",
            enable_training=True
        )

        print("✅ Optimized Claude Agent created with training enabled")

        # Training queries for Claude SDK
        training_queries = [
            "Analyze this Python code for performance issues",
            "What are the best practices for API design?",
            "Explain the SOLID principles with examples",
            "How do you optimize database queries?",
            "What is the difference between REST and GraphQL?"
        ]

        print(f"\n📚 Processing {len(training_queries)} training queries with Claude SDK...")

        for i, query in enumerate(training_queries, 1):
            print(f"\n[{i}/{len(training_queries)}] Query: {query}")
            start_time = time.time()

            try:
                response = await agent.process_query(query)
                response_time = time.time() - start_time
                print(f"✅ Claude SDK Response ({response_time:.2f}s): {response[:100]}...")
            except Exception as e:
                print(f"❌ Error: {e}")

        # Get Claude SDK specific stats
        stats = agent.get_performance_stats()
        print(f"\n📊 Claude SDK Training Stats:")
        print(f"  Agent Type: {stats['agent_type']}")
        print(f"  Total Interactions: {stats['total_interactions']}")
        print(f"  Claude SDK Success Rate: {stats['claude_sdk_success_rate']:.2%}")
        print(f"  Average Response Time: {stats['average_response_time']:.2f}s")

    except ImportError as e:
        print(f"❌ Claude SDK or Agent Lightning not available: {e}")
        print("Install with: pip install claude-agent-sdk agentlightning torch transformers")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_3_training_session():
    """Example 3: Complete training session with manager"""
    print("\n🎓 Example 3: Complete Training Session")
    print("=" * 50)

    try:
        from training_manager import get_training_manager

        # Create training manager
        manager = get_training_manager()

        # Define training queries
        research_queries = [
            "What are the current trends in artificial intelligence research?",
            "How do transformers work in natural language processing?",
            "What are the applications of reinforcement learning?",
            "Explain the concept of transfer learning with examples",
            "What are the ethical considerations in AI development?"
        ]

        print(f"🚀 Starting complete training session...")
        print(f"   Agent Type: Tongyi")
        print(f"   Queries: {len(research_queries)}")
        print(f"   Optimization Iterations: 100")

        # Run training session
        results = manager.run_training_session(
            agent_type="tongyi",
            root=".",
            queries=research_queries,
            optimization_iterations=100
        )

        print(f"\n📊 Training Session Results:")
        print(f"  Success: {'✅' if results['success'] else '❌'}")
        print(f"  Duration: {results['duration']:.2f}s")
        print(f"  Queries Processed: {results['queries_processed']}")
        print(f"  Optimization Run: {'✅' if results['optimization_run'] else '❌'}")

        if results['error']:
            print(f"  Error: {results['error']}")

        if 'final_stats' in results:
            stats = results['final_stats']
            print(f"\n📈 Final Performance:")
            print(f"  Total Interactions: {stats['total_interactions']}")
            print(f"  Average Response Time: {stats['average_response_time']:.2f}s")

    except Exception as e:
        print(f"❌ Error: {e}")


def example_4_configuration():
    """Example 4: Training configuration and customization"""
    print("\n⚙️ Example 4: Training Configuration")
    print("=" * 50)

    try:
        from training_manager import get_training_manager

        # Create training manager
        manager = get_training_manager()

        # Get current configuration
        config = manager.get_training_config_summary()

        print("📋 Current Training Configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")

        # Update configuration
        print(f"\n🔧 Updating configuration...")
        manager.update_config('training', 'enabled', 'true')
        manager.update_config('prompt_optimization', 'iterations', '200')
        manager.update_config('prompt_optimization', 'learning_rate', '0.01')

        # Get updated configuration
        updated_config = manager.get_training_config_summary()

        print("✅ Configuration Updated:")
        print(f"  Training Enabled: {updated_config['training_enabled']}")
        print(f"  Optimization Iterations: {updated_config['optimization_iterations']}")
        print(f"  Learning Rate: {updated_config['learning_rate']}")

    except Exception as e:
        print(f"❌ Error: {e}")


def example_5_export_analysis():
    """Example 5: Export and analyze training data"""
    print("\n📦 Example 5: Export and Analyze Training Data")
    print("=" * 50)

    try:
        from training_manager import get_training_manager
        import json
        import os

        # Create training manager
        manager = get_training_manager()

        # Check if training data exists
        training_path = ".tongyi_training"
        if os.path.exists(training_path):
            print(f"📁 Found training data in: {training_path}")

            # List training files
            files = os.listdir(training_path)
            print(f"📄 Training files: {files}")

            # Create a mock agent for export
            agent = manager.create_optimized_agent("tongyi", enable_training=False)

            # Export training data
            export_path = "exported_training_data.json"
            success = manager.export_training_data(agent, export_path)

            if success and os.path.exists(export_path):
                print(f"✅ Training data exported to: {export_path}")

                # Analyze exported data
                with open(export_path, 'r') as f:
                    data = json.load(f)

                print(f"\n📊 Training Data Analysis:")
                if 'interactions' in data:
                    interactions = data['interactions']
                    print(f"  Total Interactions: {len(interactions)}")

                    if interactions:
                        # Calculate some statistics
                        response_times = [i.get('response_time', 0) for i in interactions]
                        avg_time = sum(response_times) / len(response_times)
                        print(f"  Average Response Time: {avg_time:.2f}s")

                        tool_usage = {}
                        for interaction in interactions:
                            tools = interaction.get('tools_used', [])
                            for tool in tools:
                                tool_usage[tool] = tool_usage.get(tool, 0) + 1

                        if tool_usage:
                            print(f"  Tool Usage: {tool_usage}")

                if 'metrics' in data:
                    metrics = data['metrics']
                    print(f"  Performance Metrics:")
                    for key, value in metrics.items():
                        print(f"    {key}: {value}")
            else:
                print("❌ Failed to export training data")
        else:
            print(f"ℹ️  No training data found. Run some training queries first.")
            print("   Try: python agent_lightning_example.py")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all examples"""
    print("[Agent Lightning] Agent Lightning Integration Examples")
    print("=" * 60)
    print("This demo shows how to use Agent Lightning with Tongyi Agent")
    print("Make sure you have installed: pip install agentlightning torch transformers")
    print()

    # Check if Agent Lightning is available
    try:
        import agentlightning
        print("✅ Agent Lightning is available")
    except ImportError:
        print("❌ Agent Lightning not found")
        print("Install with: pip install agentlightning torch transformers")
        return

    # Run examples
    try:
        example_1_basic_training()
        example_2_claude_sdk_training()
        example_3_training_session()
        example_4_configuration()
        example_5_export_analysis()

        print("\n🎉 All examples completed!")
        print("\n💡 Next Steps:")
        print("1. Try: tongyi-cli --train 'your research question'")
        print("2. Monitor: tongyi-cli --training-stats")
        print("3. Optimize: tongyi-cli --optimize")
        print("4. Export: tongyi-cli --export-training-data data.json")

    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()