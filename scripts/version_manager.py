"""Version management script for GitHound.

This script provides utilities for managing versions across the project,
including updating configuration files and creating releases.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except FileNotFoundError:
        return 1, "", f"Command not found: {cmd[0]}"


def get_git_info(repo_root: Path) -> dict[str, str | None]:
    """Get git information from repository."""
    info = {
        "commit": None,
        "branch": None,
        "tag": None,
        "dirty": False,
    }

    # Get commit hash
    code, stdout, _ = run_command(["git", "rev-parse", "HEAD"], repo_root)
    if code == 0:
        info["commit"] = stdout

    # Get branch name
    code, stdout, _ = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_root)
    if code == 0:
        info["branch"] = stdout

    # Get tag (if on a tag)
    code, stdout, _ = run_command(["git", "describe", "--exact-match", "--tags", "HEAD"], repo_root)
    if code == 0:
        info["tag"] = stdout

    # Check if working directory is dirty
    code, stdout, _ = run_command(["git", "status", "--porcelain"], repo_root)
    if code == 0:
        info["dirty"] = bool(stdout)

    return info


def get_current_version(repo_root: Path) -> str | None:
    """Get current version from git tags."""
    # Try to get version from git describe
    code, stdout, _ = run_command(["git", "describe", "--tags", "--abbrev=0"], repo_root)
    if code == 0:
        return stdout

    # Fallback: look for version tags
    code, stdout, _ = run_command(["git", "tag", "--sort=-version:refname"], repo_root)
    if code == 0 and stdout:
        tags = stdout.split("\n")
        for tag in tags:
            if re.match(r"^v?\d+\.\d+\.\d+", tag):
                return tag

    return None


def create_version_tag(repo_root: Path, version: str, message: str | None = None) -> bool:
    """Create a version tag."""
    if not version.startswith("v"):
        version = f"v{version}"

    tag_message = message or f"Release {version}"

    code, _, stderr = run_command(["git", "tag", "-a", version, "-m", tag_message], repo_root)

    if code != 0:
        print(f"Error creating tag: {stderr}")
        return False

    print(f"Created tag: {version}")
    return True


def update_environment_files(repo_root: Path, version: str) -> None:
    """Update environment files with new version."""
    env_files = [
        repo_root / ".env.example",
        repo_root / "docker" / ".env.example",
    ]

    for env_file in env_files:
        if env_file.exists():
            content = env_file.read_text()

            # Update GITHOUND_VERSION if it exists
            content = re.sub(
                r"^GITHOUND_VERSION=.*$", f"GITHOUND_VERSION={version}", content, flags=re.MULTILINE
            )

            # Add GITHOUND_VERSION if it doesn't exist
            if "GITHOUND_VERSION=" not in content:
                content += f"\n# Version\nGITHOUND_VERSION={version}\n"

            env_file.write_text(content)
            print(f"Updated {env_file}")


def update_docker_files(repo_root: Path, version: str) -> None:
    """Update Docker-related files with new version."""
    # Update docker-compose files
    compose_files = [
        repo_root / "docker-compose.yml",
        repo_root / "docker-compose.prod.yml",
    ]

    for compose_file in compose_files:
        if compose_file.exists():
            content = compose_file.read_text()

            # Update default version in build args
            content = re.sub(
                r'GITHOUND_VERSION: "\${GITHOUND_VERSION:-[^}]*}"',
                f'GITHOUND_VERSION: "${{GITHOUND_VERSION:-{version}}}"',
                content,
            )

            compose_file.write_text(content)
            print(f"Updated {compose_file}")


def update_ci_files(repo_root: Path, version: str) -> None:
    """Update CI/CD files with new version."""
    ci_files = [
        repo_root / ".github" / "workflows" / "ci.yml",
        repo_root / ".github" / "workflows" / "release.yml",
    ]

    for ci_file in ci_files:
        if ci_file.exists():
            content = ci_file.read_text()

            # Update version references in CI files
            content = re.sub(
                r'GITHOUND_VERSION: ["\']?[^"\']*["\']?', f'GITHOUND_VERSION: "{version}"', content
            )

            ci_file.write_text(content)
            print(f"Updated {ci_file}")


def show_version_info(repo_root: Path) -> None:
    """Show current version information."""
    git_info = get_git_info(repo_root)
    current_version = get_current_version(repo_root)

    print("GitHound Version Information")
    print("=" * 40)
    print(f"Current version: {current_version or 'No version tags found'}")
    print(f"Git commit: {git_info['commit'][:8] if git_info['commit'] else 'Unknown'}")
    print(f"Git branch: {git_info['branch'] or 'Unknown'}")
    print(f"Git tag: {git_info['tag'] or 'Not on a tag'}")
    print(f"Working directory: {'dirty' if git_info['dirty'] else 'clean'}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="GitHound version management")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Show command
    subparsers.add_parser("show", help="Show current version information")

    # Tag command
    tag_parser = subparsers.add_parser("tag", help="Create a new version tag")
    tag_parser.add_argument("version", help="Version to tag (e.g., 1.0.0)")
    tag_parser.add_argument("-m", "--message", help="Tag message")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update configuration files")
    update_parser.add_argument("version", help="Version to update to")
    update_parser.add_argument("--env", action="store_true", help="Update environment files")
    update_parser.add_argument("--docker", action="store_true", help="Update Docker files")
    update_parser.add_argument("--ci", action="store_true", help="Update CI files")
    update_parser.add_argument("--all", action="store_true", help="Update all files")

    args = parser.parse_args()

    # Find repository root
    repo_root = Path(__file__).parent.parent
    if not (repo_root / ".git").exists():
        print("Error: Not in a git repository")
        sys.exit(1)

    if args.command == "show":
        show_version_info(repo_root)

    elif args.command == "tag":
        if create_version_tag(repo_root, args.version, args.message):
            print(f"Successfully created tag for version {args.version}")
        else:
            sys.exit(1)

    elif args.command == "update":
        if args.all or args.env:
            update_environment_files(repo_root, args.version)

        if args.all or args.docker:
            update_docker_files(repo_root, args.version)

        if args.all or args.ci:
            update_ci_files(repo_root, args.version)

        if not any([args.env, args.docker, args.ci, args.all]):
            print("No update targets specified. Use --all or specific flags.")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
