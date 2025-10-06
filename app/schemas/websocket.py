from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class WebSocketMessage(BaseModel):
    type: str
    showtime_id: int
    data: Any

class SeatUpdateData(BaseModel):
    seat_id: int
    status: str
    expires_at: Optional[datetime] = None
    user_session: Optional[str] = None

class SeatsReservedData(BaseModel):
    seat_ids: List[int]
    user_session: str
    timestamp: str

class SeatsReleasedData(BaseModel):
    seat_ids: List[int]
    timestamp: str

class InitialSeatData(BaseModel):
    seat_id: int
    status: str
    expires_at: Optional[str] = None
    user_session: Optional[str] = None

class InitialData(BaseModel):
    reserved_seats: List[InitialSeatData]

# WebSocket message types
class SeatUpdateMessage(WebSocketMessage):
    data: SeatUpdateData

class SeatsReservedMessage(WebSocketMessage):
    data: SeatsReservedData

class SeatsReleasedMessage(WebSocketMessage):
    data: SeatsReleasedData

class InitialDataMessage(WebSocketMessage):
    type: str = "initial_data"
    data: InitialData