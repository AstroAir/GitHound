"""Performance monitoring and profiling for GitHound search engine."""

import asyncio
import functools
import time
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from typing import Any

import psutil


class PerformanceMonitor:
    """Monitor and track search engine performance metrics."""

    def __init__(self) -> None:
        self.metrics: dict[str, list[float]] = defaultdict(list)
        self.counters: dict[str, int] = defaultdict(int)
        self.start_times: dict[str, float] = {}

        # System metrics
        self.process = psutil.Process()

    def start_timer(self, name: str) -> None:
        """Start a named timer."""
        self.start_times[name] = time.time()

    def stop_timer(self, name: str) -> float:
        """Stop a named timer and record the duration.

        Returns:
            Duration in milliseconds
        """
        if name not in self.start_times:
            return 0.0

        duration_ms = (time.time() - self.start_times[name]) * 1000
        self.metrics[name].append(duration_ms)
        del self.start_times[name]

        return duration_ms

    def record_metric(self, name: str, value: float) -> None:
        """Record a named metric value."""
        self.metrics[name].append(value)

    def increment_counter(self, name: str, amount: int = 1) -> None:
        """Increment a named counter."""
        self.counters[name] += amount

    def get_stats(self, metric_name: str) -> dict[str, float]:
        """Get statistics for a metric.

        Returns:
            Dict with min, max, avg, p50, p95, p99
        """
        values = self.metrics.get(metric_name, [])

        if not values:
            return {
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "count": 0,
            }

        sorted_values = sorted(values)
        count = len(sorted_values)

        return {
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(sorted_values) / count,
            "p50": sorted_values[int(count * 0.5)],
            "p95": sorted_values[int(count * 0.95)] if count > 20 else sorted_values[-1],
            "p99": sorted_values[int(count * 0.99)] if count > 100 else sorted_values[-1],
            "count": count,
        }

    def get_system_metrics(self) -> dict[str, Any]:
        """Get current system resource usage."""
        return {
            "cpu_percent": self.process.cpu_percent(),
            "memory_mb": self.process.memory_info().rss / 1024 / 1024,
            "memory_percent": self.process.memory_percent(),
            "num_threads": self.process.num_threads(),
        }

    def get_all_stats(self) -> dict[str, Any]:
        """Get all performance statistics."""
        stats = {
            "metrics": {},
            "counters": dict(self.counters),
            "system": self.get_system_metrics(),
        }

        # Get stats for all metrics
        for metric_name in self.metrics:
            stats["metrics"][metric_name] = self.get_stats(metric_name)

        return stats

    def reset(self) -> None:
        """Reset all metrics and counters."""
        self.metrics.clear()
        self.counters.clear()
        self.start_times.clear()

    def report(self) -> str:
        """Generate a human-readable performance report."""
        stats = self.get_all_stats()

        lines = [
            "=" * 60,
            "Performance Report",
            "=" * 60,
            "",
            "System Metrics:",
            f"  CPU Usage: {stats['system']['cpu_percent']:.1f}%",
            f"  Memory: {stats['system']['memory_mb']:.1f} MB ({stats['system']['memory_percent']:.1f}%)",
            f"  Threads: {stats['system']['num_threads']}",
            "",
            "Counters:",
        ]

        for name, value in sorted(stats["counters"].items()):
            lines.append(f"  {name}: {value}")

        lines.append("")
        lines.append("Timing Metrics:")

        for metric_name, metric_stats in sorted(stats["metrics"].items()):
            lines.append(f"  {metric_name}:")
            lines.append(f"    Count: {metric_stats['count']}")
            lines.append(f"    Avg: {metric_stats['avg']:.2f}ms")
            lines.append(f"    Min: {metric_stats['min']:.2f}ms")
            lines.append(f"    Max: {metric_stats['max']:.2f}ms")
            lines.append(f"    P95: {metric_stats['p95']:.2f}ms")

        lines.append("=" * 60)

        return "\n".join(lines)


class SearchProfiler:
    """Profiler for detailed search operation analysis."""

    def __init__(self) -> None:
        self.profiles: list[dict[str, Any]] = []
        self.current_profile: dict[str, Any] | None = None

    def start_profile(self, search_id: str, query: Any) -> None:
        """Start profiling a search operation."""
        self.current_profile = {
            "search_id": search_id,
            "query": str(query),
            "start_time": datetime.now(),
            "end_time": None,
            "stages": [],
            "total_time_ms": 0.0,
            "memory_start_mb": psutil.Process().memory_info().rss / 1024 / 1024,
            "memory_peak_mb": 0.0,
        }

    def add_stage(
        self, stage_name: str, duration_ms: float, details: dict[str, Any] | None = None
    ) -> None:
        """Add a profiling stage."""
        if not self.current_profile:
            return

        stage = {
            "name": stage_name,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(),
            "details": details or {},
        }

        self.current_profile["stages"].append(stage)

        # Update peak memory
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024
        if current_memory > self.current_profile["memory_peak_mb"]:
            self.current_profile["memory_peak_mb"] = current_memory

    def end_profile(self) -> dict[str, Any]:
        """End current profile and return results."""
        if not self.current_profile:
            return {}

        self.current_profile["end_time"] = datetime.now()
        self.current_profile["total_time_ms"] = (
            self.current_profile["end_time"] - self.current_profile["start_time"]
        ).total_seconds() * 1000

        # Calculate stage percentages
        total_time = self.current_profile["total_time_ms"]
        for stage in self.current_profile["stages"]:
            stage["percentage"] = (stage["duration_ms"] / total_time * 100) if total_time > 0 else 0

        profile = self.current_profile
        self.profiles.append(profile)
        self.current_profile = None

        return profile

    def get_profile_summary(self, profile: dict[str, Any]) -> str:
        """Generate a summary for a profile."""
        lines = [
            f"Search Profile: {profile['search_id']}",
            f"Query: {profile['query']}",
            f"Total Time: {profile['total_time_ms']:.2f}ms",
            f"Memory: {profile['memory_start_mb']:.1f}MB -> {profile['memory_peak_mb']:.1f}MB",
            "",
            "Stages:",
        ]

        for stage in profile["stages"]:
            lines.append(
                f"  {stage['name']}: {stage['duration_ms']:.2f}ms ({stage['percentage']:.1f}%)"
            )

        return "\n".join(lines)

    def get_all_profiles(self) -> list[dict[str, Any]]:
        """Get all recorded profiles."""
        return self.profiles

    def clear_profiles(self) -> None:
        """Clear all recorded profiles."""
        self.profiles.clear()


def timed(monitor: PerformanceMonitor, metric_name: str) -> Callable:
    """Decorator to time function execution.

    Args:
        monitor: PerformanceMonitor instance
        metric_name: Name of the metric to record

    Example:
        @timed(monitor, "search_execution")
        def search(query):
            # ... search logic
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            monitor.start_timer(metric_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                monitor.stop_timer(metric_name)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            monitor.start_timer(metric_name)
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                monitor.stop_timer(metric_name)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class BottleneckDetector:
    """Detect performance bottlenecks in search operations."""

    def __init__(self, threshold_ms: float = 1000.0) -> None:
        self.threshold_ms = threshold_ms
        self.bottlenecks: list[dict[str, Any]] = []

    def analyze_profile(self, profile: dict[str, Any]) -> list[dict[str, Any]]:
        """Analyze a profile for bottlenecks.

        Returns:
            List of detected bottlenecks
        """
        bottlenecks = []

        # Check total time
        if profile["total_time_ms"] > self.threshold_ms:
            bottlenecks.append(
                {
                    "type": "total_time",
                    "severity": "high",
                    "message": f"Total search time ({profile['total_time_ms']:.0f}ms) exceeds threshold",
                    "recommendation": "Consider optimizing query or using indexes",
                }
            )

        # Check individual stages
        for stage in profile["stages"]:
            if stage["duration_ms"] > self.threshold_ms * 0.5:
                bottlenecks.append(
                    {
                        "type": "slow_stage",
                        "stage": stage["name"],
                        "severity": "medium",
                        "message": f"Stage '{stage['name']}' took {stage['duration_ms']:.0f}ms",
                        "recommendation": f"Optimize {stage['name']} operation",
                    }
                )

            # Check if one stage dominates
            if stage.get("percentage", 0) > 70:
                bottlenecks.append(
                    {
                        "type": "dominant_stage",
                        "stage": stage["name"],
                        "severity": "high",
                        "message": f"Stage '{stage['name']}' accounts for {stage['percentage']:.0f}% of total time",
                        "recommendation": f"Focus optimization efforts on {stage['name']}",
                    }
                )

        # Check memory usage
        memory_increase = profile["memory_peak_mb"] - profile["memory_start_mb"]
        if memory_increase > 500:  # 500MB increase
            bottlenecks.append(
                {
                    "type": "high_memory",
                    "severity": "high",
                    "message": f"Memory increased by {memory_increase:.0f}MB",
                    "recommendation": "Consider streaming results or limiting result size",
                }
            )

        self.bottlenecks.extend(bottlenecks)
        return bottlenecks

    def get_all_bottlenecks(self) -> list[dict[str, Any]]:
        """Get all detected bottlenecks."""
        return self.bottlenecks

    def clear(self) -> None:
        """Clear all detected bottlenecks."""
        self.bottlenecks.clear()
