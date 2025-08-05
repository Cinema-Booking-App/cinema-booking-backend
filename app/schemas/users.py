from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models.users import UserStatusEnum, UserRoleEnum

class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: str
    status: UserStatusEnum = UserStatusEnum.active
    role: UserRoleEnum = UserRoleEnum.customer

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    status: Optional[UserStatusEnum] = None
    role: Optional[UserRoleEnum] = None

class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class UserResponse(UserBase):
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

