from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.users import UserLogin, UserRegister
from app.services.auth_service import login, register
from app.utils.response import success_response
router = APIRouter()

# Đăng ký tài khoản người dùng mới.
@router.post("/register")
def auth_register(user_in: UserRegister, db: Session = Depends(get_db)):
    return success_response(register(db, user_in))

# Đăng nhập tài khoản.
@router.post("/login")
def login_route(user_in: UserLogin, db: Session = Depends(get_db)):
    result = login(db, user_in)
    return success_response(result)

