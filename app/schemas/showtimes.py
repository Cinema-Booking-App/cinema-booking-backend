from pydantic import BaseModel
from datetime import date, time, datetime
from typing import Optional

class ShowtimesBase(BaseModel):
    movie_id: int
    screen_id: int
    show_date: date
    show_time: time
    format: str
    ticket_price: float

class ShowtimesCreate(ShowtimesBase):
    pass

class ShowtimesUpdate(BaseModel):
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