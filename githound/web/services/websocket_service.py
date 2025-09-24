"""WebSocket service for real-time progress updates."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Literal, TypedDict

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WebSocketMessage(BaseModel):
    """WebSocket message envelope."""

    type: str
    data: dict[str, Any]
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
    error_message: str | None
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
    status: str
    progress: float
    message: str
    timestamp: str


class StatusMessage(TypedDict):
    type: Literal["status"]
    data: StatusData


# Union type for all message types
WebSocketMessageType = (
    ConnectedMessage
    | ProgressMessage
    | ResultMessage
    | CompletedMessage
    | ErrorMessage
    | PongMessage
    | PingMessage
    | StatusMessage
)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}
        self.search_connections: dict[str, set[str]] = {}  # search_id -> connection_ids

    async def connect(self, websocket: WebSocket, connection_id: str) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connection established: {connection_id}")

    def disconnect(self, connection_id: str) -> None:
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

            # Remove from search connections
            for search_id, conn_ids in self.search_connections.items():
                conn_ids.discard(connection_id)

            # Clean up empty search connections
            self.search_connections = {
                search_id: conn_ids
                for search_id, conn_ids in self.search_connections.items()
                if conn_ids
            }

            logger.info(f"WebSocket connection closed: {connection_id}")

    def subscribe_to_search(self, connection_id: str, search_id: str) -> None:
        """Subscribe a connection to search updates."""
        if search_id not in self.search_connections:
            self.search_connections[search_id] = set()
        self.search_connections[search_id].add(connection_id)
        logger.info(f"Connection {connection_id} subscribed to search {search_id}")

    def unsubscribe_from_search(self, connection_id: str, search_id: str) -> None:
        """Unsubscribe a connection from search updates."""
        if search_id in self.search_connections:
            self.search_connections[search_id].discard(connection_id)
            if not self.search_connections[search_id]:
                del self.search_connections[search_id]
        logger.info(f"Connection {connection_id} unsubscribed from search {search_id}")

    async def send_personal_message(
        self, message: WebSocketMessageType, connection_id: str
    ) -> None:
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                self.disconnect(connection_id)

    async def send_search_update(self, message: WebSocketMessageType, search_id: str) -> None:
        """Send a message to all connections subscribed to a search."""
        if search_id not in self.search_connections:
            return

        connection_ids = list(self.search_connections[search_id])
        for connection_id in connection_ids:
            await self.send_personal_message(message, connection_id)

    async def broadcast(self, message: WebSocketMessageType) -> None:
        """Broadcast a message to all active connections."""
        connection_ids = list(self.active_connections.keys())
        for connection_id in connection_ids:
            await self.send_personal_message(message, connection_id)

    async def send_progress_update(
        self, search_id: str, progress: float, message: str, results_count: int = 0
    ) -> None:
        """Send a progress update for a search."""
        progress_message: ProgressMessage = {
            "type": "progress",
            "data": {
                "search_id": search_id,
                "progress": progress,
                "message": message,
                "results_count": results_count,
                "timestamp": datetime.now().isoformat(),
            },
        }
        await self.send_search_update(progress_message, search_id)

    async def send_search_result(self, search_id: str, result: dict[str, Any]) -> None:
        """Send a new search result."""
        result_message: ResultMessage = {
            "type": "result",
            "data": {
                "search_id": search_id,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            },
        }
        await self.send_search_update(result_message, search_id)

    async def send_search_completed(
        self, search_id: str, status: str, total_results: int, error_message: str | None = None
    ) -> None:
        """Send search completion notification."""
        completed_message: CompletedMessage = {
            "type": "completed",
            "data": {
                "search_id": search_id,
                "status": status,
                "total_results": total_results,
                "error_message": error_message,
                "timestamp": datetime.now().isoformat(),
            },
        }
        await self.send_search_update(completed_message, search_id)

    async def send_search_error(self, search_id: str, error: str) -> None:
        """Send search error notification."""
        error_message: ErrorMessage = {
            "type": "error",
            "data": {
                "search_id": search_id,
                "error": error,
                "timestamp": datetime.now().isoformat(),
            },
        }
        await self.send_search_update(error_message, search_id)

    async def send_status_update(
        self, search_id: str, status: str, progress: float, message: str
    ) -> None:
        """Send status update for a search."""
        status_message: StatusMessage = {
            "type": "status",
            "data": {
                "search_id": search_id,
                "status": status,
                "progress": progress,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            },
        }
        await self.send_search_update(status_message, search_id)

    async def handle_ping(self, connection_id: str) -> None:
        """Handle ping message and send pong response."""
        pong_message: PongMessage = {
            "type": "pong",
            "data": {"timestamp": datetime.now().isoformat()},
        }
        await self.send_personal_message(pong_message, connection_id)

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)

    def get_search_subscriber_count(self, search_id: str) -> int:
        """Get the number of connections subscribed to a search."""
        return len(self.search_connections.get(search_id, set()))

    def get_active_searches(self) -> list[str]:
        """Get list of search IDs with active subscribers."""
        return list(self.search_connections.keys())


# Global connection manager instance
connection_manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, connection_id: str) -> None:
    """WebSocket endpoint for real-time updates."""
    await connection_manager.connect(websocket, connection_id)

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "ping":
                    await connection_manager.handle_ping(connection_id)
                elif message_type == "subscribe":
                    search_id = message.get("data", {}).get("search_id")
                    if search_id:
                        connection_manager.subscribe_to_search(connection_id, search_id)
                elif message_type == "unsubscribe":
                    search_id = message.get("data", {}).get("search_id")
                    if search_id:
                        connection_manager.unsubscribe_from_search(connection_id, search_id)
                else:
                    logger.warning(f"Unknown message type: {message_type}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from {connection_id}")
            except Exception as e:
                logger.error(f"Error processing message from {connection_id}: {e}")

    except WebSocketDisconnect:
        connection_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        connection_manager.disconnect(connection_id)
