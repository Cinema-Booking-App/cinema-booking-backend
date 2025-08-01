# Nơi chứa các hàm tạo và refresh token

from jose import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings

def create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    """Tạo token JWT với dữ liệu, thời gian hết hạn và loại token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire, "type": token_type})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def refresh_token(data: dict) -> str:
    """Tạo refresh token mới."""
    to_encode = data.copy()
    # Thời gian hết hạn của refresh token có thể dài hơn
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    refreshed_token = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return refreshed_token

