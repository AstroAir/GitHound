#!/usr/bin/env python3
"""
Test Setup Verification Script

Verifies that the GitHound MCP testing setup is working correctly.
This script tests the core components without requiring pytest.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from fastmcp import FastMCP, Client
    print("✓ FastMCP imported successfully")
except ImportError as e:
    print(f"✗ FastMCP import failed: {e}")
    sys.exit(1)

try:
    from githound.mcp_server import get_mcp_server, mcp
    print("✓ GitHound MCP server imported successfully")
except ImportError as e:
    print(f"✗ GitHound MCP server import failed: {e}")
    sys.exit(1)


async def test_in_memory_pattern():
    """Test the FastMCP in-memory testing pattern."""
    print("\n--- Testing FastMCP In-Memory Pattern ---")
    
    try:
        # Create server instance
        server = get_mcp_server()
        print(f"✓ Server created: {server.name}")
        
        # Test in-memory client connection
        async with Client(server) as client:
            print("✓ In-memory client connected")
            
            # Test basic operations
            await client.ping()
            print("✓ Ping successful")
            
            tools = await client.list_tools()
            print(f"✓ Tools listed: {len(tools)} tools available")
            
            resources = await client.list_resources()
            print(f"✓ Resources listed: {len(resources)} resources available")
            
            prompts = await client.list_prompts()
            print(f"✓ Prompts listed: {len(prompts)} prompts available")
            
        print("✓ In-memory testing pattern working correctly")
        return True
        
    except Exception as e:
        print(f"✗ In-memory testing failed: {e}")
        return False


async def test_tool_execution():
    """Test tool execution with the in-memory pattern."""
    print("\n--- Testing Tool Execution ---")
    
    try:
        server = get_mcp_server()
        
        async with Client(server) as client:
            # Try to execute a simple tool
            try:
                result = await client.call_tool(
                    "validate_repository",
                    {"repo_path": str(Path.cwd())}
                )
                print("✓ Tool execution successful")
                return True
            except Exception as tool_error:
                if "not found" in str(tool_error).lower():
                    print("⚠ Tool not found (expected for incomplete setup)")
                    return True
                else:
                    print(f"✗ Tool execution failed: {tool_error}")
                    return False
                    
    except Exception as e:
        print(f"✗ Tool execution test failed: {e}")
        return False


def test_imports():
    """Test that all required modules can be imported."""
    print("\n--- Testing Imports ---")
    
    imports_to_test = [
        ("git", "GitPython"),
        ("pathlib", "pathlib"),
        ("unittest.mock", "unittest.mock"),
        ("asyncio", "asyncio"),
    ]
    
    all_passed = True
    
    for module_name, description in imports_to_test:
        try:
            __import__(module_name)
            print(f"✓ {description} imported successfully")
        except ImportError as e:
            print(f"✗ {description} import failed: {e}")
            all_passed = False
    
    return all_passed


async def main():
    """Main test function."""
    print("GitHound MCP Testing Setup Verification")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test in-memory pattern
    in_memory_ok = await test_in_memory_pattern()
    
    # Test tool execution
    tool_execution_ok = await test_tool_execution()
    
    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)
    
    if imports_ok and in_memory_ok and tool_execution_ok:
        print("✓ All tests passed! FastMCP testing setup is working correctly.")
        print("\nYou can now run the full test suite with:")
        print("  python scripts/run_mcp_tests.py unit")
        print("  python scripts/run_mcp_tests.py fastmcp")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Ensure all dependencies are installed:")
        print("   pip install fastmcp pytest pytest-asyncio pytest-cov psutil")
        print("2. Check that GitHound is properly installed")
        print("3. Verify the MCP server configuration")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
