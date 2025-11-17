#!/usr/bin/env python3
"""
Simple debug script to test Claude Code SDK connection with OpenRouter
"""
import os
import sys
import asyncio
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_basic_connection():
    """Test basic Claude Code SDK connection"""
    print("Testing basic Claude Code SDK connection...")

    try:
        from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

        # Set OpenRouter environment variables
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("ERROR: OPENROUTER_API_KEY not found")
            return False

        os.environ["ANTHROPIC_API_KEY"] = api_key
        os.environ["ANTHROPIC_BASE_URL"] = "https://openrouter.ai/api/v1"

        print(f"Using API key: {api_key[:20]}...")
        print(f"Base URL: {os.environ['ANTHROPIC_BASE_URL']}")

        # Create minimal options
        options = ClaudeCodeOptions(
            allowed_tools=["Read"],
            model="anthropic/claude-3.5-haiku",
            max_turns=1,
            system_prompt="You are a test assistant. Respond briefly with 'OK'."
        )

        print("Creating client...")
        client = ClaudeSDKClient(options)

        print("Attempting connection...")
        start_time = time.time()

        try:
            await client.connect()
            print("Client connected successfully")

            await client.query("Hello, respond with just 'OK'")
            print("Query sent")

            response_received = False
            async for message in client.receive_response():
                print(f"Received message type: {type(message)}")
                if hasattr(message, 'content'):
                    print(f"Message has content: {len(message.content)} blocks")
                    for block in message.content:
                        if hasattr(block, 'text'):
                            print(f"Text block: {block.text}")
                            if 'OK' in block.text:
                                response_received = True
                                break
                if response_received:
                    break

            await client.disconnect()
            duration = time.time() - start_time
            print(f"Query completed in {duration:.2f}s")
            return response_received

        except asyncio.TimeoutError:
            print("TIMEOUT: Connection timed out")
            return False
        except Exception as e:
            print(f"CONNECTION ERROR: {e}")
            return False

    except ImportError as e:
        print(f"IMPORT ERROR: {e}")
        return False
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_env_var_combinations():
    """Test different environment variable combinations"""

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found")
        return False

    combinations = [
        ("ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL", {
            "ANTHROPIC_API_KEY": api_key,
            "ANTHROPIC_BASE_URL": "https://openrouter.ai/api/v1"
        }),
        ("OPENAI_API_KEY + OPENAI_BASE_URL", {
            "OPENAI_API_KEY": api_key,
            "OPENAI_BASE_URL": "https://openrouter.ai/api/v1"
        }),
        ("OPENROUTER_API_KEY only", {
            "OPENROUTER_API_KEY": api_key
        })
    ]

    for name, env_vars in combinations:
        print(f"\n--- Testing: {name} ---")

        # Clear environment
        for var in ["ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENROUTER_API_KEY"]:
            if var in os.environ:
                del os.environ[var]

        # Set test variables
        for var, value in env_vars.items():
            os.environ[var] = value
            print(f"  {var}={value[:20]}..." if 'KEY' in var else f"  {var}={value}")

        # Test connection
        try:
            result = asyncio.run(test_basic_connection())
            print(f"  RESULT: {'SUCCESS' if result else 'FAILED'}")
            if result:
                print(f"\n*** WORKING CONFIGURATION: {name} ***")
                return True
        except Exception as e:
            print(f"  ERROR: {e}")

    return False

if __name__ == "__main__":
    print("Claude Code SDK + OpenRouter Debug Script")
    print("=" * 50)

    success = test_env_var_combinations()

    if success:
        print("\nFound working configuration!")
    else:
        print("\nNo working configuration found.")
        print("\nPossible issues:")
        print("1. Claude Code SDK may not support custom base URLs")
        print("2. OpenRouter may require different authentication method")
        print("3. SDK may need specific configuration not covered by environment variables")