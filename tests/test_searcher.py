"""Tests for GitHound searcher module."""

import json
import subprocess
from unittest.mock import MagicMock, Mock, patch

import pytest  # Added missing import

# [attr-defined]
from githound.models import SearchConfig, SearchResult, SearchType
from githound.searcher import search_blob_content


class TestSearchBlobContent:
    """Test search_blob_content function."""

    def test_search_blob_content_basic(self) -> None:
        """Test basic search functionality."""
        content = b"def test_function() -> None:\n    return True\n"
        query = "test_function"
        config = SearchConfig(case_sensitive=False)
        commit_hash = "abc123"
        file_path = "test.py"

        # Mock ripgrep output
        rg_output = {
            "type": "match",
            "data": {
                "path": {"text": "-"},
                "lines": {"text": "def test_function() -> None:"},
                "line_number": 1,
                "absolute_offset": 0,
                "submatches": [{"match": {"text": "test_function"}, "start": 4, "end": 17}],
            },
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                stdout=json.dumps(rg_output) + "\n", stderr="", returncode=0
            )

            results = search_blob_content(content, query, config, commit_hash, file_path)

            assert len(results) == 1
            result = results[0]
            assert result.commit_hash == commit_hash
            # Fixed: file_path is a Path object
            assert str(result.file_path) == file_path
            assert result.line_number == 1
            # Fixed: line_content -> matching_line
            assert result.matching_line == "def test_function() -> None:"
            # Fixed: match_type -> search_type
            assert result.search_type == SearchType.CONTENT

    def test_search_blob_content_case_sensitive(self) -> None:
        """Test case sensitive search."""
        content = b"def Test_Function() -> None:\n    return True\n"
        query = "test_function"
        config = SearchConfig(case_sensitive=True)
        commit_hash = "abc123"
        file_path = "test.py"

        with patch("subprocess.run") as mock_run:
            # Mock no matches for case sensitive search
            mock_run.return_value = Mock(
                stdout="", stderr="", returncode=1  # ripgrep returns 1 when no matches found
            )

            results = search_blob_content(content, query, config, commit_hash, file_path)

            assert len(results) == 0
            # Verify case sensitive flag was passed
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "-i" not in args  # Case insensitive flag should not be present

    def test_search_blob_content_case_insensitive(self) -> None:
        """Test case insensitive search."""
        content = b"def Test_Function() -> None:\n    return True\n"
        query = "test_function"
        config = SearchConfig(case_sensitive=False)
        commit_hash = "abc123"
        file_path = "test.py"

        rg_output = {
            "type": "match",
            "data": {
                "path": {"text": "-"},
                "lines": {"text": "def Test_Function() -> None:"},
                "line_number": 1,
                "absolute_offset": 0,
                "submatches": [{"match": {"text": "Test_Function"}, "start": 4, "end": 17}],
            },
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                stdout=json.dumps(rg_output) + "\n", stderr="", returncode=0
            )

            results = search_blob_content(content, query, config, commit_hash, file_path)

            assert len(results) == 1
            # Verify case insensitive flag was passed
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "-i" in args  # Case insensitive flag should be present

    def test_search_blob_content_multiple_matches(self) -> None:
        """Test search with multiple matches."""
        content = b"def test_function() -> None:\n    test_var = 'test'\n    return test_var\n"
        query = "test"
        config = SearchConfig(case_sensitive=False)
        commit_hash = "abc123"
        file_path = "test.py"

        # Mock multiple ripgrep outputs
        rg_outputs = [
            {
                "type": "match",
                "data": {
                    "path": {"text": "-"},
                    "lines": {"text": "def test_function() -> None:"},
                    "line_number": 1,
                    "absolute_offset": 0,
                    "submatches": [{"match": {"text": "test"}, "start": 4, "end": 8}],
                },
            },
            {
                "type": "match",
                "data": {
                    "path": {"text": "-"},
                    "lines": {"text": "    test_var = 'test'"},
                    "line_number": 2,
                    "absolute_offset": 20,
                    "submatches": [
                        {"match": {"text": "test"}, "start": 4, "end": 8},
                        {"match": {"text": "test"}, "start": 15, "end": 19},
                    ],
                },
            },
        ]

        stdout_content = "\n".join(json.dumps(output) for output in rg_outputs) + "\n"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout=stdout_content, stderr="", returncode=0)

            results = search_blob_content(content, query, config, commit_hash, file_path)

            assert len(results) == 2
            assert results[0].line_number == 1
            assert results[1].line_number == 2

    def test_search_blob_content_no_matches(self) -> None:
        """Test search with no matches."""
        content = b"def function() -> None:\n    return True\n"
        query = "nonexistent"
        config = SearchConfig(case_sensitive=False)
        commit_hash = "abc123"
        file_path = "test.py"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                stdout="", stderr="", returncode=1  # ripgrep returns 1 when no matches found
            )

            results = search_blob_content(content, query, config, commit_hash, file_path)

            assert len(results) == 0

    def test_search_blob_content_subprocess_error(self) -> None:
        """Test handling of subprocess errors."""
        content = b"def test_function() -> None:\n    return True\n"
        query = "test"
        config = SearchConfig(case_sensitive=False)
        commit_hash = "abc123"
        file_path = "test.py"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(2, "rg")

            with pytest.raises(subprocess.CalledProcessError):
                search_blob_content(content, query, config, commit_hash, file_path)

    def test_search_blob_content_invalid_json(self) -> None:
        """Test handling of invalid JSON output from ripgrep."""
        content = b"def test_function() -> None:\n    return True\n"
        query = "test"
        config = SearchConfig(case_sensitive=False)
        commit_hash = "abc123"
        file_path = "test.py"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="invalid json output\n", stderr="", returncode=0)

            # Should handle invalid JSON gracefully and return empty results
            results = search_blob_content(content, query, config, commit_hash, file_path)
            assert len(results) == 0

    def test_search_blob_content_binary_content(self) -> None:
        """Test search with binary content."""
        # Binary content (e.g., image file)
        content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        query = "test"
        config = SearchConfig(case_sensitive=False)
        commit_hash = "abc123"
        file_path = "image.png"

        with patch("subprocess.run") as mock_run:
            # ripgrep typically returns no matches for binary files
            mock_run.return_value = Mock(stdout="", stderr="", returncode=1)

            results = search_blob_content(content, query, config, commit_hash, file_path)

            assert len(results) == 0

    def test_search_blob_content_empty_content(self) -> None:
        """Test search with empty content."""
        content = b""
        query = "test"
        config = SearchConfig(case_sensitive=False)
        commit_hash = "abc123"
        file_path = "empty.py"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="", stderr="", returncode=1)

            results = search_blob_content(content, query, config, commit_hash, file_path)

            assert len(results) == 0

    def test_search_blob_content_regex_pattern(self) -> None:
        """Test search with regex pattern."""
        content = (
            b"def test_function_1() -> None:\n    pass\ndef test_function_2() -> None:\n    pass\n"
        )
        query = r"test_function_\d+"
        config = SearchConfig(case_sensitive=False)
        commit_hash = "abc123"
        file_path = "test.py"

        rg_outputs = [
            {
                "type": "match",
                "data": {
                    "path": {"text": "-"},
                    "lines": {"text": "def test_function_1() -> None:"},
                    "line_number": 1,
                    "absolute_offset": 0,
                    "submatches": [{"match": {"text": "test_function_1"}, "start": 4, "end": 19}],
                },
            },
            {
                "type": "match",
                "data": {
                    "path": {"text": "-"},
                    "lines": {"text": "def test_function_2() -> None:"},
                    "line_number": 3,
                    "absolute_offset": 30,
                    "submatches": [{"match": {"text": "test_function_2"}, "start": 4, "end": 19}],
                },
            },
        ]

        stdout_content = "\n".join(json.dumps(output) for output in rg_outputs) + "\n"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout=stdout_content, stderr="", returncode=0)

            results = search_blob_content(content, query, config, commit_hash, file_path)

            assert len(results) == 2
            # Fixed: line_content -> matching_line
            assert "test_function_1" in results[0].matching_line
            # Fixed: line_content -> matching_line
            assert "test_function_2" in results[1].matching_line
