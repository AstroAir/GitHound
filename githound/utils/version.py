"""Version utilities for GitHound.

This module provides utilities for accessing version information consistently
across the application, including build metadata and version comparison.
"""

import os
import subprocess
from pathlib import Path


def get_version() -> str:
    """Get the current GitHound version.

    Returns:
        Version string in semantic version format.
    """
    try:
        from .._version import __version__

        return __version__
    except ImportError:
        # Fallback for development installations
        try:
            from importlib.metadata import version

            return version("githound")
        except ImportError:
            # Final fallback
            return "0.1.0-dev"


def get_build_info() -> dict[str, str | None | bool]:
    """Get build information including git metadata.

    Returns:
        Dictionary containing build information:
        - version: Current version
        - git_commit: Git commit hash
        - git_branch: Git branch name
        - git_tag: Git tag (if on a tag)
        - build_date: Build date (if available)
        - dirty: Whether working directory has uncommitted changes
    """
    info: dict[str, str | None | bool] = {
        "version": get_version(),
        "git_commit": None,
        "git_branch": None,
        "git_tag": None,
        "build_date": None,
        "dirty": None,
    }

    # Try to get git information
    try:
        repo_root = Path(__file__).parent.parent.parent
        if (repo_root / ".git").exists():
            # Get commit hash
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    info["git_commit"] = result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

            # Get branch name
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    info["git_branch"] = result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

            # Get tag (if on a tag)
            try:
                result = subprocess.run(
                    ["git", "describe", "--exact-match", "--tags", "HEAD"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    info["git_tag"] = result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

            # Check if working directory is dirty
            try:
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    info["dirty"] = bool(result.stdout.strip())
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
    except Exception:
        # Ignore errors in git information gathering
        pass

    # Get build date from environment or file
    info["build_date"] = os.environ.get("BUILD_DATE")

    return info


def get_version_info() -> tuple[int, int, int, str | None]:
    """Parse version string into components.

    Returns:
        Tuple of (major, minor, patch, pre_release)
    """
    version = get_version()

    # Remove 'v' prefix if present
    if version.startswith("v"):
        version = version[1:]

    # Split on '-' to separate version from pre-release
    parts = version.split("-", 1)
    version_part = parts[0]
    pre_release = parts[1] if len(parts) > 1 else None

    # Parse version numbers
    try:
        major, minor, patch = map(int, version_part.split("."))
        return major, minor, patch, pre_release
    except ValueError:
        # Fallback for malformed versions
        return 0, 1, 0, "dev"


def is_development_version() -> bool:
    """Check if this is a development version.

    Returns:
        True if this is a development version.
    """
    version = get_version()
    return (
        "dev" in version.lower()
        or "alpha" in version.lower()
        or "beta" in version.lower()
        or "rc" in version.lower()
        or version.endswith("-dirty")
    )


def format_version_info(include_build_info: bool = False) -> str:
    """Format version information for display.

    Args:
        include_build_info: Whether to include build metadata.

    Returns:
        Formatted version string.
    """
    version = get_version()

    if not include_build_info:
        return version

    build_info = get_build_info()
    lines = [f"GitHound {version}"]

    if build_info["git_commit"] and isinstance(build_info["git_commit"], str):
        commit = build_info["git_commit"][:8]  # Short hash
        if build_info["dirty"]:
            commit += "-dirty"
        lines.append(f"Git: {commit}")

    if build_info["git_branch"] and build_info["git_branch"] != "HEAD":
        lines.append(f"Branch: {build_info['git_branch']}")

    if build_info["git_tag"]:
        lines.append(f"Tag: {build_info['git_tag']}")

    if build_info["build_date"]:
        lines.append(f"Built: {build_info['build_date']}")

    return "\n".join(lines)


def check_version_compatibility(required_version: str) -> bool:
    """Check if current version meets minimum requirements.

    Args:
        required_version: Minimum required version string.

    Returns:
        True if current version meets requirements.
    """
    try:
        current: tuple[int, ...] = get_version_info()[:3]  # (major, minor, patch)
        required: tuple[int, ...] = tuple(map(int, required_version.split(".")))

        # Pad shorter tuple with zeros
        max_len = max(len(current), len(required))
        current = current + (0,) * (max_len - len(current))
        required = required + (0,) * (max_len - len(required))

        return current >= required
    except (ValueError, AttributeError):
        # If we can't parse versions, assume compatible
        return True
