"""
Responsive design tests for GitHound web interface.
"""

import pytest
from playwright.async_api import Page, expect


@pytest.mark.ui
@pytest.mark.e2e
class TestResponsiveDesign:
    """Test responsive design across different screen sizes."""

    async def test_mobile_layout(self, page: Page, authenticated_user):
        """Test mobile layout and functionality."""
        # Set mobile viewport
        await page.set_viewport_size({"width": 375, "height": 667})  # iPhone SE

        # Navigate to search page
        await page.goto("/search")

        # Verify mobile navigation
        await expect(page.locator('[data-testid="mobile-menu-button"]')).to_be_visible()

        # Test mobile menu functionality
        await page.click('[data-testid="mobile-menu-button"]')
        await expect(page.locator('[data-testid="mobile-menu"]')).to_be_visible()

        # Verify search form is responsive
        search_form = page.locator('[data-testid="search-form"]')
        await expect(search_form).to_be_visible()

        # Check that form elements stack vertically on mobile
        form_width = await search_form.bounding_box()
        assert form_width["width"] <= 375, "Search form should fit mobile width"

    async def test_tablet_layout(self, page: Page, authenticated_user):
        """Test tablet layout and functionality."""
        # Set tablet viewport
        await page.set_viewport_size({"width": 768, "height": 1024})  # iPad

        # Navigate to search page
        await page.goto("/search")

        # Verify tablet navigation (should show full nav, not mobile menu)
        await expect(page.locator('[data-testid="desktop-navigation"]')).to_be_visible()
        await expect(page.locator('[data-testid="mobile-menu-button"]')).not_to_be_visible()

        # Verify search form layout
        search_form = page.locator('[data-testid="search-form"]')
        await expect(search_form).to_be_visible()

        # Check form responsiveness
        form_box = await search_form.bounding_box()
        assert form_box["width"] <= 768, "Search form should fit tablet width"

    async def test_desktop_layout(self, page: Page, authenticated_user):
        """Test desktop layout and functionality."""
        # Set desktop viewport
        await page.set_viewport_size({"width": 1920, "height": 1080})

        # Navigate to search page
        await page.goto("/search")

        # Verify desktop navigation
        await expect(page.locator('[data-testid="desktop-navigation"]')).to_be_visible()
        await expect(page.locator('[data-testid="mobile-menu-button"]')).not_to_be_visible()

        # Verify full-width layout
        main_content = page.locator('[data-testid="main-content"]')
        await expect(main_content).to_be_visible()

        # Check that sidebar is visible on desktop
        await expect(page.locator('[data-testid="sidebar"]')).to_be_visible()

    async def test_search_results_responsive(self, page: Page, authenticated_user, test_repository):
        """Test search results display across different screen sizes."""
        viewports = [
            {"width": 375, "height": 667, "name": "mobile"},
            {"width": 768, "height": 1024, "name": "tablet"},
            {"width": 1920, "height": 1080, "name": "desktop"},
        ]

        for viewport in viewports:
            # Set viewport
            await page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})

            # Navigate to search page
            await page.goto("/search")

            # Perform search
            await page.fill('[data-testid="repo-path-input"]', str(test_repository))
            await page.fill('[data-testid="search-query-input"]', "def")
            await page.click('[data-testid="submit-search"]')

            # Wait for results
            await expect(page.locator('[data-testid="search-results"]')).to_be_visible(
                timeout=30000
            )

            # Verify results container fits viewport
            results_container = page.locator('[data-testid="search-results"]')
            container_box = await results_container.bounding_box()

            assert (
                container_box["width"] <= viewport["width"]
            ), f"Results should fit {viewport['name']} width"

            # Verify result cards are responsive
            result_cards = page.locator('[data-testid="result-card"]')
            if await result_cards.count() > 0:
                first_card = result_cards.first()
                card_box = await first_card.bounding_box()
                assert (
                    card_box["width"] <= viewport["width"] - 40  # type: ignore[operator]
                ), f"Result cards should fit {viewport['name']} with margin"

    async def test_navigation_responsive(self, page: Page, authenticated_user):
        """Test navigation responsiveness."""
        # Test mobile navigation
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.goto("/")

        # Mobile should show hamburger menu
        await expect(page.locator('[data-testid="mobile-menu-button"]')).to_be_visible()
        await expect(page.locator('[data-testid="desktop-navigation"]')).not_to_be_visible()

        # Test mobile menu functionality
        await page.click('[data-testid="mobile-menu-button"]')
        mobile_menu = page.locator('[data-testid="mobile-menu"]')
        await expect(mobile_menu).to_be_visible()

        # Verify menu items are accessible
        await expect(mobile_menu.locator('[data-testid="nav-search"]')).to_be_visible()
        await expect(mobile_menu.locator('[data-testid="nav-analysis"]')).to_be_visible()

        # Test desktop navigation
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.reload()

        # Desktop should show full navigation
        await expect(page.locator('[data-testid="desktop-navigation"]')).to_be_visible()
        await expect(page.locator('[data-testid="mobile-menu-button"]')).not_to_be_visible()

    async def test_form_elements_responsive(self, page: Page, authenticated_user):
        """Test form elements responsiveness."""
        viewports = [
            {"width": 375, "height": 667},  # Mobile
            {"width": 768, "height": 1024},  # Tablet
            {"width": 1920, "height": 1080},  # Desktop
        ]

        for viewport in viewports:
            await page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
            await page.goto("/search")

            # Test input field responsiveness
            repo_input = page.locator('[data-testid="repo-path-input"]')
            query_input = page.locator('[data-testid="search-query-input"]')

            await expect(repo_input).to_be_visible()
            await expect(query_input).to_be_visible()

            # Verify inputs fit viewport
            repo_box = await repo_input.bounding_box()
            query_box = await query_input.bounding_box()

            assert (
                repo_box["width"] <= viewport["width"] - 40
            ), "Repo input should fit viewport with margin"
            assert (
                query_box["width"] <= viewport["width"] - 40
            ), "Query input should fit viewport with margin"

            # Test button responsiveness
            submit_button = page.locator('[data-testid="submit-search"]')
            await expect(submit_button).to_be_visible()

            button_box = await submit_button.bounding_box()
            assert (
                button_box["width"] <= viewport["width"] - 40
            ), "Submit button should fit viewport"

    async def test_table_responsive(self, page: Page, authenticated_user, test_repository):
        """Test table responsiveness in search results."""
        # Perform search to get results
        await page.goto("/search")
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "def")
        await page.click('[data-testid="submit-search"]')

        # Wait for results
        await expect(page.locator('[data-testid="search-results"]')).to_be_visible(timeout=30000)

        # Test mobile table view
        await page.set_viewport_size({"width": 375, "height": 667})

        # On mobile, table should either:
        # 1. Be horizontally scrollable, or
        # 2. Stack columns vertically, or
        # 3. Show as cards instead of table

        results_table = page.locator('[data-testid="results-table"]')
        if await results_table.is_visible():
            # Check if table is scrollable or responsive
            table_box = await results_table.bounding_box()

            # Table should either fit or be scrollable
            if table_box["width"] > 375:
                # Should have horizontal scroll
                overflow_x = await results_table.evaluate("el => getComputedStyle(el).overflowX")
                assert overflow_x in [
                    "auto",
                    "scroll",
                ], "Wide table should be horizontally scrollable on mobile"
        else:
            # Results might be displayed as cards on mobile
            await expect(page.locator('[data-testid="result-card"]')).to_be_visible()

    async def test_image_responsive(self, page: Page):
        """Test image responsiveness."""
        await page.goto("/")

        viewports = [
            {"width": 375, "height": 667},
            {"width": 768, "height": 1024},
            {"width": 1920, "height": 1080},
        ]

        for viewport in viewports:
            await page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
            await page.reload()

            # Check logo/images are responsive
            images = page.locator("img")
            image_count = await images.count()

            for i in range(image_count):
                image = images.nth(i)
                if await image.is_visible():
                    image_box = await image.bounding_box()
                    assert (
                        image_box["width"] <= viewport["width"]
                    ), f"Image should fit viewport width"

    async def test_text_readability_responsive(self, page: Page, authenticated_user):
        """Test text readability across different screen sizes."""
        await page.goto("/")

        viewports = [
            {"width": 375, "height": 667, "name": "mobile"},
            {"width": 768, "height": 1024, "name": "tablet"},
            {"width": 1920, "height": 1080, "name": "desktop"},
        ]

        for viewport in viewports:
            await page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
            await page.reload()

            # Check font sizes are appropriate
            body_text = page.locator("body")
            font_size = await body_text.evaluate("el => getComputedStyle(el).fontSize")

            # Font size should be at least 14px for readability
            font_size_px = int(font_size.replace("px", ""))
            assert font_size_px >= 14, f"Font size should be at least 14px on {viewport['name']}"

            # Check line height for readability
            line_height = await body_text.evaluate("el => getComputedStyle(el).lineHeight")
            if line_height != "normal":
                line_height_value = float(line_height.replace("px", ""))
                assert (
                    line_height_value >= font_size_px * 1.2
                ), f"Line height should be at least 1.2x font size on {viewport['name']}"

    async def test_touch_targets_mobile(self, page: Page, authenticated_user):
        """Test touch targets are appropriately sized for mobile."""
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.goto("/search")

        # Check button sizes meet minimum touch target requirements (44px)
        buttons = page.locator("button")
        button_count = await buttons.count()

        for i in range(min(button_count, 10)):  # Check first 10 buttons
            button = buttons.nth(i)
            if await button.is_visible():
                button_box = await button.bounding_box()

                # Minimum touch target size should be 44x44px
                assert (
                    button_box["height"] >= 44 or button_box["width"] >= 44
                ), f"Button {i} should meet minimum touch target size (44px)"

        # Check link targets
        links = page.locator("a")
        link_count = await links.count()

        for i in range(min(link_count, 10)):  # Check first 10 links
            link = links.nth(i)
            if await link.is_visible():
                link_box = await link.bounding_box()

                # Links should also meet touch target requirements
                assert (
                    link_box["height"] >= 44 or link_box["width"] >= 44
                ), f"Link {i} should meet minimum touch target size (44px)"
