from pydantic import BaseModel
<<<<<<< HEAD
from datetime import date, time, datetime
=======
>>>>>>> e06283a8d15f65a28d59c517e70b5ceb178f84f9
from typing import Optional

class ShowtimesBase(BaseModel):
    movie_id: int
<<<<<<< HEAD
    screen_id: int
    show_date: date
    show_time: time
    format: str
    ticket_price: float
=======
    room_id: int
    show_datetime: str 
    format: str
    ticket_price: float
    status: str
    language: str
    available_seats : int 
>>>>>>> e06283a8d15f65a28d59c517e70b5ceb178f84f9

class ShowtimesCreate(ShowtimesBase):
    pass

class ShowtimesUpdate(BaseModel):
<<<<<<< HEAD
    movie_id: Optional[int]
    screen_id: Optional[int]
    show_date: Optional[date]
    show_time: Optional[time]
    format: Optional[str]
    ticket_price: Optional[float]

class ShowtimesResponse(ShowtimesBase):
    showtime_id: int
    created_at: datetime
    class Config:
        orm_mode = True 
=======
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
>>>>>>> e06283a8d15f65a28d59c517e70b5ceb178f84f9
