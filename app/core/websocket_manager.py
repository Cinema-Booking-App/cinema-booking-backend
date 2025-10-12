from typing import Dict, List, Set
from fastapi import WebSocket
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Lớp quản lý kết nối WebSocket cho hệ thống đặt vé xem phim theo thời gian thực"""
    
    def __init__(self):
        # Dictionary lưu trữ các kết nối WebSocket theo showtime_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Dictionary ánh xạ kết nối WebSocket với showtime_id và session_id
        self.connection_info: Dict[WebSocket, Dict] = {}
        # Lock để tránh race condition
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, showtime_id: int, session_id: str = None):
        """Chấp nhận kết nối WebSocket mới cho một suất chiếu cụ thể"""
        try:
            await websocket.accept()
            
            async with self._lock:
                # Thêm kết nối vào nhóm của suất chiếu cụ thể
                if showtime_id not in self.active_connections:
                    self.active_connections[showtime_id] = set()
                self.active_connections[showtime_id].add(websocket)
                
                # Lưu thông tin kết nối
                self.connection_info[websocket] = {
                    "showtime_id": showtime_id,
                    "session_id": session_id,
                    "connected_at": asyncio.get_event_loop().time()
                }
                
            logger.info(
                f"✅ WebSocket connected: showtime={showtime_id}, "
                f"session={session_id}, total={len(self.active_connections[showtime_id])}"
            )
            
        except Exception as e:
            logger.error(f"❌ Error in connect: {e}")
            raise

    async def disconnect(self, websocket: WebSocket):
        """Xóa kết nối WebSocket khi client ngắt kết nối"""
        async with self._lock:
            if websocket in self.connection_info:
                info = self.connection_info[websocket]
                showtime_id = info["showtime_id"]
                session_id = info.get("session_id")
                
                # Xóa kết nối khỏi nhóm suất chiếu
                if showtime_id in self.active_connections:
                    self.active_connections[showtime_id].discard(websocket)
                    # Nếu không còn kết nối nào, xóa luôn nhóm suất chiếu
                    if not self.active_connections[showtime_id]:
                        del self.active_connections[showtime_id]
                
                # Xóa thông tin kết nối
                del self.connection_info[websocket]
                
                logger.info(
                    f"🔌 WebSocket disconnected: showtime={showtime_id}, "
                    f"session={session_id}"
                )

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Gửi tin nhắn riêng tư đến một client cụ thể"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"❌ Error sending personal message: {e}")
            await self.disconnect(websocket)

    async def broadcast_to_showtime(
        self, 
        message: dict, 
        showtime_id: int, 
        exclude_websocket: WebSocket = None,
        only_session: str = None
    ):
        """Phát sóng tin nhắn đến tất cả client đang xem một suất chiếu cụ thể"""
        if showtime_id not in self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected_connections = []
        sent_count = 0
        
        # Duyệt qua tất cả kết nối trong suất chiếu
        for connection in list(self.active_connections.get(showtime_id, set())):
            # Bỏ qua kết nối được loại trừ
            if exclude_websocket and connection == exclude_websocket:
                continue
            
            # Nếu chỉ gửi cho session cụ thể
            if only_session:
                info = self.connection_info.get(connection, {})
                if info.get("session_id") != only_session:
                    continue
                
            try:
                await connection.send_text(message_str)
                sent_count += 1
            except Exception as e:
                logger.error(f"❌ Error broadcasting to connection: {e}")
                disconnected_connections.append(connection)
        
        # Dọn dẹp các kết nối bị lỗi
        for connection in disconnected_connections:
            await self.disconnect(connection)
        
        logger.debug(f"📢 Broadcast sent to {sent_count} connections")

    async def send_seat_update(
        self, 
        showtime_id: int, 
        seat_data: dict, 
        exclude_websocket: WebSocket = None
    ):
        """Gửi cập nhật trạng thái ghế ngồi đến tất cả client đang xem suất chiếu"""
        message = {
            "type": "seat_update",
            "showtime_id": showtime_id,
            "data": seat_data
        }
        await self.broadcast_to_showtime(message, showtime_id, exclude_websocket)

    async def send_seat_reserved(
        self, 
        showtime_id: int, 
        seat_ids: List[int], 
        user_session: str, 
        exclude_websocket: WebSocket = None
    ):
        """Thông báo rằng các ghế đã được đặt chỗ"""
        from datetime import datetime
        
        message = {
            "type": "seats_reserved",
            "showtime_id": showtime_id,
            "data": {
                "seat_ids": seat_ids,
                "user_session": user_session,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.broadcast_to_showtime(message, showtime_id, exclude_websocket)

    async def send_seat_released(
        self, 
        showtime_id: int, 
        seat_ids: List[int], 
        exclude_websocket: WebSocket = None,
        reason: str = "user_cancelled"
    ):
        """Thông báo rằng các ghế đã được giải phóng"""
        from datetime import datetime
        
        message = {
            "type": "seat_released",
            "showtime_id": showtime_id,
            "seat_ids": seat_ids,
            "timestamp": datetime.now().isoformat(),
            "reason": reason
        }
        
        logger.info(f"🔄 Broadcasting seat_released: showtime={showtime_id}, seats={seat_ids}")
        await self.broadcast_to_showtime(message, showtime_id, exclude_websocket)

    def get_connection_count(self, showtime_id: int) -> int:
        """Lấy số lượng kết nối đang hoạt động cho một suất chiếu"""
        return len(self.active_connections.get(showtime_id, set()))
    
    def get_all_connections_info(self, showtime_id: int) -> List[Dict]:
        """Lấy thông tin chi tiết của tất cả kết nối cho một suất chiếu"""
        connections = self.active_connections.get(showtime_id, set())
        return [
            {
                "session_id": self.connection_info[conn].get("session_id"),
                "connected_at": self.connection_info[conn].get("connected_at")
            }
            for conn in connections
            if conn in self.connection_info
        ]

# Instance toàn cục của WebSocket manager
websocket_manager = WebSocketManager()