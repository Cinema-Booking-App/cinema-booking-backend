from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime

# Enum trạng thái combo
class ComboStatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"
    deleted = "deleted"

# ======== Dish Schemas ========= #

class DishBase(BaseModel):
    dish_name: str
    description: Optional[str] = None

class DishCreate(DishBase):
    pass

class DishResponse(DishBase):
    dish_id: int

    class Config:
        from_attributes = True

# ======== Combo Item Schemas ========= #

class ComboItemBase(BaseModel):
    dish_id: int
    quantity: int = Field(..., gt=0)  # Đảm bảo quantity > 0

class ComboItemCreate(ComboItemBase):
    pass

class ComboItemResponse(ComboItemBase):
    item_id: int
    dish_name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

# ======== Combo Schemas ========= #

class ComboBase(BaseModel):
    combo_name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)  # Đảm bảo price > 0
    image_url: Optional[str] = None
    status: Optional[ComboStatusEnum] = ComboStatusEnum.active

class ComboCreate(ComboBase):
    items: List[ComboItemCreate]

class ComboUpdate(ComboBase):
    items: Optional[List[ComboItemCreate]] = None

class ComboResponse(ComboBase):
    combo_id: int
    created_at: datetime
    items: List[ComboItemResponse]

    class Config:
        from_attributes = True