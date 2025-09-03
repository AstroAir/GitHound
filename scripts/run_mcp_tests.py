#!/usr/bin/env python3
"""
GitHound MCP Server Test Runner

Comprehensive test runner for GitHound MCP server following FastMCP testing best practices.
Provides different test suites for various testing scenarios.

Usage:
    python scripts/run_mcp_tests.py [test_suite]

Test Suites:
    unit        - Fast unit tests with in-memory testing
    integration - Integration tests requiring external services
    performance - Performance and scalability tests
    auth        - Authentication and authorization tests
    all         - All tests
    fastmcp     - Tests following FastMCP patterns only

Based on: https://gofastmcp.com/deployment/testing
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any


class MCPTestRunner:
    """Test runner for GitHound MCP server tests."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_suites = {
            "unit": {
                "description": "Fast unit tests with in-memory testing",
                "markers": "unit and not slow",
                "files": [
                    "tests/test_mcp_server.py::TestFastMCPInMemoryPatterns",
                    "tests/test_mcp_fastmcp_patterns.py::TestFastMCPInMemoryTesting",
                    "tests/test_mcp_fastmcp_patterns.py::TestMockingExternalDependencies",
                    "tests/test_mcp_fastmcp_patterns.py::TestErrorHandling",
                ]
            },
            "integration": {
                "description": "Integration tests requiring external services",
                "markers": "integration",
                "files": [
                    "tests/test_mcp_integration.py",
                ]
            },
            "performance": {
                "description": "Performance and scalability tests",
                "markers": "performance",
                "files": [
                    "tests/test_mcp_performance.py",
                ]
            },
            "auth": {
                "description": "Authentication and authorization tests",
                "markers": "auth",
                "files": [
                    "tests/test_mcp_authentication.py",
                ]
            },
            "fastmcp": {
                "description": "Tests following FastMCP patterns",
                "markers": "fastmcp",
                "files": [
                    "tests/test_mcp_fastmcp_patterns.py",
                    "tests/test_mcp_server.py::TestFastMCPInMemoryPatterns",
                ]
            },
            "all": {
                "description": "All tests",
                "markers": "",
                "files": ["tests/"]
            }
        }
    
    def run_test_suite(self, suite_name: str, extra_args: List[str] = None) -> int:
        """Run a specific test suite."""
        if suite_name not in self.test_suites:
            print(f"Error: Unknown test suite '{suite_name}'")
            print(f"Available suites: {', '.join(self.test_suites.keys())}")
            return 1
        
        suite = self.test_suites[suite_name]
        print(f"Running {suite_name} tests: {suite['description']}")
        print("-" * 60)
        
        # Build pytest command
        cmd = ["python", "-m", "pytest"]
        
        # Add markers if specified
        if suite["markers"]:
            cmd.extend(["-m", suite["markers"]])
        
        # Add test files/directories
        if suite["files"]:
            cmd.extend(suite["files"])
        
        # Add extra arguments
        if extra_args:
            cmd.extend(extra_args)
        
        # Run tests
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            return result.returncode
        except KeyboardInterrupt:
            print("\nTest execution interrupted by user")
            return 130
        except Exception as e:
            print(f"Error running tests: {e}")
            return 1
    
    def list_test_suites(self):
        """List available test suites."""
        print("Available test suites:")
        print("=" * 50)
        
        for name, suite in self.test_suites.items():
            print(f"{name:12} - {suite['description']}")
            if suite["markers"]:
                print(f"{'':12}   Markers: {suite['markers']}")
            print()
    
    def run_quick_check(self) -> int:
        """Run a quick check with essential tests."""
        print("Running quick check with essential FastMCP tests...")
        print("-" * 60)
        
        essential_tests = [
            "tests/test_mcp_server.py::TestMCPServerConfiguration::test_mcp_server_creation",
            "tests/test_mcp_server.py::TestFastMCPInMemoryPatterns::test_in_memory_server_instance",
            "tests/test_mcp_server.py::TestFastMCPInMemoryPatterns::test_in_memory_client_connection",
            "tests/test_mcp_fastmcp_patterns.py::TestFastMCPInMemoryTesting::test_in_memory_server_creation",
        ]
        
        cmd = ["python", "-m", "pytest", "-v"] + essential_tests
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            return result.returncode
        except Exception as e:
            print(f"Error running quick check: {e}")
            return 1
    
    def run_coverage_report(self) -> int:
        """Run tests with coverage reporting."""
        print("Running tests with coverage reporting...")
        print("-" * 60)
        
        cmd = [
            "python", "-m", "pytest",
            "--cov=githound",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml",
            "tests/"
        ]
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            if result.returncode == 0:
                print("\nCoverage report generated:")
                print("  - Terminal: displayed above")
                print("  - HTML: htmlcov/index.html")
                print("  - XML: coverage.xml")
            return result.returncode
        except Exception as e:
            print(f"Error running coverage: {e}")
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="GitHound MCP Server Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_mcp_tests.py unit           # Run unit tests
  python scripts/run_mcp_tests.py fastmcp       # Run FastMCP pattern tests
  python scripts/run_mcp_tests.py all --verbose # Run all tests with verbose output
  python scripts/run_mcp_tests.py --list        # List available test suites
  python scripts/run_mcp_tests.py --quick       # Run quick check
  python scripts/run_mcp_tests.py --coverage    # Run with coverage
        """
    )
    
    parser.add_argument(
        "suite",
        nargs="?",
        default="unit",
        help="Test suite to run (default: unit)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available test suites"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick check with essential tests"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage reporting"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--parallel", "-n",
        type=int,
        help="Run tests in parallel (number of workers)"
    )
    
    args, extra_args = parser.parse_known_args()
    
    runner = MCPTestRunner()
    
    # Handle special commands
    if args.list:
        runner.list_test_suites()
        return 0
    
    if args.quick:
        return runner.run_quick_check()
    
    if args.coverage:
        return runner.run_coverage_report()
    
    # Build extra arguments
    pytest_args = []
    
    if args.verbose:
        pytest_args.append("-v")
    
    if args.parallel:
        pytest_args.extend(["-n", str(args.parallel)])
    
    # Add any additional arguments
    pytest_args.extend(extra_args)
    
    # Run the specified test suite
    return runner.run_test_suite(args.suite, pytest_args)


if __name__ == "__main__":
    sys.exit(main())
