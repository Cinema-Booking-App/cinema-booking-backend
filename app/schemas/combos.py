# app/schemas/combos.py
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

# Enum trạng thái
class ComboStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"

# Schema của từng item bên trong combo
class ComboItemBase(BaseModel):
    item_name: str
    quantity: int

class ComboItemCreate(ComboItemBase):
    pass

class ComboItemResponse(ComboItemBase):
    item_id: int

    class Config:
        from_attributes = True

# Base cho combo
class ComboBase(BaseModel):
    combo_name: str
    description: Optional[str] = None
    price: float
    status: Optional[ComboStatusEnum] = ComboStatusEnum.ACTIVE

# Tạo combo kèm nhiều item
class ComboCreate(ComboBase):
    items: List[ComboItemCreate]

# Cập nhật combo (items có thể không thay đổi)
class ComboUpdate(ComboBase):
    items: Optional[List[ComboItemCreate]] = None

# Trả về combo cùng danh sách item
class ComboResponse(ComboBase):
    combo_id: int
    items: List[ComboItemResponse]

    class Config:
        from_attributes = True
