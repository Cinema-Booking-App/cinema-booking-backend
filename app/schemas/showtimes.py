from pydantic import BaseModel
from typing import Optional

class ShowtimesBase(BaseModel):
    movie_id: int
    room_id: int
    show_datetime: str 
    format: str
    ticket_price: float
    status: str
    language: str

class ShowtimesCreate(ShowtimesBase):
    pass

class ShowtimesUpdate(BaseModel):
    movie_id: Optional[int] = None
    room_id: Optional[int] = None
    show_datetime: Optional[str] = None
    format: Optional[str] = None
    ticket_price: Optional[float] = None
    status: Optional[str] = None
    language: Optional[str] = None

class ShowtimesResponse(ShowtimesBase):
    showtime_id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
