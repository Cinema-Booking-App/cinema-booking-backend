from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RoomsBase(BaseModel):
    theater_id = int
    room_name = str
    layout_id = int

class RoomCreate(RoomsBase):
    pass

class RoomUpdate(BaseModel):
    theater_id: Optional[int] = None
    room_name: Optional[str] = None
    layout_id: Optional[int] = None

class RoomResponse(RoomsBase):
    room_id = int
    created_at: Optional[datetime] = None
    
    class Config: 
        from_attributes = True
