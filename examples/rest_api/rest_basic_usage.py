#!/usr/bin/env python3
"""
REST API Basic Usage Examples

This example demonstrates basic usage of the GitHound REST API including
authentication, health checks, and simple search operations.

Usage:
    # Start the GitHound API server first:
    uvicorn githound.web.api:app --reload --port 8000

    # Then run this example:
    python examples/rest_api/basic_usage.py

This example covers:
- API health checks and status
- Basic authentication patterns
- Simple search operations
- Error handling and response parsing
- Best practices for API usage
"""

import asyncio
import json
import sys
from typing import Optional, cast, Any
import logging

try:
    import httpx
except ImportError:
    print("Error: httpx is required for REST API examples")
    print("Install with: pip install httpx")
    sys.exit(1)


# Configure logging
logging.basicConfig(  # [attr-defined]
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GitHoundAPIClient:
    """Simple client for GitHound REST API."""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None) -> None:
        """Initialize API client."""
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient()

        # Set up authentication headers
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        if api_key:
            self.headers["X-API-Key"] = api_key

    async def __aenter__(self) -> None:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except httpx.HTTPError as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "error": str(e)}

    async def start_search(self, search_request: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new search operation."""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/search",
                json=search_request,
                headers=self.headers
            )
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except httpx.HTTPError as e:
            logger.error(f"Search start failed: {e}")
            if hasattr(e, 'response') and e.response:
                try:
                    error_detail = e.response.json()
                    return {"status": "error", "error": error_detail}
                except:
                    pass
            return {"status": "error", "error": str(e)}

    async def get_search_status(self, search_id: str) -> Dict[str, Any]:
        """Get search status."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/search/{search_id}/status",
                headers=self.headers
            )
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except httpx.HTTPError as e:
            logger.error(f"Get search status failed: {e}")
            return {"status": "error", "error": str(e)}

    async def get_search_results(self, search_id: str) -> Dict[str, Any]:
        """Get search results."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/search/{search_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except httpx.HTTPError as e:
            logger.error(f"Get search results failed: {e}")
            return {"status": "error", "error": str(e)}

    async def list_searches(self) -> Dict[str, Any]:
        """List all searches."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/searches",
                headers=self.headers
            )
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except httpx.HTTPError as e:
            logger.error(f"List searches failed: {e}")
            return {"status": "error", "error": str(e)}


class APIUsageDemo:
    """Demonstration of basic API usage patterns."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url
        self.results: Dict[str, Any] = {}

    async def demonstrate_health_check(self) -> None:
        """Demonstrate API health check."""
        logger.info("=== API Health Check ===")

        async with GitHoundAPIClient(self.base_url) as client:
            health_result = await client.health_check()

            self.results['health_check'] = health_result

            if health_result.get('status') == 'healthy':
                logger.info("✓ API is healthy and ready")
                logger.info(f"  Uptime: {health_result.get if health_result is not None else None('uptime', 'N/A')}")
                logger.info(f"  Version: {health_result.get if health_result is not None else None('version', 'N/A')}")
            else:
                logger.error("✗ API health check failed")
                logger.error(f"  Error: {health_result.get if health_result is not None else None('error', 'Unknown error')}")

            return health_result

    async def demonstrate_basic_search(self, repository_path: str) -> Optional[Dict[str, Any]]:
        """Demonstrate basic search operation."""
        logger.info("\n=== Basic Search Operation ===")

        # Create search request
        search_request = {
            "query": "test",
            "repository_path": repository_path,
            "search_type": "message",
            "filters": {
                "max_results": 10
            }
        }

        logger.info(f"Starting search with query: '{search_request['query']}'")
        logger.info(f"Repository: {repository_path}")

        async with GitHoundAPIClient(self.base_url) as client:
            # Start search
            search_result = await client.start_search(search_request)

            if 'error' in search_result:
                logger.error(f"✗ Search failed to start: {search_result['error']}")
                self.results['basic_search'] = search_result
                return cast(Dict[str, Any], search_result)

            search_id = search_result.get('search_id')
            logger.info(f"✓ Search started with ID: {search_id}")

            # Monitor search progress
            max_wait_time = 30  # seconds
            wait_interval = 1   # seconds
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                status_result = await client.get_search_status(search_id)

                if 'error' in status_result:
                    logger.error(f"✗ Failed to get search status: {status_result['error']}")
                    break

                status = status_result.get('status', 'unknown')
                progress = status_result.get('progress', 0)

                logger.info(f"  Search status: {status} ({progress:.1f}%)")

                if status in ['completed', 'failed']:
                    break

                await asyncio.sleep(wait_interval)
                elapsed_time += wait_interval

            # Get final results
            if status == 'completed':
                results = await client.get_search_results(search_id)

                if 'error' not in results:
                    result_count = results.get('total_count', 0)
                    search_duration = results.get('search_duration_ms', 0)

                    logger.info(f"✓ Search completed successfully")
                    logger.info(f"  Results found: {result_count}")
                    logger.info(f"  Search duration: {search_duration:.2f}ms")

                    # Show sample results
                    search_results = results.get('results', [])
                    if search_results:
                        logger.info("  Sample results:")
                        for i, result in enumerate(search_results[:3]):
                            commit_hash = result.get('commit_hash', 'N/A')[:8]
                            message = result.get('message', 'N/A')[:50]
                            logger.info(f"    {i+1}. {commit_hash}: {message}...")

                    self.results['basic_search'] = results
                    return cast(Dict[str, Any], results)
                else:
                    logger.error(f"✗ Failed to get search results: {results['error']}")
            else:
                logger.warning(f"⚠ Search did not complete within {max_wait_time} seconds")

            self.results['basic_search'] = {"status": "timeout", "search_id": search_id}
            return self.results['basic_search']

    async def demonstrate_search_management(self) -> None:
        """Demonstrate search management operations."""
        logger.info("\n=== Search Management ===")

        async with GitHoundAPIClient(self.base_url) as client:
            # List all searches
            searches_result = await client.list_searches()

            if 'error' in searches_result:
                logger.error(f"✗ Failed to list searches: {searches_result['error']}")
                self.results['search_management'] = searches_result
                return searches_result

            searches = searches_result.get('searches', [])
            logger.info(f"✓ Found {len(searches)} searches")

            if searches:
                logger.info("  Recent searches:")
                for i, search in enumerate(searches[:5]):
                    search_id = search.get('search_id', 'N/A')[:8]
                    status = search.get('status', 'N/A')
                    results_count = search.get('results_count', 0)
                    started_at = search.get('started_at', 'N/A')

                    logger.info(f"    {i+1}. {search_id}: {status} ({results_count} results) - {started_at}")

            self.results['search_management'] = searches_result
            return searches_result

    async def demonstrate_error_handling(self) -> None:
        """Demonstrate error handling patterns."""
        logger.info("\n=== Error Handling Patterns ===")

        async with GitHoundAPIClient(self.base_url) as client:
            # Test 1: Invalid repository path
            logger.info("1. Testing invalid repository path...")
            invalid_search = {
                "query": "test",
                "repository_path": "/nonexistent/path",
                "search_type": "message"
            }

            result = await client.start_search(invalid_search)
            if 'error' in result:
                logger.info(f"   ✓ Error properly handled: {result['error']}")
            else:
                logger.warning("   ⚠ Expected error but got success")

            # Test 2: Invalid search ID
            logger.info("2. Testing invalid search ID...")
            invalid_status = await client.get_search_status("invalid-search-id")
            if 'error' in invalid_status:
                logger.info(f"   ✓ Error properly handled: {invalid_status['error']}")
            else:
                logger.warning("   ⚠ Expected error but got success")

            # Test 3: Malformed request
            logger.info("3. Testing malformed request...")
            malformed_search = {
                "invalid_field": "test"
                # Missing required fields
            }

            result = await client.start_search(malformed_search)
            if 'error' in result:
                logger.info(f"   ✓ Validation error properly handled")
            else:
                logger.warning("   ⚠ Expected validation error but got success")

            self.results['error_handling'] = {
                "invalid_repo": result,
                "invalid_search_id": invalid_status,
                "malformed_request": result
            }


async def main() -> None:
    """Main demonstration function."""

    if len(sys.argv) < 2:
        print("Usage: python basic_usage.py /path/to/repository [api_url]")
        print("Example: python basic_usage.py /path/to/repo http://localhost:8000")
        sys.exit(1)

    repository_path = sys.argv[1]
    api_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"

    print("=" * 70)
    print("GitHound REST API - Basic Usage Examples")
    print("=" * 70)
    print(f"API URL: {api_url}")
    print(f"Repository: {repository_path}")
    print()

    demo = APIUsageDemo(api_url)

    try:
        # Run all demonstrations
        await demo.demonstrate_health_check()
        await demo.demonstrate_basic_search(repository_path)
        await demo.demonstrate_search_management()
        await demo.demonstrate_error_handling()

        print("\n" + "=" * 70)
        print("Basic API usage demonstration completed!")
        print("=" * 70)

        # Save results to file
        output_file = "api_basic_usage_results.json"
        with open(output_file, 'w') as f:
            json.dump(demo.results, f, indent=2, default=str)

        print(f"\nResults saved to: {output_file}")

    except Exception as e:
        logger.error(f"API usage demonstration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
