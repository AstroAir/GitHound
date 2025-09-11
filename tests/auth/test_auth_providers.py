"""Tests for GitHound MCP server authentication providers."""

import os
import json
import pytest
import asyncio
from typing import Optional
from unittest.mock import patch, MagicMock, AsyncMock

from githound.mcp.auth.providers.base import AuthProvider, AuthResult, TokenInfo
from githound.mcp.models import User


@pytest.fixture
def mock_http_session() -> None:
    """Mock aiohttp ClientSession for testing HTTP requests."""
    with patch('aiohttp.ClientSession') as mock_session:
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
                secret_key="test-secret-key",
                issuer="test-issuer",
                audience="test-audience"
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
            from githound.mcp.auth.providers.jwt import StaticJWTVerifier
            import jwt
            import datetime
            
            secret_key = "test-secret-key"
            verifier = StaticJWTVerifier(
                secret_key=secret_key,
                issuer="test-issuer",
                audience="test-audience"
            )
            
            # Create a valid JWT token
            payload = {
                "sub": "testuser",
                "name": "Test User",
                "role": "user",
                "permissions": ["read", "search"],
                "iss": "test-issuer",
                "aud": "test-audience",
                "exp": int(datetime.datetime.utcnow().timestamp()) + 3600,
                "iat": int(datetime.datetime.utcnow().timestamp())
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
            base_url="http://localhost:8000"
        )
        
        assert provider.client_id = = "test-client-id"
        assert provider.client_secret = = "test-client-secret"
        assert provider.base_url = = "http://localhost:8000"
    
    def test_github_oauth_metadata(self) -> None:
        """Test GitHub OAuth metadata generation."""
        from githound.mcp.auth.providers.github import GitHubProvider
        
        provider = GitHubProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000"
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
            client_secret="test-client-secret"
        )
        
        assert provider.supports_dynamic_client_registration() is True
    
    @pytest.mark.asyncio
    async def test_github_authentication_flow(self) -> None:
        """Test GitHub authentication flow with mocked responses."""
        from githound.mcp.auth.providers.github import GitHubProvider
        
        provider = GitHubProvider(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        
        # Mock the HTTP client responses
        mock_token_response = {
            "access_token": "test-access-token",
            "token_type": "bearer",
            "scope": "user:email"
        }
        
        mock_user_response = {
            "login": "testuser",
            "name": "Test User",
            "email": "test@example.com",
            "id": 12345
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Mock token exchange
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_token_response)
            mock_post.return_value.__aenter__.return_value.status = 200
            
            # Mock user info
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_user_response)
            mock_get.return_value.__aenter__.return_value.status = 200
            
            # Test authentication with authorization code
            result = await provider.authenticate("test-auth-code")
            
            assert result.success is True
            assert result.user.username == "testuser"
            assert result.user.email == "test@example.com"


class TestGoogleProvider:
    """Test Google OAuth provider."""
    
    def test_google_provider_creation(self) -> None:
        """Test Google provider creation and configuration."""
        from githound.mcp.auth.providers.google import GoogleProvider
        
        provider = GoogleProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000"
        )
        
        assert provider.client_id = = "test-client-id"
        assert provider.client_secret = = "test-client-secret"
        assert provider.base_url = = "http://localhost:8000"
    
    def test_google_oauth_metadata(self) -> None:
        """Test Google OAuth metadata generation."""
        from githound.mcp.auth.providers.google import GoogleProvider
        
        provider = GoogleProvider(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000"
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
            client_secret="test-client-secret"
        )
        
        assert provider.supports_dynamic_client_registration() is True
    
    @pytest.mark.asyncio
    async def test_google_authentication_flow(self) -> None:
        """Test Google authentication flow with mocked responses."""
        from githound.mcp.auth.providers.google import GoogleProvider
        
        provider = GoogleProvider(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        
        # Mock the HTTP client responses
        mock_token_response = {
            "access_token": "test-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "id_token": "test-id-token"
        }
        
        mock_user_response = {
            "sub": "12345",
            "name": "Test User",
            "email": "test@example.com",
            "picture": "https://example.com/avatar.jpg"
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Mock token exchange
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_token_response)
            mock_post.return_value.__aenter__.return_value.status = 200
            
            # Mock user info
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_user_response)
            mock_get.return_value.__aenter__.return_value.status = 200
            
            # Test authentication with authorization code
            result = await provider.authenticate("test-auth-code")
            
            assert result.success is True
            assert result.user.username == "test@example.com"  # Google uses email as username
            assert result.user.email == "test@example.com"


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
            userinfo_endpoint="https://example.com/oauth/userinfo"
        )
        
        assert proxy.client_id = = "test-client-id"
        assert proxy.client_secret = = "test-client-secret"
        assert proxy.authorization_endpoint = = "https://example.com/oauth/authorize"
    
    def test_oauth_proxy_metadata(self) -> None:
        """Test OAuth proxy metadata generation."""
        from githound.mcp.auth.providers.oauth_proxy import OAuthProxy
        
        proxy = OAuthProxy(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url="http://localhost:8000",
            authorization_endpoint="https://example.com/oauth/authorize",
            token_endpoint="https://example.com/oauth/token",
            userinfo_endpoint="https://example.com/oauth/userinfo"
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
            authorization_endpoint="https://example.com/oauth/authorize",
            token_endpoint="https://example.com/oauth/token"
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
            userinfo_endpoint="https://example.com/oauth/userinfo"
        )
        
        client_metadata = {
            "client_name": "Test Client",
            "redirect_uris": ["http://localhost:3000/callback"]
        }
        
        mock_response = {
            "client_id": "generated-client-id",
            "client_secret": "generated-client-secret",
            "client_id_issued_at": 1234567890,
            "client_secret_expires_at": 0
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aenter__.return_value.status = 201
            
            registration = await proxy.register_client(client_metadata)
            
            assert "client_id" in registration
            assert "client_secret" in registration
            assert registration["client_id"] == "generated-client-id"
