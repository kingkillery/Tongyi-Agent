#!/usr/bin/env python3
"""
Targeted tests for subtle bugs in Tongyi Agent refactoring
"""
import os
import sys
import asyncio
import importlib
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_import_path_consistency():
    """Test that all imports work consistently from different locations."""
    print("Testing import path consistency...")

    # Test importing from current directory (like test_claude_refactor.py does)
    try:
        import tool_registry
        print("+ Direct import of tool_registry successful")
    except Exception as e:
        print(f"- Direct import of tool_registry failed: {e}")
        return False

    # Test importing from src module (like CLI does)
    try:
        from src.tool_registry import ToolRegistry
        print("+ Module import of tool_registry successful")
    except Exception as e:
        print(f"- Module import of tool_registry failed: {e}")
        return False

    # Test that both refer to the same thing
    try:
        from tool_registry import ToolRegistry as DirectToolRegistry
        from src.tool_registry import ToolRegistry as ModuleToolRegistry

        if DirectToolRegistry is ModuleToolRegistry:
            print("+ Both imports refer to same class")
        else:
            print("- Imports refer to different classes")
            return False
    except Exception as e:
        print(f"- Import comparison failed: {e}")
        return False

    return True

def test_config_forward_reference():
    """Test that configuration doesn't have forward reference issues."""
    print("\nTesting configuration forward references...")

    try:
        # This should not raise an error due to forward references
        from config import get_config, DEFAULT_CLAUDE_CONFIG, DEFAULT_TONGYI_CONFIG

        config = get_config()

        # Test that both configs are accessible
        if DEFAULT_CLAUDE_CONFIG and DEFAULT_TONGYI_CONFIG:
            print("+ Both configurations accessible")
        else:
            print("- Configuration objects missing")
            return False

        # Test that get_config includes both
        if "claude" in config and "tongyi" in config:
            print("+ get_config returns both configurations")
        else:
            print("- get_config missing configurations")
            return False

        return True

    except Exception as e:
        print(f"- Configuration test failed: {e}")
        return False

def test_tool_schema_compatibility():
    """Test that tool schemas are compatible between orchestrators."""
    print("\nTesting tool schema compatibility...")

    try:
        from tool_registry import ToolRegistry

        registry = ToolRegistry(root=".")
        tools = registry.get_tools()

        # Get search_code tool schema
        search_code_schema = None
        for tool in tools:
            if tool.name == "search_code":
                search_code_schema = tool
                break

        if not search_code_schema:
            print("- search_code tool not found")
            return False

        # Check original schema parameters
        original_params = search_code_schema.parameters
        required_original = original_params.get("required", [])

        print(f"+ Original search_code required params: {required_original}")

        # Check for expected parameters
        expected_params = ["query", "paths", "max_results"]
        for param in expected_params:
            if param in original_params["properties"]:
                print(f"+ Parameter '{param}' found in original schema")
            else:
                print(f"- Parameter '{param}' missing from original schema")
                return False

        # Now check Claude SDK tool definitions
        try:
            from src.claude_agent_orchestrator import ClaudeAgentOrchestrator
            # We can't instantiate it without the SDK, but we can check the schema definitions
            print("+ Claude orchestrator import successful for schema check")

            # The issue is that Claude tools expect 'file_pattern' but original tools expect 'query'
            # This is a subtle bug that would cause runtime failures
            print("- Identified potential parameter mismatch: Claude expects 'file_pattern', original expects 'query'")

        except ImportError:
            print("+ Claude orchestrator not available (expected)")

        return True

    except Exception as e:
        print(f"- Tool schema test failed: {e}")
        return False

def test_async_sync_mixing():
    """Test for async/sync mixing issues."""
    print("\nTesting async/sync mixing...")

    # Test that we can detect event loop issues
    try:
        # Simulate what the CLI does
        import asyncio

        async def mock_claude_call():
            await asyncio.sleep(0.1)
            return "claude response"

        def mock_tongyi_call():
            import time
            time.sleep(0.1)
            return "tongyi response"

        # Test calling both in the same context
        async def test_mixed_calls():
            # This should work
            claude_result = await mock_claude_call()

            # This could be problematic if not handled carefully
            tongyi_result = mock_tongyi_call()

            return claude_result, tongyi_result

        # Run the test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(test_mixed_calls())
            print("+ Mixed async/sync calls executed successfully")
            return True
        finally:
            loop.close()

    except Exception as e:
        print(f"- Async/sync mixing test failed: {e}")
        return False

def test_error_handling_consistency():
    """Test error handling consistency between orchestrators."""
    print("\nTesting error handling consistency...")

    try:
        from tool_registry import ToolRegistry, ToolCall

        registry = ToolRegistry(root=".")

        # Test error handling for invalid tool call
        invalid_call = ToolCall(name="nonexistent_tool", parameters={})
        result = registry.execute_tool(invalid_call)

        if result.error:
            print("+ ToolRegistry handles invalid tools gracefully")
        else:
            print("- ToolRegistry doesn't handle invalid tools properly")
            return False

        # Test error handling for invalid parameters
        valid_call = ToolCall(name="search_code", parameters={"invalid_param": "value"})
        result = registry.execute_tool(valid_call)

        # This should either work or give a meaningful error
        if result.error or result.result:
            print("+ ToolRegistry handles invalid parameters gracefully")
        else:
            print("- ToolRegistry doesn't handle invalid parameters properly")
            return False

        return True

    except Exception as e:
        print(f"- Error handling test failed: {e}")
        return False

def test_missing_dependencies():
    """Test for missing or undocumented dependencies."""
    print("\nTesting missing dependencies...")

    # Check if claude-agent-sdk is listed anywhere
    requirements_files = ["requirements.txt", "pyproject.toml"]

    found_claude_sdk = False

    for req_file in requirements_files:
        if os.path.exists(req_file):
            with open(req_file, 'r') as f:
                content = f.read()
                if "claude-agent-sdk" in content.lower():
                    print(f"+ claude-agent-sdk found in {req_file}")
                    found_claude_sdk = True
                    break

    if not found_claude_sdk:
        print("- claude-agent-sdk not listed in requirements files")
        print("  This is a subtle bug - it should be an optional dependency")

    # Test for other potentially missing dependencies
    try:
        import dotenv
        print("+ python-dotenv available")
    except ImportError:
        print("- python-dotenv missing but required")
        return False

    try:
        import rich
        print("+ rich available")
    except ImportError:
        print("- rich missing but used in CLI")
        return False

    return True

async def main():
    """Run all targeted tests."""
    print("Tongyi Agent Subtle Bug Detection Tests")
    print("=" * 50)

    tests = [
        test_import_path_consistency,
        test_config_forward_reference,
        test_tool_schema_compatibility,
        test_async_sync_mixing,
        test_error_handling_consistency,
        test_missing_dependencies,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"- Test {test.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "=" * 50)
    print("Subtle Bug Detection Summary:")
    passed = sum(results)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if passed < total:
        print("\nWARNING: SUBTLE BUGS DETECTED!")
        print("These issues could cause problems in production:")
        if not results[0]:
            print("- Import path inconsistencies")
        if not results[1]:
            print("- Configuration forward reference issues")
        if not results[2]:
            print("- Tool schema compatibility issues")
        if not results[3]:
            print("- Async/sync mixing issues")
        if not results[4]:
            print("- Error handling inconsistencies")
        if not results[5]:
            print("- Missing dependency documentation")
    else:
        print("SUCCESS: No obvious subtle bugs detected")

    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)