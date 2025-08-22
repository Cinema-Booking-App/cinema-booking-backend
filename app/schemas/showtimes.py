from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ShowtimesBase(BaseModel):
    movie_id: int
    theater_id: int 
    room_id: int
    show_datetime: datetime  
    format: str
    ticket_price: float
    status: str
    language: str

class ShowtimesCreate(ShowtimesBase):
    pass

class ShowtimesUpdate(BaseModel):
    movie_id: Optional[int] = None
    theater_id: Optional[int] = None 
    room_id: Optional[int] = None
    show_datetime: Optional[datetime] = None
    format: Optional[str] = None
    ticket_price: Optional[float] = None
    status: Optional[str] = None
    language: Optional[str] = None

class ShowtimesResponse(ShowtimesBase):
    showtime_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True