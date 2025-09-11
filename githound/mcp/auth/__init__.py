"""Authentication module for GitHound MCP server."""

from .providers import (
    EUNOMIA_AVAILABLE,
    PERMIT_AVAILABLE,
    AuthProvider,
    GitHubProvider,
    GoogleProvider,
    JWTVerifier,
    OAuthProvider,
    OAuthProxy,
)

# Import authorization providers if available
if EUNOMIA_AVAILABLE:
    from .providers import EunomiaAuthorizationProvider

if PERMIT_AVAILABLE:
    from .providers import PermitAuthorizationProvider

__all__ = [
    "AuthProvider",
    "JWTVerifier",
    "OAuthProxy",
    "OAuthProvider",
    "GitHubProvider",
    "GoogleProvider",
    "EUNOMIA_AVAILABLE",
    "PERMIT_AVAILABLE",
]

# Add authorization providers to exports if available
if EUNOMIA_AVAILABLE:
    __all__.append("EunomiaAuthorizationProvider")

if PERMIT_AVAILABLE:
    __all__.append("PermitAuthorizationProvider")
