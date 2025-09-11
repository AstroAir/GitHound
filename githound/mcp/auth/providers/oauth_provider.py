"""Full OAuth 2.0 authorization server implementation."""

import hashlib
import logging
import os
import secrets
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from ...models import User
from .base import AuthProvider, TokenInfo

logger = logging.getLogger(__name__)


@dataclass
class OAuthClient:
    """OAuth client registration."""

    client_id: str
    client_secret: str
    client_name: str
    redirect_uris: list[str]
    grant_types: list[str]
    response_types: list[str]
    scope: str
    created_at: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AuthorizationCode:
    """Authorization code data."""

    code: str
    client_id: str
    user_id: str
    redirect_uri: str
    scope: str
    expires_at: int
    code_challenge: str | None = None
    code_challenge_method: str | None = None


@dataclass
class AccessToken:
    """Access token data."""

    token: str
    client_id: str
    user_id: str
    scope: str
    expires_at: int
    refresh_token: str | None = None


class UserStore:
    """Abstract user storage interface."""

    async def get_user(self, user_id: str) -> User | None:
        """Get user by ID."""
        raise NotImplementedError

    async def authenticate_user(self, username: str, password: str) -> User | None:
        """Authenticate user with username/password."""
        raise NotImplementedError

    async def create_user(self, username: str, password: str, **kwargs: Any) -> User:
        """Create a new user."""
        raise NotImplementedError


class ClientStore:
    """Abstract client storage interface."""

    async def get_client(self, client_id: str) -> OAuthClient | None:
        """Get client by ID."""
        raise NotImplementedError

    async def create_client(self, client_metadata: dict[str, Any]) -> OAuthClient:
        """Create a new client."""
        raise NotImplementedError

    async def validate_redirect_uri(self, client_id: str, redirect_uri: str) -> bool:
        """Validate redirect URI for client."""
        raise NotImplementedError


class MemoryUserStore(UserStore):
    """In-memory user store for development/testing."""

    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._credentials: dict[str, str] = {}  # username -> password hash

    def _hash_password(self, password: str) -> str:
        """Hash password with salt."""
        salt = secrets.token_hex(16)
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return hash_bytes.hex() + ":" + salt

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        try:
            hash_part, salt = hashed.split(":", 1)
            hash_bytes = hashlib.pbkdf2_hmac(
                'sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
            return hash_bytes.hex() == hash_part
        except ValueError:
            return False

    async def get_user(self, user_id: str) -> User | None:
        """Get user by ID."""
        return self._users.get(user_id)

    async def authenticate_user(self, username: str, password: str) -> User | None:
        """Authenticate user with username/password."""
        if username not in self._credentials:
            return None

        if not self._verify_password(password, self._credentials[username]):
            return None

        # Find user by username
        for user in self._users.values():
            if user.username == username:
                return user

        return None

    async def create_user(self, username: str, password: str, **kwargs: Any) -> User:
        """Create a new user."""
        user_id = str(uuid.uuid4())
        user = User(
            username=username,
            role=kwargs.get("role", "user"),
            permissions=kwargs.get("permissions", [])
        )

        self._users[user_id] = user
        self._credentials[username] = self._hash_password(password)

        return user


class MemoryClientStore(ClientStore):
    """In-memory client store for development/testing."""

    def __init__(self) -> None:
        self._clients: dict[str, OAuthClient] = {}

    async def get_client(self, client_id: str) -> OAuthClient | None:
        """Get client by ID."""
        return self._clients.get(client_id)

    async def create_client(self, client_metadata: dict[str, Any]) -> OAuthClient:
        """Create a new client."""
        client_id = str(uuid.uuid4())
        client_secret = secrets.token_urlsafe(32)

        client = OAuthClient(
            client_id=client_id,
            client_secret=client_secret,
            client_name=client_metadata.get("client_name", "OAuth Client"),
            redirect_uris=client_metadata.get("redirect_uris", []),
            grant_types=client_metadata.get(
                "grant_types", ["authorization_code"]),
            response_types=client_metadata.get("response_types", ["code"]),
            scope=client_metadata.get("scope", "openid profile email"),
            created_at=int(time.time())
        )

        self._clients[client_id] = client
        return client

    async def validate_redirect_uri(self, client_id: str, redirect_uri: str) -> bool:
        """Validate redirect URI for client."""
        client = await self.get_client(client_id)
        if not client:
            return False

        return redirect_uri in client.redirect_uris


class OAuthProvider(AuthProvider):
    """
    Full OAuth 2.0 authorization server implementation.

    This provides a complete OAuth server with authorization endpoints,
    token management, and user authentication.
    """

    def __init__(
        self,
        base_url: str,
        user_store: UserStore | None = None,
        client_store: ClientStore | None = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize OAuth provider.

        Args:
            base_url: Base URL for OAuth endpoints
            user_store: User storage implementation
            client_store: Client storage implementation
        """
        super().__init__(**kwargs)
        self.base_url = base_url.rstrip("/")
        self.user_store = user_store or MemoryUserStore()
        self.client_store = client_store or MemoryClientStore()

        # In-memory stores for codes and tokens (use Redis in production)
        self._authorization_codes: dict[str, AuthorizationCode] = {}
        self._access_tokens: dict[str, AccessToken] = {}

        # Token expiry times (in seconds)
        self.code_expiry = 600  # 10 minutes
        self.token_expiry = 3600  # 1 hour

    def _load_from_environment(self) -> None:
        """Load OAuth provider configuration from environment variables."""
        prefix = "FASTMCP_SERVER_AUTH_OAUTH_"

        if not hasattr(self, 'base_url'):
            self.base_url = os.getenv(
                f"{prefix}BASE_URL", "http://localhost:8000")

        self.code_expiry = int(os.getenv(f"{prefix}CODE_EXPIRY", "600"))
        self.token_expiry = int(os.getenv(f"{prefix}TOKEN_EXPIRY", "3600"))

    async def validate_token(self, token: str) -> TokenInfo | None:
        """
        Validate access token and extract user information.

        Args:
            token: Access token to validate

        Returns:
            TokenInfo if valid, None otherwise
        """
        # Remove Bearer prefix if present
        if token.startswith("Bearer "):
            token = token[7:]

        # Find token in store
        token_data = self._access_tokens.get(token)
        if not token_data:
            return None

        # Check expiry
        if time.time() > token_data.expires_at:
            del self._access_tokens[token]
            return None

        # Get user information
        user = await self.user_store.get_user(token_data.user_id)
        if not user:
            return None

        return TokenInfo(
            user_id=token_data.user_id,
            username=user.username,
            email=getattr(user, 'email', None),
            roles=[user.role],
            permissions=user.permissions,
            expires_at=token_data.expires_at,
            issuer=self.base_url,
            audience=token_data.client_id
        )

    def get_oauth_metadata(self) -> dict[str, Any]:
        """Get OAuth 2.0 metadata."""
        return {
            "issuer": self.base_url,
            "authorization_endpoint": f"{self.base_url}/oauth/authorize",
            "token_endpoint": f"{self.base_url}/oauth/token",
            "userinfo_endpoint": f"{self.base_url}/oauth/userinfo",
            "jwks_uri": f"{self.base_url}/.well-known/jwks.json",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "scopes_supported": ["openid", "profile", "email"],
            "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
            "dynamic_client_registration_endpoint": f"{self.base_url}/oauth/register"
        }

    def supports_dynamic_client_registration(self) -> bool:
        """OAuth provider supports DCR."""
        return True
