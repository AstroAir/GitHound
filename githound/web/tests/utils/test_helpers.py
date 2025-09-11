"""
Test helper utilities for GitHound web tests.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from playwright.async_api import Page, Locator, expect


class TestHelpers:
    """Helper utilities for web tests."""
    
    @staticmethod
    async def wait_for_element_with_text(page: Page, selector: str, text: str, timeout: int = 10000) -> Locator:
        """Wait for an element with specific text to appear."""
        element = page.locator(selector).filter(has_text=text)
        await expect(element).to_be_visible(timeout=timeout)
        return element
    
    @staticmethod
    async def wait_for_api_call(page: Page, url_pattern: str, timeout: int = 10000) -> Dict[str, Any]:
        """Wait for a specific API call and return request details."""
        api_call = {}
        
        def handle_request(request):
            if url_pattern in request.url:
                api_call.update({
                    "url": request.url,
                    "method": request.method,
                    "headers": dict(request.headers),
                    "post_data": request.post_data
                })
        
        page.on("request", handle_request)
        
        # Wait for the API call
        start_time = time.time()
        while not api_call and (time.time() - start_time) * 1000 < timeout:
            await asyncio.sleep(0.1)
            
        if not api_call:
            raise TimeoutError(f"API call to {url_pattern} not detected within {timeout}ms")
            
        return api_call
    
    @staticmethod
    async def fill_search_form(page: Page, repo_path: str, query: str, **filters) -> None:
        """Fill the search form with given parameters."""
        await page.fill('[data-testid="repo-path-input"]', repo_path)
        await page.fill('[data-testid="search-query-input"]', query)
        
        # Apply filters if provided
        if filters.get("file_types"):
            await page.click('[data-testid="filters-tab"]')
            for file_type in filters["file_types"]:
                await page.check(f'[data-testid="file-type-{file_type}"]')
                
        if filters.get("author"):
            await page.fill('[data-testid="author-filter"]', filters["author"])
            
        if filters.get("max_results"):
            await page.fill('[data-testid="max-results"]', str(filters["max_results"]))
    
    @staticmethod
    async def perform_login(page: Page, username: str, password: str) -> None:
        """Perform user login."""
        await page.goto("/")
        await page.click('[data-testid="login-button"]')
        await page.fill('[data-testid="username-input"]', username)
        await page.fill('[data-testid="password-input"]', password)
        await page.click('[data-testid="submit-login"]')
        
        # Wait for successful login
        await expect(page.locator('[data-testid="user-menu"]')).to_be_visible(timeout=10000)
    
    @staticmethod
    async def perform_logout(page: Page) -> None:
        """Perform user logout."""
        await page.click('[data-testid="user-menu"]')
        await page.click('[data-testid="logout-button"]')
        
        # Wait for logout to complete
        await expect(page.locator('[data-testid="login-button"]')).to_be_visible(timeout=10000)
    
    @staticmethod
    async def wait_for_search_completion(page: Page, timeout: int = 30000) -> None:
        """Wait for search to complete."""
        # Wait for search results or error
        await page.wait_for_function("""
            () => {
                const results = document.querySelector('[data-testid="search-results"]');
                const error = document.querySelector('[data-testid="search-error"]');
                const cancelled = document.querySelector('[data-testid="search-cancelled"]');
                return results || error || cancelled;
            }
        """, timeout=timeout)
    
    @staticmethod
    async def get_search_results_count(page: Page) -> int:
        """Get the number of search results displayed."""
        result_cards = page.locator('[data-testid="result-card"]')
        return await result_cards.count()
    
    @staticmethod
    async def get_search_result_data(page: Page, index: int = 0) -> Dict[str, str]:
        """Get data from a specific search result."""
        result_card = page.locator('[data-testid="result-card"]').nth(index)
        
        return {
            "file_path": await result_card.locator('[data-testid="file-path"]').text_content() or "",
            "line_number": await result_card.locator('[data-testid="line-number"]').text_content() or "",
            "content": await result_card.locator('[data-testid="code-content"]').text_content() or "",
            "commit_hash": await result_card.locator('[data-testid="commit-hash"]').text_content() or "",
            "author": await result_card.locator('[data-testid="author"]').text_content() or "",
        }
    
    @staticmethod
    async def check_accessibility_violations(page: Page) -> List[Dict[str, Any]]:
        """Check for accessibility violations using axe-core."""
        try:
            # Inject axe-core
            await page.add_script_tag(url="https://unpkg.com/axe-core@4.7.0/axe.min.js")
            
            # Run accessibility scan
            violations = await page.evaluate("""
                async () => {
                    const results = await axe.run();
                    return results.violations;
                }
            """)
            
            return violations
        except Exception as e:
            print(f"Accessibility check failed: {e}")
            return []
    
    @staticmethod
    async def take_screenshot_on_failure(page: Page, test_name: str) -> str:
        """Take a screenshot when a test fails."""
        timestamp = int(time.time())
        filename = f"test-results/screenshots/{test_name}_{timestamp}.png"
        await page.screenshot(path=filename, full_page=True)
        return filename
    
    @staticmethod
    async def get_console_errors(page: Page) -> List[str]:
        """Get console errors from the page."""
        errors = []
        
        def handle_console(msg):
            if msg.type == "error":
                errors.append(msg.text)
        
        page.on("console", handle_console)
        return errors
    
    @staticmethod
    async def wait_for_websocket_message(page: Page, message_type: str, timeout: int = 10000) -> Dict[str, Any]:
        """Wait for a specific WebSocket message type."""
        message_received = {}
        
        await page.evaluate(f"""
            window.testWebSocketMessage = null;
            if (window.websocketManager) {{
                window.websocketManager.onMessage((message) => {{
                    if (message.type === '{message_type}') {{
                        window.testWebSocketMessage = message;
                    }}
                }});
            }}
        """)
        
        # Wait for the message
        await page.wait_for_function("""
            () => window.testWebSocketMessage !== null
        """, timeout=timeout)
        
        message_received = await page.evaluate("() => window.testWebSocketMessage")
        return message_received
    
    @staticmethod
    async def simulate_network_condition(page: Page, condition: str) -> None:
        """Simulate different network conditions."""
        conditions = {
            "slow_3g": {"download": 500 * 1024, "upload": 500 * 1024, "latency": 400},
            "fast_3g": {"download": 1.6 * 1024 * 1024, "upload": 750 * 1024, "latency": 150},
            "offline": {"download": 0, "upload": 0, "latency": 0}
        }
        
        if condition in conditions:
            await page.context.set_extra_http_headers({})
            # Note: Playwright doesn't have built-in network throttling
            # This would need to be implemented with a proxy or browser flags
    
    @staticmethod
    async def verify_responsive_layout(page: Page, viewport_width: int) -> Dict[str, bool]:
        """Verify responsive layout at given viewport width."""
        await page.set_viewport_size({"width": viewport_width, "height": 720})
        
        checks = {
            "mobile_menu_visible": False,
            "desktop_nav_visible": False,
            "content_fits_viewport": False,
            "text_readable": False
        }
        
        # Check mobile menu visibility
        mobile_menu = page.locator('[data-testid="mobile-menu-button"]')
        checks["mobile_menu_visible"] = await mobile_menu.is_visible()
        
        # Check desktop navigation visibility
        desktop_nav = page.locator('[data-testid="desktop-navigation"]')
        checks["desktop_nav_visible"] = await desktop_nav.is_visible()
        
        # Check content fits viewport
        main_content = page.locator('[data-testid="main-content"]')
        if await main_content.is_visible():
            content_box = await main_content.bounding_box()
            checks["content_fits_viewport"] = content_box["width"] <= viewport_width
        
        # Check text readability
        body = page.locator("body")
        font_size = await body.evaluate("el => getComputedStyle(el).fontSize")
        font_size_px = int(font_size.replace("px", ""))
        checks["text_readable"] = font_size_px >= 14
        
        return checks
    
    @staticmethod
    async def measure_performance_metrics(page: Page) -> Dict[str, float]:
        """Measure page performance metrics."""
        metrics = await page.evaluate("""
            () => {
                const navigation = performance.getEntriesByType('navigation')[0];
                const paint = performance.getEntriesByType('paint');
                
                return {
                    domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                    loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                    firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
                    firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0,
                    totalLoadTime: navigation.loadEventEnd - navigation.fetchStart
                };
            }
        """)
        
        return metrics
    
    @staticmethod
    async def verify_form_validation(page: Page, form_selector: str, required_fields: List[str]) -> Dict[str, bool]:
        """Verify form validation for required fields."""
        validation_results = {}
        
        # Try to submit empty form
        await page.click(f'{form_selector} [type="submit"]')
        
        # Check validation messages for each required field
        for field in required_fields:
            error_selector = f'[data-testid="{field}-error"]'
            error_element = page.locator(error_selector)
            validation_results[field] = await error_element.is_visible()
        
        return validation_results
    
    @staticmethod
    async def wait_for_element_count(page: Page, selector: str, expected_count: int, timeout: int = 10000) -> bool:
        """Wait for a specific number of elements to appear."""
        try:
            await page.wait_for_function(f"""
                () => document.querySelectorAll('{selector}').length === {expected_count}
            """, timeout=timeout)
            return True
        except:
            return False
