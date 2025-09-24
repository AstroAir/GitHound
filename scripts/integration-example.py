#!/usr/bin/env python3
"""
GitHound Build Integration Example

This script demonstrates how the new utility scripts integrate with
the existing build infrastructure (build.sh, build.ps1, Makefile).

Usage:
    python scripts/integration-example.py [workflow]

Workflows:
    full-dev-setup    - Complete development setup
    ci-pipeline       - CI/CD pipeline simulation
    daily-workflow    - Daily development workflow
    release-prep      - Release preparation workflow
"""

from utils import (
    console,
    get_project_root,
    print_header,
    print_info,
    print_section,
    print_step,
    print_success,
    run_command,
    StatusContext,
    is_windows,
)
import sys
from pathlib import Path
from typing import List

import typer

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))


app = typer.Typer(
    name="integration-example",
    help="GitHound Build Integration Examples",
    add_completion=False,
)


class IntegrationWorkflows:
    """Demonstrates integration between new scripts and existing build tools."""

    def __init__(self) -> None:
        self.project_root = get_project_root()
        self.build_script = "build.ps1" if is_windows() else "build.sh"

    def run_command_safe(self, command: List[str], description: str) -> bool:
        """Run a command safely with error handling."""
        try:
            with StatusContext(description):
                run_command(command, cwd=self.project_root)
            return True
        except Exception as e:
            print_step(description, "error")
            console.print(f"  [red]Error: {e}[/red]")
            return False

    def full_development_setup(self) -> None:
        """Complete development setup workflow."""
        print_header("Full Development Setup Workflow")
        print_info(
            "This workflow combines new utility scripts with existing build tools")

        steps = [
            # Step 1: Environment validation
            (["python", "scripts/health-check.py", "check"],
             "Checking system health"),

            # Step 2: Development environment setup
            (["python", "scripts/dev-env.py", "setup"],
             "Setting up development environment"),

            # Step 3: Use existing build script for dependencies
            ([f"./{self.build_script}", "install-dev"] if not is_windows()
             else ["powershell", "-ExecutionPolicy", "Bypass", "-File", self.build_script, "install-dev"],
             "Installing development dependencies (existing build script)"),

            # Step 4: Clean any existing artifacts
            (["python", "scripts/cache-manager.py", "clean", "all"],
             "Cleaning build artifacts"),

            # Step 5: Run quality checks with existing tools
            ([f"./{self.build_script}", "quality"] if not is_windows()
             else ["powershell", "-ExecutionPolicy", "Bypass", "-File", self.build_script, "quality"],
             "Running code quality checks (existing build script)"),

            # Step 6: Start services for development
            (["python", "scripts/services.py", "start", "web", "--port", "8080"],
             "Starting web server for development"),

            # Step 7: Final health check
            (["python", "scripts/health-check.py", "check"],
             "Final health validation"),
        ]

        success_count = 0
        for command, description in steps:
            if self.run_command_safe(command, description):
                success_count += 1

        print_section("Setup Summary")
        print_success(f"Completed {success_count}/{len(steps)} setup steps")

        if success_count == len(steps):
            print_info("🎉 Development environment is ready!")
            print_info("Next steps:")
            print_info("  • Web interface: http://localhost:8080")
            print_info("  • Run tests: ./build.sh test")
            print_info("  • Check services: python scripts/services.py status")
        else:
            print_info("⚠️  Some setup steps failed. Check the errors above.")

    def ci_pipeline_simulation(self) -> None:
        """Simulate a CI/CD pipeline."""
        print_header("CI/CD Pipeline Simulation")
        print_info("This simulates how new scripts integrate with CI/CD")

        steps = [
            # CI Setup
            (["python", "scripts/dev-env.py", "setup", "--force"],
             "CI: Setting up environment"),

            # Health check
            (["python", "scripts/health-check.py", "check", "--save"],
             "CI: System health check"),

            # Clean environment
            (["python", "scripts/cache-manager.py", "clean", "all"],
             "CI: Cleaning build environment"),

            # Use existing build script for main CI tasks
            ([f"./{self.build_script}", "ci"] if not is_windows()
             else ["powershell", "-ExecutionPolicy", "Bypass", "-File", self.build_script, "ci"],
             "CI: Running main CI pipeline (existing build script)"),

            # Performance benchmarks
            (["python", "scripts/benchmark.py", "run", "--save"],
             "CI: Running performance benchmarks"),

            # Generate reports
            (["python", "scripts/health-check.py", "report", "--format", "json"],
             "CI: Generating health report"),
        ]

        success_count = 0
        for command, description in steps:
            if self.run_command_safe(command, description):
                success_count += 1

        print_section("CI Pipeline Summary")
        if success_count == len(steps):
            print_success("✅ CI pipeline completed successfully!")
        else:
            print_info(
                f"⚠️  CI pipeline completed with {len(steps) - success_count} failures")

    def daily_development_workflow(self) -> None:
        """Daily development workflow."""
        print_header("Daily Development Workflow")
        print_info("Typical daily workflow combining all tools")

        print_section("Morning Setup")
        morning_steps = [
            (["python", "scripts/health-check.py", "check"],
             "Morning health check"),

            (["python", "scripts/services.py", "start", "web", "--port", "8000"],
             "Starting web server"),

            (["python", "scripts/cache-manager.py", "info"],
             "Checking cache status"),
        ]

        for command, description in morning_steps:
            self.run_command_safe(command, description)

        print_section("Development Work")
        print_info("During development, you can use:")
        console.print("  [cyan]# Code quality checks[/cyan]")
        console.print(f"  ./{self.build_script} quality")
        console.print("  [cyan]# Run tests[/cyan]")
        console.print(f"  ./{self.build_script} test")
        console.print("  [cyan]# Check service status[/cyan]")
        console.print("  python scripts/services.py status")

        print_section("End of Day Cleanup")
        cleanup_steps = [
            (["python", "scripts/cache-manager.py", "optimize"],
             "Optimizing caches"),

            (["python", "scripts/services.py", "stop", "all"],
             "Stopping all services"),
        ]

        for command, description in cleanup_steps:
            self.run_command_safe(command, description)

        print_success("Daily workflow example completed!")

    def release_preparation_workflow(self) -> None:
        """Release preparation workflow."""
        print_header("Release Preparation Workflow")
        print_info("Preparing for a release using all available tools")

        steps = [
            # Pre-release checks
            (["python", "scripts/health-check.py", "check", "--verbose"],
             "Comprehensive health check"),

            # Clean everything
            (["python", "scripts/cache-manager.py", "clean", "all"],
             "Cleaning all caches and artifacts"),

            # Use existing build script for main build
            ([f"./{self.build_script}", "clean"] if not is_windows()
             else ["powershell", "-ExecutionPolicy", "Bypass", "-File", self.build_script, "clean"],
             "Deep clean with existing build script"),

            ([f"./{self.build_script}", "build"] if not is_windows()
             else ["powershell", "-ExecutionPolicy", "Bypass", "-File", self.build_script, "build"],
             "Building release packages"),

            # Performance baseline
            (["python", "scripts/benchmark.py", "run", "--baseline"],
             "Setting performance baseline"),

            # Final validation
            (["python", "scripts/health-check.py", "report", "--output", "release-health.json"],
             "Generating release health report"),
        ]

        success_count = 0
        for command, description in steps:
            if self.run_command_safe(command, description):
                success_count += 1

        print_section("Release Preparation Summary")
        if success_count == len(steps):
            print_success("🚀 Release preparation completed successfully!")
            print_info("Release artifacts and reports are ready")
        else:
            print_info(
                f"⚠️  Release preparation completed with {len(steps) - success_count} issues")


@app.command()
def full_dev_setup() -> None:
    """Complete development setup workflow."""
    workflows = IntegrationWorkflows()
    workflows.full_development_setup()


@app.command()
def ci_pipeline() -> None:
    """CI/CD pipeline simulation."""
    workflows = IntegrationWorkflows()
    workflows.ci_pipeline_simulation()


@app.command()
def daily_workflow() -> None:
    """Daily development workflow."""
    workflows = IntegrationWorkflows()
    workflows.daily_development_workflow()


@app.command()
def release_prep() -> None:
    """Release preparation workflow."""
    workflows = IntegrationWorkflows()
    workflows.release_preparation_workflow()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """
    GitHound Build Integration Examples.

    This script demonstrates how the new utility scripts integrate with
    existing build infrastructure (build.sh, build.ps1, Makefile).
    """
    if ctx.invoked_subcommand is None:
        print_header("GitHound Build Integration Examples")

        print_info("Available workflows:")
        print_info("  • full-dev-setup  - Complete development setup")
        print_info("  • ci-pipeline     - CI/CD pipeline simulation")
        print_info("  • daily-workflow  - Daily development workflow")
        print_info("  • release-prep    - Release preparation workflow")

        print_section("Integration Philosophy")
        console.print("""
The new utility scripts are designed to [bold]complement[/bold], not replace,
the existing build infrastructure:

[cyan]• Existing build scripts[/cyan] (build.sh, build.ps1, Makefile)
  → Handle compilation, testing, packaging, and CI/CD tasks

[cyan]• New utility scripts[/cyan] (dev-env.py, services.py, etc.)
  → Handle development workflow, services, monitoring, and utilities

[cyan]• Integration approach[/cyan]
  → Use both together for comprehensive development experience
  → New scripts call existing build scripts when appropriate
  → Existing scripts can call new utilities for enhanced functionality
""")

        print_section("Quick Examples")
        console.print("""
[cyan]# Use new scripts for environment setup[/cyan]
python scripts/quick-start.py setup

[cyan]# Use existing scripts for building[/cyan]
./build.sh build

[cyan]# Use new scripts for service management[/cyan]
python scripts/services.py start web

[cyan]# Use existing scripts for testing[/cyan]
./build.sh test

[cyan]# Use new scripts for monitoring[/cyan]
python scripts/health-check.py check
""")


if __name__ == "__main__":
    app()
