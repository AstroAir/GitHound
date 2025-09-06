"""Configuration management for GitHound MCP server."""

import os
import logging
from typing import Optional, Dict, Any, cast
from .models import ServerConfig
from .auth import get_auth_provider


def configure_logging(log_level: str = "INFO") -> None:
    """Configure logging for the MCP server."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
        config.name = name

    version = os.getenv("FASTMCP_SERVER_VERSION")
    if version:
        config.version = version

    transport = os.getenv("FASTMCP_SERVER_TRANSPORT")
    if transport:
        config.transport = transport

    host = os.getenv("FASTMCP_SERVER_HOST")
    if host:
        config.host = host

    port_str = os.getenv("FASTMCP_SERVER_PORT")
    if port_str:
        try:
            config.port = int(port_str)
        except ValueError:
            pass

    log_level = os.getenv("FASTMCP_SERVER_LOG_LEVEL")
    if log_level:
        config.log_level = log_level

    enable_auth = os.getenv("FASTMCP_SERVER_ENABLE_AUTH")
    if enable_auth:
        config.enable_auth = enable_auth.lower() in ("true", "1", "yes")

    rate_limit_enabled = os.getenv("FASTMCP_SERVER_RATE_LIMIT_ENABLED")
    if rate_limit_enabled:
        config.rate_limit_enabled = rate_limit_enabled.lower() in ("true", "1", "yes")

    return config


def is_authentication_enabled() -> bool:
    """Check if authentication is enabled."""
    config = get_server_config_from_environment()
    return config.enable_auth or get_auth_provider() is not None


def get_oauth_discovery_metadata() -> Optional[Dict[str, Any]]:
    """
    Get OAuth 2.0 discovery metadata for the server.

    Returns:
        OAuth discovery metadata or None if authentication is not configured
    """
    if not is_authentication_enabled():
        return None

    auth_provider = get_auth_provider()
    if not auth_provider:
        return None

    metadata = auth_provider.get_oauth_metadata()
    if not metadata:
        return None

    # Add server-specific metadata
    config = get_server_config_from_environment()
    metadata.update({
        "server_name": config.name,
        "server_version": config.version,
        "mcp_version": "2024-11-05",
        "supports_dynamic_client_registration": auth_provider.supports_dynamic_client_registration()
    })

    return cast(Dict[str, Any], metadata)
