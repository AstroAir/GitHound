"""Authentication providers for GitHound MCP server."""

from .base import AuthProvider
from .jwt import JWTVerifier
from .oauth_proxy import OAuthProxy
from .oauth_provider import OAuthProvider
from .github import GitHubProvider
from .google import GoogleProvider

# Optional authorization providers
try:
    from .eunomia import EunomiaAuthorizationProvider
    EUNOMIA_AVAILABLE = True
except ImportError:
    EunomiaAuthorizationProvider = None
    EUNOMIA_AVAILABLE = False

try:
    from .permit import PermitAuthorizationProvider
    PERMIT_AVAILABLE = True
except ImportError:
    PermitAuthorizationProvider = None
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
