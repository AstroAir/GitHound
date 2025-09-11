"""Factory functions for creating authentication and authorization providers."""

import logging
import os
from typing import Any

from .providers import (
    EUNOMIA_AVAILABLE,
    PERMIT_AVAILABLE,
    GitHubProvider,
    GoogleProvider,
    JWTVerifier,
)
from .providers.base import AuthProvider

if EUNOMIA_AVAILABLE:
    from .providers import EunomiaAuthorizationProvider

if PERMIT_AVAILABLE:
    from .providers import PermitAuthorizationProvider

logger = logging.getLogger(__name__)


def create_auth_provider(provider_type: str, **config: Any) -> AuthProvider | None:
    """
    Create an authentication provider by type.

    Args:
        provider_type: Type of provider to create ('jwt', 'github', 'google', etc.)
        **config: Configuration parameters for the provider

    Returns:
        Configured authentication provider or None if creation fails
    """
    try:
        if provider_type.lower() == 'jwt':
            return JWTVerifier(**config)
        elif provider_type.lower() == 'github':
            return GitHubProvider(**config)
        elif provider_type.lower() == 'google':
            return GoogleProvider(**config)
        else:
            logger.error(f"Unknown provider type: {provider_type}")
            return None

    except Exception as e:
        logger.error(f"Failed to create {provider_type} provider: {e}")
        return None


def create_authorization_provider(
    base_provider: AuthProvider,
    auth_type: str,
    **config: Any
) -> AuthProvider:
    """
    Wrap a base authentication provider with authorization capabilities.

    Args:
        base_provider: The base authentication provider to wrap
        auth_type: Type of authorization provider ('eunomia', 'permit')
        **config: Configuration parameters for the authorization provider

    Returns:
        Authorization-wrapped provider or the original provider if wrapping fails
    """
    try:
        if auth_type.lower() == 'eunomia':
            if not EUNOMIA_AVAILABLE:
                logger.warning(
                    "Eunomia authorization requested but eunomia-mcp not available")
                return base_provider
            return EunomiaAuthorizationProvider(base_provider, **config)

        elif auth_type.lower() == 'permit':
            if not PERMIT_AVAILABLE:
                logger.warning(
                    "Permit.io authorization requested but permit-fastmcp not available")
                return base_provider
            return PermitAuthorizationProvider(base_provider, **config)

        else:
            logger.error(f"Unknown authorization type: {auth_type}")
            return base_provider

    except Exception as e:
        logger.error(
            f"Failed to create {auth_type} authorization provider: {e}")
        return base_provider


def create_provider_from_config(config: dict[str, Any]) -> AuthProvider | None:
    """
    Create a complete authentication/authorization provider from configuration.

    Expected configuration format:
    {
        "auth": {
            "type": "jwt|github|google",
            "config": { ... }
        },
        "authorization": {
            "type": "eunomia|permit",
            "config": { ... }
        }
    }

    Args:
        config: Configuration dictionary

    Returns:
        Configured provider or None if creation fails
    """
    try:
        # Create base authentication provider
        auth_config = config.get("auth", {})  # [attr-defined]
        auth_type = auth_config.get("type")  # [attr-defined]
        auth_params = auth_config.get("config", {})  # [attr-defined]

        if not auth_type:
            logger.error("No authentication type specified in configuration")  # [attr-defined]
            return None

        base_provider = create_auth_provider(auth_type, **auth_params)
        if not base_provider:
            return None

        # Optionally wrap with authorization provider
        authorization_config = config.get("authorization")  # [attr-defined]
        if authorization_config:
            auth_type = authorization_config.get("type")  # [attr-defined]
            auth_params = authorization_config.get("config", {})  # [attr-defined]

            if auth_type:
                base_provider = create_authorization_provider(
                    base_provider, auth_type, **auth_params
                )

        return base_provider

    except Exception as e:
        logger.error(f"Failed to create provider from configuration: {e}")  # [attr-defined]
        return None


def create_provider_from_environment() -> AuthProvider | None:
    """
    Create a provider from environment variables.

    Environment variables:
    - GITHOUND_AUTH_TYPE: Type of authentication provider
    - GITHOUND_AUTH_*: Configuration for authentication provider
    - GITHOUND_AUTHORIZATION_TYPE: Type of authorization provider (optional)
    - GITHOUND_AUTHORIZATION_*: Configuration for authorization provider

    Returns:
        Configured provider or None if creation fails
    """
    try:
        # Get authentication provider type
        auth_type = os.getenv("GITHOUND_AUTH_TYPE")
        if not auth_type:
            logger.info(
                "No GITHOUND_AUTH_TYPE specified, authentication disabled")
            return None

        # Collect authentication configuration from environment
        auth_config: dict[str, Any] = {}
        auth_prefix = "GITHOUND_AUTH_"
        for key, value in os.environ.items():
            if key.startswith(auth_prefix) and key != "GITHOUND_AUTH_TYPE":
                config_key = key[len(auth_prefix):].lower()
                auth_config[config_key] = value

        # Create base provider
        base_provider = create_auth_provider(auth_type, **auth_config)
        if not base_provider:
            return None

        # Check for authorization provider
        authorization_type = os.getenv("GITHOUND_AUTHORIZATION_TYPE")
        if authorization_type:
            # Collect authorization configuration from environment
            auth_config: dict[str, Any] = {}
            auth_prefix = "GITHOUND_AUTHORIZATION_"
            for key, value in os.environ.items():
                if key.startswith(auth_prefix) and key != "GITHOUND_AUTHORIZATION_TYPE":
                    config_key = key[len(auth_prefix):].lower()
                    auth_config[config_key] = value

            # Wrap with authorization provider
            base_provider = create_authorization_provider(
                base_provider, authorization_type, **auth_config
            )

        return base_provider

    except Exception as e:
        logger.error(f"Failed to create provider from environment: {e}")
        return None


def get_available_providers() -> dict[str, dict[str, Any]]:
    """
    Get information about available authentication and authorization providers.

    Returns:
        Dictionary with provider information
    """
    providers = {
        "authentication": {
            "jwt": {
                "name": "JWT Verifier",
                "description": "Validates JWT tokens issued by external systems",
                "available": True
            },
            "github": {
                "name": "GitHub OAuth",
                "description": "GitHub OAuth 2.0 authentication",
                "available": True
            },
            "google": {
                "name": "Google OAuth",
                "description": "Google OAuth 2.0 authentication",
                "available": True
            }
        },
        "authorization": {
            "eunomia": {
                "name": "Eunomia Authorization",
                "description": "Policy-based authorization with embedded server",
                "available": EUNOMIA_AVAILABLE,
                "package": "eunomia-mcp"
            },
            "permit": {
                "name": "Permit.io Authorization",
                "description": "Fine-grained authorization with RBAC, ABAC, and REBAC",
                "available": PERMIT_AVAILABLE,
                "package": "permit-fastmcp"
            }
        }
    }

    return providers


def validate_provider_config(config: dict[str, Any]) -> bool:
    """
    Validate a provider configuration.

    Args:
        config: Configuration to validate

    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        # Check required fields
        if "auth" not in config:
            logger.error("Missing 'auth' section in configuration")  # [attr-defined]
            return False

        auth_config = config["auth"]
        if "type" not in auth_config:
            logger.error("Missing 'type' in auth configuration")  # [attr-defined]
            return False

        # Validate authentication type
        auth_type = auth_config["type"].lower()
        if auth_type not in ["jwt", "github", "google"]:
            logger.error(f"Invalid authentication type: {auth_type}")
            return False

        # Validate authorization configuration if present
        if "authorization" in config:
            auth_config = config["authorization"]
            if "type" in auth_config:
                auth_type = auth_config["type"].lower()
                if auth_type not in ["eunomia", "permit"]:
                    logger.error(f"Invalid authorization type: {auth_type}")
                    return False

        return True

    except Exception as e:
        logger.error(f"Error validating provider configuration: {e}")  # [attr-defined]
        return False
