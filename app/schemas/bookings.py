from typing import List, Optional
from pydantic import BaseModel
from datetime import date


class BookingTicketItem(BaseModel):
    ticket_id: int
    seat: str
    type: Optional[str] = None
    price: Optional[float] = None


class BookingResponse(BaseModel):
    code: str
    customer: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    movie: Optional[str] = None
    showtime: Optional[str] = None
    date: Optional[str] = None
    seats: Optional[str] = None
    status: Optional[str] = None
    tickets: List[BookingTicketItem] = []
    printed: bool = False
    received: bool = False
    refunded: bool = False
    qr: Optional[str] = None

    class Config:
        orm_mode = True
