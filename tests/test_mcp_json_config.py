"""Tests for MCP.json configuration support."""  # [attr-defined]

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from githound.mcp.config import (  # [attr-defined]
    find_mcp_json_files,
    get_server_config,
    get_server_config_from_mcp_json,
    load_mcp_json_config,
)

# [attr-defined]
from githound.mcp.models import MCPJsonConfig, MCPServerConfig, ServerConfig


class TestMCPJsonModels:
    """Test MCP.json configuration models."""  # [attr-defined]

    def test_mcp_server_config_validation(self) -> None:
        """Test MCPServerConfig validation."""
        # Valid configuration
        config = MCPServerConfig(
            command="python",
            args=["-m", "githound.mcp_server"],
            env={"PYTHONPATH": "/path/to/githound"},
            description="Test server",
        )
        assert config.command == "python"  # [attr-defined]
        assert config.args == ["-m", "githound.mcp_server"]  # [attr-defined]
        # [attr-defined]
        assert config.env == {"PYTHONPATH": "/path/to/githound"}
        assert config.description == "Test server"  # [attr-defined]

        # Empty command should fail
        with pytest.raises(ValueError, match="Command cannot be empty"):
            MCPServerConfig(command="")

        # Whitespace-only command should fail
        with pytest.raises(ValueError, match="Command cannot be empty"):
            MCPServerConfig(command="   ")

    def test_mcp_json_config_validation(self) -> None:
        """Test MCPJsonConfig validation."""
        # Valid configuration
        server_config = MCPServerConfig(command="python")
        config = MCPJsonConfig(mcpServers={"test": server_config})
        assert "test" in config.mcpServers  # [attr-defined]

        # Empty servers should fail
        # [attr-defined]
        with pytest.raises(ValueError, match="At least one MCP server must be configured"):
            MCPJsonConfig(mcpServers={})

    def test_get_githound_server(self) -> None:
        """Test finding GitHound server in MCP.json config."""  # [attr-defined]
        # Test exact match
        server_config = MCPServerConfig(command="python")
        config = MCPJsonConfig(mcpServers={"githound": server_config})
        result = config.get_githound_server()  # [attr-defined]
        assert result is not None
        assert result[0] == "githound"

        # Test case insensitive match
        config = MCPJsonConfig(mcpServers={"GitHound": server_config})
        result = config.get_githound_server()  # [attr-defined]
        assert result is not None
        assert result[0] == "GitHound"

        # Test partial match
        config = MCPJsonConfig(mcpServers={"my-githound-server": server_config})
        result = config.get_githound_server()  # [attr-defined]
        assert result is not None
        assert result[0] == "my-githound-server"

        # Test module detection
        server_config_with_module = MCPServerConfig(
            command="python", args=["-m", "githound.mcp_server"]
        )
        config = MCPJsonConfig(mcpServers={"custom-server": server_config_with_module})
        result = config.get_githound_server()  # [attr-defined]
        assert result is not None
        assert result[0] == "custom-server"

        # Test no match
        config = MCPJsonConfig(mcpServers={"other-server": server_config})
        result = config.get_githound_server()  # [attr-defined]
        assert result is None


class TestMCPJsonConfigLoading:
    """Test MCP.json configuration file loading."""  # [attr-defined]

    def test_load_mcp_json_config_valid(self) -> None:
        """Test loading valid MCP.json configuration."""  # [attr-defined]
        config_data = {
            "mcpServers": {
                "githound": {
                    "command": "python",
                    "args": ["-m", "githound.mcp_server"],
                    "env": {"PYTHONPATH": "/path/to/githound"},
                    "description": "GitHound MCP Server",
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)  # [attr-defined]
            config_path = Path(f.name)  # [attr-defined]

        try:
            config = load_mcp_json_config(config_path)
            assert config is not None
            assert "githound" in config.mcpServers  # [attr-defined]
            # [attr-defined]
            assert config.mcpServers["githound"].command == "python"
        finally:
            config_path.unlink()  # [attr-defined]

    def test_load_mcp_json_config_invalid_json(self) -> None:
        """Test loading invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            config_path = Path(f.name)  # [attr-defined]

        try:
            config = load_mcp_json_config(config_path)
            assert config is None
        finally:
            config_path.unlink()  # [attr-defined]

    def test_load_mcp_json_config_invalid_structure(self) -> None:
        """Test loading JSON with invalid structure."""
        config_data = {"mcpServers": {}}  # Empty servers should fail validation

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)  # [attr-defined]
            config_path = Path(f.name)  # [attr-defined]

        try:
            config = load_mcp_json_config(config_path)
            assert config is None
        finally:
            config_path.unlink()  # [attr-defined]

    def test_get_server_config_from_mcp_json(self) -> None:
        """Test extracting ServerConfig from MCP.json."""  # [attr-defined]
        server_config = MCPServerConfig(
            command="python",
            args=["-m", "githound.mcp_server"],
            env={
                "FASTMCP_SERVER_NAME": "Test Server",
                "FASTMCP_SERVER_VERSION": "1.0.0",
                "FASTMCP_SERVER_LOG_LEVEL": "DEBUG",
                "FASTMCP_SERVER_ENABLE_AUTH": "true",
            },
            description="Test GitHound Server",
        )
        mcp_config = MCPJsonConfig(mcpServers={"githound": server_config})

        config = get_server_config_from_mcp_json(mcp_config)
        assert config is not None
        assert config.name == "Test Server"  # [attr-defined]
        assert config.version == "1.0.0"  # [attr-defined]
        assert config.log_level == "DEBUG"  # [attr-defined]
        assert config.enable_auth is True  # [attr-defined]

    def test_get_server_config_from_mcp_json_no_githound(self) -> None:
        """Test extracting ServerConfig when no GitHound server found."""
        server_config = MCPServerConfig(command="other-command")
        mcp_config = MCPJsonConfig(mcpServers={"other-server": server_config})

        config = get_server_config_from_mcp_json(mcp_config)
        assert config is None


class TestMCPJsonIntegration:
    """Test MCP.json integration with existing configuration system."""  # [attr-defined]

    @patch("githound.mcp.config.find_mcp_json_files")  # [attr-defined]
    @patch("githound.mcp.config.load_mcp_json_config")  # [attr-defined]
    def test_get_server_config_with_mcp_json(self, mock_load, mock_find) -> None:
        """Test get_server_config with MCP.json configuration."""  # [attr-defined]
        # Mock finding MCP.json file
        mock_config_path = Path("/mock/mcp.json")  # [attr-defined]
        mock_find.return_value = [mock_config_path]  # [attr-defined]

        # Mock loading MCP.json configuration  # [attr-defined]
        server_config = MCPServerConfig(
            command="python", env={"FASTMCP_SERVER_NAME": "MCP Test Server"}
        )
        mcp_config = MCPJsonConfig(mcpServers={"githound": server_config})
        mock_load.return_value = mcp_config  # [attr-defined]

        config = get_server_config()
        assert config.name == "MCP Test Server"  # [attr-defined]

    @patch("githound.mcp.config.find_mcp_json_files")  # [attr-defined]
    def test_get_server_config_no_mcp_json(self, mock_find) -> None:
        """Test get_server_config falls back to environment variables."""
        # Mock no MCP.json files found
        mock_find.return_value = []

        with patch.dict("os.environ", {"FASTMCP_SERVER_NAME": "Env Test Server"}):
            config = get_server_config()
            assert config.name == "Env Test Server"  # [attr-defined]

    def test_find_mcp_json_files(self) -> None:
        """Test finding MCP.json files in standard locations."""
        # This test would need to create temporary files in various locations
        # For now, just test that the function returns a list
        files = find_mcp_json_files()
        assert isinstance(files, list)
