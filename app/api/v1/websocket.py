from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
import json
import logging

from app.core.database import get_db
from app.core.websocket_manager import websocket_manager
from app.services.reservations_service import get_reserved_seats

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/seats/{showtime_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    showtime_id: int,
    session_id: str = Query(None),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time seat updates"""
    await websocket_manager.connect(websocket, showtime_id)
    
    try:
        # Send initial seat data when client connects
        try:
            if showtime_id > 0:
                reserved_seats = get_reserved_seats(showtime_id, db)
                initial_data = {
                    "type": "initial_data",
                    "showtime_id": showtime_id,
                    "data": {
                        "reserved_seats": [
                            {
                                "seat_id": seat.seat_id,
                                "status": seat.status,
                                "expires_at": seat.expires_at.isoformat() if seat.expires_at else None,
                                "user_session": seat.session_id
                            } for seat in reserved_seats
                        ]
                    }
                }
                await websocket_manager.send_personal_message(json.dumps(initial_data), websocket)
            else:
                # Send empty initial data for invalid showtime
                initial_data = {
                    "type": "initial_data",
                    "showtime_id": showtime_id,
                    "data": {
                        "reserved_seats": [],
                        "error": "Invalid showtime ID"
                    }
                }
                await websocket_manager.send_personal_message(json.dumps(initial_data), websocket)
                logger.warning(f"Invalid showtime_id: {showtime_id}")
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")
            # Send error response instead of crashing
            try:
                error_data = {
                    "type": "error",
                    "showtime_id": showtime_id,
                    "data": {
                        "message": "Failed to load initial seat data",
                        "error": str(e)
                    }
                }
                await websocket_manager.send_personal_message(json.dumps(error_data), websocket)
            except:
                pass  # If we can't even send error, just continue
        
        # Listen for messages (heartbeat, ping, etc.)
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle ping/pong for connection health
                if message.get("type") == "ping":
                    await websocket_manager.send_personal_message(
                        json.dumps({"type": "pong"}), 
                        websocket
                    )
                elif message.get("type") == "heartbeat":
                    # Client is still alive, could update last seen time
                    pass
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in websocket communication: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Unexpected error in websocket endpoint: {e}")
    finally:
        websocket_manager.disconnect(websocket)


@router.get("/ws/status/{showtime_id}")
async def get_websocket_status(showtime_id: int):
    """Get WebSocket connection status for a showtime"""
    connection_count = websocket_manager.get_connection_count(showtime_id)
    return {
        "showtime_id": showtime_id,
        "active_connections": connection_count,
        "status": "active" if connection_count > 0 else "inactive"
    }