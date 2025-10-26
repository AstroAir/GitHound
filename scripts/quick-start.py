"""
GitHound Quick Start

This script provides a one-command setup and getting started experience
for GitHound development and usage.

Usage:
    python scripts/quick-start.py [command] [options]

Commands:
    setup       - Complete project setup
    demo        - Run interactive demo
    guide       - Show getting started guide
    examples    - Run example workflows
"""

import sys
from pathlib import Path

import typer
from utils import (
    StatusContext,
    check_command_exists,
    check_python_version,
    check_virtual_env,
    confirm,
    console,
    get_project_root,
    print_error,
    print_header,
    print_info,
    print_section,
    print_step,
    print_success,
    print_warning,
    prompt,
    run_command,
    run_command_with_output,
)

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))


app = typer.Typer(
    name="quick-start",
    help="GitHound Quick Start and Setup",
    add_completion=False,
)


class QuickStartManager:
    """Manages quick start and setup processes."""

    def __init__(self) -> None:
        self.project_root = get_project_root()

    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met."""
        print_section("Prerequisites Check")

        all_good = True

        # Python version
        if not check_python_version((3, 11)):
            print_step("Python 3.11+", "error")
            print_error("Python 3.11 or higher is required")
            all_good = False
        else:
            print_step("Python 3.11+", "success")

        # Virtual environment
        if not check_virtual_env():
            print_step("Virtual environment", "warning")
            print_warning("Virtual environment recommended but not required")
        else:
            print_step("Virtual environment", "success")

        # Required commands
        required = ["git", "pip"]
        for cmd in required:
            if not check_command_exists(cmd):
                print_step(f"Command: {cmd}", "error")
                print_error(f"Required command '{cmd}' not found")
                all_good = False
            else:
                print_step(f"Command: {cmd}", "success")

        return all_good

    def setup_development_environment(self) -> bool:
        """Set up complete development environment."""
        print_header("GitHound Development Setup")

        if not self.check_prerequisites():
            print_error("Prerequisites not met. Please fix the issues above.")
            return False

        try:
            # Install package in editable mode
            with StatusContext("Installing GitHound with all dependencies"):
                run_command(
                    ["pip", "install", "-e", ".[dev,test,docs,build]"], cwd=self.project_root
                )

            # Install pre-commit hooks if available
            if check_command_exists("pre-commit"):
                with StatusContext("Setting up pre-commit hooks"):
                    run_command(["pre-commit", "install"], cwd=self.project_root)

            # Create necessary directories
            dirs_to_create = ["logs", ".cache", "temp"]
            for dir_name in dirs_to_create:
                dir_path = self.project_root / dir_name
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)

            # Run a quick test
            with StatusContext("Running quick validation test"):
                run_command(
                    ["python", "-c", "from githound import GitHound; print('✅ Setup successful!')"],
                    cwd=self.project_root,
                )

            print_success("Development environment setup completed! 🎉")
            return True

        except Exception as e:
            print_error(f"Setup failed: {e}")
            return False

    def run_interactive_demo(self) -> None:
        """Run an interactive demo of GitHound features."""
        print_header("GitHound Interactive Demo")

        # Check if GitHound is available
        try:
            run_command(["python", "-c", "import githound"], cwd=self.project_root)
        except Exception:
            print_error("GitHound not installed. Run setup first.")
            return

        print_info("This demo will show you GitHound's main features.")
        print_info("You can use the current repository as an example.")

        if not confirm("Continue with the demo?"):
            return

        # Demo 1: Repository Analysis
        print_section("Demo 1: Repository Analysis")
        print_info("Analyzing the current repository...")

        try:
            result = run_command_with_output(
                [
                    "python",
                    "-c",
                    """
from githound import GitHound
from pathlib import Path
import json

gh = GitHound(Path('.'))
info = gh.analyze_repository()
print(json.dumps({
    'total_commits': info.get if info is not None else None('total_commits', 0),
    'total_files': info.get('total_files', 0),
    'contributors': len(info.get('contributors', [])),
    'branches': len(info.get('branches', []))
}, indent=2))
""",
                ],
                cwd=self.project_root,
            )

            if result[0] == 0:
                print_success("Repository analysis completed!")
                console.print(result[1])
            else:
                print_warning("Analysis demo skipped (repository may be empty)")

        except Exception as e:
            print_warning(f"Demo failed: {e}")

        # Demo 2: Search functionality
        print_section("Demo 2: Search Functionality")

        search_term = prompt("Enter a search term (or press Enter for 'function')", "function")

        print_info(f"Searching for '{search_term}' in the repository...")

        try:
            result = run_command_with_output(
                [
                    "python",
                    "-c",
                    f"""
from githound import GitHound
from githound.models import SearchQuery
from pathlib import Path
import json

gh = GitHound(Path('.'))
query = SearchQuery(content_pattern='{search_term}')
results = list(gh.search_advanced(query))[:5]  # Limit to 5 results

print(f"Found {{len(results)}} results (showing first 5):")
for i, result in enumerate(results, 1):
    print(f"{{i}}. {{result.file_path}} ({{result.commit_hash[:8]}})")
""",
                ],
                cwd=self.project_root,
            )

            if result[0] == 0:
                print_success("Search completed!")
                console.print(result[1])
            else:
                print_warning("Search demo failed")

        except Exception as e:
            print_warning(f"Search demo failed: {e}")

        # Demo 3: CLI usage
        print_section("Demo 3: CLI Usage")
        print_info("GitHound provides a powerful CLI interface.")
        print_info("Here are some example commands you can try:")

        examples = [
            "githound analyze .",
            "githound search --content 'function' .",
            "githound blame . README.md",
            "githound web --port 8080",
        ]

        for example in examples:
            console.print(f"  [cyan]$ {example}[/cyan]")

        print_success("Demo completed! 🎉")
        print_info("Try the CLI commands above to explore more features.")

    def show_getting_started_guide(self) -> None:
        """Show comprehensive getting started guide."""
        print_header("GitHound Getting Started Guide")

        print_section("1. Installation")
        console.print(
            """
GitHound can be installed in several ways:

[cyan]# Development installation (recommended for contributors)[/cyan]
git clone https://github.com/AstroAir/GitHound.git
cd GitHound
python scripts/quick-start.py setup

[cyan]# Or using pip (when available)[/cyan]
pip install githound
"""
        )

        print_section("2. Basic Usage")
        console.print(
            """
[cyan]# Analyze a repository[/cyan]
githound analyze /path/to/repo

[cyan]# Search for content[/cyan]
githound search --content "function" /path/to/repo

[cyan]# File blame analysis[/cyan]
githound blame /path/to/repo src/main.py

[cyan]# Compare commits[/cyan]
githound diff --commit1 HEAD~1 --commit2 HEAD /path/to/repo
"""
        )

        print_section("3. Web Interface")
        console.print(
            """
[cyan]# Start web server[/cyan]
githound web --port 8000

[cyan]# Or using the services script[/cyan]
python scripts/services.py start web --port 8000

Then open http://localhost:8000 in your browser.
"""
        )

        print_section("4. MCP Server (AI Integration)")
        console.print(
            """
[cyan]# Start MCP server[/cyan]
githound mcp-server --port 3000

[cyan]# Or using the services script[/cyan]
python scripts/services.py start mcp --port 3000

This enables AI tools to interact with GitHound.
"""
        )

        print_section("5. Development Scripts")
        console.print(
            """
GitHound includes several utility scripts:

[cyan]# Development environment[/cyan]
python scripts/dev-env.py check
python scripts/dev-env.py setup

[cyan]# Service management[/cyan]
python scripts/services.py start all
python scripts/services.py status

[cyan]# Cache management[/cyan]
python scripts/cache-manager.py clean
python scripts/cache-manager.py info

[cyan]# Health checks[/cyan]
python scripts/health-check.py check
"""
        )

        print_section("6. Next Steps")
        console.print(
            """
• Check out the examples/ directory for more usage patterns
• Read the documentation in docs/
• Run the interactive demo: python scripts/quick-start.py demo
• Join the community and contribute!
"""
        )

        print_success("Happy coding with GitHound! 🐕")

    def run_example_workflows(self) -> None:
        """Run example workflows."""
        print_header("GitHound Example Workflows")

        workflows = {
            "1": ("Bug Investigation", self._workflow_bug_investigation),
            "2": ("Code Review Preparation", self._workflow_code_review),
            "3": ("Repository Analysis", self._workflow_repo_analysis),
            "4": ("Performance Monitoring", self._workflow_performance),
        }

        print_info("Available example workflows:")
        for key, (name, _) in workflows.items():
            console.print(f"  [cyan]{key}[/cyan]. {name}")

        choice = prompt("Select a workflow (1-4)", "1")

        if choice in workflows:
            name, workflow_func = workflows[choice]
            print_section(f"Workflow: {name}")
            workflow_func()
        else:
            print_error("Invalid choice")

    def _workflow_bug_investigation(self) -> None:
        """Bug investigation workflow example."""
        console.print(
            """
[bold]Bug Investigation Workflow[/bold]

When investigating a bug, follow these steps:

[cyan]1. Find recent changes to the problematic file[/cyan]
githound search --file-path "src/buggy_file.py" --date-from "2023-11-01" .

[cyan]2. Check who last modified specific lines[/cyan]
githound blame . src/buggy_file.py

[cyan]3. Compare recent commits[/cyan]
githound diff --commit1 HEAD~5 --commit2 HEAD .

[cyan]4. Search for related error messages[/cyan]
githound search --content "error_message" .

[cyan]5. Find similar issues in commit history[/cyan]
githound search --message "fix" --message "bug" .
"""
        )

    def _workflow_code_review(self) -> None:
        """Code review preparation workflow example."""
        console.print(
            """
[bold]Code Review Preparation Workflow[/bold]

Before a code review:

[cyan]1. Find all changes by the author[/cyan]
githound search --author "developer_name" --date-from "2023-11-01" .

[cyan]2. Analyze the scope of changes[/cyan]
githound analyze .

[cyan]3. Check for potential conflicts[/cyan]
githound diff --commit1 main --commit2 feature-branch .

[cyan]4. Review test coverage[/cyan]
githound search --file-path "test_*.py" --author "developer_name" .
"""
        )

    def _workflow_repo_analysis(self) -> None:
        """Repository analysis workflow example."""
        console.print(
            """
[bold]Repository Analysis Workflow[/bold]

For comprehensive repository analysis:

[cyan]1. Get repository overview[/cyan]
githound analyze .

[cyan]2. Find most active files[/cyan]
githound search --date-from "2023-01-01" . | head -20

[cyan]3. Identify key contributors[/cyan]
githound search --date-from "2023-01-01" . --export contributors.json

[cyan]4. Analyze code patterns[/cyan]
githound search --content "TODO\\|FIXME\\|HACK" .

[cyan]5. Generate reports[/cyan]
githound analyze . --export report.yaml --format yaml
"""
        )

    def _workflow_performance(self) -> None:
        """Performance monitoring workflow example."""
        console.print(
            """
[bold]Performance Monitoring Workflow[/bold]

For performance analysis:

[cyan]1. Run health checks[/cyan]
python scripts/health-check.py check

[cyan]2. Benchmark performance[/cyan]
python scripts/health-check.py benchmark

[cyan]3. Monitor services[/cyan]
python scripts/services.py status --watch

[cyan]4. Analyze cache usage[/cyan]
python scripts/cache-manager.py analyze

[cyan]5. Optimize if needed[/cyan]
python scripts/cache-manager.py optimize
"""
        )


@app.command()
def setup(
    force: bool = typer.Option(
        False, "--force", "-f", help="Force setup even if already configured"
    ),
) -> None:
    """Complete project setup."""
    manager = QuickStartManager()

    if not force:
        # Check if already set up
        try:
            run_command(["python", "-c", "import githound"], cwd=manager.project_root)
            if not confirm("GitHound appears to be already set up. Continue anyway?"):
                print_info("Setup cancelled")
                return
        except Exception:
            pass  # Not set up, continue

    success = manager.setup_development_environment()

    if success:
        print_section("What's Next?")
        print_info("• Run 'python scripts/quick-start.py demo' for an interactive demo")
        print_info("• Run 'python scripts/quick-start.py guide' for detailed usage guide")
        print_info("• Check 'python scripts/quick-start.py examples' for workflow examples")
        print_info("• Start the web interface: 'python scripts/services.py start web'")

    sys.exit(0 if success else 1)


@app.command()
def demo() -> None:
    """Run interactive demo."""
    manager = QuickStartManager()
    manager.run_interactive_demo()


@app.command()
def guide() -> None:
    """Show getting started guide."""
    manager = QuickStartManager()
    manager.show_getting_started_guide()


@app.command()
def examples() -> None:
    """Run example workflows."""
    manager = QuickStartManager()
    manager.run_example_workflows()


if __name__ == "__main__":
    app()
