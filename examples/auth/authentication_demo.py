"""Demo script showing GitHound MCP server OAuth authentication in action."""

import asyncio
import json
import os
import sys
from pathlib import Path

from githound.mcp.auth_manager import set_auth_provider
from githound.mcp.config import get_oauth_discovery_metadata  # [attr-defined]

# Add the project root to the path so we can import GitHound modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def demo_jwt_authentication() -> None:
    """Demonstrate JWT authentication."""
    print("\n" + "=" * 60)
    print("JWT Authentication Demo")
    print("=" * 60)

    try:
        import time

        import jwt

        from githound.mcp.auth.providers.jwt import StaticJWTVerifier

        # Create JWT verifier
        secret_key = "demo-secret-key-12345"
        issuer = "githound-mcp-demo"
        audience = "mcp-client"

        verifier = StaticJWTVerifier(secret_key=secret_key, issuer=issuer, audience=audience)

        set_auth_provider(verifier)

        print(f"✓ Created JWT verifier with issuer: {issuer}")

        # Create a test JWT token
        payload = {
            "sub": "user123",
            "name": "Demo User",
            "email": "demo@example.com",
            "roles": ["user"],
            "permissions": ["read", "write"],
            "iss": issuer,
            "aud": audience,
            "exp": int(time.time()) + 3600,  # Expires in 1 hour
            "iat": int(time.time()),
        }

        token = jwt.encode(payload, secret_key, algorithm="HS256")
        print("✓ Created test JWT token")

        # Test token validation
        token_info = await verifier.validate_token(token)
        if token_info:
            print("✓ Token validation successful")
            print(f"  User ID: {token_info.user_id}")
            print(f"  Username: {token_info.username}")
            print(f"  Roles: {token_info.roles}")
            print(f"  Permissions: {token_info.permissions}")
        else:
            print("✗ Token validation failed")

        # Test authentication
        auth_result = await verifier.authenticate(f"Bearer {token}")
        if auth_result.success:
            print("✓ Authentication successful")
            print(f"  User: {auth_result.user.username}")
            print(f"  Email: {auth_result.user.email}")
            print(f"  Role: {auth_result.user.role}")
        else:
            print(f"✗ Authentication failed: {auth_result.error}")

        # Test with invalid token
        invalid_result = await verifier.authenticate("Bearer invalid-token")
        if not invalid_result.success:
            print("✓ Invalid token correctly rejected")
        else:
            print("✗ Invalid token was accepted (this shouldn't happen)")

    except ImportError as e:
        print(f"⚠ JWT demo skipped (missing dependencies): {e}")
        print("  Install with: pip install PyJWT[crypto]")
    except Exception as e:
        print(f"✗ JWT demo failed: {e}")


async def demo_github_authentication() -> None:
    """Demonstrate GitHub OAuth authentication."""
    print("\n" + "=" * 60)
    print("GitHub OAuth Authentication Demo")
    print("=" * 60)

    try:
        from githound.mcp.auth.providers.github import GitHubProvider

        # Create GitHub provider (using dummy credentials for demo)
        provider = GitHubProvider(
            client_id="demo-client-id",
            client_secret="demo-client-secret",
            base_url="http://localhost:8000",
        )

        set_auth_provider(provider)

        print("✓ Created GitHub OAuth provider")

        # Test OAuth metadata
        metadata = provider.get_oauth_metadata()
        if metadata:
            print("✓ OAuth metadata generated:")
            print(f"  Provider: {metadata.get('provider')}")
            print(f"  Authorization URL: {metadata.get('authorization_endpoint')}")
            print(f"  Token URL: {metadata.get('token_endpoint')}")
            print(f"  Client ID: {metadata.get('client_id')}")
            print(f"  Scopes: {metadata.get('scopes')}")

        # Test DCR support
        if provider.supports_dynamic_client_registration():
            print("✓ Dynamic Client Registration is supported")
        else:
            print("✗ Dynamic Client Registration is not supported")

        print("\nTo use GitHub OAuth in production:")
        print("1. Create a GitHub OAuth App at https://github.com/settings/applications/new")
        print("2. Set the authorization callback URL to: http://your-server.com/oauth/callback")
        print("3. Set environment variables:")
        print("   export FASTMCP_SERVER_AUTH_GITHUB_CLIENT_ID=your-client-id")
        print("   export FASTMCP_SERVER_AUTH_GITHUB_CLIENT_SECRET=your-client-secret")

    except Exception as e:
        print(f"✗ GitHub demo failed: {e}")


async def demo_google_authentication() -> None:
    """Demonstrate Google OAuth authentication."""
    print("\n" + "=" * 60)
    print("Google OAuth Authentication Demo")
    print("=" * 60)

    try:
        from githound.mcp.auth.providers.google import GoogleProvider

        # Create Google provider (using dummy credentials for demo)
        provider = GoogleProvider(
            client_id="demo-client-id.apps.googleusercontent.com",
            client_secret="demo-client-secret",
            base_url="http://localhost:8000",
        )

        set_auth_provider(provider)

        print("✓ Created Google OAuth provider")

        # Test OAuth metadata
        metadata = provider.get_oauth_metadata()
        if metadata:
            print("✓ OAuth metadata generated:")
            print(f"  Provider: {metadata.get('provider')}")
            print(f"  Authorization URL: {metadata.get('authorization_endpoint')}")
            print(f"  Token URL: {metadata.get('token_endpoint')}")
            print(f"  Client ID: {metadata.get('client_id')}")
            print(f"  Scopes: {metadata.get('scopes')}")

        # Test DCR support
        if provider.supports_dynamic_client_registration():
            print("✓ Dynamic Client Registration is supported")
        else:
            print("✗ Dynamic Client Registration is not supported")

        print("\nTo use Google OAuth in production:")
        print("1. Create a Google Cloud project at https://console.cloud.google.com/")
        print("2. Enable the Google+ API")
        print("3. Create OAuth 2.0 credentials")
        print("4. Set the authorized redirect URI to: http://your-server.com/oauth/callback")
        print("5. Set environment variables:")
        print("   export FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID=your-client-id")
        print("   export FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET=your-client-secret")

    except Exception as e:
        print(f"✗ Google demo failed: {e}")


async def demo_oauth_proxy() -> None:
    """Demonstrate OAuth proxy functionality."""
    print("\n" + "=" * 60)
    print("OAuth Proxy Demo")
    print("=" * 60)

    try:
        from githound.mcp.auth.providers.oauth_proxy import OAuthProxy

        # Create OAuth proxy for a custom OAuth provider
        proxy = OAuthProxy(
            client_id="demo-client-id",
            client_secret="demo-client-secret",
            base_url="http://localhost:8000",
            authorization_endpoint="https://auth.example.com/oauth/authorize",
            token_endpoint="https://auth.example.com/oauth/token",
            userinfo_endpoint="https://auth.example.com/oauth/userinfo",
        )

        set_auth_provider(proxy)

        print("✓ Created OAuth proxy")

        # Test OAuth metadata
        metadata = proxy.get_oauth_metadata()
        if metadata:
            print("✓ OAuth metadata generated:")
            print(f"  Authorization URL: {metadata.get('authorization_endpoint')}")
            print(f"  Token URL: {metadata.get('token_endpoint')}")
            print(f"  Client ID: {metadata.get('client_id')}")

        # Test DCR support
        if proxy.supports_dynamic_client_registration():
            print("✓ Dynamic Client Registration is supported")

            # Demo client registration (this would fail with dummy endpoints)
            print("\nClient registration would work with real endpoints:")
            client_metadata = {
                "client_name": "GitHound MCP Server",
                "redirect_uris": ["http://localhost:8000/oauth/callback"],
                "scope": "read write",
                "grant_types": ["authorization_code", "refresh_token"],
            }
            print(f"  Client metadata: {json.dumps(client_metadata, indent=2)}")

        print("\nTo use OAuth proxy in production:")
        print("1. Set up your OAuth provider endpoints")
        print("2. Configure the proxy with real endpoints:")
        print("   - Authorization endpoint")
        print("   - Token endpoint")
        print("   - User info endpoint")
        print("3. Set environment variables for client credentials")

    except Exception as e:
        print(f"✗ OAuth proxy demo failed: {e}")


def demo_environment_configuration() -> None:
    """Demonstrate environment-based configuration."""
    print("\n" + "=" * 60)
    print("Environment Configuration Demo")
    print("=" * 60)

    # Show current environment variables
    auth_vars = {k: v for k, v in os.environ.items() if "AUTH" in k.upper() or "OAUTH" in k.upper()}

    if auth_vars:
        print("Current authentication environment variables:")
        for key, value in auth_vars.items():
            # Mask sensitive values
            if "SECRET" in key.upper() or "KEY" in key.upper():
                masked_value = value[:4] + "*" * (len(value) - 4) if len(value) > 4 else "***"
                print(f"  {key}={masked_value}")
            else:
                print(f"  {key}={value}")
    else:
        print("No authentication environment variables found")

    print("\nExample environment configurations:")

    print("\n1. JWT Authentication:")
    print("   export FASTMCP_SERVER_AUTH=githound.mcp.auth.providers.jwt.JWTVerifier")
    print(
        "   export FASTMCP_SERVER_AUTH_JWKS_URI=https://your-auth-server.com/.well-known/jwks.json"
    )
    print("   export FASTMCP_SERVER_AUTH_ISSUER=your-issuer")
    print("   export FASTMCP_SERVER_AUTH_AUDIENCE=githound-mcp")

    print("\n2. GitHub OAuth:")
    print("   export FASTMCP_SERVER_AUTH=githound.mcp.auth.providers.github.GitHubProvider")
    print("   export FASTMCP_SERVER_AUTH_GITHUB_CLIENT_ID=your-github-client-id")
    print("   export FASTMCP_SERVER_AUTH_GITHUB_CLIENT_SECRET=your-github-client-secret")

    print("\n3. Google OAuth:")
    print("   export FASTMCP_SERVER_AUTH=githound.mcp.auth.providers.google.GoogleProvider")
    print("   export FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID=your-google-client-id")
    print("   export FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET=your-google-client-secret")

    print("\n4. Custom OAuth Proxy:")
    print("   export FASTMCP_SERVER_AUTH=githound.mcp.auth.providers.oauth_proxy.OAuthProxy")
    print("   export FASTMCP_SERVER_AUTH_CLIENT_ID=your-client-id")
    print("   export FASTMCP_SERVER_AUTH_CLIENT_SECRET=your-client-secret")
    print(
        "   export FASTMCP_SERVER_AUTH_AUTHORIZATION_ENDPOINT=https://auth.example.com/oauth/authorize"
    )
    print("   export FASTMCP_SERVER_AUTH_TOKEN_ENDPOINT=https://auth.example.com/oauth/token")
    print("   export FASTMCP_SERVER_AUTH_USERINFO_ENDPOINT=https://auth.example.com/oauth/userinfo")


def demo_oauth_discovery() -> None:
    """Demonstrate OAuth discovery metadata."""
    print("\n" + "=" * 60)
    print("OAuth Discovery Metadata Demo")
    print("=" * 60)

    try:
        # Get OAuth discovery metadata
        metadata = get_oauth_discovery_metadata()

        if metadata:
            print("✓ OAuth discovery metadata available:")
            print(json.dumps(metadata, indent=2))
        else:
            print("⚠ No OAuth discovery metadata (authentication may be disabled)")
            print("  This is normal if no authentication provider is configured")

        print("\nOAuth discovery metadata is available at:")
        print("  GET /.well-known/oauth-authorization-server")
        print("  GET /.well-known/openid_configuration")

    except Exception as e:
        print(f"✗ OAuth discovery demo failed: {e}")


async def main() -> None:
    """Run all authentication demos."""
    print("GitHound MCP Server Authentication Demos")
    print("=" * 50)

    # Run all demos
    await demo_jwt_authentication()
    await demo_github_authentication()
    await demo_google_authentication()
    await demo_oauth_proxy()
    demo_environment_configuration()
    demo_oauth_discovery()

    print("\n" + "=" * 60)
    print("Demo Summary")
    print("=" * 60)
    print("✓ JWT Authentication: Token-based auth with configurable verification")
    print("✓ GitHub OAuth: OAuth 2.0 flow with GitHub as identity provider")
    print("✓ Google OAuth: OAuth 2.0 flow with Google as identity provider")
    print("✓ OAuth Proxy: Generic OAuth 2.0 proxy for custom providers")
    print("✓ Environment Config: Configuration through environment variables")
    print("✓ OAuth Discovery: Automatic metadata generation for OAuth clients")

    print("\nNext Steps:")
    print("1. Choose an authentication provider that fits your needs")
    print("2. Set up the required credentials and configuration")
    print("3. Set environment variables for your chosen provider")
    print("4. Test authentication with your MCP client")
    print("5. Configure authorization policies if using Eunomia or Permit.io")  # [attr-defined]

    print("\nFor more information, see:")
    print("- examples/authorization/ for authorization examples")
    print("- githound/mcp/auth/README.md for detailed documentation")


if __name__ == "__main__":
    asyncio.run(main())
