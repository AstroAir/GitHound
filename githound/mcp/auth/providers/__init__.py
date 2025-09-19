from typing import Optional

"""Authentication providers for GitHound MCP server."""

from .base import AuthProvider
from .github import GitHubProvider
from .google import GoogleProvider
from .jwt import JWTVerifier
from .oauth_provider import OAuthProvider
from .oauth_proxy import OAuthProxy

# Optional authorization providers
try:
    from .eunomia import EunomiaAuthorizationProvider
    EUNOMIA_AVAILABLE = True
except ImportError:
    EunomiaAuthorizationProvider = None  # type: ignore[misc,assignment]
    EUNOMIA_AVAILABLE = False

try:
    from .permit import PermitAuthorizationProvider
    PERMIT_AVAILABLE = True
except ImportError:
    PermitAuthorizationProvider = None  # type: ignore[misc,assignment]
    PERMIT_AVAILABLE = False

__all__ = [
    "AuthProvider",
    "JWTVerifier",
    "OAuthProxy",
    "OAuthProvider",
    "GitHubProvider",
    "GoogleProvider",
]

# Add authorization providers to __all__ if available
if EUNOMIA_AVAILABLE:
    __all__.append("EunomiaAuthorizationProvider")

if PERMIT_AVAILABLE:
    __all__.append("PermitAuthorizationProvider")
