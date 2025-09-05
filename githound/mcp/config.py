"""Configuration management for GitHound MCP server."""

import logging
from .models import ServerConfig


def configure_logging(log_level: str = "INFO") -> None:
    """Configure logging for the MCP server."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def get_default_config() -> ServerConfig:
    """Get default server configuration."""
    return ServerConfig()
