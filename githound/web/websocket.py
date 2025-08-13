"""WebSocket support for real-time progress updates."""

import asyncio
import json
import logging
from typing import Dict, Set
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str
    data: dict
    timestamp: datetime = datetime.now()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Active connections by search_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, search_id: str):
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
            "client_ip": websocket.client.host if websocket.client else "unknown"
        }
        
        logger.info(f"WebSocket connected for search {search_id}")
        
        # Send welcome message
        await self.send_personal_message(websocket, {
            "type": "connected",
            "data": {
                "search_id": search_id,
                "message": "Connected to GitHound progress updates"
            }
        })
    
    def disconnect(self, websocket: WebSocket):
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
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send a message to a specific WebSocket connection."""
        try:
            ws_message = WebSocketMessage(
                type=message.get("type", "message"),
                data=message.get("data", {})
            )
            await websocket.send_text(ws_message.json())
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_search(self, search_id: str, message: dict):
        """Broadcast a message to all connections for a specific search."""
        if search_id not in self.active_connections:
            return
        
        ws_message = WebSocketMessage(
            type=message.get("type", "progress"),
            data=message.get("data", {})
        )
        
        # Send to all connections for this search
        disconnected = []
        for websocket in self.active_connections[search_id].copy():
            try:
                await websocket.send_text(ws_message.json())
            except Exception as e:
                logger.error(f"Failed to broadcast to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_progress(self, search_id: str, progress: float, message: str, results_count: int = 0):
        """Broadcast progress update for a search."""
        await self.broadcast_to_search(search_id, {
            "type": "progress",
            "data": {
                "search_id": search_id,
                "progress": progress,
                "message": message,
                "results_count": results_count,
                "timestamp": datetime.now().isoformat()
            }
        })
    
    async def broadcast_result(self, search_id: str, result: dict):
        """Broadcast a new search result."""
        await self.broadcast_to_search(search_id, {
            "type": "result",
            "data": {
                "search_id": search_id,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        })
    
    async def broadcast_completion(self, search_id: str, status: str, total_results: int, error_message: str = None):
        """Broadcast search completion."""
        await self.broadcast_to_search(search_id, {
            "type": "completed",
            "data": {
                "search_id": search_id,
                "status": status,
                "total_results": total_results,
                "error_message": error_message,
                "timestamp": datetime.now().isoformat()
            }
        })
    
    async def broadcast_error(self, search_id: str, error_message: str):
        """Broadcast an error for a search."""
        await self.broadcast_to_search(search_id, {
            "type": "error",
            "data": {
                "search_id": search_id,
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            }
        })
    
    def get_connection_count(self, search_id: str = None) -> int:
        """Get the number of active connections."""
        if search_id:
            return len(self.active_connections.get(search_id, set()))
        else:
            return sum(len(connections) for connections in self.active_connections.values())
    
    def get_active_searches(self) -> list:
        """Get list of search IDs with active connections."""
        return list(self.active_connections.keys())
    
    async def ping_all_connections(self):
        """Send ping to all connections to check if they're alive."""
        all_connections = []
        for connections in self.active_connections.values():
            all_connections.extend(connections)
        
        disconnected = []
        for websocket in all_connections:
            try:
                await websocket.ping()
            except Exception:
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for websocket in disconnected:
            self.disconnect(websocket)


# Global connection manager instance
connection_manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, search_id: str):
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
                    await connection_manager.send_personal_message(websocket, {
                        "type": "error",
                        "data": {"message": "Invalid JSON message"}
                    })
                
            except asyncio.TimeoutError:
                # Send periodic ping to keep connection alive
                await connection_manager.send_personal_message(websocket, {
                    "type": "ping",
                    "data": {"timestamp": datetime.now().isoformat()}
                })
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, search_id: str, message: dict):
    """Handle messages from WebSocket clients."""
    message_type = message.get("type", "")
    
    if message_type == "ping":
        # Respond to ping
        await connection_manager.send_personal_message(websocket, {
            "type": "pong",
            "data": {"timestamp": datetime.now().isoformat()}
        })
    
    elif message_type == "status_request":
        # Send current search status
        # This would integrate with the active_searches from api.py
        await connection_manager.send_personal_message(websocket, {
            "type": "status",
            "data": {
                "search_id": search_id,
                "message": "Status request received"
            }
        })
    
    else:
        # Unknown message type
        await connection_manager.send_personal_message(websocket, {
            "type": "error",
            "data": {"message": f"Unknown message type: {message_type}"}
        })


# Background task to clean up stale connections
async def cleanup_stale_connections():
    """Periodically clean up stale WebSocket connections."""
    while True:
        try:
            await connection_manager.ping_all_connections()
            await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in connection cleanup: {e}")
            await asyncio.sleep(60)
