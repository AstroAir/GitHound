"""Configuration management for GitHound MCP server."""

import json
import logging
import os
from pathlib import Path
from typing import Any, cast

from .models import MCPJsonConfig, ServerConfig


def _get_auth_provider() -> Any | None:
    """Get auth provider with lazy import to avoid circular imports."""
    try:
        from .auth.factory import create_auth_provider

        return create_auth_provider("jwt")  # Default to JWT provider
    except Exception:
        return None


def configure_logging(log_level: str = "INFO") -> None:
    """Configure logging for the MCP server."""
    logging.basicConfig(
        level=getattr(logging, (log_level or "INFO").upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def get_default_config() -> ServerConfig:
    """Get default server configuration."""
    return ServerConfig()


def get_server_config_from_environment() -> ServerConfig:
    """Get server configuration from environment variables."""
    config = ServerConfig()

    # Load configuration from environment
    name = os.getenv("FASTMCP_SERVER_NAME")
    if name:
        config.name = name  # [attr-defined]

    version = os.getenv("FASTMCP_SERVER_VERSION")
    if version:
        config.version = version  # [attr-defined]

    transport = os.getenv("FASTMCP_SERVER_TRANSPORT")
    if transport:
        config.transport = transport  # [attr-defined]

    host = os.getenv("FASTMCP_SERVER_HOST")
    if host:
        config.host = host  # [attr-defined]

    port_str = os.getenv("FASTMCP_SERVER_PORT")
    if port_str:
        try:
            config.port = int(port_str)  # [attr-defined]
        except ValueError:
            pass

    log_level = os.getenv("FASTMCP_SERVER_LOG_LEVEL")
    if log_level:
        config.log_level = log_level  # [attr-defined]

    enable_auth = os.getenv("FASTMCP_SERVER_ENABLE_AUTH")
    if enable_auth:
        config.enable_auth = enable_auth.lower() in ("true", "1", "yes")  # [attr-defined]

    rate_limit_enabled = os.getenv("FASTMCP_SERVER_RATE_LIMIT_ENABLED")
    if rate_limit_enabled:
        config.rate_limit_enabled = rate_limit_enabled.lower() in (
            "true",
            "1",
            "yes",
        )  # [attr-defined]

    return config


def is_authentication_enabled() -> bool:
    """Check if authentication is enabled."""
    config = get_server_config_from_environment()
    # [attr-defined]
    return config.enable_auth or _get_auth_provider() is not None


def get_oauth_discovery_metadata() -> dict[str, Any] | None:
    """
    Get OAuth 2.0 discovery metadata for the server.

    Returns:
        OAuth discovery metadata or None if authentication is not configured
    """
    if not is_authentication_enabled():
        return None

    auth_provider = _get_auth_provider()
    if not auth_provider:
        return None

    metadata = auth_provider.get_oauth_metadata()
    if not metadata:
        return None

    # Add server-specific metadata
    config = get_server_config_from_environment()
    metadata.update(
        {
            "server_name": config.name,  # [attr-defined]
            "server_version": config.version,  # [attr-defined]
            "mcp_version": "2024-11-05",
            "supports_dynamic_client_registration": bool(
                getattr(auth_provider, "supports_dynamic_client_registration", False)
            ),
        }
    )

    return cast(dict[str, Any], metadata)


def find_mcp_json_files() -> list[Path]:
    """
    Find MCP.json configuration files in standard locations.  # [attr-defined]

    Returns:
        List of paths to MCP.json files that exist, in order of priority
    """
    possible_locations = [
        # Current working directory
        Path.cwd() / "mcp.json",
        # User home directory
        Path.home() / ".mcp.json",
        # Claude Desktop config location
        Path.home() / ".claude" / "mcp.json",
        # Cursor config location
        Path.home() / ".cursor" / "mcp.json",
        # VS Code workspace config
        Path.cwd() / ".vscode" / "mcp.json",
        # GitHound specific config
        Path.home() / ".githound" / "mcp.json",
    ]

    return [path for path in possible_locations if path.exists()]


def load_mcp_json_config(config_path: Path) -> MCPJsonConfig | None:
    """
    Load and parse an MCP.json configuration file.  # [attr-defined]

    Args:
        config_path: Path to the MCP.json file  # [attr-defined]

    Returns:
        Parsed MCP.json configuration or None if loading fails  # [attr-defined]
    """
    try:
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)

        # Support both pydantic v1 and v2
        config: MCPJsonConfig
        if hasattr(MCPJsonConfig, "model_validate"):
            config = MCPJsonConfig.model_validate(data)
        else:
            config = MCPJsonConfig.parse_obj(data)
        logging.getLogger(__name__).info(
            # [attr-defined]
            f"Loaded MCP.json configuration from: {config_path}"
        )
        return config

    except json.JSONDecodeError as e:
        logging.getLogger(__name__).error(
            # [attr-defined]
            f"Invalid JSON in MCP config file {config_path}: {e}"
        )
        return None
    except Exception as e:
        logging.getLogger(__name__).error(
            # [attr-defined]
            f"Failed to load MCP config file {config_path}: {e}"
        )
        return None


def get_server_config_from_mcp_json(mcp_config: MCPJsonConfig) -> ServerConfig | None:
    """
    Extract GitHound server configuration from MCP.json config.  # [attr-defined]

    Args:
        mcp_config: Parsed MCP.json configuration  # [attr-defined]

    Returns:
        ServerConfig for GitHound server or None if not found
    """
    githound_server = mcp_config.get_githound_server()  # [attr-defined]
    if not githound_server:
        return None

    server_name, server_config = githound_server

    # Create ServerConfig from MCP server config
    config = ServerConfig()

    # Extract configuration from environment variables in the MCP config
    env = server_config.env  # [attr-defined]

    if "FASTMCP_SERVER_NAME" in env:
        config.name = env["FASTMCP_SERVER_NAME"]  # [attr-defined]
    elif server_config.description:  # [attr-defined]
        config.name = server_config.description  # [attr-defined]
    else:
        config.name = server_name  # [attr-defined]

    if "FASTMCP_SERVER_VERSION" in env:
        config.version = env["FASTMCP_SERVER_VERSION"]  # [attr-defined]

    if "FASTMCP_SERVER_TRANSPORT" in env:
        config.transport = env["FASTMCP_SERVER_TRANSPORT"]  # [attr-defined]

    if "FASTMCP_SERVER_HOST" in env:
        config.host = env["FASTMCP_SERVER_HOST"]  # [attr-defined]

    if "FASTMCP_SERVER_PORT" in env:
        try:
            config.port = int(env["FASTMCP_SERVER_PORT"])  # [attr-defined]
        except ValueError:
            pass

    if "FASTMCP_SERVER_LOG_LEVEL" in env:
        config.log_level = env["FASTMCP_SERVER_LOG_LEVEL"]  # [attr-defined]

    if "FASTMCP_SERVER_ENABLE_AUTH" in env:
        config.enable_auth = env["FASTMCP_SERVER_ENABLE_AUTH"].lower() in (
            "true",
            "1",
            "yes",
        )  # [attr-defined]

    if "FASTMCP_SERVER_RATE_LIMIT_ENABLED" in env:
        config.rate_limit_enabled = env["FASTMCP_SERVER_RATE_LIMIT_ENABLED"].lower() in (
            "true",
            "1",
            "yes",
        )  # [attr-defined]

    return config


def get_server_config() -> ServerConfig:
    """
    Get server configuration with priority: MCP.json > Environment Variables > Defaults.  # [attr-defined]

    Returns:
        Complete server configuration
    """
    logger = logging.getLogger(__name__)

    # Start with environment variable configuration
    config = get_server_config_from_environment()

    # Try to find and load MCP.json configuration  # [attr-defined]
    mcp_json_files = find_mcp_json_files()

    for config_path in mcp_json_files:
        # [attr-defined]
        logger.info(f"Found MCP.json configuration file: {config_path}")

        mcp_config = load_mcp_json_config(config_path)
        if mcp_config:
            mcp_server_config = get_server_config_from_mcp_json(mcp_config)
            if mcp_server_config:
                # [attr-defined]
                logger.info(f"Using GitHound configuration from MCP.json: {config_path}")

                # MCP.json configuration takes priority, but preserve environment variables  # [attr-defined]
                # that are not overridden by MCP.json
                env_config = config
                # Support both pydantic v1 and v2
                mcp_config_dict = (
                    mcp_server_config.model_dump()
                    if hasattr(mcp_server_config, "model_dump")
                    else mcp_server_config.dict()
                )
                env_config_dict = (
                    env_config.model_dump()
                    if hasattr(env_config, "model_dump")
                    else env_config.dict()
                )

                # Merge configurations with MCP.json taking priority  # [attr-defined]
                merged_config: dict[str, Any] = {}
                default_server_config = ServerConfig()
                defaults_dict = (
                    default_server_config.model_dump()
                    if hasattr(default_server_config, "model_dump")
                    else default_server_config.dict()
                )
                for key, default_value in defaults_dict.items():
                    if mcp_config_dict[key] != default_value:
                        # MCP.json has non-default value, use it
                        merged_config[key] = mcp_config_dict[key]
                    elif env_config_dict[key] != default_value:
                        # Environment has non-default value, use it
                        merged_config[key] = env_config_dict[key]
                    else:
                        # Both are default, use default
                        merged_config[key] = default_value

                server_config: ServerConfig
                if hasattr(ServerConfig, "model_validate"):
                    server_config = ServerConfig.model_validate(merged_config)
                else:
                    server_config = ServerConfig(**merged_config)
                return server_config

    # [attr-defined]
    logger.info("No MCP.json configuration found, using environment variables and defaults")
    return config
