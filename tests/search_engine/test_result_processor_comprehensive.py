"""Comprehensive tests for GitHound search engine result processor module."""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from githound.search_engine.result_processor import (
    ResultProcessor,
    ResultFilter,
    ResultAggregator,
    ResultFormatter,
    ProcessorConfig,
    FilterCriteria,
    AggregationStrategy
)
from githound.models import SearchResult, SearchType, CommitInfo
from githound.schemas import OutputFormat, SortCriteria, SortOrder


@pytest.fixture
def processor_config() -> ProcessorConfig:
    """Create processor configuration for testing."""
    return ProcessorConfig(
        enable_deduplication=True,
        enable_filtering=True,
        enable_aggregation=True,
        max_results=1000,
        default_sort=SortCriteria.RELEVANCE,
        default_order=SortOrder.DESCENDING
    )


@pytest.fixture
def sample_search_results() -> List[SearchResult]:
    """Create sample search results for processing tests."""
    base_time = datetime.now()
    
    return [
        SearchResult(
            commit_hash="abc123",
            file_path="src/main.py",
            line_number=10,
            matching_line="def main_function():",
            search_type=SearchType.CONTENT,
            relevance_score=0.9,
            commit_info=CommitInfo(
                hash="abc123",
                short_hash="abc123",
                author_name="Alice",
                author_email="alice@example.com",
                committer_name="Alice",
                committer_email="alice@example.com",
                message="Add main function",
                date=base_time - timedelta(days=1),
                files_changed=1,
                insertions=10,
                deletions=0
            )
        ),
        SearchResult(
            commit_hash="abc123",  # Duplicate commit
            file_path="src/main.py",
            line_number=15,
            matching_line="    return True",
            search_type=SearchType.CONTENT,
            relevance_score=0.7,
            commit_info=CommitInfo(
                hash="abc123",
                short_hash="abc123",
                author_name="Alice",
                author_email="alice@example.com",
                committer_name="Alice",
                committer_email="alice@example.com",
                message="Add main function",
                date=base_time - timedelta(days=1),
                files_changed=1,
                insertions=10,
                deletions=0
            )
        ),
        SearchResult(
            commit_hash="def456",
            file_path="src/utils.py",
            line_number=25,
            matching_line="def utility_function():",
            search_type=SearchType.CONTENT,
            relevance_score=0.8,
            commit_info=CommitInfo(
                hash="def456",
                short_hash="def456",
                author_name="Bob",
                author_email="bob@example.com",
                committer_name="Bob",
                committer_email="bob@example.com",
                message="Add utility functions",
                date=base_time - timedelta(days=30),
                files_changed=2,
                insertions=50,
                deletions=5
            )
        ),
        SearchResult(
            commit_hash="ghi789",
            file_path="tests/test_main.py",
            line_number=5,
            matching_line="def test_main_function():",
            search_type=SearchType.CONTENT,
            relevance_score=0.6,
            commit_info=CommitInfo(
                hash="ghi789",
                short_hash="ghi789",
                author_name="Charlie",
                author_email="charlie@example.com",
                committer_name="Charlie",
                committer_email="charlie@example.com",
                message="Add tests for main function",
                date=base_time - timedelta(hours=6),
                files_changed=1,
                insertions=20,
                deletions=0
            )
        )
    ]


class TestResultProcessor:
    """Test ResultProcessor class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.processor = ResultProcessor()

    def test_processor_initialization(self, processor_config: ProcessorConfig) -> None:
        """Test processor initialization."""
        processor = ResultProcessor(config=processor_config)
        
        assert processor.config == processor_config
        assert processor.config.enable_deduplication is True
        assert processor.config.max_results == 1000

    def test_process_results_basic(self, sample_search_results: List[SearchResult]) -> None:
        """Test basic result processing."""
        processed = self.processor.process_results(sample_search_results)
        
        assert isinstance(processed, list)
        assert len(processed) <= len(sample_search_results)
        
        # Results should be sorted by relevance (default)
        for i in range(len(processed) - 1):
            assert processed[i].relevance_score >= processed[i + 1].relevance_score

    def test_process_results_with_deduplication(self, sample_search_results: List[SearchResult]) -> None:
        """Test result processing with deduplication."""
        config = ProcessorConfig(enable_deduplication=True)
        processor = ResultProcessor(config=config)
        
        processed = processor.process_results(sample_search_results)
        
        # Should have fewer results due to deduplication
        assert len(processed) < len(sample_search_results)
        
        # No duplicate commit hashes should remain
        commit_hashes = [r.commit_hash for r in processed]
        assert len(commit_hashes) == len(set(commit_hashes))

    def test_process_results_with_filtering(self, sample_search_results: List[SearchResult]) -> None:
        """Test result processing with filtering."""
        filter_criteria = FilterCriteria(
            min_relevance_score=0.75,
            file_extensions=[".py"],
            exclude_test_files=True
        )
        
        processed = self.processor.process_results(
            sample_search_results,
            filter_criteria=filter_criteria
        )
        
        # Should filter out low relevance and test files
        for result in processed:
            assert result.relevance_score >= 0.75
            assert not result.file_path.startswith("tests/")

    def test_process_results_with_sorting(self, sample_search_results: List[SearchResult]) -> None:
        """Test result processing with custom sorting."""
        # Sort by date (newest first)
        processed = self.processor.process_results(
            sample_search_results,
            sort_criteria=SortCriteria.DATE,
            sort_order=SortOrder.DESCENDING
        )
        
        # Results should be sorted by date
        for i in range(len(processed) - 1):
            assert processed[i].commit_info.date >= processed[i + 1].commit_info.date

    def test_process_results_with_limit(self, sample_search_results: List[SearchResult]) -> None:
        """Test result processing with result limit."""
        max_results = 2
        
        processed = self.processor.process_results(
            sample_search_results,
            max_results=max_results
        )
        
        assert len(processed) <= max_results

    def test_process_empty_results(self) -> None:
        """Test processing empty results list."""
        processed = self.processor.process_results([])
        assert processed == []

    def test_process_results_with_aggregation(self, sample_search_results: List[SearchResult]) -> None:
        """Test result processing with aggregation."""
        aggregated = self.processor.aggregate_results(
            sample_search_results,
            strategy=AggregationStrategy.BY_COMMIT
        )
        
        # Should group results by commit
        assert len(aggregated) < len(sample_search_results)
        
        # Each group should have commit hash as key
        for commit_hash, results in aggregated.items():
            assert all(r.commit_hash == commit_hash for r in results)


class TestResultFilter:
    """Test ResultFilter class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.filter = ResultFilter()

    def test_filter_by_relevance_score(self, sample_search_results: List[SearchResult]) -> None:
        """Test filtering by relevance score."""
        min_score = 0.75
        filtered = self.filter.filter_by_relevance(sample_search_results, min_score)
        
        for result in filtered:
            assert result.relevance_score >= min_score

    def test_filter_by_file_extension(self, sample_search_results: List[SearchResult]) -> None:
        """Test filtering by file extension."""
        extensions = [".py"]
        filtered = self.filter.filter_by_file_extension(sample_search_results, extensions)
        
        for result in filtered:
            assert any(result.file_path.endswith(ext) for ext in extensions)

    def test_filter_by_file_path_pattern(self, sample_search_results: List[SearchResult]) -> None:
        """Test filtering by file path pattern."""
        pattern = "src/*"
        filtered = self.filter.filter_by_file_path(sample_search_results, pattern)
        
        for result in filtered:
            assert result.file_path.startswith("src/")

    def test_filter_by_author(self, sample_search_results: List[SearchResult]) -> None:
        """Test filtering by author."""
        author = "Alice"
        filtered = self.filter.filter_by_author(sample_search_results, author)
        
        for result in filtered:
            assert result.commit_info.author_name == author

    def test_filter_by_date_range(self, sample_search_results: List[SearchResult]) -> None:
        """Test filtering by date range."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        filtered = self.filter.filter_by_date_range(
            sample_search_results,
            start_date,
            end_date
        )
        
        for result in filtered:
            assert start_date <= result.commit_info.date <= end_date

    def test_filter_exclude_test_files(self, sample_search_results: List[SearchResult]) -> None:
        """Test excluding test files."""
        filtered = self.filter.exclude_test_files(sample_search_results)
        
        for result in filtered:
            assert not any(
                test_indicator in result.file_path.lower()
                for test_indicator in ["test", "spec", "__test__"]
            )

    def test_filter_by_search_type(self, sample_search_results: List[SearchResult]) -> None:
        """Test filtering by search type."""
        search_types = [SearchType.CONTENT]
        filtered = self.filter.filter_by_search_type(sample_search_results, search_types)
        
        for result in filtered:
            assert result.search_type in search_types

    def test_combined_filters(self, sample_search_results: List[SearchResult]) -> None:
        """Test applying multiple filters."""
        criteria = FilterCriteria(
            min_relevance_score=0.7,
            file_extensions=[".py"],
            exclude_test_files=True,
            authors=["Alice", "Bob"]
        )
        
        filtered = self.filter.apply_criteria(sample_search_results, criteria)
        
        for result in filtered:
            assert result.relevance_score >= 0.7
            assert result.file_path.endswith(".py")
            assert not result.file_path.startswith("tests/")
            assert result.commit_info.author_name in ["Alice", "Bob"]


class TestResultAggregator:
    """Test ResultAggregator class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.aggregator = ResultAggregator()

    def test_aggregate_by_commit(self, sample_search_results: List[SearchResult]) -> None:
        """Test aggregating results by commit."""
        aggregated = self.aggregator.aggregate_by_commit(sample_search_results)
        
        # Should group by commit hash
        for commit_hash, results in aggregated.items():
            assert all(r.commit_hash == commit_hash for r in results)
        
        # Total results should be preserved
        total_results = sum(len(results) for results in aggregated.values())
        assert total_results == len(sample_search_results)

    def test_aggregate_by_file(self, sample_search_results: List[SearchResult]) -> None:
        """Test aggregating results by file."""
        aggregated = self.aggregator.aggregate_by_file(sample_search_results)
        
        # Should group by file path
        for file_path, results in aggregated.items():
            assert all(r.file_path == file_path for r in results)

    def test_aggregate_by_author(self, sample_search_results: List[SearchResult]) -> None:
        """Test aggregating results by author."""
        aggregated = self.aggregator.aggregate_by_author(sample_search_results)
        
        # Should group by author
        for author, results in aggregated.items():
            assert all(r.commit_info.author_name == author for r in results)

    def test_aggregate_by_date(self, sample_search_results: List[SearchResult]) -> None:
        """Test aggregating results by date."""
        aggregated = self.aggregator.aggregate_by_date(sample_search_results)
        
        # Should group by date (day level)
        for date_key, results in aggregated.items():
            # All results in group should be from same day
            dates = [r.commit_info.date.date() for r in results]
            assert len(set(dates)) == 1

    def test_aggregate_with_statistics(self, sample_search_results: List[SearchResult]) -> None:
        """Test aggregation with statistics."""
        aggregated = self.aggregator.aggregate_by_commit(sample_search_results)
        stats = self.aggregator.calculate_aggregation_stats(aggregated)
        
        assert "total_groups" in stats
        assert "total_results" in stats
        assert "average_group_size" in stats
        assert "largest_group_size" in stats


class TestResultFormatter:
    """Test ResultFormatter class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.formatter = ResultFormatter()

    def test_format_to_json(self, sample_search_results: List[SearchResult]) -> None:
        """Test formatting results to JSON."""
        formatted = self.formatter.format_results(
            sample_search_results,
            output_format=OutputFormat.JSON
        )
        
        assert isinstance(formatted, str)
        
        # Should be valid JSON
        import json
        parsed = json.loads(formatted)
        assert isinstance(parsed, list)
        assert len(parsed) == len(sample_search_results)

    def test_format_to_csv(self, sample_search_results: List[SearchResult]) -> None:
        """Test formatting results to CSV."""
        formatted = self.formatter.format_results(
            sample_search_results,
            output_format=OutputFormat.CSV
        )
        
        assert isinstance(formatted, str)
        
        # Should have CSV structure
        lines = formatted.strip().split('\n')
        assert len(lines) > 1  # Header + data rows
        
        # Header should contain expected columns
        header = lines[0]
        assert "commit_hash" in header
        assert "file_path" in header
        assert "relevance_score" in header

    def test_format_to_yaml(self, sample_search_results: List[SearchResult]) -> None:
        """Test formatting results to YAML."""
        formatted = self.formatter.format_results(
            sample_search_results,
            output_format=OutputFormat.YAML
        )
        
        assert isinstance(formatted, str)
        
        # Should be valid YAML
        import yaml
        parsed = yaml.safe_load(formatted)
        assert isinstance(parsed, list)
        assert len(parsed) == len(sample_search_results)

    def test_format_with_custom_fields(self, sample_search_results: List[SearchResult]) -> None:
        """Test formatting with custom field selection."""
        fields = ["commit_hash", "file_path", "relevance_score"]
        
        formatted = self.formatter.format_results(
            sample_search_results,
            output_format=OutputFormat.JSON,
            include_fields=fields
        )
        
        import json
        parsed = json.loads(formatted)
        
        # Each result should only have specified fields
        for result in parsed:
            assert set(result.keys()) == set(fields)

    def test_format_with_metadata(self, sample_search_results: List[SearchResult]) -> None:
        """Test formatting with metadata."""
        metadata = {
            "query": "test search",
            "timestamp": datetime.now().isoformat(),
            "total_results": len(sample_search_results)
        }
        
        formatted = self.formatter.format_results(
            sample_search_results,
            output_format=OutputFormat.JSON,
            include_metadata=True,
            metadata=metadata
        )
        
        import json
        parsed = json.loads(formatted)
        
        assert "metadata" in parsed
        assert "results" in parsed
        assert parsed["metadata"]["total_results"] == len(sample_search_results)


@pytest.mark.integration
class TestResultProcessorIntegration:
    """Integration tests for result processor components."""

    def test_end_to_end_processing_workflow(
        self,
        sample_search_results: List[SearchResult],
        processor_config: ProcessorConfig
    ) -> None:
        """Test complete result processing workflow."""
        processor = ResultProcessor(config=processor_config)
        
        # Define processing parameters
        filter_criteria = FilterCriteria(
            min_relevance_score=0.6,
            exclude_test_files=True
        )
        
        # Process results
        processed = processor.process_results(
            sample_search_results,
            filter_criteria=filter_criteria,
            sort_criteria=SortCriteria.RELEVANCE,
            sort_order=SortOrder.DESCENDING,
            max_results=10
        )
        
        # Verify processing
        assert len(processed) <= 10
        for result in processed:
            assert result.relevance_score >= 0.6
            assert not result.file_path.startswith("tests/")
        
        # Verify sorting
        for i in range(len(processed) - 1):
            assert processed[i].relevance_score >= processed[i + 1].relevance_score

    def test_processing_with_formatting(self, sample_search_results: List[SearchResult]) -> None:
        """Test processing combined with formatting."""
        processor = ResultProcessor()
        formatter = ResultFormatter()
        
        # Process results
        processed = processor.process_results(
            sample_search_results,
            max_results=5
        )
        
        # Format results
        formatted = formatter.format_results(
            processed,
            output_format=OutputFormat.JSON
        )
        
        # Verify formatted output
        import json
        parsed = json.loads(formatted)
        assert len(parsed) <= 5

    def test_performance_with_large_dataset(self) -> None:
        """Test processor performance with large dataset."""
        # Generate large dataset
        large_dataset = []
        for i in range(1000):
            result = SearchResult(
                commit_hash=f"commit_{i}",
                file_path=f"file_{i}.py",
                line_number=i,
                matching_line=f"line {i}",
                search_type=SearchType.CONTENT,
                relevance_score=0.5 + (i % 50) / 100.0
            )
            large_dataset.append(result)
        
        processor = ResultProcessor()
        
        # Process large dataset
        import time
        start_time = time.time()
        processed = processor.process_results(large_dataset, max_results=100)
        end_time = time.time()
        
        # Verify performance and results
        assert len(processed) == 100
        assert end_time - start_time < 1.0  # Should complete within 1 second
