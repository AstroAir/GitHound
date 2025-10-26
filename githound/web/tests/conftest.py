"""
Pytest configuration and shared fixtures for GitHound web tests.
"""

import asyncio
import os
import tempfile
import uuid
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from githound.web.main import app
from githound.web.services.auth_service import auth_manager

from .fixtures.test_data import TestDataManager
from .fixtures.test_repository import TestRepositoryManager
from .fixtures.test_server import TestServerManager

# Note: pytest-asyncio auto mode is configured in pytest.ini via asyncio_mode = auto


@pytest.fixture(scope="session")
def event_loop() -> Any:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_data_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory(prefix="githound_test_") as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(scope="session")
def test_server(test_data_dir: Path) -> Generator[TestServerManager, None, None]:
    """Start and manage the test server."""
    server_manager = TestServerManager(test_data_dir)
    server_manager.start()
    yield server_manager
    server_manager.stop()


@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI application."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def test_data_manager(test_data_dir: Path) -> TestDataManager:
    """Create test data manager."""
    return TestDataManager(test_data_dir)


@pytest.fixture(scope="session")
def test_repo_manager(test_data_dir: Path) -> TestRepositoryManager:
    """Create test repository manager."""
    return TestRepositoryManager(test_data_dir)


@pytest.fixture(scope="session")
async def browser() -> AsyncGenerator[Browser, None]:
    """Launch browser for testing."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=os.getenv("HEADLESS", "true").lower() == "true",
            slow_mo=int(os.getenv("SLOW_MO", "0")),
        )
        yield browser
        await browser.close()


@pytest.fixture
async def browser_context(browser: Browser) -> AsyncGenerator[BrowserContext, None]:
    """Create a new browser context for each test."""
    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        ignore_https_errors=True,
        record_video_dir="test-results/videos" if os.getenv("RECORD_VIDEO") else None,
    )
    yield context
    await context.close()


@pytest.fixture
async def page(browser_context: BrowserContext) -> AsyncGenerator[Page, None]:
    """Create a new page for each test."""
    page = await browser_context.new_page()
    yield page
    await page.close()


@pytest.fixture
def test_user_data() -> dict[str, Any]:
    """Generate test user data."""
    user_id = str(uuid.uuid4())
    return {
        "user_id": user_id,
        "username": f"testuser_{user_id[:8]}",
        "email": f"test_{user_id[:8]}@example.com",
        "password": "TestPassword123!",
        "roles": ["user"],
    }


@pytest.fixture
def test_admin_data() -> dict[str, Any]:
    """Generate test admin user data."""
    user_id = str(uuid.uuid4())
    return {
        "user_id": user_id,
        "username": f"admin_{user_id[:8]}",
        "email": f"admin_{user_id[:8]}@example.com",
        "password": "AdminPassword123!",
        "roles": ["admin"],
    }


@pytest.fixture
async def authenticated_user(
    page: Page, test_user_data: dict[str, Any], test_server: TestServerManager
) -> None:
    """Create and authenticate a test user."""
    # Create user
    from ..services.auth_service import UserCreate

    user_create_data = UserCreate(
        username=test_user_data["username"],
        email=test_user_data["email"],
        password=test_user_data["password"],
        roles=test_user_data["roles"],
    )
    auth_manager.create_user(user_create_data)

    # Login through the web interface
    await page.goto("/")
    await page.click('[data-testid="login-button"]')
    await page.fill('[data-testid="username-input"]', test_user_data["username"])
    await page.fill('[data-testid="password-input"]', test_user_data["password"])
    await page.click('[data-testid="submit-login"]')

    # Wait for successful login
    await page.wait_for_selector('[data-testid="user-menu"]', timeout=10000)

    # Return None as this is a fixture that sets up authentication


@pytest.fixture
async def authenticated_admin(
    page: Page, test_admin_data: dict[str, Any], test_server: TestServerManager
) -> None:
    """Create and authenticate a test admin user."""
    # Create admin user
    from ..services.auth_service import UserCreate

    user_create_data = UserCreate(
        username=test_admin_data["username"],
        email=test_admin_data["email"],
        password=test_admin_data["password"],
        roles=test_admin_data["roles"],
    )
    auth_manager.create_user(user_create_data)

    # Login through the web interface
    await page.goto("/")
    await page.click('[data-testid="login-button"]')
    await page.fill('[data-testid="username-input"]', test_admin_data["username"])
    await page.fill('[data-testid="password-input"]', test_admin_data["password"])
    await page.click('[data-testid="submit-login"]')

    # Wait for successful login
    await page.wait_for_selector('[data-testid="user-menu"]', timeout=10000)

    # Return None as this is a fixture that sets up authentication


@pytest.fixture
def test_repository(test_repo_manager: TestRepositoryManager) -> Path:
    """Create a test repository with sample data."""
    return test_repo_manager.create_test_repository()


@pytest.fixture(autouse=True)
async def cleanup_after_test() -> AsyncGenerator[None, None]:
    """Clean up after each test."""
    yield
    # Clean up any test data, users, etc.
    # This runs after each test
    pass


# Note: Test markers (auth, search, api, ui, performance, e2e) are defined in pytest.ini
