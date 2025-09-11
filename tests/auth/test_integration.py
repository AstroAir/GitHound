"""Integration tests for authentication system."""

import os
import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from typing import Optional, Any

from githound.mcp.auth import (
    set_auth_provider,
    get_auth_provider,
    authenticate_request,
    check_permission,
    check_tool_permission,
    _create_auth_provider_from_environment,
    _wrap_with_authorization_provider
)
from githound.mcp.auth.providers.base import AuthProvider, AuthResult, TokenInfo
from githound.mcp.models import User


class MockBaseProvider(AuthProvider):
    """Mock base authentication provider for integration testing."""
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.users = {
            "admin_token": User(username="admin", role="admin", permissions=["read", "write", "admin"]),
            "user_token": User(username="user", role="user", permissions=["read", "search"]),
            "readonly_token": User(username="readonly", role="readonly", permissions=["read"]),
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
    
    def get_oauth_metadata(self) -> Optional[dict]:
        return {
            "provider": "mock",
            "authorization_endpoint": "https://mock.example.com/oauth/authorize",
            "token_endpoint": "https://mock.example.com/oauth/token"
        }
    
    def supports_dynamic_client_registration(self) -> bool:
        return True


class MockAuthorizationProvider(AuthProvider):
    """Mock authorization provider that wraps a base provider."""
    
    def __init__(self, base_provider: AuthProvider, **kwargs) -> None:
        super().__init__(**kwargs)
        self.base_provider = base_provider
        self.config = kwargs  # [attr-defined]
    
    async def authenticate(self, token: str) -> AuthResult:
        """Pass through to base provider."""
        return await self.base_provider.authenticate(token)
    
    async def validate_token(self, token: str) -> Optional[TokenInfo]:
        """Pass through to base provider."""
        return await self.base_provider.validate_token(token)
    
    async def check_permission(self, user: User, permission: str, resource: Optional[str] = None, **context) -> bool:
        """Mock authorization logic."""
        # Admin always has access
        if user.role = = "admin":
            return True
        
        # Check for specific resource restrictions
        if resource and "secure" in resource and user.role != "admin":
            return False
        
        # Check basic permissions
        return permission in (user.permissions or [])
    
    async def check_tool_permission(self, user: User, tool_name: str, tool_args: Dict[str, Any]) -> bool:
        """Mock tool-level authorization."""
        # Admin always has access
        if user.role = = "admin":
            return True
        
        # Check for secure repository access
        repo_path = tool_args.get("repo_path", "")
        if "secure" in repo_path and user.role != "admin":
            return False
        
        # Check if user has permission for the tool
        return tool_name in (user.permissions or [])
    
    def get_oauth_metadata(self) -> Optional[dict]:
        """Pass through to base provider."""
        return self.base_provider.get_oauth_metadata()
    
    def supports_dynamic_client_registration(self) -> bool:
        """Pass through to base provider."""
        return self.base_provider.supports_dynamic_client_registration()


class TestAuthenticationIntegration:
    """Test end-to-end authentication flows."""
    
    def setup_method(self) -> None:
        """Set up test fixtures."""
        set_auth_provider(None)
    
    def teardown_method(self) -> None:
        """Clean up after tests."""
        set_auth_provider(None)
    
    @pytest.mark.asyncio
    async def test_complete_authentication_flow(self) -> None:
        """Test complete authentication flow from token to user."""
        provider = MockBaseProvider()
        set_auth_provider(provider)
        
        # Test successful authentication
        user = await authenticate_request("admin_token")
        assert user is not None
        assert user.username = = "admin"
        assert user.role = = "admin"
        assert "admin" in user.permissions
        
        # Test failed authentication
        user = await authenticate_request("invalid_token")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_permission_checking_flow(self) -> None:
        """Test permission checking with different users."""
        provider = MockBaseProvider()
        set_auth_provider(provider)
        
        # Get users
        admin_user = provider.users["admin_token"]
        user_user = provider.users["user_token"]
        readonly_user = provider.users["readonly_token"]
        
        # Test admin permissions
        assert await check_permission(admin_user, "read") is True
        assert await check_permission(admin_user, "write") is True
        assert await check_permission(admin_user, "admin") is True
        
        # Test regular user permissions
        assert await check_permission(user_user, "read") is True
        assert await check_permission(user_user, "search") is True
        assert await check_permission(user_user, "write") is False
        assert await check_permission(user_user, "admin") is False
        
        # Test readonly user permissions
        assert await check_permission(readonly_user, "read") is True
        assert await check_permission(readonly_user, "search") is False
        assert await check_permission(readonly_user, "write") is False
    
    @pytest.mark.asyncio
    async def test_authorization_wrapper_integration(self) -> None:
        """Test authorization provider wrapping base provider."""
        base_provider = MockBaseProvider()
        auth_provider = MockAuthorizationProvider(base_provider)
        set_auth_provider(auth_provider)
        
        # Test that authentication still works
        user = await authenticate_request("user_token")
        assert user is not None
        assert user.username = = "user"
        
        # Test enhanced permission checking
        user_user = base_provider.users["user_token"]
        
        # Regular resource access
        assert await check_permission(user_user, "read", "public_resource") is True
        
        # Secure resource access (should be denied for non-admin)
        assert await check_permission(user_user, "read", "secure_resource") is False
        
        # Admin should have access to secure resources
        admin_user = base_provider.users["admin_token"]
        assert await check_permission(admin_user, "read", "secure_resource") is True
    
    @pytest.mark.asyncio
    async def test_tool_permission_integration(self) -> None:
        """Test tool-level permission checking integration."""
        base_provider = MockBaseProvider()
        auth_provider = MockAuthorizationProvider(base_provider)
        set_auth_provider(auth_provider)
        
        user_user = base_provider.users["user_token"]
        admin_user = base_provider.users["admin_token"]
        
        # Test tool permission with public repository
        public_args = {"repo_path": "/public/repo", "pattern": "*.py"}
        assert await check_tool_permission(user_user, "search", public_args) is True
        
        # Test tool permission with secure repository (should be denied)
        secure_args = {"repo_path": "/secure/repo", "pattern": "*.py"}
        assert await check_tool_permission(user_user, "search", secure_args) is False
        
        # Admin should have access to secure repository
        assert await check_tool_permission(admin_user, "search", secure_args) is True
        
        # Test tool that user doesn't have permission for
        write_args = {"repo_path": "/public/repo", "content": "new content"}
        assert await check_tool_permission(user_user, "write", write_args) is False


class TestEnvironmentIntegration:
    """Test environment-based configuration integration."""
    
    def setup_method(self) -> None:
        """Set up test fixtures."""
        set_auth_provider(None)
    
    def teardown_method(self) -> None:
        """Clean up after tests."""
        set_auth_provider(None)
    
    @patch.dict(os.environ, {
        "FASTMCP_SERVER_AUTH": "githound.mcp.auth.providers.jwt.JWTVerifier",
        "FASTMCP_SERVER_AUTH_JWKS_URI": "https://example.com/.well-known/jwks.json",
        "FASTMCP_SERVER_AUTH_ISSUER": "test-issuer",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "test-audience"
    })
    @patch('githound.mcp.auth.providers.jwt.JWTVerifier')
    def test_jwt_environment_integration(self, mock_jwt) -> None:
        """Test JWT provider creation from environment."""
        mock_jwt.return_value = MockBaseProvider()
        
        provider = _create_auth_provider_from_environment()
        assert provider is not None
        
        # Verify JWT verifier was created with correct parameters
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
    @patch('githound.mcp.auth.providers.github.GitHubProvider')
    def test_github_environment_integration(self, mock_github) -> None:
        """Test GitHub provider creation from environment."""
        mock_github.return_value = MockBaseProvider()
        
        provider = _create_auth_provider_from_environment()
        assert provider is not None
        
        # Verify GitHub provider was created with correct parameters
        mock_github.assert_called_once()
        call_kwargs = mock_github.call_args[1]
        assert call_kwargs['client_id'] == "test-client-id"
        assert call_kwargs['client_secret'] == "test-client-secret"
        assert call_kwargs['base_url'] == "http://localhost:8000"


class TestAuthorizationIntegration:
    """Test authorization provider integration."""
    
    def setup_method(self) -> None:
        """Set up test fixtures."""
        set_auth_provider(None)
    
    def teardown_method(self) -> None:
        """Clean up after tests."""
        set_auth_provider(None)
    
    def test_no_authorization_wrapper(self) -> None:
        """Test behavior when no authorization is enabled."""
        base_provider = MockBaseProvider()
        
        with patch.dict(os.environ, {}, clear=True):
            wrapped_provider = _wrap_with_authorization_provider(base_provider)
            assert wrapped_provider is base_provider  # Should be unchanged
    
    @patch.dict(os.environ, {"EUNOMIA_ENABLE": "true"})
    @patch('githound.mcp.auth.EUNOMIA_AVAILABLE', False)
    def test_eunomia_not_available(self) -> None:
        """Test Eunomia authorization when package not available."""
        base_provider = MockBaseProvider()
        
        with patch('githound.mcp.auth.logger') as mock_logger:
            wrapped_provider = _wrap_with_authorization_provider(base_provider)
            assert wrapped_provider is base_provider  # Should be unchanged
            mock_logger.warning.assert_called()
    
    @patch.dict(os.environ, {"PERMIT_ENABLE": "true"})
    @patch('githound.mcp.auth.PERMIT_AVAILABLE', False)
    def test_permit_not_available(self) -> None:
        """Test Permit.io authorization when package not available."""
        base_provider = MockBaseProvider()
        
        with patch('githound.mcp.auth.logger') as mock_logger:
            wrapped_provider = _wrap_with_authorization_provider(base_provider)
            assert wrapped_provider is base_provider  # Should be unchanged
            mock_logger.warning.assert_called()
    
    @patch.dict(os.environ, {"EUNOMIA_ENABLE": "true"})
    @patch('githound.mcp.auth.EUNOMIA_AVAILABLE', True)
    @patch('githound.mcp.auth.EunomiaAuthorizationProvider')
    def test_eunomia_wrapper_applied(self, mock_eunomia) -> None:
        """Test Eunomia authorization wrapper is applied."""
        base_provider = MockBaseProvider()
        wrapped_provider = MockAuthorizationProvider(base_provider)
        mock_eunomia.return_value = wrapped_provider
        
        result = _wrap_with_authorization_provider(base_provider)
        assert result is wrapped_provider
        mock_eunomia.assert_called_once_with(base_provider)
    
    @patch.dict(os.environ, {"PERMIT_ENABLE": "true"})
    @patch('githound.mcp.auth.PERMIT_AVAILABLE', True)
    @patch('githound.mcp.auth.PermitAuthorizationProvider')
    def test_permit_wrapper_applied(self, mock_permit) -> None:
        """Test Permit.io authorization wrapper is applied."""
        base_provider = MockBaseProvider()
        wrapped_provider = MockAuthorizationProvider(base_provider)
        mock_permit.return_value = wrapped_provider
        
        result = _wrap_with_authorization_provider(base_provider)
        assert result is wrapped_provider
        mock_permit.assert_called_once_with(base_provider)
    
    @patch.dict(os.environ, {"EUNOMIA_ENABLE": "true", "PERMIT_ENABLE": "true"})
    @patch('githound.mcp.auth.EUNOMIA_AVAILABLE', True)
    @patch('githound.mcp.auth.PERMIT_AVAILABLE', True)
    @patch('githound.mcp.auth.EunomiaAuthorizationProvider')
    @patch('githound.mcp.auth.PermitAuthorizationProvider')
    def test_both_authorization_wrappers(self, mock_permit, mock_eunomia) -> None:
        """Test both authorization wrappers are applied."""
        base_provider = MockBaseProvider()
        eunomia_wrapped = MockAuthorizationProvider(base_provider)
        permit_wrapped = MockAuthorizationProvider(eunomia_wrapped)
        
        mock_eunomia.return_value = eunomia_wrapped
        mock_permit.return_value = permit_wrapped
        
        result = _wrap_with_authorization_provider(base_provider)
        assert result is permit_wrapped
        
        # Verify both wrappers were applied in correct order
        mock_eunomia.assert_called_once_with(base_provider)
        mock_permit.assert_called_once_with(eunomia_wrapped)


class TestEndToEndFlow:
    """Test complete end-to-end authentication and authorization flows."""
    
    def setup_method(self) -> None:
        """Set up test fixtures."""
        set_auth_provider(None)
    
    def teardown_method(self) -> None:
        """Clean up after tests."""
        set_auth_provider(None)
    
    @pytest.mark.asyncio
    async def test_complete_flow_with_authorization(self) -> None:
        """Test complete flow from environment setup to permission checking."""
        base_provider = MockBaseProvider()
        auth_provider = MockAuthorizationProvider(base_provider)
        
        # Simulate environment-based setup
        set_auth_provider(auth_provider)
        
        # Test authentication
        user = await authenticate_request("user_token")
        assert user is not None
        assert user.username = = "user"
        
        # Test basic permission
        assert await check_permission(user, "read") is True
        assert await check_permission(user, "write") is False
        
        # Test resource-based permission
        assert await check_permission(user, "read", "public_resource") is True
        assert await check_permission(user, "read", "secure_resource") is False
        
        # Test tool permission
        public_args = {"repo_path": "/public/repo"}
        secure_args = {"repo_path": "/secure/repo"}
        
        assert await check_tool_permission(user, "search", public_args) is True
        assert await check_tool_permission(user, "search", secure_args) is False
        
        # Test admin user has full access
        admin = await authenticate_request("admin_token")
        assert admin is not None
        
        assert await check_permission(admin, "read", "secure_resource") is True
        assert await check_tool_permission(admin, "search", secure_args) is True
    
    @pytest.mark.asyncio
    async def test_oauth_metadata_flow(self) -> None:
        """Test OAuth metadata generation through the system."""
        base_provider = MockBaseProvider()
        auth_provider = MockAuthorizationProvider(base_provider)
        set_auth_provider(auth_provider)
        
        # Test that OAuth metadata is available
        provider = get_auth_provider()
        metadata = provider.get_oauth_metadata()
        
        assert metadata is not None
        assert metadata["provider"] == "mock"
        assert "authorization_endpoint" in metadata
        assert "token_endpoint" in metadata
        
        # Test DCR support
        assert provider.supports_dynamic_client_registration() is True
