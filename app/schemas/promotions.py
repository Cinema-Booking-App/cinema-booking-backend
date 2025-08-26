from pydantic import BaseModel, validator, computed_field
from datetime import date, datetime
from typing import Optional

class PromotionBase(BaseModel):
    code: str
    discount_percentage: float
    start_date: date
    end_date: date
    max_usage: Optional[int]
    description: Optional[str]
    is_active: Optional[bool] = True

    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @validator('discount_percentage')
    def discount_must_be_valid(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('Discount percentage must be between 0 and 100')
        return v

class PromotionCreate(PromotionBase):
    pass

class PromotionUpdate(BaseModel):
    code: Optional[str]
    discount_percentage: Optional[float]
    start_date: Optional[date]
    end_date: Optional[date]
    max_usage: Optional[int]
    description: Optional[str]
    is_active: Optional[bool]

class PromotionResponse(PromotionBase):
    promotion_id: int
    used_count: int
    is_active: bool
    created_at: datetime

    @computed_field
    @property
    def status(self) -> str:
        """Compute status based on dates and active state"""
        today = date.today()
        
        if not self.is_active:
            return "Inactive"
        
        if today < self.start_date:
            return "Pending"
        elif today > self.end_date:
            return "Expired"
        else:
            return "Active"

    class Config:
        from_attributes = True

class PromotionStatusUpdate(BaseModel):
    is_active: bool 