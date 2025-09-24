"""Base authentication provider for GitHound MCP server."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ...models import User


@dataclass
class AuthResult:
    """Result of authentication attempt."""

    success: bool
    user: User | None = None
    error: str | None = None
    token: str | None = None
    expires_in: int | None = None


@dataclass
class TokenInfo:
    """Information extracted from a token."""

    user_id: str
    username: str
    email: str | None = None
    roles: list[str] | None = None
    permissions: list[str] | None = None
    expires_at: int | None = None
    issuer: str | None = None
    audience: str | None = None


class AuthProvider(ABC):
    """Base class for all authentication providers."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the authentication provider."""
        self.config = kwargs
        self._load_from_environment()

    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        # Override in subclasses to load specific environment variables
        pass

    @abstractmethod
    async def authenticate(self, token: str) -> AuthResult:
        """
        Authenticate a user with the provided token.

        Args:
            token: The authentication token

        Returns:
            AuthResult with authentication status and user info
        """
        pass

    @abstractmethod
    async def validate_token(self, token: str) -> TokenInfo | None:
        """
        Validate a token and extract user information.

        Args:
            token: The token to validate

        Returns:
            TokenInfo if valid, None otherwise
        """
        pass

    async def get_user_permissions(self, user: User) -> list[str]:
        """
        Get permissions for a user.

        Args:
            user: The user to get permissions for

        Returns:
            List of permission strings
        """
        return user.permissions or []

    async def check_permission(self, user: User, permission: str) -> bool:
        """
        Check if a user has a specific permission.

        Args:
            user: The user to check
            permission: The permission to check for

        Returns:
            True if user has permission, False otherwise
        """
        permissions = await self.get_user_permissions(user)
        return permission in permissions or "admin" in user.role

    def get_oauth_metadata(self) -> dict[str, Any] | None:
        """
        Get OAuth 2.0 metadata for this provider.

        Returns:
            OAuth metadata dict or None if not applicable
        """
        return None

    def supports_dynamic_client_registration(self) -> bool:
        """
        Check if this provider supports Dynamic Client Registration (DCR).

        Returns:
            True if DCR is supported, False otherwise
        """
        return False


class TokenVerifier(AuthProvider):
    """Base class for token-only verification providers."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.issuer = kwargs.get("issuer")
        self.audience = kwargs.get("audience")

    async def authenticate(self, token: str) -> AuthResult:
        """Authenticate by validating the token."""
        token_info = await self.validate_token(token)
        if not token_info:
            return AuthResult(success=False, error="Invalid token")

        user = User(
            username=token_info.username,
            role=token_info.roles[0] if token_info.roles else "user",
            permissions=token_info.permissions or [],
        )

        return AuthResult(success=True, user=user, token=token, expires_in=token_info.expires_at)


class RemoteAuthProvider(TokenVerifier):
    """Base class for providers that work with external identity providers."""

    def __init__(self, base_url: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.base_url = base_url.rstrip("/")

    def get_oauth_metadata(self) -> dict[str, Any]:
        """Get OAuth 2.0 metadata for MCP clients."""
        return {
            "authorization_endpoint": f"{self.base_url}/oauth/authorize",
            "token_endpoint": f"{self.base_url}/oauth/token",
            "userinfo_endpoint": f"{self.base_url}/oauth/userinfo",
            "jwks_uri": f"{self.base_url}/.well-known/jwks.json",
            "issuer": self.issuer or self.base_url,
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "scopes_supported": ["openid", "profile", "email"],
            "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
            "dynamic_client_registration_endpoint": f"{self.base_url}/oauth/register",
        }

    def supports_dynamic_client_registration(self) -> bool:
        """Remote auth providers support DCR."""
        return True
