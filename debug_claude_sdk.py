#!/usr/bin/env python3
"""
Debug script to test Claude Code SDK connection with OpenRouter
Tests different environment variable configurations to identify the correct approach
"""
import os
import sys
import asyncio
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_environment_configurations():
    """Test different environment variable configurations for OpenRouter"""

    print("=" * 80)
    print("CLAUDE CODE SDK + OPENROUTER CONNECTION DEBUG")
    print("=" * 80)

    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found in environment")
        return False

    print(f"SUCCESS: Found OpenRouter API key: {api_key[:20]}...")

    # Test configurations
    configurations = [
        {
            "name": "Current Implementation (ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL)",
            "env_vars": {
                "ANTHROPIC_API_KEY": api_key,
                "ANTHROPIC_BASE_URL": "https://openrouter.ai/api/v1"
            }
        },
        {
            "name": "OpenAI Compatible (OPENAI_API_KEY + OPENAI_BASE_URL)",
            "env_vars": {
                "OPENAI_API_KEY": api_key,
                "OPENAI_BASE_URL": "https://openrouter.ai/api/v1"
            }
        },
        {
            "name": "OpenRouter Native (OPENROUTER_API_KEY + OPENROUTER_BASE_URL)",
            "env_vars": {
                "OPENROUTER_API_KEY": api_key,
                "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1"
            }
        },
        {
            "name": "Claude Native (CLAUDE_API_KEY + CLAUDE_BASE_URL)",
            "env_vars": {
                "CLAUDE_API_KEY": api_key,
                "CLAUDE_BASE_URL": "https://openrouter.ai/api/v1"
            }
        },
        {
            "name": "Mixed Approach (ANTHROPIC_API_KEY + CLAUDE_BASE_URL)",
            "env_vars": {
                "ANTHROPIC_API_KEY": api_key,
                "CLAUDE_BASE_URL": "https://openrouter.ai/api/v1"
            }
        }
    ]

    results = []

    for config in configurations:
        print(f"\n🧪 Testing: {config['name']}")
        print("-" * 60)

        # Clear existing environment variables first
        env_vars_to_clear = [
            "ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL",
            "OPENAI_API_KEY", "OPENAI_BASE_URL",
            "OPENROUTER_API_KEY", "OPENROUTER_BASE_URL",
            "CLAUDE_API_KEY", "CLAUDE_BASE_URL"
        ]

        original_values = {}
        for var in env_vars_to_clear:
            if var in os.environ:
                original_values[var] = os.environ[var]
                del os.environ[var]

        # Set test configuration
        for var, value in config["env_vars"].items():
            os.environ[var] = value
            print(f"   {var}={value}")

        # Test the configuration
        try:
            success = test_claude_sdk_connection()
            results.append({
                "config": config["name"],
                "success": success,
                "env_vars": config["env_vars"]
            })
            print(f"   {'✅ SUCCESS' if success else '❌ FAILED'}")
        except Exception as e:
            results.append({
                "config": config["name"],
                "success": False,
                "error": str(e),
                "env_vars": config["env_vars"]
            })
            print(f"   ❌ ERROR: {e}")

        # Restore original environment
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]

        for var, value in original_values.items():
            os.environ[var] = value

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    successful_configs = [r for r in results if r["success"]]

    if successful_configs:
        print("✅ Successful configurations:")
        for result in successful_configs:
            print(f"   🎯 {result['config']}")
            for var, value in result["env_vars"].items():
                print(f"      {var}={value}")
    else:
        print("❌ No configurations succeeded. All failed.")
        print("\n🔍 Error details:")
        for result in results:
            if not result["success"]:
                print(f"   ❌ {result['config']}: {result.get('error', 'Unknown error')}")

    return len(successful_configs) > 0

def test_claude_sdk_connection():
    """Test connection to Claude Code SDK with current environment"""
    try:
        from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

        # Create minimal options
        options = ClaudeCodeOptions(
            allowed_tools=["Read"],  # Minimal tool set
            model="anthropic/claude-3.5-haiku",  # Use cheaper model for testing
            max_turns=1,  # Limit to 1 turn for quick test
            system_prompt="You are a test assistant. Respond briefly."
        )

        # Create client
        client = ClaudeSDKClient(options)

        # Test quick connection
        print("   🔄 Initializing SDK client...")

        # Try a simple query with timeout
        start_time = time.time()
        timeout = 30  # 30 second timeout

        async def test_query():
            try:
                await client.connect()
                await client.query("Hello, respond with just 'OK'")

                response_received = False
                async for message in client.receive_response():
                    if hasattr(message, 'content'):
                        for block in message.content:
                            if hasattr(block, 'text'):
                                if 'OK' in block.text:
                                    response_received = True
                                    break
                    if response_received:
                        break

                await client.disconnect()
                return response_received

            except Exception as e:
                if hasattr(client, 'is_connected') and client.is_connected:
                    try:
                        await client.disconnect()
                    except:
                        pass
                raise e

        # Run the async test with timeout
        try:
            result = asyncio.run(asyncio.wait_for(test_query(), timeout=timeout))
            duration = time.time() - start_time
            print(f"   ⏱️  Query completed in {duration:.2f}s")
            return result
        except asyncio.TimeoutError:
            print(f"   ⏰ TIMEOUT after {timeout}s")
            return False

    except ImportError as e:
        print(f"   📦 Import error: {e}")
        return False
    except Exception as e:
        print(f"   💥 Connection error: {e}")
        return False

def inspect_sdk_behavior():
    """Inspect SDK internals to understand configuration loading"""
    print("\n🔍 INSPECTING SDK BEHAVIOR")
    print("-" * 40)

    try:
        from claude_code_sdk import _internal
        print("Available internal modules:", dir(_internal))
    except:
        print("Could not access _internal module")

    # Check if SDK reads any specific config files
    home_dir = Path.home()
    potential_configs = [
        home_dir / ".claude" / "settings.json",
        home_dir / ".config" / "claude" / "settings.json",
        Path.cwd() / ".claude" / "settings.json"
    ]

    print("\n📁 Checking for configuration files:")
    for config_path in potential_configs:
        if config_path.exists():
            print(f"   ✅ Found: {config_path}")
            try:
                with open(config_path, 'r') as f:
                    print(f"      Content: {f.read()[:200]}...")
            except:
                print("      Could not read content")
        else:
            print(f"   ❌ Not found: {config_path}")

if __name__ == "__main__":
    print("Starting Claude Code SDK + OpenRouter debugging...")

    # Inspect SDK behavior first
    inspect_sdk_behavior()

    # Test different configurations
    success = test_environment_configurations()

    if success:
        print("\n🎉 At least one configuration works! Check the summary above.")
        sys.exit(0)
    else:
        print("\n💥 All configurations failed. Further investigation needed.")
        sys.exit(1)