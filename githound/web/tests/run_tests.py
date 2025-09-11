#!/usr/bin/env python3
"""
Test runner script for GitHound web frontend tests.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


class TestRunner:
    """Test runner for GitHound web frontend tests."""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent.parent.parent
        
    def run_command(self, command: List[str], cwd: Optional[Path] = None) -> int:
        """Run a command and return the exit code."""
        if cwd is None:
            cwd = self.test_dir
            
        print(f"Running: {' '.join(command)}")
        print(f"Working directory: {cwd}")
        
        result = subprocess.run(command, cwd=cwd)
        return result.returncode
    
    def setup_environment(self) -> None:
        """Set up the test environment."""
        # Set environment variables
        os.environ.update({
            "TESTING": "true",
            "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
            "REDIS_URL": "redis://localhost:6379/15",
            "GITHOUND_LOG_LEVEL": "WARNING",
        })
        
        # Create test result directories
        result_dirs = [
            "test-results/screenshots",
            "test-results/videos",
            "test-results/traces",
            "test-results/reports"
        ]
        
        for dir_path in result_dirs:
            (self.test_dir / dir_path).mkdir(parents=True, exist_ok=True)
    
    def install_dependencies(self) -> int:
        """Install test dependencies."""
        print("Installing Python dependencies...")
        exit_code = self.run_command([
            sys.executable, "-m", "pip", "install", "-e", ".[dev,test]"
        ], cwd=self.project_root)
        
        if exit_code != 0:
            return exit_code
        
        print("Installing Playwright...")
        exit_code = self.run_command([
            sys.executable, "-m", "pip", "install", "playwright", "pytest-playwright"
        ])
        
        if exit_code != 0:
            return exit_code
        
        print("Installing Playwright browsers...")
        return self.run_command(["playwright", "install"])
    
    def run_unit_tests(self) -> int:
        """Run unit tests."""
        print("\n=== Running Unit Tests ===")
        return self.run_command([
            "pytest", 
            str(self.project_root / "tests"),
            "-m", "unit and not slow",
            "--cov=githound.web",
            "--cov-report=html:test-results/coverage-html",
            "--cov-report=xml:test-results/coverage.xml",
            "--html=test-results/unit-test-report.html"
        ])
    
    def run_playwright_tests(self, browser: str = "chromium", headed: bool = False) -> int:
        """Run Playwright tests."""
        print(f"\n=== Running Playwright Tests ({browser}) ===")
        
        command = ["playwright", "test"]
        
        if browser != "all":
            command.extend(["--project", browser])
        
        if headed:
            command.append("--headed")
        
        command.extend([
            "--reporter=html:test-results/playwright-report",
            "--reporter=junit:test-results/playwright-results.xml"
        ])
        
        return self.run_command(command)
    
    def run_auth_tests(self, browser: str = "chromium") -> int:
        """Run authentication tests."""
        print(f"\n=== Running Authentication Tests ({browser}) ===")
        return self.run_command([
            "pytest", "auth/",
            f"--browser={browser}",
            "--html=test-results/auth-test-report.html"
        ])
    
    def run_search_tests(self, browser: str = "chromium") -> int:
        """Run search functionality tests."""
        print(f"\n=== Running Search Tests ({browser}) ===")
        return self.run_command([
            "pytest", "search/",
            f"--browser={browser}",
            "--html=test-results/search-test-report.html"
        ])
    
    def run_api_tests(self, browser: str = "chromium") -> int:
        """Run API integration tests."""
        print(f"\n=== Running API Integration Tests ({browser}) ===")
        return self.run_command([
            "pytest", "api/",
            f"--browser={browser}",
            "--html=test-results/api-test-report.html"
        ])
    
    def run_ui_tests(self, browser: str = "chromium") -> int:
        """Run UI/UX tests."""
        print(f"\n=== Running UI/UX Tests ({browser}) ===")
        return self.run_command([
            "pytest", "ui/",
            f"--browser={browser}",
            "--html=test-results/ui-test-report.html"
        ])
    
    def run_performance_tests(self, browser: str = "chromium") -> int:
        """Run performance tests."""
        print(f"\n=== Running Performance Tests ({browser}) ===")
        return self.run_command([
            "pytest", "performance/",
            f"--browser={browser}",
            "--html=test-results/performance-test-report.html"
        ])
    
    def run_accessibility_tests(self, browser: str = "chromium") -> int:
        """Run accessibility tests."""
        print(f"\n=== Running Accessibility Tests ({browser}) ===")
        return self.run_command([
            "pytest", "ui/test_accessibility.py",
            f"--browser={browser}",
            "--html=test-results/accessibility-test-report.html"
        ])
    
    def run_smoke_tests(self, browser: str = "chromium") -> int:
        """Run smoke tests."""
        print(f"\n=== Running Smoke Tests ({browser}) ===")
        return self.run_command([
            "pytest", 
            "-m", "smoke",
            f"--browser={browser}",
            "--html=test-results/smoke-test-report.html"
        ])
    
    def run_all_tests(self, browser: str = "chromium", headed: bool = False) -> int:
        """Run all test suites."""
        print("\n=== Running All Tests ===")
        
        test_suites = [
            ("Unit Tests", self.run_unit_tests),
            ("Authentication Tests", lambda: self.run_auth_tests(browser)),
            ("Search Tests", lambda: self.run_search_tests(browser)),
            ("API Tests", lambda: self.run_api_tests(browser)),
            ("UI Tests", lambda: self.run_ui_tests(browser)),
            ("Performance Tests", lambda: self.run_performance_tests(browser)),
            ("Accessibility Tests", lambda: self.run_accessibility_tests(browser)),
        ]
        
        results = {}
        overall_success = True
        
        for suite_name, test_func in test_suites:
            print(f"\n{'='*50}")
            print(f"Running {suite_name}")
            print(f"{'='*50}")
            
            exit_code = test_func()
            results[suite_name] = exit_code
            
            if exit_code != 0:
                overall_success = False
                print(f"❌ {suite_name} failed with exit code {exit_code}")
            else:
                print(f"✅ {suite_name} passed")
        
        # Print summary
        print(f"\n{'='*50}")
        print("TEST SUMMARY")
        print(f"{'='*50}")
        
        for suite_name, exit_code in results.items():
            status = "✅ PASS" if exit_code == 0 else "❌ FAIL"
            print(f"{suite_name}: {status}")
        
        print(f"\nOverall result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        return 0 if overall_success else 1
    
    def generate_report(self) -> None:
        """Generate a comprehensive test report."""
        print("\n=== Generating Test Report ===")
        
        # This would generate a comprehensive HTML report combining all test results
        # For now, we'll just list the available reports
        
        report_files = list((self.test_dir / "test-results").glob("*.html"))
        
        print("Available test reports:")
        for report_file in report_files:
            print(f"  - {report_file.name}: file://{report_file.absolute()}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="GitHound Web Frontend Test Runner")
    
    parser.add_argument(
        "command",
        choices=[
            "install", "unit", "playwright", "auth", "search", "api", 
            "ui", "performance", "accessibility", "smoke", "all", "report"
        ],
        help="Test command to run"
    )
    
    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit", "all"],
        default="chromium",
        help="Browser to use for tests"
    )
    
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run tests in headed mode (visible browser)"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    runner.setup_environment()
    
    command_map = {
        "install": runner.install_dependencies,
        "unit": runner.run_unit_tests,
        "playwright": lambda: runner.run_playwright_tests(args.browser, args.headed),
        "auth": lambda: runner.run_auth_tests(args.browser),
        "search": lambda: runner.run_search_tests(args.browser),
        "api": lambda: runner.run_api_tests(args.browser),
        "ui": lambda: runner.run_ui_tests(args.browser),
        "performance": lambda: runner.run_performance_tests(args.browser),
        "accessibility": lambda: runner.run_accessibility_tests(args.browser),
        "smoke": lambda: runner.run_smoke_tests(args.browser),
        "all": lambda: runner.run_all_tests(args.browser, args.headed),
        "report": runner.generate_report,
    }
    
    if args.command in command_map:
        exit_code = command_map[args.command]()
        if exit_code is None:
            exit_code = 0
        sys.exit(exit_code)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
