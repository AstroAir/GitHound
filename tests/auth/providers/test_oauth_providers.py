"""Tests for OAuth authentication providers (GitHub, Google, OAuth Proxy)."""

from unittest.mock import patch

import pytest


class TestGitHubProvider:
    """Test GitHub OAuth provider."""

    def test_github_provider_creation(self) -> None:
        """Test GitHub provider creation and configuration."""
        from githound.mcp.auth.providers.github import GitHubProvider

        provider = GitHubProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
        )

        assert provider.client_id == "test-client-id"
        assert provider.client_secret == "test-client-secret"
        assert provider.base_url == "http://localhost:8000"

    def test_github_oauth_metadata(self) -> None:
        """Test GitHub OAuth metadata generation."""
        from githound.mcp.auth.providers.github import GitHubProvider

        provider = GitHubProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
        )

        metadata = provider.get_oauth_metadata()
        assert metadata is not None
        assert metadata["provider"] == "github"
        assert metadata["client_id"] == "test-client-id"
        assert "authorization_endpoint" in metadata
        assert "token_endpoint" in metadata
        assert "scopes" in metadata

        # Check that URLs are properly constructed
        assert metadata["authorization_endpoint"] == "http://localhost:8000/oauth/authorize"
        assert metadata["token_endpoint"] == "http://localhost:8000/oauth/token"

    def test_github_dcr_support(self) -> None:
        """Test GitHub Dynamic Client Registration support."""
        from githound.mcp.auth.providers.github import GitHubProvider

        provider = GitHubProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
        )

        assert provider.supports_dynamic_client_registration() is True

    @pytest.mark.asyncio
    async def test_github_authentication_success(self) -> None:
        """Test successful GitHub authentication flow."""
        import json
        from unittest.mock import MagicMock

        from githound.mcp.auth.providers.github import GitHubProvider

        provider = GitHubProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
        )

        # Mock successful user info response from GitHub API
        mock_user_response = {
            "login": "testuser",
            "name": "Test User",
            "email": "test@example.com",
            "id": 12345,
            "avatar_url": "https://github.com/images/error/testuser_happy.gif",
        }

        # Mock urllib.request.urlopen for GitHub API call
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(mock_user_response).encode()
            mock_response.status = 200
            mock_urlopen.return_value.__enter__.return_value = mock_response

            # Test authentication with a token
            result = await provider.authenticate("gho_test_token")

            assert result.success is True
            assert result.user.username == "testuser"
            assert result.user.role == "user"  # Default role
            assert result.token == "gho_test_token"

    @pytest.mark.asyncio
    async def test_github_authentication_token_failure(self) -> None:
        """Test GitHub authentication with token validation failure."""
        import urllib.error

        from githound.mcp.auth.providers.github import GitHubProvider

        provider = GitHubProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
        )

        # Mock urllib.request.urlopen to raise an error (simulating invalid token)
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError(
                url="https://api.github.com/user",
                code=401,
                msg="Unauthorized",
                hdrs={},
                fp=None,
            )

            # Test authentication with invalid token
            result = await provider.authenticate("invalid-token")

            assert result.success is False
            assert "invalid token" in result.error.lower()

    @pytest.mark.asyncio
    async def test_github_client_registration(self) -> None:
        """Test GitHub client registration."""
        from githound.mcp.auth.providers.github import GitHubProvider

        provider = GitHubProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
        )

        client_metadata = {
            "client_name": "Test GitHound Client",
            "redirect_uris": ["http://localhost:3000/callback"],
        }

        # OAuth proxy generates UUIDs for client registration
        registration = await provider.register_client(client_metadata)

        # Verify registration response has required fields
        assert "client_id" in registration
        assert "client_secret" in registration
        assert registration["client_name"] == "Test GitHound Client"
        assert registration["redirect_uris"] == ["http://localhost:3000/callback"]

        # Verify client_id and client_secret are valid UUIDs
        import uuid

        try:
            uuid.UUID(registration["client_id"])
            uuid.UUID(registration["client_secret"])
        except ValueError:
            pytest.fail("client_id or client_secret is not a valid UUID")


class TestGoogleProvider:
    """Test Google OAuth provider."""

    def test_google_provider_creation(self) -> None:
        """Test Google provider creation and configuration."""
        from githound.mcp.auth.providers.google import GoogleProvider

        provider = GoogleProvider(
            client_id="test-client-id.apps.googleusercontent.com",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
        )

        assert provider.client_id == "test-client-id.apps.googleusercontent.com"
        assert provider.client_secret == "test-client-secret"
        assert provider.base_url == "http://localhost:8000"

    def test_google_oauth_metadata(self) -> None:
        """Test Google OAuth metadata generation."""
        from githound.mcp.auth.providers.google import GoogleProvider

        provider = GoogleProvider(
            client_id="test-client-id.apps.googleusercontent.com",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
        )

        metadata = provider.get_oauth_metadata()
        assert metadata is not None
        assert metadata["provider"] == "google"
        assert metadata["client_id"] == "test-client-id.apps.googleusercontent.com"
        assert "authorization_endpoint" in metadata
        assert "token_endpoint" in metadata
        assert "scopes" in metadata

        # Check Google-specific scopes
        assert "openid" in metadata["scopes"]
        assert "email" in metadata["scopes"]
        assert "profile" in metadata["scopes"]

    @pytest.mark.asyncio
    async def test_google_authentication_success(self) -> None:
        """Test successful Google authentication flow."""
        import json
        from unittest.mock import MagicMock

        from githound.mcp.auth.providers.google import GoogleProvider

        provider = GoogleProvider(
            client_id="test-client-id.apps.googleusercontent.com",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
        )

        # Mock successful user info response from Google API
        # Note: Google's userinfo endpoint returns 'id' not 'sub'
        mock_user_response = {
            "id": "123456789",
            "name": "Test User",
            "email": "test@gmail.com",
            "picture": "https://lh3.googleusercontent.com/test",
            "email_verified": True,
        }

        # Mock urllib.request.urlopen for Google API call
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(mock_user_response).encode()
            mock_response.status = 200
            mock_urlopen.return_value.__enter__.return_value = mock_response

            # Test authentication with a token
            result = await provider.authenticate("ya29.test_token")

            assert result.success is True
            assert result.user.username == "test@gmail.com"  # Google uses email as username
            assert result.user.role == "user"  # Default role
            assert result.token == "ya29.test_token"


class TestOAuthProxy:
    """Test OAuth proxy functionality."""

    def test_oauth_proxy_creation(self) -> None:
        """Test OAuth proxy creation and configuration."""
        from githound.mcp.auth.providers.oauth_proxy import OAuthProxy

        proxy = OAuthProxy(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
            authorization_endpoint="https://auth.example.com/oauth/authorize",
            token_endpoint="https://auth.example.com/oauth/token",
            userinfo_endpoint="https://auth.example.com/oauth/userinfo",
        )

        assert proxy.client_id == "test-client-id"
        assert proxy.client_secret == "test-client-secret"
        assert proxy.authorization_endpoint == "https://auth.example.com/oauth/authorize"
        assert proxy.token_endpoint == "https://auth.example.com/oauth/token"
        assert proxy.userinfo_endpoint == "https://auth.example.com/oauth/userinfo"

    def test_oauth_proxy_metadata(self) -> None:
        """Test OAuth proxy metadata generation."""
        from githound.mcp.auth.providers.oauth_proxy import OAuthProxy

        proxy = OAuthProxy(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
            authorization_endpoint="https://auth.example.com/oauth/authorize",
            token_endpoint="https://auth.example.com/oauth/token",
            userinfo_endpoint="https://auth.example.com/oauth/userinfo",
        )

        metadata = proxy.get_oauth_metadata()
        assert metadata is not None
        assert metadata["client_id"] == "test-client-id"

        # URLs should be proxied through the base URL
        assert metadata["authorization_endpoint"] == "http://localhost:8000/oauth/authorize"
        assert metadata["token_endpoint"] == "http://localhost:8000/oauth/token"

    @pytest.mark.asyncio
    async def test_oauth_proxy_client_registration(self) -> None:
        """Test OAuth proxy client registration."""
        from githound.mcp.auth.providers.oauth_proxy import OAuthProxy

        proxy = OAuthProxy(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
            authorization_endpoint="https://auth.example.com/oauth/authorize",
            token_endpoint="https://auth.example.com/oauth/token",
            userinfo_endpoint="https://auth.example.com/oauth/userinfo",
        )

        client_metadata = {
            "client_name": "Test Client",
            "redirect_uris": ["http://localhost:3000/callback"],
            "scope": "read write",
        }

        # OAuth proxy generates UUIDs for client registration
        registration = await proxy.register_client(client_metadata)

        # Verify registration response has required fields
        assert "client_id" in registration
        assert "client_secret" in registration
        assert registration["client_name"] == "Test Client"
        assert registration["redirect_uris"] == ["http://localhost:3000/callback"]

        # Verify client_id and client_secret are valid UUIDs
        import uuid

        try:
            uuid.UUID(registration["client_id"])
            uuid.UUID(registration["client_secret"])
        except ValueError:
            pytest.fail("client_id or client_secret is not a valid UUID")

    @pytest.mark.asyncio
    async def test_oauth_proxy_authentication(self) -> None:
        """Test OAuth proxy authentication flow."""
        from githound.mcp.auth.providers.oauth_proxy import OAuthProxy

        proxy = OAuthProxy(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
            authorization_endpoint="https://auth.example.com/oauth/authorize",
            token_endpoint="https://auth.example.com/oauth/token",
            userinfo_endpoint="https://auth.example.com/oauth/userinfo",
        )

        # Mock successful user info response
        mock_user_response = {
            "id": "user123",  # OAuth proxy looks for 'id' or 'sub'
            "login": "testuser",  # OAuth proxy checks login, preferred_username, name, or id for username
            "email": "test@example.com",
            "name": "Test User",
        }

        # Mock urllib.request.urlopen for userinfo endpoint call
        # Need to patch it in the oauth_proxy module's namespace
        import json
        from unittest.mock import MagicMock

        with patch("githound.mcp.auth.providers.oauth_proxy.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(mock_user_response).encode()
            mock_response.status = 200
            mock_urlopen.return_value.__enter__.return_value = mock_response

            # Test authentication with a token
            result = await proxy.authenticate("test-access-token")

            assert result.success is True
            assert result.user.username == "testuser"
            assert result.user.role == "user"  # Default role
            assert result.token == "test-access-token"
