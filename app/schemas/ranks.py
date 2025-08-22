from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RankBase(BaseModel):
    rank_name: str
    spending_target: float
    ticket_percent: float
    combo_percent: float
    is_default: bool


class RankCreate(RankBase):
    pass

class RankUpdate(BaseModel):
    rank_name: Optional[str] = None
    spending_target: Optional[float] = None
    ticket_percent: Optional[float] = None
    combo_percent: Optional[float] = None
    is_default: Optional[bool] = None

class RankResponse(RankBase):
    rank_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        