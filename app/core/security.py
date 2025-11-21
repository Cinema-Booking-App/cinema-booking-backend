from fastapi import Depends, HTTPException, status
from app.models.users import UserStatusEnum, Users
from app.services.auth_service import get_current_user
from datetime import datetime, timedelta
from typing import Any, Union, Optional # <--- Đã thêm Union vào đây
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Hàm get_current_active_user vẫn ở đây
def get_current_active_user(current_user = Depends(get_current_user)): 
    if current_user.status != UserStatusEnum.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản chưa được xác minh"
        )
    return current_user
# Cấu hình hashing mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None,  extra_payload: Optional[dict] = None) -> str:
    """
    Hàm tạo JWT Token.
    Hỗ trợ subject là string (userId) hoặc dictionary (cho QR code payload).
    """
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Nếu subject là dict (ví dụ payload QR), copy và thêm exp
    if isinstance(subject, dict):
        to_encode = subject.copy()
        to_encode.update({"exp": expire})
        # Đảm bảo có claim 'sub' (subject) theo chuẩn JWT
        if "sub" not in to_encode:
             to_encode["sub"] = str(subject.get("ticket_id", "qr_code"))
    else:
        # Nếu subject là string (user_id thông thường)
        to_encode = {"exp": expire, "sub": str(subject)}
        
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu có khớp hash không"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Tạo hash từ mật khẩu"""
    return pwd_context.hash(password)