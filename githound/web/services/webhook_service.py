"""
Webhook service for GitHound API.

Provides event-driven notifications for repository operations and analysis results.
"""

import asyncio
import hashlib
import hmac
import json
import time
import uuid
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
    user_id: str | None = Field(
        None, description="User who triggered the event")
    data: dict[str, Any] = Field(..., description="Event-specific data")


class WebhookEndpoint(BaseModel):
    """Webhook endpoint configuration."""
    id: str = Field(..., description="Endpoint identifier")
    url: str = Field(..., description="Webhook URL")
    secret: str | None = Field(
        None, description="Secret for signature verification")
    events: list[str] = Field(..., description="Events to subscribe to")
    active: bool = Field(True, description="Whether endpoint is active")
    created_at: datetime = Field(default_factory=datetime.now)
    last_delivery: datetime | None = Field(
        None, description="Last successful delivery")
    failure_count: int = Field(0, description="Consecutive failure count")
    max_failures: int = Field(5, description="Max failures before disabling")


class WebhookDelivery(BaseModel):
    """Webhook delivery record."""
    delivery_id: str = Field(..., description="Delivery identifier")
    endpoint_id: str = Field(..., description="Target endpoint ID")
    event: WebhookEvent = Field(..., description="Event data")
    status_code: int | None = Field(None, description="HTTP response status")
    response_body: str | None = Field(None, description="Response body")
    delivery_time: datetime | None = Field(
        None, description="Delivery timestamp")
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
        """Trigger an event to all subscribed endpoints."""
        delivery_ids = []
        
        for endpoint in self.endpoints.values():
            if not endpoint.active:
                continue
                
            if endpoint.failure_count >= endpoint.max_failures:
                continue
                
            if event.event_type not in endpoint.events:
                continue
            
            delivery_id = str(uuid.uuid4())
            delivery_ids.append(delivery_id)
            
            # Schedule delivery in background
            asyncio.create_task(
                self._deliver_webhook(delivery_id, endpoint, event)
            )
        
        return delivery_ids

    async def _deliver_webhook(
        self,
        delivery_id: str,
        endpoint: WebhookEndpoint,
        event: WebhookEvent
    ) -> None:
        """Deliver a webhook to an endpoint with retries."""
        delivery = WebhookDelivery(
            delivery_id=delivery_id,
            endpoint_id=endpoint.id,
            event=event
        )
        
        for retry_count in range(len(self.retry_delays) + 1):
            try:
                start_time = time.time()
                
                # Prepare payload
                payload = event.dict()
                payload_json = json.dumps(payload, default=str)
                
                # Prepare headers
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "GitHound-Webhook/1.0",
                    "X-GitHound-Event": event.event_type,
                    "X-GitHound-Delivery": delivery_id,
                    "X-GitHound-Timestamp": str(int(event.timestamp.timestamp()))
                }
                
                # Add signature if secret is configured
                if endpoint.secret:
                    signature = self._generate_signature(payload_json, endpoint.secret)
                    headers["X-GitHound-Signature"] = signature
                
                # Make HTTP request
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        endpoint.url,
                        data=payload_json,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        delivery.status_code = response.status
                        delivery.response_body = await response.text()
                        delivery.delivery_time = datetime.now()
                        delivery.duration_ms = (time.time() - start_time) * 1000
                        delivery.retry_count = retry_count
                
                # Check if delivery was successful
                if 200 <= delivery.status_code < 300:
                    endpoint.last_delivery = delivery.delivery_time
                    endpoint.failure_count = 0
                    self._add_delivery_record(delivery)
                    return
                else:
                    delivery.error = f"HTTP {delivery.status_code}: {delivery.response_body}"
                
            except Exception as e:
                delivery.error = str(e)
                delivery.delivery_time = datetime.now()
                delivery.duration_ms = (time.time() - start_time) * 1000
                delivery.retry_count = retry_count
            
            # If this was the last retry, mark as failed
            if retry_count >= len(self.retry_delays):
                endpoint.failure_count += 1
                self._add_delivery_record(delivery)
                return
            
            # Wait before retry
            await asyncio.sleep(self.retry_delays[retry_count])

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
        
        # Keep only the most recent deliveries
        if len(self.delivery_history) > self.max_history:
            self.delivery_history = self.delivery_history[-self.max_history:]

    def get_delivery_history(
        self,
        endpoint_id: str | None = None,
        limit: int = 100
    ) -> list[WebhookDelivery]:
        """Get delivery history."""
        history = self.delivery_history
        
        if endpoint_id:
            history = [d for d in history if d.endpoint_id == endpoint_id]
        
        return history[-limit:]

    def get_delivery_stats(self, endpoint_id: str | None = None) -> dict[str, Any]:
        """Get delivery statistics."""
        history = self.delivery_history
        
        if endpoint_id:
            history = [d for d in history if d.endpoint_id == endpoint_id]
        
        total_deliveries = len(history)
        successful_deliveries = len([d for d in history if d.status_code and 200 <= d.status_code < 300])
        failed_deliveries = total_deliveries - successful_deliveries
        
        avg_duration = 0
        if history:
            durations = [d.duration_ms for d in history if d.duration_ms is not None]
            if durations:
                avg_duration = sum(durations) / len(durations)
        
        return {
            "total_deliveries": total_deliveries,
            "successful_deliveries": successful_deliveries,
            "failed_deliveries": failed_deliveries,
            "success_rate": successful_deliveries / total_deliveries if total_deliveries > 0 else 0,
            "average_duration_ms": avg_duration
        }

    # Event helper methods
    
    async def trigger_search_completed(
        self,
        repository_path: str,
        search_id: str,
        user_id: str | None = None,
        results_count: int = 0,
        duration_ms: float = 0
    ) -> list[str]:
        """Trigger search completed event."""
        event = WebhookEvent(
            event_type="search.completed",
            event_id=str(uuid.uuid4()),
            repository_path=repository_path,
            user_id=user_id,
            data={
                "search_id": search_id,
                "results_count": results_count,
                "duration_ms": duration_ms
            }
        )
        return await self.trigger_event(event)

    async def trigger_analysis_completed(
        self,
        repository_path: str,
        analysis_type: str,
        user_id: str | None = None,
        **analysis_data: Any
    ) -> list[str]:
        """Trigger analysis completed event."""
        event = WebhookEvent(
            event_type="analysis.completed",
            event_id=str(uuid.uuid4()),
            repository_path=repository_path,
            user_id=user_id,
            data={
                "analysis_type": analysis_type,
                **analysis_data
            }
        )
        return await self.trigger_event(event)

    async def trigger_repository_updated(
        self,
        repository_path: str,
        operation: str,
        user_id: str | None = None,
        **operation_data: Any
    ) -> list[str]:
        """Trigger repository updated event."""
        event = WebhookEvent(
            event_type="repository.updated",
            event_id=str(uuid.uuid4()),
            repository_path=repository_path,
            user_id=user_id,
            data={
                "operation": operation,
                **operation_data
            }
        )
        return await self.trigger_event(event)


# Global webhook manager instance
webhook_manager = WebhookManager()
