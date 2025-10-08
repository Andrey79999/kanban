"""Tests for WebSocket functionality.

Tests cover WebSocket connections, message broadcasting,
and real-time update scenarios.
"""

import asyncio
import json

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from main import app
from services.websocket_manager import WebSocketManager


class TestWebSocketManager:
    """Unit tests for WebSocket manager."""
    
    @pytest.mark.asyncio
    async def test_websocket_manager_initialization(self):
        """Test WebSocket manager initializes correctly."""
        # Arrange & Act
        manager = WebSocketManager()
        
        # Assert
        assert manager.connection_count == 0
        assert len(manager.active_connections) == 0
        assert len(manager.connection_ids) == 0
    
    @pytest.mark.asyncio
    async def test_broadcast_message_format(self):
        """Test broadcast message includes timestamp."""
        # Arrange
        manager = WebSocketManager()
        message = {"type": "test", "data": {"value": 123}}
        
        # Act
        await manager.broadcast(message)
        
        # Assert
        assert "timestamp" in message


class TestWebSocketEndpoint:
    """Integration tests for WebSocket endpoint."""
    
    def test_websocket_connection_handshake(self):
        """Test WebSocket connection establishment."""
        # Arrange
        client = TestClient(app)
        
        # Act & Assert
        with client.websocket_connect("/ws?client_id=test123") as websocket:
            data = websocket.receive_json()
            
            # Should receive welcome message
            assert data["type"] == "connected"
            assert data["data"]["client_id"] == "test123"
            assert "message" in data["data"]
    
    def test_websocket_ping_pong(self):
        """Test WebSocket keepalive ping/pong."""
        # Arrange
        client = TestClient(app)
        
        # Act & Assert
        with client.websocket_connect("/ws") as websocket:
            # Receive welcome message
            websocket.receive_json()
            
            # Send ping
            websocket.send_text("ping")
            
            # Receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"
    
    def test_websocket_auto_generate_client_id(self):
        """Test client ID is auto-generated if not provided."""
        # Arrange
        client = TestClient(app)
        
        # Act & Assert
        with client.websocket_connect("/ws") as websocket:
            data = websocket.receive_json()
            
            # Should have generated client_id
            assert data["type"] == "connected"
            assert "client_id" in data["data"]
            assert len(data["data"]["client_id"]) > 0
