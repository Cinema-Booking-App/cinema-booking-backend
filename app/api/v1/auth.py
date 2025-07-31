from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import EmailVerificationRequest, UserLogin, UserRegister
from app.services.auth_service import login, register, resend_verification_code, verify_email
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

# Xác nhận email với mã OTP
@router.post("/verify-email")
def verify_user_email(request: EmailVerificationRequest, db: Session = Depends(get_db)):
    return success_response(verify_email(db, request))

# Gửi lại mã xác nhận
@router.post("/resend-verification")
def resend_verification(email: str, db: Session = Depends(get_db)):
    return resend_verification_code(db, email)
