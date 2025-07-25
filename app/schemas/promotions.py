from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class PromotionBase(BaseModel):
    code: str
    discount_percentage: float
    start_date: date
    end_date: date
    max_usage: Optional[int]
    description: Optional[str]

class PromotionCreate(PromotionBase):
    pass

class PromotionUpdate(BaseModel):
    code: Optional[str]
    discount_percentage: Optional[float]
    start_date: Optional[date]
    end_date: Optional[date]
    max_usage: Optional[int]
    description: Optional[str]

class PromotionResponse(PromotionBase):
    promotion_id: int
    used_count: int
    created_at: datetime

    class Config:
        from_attributes = True 