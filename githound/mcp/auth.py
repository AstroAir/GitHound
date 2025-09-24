"""Authentication and authorization functionality for GitHound MCP server."""

import logging
import os
from importlib import import_module
from typing import Any, Dict, List, Optional, Protocol

from .models import User

# Define the protocol first to avoid import issues


class AuthProvider(Protocol):
    """Protocol defining the interface for authentication providers."""

    async def authenticate(self, token: str) -> Any: ...
    async def validate_token(self, token: str) -> Any: ...
    async def check_permission(self, user: Any, permission: str) -> bool: ...
    def get_oauth_metadata(self) -> Optional[Dict[str, Any]]: ...
    def supports_dynamic_client_registration(self) -> bool: ...


# Try to import concrete implementations, fall back to Any types
try:
    from .auth.providers.base import AuthResult, TokenInfo
except ImportError:
    # Fallback for when auth module structure is not yet complete
    AuthResult = Any
    TokenInfo = Any

logger = logging.getLogger(__name__)

# Global authentication provider instance
_auth_provider: Optional[AuthProvider] = None


def get_auth_provider() -> Optional[AuthProvider]:
    """Get the current authentication provider."""
    global _auth_provider

    if _auth_provider is None:
        _auth_provider = _create_auth_provider_from_environment()

    return _auth_provider


def set_auth_provider(provider: AuthProvider) -> None:
    """Set the authentication provider."""
    global _auth_provider
    _auth_provider = provider


def _create_auth_provider_from_environment() -> Optional[AuthProvider]:
    """Create authentication provider from environment configuration."""
    provider_class_path = os.getenv("FASTMCP_SERVER_AUTH")
    if not provider_class_path:
        return None

    try:
        # Parse module and class name
        module_path, class_name = provider_class_path.rsplit(".", 1)

        # Import the module and get the class
        module = import_module(module_path)
        provider_class: Type[AuthProvider] = getattr(module, class_name)

        # Create provider instance (it will load config from environment)
        provider: AuthProvider = provider_class()

        # Check if authorization wrapper is requested
        provider = _wrap_with_authorization_provider(provider)

        logger.info(f"Created authentication provider: {provider_class_path}")
        return provider

    except Exception as e:
        logger.error(f"Failed to create authentication provider from {provider_class_path}: {e}")
        return None


def _wrap_with_authorization_provider(base_provider: AuthProvider) -> AuthProvider:
    """
    Wrap the base authentication provider with optional authorization providers.

    Args:
        base_provider: The base authentication provider

    Returns:
        The provider, optionally wrapped with authorization capabilities
    """
    provider = base_provider

    # Check for Eunomia authorization
    if os.getenv("EUNOMIA_ENABLE", "false").lower() == "true":
        try:
            from .providers.eunomia import EunomiaAuthorizationProvider

            provider = EunomiaAuthorizationProvider(provider)
            logger.info("Wrapped provider with Eunomia authorization")
        except ImportError:
            logger.warning("Eunomia authorization requested but eunomia-mcp not available")

    # Check for Permit.io authorization
    if os.getenv("PERMIT_ENABLE", "false").lower() == "true":
        try:
            from .providers.permit import PermitAuthorizationProvider

            provider = PermitAuthorizationProvider(provider)
            logger.info("Wrapped provider with Permit.io authorization")
        except ImportError:
            logger.warning("Permit.io authorization requested but permit-fastmcp not available")

    return provider


async def authenticate_request(token: str) -> Optional[User]:
    """
    Authenticate a request with the provided token.

    Args:
        token: Authentication token from request

    Returns:
        User if authenticated, None otherwise
    """
    provider = get_auth_provider()
    if not provider:
        return None

    try:
        result = await provider.authenticate(token)
        return result.user if result.success else None
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None


async def validate_token(token: str) -> Any:
    """
    Validate a token and extract user information.

    Args:
        token: Token to validate

    Returns:
        TokenInfo if valid, None otherwise
    """
    provider = get_auth_provider()
    if not provider:
        return None

    try:
        return await provider.validate_token(token)
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return None


def get_current_user() -> User | None:
    """Get the current authenticated user."""
    # This would be implemented with request context in a real web framework
    # For now, return None as this is primarily used for testing
    return None


def check_rate_limit(user: User | None = None) -> bool:
    """Check if the current user/request is within rate limits."""
    # This is a placeholder implementation for testing
    # In a real implementation, this would check rate limiting rules
    return True


async def check_permission(
    user: User, permission: str, resource: Optional[str] = None, **context: Any
) -> bool:
    """
    Check if a user has a specific permission.

    Args:
        user: User to check
        permission: Permission to check for
        resource: Resource being accessed (optional)
        **context: Additional context for authorization (e.g., tool arguments)

    Returns:
        True if user has permission, False otherwise
    """
    provider = get_auth_provider()
    if not provider:
        # Default behavior: admin role has all permissions
        return user.role == "admin" or permission in (user.permissions or [])

    try:
        # Check if provider supports enhanced permission checking with context
        if (
            hasattr(provider, "check_permission")
            and "resource" in provider.check_permission.__code__.co_varnames
        ):
            return await provider.check_permission(user, permission, resource, **context)
        else:
            # Fallback to basic permission checking
            return await provider.check_permission(user, permission)
    except Exception as e:
        logger.error(f"Permission check error: {e}")
        return False


async def check_tool_permission(user: User, tool_name: str, tool_args: Dict[str, Any]) -> bool:
    """
    Check if a user has permission to execute a specific tool with given arguments.

    This function is specifically designed for authorization providers that support
    Attribute-Based Access Control (ABAC) with tool arguments.

    Args:
        user: User requesting access
        tool_name: Name of the tool being called
        tool_args: Arguments passed to the tool

    Returns:
        True if access is granted, False otherwise
    """
    provider = get_auth_provider()
    if not provider:
        # Default behavior: admin role has all permissions
        return user.role == "admin"

    try:
        # Check if provider supports tool-specific permission checking
        if hasattr(provider, "check_tool_permission"):
            return await provider.check_tool_permission(user, tool_name, tool_args)
        else:
            # Fallback to regular permission check with tool arguments as context
            return await check_permission(user, tool_name, f"tool:{tool_name}", **tool_args)
    except Exception as e:
        logger.error(f"Tool permission check error: {e}")
        return False


def get_oauth_metadata() -> Optional[Dict[str, Any]]:
    """
    Get OAuth 2.0 metadata for the current provider.

    Returns:
        OAuth metadata dict or None if not applicable
    """
    provider = get_auth_provider()
    if not provider:
        return None

    return provider.get_oauth_metadata()


def supports_dynamic_client_registration() -> bool:
    """
    Check if the current provider supports Dynamic Client Registration.

    Returns:
        True if DCR is supported, False otherwise
    """
    provider = get_auth_provider()
    if not provider:
        return False

    return provider.supports_dynamic_client_registration()
