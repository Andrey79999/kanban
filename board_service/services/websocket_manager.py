"""WebSocket manager for real-time updates.

This module manages WebSocket connections and broadcasts
task updates to all connected clients.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Set

from fastapi import WebSocket, WebSocketDisconnect


class WebSocketManager:
    """Manager for WebSocket connections and message broadcasting.
    
    Implements the Observer pattern for real-time updates.
    Maintains a set of active connections and broadcasts events.
    
    Attributes:
        active_connections: Set of active WebSocket connections
        connection_ids: Mapping of connection IDs to WebSockets
    """
    
    def __init__(self) -> None:
        """Initialize WebSocket manager."""
        self.active_connections: Set[WebSocket] = set()
        self.connection_ids: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection to register
            client_id: Unique client identifier
        """
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
            self.connection_ids[client_id] = websocket
    
    async def disconnect(self, websocket: WebSocket, client_id: str) -> None:
        """Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
            client_id: Client identifier
        """
        async with self._lock:
            self.active_connections.discard(websocket)
            self.connection_ids.pop(client_id, None)
    
    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected clients.
        
        Failed connections are automatically removed.
        
        Args:
            message: Message dictionary to broadcast
        """
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        disconnected: List[WebSocket] = []
        
        for connection in self.active_connections.copy():
            try:
                await connection.send_json(message)
            except (WebSocketDisconnect, RuntimeError):
                disconnected.append(connection)
        
        # Remove disconnected clients
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    self.active_connections.discard(conn)
                    # Remove from connection_ids
                    for cid, ws in list(self.connection_ids.items()):
                        if ws == conn:
                            self.connection_ids.pop(cid, None)
                            break
    
    async def send_personal_message(
        self,
        message: dict,
        client_id: str
    ) -> bool:
        """Send a message to a specific client.
        
        Args:
            message: Message dictionary to send
            client_id: Target client identifier
            
        Returns:
            True if message was sent, False if client not found
        """
        websocket = self.connection_ids.get(client_id)
        if websocket:
            try:
                await websocket.send_json(message)
                return True
            except (WebSocketDisconnect, RuntimeError):
                await self.disconnect(websocket, client_id)
        return False
    
    async def broadcast_task_created(self, task_data: dict) -> None:
        """Broadcast task creation event.
        
        Args:
            task_data: Created task data
        """
        await self.broadcast({
            "type": "task_created",
            "data": task_data,
        })
    
    async def broadcast_task_updated(self, task_data: dict) -> None:
        """Broadcast task update event.
        
        Args:
            task_data: Updated task data
        """
        await self.broadcast({
            "type": "task_updated",
            "data": task_data,
        })
    
    async def broadcast_task_deleted(self, task_id: int) -> None:
        """Broadcast task deletion event.
        
        Args:
            task_id: Deleted task ID
        """
        await self.broadcast({
            "type": "task_deleted",
            "data": {"task_id": task_id},
        })
    
    async def broadcast_task_status_changed(
        self,
        task_id: int,
        old_status: str,
        new_status: str
    ) -> None:
        """Broadcast task status change event.
        
        Args:
            task_id: Task ID
            old_status: Previous status
            new_status: New status
        """
        await self.broadcast({
            "type": "task_status_changed",
            "data": {
                "task_id": task_id,
                "old_status": old_status,
                "new_status": new_status,
            },
        })
    
    @property
    def connection_count(self) -> int:
        """Get the number of active connections.
        
        Returns:
            Number of active WebSocket connections
        """
        return len(self.active_connections)


# Global WebSocket manager instance
ws_manager = WebSocketManager()
