"""
Search interface tests for GitHound web interface.
"""

import pytest
from playwright.async_api import Page, expect


@pytest.mark.search
@pytest.mark.e2e
class TestSearchInterface:
    """Test search interface functionality."""

    async def test_advanced_search_form(self, page: Page, authenticated_user, test_repository):
        """Test advanced search form functionality."""
        # Navigate to search page
        await page.goto("/search")

        # Fill advanced search form
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "function")

        # Set search filters
        await page.click('[data-testid="filters-tab"]')
        await page.check('[data-testid="file-type-py"]')
        await page.check('[data-testid="file-type-js"]')
        await page.fill('[data-testid="author-filter"]', "test@example.com")
        await page.fill('[data-testid="max-results"]', "50")

        # Submit search
        await page.click('[data-testid="submit-search"]')

        # Verify search is initiated
        await expect(page.locator('[data-testid="search-progress"]')).to_be_visible()
        await expect(page.locator('[data-testid="search-status"]')).to_contain_text("Searching...")

    async def test_fuzzy_search_functionality(
        self, page: Page, authenticated_user, test_repository
    ):
        """Test fuzzy search functionality."""
        # Navigate to search page
        await page.goto("/search")

        # Switch to fuzzy search tab
        await page.click('[data-testid="fuzzy-search-tab"]')

        # Fill fuzzy search form
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="fuzzy-query-input"]', "functon")  # Intentional typo
        await page.fill('[data-testid="fuzzy-threshold"]', "0.8")

        # Submit fuzzy search
        await page.click('[data-testid="submit-fuzzy-search"]')

        # Verify search is initiated
        await expect(page.locator('[data-testid="search-progress"]')).to_be_visible()
        await expect(page.locator('[data-testid="search-type-indicator"]')).to_contain_text(
            "Fuzzy Search"
        )

    async def test_historical_search_functionality(
        self, page: Page, authenticated_user, test_repository
    ):
        """Test historical search functionality."""
        # Navigate to search page
        await page.goto("/search")

        # Switch to historical search tab
        await page.click('[data-testid="historical-search-tab"]')

        # Fill historical search form
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="historical-query-input"]', "class")
        await page.fill('[data-testid="commit-from"]', "HEAD~5")
        await page.fill('[data-testid="commit-to"]', "HEAD")

        # Submit historical search
        await page.click('[data-testid="submit-historical-search"]')

        # Verify search is initiated
        await expect(page.locator('[data-testid="search-progress"]')).to_be_visible()
        await expect(page.locator('[data-testid="search-type-indicator"]')).to_contain_text(
            "Historical Search"
        )

    async def test_search_results_display(self, page: Page, authenticated_user, test_repository):
        """Test search results display and formatting."""
        # Perform a search
        await page.goto("/search")
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "def")
        await page.click('[data-testid="submit-search"]')

        # Wait for results
        await expect(page.locator('[data-testid="search-results"]')).to_be_visible(timeout=30000)

        # Verify result structure
        result_cards = page.locator('[data-testid="result-card"]')
        await expect(result_cards.first()).to_be_visible()

        # Check result card content
        first_result = result_cards.first()
        await expect(first_result.locator('[data-testid="file-path"]')).to_be_visible()
        await expect(first_result.locator('[data-testid="line-number"]')).to_be_visible()
        await expect(first_result.locator('[data-testid="code-content"]')).to_be_visible()
        await expect(first_result.locator('[data-testid="commit-info"]')).to_be_visible()

    async def test_search_pagination(self, page: Page, authenticated_user, test_repository):
        """Test search results pagination."""
        # Perform a search that should return many results
        await page.goto("/search")
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "import")
        await page.fill('[data-testid="max-results"]', "100")
        await page.click('[data-testid="submit-search"]')

        # Wait for results
        await expect(page.locator('[data-testid="search-results"]')).to_be_visible(timeout=30000)

        # Check if pagination is present
        pagination = page.locator('[data-testid="pagination"]')
        if await pagination.is_visible():
            # Test pagination navigation
            await page.click('[data-testid="next-page"]')
            await expect(page.locator('[data-testid="current-page"]')).to_contain_text("2")

            await page.click('[data-testid="prev-page"]')
            await expect(page.locator('[data-testid="current-page"]')).to_contain_text("1")

    async def test_search_filters_application(
        self, page: Page, authenticated_user, test_repository
    ):
        """Test search filters are properly applied."""
        # Navigate to search page
        await page.goto("/search")

        # Fill search form with filters
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "def")

        # Apply file type filter
        await page.click('[data-testid="filters-tab"]')
        await page.check('[data-testid="file-type-py"]')
        await page.uncheck('[data-testid="file-type-js"]')

        # Submit search
        await page.click('[data-testid="submit-search"]')

        # Wait for results
        await expect(page.locator('[data-testid="search-results"]')).to_be_visible(timeout=30000)

        # Verify all results are from Python files
        result_cards = page.locator('[data-testid="result-card"]')
        count = await result_cards.count()

        for i in range(min(count, 5)):  # Check first 5 results
            file_path = (
                await result_cards.nth(i).locator('[data-testid="file-path"]').text_content()
            )
            assert file_path.endswith(".py"), f"Expected Python file, got: {file_path}"

    async def test_search_error_handling(self, page: Page, authenticated_user):
        """Test search error handling for invalid inputs."""
        # Navigate to search page
        await page.goto("/search")

        # Try to search with invalid repository path
        await page.fill('[data-testid="repo-path-input"]', "/nonexistent/repo")
        await page.fill('[data-testid="search-query-input"]', "function")
        await page.click('[data-testid="submit-search"]')

        # Verify error message
        await expect(page.locator('[data-testid="search-error"]')).to_be_visible()
        await expect(page.locator('[data-testid="search-error"]')).to_contain_text(
            "Repository not found"
        )

    async def test_search_form_validation(self, page: Page, authenticated_user):
        """Test search form validation."""
        # Navigate to search page
        await page.goto("/search")

        # Try to submit empty form
        await page.click('[data-testid="submit-search"]')

        # Verify validation errors
        await expect(page.locator('[data-testid="repo-path-error"]')).to_be_visible()
        await expect(page.locator('[data-testid="query-error"]')).to_be_visible()

        # Fill only repository path
        await page.fill('[data-testid="repo-path-input"]', "/test/repo")
        await page.click('[data-testid="submit-search"]')

        # Verify query is still required
        await expect(page.locator('[data-testid="query-error"]')).to_be_visible()

    async def test_search_cancellation(self, page: Page, authenticated_user, test_repository):
        """Test search cancellation functionality."""
        # Start a search
        await page.goto("/search")
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "function")
        await page.click('[data-testid="submit-search"]')

        # Verify search is running
        await expect(page.locator('[data-testid="search-progress"]')).to_be_visible()

        # Cancel the search
        await page.click('[data-testid="cancel-search"]')

        # Verify search is cancelled
        await expect(page.locator('[data-testid="search-cancelled"]')).to_be_visible()
        await expect(page.locator('[data-testid="search-progress"]')).not_to_be_visible()

    async def test_search_export_functionality(
        self, page: Page, authenticated_user, test_repository
    ):
        """Test search results export functionality."""
        # Perform a search
        await page.goto("/search")
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "def")
        await page.click('[data-testid="submit-search"]')

        # Wait for results
        await expect(page.locator('[data-testid="search-results"]')).to_be_visible(timeout=30000)

        # Test export functionality
        await page.click('[data-testid="export-button"]')

        # Select export format
        await page.select_option('[data-testid="export-format"]', "json")
        await page.click('[data-testid="confirm-export"]')

        # Verify export is initiated
        await expect(page.locator('[data-testid="export-progress"]')).to_be_visible()

    async def test_search_history(self, page: Page, authenticated_user, test_repository):
        """Test search history functionality."""
        # Perform multiple searches
        searches = ["function", "class", "import"]

        for query in searches:
            await page.goto("/search")
            await page.fill('[data-testid="repo-path-input"]', str(test_repository))
            await page.fill('[data-testid="search-query-input"]', query)
            await page.click('[data-testid="submit-search"]')

            # Wait for search to complete
            await expect(page.locator('[data-testid="search-results"]')).to_be_visible(
                timeout=30000
            )

        # Check search history
        await page.click('[data-testid="search-history-tab"]')

        # Verify search history contains our searches
        history_items = page.locator('[data-testid="history-item"]')
        await expect(history_items).to_have_count(3)

        # Test clicking on a history item
        await history_items.first().click()

        # Verify the search form is populated
        query_input = page.locator('[data-testid="search-query-input"]')
        await expect(query_input).to_have_value(searches[-1])  # Most recent search
