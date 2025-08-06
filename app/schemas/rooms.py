from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RoomsBase(BaseModel):
    room_name: str
    layout_id: Optional[int] = None
    room_status: str = "active"

class RoomCreate(RoomsBase):
    pass

class RoomUpdate(BaseModel):
    theater_id: Optional[int] = None
    room_name: Optional[str] = None
    layout_id: Optional[int] = None
    room_status: Optional[str] = None

class RoomResponse(RoomsBase):
    room_id: int
    theater_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True