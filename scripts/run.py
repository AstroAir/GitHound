#!/usr/bin/env python3
"""
GitHound Script Runner

Unified interface to all GitHound utility scripts with cross-platform support.
This script provides a convenient way to discover and run all available scripts.

Usage:
    python scripts/run.py [script] [args...]
    python scripts/run.py --list
    python scripts/run.py --help-all

Examples:
    python scripts/run.py dev-env check
    python scripts/run.py services start web
    python scripts/run.py quick-start setup
"""

from utils import (
    console,
    get_project_root,
    print_error,
    print_header,
    print_info,
    print_section,
    print_success,
)
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import typer
from rich.table import Table

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))


app = typer.Typer(
    name="run",
    help="GitHound Script Runner - Unified interface to all utility scripts",
    add_completion=False,
)


class ScriptRunner:
    """Manages and runs GitHound utility scripts."""

    def __init__(self):
        self.project_root = get_project_root()
        self.scripts_dir = self.project_root / "scripts"

        # Define available scripts
        self.scripts = {
            "dev-env": {
                "file": "dev-env.py",
                "description": "Development environment management",
                "commands": ["setup", "check", "info", "clean", "validate"],
                "category": "Development",
            },
            "services": {
                "file": "services.py",
                "description": "Service management (web, MCP server)",
                "commands": ["start", "stop", "restart", "status", "logs", "health"],
                "category": "Services",
            },
            "cache-manager": {
                "file": "cache-manager.py",
                "description": "Cache and data management",
                "commands": ["clean", "info", "analyze", "optimize"],
                "category": "Maintenance",
            },
            "health-check": {
                "file": "health-check.py",
                "description": "System health validation",
                "commands": ["check", "report", "monitor", "benchmark"],
                "category": "Monitoring",
            },
            "quick-start": {
                "file": "quick-start.py",
                "description": "One-command setup and demos",
                "commands": ["setup", "demo", "guide", "examples"],
                "category": "Getting Started",
            },
            "benchmark": {
                "file": "benchmark.py",
                "description": "Performance benchmarking",
                "commands": ["run", "compare", "baseline", "report"],
                "category": "Performance",
            },
            "run-mcp-tests": {
                "file": "run_mcp_tests.py",
                "description": "MCP server testing",
                "commands": ["unit", "integration", "performance", "all"],
                "category": "Testing",
            },
        }

    def list_scripts(self) -> None:
        """List all available scripts."""
        print_header("GitHound Utility Scripts")

        # Group by category
        categories = {}
        for script_name, script_info in self.scripts.items():
            category = script_info["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append((script_name, script_info))

        for category, scripts in categories.items():
            print_section(category)

            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Script", style="cyan", width=15)
            table.add_column("Description", style="white", width=40)
            table.add_column("Commands", style="yellow", width=30)

            for script_name, script_info in scripts:
                commands_str = ", ".join(script_info["commands"][:3])
                if len(script_info["commands"]) > 3:
                    commands_str += "..."

                table.add_row(
                    script_name,
                    script_info["description"],
                    commands_str
                )

            console.print(table)
            console.print()

    def show_script_help(self, script_name: str) -> None:
        """Show help for a specific script."""
        if script_name not in self.scripts:
            print_error(f"Unknown script: {script_name}")
            return

        script_info = self.scripts[script_name]
        script_file = self.scripts_dir / script_info["file"]

        print_header(f"Help for {script_name}")
        print_info(f"Description: {script_info['description']}")
        print_info(f"File: {script_file}")
        print_info(f"Category: {script_info['category']}")

        # Run the script with --help
        try:
            result = subprocess.run([
                sys.executable, str(script_file), "--help"
            ], capture_output=True, text=True, cwd=self.project_root)

            if result.returncode == 0:
                console.print("\n[bold]Script Help:[/bold]")
                console.print(result.stdout)
            else:
                print_error("Failed to get script help")
        except Exception as e:
            print_error(f"Error running script help: {e}")

    def show_all_help(self) -> None:
        """Show help for all scripts."""
        print_header("GitHound Scripts - Complete Help")

        for script_name in self.scripts:
            self.show_script_help(script_name)
            console.print("\n" + "="*80 + "\n")

    def run_script(self, script_name: str, args: List[str]) -> int:
        """Run a specific script with arguments."""
        if script_name not in self.scripts:
            print_error(f"Unknown script: {script_name}")
            print_info("Available scripts:")
            for name in self.scripts:
                print_info(f"  - {name}")
            return 1

        script_info = self.scripts[script_name]
        script_file = self.scripts_dir / script_info["file"]

        if not script_file.exists():
            print_error(f"Script file not found: {script_file}")
            return 1

        # Run the script
        try:
            cmd = [sys.executable, str(script_file)] + args
            result = subprocess.run(cmd, cwd=self.project_root)
            return result.returncode
        except KeyboardInterrupt:
            print_info("\nScript execution interrupted")
            return 130
        except Exception as e:
            print_error(f"Error running script: {e}")
            return 1

    def suggest_commands(self, script_name: str) -> None:
        """Suggest common commands for a script."""
        if script_name in self.scripts:
            script_info = self.scripts[script_name]
            print_info(f"Common commands for {script_name}:")
            for cmd in script_info["commands"]:
                console.print(
                    f"  [cyan]python scripts/run.py {script_name} {cmd}[/cyan]")


@app.command()
def list_scripts() -> None:
    """List all available scripts."""
    runner = ScriptRunner()
    runner.list_scripts()


@app.command()
def help_script(
    script_name: str = typer.Argument(..., help="Script to show help for")
) -> None:
    """Show help for a specific script."""
    runner = ScriptRunner()
    runner.show_script_help(script_name)


@app.command()
def help_all() -> None:
    """Show help for all scripts."""
    runner = ScriptRunner()
    runner.show_all_help()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    list_scripts: bool = typer.Option(
        False, "--list", "-l", help="List all scripts"),
    help_all: bool = typer.Option(
        False, "--help-all", help="Show help for all scripts"),
) -> None:
    """
    GitHound Script Runner - Unified interface to all utility scripts.

    Run scripts directly:
        python scripts/run.py dev-env check
        python scripts/run.py services start web
        python scripts/run.py quick-start setup

    Get information:
        python scripts/run.py --list
        python scripts/run.py --help-all
    """
    runner = ScriptRunner()

    if list_scripts:
        runner.list_scripts()
        return

    if help_all:
        runner.show_all_help()
        return

    # If no command specified, show usage
    if ctx.invoked_subcommand is None:
        # Check if we have arguments that might be a script name
        if ctx.params.get('args'):
            args = ctx.params['args']
            if args:
                script_name = args[0]
                script_args = args[1:] if len(args) > 1 else []

                exit_code = runner.run_script(script_name, script_args)
                sys.exit(exit_code)

        # Show default help
        print_header("GitHound Script Runner")
        print_info("Unified interface to all GitHound utility scripts")

        console.print("\n[bold]Quick Examples:[/bold]")
        console.print(
            "  [cyan]python scripts/run.py --list[/cyan]                    # List all scripts")
        console.print(
            "  [cyan]python scripts/run.py dev-env check[/cyan]            # Check development environment")
        console.print(
            "  [cyan]python scripts/run.py services start web[/cyan]       # Start web server")
        console.print(
            "  [cyan]python scripts/run.py quick-start setup[/cyan]        # Complete setup")
        console.print(
            "  [cyan]python scripts/run.py health-check check[/cyan]       # System health check")

        console.print("\n[bold]Getting Help:[/bold]")
        console.print(
            "  [cyan]python scripts/run.py --help-all[/cyan]               # Help for all scripts")
        console.print(
            "  [cyan]python scripts/run.py help-script dev-env[/cyan]      # Help for specific script")

        runner.list_scripts()


# Handle direct script execution
if __name__ == "__main__":
    # Check if we have command line arguments that look like script execution
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        # Direct script execution: python scripts/run.py script-name args...
        runner = ScriptRunner()
        script_name = sys.argv[1]
        script_args = sys.argv[2:] if len(sys.argv) > 2 else []

        exit_code = runner.run_script(script_name, script_args)
        sys.exit(exit_code)
    else:
        # Use typer for command parsing
        app()
