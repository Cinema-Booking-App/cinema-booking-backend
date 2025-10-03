from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class SeatsBase(BaseModel):
    seat_type: str
    seat_code: str
    is_available: bool = True
    row_number: int
    column_number: int
    is_edge: bool = False

class SeatsCreate(SeatsBase):
    room_id: int

class SeatsUpdate(SeatsBase):
    seat_type: Optional[str] = None
    seat_code: Optional[str] = None
    is_available: Optional[bool] = None
    row_number: Optional[int] = None
    column_number: Optional[int] = None   
    is_edge: Optional[bool] = None

class SeatsResponse(SeatsBase):
    seat_id: int
    room_id: int
    created_at: Optional[datetime] = None 

    class Config:
        from_attributes = True 