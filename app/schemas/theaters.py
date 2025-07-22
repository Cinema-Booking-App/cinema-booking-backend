from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TheaterBase(BaseModel):
    name: str
    address: str
    city: Optional[str] = None
    phone: Optional[str] = None

class TheaterCreate(TheaterBase):
    pass

class TheaterUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None

class TheaterResponse(TheaterBase):
    theater_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True 