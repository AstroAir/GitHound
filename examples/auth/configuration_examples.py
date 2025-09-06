#!/usr/bin/env python3
"""Examples of how to configure OAuth authentication for GitHound MCP server."""

import os
from typing import Dict, Any


def setup_github_oauth() -> Dict[str, str]:
    """
    Example configuration for GitHub OAuth.
    
    To use GitHub OAuth:
    1. Create a GitHub OAuth App at https://github.com/settings/applications/new
    2. Set the authorization callback URL to: http://your-server.com/oauth/callback
    3. Copy the Client ID and Client Secret
    4. Set these environment variables
    
    Returns:
        Dictionary of environment variables to set
    """
    return {
        "FASTMCP_SERVER_AUTH": "githound.mcp.auth.providers.github.GitHubProvider",
        "FASTMCP_SERVER_AUTH_GITHUB_CLIENT_ID": "Ov23li...",  # Your GitHub OAuth App ID
        "FASTMCP_SERVER_AUTH_GITHUB_CLIENT_SECRET": "github_pat_...",  # Your GitHub OAuth App Secret
        "FASTMCP_SERVER_BASE_URL": "http://localhost:8000",  # Your MCP server URL
        "FASTMCP_SERVER_ENABLE_AUTH": "true"
    }


def setup_google_oauth() -> Dict[str, str]:
    """
    Example configuration for Google OAuth.
    
    To use Google OAuth:
    1. Create a project in Google Cloud Console
    2. Enable the Google+ API
    3. Create OAuth 2.0 credentials
    4. Add your server's callback URL: http://your-server.com/oauth/callback
    5. Copy the Client ID and Client Secret
    6. Set these environment variables
    
    Returns:
        Dictionary of environment variables to set
    """
    return {
        "FASTMCP_SERVER_AUTH": "githound.mcp.auth.providers.google.GoogleProvider",
        "FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID": "123456.apps.googleusercontent.com",
        "FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET": "GOCSPX-...",
        "FASTMCP_SERVER_BASE_URL": "http://localhost:8000",
        "FASTMCP_SERVER_ENABLE_AUTH": "true"
    }


def setup_jwt_verifier() -> Dict[str, str]:
    """
    Example configuration for JWT token verification.
    
    To use JWT verification:
    1. Set up your JWT issuer (auth server)
    2. Configure JWKS endpoint or static secret
    3. Set these environment variables
    
    Returns:
        Dictionary of environment variables to set
    """
    return {
        "FASTMCP_SERVER_AUTH": "githound.mcp.auth.providers.jwt.JWTVerifier",
        "FASTMCP_SERVER_AUTH_JWKS_URI": "https://your-auth-server.com/.well-known/jwks.json",
        "FASTMCP_SERVER_AUTH_ISSUER": "your-issuer",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "githound-mcp",
        "FASTMCP_SERVER_ENABLE_AUTH": "true"
    }


def setup_static_jwt_verifier() -> Dict[str, str]:
    """
    Example configuration for static JWT verification (for testing).
    
    WARNING: Only use this for development/testing!
    In production, use proper JWKS-based verification.
    
    Returns:
        Dictionary of environment variables to set
    """
    return {
        "FASTMCP_SERVER_AUTH": "githound.mcp.auth.providers.jwt.StaticJWTVerifier",
        "FASTMCP_SERVER_AUTH_SECRET_KEY": "your-secret-key-here",
        "FASTMCP_SERVER_AUTH_ISSUER": "your-issuer",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "githound-mcp",
        "FASTMCP_SERVER_ENABLE_AUTH": "true"
    }


def setup_oauth_proxy() -> Dict[str, str]:
    """
    Example configuration for custom OAuth provider proxy.
    
    To use OAuth proxy:
    1. Set up your OAuth provider endpoints
    2. Register your application with the OAuth provider
    3. Set these environment variables
    
    Returns:
        Dictionary of environment variables to set
    """
    return {
        "FASTMCP_SERVER_AUTH": "githound.mcp.auth.providers.oauth_proxy.OAuthProxy",
        "FASTMCP_SERVER_AUTH_CLIENT_ID": "your-client-id",
        "FASTMCP_SERVER_AUTH_CLIENT_SECRET": "your-client-secret",
        "FASTMCP_SERVER_AUTH_AUTHORIZATION_ENDPOINT": "https://auth.example.com/oauth/authorize",
        "FASTMCP_SERVER_AUTH_TOKEN_ENDPOINT": "https://auth.example.com/oauth/token",
        "FASTMCP_SERVER_AUTH_USERINFO_ENDPOINT": "https://auth.example.com/oauth/userinfo",
        "FASTMCP_SERVER_BASE_URL": "http://localhost:8000",
        "FASTMCP_SERVER_ENABLE_AUTH": "true"
    }


def setup_eunomia_authorization() -> Dict[str, str]:
    """
    Example configuration for Eunomia authorization integration.
    
    To use Eunomia authorization:
    1. Install eunomia-mcp: pip install eunomia-mcp
    2. Set up your base authentication provider (JWT, GitHub, etc.)
    3. Add these environment variables
    
    Returns:
        Dictionary of environment variables to set
    """
    return {
        # Base authentication (example with JWT)
        "FASTMCP_SERVER_AUTH": "githound.mcp.auth.providers.jwt.JWTVerifier",
        "FASTMCP_SERVER_AUTH_JWKS_URI": "https://your-auth-server.com/.well-known/jwks.json",
        "FASTMCP_SERVER_AUTH_ISSUER": "your-issuer",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "githound-mcp",
        
        # Eunomia authorization
        "EUNOMIA_ENABLE": "true",
        "EUNOMIA_POLICY_FILE": "githound_policies.json",
        "EUNOMIA_SERVER_NAME": "githound-mcp",
        "EUNOMIA_ENABLE_AUDIT_LOGGING": "true",
        "EUNOMIA_BYPASS_METHODS": '["initialize", "ping"]',
        
        "FASTMCP_SERVER_ENABLE_AUTH": "true"
    }


def setup_permit_authorization() -> Dict[str, str]:
    """
    Example configuration for Permit.io authorization integration.
    
    To use Permit.io authorization:
    1. Install permit-fastmcp: pip install permit-fastmcp
    2. Sign up at https://permit.io and get your API key
    3. Set up your base authentication provider
    4. Add these environment variables
    
    Returns:
        Dictionary of environment variables to set
    """
    return {
        # Base authentication (example with GitHub)
        "FASTMCP_SERVER_AUTH": "githound.mcp.auth.providers.github.GitHubProvider",
        "FASTMCP_SERVER_AUTH_GITHUB_CLIENT_ID": "your-github-client-id",
        "FASTMCP_SERVER_AUTH_GITHUB_CLIENT_SECRET": "your-github-client-secret",
        
        # Permit.io authorization
        "PERMIT_ENABLE": "true",
        "PERMIT_MCP_PERMIT_PDP_URL": "http://localhost:7766",  # or https://cloudpdp.api.permit.io
        "PERMIT_MCP_PERMIT_API_KEY": "your-permit-api-key",
        "PERMIT_MCP_IDENTITY_MODE": "jwt",
        "PERMIT_MCP_IDENTITY_JWT_SECRET": "your-jwt-secret",
        "PERMIT_MCP_ENABLE_AUDIT_LOGGING": "true",
        "PERMIT_MCP_BYPASSED_METHODS": '["initialize", "ping"]',
        
        "FASTMCP_SERVER_BASE_URL": "http://localhost:8000",
        "FASTMCP_SERVER_ENABLE_AUTH": "true"
    }


def setup_combined_authorization() -> Dict[str, str]:
    """
    Example configuration for both Eunomia and Permit.io authorization.
    
    This creates a layered authorization system where both providers
    must grant access for a request to succeed.
    
    Returns:
        Dictionary of environment variables to set
    """
    return {
        # Base authentication
        "FASTMCP_SERVER_AUTH": "githound.mcp.auth.providers.jwt.JWTVerifier",
        "FASTMCP_SERVER_AUTH_JWKS_URI": "https://your-auth-server.com/.well-known/jwks.json",
        "FASTMCP_SERVER_AUTH_ISSUER": "your-issuer",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "githound-mcp",
        
        # Eunomia authorization
        "EUNOMIA_ENABLE": "true",
        "EUNOMIA_POLICY_FILE": "githound_policies.json",
        "EUNOMIA_SERVER_NAME": "githound-mcp",
        "EUNOMIA_ENABLE_AUDIT_LOGGING": "true",
        
        # Permit.io authorization
        "PERMIT_ENABLE": "true",
        "PERMIT_MCP_PERMIT_PDP_URL": "http://localhost:7766",
        "PERMIT_MCP_PERMIT_API_KEY": "your-permit-api-key",
        "PERMIT_MCP_IDENTITY_MODE": "jwt",
        "PERMIT_MCP_IDENTITY_JWT_SECRET": "your-jwt-secret",
        "PERMIT_MCP_ENABLE_AUDIT_LOGGING": "true",
        
        "FASTMCP_SERVER_ENABLE_AUTH": "true"
    }


def apply_configuration(config: Dict[str, str], dry_run: bool = True) -> None:
    """
    Apply a configuration by setting environment variables.
    
    Args:
        config: Dictionary of environment variables to set
        dry_run: If True, only print what would be set (default: True)
    """
    print(f"Configuration: {len(config)} environment variables")
    print("-" * 50)
    
    for key, value in config.items():
        if dry_run:
            # Mask sensitive values for display
            if any(sensitive in key.upper() for sensitive in ['SECRET', 'KEY', 'TOKEN']):
                display_value = value[:8] + '...' if len(value) > 8 else '***'
                print(f"export {key}={display_value}")
            else:
                print(f"export {key}={value}")
        else:
            os.environ[key] = value
            print(f"✓ Set {key}")
    
    if dry_run:
        print("\nTo apply this configuration:")
        print("1. Copy the export commands above")
        print("2. Run them in your shell")
        print("3. Or call apply_configuration(config, dry_run=False)")
    else:
        print(f"\n✓ Applied {len(config)} environment variables")


def main():
    """Demonstrate configuration examples."""
    print("GitHound MCP Server Authentication Configuration Examples")
    print("=" * 60)
    
    examples = {
        "GitHub OAuth": setup_github_oauth,
        "Google OAuth": setup_google_oauth,
        "JWT Verifier": setup_jwt_verifier,
        "Static JWT (Testing)": setup_static_jwt_verifier,
        "OAuth Proxy": setup_oauth_proxy,
        "Eunomia Authorization": setup_eunomia_authorization,
        "Permit.io Authorization": setup_permit_authorization,
        "Combined Authorization": setup_combined_authorization,
    }
    
    for name, setup_func in examples.items():
        print(f"\n{name}:")
        print("-" * len(name))
        config = setup_func()
        apply_configuration(config, dry_run=True)
    
    print("\n" + "=" * 60)
    print("Usage Instructions:")
    print("1. Choose the configuration that matches your needs")
    print("2. Replace placeholder values with your actual credentials")
    print("3. Set the environment variables in your deployment")
    print("4. Restart your GitHound MCP server")
    print("5. Test authentication with your MCP client")
    
    print("\nSecurity Notes:")
    print("- Never commit secrets to version control")
    print("- Use environment variables or secure secret management")
    print("- Rotate credentials regularly")
    print("- Use HTTPS in production")
    print("- Validate redirect URIs carefully")


if __name__ == "__main__":
    main()
