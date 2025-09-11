#!/usr/bin/env python3
"""
GitHound Health Check

This script performs comprehensive health checks on the GitHound system,
including dependencies, configuration, services, and performance.

Usage:
    python scripts/health-check.py [command] [options]

Commands:
    check       - Run health checks
    report      - Generate detailed health report
    monitor     - Continuous health monitoring
    benchmark   - Performance benchmarks
"""

from utils import (
    check_command_exists,
    check_python_version,
    check_virtual_env,
    console,
    get_git_info,
    get_platform_info,
    get_project_root,
    get_python_info,
    print_error,
    print_header,
    print_info,
    print_section,
    print_step,
    print_success,
    print_warning,
    run_command_with_output,
    StatusContext,
)
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.table import Table

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))


app = typer.Typer(
    name="health-check",
    help="GitHound Health Check System",
    add_completion=False,
)


class HealthChecker:
    """Comprehensive health checker for GitHound."""

    def __init__(self) -> None:
        self.project_root = get_project_root()
        self.checks = {}
        self.start_time = None

    def add_check_result(self, category: str, check_name: str, passed: bool, details: str = "", warning: bool = False) -> None:
        """Add a check result."""
        if category not in self.checks:
            self.checks[category] = {}

        self.checks[category][check_name] = {
            "passed": passed,
            "details": details,
            "warning": warning,
            "timestamp": datetime.now().isoformat(),
        }

    def check_system_health(self) -> Dict[str, bool]:
        """Check system health."""
        print_section("System Health")

        results: dict[str, Any] = {}

        # Python version
        python_ok = check_python_version((3, 11))
        print_step("Python 3.11+", "success" if python_ok else "error")
        self.add_check_result("system", "python_version", python_ok,
                              f"Python {'.'.join(map(str, sys.version_info[:3]))}")
        results["python"] = python_ok

        # Virtual environment
        venv_ok = check_virtual_env()
        print_step("Virtual environment", "success" if venv_ok else "error")
        self.add_check_result("system", "virtual_env", venv_ok)
        results["venv"] = venv_ok

        # Required commands
        required_commands = ["git", "python", "pip"]
        for cmd in required_commands:
            cmd_ok = check_command_exists(cmd)
            print_step(f"Command: {cmd}", "success" if cmd_ok else "error")
            self.add_check_result("system", f"command_{cmd}", cmd_ok)
            results[f"cmd_{cmd}"] = cmd_ok

        # Optional but recommended commands
        optional_commands = ["rg", "ripgrep", "pre-commit"]
        for cmd in optional_commands:
            cmd_ok = check_command_exists(cmd)
            status = "success" if cmd_ok else "skip"
            print_step(f"Optional: {cmd}", status)
            self.add_check_result(
                "system", f"optional_{cmd}", cmd_ok, warning=not cmd_ok)
            results[f"opt_{cmd}"] = cmd_ok

        return results

    def check_dependencies(self) -> Dict[str, bool]:
        """Check Python dependencies."""
        print_section("Dependencies")

        results: dict[str, Any] = {}

        # Core dependencies
        core_deps = [
            "githound", "typer", "rich", "pydantic", "fastapi",
            "GitPython", "ripgrepy", "rapidfuzz"
        ]

        for dep in core_deps:
            try:
                if dep == "githound":
                    # Special check for editable install
                    exit_code, stdout, _ = run_command_with_output(
                        ["pip", "show", "githound"])
                    dep_ok = exit_code == 0 and "editable" in stdout.lower()
                    details = "editable install" if dep_ok else "not installed or not editable"
                else:
                    exit_code, _, _ = run_command_with_output([
                        "python", "-c", f"import {dep.replace('-', '_')}"
                    ])
                    dep_ok = exit_code == 0
                    details = "available" if dep_ok else "missing"

                print_step(f"Dependency: {dep}",
                           "success" if dep_ok else "error")
                self.add_check_result("dependencies", dep, dep_ok, details)
                results[dep] = dep_ok

            except Exception as e:
                print_step(f"Dependency: {dep}", "error")
                self.add_check_result("dependencies", dep, False, str(e))
                results[dep] = False

        # Development dependencies
        dev_deps = ["pytest", "black", "isort", "ruff", "mypy"]
        for dep in dev_deps:
            try:
                exit_code, _, _ = run_command_with_output([
                    "python", "-c", f"import {dep}"
                ])
                dep_ok = exit_code == 0
                status = "success" if dep_ok else "skip"
                print_step(f"Dev dependency: {dep}", status)
                self.add_check_result("dev_dependencies",
                                      dep, dep_ok, warning=not dep_ok)
                results[f"dev_{dep}"] = dep_ok

            except Exception:
                print_step(f"Dev dependency: {dep}", "skip")
                self.add_check_result("dev_dependencies",
                                      dep, False, warning=True)
                results[f"dev_{dep}"] = False

        return results

    def check_configuration(self) -> Dict[str, bool]:
        """Check configuration files."""
        print_section("Configuration")

        results: dict[str, Any] = {}

        # Required configuration files
        config_files = [
            ("pyproject.toml", "Project configuration"),  # [attr-defined]
            ("README.md", "Documentation"),
            (".gitignore", "Git ignore rules"),
        ]

        for filename, description in config_files:
            file_path = self.project_root / filename
            file_ok = file_path.exists()
            print_step(f"{description}", "success" if file_ok else "error")
            self.add_check_result("configuration", filename, file_ok)  # [attr-defined]
            results[filename] = file_ok

        # Optional configuration files
        optional_configs = [
            (".pre-commit-config.yaml", "Pre-commit hooks"),  # [attr-defined]
            ("mkdocs.yml", "Documentation config"),  # [attr-defined]
            ("pytest.ini", "Test configuration"),  # [attr-defined]
        ]

        for filename, description in optional_configs:
            file_path = self.project_root / filename
            file_ok = file_path.exists()
            status = "success" if file_ok else "skip"
            print_step(f"{description}", status)
            self.add_check_result("configuration", filename,  # [attr-defined]
                                  file_ok, warning=not file_ok)
            results[filename] = file_ok

        return results

    def check_git_health(self) -> Dict[str, bool]:
        """Check Git repository health."""
        print_section("Git Repository")

        results: dict[str, Any] = {}

        git_info = get_git_info()

        if git_info:
            print_step("Git repository", "success")
            self.add_check_result("git", "repository", True,
                                  f"Branch: {git_info.get if git_info is not None else None('branch', 'unknown')}")
            results["repository"] = True

            # Check for uncommitted changes
            clean = not git_info.get("dirty", True)
            print_step("Working directory clean",
                       "success" if clean else "warning")
            self.add_check_result(
                "git", "clean_working_dir", clean, warning=not clean)
            results["clean"] = clean

            # Check remote
            if git_info.get("remote"):
                print_step("Remote configured", "success")
                self.add_check_result(
                    "git", "remote", True, git_info["remote"])
                results["remote"] = True
            else:
                print_step("Remote configured", "warning")
                self.add_check_result("git", "remote", False, warning=True)
                results["remote"] = False
        else:
            print_step("Git repository", "error")
            self.add_check_result("git", "repository", False)
            results["repository"] = False

        return results

    def check_services(self) -> Dict[str, bool]:
        """Check service health."""
        print_section("Services")

        results: dict[str, Any] = {}

        # Import services manager
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from services import ServiceManager

            manager = ServiceManager()

            for service_name in ["web", "mcp"]:
                running, pid = manager.is_service_running(service_name)
                status = "success" if running else "skip"
                print_step(f"{service_name.upper()} service", status)

                details = f"PID: {pid}" if running else "not running"
                self.add_check_result(
                    "services", service_name, running, details, warning=not running)
                results[service_name] = running

        except Exception as e:
            print_step("Service check", "error")
            self.add_check_result("services", "check_failed", False, str(e))
            results["check_failed"] = False

        return results

    def run_performance_benchmark(self) -> Dict[str, float]:
        """Run basic performance benchmarks."""
        print_section("Performance Benchmark")

        benchmarks: dict[str, Any] = {}

        try:
            # Import time
            start = time.time()
            import githound
            import_time = time.time() - start
            benchmarks["import_time"] = import_time

            print_step(f"Import time: {import_time:.3f}s",
                       "success" if import_time < 1.0 else "warning")
            self.add_check_result("performance", "import_time", import_time < 1.0,
                                  f"{import_time:.3f}s", warning=import_time >= 1.0)

            # Basic functionality test
            start = time.time()
            from githound.models import SearchQuery
            query = SearchQuery(content_pattern="test")
            basic_time = time.time() - start
            benchmarks["basic_ops_time"] = basic_time

            print_step(f"Basic operations: {basic_time:.3f}s",
                       "success" if basic_time < 0.1 else "warning")
            self.add_check_result("performance", "basic_ops", basic_time < 0.1,
                                  f"{basic_time:.3f}s", warning=basic_time >= 0.1)

        except Exception as e:
            print_step("Performance benchmark", "error")
            self.add_check_result(
                "performance", "benchmark_failed", False, str(e))

        return benchmarks

    def generate_health_report(self) -> Dict:
        """Generate comprehensive health report."""
        self.start_time = datetime.now()

        print_header("GitHound Health Check")

        # Run all checks
        system_results = self.check_system_health()
        dep_results = self.check_dependencies()
        config_results = self.check_configuration()  # [attr-defined]
        git_results = self.check_git_health()
        service_results = self.check_services()
        perf_results = self.run_performance_benchmark()

        # Calculate summary
        all_results = {
            **system_results, **dep_results, **config_results,
            **git_results, **service_results
        }

        total_checks = len(all_results)
        passed_checks = sum(1 for result in all_results.values() if result)
        failed_checks = total_checks - passed_checks

        # Count warnings
        warning_count = sum(
            1 for category in self.checks.values()
            for check in category.values()
            if check.get("warning", False)
        )

        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        report = {
            "timestamp": self.start_time.isoformat(),
            "duration": duration,
            "summary": {
                "total_checks": total_checks,
                "passed": passed_checks,
                "failed": failed_checks,
                "warnings": warning_count,
                "health_score": (passed_checks / total_checks * 100) if total_checks > 0 else 0,
            },
            "system_info": {
                "python": get_python_info(),
                "platform": get_platform_info(),
                "git": get_git_info(),
            },
            "checks": self.checks,
            "benchmarks": perf_results,
        }

        return report


@app.command()
def check(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose output"),
    save_report: bool = typer.Option(
        False, "--save", "-s", help="Save report to file"),
) -> None:
    """Run comprehensive health checks."""
    checker = HealthChecker()
    report = checker.generate_health_report()

    # Print summary
    print_section("Health Check Summary")
    summary = report["summary"]

    if summary["failed"] == 0:
        print_success(f"All {summary['total_checks']} checks passed! ✨")
    else:
        print_warning(
            f"{summary['passed']}/{summary['total_checks']} checks passed")
        print_info(f"Failed: {summary['failed']}")
        print_info(f"Warnings: {summary['warnings']}")

    print_info(f"Health Score: {summary['health_score']:.1f}%")
    print_info(f"Check Duration: {report['duration']:.2f}s")

    if save_report:
        report_file = Path("health-report.json")
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print_info(f"Report saved to: {report_file}")

    # Exit with error code if checks failed
    if summary["failed"] > 0:
        sys.exit(1)


@app.command()
def report(
    output: str = typer.Option(
        "health-report.json", "--output", "-o", help="Output file"),
    format: str = typer.Option(
        "json", "--format", "-f", help="Output format (json, yaml)"),
) -> None:
    """Generate detailed health report."""
    checker = HealthChecker()
    report = checker.generate_health_report()

    output_path = Path(output)

    if format.lower() == "yaml":
        try:
            import yaml
            with open(output_path, "w") as f:
                yaml.dump(report, f, default_flow_style=False, default=str)
        except ImportError:
            print_error("PyYAML not available, falling back to JSON")
            format = "json"

    if format.lower() == "json":
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

    print_success(f"Health report saved to: {output_path}")


@app.command()
def monitor(
    interval: int = typer.Option(
        30, "--interval", "-i", help="Check interval in seconds"),
    max_checks: int = typer.Option(
        0, "--max-checks", "-n", help="Maximum number of checks (0 = unlimited)"),
) -> None:
    """Continuous health monitoring."""
    print_header("GitHound Health Monitoring")
    print_info(f"Monitoring every {interval} seconds (Ctrl+C to stop)")

    check_count = 0

    try:
        while True:
            check_count += 1

            print_section(
                f"Health Check #{check_count} - {datetime.now().strftime('%H:%M:%S')}")

            checker = HealthChecker()

            # Quick health check (just critical items)
            system_ok = checker.check_system_health()
            service_ok = checker.check_services()

            # Simple status
            if all(system_ok.values()) and all(service_ok.values()):
                print_success("System healthy ✅")
            else:
                print_warning("System issues detected ⚠️")

            if max_checks > 0 and check_count >= max_checks:
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        print_info(f"\nMonitoring stopped after {check_count} checks")


@app.command()
def benchmark() -> None:
    """Run performance benchmarks."""
    print_header("GitHound Performance Benchmark")

    checker = HealthChecker()
    benchmarks = checker.run_performance_benchmark()

    print_section("Benchmark Results")
    for metric, value in benchmarks.items():
        print_info(f"{metric.replace('_', ' ').title()}: {value:.3f}s")


if __name__ == "__main__":
    app()
