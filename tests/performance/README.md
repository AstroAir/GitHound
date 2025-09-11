# Performance Tests

This directory contains performance tests for GitHound operations to ensure scalability and efficiency.

## Test Categories

### Git Operations Performance

- Repository loading and initialization
- Commit history retrieval with large datasets
- Blame operations on large files
- Diff calculations for complex changes
- Branch and tag enumeration

### Search Performance

- Large repository search operations
- Complex query pattern matching
- Concurrent search operations
- Memory usage during searches
- Search result pagination

### MCP Server Performance

- Tool invocation latency
- Resource access performance
- Concurrent client handling
- Memory usage under load
- Response time benchmarks

### API Performance

- REST endpoint response times
- WebSocket connection handling
- Concurrent request processing
- Large data export operations
- Database query performance

## Running Performance Tests

Run all performance tests:

```bash
pytest tests/performance/ -m performance
```

Run specific performance test categories:

```bash
pytest tests/performance/test_git_performance.py
pytest tests/performance/test_search_performance.py
pytest tests/performance/test_mcp_performance.py
pytest tests/performance/test_api_performance.py
```

Run with benchmarking:

```bash
pytest tests/performance/ --benchmark-only
```

## Performance Benchmarks

### Target Performance Metrics

#### Git Operations

- Repository loading: < 1 second for repos up to 10k commits
- Commit history (100 commits): < 500ms
- File blame (1000 lines): < 2 seconds
- Diff calculation: < 1 second for typical changes

#### Search Operations

- Simple search (1000 commits): < 3 seconds
- Complex pattern search: < 10 seconds
- Concurrent searches (5 parallel): < 15 seconds total

#### MCP Server

- Tool invocation latency: < 100ms
- Resource access: < 200ms
- Concurrent clients (10): < 2 seconds response time

#### API Performance

- REST endpoint response: < 500ms
- WebSocket connection: < 100ms setup
- Large export (10MB): < 30 seconds

## Test Configuration

### Performance Test Settings

```python
# Performance test configuration
PERFORMANCE_CONFIG = {
    'large_repo_commits': 10000,
    'large_file_lines': 5000,
    'concurrent_operations': 10,
    'timeout_seconds': 60,
    'memory_limit_mb': 512,
    'benchmark_rounds': 5
}
```

### Benchmark Fixtures

```python
@pytest.fixture
def large_repository():
    """Create a large test repository for performance testing."""
    # Implementation details...

@pytest.fixture
def performance_monitor():
    """Monitor resource usage during tests."""
    # Implementation details...
```

## Performance Monitoring

### Memory Usage Tracking

```python
import psutil
import pytest

class MemoryMonitor:
    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = self.get_memory_usage()

    def get_memory_usage(self):
        return self.process.memory_info().rss / 1024 / 1024  # MB

    def check_memory_increase(self, max_increase_mb=100):
        current_memory = self.get_memory_usage()
        increase = current_memory - self.baseline_memory
        assert increase < max_increase_mb, f"Memory increased by {increase}MB"
```

### CPU Usage Monitoring

```python
import time
import threading

class CPUMonitor:
    def __init__(self):
        self.cpu_samples = []
        self.monitoring = False

    def start_monitoring(self):
        self.monitoring = True
        thread = threading.Thread(target=self._monitor_cpu)
        thread.start()

    def stop_monitoring(self):
        self.monitoring = False
        return sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0

    def _monitor_cpu(self):
        while self.monitoring:
            self.cpu_samples.append(psutil.cpu_percent())
            time.sleep(0.1)
```

## Test Data Generation

### Large Repository Generator

```python
def create_large_test_repo(commit_count=1000, file_count=100):
    """Create a large repository for performance testing."""
    # Generate repository with specified characteristics
    # Include various file types and sizes
    # Create realistic commit patterns
    pass
```

### Performance Test Fixtures

```python
@pytest.fixture(scope="session")
def large_test_repository():
    """Session-scoped large repository for performance tests."""
    # Create once per test session
    pass

@pytest.fixture
def performance_baseline():
    """Establish performance baseline for comparisons."""
    # Record baseline metrics
    pass
```

## Continuous Performance Monitoring

### Performance Regression Detection

```python
class PerformanceRegression:
    def __init__(self, baseline_file="performance_baseline.json"):
        self.baseline_file = baseline_file
        self.load_baseline()

    def load_baseline(self):
        # Load historical performance data
        pass

    def check_regression(self, test_name, current_time, threshold=1.2):
        # Compare against baseline with threshold
        pass

    def update_baseline(self, test_name, time_taken):
        # Update baseline with new measurements
        pass
```

### Performance Reporting

```python
def generate_performance_report(test_results):
    """Generate performance test report."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_results': test_results,
        'summary': {
            'total_tests': len(test_results),
            'passed': sum(1 for r in test_results if r['passed']),
            'failed': sum(1 for r in test_results if not r['passed']),
            'average_duration': sum(r['duration'] for r in test_results) / len(test_results)
        }
    }
    return report
```
