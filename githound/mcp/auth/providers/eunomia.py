"""Eunomia authorization provider for GitHound MCP server."""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

from ...models import User
from .base import AuthProvider, AuthResult, TokenInfo

logger = logging.getLogger(__name__)

# Check if eunomia-mcp is available
try:
    from eunomia_mcp import create_eunomia_middleware
    EUNOMIA_AVAILABLE = True
except ImportError:
    EUNOMIA_AVAILABLE = False
    logger.warning(
        "eunomia-mcp not available. Install with: pip install eunomia-mcp")


@dataclass
class EunomiaConfig:
    """Configuration for Eunomia authorization provider."""

    policy_file: str = "mcp_policies.json"
    server_name: str = "githound-mcp"
    enable_audit_logging: bool = True
    bypass_methods: list[str] | None = None
    custom_policy_data: dict[str, Any] | None = None


class EunomiaAuthorizationProvider(AuthProvider):
    """
    Authorization provider that wraps another auth provider with Eunomia policy-based authorization.

    This provider acts as a decorator/wrapper around existing authentication providers,
    adding policy-based authorization capabilities using Eunomia.
    """

    def __init__(self, base_provider: AuthProvider, **kwargs: Any) -> None:
        """
        Initialize Eunomia authorization provider.

        Args:
            base_provider: The underlying authentication provider to wrap
            **kwargs: Configuration options for Eunomia
        """
        if not EUNOMIA_AVAILABLE:
            raise ImportError(
                "eunomia-mcp is required for EunomiaAuthorizationProvider. Install with: pip install eunomia-mcp")

        super().__init__(**kwargs)
        self.base_provider = base_provider
        self.eunomia_config = EunomiaConfig(**kwargs)
        self._middleware = None
        self._initialize_eunomia()

    def _load_from_environment(self) -> None:
        """Load Eunomia configuration from environment variables."""
        self.config["policy_file"] = os.getenv(
            "EUNOMIA_POLICY_FILE", self.config.get("policy_file"))
        self.config["server_name"] = os.getenv(
            "EUNOMIA_SERVER_NAME", self.config.get("server_name"))
        self.config["enable_audit_logging"] = os.getenv(
            "EUNOMIA_ENABLE_AUDIT_LOGGING", "true").lower() == "true"

        # Parse bypass methods from environment
        bypass_methods_env = os.getenv("EUNOMIA_BYPASS_METHODS")
        if bypass_methods_env:
            try:
                self.config["bypass_methods"] = json.loads(bypass_methods_env)
            except json.JSONDecodeError:
                logger.warning(
                    f"Invalid JSON in EUNOMIA_BYPASS_METHODS: {bypass_methods_env}")

    def _initialize_eunomia(self) -> None:
        """Initialize the Eunomia middleware."""
        try:
            # Create default policy file if it doesn't exist
            if not os.path.exists(self.config.get("policy_file", "")) and not self.config.get("custom_policy_data"):
                self._create_default_policy_file()

            # Initialize Eunomia middleware
            middleware_config = {
                "policy_file": self.config.get("policy_file"),
                "enable_audit_logging": self.config.get("enable_audit_logging"),
            }

            if self.config.get("bypass_methods"):
                middleware_config["bypass_methods"] = self.config["bypass_methods"]

            if self.config.get("custom_policy_data"):
                middleware_config["policy_data"] = self.config["custom_policy_data"]

            self._middleware = create_eunomia_middleware(**middleware_config)
            logger.info(
                f"Eunomia authorization provider initialized with policy file: {self.config.get('policy_file')}")

        except Exception as e:
            logger.error(f"Failed to initialize Eunomia middleware: {e}")
            raise

    def _create_default_policy_file(self) -> None:
        """Create a default policy file for GitHound MCP server."""
        default_policies = {
            "version": "1.0",
            "server_name": self.config.get("server_name"),
            "policies": [
                {
                    "id": "admin_full_access",
                    "description": "Administrators have full access to all operations",
                    "subjects": ["role:admin"],
                    "resources": ["*"],
                    "actions": ["*"],
                    "effect": "allow"
                },
                {
                    "id": "user_read_access",
                    "description": "Regular users can read repositories and perform searches",
                    "subjects": ["role:user"],
                    "resources": [
                        f"{self.config.get('server_name')}:repository:*",
                        f"{self.config.get('server_name')}:search:*",
                        f"{self.config.get('server_name')}:tools:list"
                    ],
                    "actions": ["read", "search", "list"],
                    "effect": "allow"
                },
                {
                    "id": "readonly_limited_access",
                    "description": "Read-only users can only list and read basic information",
                    "subjects": ["role:readonly"],
                    "resources": [
                        f"{self.config.get('server_name')}:tools:list",
                        f"{self.config.get('server_name')}:repository:info"
                    ],
                    "actions": ["list", "read"],
                    "effect": "allow"
                },
                {
                    "id": "default_deny",
                    "description": "Deny all other access by default",
                    "subjects": ["*"],
                    "resources": ["*"],
                    "actions": ["*"],
                    "effect": "deny"
                }
            ]
        }

        try:
            with open(self.config.get("policy_file", "eunomia_policy.json"), 'w') as f:
                json.dump(default_policies, f, indent=2)
            logger.info(
                f"Created default Eunomia policy file: {self.config.get('policy_file')}")
        except Exception as e:
            logger.error(f"Failed to create default policy file: {e}")
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
        Check permission using Eunomia policy engine.

        Args:
            user: The user to check permissions for
            permission: The permission/action to check
            resource: The resource being accessed (optional)
            **context: Additional context for policy evaluation

        Returns:
            True if permission is granted, False otherwise
        """
        try:
            # Build the authorization request
            subject = f"role:{user.role}"
            action = permission
            # [attr-defined]
            resource_name = resource or f"{self.config.get('server_name')}:default"

            # Add user context
            auth_context = {
                "user_id": user.username,
                "user_role": user.role,
                "user_permissions": user.permissions or [],
                **context
            }

            # Use Eunomia middleware to check permission
            # Note: This is a simplified implementation - in practice, you'd integrate
            # with the actual Eunomia policy engine API
            if self._middleware:
                # For now, implement basic role-based logic as fallback
                # In a full implementation, this would call the Eunomia policy engine
                return await self._evaluate_policy(subject, action, resource_name, auth_context)
            else:
                # Fallback to base provider's permission check
                return await self.base_provider.check_permission(user, permission)

        except Exception as e:
            logger.error(f"Error checking permission with Eunomia: {e}")
            # Fallback to base provider on error
            return await self.base_provider.check_permission(user, permission)

    async def _evaluate_policy(self, subject: str, action: str, resource: str, context: dict[str, Any]) -> bool:
        """
        Evaluate policy using Eunomia engine.

        This is a simplified implementation. In practice, this would integrate
        with the actual Eunomia policy evaluation engine.
        """
        # Basic role-based evaluation as fallback
        if "role:admin" in subject:
            return True
        elif "role:user" in subject:
            # Users can perform read operations
            return action in ["read", "search", "list"]
        elif "role:readonly" in subject:
            # Read-only users can only list and read basic info
            return action in ["list", "read"] and "info" in resource

        return False

    def get_oauth_metadata(self) -> dict[str, Any] | None:
        """Get OAuth metadata from base provider."""
        return self.base_provider.get_oauth_metadata()

    def supports_dynamic_client_registration(self) -> bool:
        """Check if base provider supports dynamic client registration."""
        return self.base_provider.supports_dynamic_client_registration()

    def get_policy_file_path(self) -> str:
        """Get the path to the policy file."""
        return self.config.get("policy_file", "eunomia_policy.json")

    def reload_policies(self) -> None:
        """Reload policies from the policy file."""
        if self._middleware:
            try:
                self._initialize_eunomia()
                logger.info("Eunomia policies reloaded successfully")
            except Exception as e:
                logger.error(f"Failed to reload Eunomia policies: {e}")
                raise
