#!/usr/bin/env python3
"""
GitHound Cache Manager

This script manages various caches and temporary data used by GitHound,
including build caches, test caches, and application data.

Usage:
    python scripts/cache-manager.py [command] [options]

Commands:
    clean       - Clean caches
    info        - Show cache information
    analyze     - Analyze cache usage
    optimize    - Optimize caches
"""

from utils import (
    console,
    format_bytes,
    get_directory_size,
    get_project_root,
    print_error,
    print_header,
    print_info,
    print_section,
    print_step,
    print_success,
    print_warning,
    safe_remove_directory,
    safe_remove_file,
    StatusContext,
    confirm,
)
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import typer
from rich.table import Table

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))


app = typer.Typer(
    name="cache-manager",
    help="GitHound Cache Manager",
    add_completion=False,
)


class CacheManager:
    """Manages GitHound caches and temporary data."""

    def __init__(self):
        self.project_root = get_project_root()

        # Define cache locations
        self.cache_locations = {
            # Python caches
            "__pycache__": {
                "description": "Python bytecode cache",
                "pattern": "**/__pycache__",
                "type": "directory",
                "safe_to_delete": True,
            },
            "pytest_cache": {
                "description": "Pytest cache",
                "pattern": ".pytest_cache",
                "type": "directory",
                "safe_to_delete": True,
            },
            "mypy_cache": {
                "description": "MyPy type checker cache",
                "pattern": ".mypy_cache",
                "type": "directory",
                "safe_to_delete": True,
            },
            "ruff_cache": {
                "description": "Ruff linter cache",
                "pattern": ".ruff_cache",
                "type": "directory",
                "safe_to_delete": True,
            },

            # Build artifacts
            "build": {
                "description": "Build artifacts",
                "pattern": "build",
                "type": "directory",
                "safe_to_delete": True,
            },
            "dist": {
                "description": "Distribution packages",
                "pattern": "dist",
                "type": "directory",
                "safe_to_delete": True,
            },
            "egg_info": {
                "description": "Egg info directories",
                "pattern": "*.egg-info",
                "type": "directory",
                "safe_to_delete": True,
            },

            # Test and coverage
            "coverage": {
                "description": "Coverage data",
                "pattern": ".coverage*",
                "type": "file",
                "safe_to_delete": True,
            },
            "htmlcov": {
                "description": "HTML coverage reports",
                "pattern": "htmlcov",
                "type": "directory",
                "safe_to_delete": True,
            },

            # Documentation
            "docs_build": {
                "description": "Documentation build",
                "pattern": "docs/site",
                "type": "directory",
                "safe_to_delete": True,
            },

            # Application caches
            "app_cache": {
                "description": "Application cache",
                "pattern": ".cache",
                "type": "directory",
                "safe_to_delete": False,  # May contain user data
            },
            "logs": {
                "description": "Log files",
                "pattern": "logs",
                "type": "directory",
                "safe_to_delete": False,  # May contain important logs
            },
            "temp": {
                "description": "Temporary files",
                "pattern": "temp",
                "type": "directory",
                "safe_to_delete": True,
            },

            # IDE and editor caches
            "vscode": {
                "description": "VS Code settings",
                "pattern": ".vscode",
                "type": "directory",
                "safe_to_delete": False,
            },
            "idea": {
                "description": "IntelliJ IDEA files",
                "pattern": ".idea",
                "type": "directory",
                "safe_to_delete": False,
            },
        }

    def find_cache_items(self, cache_type: str) -> List[Path]:
        """Find cache items of a specific type."""
        if cache_type not in self.cache_locations:
            return []

        config = self.cache_locations[cache_type]
        pattern = config["pattern"]

        if pattern.startswith("**/"):
            # Recursive pattern
            return list(self.project_root.rglob(pattern[3:]))
        else:
            # Direct pattern
            return list(self.project_root.glob(pattern))

    def get_cache_info(self, cache_type: str) -> Dict:
        """Get information about a cache type."""
        config = self.cache_locations[cache_type]
        items = self.find_cache_items(cache_type)

        total_size = 0
        item_count = 0

        for item in items:
            if item.exists():
                if item.is_file():
                    total_size += item.stat().st_size
                    item_count += 1
                elif item.is_dir():
                    total_size += get_directory_size(item)
                    item_count += 1

        return {
            "type": cache_type,
            "description": config["description"],
            "items": items,
            "item_count": item_count,
            "total_size": total_size,
            "safe_to_delete": config["safe_to_delete"],
        }

    def get_all_cache_info(self) -> Dict[str, Dict]:
        """Get information about all caches."""
        return {
            cache_type: self.get_cache_info(cache_type)
            for cache_type in self.cache_locations
        }

    def clean_cache(self, cache_type: str, force: bool = False) -> Tuple[bool, int, int]:
        """
        Clean a specific cache type.

        Returns:
            (success, files_removed, bytes_freed)
        """
        if cache_type not in self.cache_locations:
            return False, 0, 0

        config = self.cache_locations[cache_type]

        # Safety check
        if not config["safe_to_delete"] and not force:
            print_warning(
                f"Cache '{cache_type}' is not safe to delete automatically")
            if not confirm(f"Delete {config['description']} anyway?"):
                return False, 0, 0

        items = self.find_cache_items(cache_type)
        files_removed = 0
        bytes_freed = 0

        for item in items:
            if not item.exists():
                continue

            try:
                if item.is_file():
                    size = item.stat().st_size
                    if safe_remove_file(item):
                        files_removed += 1
                        bytes_freed += size
                elif item.is_dir():
                    size = get_directory_size(item)
                    if safe_remove_directory(item):
                        files_removed += 1
                        bytes_freed += size
            except Exception as e:
                print_warning(f"Failed to remove {item}: {e}")

        return True, files_removed, bytes_freed

    def clean_all_safe_caches(self) -> Tuple[int, int]:
        """Clean all caches that are safe to delete."""
        total_files = 0
        total_bytes = 0

        for cache_type, config in self.cache_locations.items():
            if config["safe_to_delete"]:
                success, files, bytes_freed = self.clean_cache(cache_type)
                if success:
                    total_files += files
                    total_bytes += bytes_freed
                    if files > 0:
                        print_step(
                            f"Cleaned {config['description']}: {files} items, {format_bytes(bytes_freed)}",
                            "success"
                        )

        return total_files, total_bytes

    def analyze_cache_usage(self) -> Dict:
        """Analyze cache usage patterns."""
        all_info = self.get_all_cache_info()

        analysis = {
            "total_caches": len(all_info),
            "total_size": sum(info["total_size"] for info in all_info.values()),
            "total_items": sum(info["item_count"] for info in all_info.values()),
            "safe_to_delete_size": sum(
                info["total_size"] for info in all_info.values()
                if info["safe_to_delete"]
            ),
            "largest_caches": sorted(
                all_info.items(),
                key=lambda x: x[1]["total_size"],
                reverse=True
            )[:5],
            "by_category": {
                "build": sum(
                    info["total_size"] for cache_type, info in all_info.items()
                    if cache_type in ["build", "dist", "egg_info"]
                ),
                "python": sum(
                    info["total_size"] for cache_type, info in all_info.items()
                    if cache_type in ["__pycache__", "mypy_cache", "ruff_cache"]
                ),
                "test": sum(
                    info["total_size"] for cache_type, info in all_info.items()
                    if cache_type in ["pytest_cache", "coverage", "htmlcov"]
                ),
                "docs": sum(
                    info["total_size"] for cache_type, info in all_info.items()
                    if cache_type in ["docs_build"]
                ),
                "app": sum(
                    info["total_size"] for cache_type, info in all_info.items()
                    if cache_type in ["app_cache", "logs", "temp"]
                ),
            }
        }

        return analysis


@app.command()
def clean(
    cache_type: str = typer.Argument(
        None, help="Specific cache to clean (or 'all' for safe caches)"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force clean even unsafe caches"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be cleaned"),
) -> None:
    """Clean caches."""
    manager = CacheManager()

    if dry_run:
        print_header("Cache Cleaning - Dry Run")

        if cache_type == "all" or cache_type is None:
            all_info = manager.get_all_cache_info()
            safe_caches = {k: v for k, v in all_info.items()
                           if v["safe_to_delete"]}
        else:
            if cache_type not in manager.cache_locations:
                print_error(f"Unknown cache type: {cache_type}")
                sys.exit(1)
            safe_caches = {cache_type: manager.get_cache_info(cache_type)}

        total_size = sum(info["total_size"] for info in safe_caches.values())
        total_items = sum(info["item_count"] for info in safe_caches.values())

        print_info(f"Would clean {len(safe_caches)} cache types")
        print_info(f"Would remove {total_items} items")
        print_info(f"Would free {format_bytes(total_size)}")

        for cache_name, info in safe_caches.items():
            if info["item_count"] > 0:
                print_step(
                    f"{info['description']}: {info['item_count']} items, {format_bytes(info['total_size'])}",
                    "running"
                )

        return

    print_header("Cache Cleaning")

    if cache_type == "all" or cache_type is None:
        # Clean all safe caches
        with StatusContext("Cleaning safe caches"):
            total_files, total_bytes = manager.clean_all_safe_caches()

        print_success(
            f"Cleaned {total_files} items, freed {format_bytes(total_bytes)}")

    else:
        # Clean specific cache
        if cache_type not in manager.cache_locations:
            print_error(f"Unknown cache type: {cache_type}")
            print_info("Available cache types:")
            for ct in manager.cache_locations:
                print_info(f"  - {ct}")
            sys.exit(1)

        config = manager.cache_locations[cache_type]

        with StatusContext(f"Cleaning {config['description']}"):
            success, files_removed, bytes_freed = manager.clean_cache(
                cache_type, force)

        if success:
            print_success(
                f"Cleaned {files_removed} items, freed {format_bytes(bytes_freed)}")
        else:
            print_error("Cache cleaning failed or was cancelled")
            sys.exit(1)


@app.command()
def info(
    cache_type: str = typer.Argument(
        None, help="Specific cache to show info for"),
) -> None:
    """Show cache information."""
    manager = CacheManager()

    print_header("GitHound Cache Information")

    if cache_type:
        # Show specific cache info
        if cache_type not in manager.cache_locations:
            print_error(f"Unknown cache type: {cache_type}")
            sys.exit(1)

        info = manager.get_cache_info(cache_type)

        print_section(f"{info['description']} ({cache_type})")
        print_info(f"Items: {info['item_count']}")
        print_info(f"Size: {format_bytes(info['total_size'])}")
        print_info(
            f"Safe to delete: {'Yes' if info['safe_to_delete'] else 'No'}")

        if info['items']:
            print_info("Locations:")
            for item in info['items'][:10]:  # Show first 10
                print_info(f"  - {item}")
            if len(info['items']) > 10:
                print_info(f"  ... and {len(info['items']) - 10} more")

    else:
        # Show all cache info
        all_info = manager.get_all_cache_info()

        table = Table(title="Cache Overview")
        table.add_column("Cache Type", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Items", style="yellow", justify="right")
        table.add_column("Size", style="green", justify="right")
        table.add_column("Safe", style="magenta", justify="center")

        total_size = 0
        total_items = 0

        for cache_type, info in all_info.items():
            total_size += info["total_size"]
            total_items += info["item_count"]

            table.add_row(
                cache_type,
                info["description"],
                str(info["item_count"]),
                format_bytes(info["total_size"]),
                "✅" if info["safe_to_delete"] else "⚠️"
            )

        console.print(table)

        print_section("Summary")
        print_info(f"Total caches: {len(all_info)}")
        print_info(f"Total items: {total_items}")
        print_info(f"Total size: {format_bytes(total_size)}")


@app.command()
def analyze() -> None:
    """Analyze cache usage patterns."""
    manager = CacheManager()

    print_header("GitHound Cache Analysis")

    with StatusContext("Analyzing cache usage"):
        analysis = manager.analyze_cache_usage()

    print_section("Overview")
    print_info(f"Total caches: {analysis['total_caches']}")
    print_info(f"Total items: {analysis['total_items']}")
    print_info(f"Total size: {format_bytes(analysis['total_size'])}")
    print_info(
        f"Safe to delete: {format_bytes(analysis['safe_to_delete_size'])}")

    print_section("Largest Caches")
    for cache_type, info in analysis['largest_caches']:
        if info['total_size'] > 0:
            print_info(
                f"{info['description']}: {format_bytes(info['total_size'])}")

    print_section("By Category")
    for category, size in analysis['by_category'].items():
        if size > 0:
            print_info(f"{category.title()}: {format_bytes(size)}")


@app.command()
def optimize() -> None:
    """Optimize caches for better performance."""
    manager = CacheManager()

    print_header("Cache Optimization")

    # For now, optimization just means cleaning safe caches
    # In the future, this could include more sophisticated optimization

    analysis = manager.analyze_cache_usage()

    if analysis['safe_to_delete_size'] > 1024 * 1024:  # > 1MB
        print_info(
            f"Found {format_bytes(analysis['safe_to_delete_size'])} of safe-to-delete caches")

        if confirm("Clean safe caches to optimize performance?"):
            with StatusContext("Optimizing caches"):
                total_files, total_bytes = manager.clean_all_safe_caches()

            print_success(
                f"Optimization complete: freed {format_bytes(total_bytes)}")
        else:
            print_info("Optimization cancelled")
    else:
        print_success("Caches are already optimized!")


if __name__ == "__main__":
    app()
