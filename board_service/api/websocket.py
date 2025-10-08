"""WebSocket API endpoints for real-time updates.

This module provides WebSocket endpoints for clients to receive
real-time updates about task changes.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from services.websocket_manager import ws_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None, description="Optional client identifier"),
) -> None:
    """WebSocket endpoint for real-time task updates.
    
    Clients connect to this endpoint to receive real-time notifications
    about task changes (create, update, delete, status change).
    
    Args:
        websocket: WebSocket connection
        client_id: Optional client identifier (auto-generated if not provided)
        
    Message format:
        ```json
        {
            "type": "task_created" | "task_updated" | "task_deleted" | "task_status_changed",
            "data": {...},
            "timestamp": "2024-01-01T12:00:00"
        }
        ```
    
    Example client connection (JavaScript):
        ```javascript
        const ws = new WebSocket('ws://localhost:8000/ws?client_id=user123');
        
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            console.log('Received:', message);
            
            switch(message.type) {
                case 'task_created':
                    // Handle new task
                    break;
                case 'task_updated':
                    // Handle updated task
                    break;
                case 'task_deleted':
                    // Handle deleted task
                    break;
                case 'task_status_changed':
                    // Handle status change
                    break;
            }
        };
        ```
    """
    # Generate client ID if not provided
    if not client_id:
        client_id = str(uuid.uuid4())
    
    # Accept connection
    await ws_manager.connect(websocket, client_id)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "data": {
                "client_id": client_id,
                "message": "Connected to kanban board updates",
                "active_connections": ws_manager.connection_count,
            },
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            # Wait for messages from client (e.g., ping/pong for keepalive)
            data = await websocket.receive_text()
            
            # Echo back for keepalive
            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "data": {"client_id": client_id},
                })
    
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, client_id)
    except Exception as e:
        # Log error and disconnect
        print(f"WebSocket error for client {client_id}: {e}")
        await ws_manager.disconnect(websocket, client_id)
