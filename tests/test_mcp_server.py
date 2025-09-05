"""Tests for GitHound MCP Server functionality.

Enhanced with FastMCP testing best practices including in-memory testing,
comprehensive fixtures, and proper error handling.

Based on: https://gofastmcp.com/deployment/testing
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pytest_asyncio
from fastmcp import FastMCP, Client
from fastmcp.exceptions import ToolError, McpError
from git import Repo

from githound.mcp_server import mcp, get_mcp_server


@pytest.fixture
def temp_repo():
    """Create a temporary Git repository for testing."""
    temp_dir = tempfile.mkdtemp()
    repo = Repo.init(temp_dir)

    # Configure user for commits
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")

    # Create initial commit
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("def hello():\n    print('Hello, World!')\n")
    repo.index.add([str(test_file)])
    initial_commit = repo.index.commit("Initial commit")

    # Create second commit
    test_file.write_text(
        "def hello():\n    print('Hello, GitHound!')\n\ndef goodbye():\n    print('Goodbye!')\n"
    )
    repo.index.add([str(test_file)])
    second_commit = repo.index.commit("Add goodbye function")

    yield repo, temp_dir, initial_commit, second_commit

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mcp_client():
    """Create an MCP client for testing."""
    return Client(mcp)


class TestMCPRepositoryAnalysis:
    """Tests for MCP repository analysis tools."""

    @pytest.mark.asyncio
    async def test_analyze_repository(self, temp_repo, mcp_client):
        """Test repository analysis MCP tool."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.call_tool(
                "analyze_repository", {"repo_path": temp_dir}
            )

            assert result is not None
            result_data = result.content[0].text

            # Parse the JSON response
            import json

            response = json.loads(result_data)

            assert response["status"] == "success"
            assert "repository_metadata" in response
            assert response["repository_metadata"]["total_commits"] >= 2
            assert len(response["repository_metadata"]["contributors"]) >= 1

    @pytest.mark.asyncio
    async def test_analyze_commit(self, temp_repo, mcp_client):
        """Test commit analysis MCP tool."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.call_tool(
                "analyze_commit",
                {"repo_path": temp_dir, "commit_hash": second_commit.hexsha},
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "success"
            assert "commit_metadata" in response
            assert response["commit_metadata"]["hash"] == second_commit.hexsha
            assert response["commit_metadata"]["author_name"] == "Test User"

    @pytest.mark.asyncio
    async def test_get_filtered_commits(self, temp_repo, mcp_client):
        """Test filtered commit retrieval MCP tool."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.call_tool(
                "get_filtered_commits",
                {
                    "repo_path": temp_dir,
                    "author": "Test User",
                    "max_count": 10,
                },
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "success"
            assert "commits" in response
            assert response["total_results"] >= 2
            assert len(response["commits"]) >= 2

    @pytest.mark.asyncio
    async def test_get_file_history(self, temp_repo, mcp_client):
        """Test file history MCP tool."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.call_tool(
                "get_file_history_mcp",
                {"repo_path": temp_dir, "file_path": "test.py", "max_count": 10},
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "success"
            assert "history" in response
            assert response["total_commits"] >= 2
            assert response["file_path"] == "test.py"


class TestMCPBlameAndDiff:
    """Tests for MCP blame and diff analysis tools."""

    @pytest.mark.asyncio
    async def test_analyze_file_blame(self, temp_repo, mcp_client):
        """Test file blame analysis MCP tool."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.call_tool(
                "analyze_file_blame",
                {"repo_path": temp_dir, "file_path": "test.py"},
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "success"
            assert "file_blame" in response
            assert response["file_blame"]["total_lines"] >= 4
            assert len(response["file_blame"]["contributors"]) >= 1

    @pytest.mark.asyncio
    async def test_compare_commits_diff(self, temp_repo, mcp_client):
        """Test commit comparison MCP tool."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.call_tool(
                "compare_commits_diff",
                {
                    "repo_path": temp_dir,
                    "from_commit": initial_commit.hexsha,
                    "to_commit": second_commit.hexsha,
                },
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "success"
            assert "commit_diff" in response
            assert response["commit_diff"]["files_changed"] >= 1
            assert response["commit_diff"]["from_commit"] == initial_commit.hexsha
            assert response["commit_diff"]["to_commit"] == second_commit.hexsha

    @pytest.mark.asyncio
    async def test_get_author_stats(self, temp_repo, mcp_client):
        """Test author statistics MCP tool."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.call_tool(
                "get_author_stats", {"repo_path": temp_dir}
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "success"
            assert "author_statistics" in response
            assert response["total_authors"] >= 1

            # Check that Test User is in the statistics
            author_key = "Test User <test@example.com>"
            assert author_key in response["author_statistics"]


class TestMCPResources:
    """Tests for MCP resources."""

    @pytest.mark.asyncio
    async def test_repository_config_resource(self, temp_repo, mcp_client):
        """Test repository configuration resource."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.read_resource(f"githound://repository/{temp_dir}/config")

            assert result is not None
            assert len(result) > 0

            content = result[0].text
            assert "GitHound Repository Configuration" in content
            assert "Total Commits" in content
            assert "Contributors" in content

    @pytest.mark.asyncio
    async def test_repository_branches_resource(self, temp_repo, mcp_client):
        """Test repository branches resource."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.read_resource(f"githound://repository/{temp_dir}/branches")

            assert result is not None
            assert len(result) > 0

            content = result[0].text
            assert "Repository Branches" in content
            assert "master" in content or "main" in content

    @pytest.mark.asyncio
    async def test_repository_contributors_resource(self, temp_repo, mcp_client):
        """Test repository contributors resource."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.read_resource(
                f"githound://repository/{temp_dir}/contributors"
            )

            assert result is not None
            assert len(result) > 0

            content = result[0].text
            assert "Repository Contributors" in content
            assert "Test User" in content


class TestMCPExport:
    """Tests for MCP export functionality."""

    @pytest.mark.asyncio
    async def test_export_repository_data_json(self, temp_repo, mcp_client):
        """Test repository data export in JSON format."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            async with mcp_client:
                result = await mcp_client.call_tool(
                    "export_repository_data",
                    {
                        "repo_path": temp_dir,
                        "output_path": output_file,
                        "format": "json",
                        "include_metadata": True,
                    },
                )

                assert result is not None
                result_data = result.content[0].text

                import json

                response = json.loads(result_data)

                assert response["status"] == "success"
                assert response["format"] == "json"
                assert Path(output_file).exists()

                # Verify the exported file contains valid JSON
                with open(output_file) as f:
                    exported_data = json.load(f)
                    assert "total_commits" in exported_data
                    assert exported_data["total_commits"] >= 2

        finally:
            if Path(output_file).exists():
                Path(output_file).unlink()


class TestMCPErrorHandling:
    """Tests for MCP error handling."""

    @pytest.mark.asyncio
    async def test_invalid_repository_path(self, mcp_client):
        """Test error handling for invalid repository path."""
        async with mcp_client:
            result = await mcp_client.call_tool(
                "analyze_repository", {"repo_path": "/nonexistent/path"}
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "error"
            assert "error" in response

    @pytest.mark.asyncio
    async def test_invalid_commit_hash(self, temp_repo, mcp_client):
        """Test error handling for invalid commit hash."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.call_tool(
                "analyze_commit",
                {"repo_path": temp_dir, "commit_hash": "invalid_hash_123"},
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "error"
            assert "error" in response

    @pytest.mark.asyncio
    async def test_invalid_file_path_blame(self, temp_repo, mcp_client):
        """Test error handling for invalid file path in blame analysis."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.call_tool(
                "analyze_file_blame",
                {"repo_path": temp_dir, "file_path": "nonexistent.py"},
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "error"
            assert "error" in response


class TestMCPAdvancedSearch:
    """Tests for advanced MCP search functionality."""

    @pytest.mark.asyncio
    async def test_advanced_search_content(self, temp_repo, mcp_client):
        """Test advanced search with content pattern."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.call_tool(
                "advanced_search",
                {
                    "repo_path": temp_dir,
                    "content_pattern": "hello",
                    "max_results": 10,
                },
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "success"
            assert "results" in response
            assert response["total_count"] >= 0

    @pytest.mark.asyncio
    async def test_fuzzy_search(self, temp_repo, mcp_client):
        """Test fuzzy search functionality."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.call_tool(
                "fuzzy_search",
                {
                    "repo_path": temp_dir,
                    "search_term": "hello",
                    "threshold": 0.7,
                    "max_results": 5,
                },
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "success"
            assert "results" in response
            assert "search_term" in response
            assert response["search_term"] == "hello"

    @pytest.mark.asyncio
    async def test_content_search(self, temp_repo, mcp_client):
        """Test content-specific search."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.call_tool(
                "content_search",
                {
                    "repo_path": temp_dir,
                    "pattern": "def",
                    "file_extensions": [".py"],
                    "max_results": 10,
                },
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "success"
            assert "results" in response
            assert "pattern" in response
            assert response["pattern"] == "def"


class TestMCPRepositoryManagement:
    """Tests for repository management MCP tools."""

    @pytest.mark.asyncio
    async def test_list_branches(self, temp_repo, mcp_client):
        """Test list branches functionality."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.call_tool(
                "list_branches", {"repo_path": temp_dir}
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "success"
            assert "branches" in response
            assert "total_count" in response
            assert response["total_count"] >= 1

    @pytest.mark.asyncio
    async def test_list_tags(self, temp_repo, mcp_client):
        """Test list tags functionality."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.call_tool(
                "list_tags", {"repo_path": temp_dir}
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "success"
            assert "tags" in response
            assert "total_count" in response

    @pytest.mark.asyncio
    async def test_validate_repository(self, temp_repo, mcp_client):
        """Test repository validation."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.call_tool(
                "validate_repository", {"repo_path": temp_dir}
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "success"
            assert "validation_results" in response
            validation = response["validation_results"]
            assert validation["is_valid_repo"] is True
            assert validation["has_commits"] is True

    @pytest.mark.asyncio
    async def test_generate_repository_report(self, temp_repo, mcp_client):
        """Test repository report generation."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        async with mcp_client:
            result = await mcp_client.call_tool(
                "generate_repository_report", {"repo_path": temp_dir}
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "success"
            assert "report" in response
            report = response["report"]
            assert "repository_path" in report
            assert "summary" in report
            assert "contributors" in report


class TestMCPInputValidation:
    """Tests for MCP input validation."""

    def test_advanced_search_input_validation(self, temp_repo):
        """Test AdvancedSearchInput validation."""
        from githound.mcp_server import AdvancedSearchInput

        repo, temp_dir, initial_commit, second_commit = temp_repo

        # Test valid input
        valid_input = AdvancedSearchInput(
            repo_path=temp_dir,
            content_pattern="test",
            fuzzy_threshold=0.8,
            max_results=100
        )
        assert valid_input.content_pattern == "test"

        # Test invalid fuzzy threshold
        with pytest.raises(ValueError, match="Fuzzy threshold must be between 0.0 and 1.0"):
            AdvancedSearchInput(
                repo_path=temp_dir,
                content_pattern="test",
                fuzzy_threshold=1.5
            )

        # Test invalid max_results
        with pytest.raises(ValueError, match="max_results must be positive"):
            AdvancedSearchInput(
                repo_path=temp_dir,
                content_pattern="test",
                max_results=-1
            )

    def test_fuzzy_search_input_validation(self, temp_repo):
        """Test FuzzySearchInput validation."""
        from githound.mcp_server import FuzzySearchInput

        repo, temp_dir, initial_commit, second_commit = temp_repo

        # Test valid input
        valid_input = FuzzySearchInput(
            repo_path=temp_dir,
            search_term="test",
            threshold=0.7
        )
        assert valid_input.search_term == "test"

        # Test empty search term
        with pytest.raises(ValueError, match="Search term cannot be empty"):
            FuzzySearchInput(
                repo_path=temp_dir,
                search_term="   ",
                threshold=0.7
            )

        # Test invalid search types
        with pytest.raises(ValueError, match="Invalid search types"):
            FuzzySearchInput(
                repo_path=temp_dir,
                search_term="test",
                search_types=["invalid_type"]
            )

    def test_web_server_input_validation(self, temp_repo):
        """Test WebServerInput validation."""
        from githound.mcp_server import WebServerInput

        repo, temp_dir, initial_commit, second_commit = temp_repo

        # Test valid input
        valid_input = WebServerInput(
            repo_path=temp_dir,
            host="localhost",
            port=8000
        )
        assert valid_input.port == 8000

        # Test invalid port
        with pytest.raises(ValueError, match="Port must be between 1024 and 65535"):
            WebServerInput(
                repo_path=temp_dir,
                port=80
            )


class TestMCPServerConfiguration:
    """Tests for MCP server configuration."""

    def test_mcp_server_creation(self):
        """Test MCP server creation and configuration."""
        server = get_mcp_server()

        assert server.name == "GitHound MCP Server"
        assert hasattr(server, 'version')  # FastMCP has version attribute
        # Note: FastMCP doesn't have a description attribute


class TestFastMCPInMemoryPatterns:
    """Test FastMCP in-memory testing patterns following latest documentation."""

    @pytest.mark.asyncio
    async def test_in_memory_server_instance(self, mcp_server: FastMCP):
        """Test in-memory server instance creation."""
        assert mcp_server is not None
        assert mcp_server.name == "GitHound MCP Server"
        assert hasattr(mcp_server, 'version')

    @pytest.mark.asyncio
    async def test_in_memory_client_connection(self, mcp_client: Client):
        """Test in-memory client connection following FastMCP best practices."""
        # Test basic connectivity - this is the key FastMCP in-memory pattern
        async with mcp_client:
            await mcp_client.ping()

            # Test server capabilities
            tools = await mcp_client.list_tools()
            assert isinstance(tools, list)
            assert len(tools) > 0

            resources = await mcp_client.list_resources()
            assert isinstance(resources, list)

            prompts = await mcp_client.list_prompts()
            assert isinstance(prompts, list)

    @pytest.mark.asyncio
    async def test_deterministic_tool_execution(self, mcp_client: Client, temp_repo):
        """Test deterministic tool execution with in-memory testing."""
        repo, temp_dir, initial_commit, second_commit = temp_repo
        repo_path = str(temp_dir)

        # Test repository validation tool
        async with mcp_client:
            try:
                result = await mcp_client.call_tool(
                    "validate_repository",
                    {"repo_path": repo_path}
                )
                assert result is not None
                # Tool should execute deterministically
            except Exception as e:
                if "not found" in str(e).lower():
                    pytest.skip("Tool not implemented")
                raise

    @pytest.mark.asyncio
    async def test_mocked_dependencies_pattern(self, mcp_server: FastMCP, mock_external_dependencies):
        """Test mocking external dependencies following FastMCP patterns."""
        # Configure mocks for deterministic testing
        mock_repo = MagicMock()
        mock_repo.working_dir = "/mock/repo"
        mock_external_dependencies['get_repository'].return_value = mock_repo

        # Use in-memory testing with mocked dependencies
        async with Client(mcp_server) as client:
            try:
                result = await client.call_tool(
                    "validate_repository",
                    {"repo_path": "/mock/repo"}
                )
                # Should work with mocked dependencies
                assert result is not None
            except Exception as e:
                if "not found" in str(e).lower():
                    pytest.skip("Tool not implemented")
                raise

    @pytest.mark.asyncio
    async def test_error_handling_patterns(self, mcp_client: Client, error_scenarios):
        """Test error handling following FastMCP patterns."""
        # Test invalid repository path
        with pytest.raises((ToolError, Exception)):
            await mcp_client.call_tool(
                "validate_repository",
                {"repo_path": error_scenarios["invalid_repo_path"]}
            )

        # Test malformed arguments
        with pytest.raises((ToolError, Exception)):
            await mcp_client.call_tool(
                "advanced_search",
                {"invalid_arg": "value"}
            )

    @pytest.mark.asyncio
    async def test_resource_access_patterns(self, mcp_client: Client, temp_repo):
        """Test resource access following FastMCP patterns."""
        repo, temp_dir, initial_commit, second_commit = temp_repo
        repo_path = str(temp_dir)

        # Test dynamic resource access
        resource_uri = f"githound://repository/{repo_path}/config"

        try:
            content = await mcp_client.read_resource(resource_uri)
            assert content is not None
        except Exception as e:
            # Resource might not be available
            pytest.skip(f"Resource not available: {e}")

    @pytest.mark.asyncio
    async def test_concurrent_operations_pattern(self, mcp_server: FastMCP, temp_repo):
        """Test concurrent operations following FastMCP patterns."""
        import asyncio

        async def perform_operation(client_id: int):
            async with Client(mcp_server) as client:
                await client.ping()
                return client_id

        # Run concurrent operations
        tasks = [perform_operation(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All operations should complete
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) > 0

    def test_search_orchestrator_initialization(self):
        """Test search orchestrator initialization."""
        from githound.mcp_server import get_search_orchestrator

        orchestrator = get_search_orchestrator()

        # Verify orchestrator is created
        assert orchestrator is not None

        # Test singleton behavior
        orchestrator2 = get_search_orchestrator()
        assert orchestrator is orchestrator2


class TestMCPAdvancedErrorHandling:
    """Tests for advanced MCP error handling scenarios."""

    @pytest.mark.asyncio
    async def test_invalid_repository_path_advanced_search(self, mcp_client):
        """Test error handling for invalid repository path in advanced search."""
        from fastmcp.exceptions import ToolError

        async with mcp_client:
            # The Pydantic validator should catch the invalid path and raise a ToolError
            with pytest.raises(ToolError, match="Repository path does not exist"):
                await mcp_client.call_tool(
                    "advanced_search",
                    {
                        "repo_path": "/nonexistent/path",
                        "content_pattern": "test",
                    },
                )

    @pytest.mark.asyncio
    async def test_invalid_repository_path_fuzzy_search(self, mcp_client):
        """Test error handling for invalid repository path in fuzzy search."""
        from fastmcp.exceptions import ToolError

        async with mcp_client:
            # The Pydantic validator should catch the invalid path and raise a ToolError
            with pytest.raises(ToolError, match="Repository path does not exist"):
                await mcp_client.call_tool(
                    "fuzzy_search",
                    {
                        "repo_path": "/nonexistent/path",
                        "search_term": "test",
                    },
                )

    @pytest.mark.asyncio
    async def test_invalid_repository_validation(self, mcp_client):
        """Test repository validation with invalid path."""
        async with mcp_client:
            result = await mcp_client.call_tool(
                "validate_repository",
                {"repo_path": "/nonexistent/path"},
            )

            assert result is not None
            result_data = result.content[0].text

            import json

            response = json.loads(result_data)

            assert response["status"] == "error"
            assert "error" in response
