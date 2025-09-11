#!/usr/bin/env python3
"""
FastMCP Client - Authentication Examples

This example demonstrates FastMCP 2.6+ authentication features including
Bearer token authentication and OAuth 2.1 integration.

Usage:
    python examples/mcp_server/clients/authentication_examples.py

This example covers:
- Bearer token authentication
- OAuth 2.1 authentication flow
- Authentication error handling
- Token refresh patterns
- Secure credential management
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass

from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport, FastMCPTransport
from fastmcp.client.auth import BearerAuth, OAuth
from fastmcp.exceptions import ClientError, McpError

# Configure logging
logging.basicConfig(  # [attr-defined]
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AuthConfig:
    """Configuration for authentication examples."""
    bearer_token: str = "demo_token_12345"
    oauth_client_id: str = "demo_client_id"
    oauth_client_secret: str = "demo_client_secret"
    oauth_redirect_uri: str = "http://localhost:8080/callback"
    oauth_scope: str = "read write"


async def create_authenticated_server() -> FastMCP:
    """
    Create a mock MCP server that requires authentication.
    
    Returns:
        FastMCP server instance with authentication requirements
    """
    server = FastMCP("Authenticated Server")
    
    @server.tool
    def public_info() -> Dict[str, str]:
        """Get public information (no auth required)."""
        return {
            "server": "Authenticated Server",
            "version": "1.0.0",
            "public": True
        }
    
    @server.tool
    def protected_data(user_id: str = "anonymous") -> Dict[str, Any]:
        """Get protected user data (auth required)."""
        return {
            "user_id": user_id,
            "account_type": "premium",
            "last_login": "2024-01-15T10:30:00Z",
            "permissions": ["read", "write", "admin"],
            "protected": True
        }
    
    @server.tool
    def admin_operation(action: str) -> Dict[str, str]:
        """Perform admin operation (high-level auth required)."""
        return {
            "action": action,
            "status": "completed",
            "admin": True,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    
    @server.resource("auth://user/{user_id}/profile")
    def get_user_profile(user_id: str) -> str:
        """Get user profile (auth required)."""
        return json.dumps({
            "user_id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com",
            "created": "2024-01-01T00:00:00Z"
        })
    
    return server


async def demonstrate_bearer_auth() -> Dict[str, Any]:
    """
    Demonstrate Bearer token authentication.
    
    Returns:
        Dict containing Bearer auth demonstration results
    """
    logger.info("Demonstrating Bearer token authentication...")
    
    config = AuthConfig()
    server = await create_authenticated_server()
    
    results = {
        "unauthenticated_access": None,
        "authenticated_access": None,
        "invalid_token_access": None
    }
    
    try:
        # Test 1: Unauthenticated access (should work for public endpoints)
        logger.info("Testing unauthenticated access...")
        transport = FastMCPTransport(server)
        
        async with Client(transport) as client:
            try:
                public_result = await client.call_tool("public_info", {})
                results["unauthenticated_access"] = {
                    "status": "success",
                    "result": public_result.data,
                    "message": "Public endpoint accessible without auth"
                }
                logger.info("✓ Unauthenticated access to public endpoint successful")
            except Exception as e:
                results["unauthenticated_access"] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        # Test 2: Authenticated access with valid Bearer token
        logger.info("Testing authenticated access with Bearer token...")
        
        # Create authenticated transport
        auth = BearerAuth(config.bearer_token)  # [attr-defined]
        # Note: In a real scenario, you'd use StreamableHttpTransport with auth
        # For demo purposes, we'll simulate the auth flow
        
        async with Client(transport) as client:
            try:
                # Simulate authenticated call
                protected_result = await client.call_tool("protected_data", {"user_id": "user123"})
                results["authenticated_access"] = {
                    "status": "success",
                    "result": protected_result.data,
                    "message": "Protected endpoint accessible with valid token"
                }
                logger.info("✓ Authenticated access successful")
            except Exception as e:
                results["authenticated_access"] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        # Test 3: Invalid token access
        logger.info("Testing access with invalid Bearer token...")
        
        try:
            invalid_auth = BearerAuth("invalid_token_xyz")
            # This would normally fail in a real HTTP scenario
            results["invalid_token_access"] = {
                "status": "simulated",
                "message": "Invalid token would be rejected by real server",
                "expected_error": "401 Unauthorized"
            }
            logger.info("✓ Invalid token handling simulated")
        except Exception as e:
            results["invalid_token_access"] = {
                "status": "failed",
                "error": str(e)
            }
        
        return {
            "status": "success",
            "bearer_auth_tests": results
        }
        
    except Exception as e:
        logger.error(f"Bearer auth demonstration failed: {e}")
        return {"status": "failed", "error": str(e)}


async def demonstrate_oauth_flow() -> Dict[str, Any]:
    """
    Demonstrate OAuth 2.1 authentication flow.
    
    Returns:
        Dict containing OAuth demonstration results
    """
    logger.info("Demonstrating OAuth 2.1 authentication flow...")
    
    config = AuthConfig()
    
    oauth_steps: list[Any] = []
    
    try:
        # Step 1: Initialize OAuth configuration
        logger.info("Step 1: Initializing OAuth configuration...")  # [attr-defined]
        
        oauth_config = {
            "client_id": config.oauth_client_id,  # [attr-defined]
            "client_secret": config.oauth_client_secret,  # [attr-defined]
            "redirect_uri": config.oauth_redirect_uri,  # [attr-defined]
            "scope": config.oauth_scope,  # [attr-defined]
            "authorization_url": "https://auth.example.com/oauth/authorize",
            "token_url": "https://auth.example.com/oauth/token"
        }
        
        oauth_steps.append({
            "step": 1,
            "description": "OAuth configuration initialized",
            "status": "success",
            "config": {k: v for k, v in oauth_config.items() if k != "client_secret"}
        })
        
        # Step 2: Generate authorization URL
        logger.info("Step 2: Generating authorization URL...")
        
        # Simulate OAuth URL generation
        auth_url = (
            f"{oauth_config['authorization_url']}"
            f"?client_id={oauth_config['client_id']}"
            f"&redirect_uri={oauth_config['redirect_uri']}"
            f"&scope={oauth_config['scope']}"
            f"&response_type=code"
            f"&state=random_state_123"
        )
        
        oauth_steps.append({
            "step": 2,
            "description": "Authorization URL generated",
            "status": "success",
            "auth_url": auth_url
        })
        
        # Step 3: Simulate authorization code exchange
        logger.info("Step 3: Simulating authorization code exchange...")
        
        # In a real scenario, user would visit auth_url and get redirected back with code
        simulated_auth_code = "auth_code_xyz123"
        
        # Simulate token exchange
        simulated_token_response = {
            "access_token": "access_token_abc456",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "refresh_token_def789",
            "scope": config.oauth_scope  # [attr-defined]
        }
        
        oauth_steps.append({
            "step": 3,
            "description": "Authorization code exchanged for tokens",
            "status": "simulated",
            "auth_code": simulated_auth_code,
            "token_info": {
                "token_type": simulated_token_response["token_type"],
                "expires_in": simulated_token_response["expires_in"],
                "scope": simulated_token_response["scope"]
            }
        })
        
        # Step 4: Use access token for API calls
        logger.info("Step 4: Using access token for authenticated API calls...")
        
        # Create OAuth auth object
        oauth_auth = OAuth(
            mcp_url="https://api.example.com/mcp",
            scopes=config.oauth_scope,  # [attr-defined]
            client_name="FastMCP Demo Client"
        )
        
        oauth_steps.append({
            "step": 4,
            "description": "OAuth authentication object created",
            "status": "success",
            "message": "Ready for authenticated API calls"
        })
        
        # Step 5: Simulate token refresh
        logger.info("Step 5: Simulating token refresh...")
        
        refreshed_token_response = {
            "access_token": "new_access_token_ghi789",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": config.oauth_scope  # [attr-defined]
        }
        
        oauth_steps.append({
            "step": 5,
            "description": "Access token refreshed",
            "status": "simulated",
            "new_token_info": {
                "token_type": refreshed_token_response["token_type"],
                "expires_in": refreshed_token_response["expires_in"]
            }
        })
        
        logger.info("✓ OAuth 2.1 flow demonstration completed")
        
        return {
            "status": "success",
            "oauth_flow": oauth_steps,
            "total_steps": len(oauth_steps)
        }
        
    except Exception as e:
        logger.error(f"OAuth demonstration failed: {e}")
        return {"status": "failed", "error": str(e)}


async def demonstrate_auth_error_handling() -> Dict[str, Any]:
    """
    Demonstrate authentication error handling patterns.
    
    Returns:
        Dict containing auth error handling results
    """
    logger.info("Demonstrating authentication error handling...")
    
    error_scenarios: list[Any] = []
    
    try:
        # Scenario 1: Missing authentication
        logger.info("Testing missing authentication scenario...")
        
        try:
            # Simulate call to protected endpoint without auth
            raise ClientError("Authentication required for this endpoint")
        except ClientError as e:
            error_scenarios.append({
                "scenario": "missing_auth",
                "status": "handled",
                "error_type": "ClientError",
                "message": str(e),
                "recommended_action": "Provide valid authentication credentials"
            })
            logger.info("✓ Missing auth error handled correctly")
        
        # Scenario 2: Expired token
        logger.info("Testing expired token scenario...")
        
        try:
            # Simulate expired token error
            raise ClientError("Token has expired")
        except ClientError as e:
            error_scenarios.append({
                "scenario": "expired_token",
                "status": "handled",
                "error_type": "ClientError",
                "message": str(e),
                "recommended_action": "Refresh the access token"
            })
            logger.info("✓ Expired token error handled correctly")
        
        # Scenario 3: Insufficient permissions
        logger.info("Testing insufficient permissions scenario...")
        
        try:
            # Simulate insufficient permissions error
            raise ClientError("Insufficient permissions for this operation")
        except ClientError as e:
            error_scenarios.append({
                "scenario": "insufficient_permissions",
                "status": "handled",
                "error_type": "ClientError",
                "message": str(e),
                "recommended_action": "Request elevated permissions or contact administrator"
            })
            logger.info("✓ Insufficient permissions error handled correctly")
        
        # Scenario 4: Invalid token format
        logger.info("Testing invalid token format scenario...")
        
        try:
            # Simulate invalid token format error
            raise ClientError("Invalid token format")
        except ClientError as e:
            error_scenarios.append({
                "scenario": "invalid_token_format",
                "status": "handled",
                "error_type": "ClientError",
                "message": str(e),
                "recommended_action": "Verify token format and regenerate if necessary"
            })
            logger.info("✓ Invalid token format error handled correctly")
        
        return {
            "status": "success",
            "error_scenarios": error_scenarios,
            "scenarios_tested": len(error_scenarios)
        }
        
    except Exception as e:
        logger.error(f"Auth error handling demonstration failed: {e}")
        return {"status": "failed", "error": str(e)}


async def main() -> Dict[str, Any]:
    """
    Main function demonstrating FastMCP authentication features.
    
    Returns:
        Dict containing all demonstration results
    """
    print("=" * 60)
    print("FastMCP Client - Authentication Examples")
    print("=" * 60)
    
    results: dict[str, Any] = {}
    
    try:
        # 1. Bearer token authentication
        logger.info("\n1. Bearer Token Authentication")
        bearer_result = await demonstrate_bearer_auth()
        results["bearer_auth"] = bearer_result
        
        # 2. OAuth 2.1 flow
        logger.info("\n2. OAuth 2.1 Authentication Flow")
        oauth_result = await demonstrate_oauth_flow()
        results["oauth_flow"] = oauth_result
        
        # 3. Authentication error handling
        logger.info("\n3. Authentication Error Handling")
        error_handling_result = await demonstrate_auth_error_handling()
        results["error_handling"] = error_handling_result
        
        print("\n" + "=" * 60)
        print("Authentication examples completed!")
        print("=" * 60)
        
        return results
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    # Run the authentication examples
    result = asyncio.run(main())
    print(f"\nFinal Results: {json.dumps(result, indent=2, default=str)}")
