from typing import List, Optional
from pydantic import BaseModel, EmailStr
from app.models.users import UserStatusEnum, GenderEnum
from app.schemas.roles import RoleResponse
from datetime import datetime, date

class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    status: UserStatusEnum = UserStatusEnum.active
    is_verified: Optional[bool] = False

class UserCreate(UserBase):
    password: str

# Schema update user (cả admin lẫn user đều dùng được, tuỳ API nào cho phép)
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    status: Optional[UserStatusEnum] = None
    is_verified: Optional[bool] = None
    rank_id: Optional[int] = None

class UserResponse(UserBase):
    user_id: int
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    status: UserStatusEnum
    is_verified: bool
    last_login: Optional[datetime] = None
    loyalty_points: int
    rank_name: Optional[str] = None
    total_spent: float
    roles: List[RoleResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Schema dành cho USER (xem profile của chính mình)
class UserProfileResponse(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    loyalty_points: int
    rank_name: Optional[str] = None

    class Config:
        from_attributes = True

