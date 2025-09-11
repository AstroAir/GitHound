"""
Unit tests for webhook system.

Tests webhook event triggering, delivery, retry logic, and management functionality.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import aiohttp

from githound.web.webhooks import (
    WebhookEvent,
    WebhookEndpoint,
    WebhookDelivery,
    WebhookManager,
    EventTypes,
    trigger_repository_event,
    trigger_search_event
)


@pytest.fixture
def webhook_manager() -> None:
    """Create WebhookManager instance for testing."""
    return WebhookManager()


@pytest.fixture
def sample_webhook_endpoint() -> None:
    """Create sample webhook endpoint for testing."""
    return WebhookEndpoint(
        id="test-webhook-1",
        url="https://example.com/webhook",
        events=["repository.created", "branch.merged"],
        secret="test-secret",
        active=True
    )


@pytest.fixture
def sample_webhook_event() -> None:
    """Create sample webhook event for testing."""
    return WebhookEvent(
        event_type="repository.created",
        event_id="event-123",
        repository_path="/test/repo",
        user_id="test-user",
        data={"status": "created", "path": "/test/repo"}
    )


class TestWebhookEvent:
    """Test WebhookEvent model."""

    def test_webhook_event_creation(self) -> None:
        """Test webhook event creation."""
        event = WebhookEvent(
            event_type="repository.created",
            event_id="event-123",
            repository_path="/test/repo",
            user_id="test-user",
            data={"status": "created"}
        )

        assert event.event_type = = "repository.created"
        assert event.event_id = = "event-123"
        assert event.repository_path = = "/test/repo"
        assert event.user_id = = "test-user"
        assert event.data = = {"status": "created"}
        assert isinstance(event.timestamp, datetime)

    def test_webhook_event_default_timestamp(self) -> None:
        """Test webhook event with default timestamp."""
        event = WebhookEvent(
            event_type="branch.created",
            event_id="event-456",
            repository_path="/test/repo",
            user_id="test-user",
            data={}
        )

        # Timestamp should be recent
        time_diff = datetime.now() - event.timestamp
        assert time_diff.total_seconds() < 1


class TestWebhookEndpoint:
    """Test WebhookEndpoint model."""

    def test_webhook_endpoint_creation(self, sample_webhook_endpoint) -> None:
        """Test webhook endpoint creation."""
        endpoint = sample_webhook_endpoint

        assert endpoint.id = = "test-webhook-1"
        assert endpoint.url = = "https://example.com/webhook"
        assert endpoint.events = = ["repository.created", "branch.merged"]
        assert endpoint.secret = = "test-secret"
        assert endpoint.active is True
        assert isinstance(endpoint.created_at, datetime)
        assert endpoint.failure_count = = 0
        assert endpoint.max_failures = = 5

    def test_webhook_endpoint_defaults(self) -> None:
        """Test webhook endpoint with default values."""
        endpoint = WebhookEndpoint(
            id="test-webhook-2",
            url="https://example.com/webhook2",
            events=["commit.created"]
        )

        assert endpoint.secret is None
        assert endpoint.active is True
        assert endpoint.failure_count = = 0
        assert endpoint.max_failures = = 5
        assert endpoint.last_delivery is None


class TestWebhookManager:
    """Test WebhookManager functionality."""

    def test_add_endpoint(self, webhook_manager, sample_webhook_endpoint) -> None:
        """Test adding webhook endpoint."""
        endpoint_id = webhook_manager.add_endpoint(sample_webhook_endpoint)

        assert endpoint_id == sample_webhook_endpoint.id
        assert sample_webhook_endpoint.id in webhook_manager.endpoints
        assert webhook_manager.endpoints[sample_webhook_endpoint.id] == sample_webhook_endpoint

    def test_remove_endpoint(self, webhook_manager, sample_webhook_endpoint) -> None:
        """Test removing webhook endpoint."""
        # Add endpoint first
        webhook_manager.add_endpoint(sample_webhook_endpoint)

        # Remove endpoint
        result = webhook_manager.remove_endpoint(sample_webhook_endpoint.id)

        assert result is True
        assert sample_webhook_endpoint.id not in webhook_manager.endpoints

    def test_remove_nonexistent_endpoint(self, webhook_manager) -> None:
        """Test removing non-existent endpoint."""
        result = webhook_manager.remove_endpoint("nonexistent-id")
        assert result is False

    def test_get_endpoint(self, webhook_manager, sample_webhook_endpoint) -> None:
        """Test getting webhook endpoint."""
        webhook_manager.add_endpoint(sample_webhook_endpoint)

        endpoint = webhook_manager.get_endpoint(sample_webhook_endpoint.id)
        assert endpoint == sample_webhook_endpoint

    def test_get_nonexistent_endpoint(self, webhook_manager) -> None:
        """Test getting non-existent endpoint."""
        endpoint = webhook_manager.get_endpoint("nonexistent-id")
        assert endpoint is None

    def test_list_endpoints(self, webhook_manager, sample_webhook_endpoint) -> None:
        """Test listing webhook endpoints."""
        webhook_manager.add_endpoint(sample_webhook_endpoint)

        endpoints = webhook_manager.list_endpoints()
        assert len(endpoints) == 1
        assert endpoints[0] == sample_webhook_endpoint

    def test_update_endpoint(self, webhook_manager, sample_webhook_endpoint) -> None:
        """Test updating webhook endpoint."""
        webhook_manager.add_endpoint(sample_webhook_endpoint)

        updates = {
            "url": "https://updated.example.com/webhook",
            "active": False
        }

        result = webhook_manager.update_endpoint(
            sample_webhook_endpoint.id, updates)

        assert result is True
        updated_endpoint = webhook_manager.get_endpoint(
            sample_webhook_endpoint.id)
        assert updated_endpoint.url = = "https://updated.example.com/webhook"
        assert updated_endpoint.active is False

    def test_update_nonexistent_endpoint(self, webhook_manager) -> None:
        """Test updating non-existent endpoint."""
        result = webhook_manager.update_endpoint(
            "nonexistent-id", {"active": False})
        assert result is False

    @pytest.mark.asyncio
    async def test_trigger_event_success(self, webhook_manager, sample_webhook_endpoint, sample_webhook_event) -> None:
        """Test successful event triggering."""
        webhook_manager.add_endpoint(sample_webhook_endpoint)

        with patch.object(webhook_manager, '_deliver_webhook', new_callable=AsyncMock) as mock_deliver:
            mock_deliver.return_value = "delivery-123"

            delivery_ids = await webhook_manager.trigger_event(sample_webhook_event)

            assert len(delivery_ids) == 1
            assert delivery_ids[0] == "delivery-123"
            mock_deliver.assert_called_once_with(
                sample_webhook_endpoint, sample_webhook_event)

    @pytest.mark.asyncio
    async def test_trigger_event_no_matching_endpoints(self, webhook_manager, sample_webhook_endpoint) -> None:
        """Test event triggering with no matching endpoints."""
        # Add endpoint that doesn't match the event type
        sample_webhook_endpoint.events = ["commit.created"]
        webhook_manager.add_endpoint(sample_webhook_endpoint)

        event = WebhookEvent(
            event_type="repository.created",  # Different event type
            event_id="event-123",
            repository_path="/test/repo",
            user_id="test-user",
            data={}
        )

        delivery_ids = await webhook_manager.trigger_event(event)
        assert len(delivery_ids) == 0

    @pytest.mark.asyncio
    async def test_trigger_event_inactive_endpoint(self, webhook_manager, sample_webhook_endpoint, sample_webhook_event) -> None:
        """Test event triggering with inactive endpoint."""
        sample_webhook_endpoint.active = False
        webhook_manager.add_endpoint(sample_webhook_endpoint)

        delivery_ids = await webhook_manager.trigger_event(sample_webhook_event)
        assert len(delivery_ids) == 0

    @pytest.mark.asyncio
    async def test_trigger_event_max_failures_exceeded(self, webhook_manager, sample_webhook_endpoint, sample_webhook_event) -> None:
        """Test event triggering with endpoint that has exceeded max failures."""
        sample_webhook_endpoint.failure_count = 10  # Exceeds max_failures (5)
        webhook_manager.add_endpoint(sample_webhook_endpoint)

        delivery_ids = await webhook_manager.trigger_event(sample_webhook_event)
        assert len(delivery_ids) == 0

    @pytest.mark.asyncio
    async def test_deliver_webhook_success(self, webhook_manager, sample_webhook_endpoint, sample_webhook_event) -> None:
        """Test successful webhook delivery."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            # Create proper async context manager mocks
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="OK")

            mock_post_context = AsyncMock()
            mock_post_context.__aenter__ = AsyncMock(
                return_value=mock_response)
            mock_post_context.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_session.post = Mock(return_value=mock_post_context)

            mock_session_context = AsyncMock()
            mock_session_context.__aenter__ = AsyncMock(
                return_value=mock_session)
            mock_session_context.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session_context

            delivery_id = await webhook_manager._deliver_webhook(sample_webhook_endpoint, sample_webhook_event)

            assert delivery_id.startswith("delivery_")
            assert sample_webhook_endpoint.failure_count = = 0
            assert sample_webhook_endpoint.last_delivery is not None

    @pytest.mark.asyncio
    async def test_deliver_webhook_http_error(self, webhook_manager, sample_webhook_endpoint, sample_webhook_event) -> None:
        """Test webhook delivery with HTTP error."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(
                return_value="Internal Server Error")

            mock_session.__aenter__.return_value = mock_session
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session

            with patch.object(webhook_manager, '_schedule_retry', new_callable=AsyncMock) as mock_retry:
                delivery_id = await webhook_manager._deliver_webhook(sample_webhook_endpoint, sample_webhook_event)

                assert delivery_id.startswith("delivery_")
                assert sample_webhook_endpoint.failure_count = = 1
                mock_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_deliver_webhook_network_error(self, webhook_manager, sample_webhook_endpoint, sample_webhook_event) -> None:
        """Test webhook delivery with network error."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session.post.side_effect = aiohttp.ClientError(
                "Network error")
            mock_session_class.return_value = mock_session

            with patch.object(webhook_manager, '_schedule_retry', new_callable=AsyncMock) as mock_retry:
                delivery_id = await webhook_manager._deliver_webhook(sample_webhook_endpoint, sample_webhook_event)

                assert delivery_id.startswith("delivery_")
                assert sample_webhook_endpoint.failure_count = = 1
                mock_retry.assert_called_once()

    def test_generate_signature(self, webhook_manager) -> None:
        """Test HMAC signature generation."""
        payload = '{"test": "data"}'
        secret = "test-secret"

        signature = webhook_manager._generate_signature(payload, secret)

        assert signature.startswith("sha256=")
        assert len(signature) > 10

        # Test that same payload and secret generate same signature
        signature2 = webhook_manager._generate_signature(payload, secret)
        assert signature == signature2

    def test_add_delivery_record(self, webhook_manager, sample_webhook_endpoint, sample_webhook_event) -> None:
        """Test adding delivery record."""
        delivery = WebhookDelivery(
            delivery_id="test-delivery",
            endpoint_id=sample_webhook_endpoint.id,
            event=sample_webhook_event,
            status_code=200
        )

        webhook_manager._add_delivery_record(delivery)

        assert len(webhook_manager.delivery_history) == 1
        assert webhook_manager.delivery_history[0] == delivery

    def test_get_delivery_history(self, webhook_manager, sample_webhook_endpoint, sample_webhook_event) -> None:
        """Test getting delivery history."""
        # Add some delivery records
        for i in range(3):
            delivery = WebhookDelivery(
                delivery_id=f"delivery-{i}",
                endpoint_id=sample_webhook_endpoint.id,
                event=sample_webhook_event,
                status_code=200
            )
            webhook_manager._add_delivery_record(delivery)

        history = webhook_manager.get_delivery_history()
        assert len(history) == 3

        # Test with endpoint filter
        history_filtered = webhook_manager.get_delivery_history(
            endpoint_id=sample_webhook_endpoint.id)
        assert len(history_filtered) == 3

        # Test with limit
        history_limited = webhook_manager.get_delivery_history(limit=2)
        assert len(history_limited) == 2

    def test_get_endpoint_stats(self, webhook_manager, sample_webhook_endpoint, sample_webhook_event) -> None:
        """Test getting endpoint statistics."""
        webhook_manager.add_endpoint(sample_webhook_endpoint)

        # Add some delivery records
        successful_delivery = WebhookDelivery(
            delivery_id="success-1",
            endpoint_id=sample_webhook_endpoint.id,
            event=sample_webhook_event,
            status_code=200,
            duration_ms=150.0
        )

        failed_delivery = WebhookDelivery(
            delivery_id="failed-1",
            endpoint_id=sample_webhook_endpoint.id,
            event=sample_webhook_event,
            status_code=500,
            error="Server error"
        )

        webhook_manager._add_delivery_record(successful_delivery)
        webhook_manager._add_delivery_record(failed_delivery)

        stats = webhook_manager.get_endpoint_stats(sample_webhook_endpoint.id)

        assert stats["endpoint_id"] == sample_webhook_endpoint.id
        assert stats["total_deliveries"] == 2
        assert stats["successful_deliveries"] == 1
        assert stats["failed_deliveries"] == 1
        assert stats["success_rate"] == 0.5
        assert stats["average_duration_ms"] == 150.0


class TestEventTypes:
    """Test event type constants."""

    def test_event_types_exist(self) -> None:
        """Test that all expected event types are defined."""
        expected_events = [
            "repository.created",
            "repository.cloned",
            "branch.created",
            "branch.deleted",
            "branch.merged",
            "commit.created",
            "tag.created",
            "tag.deleted",
            "search.completed",
            "analysis.completed",
            "export.completed",
            "conflict.detected"
        ]

        for event_type in expected_events:
            assert hasattr(EventTypes, event_type.replace(".", "_").upper())


class TestHelperFunctions:
    """Test helper functions for triggering events."""

    @pytest.mark.asyncio
    async def test_trigger_repository_event(self) -> None:
        """Test triggering repository event."""
        with patch('githound.web.webhooks.webhook_manager') as mock_manager:
            mock_manager.trigger_event = AsyncMock(
                return_value=["delivery-123"])

            result = await trigger_repository_event(
                "repository.created",
                "/test/repo",
                "test-user",
                {"status": "created"}
            )

            assert result == ["delivery-123"]
            mock_manager.trigger_event.assert_called_once()

            # Check the event that was passed
            call_args = mock_manager.trigger_event.call_args[0]
            event = call_args[0]
            assert event.event_type = = "repository.created"
            assert event.repository_path = = "/test/repo"
            assert event.user_id = = "test-user"
            assert event.data = = {"status": "created"}

    @pytest.mark.asyncio
    async def test_trigger_search_event(self) -> None:
        """Test triggering search event."""
        with patch('githound.web.webhooks.trigger_repository_event') as mock_trigger:
            mock_trigger.return_value = ["delivery-456"]

            search_results = {"total_results": 10, "duration_ms": 1500}
            result = await trigger_search_event("/test/repo", "test-user", search_results)

            assert result == ["delivery-456"]
            mock_trigger.assert_called_once_with(
                EventTypes.SEARCH_COMPLETED,
                "/test/repo",
                "test-user",
                search_results
            )
