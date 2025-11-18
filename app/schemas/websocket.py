"""
Schemas cho WebSocket - Định nghĩa cấu trúc dữ liệu cho tin nhắn WebSocket realtime
File này chứa các model Pydantic để validate và serialize dữ liệu WebSocket
"""

from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime


class WebSocketMessage(BaseModel):
    """Schema cơ bản cho tất cả tin nhắn WebSocket"""
    type: str          # Loại tin nhắn (seat_update, seats_reserved, etc.)
    showtime_id: int   # ID suất chiếu phim
    data: Any          # Dữ liệu tin nhắn (có thể là bất kỳ kiểu nào)


class SeatUpdateData(BaseModel):
    """Dữ liệu cập nhật trạng thái một ghế cụ thể"""
    seat_id: int                           # ID ghế được cập nhật
    status: str                            # Trạng thái mới (available, reserved, pending)
    expires_at: Optional[datetime] = None  # Thời gian hết hạn đặt ghế (nếu có)
    user_session: Optional[str] = None     # Session của người đặt ghế (nếu có)


class SeatsReservedData(BaseModel):
    """Dữ liệu thông báo ghế đã được đặt"""
    seat_ids: List[int]  # Danh sách ID các ghế đã được đặt
    user_session: str    # Session của người đặt ghế
    timestamp: str       # Thời điểm đặt ghế (ISO format)


class SeatsReleasedData(BaseModel):
    """Dữ liệu thông báo ghế đã được giải phóng"""
    seat_ids: List[int]  # Danh sách ID các ghế được giải phóng
    timestamp: str       # Thời điểm giải phóng ghế (ISO format)


class InitialSeatData(BaseModel):
    """Thông tin một ghế trong dữ liệu ban đầu"""
    seat_id: int                        # ID ghế
    status: str                         # Trạng thái ghế hiện tại
    expires_at: Optional[str] = None    # Thời gian hết hạn (string ISO)
    user_session: Optional[str] = None  # Session người đặt (nếu có)


class InitialData(BaseModel):
    """Dữ liệu ban đầu gửi cho client khi kết nối"""
    reserved_seats: List[InitialSeatData]  # Danh sách tất cả ghế đã được đặt


# ================================
# CÁC LOẠI TIN NHẮN WEBSOCKET CỤ THỂ
# ================================

class SeatUpdateMessage(WebSocketMessage):
    """Tin nhắn cập nhật trạng thái ghế"""
    data: SeatUpdateData


class SeatsReservedMessage(WebSocketMessage):
    """Tin nhắn thông báo ghế đã được đặt"""
    data: SeatsReservedData


class SeatsReleasedMessage(WebSocketMessage):
    """Tin nhắn thông báo ghế đã được giải phóng"""
    data: SeatsReleasedData


class InitialDataMessage(WebSocketMessage):
    """Tin nhắn dữ liệu ban đầu khi client kết nối"""
    type: str = "initial_data"  # Loại tin nhắn cố định
    data: InitialData           # Dữ liệu ghế ban đầu