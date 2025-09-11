"""
Webhook system for GitHound API.

Provides event-driven notifications for repository operations and analysis results.
"""

import asyncio
import hashlib
import hmac
import json
import time
from datetime import datetime
from typing import Any

import aiohttp
from pydantic import BaseModel, Field


class WebhookEvent(BaseModel):
    """Webhook event model."""
    event_type: str = Field(..., description="Type of event")
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(default_factory=datetime.now)
    repository_path: str = Field(..., description="Repository path")
    user_id: str | None = Field(None, description="User who triggered the event")
    data: dict[str, Any] = Field(..., description="Event-specific data")


class WebhookEndpoint(BaseModel):
    """Webhook endpoint configuration."""
    id: str = Field(..., description="Endpoint identifier")
    url: str = Field(..., description="Webhook URL")
    secret: str | None = Field(None, description="Secret for signature verification")
    events: list[str] = Field(..., description="Events to subscribe to")
    active: bool = Field(True, description="Whether endpoint is active")
    created_at: datetime = Field(default_factory=datetime.now)
    last_delivery: datetime | None = Field(None, description="Last successful delivery")
    failure_count: int = Field(0, description="Consecutive failure count")
    max_failures: int = Field(5, description="Max failures before disabling")


class WebhookDelivery(BaseModel):
    """Webhook delivery record."""
    delivery_id: str = Field(..., description="Delivery identifier")
    endpoint_id: str = Field(..., description="Target endpoint ID")
    event: WebhookEvent = Field(..., description="Event data")
    status_code: int | None = Field(None, description="HTTP response status")
    response_body: str | None = Field(None, description="Response body")
    delivery_time: datetime | None = Field(None, description="Delivery timestamp")
    duration_ms: float | None = Field(None, description="Delivery duration")
    error: str | None = Field(None, description="Error message if failed")
    retry_count: int = Field(0, description="Number of retries")


class WebhookManager:
    """Manages webhook endpoints and event delivery."""

    def __init__(self) -> None:
        self.endpoints: dict[str, WebhookEndpoint] = {}
        self.delivery_history: list[WebhookDelivery] = []
        self.max_history = 1000  # Keep last 1000 deliveries
        self.retry_delays = [1, 5, 15, 60, 300]  # Retry delays in seconds

    def add_endpoint(self, endpoint: WebhookEndpoint) -> str:
        """Add a webhook endpoint."""
        self.endpoints[endpoint.id] = endpoint
        return endpoint.id

    def remove_endpoint(self, endpoint_id: str) -> bool:
        """Remove a webhook endpoint."""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            return True
        return False

    def get_endpoint(self, endpoint_id: str) -> WebhookEndpoint | None:
        """Get a webhook endpoint."""
        return self.endpoints.get(endpoint_id)

    def list_endpoints(self) -> list[WebhookEndpoint]:
        """List all webhook endpoints."""
        return list(self.endpoints.values())

    def update_endpoint(self, endpoint_id: str, updates: dict[str, Any]) -> bool:
        """Update a webhook endpoint."""
        if endpoint_id not in self.endpoints:
            return False

        endpoint = self.endpoints[endpoint_id]
        for key, value in updates.items():
            if hasattr(endpoint, key):
                setattr(endpoint, key, value)

        return True

    async def trigger_event(self, event: WebhookEvent) -> list[str]:
        """Trigger a webhook event to all subscribed endpoints."""
        delivery_ids: list[Any] = []

        for endpoint in self.endpoints.values():
            if (endpoint.active and
                event.event_type in endpoint.events and
                endpoint.failure_count < endpoint.max_failures):

                delivery_id = await self._deliver_webhook(endpoint, event)
                delivery_ids.append(delivery_id)

        return delivery_ids

    async def _deliver_webhook(self, endpoint: WebhookEndpoint, event: WebhookEvent) -> str:
        """Deliver a webhook to a specific endpoint."""
        delivery_id = f"delivery_{int(time.time() * 1000)}_{endpoint.id}"

        delivery = WebhookDelivery(
            delivery_id=delivery_id,
            endpoint_id=endpoint.id,
            event=event,
            status_code=None,
            response_body=None,
            delivery_time=None,
            duration_ms=None,
            error=None,
            retry_count=0,
        )

        try:
            # Prepare payload
            payload = {
                "event_type": event.event_type,
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "repository_path": event.repository_path,
                "user_id": event.user_id,
                "data": event.data
            }

            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "GitHound-Webhook/1.0",
                "X-GitHound-Event": event.event_type,
                "X-GitHound-Delivery": delivery_id
            }

            # Add signature if secret is configured
            if endpoint.secret:
                signature = self._generate_signature(json.dumps(payload), endpoint.secret)
                headers["X-GitHound-Signature"] = signature

            # Deliver webhook
            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint.url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    delivery.status_code = response.status
                    delivery.response_body = await response.text()
                    delivery.delivery_time = datetime.now()
                    delivery.duration_ms = (time.time() - start_time) * 1000

                    if response.status >= 200 and response.status < 300:
                        # Success
                        endpoint.last_delivery = delivery.delivery_time
                        endpoint.failure_count = 0
                    else:
                        # HTTP error
                        endpoint.failure_count += 1
                        delivery.error = f"HTTP {response.status}: {delivery.response_body}"

                        # Schedule retry if not too many failures
                        if endpoint.failure_count < endpoint.max_failures:
                            await self._schedule_retry(endpoint, event, delivery.retry_count + 1)

        except Exception as e:
            # Network or other error
            delivery.error = str(e)
            delivery.delivery_time = datetime.now()
            delivery.duration_ms = (time.time() - start_time) * 1000

            endpoint.failure_count += 1

            # Schedule retry if not too many failures
            if endpoint.failure_count < endpoint.max_failures:
                await self._schedule_retry(endpoint, event, delivery.retry_count + 1)

        # Store delivery record
        self._add_delivery_record(delivery)

        return delivery_id

    async def _schedule_retry(self, endpoint: WebhookEndpoint, event: WebhookEvent, retry_count: int) -> None:
        """Schedule a webhook retry."""
        if retry_count > len(self.retry_delays):
            return  # Max retries exceeded

        delay = self.retry_delays[retry_count - 1]

        # Schedule retry (in a real implementation, this would use a task queue)
        asyncio.create_task(self._retry_webhook(endpoint, event, retry_count, delay))

    async def _retry_webhook(self, endpoint: WebhookEndpoint, event: WebhookEvent, retry_count: int, delay: int) -> None:
        """Retry a failed webhook delivery."""
        await asyncio.sleep(delay)

        # Create new delivery record for retry
        delivery_id = f"retry_{retry_count}_{int(time.time() * 1000)}_{endpoint.id}"

        delivery = WebhookDelivery(
            delivery_id=delivery_id,
            endpoint_id=endpoint.id,
            event=event,
            status_code=None,
            response_body=None,
            delivery_time=None,
            duration_ms=None,
            error=None,
            retry_count=retry_count,
        )

        # Attempt delivery again
        await self._deliver_webhook(endpoint, event)

    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload."""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    def _add_delivery_record(self, delivery: WebhookDelivery) -> None:
        """Add delivery record to history."""
        self.delivery_history.append(delivery)

        # Keep only recent deliveries
        if len(self.delivery_history) > self.max_history:
            self.delivery_history = self.delivery_history[-self.max_history:]

    def get_delivery_history(self, endpoint_id: str | None = None, limit: int = 100) -> list[WebhookDelivery]:
        """Get webhook delivery history."""
        history = self.delivery_history

        if endpoint_id:
            history = [d for d in history if d.endpoint_id == endpoint_id]

        return history[-limit:]

    def get_endpoint_stats(self, endpoint_id: str) -> dict[str, Any]:
        """Get statistics for a webhook endpoint."""
        endpoint = self.endpoints.get(endpoint_id)
        if not endpoint:
            return {}

        deliveries = [d for d in self.delivery_history if d.endpoint_id == endpoint_id]

        successful_deliveries = [d for d in deliveries if d.status_code and 200 <= d.status_code < 300]
        failed_deliveries = [d for d in deliveries if d.error or (d.status_code and d.status_code >= 400)]

        avg_duration = 0.0
        if deliveries:
            durations = [d.duration_ms for d in deliveries if d.duration_ms]
            if durations:
                avg_duration = sum(durations) / len(durations)

        return {
            "endpoint_id": endpoint_id,
            "total_deliveries": len(deliveries),
            "successful_deliveries": len(successful_deliveries),
            "failed_deliveries": len(failed_deliveries),
            "success_rate": len(successful_deliveries) / len(deliveries) if deliveries else 0,
            "average_duration_ms": avg_duration,
            "last_delivery": endpoint.last_delivery,
            "failure_count": endpoint.failure_count,
            "active": endpoint.active
        }


# Global webhook manager instance
webhook_manager = WebhookManager()


# Event types
class EventTypes:
    """Webhook event type constants."""
    REPOSITORY_CREATED = "repository.created"
    REPOSITORY_CLONED = "repository.cloned"
    BRANCH_CREATED = "branch.created"
    BRANCH_DELETED = "branch.deleted"
    BRANCH_MERGED = "branch.merged"
    COMMIT_CREATED = "commit.created"
    TAG_CREATED = "tag.created"
    TAG_DELETED = "tag.deleted"
    SEARCH_COMPLETED = "search.completed"
    ANALYSIS_COMPLETED = "analysis.completed"
    EXPORT_COMPLETED = "export.completed"
    CONFLICT_DETECTED = "conflict.detected"


# Helper functions for triggering events
async def trigger_repository_event(event_type: str, repo_path: str, user_id: str, data: dict[str, Any]) -> list[str]:
    """Trigger a repository-related event."""
    event = WebhookEvent(
        event_type=event_type,
        event_id=f"repo_{int(time.time() * 1000)}",
        repository_path=repo_path,
        user_id=user_id,
        data=data
    )

    return await webhook_manager.trigger_event(event)


async def trigger_search_event(repo_path: str, user_id: str, search_results: dict[str, Any]) -> list[str]:
    """Trigger a search completed event."""
    return await trigger_repository_event(
        EventTypes.SEARCH_COMPLETED,
        repo_path,
        user_id,
        search_results
    )
