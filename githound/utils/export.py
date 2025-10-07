"""Export utilities for GitHound search results."""

import csv
import json
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO, cast

# Optional dependencies with graceful fallbacks
try:
    import pandas as pd  # type: ignore[import-not-found]
    HAS_PANDAS = True
except ImportError:
    pd = cast(Any, None)
    HAS_PANDAS = False

try:
    import yaml  # type: ignore[import-not-found]
    HAS_YAML = True
except ImportError:
    yaml = cast(Any, None)
    HAS_YAML = False

from rich.console import Console

from ..models import SearchMetrics, SearchResult
from ..schemas import (
    DataFilter,
    ExportOptions,
    OutputFormat,
    SortCriteria,
)


class ExportManager:
    """Manager for exporting search results in various formats."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def export_to_json(
        self,
        results: list[SearchResult],
        output_file: Path,
        include_metadata: bool = True,
        pretty: bool = True,
    ) -> None:
        """Export results to JSON format."""
        try:
            json_data = self._prepare_json_data(results, include_metadata)

            with open(output_file, "w", encoding="utf-8") as f:
                if pretty:
                    json.dump(json_data, f, indent=2,
                              default=self._json_serializer)
                else:
                    json.dump(json_data, f, default=self._json_serializer)

            self.console.print(
                f"[green]✓ Exported {len(results)} results to {output_file}[/green]")

        except Exception as e:
            self.console.print(f"[red]✗ Failed to export to JSON: {e}[/red]")
            raise

    def export_to_yaml(
        self,
        results: list[SearchResult],
        output_file: Path,
        include_metadata: bool = True,
        pretty: bool = True,
    ) -> None:
        """Export results to YAML format."""
        if not HAS_YAML:
            self.console.print(
                "[yellow]⚠ YAML export requires PyYAML. Falling back to JSON format.[/yellow]"
            )
            json_file = output_file.with_suffix(".json")
            self.export_to_json(results, json_file, include_metadata, pretty)
            return

        try:
            yaml_data = self._prepare_json_data(results, include_metadata)

            with open(output_file, "w", encoding="utf-8") as f:
                if pretty:
                    yaml.dump(
                        yaml_data,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        indent=2,
                        sort_keys=False,
                    )
                else:
                    yaml.dump(yaml_data, f, default_flow_style=True,
                              allow_unicode=True)

            self.console.print(
                f"[green]✓ Exported {len(results)} results to {output_file}[/green]")

        except Exception as e:
            self.console.print(f"[red]✗ Failed to export to YAML: {e}[/red]")
            raise

    def export_to_csv(
        self, results: list[SearchResult], output_file: Path, include_metadata: bool = True
    ) -> None:
        """Export results to CSV format."""
        try:
            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write header
                header = self._get_csv_header(include_metadata)
                writer.writerow(header)

                # Write data
                for result in results:
                    row = self._result_to_csv_row(result, include_metadata)
                    writer.writerow(row)

            self.console.print(
                f"[green]✓ Exported {len(results)} results to {output_file}[/green]")

        except Exception as e:
            self.console.print(f"[red]✗ Failed to export to CSV: {e}[/red]")
            raise

    def export_to_excel(
        self, results: list[SearchResult], output_file: Path, include_metadata: bool = True
    ) -> None:
        """Export results to Excel format."""
        if not HAS_PANDAS:
            self.console.print(
                "[yellow]⚠ Excel export requires pandas. Falling back to CSV format.[/yellow]"
            )
            csv_file = output_file.with_suffix(".csv")
            self.export_to_csv(results, csv_file, include_metadata)
            return

        try:
            # Prepare data for DataFrame
            data: list[Any] = []
            for result in results:
                row_dict = self._result_to_dict(result, include_metadata)
                data.append(row_dict)

            # Create DataFrame and export
            df = pd.DataFrame(data)
            df.to_excel(output_file, index=False, engine="openpyxl")

            self.console.print(
                f"[green]✓ Exported {len(results)} results to {output_file}[/green]")

        except ImportError:
            self.console.print(
                "[red]✗ Excel export requires 'openpyxl' package. Install with: pip install openpyxl[/red]"
            )
            raise
        except Exception as e:
            self.console.print(f"[red]✗ Failed to export to Excel: {e}[/red]")
            raise

    def export_to_text(
        self, results: list[SearchResult], output_file: Path, format_style: str = "detailed"
    ) -> None:
        """Export results to plain text format."""
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                if format_style == "simple":
                    self._write_simple_text(results, f)
                elif format_style == "detailed":
                    self._write_detailed_text(results, f)
                elif format_style == "summary":
                    self._write_summary_text(results, f)
                else:
                    raise ValueError(f"Unknown format style: {format_style}")

            self.console.print(
                f"[green]✓ Exported {len(results)} results to {output_file}[/green]")

        except Exception as e:
            self.console.print(f"[red]✗ Failed to export to text: {e}[/red]")
            raise

    def stream_export_csv(
        self, results: Iterator[SearchResult], output_file: Path, include_metadata: bool = True
    ) -> None:
        """Stream export results to CSV for large datasets."""
        try:
            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write header
                header = self._get_csv_header(include_metadata)
                writer.writerow(header)

                # Stream write data
                count = 0
                for result in results:
                    row = self._result_to_csv_row(result, include_metadata)
                    writer.writerow(row)
                    count += 1

                    # Flush periodically for large datasets
                    if count % 1000 == 0:
                        f.flush()
                        self.console.print(
                            f"[cyan]Exported {count} results...[/cyan]")

            self.console.print(
                f"[green]✓ Streamed {count} results to {output_file}[/green]")

        except Exception as e:
            self.console.print(
                f"[red]✗ Failed to stream export to CSV: {e}[/red]")
            raise

    def export_metrics(
        self, metrics: SearchMetrics, output_file: Path, format: str = "json"
    ) -> None:
        """Export search metrics."""
        try:
            if format.lower() == "json":
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(metrics.dict() if metrics is not None else None, f, indent=2,
                              default=self._json_serializer)
            elif format.lower() == "txt":
                with open(output_file, "w", encoding="utf-8") as f:
                    self._write_metrics_text(metrics, f)
            else:
                raise ValueError(f"Unsupported metrics format: {format}")

            self.console.print(
                f"[green]✓ Exported metrics to {output_file}[/green]")

        except Exception as e:
            self.console.print(f"[red]✗ Failed to export metrics: {e}[/red]")
            raise

    def _prepare_json_data(
        self, results: list[SearchResult], include_metadata: bool
    ) -> dict[str, Any]:
        """Prepare data for JSON export."""
        json_results: list[Any] = []

        for result in results:
            result_dict: dict[str, Any] = {
                "commit_hash": result.commit_hash,
                "file_path": str(result.file_path),
                "search_type": result.search_type.value,
                "relevance_score": result.relevance_score,
            }

            if result.line_number is not None:
                result_dict["line_number"] = result.line_number

            if result.matching_line is not None:
                result_dict["matching_line"] = result.matching_line

            if include_metadata and result.commit_info:
                result_dict["commit_info"] = {
                    "author_name": result.commit_info.author_name,
                    "author_email": result.commit_info.author_email,
                    "message": result.commit_info.message,
                    "date": result.commit_info.date,
                    "files_changed": result.commit_info.files_changed,
                    "insertions": result.commit_info.insertions,
                    "deletions": result.commit_info.deletions,
                }

            if result.match_context:
                result_dict["match_context"] = result.match_context

            json_results.append(result_dict)

        return {
            "results": json_results,
            "total_count": len(results),
            "exported_at": datetime.now().isoformat(),
        }

    def _get_csv_header(self, include_metadata: bool) -> list[str]:
        """Get CSV header row."""
        header = [
            "commit_hash",
            "file_path",
            "line_number",
            "matching_line",
            "search_type",
            "relevance_score",
        ]

        if include_metadata:
            header.extend(
                [
                    "author_name",
                    "author_email",
                    "commit_date",
                    "commit_message",
                    "files_changed",
                    "insertions",
                    "deletions",
                ]
            )

        return header

    def _result_to_csv_row(self, result: SearchResult, include_metadata: bool) -> list[str]:
        """Convert a search result to CSV row."""
        row = [
            result.commit_hash,
            str(result.file_path),
            str(result.line_number) if result.line_number is not None else "",
            result.matching_line or "",
            result.search_type.value,
            str(result.relevance_score),
        ]

        if include_metadata:
            if result.commit_info:
                row.extend(
                    [
                        result.commit_info.author_name,
                        result.commit_info.author_email,
                        (
                            result.commit_info.date.isoformat()
                            if isinstance(result.commit_info.date, datetime)
                            else str(result.commit_info.date)
                        ),
                        result.commit_info.message,
                        str(result.commit_info.files_changed),
                        str(result.commit_info.insertions),
                        str(result.commit_info.deletions),
                    ]
                )
            else:
                row.extend(["", "", "", "", "", "", ""])

        return row

    def _result_to_dict(self, result: SearchResult, include_metadata: bool) -> dict[str, Any]:
        """Convert a search result to dictionary for DataFrame."""
        data = {
            "commit_hash": result.commit_hash,
            "file_path": str(result.file_path),
            "line_number": result.line_number,
            "matching_line": result.matching_line,
            "search_type": result.search_type.value,
            "relevance_score": result.relevance_score,
        }

        if include_metadata and result.commit_info:
            data.update(
                {
                    "author_name": result.commit_info.author_name,
                    "author_email": result.commit_info.author_email,
                    "commit_date": (
                        result.commit_info.date.isoformat()
                        if isinstance(result.commit_info.date, datetime)
                        else str(result.commit_info.date)
                    ),
                    "commit_message": result.commit_info.message,
                    "files_changed": result.commit_info.files_changed,
                    "insertions": result.commit_info.insertions,
                    "deletions": result.commit_info.deletions,
                }
            )

        return data

    def _write_simple_text(self, results: list[SearchResult], f: TextIO) -> None:
        """Write results in simple text format."""
        for result in results:
            f.write(f"Commit: {result.commit_hash}\n")
            f.write(f"File: {result.file_path}\n")
            if result.matching_line:
                f.write(f"Match: {result.matching_line}\n")
            f.write("\n")

    def _write_detailed_text(self, results: list[SearchResult], f: TextIO) -> None:
        """Write results in detailed text format."""
        for i, result in enumerate(results, 1):
            f.write(f"=== Result {i} ===\n")
            f.write(f"Commit: {result.commit_hash}\n")
            f.write(f"File: {result.file_path}\n")
            f.write(f"Search Type: {result.search_type.value}\n")
            f.write(f"Relevance Score: {result.relevance_score:.3f}\n")

            if result.line_number:
                f.write(f"Line: {result.line_number}\n")

            if result.matching_line:
                f.write(f"Match: {result.matching_line}\n")

            if result.commit_info:
                f.write(
                    f"Author: {result.commit_info.author_name} <{result.commit_info.author_email}>\n"
                )
                f.write(f"Date: {result.commit_info.date}\n")
                f.write(f"Message: {result.commit_info.message}\n")

            f.write("\n")

    def _write_summary_text(self, results: list[SearchResult], f: TextIO) -> None:
        """Write results in summary text format."""
        f.write("GitHound Search Results Summary\n")
        f.write("==============================\n\n")
        f.write(f"Total Results: {len(results)}\n")
        f.write(
            f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Group by search type
        by_type: dict[str, list[SearchResult]] = {}
        for result in results:
            search_type = result.search_type.value
            if search_type not in by_type:
                by_type[search_type] = []
            by_type[search_type].append(result)

        for search_type, type_results in by_type.items():
            f.write(f"{search_type.upper()} Results ({len(type_results)}):\n")
            f.write("-" * 40 + "\n")

            for result in type_results[:10]:  # Show first 10
                f.write(f"  {result.commit_hash[:8]} - {result.file_path}\n")

            if len(type_results) > 10:
                f.write(f"  ... and {len(type_results) - 10} more\n")

            f.write("\n")

    def _write_metrics_text(self, metrics: SearchMetrics, f: TextIO) -> None:
        """Write metrics in text format."""
        f.write("GitHound Search Metrics\n")
        f.write("======================\n\n")
        f.write(f"Commits Searched: {metrics.total_commits_searched}\n")
        f.write(f"Files Searched: {metrics.total_files_searched}\n")
        f.write(f"Results Found: {metrics.total_results_found}\n")
        f.write(f"Search Duration: {metrics.search_duration_ms:.2f} ms\n")
        f.write(f"Cache Hits: {metrics.cache_hits}\n")
        f.write(f"Cache Misses: {metrics.cache_misses}\n")

        if metrics.memory_usage_mb:
            f.write(f"Peak Memory Usage: {metrics.memory_usage_mb:.2f} MB\n")

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for datetime and other objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        return str(obj)

    def export_with_options(
        self, results: list[SearchResult], output_file: Path, options: ExportOptions
    ) -> None:
        """Export results with advanced options including filtering and sorting."""
        try:
            # Apply filters
            filtered_results = self._apply_filters(results, options.filters)

            # Apply sorting
            sorted_results = self._apply_sorting(
                filtered_results, options.sort_by)

            # Apply field selection
            if options.fields or options.exclude_fields:
                # This would be implemented for structured formats
                pass

            # Export based on format
            if options.format == OutputFormat.JSON:
                self.export_to_json(
                    sorted_results, output_file, options.include_metadata, options.pretty_print
                )
            elif options.format == OutputFormat.YAML:
                self.export_to_yaml(
                    sorted_results, output_file, options.include_metadata, options.pretty_print
                )
            elif options.format == OutputFormat.CSV:
                self.export_to_csv(sorted_results, output_file,
                                   options.include_metadata)
            elif options.format == OutputFormat.TEXT:
                self.export_to_text(sorted_results, output_file, "detailed")
            else:
                raise ValueError(
                    f"Unsupported export format: {options.format}")

        except Exception as e:
            self.console.print(
                f"[red]✗ Failed to export with options: {e}[/red]")
            raise

    def _apply_filters(
        self, results: list[SearchResult], filters: list[DataFilter]
    ) -> list[SearchResult]:
        """Apply data filters to results."""
        if not filters:
            return results

        filtered_results: list[Any] = []
        for result in results:
            include_result = True

            for filter_criteria in filters:
                if not self._evaluate_filter(result, filter_criteria):
                    include_result = False
                    break

            if include_result:
                filtered_results.append(result)

        return filtered_results

    def _evaluate_filter(self, result: SearchResult, filter_criteria: DataFilter) -> bool:
        """Evaluate a single filter against a result."""
        # Get the field value from the result
        field_value = self._get_field_value(result, filter_criteria.field)

        if field_value is None:
            return False

        # Convert to string for string operations
        if isinstance(field_value, str):
            if not filter_criteria.case_sensitive:
                field_value = field_value.lower()
                if isinstance(filter_criteria.value, str):
                    filter_criteria.value = filter_criteria.value.lower()

        # Apply the filter operator
        from ..schemas import FilterOperator

        if filter_criteria.operator == FilterOperator.EQUALS:
            return bool(field_value == filter_criteria.value)
        elif filter_criteria.operator == FilterOperator.NOT_EQUALS:
            return bool(field_value != filter_criteria.value)
        elif filter_criteria.operator == FilterOperator.CONTAINS:
            return bool(str(filter_criteria.value) in str(field_value))
        elif filter_criteria.operator == FilterOperator.NOT_CONTAINS:
            return bool(str(filter_criteria.value) not in str(field_value))
        elif filter_criteria.operator == FilterOperator.STARTS_WITH:
            return bool(str(field_value).startswith(str(filter_criteria.value)))
        elif filter_criteria.operator == FilterOperator.ENDS_WITH:
            return bool(str(field_value).endswith(str(filter_criteria.value)))
        elif filter_criteria.operator == FilterOperator.GREATER_THAN:
            return self._compare_numeric(field_value, filter_criteria.value, lambda x, y: x > y)
        elif filter_criteria.operator == FilterOperator.LESS_THAN:
            return self._compare_numeric(field_value, filter_criteria.value, lambda x, y: x < y)
        elif filter_criteria.operator == FilterOperator.GREATER_EQUAL:
            return self._compare_numeric(field_value, filter_criteria.value, lambda x, y: x >= y)
        elif filter_criteria.operator == FilterOperator.LESS_EQUAL:
            return self._compare_numeric(field_value, filter_criteria.value, lambda x, y: x <= y)
        elif filter_criteria.operator == FilterOperator.IN:
            try:
                # Ensure the value is a container type for 'in' operator
                if isinstance(filter_criteria.value, (list, tuple, set, str)):
                    return bool(field_value in filter_criteria.value)
                else:
                    return False
            except TypeError:
                return False
        elif filter_criteria.operator == FilterOperator.NOT_IN:
            try:
                # Ensure the value is a container type for 'not in' operator
                if isinstance(filter_criteria.value, (list, tuple, set, str)):
                    return bool(field_value not in filter_criteria.value)
                else:
                    return True
            except TypeError:
                return True
        elif filter_criteria.operator == FilterOperator.REGEX:
            import re

            pattern = re.compile(
                str(filter_criteria.value),
                re.IGNORECASE if not filter_criteria.case_sensitive else 0,
            )
            return bool(pattern.search(str(field_value)))

        # This line is unreachable if all enum members are handled.
        # Adding a safeguard for unexpected cases.
        raise ValueError(
            f"Unsupported filter operator: {filter_criteria.operator}")

    def _get_field_value(self, result: SearchResult, field_path: str) -> Any:
        """Get a field value from a result using dot notation."""
        obj = result
        for field in field_path.split("."):
            if hasattr(obj, field):
                obj = getattr(obj, field)
            else:
                return None
        return obj

    def _compare_numeric(self, val1: Any, val2: Any, op: Any) -> bool:
        """Safely compare two values as numbers."""
        try:
            num1 = float(val1)
            num2 = float(val2)
            return bool(op(num1, num2))
        except (ValueError, TypeError):
            return False

    def _apply_sorting(
        self, results: list[SearchResult], sort_criteria: list[SortCriteria]
    ) -> list[SearchResult]:
        """Apply sorting to results."""
        if not sort_criteria:
            return results

        # Sort by multiple criteria (reverse order for proper precedence)
        sorted_results = results.copy()
        for criteria in reversed(sort_criteria):
            reverse = criteria.order.value == "desc"
            sorted_results.sort(
                key=lambda x: self._get_field_value(x, criteria.field) or "", reverse=reverse
            )

        return sorted_results
