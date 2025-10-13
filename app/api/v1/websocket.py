from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
import json
import logging
import asyncio

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
    """Endpoint WebSocket chính cho cập nhật trạng thái ghế theo thời gian thực"""
    
    # Kết nối client vào nhóm suất chiếu
    try:
        await websocket_manager.connect(websocket, showtime_id, session_id)
    except Exception as e:
        logger.error(f"❌ Failed to connect websocket: {e}")
        return
    
    try:
        # Gửi dữ liệu ban đầu khi client kết nối
        await send_initial_data(websocket, showtime_id, db)
        
        # Vòng lặp nhận tin nhắn từ client
        await handle_client_messages(websocket)
                
    except WebSocketDisconnect:
        logger.info(f"🔌 Client disconnected normally: showtime={showtime_id}")
    except Exception as e:
        logger.error(f"❌ Unexpected error in WebSocket: {e}", exc_info=True)
    finally:
        # Luôn đảm bảo ngắt kết nối và dọn dẹp
        await websocket_manager.disconnect(websocket)


async def send_initial_data(websocket: WebSocket, showtime_id: int, db: Session):
    """Gửi dữ liệu ban đầu cho client khi kết nối"""
    try:
        if showtime_id <= 0:
            await send_error(websocket, showtime_id, "Invalid showtime ID")
            return
        
        # Lấy danh sách ghế đã được đặt
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
        
        await websocket.send_text(json.dumps(initial_data))
        logger.info(f"📤 Sent initial data: {len(reserved_seats)} reserved seats")
        
    except Exception as e:
        logger.error(f"❌ Error sending initial data: {e}", exc_info=True)
        await send_error(websocket, showtime_id, f"Failed to load initial data: {str(e)}")


async def send_error(websocket: WebSocket, showtime_id: int, error_message: str):
    """Gửi thông báo lỗi đến client"""
    try:
        error_data = {
            "type": "error",
            "showtime_id": showtime_id,
            "data": {
                "message": error_message
            }
        }
        await websocket.send_text(json.dumps(error_data))
    except Exception as e:
        logger.error(f"❌ Failed to send error message: {e}")


async def handle_client_messages(websocket: WebSocket):
    """Xử lý tin nhắn từ client"""
    try:
        while True:
            # Thêm timeout để tránh treo vô thời hạn
            data = await asyncio.wait_for(
                websocket.receive_text(), 
                timeout=60.0  # 60 giây timeout
            )
            
            message = json.loads(data)
            message_type = message.get("type")
            
            # Xử lý các loại tin nhắn
            if message_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                
            elif message_type == "heartbeat":
                # Heartbeat - giữ kết nối sống
                await websocket.send_text(json.dumps({
                    "type": "heartbeat_ack",
                    "timestamp": message.get("timestamp")
                }))
                
            else:
                logger.debug(f"📨 Received message type: {message_type}")
                
    except asyncio.TimeoutError:
        logger.warning("⏱️ WebSocket timeout - no message received in 60s")
        raise WebSocketDisconnect()
    except WebSocketDisconnect:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON received: {e}")
    except Exception as e:
        logger.error(f"❌ Error handling message: {e}", exc_info=True)
        raise


@router.get("/ws/status/{showtime_id}")
async def get_websocket_status(showtime_id: int):
    """Lấy trạng thái kết nối WebSocket cho một suất chiếu"""
    connection_count = websocket_manager.get_connection_count(showtime_id)
    connections_info = websocket_manager.get_all_connections_info(showtime_id)
    
    return {
        "showtime_id": showtime_id,
        "active_connections": connection_count,
        "status": "active" if connection_count > 0 else "inactive",
        "connections": connections_info
    }