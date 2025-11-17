#!/usr/bin/env python3
"""
Test script for PDF tools functionality.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pdf_tools import get_pdf_processor, PDFProcessor

def test_pdf_tools():
    """Test PDF tools functionality."""
    print("Testing PDF Tools...")

    # Test PDF processor initialization
    try:
        processor = get_pdf_processor()
        print("✓ PDF processor initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize PDF processor: {e}")
        return False

    # Test tool registry integration
    try:
        from tool_registry import ToolRegistry
        registry = ToolRegistry(".")
        tools = registry.get_tools()

        pdf_tools = [tool for tool in tools if tool.name.startswith('pdf_')]
        print(f"✓ Found {len(pdf_tools)} PDF tools in registry:")
        for tool in pdf_tools:
            print(f"  - {tool.name}: {tool.description}")

    except Exception as e:
        print(f"✗ Failed to test tool registry: {e}")
        return False

    # Test tool execution (with dummy parameters)
    try:
        from tool_registry import ToolCall

        # Test pdf_info tool
        info_call = ToolCall(name="pdf_info", parameters={"path": "test.pdf"})
        result = registry.execute_tool(info_call)

        if result.error:
            print(f"✓ PDF info tool handles missing file correctly: {result.error}")
        else:
            print("✗ PDF info tool should have failed for missing file")

    except Exception as e:
        print(f"✗ Failed to test tool execution: {e}")
        return False

    print("\n✓ PDF tools integration test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_pdf_tools()
    sys.exit(0 if success else 1)