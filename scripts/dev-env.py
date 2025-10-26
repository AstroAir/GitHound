"""
GitHound Development Environment Manager

This script helps set up, validate, and manage the GitHound development environment
with cross-platform support and comprehensive validation.

Usage:
    python scripts/dev-env.py [command] [options]

Commands:
    setup       - Set up development environment
    check       - Check environment status
    validate    - Validate all dependencies and configuration
    info        - Show environment information
    clean       - Clean development artifacts
    reset       - Reset development environment
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
    run_command,
    run_command_with_output,
)

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))


app = typer.Typer(
    name="dev-env",
    help="GitHound Development Environment Manager",
    add_completion=False,
)


class DevEnvironmentManager:
    """Manages GitHound development environment setup and validation."""

    def __init__(self) -> None:
        self.project_root = get_project_root()
        self.required_commands = ["git", "python", "pip"]
        self.optional_commands = ["rg", "ripgrep", "pre-commit", "mkdocs"]
        self.required_python_version = (3, 11)

    def check_system_requirements(self) -> dict[str, bool]:
        """Check system requirements."""
        results: dict[str, Any] = {}

        print_section("System Requirements")

        # Python version
        python_ok = check_python_version(self.required_python_version)
        print_step(
            f"Python {self.required_python_version[0]}.{self.required_python_version[1]}+",
            "success" if python_ok else "error",
        )
        results["python_version"] = python_ok

        # Virtual environment
        venv_ok = check_virtual_env()
        print_step("Virtual environment", "success" if venv_ok else "error")
        results["virtual_env"] = venv_ok

        # Required commands
        for cmd in self.required_commands:
            cmd_ok = check_command_exists(cmd)
            print_step(f"Command: {cmd}", "success" if cmd_ok else "error")
            results[f"cmd_{cmd}"] = cmd_ok

        # Optional commands
        for cmd in self.optional_commands:
            cmd_ok = check_command_exists(cmd)
            print_step(f"Optional: {cmd}", "success" if cmd_ok else "skip")
            results[f"opt_{cmd}"] = cmd_ok

        return results

    def check_dependencies(self) -> dict[str, bool]:
        """Check Python dependencies."""
        results: dict[str, Any] = {}

        print_section("Python Dependencies")

        # Check if package is installed in development mode
        exit_code, stdout, stderr = run_command_with_output(
            ["pip", "show", "githound"], cwd=self.project_root
        )

        if exit_code == 0 and "editable" in stdout.lower():
            print_step("GitHound (editable install)", "success")
            results["githound_editable"] = True
        else:
            print_step("GitHound (editable install)", "error")
            results["githound_editable"] = False

        # Check development dependencies
        dev_deps = [
            "pytest",
            "black",
            "isort",
            "ruff",
            "mypy",
            "pre-commit",
            "mkdocs",
            "rich",
            "typer",
        ]

        for dep in dev_deps:
            exit_code, _, _ = run_command_with_output(
                ["python", "-c", f"import {dep}"], cwd=self.project_root
            )
            dep_ok = exit_code == 0
            print_step(f"Dependency: {dep}", "success" if dep_ok else "error")
            results[f"dep_{dep}"] = dep_ok

        return results

    def check_git_configuration(self) -> dict[str, bool]:
        """Check Git configuration."""
        results: dict[str, Any] = {}

        print_section("Git Configuration")

        git_info = get_git_info()

        # Check if in git repository
        if git_info:
            print_step("Git repository", "success")
            results["git_repo"] = True

            # Check for uncommitted changes
            if git_info.get("dirty", False):
                print_step("Working directory clean", "error")
                results["git_clean"] = False
            else:
                print_step("Working directory clean", "success")
                results["git_clean"] = True
        else:
            print_step("Git repository", "error")
            results["git_repo"] = False
            results["git_clean"] = False

        # Check git user configuration
        exit_code, stdout, _ = run_command_with_output(
            ["git", "config", "user.name"]
        )  # [attr-defined]
        if exit_code == 0 and stdout.strip():
            print_step("Git user.name configured", "success")  # [attr-defined]
            results["git_user_name"] = True
        else:
            print_step("Git user.name configured", "error")  # [attr-defined]
            results["git_user_name"] = False

        exit_code, stdout, _ = run_command_with_output(
            ["git", "config", "user.email"]
        )  # [attr-defined]
        if exit_code == 0 and stdout.strip():
            print_step("Git user.email configured", "success")  # [attr-defined]
            results["git_user_email"] = True
        else:
            print_step("Git user.email configured", "error")  # [attr-defined]
            results["git_user_email"] = False

        return results

    def check_pre_commit_hooks(self) -> dict[str, bool]:
        """Check pre-commit hooks."""
        results: dict[str, Any] = {}

        print_section("Pre-commit Hooks")

        pre_commit_config = self.project_root / ".pre-commit-config.yaml"  # [attr-defined]
        if pre_commit_config.exists():  # [attr-defined]
            print_step("Pre-commit config exists", "success")
            results["precommit_config"] = True

            # Check if hooks are installed
            git_hooks_dir = self.project_root / ".git" / "hooks"
            pre_commit_hook = git_hooks_dir / "pre-commit"

            if pre_commit_hook.exists():
                print_step("Pre-commit hooks installed", "success")
                results["precommit_installed"] = True
            else:
                print_step("Pre-commit hooks installed", "error")
                results["precommit_installed"] = False
        else:
            print_step("Pre-commit config exists", "error")
            results["precommit_config"] = False
            results["precommit_installed"] = False

        return results

    def setup_development_environment(self, force: bool = False) -> bool:
        """Set up the development environment."""
        print_header("Setting up GitHound Development Environment")

        try:
            # Install package in editable mode with all dependencies
            with StatusContext("Installing GitHound in editable mode"):
                run_command(
                    ["pip", "install", "-e", ".[dev,test,docs,build]"], cwd=self.project_root
                )

            # Install pre-commit hooks
            if check_command_exists("pre-commit"):
                with StatusContext("Installing pre-commit hooks"):
                    run_command(["pre-commit", "install"], cwd=self.project_root)
            else:
                print_warning("pre-commit not available, skipping hook installation")

            # Create necessary directories
            directories = [
                self.project_root / "logs",
                self.project_root / ".cache",
                self.project_root / "temp",
            ]

            for directory in directories:
                if not directory.exists():
                    directory.mkdir(parents=True, exist_ok=True)
                    print_info(f"Created directory: {directory}")

            print_success("Development environment setup completed!")
            return True

        except Exception as e:
            print_error(f"Setup failed: {e}")
            return False

    def clean_development_artifacts(self) -> bool:
        """Clean development artifacts."""
        print_header("Cleaning Development Artifacts")

        try:
            # Directories to clean
            clean_dirs = [
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                "htmlcov",
                "build",
                "dist",
                "*.egg-info",
                "__pycache__",
            ]

            for pattern in clean_dirs:
                paths = list(self.project_root.rglob(pattern))
                for path in paths:
                    if path.is_dir():
                        import shutil

                        shutil.rmtree(path, ignore_errors=True)
                        print_info(f"Removed directory: {path}")
                    elif path.is_file():
                        path.unlink(missing_ok=True)
                        print_info(f"Removed file: {path}")

            # Clean .pyc files
            pyc_files = list(self.project_root.rglob("*.pyc"))
            for pyc_file in pyc_files:
                pyc_file.unlink(missing_ok=True)

            if pyc_files:
                print_info(f"Removed {len(pyc_files)} .pyc files")

            print_success("Development artifacts cleaned!")
            return True

        except Exception as e:
            print_error(f"Cleaning failed: {e}")
            return False


@app.command()
def setup(
    force: bool = typer.Option(
        False, "--force", "-f", help="Force setup even if already configured"
    )
) -> None:
    """Set up the development environment."""
    manager = DevEnvironmentManager()

    if not force:
        # Check if already set up
        deps = manager.check_dependencies()
        if deps.get("githound_editable", False):
            if not confirm("Development environment appears to be set up. Continue anyway?"):
                print_info("Setup cancelled")
                return

    success = manager.setup_development_environment(force)
    sys.exit(0 if success else 1)


@app.command()
def check() -> None:
    """Check the development environment status."""
    manager = DevEnvironmentManager()

    print_header("GitHound Development Environment Check")

    # Run all checks
    system_results = manager.check_system_requirements()
    dep_results = manager.check_dependencies()
    git_results = manager.check_git_configuration()  # [attr-defined]
    precommit_results = manager.check_pre_commit_hooks()

    # Summary
    all_results = {**system_results, **dep_results, **git_results, **precommit_results}
    total_checks = len(all_results)
    passed_checks = sum(1 for result in all_results.values() if result)

    print_section("Summary")
    if passed_checks == total_checks:
        print_success(f"All {total_checks} checks passed! ✨")
    else:
        failed_checks = total_checks - passed_checks
        print_warning(f"{passed_checks}/{total_checks} checks passed ({failed_checks} failed)")
        print_info("Run 'python scripts/dev-env.py setup' to fix issues")


@app.command()
def info() -> None:
    """Show development environment information."""
    print_header("GitHound Development Environment Information")

    # Python info
    python_info = get_python_info()
    print_section("Python Environment")
    for key, value in python_info.items():
        console.print(
            f"  [cyan]{key.replace if key is not None else None('_', ' ').title()}:[/cyan] {value}"
        )

    # Git info
    git_info = get_git_info()
    if git_info:
        print_section("Git Repository")
        for key, value in git_info.items():
            console.print(
                f"  [cyan]{key.replace if key is not None else None('_', ' ').title()}:[/cyan] {value}"
            )

    # Platform info
    platform_info = get_platform_info()
    print_section("Platform Information")
    for key, value in platform_info.items():
        console.print(
            f"  [cyan]{key.replace if key is not None else None('_', ' ').title()}:[/cyan] {value}"
        )


@app.command()
def clean() -> None:
    """Clean development artifacts."""
    manager = DevEnvironmentManager()

    if confirm("This will remove build artifacts, caches, and temporary files. Continue?"):
        success = manager.clean_development_artifacts()
        sys.exit(0 if success else 1)
    else:
        print_info("Cleaning cancelled")


@app.command()
def validate() -> None:
    """Validate the complete development environment."""
    manager = DevEnvironmentManager()

    print_header("GitHound Development Environment Validation")

    # Run comprehensive validation
    with StatusContext("Running validation tests"):
        # Quick test of core functionality
        try:
            run_command(
                [
                    "python",
                    "-c",
                    "from githound import GitHound; print('✅ Core import successful')",
                ],
                cwd=manager.project_root,
            )
        except Exception as e:
            print_error(f"Core import failed: {e}")
            sys.exit(1)

    print_success("Development environment validation completed!")


if __name__ == "__main__":
    app()
