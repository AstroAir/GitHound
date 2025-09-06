"""Tests for OAuth authentication providers (GitHub, Google, OAuth Proxy)."""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from typing import Dict, Any

from githound.mcp.auth.providers.base import AuthResult


class TestGitHubProvider:
    """Test GitHub OAuth provider."""
    
    def test_github_provider_creation(self):
        """Test GitHub provider creation and configuration."""
        from githound.mcp.auth.providers.github import GitHubProvider
        
        provider = GitHubProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000"
        )
        
        assert provider.client_id == "test-client-id"
        assert provider.client_secret == "test-client-secret"
        assert provider.base_url == "http://localhost:8000"
    
    def test_github_oauth_metadata(self):
        """Test GitHub OAuth metadata generation."""
        from githound.mcp.auth.providers.github import GitHubProvider
        
        provider = GitHubProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000"
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
    
    def test_github_dcr_support(self):
        """Test GitHub Dynamic Client Registration support."""
        from githound.mcp.auth.providers.github import GitHubProvider
        
        provider = GitHubProvider(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        
        assert provider.supports_dynamic_client_registration() is True
    
    @pytest.mark.asyncio
    async def test_github_authentication_success(self):
        """Test successful GitHub authentication flow."""
        from githound.mcp.auth.providers.github import GitHubProvider
        
        provider = GitHubProvider(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        
        # Mock successful token exchange
        mock_token_response = {
            "access_token": "gho_test_token",
            "token_type": "bearer",
            "scope": "user:email"
        }
        
        # Mock successful user info
        mock_user_response = {
            "login": "testuser",
            "name": "Test User",
            "email": "test@example.com",
            "id": 12345,
            "avatar_url": "https://github.com/images/error/testuser_happy.gif"
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_instance
            
            # Mock POST request for token exchange
            mock_post_response = AsyncMock()
            mock_post_response.json.return_value = mock_token_response
            mock_post_response.status = 200
            mock_instance.post.return_value.__aenter__.return_value = mock_post_response
            
            # Mock GET request for user info
            mock_get_response = AsyncMock()
            mock_get_response.json.return_value = mock_user_response
            mock_get_response.status = 200
            mock_instance.get.return_value.__aenter__.return_value = mock_get_response
            
            # Test authentication
            result = await provider.authenticate("test-auth-code")
            
            assert result.success is True
            assert result.user.username == "testuser"
            assert result.user.email == "test@example.com"
            assert result.user.role == "user"  # Default role
            assert result.token == "gho_test_token"
    
    @pytest.mark.asyncio
    async def test_github_authentication_token_failure(self):
        """Test GitHub authentication with token exchange failure."""
        from githound.mcp.auth.providers.github import GitHubProvider
        
        provider = GitHubProvider(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_instance
            
            # Mock failed token exchange
            mock_post_response = AsyncMock()
            mock_post_response.status = 400
            mock_post_response.text.return_value = "Bad Request"
            mock_instance.post.return_value.__aenter__.return_value = mock_post_response
            
            # Test authentication
            result = await provider.authenticate("invalid-auth-code")
            
            assert result.success is False
            assert "token exchange failed" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_github_client_registration(self):
        """Test GitHub client registration."""
        from githound.mcp.auth.providers.github import GitHubProvider
        
        provider = GitHubProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000"
        )
        
        client_metadata = {
            "client_name": "Test GitHound Client",
            "redirect_uris": ["http://localhost:3000/callback"]
        }
        
        mock_registration_response = {
            "client_id": "new-client-id",
            "client_secret": "new-client-secret",
            "client_id_issued_at": 1234567890,
            "client_secret_expires_at": 0
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_instance
            
            mock_post_response = AsyncMock()
            mock_post_response.json.return_value = mock_registration_response
            mock_post_response.status = 201
            mock_instance.post.return_value.__aenter__.return_value = mock_post_response
            
            registration = await provider.register_client(client_metadata)
            
            assert registration["client_id"] == "new-client-id"
            assert registration["client_secret"] == "new-client-secret"


class TestGoogleProvider:
    """Test Google OAuth provider."""
    
    def test_google_provider_creation(self):
        """Test Google provider creation and configuration."""
        from githound.mcp.auth.providers.google import GoogleProvider
        
        provider = GoogleProvider(
            client_id="test-client-id.apps.googleusercontent.com",
            client_secret="test-client-secret",
            base_url="http://localhost:8000"
        )
        
        assert provider.client_id == "test-client-id.apps.googleusercontent.com"
        assert provider.client_secret == "test-client-secret"
        assert provider.base_url == "http://localhost:8000"
    
    def test_google_oauth_metadata(self):
        """Test Google OAuth metadata generation."""
        from githound.mcp.auth.providers.google import GoogleProvider
        
        provider = GoogleProvider(
            client_id="test-client-id.apps.googleusercontent.com",
            client_secret="test-client-secret",
            base_url="http://localhost:8000"
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
    async def test_google_authentication_success(self):
        """Test successful Google authentication flow."""
        from githound.mcp.auth.providers.google import GoogleProvider
        
        provider = GoogleProvider(
            client_id="test-client-id.apps.googleusercontent.com",
            client_secret="test-client-secret"
        )
        
        # Mock successful token exchange
        mock_token_response = {
            "access_token": "ya29.test_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "id_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.test.signature"
        }
        
        # Mock successful user info
        mock_user_response = {
            "sub": "123456789",
            "name": "Test User",
            "email": "test@gmail.com",
            "picture": "https://lh3.googleusercontent.com/test",
            "email_verified": True
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_instance
            
            # Mock POST request for token exchange
            mock_post_response = AsyncMock()
            mock_post_response.json.return_value = mock_token_response
            mock_post_response.status = 200
            mock_instance.post.return_value.__aenter__.return_value = mock_post_response
            
            # Mock GET request for user info
            mock_get_response = AsyncMock()
            mock_get_response.json.return_value = mock_user_response
            mock_get_response.status = 200
            mock_instance.get.return_value.__aenter__.return_value = mock_get_response
            
            # Test authentication
            result = await provider.authenticate("test-auth-code")
            
            assert result.success is True
            assert result.user.username == "test@gmail.com"  # Google uses email as username
            assert result.user.email == "test@gmail.com"
            assert result.user.role == "user"  # Default role
            assert result.token == "ya29.test_token"


class TestOAuthProxy:
    """Test OAuth proxy functionality."""
    
    def test_oauth_proxy_creation(self):
        """Test OAuth proxy creation and configuration."""
        from githound.mcp.auth.providers.oauth_proxy import OAuthProxy
        
        proxy = OAuthProxy(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
            authorization_endpoint="https://auth.example.com/oauth/authorize",
            token_endpoint="https://auth.example.com/oauth/token",
            userinfo_endpoint="https://auth.example.com/oauth/userinfo"
        )
        
        assert proxy.client_id == "test-client-id"
        assert proxy.client_secret == "test-client-secret"
        assert proxy.authorization_endpoint == "https://auth.example.com/oauth/authorize"
        assert proxy.token_endpoint == "https://auth.example.com/oauth/token"
        assert proxy.userinfo_endpoint == "https://auth.example.com/oauth/userinfo"
    
    def test_oauth_proxy_metadata(self):
        """Test OAuth proxy metadata generation."""
        from githound.mcp.auth.providers.oauth_proxy import OAuthProxy
        
        proxy = OAuthProxy(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
            authorization_endpoint="https://auth.example.com/oauth/authorize",
            token_endpoint="https://auth.example.com/oauth/token",
            userinfo_endpoint="https://auth.example.com/oauth/userinfo"
        )
        
        metadata = proxy.get_oauth_metadata()
        assert metadata is not None
        assert metadata["client_id"] == "test-client-id"
        
        # URLs should be proxied through the base URL
        assert metadata["authorization_endpoint"] == "http://localhost:8000/oauth/authorize"
        assert metadata["token_endpoint"] == "http://localhost:8000/oauth/token"
    
    @pytest.mark.asyncio
    async def test_oauth_proxy_client_registration(self):
        """Test OAuth proxy client registration."""
        from githound.mcp.auth.providers.oauth_proxy import OAuthProxy
        
        proxy = OAuthProxy(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
            authorization_endpoint="https://auth.example.com/oauth/authorize",
            token_endpoint="https://auth.example.com/oauth/token",
            userinfo_endpoint="https://auth.example.com/oauth/userinfo"
        )
        
        client_metadata = {
            "client_name": "Test Client",
            "redirect_uris": ["http://localhost:3000/callback"],
            "scope": "read write"
        }
        
        mock_response = {
            "client_id": "generated-client-id",
            "client_secret": "generated-client-secret",
            "client_id_issued_at": 1234567890,
            "client_secret_expires_at": 0
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_instance
            
            mock_post_response = AsyncMock()
            mock_post_response.json.return_value = mock_response
            mock_post_response.status = 201
            mock_instance.post.return_value.__aenter__.return_value = mock_post_response
            
            registration = await proxy.register_client(client_metadata)
            
            assert registration["client_id"] == "generated-client-id"
            assert registration["client_secret"] == "generated-client-secret"
    
    @pytest.mark.asyncio
    async def test_oauth_proxy_authentication(self):
        """Test OAuth proxy authentication flow."""
        from githound.mcp.auth.providers.oauth_proxy import OAuthProxy
        
        proxy = OAuthProxy(
            client_id="test-client-id",
            client_secret="test-client-secret",
            authorization_endpoint="https://auth.example.com/oauth/authorize",
            token_endpoint="https://auth.example.com/oauth/token",
            userinfo_endpoint="https://auth.example.com/oauth/userinfo"
        )
        
        # Mock successful token exchange
        mock_token_response = {
            "access_token": "test-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "read write"
        }
        
        # Mock successful user info
        mock_user_response = {
            "sub": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "name": "Test User"
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_instance
            
            # Mock POST request for token exchange
            mock_post_response = AsyncMock()
            mock_post_response.json.return_value = mock_token_response
            mock_post_response.status = 200
            mock_instance.post.return_value.__aenter__.return_value = mock_post_response
            
            # Mock GET request for user info
            mock_get_response = AsyncMock()
            mock_get_response.json.return_value = mock_user_response
            mock_get_response.status = 200
            mock_instance.get.return_value.__aenter__.return_value = mock_get_response
            
            # Test authentication
            result = await proxy.authenticate("test-auth-code")
            
            assert result.success is True
            assert result.user.username == "testuser"
            assert result.user.email == "test@example.com"
            assert result.token == "test-access-token"
