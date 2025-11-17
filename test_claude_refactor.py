#!/usr/bin/env python3
"""
Test script for the refactored Tongyi Agent with Claude Agent SDK
"""
import os
import sys
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from config import DEFAULT_CLAUDE_CONFIG, DEFAULT_TONGYI_CONFIG
        print("+ Configuration imports successful")
    except Exception as e:
        print(f"- Configuration import failed: {e}")
        return False

    try:
        from tool_registry import ToolRegistry
        print("+ ToolRegistry import successful")
    except Exception as e:
        print(f"- ToolRegistry import failed: {e}")
        return False

    # Test Claude SDK import (optional)
    try:
        from claude_agent_orchestrator import ClaudeAgentOrchestrator
        print("+ ClaudeAgentOrchestrator import successful")
        claude_available = True
    except ImportError as e:
        print(f" ClaudeAgentOrchestrator import failed (expected if SDK not installed): {e}")
        claude_available = False

    # Test Tongyi import (fallback)
    try:
        from tongyi_orchestrator import TongyiOrchestrator
        print("+ TongyiOrchestrator import successful")
        tongyi_available = True
    except Exception as e:
        print(f" TongyiOrchestrator import failed: {e}")
        tongyi_available = False

    return claude_available or tongyi_available

def test_tool_registry():
    """Test ToolRegistry functionality."""
    print("\nTesting ToolRegistry...")

    try:
        from tool_registry import ToolRegistry

        # Create registry instance
        registry = ToolRegistry(root=".")

        # Test getting tools
        tools = registry.get_tools()
        print(f"+ ToolRegistry loaded {len(tools)} tools")

        # Test tool names
        tool_names = [tool.name for tool in tools]
        expected_tools = ["search_code", "read_file", "run_sandbox", "search_papers",
                         "clean_csv", "clean_markdown", "summarize_results"]

        for tool in expected_tools:
            if tool in tool_names:
                print(f"+ Tool '{tool}' available")
            else:
                print(f"- Tool '{tool}' missing")
                return False

        return True

    except Exception as e:
        print(f"- ToolRegistry test failed: {e}")
        return False

def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")

    try:
        from config import get_config, DEFAULT_CLAUDE_CONFIG, DEFAULT_TONGYI_CONFIG

        # Test config function
        config = get_config()

        if "tongyi" in config:
            print("+ Tongyi configuration loaded")
        else:
            print("- Tongyi configuration missing")
            return False

        if "claude" in config:
            print("+ Claude configuration loaded")
        else:
            print("- Claude configuration missing")
            return False

        if "tools" in config:
            print("+ Tools configuration loaded")
        else:
            print("- Tools configuration missing")
            return False

        # Test specific config values
        print(f"+ Claude model: {DEFAULT_CLAUDE_CONFIG.model_name}")
        print(f"+ Tongyi model: {DEFAULT_TONGYI_CONFIG.model_name}")

        return True

    except Exception as e:
        print(f"- Configuration test failed: {e}")
        return False

async def test_claude_orchestrator():
    """Test Claude Agent Orchestrator initialization (if available)."""
    print("\nTesting ClaudeAgentOrchestrator...")

    try:
        from claude_agent_orchestrator import ClaudeAgentOrchestrator

        # Try to initialize (may fail if SDK not installed)
        try:
            orchestrator = ClaudeAgentOrchestrator(root=".")
            print("+ ClaudeAgentOrchestrator initialized successfully")

            # Test session stats
            stats = orchestrator.get_session_stats()
            print(f"+ Session stats: {stats}")

            return True

        except Exception as e:
            print(f" ClaudeAgentOrchestrator initialization failed: {e}")
            return False

    except ImportError:
        print(" ClaudeAgentOrchestrator not available")
        return False

def test_cli_imports():
    """Test CLI module imports."""
    print("\nTesting CLI imports...")

    try:
        from tongyi_agent.cli import CLAUDE_ORCHESTRATOR_AVAILABLE, TONGYI_ORCHESTRATOR_AVAILABLE

        print(f"+ Claude orchestrator available: {CLAUDE_ORCHESTRATOR_AVAILABLE}")
        print(f"+ Tongyi orchestrator available: {TONGYI_ORCHESTRATOR_AVAILABLE}")

        if CLAUDE_ORCHESTRATOR_AVAILABLE or TONGYI_ORCHESTRATOR_AVAILABLE:
            print("+ At least one orchestrator is available")
            return True
        else:
            print("- No orchestrators available")
            return False

    except Exception as e:
        print(f"- CLI import test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("Tongyi Agent Refactoring Test Suite")
    print("=" * 50)

    tests = [
        test_imports,
        test_config,
        test_tool_registry,
        test_cli_imports,
    ]

    # Add async tests
    async_tests = [
        test_claude_orchestrator,
    ]

    # Run sync tests
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"- Test {test.__name__} crashed: {e}")
            results.append(False)

    # Run async tests
    for test in async_tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"- Async test {test.__name__} crashed: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"SUCCESS: All {total} tests passed!")
        print("Tongyi Agent refactoring completed successfully!")
    else:
        print(f"WARNING: {passed}/{total} tests passed")
        print("Some components may need attention.")

    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)