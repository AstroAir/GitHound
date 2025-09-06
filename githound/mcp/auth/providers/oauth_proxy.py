"""OAuth proxy provider for non-DCR OAuth providers."""

import os
import json
import uuid
import time
import logging
from typing import Dict, Any, Optional, List, cast
from urllib.parse import urlencode, parse_qs, urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from .base import RemoteAuthProvider, TokenInfo, AuthResult

logger = logging.getLogger(__name__)


class OAuthProxy(RemoteAuthProvider):
    """
    OAuth proxy for providers that don't support Dynamic Client Registration.
    
    This class bridges the gap between MCP's expectation of DCR and traditional
    OAuth providers that require manual app registration.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str,
        authorization_endpoint: str,
        token_endpoint: str,
        userinfo_endpoint: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize OAuth proxy.
        
        Args:
            client_id: OAuth client ID from provider
            client_secret: OAuth client secret from provider
            base_url: Base URL for this MCP server
            authorization_endpoint: Provider's authorization endpoint
            token_endpoint: Provider's token endpoint
            userinfo_endpoint: Provider's userinfo endpoint (optional)
            scopes: Default scopes to request
        """
        super().__init__(base_url=base_url, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorization_endpoint = authorization_endpoint
        self.token_endpoint = token_endpoint
        self.userinfo_endpoint = userinfo_endpoint
        self.scopes = scopes or ["openid", "profile", "email"]
        
        # Store dynamic client registrations
        self._registered_clients: Dict[str, Dict[str, Any]] = {}
    
    def _load_from_environment(self) -> None:
        """Load OAuth proxy configuration from environment variables."""
        # Override in subclasses for provider-specific environment variables
        pass
    
    async def validate_token(self, token: str) -> Optional[TokenInfo]:
        """
        Validate token by calling the provider's userinfo endpoint.
        
        Args:
            token: Access token to validate
            
        Returns:
            TokenInfo if valid, None otherwise
        """
        if not self.userinfo_endpoint:
            logger.warning("No userinfo endpoint configured for token validation")
            return None
        
        try:
            # Remove Bearer prefix if present
            if token.startswith("Bearer "):
                token = token[7:]
            
            # Call userinfo endpoint
            request = Request(
                self.userinfo_endpoint,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            with urlopen(request) as response:
                user_data = json.loads(response.read().decode())
            
            # Extract user information
            user_id = user_data.get("id") or user_data.get("sub")
            username = (
                user_data.get("login") or 
                user_data.get("preferred_username") or 
                user_data.get("name") or 
                user_id
            )
            email = user_data.get("email")
            
            if not user_id:
                logger.warning("Userinfo response missing user ID")
                return None
            
            return TokenInfo(
                user_id=str(user_id),
                username=username,
                email=email,
                roles=["user"],  # Default role
                permissions=[],  # No permissions by default
                expires_at=None,  # Access tokens don't have expiry in userinfo
                issuer=self.issuer,
                audience=self.audience
            )
            
        except (URLError, HTTPError, json.JSONDecodeError) as e:
            logger.warning(f"Error validating token with userinfo endpoint: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error validating token: {e}")
            return None
    
    def get_oauth_metadata(self) -> Dict[str, Any]:
        """Get OAuth 2.0 metadata for MCP clients."""
        return {
            "authorization_endpoint": f"{self.base_url}/oauth/authorize",
            "token_endpoint": f"{self.base_url}/oauth/token",
            "userinfo_endpoint": f"{self.base_url}/oauth/userinfo",
            "issuer": self.base_url,
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "scopes_supported": self.scopes,
            "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
            "dynamic_client_registration_endpoint": f"{self.base_url}/oauth/register"
        }
    
    def supports_dynamic_client_registration(self) -> bool:
        """OAuth proxy presents DCR interface to MCP clients."""
        return True
    
    async def register_client(self, client_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle dynamic client registration request.
        
        Since the upstream provider doesn't support DCR, we accept any
        registration and use our pre-configured credentials.
        
        Args:
            client_metadata: Client registration metadata
            
        Returns:
            Client registration response
        """
        client_id = str(uuid.uuid4())
        client_secret = str(uuid.uuid4())
        
        # Store client registration
        self._registered_clients[client_id] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_name": client_metadata.get("client_name", "MCP Client"),
            "redirect_uris": client_metadata.get("redirect_uris", []),
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "scope": " ".join(self.scopes),
            "created_at": int(time.time())
        }
        
        return self._registered_clients[client_id]
    
    async def handle_authorization(self, params: Dict[str, str]) -> str:
        """
        Handle authorization request by redirecting to upstream provider.
        
        Args:
            params: Authorization request parameters
            
        Returns:
            Redirect URL to upstream provider
        """
        # Validate client
        client_id = params.get("client_id")
        if not client_id or client_id not in self._registered_clients:
            raise ValueError("Invalid client_id")
        
        # Build authorization URL for upstream provider
        auth_params = {
            "client_id": self.client_id,  # Our registered client ID
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": params.get("state", ""),
            "redirect_uri": f"{self.base_url}/oauth/callback"  # Our callback
        }
        
        auth_url = f"{self.authorization_endpoint}?{urlencode(auth_params)}"
        return auth_url
    
    async def handle_token_exchange(self, params: Dict[str, str]) -> Dict[str, Any]:
        """
        Handle token exchange by calling upstream provider.
        
        Args:
            params: Token request parameters
            
        Returns:
            Token response
        """
        # Validate client
        client_id = params.get("client_id")
        if not client_id or client_id not in self._registered_clients:
            raise ValueError("Invalid client_id")
        
        # Exchange authorization code with upstream provider
        token_data = {
            "grant_type": "authorization_code",
            "code": params.get("code"),
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": f"{self.base_url}/oauth/callback"
        }
        
        try:
            request = Request(
                self.token_endpoint,
                data=urlencode(token_data).encode(),
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            with urlopen(request) as response:
                token_response = cast(Dict[str, Any], json.loads(response.read().decode()))

            return token_response
            
        except (URLError, HTTPError, json.JSONDecodeError) as e:
            logger.error(f"Error exchanging token with upstream provider: {e}")
            raise ValueError("Token exchange failed")
    
    async def handle_callback(self, params: Dict[str, str]) -> Dict[str, Any]:
        """
        Handle OAuth callback from upstream provider.
        
        Args:
            params: Callback parameters
            
        Returns:
            Processed callback data
        """
        code = params.get("code")
        state = params.get("state")
        error = params.get("error")
        
        if error:
            return {"error": error, "error_description": params.get("error_description")}
        
        if not code:
            return {"error": "missing_code", "error_description": "Authorization code not provided"}
        
        return {"code": code, "state": state}
