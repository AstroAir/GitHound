#!/usr/bin/env python3
"""
Example: GitHound MCP Server with Eunomia Authorization

This example demonstrates how to set up GitHound MCP server with Eunomia
policy-based authorization. Eunomia provides embedded authorization with
JSON-based policies.

Requirements:
    pip install eunomia-mcp

Usage:
    python eunomia_example.py
"""

import os
import json
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up environment for Eunomia
os.environ["EUNOMIA_ENABLE"] = "true"
os.environ["EUNOMIA_POLICY_FILE"] = "githound_eunomia_policies.json"
os.environ["EUNOMIA_SERVER_NAME"] = "githound-demo"
os.environ["EUNOMIA_ENABLE_AUDIT_LOGGING"] = "true"

# Import GitHound components
from githound.mcp.auth import set_auth_provider, check_permission, check_tool_permission
from githound.mcp.auth.providers import JWTVerifier, EunomiaAuthorizationProvider
from githound.mcp.models import User


def create_demo_policy_file():
    """Create a demo policy file for GitHound with Eunomia."""
    policies = {
        "version": "1.0",
        "server_name": "githound-demo",
        "policies": [
            {
                "id": "admin_full_access",
                "description": "Administrators have full access to all GitHound operations",
                "subjects": ["role:admin"],
                "resources": ["*"],
                "actions": ["*"],
                "effect": "allow"
            },
            {
                "id": "developer_code_access",
                "description": "Developers can access code analysis tools",
                "subjects": ["role:developer"],
                "resources": [
                    "githound-demo:repository:*",
                    "githound-demo:search:*",
                    "githound-demo:blame:*",
                    "githound-demo:diff:*",
                    "githound-demo:tools:list"
                ],
                "actions": ["read", "search", "analyze", "list"],
                "effect": "allow"
            },
            {
                "id": "analyst_read_only",
                "description": "Analysts can only read repository information",
                "subjects": ["role:analyst"],
                "resources": [
                    "githound-demo:repository:info",
                    "githound-demo:tools:list"
                ],
                "actions": ["read", "list"],
                "effect": "allow"
            },
            {
                "id": "intern_limited_access",
                "description": "Interns have very limited access",
                "subjects": ["role:intern"],
                "resources": [
                    "githound-demo:tools:list"
                ],
                "actions": ["list"],
                "effect": "allow"
            },
            {
                "id": "secure_repo_restriction",
                "description": "Restrict access to secure repositories",
                "subjects": ["*"],
                "resources": ["githound-demo:repository:/secure/*"],
                "actions": ["*"],
                "effect": "deny",
                "conditions": {
                    "subject_role": {"not_in": ["admin", "security-lead"]}
                }
            },
            {
                "id": "default_deny",
                "description": "Deny all other access by default",
                "subjects": ["*"],
                "resources": ["*"],
                "actions": ["*"],
                "effect": "deny"
            }
        ]
    }
    
    policy_file = "githound_eunomia_policies.json"
    with open(policy_file, 'w') as f:
        json.dump(policies, f, indent=2)
    
    logger.info(f"Created demo policy file: {policy_file}")
    return policy_file


async def demo_eunomia_authorization():
    """Demonstrate Eunomia authorization with GitHound."""
    
    print("\n" + "="*60)
    print("GitHound MCP Server - Eunomia Authorization Demo")
    print("="*60)
    
    # Create demo policy file
    policy_file = create_demo_policy_file()
    
    # Create a simple JWT verifier for demo (in production, use proper JWKS)
    from githound.mcp.auth.providers.jwt import StaticJWTVerifier
    
    jwt_provider = StaticJWTVerifier(
        secret_key="demo-secret-key",
        issuer="githound-demo",
        audience="mcp-client"
    )
    
    # Wrap with Eunomia authorization
    auth_provider = EunomiaAuthorizationProvider(
        base_provider=jwt_provider,
        policy_file=policy_file,
        server_name="githound-demo",
        enable_audit_logging=True
    )
    
    # Set as the global auth provider
    set_auth_provider(auth_provider)
    
    print(f"✓ Created Eunomia authorization provider")
    print(f"✓ Policy file: {policy_file}")
    
    # Create test users with different roles
    test_users = [
        User(username="admin_user", role="admin", permissions=[]),
        User(username="dev_user", role="developer", permissions=[]),
        User(username="analyst_user", role="analyst", permissions=[]),
        User(username="intern_user", role="intern", permissions=[]),
    ]
    
    # Test permissions for different operations
    test_operations = [
        ("search", "githound-demo:search:files"),
        ("analyze", "githound-demo:blame:file"),
        ("read", "githound-demo:repository:info"),
        ("list", "githound-demo:tools:list"),
        ("admin", "githound-demo:admin:config"),
    ]
    
    print("\n" + "-"*60)
    print("Permission Test Results:")
    print("-"*60)
    print(f"{'User':<15} {'Role':<12} {'Operation':<10} {'Resource':<25} {'Allowed':<8}")
    print("-"*60)
    
    for user in test_users:
        for operation, resource in test_operations:
            try:
                allowed = await check_permission(user, operation, resource)
                status = "✓ YES" if allowed else "✗ NO"
                print(f"{user.username:<15} {user.role:<12} {operation:<10} {resource:<25} {status:<8}")
            except Exception as e:
                print(f"{user.username:<15} {user.role:<12} {operation:<10} {resource:<25} ERROR")
    
    # Test tool-level permissions with arguments
    print("\n" + "-"*60)
    print("Tool Permission Test Results:")
    print("-"*60)
    
    tool_tests = [
        ("search_files", {"repo_path": "/public/repo", "pattern": "*.py"}),
        ("search_files", {"repo_path": "/secure/repo", "pattern": "*.py"}),
        ("git_blame", {"file_path": "/public/repo/main.py"}),
        ("git_diff", {"repo_path": "/secure/repo", "commit": "abc123"}),
    ]
    
    for user in test_users[:2]:  # Test with admin and developer
        for tool_name, tool_args in tool_tests:
            try:
                allowed = await check_tool_permission(user, tool_name, tool_args)
                status = "✓ YES" if allowed else "✗ NO"
                args_str = str(tool_args)[:30] + "..." if len(str(tool_args)) > 30 else str(tool_args)
                print(f"{user.username:<15} {tool_name:<15} {args_str:<35} {status}")
            except Exception as e:
                print(f"{user.username:<15} {tool_name:<15} ERROR: {e}")
    
    print("\n" + "-"*60)
    print("Policy File Contents:")
    print("-"*60)
    
    with open(policy_file, 'r') as f:
        policy_content = json.load(f)
    
    print(f"Server: {policy_content['server_name']}")
    print(f"Policies: {len(policy_content['policies'])}")
    
    for policy in policy_content['policies']:
        print(f"\n  Policy: {policy['id']}")
        print(f"    Description: {policy['description']}")
        print(f"    Subjects: {policy['subjects']}")
        print(f"    Effect: {policy['effect']}")
    
    # Demonstrate policy reloading
    print("\n" + "-"*60)
    print("Policy Management:")
    print("-"*60)
    
    print("✓ Policies loaded from:", auth_provider.get_policy_file_path())
    
    # You can reload policies at runtime
    try:
        auth_provider.reload_policies()
        print("✓ Policies reloaded successfully")
    except Exception as e:
        print(f"✗ Policy reload failed: {e}")
    
    print("\n" + "="*60)
    print("Demo Complete!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Customize the policy file for your use case")
    print("2. Set up proper JWT authentication")
    print("3. Configure audit logging")
    print("4. Use eunomia-mcp CLI tools for policy management")
    print("\nEunomia CLI Commands:")
    print("  eunomia-mcp init                    # Create default policies")
    print("  eunomia-mcp validate policies.json # Validate policy file")
    print("  eunomia-mcp --help                 # Show all commands")


if __name__ == "__main__":
    asyncio.run(demo_eunomia_authorization())
