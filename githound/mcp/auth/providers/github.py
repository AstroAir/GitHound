"""GitHub OAuth provider for GitHound MCP server."""

import os
import json
import logging
from typing import Optional, List, Any, Dict

from .oauth_proxy import OAuthProxy, TokenInfo

logger = logging.getLogger(__name__)


class GitHubProvider(OAuthProxy):
    """
    GitHub OAuth provider using OAuth proxy pattern.

    GitHub doesn't support Dynamic Client Registration, so this provider
    uses the OAuth proxy pattern to bridge the gap.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str,
        scopes: Optional[List[str]] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize GitHub OAuth provider.

        Args:
            client_id: GitHub OAuth App client ID
            client_secret: GitHub OAuth App client secret
            base_url: Base URL for this MCP server
            scopes: GitHub scopes to request (default: ["user:email"])
        """
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            authorization_endpoint="https://github.com/login/oauth/authorize",
            token_endpoint="https://github.com/login/oauth/access_token",
            userinfo_endpoint="https://api.github.com/user",
            scopes=scopes or ["user:email"],
            **kwargs
        )

    def _load_from_environment(self) -> None:
        """Load GitHub OAuth configuration from environment variables."""
        prefix = "FASTMCP_SERVER_AUTH_GITHUB_"

        if not hasattr(self, 'client_id'):
            self.client_id = os.getenv(f"{prefix}CLIENT_ID") or ""
        if not hasattr(self, 'client_secret'):
            self.client_secret = os.getenv(f"{prefix}CLIENT_SECRET") or ""
        if not hasattr(self, 'base_url'):
            self.base_url = os.getenv(
                "FASTMCP_SERVER_BASE_URL", "http://localhost:8000")

        # Validate required configuration
        if not all([self.client_id, self.client_secret]):
            missing = []
            if not self.client_id:
                missing.append(f"{prefix}CLIENT_ID")
            if not self.client_secret:
                missing.append(f"{prefix}CLIENT_SECRET")
            raise ValueError(
                f"Missing required GitHub OAuth configuration: {', '.join(missing)}")

    async def validate_token(self, token: str) -> Optional[TokenInfo]:
        """
        Validate GitHub access token and extract user information.

        Args:
            token: GitHub access token

        Returns:
            TokenInfo if valid, None otherwise
        """
        try:
            # Remove Bearer prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            # Get user information from GitHub API
            import urllib.request
            import urllib.error

            request = urllib.request.Request(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "GitHound-MCP-Server"
                }
            )

            with urllib.request.urlopen(request) as response:
                user_data = json.loads(response.read().decode())

            # Get user email (might be private)
            email = user_data.get("email")
            if not email:
                try:
                    email_request = urllib.request.Request(
                        "https://api.github.com/user/emails",
                        headers={
                            "Authorization": f"token {token}",
                            "Accept": "application/vnd.github.v3+json",
                            "User-Agent": "GitHound-MCP-Server"
                        }
                    )

                    with urllib.request.urlopen(email_request) as email_response:
                        emails = json.loads(email_response.read().decode())
                        # Find primary email
                        for email_data in emails:
                            if email_data.get("primary"):
                                email = email_data.get("email")
                                break
                except Exception as e:
                    logger.warning(
                        f"Could not fetch user email from GitHub: {e}")

            # Extract user information
            user_id = str(user_data.get("id"))
            username = user_data.get("login")
            name = user_data.get("name") or username

            if not user_id or not username:
                logger.warning(
                    "GitHub API response missing required user data")
                return None

            # Determine permissions based on GitHub user type
            permissions = ["read"]
            if user_data.get("type") == "Organization":
                permissions.append("admin")

            return TokenInfo(
                user_id=user_id,
                username=username,
                email=email,
                roles=["user"],
                permissions=permissions,
                expires_at=None,  # GitHub tokens don't expire
                issuer="https://github.com",
                audience=self.client_id
            )

        except urllib.error.HTTPError as e:
            if e.code == 401:
                logger.warning("GitHub token is invalid or expired")
            else:
                logger.warning(f"GitHub API error: {e.code} {e.reason}")
            return None
        except Exception as e:
            logger.error(f"Error validating GitHub token: {e}")
            return None

    def get_oauth_metadata(self) -> Dict[str, Any]:
        """Get OAuth 2.0 metadata for GitHub integration."""
        metadata = super().get_oauth_metadata()
        metadata.update({
            "scopes_supported": ["user", "user:email", "repo", "public_repo"],
            "provider": "github",
            "provider_name": "GitHub"
        })
        return metadata


class GitHubEnterpriseProvider(GitHubProvider):
    """
    GitHub Enterprise OAuth provider.

    Extends GitHubProvider to work with GitHub Enterprise Server instances.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str,
        github_base_url: str,
        scopes: Optional[List[str]] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize GitHub Enterprise OAuth provider.

        Args:
            client_id: GitHub Enterprise OAuth App client ID
            client_secret: GitHub Enterprise OAuth App client secret
            base_url: Base URL for this MCP server
            github_base_url: Base URL for GitHub Enterprise instance
            scopes: GitHub scopes to request
        """
        self.github_base_url = github_base_url.rstrip("/")

        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            scopes=scopes,
            **kwargs
        )

        # Override endpoints for GitHub Enterprise
        self.authorization_endpoint = f"{self.github_base_url}/login/oauth/authorize"
        self.token_endpoint = f"{self.github_base_url}/login/oauth/access_token"
        self.userinfo_endpoint = f"{self.github_base_url}/api/v3/user"

    def _load_from_environment(self) -> None:
        """Load GitHub Enterprise OAuth configuration from environment variables."""
        prefix = "FASTMCP_SERVER_AUTH_GITHUB_ENTERPRISE_"

        if not hasattr(self, 'client_id'):
            self.client_id = os.getenv(f"{prefix}CLIENT_ID") or ""
        if not hasattr(self, 'client_secret'):
            self.client_secret = os.getenv(f"{prefix}CLIENT_SECRET") or ""
        if not hasattr(self, 'github_base_url'):
            self.github_base_url = os.getenv(f"{prefix}BASE_URL") or ""
        if not hasattr(self, 'base_url'):
            self.base_url = os.getenv(
                "FASTMCP_SERVER_BASE_URL", "http://localhost:8000")

        # Validate required configuration
        if not all([self.client_id, self.client_secret, self.github_base_url]):
            missing = []
            if not self.client_id:
                missing.append(f"{prefix}CLIENT_ID")
            if not self.client_secret:
                missing.append(f"{prefix}CLIENT_SECRET")
            if not self.github_base_url:
                missing.append(f"{prefix}BASE_URL")
            raise ValueError(
                f"Missing required GitHub Enterprise OAuth configuration: {', '.join(missing)}")

    async def validate_token(self, token: str) -> Optional[TokenInfo]:
        """
        Validate GitHub Enterprise access token.

        Args:
            token: GitHub Enterprise access token

        Returns:
            TokenInfo if valid, None otherwise
        """
        try:
            # Remove Bearer prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            # Get user information from GitHub Enterprise API
            import urllib.request
            import urllib.error

            request = urllib.request.Request(
                f"{self.github_base_url}/api/v3/user",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "GitHound-MCP-Server"
                }
            )

            with urllib.request.urlopen(request) as response:
                user_data = json.loads(response.read().decode())

            # Extract user information (same as GitHub.com)
            user_id = str(user_data.get("id"))
            username = user_data.get("login")
            email = user_data.get("email")

            if not user_id or not username:
                logger.warning(
                    "GitHub Enterprise API response missing required user data")
                return None

            return TokenInfo(
                user_id=user_id,
                username=username,
                email=email,
                roles=["user"],
                permissions=["read"],
                expires_at=None,
                issuer=self.github_base_url,
                audience=self.client_id
            )

        except urllib.error.HTTPError as e:
            if e.code == 401:
                logger.warning("GitHub Enterprise token is invalid or expired")
            else:
                logger.warning(
                    f"GitHub Enterprise API error: {e.code} {e.reason}")
            return None
        except Exception as e:
            logger.error(f"Error validating GitHub Enterprise token: {e}")
            return None
