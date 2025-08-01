from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models.users import UserStatusEnum

class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    status: UserStatusEnum = UserStatusEnum.active

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    status: Optional[UserStatusEnum] = None

class UserResponse(UserBase):
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

