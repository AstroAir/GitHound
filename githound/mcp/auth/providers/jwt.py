"""JWT token verification provider for GitHound MCP server."""

import os
import json
import time
import logging
from typing import Optional, Dict, Any, Union
from urllib.request import urlopen
from urllib.error import URLError

try:
    import jwt
    from jwt import PyJWKClient
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    # Create dummy classes for type checking

    class PyJWKClient:  # type: ignore
        def __init__(self, uri: str) -> None: ...
        def get_signing_key_from_jwt(self, token: str) -> Any: ...

from .base import TokenVerifier, TokenInfo

logger = logging.getLogger(__name__)


class JWTVerifier(TokenVerifier):
    """JWT token verification provider."""

    def __init__(self, jwks_uri: Optional[str] = None, issuer: Optional[str] = None, audience: Optional[str] = None, **kwargs: Any) -> None:
        """
        Initialize JWT verifier.

        Args:
            jwks_uri: URI to fetch JSON Web Key Set
            issuer: Expected token issuer
            audience: Expected token audience
        """
        if not JWT_AVAILABLE:
            raise ImportError(
                "PyJWT is required for JWT verification. Install with: pip install PyJWT[crypto]")

        super().__init__(issuer=issuer, audience=audience, **kwargs)
        self.jwks_uri = jwks_uri
        self.jwks_client: Optional[PyJWKClient]
        if jwks_uri:
            self.jwks_client = PyJWKClient(jwks_uri)
        else:
            self.jwks_client = None
        self._cached_keys: Dict[str, Any] = {}
        self._cache_expiry = 0

    def _load_from_environment(self) -> None:
        """Load JWT configuration from environment variables."""
        prefix = "FASTMCP_SERVER_AUTH_JWT_"

        if not hasattr(self, 'jwks_uri'):
            self.jwks_uri = os.getenv(f"{prefix}JWKS_URI")
        if not hasattr(self, 'issuer'):
            self.issuer = os.getenv(f"{prefix}ISSUER")
        if not hasattr(self, 'audience'):
            self.audience = os.getenv(f"{prefix}AUDIENCE")

        # Validate required configuration
        if not all([self.jwks_uri, self.issuer, self.audience]):
            missing = []
            if not self.jwks_uri:
                missing.append(f"{prefix}JWKS_URI")
            if not self.issuer:
                missing.append(f"{prefix}ISSUER")
            if not self.audience:
                missing.append(f"{prefix}AUDIENCE")
            raise ValueError(
                f"Missing required JWT configuration: {', '.join(missing)}")

    async def validate_token(self, token: str) -> Optional[TokenInfo]:
        """
        Validate JWT token and extract user information.

        Args:
            token: JWT token to validate

        Returns:
            TokenInfo if valid, None otherwise
        """
        try:
            # Remove Bearer prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            # Check if jwks_client is available
            if not self.jwks_client:
                logger.error("JWKS client not initialized")
                return None

            # Get signing key
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Decode and validate token
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "HS256"],
                issuer=self.issuer,
                audience=self.audience,
                options={"verify_exp": True}
            )

            # Extract user information
            user_id = payload.get("sub")
            username = payload.get(
                "preferred_username") or payload.get("name") or user_id
            email = payload.get("email")
            roles = payload.get("roles", [])
            permissions = payload.get("permissions", [])
            expires_at = payload.get("exp")

            if not user_id:
                logger.warning("JWT token missing 'sub' claim")
                return None

            return TokenInfo(
                user_id=user_id,
                username=username,
                email=email,
                roles=roles if isinstance(roles, list) else [roles],
                permissions=permissions if isinstance(
                    permissions, list) else [permissions],
                expires_at=expires_at,
                issuer=payload.get("iss"),
                audience=payload.get("aud")
            )

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error validating JWT token: {e}")
            return None

    def get_oauth_metadata(self) -> Optional[Dict[str, Any]]:
        """JWT verifier doesn't provide OAuth metadata."""
        return None

    def supports_dynamic_client_registration(self) -> bool:
        """JWT verifier doesn't support DCR."""
        return False


class StaticJWTVerifier(TokenVerifier):
    """JWT verifier with static secret key (for development/testing)."""

    def __init__(self, secret_key: Optional[str] = None, issuer: Optional[str] = None, audience: Optional[str] = None, algorithm: str = "HS256", **kwargs: Any) -> None:
        """
        Initialize static JWT verifier.

        Args:
            secret_key: Secret key for token verification
            issuer: Expected token issuer
            audience: Expected token audience
            algorithm: JWT algorithm (default: HS256)
        """
        if not JWT_AVAILABLE:
            raise ImportError(
                "PyJWT is required for JWT verification. Install with: pip install PyJWT")

        super().__init__(issuer=issuer, audience=audience, **kwargs)
        self.secret_key = secret_key
        self.algorithm = algorithm

    def _load_from_environment(self) -> None:
        """Load static JWT configuration from environment variables."""
        prefix = "FASTMCP_SERVER_AUTH_JWT_"

        if not hasattr(self, 'secret_key'):
            self.secret_key = os.getenv(f"{prefix}SECRET_KEY")
        if not hasattr(self, 'issuer'):
            self.issuer = os.getenv(f"{prefix}ISSUER")
        if not hasattr(self, 'audience'):
            self.audience = os.getenv(f"{prefix}AUDIENCE")
        if not hasattr(self, 'algorithm'):
            self.algorithm = os.getenv(f"{prefix}ALGORITHM", "HS256")

        if not all([self.secret_key, self.issuer, self.audience]):
            missing = []
            if not self.secret_key:
                missing.append(f"{prefix}SECRET_KEY")
            if not self.issuer:
                missing.append(f"{prefix}ISSUER")
            if not self.audience:
                missing.append(f"{prefix}AUDIENCE")
            raise ValueError(
                f"Missing required static JWT configuration: {', '.join(missing)}")

    async def validate_token(self, token: str) -> Optional[TokenInfo]:
        """
        Validate JWT token with static secret.

        Args:
            token: JWT token to validate

        Returns:
            TokenInfo if valid, None otherwise
        """
        try:
            # Remove Bearer prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            # Check that secret_key is available
            if not self.secret_key:
                return None

            # Decode and validate token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience,
                options={"verify_exp": True}
            )

            # Extract user information
            user_id = payload.get("sub")
            username = payload.get(
                "preferred_username") or payload.get("name") or user_id
            email = payload.get("email")
            roles = payload.get("roles", [])
            permissions = payload.get("permissions", [])
            expires_at = payload.get("exp")

            if not user_id:
                logger.warning("JWT token missing 'sub' claim")
                return None

            return TokenInfo(
                user_id=user_id,
                username=username,
                email=email,
                roles=roles if isinstance(roles, list) else [roles],
                permissions=permissions if isinstance(
                    permissions, list) else [permissions],
                expires_at=expires_at,
                issuer=payload.get("iss"),
                audience=payload.get("aud")
            )

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error validating JWT token: {e}")
            return None
