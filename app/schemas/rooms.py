from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RoomsBase(BaseModel):
    room_name : str
    layout_id : Optional[int] = None

class RoomCreate(RoomsBase):
    pass

class RoomUpdate(BaseModel):
    theater_id: Optional[int] = None
    room_name: Optional[str] = None
    layout_id: Optional[int] = None

class RoomResponse(RoomsBase):
    room_id : int
    theater_id : int =  None
    created_at: Optional[datetime] = None
    
    class Config: 
        from_attributes = True
