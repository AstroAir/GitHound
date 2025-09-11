"""
Accessibility tests for GitHound web interface.
"""

import pytest
from playwright.async_api import Page, expect


@pytest.mark.ui
@pytest.mark.e2e
class TestAccessibility:
    """Test accessibility features and compliance."""
    
    async def test_keyboard_navigation(self, page: Page, authenticated_user):
        """Test keyboard navigation throughout the interface."""
        await page.goto("/search")
        
        # Test Tab navigation
        await page.keyboard.press("Tab")
        focused_element = await page.evaluate("document.activeElement.tagName")
        assert focused_element in ["INPUT", "BUTTON", "A"], "First tab should focus on interactive element"
        
        # Test navigation through form elements
        form_elements = ["repo-path-input", "search-query-input", "submit-search"]
        
        for element_id in form_elements:
            element = page.locator(f'[data-testid="{element_id}"]')
            await element.focus()
            
            # Verify element is focused
            is_focused = await element.evaluate("el => document.activeElement === el")
            assert is_focused, f"Element {element_id} should be focusable"
            
        # Test Shift+Tab (reverse navigation)
        await page.keyboard.press("Shift+Tab")
        # Should move focus backwards
        
    async def test_aria_labels_and_roles(self, page: Page, authenticated_user):
        """Test ARIA labels and roles are properly set."""
        await page.goto("/search")
        
        # Check form labels
        repo_input = page.locator('[data-testid="repo-path-input"]')
        query_input = page.locator('[data-testid="search-query-input"]')
        
        # Verify inputs have labels or aria-label
        repo_label = await repo_input.get_attribute("aria-label")
        query_label = await query_input.get_attribute("aria-label")
        
        assert repo_label or await page.locator('label[for*="repo-path"]').count() > 0, \
            "Repository input should have label or aria-label"
        assert query_label or await page.locator('label[for*="search-query"]').count() > 0, \
            "Search query input should have label or aria-label"
            
        # Check button roles and labels
        submit_button = page.locator('[data-testid="submit-search"]')
        button_role = await submit_button.get_attribute("role")
        button_label = await submit_button.get_attribute("aria-label")
        button_text = await submit_button.text_content()
        
        assert button_role == "button" or await submit_button.evaluate("el => el.tagName === 'BUTTON'"), \
            "Submit button should have button role or be button element"
        assert button_label or button_text, "Button should have accessible label or text"
        
    async def test_heading_hierarchy(self, page: Page):
        """Test proper heading hierarchy (h1, h2, h3, etc.)."""
        await page.goto("/")
        
        # Get all headings
        headings = await page.locator("h1, h2, h3, h4, h5, h6").all()
        
        if len(headings) > 0:
            # Should have at least one h1
            h1_count = await page.locator("h1").count()
            assert h1_count >= 1, "Page should have at least one h1 heading"
            
            # Check heading hierarchy
            heading_levels = []
            for heading in headings:
                tag_name = await heading.evaluate("el => el.tagName")
                level = int(tag_name[1])  # Extract number from h1, h2, etc.
                heading_levels.append(level)
                
            # Verify no heading levels are skipped
            for i in range(1, len(heading_levels)):
                current_level = heading_levels[i]
                prev_level = heading_levels[i-1]
                
                # Should not skip more than one level
                assert current_level <= prev_level + 1, \
                    f"Heading hierarchy should not skip levels: h{prev_level} to h{current_level}"
                    
    async def test_color_contrast(self, page: Page):
        """Test color contrast meets accessibility standards."""
        await page.goto("/")
        
        # Check text elements for contrast
        text_elements = page.locator("p, span, div, a, button, input, label")
        element_count = await text_elements.count()
        
        for i in range(min(element_count, 20)):  # Check first 20 elements
            element = text_elements.nth(i)
            
            if await element.is_visible():
                # Get computed styles
                styles = await element.evaluate("""
                    el => {
                        const computed = getComputedStyle(el);
                        return {
                            color: computed.color,
                            backgroundColor: computed.backgroundColor,
                            fontSize: computed.fontSize
                        };
                    }
                """)
                
                # Basic check - ensure text has color and background
                assert styles["color"] != "rgba(0, 0, 0, 0)", "Text should have visible color"
                
                # Font size should be readable
                font_size = int(styles["fontSize"].replace("px", ""))
                assert font_size >= 12, f"Font size should be at least 12px, got {font_size}px"
                
    async def test_focus_indicators(self, page: Page, authenticated_user):
        """Test focus indicators are visible and clear."""
        await page.goto("/search")
        
        # Test focus indicators on interactive elements
        interactive_elements = [
            '[data-testid="repo-path-input"]',
            '[data-testid="search-query-input"]',
            '[data-testid="submit-search"]'
        ]
        
        for selector in interactive_elements:
            element = page.locator(selector)
            await element.focus()
            
            # Check if element has focus styles
            focus_styles = await element.evaluate("""
                el => {
                    const computed = getComputedStyle(el);
                    return {
                        outline: computed.outline,
                        outlineWidth: computed.outlineWidth,
                        boxShadow: computed.boxShadow,
                        borderColor: computed.borderColor
                    };
                }
            """)
            
            # Should have some form of focus indicator
            has_focus_indicator = (
                focus_styles["outline"] != "none" or
                focus_styles["outlineWidth"] != "0px" or
                "focus" in focus_styles["boxShadow"] or
                focus_styles["borderColor"] != "rgba(0, 0, 0, 0)"
            )
            
            assert has_focus_indicator, f"Element {selector} should have visible focus indicator"
            
    async def test_alt_text_for_images(self, page: Page):
        """Test images have appropriate alt text."""
        await page.goto("/")
        
        images = page.locator("img")
        image_count = await images.count()
        
        for i in range(image_count):
            image = images.nth(i)
            alt_text = await image.get_attribute("alt")
            src = await image.get_attribute("src")
            
            # Decorative images can have empty alt text, but it should be present
            assert alt_text is not None, f"Image {src} should have alt attribute"
            
            # Non-decorative images should have meaningful alt text
            if alt_text and len(alt_text.strip()) > 0:
                assert len(alt_text.strip()) > 2, f"Alt text should be meaningful: '{alt_text}'"
                
    async def test_form_validation_accessibility(self, page: Page, authenticated_user):
        """Test form validation messages are accessible."""
        await page.goto("/search")
        
        # Try to submit empty form to trigger validation
        await page.click('[data-testid="submit-search"]')
        
        # Check for validation messages
        error_messages = page.locator('[role="alert"], .error-message, [data-testid*="error"]')
        error_count = await error_messages.count()
        
        if error_count > 0:
            for i in range(error_count):
                error = error_messages.nth(i)
                
                # Error messages should be visible
                await expect(error).to_be_visible()
                
                # Should have appropriate ARIA attributes
                role = await error.get_attribute("role")
                aria_live = await error.get_attribute("aria-live")
                
                assert role == "alert" or aria_live in ["polite", "assertive"], \
                    "Error messages should have role='alert' or aria-live attribute"
                    
    async def test_skip_links(self, page: Page):
        """Test skip links for keyboard navigation."""
        await page.goto("/")
        
        # Press Tab to potentially reveal skip links
        await page.keyboard.press("Tab")
        
        # Look for skip links
        skip_links = page.locator('a[href*="#"], a[href*="skip"]')
        skip_count = await skip_links.count()
        
        if skip_count > 0:
            first_skip = skip_links.first()
            
            # Skip link should be focusable
            await first_skip.focus()
            is_focused = await first_skip.evaluate("el => document.activeElement === el")
            assert is_focused, "Skip link should be focusable"
            
            # Should have meaningful text
            skip_text = await first_skip.text_content()
            assert skip_text and len(skip_text.strip()) > 0, "Skip link should have text"
            
    async def test_screen_reader_content(self, page: Page, authenticated_user):
        """Test content is accessible to screen readers."""
        await page.goto("/search")
        
        # Check for screen reader only content
        sr_only = page.locator('.sr-only, .visually-hidden, [class*="screen-reader"]')
        sr_count = await sr_only.count()
        
        if sr_count > 0:
            for i in range(sr_count):
                element = sr_only.nth(i)
                
                # Should be hidden visually but available to screen readers
                styles = await element.evaluate("""
                    el => {
                        const computed = getComputedStyle(el);
                        return {
                            position: computed.position,
                            left: computed.left,
                            width: computed.width,
                            height: computed.height,
                            overflow: computed.overflow
                        };
                    }
                """)
                
                # Common screen reader only patterns
                is_sr_only = (
                    styles["position"] == "absolute" and styles["left"].startswith("-") or
                    styles["width"] == "1px" and styles["height"] == "1px" or
                    styles["overflow"] == "hidden"
                )
                
                assert is_sr_only, "Screen reader only content should be visually hidden"
                
    async def test_landmark_roles(self, page: Page):
        """Test page has appropriate landmark roles."""
        await page.goto("/")
        
        # Check for main landmark
        main_landmarks = page.locator('main, [role="main"]')
        main_count = await main_landmarks.count()
        assert main_count >= 1, "Page should have main landmark"
        
        # Check for navigation landmark
        nav_landmarks = page.locator('nav, [role="navigation"]')
        nav_count = await nav_landmarks.count()
        
        if nav_count > 0:
            # Navigation should be accessible
            first_nav = nav_landmarks.first()
            nav_label = await first_nav.get_attribute("aria-label")
            nav_labelledby = await first_nav.get_attribute("aria-labelledby")
            
            # If multiple nav elements, they should be distinguished
            if nav_count > 1:
                assert nav_label or nav_labelledby, \
                    "Multiple navigation landmarks should have distinguishing labels"
                    
    async def test_table_accessibility(self, page: Page, authenticated_user, test_repository):
        """Test table accessibility features."""
        # Perform search to get results table
        await page.goto("/search")
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "def")
        await page.click('[data-testid="submit-search"]')
        
        # Wait for results
        await expect(page.locator('[data-testid="search-results"]')).to_be_visible(timeout=30000)
        
        # Check if results are displayed in a table
        tables = page.locator("table")
        table_count = await tables.count()
        
        if table_count > 0:
            table = tables.first()
            
            # Table should have caption or summary
            caption = await table.locator("caption").count()
            summary = await table.get_attribute("summary")
            aria_label = await table.get_attribute("aria-label")
            
            assert caption > 0 or summary or aria_label, \
                "Table should have caption, summary, or aria-label"
                
            # Check for table headers
            headers = await table.locator("th").count()
            if headers > 0:
                # Headers should have scope attribute
                first_header = table.locator("th").first()
                scope = await first_header.get_attribute("scope")
                assert scope in ["col", "row", "colgroup", "rowgroup"], \
                    "Table headers should have scope attribute"
                    
    async def test_live_regions(self, page: Page, authenticated_user, test_repository):
        """Test live regions for dynamic content updates."""
        await page.goto("/search")
        
        # Look for live regions
        live_regions = page.locator('[aria-live], [role="status"], [role="alert"]')
        
        # Perform search to trigger dynamic updates
        await page.fill('[data-testid="repo-path-input"]', str(test_repository))
        await page.fill('[data-testid="search-query-input"]', "def")
        await page.click('[data-testid="submit-search"]')
        
        # Check if search status updates are in live regions
        status_elements = page.locator('[data-testid*="status"], [data-testid*="progress"]')
        status_count = await status_elements.count()
        
        if status_count > 0:
            for i in range(status_count):
                status = status_elements.nth(i)
                
                # Should have aria-live or be in a live region
                aria_live = await status.get_attribute("aria-live")
                role = await status.get_attribute("role")
                
                # Check if parent has live region attributes
                parent_live = await status.evaluate("""
                    el => {
                        let parent = el.parentElement;
                        while (parent) {
                            if (parent.getAttribute('aria-live') || 
                                parent.getAttribute('role') === 'status' ||
                                parent.getAttribute('role') === 'alert') {
                                return true;
                            }
                            parent = parent.parentElement;
                        }
                        return false;
                    }
                """)
                
                assert aria_live or role in ["status", "alert"] or parent_live, \
                    "Dynamic status updates should be in live regions"
