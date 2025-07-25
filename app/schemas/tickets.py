from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TicketsBase(BaseModel):
    showtime_id: int
    seat_id: int

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime("%H:%M %d-%m-%Y") if v else None
        }

class TicketsCreate(TicketsBase):
    user_id:  Optional[int] = None
    promotion_id:  Optional[int] = None

    pass

class TicketsUpdate(TicketsBase):
    status:  Optional[str] = None

class TicketsResponse(TicketsBase):
    ticket_id: int
    price: float
    booking_time: datetime
    status: str
    cancelled_at:  Optional[datetime] = None
    seat_code: str
    seat_type: str

    class Config:
        from_attributes = True