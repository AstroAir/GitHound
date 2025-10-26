"""Authentication and authorization module for GitHound MCP server.

This module provides comprehensive OAuth 2.0 and JWT authentication support
for the GitHound MCP server, following FastMCP authentication patterns.

Key Features:
    - Multiple authentication providers (JWT, OAuth, GitHub, Google)
    - Optional authorization providers (Eunomia, Permit.io)
    - Dynamic client registration support
    - Rate limiting and security features
    - Environment-based configuration
    - Extensible provider architecture

Authentication Providers:
    - JWTVerifier: Validates JWT tokens from external systems
    - OAuthProxy: Bridges non-DCR OAuth providers with MCP
    - GitHubProvider: GitHub OAuth integration
    - GoogleProvider: Google OAuth integration

Authorization Providers (optional):
    - EunomiaAuthorizationProvider: Policy-based authorization
    - PermitAuthorizationProvider: Fine-grained RBAC/ABAC authorization

The module automatically detects available optional dependencies and
exposes only the providers that can be used in the current environment.
"""

import logging

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

# Import auth functions from the main auth manager module
# Note: Avoiding circular import - these functions are available in githound.mcp.auth_manager
# from githound.mcp.auth_manager import check_rate_limit, get_current_user

# Import authorization providers if available
if EUNOMIA_AVAILABLE:
    pass

if PERMIT_AVAILABLE:
    pass

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

logger = logging.getLogger(__name__)
