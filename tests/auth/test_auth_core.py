"""Tests for core authentication functionality."""

import os
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Optionalnal

from githound.mcp.auth import (
    set_auth_provider,
    get_auth_provider,
    authenticate_request,
    validate_token,
    check_permission,
    check_tool_permission,
    get_current_user,
    check_rate_limit
)
from githound.mcp.auth.providers.base import AuthProvider, AuthResult, TokenInfo
from githound.mcp.models import User


class MockAuthProvider(AuthProvider):
    """Mock authentication provider for testing."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.users = {
            "valid_token": User(username="testuser", role="user", permissions=["read"]),
            "admin_token": User(username="admin", role="admin", permissions=["read", "write", "admin"]),
        }

    async def authenticate(self, token: str) -> AuthResult:
        """Mock authentication."""
        if token in self.users:
            return AuthResult(success=True, user=self.users[token], token=token)
        return AuthResult(success=False, error="Invalid token")

    async def validate_token(self, token: str) -> Optional[TokenInfo]:
        """Mock token validation."""
        if token in self.users:
            user = self.users[token]
            return TokenInfo(
                user_id=user.username,
                username=user.username,
                roles=[user.role],
                permissions=user.permissions
            )
        return None

    async def check_permission(self, user: User, permission: str, resource: Optional[str] = None, **context) -> bool:
        """Mock permission checking."""
        if user.role = = "admin":
            return True
        return permission in (user.permissions or [])

    def get_oauth_metadata(self) -> Optional[dict]:
        return None

    def supports_dynamic_client_registration(self) -> bool:
        return False


class TestAuthCore:
    """Test core authentication functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Clear any existing auth provider
        set_auth_provider(None)

    def teardown_method(self) -> None:
        """Clean up after tests."""
        # Clear auth provider
        set_auth_provider(None)

    def test_set_get_auth_provider(self) -> None:
        """Test setting and getting auth provider."""
        provider = MockAuthProvider()

        # Initially no provider
        assert get_auth_provider() is None

        # Set provider
        set_auth_provider(provider)
        assert get_auth_provider() is provider

        # Clear provider
        set_auth_provider(None)
        assert get_auth_provider() is None

    @pytest.mark.asyncio
    async def test_authenticate_request_success(self) -> None:
        """Test successful request authentication."""
        provider = MockAuthProvider()
        set_auth_provider(provider)

        user = await authenticate_request("valid_token")
        assert user is not None
        assert user.username = = "testuser"
        assert user.role = = "user"

    @pytest.mark.asyncio
    async def test_authenticate_request_failure(self) -> None:
        """Test failed request authentication."""
        provider = MockAuthProvider()
        set_auth_provider(provider)

        user = await authenticate_request("invalid_token")
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_request_no_provider(self) -> None:
        """Test authentication with no provider set."""
        user = await authenticate_request("any_token")
        assert user is None

    @pytest.mark.asyncio
    async def test_validate_token_success(self) -> None:
        """Test successful token validation."""
        provider = MockAuthProvider()
        set_auth_provider(provider)

        token_info = await validate_token("valid_token")
        assert token_info is not None
        assert token_info.username = = "testuser"
        assert "user" in token_info.roles
        assert "read" in token_info.permissions

    @pytest.mark.asyncio
    async def test_validate_token_failure(self) -> None:
        """Test failed token validation."""
        provider = MockAuthProvider()
        set_auth_provider(provider)

        token_info = await validate_token("invalid_token")
        assert token_info is None

    @pytest.mark.asyncio
    async def test_check_permission_success(self) -> None:
        """Test successful permission check."""
        provider = MockAuthProvider()
        set_auth_provider(provider)

        user = User(username="testuser", role="user", permissions=["read"])

        # User has read permission
        allowed = await check_permission(user, "read")
        assert allowed is True

        # User doesn't have write permission
        allowed = await check_permission(user, "write")
        assert allowed is False

    @pytest.mark.asyncio
    async def test_check_permission_admin(self) -> None:
        """Test admin permission check."""
        provider = MockAuthProvider()
        set_auth_provider(provider)

        admin_user = User(username="admin", role="admin", permissions=[])

        # Admin should have all permissions
        allowed = await check_permission(admin_user, "read")
        assert allowed is True

        allowed = await check_permission(admin_user, "write")
        assert allowed is True

        allowed = await check_permission(admin_user, "admin")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_check_permission_no_provider(self) -> None:
        """Test permission check with no provider."""
        user = User(username="testuser", role="user", permissions=["read"])

        # Should fall back to basic role/permission check
        allowed = await check_permission(user, "read")
        assert allowed is True

        # Admin role should have all permissions
        admin_user = User(username="admin", role="admin", permissions=[])
        allowed = await check_permission(admin_user, "anything")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_check_tool_permission(self) -> None:
        """Test tool-level permission checking."""
        provider = MockAuthProvider()
        set_auth_provider(provider)

        user = User(username="testuser", role="user", permissions=["search"])
        tool_args = {"repo_path": "/test/repo", "pattern": "*.py"}

        # Mock the provider to support tool permission checking
        provider.check_tool_permission = AsyncMock(return_value=True)

        allowed = await check_tool_permission(user, "search_files", tool_args)
        assert allowed is True

        # Verify the method was called with correct arguments
        provider.check_tool_permission.assert_called_once_with(
            user, "search_files", tool_args)

    @pytest.mark.asyncio
    async def test_check_tool_permission_fallback(self) -> None:
        """Test tool permission fallback to regular permission check."""
        provider = MockAuthProvider()
        set_auth_provider(provider)

        user = User(username="testuser", role="user",
                    permissions=["search_files"])
        tool_args = {"repo_path": "/test/repo"}

        # Provider doesn't have check_tool_permission method
        allowed = await check_tool_permission(user, "search_files", tool_args)
        assert allowed is True  # Should fall back to regular permission check

    @pytest.mark.asyncio
    async def test_check_tool_permission_no_provider(self) -> None:
        """Test tool permission check with no provider."""
        admin_user = User(username="admin", role="admin", permissions=[])
        tool_args = {"repo_path": "/test/repo"}

        # Admin should have access
        allowed = await check_tool_permission(admin_user, "any_tool", tool_args)
        assert allowed is True

        # Regular user should not have access
        user = User(username="user", role="user", permissions=[])
        allowed = await check_tool_permission(user, "any_tool", tool_args)
        assert allowed is False

    def test_get_current_user(self) -> None:
        """Test getting current user."""
        # This is a placeholder implementation
        user = get_current_user()
        assert user is None

    def test_check_rate_limit(self) -> None:
        """Test rate limiting check."""
        # This is a placeholder implementation
        user = User(username="testuser", role="user", permissions=[])

        # Should always return True in the placeholder implementation
        allowed = check_rate_limit(user)
        assert allowed is True

        # Should work with None user too
        allowed = check_rate_limit(None)
        assert allowed is True


class TestAuthEnvironment:
    """Test environment-based authentication configuration."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Clear any existing auth provider
        set_auth_provider(None)

    def teardown_method(self) -> None:
        """Clean up after tests."""
        # Clear auth provider
        set_auth_provider(None)

    @patch.dict(os.environ, {}, clear=True)
    def test_no_auth_environment(self) -> None:
        """Test behavior with no authentication environment variables."""
        from githound.mcp.auth import _create_auth_provider_from_environment

        provider = _create_auth_provider_from_environment()
        assert provider is None

    @patch.dict(os.environ, {
        "FASTMCP_SERVER_AUTH": "githound.mcp.auth.providers.jwt.JWTVerifier",
        "FASTMCP_SERVER_AUTH_JWKS_URI": "https://example.com/.well-known/jwks.json",
        "FASTMCP_SERVER_AUTH_ISSUER": "test-issuer",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "test-audience"
    })
    def test_jwt_environment_config(self) -> None:
        """Test JWT provider creation from environment."""
        from githound.mcp.auth import _create_auth_provider_from_environment

        with patch('githound.mcp.auth.providers.jwt.JWTVerifier') as mock_jwt:
            mock_jwt.return_value = MockAuthProvider()

            provider = _create_auth_provider_from_environment()

            # Should have created JWT verifier with correct parameters
            mock_jwt.assert_called_once()
            call_kwargs = mock_jwt.call_args[1]
            assert call_kwargs['jwks_uri'] == "https://example.com/.well-known/jwks.json"
            assert call_kwargs['issuer'] == "test-issuer"
            assert call_kwargs['audience'] == "test-audience"

    @patch.dict(os.environ, {
        "FASTMCP_SERVER_AUTH": "githound.mcp.auth.providers.github.GitHubProvider",
        "FASTMCP_SERVER_AUTH_GITHUB_CLIENT_ID": "test-client-id",
        "FASTMCP_SERVER_AUTH_GITHUB_CLIENT_SECRET": "test-client-secret",
        "FASTMCP_SERVER_BASE_URL": "http://localhost:8000"
    })
    def test_github_environment_config(self) -> None:
        """Test GitHub provider creation from environment."""
        from githound.mcp.auth import _create_auth_provider_from_environment

        with patch('githound.mcp.auth.providers.github.GitHubProvider') as mock_github:
            mock_github.return_value = MockAuthProvider()

            provider = _create_auth_provider_from_environment()

            # Should have created GitHub provider with correct parameters
            mock_github.assert_called_once()
            call_kwargs = mock_github.call_args[1]
            assert call_kwargs['client_id'] == "test-client-id"
            assert call_kwargs['client_secret'] == "test-client-secret"
            assert call_kwargs['base_url'] == "http://localhost:8000"
