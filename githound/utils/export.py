"""Export utilities for GitHound search results."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TextIO, Iterator, Dict, Any

import pandas as pd
from rich.console import Console

from ..models import SearchResult, SearchMetrics


class ExportManager:
    """Manager for exporting search results in various formats."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def export_to_json(
        self, 
        results: List[SearchResult], 
        output_file: Path,
        include_metadata: bool = True,
        pretty: bool = True
    ):
        """Export results to JSON format."""
        try:
            json_data = self._prepare_json_data(results, include_metadata)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(json_data, f, indent=2, default=self._json_serializer)
                else:
                    json.dump(json_data, f, default=self._json_serializer)
            
            self.console.print(f"[green]✓ Exported {len(results)} results to {output_file}[/green]")
            
        except Exception as e:
            self.console.print(f"[red]✗ Failed to export to JSON: {e}[/red]")
            raise
    
    def export_to_csv(
        self, 
        results: List[SearchResult], 
        output_file: Path,
        include_metadata: bool = True
    ):
        """Export results to CSV format."""
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                header = self._get_csv_header(include_metadata)
                writer.writerow(header)
                
                # Write data
                for result in results:
                    row = self._result_to_csv_row(result, include_metadata)
                    writer.writerow(row)
            
            self.console.print(f"[green]✓ Exported {len(results)} results to {output_file}[/green]")
            
        except Exception as e:
            self.console.print(f"[red]✗ Failed to export to CSV: {e}[/red]")
            raise
    
    def export_to_excel(
        self, 
        results: List[SearchResult], 
        output_file: Path,
        include_metadata: bool = True
    ):
        """Export results to Excel format."""
        try:
            # Prepare data for DataFrame
            data = []
            for result in results:
                row_dict = self._result_to_dict(result, include_metadata)
                data.append(row_dict)
            
            # Create DataFrame and export
            df = pd.DataFrame(data)
            df.to_excel(output_file, index=False, engine='openpyxl')
            
            self.console.print(f"[green]✓ Exported {len(results)} results to {output_file}[/green]")
            
        except ImportError:
            self.console.print("[red]✗ Excel export requires 'openpyxl' package. Install with: pip install openpyxl[/red]")
            raise
        except Exception as e:
            self.console.print(f"[red]✗ Failed to export to Excel: {e}[/red]")
            raise
    
    def export_to_text(
        self, 
        results: List[SearchResult], 
        output_file: Path,
        format_style: str = "detailed"
    ):
        """Export results to plain text format."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                if format_style == "simple":
                    self._write_simple_text(results, f)
                elif format_style == "detailed":
                    self._write_detailed_text(results, f)
                elif format_style == "summary":
                    self._write_summary_text(results, f)
                else:
                    raise ValueError(f"Unknown format style: {format_style}")
            
            self.console.print(f"[green]✓ Exported {len(results)} results to {output_file}[/green]")
            
        except Exception as e:
            self.console.print(f"[red]✗ Failed to export to text: {e}[/red]")
            raise
    
    def stream_export_csv(
        self, 
        results: Iterator[SearchResult], 
        output_file: Path,
        include_metadata: bool = True
    ):
        """Stream export results to CSV for large datasets."""
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
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
                        self.console.print(f"[cyan]Exported {count} results...[/cyan]")
            
            self.console.print(f"[green]✓ Streamed {count} results to {output_file}[/green]")
            
        except Exception as e:
            self.console.print(f"[red]✗ Failed to stream export to CSV: {e}[/red]")
            raise
    
    def export_metrics(
        self, 
        metrics: SearchMetrics, 
        output_file: Path,
        format: str = "json"
    ):
        """Export search metrics."""
        try:
            if format.lower() == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(metrics.dict(), f, indent=2, default=self._json_serializer)
            elif format.lower() == "txt":
                with open(output_file, 'w', encoding='utf-8') as f:
                    self._write_metrics_text(metrics, f)
            else:
                raise ValueError(f"Unsupported metrics format: {format}")
            
            self.console.print(f"[green]✓ Exported metrics to {output_file}[/green]")
            
        except Exception as e:
            self.console.print(f"[red]✗ Failed to export metrics: {e}[/red]")
            raise
    
    def _prepare_json_data(self, results: List[SearchResult], include_metadata: bool) -> Dict[str, Any]:
        """Prepare data for JSON export."""
        json_results = []
        
        for result in results:
            result_dict = {
                "commit_hash": result.commit_hash,
                "file_path": str(result.file_path),
                "search_type": result.search_type.value,
                "relevance_score": result.relevance_score
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
                    "deletions": result.commit_info.deletions
                }
            
            if result.match_context:
                result_dict["match_context"] = result.match_context
            
            json_results.append(result_dict)
        
        return {
            "results": json_results,
            "total_count": len(results),
            "exported_at": datetime.now().isoformat()
        }
    
    def _get_csv_header(self, include_metadata: bool) -> List[str]:
        """Get CSV header row."""
        header = [
            "commit_hash", "file_path", "line_number", "matching_line",
            "search_type", "relevance_score"
        ]
        
        if include_metadata:
            header.extend([
                "author_name", "author_email", "commit_date", 
                "commit_message", "files_changed", "insertions", "deletions"
            ])
        
        return header
    
    def _result_to_csv_row(self, result: SearchResult, include_metadata: bool) -> List[str]:
        """Convert a search result to CSV row."""
        row = [
            result.commit_hash,
            str(result.file_path),
            result.line_number or "",
            result.matching_line or "",
            result.search_type.value,
            result.relevance_score
        ]
        
        if include_metadata:
            if result.commit_info:
                row.extend([
                    result.commit_info.author_name,
                    result.commit_info.author_email,
                    result.commit_info.date.isoformat() if isinstance(result.commit_info.date, datetime) else str(result.commit_info.date),
                    result.commit_info.message,
                    result.commit_info.files_changed,
                    result.commit_info.insertions,
                    result.commit_info.deletions
                ])
            else:
                row.extend(["", "", "", "", "", "", ""])
        
        return row
    
    def _result_to_dict(self, result: SearchResult, include_metadata: bool) -> Dict[str, Any]:
        """Convert a search result to dictionary for DataFrame."""
        data = {
            "commit_hash": result.commit_hash,
            "file_path": str(result.file_path),
            "line_number": result.line_number,
            "matching_line": result.matching_line,
            "search_type": result.search_type.value,
            "relevance_score": result.relevance_score
        }
        
        if include_metadata and result.commit_info:
            data.update({
                "author_name": result.commit_info.author_name,
                "author_email": result.commit_info.author_email,
                "commit_date": result.commit_info.date,
                "commit_message": result.commit_info.message,
                "files_changed": result.commit_info.files_changed,
                "insertions": result.commit_info.insertions,
                "deletions": result.commit_info.deletions
            })
        
        return data
    
    def _write_simple_text(self, results: List[SearchResult], f: TextIO):
        """Write results in simple text format."""
        for result in results:
            f.write(f"Commit: {result.commit_hash}\n")
            f.write(f"File: {result.file_path}\n")
            if result.matching_line:
                f.write(f"Match: {result.matching_line}\n")
            f.write("\n")
    
    def _write_detailed_text(self, results: List[SearchResult], f: TextIO):
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
                f.write(f"Author: {result.commit_info.author_name} <{result.commit_info.author_email}>\n")
                f.write(f"Date: {result.commit_info.date}\n")
                f.write(f"Message: {result.commit_info.message}\n")
            
            f.write("\n")
    
    def _write_summary_text(self, results: List[SearchResult], f: TextIO):
        """Write results in summary text format."""
        f.write(f"GitHound Search Results Summary\n")
        f.write(f"==============================\n\n")
        f.write(f"Total Results: {len(results)}\n")
        f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Group by search type
        by_type = {}
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
    
    def _write_metrics_text(self, metrics: SearchMetrics, f: TextIO):
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
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime and other objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        return str(obj)
