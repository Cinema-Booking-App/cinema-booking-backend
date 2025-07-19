from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.user import UserLogin, UserRegister, UserResponse
from app.services.auth_service import login, register
router = APIRouter()

# Đăng ký tài khoản người dùng mới.
@router.post("/register",response_model= UserResponse)
def auth_register(user_in: UserRegister, db: Session = Depends(get_db)):
    return register(db, user_in)

# Đăng nhập tài khoản.
@router.post("/login")
def auth_login(user_in: UserLogin, db: Session = Depends(get_db)):
    return login(db, user_in)

# @router.post("/refresh")
# def refresh_token(refresh_token: str):
#     try:
#         payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#         if payload.get("type") != "refresh":
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
#         email = payload.get("sub")
#         access_token = create_access_token({"sub": email})
#         return {"access_token": access_token, "token_type": "bearer"}
#     except JWTError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

