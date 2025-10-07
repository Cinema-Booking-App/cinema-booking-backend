# Import các thư viện cần thiết cho WebSocket API
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
import json
import logging

# Import các module nội bộ
from app.core.database import get_db
from app.core.websocket_manager import websocket_manager  # Manager quản lý kết nối WebSocket
from app.services.reservations_service import get_reserved_seats  # Service lấy thông tin ghế đã đặt

# Khởi tạo logger để ghi log hoạt động WebSocket
logger = logging.getLogger(__name__)
router = APIRouter()  # Router cho các endpoint WebSocket

@router.websocket("/ws/seats/{showtime_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    showtime_id: int,
    session_id: str = Query(None),
    db: Session = Depends(get_db)
):
    """Endpoint WebSocket chính cho cập nhật trạng thái ghế theo thời gian thực
    
    Args:
        websocket (WebSocket): Kết nối WebSocket từ client
        showtime_id (int): ID suất chiếu phim
        session_id (str): ID phiên của người dùng (tùy chọn)
        db (Session): Phiên kết nối database
    """
    # Kết nối client vào nhóm suất chiếu
    await websocket_manager.connect(websocket, showtime_id)
    
    try:
        # Gửi dữ liệu ban đầu khi client kết nối (danh sách ghế đã đặt)
        try:
            if showtime_id > 0:  # Kiểm tra showtime_id hợp lệ
                # Lấy danh sách ghế đã được đặt cho suất chiếu này
                reserved_seats = get_reserved_seats(showtime_id, db)
                
                # Tạo dữ liệu ban đầu gửi cho client
                initial_data = {
                    "type": "initial_data",  # Loại tin nhắn: dữ liệu ban đầu
                    "showtime_id": showtime_id,
                    "data": {
                        "reserved_seats": [  # Danh sách ghế đã đặt
                            {
                                "seat_id": seat.seat_id,  # ID ghế
                                "status": seat.status,    # Trạng thái ghế (pending, confirmed)
                                "expires_at": seat.expires_at.isoformat() if seat.expires_at else None,  # Thời gian hết hạn
                                "user_session": seat.session_id  # Phiên người đặt
                            } for seat in reserved_seats
                        ]
                    }
                }
                # Gửi dữ liệu ban đầu đến client vừa kết nối
                await websocket_manager.send_personal_message(json.dumps(initial_data), websocket)
            else:
                # Gửi dữ liệu trống cho showtime_id không hợp lệ
                initial_data = {
                    "type": "initial_data",
                    "showtime_id": showtime_id,
                    "data": {
                        "reserved_seats": [],  # Danh sách trống
                        "error": "Invalid showtime ID"  # Thông báo lỗi
                    }
                }
                await websocket_manager.send_personal_message(json.dumps(initial_data), websocket)
                logger.warning(f"Showtime_id không hợp lệ: {showtime_id}")
        except Exception as e:
            logger.error(f"Lỗi khi gửi dữ liệu ban đầu: {e}")
            # Gửi thông báo lỗi thay vì crash ứng dụng
            try:
                error_data = {
                    "type": "error",  # Loại tin nhắn: lỗi
                    "showtime_id": showtime_id,
                    "data": {
                        "message": "Không thể tải dữ liệu ghế ban đầu",
                        "error": str(e)
                    }
                }
                await websocket_manager.send_personal_message(json.dumps(error_data), websocket)
            except:
                pass  # Nếu không thể gửi lỗi, tiếp tục
        
        # Lắng nghe tin nhắn từ client (heartbeat, ping, v.v.)
        while True:
            try:
                # Nhận tin nhắn text từ client
                data = await websocket.receive_text()
                message = json.loads(data)  # Parse JSON
                
                # Xử lý ping/pong để kiểm tra sức khỏe kết nối
                if message.get("type") == "ping":
                    # Trả lời pong khi nhận ping
                    await websocket_manager.send_personal_message(
                        json.dumps({"type": "pong"}), 
                        websocket
                    )
                elif message.get("type") == "heartbeat":
                    # Client vẫn sống, có thể cập nhật thời gian gần đây nhất
                    pass
                    
            except WebSocketDisconnect:
                # Client ngắt kết nối bình thường
                break
            except Exception as e:
                logger.error(f"Lỗi trong giao tiếp WebSocket: {e}")
                break
                
    except WebSocketDisconnect:
        # Xử lý khi client ngắt kết nối
        pass
    except Exception as e:
        logger.error(f"Lỗi không mong muốn trong WebSocket endpoint: {e}")
    finally:
        # Luôn đảm bảo ngắt kết nối và dọn dẹp
        websocket_manager.disconnect(websocket)


@router.get("/ws/status/{showtime_id}")
async def get_websocket_status(showtime_id: int):
    """Lấy trạng thái kết nối WebSocket cho một suất chiếu
    
    Args:
        showtime_id (int): ID suất chiếu cần kiểm tra
        
    Returns:
        dict: Thông tin trạng thái bao gồm số kết nối đang hoạt động
    """
    # Đếm số kết nối WebSocket đang hoạt động
    connection_count = websocket_manager.get_connection_count(showtime_id)
    return {
        "showtime_id": showtime_id,
        "active_connections": connection_count,  # Số kết nối đang hoạt động
        "status": "active" if connection_count > 0 else "inactive"  # Trạng thái: hoạt động hoặc không hoạt động
    }