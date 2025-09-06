#!/usr/bin/env python3
"""
Example: GitHound MCP Server with Permit.io Authorization

This example demonstrates how to set up GitHound MCP server with Permit.io
fine-grained authorization. Permit.io provides cloud-native authorization
with RBAC, ABAC, and REBAC capabilities.

Requirements:
    pip install permit-fastmcp

Setup:
    1. Sign up at https://permit.io
    2. Get your API key from the dashboard
    3. Run local PDP: docker run -p 7766:7766 permitio/pdp:latest
    4. Set PERMIT_API_KEY environment variable

Usage:
    export PERMIT_API_KEY=your-api-key
    python permit_example.py
"""

import os
import asyncio
import logging
import jwt
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up environment for Permit.io
os.environ["PERMIT_ENABLE"] = "true"
os.environ["PERMIT_MCP_PERMIT_PDP_URL"] = "http://localhost:7766"
os.environ["PERMIT_MCP_IDENTITY_MODE"] = "jwt"
os.environ["PERMIT_MCP_IDENTITY_JWT_SECRET"] = "demo-secret-key"
os.environ["PERMIT_MCP_ENABLE_AUDIT_LOGGING"] = "true"

# Import GitHound components
from githound.mcp.auth import set_auth_provider, check_permission, check_tool_permission
from githound.mcp.auth.providers import JWTVerifier, PermitAuthorizationProvider
from githound.mcp.models import User


def create_demo_jwt_token(username: str, role: str) -> str:
    """Create a demo JWT token for testing."""
    payload = {
        "sub": username,
        "name": username,
        "role": role,
        "permissions": [],
        "iss": "githound-demo",
        "aud": "mcp-client",
        "exp": int(datetime.datetime.utcnow().timestamp()) + 3600,
        "iat": int(datetime.datetime.utcnow().timestamp())
    }
    
    return jwt.encode(payload, "demo-secret-key", algorithm="HS256")


async def demo_permit_authorization():
    """Demonstrate Permit.io authorization with GitHound."""
    
    print("\n" + "="*60)
    print("GitHound MCP Server - Permit.io Authorization Demo")
    print("="*60)
    
    # Check if API key is set
    api_key = os.getenv("PERMIT_API_KEY")
    if not api_key:
        print("⚠️  PERMIT_API_KEY not set. Using demo mode.")
        print("   For full functionality, set your Permit.io API key:")
        print("   export PERMIT_API_KEY=your-api-key")
        api_key = "demo-api-key"
    
    # Create a JWT verifier for demo
    from githound.mcp.auth.providers.jwt import StaticJWTVerifier
    
    jwt_provider = StaticJWTVerifier(
        secret_key="demo-secret-key",
        issuer="githound-demo",
        audience="mcp-client"
    )
    
    # Wrap with Permit.io authorization
    auth_provider = PermitAuthorizationProvider(
        base_provider=jwt_provider,
        permit_pdp_url="http://localhost:7766",
        permit_api_key=api_key,
        server_name="githound-mcp",
        identity_mode="jwt",
        identity_jwt_secret="demo-secret-key",
        enable_audit_logging=True
    )
    
    # Set as the global auth provider
    set_auth_provider(auth_provider)
    
    print(f"✓ Created Permit.io authorization provider")
    print(f"✓ PDP URL: {auth_provider.get_permit_config().permit_pdp_url}")
    print(f"✓ Identity Mode: {auth_provider.get_permit_config().identity_mode}")
    
    # Create test users with different roles
    test_users = [
        User(username="admin", role="admin", permissions=[]),
        User(username="developer", role="user", permissions=["search", "analyze"]),
        User(username="analyst", role="readonly", permissions=["read"]),
        User(username="intern", role="intern", permissions=[]),
    ]
    
    # Test basic permissions
    test_operations = [
        ("search", "githound-mcp:search"),
        ("analyze", "githound-mcp:blame"),
        ("read", "githound-mcp:repository"),
        ("list", "githound-mcp:tools"),
        ("admin", "githound-mcp:admin"),
    ]
    
    print("\n" + "-"*60)
    print("Basic Permission Test Results:")
    print("-"*60)
    print(f"{'User':<15} {'Role':<12} {'Operation':<10} {'Resource':<20} {'Allowed':<8}")
    print("-"*60)
    
    for user in test_users:
        for operation, resource in test_operations:
            try:
                allowed = await check_permission(user, operation, resource)
                status = "✓ YES" if allowed else "✗ NO"
                print(f"{user.username:<15} {user.role:<12} {operation:<10} {resource:<20} {status:<8}")
            except Exception as e:
                print(f"{user.username:<15} {user.role:<12} {operation:<10} {resource:<20} ERROR")
    
    # Test ABAC (Attribute-Based Access Control) with tool arguments
    print("\n" + "-"*60)
    print("ABAC Tool Permission Test Results:")
    print("-"*60)
    print("Testing conditional access based on tool arguments...")
    
    # Create a user for ABAC testing
    abac_user = User(username="conditional_user", role="user", permissions=["conditional-greet"])
    
    # Test conditional tool with different argument values
    abac_tests = [
        ("conditional-greet", {"name": "Alice", "number": 5}),   # Should be denied (number <= 10)
        ("conditional-greet", {"name": "Bob", "number": 15}),   # Should be allowed (number > 10)
        ("conditional-greet", {"name": "Charlie", "number": 25}), # Should be allowed (number > 10)
        ("search_files", {"repo_path": "/public/repo", "max_results": 10}),
        ("search_files", {"repo_path": "/secure/repo", "max_results": 100}),
    ]
    
    print(f"{'Tool':<20} {'Arguments':<35} {'Allowed':<8}")
    print("-"*60)
    
    for tool_name, tool_args in abac_tests:
        try:
            allowed = await check_tool_permission(abac_user, tool_name, tool_args)
            status = "✓ YES" if allowed else "✗ NO"
            args_str = str(tool_args)[:30] + "..." if len(str(tool_args)) > 30 else str(tool_args)
            print(f"{tool_name:<20} {args_str:<35} {status:<8}")
        except Exception as e:
            print(f"{tool_name:<20} ERROR: {str(e)[:30]:<30} ERROR")
    
    # Demonstrate JWT-based identity extraction
    print("\n" + "-"*60)
    print("JWT Identity Extraction Demo:")
    print("-"*60)
    
    # Create JWT tokens for different users
    jwt_tokens = {
        "admin": create_demo_jwt_token("admin", "admin"),
        "user": create_demo_jwt_token("developer", "user"),
        "readonly": create_demo_jwt_token("analyst", "readonly")
    }
    
    print("Created JWT tokens for identity extraction:")
    for role, token in jwt_tokens.items():
        # Decode to show contents (for demo purposes)
        try:
            decoded = jwt.decode(token, "demo-secret-key", algorithms=["HS256"])
            print(f"  {role}: sub={decoded['sub']}, role={decoded.get('role', 'N/A')}")
        except Exception as e:
            print(f"  {role}: Error decoding token")
    
    # Test permission checking with JWT context
    print("\nTesting permissions with JWT context:")
    for role, token in jwt_tokens.items():
        try:
            # In a real scenario, the JWT would be extracted from the request
            # Here we simulate by creating a user from the JWT payload
            decoded = jwt.decode(token, "demo-secret-key", algorithms=["HS256"])
            jwt_user = User(
                username=decoded["sub"],
                role=decoded.get("role", "user"),
                permissions=decoded.get("permissions", [])
            )
            
            # Test a search operation
            allowed = await check_permission(jwt_user, "search", "githound-mcp:search")
            status = "✓ YES" if allowed else "✗ NO"
            print(f"  {jwt_user.username} (from JWT): search permission = {status}")
            
        except Exception as e:
            print(f"  {role}: Error testing JWT permission - {e}")
    
    # Show configuration
    print("\n" + "-"*60)
    print("Permit.io Configuration:")
    print("-"*60)
    
    config = auth_provider.get_permit_config()
    print(f"PDP URL: {config.permit_pdp_url}")
    print(f"Server Name: {config.server_name}")
    print(f"Identity Mode: {config.identity_mode}")
    print(f"Audit Logging: {config.enable_audit_logging}")
    print(f"Bypass Methods: {config.bypass_methods}")
    
    # Demonstrate configuration updates
    print("\n" + "-"*60)
    print("Configuration Management:")
    print("-"*60)
    
    print("✓ Current configuration loaded")
    
    # You can update configuration at runtime
    try:
        auth_provider.update_permit_config(
            enable_audit_logging=False,
            bypass_methods=["initialize", "ping", "health"]
        )
        print("✓ Configuration updated successfully")
        
        # Show updated config
        updated_config = auth_provider.get_permit_config()
        print(f"✓ Audit logging now: {updated_config.enable_audit_logging}")
        print(f"✓ Bypass methods now: {updated_config.bypass_methods}")
        
    except Exception as e:
        print(f"✗ Configuration update failed: {e}")
    
    print("\n" + "="*60)
    print("Demo Complete!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Set up your Permit.io account and get an API key")
    print("2. Configure resources and policies in Permit.io dashboard")
    print("3. Set up proper JWT authentication")
    print("4. Configure user roles in Permit.io Directory")
    print("5. Set up production PDP (local Docker or cloud)")
    
    print("\nPermit.io Setup Commands:")
    print("  # Run local PDP")
    print("  docker run -p 7766:7766 permitio/pdp:latest")
    print("  ")
    print("  # Or use cloud PDP")
    print("  export PERMIT_MCP_PERMIT_PDP_URL=https://cloudpdp.api.permit.io")
    
    print("\nPolicy Mapping in Permit.io:")
    print("  Resources: githound_mcp, githound_mcp_tools, githound_mcp_repositories")
    print("  Actions: search, analyze, blame, diff, list, read")
    print("  Roles: Admin, User, ReadOnly")
    print("  Users: Assign roles to users in Directory")


if __name__ == "__main__":
    asyncio.run(demo_permit_authorization())
