from typing import Dict, List, Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # Dictionary to store connections by showtime_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Dictionary to store showtime_id by websocket connection
        self.connection_showtime_map: Dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, showtime_id: int):
        """Accept a new WebSocket connection for a specific showtime"""
        await websocket.accept()
        
        # Add to showtime-specific connections
        if showtime_id not in self.active_connections:
            self.active_connections[showtime_id] = set()
        self.active_connections[showtime_id].add(websocket)
        
        # Map connection to showtime
        self.connection_showtime_map[websocket] = showtime_id
        
        logger.info(f"WebSocket connected for showtime {showtime_id}. Total connections: {len(self.active_connections[showtime_id])}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.connection_showtime_map:
            showtime_id = self.connection_showtime_map[websocket]
            
            # Remove from showtime connections
            if showtime_id in self.active_connections:
                self.active_connections[showtime_id].discard(websocket)
                if not self.active_connections[showtime_id]:
                    del self.active_connections[showtime_id]
            
            # Remove from connection map
            del self.connection_showtime_map[websocket]
            
            logger.info(f"WebSocket disconnected for showtime {showtime_id}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to a specific client"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast_to_showtime(self, message: dict, showtime_id: int, exclude_websocket: WebSocket = None):
        """Broadcast message to all clients watching a specific showtime"""
        if showtime_id not in self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected_connections = []
        
        for connection in self.active_connections[showtime_id].copy():
            if exclude_websocket and connection == exclude_websocket:
                continue
                
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected_connections.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)

    async def send_seat_update(self, showtime_id: int, seat_data: dict, exclude_websocket: WebSocket = None):
        """Send seat status update to all clients watching a showtime"""
        message = {
            "type": "seat_update",
            "showtime_id": showtime_id,
            "data": seat_data
        }
        await self.broadcast_to_showtime(message, showtime_id, exclude_websocket)

    async def send_seat_reserved(self, showtime_id: int, seat_ids: List[int], user_session: str, exclude_websocket: WebSocket = None):
        """Notify that seats have been reserved"""
        message = {
            "type": "seats_reserved",
            "showtime_id": showtime_id,
            "data": {
                "seat_ids": seat_ids,
                "user_session": user_session,
                "timestamp": json.dumps({"$date": {"$numberLong": str(int(__import__('time').time() * 1000))}})
            }
        }
        await self.broadcast_to_showtime(message, showtime_id, exclude_websocket)

    async def send_seat_released(self, showtime_id: int, seat_ids: List[int], exclude_websocket: WebSocket = None):
        """Notify that seats have been released"""
        message = {
            "type": "seats_released",
            "showtime_id": showtime_id,
            "data": {
                "seat_ids": seat_ids,
                "timestamp": json.dumps({"$date": {"$numberLong": str(int(__import__('time').time() * 1000))}})
            }
        }
        await self.broadcast_to_showtime(message, showtime_id, exclude_websocket)

    def get_connection_count(self, showtime_id: int) -> int:
        """Get number of active connections for a showtime"""
        return len(self.active_connections.get(showtime_id, set()))

# Global WebSocket manager instance
websocket_manager = WebSocketManager()