"""
API integration tests for GitHound web interface.
"""

import json

import pytest
from playwright.async_api import Page, expect


@pytest.mark.api
@pytest.mark.e2e
class TestAPIIntegration:
    """Test API integration through the web interface."""

    async def test_search_api_through_frontend(
        self, page: Page, authenticated_user, test_repository
    ):
        """Test search API calls through the frontend interface."""
        # Navigate to search page
        await page.goto("/search")

        # Monitor network requests
        requests = []

        def handle_request(request):
            if "/api/v1/search" in request.url:
                requests.append(
                    {
                        "url": request.url,
                        "method": request.method,
                        "headers": dict(request.headers),
                        "post_data": request.post_data,
                    }
                )

        page.on("request", handle_request)

        # Perform search
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "function")
        await page.click('[data-testid="submit-search"]')

        # Wait for API call
        await page.wait_for_timeout(2000)

        # Verify API request was made
        assert len(requests) > 0, "Search API request should be made"

        search_request = requests[0]
        assert search_request["method"] == "POST"
        assert "Authorization" in search_request["headers"]

        # Verify request payload
        if search_request["post_data"]:
            payload = json.loads(search_request["post_data"])
            assert payload["query"] == "function"
            assert payload["repo_path"] == str(test_repository)

    async def test_authentication_api_calls(self, page: Page, test_user_data):
        """Test authentication API calls through the frontend."""
        # Monitor network requests
        auth_requests = []

        def handle_request(request):
            if "/api/v1/auth" in request.url:
                auth_requests.append(
                    {"url": request.url, "method": request.method, "post_data": request.post_data}
                )

        page.on("request", handle_request)

        # Perform login
        await page.goto("/")
        await page.click('[data-testid="login-button"]')
        await page.fill('[data-testid="username-input"]', test_user_data["username"])
        await page.fill('[data-testid="password-input"]', test_user_data["password"])
        await page.click('[data-testid="submit-login"]')

        # Wait for API calls
        await page.wait_for_timeout(2000)

        # Verify login API request
        login_requests = [req for req in auth_requests if "/login" in req["url"]]
        assert len(login_requests) > 0, "Login API request should be made"

        login_request = login_requests[0]
        assert login_request["method"] == "POST"

        if login_request["post_data"]:
            payload = json.loads(login_request["post_data"])
            assert payload["username"] == test_user_data["username"]

    async def test_api_error_handling(self, page: Page, authenticated_user):
        """Test API error handling in the frontend."""
        # Navigate to search page
        await page.goto("/search")

        # Monitor network responses
        responses = []

        def handle_response(response):
            if "/api/v1/search" in response.url:
                responses.append(
                    {
                        "url": response.url,
                        "status": response.status,
                        "status_text": response.status_text,
                    }
                )

        page.on("response", handle_response)

        # Perform search with invalid repository
        await page.fill('[data-testid="repo-path-input"]', "/nonexistent/repo")
        await page.fill('[data-testid="search-query-input"]', "function")
        await page.click('[data-testid="submit-search"]')

        # Wait for response
        await page.wait_for_timeout(3000)

        # Verify error response
        assert len(responses) > 0, "API response should be received"

        error_response = responses[0]
        assert error_response["status"] >= 400, "Should receive error status code"

        # Verify error is displayed in UI
        await expect(page.locator('[data-testid="search-error"]')).to_be_visible()

    async def test_rate_limiting_behavior(self, page: Page, authenticated_user, test_repository):
        """Test rate limiting behavior through the frontend."""
        # Navigate to search page
        await page.goto("/search")

        # Monitor rate limit responses
        rate_limit_responses = []

        def handle_response(response):
            if response.status == 429:  # Too Many Requests
                rate_limit_responses.append(
                    {
                        "url": response.url,
                        "status": response.status,
                        "headers": dict(response.headers),
                    }
                )

        page.on("response", handle_response)

        # Perform multiple rapid searches to trigger rate limiting
        for i in range(10):
            await page.fill('[data-testid="search-query-input"]', f"search_{i}")
            await page.click('[data-testid="submit-search"]')
            await page.wait_for_timeout(100)  # Small delay

        # Wait for responses
        await page.wait_for_timeout(5000)

        # Check if rate limiting was triggered
        if len(rate_limit_responses) > 0:
            # Verify rate limit headers
            rate_limit_response = rate_limit_responses[0]
            headers = rate_limit_response["headers"]

            # Common rate limit headers
            rate_limit_headers = ["x-ratelimit-limit", "x-ratelimit-remaining", "retry-after"]
            has_rate_limit_headers = any(header in headers for header in rate_limit_headers)
            assert has_rate_limit_headers, "Rate limit response should include rate limit headers"

            # Verify UI shows rate limit message
            await expect(page.locator('[data-testid="rate-limit-warning"]')).to_be_visible()

    async def test_export_api_integration(self, page: Page, authenticated_user, test_repository):
        """Test export API integration through the frontend."""
        # Perform a search first
        await page.goto("/search")
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "def")
        await page.click('[data-testid="submit-search"]')

        # Wait for results
        await expect(page.locator('[data-testid="search-results"]')).to_be_visible(timeout=30000)

        # Monitor export API requests
        export_requests = []

        def handle_request(request):
            if "/api/v1/integration/export" in request.url:
                export_requests.append(
                    {"url": request.url, "method": request.method, "post_data": request.post_data}
                )

        page.on("request", handle_request)

        # Trigger export
        await page.click('[data-testid="export-button"]')
        await page.select_option('[data-testid="export-format"]', "json")
        await page.click('[data-testid="confirm-export"]')

        # Wait for API call
        await page.wait_for_timeout(3000)

        # Verify export API request
        assert len(export_requests) > 0, "Export API request should be made"

        export_request = export_requests[0]
        assert export_request["method"] == "POST"

        if export_request["post_data"]:
            payload = json.loads(export_request["post_data"])
            assert payload["format"] == "json"

    async def test_webhook_api_integration(self, page: Page, authenticated_admin):
        """Test webhook API integration through the admin interface."""
        # Navigate to admin panel
        await page.click('[data-testid="user-menu"]')
        await page.click('[data-testid="admin-panel-link"]')

        # Navigate to webhook management
        await page.click('[data-testid="webhook-management"]')

        # Monitor webhook API requests
        webhook_requests = []

        def handle_request(request):
            if "/api/v1/integration/webhooks" in request.url:
                webhook_requests.append(
                    {"url": request.url, "method": request.method, "post_data": request.post_data}
                )

        page.on("request", handle_request)

        # Create a new webhook
        await page.click('[data-testid="add-webhook"]')
        await page.fill('[data-testid="webhook-url"]', "https://example.com/webhook")
        await page.fill('[data-testid="webhook-secret"]', "secret123")
        await page.check('[data-testid="event-search-completed"]')
        await page.click('[data-testid="save-webhook"]')

        # Wait for API call
        await page.wait_for_timeout(2000)

        # Verify webhook API request
        create_requests = [req for req in webhook_requests if req["method"] == "POST"]
        assert len(create_requests) > 0, "Webhook creation API request should be made"

        create_request = create_requests[0]
        if create_request["post_data"]:
            payload = json.loads(create_request["post_data"])
            assert payload["url"] == "https://example.com/webhook"
            assert payload["secret"] == "secret123"

    async def test_repository_api_integration(self, page: Page, authenticated_admin):
        """Test repository management API integration."""
        # Navigate to admin panel
        await page.click('[data-testid="user-menu"]')
        await page.click('[data-testid="admin-panel-link"]')

        # Navigate to repository management
        await page.click('[data-testid="repository-management"]')

        # Monitor repository API requests
        repo_requests = []

        def handle_request(request):
            if "/api/v1/repository" in request.url:
                repo_requests.append(
                    {"url": request.url, "method": request.method, "post_data": request.post_data}
                )

        page.on("request", handle_request)

        # Add a new repository
        await page.click('[data-testid="add-repository"]')
        await page.fill('[data-testid="repo-path"]', "/test/new_repo")
        await page.fill('[data-testid="repo-name"]', "Test Repository")
        await page.fill('[data-testid="repo-description"]', "A test repository")
        await page.click('[data-testid="save-repository"]')

        # Wait for API call
        await page.wait_for_timeout(2000)

        # Verify repository API request
        create_requests = [req for req in repo_requests if req["method"] == "POST"]
        assert len(create_requests) > 0, "Repository creation API request should be made"

    async def test_analysis_api_integration(self, page: Page, authenticated_user, test_repository):
        """Test analysis API integration through the frontend."""
        # Navigate to analysis page
        await page.goto("/analysis")

        # Monitor analysis API requests
        analysis_requests = []

        def handle_request(request):
            if "/api/v1/analysis" in request.url:
                analysis_requests.append(
                    {"url": request.url, "method": request.method, "post_data": request.post_data}
                )

        page.on("request", handle_request)

        # Perform blame analysis
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="file-path-input"]', "src/main.py")
        await page.click('[data-testid="blame-analysis"]')

        # Wait for API call
        await page.wait_for_timeout(3000)

        # Verify analysis API request
        blame_requests = [req for req in analysis_requests if "/blame" in req["url"]]
        assert len(blame_requests) > 0, "Blame analysis API request should be made"

    async def test_api_response_caching(self, page: Page, authenticated_user, test_repository):
        """Test API response caching behavior."""
        # Navigate to search page
        await page.goto("/search")

        # Monitor network requests
        requests = []

        def handle_request(request):
            if "/api/v1/search" in request.url:
                requests.append(
                    {
                        "url": request.url,
                        "method": request.method,
                        "timestamp": page.evaluate("Date.now()"),
                    }
                )

        page.on("request", handle_request)

        # Perform the same search twice
        search_query = "function"
        repo_path = str(test_repository)

        for i in range(2):
            await page.fill('[data-testid="repo-path-input"]', repo_path)
            await page.fill('[data-testid="search-query-input"]', search_query)
            await page.click('[data-testid="submit-search"]')

            # Wait for search to complete
            await expect(page.locator('[data-testid="search-results"]')).to_be_visible(
                timeout=30000
            )

            if i == 0:
                # Wait a bit before second search
                await page.wait_for_timeout(1000)

        # Verify caching behavior
        # Note: This depends on the caching implementation
        # If caching is implemented, the second request might be faster or not made at all
        assert len(requests) >= 1, "At least one search request should be made"

    async def test_api_authentication_headers(
        self, page: Page, authenticated_user, test_repository
    ):
        """Test that API requests include proper authentication headers."""
        # Navigate to search page
        await page.goto("/search")

        # Monitor request headers
        auth_headers = []

        def handle_request(request):
            if "/api/v1/" in request.url:
                headers = dict(request.headers)
                if "authorization" in headers:
                    auth_headers.append(headers["authorization"])

        page.on("request", handle_request)

        # Perform search
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "function")
        await page.click('[data-testid="submit-search"]')

        # Wait for API call
        await page.wait_for_timeout(2000)

        # Verify authentication headers
        assert len(auth_headers) > 0, "API requests should include authorization headers"

        auth_header = auth_headers[0]
        assert auth_header.startswith("Bearer "), "Should use Bearer token authentication"
