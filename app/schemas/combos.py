from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Combo Item dùng để lồng trong combo
class ComboItemBase(BaseModel):
    dish_id: int
    quantity: int

class ComboItemCreate(ComboItemBase):
    pass

class ComboItemUpdate(BaseModel):
    dish_id: Optional[int]
    quantity: Optional[int]

class ComboItemResponse(ComboItemBase):
    item_id: int

    class Config:
        from_attributes = True


# Combo
class ComboBase(BaseModel):
    combo_name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    status: Optional[str] = None

class ComboCreate(ComboBase):
    items: List[ComboItemCreate]
    status: Optional[str] = "active"

class ComboUpdate(BaseModel):
    combo_name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    status: Optional[str] = None
    items: Optional[List[ComboItemUpdate]]

class ComboResponse(ComboBase):
    combo_id: int
    combo_items: List[ComboItemResponse] = []

    class Config:
        from_attributes = True

# Schema cơ sở cho ComboDish
class ComboDishBase(BaseModel):
    dish_name: str
    description: Optional[str] = None

# Schema cho tạo mới ComboDish
class ComboDishCreate(ComboDishBase):
    pass

# Schema cho cập nhật ComboDish
class ComboDishUpdate(BaseModel):
    dish_name: Optional[str] = None
    description: Optional[str] = None

# Schema cho phản hồi ComboDish
class ComboDishResponse(ComboDishBase):
    dish_id: int

    class Config:
        from_attributes = True
