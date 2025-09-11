# GitHound Utilities

This directory contains utility modules that provide supporting functionality for the GitHound application.

## Modules

### Progress Management (`progress.py`)

Advanced progress reporting and cancellation support for long-running operations.

#### Key Classes

- **ProgressManager**: Advanced progress manager with multiple task tracking and cancellation support
- **CancellationToken**: Thread-safe cancellation token for graceful operation termination
- **SimpleProgressReporter**: Basic progress reporter for simple use cases

#### Features

- **Multi-task Progress Tracking**: Track progress across multiple concurrent operations
- **Cancellation Support**: Graceful cancellation with Ctrl+C handling
- **Rich Progress Display**: Beautiful progress bars with time estimates
- **Final Statistics**: Comprehensive summary after operation completion
- **Thread Safety**: Safe to use across multiple threads

#### Usage Example

```python
from githound.utils import ProgressManager

with ProgressManager(enable_cancellation=True) as progress:
    # Add tasks
    task1 = progress.add_task("search", "Searching commits...", 100)
    task2 = progress.add_task("index", "Building index...", 50)

    # Update progress
    progress.update_task("search", completed=25, description="Found 10 matches")
    progress.update_task("index", advance=10)

    # Complete tasks
    progress.complete_task("search", "Search completed")
    progress.complete_task("index", "Index built")
```

### Export Management (`export.py`)

Comprehensive export utilities for search results in multiple formats.

#### Key Classes

- **ExportManager**: Manager for exporting search results in various formats

#### Supported Formats

- **JSON**: Structured data with optional metadata
- **CSV**: Tabular data compatible with spreadsheet applications
- **Excel**: Native Excel format with formatting (requires openpyxl)
- **Text**: Human-readable plain text in multiple styles
- **Streaming**: Memory-efficient export for large datasets

#### Features

- **Multiple Export Formats**: JSON, CSV, Excel, and text formats
- **Metadata Inclusion**: Optional detailed commit information
- **Streaming Export**: Handle large result sets efficiently
- **Custom Formatting**: Different text output styles (simple, detailed, summary)
- **Error Handling**: Robust error handling with user-friendly messages

#### Usage Example

```python
from githound.utils import ExportManager
from pathlib import Path

export_manager = ExportManager()

# Export to JSON with metadata
export_manager.export_to_json(
    results,
    Path("results.json"),
    include_metadata=True
)

# Export to CSV
export_manager.export_to_csv(
    results,
    Path("results.csv")
)

# Export to Excel (requires openpyxl)
export_manager.export_to_excel(
    results,
    Path("results.xlsx")
)

# Export to text with detailed formatting
export_manager.export_to_text(
    results,
    Path("results.txt"),
    format_style="detailed"
)

# Stream export for large datasets
export_manager.stream_export_csv(
    result_iterator,
    Path("large_results.csv")
)
```

## Integration with CLI

These utilities are integrated into the GitHound CLI to provide:

1. **Enhanced Progress Reporting**: Real-time progress updates with cancellation support
2. **Flexible Export Options**: Multiple output formats for different use cases
3. **User Experience**: Rich, interactive interface with detailed feedback

## Performance Considerations

- **Memory Efficiency**: Streaming exports prevent memory issues with large datasets
- **Progress Throttling**: Updates are throttled to prevent UI spam
- **Cancellation Handling**: Graceful shutdown preserves partial results
- **Error Recovery**: Robust error handling maintains application stability

## Future Enhancements

- **Custom Export Templates**: User-defined export formats
- **Compression Support**: Automatic compression for large exports
- **Cloud Export**: Direct export to cloud storage services
- **Real-time Streaming**: WebSocket-based real-time progress updates
