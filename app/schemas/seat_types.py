from typing import Optional
from pydantic import BaseModel

class SeatTypeBase(BaseModel):
    type_name  : Optional[str] = None
    price_multiplier : Optional[float] = None
    additional_fee : Optional[float] = None
    note  : Optional[str] = None

class SeatTypeCreate(SeatTypeBase):
    pass

class SeatTypeUpdate(BaseModel):
    type_name  : Optional[str] = None
    price_multiplier : Optional[float] = None
    additional_fee : Optional[float] = None
    note  : Optional[str] = None

class SeatTypeResponse(SeatTypeBase):
    seat_type_id : int
    class Config:
        from_attributes = True