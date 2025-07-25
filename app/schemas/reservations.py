from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class SeatReservationsBase(BaseModel):
    seat_id: int
    showtime_id: int
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    status: str = "pending"
    transaction_id: Optional[int] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime("%H:%M %d-%m-%Y") if v else None
        }

class SeatReservationsCreate(SeatReservationsBase):
    pass

class SeatReservationsUpdate(SeatReservationsBase):
    seat_id: Optional[int] = None
    showtime_id: Optional[int] = None
    reserved_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    status: Optional[str] = None
    transaction_id: Optional[int] = None

class SeatReservationsResponse(SeatReservationsBase):
    reservation_id: int
    reserved_at: datetime
    expires_at: datetime
    
