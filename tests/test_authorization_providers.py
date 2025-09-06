"""Tests for authorization providers (Eunomia and Permit.io)."""

import os
import json
import pytest
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from typing import Optional

from githound.mcp.auth.providers.base import AuthProvider, AuthResult, TokenInfo
from githound.mcp.models import User


class MockBaseProvider(AuthProvider):
    """Mock base authentication provider for testing."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.users = {
            "admin": User(username="admin", role="admin", permissions=[]),
            "user": User(username="user", role="user", permissions=["read", "search"]),
            "readonly": User(username="readonly", role="readonly", permissions=["read"]),
        }
    
    async def authenticate(self, token: str) -> AuthResult:
        """Mock authentication."""
        username = token.replace("Bearer ", "").replace("token_", "")
        if username in self.users:
            return AuthResult(success=True, user=self.users[username], token=token)
        return AuthResult(success=False, error="Invalid token")
    
    async def validate_token(self, token: str) -> Optional[TokenInfo]:
        """Mock token validation."""
        username = token.replace("Bearer ", "").replace("token_", "")
        if username in self.users:
            user = self.users[username]
            return TokenInfo(
                user_id=user.username,
                username=user.username,
                roles=[user.role],
                permissions=user.permissions
            )
        return None
    
    def get_oauth_metadata(self) -> Optional[dict]:
        return None
    
    def supports_dynamic_client_registration(self) -> bool:
        return False


class TestEunomiaAuthorizationProvider:
    """Test Eunomia authorization provider."""
    
    @pytest.fixture
    def mock_base_provider(self):
        """Create a mock base provider."""
        return MockBaseProvider()
    
    @pytest.fixture
    def policy_file(self):
        """Create a temporary policy file."""
        policy_data = {
            "version": "1.0",
            "server_name": "test-server",
            "policies": [
                {
                    "id": "admin_access",
                    "subjects": ["role:admin"],
                    "resources": ["*"],
                    "actions": ["*"],
                    "effect": "allow"
                },
                {
                    "id": "user_read",
                    "subjects": ["role:user"],
                    "resources": ["test-server:*"],
                    "actions": ["read", "search"],
                    "effect": "allow"
                },
                {
                    "id": "default_deny",
                    "subjects": ["*"],
                    "resources": ["*"],
                    "actions": ["*"],
                    "effect": "deny"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(policy_data, f)
            return f.name
    
    @pytest.mark.skipif(
        not os.getenv("TEST_EUNOMIA", "false").lower() == "true",
        reason="Eunomia tests require eunomia-mcp package and TEST_EUNOMIA=true"
    )
    def test_eunomia_provider_creation(self, mock_base_provider, policy_file):
        """Test creating Eunomia authorization provider."""
        try:
            from githound.mcp.auth.providers.eunomia import EunomiaAuthorizationProvider
            
            provider = EunomiaAuthorizationProvider(
                base_provider=mock_base_provider,
                policy_file=policy_file,
                server_name="test-server"
            )
            
            assert provider.base_provider == mock_base_provider
            assert provider.config.policy_file == policy_file
            assert provider.config.server_name == "test-server"
            
        except ImportError:
            pytest.skip("eunomia-mcp not available")
    
    @pytest.mark.skipif(
        not os.getenv("TEST_EUNOMIA", "false").lower() == "true",
        reason="Eunomia tests require eunomia-mcp package and TEST_EUNOMIA=true"
    )
    @pytest.mark.asyncio
    async def test_eunomia_authentication_passthrough(self, mock_base_provider, policy_file):
        """Test that authentication passes through to base provider."""
        try:
            from githound.mcp.auth.providers.eunomia import EunomiaAuthorizationProvider
            
            provider = EunomiaAuthorizationProvider(
                base_provider=mock_base_provider,
                policy_file=policy_file
            )
            
            # Test successful authentication
            result = await provider.authenticate("token_admin")
            assert result.success is True
            assert result.user.username == "admin"
            
            # Test failed authentication
            result = await provider.authenticate("invalid_token")
            assert result.success is False
            
        except ImportError:
            pytest.skip("eunomia-mcp not available")
    
    @pytest.mark.skipif(
        not os.getenv("TEST_EUNOMIA", "false").lower() == "true",
        reason="Eunomia tests require eunomia-mcp package and TEST_EUNOMIA=true"
    )
    @pytest.mark.asyncio
    async def test_eunomia_permission_checking(self, mock_base_provider, policy_file):
        """Test Eunomia permission checking."""
        try:
            from githound.mcp.auth.providers.eunomia import EunomiaAuthorizationProvider
            
            provider = EunomiaAuthorizationProvider(
                base_provider=mock_base_provider,
                policy_file=policy_file,
                server_name="test-server"
            )
            
            admin_user = User(username="admin", role="admin", permissions=[])
            user_user = User(username="user", role="user", permissions=["read"])
            readonly_user = User(username="readonly", role="readonly", permissions=["read"])
            
            # Admin should have full access
            assert await provider.check_permission(admin_user, "read", "test-server:repo") is True
            assert await provider.check_permission(admin_user, "write", "test-server:repo") is True
            
            # User should have read access
            assert await provider.check_permission(user_user, "read", "test-server:repo") is True
            assert await provider.check_permission(user_user, "search", "test-server:repo") is True
            
            # Readonly should have limited access
            assert await provider.check_permission(readonly_user, "read", "test-server:info") is True
            assert await provider.check_permission(readonly_user, "write", "test-server:repo") is False
            
        except ImportError:
            pytest.skip("eunomia-mcp not available")
    
    def test_eunomia_environment_loading(self, mock_base_provider):
        """Test loading Eunomia configuration from environment."""
        with patch.dict(os.environ, {
            "EUNOMIA_POLICY_FILE": "custom_policies.json",
            "EUNOMIA_SERVER_NAME": "custom-server",
            "EUNOMIA_ENABLE_AUDIT_LOGGING": "false",
            "EUNOMIA_BYPASS_METHODS": '["init", "ping"]'
        }):
            try:
                from githound.mcp.auth.providers.eunomia import EunomiaAuthorizationProvider
                
                with patch('os.path.exists', return_value=True), \
                     patch('githound.mcp.auth.providers.eunomia.create_eunomia_middleware'):
                    
                    provider = EunomiaAuthorizationProvider(mock_base_provider)
                    
                    assert provider.config.policy_file == "custom_policies.json"
                    assert provider.config.server_name == "custom-server"
                    assert provider.config.enable_audit_logging is False
                    assert provider.config.bypass_methods == ["init", "ping"]
                    
            except ImportError:
                pytest.skip("eunomia-mcp not available")


class TestPermitAuthorizationProvider:
    """Test Permit.io authorization provider."""
    
    @pytest.fixture
    def mock_base_provider(self):
        """Create a mock base provider."""
        return MockBaseProvider()
    
    @pytest.mark.skipif(
        not os.getenv("TEST_PERMIT", "false").lower() == "true",
        reason="Permit tests require permit-fastmcp package and TEST_PERMIT=true"
    )
    def test_permit_provider_creation(self, mock_base_provider):
        """Test creating Permit.io authorization provider."""
        try:
            from githound.mcp.auth.providers.permit import PermitAuthorizationProvider
            
            provider = PermitAuthorizationProvider(
                base_provider=mock_base_provider,
                permit_api_key="test-api-key",
                permit_pdp_url="http://localhost:7766",
                server_name="test-server"
            )
            
            assert provider.base_provider == mock_base_provider
            assert provider.config.permit_api_key == "test-api-key"
            assert provider.config.permit_pdp_url == "http://localhost:7766"
            assert provider.config.server_name == "test-server"
            
        except ImportError:
            pytest.skip("permit-fastmcp not available")
    
    @pytest.mark.skipif(
        not os.getenv("TEST_PERMIT", "false").lower() == "true",
        reason="Permit tests require permit-fastmcp package and TEST_PERMIT=true"
    )
    @pytest.mark.asyncio
    async def test_permit_authentication_passthrough(self, mock_base_provider):
        """Test that authentication passes through to base provider."""
        try:
            from githound.mcp.auth.providers.permit import PermitAuthorizationProvider
            
            with patch('githound.mcp.auth.providers.permit.PermitMcpMiddleware'):
                provider = PermitAuthorizationProvider(
                    base_provider=mock_base_provider,
                    permit_api_key="test-api-key"
                )
                
                # Test successful authentication
                result = await provider.authenticate("token_admin")
                assert result.success is True
                assert result.user.username == "admin"
                
                # Test failed authentication
                result = await provider.authenticate("invalid_token")
                assert result.success is False
                
        except ImportError:
            pytest.skip("permit-fastmcp not available")
    
    @pytest.mark.skipif(
        not os.getenv("TEST_PERMIT", "false").lower() == "true",
        reason="Permit tests require permit-fastmcp package and TEST_PERMIT=true"
    )
    @pytest.mark.asyncio
    async def test_permit_permission_checking(self, mock_base_provider):
        """Test Permit.io permission checking."""
        try:
            from githound.mcp.auth.providers.permit import PermitAuthorizationProvider
            
            with patch('githound.mcp.auth.providers.permit.PermitMcpMiddleware'):
                provider = PermitAuthorizationProvider(
                    base_provider=mock_base_provider,
                    permit_api_key="test-api-key",
                    server_name="test-server"
                )
                
                admin_user = User(username="admin", role="admin", permissions=[])
                user_user = User(username="user", role="user", permissions=["read"])
                readonly_user = User(username="readonly", role="readonly", permissions=["read"])
                
                # Admin should have full access
                assert await provider.check_permission(admin_user, "read", "test-server") is True
                assert await provider.check_permission(admin_user, "write", "test-server") is True
                
                # User should have read access
                assert await provider.check_permission(user_user, "read", "test-server") is True
                assert await provider.check_permission(user_user, "search", "test-server") is True
                
                # Readonly should have limited access
                assert await provider.check_permission(readonly_user, "read", "test-server:info") is True
                assert await provider.check_permission(readonly_user, "write", "test-server") is False
                
        except ImportError:
            pytest.skip("permit-fastmcp not available")
    
    @pytest.mark.skipif(
        not os.getenv("TEST_PERMIT", "false").lower() == "true",
        reason="Permit tests require permit-fastmcp package and TEST_PERMIT=true"
    )
    @pytest.mark.asyncio
    async def test_permit_tool_permission_checking(self, mock_base_provider):
        """Test Permit.io tool-level permission checking with ABAC."""
        try:
            from githound.mcp.auth.providers.permit import PermitAuthorizationProvider
            
            with patch('githound.mcp.auth.providers.permit.PermitMcpMiddleware'):
                provider = PermitAuthorizationProvider(
                    base_provider=mock_base_provider,
                    permit_api_key="test-api-key"
                )
                
                user = User(username="user", role="user", permissions=["conditional-greet"])
                
                # Test ABAC with tool arguments
                # Should be denied when number <= 10
                assert await provider.check_tool_permission(
                    user, "conditional-greet", {"name": "Alice", "number": 5}
                ) is False
                
                # Should be allowed when number > 10
                assert await provider.check_tool_permission(
                    user, "conditional-greet", {"name": "Bob", "number": 15}
                ) is True
                
        except ImportError:
            pytest.skip("permit-fastmcp not available")
    
    def test_permit_environment_loading(self, mock_base_provider):
        """Test loading Permit.io configuration from environment."""
        with patch.dict(os.environ, {
            "PERMIT_MCP_PERMIT_PDP_URL": "http://custom:7766",
            "PERMIT_MCP_PERMIT_API_KEY": "custom-api-key",
            "PERMIT_MCP_IDENTITY_MODE": "header",
            "PERMIT_MCP_ENABLE_AUDIT_LOGGING": "false",
            "PERMIT_MCP_BYPASSED_METHODS": '["init", "ping"]'
        }):
            try:
                from githound.mcp.auth.providers.permit import PermitAuthorizationProvider
                
                with patch('githound.mcp.auth.providers.permit.PermitMcpMiddleware'):
                    provider = PermitAuthorizationProvider(mock_base_provider)
                    
                    assert provider.config.permit_pdp_url == "http://custom:7766"
                    assert provider.config.permit_api_key == "custom-api-key"
                    assert provider.config.identity_mode == "header"
                    assert provider.config.enable_audit_logging is False
                    assert provider.config.bypass_methods == ["init", "ping"]
                    
            except ImportError:
                pytest.skip("permit-fastmcp not available")


class TestAuthorizationIntegration:
    """Test integration of authorization providers with GitHound auth system."""
    
    @pytest.mark.asyncio
    async def test_auth_wrapper_environment_detection(self):
        """Test that authorization wrappers are applied based on environment."""
        from githound.mcp.auth import _wrap_with_authorization_provider
        
        mock_provider = MockBaseProvider()
        
        # Test with no authorization enabled
        with patch.dict(os.environ, {}, clear=True):
            wrapped = _wrap_with_authorization_provider(mock_provider)
            assert wrapped == mock_provider  # Should be unchanged
        
        # Test with Eunomia enabled but not available
        with patch.dict(os.environ, {"EUNOMIA_ENABLE": "true"}):
            with patch('githound.mcp.auth.logger') as mock_logger:
                wrapped = _wrap_with_authorization_provider(mock_provider)
                assert wrapped == mock_provider  # Should be unchanged
                mock_logger.warning.assert_called()
        
        # Test with Permit enabled but not available
        with patch.dict(os.environ, {"PERMIT_ENABLE": "true"}):
            with patch('githound.mcp.auth.logger') as mock_logger:
                wrapped = _wrap_with_authorization_provider(mock_provider)
                assert wrapped == mock_provider  # Should be unchanged
                mock_logger.warning.assert_called()
    
    @pytest.mark.asyncio
    async def test_enhanced_permission_checking(self):
        """Test enhanced permission checking with context."""
        from githound.mcp.auth import check_permission, check_tool_permission
        from githound.mcp.auth import set_auth_provider
        
        # Create a mock provider that supports enhanced permission checking
        mock_provider = Mock()
        mock_provider.check_permission = AsyncMock(return_value=True)
        mock_provider.check_tool_permission = AsyncMock(return_value=True)
        
        set_auth_provider(mock_provider)
        
        user = User(username="test", role="user", permissions=[])
        
        # Test enhanced permission checking
        result = await check_permission(user, "read", "resource", extra_context="value")
        assert result is True
        mock_provider.check_permission.assert_called_with(
            user, "read", "resource", extra_context="value"
        )
        
        # Test tool permission checking
        tool_args = {"arg1": "value1", "arg2": "value2"}
        result = await check_tool_permission(user, "test_tool", tool_args)
        assert result is True
        mock_provider.check_tool_permission.assert_called_with(user, "test_tool", tool_args)
        
        # Clean up
        set_auth_provider(None)
