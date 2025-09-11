#!/usr/bin/env python3
"""
GitHound Performance Benchmark

This script runs comprehensive performance benchmarks for GitHound
to measure and track performance over time.

Usage:
    python scripts/benchmark.py [command] [options]

Commands:
    run         - Run benchmarks
    compare     - Compare with baseline
    report      - Generate benchmark report
    baseline    - Set current performance as baseline
"""

from utils import (
    console,
    get_project_root,
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
from typing import Optional, Union, Any

import typer

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))


app = typer.Typer(
    name="benchmark",
    help="GitHound Performance Benchmark Suite",
    add_completion=False,
)


class BenchmarkRunner:
    """Runs performance benchmarks for GitHound."""

    def __init__(self) -> None:
        self.project_root = get_project_root()
        self.benchmark_dir = self.project_root / ".benchmarks"
        self.benchmark_dir.mkdir(exist_ok=True)
        self.baseline_file = self.benchmark_dir / "baseline.json"

    def run_import_benchmark(self) -> Dict[str, float]:
        """Benchmark import times."""
        print_section("Import Benchmarks")

        benchmarks: dict[str, Any] = {}

        # Core import
        start = time.time()
        try:
            run_command_with_output([
                "python", "-c", "import githound"
            ], cwd=self.project_root)
            import_time = time.time() - start
            benchmarks["core_import"] = import_time
            print_step(f"Core import: {import_time:.3f}s",
                       "success" if import_time < 1.0 else "warning")
        except Exception as e:
            print_step("Core import", "error")
            benchmarks["core_import"] = float('inf')

        # CLI import
        start = time.time()
        try:
            run_command_with_output([
                "python", "-c", "from githound.cli import app"
            ], cwd=self.project_root)
            cli_time = time.time() - start
            benchmarks["cli_import"] = cli_time
            print_step(f"CLI import: {cli_time:.3f}s",
                       "success" if cli_time < 2.0 else "warning")
        except Exception as e:
            print_step("CLI import", "error")
            benchmarks["cli_import"] = float('inf')

        # Search engine import
        start = time.time()
        try:
            run_command_with_output([
                "python", "-c", "from githound.search_engine import SearchOrchestrator"
            ], cwd=self.project_root)
            search_time = time.time() - start
            benchmarks["search_import"] = search_time
            print_step(f"Search engine import: {search_time:.3f}s",
                       "success" if search_time < 1.5 else "warning")
        except Exception as e:
            print_step("Search engine import", "error")
            benchmarks["search_import"] = float('inf')

        return benchmarks

    def run_functionality_benchmark(self) -> Dict[str, float]:
        """Benchmark core functionality."""
        print_section("Functionality Benchmarks")

        benchmarks: dict[str, Any] = {}

        # Repository analysis
        start = time.time()
        try:
            result = run_command_with_output([
                "python", "-c", """
from githound import GitHound
from pathlib import Path
import time

start = time.time()
gh = GitHound(Path('.'))
info = gh.analyze_repository()
duration = time.time() - start
print(f"Analysis took {duration:.3f}s")
"""
            ], cwd=self.project_root)

            if result[0] == 0:
                # Extract duration from output
                output_lines = result[1].strip().split('\n')
                for line in output_lines:
                    if "Analysis took" in line:
                        duration_str = line.split()[-1].replace('s', '')
                        benchmarks["repo_analysis"] = float(duration_str)
                        break
                else:
                    benchmarks["repo_analysis"] = time.time() - start

                print_step(f"Repository analysis: {benchmarks['repo_analysis']:.3f}s",
                           "success" if benchmarks["repo_analysis"] < 5.0 else "warning")
            else:
                print_step("Repository analysis", "error")
                benchmarks["repo_analysis"] = float('inf')
        except Exception as e:
            print_step("Repository analysis", "error")
            benchmarks["repo_analysis"] = float('inf')

        # Search functionality
        start = time.time()
        try:
            result = run_command_with_output([
                "python", "-c", """
from githound import GitHound
from githound.models import SearchQuery
from pathlib import Path
import time

start = time.time()
gh = GitHound(Path('.'))
query = SearchQuery(content_pattern='function')
results = list(gh.search_advanced(query))
duration = time.time() - start
print(f"Search took {duration:.3f}s, found {len(results)} results")
"""
            ], cwd=self.project_root)

            if result[0] == 0:
                # Extract duration from output
                output_lines = result[1].strip().split('\n')
                for line in output_lines:
                    if "Search took" in line:
                        duration_str = line.split()[2].replace('s,', '')
                        benchmarks["search_functionality"] = float(
                            duration_str)
                        break
                else:
                    benchmarks["search_functionality"] = time.time() - start

                print_step(f"Search functionality: {benchmarks['search_functionality']:.3f}s",
                           "success" if benchmarks["search_functionality"] < 10.0 else "warning")
            else:
                print_step("Search functionality", "error")
                benchmarks["search_functionality"] = float('inf')
        except Exception as e:
            print_step("Search functionality", "error")
            benchmarks["search_functionality"] = float('inf')

        return benchmarks

    def run_cli_benchmark(self) -> Dict[str, float]:
        """Benchmark CLI performance."""
        print_section("CLI Benchmarks")

        benchmarks: dict[str, Any] = {}

        # CLI help command
        start = time.time()
        try:
            result = run_command_with_output([
                "python", "-m", "githound.cli", "--help"
            ], cwd=self.project_root)
            help_time = time.time() - start

            if result[0] == 0:
                benchmarks["cli_help"] = help_time
                print_step(f"CLI help: {help_time:.3f}s",
                           "success" if help_time < 2.0 else "warning")
            else:
                print_step("CLI help", "error")
                benchmarks["cli_help"] = float('inf')
        except Exception as e:
            print_step("CLI help", "error")
            benchmarks["cli_help"] = float('inf')

        # CLI version command
        start = time.time()
        try:
            result = run_command_with_output([
                "python", "-m", "githound.cli", "version"
            ], cwd=self.project_root)
            version_time = time.time() - start

            if result[0] == 0:
                benchmarks["cli_version"] = version_time
                print_step(f"CLI version: {version_time:.3f}s",
                           "success" if version_time < 1.0 else "warning")
            else:
                print_step("CLI version", "error")
                benchmarks["cli_version"] = float('inf')
        except Exception as e:
            print_step("CLI version", "error")
            benchmarks["cli_version"] = float('inf')

        return benchmarks

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmark suites."""
        print_header("GitHound Performance Benchmarks")

        start_time = datetime.now()

        results: Dict[str, Any] = {
            "metadata": {
                "timestamp": start_time.isoformat(),
                "version": "0.1.0",  # Could be extracted from pyproject.toml
            },
            "import": self.run_import_benchmark(),
            "functionality": self.run_functionality_benchmark(),
            "cli": self.run_cli_benchmark(),
        }

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        results["metadata"]["duration"] = duration

        print_section("Benchmark Summary")
        print_info(f"Total benchmark time: {duration:.2f}s")

        # Calculate overall score
        all_times: list[Any] = []
        for category in ["import", "functionality", "cli"]:
            for benchmark, time_val in results[category].items():
                if time_val != float('inf'):
                    all_times.append(time_val)

        if all_times:
            avg_time = sum(all_times) / len(all_times)
            print_info(f"Average operation time: {avg_time:.3f}s")
            results["metadata"]["average_time"] = avg_time

        return results

    def save_benchmark_results(self, results: Dict[str, Any], filename: Optional[str] = None) -> Path:
        """Save benchmark results to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_{timestamp}.json"

        filepath = self.benchmark_dir / filename
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        return filepath

    def load_baseline(self) -> Optional[Dict[str, Any]]:
        """Load baseline benchmark results."""
        if not self.baseline_file.exists():
            return None

        try:
            with open(self.baseline_file, 'r') as f:
                data: Dict[str, Any] = json.load(f)
                return data
        except Exception:
            return None

    def save_baseline(self, results: Dict[str, Any]) -> None:
        """Save results as baseline."""
        with open(self.baseline_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

    def compare_with_baseline(self, current: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current results with baseline."""
        baseline = self.load_baseline()
        if not baseline:
            return {"error": "No baseline found"}

        comparison = {
            "baseline_date": baseline["metadata"]["timestamp"],
            "current_date": current["metadata"]["timestamp"],
            "improvements": [],
            "regressions": [],
            "unchanged": [],
        }

        for category in ["import", "functionality", "cli"]:
            if category not in baseline or category not in current:
                continue

            for benchmark in baseline[category]:
                if benchmark not in current[category]:
                    continue

                baseline_time = baseline[category][benchmark]
                current_time = current[category][benchmark]

                if baseline_time == float('inf') or current_time == float('inf'):
                    continue

                change_pct = ((current_time - baseline_time) /
                              baseline_time) * 100

                item = {
                    "benchmark": f"{category}.{benchmark}",
                    "baseline": baseline_time,
                    "current": current_time,
                    "change_pct": change_pct,
                }

                if abs(change_pct) < 5:  # Less than 5% change
                    comparison["unchanged"].append(item)
                elif change_pct < 0:  # Improvement (faster)
                    comparison["improvements"].append(item)
                else:  # Regression (slower)
                    comparison["regressions"].append(item)

        return comparison


@app.command()
def run(
    save: bool = typer.Option(True, "--save/--no-save",
                              help="Save results to file"),
    baseline: bool = typer.Option(
        False, "--baseline", help="Set as new baseline"),
) -> None:
    """Run performance benchmarks."""
    runner = BenchmarkRunner()

    results = runner.run_all_benchmarks()

    if save:
        filepath = runner.save_benchmark_results(results)
        print_info(f"Results saved to: {filepath}")

    if baseline:
        runner.save_baseline(results)
        print_success("Results saved as new baseline")


@app.command()
def compare() -> None:
    """Compare current performance with baseline."""
    runner = BenchmarkRunner()

    print_header("Benchmark Comparison")

    with StatusContext("Running current benchmarks"):
        current = runner.run_all_benchmarks()

    comparison = runner.compare_with_baseline(current)

    if "error" in comparison:
        print_error(comparison["error"])
        print_info("Run 'python scripts/benchmark.py baseline' to set a baseline")
        return

    print_section("Comparison Results")
    print_info(f"Baseline: {comparison['baseline_date']}")
    print_info(f"Current:  {comparison['current_date']}")

    if comparison["improvements"]:
        print_section("Improvements (Faster)")
        for item in comparison["improvements"]:
            print_success(
                f"{item['benchmark']}: {item['change_pct']:.1f}% faster")

    if comparison["regressions"]:
        print_section("Regressions (Slower)")
        for item in comparison["regressions"]:
            print_warning(
                f"{item['benchmark']}: {item['change_pct']:.1f}% slower")

    if comparison["unchanged"]:
        print_section("Unchanged (< 5% change)")
        for item in comparison["unchanged"]:
            print_info(
                f"{item['benchmark']}: {item['change_pct']:.1f}% change")


@app.command()
def baseline() -> None:
    """Set current performance as baseline."""
    runner = BenchmarkRunner()

    if runner.baseline_file.exists():
        from utils import confirm
        if not confirm("Baseline already exists. Overwrite?"):
            print_info("Baseline update cancelled")
            return

    print_header("Setting Performance Baseline")

    results = runner.run_all_benchmarks()
    runner.save_baseline(results)

    print_success("Baseline set successfully!")
    print_info(f"Baseline saved to: {runner.baseline_file}")


@app.command()
def report(
    output: str = typer.Option(
        "benchmark-report.json", "--output", "-o", help="Output file"),
) -> None:
    """Generate detailed benchmark report."""
    runner = BenchmarkRunner()

    results = runner.run_all_benchmarks()

    # Add comparison if baseline exists
    comparison = runner.compare_with_baseline(results)
    if "error" not in comparison:
        results["comparison"] = comparison

    output_path = Path(output)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print_success(f"Benchmark report saved to: {output_path}")


if __name__ == "__main__":
    app()
