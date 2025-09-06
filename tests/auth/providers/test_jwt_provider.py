"""Tests for JWT authentication providers."""

import os
import pytest
import jwt
import datetime
from unittest.mock import patch, Mock, AsyncMock
from typing import Optional

from githound.mcp.auth.providers.base import AuthResult, TokenInfo
from githound.mcp.models import User


class TestJWTVerifier:
    """Test JWT token verification with JWKS."""
    
    @pytest.mark.skipif(
        not os.getenv("TEST_JWT", "false").lower() == "true",
        reason="JWT tests require PyJWT package and TEST_JWT=true"
    )
    def test_jwt_verifier_creation(self):
        """Test JWT verifier creation."""
        try:
            from githound.mcp.auth.providers.jwt import JWTVerifier
            
            verifier = JWTVerifier(
                jwks_uri="https://example.com/.well-known/jwks.json",
                issuer="test-issuer",
                audience="test-audience"
            )
            
            assert verifier.jwks_uri == "https://example.com/.well-known/jwks.json"
            assert verifier.issuer == "test-issuer"
            assert verifier.audience == "test-audience"
            
        except ImportError:
            pytest.skip("PyJWT not available")
    
    @pytest.mark.skipif(
        not os.getenv("TEST_JWT", "false").lower() == "true",
        reason="JWT tests require PyJWT package and TEST_JWT=true"
    )
    @pytest.mark.asyncio
    async def test_jwt_verifier_invalid_token(self):
        """Test JWT verifier with invalid token."""
        try:
            from githound.mcp.auth.providers.jwt import JWTVerifier
            
            verifier = JWTVerifier(
                jwks_uri="https://example.com/.well-known/jwks.json",
                issuer="test-issuer",
                audience="test-audience"
            )
            
            # Test with invalid token
            result = await verifier.validate_token("invalid-token")
            assert result is None
            
            # Test authentication with invalid token
            auth_result = await verifier.authenticate("Bearer invalid-token")
            assert auth_result.success is False
            assert auth_result.error is not None
            
        except ImportError:
            pytest.skip("PyJWT not available")
    
    @pytest.mark.skipif(
        not os.getenv("TEST_JWT", "false").lower() == "true",
        reason="JWT tests require PyJWT package and TEST_JWT=true"
    )
    @pytest.mark.asyncio
    async def test_jwt_verifier_with_mocked_jwks(self):
        """Test JWT verifier with mocked JWKS response."""
        try:
            from githound.mcp.auth.providers.jwt import JWTVerifier
            
            # Mock JWKS response
            mock_jwks = {
                "keys": [
                    {
                        "kty": "RSA",
                        "kid": "test-key-id",
                        "use": "sig",
                        "alg": "RS256",
                        "n": "test-modulus",
                        "e": "AQAB"
                    }
                ]
            }
            
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_response = AsyncMock()
                mock_response.json.return_value = mock_jwks
                mock_response.status = 200
                mock_get.return_value.__aenter__.return_value = mock_response
                
                verifier = JWTVerifier(
                    jwks_uri="https://example.com/.well-known/jwks.json",
                    issuer="test-issuer",
                    audience="test-audience"
                )
                
                # This would normally fail due to invalid signature,
                # but we're testing the JWKS fetching mechanism
                result = await verifier.validate_token("invalid.jwt.token")
                assert result is None  # Expected due to invalid token format
                
        except ImportError:
            pytest.skip("PyJWT not available")


class TestStaticJWTVerifier:
    """Test static JWT verification with shared secret."""
    
    @pytest.mark.skipif(
        not os.getenv("TEST_JWT", "false").lower() == "true",
        reason="JWT tests require PyJWT package and TEST_JWT=true"
    )
    def test_static_jwt_verifier_creation(self):
        """Test static JWT verifier creation."""
        try:
            from githound.mcp.auth.providers.jwt import StaticJWTVerifier
            
            verifier = StaticJWTVerifier(
                secret_key="test-secret-key",
                issuer="test-issuer",
                audience="test-audience"
            )
            
            assert verifier.secret_key == "test-secret-key"
            assert verifier.issuer == "test-issuer"
            assert verifier.audience == "test-audience"
            
        except ImportError:
            pytest.skip("PyJWT not available")
    
    @pytest.mark.skipif(
        not os.getenv("TEST_JWT", "false").lower() == "true",
        reason="JWT tests require PyJWT package and TEST_JWT=true"
    )
    @pytest.mark.asyncio
    async def test_static_jwt_verifier_valid_token(self):
        """Test static JWT verifier with valid token."""
        try:
            from githound.mcp.auth.providers.jwt import StaticJWTVerifier
            
            secret_key = "test-secret-key"
            issuer = "test-issuer"
            audience = "test-audience"
            
            verifier = StaticJWTVerifier(
                secret_key=secret_key,
                issuer=issuer,
                audience=audience
            )
            
            # Create a valid JWT token
            payload = {
                "sub": "testuser",
                "name": "Test User",
                "email": "test@example.com",
                "role": "user",
                "permissions": ["read", "search"],
                "iss": issuer,
                "aud": audience,
                "exp": int(datetime.datetime.utcnow().timestamp()) + 3600,
                "iat": int(datetime.datetime.utcnow().timestamp())
            }
            
            token = jwt.encode(payload, secret_key, algorithm="HS256")
            
            # Test token validation
            token_info = await verifier.validate_token(token)
            assert token_info is not None
            assert token_info.username == "testuser"
            assert token_info.user_id == "testuser"
            assert "user" in token_info.roles
            assert "read" in token_info.permissions
            assert "search" in token_info.permissions
            
            # Test authentication
            auth_result = await verifier.authenticate(f"Bearer {token}")
            assert auth_result.success is True
            assert auth_result.user.username == "testuser"
            assert auth_result.user.email == "test@example.com"
            assert auth_result.user.role == "user"
            assert "read" in auth_result.user.permissions
            
        except ImportError:
            pytest.skip("PyJWT not available")
    
    @pytest.mark.skipif(
        not os.getenv("TEST_JWT", "false").lower() == "true",
        reason="JWT tests require PyJWT package and TEST_JWT=true"
    )
    @pytest.mark.asyncio
    async def test_static_jwt_verifier_expired_token(self):
        """Test static JWT verifier with expired token."""
        try:
            from githound.mcp.auth.providers.jwt import StaticJWTVerifier
            
            secret_key = "test-secret-key"
            issuer = "test-issuer"
            audience = "test-audience"
            
            verifier = StaticJWTVerifier(
                secret_key=secret_key,
                issuer=issuer,
                audience=audience
            )
            
            # Create an expired JWT token
            payload = {
                "sub": "testuser",
                "name": "Test User",
                "iss": issuer,
                "aud": audience,
                "exp": int(datetime.datetime.utcnow().timestamp()) - 3600,  # Expired 1 hour ago
                "iat": int(datetime.datetime.utcnow().timestamp()) - 7200   # Issued 2 hours ago
            }
            
            token = jwt.encode(payload, secret_key, algorithm="HS256")
            
            # Test token validation
            token_info = await verifier.validate_token(token)
            assert token_info is None
            
            # Test authentication
            auth_result = await verifier.authenticate(f"Bearer {token}")
            assert auth_result.success is False
            assert "expired" in auth_result.error.lower()
            
        except ImportError:
            pytest.skip("PyJWT not available")
    
    @pytest.mark.skipif(
        not os.getenv("TEST_JWT", "false").lower() == "true",
        reason="JWT tests require PyJWT package and TEST_JWT=true"
    )
    @pytest.mark.asyncio
    async def test_static_jwt_verifier_wrong_issuer(self):
        """Test static JWT verifier with wrong issuer."""
        try:
            from githound.mcp.auth.providers.jwt import StaticJWTVerifier
            
            secret_key = "test-secret-key"
            issuer = "test-issuer"
            audience = "test-audience"
            
            verifier = StaticJWTVerifier(
                secret_key=secret_key,
                issuer=issuer,
                audience=audience
            )
            
            # Create a JWT token with wrong issuer
            payload = {
                "sub": "testuser",
                "name": "Test User",
                "iss": "wrong-issuer",  # Wrong issuer
                "aud": audience,
                "exp": int(datetime.datetime.utcnow().timestamp()) + 3600,
                "iat": int(datetime.datetime.utcnow().timestamp())
            }
            
            token = jwt.encode(payload, secret_key, algorithm="HS256")
            
            # Test token validation
            token_info = await verifier.validate_token(token)
            assert token_info is None
            
            # Test authentication
            auth_result = await verifier.authenticate(f"Bearer {token}")
            assert auth_result.success is False
            assert "issuer" in auth_result.error.lower()
            
        except ImportError:
            pytest.skip("PyJWT not available")
    
    @pytest.mark.skipif(
        not os.getenv("TEST_JWT", "false").lower() == "true",
        reason="JWT tests require PyJWT package and TEST_JWT=true"
    )
    @pytest.mark.asyncio
    async def test_static_jwt_verifier_invalid_signature(self):
        """Test static JWT verifier with invalid signature."""
        try:
            from githound.mcp.auth.providers.jwt import StaticJWTVerifier
            
            secret_key = "test-secret-key"
            wrong_secret = "wrong-secret-key"
            issuer = "test-issuer"
            audience = "test-audience"
            
            verifier = StaticJWTVerifier(
                secret_key=secret_key,
                issuer=issuer,
                audience=audience
            )
            
            # Create a JWT token with wrong secret
            payload = {
                "sub": "testuser",
                "name": "Test User",
                "iss": issuer,
                "aud": audience,
                "exp": int(datetime.datetime.utcnow().timestamp()) + 3600,
                "iat": int(datetime.datetime.utcnow().timestamp())
            }
            
            token = jwt.encode(payload, wrong_secret, algorithm="HS256")
            
            # Test token validation
            token_info = await verifier.validate_token(token)
            assert token_info is None
            
            # Test authentication
            auth_result = await verifier.authenticate(f"Bearer {token}")
            assert auth_result.success is False
            assert "signature" in auth_result.error.lower()
            
        except ImportError:
            pytest.skip("PyJWT not available")
