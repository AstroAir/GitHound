"""Permit.io authorization provider for GitHound MCP server."""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

from ...models import User
from .base import AuthProvider, AuthResult, TokenInfo

logger = logging.getLogger(__name__)

# Check if permit-fastmcp is available
try:
    from permit_fastmcp.middleware.middleware import PermitMcpMiddleware
    PERMIT_AVAILABLE = True
except ImportError:
    PERMIT_AVAILABLE = False
    logger.warning(
        "permit-fastmcp not available. Install with: pip install permit-fastmcp")


@dataclass
class PermitConfig:
    """Configuration for Permit.io authorization provider."""  # [attr-defined]

    permit_pdp_url: str = "http://localhost:7766"
    permit_api_key: str | None = None
    server_name: str = "githound-mcp"
    enable_audit_logging: bool = True
    identity_mode: str = "fixed"  # fixed, header, jwt, source
    identity_jwt_secret: str | None = None
    bypass_methods: list[str] | None = None
    known_methods: list[str] | None = None


class PermitAuthorizationProvider(AuthProvider):
    """
    Authorization provider that wraps another auth provider with Permit.io fine-grained authorization.

    This provider acts as a decorator/wrapper around existing authentication providers,
    adding fine-grained authorization capabilities using Permit.io.
    """

    def __init__(self, base_provider: AuthProvider, **kwargs: Any) -> None:
        """
        Initialize Permit.io authorization provider.

        Args:
            base_provider: The underlying authentication provider to wrap
            **kwargs: Configuration options for Permit.io  # [attr-defined]
        """
        if not PERMIT_AVAILABLE:
            raise ImportError(
                "permit-fastmcp is required for PermitAuthorizationProvider. Install with: pip install permit-fastmcp")

        super().__init__(**kwargs)
        self.base_provider = base_provider
        self.permit_config = PermitConfig(**kwargs)  # [attr-defined]
        self._middleware = None
        self._initialize_permit()

    def _load_from_environment(self) -> None:
        """Load Permit.io configuration from environment variables."""
        self.config["permit_pdp_url"] = os.getenv(
            "PERMIT_MCP_PERMIT_PDP_URL", self.config.get("permit_pdp_url"))
        self.config["permit_api_key"] = os.getenv(
            "PERMIT_MCP_PERMIT_API_KEY", self.config.get("permit_api_key"))
        self.config["server_name"] = os.getenv(
            "PERMIT_MCP_SERVER_NAME", self.config.get("server_name"))
        self.config["enable_audit_logging"] = os.getenv(
            "PERMIT_MCP_ENABLE_AUDIT_LOGGING", "true").lower() == "true"
        self.config["identity_mode"] = os.getenv(
            "PERMIT_MCP_IDENTITY_MODE", self.config.get("identity_mode"))
        self.config["identity_jwt_secret"] = os.getenv(
            "PERMIT_MCP_IDENTITY_JWT_SECRET", self.config.get("identity_jwt_secret"))

        # Parse JSON arrays from environment
        bypass_methods_env = os.getenv("PERMIT_MCP_BYPASSED_METHODS")
        if bypass_methods_env:
            try:
                self.config["bypass_methods"] = json.loads(bypass_methods_env)
            except json.JSONDecodeError:
                logger.warning(
                    f"Invalid JSON in PERMIT_MCP_BYPASSED_METHODS: {bypass_methods_env}")

        known_methods_env = os.getenv("PERMIT_MCP_KNOWN_METHODS")
        if known_methods_env:
            try:
                self.config["known_methods"] = json.loads(known_methods_env)
            except json.JSONDecodeError:
                logger.warning(
                    f"Invalid JSON in PERMIT_MCP_KNOWN_METHODS: {known_methods_env}")

    def _initialize_permit(self) -> None:
        """Initialize the Permit.io middleware."""
        try:
            if not self.config.get("permit_api_key"):
                raise ValueError(
                    "Permit.io API key is required. Set PERMIT_MCP_PERMIT_API_KEY environment variable.")

            # Initialize Permit.io middleware
            middleware_config = {
                "permit_pdp_url": self.config.get("permit_pdp_url"),
                "permit_api_key": self.config.get("permit_api_key"),
                "enable_audit_logging": self.config.get("enable_audit_logging"),
            }

            if self.config.get("bypass_methods"):
                middleware_config["bypass_methods"] = self.config["bypass_methods"]

            if self.config.get("known_methods"):
                middleware_config["known_methods"] = self.config["known_methods"]

            # Set up identity extraction based on mode
            if self.config.get("identity_mode") == "jwt" and self.config.get("identity_jwt_secret"):
                os.environ["PERMIT_MCP_IDENTITY_MODE"] = "jwt"
                os.environ["PERMIT_MCP_IDENTITY_JWT_SECRET"] = self.config["identity_jwt_secret"]
            elif self.config.get("identity_mode") in ["header", "source", "fixed"]:
                os.environ["PERMIT_MCP_IDENTITY_MODE"] = self.config["identity_mode"]

            self._middleware = PermitMcpMiddleware(
                **middleware_config)  # [attr-defined]
            logger.info(
                # [attr-defined]
                f"Permit.io authorization provider initialized with PDP URL: {self.config.get('permit_pdp_url')}")

        except Exception as e:
            logger.error(f"Failed to initialize Permit.io middleware: {e}")
            raise

    async def authenticate(self, token: str) -> AuthResult:
        """
        Authenticate using the base provider.

        Args:
            token: The authentication token

        Returns:
            AuthResult from the base provider
        """
        return await self.base_provider.authenticate(token)

    async def validate_token(self, token: str) -> TokenInfo | None:
        """
        Validate token using the base provider.

        Args:
            token: The token to validate

        Returns:
            TokenInfo from the base provider
        """
        return await self.base_provider.validate_token(token)

    async def check_permission(self, user: User, permission: str, resource: str | None = None, **context: Any) -> bool:
        """
        Check permission using Permit.io policy engine.

        Args:
            user: The user to check permissions for
            permission: The permission/action to check
            resource: The resource being accessed (optional)
            **context: Additional context for policy evaluation (e.g., tool arguments)

        Returns:
            True if permission is granted, False otherwise
        """
        try:
            # Build the authorization request for Permit.io
            subject = user.username
            action = permission
            # [attr-defined]
            resource_name = resource or f"{self.config.get('server_name')}"

            # Add user context and tool arguments for ABAC policies
            auth_context = {
                "user_id": user.username,
                "user_role": user.role,
                "user_permissions": user.permissions or [],
                **context  # This includes tool arguments for ABAC evaluation
            }

            # Use Permit.io middleware to check permission
            if self._middleware:
                # This would integrate with the actual Permit.io policy engine
                # For now, implement a simplified version
                return await self._evaluate_permit_policy(subject, action, resource_name, auth_context)
            else:
                # Fallback to base provider's permission check
                return await self.base_provider.check_permission(user, permission)

        except Exception as e:
            logger.error(f"Error checking permission with Permit.io: {e}")
            # Fallback to base provider on error
            return await self.base_provider.check_permission(user, permission)

    async def _evaluate_permit_policy(self, subject: str, action: str, resource: str, context: dict[str, Any]) -> bool:
        """
        Evaluate policy using Permit.io engine.

        This is a simplified implementation. In practice, this would integrate
        with the actual Permit.io policy evaluation engine through the middleware.
        """
        try:
            # In a real implementation, this would call the Permit.io PDP
            # through the middleware to evaluate policies

            # For demonstration, implement basic RBAC logic
            user_role = context.get("user_role", "user")

            # Admin role has full access
            if user_role == "admin":
                return True

            # User role has read access to most resources
            if user_role == "user":
                if action in ["read", "search", "list"]:
                    return True
                # Check for specific tool permissions
                if action in context.get("user_permissions", []):
                    return True

            # Read-only role has very limited access
            if user_role == "readonly":
                if action in ["list", "read"] and "info" in resource:
                    return True

            # ABAC example: Check tool arguments for conditional access
            # This demonstrates how tool arguments can be used in policies
            if "arg_number" in context:
                number_value = context.get("arg_number", 0)
                if isinstance(number_value, (int, float)) and number_value > 10:
                    # Allow access to conditional tools when number > 10
                    if action == "conditional-greet":
                        return True

            return False

        except Exception as e:
            logger.error(f"Error evaluating Permit.io policy: {e}")
            return False

    def get_oauth_metadata(self) -> dict[str, Any] | None:
        """Get OAuth metadata from base provider."""
        return self.base_provider.get_oauth_metadata()

    def supports_dynamic_client_registration(self) -> bool:
        """Check if base provider supports dynamic client registration."""
        return self.base_provider.supports_dynamic_client_registration()

    def get_permit_config(self) -> dict[str, Any]:
        """Get the current Permit.io configuration."""
        return self.config

    def update_permit_config(self, **kwargs: Any) -> None:
        """Update Permit.io configuration and reinitialize."""  # [attr-defined]
        for key, value in kwargs.items():
            if hasattr(self.config, key):  # [attr-defined]
                setattr(self.config, key, value)  # [attr-defined]

        # Reinitialize with new configuration
        self._initialize_permit()
        # [attr-defined]
        logger.info("Permit.io configuration updated and reinitialized")

    async def check_tool_permission(self, user: User, tool_name: str, tool_args: dict[str, Any]) -> bool:
        """
        Check permission for a specific tool with its arguments.

        This method demonstrates ABAC (Attribute-Based Access Control) where
        tool arguments are used as attributes in policy evaluation.

        Args:
            user: The user requesting access
            tool_name: The name of the tool being called
            tool_args: The arguments passed to the tool

        Returns:
            True if access is granted, False otherwise
        """
        # Flatten tool arguments as individual attributes for policy evaluation
        flattened_args: dict[str, Any] = {}
        for key, value in tool_args.items():
            flattened_args[f"arg_{key}"] = value

        return await self.check_permission(
            user=user,
            permission=tool_name,
            resource=f"{self.config.get('server_name')}",
            **flattened_args
        )
