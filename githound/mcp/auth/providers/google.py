"""Google OAuth provider for GitHound MCP server."""

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, cast

from .oauth_proxy import OAuthProxy, TokenInfo

logger = logging.getLogger(__name__)


class GoogleProvider(OAuthProxy):
    """
    Google OAuth provider using OAuth proxy pattern.

    Google doesn't support Dynamic Client Registration for most use cases,
    so this provider uses the OAuth proxy pattern.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str,
        scopes: list[str] | None = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize Google OAuth provider.

        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            base_url: Base URL for this MCP server
            scopes: Google scopes to request (default: ["openid", "profile", "email"])
        """
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
            token_endpoint="https://oauth2.googleapis.com/token",
            userinfo_endpoint="https://www.googleapis.com/oauth2/v2/userinfo",
            scopes=scopes or ["openid", "profile", "email"],
            **kwargs
        )

    def _load_from_environment(self) -> None:
        """Load Google OAuth configuration from environment variables."""
        prefix = "FASTMCP_SERVER_AUTH_GOOGLE_"

        if not hasattr(self, 'client_id'):
            self.client_id = os.getenv(f"{prefix}CLIENT_ID") or ""
        if not hasattr(self, 'client_secret'):
            self.client_secret = os.getenv(f"{prefix}CLIENT_SECRET") or ""
        if not hasattr(self, 'base_url'):
            self.base_url = os.getenv(
                "FASTMCP_SERVER_BASE_URL", "http://localhost:8000")

        # Validate required configuration
        if not all([self.client_id, self.client_secret]):
            missing: list[Any] = []
            if not self.client_id:
                missing.append(f"{prefix}CLIENT_ID")
            if not self.client_secret:
                missing.append(f"{prefix}CLIENT_SECRET")
            raise ValueError(
                f"Missing required Google OAuth configuration: {', '.join(missing)}")

    async def validate_token(self, token: str) -> TokenInfo | None:
        """
        Validate Google access token and extract user information.

        Args:
            token: Google access token

        Returns:
            TokenInfo if valid, None otherwise
        """
        try:
            # Remove Bearer prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            # Get user information from Google API
            request = urllib.request.Request(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json"
                }
            )

            with urllib.request.urlopen(request) as response:
                user_data = json.loads(response.read().decode("utf-8"))

            # Extract user information
            user_id = user_data.get("id")
            username = user_data.get("email") or user_data.get("name")
            email = user_data.get("email")
            name = user_data.get("name")

            if not user_id:
                logger.warning("Google API response missing user ID")
                return None

            # Use email as username if available, otherwise use name
            if not username:
                username = f"user_{user_id}"

            return TokenInfo(
                user_id=str(user_id),
                username=username,
                email=email,
                roles=["user"],
                permissions=["read"],
                expires_at=None,  # We don't get expiry from userinfo endpoint
                issuer="https://accounts.google.com",
                audience=self.client_id
            )

        except urllib.error.HTTPError as e:
            if e.code == 401:
                logger.warning("Google token is invalid or expired")
            else:
                logger.warning(f"Google API error: {e.code} {e.reason}")
            return None
        except Exception as e:
            logger.error(f"Error validating Google token: {e}")
            return None

    def get_oauth_metadata(self) -> dict[str, Any]:
        """Get OAuth 2.0 metadata for Google integration."""
        metadata = super().get_oauth_metadata()
        metadata.update({
            "scopes_supported": [
                "openid", "profile", "email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/userinfo.email"
            ],
            "provider": "google",
            "provider_name": "Google"
        })
        return metadata


class GoogleWorkspaceProvider(GoogleProvider):
    """
    Google Workspace OAuth provider.

    Extends GoogleProvider with Workspace-specific features and scopes.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str,
        domain: str | None = None,
        scopes: list[str] | None = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize Google Workspace OAuth provider.

        Args:
            client_id: Google Workspace OAuth client ID
            client_secret: Google Workspace OAuth client secret
            base_url: Base URL for this MCP server
            domain: Workspace domain to restrict access to
            scopes: Google Workspace scopes to request
        """
        self.domain = domain

        # Default Workspace scopes
        default_scopes = [
            "openid", "profile", "email",
            "https://www.googleapis.com/auth/admin.directory.user.readonly"
        ]

        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            scopes=scopes or default_scopes,
            **kwargs
        )

    def _load_from_environment(self) -> None:
        """Load Google Workspace OAuth configuration from environment variables."""
        prefix = "FASTMCP_SERVER_AUTH_GOOGLE_WORKSPACE_"

        if not hasattr(self, 'client_id'):
            self.client_id = os.getenv(f"{prefix}CLIENT_ID") or ""
        if not hasattr(self, 'client_secret'):
            self.client_secret = os.getenv(f"{prefix}CLIENT_SECRET") or ""
        if not hasattr(self, 'domain'):
            self.domain = os.getenv(f"{prefix}DOMAIN")
        if not hasattr(self, 'base_url'):
            self.base_url = os.getenv(
                "FASTMCP_SERVER_BASE_URL", "http://localhost:8000")

        # Validate required configuration
        if not all([self.client_id, self.client_secret]):
            missing: list[Any] = []
            if not self.client_id:
                missing.append(f"{prefix}CLIENT_ID")
            if not self.client_secret:
                missing.append(f"{prefix}CLIENT_SECRET")
            raise ValueError(
                f"Missing required Google Workspace OAuth configuration: {', '.join(missing)}")

    async def validate_token(self, token: str) -> TokenInfo | None:
        """
        Validate Google Workspace access token with domain restriction.

        Args:
            token: Google Workspace access token

        Returns:
            TokenInfo if valid, None otherwise
        """
        token_info = await super().validate_token(token)
        if not token_info:
            return None

        # Check domain restriction if configured
        if self.domain and token_info.email:
            email_domain = token_info.email.split("@")[-1]
            if email_domain.lower() != self.domain.lower():
                logger.warning(
                    f"User email domain {email_domain} doesn't match required domain {self.domain}")
                return None

        # Enhanced permissions for Workspace users
        if token_info.email and token_info.email.endswith(f"@{self.domain}"):
            token_info.permissions = ["read", "write"]

            # Check if user is admin (this would require additional API calls in practice)
            # For now, we'll use a simple heuristic
            if "admin" in token_info.email.lower():
                token_info.roles = ["admin"]
                token_info.permissions.append("admin")

        return token_info

    def get_oauth_metadata(self) -> dict[str, Any]:
        """Get OAuth 2.0 metadata for Google Workspace integration."""
        metadata = super().get_oauth_metadata()
        metadata.update({
            "scopes_supported": [
                "openid", "profile", "email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/admin.directory.user.readonly",
                "https://www.googleapis.com/auth/admin.directory.group.readonly"
            ],
            "provider": "google_workspace",
            "provider_name": "Google Workspace",
            "domain": self.domain
        })
        return metadata


class GoogleServiceAccountProvider(GoogleProvider):
    """
    Google Service Account provider for server-to-server authentication.

    This provider validates Google service account tokens (JWT).
    """

    def __init__(
        self,
        service_account_email: str,
        project_id: str,
        **kwargs: Any
    ) -> None:
        """
        Initialize Google Service Account provider.

        Args:
            service_account_email: Service account email
            project_id: Google Cloud project ID
        """
        self.service_account_email = service_account_email
        self.project_id = project_id

        # Service accounts don't use OAuth flow
        super().__init__(
            client_id=service_account_email,
            client_secret="",  # Not used for service accounts
            base_url="",  # Not used for service accounts
            **kwargs
        )

    def _load_from_environment(self) -> None:
        """Load Google Service Account configuration from environment variables."""
        prefix = "FASTMCP_SERVER_AUTH_GOOGLE_SERVICE_ACCOUNT_"

        if not hasattr(self, 'service_account_email'):
            email = os.getenv(f"{prefix}EMAIL")
            if email:
                self.service_account_email = email
        if not hasattr(self, 'project_id'):
            project_id = os.getenv(f"{prefix}PROJECT_ID")
            if project_id:
                self.project_id = project_id

        # Validate required configuration
        if not all([self.service_account_email, self.project_id]):
            missing: list[Any] = []
            if not self.service_account_email:
                missing.append(f"{prefix}EMAIL")
            if not self.project_id:
                missing.append(f"{prefix}PROJECT_ID")
            raise ValueError(
                f"Missing required Google Service Account configuration: {', '.join(missing)}")

    async def validate_token(self, token: str) -> TokenInfo | None:
        """
        Validate Google Service Account JWT token.

        Args:
            token: Service account JWT token

        Returns:
            TokenInfo if valid, None otherwise
        """
        try:
            # This would require JWT validation against Google's public keys
            # For now, we'll implement a basic validation
            import base64

            # Remove Bearer prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            # Basic JWT structure validation
            parts = token.split(".")
            if len(parts) != 3:
                return None

            # Decode header and payload (without verification for now)
            header = json.loads(
                base64.urlsafe_b64decode(parts[0] + "==").decode())
            payload = json.loads(
                base64.urlsafe_b64decode(parts[1] + "==").decode())

            # Validate issuer is our service account
            if payload.get("iss") != self.service_account_email:
                return None

            return TokenInfo(
                user_id=self.service_account_email,
                username=self.service_account_email,
                email=self.service_account_email,
                roles=["service"],
                permissions=["read", "write", "admin"],
                expires_at=payload.get("exp"),
                issuer=payload.get("iss"),
                audience=payload.get("aud")
            )

        except Exception as e:
            logger.error(f"Error validating Google Service Account token: {e}")
            return None

    def supports_dynamic_client_registration(self) -> bool:
        """Service accounts don't support DCR."""
        return False
