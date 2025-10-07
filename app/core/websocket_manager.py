from typing import Dict, List, Set
from fastapi import WebSocket
import json
import logging

# Khởi tạo logger để ghi log các hoạt động WebSocket
logger = logging.getLogger(__name__)

class WebSocketManager:
    """Lớp quản lý kết nối WebSocket cho hệ thống đặt vé xem phim theo thời gian thực"""
    
    def __init__(self):
        # Dictionary lưu trữ các kết nối WebSocket theo showtime_id (ID suất chiếu)
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Dictionary ánh xạ kết nối WebSocket với showtime_id tương ứng
        self.connection_showtime_map: Dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, showtime_id: int):
        """Chấp nhận kết nối WebSocket mới cho một suất chiếu cụ thể"""
        await websocket.accept()
        
        # Thêm kết nối vào nhóm của suất chiếu cụ thể
        if showtime_id not in self.active_connections:
            self.active_connections[showtime_id] = set()
        self.active_connections[showtime_id].add(websocket)
        
        # Ánh xạ kết nối với suất chiếu
        self.connection_showtime_map[websocket] = showtime_id
        
        logger.info(f"WebSocket kết nối thành công cho suất chiếu {showtime_id}. Tổng số kết nối: {len(self.active_connections[showtime_id])}")

    def disconnect(self, websocket: WebSocket):
        """Xóa kết nối WebSocket khi client ngắt kết nối"""
        if websocket in self.connection_showtime_map:
            showtime_id = self.connection_showtime_map[websocket]
            
            # Xóa kết nối khỏi nhóm suất chiếu
            if showtime_id in self.active_connections:
                self.active_connections[showtime_id].discard(websocket)
                # Nếu không còn kết nối nào, xóa luôn nhóm suất chiếu
                if not self.active_connections[showtime_id]:
                    del self.active_connections[showtime_id]
            
            # Xóa ánh xạ kết nối
            del self.connection_showtime_map[websocket]
            
            logger.info(f"WebSocket đã ngắt kết nối cho suất chiếu {showtime_id}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Gửi tin nhắn riêng tư đến một client cụ thể"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Lỗi khi gửi tin nhắn cá nhân: {e}")
            self.disconnect(websocket)

    async def broadcast_to_showtime(self, message: dict, showtime_id: int, exclude_websocket: WebSocket = None):
        """Phát sóng tin nhắn đến tất cả client đang xem một suất chiếu cụ thể"""
        if showtime_id not in self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected_connections = []
        
        # Duyệt qua tất cả kết nối trong suất chiếu
        for connection in self.active_connections[showtime_id].copy():
            # Bỏ qua kết nối được loại trừ (thường là người gửi)
            if exclude_websocket and connection == exclude_websocket:
                continue
                
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Lỗi khi phát sóng đến kết nối: {e}")
                disconnected_connections.append(connection)
        
        # Dọn dẹp các kết nối bị lỗi
        for connection in disconnected_connections:
            self.disconnect(connection)

    async def send_seat_update(self, showtime_id: int, seat_data: dict, exclude_websocket: WebSocket = None):
        """Gửi cập nhật trạng thái ghế ngồi đến tất cả client đang xem suất chiếu"""
        message = {
            "type": "seat_update",  # Loại tin nhắn: cập nhật ghế
            "showtime_id": showtime_id,
            "data": seat_data  # Dữ liệu trạng thái ghế
        }
        await self.broadcast_to_showtime(message, showtime_id, exclude_websocket)

    async def send_seat_reserved(self, showtime_id: int, seat_ids: List[int], user_session: str, exclude_websocket: WebSocket = None):
        """Thông báo rằng các ghế đã được đặt chỗ"""
        message = {
            "type": "seats_reserved",  # Loại tin nhắn: ghế đã được đặt
            "showtime_id": showtime_id,
            "data": {
                "seat_ids": seat_ids,  # Danh sách ID ghế được đặt
                "user_session": user_session,  # Phiên người dùng đặt ghế
                "timestamp": json.dumps({"$date": {"$numberLong": str(int(__import__('time').time() * 1000))}})  # Thời gian đặt ghế
            }
        }
        await self.broadcast_to_showtime(message, showtime_id, exclude_websocket)

    async def send_seat_released(self, showtime_id: int, seat_ids: List[int], exclude_websocket: WebSocket = None):
        """Thông báo rằng các ghế đã được giải phóng (hết thời gian giữ chỗ hoặc hủy đặt)"""
        message = {
            "type": "seats_released",  # Loại tin nhắn: ghế đã được giải phóng
            "showtime_id": showtime_id,
            "data": {
                "seat_ids": seat_ids,  # Danh sách ID ghế được giải phóng
                "timestamp": json.dumps({"$date": {"$numberLong": str(int(__import__('time').time() * 1000))}})  # Thời gian giải phóng ghế
            }
        }
        await self.broadcast_to_showtime(message, showtime_id, exclude_websocket)

    def get_connection_count(self, showtime_id: int) -> int:
        """Lấy số lượng kết nối đang hoạt động cho một suất chiếu"""
        return len(self.active_connections.get(showtime_id, set()))

# Instance toàn cục của WebSocket manager để sử dụng trong toàn bộ ứng dụng
websocket_manager = WebSocketManager()