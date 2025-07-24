from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class SeatReservationsBase(BaseModel):
    seat_id: int
    showtime_id: int
    user_id: Optional[int] = None 
    session_id: Optional[str] = None
    reserved_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    status: str = "pending"
    transaction_id: Optional[int] = None

    class Config:
        from_attributes = True

class SeatReservationsCreate(SeatReservationsBase):
    expires_at: datetime 

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