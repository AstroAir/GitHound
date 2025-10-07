"""
WebSocket utilities for GitHound.

Provides a lightweight ConnectionManager used by tests to verify payload
shapes and JSON serialization.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, TypedDict


# Minimal type alias for test usage
ProgressMessage = Dict[str, Any]


class ConnectionManager:
    """Lightweight connection manager used for broadcasting typed messages."""

    async def broadcast_to_search(self, search_id: str, message: dict[str, Any]) -> None:
        # In real implementation, this would fan out to subscribers.
        # Tests will monkeypatch this.
        return None

    async def broadcast_progress(
        self, search_id: str, progress: float, message: str, results_count: int = 0
    ) -> None:
        payload: dict[str, Any] = {
            "type": "progress",
            "data": {
                "search_id": search_id,
                "progress": float(progress),
                "message": message,
                "results_count": int(results_count),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        }
        await self.broadcast_to_search(search_id, payload)

    async def broadcast_result(self, search_id: str, result: dict[str, Any]) -> None:
        payload = {
            "type": "result",
            "data": {
                "search_id": search_id,
                "result": result,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        }
        await self.broadcast_to_search(search_id, payload)

    async def broadcast_completion(
        self, search_id: str, status: str, total_results: int, error_message: str | None
    ) -> None:
        payload = {
            "type": "completed",
            "data": {
                "search_id": search_id,
                "status": status,
                "total_results": total_results,
                "error_message": error_message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        }
        await self.broadcast_to_search(search_id, payload)

    async def broadcast_error(self, search_id: str, error: str) -> None:
        payload = {
            "type": "error",
            "data": {
                "search_id": search_id,
                "error": error,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        }
        await self.broadcast_to_search(search_id, payload)

    async def send_personal_message(self, websocket: Any, payload: ProgressMessage) -> None:
        # Serialize to JSON and send using the provided ws object's send_text
        await websocket.send_text(json.dumps(payload))