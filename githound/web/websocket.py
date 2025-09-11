"""WebSocket support for real-time progress updates."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional, Dict, List, TypedDict, Literal, Union

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WebSocketMessage(BaseModel):
    """WebSocket message envelope."""

    type: str
    data: dict
    timestamp: datetime = datetime.now()


# Strongly-typed payloads
class ConnectedData(TypedDict):
    search_id: str
    message: str


class ConnectedMessage(TypedDict):
    type: Literal["connected"]
    data: ConnectedData


class ProgressData(TypedDict):
    search_id: str
    progress: float
    message: str
    results_count: int
    timestamp: str


class ProgressMessage(TypedDict):
    type: Literal["progress"]
    data: ProgressData


class ResultData(TypedDict):
    search_id: str
    result: dict[str, Any]
    timestamp: str


class ResultMessage(TypedDict):
    type: Literal["result"]
    data: ResultData


class CompletedData(TypedDict):
    search_id: str
    status: str
    total_results: int
    error_message: Optional[str]
    timestamp: str


class CompletedMessage(TypedDict):
    type: Literal["completed"]
    data: CompletedData


class ErrorData(TypedDict):
    search_id: str
    error: str
    timestamp: str


class ErrorMessage(TypedDict):
    type: Literal["error"]
    data: ErrorData


class PongData(TypedDict):
    timestamp: str


class PongMessage(TypedDict):
    type: Literal["pong"]
    data: PongData


class PingData(TypedDict):
    timestamp: str


class PingMessage(TypedDict):
    type: Literal["ping"]
    data: PingData


class StatusData(TypedDict):
    search_id: str
    message: str


class StatusMessage(TypedDict):
    type: Literal["status"]
    data: StatusData


WebSocketPayload = Union[
    ConnectedMessage,
    ProgressMessage,
    ResultMessage,
    CompletedMessage,
    ErrorMessage,
    PongMessage,
    PingMessage,
    StatusMessage,
]


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self) -> None:
        # Active connections by search_id
        self.active_connections: dict[str, set[WebSocket]] = {}
        # Connection metadata
        self.connection_metadata: dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, search_id: str) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()

        # Add to active connections
        if search_id not in self.active_connections:
            self.active_connections[search_id] = set()

        self.active_connections[search_id].add(websocket)

        # Store metadata
        self.connection_metadata[websocket] = {
            "search_id": search_id,
            "connected_at": datetime.now(),
            "client_ip": websocket.client.host if websocket.client else "unknown",
        }

        logger.info(f"WebSocket connected for search {search_id}")

        # Send welcome message
        await self.send_personal_message(
            websocket,
            {
                "type": "connected",
                "data": {
                    "search_id": search_id,
                    "message": "Connected to GitHound progress updates",
                },
            },
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.connection_metadata:
            search_id = self.connection_metadata[websocket]["search_id"]

            # Remove from active connections
            if search_id in self.active_connections:
                self.active_connections[search_id].discard(websocket)

                # Clean up empty search groups
                if not self.active_connections[search_id]:
                    del self.active_connections[search_id]

            # Remove metadata
            del self.connection_metadata[websocket]

            logger.info(f"WebSocket disconnected for search {search_id}")

    async def send_personal_message(self, websocket: WebSocket, message: WebSocketPayload | dict[str, Any]) -> None:
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)

    async def broadcast_to_search(self, search_id: str, message: WebSocketPayload | dict[str, Any]) -> None:
        """Broadcast a message to all connections for a specific search."""
        if search_id not in self.active_connections:
            return

        payload_str = json.dumps(message)

        # Send to all connections for this search
        disconnected: list[Any] = []
        for websocket in self.active_connections[search_id].copy():
            try:
                await websocket.send_text(payload_str)
            except Exception as e:
                logger.error(f"Failed to broadcast to WebSocket: {e}")
                disconnected.append(websocket)

        # Clean up disconnected sockets
        for websocket in disconnected:
            self.disconnect(websocket)

    async def broadcast_progress(
        self, search_id: str, progress: float, message: str, results_count: int = 0
    ) -> None:
        """Broadcast progress update for a search."""
        payload: ProgressMessage = {
            "type": "progress",
            "data": {
                "search_id": search_id,
                "progress": progress,
                "message": message,
                "results_count": results_count,
                "timestamp": datetime.now().isoformat(),
            },
        }
        await self.broadcast_to_search(search_id, payload)

    async def broadcast_result(self, search_id: str, result: dict[str, Any]) -> None:
        """Broadcast a new search result."""
        payload: ResultMessage = {
            "type": "result",
            "data": {
                "search_id": search_id,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            },
        }
        await self.broadcast_to_search(search_id, payload)

    async def broadcast_completion(
        self, search_id: str, status: str, total_results: int, error_message: str | None = None
    ) -> None:
        """Broadcast search completion."""
        payload: CompletedMessage = {
            "type": "completed",
            "data": {
                "search_id": search_id,
                "status": status,
                "total_results": total_results,
                "error_message": error_message,
                "timestamp": datetime.now().isoformat(),
            },
        }
        await self.broadcast_to_search(search_id, payload)

    async def broadcast_error(self, search_id: str, error_message: str) -> None:
        """Broadcast an error for a search."""
        payload: ErrorMessage = {
            "type": "error",
            "data": {
                "search_id": search_id,
                "error": error_message,
                "timestamp": datetime.now().isoformat(),
            },
        }
        await self.broadcast_to_search(search_id, payload)

    def get_connection_count(self, search_id: str | None = None) -> int:
        """Get the number of active connections."""
        if search_id:
            return len(self.active_connections.get(search_id, set()))
        else:
            return sum(len(connections) for connections in self.active_connections.values())

    def get_active_searches(self) -> list:
        """Get list of search IDs with active connections."""
        return list(self.active_connections.keys())

    async def ping_all_connections(self) -> None:
        """Send ping to all connections to check if they're alive."""
        all_connections: list[WebSocket] = []
        for connections in self.active_connections.values():
            all_connections.extend(connections)

        disconnected: list[Any] = []
        for websocket in all_connections:
            try:
                # Send a ping message to check if connection is alive
                await websocket.send_text('{"type": "ping"}')
            except Exception:
                disconnected.append(websocket)

        # Clean up disconnected sockets
        for websocket in disconnected:
            self.disconnect(websocket)


# Global connection manager instance
connection_manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, search_id: str) -> None:
    """WebSocket endpoint for real-time progress updates."""
    await connection_manager.connect(websocket, search_id)

    try:
        while True:
            # Keep connection alive and handle incoming messages
            try:
                # Wait for messages from client (e.g., ping, status requests)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                try:
                    message = json.loads(data)
                    await handle_client_message(websocket, search_id, message)
                except json.JSONDecodeError:
                    payload: ErrorMessage = {
                        "type": "error",
                        "data": {
                            "search_id": search_id,
                            "error": "Invalid JSON message",
                            "timestamp": datetime.now().isoformat(),
                        },
                    }
                    await connection_manager.send_personal_message(websocket, payload)

            except TimeoutError:
                # Send periodic ping to keep connection alive
                ping_payload: PingMessage = {
                    "type": "ping",
                    "data": {"timestamp": datetime.now().isoformat()},
                }
                await connection_manager.send_personal_message(websocket, ping_payload)

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, search_id: str, message: dict) -> None:
    """Handle messages from WebSocket clients."""
    message_type = message.get("type", "")

    if message_type == "ping":
        # Respond to ping
        pong_payload: PongMessage = {
            "type": "pong",
            "data": {"timestamp": datetime.now().isoformat()},
        }
        await connection_manager.send_personal_message(websocket, pong_payload)

    elif message_type == "status_request":
        # Send current search status
        # This would integrate with the active_searches from api.py
        status_payload: StatusMessage = {
            "type": "status",
            "data": {"search_id": search_id, "message": "Status request received"},
        }
        await connection_manager.send_personal_message(websocket, status_payload)

    else:
        # Unknown message type
        error_payload: ErrorMessage = {
            "type": "error",
            "data": {
                "search_id": search_id,
                "error": f"Unknown message type: {message_type}",
                "timestamp": datetime.now().isoformat(),
            },
        }
        await connection_manager.send_personal_message(websocket, error_payload)


# Background task to clean up stale connections
async def cleanup_stale_connections() -> None:
    """Periodically clean up stale WebSocket connections."""
    while True:
        try:
            await connection_manager.ping_all_connections()
            await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in connection cleanup: {e}")
            await asyncio.sleep(60)
