#!/usr/bin/env python3
"""
Simple Test Runner for GitHound

This script manually runs tests without pytest to identify and fix issues.
"""

import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test basic imports to identify missing dependencies."""
    print("Testing basic imports...")
    
    tests = [
        ("pathlib", "pathlib"),
        ("typing", "typing"),
        ("asyncio", "asyncio"),
        ("unittest.mock", "unittest.mock"),
    ]
    
    failed_imports = []
    
    for module_name, description in tests:
        try:
            __import__(module_name)
            print(f"✓ {description}")
        except ImportError as e:
            print(f"✗ {description}: {e}")
            failed_imports.append((module_name, str(e)))
    
    return failed_imports

def test_githound_imports():
    """Test GitHound module imports."""
    print("\nTesting GitHound imports...")
    
    githound_modules = [
        "githound",
        "githound.models",
        "githound.git_handler",
        "githound.mcp_server",
    ]
    
    failed_imports = []
    
    for module_name in githound_modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except ImportError as e:
            print(f"✗ {module_name}: {e}")
            failed_imports.append((module_name, str(e)))
        except Exception as e:
            print(f"✗ {module_name}: {type(e).__name__}: {e}")
            failed_imports.append((module_name, f"{type(e).__name__}: {e}"))
    
    return failed_imports

def test_basic_functionality():
    """Test basic functionality that doesn't require external dependencies."""
    print("\nTesting basic functionality...")
    
    try:
        # Test models
        from githound.models import GitHoundConfig
        config = GitHoundConfig(repo_path=".", search_query="test")
        print(f"✓ GitHoundConfig created: {config.repo_path}")
        
        return []
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        traceback.print_exc()
        return [("basic_functionality", str(e))]

def test_git_operations():
    """Test Git operations if GitPython is available."""
    print("\nTesting Git operations...")
    
    try:
        from githound.git_handler import get_repository
        # Try to get repository for current directory
        repo = get_repository(".")
        print(f"✓ Git repository loaded: {repo.working_dir}")
        return []
    except ImportError as e:
        print(f"✗ GitPython not available: {e}")
        return [("git_operations", f"GitPython not available: {e}")]
    except Exception as e:
        print(f"✗ Git operations failed: {e}")
        return [("git_operations", str(e))]

def test_mcp_server():
    """Test MCP server functionality if FastMCP is available."""
    print("\nTesting MCP server...")
    
    try:
        from githound.mcp_server import get_mcp_server
        server = get_mcp_server()
        print(f"✓ MCP server created: {server.name}")
        return []
    except ImportError as e:
        print(f"✗ FastMCP not available: {e}")
        return [("mcp_server", f"FastMCP not available: {e}")]
    except Exception as e:
        print(f"✗ MCP server test failed: {e}")
        return [("mcp_server", str(e))]

def main():
    """Run all tests and report results."""
    print("GitHound Simple Test Runner")
    print("=" * 50)
    
    all_failures = []
    
    # Run tests
    all_failures.extend(test_imports())
    all_failures.extend(test_githound_imports())
    all_failures.extend(test_basic_functionality())
    all_failures.extend(test_git_operations())
    all_failures.extend(test_mcp_server())
    
    # Report results
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    if not all_failures:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {len(all_failures)} test(s) failed:")
        for test_name, error in all_failures:
            print(f"  - {test_name}: {error}")
        
        print("\nRequired dependencies to install:")
        dependencies = set()
        for test_name, error in all_failures:
            if "git" in error.lower():
                dependencies.add("GitPython")
            if "fastmcp" in error.lower():
                dependencies.add("fastmcp")
            if "pydantic" in error.lower():
                dependencies.add("pydantic")
            if "typer" in error.lower():
                dependencies.add("typer")
            if "ripgrepy" in error.lower():
                dependencies.add("ripgrepy")
        
        if dependencies:
            print("  pip install " + " ".join(dependencies))
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
