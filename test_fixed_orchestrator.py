#!/usr/bin/env python3
"""
Test script to verify the fixed ClaudeAgentOrchestrator works with OpenRouter
"""
import os
import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_orchestrator():
    """Test the fixed ClaudeAgentOrchestrator"""
    print("Testing fixed ClaudeAgentOrchestrator...")

    try:
        from claude_agent_orchestrator import ClaudeAgentOrchestrator

        print("SUCCESS: Successfully imported ClaudeAgentOrchestrator")

        # Initialize orchestrator
        print("INITIALIZING: ClaudeAgentOrchestrator...")
        orchestrator = ClaudeAgentOrchestrator()

        print("SUCCESS: ClaudeAgentOrchestrator initialized successfully")

        # Test a simple query
        print("TESTING: Processing simple query...")
        test_query = "Hello, please respond with a brief greeting and tell me what tools you have access to."

        response = await orchestrator.process_query(test_query)

        print("SUCCESS: Query processed successfully!")
        print(f"\nResponse: {response[:500]}...")

        # Get session stats
        stats = orchestrator.get_session_stats()
        print(f"\nSession Stats: {stats}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_environment():
    """Check environment setup"""
    print("Checking environment setup...")

    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        print(f"SUCCESS: OPENROUTER_API_KEY: {api_key[:20]}...")
    else:
        print("ERROR: OPENROUTER_API_KEY not found")
        return False

    # Check for conflicting variables
    conflicting_vars = ["ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "OPENAI_API_KEY", "OPENAI_BASE_URL"]
    conflicts = []
    for var in conflicting_vars:
        if var in os.environ:
            conflicts.append(var)

    if conflicts:
        print(f"WARNING: Conflicting environment variables found: {conflicts}")
        print("These should be cleared for optimal performance")
    else:
        print("SUCCESS: No conflicting environment variables")

    return True

if __name__ == "__main__":
    print("ClaudeAgentOrchestrator Verification Test")
    print("=" * 50)

    # Check environment first
    if not check_environment():
        print("\nERROR: Environment setup failed")
        sys.exit(1)

    print("\n" + "=" * 50)

    # Test orchestrator
    success = asyncio.run(test_orchestrator())

    if success:
        print("\nSUCCESS: ClaudeAgentOrchestrator test PASSED!")
        print("The OpenRouter integration is working correctly.")
    else:
        print("\nFAILED: ClaudeAgentOrchestrator test FAILED!")
        print("Further debugging may be needed.")
        sys.exit(1)