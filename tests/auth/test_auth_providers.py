"""Tests for GitHound MCP server authentication providers."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_http_session() -> None:
    """Mock aiohttp ClientSession for testing HTTP requests."""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_instance
        mock_session.return_value.__aexit__.return_value = None
        yield mock_instance


class TestJWTVerifier:
    """Test JWT token verification."""

    @pytest.mark.asyncio
    async def test_jwt_verifier_basic(self) -> None:
        """Test basic JWT verifier functionality."""
        try:
            from githound.mcp.auth.providers.jwt import StaticJWTVerifier

            # Create a static JWT verifier for testing
            verifier = StaticJWTVerifier(
                secret_key="test-secret-key", issuer="test-issuer", audience="test-audience"
            )

            # Test with invalid token
            result = await verifier.validate_token("invalid-token")
            assert result is None, "Invalid token should return None"

        except ImportError:
            pytest.skip("JWT dependencies not available")

    @pytest.mark.asyncio
    async def test_jwt_verifier_authentication(self) -> None:
        """Test JWT authentication flow."""
        try:
            import time

            import jwt

            from githound.mcp.auth.providers.jwt import StaticJWTVerifier

            secret_key = "test-secret-key"
            verifier = StaticJWTVerifier(
                secret_key=secret_key, issuer="test-issuer", audience="test-audience"
            )

            # Create a valid JWT token
            # Use time.time() instead of datetime.utcnow().timestamp() to avoid timezone issues
            current_time = int(time.time())
            payload = {
                "sub": "user-123",  # Subject (user ID)
                "preferred_username": "testuser",  # Username
                "name": "Test User",  # Display name
                "role": "user",
                "permissions": ["read", "search"],
                "iss": "test-issuer",
                "aud": "test-audience",
                "exp": current_time + 3600,  # Expires in 1 hour
                "iat": current_time,  # Issued now
            }

            token = jwt.encode(payload, secret_key, algorithm="HS256")

            # Test authentication
            result = await verifier.authenticate(f"Bearer {token}")
            assert result.success is True
            assert result.user.username == "testuser"
            assert result.user.role == "user"

        except ImportError:
            pytest.skip("JWT dependencies not available")


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
        assert "authorization_endpoint" in metadata
        assert metadata["provider"] == "github"
        assert "client_id" in metadata
        assert metadata["client_id"] == "test-client-id"

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
    async def test_github_authentication_flow(self) -> None:
        """Test GitHub authentication flow with mocked responses."""
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


class TestGoogleProvider:
    """Test Google OAuth provider."""

    def test_google_provider_creation(self) -> None:
        """Test Google provider creation and configuration."""
        from githound.mcp.auth.providers.google import GoogleProvider

        provider = GoogleProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
        )

        assert provider.client_id == "test-client-id"
        assert provider.client_secret == "test-client-secret"
        assert provider.base_url == "http://localhost:8000"

    def test_google_oauth_metadata(self) -> None:
        """Test Google OAuth metadata generation."""
        from githound.mcp.auth.providers.google import GoogleProvider

        provider = GoogleProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
        )

        metadata = provider.get_oauth_metadata()
        assert metadata is not None
        assert "authorization_endpoint" in metadata
        assert metadata["provider"] == "google"
        assert "client_id" in metadata
        assert metadata["client_id"] == "test-client-id"

    def test_google_dcr_support(self) -> None:
        """Test Google Dynamic Client Registration support."""
        from githound.mcp.auth.providers.google import GoogleProvider

        provider = GoogleProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
        )

        assert provider.supports_dynamic_client_registration() is True

    @pytest.mark.asyncio
    async def test_google_authentication_flow(self) -> None:
        """Test Google authentication flow with mocked responses."""
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
            authorization_endpoint="https://example.com/oauth/authorize",
            token_endpoint="https://example.com/oauth/token",
            userinfo_endpoint="https://example.com/oauth/userinfo",
        )

        assert proxy.client_id == "test-client-id"
        assert proxy.client_secret == "test-client-secret"
        assert proxy.authorization_endpoint == "https://example.com/oauth/authorize"

    def test_oauth_proxy_metadata(self) -> None:
        """Test OAuth proxy metadata generation."""
        from githound.mcp.auth.providers.oauth_proxy import OAuthProxy

        proxy = OAuthProxy(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
            authorization_endpoint="https://example.com/oauth/authorize",
            token_endpoint="https://example.com/oauth/token",
            userinfo_endpoint="https://example.com/oauth/userinfo",
        )

        metadata = proxy.get_oauth_metadata()
        assert metadata is not None
        assert metadata["authorization_endpoint"] == "http://localhost:8000/oauth/authorize"
        assert metadata["token_endpoint"] == "http://localhost:8000/oauth/token"

    def test_oauth_proxy_dcr_support(self) -> None:
        """Test OAuth proxy Dynamic Client Registration support."""
        from githound.mcp.auth.providers.oauth_proxy import OAuthProxy

        proxy = OAuthProxy(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
            authorization_endpoint="https://example.com/oauth/authorize",
            token_endpoint="https://example.com/oauth/token",
        )

        assert proxy.supports_dynamic_client_registration() is True

    @pytest.mark.asyncio
    async def test_oauth_proxy_client_registration(self) -> None:
        """Test OAuth proxy client registration."""
        from githound.mcp.auth.providers.oauth_proxy import OAuthProxy

        proxy = OAuthProxy(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
            authorization_endpoint="https://example.com/oauth/authorize",
            token_endpoint="https://example.com/oauth/token",
            userinfo_endpoint="https://example.com/oauth/userinfo",
        )

        client_metadata = {
            "client_name": "Test Client",
            "redirect_uris": ["http://localhost:3000/callback"],
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
